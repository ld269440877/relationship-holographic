"""
互动样本API路由
"""
import json
from datetime import datetime
from typing import Any, cast

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy.sql.elements import ColumnElement
from sqlmodel import Session, col, func, select

from backend.api.training import build_training_visual_map, persist_sample_multigranular_map
from backend.database.connection import get_session
from backend.models.sample import InteractionSample, SampleAnnotationVersion

router = APIRouter(prefix="/api/samples", tags=["样本"])


def _sql_column(value: Any) -> ColumnElement[Any]:
    return cast(ColumnElement[Any], value)


class SampleAnnotationBackfillRequest(BaseModel):
    limit: int = Field(default=100, ge=1, le=1000)
    force: bool = False


class GoldSampleBackfillRequest(BaseModel):
    target_count: int = Field(default=100, ge=1, le=500)
    force: bool = False


class GoldSampleReviewRequest(BaseModel):
    sample_id: int
    reviewer_id: str = Field(default="expert-default", min_length=2, max_length=80)
    decision: str = Field(default="approved", pattern="^(approved|needs_revision|rejected)$")
    confidence: float = Field(default=0.85, ge=0, le=1)
    notes: str | None = Field(default=None, max_length=1000)
    expected_scores: dict[str, float] = Field(default_factory=dict)
    safety: dict[str, object] = Field(default_factory=dict)


class GoldConflictResolveRequest(BaseModel):
    sample_ids: list[int] = Field(default_factory=list)
    limit: int = Field(default=20, ge=1, le=100)
    reviewer_id: str = Field(default="consensus-panel-v1", min_length=2, max_length=80)
    dry_run: bool = True


@router.get("")
def get_samples(
    scenario_category: str | None = None,
    difficulty_level: int | None = None,
    attachment_signal: str | None = None,
    limit: int = Query(default=20, le=100),
    offset: int = Query(default=0, ge=0),
    session: Session = Depends(get_session),
) -> dict:
    """获取互动样本列表"""
    query = select(InteractionSample)
    count_query = select(func.count()).select_from(InteractionSample)

    if scenario_category:
        query = query.where(InteractionSample.scenario_category == scenario_category)
        count_query = count_query.where(InteractionSample.scenario_category == scenario_category)
    if difficulty_level:
        query = query.where(InteractionSample.difficulty_level == difficulty_level)
        count_query = count_query.where(InteractionSample.difficulty_level == difficulty_level)
    if attachment_signal:
        query = query.where(InteractionSample.attachment_signal == attachment_signal)
        count_query = count_query.where(InteractionSample.attachment_signal == attachment_signal)

    query = query.offset(offset).limit(limit)
    results = session.exec(query).all()
    total = session.exec(count_query).one()
    return {"items": list(results), "total": total}


@router.post("/annotations/backfill")
def backfill_sample_annotations(
    request: SampleAnnotationBackfillRequest,
    session: Session = Depends(get_session),
) -> dict:
    """把历史样本升级为多粒度关系动力学标本。"""
    query = select(InteractionSample).limit(request.limit)
    if not request.force:
        query = query.where(InteractionSample.annotation_version == "legacy-v0")
    samples = session.exec(query).all()
    updated = 0
    for sample in samples:
        persist_sample_multigranular_map(sample)
        sample.updated_at = datetime.now()
        session.add(sample)
        updated += 1
    session.commit()
    return {
        "updated": updated,
        "annotation_version": "multigranular-v1",
        "fields": [
            "five_w_two_h_json",
            "signal_highlights_json",
            "emotion_flow_json",
            "feeling_tags_json",
            "need_radar_json",
            "boundary_state_json",
            "source_trace_json",
            "quality_json",
        ],
    }


@router.post("/gold/backfill")
def backfill_gold_samples(
    request: GoldSampleBackfillRequest,
    session: Session = Depends(get_session),
) -> dict:
    """为 Gold Set 校准搭建样本版本槽位，不复制或污染原始样本文本。"""
    samples = list(session.exec(select(InteractionSample).order_by(InteractionSample.id).limit(max(request.target_count, 1))).all())
    if not samples:
        return {"created_versions": 0, "updated_samples": 0, "target_count": request.target_count, "message": "no_samples"}

    created = 0
    updated_sample_ids: set[int] = set()
    for index in range(request.target_count):
        sample = samples[index % len(samples)]
        if sample.id is None:
            continue
        slot_version = f"gold-v1-slot-{index + 1:03d}"
        existing = session.exec(
            select(SampleAnnotationVersion)
            .where(SampleAnnotationVersion.sample_id == sample.id)
            .where(SampleAnnotationVersion.version == slot_version)
        ).first()
        if existing and not request.force:
            continue
        visual_map = persist_sample_multigranular_map(sample)
        gold_label = _gold_label_for_sample(sample, visual_map, slot_version)
        sample.gold_label_json = json.dumps(gold_label, ensure_ascii=False)
        sample.is_gold_sample = True
        sample.review_status = "gold"
        sample.updated_at = datetime.now()
        session.add(sample)
        version = existing or SampleAnnotationVersion(sample_id=sample.id, version=slot_version)
        version.annotator_type = "gold_scaffold"
        version.schema_version = "sample-gold-v1"
        version.tension_dimensions_json = sample.tension_dimensions_json
        version.source_trace_json = sample.source_trace_json
        version.quality_json = sample.quality_json
        version.safety_json = json.dumps(gold_label["safety"], ensure_ascii=False)
        version.gold_label_json = sample.gold_label_json
        version.review_status = "gold"
        version.is_gold = True
        session.add(version)
        created += 1
        updated_sample_ids.add(sample.id)
    session.commit()
    return {
        "target_count": request.target_count,
        "created_versions": created,
        "updated_samples": len(updated_sample_ids),
        "version_prefix": "gold-v1-slot",
        "principle": "Gold Set 是评分校准证据层；同一样本可有多个标注版本，但原始样本文本保持不变。",
    }


