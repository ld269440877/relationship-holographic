"""
资源库API路由
"""
import hashlib
import json
from datetime import datetime
from typing import Any

import httpx
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy import or_, text
from sqlalchemy.sql.elements import ColumnElement
from sqlmodel import Session, col, func, select

from backend.core.resource_source_catalog import SOURCE_CATALOG
from backend.core.vector_index import resource_similarity_queue
from backend.database.connection import get_session
from backend.database.resource_quality_governance import resource_quality_report
from backend.models.evolution import PipelineRunLog
from backend.models.resource import ResourceLibrary

router = APIRouter(prefix="/api/resources", tags=["资源"])

MISSION_AXIS_FILTERS: dict[str, tuple[str, ...]] = {
    "micro_signal": ("微关系信号", "微动作", "信号", "停顿", "语气", "间接信号", "原子信号"),
    "emotion_flow": ("情绪流动", "情绪流", "情绪信号", "感受", "失望", "委屈", "正向情绪"),
    "boundary_consent": ("边界与同意", "边界", "同意", "可拒绝", "退路", "亲密节奏", "即时止损"),
    "flirty_tension": ("暧昧张力", "暧昧", "调情", "轻挑战", "土味情话", "双关幽默", "成人暧昧"),
    "conflict_repair": ("冲突修复", "冲突", "修复", "冷战修复", "失望修复", "可靠行动", "道歉"),
    "long_connection": ("长期连接", "长期", "承诺", "异地", "偏好校准", "价值观", "共同约定"),
    "humor_interaction": ("幽默互动", "幽默", "低压幽默", "轻调侃", "笑点", "玩笑", "自嘲"),
    "mistake_rewrite": ("错题改写", "常见失误", "更好回应", "三步训练", "改写", "练习任务", "之前到之后"),
    "self_disclosure_depth": ("自我表露深度", "表露深度", "脆弱层", "存在层", "交浅言深"),
    "relationship_need_calibration": ("关系需求校准", "情绪价值", "安全感", "归属感", "价值认同", "能力感", "认同位置", "性别刻板印象去偏"),
}

VERIFIED_SOURCE_URLS = {
    item["url"]
    for item in SOURCE_CATALOG
    if "周期检查" not in item["quality_notes"] and "需周期检查" not in item["quality_notes"]
}

EXACT_MISSION_AXES = {"relationship_need_calibration", "self_disclosure_depth"}


class ResourceSimilarityActionRequest(BaseModel):
    resource_ids: list[int] = Field(default_factory=list, min_length=1, max_length=200)
    action: str = Field(pattern="^(quarantine_variants|request_review|restore_reviewed)$")
    reviewer_id: str = Field(min_length=2, max_length=80)
    reason: str = Field(min_length=8, max_length=500)
    dry_run: bool = True


class ResourceSimilarityRewriteRequest(BaseModel):
    resource_ids: list[int] = Field(default_factory=list, min_length=1, max_length=80)
    reviewer_id: str = Field(min_length=2, max_length=80)
    reason: str = Field(min_length=8, max_length=500)
    dry_run: bool = True
    mark_originals_quarantine: bool = True


class SourceLinkHealthCheckRequest(BaseModel):
    source_urls: list[str] = Field(default_factory=list, max_length=40)
    limit: int = Field(default=40, ge=1, le=200)
    timeout_seconds: float = Field(default=4.0, ge=1.0, le=10.0)
    dry_run: bool = True


def _source_link_status(source_url: str) -> str:
    if source_url in VERIFIED_SOURCE_URLS:
        return "verified_anchor"
    if source_url.startswith("https://"):
        return "registered_https"
    if source_url.startswith("http://"):
        return "registered_http"
    return "unknown"


def check_source_link_health(source_url: str, timeout_seconds: float = 4.0) -> dict[str, Any]:
    """Check link metadata only; never stores or returns page body."""
    checked_at = datetime.now().isoformat()
    request_url = source_url.strip()
    if not request_url.startswith(("http://", "https://")):
        return {
            "source_url": request_url,
            "status": "invalid",
            "http_code": None,
            "redirect_url": None,
            "redirected": False,
            "last_checked_at": checked_at,
            "error_type": "unsupported_scheme",
        }
    try:
        with httpx.Client(follow_redirects=True, timeout=timeout_seconds) as client:
            response = client.head(request_url)
            if response.status_code in {403, 405}:
                response = client.get(request_url)
        final_url = str(response.url)
        status = "ok" if response.status_code < 400 else "invalid"
        return {
            "source_url": request_url,
            "status": status,
            "http_code": response.status_code,
            "redirect_url": final_url if final_url != request_url else None,
            "redirected": final_url != request_url,
            "last_checked_at": checked_at,
            "error_type": None,
        }
    except httpx.TimeoutException:
        error_type = "timeout"
    except httpx.HTTPError:
        error_type = "http_error"
    return {
        "source_url": request_url,
        "status": "unknown",
        "http_code": None,
        "redirect_url": None,
        "redirected": False,
        "last_checked_at": checked_at,
        "error_type": error_type,
    }


@router.get("")
def get_resources(
    type: str | None = None,
    resource_type: str | None = None,
    category: str | None = None,
    applicable_scene: str | None = None,
    mission_axis: str | None = None,
    q: str | None = None,
    tag: str | None = None,
    source: str | None = None,
    expression_tool: str | None = None,
    expression_goal: str | None = None,
    include_low_quality: bool = False,
    page: int = Query(default=1, ge=1),
    limit: int = Query(default=100, le=1000),
    offset: int = Query(default=0, ge=0),
    session: Session = Depends(get_session)
) -> dict:
    """获取资源列表"""
    effective_type = type or resource_type
    query = select(ResourceLibrary)
    count_query = select(func.count()).select_from(ResourceLibrary)

    query, count_query = _apply_exact_resource_filters(
        query,
        count_query,
        resource_type=effective_type,
        category=category,
        applicable_scene=applicable_scene,
    )
    query, count_query = _apply_mission_axis_filter(query, count_query, mission_axis)
    if q:
        query, count_query = _apply_filter(query, count_query, _keyword_filter(q))
    if tag:
        tag_keyword = f"%{tag.strip()}%"
        query = query.where(col(ResourceLibrary.tags).like(tag_keyword))
        count_query = count_query.where(col(ResourceLibrary.tags).like(tag_keyword))
    if source:
        source_keyword = f"%{source.strip()}%"
        query = query.where(or_(
            col(ResourceLibrary.source).like(source_keyword),
            col(ResourceLibrary.source_url).like(source_keyword),
        ))
        count_query = count_query.where(or_(
            col(ResourceLibrary.source).like(source_keyword),
            col(ResourceLibrary.source_url).like(source_keyword),
        ))
    if expression_tool:
        tool_terms = _expression_tool_filter_terms(expression_tool, session)
        tool_filters = [
            col(ResourceLibrary.expression_tool_ids_json).like(f"%{term}%")
            for term in tool_terms
        ]
        if tool_filters:
            query = query.where(or_(*tool_filters))
            count_query = count_query.where(or_(*tool_filters))
    if expression_goal:
        goal_keyword = f"%{expression_goal.strip()}%"
        query = query.where(col(ResourceLibrary.expression_goal).like(goal_keyword))
        count_query = count_query.where(col(ResourceLibrary.expression_goal).like(goal_keyword))

    visible_statuses = ("reviewed", "published")
    query = query.where(ResourceLibrary.review_status.in_(visible_statuses))
    count_query = count_query.where(ResourceLibrary.review_status.in_(visible_statuses))
    query, count_query = _exclude_non_user_resource_sources(query, count_query)
    if not include_low_quality:
        query, count_query = _apply_default_case_quality_gate(query, count_query)
    effective_offset = offset if offset > 0 else (page - 1) * limit
    if effective_type or category or applicable_scene or mission_axis or q or tag or source or expression_tool or expression_goal:
        query = query.order_by(
            ResourceLibrary.id % 47,
            ResourceLibrary.applicable_scene,
            ResourceLibrary.type,
            ResourceLibrary.id,
        )
    else:
        query = query.where(col(ResourceLibrary.tags).like("%具体案例%"))
        count_query = count_query.where(col(ResourceLibrary.tags).like("%具体案例%"))
        query = query.order_by(
            ResourceLibrary.id % 47,
            ResourceLibrary.applicable_scene,
            ResourceLibrary.type,
            ResourceLibrary.id,
        )
    query = query.offset(effective_offset).limit(limit)
    results = session.exec(query).all()
    total = session.exec(count_query).one()
    return {"items": list(results), "total": total, "page": page, "limit": limit, "offset": effective_offset}


