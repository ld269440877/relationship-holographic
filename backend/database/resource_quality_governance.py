"""Resource quality governance.

The resource ocean should be useful to read, not just large. This module
enriches existing resources with source-level reading guidance, audit-friendly
license notes, quality scores, and exact duplicate cleanup.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import shutil
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any

from sqlmodel import Session, col, func, select

from backend.core.resource_source_catalog import SOURCE_CATALOG
from backend.database.connection import DB_PATH, create_db_and_tables, engine
from backend.models.evolution import PipelineRunLog
from backend.models.resource import ResourceLibrary


@dataclass(frozen=True)
class SourceGuide:
    title: str
    summary: str
    excerpt: str
    license_note: str


CATALOG_BY_URL = {item["url"]: item for item in SOURCE_CATALOG}
CATALOG_BY_NAME = {item["name"]: item for item in SOURCE_CATALOG}

EXPRESSION_TOOL_RULES: tuple[tuple[tuple[str, ...], tuple[str, ...], str, str, str], ...] = (
    (("冲突", "冷战", "降温", "吵", "失望"), ("expr_tool_041", "expr_tool_044", "expr_tool_050"), "降低防御", "承接/降温", "急于解释"),
    (("修复", "道歉", "补偿", "重新约定"), ("expr_tool_041", "expr_tool_029", "expr_tool_047"), "修复信任", "道歉/修复", "求立刻原谅"),
    (("边界", "同意", "拒绝", "退路", "亲密推进"), ("expr_tool_027", "expr_tool_056", "expr_tool_019"), "确认边界", "边界请求", "隐藏命令"),
    (("暧昧", "调情", "轻挑战", "土味", "坏笑"), ("expr_tool_017", "expr_tool_006", "expr_tool_039"), "制造轻张力", "低压调情", "越界推进"),
    (("长期", "异地", "承诺", "价值观", "偏好"), ("expr_tool_023", "expr_tool_059", "expr_tool_060"), "提出请求", "长期协商", "模糊约定"),
    (("初识", "深聊", "话题", "破冰"), ("expr_tool_005", "expr_tool_054", "expr_tool_019"), "引导深聊", "开放提问", "逼问隐私"),
    (("幽默", "玩笑", "段子", "自嘲"), ("expr_tool_016", "expr_tool_017", "expr_tool_019"), "降低防御", "低压幽默", "用玩笑逃避责任"),
    (("错题", "常见失误", "更好回应", "改写"), ("expr_tool_003", "expr_tool_041", "expr_tool_028"), "错题改写", "回应改写", "结构混乱"),
)

MISSION_KEYWORDS = (
    "微关系",
    "对话",
    "回应",
    "情绪流动",
    "情绪",
    "感受",
    "需求",
    "边界",
    "同意",
    "暧昧",
    "亲密",
    "冲突",
    "修复",
    "连接",
    "信任",
    "退路",
    "轻问题",
    "停顿",
    "语气",
    "靠近",
    "后退",
    "错题",
    "训练",
    "练习",
)
OFF_MISSION_KEYWORDS = (
    "公共卫生",
    "人口研究",
    "官方统计",
    "婚育史",
    "家庭成长数据",
    "开放数据",
    "性取向数据",
    "行业数据",
    "用户画像",
    "风险行为",
    "数据可视化",
    "人口结构",
)
LEGACY_HIDDEN_TAG = "legacy_generated_hidden"
LEGACY_SOFT_HIDE_STATUS = "quarantine"
LEGACY_SOFT_HIDE_ACTION = "resource_quality_soft_hide_legacy_generated"
OFF_MISSION_SOFT_HIDE_ACTION = "resource_quality_soft_hide_off_mission"
FAMILY_CAP_SOFT_HIDE_ACTION = "resource_quality_soft_hide_family_over_cap"

LOCAL_GUIDES: dict[str, SourceGuide] = {
    "local_anchor:深度聊天话题库": SourceGuide(
        title="深度聊天话题库",
        summary="本地原创话题库，按事实、感受、边界、期待四层组织，适合把聊天从表层寒暄带到可退出的深聊。",
        excerpt="每个问题都应允许跳过；好的深聊不是逼问，而是让对方更容易选择真实。",
        license_note="project_original",
    ),
    "local_anchor:情绪流动故事库": SourceGuide(
        title="情绪流动故事库",
        summary="本地原创故事库，强调动作、停顿、语气和关系状态变化，用于训练从台词背后读取情绪流。",
        excerpt="故事重点不是制造刺激，而是看见靠近、后退、试探和修复如何在一句话里发生。",
        license_note="project_original",
    ),
    "local_anchor:成人暧昧语言游戏库": SourceGuide(
        title="成人暧昧语言游戏库",
        summary="本地原创成人暧昧训练库，只保留安全、同意、可拒绝的低压幽默和亲密确认练习。",
        excerpt="暧昧的底线是对方随时可以不接；越有张力，越需要清楚退路。",
        license_note="project_original",
    ),
    "local_anchor:从之前到之后对话诊断库": SourceGuide(
        title="从之前到之后对话诊断库",
        summary="本地原创对话诊断库，把关闭连接的旧句子改写为能承接情绪、确认边界、继续流动的新句子。",
        excerpt="先停止指责，再承认情绪，最后只提出一个可回答的小问题。",
        license_note="project_original",
    ),
}


def normalize_text(value: str) -> str:
    collapsed = re.sub(r"\s+", " ", value.strip().lower())
    return collapsed


def content_fingerprint(resource: ResourceLibrary) -> str:
    return "sha256:" + hashlib.sha256(normalize_text(resource.content).encode("utf-8")).hexdigest()


def _clean_source_name(source: str | None) -> str:
    return (source or "").replace("public_anchor:", "").replace("local_anchor:", "").strip()


def _guide_for(resource: ResourceLibrary) -> SourceGuide:
    if resource.source in LOCAL_GUIDES:
        return LOCAL_GUIDES[resource.source or ""]
    catalog = CATALOG_BY_URL.get(resource.source_url or "") or CATALOG_BY_NAME.get(_clean_source_name(resource.source))
    if catalog:
        themes = "、".join(catalog["themes"][:4])
        scenes = "、".join(catalog["scenes"][:4])
        return SourceGuide(
            title=catalog["name"],
            summary=(
                f"{catalog['summary']} 内容结构：{catalog['structure']} "
                f"可用于 {scenes} 等场景，重点主题包括 {themes}。"
            ),
            excerpt=(
                f"导读重点：先到原站阅读完整材料，再把其中的“{catalog['themes'][0]}”"
                "转化为事实、感受、需求、边界和下一句回应。"
            ),
            license_note="metadata_summary_link_only",
        )
    if resource.source_url and resource.source_url.startswith("http"):
        source_name = _clean_source_name(resource.source) or resource.source_url
        return SourceGuide(
            title=source_name,
            summary=(
                f"{source_name} 是资源库登记的公开阅读入口。当前条目保存的是本项目围绕该入口派生的"
                "结构化学习卡、训练转化和阅读路线，不复制第三方全文。"
            ),
            excerpt="导读重点：点击原站阅读完整材料，再回到资源卡练习事实、感受、需求、边界和下一句回应。",
            license_note="metadata_summary_link_only",
        )
    return SourceGuide(
        title=_clean_source_name(resource.source) or "项目资源",
        summary="项目内训练资源，建议结合场景、标签和使用提示阅读；无可靠公开来源时不伪装为权威原文。",
        excerpt="先看情绪流，再看边界和可拒绝空间。",
        license_note="project_or_uncatalogued_source",
    )


def _quality_score(resource: ResourceLibrary, guide: SourceGuide) -> float:
    score = 45.0
    if resource.title:
        score += 6
    if resource.source_url and resource.source_url.startswith("http"):
        score += 14
    if resource.source_summary or guide.summary:
        score += 10
    if resource.source_excerpt or guide.excerpt:
        score += 8
    if resource.tags and len(resource.tags.split(",")) >= 5:
        score += 7
    if len(resource.content) >= 120:
        score += 8
    if resource.review_status == "published":
        score += 5
    if resource.effectiveness_rating:
        score += min(5, float(resource.effectiveness_rating) / 2)
    return round(min(100.0, score), 1)


def expression_annotation(resource: ResourceLibrary) -> dict[str, Any]:
    haystack = " ".join(
        str(value or "")
        for value in (
            resource.title,
            resource.category,
            resource.content,
            resource.usage_tip,
            resource.tags,
            resource.applicable_scene,
        )
    )
    for keywords, tool_ids, goal, speech_act, mistake in EXPRESSION_TOOL_RULES:
        if any(keyword in haystack for keyword in keywords):
            return _expression_annotation_payload(resource, list(tool_ids), goal, speech_act, mistake)
    return _expression_annotation_payload(resource, ["expr_tool_005", "expr_tool_027", "expr_tool_041"], "说清事实", "事实/感受/边界", "抽象表达")


def _expression_annotation_payload(
    resource: ResourceLibrary,
    tool_ids: list[str],
    goal: str,
    speech_act: str,
    mistake: str,
) -> dict[str, Any]:
    level = "D3 改写" if any(marker in str(resource.content) for marker in ("常见失误", "更好回应", "练习任务")) else "D2 套用"
    drills = [
        {"type": "identify", "prompt": "指出这张资源卡最适合练的表达工具。"},
        {"type": "rewrite", "prompt": f"用{goal}目标重写一句回应，并保留可拒绝空间。"},
        {"type": "transfer", "prompt": "换一个相邻场景，用同一工具说一次。"},
    ]
    return {
        "expression_tool_ids_json": json.dumps(tool_ids, ensure_ascii=False),
        "expression_goal": goal,
        "expression_level": level,
        "speech_act": speech_act,
        "mistake_pattern": mistake,
        "recommended_drills_json": json.dumps(drills, ensure_ascii=False),
    }


def mission_alignment_score(resource: ResourceLibrary) -> float:
    haystack = " ".join(
        str(value or "")
        for value in (
            resource.title,
            resource.category,
            resource.content,
            resource.usage_tip,
            resource.tags,
            resource.source_summary,
            resource.source_excerpt,
            resource.applicable_scene,
        )
    )
    score = 35.0
    score += sum(3.0 for keyword in MISSION_KEYWORDS if keyword in haystack)
    score -= sum(8.0 for keyword in OFF_MISSION_KEYWORDS if keyword in haystack)
    if resource.type in {"flirty", "joke", "game", "story", "phrase"}:
        score += 12
    if resource.applicable_scene in {"初识", "暧昧", "热恋", "冲突", "修复", "复联", "异地", "平淡", "承诺", "分歧"}:
        score += 10
    if "公开来源" in str(resource.tags or "") and not any(keyword in haystack for keyword in ("对话", "回应", "训练", "情绪", "边界")):
        score -= 15
    return round(max(0.0, min(100.0, score)), 1)


def has_off_mission_marker(resource: ResourceLibrary) -> bool:
    haystack = " ".join(
        str(value or "")
        for value in (
            resource.title,
            resource.category,
            resource.content,
            resource.usage_tip,
            resource.tags,
            resource.source_summary,
            resource.source_excerpt,
            resource.applicable_scene,
        )
    )
    return any(keyword in haystack for keyword in OFF_MISSION_KEYWORDS)


def enrich_resources(session: Session, dry_run: bool = False) -> int:
    updated = 0
    resources = list(session.exec(select(ResourceLibrary)).all())
    for resource in resources:
        guide = _guide_for(resource)
        fingerprint = content_fingerprint(resource)
        next_values = {
            "source_title": guide.title,
            "source_summary": guide.summary,
            "source_excerpt": guide.excerpt,
            "source_license": guide.license_note,
            "content_fingerprint": fingerprint,
            "quality_score": _quality_score(resource, guide),
        }
        next_values.update(expression_annotation(resource))
        changed = any(getattr(resource, key) != value for key, value in next_values.items())
        if not changed:
            continue
        updated += 1
        if not dry_run:
            for key, value in next_values.items():
                setattr(resource, key, value)
            session.add(resource)
    if not dry_run:
        session.commit()
    return updated


def _keep_key(resource: ResourceLibrary) -> tuple[int, float, int, int]:
    has_public_url = 1 if resource.source_url and resource.source_url.startswith("http") else 0
    status_rank = {"published": 3, "reviewed": 2, "draft": 1}.get(resource.review_status, 0)
    quality = float(resource.quality_score or 0)
    return (has_public_url, quality, status_rank, int(resource.id or 0))


def remove_exact_duplicates(session: Session, dry_run: bool = False) -> dict[str, int]:
    rows = session.exec(
        select(ResourceLibrary.content_fingerprint, func.count(ResourceLibrary.id))
        .where(ResourceLibrary.content_fingerprint.is_not(None))
        .group_by(ResourceLibrary.content_fingerprint)
        .having(func.count(ResourceLibrary.id) > 1)
    ).all()
    clusters = 0
    deleted = 0
    for fingerprint, count in rows:
        if not fingerprint or int(count) <= 1:
            continue
        duplicates = list(
            session.exec(
                select(ResourceLibrary).where(ResourceLibrary.content_fingerprint == fingerprint)
            ).all()
        )
        if len(duplicates) <= 1:
            continue
        clusters += 1
        keep = sorted(duplicates, key=_keep_key, reverse=True)[0]
        for resource in duplicates:
            if resource.id == keep.id:
                continue
            deleted += 1
            if not dry_run:
                session.delete(resource)
    if not dry_run and deleted:
        session.commit()
    return {"duplicate_clusters": clusters, "deleted": deleted}


def soft_hide_legacy_generated_variants(
    session: Session,
    *,
    dry_run: bool = False,
    limit: int | None = None,
    reviewer_id: str = "resource-quality-governance",
) -> dict[str, Any]:
    query = (
        select(ResourceLibrary)
        .where(col(ResourceLibrary.review_status).in_(("reviewed", "published")))
        .where(ResourceLibrary.tags.contains(LEGACY_HIDDEN_TAG))
        .order_by(ResourceLibrary.id)
    )
    resources = list(session.exec(query).all())
    if limit is not None:
        resources = resources[:limit]
    from_status_counts: dict[str, int] = {}
    source_counts: dict[str, int] = {}
    affected_ids: list[int] = []
    now = datetime.now()
    for resource in resources:
        if resource.id is None:
            continue
        from_status = str(resource.review_status or "draft")
        from_status_counts[from_status] = from_status_counts.get(from_status, 0) + 1
        source = str(resource.source or "unknown")
        source_counts[source] = source_counts.get(source, 0) + 1
        affected_ids.append(int(resource.id))
        if dry_run:
            continue
        resource.review_status = LEGACY_SOFT_HIDE_STATUS
        resource.published_at = None
        session.add(resource)
        session.add(
            PipelineRunLog(
                target_type="resource",
                target_id=int(resource.id),
                action=LEGACY_SOFT_HIDE_ACTION,
                from_status=from_status,
                to_status=LEGACY_SOFT_HIDE_STATUS,
                result_json=json.dumps(
                    {
                        "reviewer_id": reviewer_id,
                        "reason": "legacy generated high-similarity variants are hidden from default browsing",
                        "content_deleted": False,
                        "resource_uuid_hash": _sha256(str(resource.resource_uuid or "")),
                        "title_hash": _sha256(str(resource.title or "")),
                        "source": source,
                    },
                    ensure_ascii=False,
                    sort_keys=True,
                ),
                message="旧生成近重复变体已从默认资源海洋隐藏；内容保留用于审计和重写。",
                created_at=now,
            )
        )
    if not dry_run and resources:
        session.commit()
    return {
        "dry_run": dry_run,
        "matched": len(resources),
        "affected": len(affected_ids),
        "from_status_counts": from_status_counts,
        "to_status": LEGACY_SOFT_HIDE_STATUS,
        "top_sources": _top_counts(source_counts, limit=12),
        "sample_ids": affected_ids[:20],
        "safety_flags": {
            "content_deleted": False,
            "default_listing_hides_quarantine": True,
            "raw_content_returned": False,
            "reason_text_hashed": True,
        },
    }


def soft_hide_off_mission_resources(
    session: Session,
    *,
    dry_run: bool = False,
    reviewer_id: str = "resource-quality-governance",
) -> dict[str, Any]:
    visible = list(
        session.exec(
            select(ResourceLibrary)
            .where(col(ResourceLibrary.review_status).in_(("reviewed", "published")))
            .order_by(ResourceLibrary.id)
        ).all()
    )
    resources = [
        resource
        for resource in visible
        if has_off_mission_marker(resource) and mission_alignment_score(resource) < 60
    ]
    source_counts: dict[str, int] = {}
    type_counts: dict[str, int] = {}
    affected_ids: list[int] = []
    now = datetime.now()
    for resource in resources:
        if resource.id is None:
            continue
        source = str(resource.source or "unknown")
        source_counts[source] = source_counts.get(source, 0) + 1
        resource_type = str(resource.type or "unknown")
        type_counts[resource_type] = type_counts.get(resource_type, 0) + 1
        affected_ids.append(int(resource.id))
        if dry_run:
            continue
        before = str(resource.review_status or "draft")
        resource.review_status = LEGACY_SOFT_HIDE_STATUS
        resource.published_at = None
        session.add(resource)
        session.add(
            PipelineRunLog(
                target_type="resource",
                target_id=int(resource.id),
                action=OFF_MISSION_SOFT_HIDE_ACTION,
                from_status=before,
                to_status=LEGACY_SOFT_HIDE_STATUS,
                result_json=json.dumps(
                    {
                        "reviewer_id": reviewer_id,
                        "reason": "off-mission source-transformed resource hidden from default relationship training ocean",
                        "mission_alignment_score": mission_alignment_score(resource),
                        "content_deleted": False,
                        "resource_uuid_hash": _sha256(str(resource.resource_uuid or "")),
                        "title_hash": _sha256(str(resource.title or "")),
                        "source": source,
                    },
                    ensure_ascii=False,
                    sort_keys=True,
                ),
                message="偏离关系训练主线的采集转化卡已从默认资源海洋隐藏；内容保留用于来源审计。",
                created_at=now,
            )
        )
    if not dry_run and resources:
        session.commit()
    return {
        "dry_run": dry_run,
        "matched": len(resources),
        "affected": len(affected_ids),
        "to_status": LEGACY_SOFT_HIDE_STATUS,
        "top_sources": _top_counts(source_counts, limit=12),
        "type_counts": _top_counts(type_counts, limit=8),
        "sample_ids": affected_ids[:20],
        "safety_flags": {
            "content_deleted": False,
            "default_listing_hides_quarantine": True,
            "raw_content_returned": False,
            "reason_text_hashed": True,
        },
    }


def soft_hide_resource_family_over_cap(
    session: Session,
    *,
    cap: int = 24,
    dry_run: bool = False,
    reviewer_id: str = "resource-quality-governance",
) -> dict[str, Any]:
    visible = list(
        session.exec(
            select(ResourceLibrary)
            .where(col(ResourceLibrary.review_status).in_(("reviewed", "published")))
            .order_by(ResourceLibrary.id)
        ).all()
    )
    families: dict[str, list[ResourceLibrary]] = {}
    for resource in visible:
        key = _resource_family_key(resource)
        if key:
            families.setdefault(key, []).append(resource)

    affected_ids: list[int] = []
    affected_families: list[dict[str, Any]] = []
    now = datetime.now()
    for family_key, members in families.items():
        if len(members) <= cap:
            continue
        sorted_members = sorted(members, key=_keep_key, reverse=True)
        hidden_members = sorted_members[cap:]
        affected_families.append({
            "family_key_hash": _sha256(family_key),
            "family_size": len(members),
            "hidden": len(hidden_members),
            "kept": min(len(members), cap),
        })
        for resource in hidden_members:
            if resource.id is None:
                continue
            affected_ids.append(int(resource.id))
            if dry_run:
                continue
            before = str(resource.review_status or "draft")
            resource.review_status = LEGACY_SOFT_HIDE_STATUS
            resource.published_at = None
            resource.tags = _append_tag(resource.tags, "family_over_cap_hidden")
            session.add(resource)
            session.add(
                PipelineRunLog(
                    target_type="resource",
                    target_id=int(resource.id),
                    action=FAMILY_CAP_SOFT_HIDE_ACTION,
                    from_status=before,
                    to_status=LEGACY_SOFT_HIDE_STATUS,
                    result_json=json.dumps(
                        {
                            "reviewer_id": reviewer_id,
                            "family_key_hash": _sha256(family_key),
                            "cap": cap,
                            "content_deleted": False,
                            "resource_uuid_hash": _sha256(str(resource.resource_uuid or "")),
                            "title_hash": _sha256(str(resource.title or "")),
                        },
                        ensure_ascii=False,
                        sort_keys=True,
                    ),
                    message=f"语义家族默认展示超过 {cap} 条的变体已软隐藏；内容保留用于审计和后续重写。",
                    created_at=now,
                )
            )
    if not dry_run and affected_ids:
        session.commit()
    return {
        "dry_run": dry_run,
        "cap": cap,
        "affected_families": len(affected_families),
        "affected": len(affected_ids),
        "sample_ids": affected_ids[:20],
        "top_families": sorted(affected_families, key=lambda item: (-int(item["hidden"]), -int(item["family_size"])))[:12],
        "safety_flags": {
            "content_deleted": False,
            "default_listing_hides_quarantine": True,
            "family_key_hashed": True,
            "raw_content_returned": False,
        },
    }


def resource_quality_report(session: Session) -> dict[str, Any]:
    total = int(session.exec(select(func.count()).select_from(ResourceLibrary)).one())
    distinct = int(session.exec(select(func.count(func.distinct(ResourceLibrary.content_fingerprint)))).one())
    avg_quality = session.exec(select(func.avg(ResourceLibrary.quality_score))).one()
    missing_guidance = int(
        session.exec(
            select(func.count())
            .select_from(ResourceLibrary)
            .where(
                (col(ResourceLibrary.source_summary).is_(None))
                | (col(ResourceLibrary.source_excerpt).is_(None))
                | (col(ResourceLibrary.content_fingerprint).is_(None))
            )
        ).one()
    )
    resources = list(session.exec(select(ResourceLibrary)).all())
    visible_resources = [resource for resource in resources if resource.review_status in {"reviewed", "published"}]
    trainable_visible_resources = [
        resource
        for resource in visible_resources
        if resource.type != "media" and "来源锚点" not in str(resource.title or "")
    ]
    alignment_scores = [mission_alignment_score(resource) for resource in visible_resources]
    off_mission = sum(1 for score in alignment_scores if score < 60)
    practice_scores = [_practice_completeness_score(resource) for resource in trainable_visible_resources]
    family_counts = _family_counts(visible_resources)
    duplicate_families = {key: count for key, count in family_counts.items() if count > 1}
    first_page = sorted(
        visible_resources,
        key=lambda item: (int(item.id or 0) % 47, item.applicable_scene or "", item.type or "", int(item.id or 0)),
    )[:48]
    first_page_runs = _continuous_family_runs(first_page)
    return {
        "total": total,
        "distinct_fingerprints": distinct,
        "exact_duplicate_debt": max(0, total - distinct),
        "avg_quality_score": round(float(avg_quality or 0), 1),
        "missing_guidance": missing_guidance,
        "avg_mission_alignment": round(sum(alignment_scores) / len(alignment_scores), 1) if alignment_scores else 0,
        "off_mission_count": off_mission,
        "perceived_duplicate_debt": {
            "visible_resources": len(visible_resources),
            "duplicate_families": len(duplicate_families),
            "duplicate_family_items": sum(duplicate_families.values()),
            "largest_family_size": max(duplicate_families.values(), default=0),
            "first_page_max_continuous_family_run": max(first_page_runs, default=0),
            "first_page_runs_over_three": sum(1 for count in first_page_runs if count > 3),
        },
        "practice_completeness": {
            "avg_score": round(sum(practice_scores) / len(practice_scores), 1) if practice_scores else 0,
            "complete_cards": sum(1 for score in practice_scores if score >= 80),
            "thin_cards": sum(1 for score in practice_scores if score < 50),
            "trainable_cards": len(trainable_visible_resources),
            "source_anchor_cards_excluded": len(visible_resources) - len(trainable_visible_resources),
            "required_markers": ["场景", "TA说/对方说", "常见失误", "更好回应", "边界/同意", "练习任务"],
        },
        "checked_at": datetime.now().isoformat(timespec="seconds"),
    }


def _family_counts(resources: list[ResourceLibrary]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for resource in resources:
        key = _resource_family_key(resource)
        if not key:
            continue
        counts[key] = counts.get(key, 0) + 1
    return counts


def _resource_family_key(resource: ResourceLibrary) -> str:
    title = str(resource.title or "")
    for separator in ("｜", "|"):
        if separator in title:
            title = title.split(separator, 1)[0]
    title = normalize_text(title).replace("具体故事卡", "").replace("三步训练", "").strip()
    parts = [
        normalize_text(str(resource.applicable_scene or "")),
        normalize_text(str(resource.category or "")),
        title,
    ]
    return "::".join(part for part in parts if part)


def _continuous_family_runs(resources: list[ResourceLibrary]) -> list[int]:
    runs: list[int] = []
    previous = None
    count = 0
    for resource in resources:
        key = _resource_family_key(resource)
        if key == previous:
            count += 1
        else:
            if count:
                runs.append(count)
            previous = key
            count = 1 if key else 0
    if count:
        runs.append(count)
    return runs


def _practice_completeness_score(resource: ResourceLibrary) -> float:
    text = "\n".join([
        str(resource.title or ""),
        str(resource.content or ""),
        str(resource.usage_tip or ""),
        str(resource.tags or ""),
        str(resource.recommended_drills_json or ""),
    ]).lower()
    marker_groups = [
        ("场景",),
        ("ta说", "对方说"),
        ("常见失误", "低质量回应"),
        ("更好回应", "更好做法"),
        ("边界", "同意", "可拒绝"),
        ("练习任务", "推荐练习", "drill"),
    ]
    matched = sum(1 for markers in marker_groups if any(marker in text for marker in markers))
    score = matched / len(marker_groups) * 100
    if len(str(resource.content or "")) < 80:
        score -= 15
    return round(max(0.0, min(100.0, score)), 1)


def run_resource_quality_governance(dry_run: bool = False, delete_duplicates: bool = True) -> dict[str, Any]:
    create_db_and_tables()
    with Session(engine) as session:
        before = resource_quality_report(session)
        enriched = enrich_resources(session, dry_run=dry_run)
        duplicate_result = remove_exact_duplicates(session, dry_run=dry_run) if delete_duplicates else {"duplicate_clusters": 0, "deleted": 0}
        soft_hidden = soft_hide_legacy_generated_variants(session, dry_run=dry_run)
        off_mission_hidden = soft_hide_off_mission_resources(session, dry_run=dry_run)
        family_over_cap_hidden = soft_hide_resource_family_over_cap(session, dry_run=dry_run)
        after = before if dry_run else resource_quality_report(session)
    return {
        "dry_run": dry_run,
        "before": before,
        "enriched": enriched,
        "dedupe": duplicate_result,
        "soft_hidden_legacy_generated": soft_hidden,
        "soft_hidden_off_mission": off_mission_hidden,
        "soft_hidden_family_over_cap": family_over_cap_hidden,
        "after": after,
        "principle": "保存来源链接、导读、短摘录/摘要和训练转化；不把第三方全文复制进数据库。",
    }


def backup_database(db_path: Path = DB_PATH) -> Path:
    backup_dir = db_path.parent / "backups"
    backup_dir.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    backup_path = backup_dir / f"{db_path.stem}-before-resource-quality-governance-{timestamp}{db_path.suffix}"
    shutil.copy2(db_path, backup_path)
    return backup_path


def _sha256(value: str) -> str:
    return "sha256:" + hashlib.sha256(value.encode("utf-8")).hexdigest()


def _append_tag(raw: str | None, tag: str) -> str:
    tags = [item.strip() for item in str(raw or "").split(",") if item.strip()]
    if tag not in tags:
        tags.append(tag)
    return ",".join(tags)


def _top_counts(counts: dict[str, int], *, limit: int) -> list[dict[str, Any]]:
    return [
        {"key": key, "count": count}
        for key, count in sorted(counts.items(), key=lambda item: (-item[1], item[0]))[:limit]
    ]


def main() -> None:
    parser = argparse.ArgumentParser(description="资源海洋质量治理：导读回填、质量评分、精确去重")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--keep-duplicates", action="store_true")
    args = parser.parse_args()
    backup_path = None if args.dry_run else backup_database()
    result = run_resource_quality_governance(dry_run=args.dry_run, delete_duplicates=not args.keep_duplicates)
    result["backup_path"] = str(backup_path) if backup_path else None
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