@router.get("/gold/summary")
def get_gold_summary(session: Session = Depends(get_session)) -> dict:
    """Gold Set 复核质量摘要，用于判断评分基准是否足够可信。"""
    samples = list(session.exec(select(InteractionSample).where(InteractionSample.is_gold_sample == True)).all())  # noqa: E712
    versions = list(session.exec(select(SampleAnnotationVersion).where(SampleAnnotationVersion.is_gold == True)).all())  # noqa: E712
    expert_versions = [item for item in versions if item.annotator_type in {"expert_review", "human_review"}]
    calibration_versions = [item for item in versions if item.annotator_type in {"expert_review", "human_review", "consensus_review"}]
    scaffold_versions = [item for item in versions if item.annotator_type == "gold_scaffold"]
    approved = [item for item in expert_versions if item.review_status == "approved"]
    needs_revision = [item for item in expert_versions if item.review_status == "needs_revision"]
    rejected = [item for item in expert_versions if item.review_status == "rejected"]
    confidence_values = [_loads_dict(item.quality_json).get("expert_confidence") for item in expert_versions]
    confidence = [float(item) for item in confidence_values if isinstance(item, int | float)]
    pending = max(0, len(samples) - len({item.sample_id for item in expert_versions}))
    coverage_rate = round((len(approved) / max(len(samples), 1)) * 100, 1) if samples else 0
    consistency = _gold_interrater_consistency(calibration_versions)
    return {
        "summary": {
            "gold_samples": len(samples),
            "annotation_versions": len(versions),
            "scaffold_versions": len(scaffold_versions),
            "expert_reviews": len(expert_versions),
            "approved": len(approved),
            "needs_revision": len(needs_revision),
            "rejected": len(rejected),
            "pending_review": pending,
            "expert_coverage_rate": coverage_rate,
            "average_confidence": round(sum(confidence) / len(confidence), 3) if confidence else 0,
            "interrater_consistency": consistency["summary"],
            "consensus_reviews": len([item for item in versions if item.annotator_type == "consensus_review"]),
        },
        "quality_gates": {
            "ready_for_strict_calibration": (
                coverage_rate >= 70
                and (sum(confidence) / len(confidence) if confidence else 0) >= 0.8
                and consistency["quality_gates"]["ready_for_multi_reviewer_calibration"]
            ),
            "minimum_expert_reviews": 30,
            "target_expert_coverage_rate": 70,
            "target_average_confidence": 0.8,
            "target_decision_agreement_rate": 0.8,
            "target_score_delta": 8,
        },
        "next_actions": _gold_next_actions(len(samples), len(expert_versions), pending, coverage_rate, confidence),
        "principle": "Gold Set 必须从脚手架进入专家复核；只有有信心、有安全门禁、有版本记录的样本，才适合作为评分基准。",
    }


@router.get("/gold/interrater")
def get_gold_interrater_consistency(
    sample_id: int | None = None,
    session: Session = Depends(get_session),
) -> dict:
    """计算 Gold Set 跨审阅者一致性，用于判断评分基准是否稳定。"""
    query = select(SampleAnnotationVersion).where(SampleAnnotationVersion.is_gold == True)  # noqa: E712
    if sample_id is not None:
        query = query.where(SampleAnnotationVersion.sample_id == sample_id)
    versions = list(session.exec(query).all())
    expert_versions = [item for item in versions if item.annotator_type in {"expert_review", "human_review", "consensus_review"}]
    report = _gold_interrater_consistency(expert_versions)
    report["sample_id"] = sample_id
    report["principle"] = "跨审阅者一致性比单次信心更重要；冲突样本必须先复议，再进入严格评分校准。"
    return report