def _exclude_non_user_resource_sources(query: Any, count_query: Any) -> tuple[Any, Any]:
    for condition in _non_user_resource_exclusion_conditions():
        query = query.where(condition)
        count_query = count_query.where(condition)
    return query, count_query


def _apply_default_case_quality_gate(query: Any, count_query: Any) -> tuple[Any, Any]:
    condition = or_(
        ResourceLibrary.case_completeness_score.is_(None),
        ResourceLibrary.case_completeness_score >= 85,
        ~col(ResourceLibrary.tags).like("%具体案例%"),
    )
    return query.where(condition), count_query.where(condition)


def _non_user_resource_exclusion_conditions() -> tuple[ColumnElement[bool], ...]:
    return (
        or_(ResourceLibrary.resource_uuid.is_(None), ~col(ResourceLibrary.resource_uuid).like("pytest%")),
        or_(ResourceLibrary.resource_uuid.is_(None), ~col(ResourceLibrary.resource_uuid).like("%pytest%")),
        or_(ResourceLibrary.source.is_(None), ~col(ResourceLibrary.source).like("pytest%")),
        or_(ResourceLibrary.source.is_(None), ~col(ResourceLibrary.source).like("%pytest%")),
        or_(ResourceLibrary.source_url.is_(None), ~col(ResourceLibrary.source_url).like("pytest%")),
        or_(ResourceLibrary.source_url.is_(None), ~col(ResourceLibrary.source_url).like("%pytest%")),
    )


def _apply_filter(query: Any, count_query: Any, condition: ColumnElement[bool]) -> tuple[Any, Any]:
    return query.where(condition), count_query.where(condition)


def _apply_exact_resource_filters(
    query: Any,
    count_query: Any,
    *,
    resource_type: str | None,
    category: str | None,
    applicable_scene: str | None,
) -> tuple[Any, Any]:
    if resource_type:
        query = query.where(ResourceLibrary.type == resource_type)
        count_query = count_query.where(ResourceLibrary.type == resource_type)
    if category:
        query = query.where(ResourceLibrary.category == category)
        count_query = count_query.where(ResourceLibrary.category == category)
    if applicable_scene:
        query = query.where(ResourceLibrary.applicable_scene == applicable_scene)
        count_query = count_query.where(ResourceLibrary.applicable_scene == applicable_scene)
    return query, count_query


def _keyword_filter(value: str) -> ColumnElement[bool]:
    keyword = f"%{value.strip()}%"
    return or_(
        col(ResourceLibrary.title).like(keyword),
        col(ResourceLibrary.content).like(keyword),
        col(ResourceLibrary.usage_tip).like(keyword),
        col(ResourceLibrary.tags).like(keyword),
        col(ResourceLibrary.source).like(keyword),
    )


def _apply_mission_axis_filter(
    query: Any,
    count_query: Any,
    mission_axis: str | None,
) -> tuple[Any, Any]:
    if not mission_axis:
        return query, count_query
    if mission_axis in EXACT_MISSION_AXES:
        return _apply_filter(query, count_query, col(ResourceLibrary.coverage_axis) == mission_axis)
    axis_terms = MISSION_AXIS_FILTERS.get(mission_axis, (mission_axis.strip(),))
    axis_filters = [col(ResourceLibrary.coverage_axis) == mission_axis]
    axis_filters.extend(
        col(ResourceLibrary.title).like(f"%{term}%")
        | col(ResourceLibrary.content).like(f"%{term}%")
        | col(ResourceLibrary.usage_tip).like(f"%{term}%")
        | col(ResourceLibrary.tags).like(f"%{term}%")
        | col(ResourceLibrary.category).like(f"%{term}%")
        for term in axis_terms
        if term
    )
    if not axis_filters:
        return query, count_query
    return _apply_filter(query, count_query, or_(*axis_filters))


def _resource_similarity_target_status(action: str, from_status: str) -> str:
    if action == "quarantine_variants":
        return "quarantine"
    if action == "request_review":
        return "draft"
    if action == "restore_reviewed":
        return "reviewed"
    return from_status


def _resource_similarity_transition(resource: ResourceLibrary, action: str) -> dict[str, Any]:
    from_status = str(resource.review_status or "draft")
    return {
        "resource_id": resource.id,
        "title": resource.title,
        "from_status": from_status,
        "to_status": _resource_similarity_target_status(action, from_status),
        "quality_score": resource.quality_score,
        "family_key": "::".join(
            part
            for part in [
                str(resource.applicable_scene or "").strip(),
                str(resource.category or "").strip(),
                str(resource.title or "").split("｜", 1)[0].strip(),
            ]
            if part
        ),
    }


def _resource_similarity_action_report(
    data: ResourceSimilarityActionRequest,
    resources: list[ResourceLibrary],
    transitions: list[dict[str, Any]],
    logs: list[PipelineRunLog],
) -> dict[str, Any]:
    from_counts: dict[str, int] = {}
    to_counts: dict[str, int] = {}
    category_counts: dict[str, int] = {}
    for transition in transitions:
        from_status = str(transition["from_status"])
        to_status = str(transition["to_status"])
        from_counts[from_status] = from_counts.get(from_status, 0) + 1
        to_counts[to_status] = to_counts.get(to_status, 0) + 1
    for resource in resources:
        category = str(resource.category or "uncategorized")
        category_counts[category] = category_counts.get(category, 0) + 1
    return {
        "resource_count": len(resources),
        "reviewer_id": data.reviewer_id,
        "reason_hash": _resource_similarity_reason_hash(data.reason),
        "category_counts": category_counts,
        "from_status_counts": from_counts,
        "to_status_counts": to_counts,
        "audit_log_ids": [log.id for log in logs if log.id is not None],
        "next_action": _resource_similarity_next_action(data.action),
        "safety_flags": {
            "raw_source_text_saved": False,
            "reason_text_returned": False,
            "content_deleted": False,
            "default_listing_hides_quarantine": True,
        },
    }


def _resource_similarity_audit_payload(
    resource: ResourceLibrary,
    data: ResourceSimilarityActionRequest,
    from_status: str,
    to_status: str,
) -> dict[str, Any]:
    return {
        "resource_id": resource.id,
        "resource_uuid": resource.resource_uuid,
        "title_hash": hashlib.sha256(str(resource.title or "").encode("utf-8")).hexdigest(),
        "from_status": from_status,
        "to_status": to_status,
        "reviewer_id": data.reviewer_id,
        "reason_hash": _resource_similarity_reason_hash(data.reason),
        "quality_score": resource.quality_score,
        "category": resource.category,
        "applicable_scene": resource.applicable_scene,
        "raw_source_text_saved": False,
        "content_deleted": False,
    }


def _resource_similarity_reason_hash(reason: str) -> str:
    return "sha256:" + hashlib.sha256(reason.strip().encode("utf-8")).hexdigest()


def _resource_similarity_next_action(action: str) -> str:
    if action == "quarantine_variants":
        return "刷新资源海洋和近重复队列，确认默认列表不再展示被隔离变体。"
    if action == "request_review":
        return "由内容审阅人重写为更具体案例，复审后再恢复 reviewed/published。"
    if action == "restore_reviewed":
        return "恢复后重新运行质量报告，确认内容具备足够具体性和差异性。"
    return "继续观察近重复队列。"


