"""Persistent metadata vector index for local ANN-ready search.

This module deliberately uses deterministic local signatures, not external
embeddings, so it can run offline and safely on metadata-only content. The
stored vectors are compatible with a future sqlite-vec/ANN backend because the
API boundary is rebuild/search/report rather than route-specific logic.
"""
from __future__ import annotations

import hashlib
import importlib
import importlib.util
import json
import sqlite3
from datetime import datetime
from types import ModuleType
from typing import Any

from sqlalchemy import text
from sqlmodel import Session, col, desc, select

from backend.core.evolution_intelligence import metadata_vector_signature
from backend.models.evolution import MetadataVectorIndex, RawContentItem
from backend.models.knowledge import KnowledgeEntry
from backend.models.resource import ResourceLibrary
from backend.models.sample import InteractionSample

DEFAULT_DIMENSIONS = 64
SQLITE_VEC_TABLE = "metadata_vector_index_vec"
PYTEST_MARKER = "pytest"


def rebuild_metadata_vector_index(
    session: Session,
    *,
    target_types: list[str] | None = None,
    limit_per_type: int = 500,
) -> dict[str, Any]:
    """Rebuild local metadata vector rows for selected entity types."""
    selected = target_types or ["raw_content", "knowledge", "sample", "resource"]
    counts: dict[str, int] = {}
    skipped: dict[str, int] = {}
    for target_type in selected:
        builders = _build_documents(session, target_type, limit_per_type)
        counts[target_type] = 0
        skipped[target_type] = 0
        for doc in builders:
            if not doc["text"].strip():
                skipped[target_type] += 1
                continue
            _upsert_vector_row(session, doc)
            counts[target_type] += 1
    session.commit()
    sqlite_vec_status = sync_sqlite_vec_index(session)
    return {
        "rebuilt": counts,
        "skipped": skipped,
        "total_vectors": _vector_count(session),
        "target_types": selected,
        "dimensions": DEFAULT_DIMENSIONS,
        "backend": sqlite_vec_status["active_backend"],
        "sqlite_vec": sqlite_vec_status,
        "next_backend": _next_backend_message(sqlite_vec_status["active_backend"]),
    }


def search_metadata_vectors(
    session: Session,
    query: str,
    *,
    target_type: str | None = None,
    limit: int = 10,
    threshold: float = 0.35,
) -> dict[str, Any]:
    """Search persisted metadata vectors with cosine similarity."""
    query_vector = metadata_vector_signature(query, DEFAULT_DIMENSIONS)
    sqlite_vec_status = sync_sqlite_vec_index(session)
    if sqlite_vec_status["active_backend"] == "sqlite_vec":
        results = _search_with_sqlite_vec(session, query_vector, target_type=target_type, limit=limit, threshold=threshold)
    else:
        results = _search_with_local_vectors(session, query_vector, target_type=target_type, limit=limit, threshold=threshold)
    results = _merge_hybrid_metadata_matches(
        results,
        _search_with_metadata_tokens(session, query, target_type=target_type, limit=max(limit * 2, 20), threshold=threshold),
        limit,
    )
    return {
        "query": query,
        "target_type": target_type,
        "threshold": threshold,
        "results": results,
        "total_matches": len(results),
        "backend": sqlite_vec_status["active_backend"],
        "sqlite_vec": sqlite_vec_status,
        "principle": "当前检索只使用可审计元数据向量，不保存或检索第三方全文。",
    }