@router.get("/gold/conflict-queue")
def get_gold_conflict_queue(limit: int = Query(default=20, ge=1, le=100), session: Session = Depends(get_session)) -> dict:
    """Return Gold Set samples that need calibration because reviewers disagree."""
    versions = list(session.exec(select(SampleAnnotationVersion).where(SampleAnnotationVersion.is_gold == True)).all())  # noqa: E712
    expert_versions = [item for item in versions if item.annotator_type in {"expert_review", "human_review", "consensus_review"}]
    grouped: dict[int, list[SampleAnnotationVersion]] = {}
    for version in expert_versions:
        grouped.setdefault(version.sample_id, []).append(version)
    sample_ids = [sample_id for sample_id, items in grouped.items() if len(_reviewer_ids(items)) >= 2]
    samples = {
        int(sample.id or 0): sample
        for sample in session.exec(select(InteractionSample).where(InteractionSample.id.in_(sample_ids))).all()  # type: ignore[attr-defined]
        if sample.id is not None
    } if sample_ids else {}
    items = [
        _gold_conflict_queue_item(sample_id, reviews, samples.get(sample_id))
        for sample_id, reviews in grouped.items()
        if len(_reviewer_ids(reviews)) >= 2
    ]
    conflicts = [item for item in items if item["priority"]["score"] > 0]
    conflicts.sort(key=lambda item: (-int(item["priority"]["score"]), int(item["sample_id"])))
    return {
        "items": conflicts[:limit],
        "total": len(conflicts),
        "quality_gates": {
            "ready_for_strict_calibration": len(conflicts) == 0,
            "target_open_conflicts": 0,
        },
        "next_actions": _gold_conflict_next_actions(conflicts),
        "principle": "Gold Set 冲突队列优先处理决策分歧、总分大幅偏差和低信心差异；复议只新增版本，不覆盖历史证据。",
    }


@router.post("/gold/conflicts/resolve")
def resolve_gold_conflicts(request: GoldConflictResolveRequest, session: Session = Depends(get_session)) -> dict:
    """Resolve open Gold Set conflicts by adding auditable consensus versions."""
    queue = get_gold_conflict_queue(limit=max(request.limit, len(request.sample_ids) or 1), session=session)
    selected = [
        item for item in queue["items"]
        if not request.sample_ids or int(item["sample_id"]) in set(request.sample_ids)
    ][:request.limit]
    if request.dry_run:
        return {
            "dry_run": True,
            "selected": selected,
            "would_create_versions": len(selected),
            "principle": "共识复议只基于既有专家版本生成 consensus_review 版本，不删除或覆盖历史分歧。",
        }
    created = []
    for item in selected:
        version = _create_consensus_review_version(int(item["sample_id"]), item, request.reviewer_id, session)
        if version:
            created.append(_version_card(version))
    session.commit()
    after = get_gold_conflict_queue(limit=request.limit, session=session)
    return {
        "dry_run": False,
        "created_versions": created,
        "resolved_count": len(created),
        "remaining_open_conflicts": after["total"],
        "principle": "已新增 consensus_review 版本并保留全部专家历史版本；共识不伪装成外部专家输入。",
    }


@router.get("/gold/review-queue")
def get_gold_review_queue(limit: int = Query(default=20, ge=1, le=100), session: Session = Depends(get_session)) -> dict:
    """返回优先级最高的 Gold Set 待复核样本。"""
    samples = list(session.exec(
        select(InteractionSample)
        .where(InteractionSample.is_gold_sample == True)  # noqa: E712
        .order_by(_sql_column(InteractionSample.updated_at).desc(), InteractionSample.id)
        .limit(max(limit * 20, 100))
    ).all())
    queue = []
    for sample in samples:
        if sample.id is None:
            continue
        latest_review = _latest_expert_review(sample.id, session)
        if latest_review and latest_review.review_status == "approved":
            continue
        visual_map = build_training_visual_map(sample)
        gold_label = _loads_dict(sample.gold_label_json)
        queue.append({
            "sample": _gold_sample_card(sample),
            "gold_label": gold_label,
            "visual_map": {
                "emotion_thermometer": visual_map.get("emotion_thermometer", {}),
                "need_radar": visual_map.get("need_radar", []),
                "boundary_band": visual_map.get("boundary_band", {}),
                "tension_dimensions": visual_map.get("tension_dimensions", []),
            },
            "latest_review": _version_card(latest_review) if latest_review else None,
            "review_priority": _gold_review_priority(sample, latest_review),
        })
        if len(queue) >= limit:
            break
    return {
        "items": queue,
        "total": len(queue),
        "principle": "复核优先处理高难度、高边界压力、缺专家版本或上次需要修订的样本。",
    }