def _resource_rewrite_blueprint(original: ResourceLibrary, index: int) -> dict[str, Any]:
    scene = original.applicable_scene or "修复"
    category = original.category or "关系训练"
    source_title = (original.source_title or original.source or "近重复资源").replace("public_anchor:", "")
    scenario = _rewrite_scenario(scene, index)
    title = f"{scenario['theme']}｜差异化案例{index}"
    dialogue_script = _rewrite_dialogue_script(scenario)
    dialogue = "；".join(f"{item['speaker']}：{item['line']}" for item in dialogue_script)
    blueprint = _rewrite_case_blueprint(
        original=original,
        index=index,
        scene=scene,
        category=category,
        title=title,
        scenario=scenario,
        dialogue_script=dialogue_script,
    )
    content = (
        f"场景：{scenario['situation']}\n"
        f"TA说：{scenario['their_words']}\n"
        f"完整对话：{dialogue}\n"
        f"常见失误：{scenario['mistake']}\n"
        f"更好回应：{scenario['better']}\n"
        f"情绪信号：{scenario['signal']}\n"
        f"边界与同意：{scenario['boundary']}\n"
        f"练习任务：{scenario['practice']}"
    )
    fingerprint = hashlib.sha256(
        "::".join([title, content, scene, category, str(index)]).encode("utf-8")
    ).hexdigest()
    tags = ",".join([
        "具体案例",
        "近重复重写补位",
        scene,
        *_split_tags(original.tags)[:4],
        *scenario["tags"],
    ])
    return {
        "resource_uuid": f"rewrite:{original.resource_uuid}:{fingerprint[:12]}",
        "type": original.type,
        "category": category,
        "title": title,
        "content": content,
        "emotional_tone": {"primary": scenario["tone"], "flow": ["事实", "感受", "边界", "行动"]},
        "emotional_intensity": min(10, max(4, int(original.emotional_intensity or 6) + (index % 2))),
        "applicable_scene": scene,
        "difficulty_level": min(3, max(1, int(original.difficulty_level or 2))),
        "gender_target": original.gender_target or "通用",
        "attachment_suitability": original.attachment_suitability or "通用",
        "usage_tip": "这是为近重复治理生成的本地原创补位案例，重点训练具体场景、原话、失误、改写和边界。",
        "effectiveness_rating": max(8, int(original.effectiveness_rating or 8)),
        "source": "project_original:resource_similarity_rewrite",
        "source_url": "synthetic://relationship-training/resource-similarity-rewrite",
        "source_title": f"重写自近重复家族：{source_title}",
        "source_excerpt": "本地原创差异化训练案例，不保存或复刻第三方全文。",
        "source_summary": f"针对 {scene} / {category} 的近重复资源生成具体场景补位，保留原资源审计链。",
        "content_fingerprint": fingerprint,
        "quality_score": max(float(original.quality_score or 86), 92.0),
        "tags": tags,
        "case_blueprint_json": json.dumps(blueprint, ensure_ascii=False, sort_keys=True),
        "case_completeness_score": 100.0,
        "coverage_axis": blueprint["axis"],
        "variant_family": f"resource_similarity_rewrite:{scene}:{category}",
        "variant_signature": fingerprint[:16],
        "content_unit": "case_card",
    }


def _rewrite_dialogue_script(scenario: dict[str, Any]) -> list[dict[str, str]]:
    return [
        {"speaker": "TA", "line": str(scenario["their_words"]), "purpose": "原始信号"},
        {"speaker": "低质量回应", "line": str(scenario["mistake"]), "purpose": "展示常见误判"},
        {"speaker": "更好回应", "line": str(scenario["better"]), "purpose": "承接语境并保留边界"},
        {"speaker": "TA", "line": str(scenario.get("reply") or "这样说我比较能接住，也知道自己可以慢一点回应。"), "purpose": "更可能出现的反馈"},
        {"speaker": "边界收束", "line": str(scenario["boundary"]), "purpose": "说明可继续、暂停或拒绝"},
    ]


def _rewrite_case_blueprint(
    *,
    original: ResourceLibrary,
    index: int,
    scene: str,
    category: str,
    title: str,
    scenario: dict[str, Any],
    dialogue_script: list[dict[str, str]],
) -> dict[str, Any]:
    axis = _rewrite_axis(category, scene, scenario)
    return {
        "version": "resource_similarity_rewrite_v2",
        "source_resource_id": original.id,
        "source_resource_uuid": original.resource_uuid,
        "axis": axis,
        "axis_label": _rewrite_axis_label(axis),
        "resource_type": original.type,
        "resource_type_label": "近重复差异化训练卡",
        "scene": scene,
        "relation_stage": scene,
        "category": category,
        "title": title,
        "setting": scenario["situation"],
        "trigger": f"近重复资源簇中缺少足够具体的“{scene}”训练画面，需要转成可练的一段对话。",
        "their_words": scenario["their_words"],
        "surface_signal": scenario["signal"],
        "deeper_need": scenario.get("need") or "希望自己的感受被看见，同时不被催促、控制或定性。",
        "common_mistake": scenario["mistake"],
        "why_wrong": scenario.get("why_wrong") or "这个回应把注意力放在辩解、逼问或评价上，没有贴住对方刚说出的具体信号。",
        "better_response": scenario["better"],
        "dialogue_script": dialogue_script,
        "response_steps": scenario.get("steps") or ["复述具体事实", "命名可校正感受", "给低压力选择", "保留暂停或拒绝出口"],
        "boundary_note": scenario["boundary"],
        "practice_task": scenario["practice"],
        "transfer_scene": scenario.get("transfer") or "换到相邻关系阶段，保留事实-感受-选择结构，但重写具体原话和回应。",
        "variant_deltas": [
            f"差异化序号：{index}",
            f"具体场景：{scenario['theme']}",
            "每张补位卡必须包含完整对话、错误回应、更好回应、边界和练习任务。",
        ],
        "source_mapping": {
            "source_policy": "project_original_no_third_party_full_text",
            "rewrite_reason": "near_duplicate_family_to_concrete_training_case",
        },
        "quality_notes": {
            "specificity": 20,
            "dialogue_completeness": 20,
            "better_response_grounded": 20,
            "boundary_clarity": 20,
            "practice_ready": 20,
        },
    }


def _rewrite_axis(category: str, scene: str, scenario: dict[str, Any]) -> str:
    text = " ".join([category, scene, " ".join(str(item) for item in scenario.get("tags", []))])
    if any(token in text for token in ("边界", "同意", "可拒绝", "亲密节奏")):
        return "boundary_consent"
    if any(token in text for token in ("冲突", "修复", "道歉", "冷战", "失望")):
        return "conflict_repair"
    if any(token in text for token in ("幽默", "玩笑", "游戏", "调侃")):
        return "humor_interaction"
    if any(token in text for token in ("暧昧", "调情", "表白", "张力")):
        return "flirty_tension"
    if any(token in text for token in ("长期", "异地", "期待", "连接")):
        return "long_connection"
    if any(token in text for token in ("情绪", "感受", "自我揭露", "沉默陪伴")):
        return "emotion_flow"
    return "micro_signal"


def _rewrite_axis_label(axis: str) -> str:
    return {
        "micro_signal": "微关系信号",
        "emotion_flow": "情绪流动",
        "boundary_consent": "边界与同意",
        "flirty_tension": "暧昧张力",
        "conflict_repair": "冲突修复",
        "long_connection": "长期连接",
        "humor_interaction": "幽默互动",
    }.get(axis, "微关系信号")