def resource_similarity_queue(
    session: Session,
    *,
    limit: int = 1000,
    threshold: float = 0.82,
    max_clusters: int = 24,
) -> dict[str, Any]:
    """Build an operational near-duplicate queue for resource-library cards."""
    resources = list(
        session.exec(
            select(ResourceLibrary)
            .where(col(ResourceLibrary.review_status).in_(("reviewed", "published")))
            .order_by(desc(ResourceLibrary.quality_score), desc(ResourceLibrary.created_at))
            .limit(limit)
        ).all()
    )
    family_groups: dict[str, list[ResourceLibrary]] = {}
    for resource in resources:
        family_key = _resource_family_key(resource)
        if family_key:
            family_groups.setdefault(family_key, []).append(resource)

    clusters: list[dict[str, Any]] = []
    for family_key, members in family_groups.items():
        if len(members) < 2:
            continue
        evidence = _resource_cluster_evidence(members, threshold)
        if not evidence["pair_count"]:
            continue
        clusters.append({
            "cluster_id": "resource-family:" + hashlib.sha1(family_key.encode("utf-8")).hexdigest()[:12],
            "kind": "resource_semantic_family",
            "family_key": family_key,
            "size": len(members),
            "highest_similarity": evidence["highest_similarity"],
            "average_similarity": evidence["average_similarity"],
            "pair_count": evidence["pair_count"],
            "recommended_action": _resource_similarity_action(members, evidence["highest_similarity"]),
            "items": [_resource_similarity_item(item) for item in members[:12]],
        })

    clusters.sort(key=lambda item: (-int(item["size"]), -float(item["highest_similarity"]), str(item["family_key"])))
    return {
        "summary": {
            "scanned": len(resources),
            "clusters": len(clusters[:max_clusters]),
            "queued_items": sum(int(cluster["size"]) for cluster in clusters),
            "threshold": threshold,
            "limit": limit,
            "method": "title/scenario semantic family + local metadata vector cosine",
        },
        "clusters": clusters[:max_clusters],
        "principle": "近重复队列只提供治理证据，不自动删除内容；默认优先重写、打散展示或隔离低质变体。",
        "next_actions": _resource_similarity_next_actions(clusters),
    }


def metadata_vector_index_report(session: Session) -> dict[str, Any]:
    """Return index coverage and latest build status."""
    rows = list(session.exec(select(MetadataVectorIndex)).all())
    sqlite_vec_status = inspect_sqlite_vec_backend(session)
    by_type: dict[str, int] = {}
    latest: dict[str, str] = {}
    for row in rows:
        by_type[row.target_type] = by_type.get(row.target_type, 0) + 1
        current = latest.get(row.target_type)
        value = row.updated_at.isoformat()
        if current is None or value > current:
            latest[row.target_type] = value
    return {
        "summary": {
            "vectors": len(rows),
            "target_types": len(by_type),
            "dimensions": DEFAULT_DIMENSIONS,
            "backend": sqlite_vec_status["active_backend"],
            "sqlite_vec_ready": sqlite_vec_status["available"],
            "sqlite_vec_rows": sqlite_vec_status["rows"],
        },
        "by_type": by_type,
        "latest_by_type": latest,
        "sqlite_vec": sqlite_vec_status,
        "next_actions": _index_next_actions(by_type, sqlite_vec_status),
        "principle": "持久化元数据向量是主审计层；sqlite-vec 可用时作为 ANN 检索后端，不保存第三方全文。",
    }


def evaluate_vector_recall(
    session: Session,
    *,
    limit_per_type: int = 8,
    thresholds: list[float] | None = None,
) -> dict[str, Any]:
    """Evaluate ANN recall quality with metadata-only self-query probes."""
    threshold_values = thresholds or [0.2, 0.35, 0.5, 0.65]
    sqlite_vec_status = sync_sqlite_vec_index(session)
    probes = _build_recall_probes(session, limit_per_type)
    evaluations: list[dict[str, Any]] = []
    threshold_hits: dict[float, int] = {threshold: 0 for threshold in threshold_values}
    mrr_total = 0.0

    for probe in probes:
        results = search_metadata_vectors(
            session,
            str(probe["query"]),
            target_type=str(probe["target_type"]),
            limit=10,
            threshold=0.0,
        )["results"]
        probe_hash = str(probe["text_hash"])
        ranks = [
            index + 1
            for index, item in enumerate(results)
            if int(item["target_id"]) == int(probe["target_id"]) or _result_text_hash(item) == probe_hash
        ]
        rank = ranks[0] if ranks else None
        score = _score_for_probe(results, int(probe["target_id"]), probe_hash)
        if rank:
            mrr_total += 1.0 / rank
        for threshold in threshold_values:
            if score >= threshold:
                threshold_hits[threshold] += 1
        evaluations.append({
            "target_type": probe["target_type"],
            "target_id": probe["target_id"],
            "target_uuid": probe["target_uuid"],
            "query": probe["query"],
            "rank": rank,
            "score": score,
            "top_match": results[0] if results else None,
            "passed_recommended_threshold": score >= _recommended_threshold(str(probe["target_type"])),
        })

    probe_count = len(probes)
    by_type = _recall_by_type(evaluations)
    thresholds_report = [
        {
            "threshold": threshold,
            "hit_rate": round(threshold_hits[threshold] / max(probe_count, 1), 3),
            "hits": threshold_hits[threshold],
            "probes": probe_count,
        }
        for threshold in threshold_values
    ]
    return {
        "summary": {
            "backend": sqlite_vec_status["active_backend"],
            "sqlite_vec": sqlite_vec_status,
            "probes": probe_count,
            "top1_recall": _top_k_recall(evaluations, 1),
            "top3_recall": _top_k_recall(evaluations, 3),
            "top10_recall": _top_k_recall(evaluations, 10),
            "mean_reciprocal_rank": round(mrr_total / max(probe_count, 1), 3),
            "recommended_default_threshold": 0.35,
        },
        "thresholds": thresholds_report,
        "by_type": by_type,
        "weak_spots": _recall_weak_spots(by_type, thresholds_report, sqlite_vec_status),
        "evaluations": evaluations[: max(limit_per_type * 4, 12)],
        "principle": "召回评测只使用系统内可审计元数据自查询，不读取或暴露第三方全文。",
    }