@router.post("/gold/reviews")
def submit_gold_review(request: GoldSampleReviewRequest, session: Session = Depends(get_session)) -> dict:
    """提交 Gold Set 专家复核，生成独立版本并同步样本校准标签。"""
    sample = session.exec(select(InteractionSample).where(InteractionSample.id == request.sample_id)).first()
    if not sample:
        raise HTTPException(status_code=404, detail="样本不存在")
    visual_map = persist_sample_multigranular_map(sample)
    previous = _loads_dict(sample.gold_label_json) or _gold_label_for_sample(sample, visual_map, "gold-v1")
    expected_scores = _merge_expected_scores(previous.get("expected_scores"), request.expected_scores)
    version_name = f"gold-review-{datetime.now().strftime('%Y%m%d%H%M%S')}-{sample.id}"
    gold_label = {
        **previous,
        "version": version_name,
        "ideal_response": sample.good_response_soft,
        "expected_scores": expected_scores,
        "expert_review": {
            "reviewer_id": request.reviewer_id,
            "decision": request.decision,
            "confidence": request.confidence,
            "notes": request.notes,
            "reviewed_at": datetime.now().isoformat(timespec="seconds"),
        },
        "safety": {
            **(previous.get("safety") if isinstance(previous.get("safety"), dict) else {}),
            "review_status": request.decision,
            "manipulation_allowed": False,
            "raw_private_text_allowed": False,
            **request.safety,
        },
    }
    quality = _loads_dict(sample.quality_json)
    quality.update({
        "expert_confidence": request.confidence,
        "expert_decision": request.decision,
        "reviewer_id": request.reviewer_id,
        "reviewed_at": datetime.now().isoformat(timespec="seconds"),
    })
    version = SampleAnnotationVersion(
        sample_id=sample.id or 0,
        version=version_name,
        annotator_type="expert_review",
        schema_version="sample-gold-review-v1",
        tension_dimensions_json=sample.tension_dimensions_json,
        source_trace_json=sample.source_trace_json,
        quality_json=json.dumps(quality, ensure_ascii=False),
        safety_json=json.dumps(gold_label["safety"], ensure_ascii=False),
        gold_label_json=json.dumps(gold_label, ensure_ascii=False),
        review_status=request.decision,
        is_gold=True,
    )
    sample.gold_label_json = json.dumps(gold_label, ensure_ascii=False)
    sample.quality_json = json.dumps(quality, ensure_ascii=False)
    sample.is_gold_sample = request.decision != "rejected"
    sample.review_status = "gold" if request.decision == "approved" else request.decision
    sample.updated_at = datetime.now()
    session.add(sample)
    session.add(version)
    session.commit()
    session.refresh(version)
    session.refresh(sample)
    return {
        "ok": True,
        "sample_id": sample.id,
        "version": _version_card(version),
        "sample_review_status": sample.review_status,
        "principle": "专家复核不覆盖历史脚手架，而是新增可审计版本；训练评分读取最新 gold_label 进行校准。",
    }


@router.get("/random", response_model=InteractionSample | None)
def get_random_sample(
    scenario_category: str | None = None,
    difficulty_level: int | None = None,
    session: Session = Depends(get_session),
) -> InteractionSample | None:
    """随机获取一个样本用于训练"""
    query = select(InteractionSample).where(col(InteractionSample.review_status).in_(("reviewed", "published", "gold")))

    if scenario_category:
        query = query.where(InteractionSample.scenario_category == scenario_category)
    if difficulty_level:
        query = query.where(InteractionSample.difficulty_level == difficulty_level)

    # SQLite 不同部署随机函数差异较多，这里用 Python 随机保持可移植。
    results = session.exec(query).all()
    if results:
        import random
        return random.choice(list(results))
    return None


@router.get("/categories")
def get_categories() -> list[str]:
    """获取所有场景分类"""
    return ["初识", "暧昧", "热恋", "冲突", "平淡", "修复"]


@router.get("/attachments")
def get_attachments() -> list[str]:
    """获取所有依恋类型"""
    return ["安全型", "焦虑型", "回避型", "恐惧-回避型"]


@router.get("/{sample_id}", response_model=InteractionSample)
def get_sample(
    sample_id: int,
    session: Session = Depends(get_session),
) -> InteractionSample:
    """获取单个样本详情"""
    result = session.exec(
        select(InteractionSample).where(InteractionSample.id == sample_id)
    ).first()

    if not result:
        raise HTTPException(status_code=404, detail="样本不存在")

    return result


@router.get("/{sample_id}/annotation-map")
def get_sample_annotation_map(
    sample_id: int,
    session: Session = Depends(get_session),
) -> dict:
    """获取样本的多粒度标注地图。"""
    sample = session.exec(
        select(InteractionSample).where(InteractionSample.id == sample_id)
    ).first()
    if not sample:
        raise HTTPException(status_code=404, detail="样本不存在")
    if sample.annotation_version == "legacy-v0":
        persist_sample_multigranular_map(sample)
        session.add(sample)
        session.commit()
        session.refresh(sample)
    return build_training_visual_map(sample)