def _rewrite_scenario(scene: str, index: int) -> dict[str, Any]:
    templates = [
        {
            "theme": "晚回消息后的轻确认",
            "situation": "晚上十点半，对方隔了四小时回你：刚忙完，脑子有点空。",
            "their_words": "刚忙完，今天有点累。",
            "mistake": "你是不是不想理我？那算了。",
            "better": "辛苦了。你现在更想安静一下，还是让我陪你聊两句轻的？我不催你回。",
            "signal": "疲惫里带着报备，可能是在保留连接，也可能是在请求低压力空间。",
            "boundary": "不把晚回等同于冷淡，先给对方选择沉默或继续的权利。",
            "practice": "把追问改成一个二选一的轻确认，并允许对方明天再回。",
            "tags": ["晚回消息", "低压力陪伴"],
            "tone": "温柔",
        },
        {
            "theme": "失望后的重新约定",
            "situation": "你答应周末一起吃饭，却临时改了安排。对方没有吵，只回了一个“嗯”。",
            "their_words": "嗯，知道了。",
            "mistake": "你别这样，我也不是故意的。",
            "better": "这个“嗯”我听着有失望。是我临时改变让你没有被优先考虑。今晚我先不解释，先补一个确定的新时间：周六六点，可以吗？",
            "signal": "短回复可能是在压住委屈，不代表事情已经过去。",
            "boundary": "修复不是逼对方马上原谅，而是先承担影响并给出可靠行动。",
            "practice": "写一句包含影响承认、少解释、具体补偿时间的回应。",
            "tags": ["失望修复", "可靠行动"],
            "tone": "修复",
        },
        {
            "theme": "亲密推进前的明确确认",
            "situation": "两个人靠得很近，气氛升温，但对方突然安静，眼神从你身上移开。",
            "their_words": "我不是不喜欢你，就是有点紧张。",
            "mistake": "都这样了你还紧张什么？",
            "better": "谢谢你直接说。我们可以慢下来，停在拥抱也很好；你不用证明什么，我更在意你舒服。",
            "signal": "喜欢和紧张可以同时存在，沉默可能是需要确认节奏。",
            "boundary": "任何亲密推进都要以清晰同意和可随时停止为前提。",
            "practice": "写一句让对方不用解释、也不用迎合的降速回应。",
            "tags": ["边界与同意", "亲密节奏"],
            "tone": "克制",
        },
        {
            "theme": "朋友聚会里的被忽略感",
            "situation": "聚会中你讲了两次话都被岔开，对方一直和朋友聊工作梗。",
            "their_words": "你刚才怎么突然不说话了？",
            "mistake": "你现在才发现？你眼里根本没有我。",
            "better": "我刚才有点落单，尤其我说话被岔开的时候。不是要你只围着我转，但我需要你偶尔把我带回场子里。",
            "signal": "沉默不是作，可能是在社交场里失去位置感。",
            "boundary": "表达需要时只描述具体场景，不把一次忽略升级成人格否定。",
            "practice": "写出事实、感受、具体请求，不使用绝对化词。",
            "tags": ["社交场景", "被忽略感"],
            "tone": "坦诚",
        },
        {
            "theme": "初次邀约里的可拒绝出口",
            "situation": "你们第一次聊得不错，你想约周末喝咖啡，但还不确定对方是否愿意推进。",
            "their_words": "这周末我还没想好安排。",
            "mistake": "那你到底有没有兴趣？别吊着我。",
            "better": "没关系，你不用现在定。如果你愿意，我们可以先约一个轻一点的咖啡；如果这周不合适，也完全没压力。",
            "signal": "模糊回应可能是在保留选择，不一定是拒绝。",
            "boundary": "邀约要给对方明确拒绝和延后的空间。",
            "practice": "写一句邀请，里面必须包含时间、轻量选项和可拒绝出口。",
            "tags": ["初识邀约", "可拒绝出口"],
            "tone": "轻松",
        },
        {
            "theme": "价值观分歧的降温问法",
            "situation": "聊到消费习惯时，你们明显观点不同，气氛开始变硬。",
            "their_words": "我觉得花钱享受生活没有错。",
            "mistake": "你这样以后肯定存不下钱。",
            "better": "我听见你在重视当下体验。我比较在意安全感，我们能不能先不判断对错，分别说说钱对我们意味着什么？",
            "signal": "价值观分歧背后常常是安全感和自由感的不同权重。",
            "boundary": "不把分歧升级为人格评判，先回到各自需求。",
            "practice": "把一句评判改成“我在意什么 + 我想了解你在意什么”。",
            "tags": ["价值观", "分歧降温"],
            "tone": "克制",
        },
        {
            "theme": "冷战后的第一句破冰",
            "situation": "争吵后两天没有联系，你想重新打开对话，但不想逼对方马上和好。",
            "their_words": "我现在不知道该怎么说。",
            "mistake": "你总是逃避，能不能成熟一点？",
            "better": "我也还没完全整理好，但我不想让沉默继续扩大。今天先不争对错，我想先确认你还愿不愿意找个时间慢慢说。",
            "signal": "不知道怎么说可能是还在防御，也可能是怕再次爆发。",
            "boundary": "破冰不是逼供，先确认是否愿意恢复沟通。",
            "practice": "写一句不追责、不逼迫、只打开谈话入口的破冰话。",
            "tags": ["冷战修复", "重新开口"],
            "tone": "修复",
        },
        {
            "theme": "复联时不翻旧账的试探",
            "situation": "一段关系中断后，对方突然点赞你的动态，你想回应但不想立刻拉回旧循环。",
            "their_words": "最近看起来过得不错。",
            "mistake": "你现在知道回来找我了？",
            "better": "还在慢慢调整。看到你留言我有点意外，也有点平静。如果只是问候，我收到了；如果你想聊清楚，我们可以另约时间。",
            "signal": "轻触可能是试探，也可能只是礼貌问候。",
            "boundary": "复联要区分问候和重启，不自动把小信号解释成承诺。",
            "practice": "写一句既回应善意、又不立刻进入旧关系定位的话。",
            "tags": ["复联", "旧循环边界"],
            "tone": "克制",
        },
        {
            "theme": "异地疲惫里的连接维护",
            "situation": "异地一周后，对方说最近视频有点累，但你很想保持亲密。",
            "their_words": "今天能不能不视频，我真的有点累。",
            "mistake": "你是不是不想我了？",
            "better": "可以。你累的时候我们不用硬撑仪式感。我会想你，但今晚你先休息；明天我们发三张今天的小照片就好。",
            "signal": "减少视频不等于减少在意，可能是能量不足。",
            "boundary": "维护连接不能变成打卡压力，需要允许低能量版本。",
            "practice": "设计一个比视频更轻的连接动作，并说清楚不施压。",
            "tags": ["异地", "低能量连接"],
            "tone": "温柔",
        },
        {
            "theme": "家务分工里的具体请求",
            "situation": "同居后你连续三次收拾厨房，对方没注意到你的疲惫。",
            "their_words": "你怎么突然脸色不好？",
            "mistake": "你眼里就没有活，什么都要我说。",
            "better": "我这几天连续收厨房有点累。不是要你猜，我想我们把晚饭后的收尾固定轮换，今天你负责台面和垃圾，可以吗？",
            "signal": "怨气常来自长期未说清的期待。",
            "boundary": "提出请求要落到具体任务，不用羞辱对方来证明自己累。",
            "practice": "把一句抱怨改成一个可执行的分工请求。",
            "tags": ["长期连接", "家务分工"],
            "tone": "坚定",
        },
        {
            "theme": "纪念日落差的温和说明",
            "situation": "你重视纪念日，对方只发了一句节日快乐，你心里有落差。",
            "their_words": "我以为你不太在意这些形式。",
            "mistake": "你根本不懂我，连这点心意都没有。",
            "better": "我确实在意，不是礼物大小，是被记得的感觉。以后这种日子，我们能不能提前说各自期待，免得靠猜？",
            "signal": "落差背后常是“我有没有被放在心上”的确认需求。",
            "boundary": "说明期待，不把一次疏忽定性为不爱。",
            "practice": "写一句表达落差但不攻击动机的回应。",
            "tags": ["纪念日", "期待校准"],
            "tone": "坦诚",
        },
        {
            "theme": "玩笑越界后的即时修复",
            "situation": "你开了一个玩笑，对方笑了一下但马上转移话题，气氛有点僵。",
            "their_words": "算了，说别的吧。",
            "mistake": "你怎么这么开不起玩笑？",
            "better": "刚才那个玩笑可能越界了，我收回。谢谢你没有硬接，以后这种点我会避开。",
            "signal": "转移话题可能是在体面地提示不舒服。",
            "boundary": "幽默不能要求对方配合，越界后先收回而不是辩解。",
            "practice": "写一句承认越界、停止继续、给出以后调整的修复话。",
            "tags": ["幽默互动", "越界修复"],
            "tone": "真诚",
        },
        {
            "theme": "暧昧推拉里的不操控表达",
            "situation": "对方主动夸你，你想制造张力，但不想用冷暴力或吊胃口。",
            "their_words": "你今天还挺好看的。",
            "mistake": "现在才发现？晚了。",
            "better": "这句我收下了，不过我得观察一下你是只会夸今天，还是平时也这么有眼光。",
            "signal": "轻夸是靠近信号，可以接住再轻轻挑战。",
            "boundary": "张力来自玩味和回应，不来自惩罚、贬低或让对方不安。",
            "practice": "写一句“接住夸奖 + 轻挑战”的回应，不使用否定人格的词。",
            "tags": ["暧昧张力", "轻挑战"],
            "tone": "调皮",
        },
        {
            "theme": "脆弱自我揭露后的承接",
            "situation": "对方第一次说起自己不被重视的经历，说完后有点后悔。",
            "their_words": "算了，我说这些是不是有点矫情。",
            "mistake": "这有什么，大家都经历过。",
            "better": "不矫情。你愿意说出来，我会认真听。我们不用马上解决它，我只想先陪你把这部分放稳一点。",
            "signal": "自我否定往往是在测试表达脆弱是否安全。",
            "boundary": "承接脆弱时不抢着分析，也不逼对方继续暴露。",
            "practice": "写一句确认对方表达合理、同时允许停下来的回应。",
            "tags": ["自我揭露", "安全承接"],
            "tone": "温柔",
        },
        {
            "theme": "需要独处时的连接保留",
            "situation": "你压力很大想独处，但担心对方误会你在疏远。",
            "their_words": "你是不是最近不想见我？",
            "mistake": "我就想一个人待着，你别烦我。",
            "better": "不是不想见你，是我现在能量很低，怕见面时也心不在焉。我今晚先安静一下，明天中午给你发消息，好吗？",
            "signal": "独处需求如果不说明时间和连接，会被理解成撤退。",
            "boundary": "表达空间需求时给出回来的时间，不让对方在不确定里悬着。",
            "practice": "写一句包含不是拒绝、需要空间、何时回来三要素的话。",
            "tags": ["空间边界", "连接保留"],
            "tone": "坦诚",
        },
        {
            "theme": "吃醋时不控制的表达",
            "situation": "你看到对方和朋友聊得很开心，心里有点酸，但不想变成查问。",
            "their_words": "你刚才怎么突然安静了？",
            "mistake": "你和TA到底什么关系？",
            "better": "我刚才有点吃醋，也知道这不等于你做错了什么。我想要一点被安放的感觉，不是要限制你交朋友。",
            "signal": "吃醋可能是安全感提醒，不必直接变成控制行为。",
            "boundary": "说自己的感受，不要求对方切断正常社交。",
            "practice": "写一句把吃醋说成自我感受，而不是审问对方的回应。",
            "tags": ["安全感", "非控制表达"],
            "tone": "克制",
        },
        {
            "theme": "忙碌期里的期待重排",
            "situation": "对方进入项目冲刺期，回复变少，你开始焦虑。",
            "their_words": "这两周我真的会很忙。",
            "mistake": "忙到连一句话都不能回吗？",
            "better": "我知道你这两周压力大。我们把期待调轻一点：每天不用长聊，但睡前给我一个安全到达或晚安，我会更安心。",
            "signal": "忙碌会压缩互动，需要从频率要求转成最低连接约定。",
            "boundary": "不否认对方压力，也不压掉自己的基本安全需求。",
            "practice": "设计一个两周临时连接协议，包含最低频率和复盘时间。",
            "tags": ["忙碌期", "连接协议"],
            "tone": "协商",
        },
        {
            "theme": "道歉后不索要原谅",
            "situation": "你意识到自己刚才语气很冲，想道歉，但对方还在生气。",
            "their_words": "你每次道歉都像要我马上没事。",
            "mistake": "我都道歉了你还想怎样？",
            "better": "你说得对，我以前道歉里有催你翻篇的压力。这次我只先承认我语气伤人，原不原谅由你决定，我会用后面的行动改。",
            "signal": "对方抗拒的可能不是道歉，而是被要求立刻恢复关系。",
            "boundary": "道歉是承担，不是交换原谅。",
            "practice": "写一句不索要原谅、只承认影响和行动方向的道歉。",
            "tags": ["道歉", "修复责任"],
            "tone": "真诚",
        },
        {
            "theme": "表白被犹豫后的体面承接",
            "situation": "你表达好感后，对方没有拒绝也没有答应，只说需要想想。",
            "their_words": "我需要一点时间想想。",
            "mistake": "你是不是在养备胎？",
            "better": "谢谢你认真对待。你可以想，我不会用压力催答案。无论结果怎样，我都希望我们能诚实一点，不用互相猜。",
            "signal": "犹豫可能是慎重，也可能是边界提醒。",
            "boundary": "表白后不把等待变成情绪勒索。",
            "practice": "写一句允许对方思考、也保护自己不长期悬置的回应。",
            "tags": ["表白", "体面承接"],
            "tone": "成熟",
        },
        {
            "theme": "玩游戏输赢里的轻调侃",
            "situation": "你们玩问答小游戏，对方赢了，气氛轻松。",
            "their_words": "看来还是我比较懂你。",
            "mistake": "你别太得意。",
            "better": "是，你赢得有点危险了。下一题我要认真防守，但你可以继续得意三秒。",
            "signal": "轻胜负能制造亲近，但要保持玩笑而非压制。",
            "boundary": "调侃只针对情境，不贬低能力或外貌。",
            "practice": "写一句让对方有被接住的得意感，同时继续互动的调侃。",
            "tags": ["游戏互动", "低压幽默"],
            "tone": "幽默",
        },
        {
            "theme": "对方求建议前先问许可",
            "situation": "对方抱怨工作委屈，你马上想到解决方案，但不确定TA想要建议还是陪伴。",
            "their_words": "我今天真的被气到了。",
            "mistake": "你应该直接跟领导说清楚。",
            "better": "听起来你今天被压得很难受。我可以先陪你骂两句，也可以帮你一起想办法；你现在更想要哪一种？",
            "signal": "强烈情绪时，建议可能太早，先确认支持方式。",
            "boundary": "不给未经邀请的指导，先问对方需要什么支持。",
            "practice": "写一句“情绪标注 + 支持方式选择题”。",
            "tags": ["情绪支持", "建议许可"],
            "tone": "共情",
        },
        {
            "theme": "需求没被满足时的复盘邀请",
            "situation": "你说过想要更多主动分享，但一周过去几乎没有变化。",
            "their_words": "我以为我已经比以前多说了。",
            "mistake": "你根本没把我的话放心上。",
            "better": "我看到你有在试，只是我们对“多分享”的标准可能不一样。要不要今晚花十分钟对齐一下：什么频率对你不累、对我也安心？",
            "signal": "执行落差可能来自定义不清，而非不在乎。",
            "boundary": "复盘聚焦标准和方法，不否定对方努力。",
            "practice": "写一句承认努力、提出对齐标准的复盘邀请。",
            "tags": ["需求复盘", "期待对齐"],
            "tone": "协作",
        },
        {
            "theme": "沉默陪伴里的不追问",
            "situation": "对方明显低落，但只说没事，你感觉TA还没准备好展开。",
            "their_words": "没事，我就是有点累。",
            "mistake": "你不说我怎么知道？",
            "better": "好，那我不追问。你可以先安静一下，我在旁边；如果你想说，我会听。",
            "signal": "没事有时是暂时没有力气组织语言。",
            "boundary": "陪伴不是挖答案，尊重对方暂时不说。",
            "practice": "写一句允许沉默、同时保留陪伴入口的话。",
            "tags": ["沉默陪伴", "不追问"],
            "tone": "安稳",
        },
        {
            "theme": "公开场合里的边界救场",
            "situation": "朋友当众开你们关系的玩笑，对方明显不自在。",
            "their_words": "哈哈，别说这个了。",
            "mistake": "没事啦，大家都开玩笑。",
            "better": "这个话题先到这。我们换一个轻松点的，别让TA被围观。",
            "signal": "勉强笑可能是在请求你帮忙挡一下。",
            "boundary": "公开场合优先保护当事人的体面和退出权。",
            "practice": "写一句对外截断话题、对内保护对方的救场句。",
            "tags": ["公开边界", "救场"],
            "tone": "坚定",
        },
        {
            "theme": "身体亲密后的情绪安放",
            "situation": "亲密后对方突然变安静，你不知道TA是在放松还是有不安。",
            "their_words": "我想靠一会儿，不想说话。",
            "mistake": "你是不是后悔了？",
            "better": "好，我们就安静靠一会儿。如果你之后有任何不舒服或想调整的地方，都可以跟我说，我会认真听。",
            "signal": "亲密后的安静可能是放松，也可能需要安全确认。",
            "boundary": "不逼问感受，但明确任何不适都可以被说出和尊重。",
            "practice": "写一句亲密后的低压安放话，包含不逼问和可反馈。",
            "tags": ["亲密后照护", "同意延续"],
            "tone": "温柔",
        },
        {
            "theme": "计划变更前的提前告知",
            "situation": "你发现今晚可能要加班，原定见面大概率会迟到。",
            "their_words": "所以你又要晚到吗？",
            "mistake": "我也没办法，你理解一下。",
            "better": "我现在提前告诉你，不想让你空等。我大概会晚四十分钟；你可以选择改明天，或者我到后负责安排晚饭。",
            "signal": "对方生气的重点可能不是变更，而是被动等待。",
            "boundary": "变更计划要给对方选择权，不把理解当义务。",
            "practice": "写一句包含提前告知、预计时间、替代选项的回应。",
            "tags": ["计划变更", "可靠行动"],
            "tone": "负责",
        },
        {
            "theme": "夸奖后的具体化追问",
            "situation": "对方说喜欢和你聊天，你想把连接从泛泛的甜推进到更真实。",
            "their_words": "跟你聊天还挺舒服的。",
            "mistake": "那你是不是喜欢我？",
            "better": "这句我很开心。你说的舒服，是因为轻松，还是因为有些话不用解释太多？我想知道哪部分对你重要。",
            "signal": "舒服是连接信号，可以温柔追问具体来源。",
            "boundary": "不把夸奖立刻逼成关系定义。",
            "practice": "写一句接住夸奖，并把感受具体化的开放问题。",
            "tags": ["连接深化", "开放追问"],
            "tone": "好奇",
        },
    ]
    scene_offsets = {
        "初识": 4,
        "邀约": 4,
        "暧昧": 9,
        "调情": 9,
        "撩": 9,
        "情话": 22,
        "热恋": 2,
        "亲密": 22,
        "冲突": 1,
        "修复": 1,
        "冷战": 6,
        "复联": 7,
        "异地": 8,
        "长期": 10,
        "家庭": 10,
        "家务": 10,
        "纪念日": 11,
        "幽默": 12,
        "玩笑": 12,
        "互怼": 17,
        "边界": 18,
        "分歧": 5,
        "平淡": 19,
    }
    offset = 0
    for keyword, value in scene_offsets.items():
        if keyword in scene:
            offset = value
            break
    return templates[(index - 1 + offset) % len(templates)]