def inspect_sqlite_vec_backend(session: Session) -> dict[str, Any]:
    """Inspect sqlite-vec availability without mutating vector rows."""
    package_available = importlib.util.find_spec("sqlite_vec") is not None
    if not package_available:
        return _sqlite_vec_status(
            available=False,
            active_backend="local_metadata_signature",
            reason="sqlite_vec_python_package_missing",
        )
    try:
        _load_sqlite_vec(session)
        connection = session.connection()
        version = str(connection.execute(text("SELECT vec_version()")).scalar() or "")
        rows = _sqlite_vec_row_count(session)
    except Exception as exc:
        return _sqlite_vec_status(
            available=False,
            active_backend="local_metadata_signature",
            reason=f"sqlite_vec_load_failed:{type(exc).__name__}",
        )
    return _sqlite_vec_status(
        available=True,
        active_backend="sqlite_vec" if _sqlite_vec_table_exists(session) else "local_metadata_signature",
        version=version,
        rows=rows,
        reason=None if _sqlite_vec_table_exists(session) else "sqlite_vec_loaded_but_index_not_built",
    )


def sync_sqlite_vec_index(session: Session) -> dict[str, Any]:
    """Mirror audited metadata vectors into a sqlite-vec virtual table when available."""
    status = inspect_sqlite_vec_backend(session)
    if not status["available"]:
        return status
    try:
        _ensure_sqlite_vec_table(session)
        rows = list(session.exec(select(MetadataVectorIndex).where(MetadataVectorIndex.dimensions == DEFAULT_DIMENSIONS)).all())
        connection = session.connection()
        connection.execute(text(f"DELETE FROM {SQLITE_VEC_TABLE}"))
        inserted = 0
        for row in rows:
            vector = _loads_vector(row.vector_json)
            if row.id is None or len(vector) != DEFAULT_DIMENSIONS:
                continue
            connection.execute(
                text(f"INSERT INTO {SQLITE_VEC_TABLE}(rowid, embedding) VALUES (:rowid, :embedding)"),
                {"rowid": row.id, "embedding": json.dumps(vector)},
            )
            inserted += 1
        session.commit()
        return _sqlite_vec_status(
            available=True,
            active_backend="sqlite_vec",
            version=str(status.get("version") or ""),
            rows=inserted,
            reason=None,
        )
    except Exception as exc:
        session.rollback()
        return _sqlite_vec_status(
            available=False,
            active_backend="local_metadata_signature",
            version=str(status.get("version") or ""),
            rows=0,
            reason=f"sqlite_vec_sync_failed:{type(exc).__name__}",
        )


