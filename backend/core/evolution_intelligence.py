"""Typed evolution intelligence helpers.

This module keeps the high-risk evolution calculations independent from
FastAPI routes and SQLModel query plumbing: dedupe reports, safety summaries,
and scheduler next actions.
"""
from __future__ import annotations

import hashlib
import json
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from typing import Any, TypedDict, cast


@dataclass(frozen=True)
class RawDedupeCandidate:
    """Minimal raw-content shape required for duplicate analysis."""

    id: int | None
    raw_uuid: str
    title: str | None
    content_hash: str | None
    processing_status: str
    url: str | None = None
    source_id: int | None = None


@dataclass(frozen=True)
class SafetyEventSnapshot:
    """Minimal safety event shape required for audit reports."""

    id: int | None
    task_type: str
    source: str
    risk_level: str
    flags_json: str
    payload_hash: str
    payload_preview: str | None
    message: str | None
    alternatives_json: str | None
    blocked: bool
    created_at_iso: str


class DedupeCluster(TypedDict, total=False):
    kind: str
    item_ids: list[int]
    raw_uuids: list[str]
    titles: list[str | None]
    statuses: list[str]
    recommendation: str
    similarity_scores: list[float]


def loads_list(text: str | None) -> list[Any]:
    """Load a JSON list, returning an empty list for absent or malformed data."""
    if not text:
        return []
    try:
        data: Any = json.loads(text)
    except Exception:
        return []
    return data if isinstance(data, list) else []


def loads_dict(text: str | None) -> dict[str, Any]:
    """Load a JSON object, returning an empty dict for absent or malformed data."""
    if not text:
        return {}
    try:
        data: Any = json.loads(text)
    except Exception:
        return {}
    return cast(dict[str, Any], data) if isinstance(data, dict) else {}


def semantic_tokens(text: str) -> set[str]:
    """Tokenize mixed Chinese/Latin titles for conservative semantic dedupe."""
    normalized = "".join(char.lower() if char.isalnum() or "\u4e00" <= char <= "\u9fff" else " " for char in text)
    words = {word for word in normalized.split() if len(word) >= 2}
    chinese_chars = {char for char in normalized if "\u4e00" <= char <= "\u9fff"}
    return words | chinese_chars