def _resource_rewrite_batch_report(
    data: ResourceSimilarityRewriteRequest,
    originals: list[ResourceLibrary],
    drafts: list[dict[str, Any]],
    logs: list[PipelineRunLog],
) -> dict[str, Any]:
    return {
        "original_count": len(originals),
        "replacement_count": len(drafts),
        "reviewer_id": data.reviewer_id,
        "reason_hash": _resource_similarity_reason_hash(data.reason),
        "mark_originals_quarantine": data.mark_originals_quarantine,
        "scenes": sorted({str(item.applicable_scene or "unknown") for item in originals}),
        "audit_log_ids": [log.id for log in logs if log.id is not None],
        "safety_flags": {
            "project_original_only": True,
            "third_party_full_text_saved": False,
            "reason_text_returned": False,
            "original_content_deleted": False,
        },
        "next_action": "刷新资源海洋和近重复队列，确认新补位案例有具体场景、原话、失误、改写、情绪信号和边界任务。",
    }


def _resource_rewrite_audit_payload(
    original: ResourceLibrary,
    draft: dict[str, Any],
    data: ResourceSimilarityRewriteRequest,
    from_status: str,
) -> dict[str, Any]:
    return {
        "original_resource_id": original.id,
        "original_uuid": original.resource_uuid,
        "replacement_uuid": draft["resource_uuid"],
        "from_status": from_status,
        "to_status": "quarantine",
        "reviewer_id": data.reviewer_id,
        "reason_hash": _resource_similarity_reason_hash(data.reason),
        "replacement_fingerprint": draft["content_fingerprint"],
        "third_party_full_text_saved": False,
        "original_content_deleted": False,
    }