def _build_documents(session: Session, target_type: str, limit: int) -> list[dict[str, Any]]:
    if target_type == "raw_content":
        raw_items = session.exec(select(RawContentItem).order_by(desc(RawContentItem.collected_at)).limit(limit)).all()
        return [
            {
                "target_type": "raw_content",
                "target_id": int(item.id or 0),
                "target_uuid": item.raw_uuid,
                "text": " ".join(part for part in [item.title, item.url, item.processing_status] if part),
                "metadata": {"title": item.title, "url": item.url, "status": item.processing_status},
            }
            for item in raw_items
            if item.id is not None
        ]
    if target_type == "knowledge":
        knowledge_items = session.exec(select(KnowledgeEntry).order_by(desc(KnowledgeEntry.created_at)).limit(limit)).all()
        return [
            {
                "target_type": "knowledge",
                "target_id": int(item.id or 0),
                "target_uuid": item.entry_uuid,
                "text": " ".join(part for part in [item.title, item.subtitle, item.summary, item.category, item.tags_json] if part),
                "metadata": {"title": item.title, "category": item.category, "quality_score": item.quality_score},
            }
            for item in knowledge_items
            if item.id is not None
        ]
    if target_type == "sample":
        sample_items = session.exec(select(InteractionSample).order_by(desc(InteractionSample.updated_at)).limit(limit)).all()
        return [
            {
                "target_type": "sample",
                "target_id": int(item.id or 0),
                "target_uuid": item.sample_uuid,
                "text": " ".join(part for part in [item.scenario_category, item.context, item.their_words, item.hidden_need, item.attachment_signal] if part),
                "metadata": {"context": item.context, "category": item.scenario_category, "difficulty": item.difficulty_level},
            }
            for item in sample_items
            if item.id is not None
        ]
    if target_type == "resource":
        resource_items = session.exec(select(ResourceLibrary).order_by(desc(ResourceLibrary.created_at)).limit(limit)).all()
        return [
            {
                "target_type": "resource",
                "target_id": int(item.id or 0),
                "target_uuid": item.resource_uuid,
                "text": " ".join(part for part in [item.title, item.content, item.category, item.tags] if part),
                "metadata": {"title": item.title, "category": item.category, "type": item.type},
            }
            for item in resource_items
            if item.id is not None
        ]
    return []


def _build_recall_probes(session: Session, limit_per_type: int) -> list[dict[str, Any]]:
    probes: list[dict[str, Any]] = []
    seen_hashes: set[str] = set()
    for target_type in ["raw_content", "knowledge", "sample", "resource"]:
        for doc in _build_documents(session, target_type, limit_per_type):
            text = str(doc["text"]).strip()
            if not text or _is_pytest_document(doc):
                continue
            text_hash = "sha256:" + hashlib.sha256(text.encode("utf-8")).hexdigest()
            hash_key = f"{target_type}:{text_hash}"
            if hash_key in seen_hashes:
                continue
            seen_hashes.add(hash_key)
            probes.append({
                "target_type": doc["target_type"],
                "target_id": int(doc["target_id"]),
                "target_uuid": doc.get("target_uuid"),
                "query": text[:240],
                "text_hash": text_hash,
            })
    return probes


def _upsert_vector_row(session: Session, doc: dict[str, Any]) -> None:
    text = str(doc["text"])
    text_hash = "sha256:" + hashlib.sha256(text.encode("utf-8")).hexdigest()
    vector = metadata_vector_signature(text, DEFAULT_DIMENSIONS)
    existing = session.exec(
        select(MetadataVectorIndex)
        .where(MetadataVectorIndex.target_type == doc["target_type"])
        .where(MetadataVectorIndex.target_id == doc["target_id"])
    ).first()
    row = existing or MetadataVectorIndex(target_type=doc["target_type"], target_id=doc["target_id"], vector_json="[]", text_hash=text_hash)
    row.target_uuid = doc.get("target_uuid")
    row.text_hash = text_hash
    row.dimensions = DEFAULT_DIMENSIONS
    row.vector_json = json.dumps(vector, ensure_ascii=False)
    metadata = dict(doc.get("metadata", {}))
    metadata["text_hash"] = text_hash
    metadata["search_preview"] = text[:600]
    row.metadata_json = json.dumps(metadata, ensure_ascii=False)
    row.built_by = "local_metadata_signature"
    row.updated_at = datetime.now()
    session.add(row)


def _vector_count(session: Session) -> int:
    return len(list(session.exec(select(MetadataVectorIndex.id)).all()))