def metadata_vector_signature(text: str, dimensions: int = 64) -> list[float]:
    """Build a deterministic local vector signature for metadata-level dedupe."""
    tokens = sorted(semantic_tokens(text) | _char_ngrams(text))
    if not tokens:
        return [0.0] * dimensions
    vector = [0.0] * dimensions
    for token in tokens:
        digest = hashlib.blake2b(token.encode("utf-8"), digest_size=4).digest()
        number = int.from_bytes(digest, "big")
        index = number % dimensions
        sign = 1.0 if (number // dimensions) % 2 == 0 else -1.0
        vector[index] += sign
    norm = sum(value * value for value in vector) ** 0.5
    if norm == 0:
        return [0.0] * dimensions
    return [round(value / norm, 6) for value in vector]


def metadata_vector_similarity(left: str, right: str) -> float:
    """Return cosine similarity between two metadata vector signatures."""
    left_vector = metadata_vector_signature(left)
    right_vector = metadata_vector_signature(right)
    return round(sum(left_value * right_value for left_value, right_value in zip(left_vector, right_vector, strict=True)), 3)


def build_dedupe_report(items: Sequence[RawDedupeCandidate]) -> dict[str, Any]:
    """Build exact-hash and semantic-title duplicate clusters."""
    candidates = [item for item in items if _is_operational_dedupe_candidate(item)]
    hash_groups: dict[str, list[RawDedupeCandidate]] = {}
    for item in candidates:
        if item.content_hash:
            hash_groups.setdefault(item.content_hash, []).append(item)

    exact_clusters = [_dedupe_cluster("hash", group) for group in hash_groups.values() if len(group) > 1]
    semantic_clusters = _semantic_dedupe_clusters(candidates)
    vector_clusters = _vector_dedupe_clusters(candidates)
    duplicate_ids: set[int] = set()
    for cluster in exact_clusters + semantic_clusters + vector_clusters:
        duplicate_ids.update(cluster["item_ids"])

    return {
        "principle": "先用 hash 抓确定重复，再用标题 token Jaccard 抓语义近邻；数给风险，图给簇结构。",
        "method": {
            "exact": "content_hash",
            "semantic": "title_token_jaccard>=0.72",
            "vector": "metadata_char_ngram_cosine>=0.86",
            "vector_ready": "当前使用本地元数据向量签名；安装 sqlite-vec 后可把同一签名持久化并替换为 ANN 检索。",
        },
        "summary": {
            "scanned": len(candidates),
            "ignored": len(items) - len(candidates),
            "clusters": len(exact_clusters) + len(semantic_clusters) + len(vector_clusters),
            "exact_clusters": len(exact_clusters),
            "semantic_clusters": len(semantic_clusters),
            "vector_clusters": len(vector_clusters),
            "duplicate_review_needed": len(duplicate_ids),
        },
        "clusters": (exact_clusters + semantic_clusters + vector_clusters)[:24],
    }


def build_safety_events_report(events: Sequence[SafetyEventSnapshot]) -> dict[str, Any]:
    """Summarize blocked safety events for evolution reports."""
    flag_counts: dict[str, int] = {}
    risk_counts: dict[str, int] = {}
    for event in events:
        risk_counts[event.risk_level] = risk_counts.get(event.risk_level, 0) + 1
        for flag in loads_list(event.flags_json):
            flag_key = str(flag)
            flag_counts[flag_key] = flag_counts.get(flag_key, 0) + 1
    return {
        "summary": {
            "total": len(events),
            "blocked": sum(1 for event in events if event.blocked),
            "by_risk": risk_counts,
            "top_flags": [flag for flag, _count in sorted(flag_counts.items(), key=lambda item: (-item[1], item[0]))],
        },
        "events": [_safety_event_to_dict(event) for event in events[:20]],
    }


def scheduler_next_actions(
    batch_result: Mapping[str, Any],
    dedupe: Mapping[str, Any],
    import_quality: Mapping[str, Any],
    safety: Mapping[str, Any],
) -> list[dict[str, str]]:
    """Select next commander actions from batch, dedupe, import quality, and safety reports."""
    actions: list[dict[str, str]] = []
    duplicate_count = _as_int(_summary_value(dedupe, "duplicate_review_needed"))
    if duplicate_count:
        actions.append({"priority": "high", "action": "复核语义重复候选", "reason": f"{duplicate_count} 条候选进入重复复核队列。"})

    quality_score = _as_float(import_quality.get("quality_score"))
    if quality_score < 75:
        actions.append({"priority": "high", "action": "提升导入字段完整度", "reason": f"导入质量分 {quality_score:g}，低于世界级训练资产阈值。"})

    blocked = _as_int(_summary_value(safety, "blocked"))
    if blocked:
        actions.append({"priority": "high", "action": "审计安全硬阻断样例", "reason": f"发现 {blocked} 条高风险请求。"})

    batch_summary = _as_mapping(batch_result.get("summary"))
    if _as_int(batch_summary.get("published_assets")) == 0:
        actions.append({"priority": "medium", "action": "增加 reviewed 标注并发布训练资产", "reason": "本轮没有发布新训练资产。"})

    if not actions:
        actions.append({"priority": "low", "action": "维持每周调度", "reason": "数据生命体本轮状态健康，可继续周期运行。"})
    return actions[:6]


def _semantic_dedupe_clusters(items: Sequence[RawDedupeCandidate]) -> list[DedupeCluster]:
    clusters: list[DedupeCluster] = []
    used_pairs: set[tuple[int, int]] = set()
    for index, item in enumerate(items):
        if item.id is None or not item.title:
            continue
        tokens = semantic_tokens(item.title)
        if not tokens:
            continue
        members = [item]
        scores: list[float] = []
        for peer in items[index + 1:]:
            if peer.id is None or not peer.title:
                continue
            low, high = sorted((item.id, peer.id))
            pair = (low, high)
            if pair in used_pairs:
                continue
            peer_tokens = semantic_tokens(peer.title)
            if not peer_tokens:
                continue
            score = len(tokens & peer_tokens) / max(len(tokens | peer_tokens), 1)
            if score >= 0.72:
                used_pairs.add(pair)
                members.append(peer)
                scores.append(round(score, 3))
        if len(members) > 1:
            cluster = _dedupe_cluster("semantic_title", members)
            cluster["similarity_scores"] = scores
            clusters.append(cluster)
    return clusters


def _vector_dedupe_clusters(items: Sequence[RawDedupeCandidate]) -> list[DedupeCluster]:
    clusters: list[DedupeCluster] = []
    used_pairs: set[tuple[int, int]] = set()
    signatures = {
        item.id: metadata_vector_signature(_candidate_metadata_text(item))
        for item in items
        if item.id is not None and _candidate_metadata_text(item)
    }
    for index, item in enumerate(items):
        if item.id is None or item.id not in signatures:
            continue
        members = [item]
        scores: list[float] = []
        for peer in items[index + 1:]:
            if peer.id is None or peer.id not in signatures:
                continue
            low, high = sorted((item.id, peer.id))
            pair = (low, high)
            if pair in used_pairs:
                continue
            score = round(
                sum(
                    left_value * right_value
                    for left_value, right_value in zip(signatures[item.id], signatures[peer.id], strict=True)
                ),
                3,
            )
            if score >= 0.86:
                used_pairs.add(pair)
                members.append(peer)
                scores.append(score)
        if len(members) > 1:
            cluster = _dedupe_cluster("vector_signature", members)
            cluster["similarity_scores"] = scores
            clusters.append(cluster)
    return clusters


def _dedupe_cluster(kind: str, items: Sequence[RawDedupeCandidate]) -> DedupeCluster:
    return {
        "kind": kind,
        "item_ids": [item.id for item in items if item.id is not None],
        "raw_uuids": [item.raw_uuid for item in items],
        "titles": [item.title for item in items],
        "statuses": [item.processing_status for item in items],
        "recommendation": "merge_or_keep_best_metadata",
    }


def _candidate_metadata_text(item: RawDedupeCandidate) -> str:
    return " ".join(part for part in [item.title, item.url] if part)


def _is_operational_dedupe_candidate(item: RawDedupeCandidate) -> bool:
    raw_uuid = item.raw_uuid.lower()
    title = (item.title or "").lower()
    status = item.processing_status.lower()
    url = (item.url or "").lower()
    if "pytest" in raw_uuid or "pytest" in title or "pytest" in url:
        return False
    if raw_uuid.startswith(("raw_dedupe_", "vector-raw-")):
        return False
    if "example.com/vector/" in url or title.startswith("hash duplicate"):
        return False
    if "source_anchor" in raw_uuid or "source_anchor" in status or "浏览冲浪来源锚点" in (item.title or ""):
        return False
    if "结构化采集锚点" in (item.title or ""):
        return False
    if status in {"source_anchor_registered", "test", "pytest"}:
        return False
    return True


def _char_ngrams(text: str) -> set[str]:
    normalized = "".join(char.lower() if char.isalnum() or "\u4e00" <= char <= "\u9fff" else " " for char in text)
    compact = "".join(normalized.split())
    grams: set[str] = set()
    for size in (2, 3):
        for index in range(max(0, len(compact) - size + 1)):
            grams.add(compact[index:index + size])
    return grams


def _safety_event_to_dict(event: SafetyEventSnapshot) -> dict[str, Any]:
    return {
        "id": event.id,
        "task_type": event.task_type,
        "source": event.source,
        "risk_level": event.risk_level,
        "flags": loads_list(event.flags_json),
        "payload_hash": event.payload_hash,
        "payload_preview": event.payload_preview,
        "message": event.message,
        "alternatives": loads_list(event.alternatives_json),
        "blocked": event.blocked,
        "created_at": event.created_at_iso,
    }


def _summary_value(report: Mapping[str, Any], key: str) -> Any:
    summary = _as_mapping(report.get("summary"))
    return summary.get(key)


def _as_mapping(value: Any) -> Mapping[str, Any]:
    return cast(Mapping[str, Any], value) if isinstance(value, Mapping) else {}


def _as_int(value: Any) -> int:
    try:
        return int(value or 0)
    except (TypeError, ValueError):
        return 0


def _as_float(value: Any) -> float:
    try:
        return float(value or 0)
    except (TypeError, ValueError):
        return 0.0