def _resource_rewrite_created_item(resource: ResourceLibrary) -> dict[str, Any]:
    return {
        "id": resource.id,
        "resource_uuid": resource.resource_uuid,
        "title": resource.title,
        "category": resource.category,
        "applicable_scene": resource.applicable_scene,
        "review_status": resource.review_status,
        "quality_score": resource.quality_score,
    }


def _split_tags(value: str | None) -> list[str]:
    if not value:
        return []
    return [item.strip() for item in value.split(",") if item.strip()]


@router.get("/random", response_model=ResourceLibrary | None)
def get_random_resource(
    type: str | None = None,
    resource_type: str | None = None,
    applicable_scene: str | None = None,
    session: Session = Depends(get_session)
) -> ResourceLibrary | None:
    """随机获取一个资源"""
    effective_type = type or resource_type
    query = select(ResourceLibrary)

    if effective_type:
        query = query.where(ResourceLibrary.type == effective_type)
    if applicable_scene:
        query = query.where(ResourceLibrary.applicable_scene == applicable_scene)

    results = session.exec(query).all()
    if results:
        import random
        return random.choice(list(results))
    return None


@router.get("/types")
def get_resource_types() -> list[str]:
    """获取所有资源类型"""
    return ["joke", "story", "flirty", "phrase", "riddle", "game", "media"]


@router.get("/quality-report")
def get_resource_quality_report(session: Session = Depends(get_session)) -> dict:
    """获取资源海洋质量报告：规模、去重、导读覆盖和质量分。"""
    report = resource_quality_report(session)
    report["principle"] = "资源海洋以可点击来源、导读摘要、短摘录/摘要、训练转化和去重指纹为主，不复制第三方全文。"
    return report


@router.get("/similarity")
def get_resource_similarity_queue(
    limit: int = Query(default=1000, ge=20, le=5000),
    threshold: float = Query(default=0.82, ge=0.5, le=0.99),
    max_clusters: int = Query(default=24, ge=1, le=100),
    session: Session = Depends(get_session),
) -> dict:
    """获取资源海洋近重复治理队列。"""
    return resource_similarity_queue(session, limit=limit, threshold=threshold, max_clusters=max_clusters)


@router.post("/similarity/action")
def resource_similarity_action(data: ResourceSimilarityActionRequest, session: Session = Depends(get_session)) -> dict:
    """对近重复资源簇执行保守治理动作。"""
    resources = list(session.exec(select(ResourceLibrary).where(col(ResourceLibrary.id).in_(data.resource_ids))).all())
    found_ids = {int(item.id or 0) for item in resources}
    missing_ids = [resource_id for resource_id in data.resource_ids if resource_id not in found_ids]
    if missing_ids:
        raise HTTPException(status_code=404, detail={"missing_resource_ids": missing_ids})

    transitions = [_resource_similarity_transition(item, data.action) for item in resources]
    report = _resource_similarity_action_report(data, resources, transitions, [])
    if data.dry_run:
        return {
            "dry_run": True,
            "action": data.action,
            "transitions": transitions,
            "governance_report": report,
            "principle": "dry-run 只预演近重复治理；真实执行会保留资源记录并写入 pipeline_run_logs。",
        }

    logs: list[PipelineRunLog] = []
    now = datetime.now()
    for resource in resources:
        before = str(resource.review_status or "draft")
        after = _resource_similarity_target_status(data.action, before)
        resource.review_status = after
        resource.reviewer_id = data.reviewer_id
        resource.reviewed_at = now if after in {"reviewed", "published"} else resource.reviewed_at
        if after != "published":
            resource.published_at = None
        session.add(resource)
        payload = _resource_similarity_audit_payload(resource, data, before, after)
        log = PipelineRunLog(
            target_type="resource",
            target_id=int(resource.id or 0),
            action=f"resource_similarity_{data.action}",
            from_status=before,
            to_status=after,
            result_json=json.dumps(payload, ensure_ascii=False),
            message=f"resource similarity governance: {data.action}; reason_hash={payload['reason_hash']}",
        )
        session.add(log)
        logs.append(log)
    session.commit()
    for log in logs:
        session.refresh(log)
    applied_transitions = [_resource_similarity_transition(item, data.action) for item in resources]
    return {
        "dry_run": False,
        "action": data.action,
        "transitions": applied_transitions,
        "audit_logs": [
            {"id": log.id, "target_id": log.target_id, "action": log.action, "created_at": log.created_at.isoformat()}
            for log in logs
        ],
        "governance_report": _resource_similarity_action_report(data, resources, applied_transitions, logs),
        "principle": "近重复资源治理只改变展示/复审状态，不删除素材；审计日志不保存人工说明明文。",
    }


@router.post("/similarity/rewrite-batch")
def resource_similarity_rewrite_batch(data: ResourceSimilarityRewriteRequest, session: Session = Depends(get_session)) -> dict:
    """为近重复资源簇生成差异化本地原创补位资源。"""
    originals = list(session.exec(select(ResourceLibrary).where(col(ResourceLibrary.id).in_(data.resource_ids))).all())
    found_ids = {int(item.id or 0) for item in originals}
    missing_ids = [resource_id for resource_id in data.resource_ids if resource_id not in found_ids]
    if missing_ids:
        raise HTTPException(status_code=404, detail={"missing_resource_ids": missing_ids})
    drafts = [_resource_rewrite_blueprint(item, index) for index, item in enumerate(originals, start=1)]
    governance_report = _resource_rewrite_batch_report(data, originals, drafts, [])
    if data.dry_run:
        return {
            "dry_run": True,
            "created": 0,
            "drafts": drafts,
            "governance_report": governance_report,
            "principle": "dry-run 只生成本地原创重写草案；真实执行会新增 reviewed 补位资源，可选隔离原重复变体。",
        }

    now = datetime.now()
    created: list[ResourceLibrary] = []
    logs: list[PipelineRunLog] = []
    for original, draft in zip(originals, drafts, strict=True):
        replacement = ResourceLibrary(
            resource_uuid=draft["resource_uuid"],
            type=str(draft["type"]),
            category=str(draft["category"]),
            title=str(draft["title"]),
            content=str(draft["content"]),
            emotional_tone_json=json.dumps(draft["emotional_tone"], ensure_ascii=False),
            emotional_intensity=int(draft["emotional_intensity"]),
            applicable_scene=str(draft["applicable_scene"]),
            difficulty_level=int(draft["difficulty_level"]),
            gender_target=str(draft["gender_target"]),
            attachment_suitability=str(draft["attachment_suitability"]),
            usage_tip=str(draft["usage_tip"]),
            effectiveness_rating=int(draft["effectiveness_rating"]),
            review_status="reviewed",
            reviewer_id=data.reviewer_id,
            reviewed_at=now,
            source=str(draft["source"]),
            source_url=str(draft["source_url"]),
            source_title=str(draft["source_title"]),
            source_excerpt=str(draft["source_excerpt"]),
            source_summary=str(draft["source_summary"]),
            source_license="project_original",
            content_fingerprint=str(draft["content_fingerprint"]),
            quality_score=float(draft["quality_score"]),
            tags=str(draft["tags"]),
            expression_tool_ids_json=original.expression_tool_ids_json,
            expression_goal=original.expression_goal,
            expression_level=original.expression_level,
            speech_act=original.speech_act,
            mistake_pattern=original.mistake_pattern,
            recommended_drills_json=original.recommended_drills_json,
            case_blueprint_json=str(draft["case_blueprint_json"]),
            variant_signature=str(draft["variant_signature"]),
            content_unit=str(draft["content_unit"]),
            coverage_axis=str(draft["coverage_axis"]),
            variant_family=str(draft["variant_family"]),
            case_completeness_score=float(draft["case_completeness_score"]),
        )
        session.add(replacement)
        created.append(replacement)
        if data.mark_originals_quarantine:
            before = str(original.review_status or "draft")
            original.review_status = "quarantine"
            original.reviewer_id = data.reviewer_id
            original.published_at = None
            session.add(original)
            log = PipelineRunLog(
                target_type="resource",
                target_id=int(original.id or 0),
                action="resource_similarity_rewrite_and_quarantine_original",
                from_status=before,
                to_status="quarantine",
                result_json=json.dumps(_resource_rewrite_audit_payload(original, draft, data, before), ensure_ascii=False),
                message=f"resource rewrite replacement created; reason_hash={_resource_similarity_reason_hash(data.reason)}",
            )
            session.add(log)
            logs.append(log)
    session.commit()
    for item in created:
        session.refresh(item)
    for log in logs:
        session.refresh(log)
    return {
        "dry_run": False,
        "created": len(created),
        "items": [_resource_rewrite_created_item(item) for item in created],
        "audit_logs": [
            {"id": log.id, "target_id": log.target_id, "action": log.action, "created_at": log.created_at.isoformat()}
            for log in logs
        ],
        "governance_report": _resource_rewrite_batch_report(data, originals, drafts, logs),
        "principle": "重写补位新增 project_original 资源，并可隔离原近重复变体；不复制第三方全文。",
    }