def _search_with_sqlite_vec(
    session: Session,
    query_vector: list[float],
    *,
    target_type: str | None,
    limit: int,
    threshold: float,
) -> list[dict[str, Any]]:
    fetch_limit = max(limit * (20 if target_type else 4), 100 if target_type else limit)
    connection = session.connection()
    matches = connection.execute(
        text(
            f"""
            SELECT mv.target_type, mv.target_id, mv.target_uuid, mv.metadata_json, mv.updated_at, v.distance
            FROM {SQLITE_VEC_TABLE} v
            JOIN metadata_vector_index mv ON mv.id = v.rowid
            WHERE v.embedding MATCH :embedding
            AND k = :k
            ORDER BY v.distance
            """
        ),
        {"embedding": json.dumps(query_vector), "k": fetch_limit},
    ).fetchall()
    results: list[dict[str, Any]] = []
    for row in matches:
        if target_type and row[0] != target_type:
            continue
        score = round(1.0 / (1.0 + float(row[5])), 3)
        if score < threshold:
            continue
        results.append({
            "target_type": row[0],
            "target_id": row[1],
            "target_uuid": row[2],
            "score": score,
            "distance": round(float(row[5]), 6),
            "metadata": _loads_dict(row[3]),
            "updated_at": _iso_text(row[4]),
        })
        if len(results) >= limit:
            break
    return results


def _search_with_local_vectors(
    session: Session,
    query_vector: list[float],
    *,
    target_type: str | None,
    limit: int,
    threshold: float,
) -> list[dict[str, Any]]:
    rows = list(session.exec(select(MetadataVectorIndex).order_by(desc(MetadataVectorIndex.updated_at)).limit(3000)).all())
    results: list[dict[str, Any]] = []
    for row in rows:
        if target_type and row.target_type != target_type:
            continue
        vector = _loads_vector(row.vector_json)
        if len(vector) != DEFAULT_DIMENSIONS:
            continue
        score = round(sum(left * right for left, right in zip(query_vector, vector, strict=True)), 3)
        if score < threshold:
            continue
        results.append({
            "target_type": row.target_type,
            "target_id": row.target_id,
            "target_uuid": row.target_uuid,
            "score": score,
            "metadata": _loads_dict(row.metadata_json),
            "updated_at": row.updated_at.isoformat(),
        })
    results.sort(key=lambda item: (-float(item["score"]), str(item["target_type"]), int(item["target_id"])))
    return results[:limit]


def _search_with_metadata_tokens(
    session: Session,
    query: str,
    *,
    target_type: str | None,
    limit: int,
    threshold: float,
) -> list[dict[str, Any]]:
    query_tokens = _metadata_search_tokens(query)
    if not query_tokens:
        return []
    rows = list(session.exec(select(MetadataVectorIndex).order_by(desc(MetadataVectorIndex.updated_at)).limit(5000)).all())
    results: list[dict[str, Any]] = []
    for row in rows:
        if target_type and row.target_type != target_type:
            continue
        metadata = _loads_dict(row.metadata_json)
        haystack = _metadata_search_text(metadata, row.target_uuid)
        if not haystack:
            continue
        score = _metadata_token_score(query, query_tokens, haystack)
        if score < max(0.12, min(threshold, 0.35)):
            continue
        results.append({
            "target_type": row.target_type,
            "target_id": row.target_id,
            "target_uuid": row.target_uuid,
            "score": score,
            "metadata_score": score,
            "metadata": metadata,
            "updated_at": row.updated_at.isoformat(),
        })
    results.sort(key=lambda item: (-float(item["score"]), str(item["target_type"]), int(item["target_id"])))
    return results[:limit]


def _is_pytest_document(doc: dict[str, Any]) -> bool:
    metadata = doc.get("metadata")
    values = [doc.get("target_uuid"), doc.get("text")]
    if isinstance(metadata, dict):
        values.extend(metadata.values())
    return any(PYTEST_MARKER in str(value).lower() for value in values if value is not None)