def _gold_label_for_sample(sample: InteractionSample, visual_map: dict, version: str) -> dict:
    quality = visual_map.get("quality") or {}
    safety_score = float(quality.get("safety_score", 0.9))
    expected_total = round(74 + safety_score * 12 + min(sample.difficulty_level, 3) * 2, 1)
    return {
        "version": version,
        "ideal_response": sample.good_response_soft,
        "expected_scores": {
            "total_score": expected_total,
            "emotion_score": 78,
            "need_score": 78,
            "safety_score": round(safety_score * 100, 1),
            "connection_score": 76,
            "boundary_score": 80 if (sample.boundary_test_level or 1) <= 7 else 68,
            "style_score": 74,
            "repair_score": 72,
        },
        "tension_dimensions": visual_map.get("tension_dimensions", []),
        "source_trace": visual_map.get("source_trace", {}),
        "quality": quality,
        "safety": {
            "review_status": "gold",
            "manipulation_allowed": False,
            "raw_private_text_allowed": False,
            "safety_score": safety_score,
        },
    }


def _latest_expert_review(sample_id: int, session: Session) -> SampleAnnotationVersion | None:
    return session.exec(
        select(SampleAnnotationVersion)
        .where(SampleAnnotationVersion.sample_id == sample_id)
        .where(SampleAnnotationVersion.annotator_type.in_(["expert_review", "human_review"]))  # type: ignore[attr-defined]
        .order_by(_sql_column(SampleAnnotationVersion.created_at).desc())
    ).first()


def _merge_expected_scores(existing: object, updates: dict[str, float]) -> dict[str, float]:
    base = existing if isinstance(existing, dict) else {}
    keys = [
        "total_score",
        "emotion_score",
        "need_score",
        "safety_score",
        "connection_score",
        "boundary_score",
        "style_score",
        "repair_score",
    ]
    merged: dict[str, float] = {}
    for key in keys:
        value = updates.get(key, base.get(key, 75) if isinstance(base, dict) else 75)
        merged[key] = round(max(0, min(100, float(value))), 1)
    return merged


def _gold_sample_card(sample: InteractionSample) -> dict:
    return {
        "id": sample.id,
        "sample_uuid": sample.sample_uuid,
        "scenario_category": sample.scenario_category,
        "difficulty_level": sample.difficulty_level,
        "context": sample.context,
        "their_words": sample.their_words,
        "hidden_need": sample.hidden_need,
        "attachment_signal": sample.attachment_signal,
        "boundary_test_level": sample.boundary_test_level,
        "good_response_soft": sample.good_response_soft,
        "review_status": sample.review_status,
        "updated_at": sample.updated_at.isoformat(),
    }


def _version_card(version: SampleAnnotationVersion | None) -> dict | None:
    if version is None:
        return None
    quality = _loads_dict(version.quality_json)
    return {
        "id": version.id,
        "sample_id": version.sample_id,
        "version": version.version,
        "annotator_type": version.annotator_type,
        "schema_version": version.schema_version,
        "review_status": version.review_status,
        "is_gold": version.is_gold,
        "expert_confidence": quality.get("expert_confidence"),
        "expert_decision": quality.get("expert_decision"),
        "created_at": version.created_at.isoformat(),
    }


def _gold_review_priority(sample: InteractionSample, latest_review: SampleAnnotationVersion | None) -> dict:
    boundary = sample.boundary_test_level or 1
    score = sample.difficulty_level * 15 + boundary * 4
    reasons = []
    if latest_review is None:
        score += 30
        reasons.append("缺专家复核")
    elif latest_review.review_status == "needs_revision":
        score += 20
        reasons.append("上次需要修订")
    if boundary >= 7:
        reasons.append("高边界压力")
    if sample.difficulty_level >= 3:
        reasons.append("高难度")
    return {"score": min(100, score), "reasons": reasons or ["常规抽检"]}