@router.get("/sources")
def get_resource_sources(
    limit: int = Query(default=48, ge=1, le=200),
    session: Session = Depends(get_session),
) -> dict:
    """获取资源库中的公开信息源目录，用于前端透明展示。"""
    health_by_url = _latest_source_health_by_url(session)
    rows = session.exec(
        select(
            ResourceLibrary.source,
            ResourceLibrary.source_url,
            func.count(ResourceLibrary.id),
        )
        .where(ResourceLibrary.source_url.like("http%"))
        .group_by(ResourceLibrary.source, ResourceLibrary.source_url)
        .order_by(func.count(ResourceLibrary.id).desc())
        .limit(limit)
    ).all()
    counts = {
        str(source_url): int(count)
        for source, source_url, count in rows
        if source and source_url
    }
    items = []
    known_urls = set()
    for item in SOURCE_CATALOG:
        source_url = item["url"]
        known_urls.add(source_url)
        items.append({
            "source": f"public_anchor:{item['name']}",
            "name": item["name"],
            "source_url": source_url,
            "count": counts.get(source_url, 0),
            "group": item["group"],
            "summary": item["summary"],
            "structure": item["structure"],
            "quality_notes": item["quality_notes"],
            "link_status": _source_link_status(source_url),
            "health": health_by_url.get(source_url) or _default_source_health(source_url),
            "themes": list(item["themes"]),
            "scenes": list(item["scenes"]),
        })
    for item in _source_registry_items(session, counts, known_urls, health_by_url):
        items.append(item)
    for source, source_url, count in rows:
        if not source or not source_url or source_url in known_urls:
            continue
        known_urls.add(str(source_url))
        clean_name = str(source).replace("public_anchor:", "")
        items.append({
            "source": source,
            "name": clean_name,
            "source_url": source_url,
            "count": int(count),
            "group": "扩展信息源",
            "summary": f"{clean_name} 是资源库登记的扩展入口，当前用于承载关系学习、故事、互动练习或数据参考的派生素材。",
            "structure": "外部网站/数据入口 + 本项目派生训练卡片 + 标签化检索。",
            "quality_notes": "已作为可点击来源锚点登记；后续应纳入周期性链接有效性检查。",
            "link_status": _source_link_status(str(source_url)),
            "health": health_by_url.get(str(source_url)) or _default_source_health(str(source_url)),
            "themes": [],
            "scenes": [],
        })
    limited_items = items[:limit]
    return {"items": limited_items, "total": len(limited_items)}


@router.post("/sources/health-check")
def source_link_health_check(
    data: SourceLinkHealthCheckRequest,
    session: Session = Depends(get_session),
) -> dict:
    """检查来源链接健康，只保存状态码/跳转等元数据，不抓取或保存正文。"""
    source_urls = data.source_urls or _registered_source_urls(session, data.limit)
    source_urls = list(dict.fromkeys(source_urls))[:data.limit]
    planned = [_default_source_health(url) for url in source_urls]
    if data.dry_run:
        return {
            "dry_run": True,
            "items": planned,
            "summary": _source_health_summary(planned),
            "principle": "dry-run 只列出待检查 URL；真实检查只记录状态码、跳转和时间，不保存网页正文。",
        }

    checked = [check_source_link_health(url, data.timeout_seconds) for url in source_urls]
    invalid_urls = [item["source_url"] for item in checked if item["status"] == "invalid"]
    if invalid_urls:
        _downgrade_invalid_source_resources(invalid_urls, session)
    log = PipelineRunLog(
        target_type="resource_source",
        target_id=0,
        action="source_link_health_check",
        from_status="scheduled",
        to_status="completed",
        result_json=json.dumps({
            "items": checked,
            "summary": _source_health_summary(checked),
            "body_saved": False,
            "invalid_links_downgraded": len(invalid_urls),
        }, ensure_ascii=False),
        message=f"checked {len(checked)} source links; invalid={len(invalid_urls)}",
    )
    session.add(log)
    session.commit()
    session.refresh(log)
    return {
        "dry_run": False,
        "items": checked,
        "summary": _source_health_summary(checked),
        "audit_log_id": log.id,
        "principle": "来源健康审计只落库元数据，不保存网页正文；失效链接对应资源会被降级为 draft 以避免默认展示。",
    }


@router.get("/filters")
def get_resource_filters(
    limit: int = Query(default=80, ge=10, le=300),
    session: Session = Depends(get_session),
) -> dict[str, Any]:
    """Return database-backed filter suggestions for the resource ocean."""
    visible_query = select(ResourceLibrary).where(ResourceLibrary.review_status.in_(("reviewed", "published")))
    for condition in _non_user_resource_exclusion_conditions():
        visible_query = visible_query.where(condition)
    resources = session.exec(visible_query).all()
    types: dict[str, int] = {}
    categories: dict[str, int] = {}
    scenes: dict[str, int] = {}
    tags: dict[str, int] = {}
    sources: dict[str, int] = {}
    expression_goals: dict[str, int] = {}
    coverage_axes: dict[str, int] = {}
    quality_bands: dict[str, int] = {}
    expression_tools: dict[str, dict[str, Any]] = {}
    keyword_terms: dict[str, int] = {}
    for resource in resources:
        _count_value(types, resource.type)
        _count_value(categories, resource.category)
        _count_value(scenes, resource.applicable_scene)
        _count_value(sources, resource.source)
        _count_value(expression_goals, resource.expression_goal)
        _count_value(coverage_axes, resource.coverage_axis)
        _count_value(quality_bands, _quality_band(resource.case_completeness_score))
        for tag in _split_tags(resource.tags):
            _count_value(tags, tag)
            _count_value(keyword_terms, tag)
        for token in [
            resource.title,
            resource.category,
            resource.applicable_scene,
            resource.expression_goal,
            resource.speech_act,
            resource.mistake_pattern,
        ]:
            _count_value(keyword_terms, token)
        for tool_id in _loads_string_list(resource.expression_tool_ids_json):
            if not tool_id:
                continue
            item = expression_tools.setdefault(tool_id, {"id": tool_id, "name": tool_id, "count": 0})
            item["count"] += 1
    _attach_expression_tool_names(expression_tools, session)
    return {
        "types": _option_list(types, limit=limit),
        "categories": _option_list(categories, limit=limit),
        "scenes": _option_list(scenes, limit=limit),
        "tags": _option_list(tags, limit=limit),
        "sources": _option_list(sources, limit=limit),
        "expression_goals": _option_list(expression_goals, limit=limit),
        "coverage_axes": _option_list(coverage_axes, limit=limit),
        "quality_bands": _option_list(quality_bands, limit=limit),
        "expression_tools": sorted(
            expression_tools.values(),
            key=lambda item: (-int(item["count"]), str(item["name"])),
        )[:limit],
        "keywords": _option_list(keyword_terms, limit=limit),
        "principle": "筛选建议来自当前 SQLite 可见资源，不含 quarantine 测试资产或被隔离内容；用户仍可手动输入任意关键词。",
    }