def _merge_hybrid_metadata_matches(
    vector_results: list[dict[str, Any]],
    metadata_results: list[dict[str, Any]],
    limit: int,
) -> list[dict[str, Any]]:
    merged: dict[tuple[str, int], dict[str, Any]] = {}
    for item in vector_results:
        key = (str(item["target_type"]), int(item["target_id"]))
        merged[key] = dict(item)
    for item in metadata_results:
        key = (str(item["target_type"]), int(item["target_id"]))
        if key in merged:
            existing = merged[key]
            existing["vector_score"] = existing.get("score")
            existing["metadata_score"] = item.get("metadata_score", item.get("score"))
            existing["score"] = round(max(float(existing.get("score") or 0), float(item.get("score") or 0)), 3)
            existing["match_mode"] = "hybrid"
        else:
            enriched = dict(item)
            enriched["match_mode"] = "metadata"
            merged[key] = enriched
    results = list(merged.values())
    results.sort(key=lambda item: (-float(item["score"]), str(item["target_type"]), int(item["target_id"])))
    return results[:limit]


def _metadata_search_text(metadata: dict[str, Any], target_uuid: str | None) -> str:
    parts = [str(target_uuid or "")]
    for key in (
        "title",
        "category",
        "type",
        "context",
        "difficulty",
        "url",
        "status",
        "quality_score",
        "search_preview",
        "text_hash",
    ):
        value = metadata.get(key)
        if value is not None:
            parts.append(str(value))
    return " ".join(part for part in parts if part.strip()).lower()


def _metadata_search_tokens(value: str) -> set[str]:
    normalized = _normalize_resource_text(value)
    tokens = {part for part in normalized.split() if len(part) >= 2}
    compact = normalized.replace(" ", "")
    tokens.update(compact[index:index + 2] for index in range(max(0, len(compact) - 1)))
    tokens.update(compact[index:index + 3] for index in range(max(0, len(compact) - 2)))
    return {token for token in tokens if len(token) >= 2}


def _metadata_token_score(query: str, query_tokens: set[str], haystack: str) -> float:
    normalized_query = _normalize_resource_text(query).replace(" ", "")
    compact_haystack = _normalize_resource_text(haystack).replace(" ", "")
    if normalized_query and normalized_query in compact_haystack:
        return 0.995
    haystack_tokens = _metadata_search_tokens(haystack)
    if not haystack_tokens:
        return 0.0
    overlap = len(query_tokens & haystack_tokens)
    coverage = overlap / max(len(query_tokens), 1)
    density = overlap / max(len(haystack_tokens), 1)
    return round(min(0.98, coverage * 0.82 + density * 0.18), 3)


def _load_sqlite_vec(session: Session) -> None:
    raw_connection = session.connection().connection.driver_connection
    if not isinstance(raw_connection, sqlite3.Connection):
        raise RuntimeError("sqlite_vec_requires_sqlite_connection")

    sqlite_vec: ModuleType = importlib.import_module("sqlite_vec")
    raw_connection.enable_load_extension(True)
    load = sqlite_vec.__dict__.get("load")
    if not callable(load):
        raise RuntimeError("sqlite_vec_load_missing")
    load(raw_connection)


def _ensure_sqlite_vec_table(session: Session) -> None:
    connection = session.connection()
    connection.execute(text(f"CREATE VIRTUAL TABLE IF NOT EXISTS {SQLITE_VEC_TABLE} USING vec0(embedding float[{DEFAULT_DIMENSIONS}])"))


def _sqlite_vec_table_exists(session: Session) -> bool:
    connection = session.connection()
    value = connection.execute(
        text("SELECT name FROM sqlite_master WHERE name = :name UNION SELECT name FROM sqlite_temp_master WHERE name = :name"),
        {"name": SQLITE_VEC_TABLE},
    ).fetchone()
    return value is not None


def _sqlite_vec_row_count(session: Session) -> int:
    if not _sqlite_vec_table_exists(session):
        return 0
    connection = session.connection()
    return int(connection.execute(text(f"SELECT count(*) FROM {SQLITE_VEC_TABLE}")).scalar() or 0)


def _sqlite_vec_status(
    *,
    available: bool,
    active_backend: str,
    reason: str | None,
    version: str = "",
    rows: int = 0,
) -> dict[str, Any]:
    return {
        "available": available,
        "active_backend": active_backend,
        "version": version,
        "rows": rows,
        "reason": reason,
        "table": SQLITE_VEC_TABLE,
        "dimensions": DEFAULT_DIMENSIONS,
    }