def _gold_interrater_consistency(versions: list[SampleAnnotationVersion]) -> dict:
    grouped: dict[int, list[SampleAnnotationVersion]] = {}
    for version in versions:
        grouped.setdefault(version.sample_id, []).append(version)

    resolved_samples = {sample_id for sample_id, items in grouped.items() if _latest_consensus_review(items)}
    expert_grouped = {
        sample_id: [item for item in items if item.annotator_type in {"expert_review", "human_review"}]
        for sample_id, items in grouped.items()
    }
    multi_reviewer_samples = {
        sample_id: items
        for sample_id, items in expert_grouped.items()
        if sample_id not in resolved_samples and len(_reviewer_ids(items)) >= 2
    }
    comparable_pairs = 0
    decision_agreements = 0
    total_score_delta = 0.0
    confidence_delta = 0.0
    conflicts: list[dict] = []

    for sample_id, items in multi_reviewer_samples.items():
        newest_by_reviewer = _latest_review_by_reviewer(items)
        pair_metrics = _pairwise_review_metrics(list(newest_by_reviewer.values()))
        comparable_pairs += pair_metrics["pairs"]
        decision_agreements += pair_metrics["decision_agreements"]
        total_score_delta += pair_metrics["total_score_delta"]
        confidence_delta += pair_metrics["confidence_delta"]
        if pair_metrics["has_conflict"]:
            conflicts.append({
                "sample_id": sample_id,
                "reviewers": sorted(newest_by_reviewer),
                "decisions": sorted({review.review_status for review in newest_by_reviewer.values()}),
                "max_total_score_delta": round(pair_metrics["max_total_score_delta"], 1),
                "recommendation": "复议冲突样本，统一评分锚点后再进入严格校准。",
            })

    decision_rate = round(decision_agreements / comparable_pairs, 3) if comparable_pairs else 0.0
    average_score_delta = round(total_score_delta / comparable_pairs, 2) if comparable_pairs else 0.0
    average_confidence_delta = round(confidence_delta / comparable_pairs, 3) if comparable_pairs else 0.0
    return {
        "summary": {
            "expert_reviews": sum(1 for item in versions if item.annotator_type in {"expert_review", "human_review"}),
            "consensus_reviews": sum(1 for item in versions if item.annotator_type == "consensus_review"),
            "reviewed_samples": len(grouped),
            "multi_reviewer_samples": len(multi_reviewer_samples),
            "comparable_pairs": comparable_pairs,
            "decision_agreement_rate": decision_rate,
            "average_total_score_delta": average_score_delta,
            "average_confidence_delta": average_confidence_delta,
            "conflict_samples": len(conflicts),
            "resolved_conflict_samples": len(resolved_samples),
        },
        "quality_gates": {
            "ready_for_multi_reviewer_calibration": comparable_pairs >= 3 and decision_rate >= 0.8 and average_score_delta <= 8 and not conflicts,
            "minimum_comparable_pairs": 3,
            "target_decision_agreement_rate": 0.8,
            "target_average_total_score_delta": 8,
        },
        "conflicts": conflicts[:20],
        "next_actions": _interrater_next_actions(comparable_pairs, decision_rate, average_score_delta, conflicts),
    }


def _gold_conflict_queue_item(
    sample_id: int,
    reviews: list[SampleAnnotationVersion],
    sample: InteractionSample | None,
) -> dict:
    if _latest_consensus_review(reviews):
        return {
            "sample_id": sample_id,
            "sample": _gold_sample_card(sample) if sample else None,
            "reviewers": [],
            "decisions": [],
            "pair_count": 0,
            "decision_agreement_rate": 1,
            "max_total_score_delta": 0,
            "average_total_score_delta": 0,
            "average_confidence_delta": 0,
            "latest_reviews": [],
            "priority": {"score": 0, "reasons": ["已有共识复议版本"]},
            "recommended_action": "已关闭开放冲突，历史专家分歧保留为审计证据。",
        }
    newest = _latest_review_by_reviewer(reviews)
    latest_reviews = list(newest.values())
    metrics = _pairwise_review_metrics(latest_reviews)
    decisions = sorted({review.review_status for review in latest_reviews})
    score = _gold_conflict_priority(metrics, decisions)
    return {
        "sample_id": sample_id,
        "sample": _gold_sample_card(sample) if sample else None,
        "reviewers": sorted(newest),
        "decisions": decisions,
        "pair_count": metrics["pairs"],
        "decision_agreement_rate": round(metrics["decision_agreements"] / metrics["pairs"], 3) if metrics["pairs"] else 0,
        "max_total_score_delta": round(metrics["max_total_score_delta"], 1),
        "average_total_score_delta": round(metrics["total_score_delta"] / metrics["pairs"], 1) if metrics["pairs"] else 0,
        "average_confidence_delta": round(metrics["confidence_delta"] / metrics["pairs"], 3) if metrics["pairs"] else 0,
        "latest_reviews": [_gold_conflict_review_card(review) for review in latest_reviews],
        "priority": {
            "score": score,
            "reasons": _gold_conflict_reasons(metrics, decisions),
        },
        "recommended_action": "召集复议，先统一评分锚点与安全边界，再新增 consensus reviewer 版本。",
    }


def _gold_conflict_priority(metrics: dict, decisions: list[str]) -> int:
    if not metrics["has_conflict"]:
        return 0
    score = 35
    if len(decisions) > 1:
        score += 35
    score += min(25, int(metrics["max_total_score_delta"]))
    if metrics["confidence_delta"] > 0.2:
        score += 5
    return min(100, score)


def _gold_conflict_reasons(metrics: dict, decisions: list[str]) -> list[str]:
    reasons: list[str] = []
    if len(decisions) > 1:
        reasons.append("决策分歧")
    if metrics["max_total_score_delta"] > 12:
        reasons.append("总分差超过 12")
    if metrics["confidence_delta"] > 0.2:
        reasons.append("信心差较大")
    return reasons or ["轻微评分偏差"]