def _registered_source_urls(session: Session, limit: int) -> list[str]:
    urls = [str(item["url"]) for item in SOURCE_CATALOG if str(item.get("url") or "").startswith("http")]
    rows = session.exec(
        select(ResourceLibrary.source_url)
        .where(ResourceLibrary.source_url.like("http%"))
        .group_by(ResourceLibrary.source_url)
        .limit(limit)
    ).all()
    urls.extend(str(url) for url in rows if url)
    try:
        registry_rows = session.exec(
            text(
                """
                SELECT url
                FROM source_registry
                WHERE active = 1
                  AND url LIKE 'http%'
                  AND lower(coalesce(name, '')) NOT LIKE '%pytest%'
                  AND lower(coalesce(source_uuid, '')) NOT LIKE '%pytest%'
                LIMIT :limit
                """
            ),
            params={"limit": limit},
        ).all()
        urls.extend(str(row[0] if isinstance(row, tuple) else row) for row in registry_rows if row)
    except Exception:
        pass
    return list(dict.fromkeys(urls))[:limit]


def _source_registry_items(
    session: Session,
    counts: dict[str, int],
    known_urls: set[str],
    health_by_url: dict[str, dict[str, Any]],
) -> list[dict[str, Any]]:
    try:
        rows = session.exec(
            text(
                """
                SELECT source_uuid, name, source_type, url, trust_score,
                       update_frequency, allowed_use_json, last_checked_at
                FROM source_registry
                WHERE active = 1
                  AND url LIKE 'http%'
                  AND lower(coalesce(name, '')) NOT LIKE '%pytest%'
                  AND lower(coalesce(source_uuid, '')) NOT LIKE '%pytest%'
                ORDER BY trust_score DESC, id DESC
                LIMIT 240
                """
            )
        ).all()
    except Exception:
        return []

    items: list[dict[str, Any]] = []
    for row in rows:
        data = row._mapping if hasattr(row, "_mapping") else row
        source_url = str(data["url"] or "")
        if not source_url or source_url in known_urls:
            continue
        known_urls.add(source_url)
        metadata = _registry_surf_metadata(str(data["allowed_use_json"] or ""))
        name = str(data["name"] or source_url)
        items.append({
            "source": f"source_registry:{data['source_uuid']}",
            "name": name,
            "source_url": source_url,
            "count": counts.get(source_url, 0),
            "group": metadata.get("group") or _registry_group_label(str(data["source_type"] or "")),
            "summary": metadata.get("summary") or f"{name} 是来源登记表中的公开信息源，用于关系学习、沟通训练或数据参考的结构化入口。",
            "structure": metadata.get("structure") or "来源登记 + 元数据锚点 + 本地原创训练卡转化。",
            "quality_notes": metadata.get("quality_notes") or f"可信度 {float(data['trust_score'] or 0):.2f}；默认只保存链接、标题、摘要、短摘录和结构化分析。",
            "link_status": _source_link_status(source_url),
            "health": health_by_url.get(source_url) or _default_source_health(source_url),
            "themes": _string_list(metadata.get("themes")),
            "scenes": _string_list(metadata.get("scenes")),
        })
    return items


def _registry_surf_metadata(raw: str) -> dict[str, Any]:
    try:
        payload = json.loads(raw or "{}")
    except json.JSONDecodeError:
        return {}
    if isinstance(payload, dict):
        metadata = payload.get("surf_metadata")
        return metadata if isinstance(metadata, dict) else {}
    return {}


def _registry_group_label(source_type: str) -> str:
    return {
        "open_data": "开放数据导航",
        "course": "课程入口",
        "media": "媒体与播客",
        "chinese_source": "中文心理科普",
        "safety_education": "安全关系教育",
        "research": "研究机构",
    }.get(source_type, "扩展信息源")


def _string_list(value: Any) -> list[str]:
    if isinstance(value, list):
        return [str(item) for item in value if str(item).strip()]
    if isinstance(value, tuple):
        return [str(item) for item in value if str(item).strip()]
    return []


def _default_source_health(source_url: str) -> dict[str, Any]:
    return {
        "source_url": source_url,
        "status": _source_link_status(source_url),
        "http_code": None,
        "redirect_url": None,
        "redirected": False,
        "last_checked_at": None,
        "error_type": None,
    }


def _latest_source_health_by_url(session: Session) -> dict[str, dict[str, Any]]:
    log = session.exec(
        select(PipelineRunLog)
        .where(PipelineRunLog.target_type == "resource_source")
        .where(PipelineRunLog.action == "source_link_health_check")
        .order_by(PipelineRunLog.created_at.desc(), PipelineRunLog.id.desc())
        .limit(1)
    ).first()
    if not log:
        return {}
    try:
        payload = json.loads(log.result_json or "{}")
    except json.JSONDecodeError:
        return {}
    items = payload.get("items", [])
    if not isinstance(items, list):
        return {}
    return {
        str(item.get("source_url")): item
        for item in items
        if isinstance(item, dict) and item.get("source_url")
    }


def _source_health_summary(items: list[dict[str, Any]]) -> dict[str, int]:
    summary = {"total": len(items), "ok": 0, "invalid": 0, "unknown": 0}
    for item in items:
        status = str(item.get("status") or "unknown")
        summary[status if status in summary else "unknown"] += 1
    return summary


def _downgrade_invalid_source_resources(invalid_urls: list[str], session: Session) -> int:
    resources = session.exec(
        select(ResourceLibrary)
        .where(ResourceLibrary.source_url.in_(invalid_urls))
        .where(ResourceLibrary.review_status.in_(("reviewed", "published")))
    ).all()
    for resource in resources:
        resource.review_status = "draft"
        resource.published_at = None
        session.add(resource)
    return len(resources)


@router.get("/{resource_id}", response_model=ResourceLibrary)
def get_resource(
    resource_id: int,
    session: Session = Depends(get_session)
) -> ResourceLibrary:
    """获取单个资源详情"""
    result = session.exec(
        select(ResourceLibrary).where(ResourceLibrary.id == resource_id)
    ).first()

    if not result:
        raise HTTPException(status_code=404, detail="资源不存在")

    return result


def _count_value(target: dict[str, int], raw: str | None) -> None:
    value = str(raw or "").strip()
    if not value:
        return
    target[value] = target.get(value, 0) + 1


def _option_list(values: dict[str, int], *, limit: int) -> list[dict[str, Any]]:
    return [
        {"value": value, "label": value, "count": count}
        for value, count in sorted(values.items(), key=lambda item: (-item[1], item[0]))[:limit]
    ]


def _quality_band(value: float | None) -> str:
    if value is None:
        return "未评分"
    score = float(value)
    if score >= 95:
        return "完整案例 95+"
    if score >= 85:
        return "合格案例 85-94"
    if score >= 60:
        return "待补全 60-84"
    return "低完整度 <60"


def _loads_string_list(raw: str | None) -> list[str]:
    if not raw:
        return []
    try:
        value = json.loads(raw)
    except json.JSONDecodeError:
        return []
    if not isinstance(value, list):
        return []
    return [str(item) for item in value if str(item).strip()]


def _attach_expression_tool_names(expression_tools: dict[str, dict[str, Any]], session: Session) -> None:
    if not expression_tools:
        return
    try:
        from backend.models.expression import ExpressionTool

        rows = session.exec(
            select(ExpressionTool).where(col(ExpressionTool.tool_uuid).in_(list(expression_tools)))
        ).all()
    except Exception:
        return
    for row in rows:
        item = expression_tools.get(row.tool_uuid)
        if item:
            item["name"] = row.name


def _expression_tool_filter_terms(raw: str, session: Session) -> list[str]:
    term = raw.strip()
    if not term:
        return []
    terms = [term]
    try:
        from backend.models.expression import ExpressionTool

        keyword = f"%{term}%"
        rows = session.exec(
            select(ExpressionTool).where(or_(
                col(ExpressionTool.tool_uuid).like(keyword),
                col(ExpressionTool.name).like(keyword),
                col(ExpressionTool.category).like(keyword),
            )).limit(20)
        ).all()
    except Exception:
        return terms
    for row in rows:
        if row.tool_uuid not in terms:
            terms.append(row.tool_uuid)
    return terms