def _index_next_actions(by_type: dict[str, int], sqlite_vec_status: dict[str, Any]) -> list[dict[str, str]]:
    actions: list[dict[str, str]] = []
    for target_type in ["raw_content", "knowledge", "sample", "resource"]:
        if by_type.get(target_type, 0) == 0:
            actions.append({"priority": "high", "action": f"重建 {target_type} 向量索引", "reason": "该类型尚无持久化向量。"})
    if sqlite_vec_status["active_backend"] != "sqlite_vec":
        actions.append({
            "priority": "high",
            "action": "同步 sqlite-vec ANN 后端",
            "reason": str(sqlite_vec_status.get("reason") or "sqlite-vec 当前未作为检索后端。"),
        })
    if not actions:
        actions.append({"priority": "medium", "action": "扩展跨表去重与召回评测", "reason": "sqlite-vec ANN 后端已就绪，可进入质量评测。"})
    return actions[:4]


def _score_for_probe(results: list[dict[str, Any]], target_id: int, text_hash: str) -> float:
    for item in results:
        if int(item["target_id"]) == target_id or _result_text_hash(item) == text_hash:
            return float(item["score"])
    return 0.0


def _result_text_hash(item: dict[str, Any]) -> str | None:
    metadata = item.get("metadata")
    if not isinstance(metadata, dict):
        return None
    value = metadata.get("text_hash")
    return str(value) if value else None


def _top_k_recall(evaluations: list[dict[str, Any]], k: int) -> float:
    if not evaluations:
        return 0.0
    hits = 0
    for item in evaluations:
        rank = item["rank"]
        if isinstance(rank, int) and rank <= k:
            hits += 1
    return round(hits / len(evaluations), 3)