def _gold_conflict_review_card(version: SampleAnnotationVersion) -> dict:
    quality = _loads_dict(version.quality_json)
    return {
        "version": version.version,
        "reviewer_id": str(quality.get("reviewer_id") or version.annotator_type),
        "decision": version.review_status,
        "total_score": _review_total_score(version),
        "confidence": _review_confidence(version),
        "created_at": version.created_at.isoformat(),
    }


def _gold_conflict_next_actions(conflicts: list[dict]) -> list[dict[str, str]]:
    if not conflicts:
        return [{"priority": "low", "action": "进入严格校准候选", "reason": "当前没有开放 Gold Set 冲突样本。"}]
    high = sum(1 for item in conflicts if int(item["priority"]["score"]) >= 80)
    actions = [{"priority": "high", "action": "复议 Gold Set 冲突队列", "reason": f"当前 {len(conflicts)} 个样本存在多审冲突。"}]
    if high:
        actions.append({"priority": "high", "action": "优先处理高危分歧", "reason": f"{high} 个冲突样本优先级超过 80。"})
    actions.append({"priority": "medium", "action": "补 consensus reviewer 版本", "reason": "复议完成后新增共识版本，保留全部历史审阅证据。"})
    return actions[:4]


def _create_consensus_review_version(
    sample_id: int,
    conflict_item: dict,
    reviewer_id: str,
    session: Session,
) -> SampleAnnotationVersion | None:
    sample = session.exec(select(InteractionSample).where(InteractionSample.id == sample_id)).first()
    if not sample:
        return None
    reviews = list(session.exec(
        select(SampleAnnotationVersion)
        .where(SampleAnnotationVersion.sample_id == sample_id)
        .where(SampleAnnotationVersion.is_gold == True)  # noqa: E712
    ).all())
    if _latest_consensus_review(reviews):
        return None
    source_reviews = [review for review in reviews if review.annotator_type in {"expert_review", "human_review"}]
    if not source_reviews:
        return None
    total_scores = [_review_total_score(review) for review in source_reviews]
    confidence = min(0.95, max(0.72, sum(_review_confidence(review) for review in source_reviews) / max(len(source_reviews), 1)))
    consensus_score = round(sum(total_scores) / max(len(total_scores), 1), 1)
    approved_votes = sum(1 for review in source_reviews if review.review_status == "approved")
    decision = "approved" if approved_votes >= max(1, len(source_reviews) / 2) else "needs_revision"
    previous = _loads_dict(sample.gold_label_json)
    expected_scores = _merge_expected_scores(previous.get("expected_scores"), {"total_score": consensus_score})
    version_name = f"gold-consensus-{datetime.now().strftime('%Y%m%d%H%M%S')}-{sample_id}"
    consensus_label = {
        **previous,
        "version": version_name,
        "expected_scores": expected_scores,
        "consensus_review": {
            "reviewer_id": reviewer_id,
            "decision": decision,
            "confidence": round(confidence, 3),
            "source_review_count": len(source_reviews),
            "resolved_conflict": True,
            "resolved_at": datetime.now().isoformat(timespec="seconds"),
            "conflict_priority": conflict_item.get("priority", {}),
        },
        "safety": {
            **(previous.get("safety") if isinstance(previous.get("safety"), dict) else {}),
            "review_status": decision,
            "manipulation_allowed": False,
            "raw_private_text_allowed": False,
            "consensus_reviewed": True,
        },
    }
    quality = _loads_dict(sample.quality_json)
    quality.update({
        "expert_confidence": round(confidence, 3),
        "expert_decision": decision,
        "reviewer_id": reviewer_id,
        "reviewed_at": datetime.now().isoformat(timespec="seconds"),
        "consensus_review": True,
        "source_review_count": len(source_reviews),
    })
    version = SampleAnnotationVersion(
        sample_id=sample_id,
        version=version_name,
        annotator_type="consensus_review",
        schema_version="sample-gold-consensus-v1",
        tension_dimensions_json=sample.tension_dimensions_json,
        source_trace_json=sample.source_trace_json,
        quality_json=json.dumps(quality, ensure_ascii=False),
        safety_json=json.dumps(consensus_label["safety"], ensure_ascii=False),
        gold_label_json=json.dumps(consensus_label, ensure_ascii=False),
        review_status=decision,
        is_gold=True,
    )
    sample.gold_label_json = json.dumps(consensus_label, ensure_ascii=False)
    sample.quality_json = json.dumps(quality, ensure_ascii=False)
    sample.is_gold_sample = decision != "rejected"
    sample.review_status = "gold" if decision == "approved" else decision
    sample.updated_at = datetime.now()
    session.add(sample)
    session.add(version)
    session.flush()
    return version


def _reviewer_ids(versions: list[SampleAnnotationVersion]) -> set[str]:
    reviewers: set[str] = set()
    for version in versions:
        reviewer = _loads_dict(version.quality_json).get("reviewer_id")
        reviewers.add(str(reviewer or version.annotator_type))
    return reviewers