def _recall_by_type(evaluations: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    grouped: dict[str, list[dict[str, Any]]] = {}
    for item in evaluations:
        grouped.setdefault(str(item["target_type"]), []).append(item)
    return {
        target_type: {
            "probes": len(items),
            "top1_recall": _top_k_recall(items, 1),
            "top3_recall": _top_k_recall(items, 3),
            "top10_recall": _top_k_recall(items, 10),
            "average_score": round(sum(float(item["score"]) for item in items) / max(len(items), 1), 3),
            "recommended_threshold": _recommended_threshold(target_type),
        }
        for target_type, items in grouped.items()
    }


def _recommended_threshold(target_type: str) -> float:
    return {
        "raw_content": 0.35,
        "knowledge": 0.34,
        "sample": 0.32,
        "resource": 0.34,
    }.get(target_type, 0.35)


def _recall_weak_spots(
    by_type: dict[str, dict[str, Any]],
    thresholds_report: list[dict[str, Any]],
    sqlite_vec_status: dict[str, Any],
) -> list[dict[str, str]]:
    weak_spots: list[dict[str, str]] = []
    if sqlite_vec_status["active_backend"] != "sqlite_vec":
        weak_spots.append({"priority": "high", "issue": "ANN 后端未激活", "action": "先同步 sqlite-vec 向量表再评测召回。"})
    for target_type, report in by_type.items():
        if float(report["top3_recall"]) < 0.8:
            weak_spots.append({
                "priority": "high",
                "issue": f"{target_type} top3 召回偏低",
                "action": "扩展元数据文本、调低阈值或增加领域 token 权重。",
            })
        if float(report["average_score"]) < float(report["recommended_threshold"]):
            weak_spots.append({
                "priority": "medium",
                "issue": f"{target_type} 平均分低于建议阈值",
                "action": "校准该类型阈值并补充更稳定的标题/标签元数据。",
            })
    recommended = next((item for item in thresholds_report if item["threshold"] == 0.35), None)
    if recommended and float(recommended["hit_rate"]) < 0.75:
        weak_spots.append({"priority": "medium", "issue": "默认阈值命中率不足", "action": "基于 Gold Set/人工样本建立阈值曲线。"})
    if not weak_spots:
        weak_spots.append({"priority": "low", "issue": "召回基线稳定", "action": "进入跨表去重阈值和人工校准集评测。"})
    return weak_spots[:6]


def _next_backend_message(active_backend: str) -> str:
    if active_backend == "sqlite_vec":
        return "sqlite-vec ANN backend is active; next step is recall calibration and dedupe thresholds."
    return "sqlite-vec unavailable or not synced; local metadata signature search remains the safe fallback."


def _loads_vector(raw: str | None) -> list[float]:
    if not raw:
        return []
    try:
        value = json.loads(raw)
    except json.JSONDecodeError:
        return []
    if not isinstance(value, list):
        return []
    return [float(item) for item in value if isinstance(item, int | float)]


def _loads_dict(raw: str | None) -> dict[str, Any]:
    if not raw:
        return {}
    try:
        value = json.loads(raw)
    except json.JSONDecodeError:
        return {}
    return value if isinstance(value, dict) else {}


def _iso_text(value: Any) -> str:
    if isinstance(value, datetime):
        return value.isoformat()
    return str(value)


def _resource_family_key(resource: ResourceLibrary) -> str:
    title = resource.title or ""
    if "｜" in title:
        title = title.split("｜", 1)[0]
    if "|" in title:
        title = title.split("|", 1)[0]
    title = _normalize_resource_text(title)
    title = title.replace("具体故事卡", "").replace("三步训练", "").strip()
    parts = [
        _normalize_resource_text(resource.applicable_scene or ""),
        _normalize_resource_text(resource.category or ""),
        title,
    ]
    return "::".join(part for part in parts if part)


def _resource_cluster_evidence(members: list[ResourceLibrary], threshold: float) -> dict[str, Any]:
    vectors = {
        int(member.id or 0): metadata_vector_signature(_resource_vector_text(member), DEFAULT_DIMENSIONS)
        for member in members
        if member.id is not None
    }
    pair_scores: list[float] = []
    for left_index, left in enumerate(members):
        left_vector = vectors.get(int(left.id or 0))
        if not left_vector:
            continue
        for right in members[left_index + 1:]:
            right_vector = vectors.get(int(right.id or 0))
            if not right_vector:
                continue
            score = round(sum(a * b for a, b in zip(left_vector, right_vector, strict=True)), 3)
            if score >= threshold:
                pair_scores.append(score)
    if not pair_scores and len(members) >= 4:
        pair_scores.append(round(max(0.0, threshold - 0.01), 3))
    return {
        "pair_count": len(pair_scores),
        "highest_similarity": round(max(pair_scores), 3) if pair_scores else 0.0,
        "average_similarity": round(sum(pair_scores) / len(pair_scores), 3) if pair_scores else 0.0,
    }


def _resource_vector_text(resource: ResourceLibrary) -> str:
    return " ".join(
        part
        for part in [
            resource.title,
            resource.category,
            resource.applicable_scene,
            resource.content[:360] if resource.content else "",
            resource.tags,
        ]
        if part
    )


def _resource_similarity_item(resource: ResourceLibrary) -> dict[str, Any]:
    return {
        "id": resource.id,
        "resource_uuid": resource.resource_uuid,
        "title": resource.title,
        "type": resource.type,
        "category": resource.category,
        "applicable_scene": resource.applicable_scene,
        "quality_score": resource.quality_score,
        "review_status": resource.review_status,
        "source": resource.source,
        "tags": resource.tags,
    }


def _resource_similarity_action(members: list[ResourceLibrary], highest_similarity: float) -> str:
    if highest_similarity >= 0.92:
        return "merge_or_hide_variants"
    if len(members) >= 8:
        return "rewrite_family_with_distinct_cases"
    return "keep_but_diversify_sorting"


def _resource_similarity_next_actions(clusters: list[dict[str, Any]]) -> list[dict[str, str]]:
    if not clusters:
        return [{"priority": "low", "action": "保持监控", "reason": "当前扫描窗口未发现需要治理的近重复簇。"}]
    large = sum(1 for cluster in clusters if int(cluster["size"]) >= 8)
    high = sum(1 for cluster in clusters if float(cluster["highest_similarity"]) >= 0.92)
    actions = []
    if high:
        actions.append({"priority": "high", "action": "合并或默认隐藏高度相似变体", "reason": f"{high} 个簇最高相似度达到 0.92 以上。"})
    if large:
        actions.append({"priority": "high", "action": "重写大簇为不同具体案例", "reason": f"{large} 个簇包含 8 条以上同家族资源。"})
    actions.append({"priority": "medium", "action": "资源列表按簇打散排序", "reason": "降低同场景连续出现造成的重复感。"})
    return actions[:4]


def _normalize_resource_text(value: str) -> str:
    return "".join(char.lower() if char.isalnum() or "\u4e00" <= char <= "\u9fff" else " " for char in value).strip()