def _latest_consensus_review(versions: list[SampleAnnotationVersion]) -> SampleAnnotationVersion | None:
    consensus = [version for version in versions if version.annotator_type == "consensus_review"]
    return sorted(consensus, key=lambda item: item.created_at)[-1] if consensus else None


def _latest_review_by_reviewer(versions: list[SampleAnnotationVersion]) -> dict[str, SampleAnnotationVersion]:
    newest: dict[str, SampleAnnotationVersion] = {}
    for version in sorted([item for item in versions if item.annotator_type != "consensus_review"], key=lambda item: item.created_at):
        reviewer = str(_loads_dict(version.quality_json).get("reviewer_id") or version.annotator_type)
        newest[reviewer] = version
    return newest


def _pairwise_review_metrics(versions: list[SampleAnnotationVersion]) -> dict:
    pairs = 0
    agreements = 0
    total_score_delta = 0.0
    confidence_delta = 0.0
    max_score_delta = 0.0
    has_conflict = False
    for left_index, left in enumerate(versions):
        for right in versions[left_index + 1:]:
            pairs += 1
            if left.review_status == right.review_status:
                agreements += 1
            else:
                has_conflict = True
            left_score = _review_total_score(left)
            right_score = _review_total_score(right)
            score_delta = abs(left_score - right_score)
            total_score_delta += score_delta
            max_score_delta = max(max_score_delta, score_delta)
            confidence_delta += abs(_review_confidence(left) - _review_confidence(right))
            if score_delta > 12:
                has_conflict = True
    return {
        "pairs": pairs,
        "decision_agreements": agreements,
        "total_score_delta": total_score_delta,
        "confidence_delta": confidence_delta,
        "max_total_score_delta": max_score_delta,
        "has_conflict": has_conflict,
    }


def _review_total_score(version: SampleAnnotationVersion) -> float:
    gold_label = _loads_dict(version.gold_label_json)
    expected = gold_label.get("expected_scores") if isinstance(gold_label.get("expected_scores"), dict) else {}
    value = expected.get("total_score", 75) if isinstance(expected, dict) else 75
    return float(value)


def _review_confidence(version: SampleAnnotationVersion) -> float:
    confidence = _loads_dict(version.quality_json).get("expert_confidence", 0)
    return float(confidence) if isinstance(confidence, int | float) else 0.0


def _interrater_next_actions(
    comparable_pairs: int,
    decision_rate: float,
    average_score_delta: float,
    conflicts: list[dict],
) -> list[dict[str, str]]:
    actions: list[dict[str, str]] = []
    if comparable_pairs < 3:
        actions.append({"priority": "high", "action": "增加双审样本", "reason": f"当前只有 {comparable_pairs} 组可比较审阅对，至少需要 3 组。"})
    if decision_rate and decision_rate < 0.8:
        actions.append({"priority": "high", "action": "复议决策分歧", "reason": f"当前决策一致率 {decision_rate:.2f}，低于 0.80。"})
    if average_score_delta > 8:
        actions.append({"priority": "medium", "action": "校准评分锚点", "reason": f"总分平均差 {average_score_delta:.1f}，高于 8 分阈值。"})
    if conflicts:
        actions.append({"priority": "medium", "action": "处理冲突样本", "reason": f"{len(conflicts)} 个样本存在决策或分数冲突。"})
    if not actions:
        actions.append({"priority": "low", "action": "进入多审阅者校准", "reason": "决策一致率和分数差已达到多审阅者门禁。"})
    return actions[:4]


def _gold_next_actions(
    gold_samples: int,
    expert_reviews: int,
    pending: int,
    coverage_rate: float,
    confidence: list[float],
) -> list[dict[str, str]]:
    actions: list[dict[str, str]] = []
    avg_confidence = sum(confidence) / len(confidence) if confidence else 0
    if gold_samples < 100:
        actions.append({"priority": "high", "action": "扩充 Gold Set 脚手架", "reason": f"当前 Gold 样本 {gold_samples} 条，目标至少 100 条。"})
    if pending:
        actions.append({"priority": "high", "action": "推进专家复核队列", "reason": f"仍有 {pending} 条 Gold 样本缺专家版本。"})
    if coverage_rate < 70:
        actions.append({"priority": "medium", "action": "提高专家覆盖率", "reason": f"当前专家覆盖率 {coverage_rate}%，目标 70%。"})
    if avg_confidence and avg_confidence < 0.8:
        actions.append({"priority": "medium", "action": "复核低信心标注", "reason": f"平均信心 {avg_confidence:.2f}，低于 0.80。"})
    if not actions:
        actions.append({"priority": "low", "action": "进入严格校准", "reason": "Gold Set 专家覆盖和信心达到严格校准阈值。"})
    return actions[:4]


def _loads_dict(raw: str | None) -> dict:
    if not raw:
        return {}
    try:
        value = json.loads(raw)
    except json.JSONDecodeError:
        return {}
    return value if isinstance(value, dict) else {}
