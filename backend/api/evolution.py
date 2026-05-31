"""系统进化中心 API。"""
import hashlib
import json
from datetime import datetime
from urllib.parse import urlparse

import httpx
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlmodel import Session, desc, select

from backend.core.evolution_intelligence import (
    RawDedupeCandidate,
    SafetyEventSnapshot,
    semantic_tokens,
)
from backend.core.evolution_intelligence import (
    build_dedupe_report as build_typed_dedupe_report,
)
from backend.core.evolution_intelligence import (
    build_safety_events_report as build_typed_safety_events_report,
)
from backend.core.evolution_intelligence import (
    loads_dict as typed_loads_dict,
)
from backend.core.evolution_intelligence import (
    loads_list as typed_loads_list,
)
from backend.core.evolution_intelligence import (
    scheduler_next_actions as typed_scheduler_next_actions,
)
from backend.core.vector_index import (
    evaluate_vector_recall,
    metadata_vector_index_report,
    rebuild_metadata_vector_index,
    search_metadata_vectors,
)
from backend.database.connection import get_session
from backend.models.evolution import (
    AnnotationJob,
    EvolutionItem,
    EvolutionReport,
    EvolutionSource,
    PipelineRunLog,
    RawContentItem,
    SourceRegistry,
    TrainingAssetVersion,
)
from backend.models.knowledge import ContentImportBatch, ContentImportIssue, KnowledgeEntry
from backend.models.resource import ResourceLibrary
from backend.models.sample import InteractionSample
from backend.models.training import SafetyEvent

router = APIRouter(prefix="/api/evolution", tags=["系统进化"])


class EvolutionItemCreate(BaseModel):
    title: str
    content: str
    category: str = "research"
    summary: str | None = None
    tags: list[str] = []
    source_name: str = "manual"
    source_type: str = "manual"
    source_url: str | None = None
    quality_score: float = 70
    status: str = "published"


class SourceRegistryCreate(BaseModel):
    source_uuid: str | None = None
    name: str
    source_type: str = "manual"
    url: str | None = None
    trust_score: float = 0.8
    update_frequency: str = "weekly"
    allowed_use: list[str] = ["summary", "metadata", "derived_training_pattern"]
    disallowed_use: list[str] = ["full_text_republication", "identifiable_private_dialogue"]
    active: bool = True


class RawContentCreate(BaseModel):
    raw_uuid: str | None = None
    source_id: int | None = None
    title: str | None = None
    url: str | None = None
    content: str | None = None
    raw_storage_policy: str = "metadata_only"
    privacy_risk: float = 0.0
    copyright_risk: float = 0.0
    consent_status: str = "public_summary_allowed"
    processing_status: str = "raw"


class AnnotationJobCreate(BaseModel):
    target_type: str
    target_id: int
    annotator_type: str = "ai"
    annotator_version: str | None = None
    schema_version: str = "relationship-primitives-v1"
    result: dict = {}
    confidence: float = 0.0
    status: str = "draft"


class TrainingAssetVersionCreate(BaseModel):
    asset_type: str
    asset_id: int
    version: str
    source_trace: dict = {}
    quality: dict = {}
    review_status: str = "draft"


class PipelineAdvanceRequest(BaseModel):
    target_type: str = "raw_content"
    target_id: int
    action: str
    result: dict = {}
    message: str | None = None


class PipelineBatchRunRequest(BaseModel):
    limit: int = Field(default=20, ge=1, le=100)
    actions: list[str] = Field(default_factory=lambda: ["sanitize", "dedupe", "annotate", "publish", "report"])
    raw_ids: list[int] = Field(default_factory=list)
    dry_run: bool = False
    duplicate_policy: str = "skip_annotate"
    min_confidence: float = Field(default=0.72, ge=0, le=1)
    publish_review_status: str = "published"
    report_period_type: str = "daily"
    promote_reviewed_assets: bool = True


class ScheduledEvolutionRunRequest(BaseModel):
    period_type: str = "weekly"
    lookback_days: int = Field(default=7, ge=1, le=90)
    batch_limit: int = Field(default=50, ge=1, le=200)
    dry_run: bool = False
    duplicate_policy: str = "skip_annotate"
    min_confidence: float = Field(default=0.74, ge=0, le=1)


class SourceFetchRequest(BaseModel):
    source_ids: list[int] = Field(default_factory=list)
    limit_per_source: int = Field(default=3, ge=1, le=10)
    dry_run: bool = True
    timeout_seconds: float = Field(default=5.0, ge=1.0, le=20.0)


class VectorIndexRebuildRequest(BaseModel):
    target_types: list[str] | None = None
    limit_per_type: int = Field(default=500, ge=1, le=5000)


class VectorSearchRequest(BaseModel):
    query: str = Field(min_length=1, max_length=500)
    target_type: str | None = None
    limit: int = Field(default=10, ge=1, le=50)
    threshold: float = Field(default=0.35, ge=-1, le=1)


class VectorRecallEvaluationRequest(BaseModel):
    limit_per_type: int = Field(default=8, ge=1, le=50)
    thresholds: list[float] | None = None


class ReviewedAssetBackfillRequest(BaseModel):
    limit: int = Field(default=200, ge=1, le=1000)
    force: bool = False


class ReviewedAssetActionRequest(BaseModel):
    asset_type: str = Field(pattern="^(resource|knowledge_entry)$")
    asset_id: int
    action: str = Field(pattern="^(confirm_publish|withdraw|request_review)$")
    reviewer_id: str = Field(default="governance-console", min_length=2, max_length=80)
    reason: str | None = Field(default=None, max_length=500)
    dry_run: bool = True


class ReviewedAssetAutoReviewRequest(BaseModel):
    limit: int = Field(default=50, ge=1, le=200)
    reviewer_id: str = Field(default="auto-review-governance", min_length=2, max_length=80)
    min_priority_score: int = Field(default=85, ge=0, le=100)
    publish_ready_assets: bool = True
    request_review_blocked_assets: bool = False
    dry_run: bool = True


class BoutiqueResourceBatchRequest(BaseModel):
    limit: int = Field(default=8, ge=1, le=24)
    reviewer_id: str = Field(default="boutique-curator", min_length=2, max_length=80)
    dry_run: bool = True


class ImportQualityRepairRequest(BaseModel):
    limit: int = Field(default=100, ge=1, le=1000)
    dry_run: bool = True


class ImportIssueActionRequest(BaseModel):
    issue_ids: list[int] = Field(min_length=1, max_length=100)
    action: str = Field(pattern="^(resolve|request_review|reopen)$")
    reviewer_id: str = Field(default="import-governance", min_length=2, max_length=80)
    resolution: str | None = Field(default=None, min_length=4, max_length=500)
    dry_run: bool = True


class BatchRollbackPlanRequest(BaseModel):
    batch_id: int
    include_logs: bool = True
    dry_run: bool = True


@router.get("/latest")
def latest(session: Session = Depends(get_session)) -> dict:
    """获取进化中心最新数据。"""
    items = session.exec(
        select(EvolutionItem)
        .where(EvolutionItem.status == "published")
        .order_by(desc(EvolutionItem.created_at))
        .limit(10)
    ).all()
    report = session.exec(
        select(EvolutionReport).order_by(desc(EvolutionReport.created_at)).limit(1)
    ).first()
    return {
        "items": [_item_to_dict(item) for item in items],
        "latest_report": _report_to_dict(report) if report else None,
        "summary": build_pipeline_summary(session),
        "principle": "SQLite 是唯一真数据源；API 是唯一数据出口；JSON 仅作为历史导入源。",
    }


@router.get("/summary")
def summary(session: Session = Depends(get_session)) -> dict:
    """获取进化流水线生命体状态。"""
    return build_pipeline_summary(session)


@router.get("/pipeline")
def pipeline(session: Session = Depends(get_session)) -> dict:
    """获取从源数据到训练资产的全链路进化流水线。"""
    sources = session.exec(select(SourceRegistry).order_by(desc(SourceRegistry.created_at)).limit(100)).all()
    raw_items = session.exec(select(RawContentItem).order_by(desc(RawContentItem.collected_at)).limit(100)).all()
    jobs = session.exec(select(AnnotationJob).order_by(desc(AnnotationJob.created_at)).limit(100)).all()
    assets = session.exec(select(TrainingAssetVersion).order_by(desc(TrainingAssetVersion.created_at)).limit(100)).all()
    samples = session.exec(select(InteractionSample).order_by(desc(InteractionSample.updated_at), desc(InteractionSample.id)).limit(120)).all()
    resources = session.exec(select(ResourceLibrary).order_by(desc(ResourceLibrary.created_at), desc(ResourceLibrary.id)).limit(120)).all()
    knowledge_entries = session.exec(select(KnowledgeEntry).order_by(desc(KnowledgeEntry.updated_at), desc(KnowledgeEntry.id)).limit(120)).all()
    logs = session.exec(select(PipelineRunLog).order_by(desc(PipelineRunLog.created_at)).limit(50)).all()

    return {
        "principle": "源数据只做合规登记和可追踪抽象；训练资产必须经过隐私、版权、安全、质量四重门。",
        "stages": [
            {"id": "source_registry", "name": "来源登记", "count": len(sources), "risk_gate": "许可/可信度/更新频率"},
            {"id": "raw_candidate", "name": "候选元数据", "count": len(raw_items), "risk_gate": "PII/版权/重复"},
            {"id": "annotation", "name": "关系元标注", "count": len(jobs), "risk_gate": "置信度/安全边界"},
            {"id": "asset_version", "name": "训练资产版本", "count": len(assets), "risk_gate": "回归测试/人工抽检"},
            {"id": "published_training", "name": "发布到训练", "count": _count_published_assets(assets), "risk_gate": "可解释评分/可撤回"},
        ],
        "classification_axes": [
            "source_type",
            "privacy_risk",
            "copyright_risk",
            "processing_status",
            "schema_version",
            "review_status",
            "asset_type",
        ],
        "status_counts": {
            "raw": _count_by(raw_items, "processing_status"),
            "annotation": _count_by(jobs, "status"),
            "assets": _count_by(assets, "review_status"),
            "samples": _count_by(samples, "review_status"),
            "resources": _count_by(resources, "review_status"),
            "knowledge": _count_by(knowledge_entries, "review_status"),
        },
        "sources": [_source_registry_to_dict(source) for source in sources[:20]],
        "raw_items": [_raw_item_to_dict(item) for item in raw_items[:20]],
        "annotation_jobs": [_annotation_job_to_dict(job) for job in jobs[:20]],
        "asset_versions": [_asset_version_to_dict(asset) for asset in assets[:20]],
        "reviewed_assets": _reviewed_asset_inventory(samples, resources, knowledge_entries),
        "recent_logs": [_pipeline_log_to_dict(log) for log in logs[:20]],
        "visual_metrics": _build_evolution_visual_metrics(sources, raw_items, jobs, assets, logs),
        "next_actions": _pipeline_metadata_actions(sources, raw_items, jobs, assets, samples, resources, knowledge_entries),
    }


@router.post("/sources")
def create_source_registry(data: SourceRegistryCreate, session: Session = Depends(get_session)) -> dict:
    """登记一个合规内容来源。"""
    source_uuid = data.source_uuid or _slug_uuid("source", data.name, data.url or data.source_type)
    existing = session.exec(select(SourceRegistry).where(SourceRegistry.source_uuid == source_uuid)).first()
    if existing:
        return _source_registry_to_dict(existing)

    source = SourceRegistry(
        source_uuid=source_uuid,
        name=data.name,
        source_type=data.source_type,
        url=data.url,
        trust_score=data.trust_score,
        update_frequency=data.update_frequency,
        allowed_use_json=json.dumps(data.allowed_use, ensure_ascii=False),
        disallowed_use_json=json.dumps(data.disallowed_use, ensure_ascii=False),
        active=data.active,
        last_checked_at=datetime.now(),
    )
    session.add(source)
    session.commit()
    session.refresh(source)
    return _source_registry_to_dict(source)


@router.post("/raw-items")
def create_raw_item(data: RawContentCreate, session: Session = Depends(get_session)) -> dict:
    """保存候选内容元数据，不默认保存社交平台可识别原文。"""
    content_hash = _content_hash(data.content or data.url or data.title or "")
    raw_uuid = data.raw_uuid or _slug_uuid("raw", data.url or data.title or "candidate", content_hash)
    existing = session.exec(select(RawContentItem).where(RawContentItem.raw_uuid == raw_uuid)).first()
    if existing:
        return _raw_item_to_dict(existing)

    item = RawContentItem(
        raw_uuid=raw_uuid,
        source_id=data.source_id,
        title=data.title,
        url=data.url,
        content_hash=content_hash,
        raw_storage_policy=data.raw_storage_policy,
        privacy_risk=data.privacy_risk,
        copyright_risk=data.copyright_risk,
        consent_status=data.consent_status,
        processing_status=data.processing_status,
    )
    session.add(item)
    session.commit()
    session.refresh(item)
    return _raw_item_to_dict(item)


@router.post("/annotation-jobs")
def create_annotation_job(data: AnnotationJobCreate, session: Session = Depends(get_session)) -> dict:
    """创建一次关系元基础标注任务。"""
    job = AnnotationJob(
        target_type=data.target_type,
        target_id=data.target_id,
        annotator_type=data.annotator_type,
        annotator_version=data.annotator_version,
        schema_version=data.schema_version,
        result_json=json.dumps(data.result, ensure_ascii=False),
        confidence=data.confidence,
        status=data.status,
    )
    session.add(job)
    session.commit()
    session.refresh(job)
    return _annotation_job_to_dict(job)


@router.post("/asset-versions")
def create_asset_version(data: TrainingAssetVersionCreate, session: Session = Depends(get_session)) -> dict:
    """记录训练资产版本和来源追踪。"""
    asset = TrainingAssetVersion(
        asset_type=data.asset_type,
        asset_id=data.asset_id,
        version=data.version,
        source_trace_json=json.dumps(data.source_trace, ensure_ascii=False),
        quality_json=json.dumps(data.quality, ensure_ascii=False),
        review_status=data.review_status,
        published_at=datetime.now() if data.review_status == "published" else None,
    )
    session.add(asset)
    session.commit()
    session.refresh(asset)
    return _asset_version_to_dict(asset)


@router.post("/pipeline/advance")
def advance_pipeline(data: PipelineAdvanceRequest, session: Session = Depends(get_session)) -> dict:
    """执行一次流水线状态推进，并写入处理日志。"""
    target, from_status = _resolve_pipeline_target(data.target_type, data.target_id, session)
    to_status = _next_pipeline_status(data.target_type, data.action)
    _apply_pipeline_status(target, data.target_type, to_status)
    if data.target_type == "asset_version" and to_status == "published":
        target.published_at = datetime.now()
    effects = _run_pipeline_side_effects(
        target=target,
        target_type=data.target_type,
        action=data.action,
        to_status=to_status,
        result=data.result,
        session=session,
    )
    log_result = dict(data.result)
    if effects:
        log_result["effects"] = effects

    log = PipelineRunLog(
        target_type=data.target_type,
        target_id=data.target_id,
        action=data.action,
        from_status=from_status,
        to_status=to_status,
        result_json=json.dumps(log_result, ensure_ascii=False),
        message=data.message or _default_pipeline_message(data.action, from_status, to_status),
    )
    session.add(target)
    session.add(log)
    session.commit()
    session.refresh(log)
    return {
        "target_type": data.target_type,
        "target_id": data.target_id,
        "from_status": from_status,
        "to_status": to_status,
        "effects": effects,
        "log": _pipeline_log_to_dict(log),
    }


@router.post("/pipeline/run-batch")
def run_pipeline_batch(data: PipelineBatchRunRequest, session: Session = Depends(get_session)) -> dict:
    """批量推进数据生命体闭环：脱敏、去重、标注、资产发布、进化报告。"""
    return _run_pipeline_batch(data, session)


@router.post("/sources/fetch")
def fetch_registered_sources(data: SourceFetchRequest, session: Session = Depends(get_session)) -> dict:
    """从已登记合规来源抓取元数据候选，只保留摘要/标题/url/hash。"""
    return _fetch_registered_sources(data, session)


@router.post("/scheduler/run-weekly")
def run_weekly_scheduler(data: ScheduledEvolutionRunRequest, session: Session = Depends(get_session)) -> dict:
    """执行一次本地动态进化调度，生成可审计周报。"""
    return _run_scheduled_evolution(data, session)


@router.get("/dedupe/report")
def dedupe_report(limit: int = Query(default=120, ge=1, le=500), session: Session = Depends(get_session)) -> dict:
    """输出候选内容的 hash + 语义标题去重报告。"""
    items = session.exec(
        select(RawContentItem).order_by(desc(RawContentItem.collected_at)).limit(limit)
    ).all()
    return _build_dedupe_report(list(items))


@router.get("/vector-index/report")
def vector_index_report(session: Session = Depends(get_session)) -> dict:
    """返回持久化元数据向量索引覆盖率与后端状态。"""
    return metadata_vector_index_report(session)


@router.post("/vector-index/rebuild")
def rebuild_vector_index(data: VectorIndexRebuildRequest, session: Session = Depends(get_session)) -> dict:
    """重建本地元数据向量索引，为 sqlite-vec/ANN 替换做准备。"""
    return rebuild_metadata_vector_index(session, target_types=data.target_types, limit_per_type=data.limit_per_type)


@router.post("/vector-index/search")
def search_vector_index(data: VectorSearchRequest, session: Session = Depends(get_session)) -> dict:
    """基于持久化元数据向量做相似检索。"""
    return search_metadata_vectors(session, data.query, target_type=data.target_type, limit=data.limit, threshold=data.threshold)


@router.post("/vector-index/evaluate")
def evaluate_vector_index(data: VectorRecallEvaluationRequest, session: Session = Depends(get_session)) -> dict:
    """评估 sqlite-vec 召回质量和阈值命中曲线。"""
    return evaluate_vector_recall(session, limit_per_type=data.limit_per_type, thresholds=data.thresholds)


@router.get("/import-quality")
def import_quality_report(session: Session = Depends(get_session)) -> dict:
    """输出 JSON/Markdown/知识/样本/资源导入质量报告。"""
    return _build_import_quality_report(session)


@router.post("/import-quality/repair-plan")
def import_quality_repair_plan(data: ImportQualityRepairRequest, session: Session = Depends(get_session)) -> dict:
    """生成或执行安全的导入字段补全计划，不写入第三方全文。"""
    return _run_import_quality_repair(data, session)


@router.get("/import-quality/issues")
def import_quality_issues(
    status: str = Query(default="active", pattern="^(active|open|review_requested|resolved|reopened|all)$"),
    limit: int = Query(default=100, ge=1, le=500),
    session: Session = Depends(get_session),
) -> dict:
    """查看导入 issue 治理队列。"""
    query = select(ContentImportIssue)
    if status not in {"active", "all"}:
        query = query.where(ContentImportIssue.status == status)
    issues = list(session.exec(query.order_by(desc(ContentImportIssue.updated_at), desc(ContentImportIssue.created_at)).limit(limit)).all())
    if status == "active":
        issues = _active_import_issues(issues)
    samples = list(session.exec(select(InteractionSample).limit(5000)).all())
    resources = list(session.exec(select(ResourceLibrary).limit(5000)).all())
    knowledge_entries = list(session.exec(select(KnowledgeEntry).limit(5000)).all())
    return {
        "items": [_import_issue_to_dict(issue) for issue in issues],
        "total": len(issues),
        "status": status,
        "summary": _import_issue_governance_summary(session),
        "source_groups": _import_issue_source_groups(session),
        "triage": _import_issue_triage(issues, samples, resources, knowledge_entries),
        "principle": "导入 issue 只能通过带 reviewer 与 resolution 的状态变更关闭，避免用代码把历史来源问题刷掉。",
    }


@router.get("/import-quality/issues/audit")
def import_quality_issue_audit(
    limit: int = Query(default=50, ge=1, le=200),
    session: Session = Depends(get_session),
) -> dict:
    """Return redacted historical governance actions for import issue closure review."""
    return _import_issue_audit_history(session, limit)


@router.post("/import-quality/issues/action")
def import_quality_issue_action(data: ImportIssueActionRequest, session: Session = Depends(get_session)) -> dict:
    """Resolve, request review, or reopen historical import issues with audit logs."""
    return _apply_import_issue_action(data, session)


@router.post("/import-batches/rollback-plan")
def import_batch_rollback_plan(data: BatchRollbackPlanRequest, session: Session = Depends(get_session)) -> dict:
    """Build a non-destructive rollback plan for an import batch."""
    batch = session.exec(select(ContentImportBatch).where(ContentImportBatch.id == data.batch_id)).first()
    if not batch:
        raise HTTPException(status_code=404, detail="导入批次不存在")
    issues = list(session.exec(
        select(ContentImportIssue)
        .where(ContentImportIssue.batch_id == data.batch_id)
        .order_by(desc(ContentImportIssue.created_at), desc(ContentImportIssue.id))
    ).all())
    source_name = str(batch.source_name or "")
    knowledge_entries = list(session.exec(
        select(KnowledgeEntry)
        .where(KnowledgeEntry.source == source_name)
        .order_by(desc(KnowledgeEntry.updated_at), desc(KnowledgeEntry.id))
        .limit(200)
    ).all())
    resources = list(session.exec(
        select(ResourceLibrary)
        .where(ResourceLibrary.source == source_name)
        .order_by(desc(ResourceLibrary.created_at), desc(ResourceLibrary.id))
        .limit(200)
    ).all())
    logs: list[PipelineRunLog] = []
    if data.include_logs:
        logs = list(session.exec(
            select(PipelineRunLog)
            .where(PipelineRunLog.result_json.contains(f'"batch_id": {data.batch_id}'))
            .order_by(desc(PipelineRunLog.created_at), desc(PipelineRunLog.id))
            .limit(100)
        ).all())
    return {
        "dry_run": data.dry_run,
        "batch": _import_batch_to_dict(batch),
        "impact": {
            "issues": len(issues),
            "knowledge_entries": len(knowledge_entries),
            "resources": len(resources),
            "logs": len(logs),
        },
        "planned_transitions": {
            "batch_status": {"from": batch.status, "to": "rollback_review"},
            "issues": [
                {"id": issue.id, "from": _normalized_import_issue_status(issue), "to": "reopened"}
                for issue in issues
            ],
            "knowledge_entries": [
                {"id": entry.id, "from": entry.review_status, "to": "draft", "title": entry.title}
                for entry in knowledge_entries
            ],
            "resources": [
                {"id": resource.id, "from": resource.review_status, "to": "draft", "title": resource.title}
                for resource in resources
            ],
        },
        "audit_payload": {
            "batch_id": data.batch_id,
            "source_name_hash": _hash_text(source_name),
            "rule_version": "batch-rollback-plan-v1",
            "prompt_version": "none",
            "content_deleted": False,
            "dry_run_only": True,
        },
        "quality_summary": {
            "duplicate_rate": _safe_ratio(batch.skipped_entries, max(batch.imported_entries + batch.skipped_entries, 1)),
            "publish_rate": _safe_ratio(
                len([item for item in [*knowledge_entries, *resources] if item.review_status == "published"]),
                max(len(knowledge_entries) + len(resources), 1),
            ),
            "quarantine_count": len([item for item in resources if item.review_status == "quarantine"]),
            "open_issue_count": len([issue for issue in issues if _normalized_import_issue_status(issue) != "resolved"]),
        },
        "principle": "回滚计划只预演状态迁移，不删除行；真实回滚必须走单独人工确认动作并写审计日志。",
    }


@router.get("/safety-events")
def safety_events(limit: int = Query(default=50, ge=1, le=200), session: Session = Depends(get_session)) -> dict:
    """查看安全硬阻断审计事件，避免高风险请求只存在于一次响应里。"""
    events = session.exec(select(SafetyEvent).order_by(desc(SafetyEvent.created_at)).limit(limit)).all()
    return _build_safety_events_report(list(events))


@router.get("/items")
def list_items(
    category: str | None = None,
    status: str = "published",
    limit: int = Query(default=50, le=200),
    session: Session = Depends(get_session),
) -> list[dict]:
    query = select(EvolutionItem).where(EvolutionItem.status == status)
    if category:
        query = query.where(EvolutionItem.category == category)
    items = session.exec(query.order_by(desc(EvolutionItem.created_at)).limit(limit)).all()
    return [_item_to_dict(item) for item in items]


@router.post("/items")
def create_item(data: EvolutionItemCreate, session: Session = Depends(get_session)) -> dict:
    source = session.exec(
        select(EvolutionSource).where(EvolutionSource.name == data.source_name)
    ).first()
    if not source:
        source = EvolutionSource(name=data.source_name, source_type=data.source_type, url=data.source_url)
        session.add(source)
        session.commit()
        session.refresh(source)

    item = EvolutionItem(
        source_id=source.id,
        title=data.title,
        content=data.content,
        summary=data.summary,
        category=data.category,
        tags_json=json.dumps(data.tags, ensure_ascii=False),
        quality_score=data.quality_score,
        status=data.status,
        published_at=datetime.now() if data.status == "published" else None,
    )
    session.add(item)
    session.commit()
    session.refresh(item)
    return _item_to_dict(item)


@router.get("/reports/latest")
def latest_report(session: Session = Depends(get_session)) -> dict:
    report = session.exec(
        select(EvolutionReport).order_by(desc(EvolutionReport.created_at)).limit(1)
    ).first()
    if not report:
        raise HTTPException(status_code=404, detail="暂无进化报告")
    return _report_to_dict(report)


def _run_pipeline_batch(data: PipelineBatchRunRequest, session: Session) -> dict:
    actions = set(data.actions)
    raw_candidates = _batch_raw_candidates(data, session)
    reviewed_jobs = _batch_reviewed_jobs(data, session)

    if data.dry_run:
        return _batch_dry_run_response(actions, raw_candidates, reviewed_jobs)

    summary = _batch_summary(raw_candidates)
    events: list[dict] = []

    for raw in raw_candidates:
        events.extend(_process_batch_raw(raw, actions, data, summary, session))

    if "publish" in actions:
        events.extend(_publish_batch_jobs(_batch_reviewed_jobs(data, session), data, summary, session))

    report = None
    if "report" in actions:
        report = _create_batch_evolution_report(data.report_period_type, summary, session)
        summary["reports"] += 1

    return {
        "dry_run": False,
        "actions": sorted(actions),
        "summary": summary,
        "events": events[-20:],
        "report": _report_to_dict(report) if report else None,
        "pipeline": pipeline(session),
    }


def _batch_raw_candidates(data: PipelineBatchRunRequest, session: Session) -> list[RawContentItem]:
    query = (
        select(RawContentItem)
        .where(RawContentItem.processing_status != "published")
        .where(RawContentItem.processing_status != "rejected")
    )
    if data.raw_ids:
        query = query.where(RawContentItem.id.in_(data.raw_ids))
    return session.exec(query.order_by(RawContentItem.collected_at).limit(data.limit)).all()


def _batch_reviewed_jobs(data: PipelineBatchRunRequest, session: Session) -> list[AnnotationJob]:
    query = (
        select(AnnotationJob)
        .where(AnnotationJob.target_type == "raw_content")
        .where(AnnotationJob.status == "reviewed")
    )
    if data.raw_ids:
        query = query.where(AnnotationJob.target_id.in_(data.raw_ids))
    return session.exec(query.order_by(AnnotationJob.created_at).limit(data.limit)).all()


def _fetch_registered_sources(data: SourceFetchRequest, session: Session) -> dict:
    query = select(SourceRegistry).where(SourceRegistry.active == True)  # noqa: E712
    if data.source_ids:
        query = query.where(SourceRegistry.id.in_(data.source_ids))
    sources = list(session.exec(query.order_by(SourceRegistry.created_at).limit(50)).all())

    fetched: list[dict] = []
    skipped: list[dict] = []
    for source in sources:
        if not source.url:
            skipped.append({"source_id": source.id, "reason": "missing_url"})
            continue
        parsed = urlparse(source.url)
        if parsed.scheme not in {"http", "https"} or not parsed.netloc:
            skipped.append({"source_id": source.id, "url": source.url, "reason": "invalid_or_unsupported_url"})
            continue

        candidate = _source_metadata_candidate(source)
        if data.dry_run:
            fetched.append({**candidate, "dry_run": True})
            continue

        try:
            response = httpx.get(source.url, timeout=data.timeout_seconds, follow_redirects=True)
            response.raise_for_status()
        except httpx.HTTPError as exc:
            skipped.append({"source_id": source.id, "url": source.url, "reason": f"fetch_failed:{exc.__class__.__name__}"})
            continue

        title = _extract_html_title(response.text, source.name)
        raw_data = RawContentCreate(
            source_id=source.id,
            title=title,
            url=str(response.url),
            content=f"{title}|{response.url}|{response.headers.get('etag', '')}|{response.headers.get('last-modified', '')}",
            privacy_risk=0.02,
            copyright_risk=0.18,
            consent_status="metadata_or_summary_only",
        )
        raw = create_raw_item(raw_data, session)
        source.last_checked_at = datetime.now()
        session.add(source)
        fetched.append({**candidate, "raw_item": raw, "dry_run": False})

    if not data.dry_run:
        session.commit()

    return {
        "dry_run": data.dry_run,
        "principle": "来源抓取只生成标题、URL、hash 和风险评分等元数据候选，不保存第三方全文或可识别私密对话。",
        "sources_scanned": len(sources),
        "candidates": fetched[: data.limit_per_source * max(1, len(sources))],
        "skipped": skipped,
        "next_actions": [
            "run /api/evolution/pipeline/run-batch to sanitize, dedupe, annotate and publish reviewed assets",
            "upgrade metadata signatures to sqlite-vec when vector extension is available",
        ],
    }


def _source_metadata_candidate(source: SourceRegistry) -> dict:
    return {
        "source_id": source.id,
        "source_uuid": source.source_uuid,
        "source_name": source.name,
        "source_type": source.source_type,
        "url": source.url,
        "trust_score": source.trust_score,
        "storage_policy": "metadata_only",
    }


def _extract_html_title(text: str, fallback: str) -> str:
    lower = text.lower()
    start = lower.find("<title")
    if start < 0:
        return fallback
    close_start = lower.find(">", start)
    close_end = lower.find("</title>", close_start)
    if close_start < 0 or close_end < 0:
        return fallback
    title = text[close_start + 1:close_end].strip()
    return title[:180] or fallback


def _batch_dry_run_response(
    actions: set[str],
    raw_candidates: list[RawContentItem],
    reviewed_jobs: list[AnnotationJob],
) -> dict:
    return {
        "dry_run": True,
        "candidate_counts": {
            "raw_items": len(raw_candidates),
            "reviewed_annotation_jobs": len(reviewed_jobs),
        },
        "actions": sorted(actions),
        "next_actions": [
            "run without dry_run to apply sanitize/dedupe/annotate/publish/report",
        ],
    }


def _batch_summary(raw_candidates: list[RawContentItem]) -> dict[str, int]:
    return {
        "raw_seen": len(raw_candidates),
        "sanitized": 0,
        "deduped": 0,
        "duplicate_review_needed": 0,
        "annotated": 0,
        "asset_versions": 0,
        "published_assets": 0,
        "reports": 0,
        "skipped": 0,
    }


def _process_batch_raw(
    raw: RawContentItem,
    actions: set[str],
    data: PipelineBatchRunRequest,
    summary: dict[str, int],
    session: Session,
) -> list[dict]:
    events: list[dict] = []
    duplicate_review_needed = False
    if "sanitize" in actions and raw.processing_status in {"raw", "collected", "imported", "sanitized"}:
        event = advance_pipeline(
            PipelineAdvanceRequest(
                target_type="raw_content",
                target_id=raw.id or 0,
                action="sanitize",
                result=_batch_sanitize_result(raw),
                message="batch sanitize: privacy/copyright risk normalized",
            ),
            session,
        )
        summary["sanitized"] += 1
        events.append(event)

    if "dedupe" in actions and raw.processing_status in {"raw", "sanitized", "deduped"}:
        event = advance_pipeline(
            PipelineAdvanceRequest(
                target_type="raw_content",
                target_id=raw.id or 0,
                action="dedupe",
                result={"method": "hash+title_similarity"},
                message="batch dedupe: hash and semantic title similarity checked",
            ),
            session,
        )
        summary["deduped"] += 1
        dedupe_effect = event["effects"][0] if event["effects"] else {}
        duplicate_review_needed = dedupe_effect.get("decision") == "duplicate_review_needed"
        if duplicate_review_needed:
            summary["duplicate_review_needed"] += 1
        events.append(event)

    if duplicate_review_needed and data.duplicate_policy == "skip_annotate":
        summary["skipped"] += 1
        return events

    if "annotate" in actions and raw.processing_status in {"raw", "sanitized", "deduped", "annotated", "reviewed"}:
        event = advance_pipeline(
            PipelineAdvanceRequest(
                target_type="raw_content",
                target_id=raw.id or 0,
                action="annotate",
                result=_batch_annotation_result(raw, data.min_confidence),
                message="batch annotate: relationship primitive labels generated",
            ),
            session,
        )
        summary["annotated"] += 1
        events.append(event)
    return events


def _publish_batch_jobs(
    reviewed_jobs: list[AnnotationJob],
    data: PipelineBatchRunRequest,
    summary: dict[str, int],
    session: Session,
) -> list[dict]:
    events: list[dict] = []
    for job in reviewed_jobs:
        event = advance_pipeline(
            PipelineAdvanceRequest(
                target_type="annotation_job",
                target_id=job.id or 0,
                action="publish",
                result={
                    "version": f"batch-{datetime.now().strftime('%Y%m%d')}",
                    "review_status": data.publish_review_status,
                },
                message="batch publish: reviewed annotation promoted to training asset version",
            ),
            session,
        )
        summary["asset_versions"] += 1
        if data.publish_review_status == "published":
            summary["published_assets"] += 1
        events.append(event)
    return events


@router.post("/reviewed-assets/promote")
def promote_reviewed_assets(session: Session = Depends(get_session)) -> dict:
    """汇总样本、资源和知识条目的 reviewed/published 状态。"""
    samples = list(session.exec(select(InteractionSample).order_by(desc(InteractionSample.updated_at), desc(InteractionSample.id)).limit(500)).all())
    resources = list(session.exec(select(ResourceLibrary).order_by(desc(ResourceLibrary.created_at), desc(ResourceLibrary.id)).limit(500)).all())
    knowledge_entries = list(session.exec(select(KnowledgeEntry).order_by(desc(KnowledgeEntry.updated_at), desc(KnowledgeEntry.id)).limit(500)).all())
    inventory = _reviewed_asset_inventory(samples, resources, knowledge_entries)
    return {
        "principle": "reviewed/published 是统一发布门禁；资产只有进入 reviewed 才适合进入 published。",
        "inventory": inventory,
        "totals": {
            "samples": len(samples),
            "resources": len(resources),
            "knowledge_entries": len(knowledge_entries),
        },
        "next_actions": _reviewed_asset_next_actions(inventory),
    }


@router.post("/reviewed-assets/backfill")
def backfill_reviewed_assets(data: ReviewedAssetBackfillRequest, session: Session = Depends(get_session)) -> dict:
    """把资源和知识条目的 reviewed/published 状态按质量阈值回填。"""
    resources = list(session.exec(select(ResourceLibrary).order_by(desc(ResourceLibrary.created_at), desc(ResourceLibrary.id)).limit(data.limit)).all())
    knowledge_entries = list(session.exec(select(KnowledgeEntry).order_by(desc(KnowledgeEntry.updated_at), desc(KnowledgeEntry.id)).limit(data.limit)).all())
    sample_inventory = _reviewed_asset_inventory(
        list(session.exec(select(InteractionSample).order_by(desc(InteractionSample.updated_at), desc(InteractionSample.id)).limit(data.limit)).all()),
        resources,
        knowledge_entries,
    )
    updated_resources = _backfill_resource_review_status(resources, data.force, session)
    updated_knowledge = _backfill_knowledge_review_status(knowledge_entries, data.force, session)
    session.commit()
    return {
        "principle": "reviewed/published 需要可回填、可审计的质量阈值，而不是只停在种子数据上。",
        "updated": {
            "resources": updated_resources,
            "knowledge_entries": updated_knowledge,
        },
        "inventory": {
            "samples": sample_inventory["samples"],
            "resources": _status_counts(resources, "review_status"),
            "knowledge_entries": _status_counts(knowledge_entries, "review_status"),
        },
        "next_actions": _reviewed_asset_next_actions(
            _reviewed_asset_inventory(
                list(session.exec(select(InteractionSample).order_by(desc(InteractionSample.updated_at), desc(InteractionSample.id)).limit(data.limit)).all()),
                list(session.exec(select(ResourceLibrary).order_by(desc(ResourceLibrary.created_at), desc(ResourceLibrary.id)).limit(data.limit)).all()),
                list(session.exec(select(KnowledgeEntry).order_by(desc(KnowledgeEntry.updated_at), desc(KnowledgeEntry.id)).limit(data.limit)).all()),
            )
        ),
    }


@router.get("/reviewed-assets/publish-candidates")
def reviewed_asset_publish_candidates(limit: int = Query(default=20, ge=1, le=100), session: Session = Depends(get_session)) -> dict:
    """Return reviewed assets that are closest to safe publication."""
    scan_limit = max(limit * 5, 200)
    resources = list(session.exec(
        select(ResourceLibrary)
        .where(ResourceLibrary.review_status == "reviewed")
        .order_by(desc(ResourceLibrary.effectiveness_rating), desc(ResourceLibrary.created_at), desc(ResourceLibrary.id))
        .limit(scan_limit)
    ).all())
    knowledge_entries = list(session.exec(
        select(KnowledgeEntry)
        .where(KnowledgeEntry.review_status == "reviewed")
        .order_by(desc(KnowledgeEntry.quality_score), desc(KnowledgeEntry.updated_at), desc(KnowledgeEntry.id))
        .limit(scan_limit)
    ).all())
    candidates = [_resource_publish_candidate(item) for item in resources] + [_knowledge_publish_candidate(item) for item in knowledge_entries]
    candidates.sort(key=lambda item: (-int(item["priority"]["score"]), item["asset_type"], int(item["id"] or 0)))
    selected = candidates[:limit]
    return {
        "items": selected,
        "total": len(candidates),
        "publish_ready": sum(1 for item in candidates if item["publish_ready"]),
        "quality_gates": {
            "has_publish_candidates": bool(candidates),
            "requires_manual_confirmation": True,
            "minimum_priority_for_auto_publish": 85,
        },
        "next_actions": _publish_candidate_next_actions(candidates),
        "principle": "发布候选只暴露元数据、质量信号和安全理由；最终发布仍要保留 reviewed -> published 的可审计门禁。",
    }


@router.post("/reviewed-assets/boutique-batch")
def create_boutique_resource_batch(data: BoutiqueResourceBatchRequest, session: Session = Depends(get_session)) -> dict:
    """Create project-original concrete practice cards that satisfy reviewed publish gates."""
    now = datetime.now()
    drafts = _boutique_resource_specs()[:data.limit]
    existing_cards = list(session.exec(
        select(ResourceLibrary).where(ResourceLibrary.resource_uuid.in_([item["resource_uuid"] for item in drafts]))
    ).all())
    existing_uuids = {card.resource_uuid for card in existing_cards}
    cards = [_boutique_resource_from_spec(spec, data.reviewer_id, now) for spec in drafts if spec["resource_uuid"] not in existing_uuids]
    candidates = [_resource_publish_candidate(card) for card in existing_cards] + [_resource_publish_candidate(card) for card in cards]
    if data.dry_run:
        return {
            "dry_run": True,
            "created": 0,
            "skipped_existing": len(existing_uuids),
            "items": candidates,
            "publish_ready": sum(1 for item in candidates if item["publish_ready"]),
            "principle": "dry-run 只生成项目原创精品训练卡预览；不抓取、不保存第三方全文，不绕过 reviewed 发布门禁。",
        }

    for card in cards:
        session.add(card)
    session.commit()
    for card in cards:
        session.refresh(card)
    created_candidates = [_resource_publish_candidate(card) for card in existing_cards] + [_resource_publish_candidate(card) for card in cards]
    session.add(PipelineRunLog(
        target_type="resource",
        target_id=0,
        action="create_boutique_batch",
        from_status="missing",
        to_status="reviewed",
        result_json=json.dumps({
            "created_resource_ids": [card.id for card in cards],
            "reviewer_id": data.reviewer_id,
            "publish_ready": sum(1 for item in created_candidates if item["publish_ready"]),
            "raw_source_text_saved": False,
            "third_party_full_text_saved": False,
        }, ensure_ascii=False),
        message=f"created {len(cards)} project-original boutique reviewed resource cards",
    ))
    session.commit()
    return {
        "dry_run": False,
        "created": len(cards),
        "skipped_existing": len(existing_uuids),
        "items": created_candidates,
        "publish_ready": sum(1 for item in created_candidates if item["publish_ready"]),
        "principle": "已创建的是项目原创 reviewed 精品训练卡；不抓取、不保存第三方全文，进入 published 仍需 reviewed-assets/action 人工确认。",
    }


@router.post("/reviewed-assets/action")
def reviewed_asset_action(data: ReviewedAssetActionRequest, session: Session = Depends(get_session)) -> dict:
    """Confirm publish, withdraw, or request re-review for reviewed assets."""
    target = _load_reviewed_asset(data.asset_type, data.asset_id, session)
    from_status = str(target.review_status or "draft")
    to_status = _reviewed_asset_target_status(data.action, from_status)
    candidate = _reviewed_asset_candidate_card(target, data.asset_type)
    publish_ready = bool(candidate.get("publish_ready")) if data.action == "confirm_publish" else True
    if data.action == "confirm_publish" and from_status != "reviewed":
        raise HTTPException(status_code=409, detail="只有 reviewed 资产可以人工确认发布")
    if data.action == "confirm_publish" and not publish_ready:
        raise HTTPException(status_code=409, detail="资产未达到发布候选质量阈值")
    if data.action == "withdraw" and from_status != "published":
        raise HTTPException(status_code=409, detail="只有 published 资产可以撤回")
    if data.dry_run:
        return {
            "dry_run": True,
            "asset": candidate,
            "from_status": from_status,
            "to_status": to_status,
            "would_log": _reviewed_asset_audit_payload(data, candidate, from_status, to_status),
            "principle": "发布治理 dry-run 不改状态；真实执行会写入 pipeline_run_logs 审计。",
        }
    now = datetime.now()
    target.review_status = to_status
    target.reviewer_id = data.reviewer_id
    target.reviewed_at = now if to_status in {"reviewed", "published"} else target.reviewed_at
    if to_status == "published":
        target.published_at = now
    if data.action == "withdraw":
        target.published_at = None
    updated_candidate = _reviewed_asset_candidate_card(target, data.asset_type)
    session.add(target)
    log = PipelineRunLog(
        target_type=data.asset_type,
        target_id=data.asset_id,
        action=data.action,
        from_status=from_status,
        to_status=to_status,
        result_json=json.dumps(_reviewed_asset_audit_payload(data, updated_candidate, from_status, to_status), ensure_ascii=False),
        message=data.reason or f"reviewed asset governance action: {data.action}",
    )
    session.add(log)
    session.commit()
    session.refresh(log)
    return {
        "dry_run": False,
        "asset": updated_candidate,
        "from_status": from_status,
        "to_status": to_status,
        "audit_log": {
            "id": log.id,
            "action": log.action,
            "created_at": log.created_at.isoformat(),
        },
        "principle": "人工确认、撤回和复审请求均以 SQLite 状态和 pipeline_run_logs 为审计主真源。",
    }


@router.post("/reviewed-assets/auto-review")
def auto_review_reviewed_assets(data: ReviewedAssetAutoReviewRequest, session: Session = Depends(get_session)) -> dict:
    """Batch-review publish candidates without bypassing quality gates."""
    candidates = reviewed_asset_publish_candidates(limit=data.limit, session=session)["items"]
    decisions = [_auto_review_decision(item, data) for item in candidates]
    if data.dry_run:
        return {
            "dry_run": True,
            "summary": _auto_review_summary(decisions),
            "items": decisions,
            "quality_gates": {
                "publishes_only_publish_ready": True,
                "minimum_priority_score": data.min_priority_score,
                "blocked_assets_require_explicit_re_review": not data.request_review_blocked_assets,
            },
            "principle": "自动审核只推进已满足质量阈值的 reviewed 资产；阻断项默认只记录原因，不绕过人工复审。",
        }

    applied: list[dict] = []
    for decision in decisions:
        action = str(decision["action"])
        if action == "hold":
            continue
        target = _load_reviewed_asset(str(decision["asset_type"]), int(decision["id"]), session)
        from_status = str(target.review_status or "draft")
        to_status = _reviewed_asset_target_status(action, from_status)
        now = datetime.now()
        target.review_status = to_status
        target.reviewer_id = data.reviewer_id
        target.reviewed_at = now if to_status in {"reviewed", "published"} else target.reviewed_at
        if to_status == "published":
            target.published_at = now
        session.add(target)
        session.add(PipelineRunLog(
            target_type=str(decision["asset_type"]),
            target_id=int(decision["id"]),
            action=f"auto_review:{action}",
            from_status=from_status,
            to_status=to_status,
            result_json=json.dumps(_auto_review_audit_payload(decision, data, from_status, to_status), ensure_ascii=False),
            message=str(decision["reason"]),
        ))
        applied.append({**decision, "from_status": from_status, "to_status": to_status})
    session.commit()
    return {
        "dry_run": False,
        "summary": _auto_review_summary(decisions),
        "applied": applied,
        "held": [item for item in decisions if item["action"] == "hold"],
        "principle": "自动审核批处理写入 pipeline_run_logs，发布只发生在 publish_ready 且优先级达标的资产上。",
    }


def build_pipeline_summary(session: Session) -> dict:
    """基于现有进化表计算流水线状态，不引入新 schema。"""
    items = session.exec(select(EvolutionItem)).all()
    sources = session.exec(select(EvolutionSource)).all()
    registry_sources = session.exec(select(SourceRegistry).order_by(desc(SourceRegistry.created_at)).limit(100)).all()
    raw_items = session.exec(select(RawContentItem).order_by(desc(RawContentItem.collected_at)).limit(100)).all()
    jobs = session.exec(select(AnnotationJob).order_by(desc(AnnotationJob.created_at)).limit(100)).all()
    assets = session.exec(select(TrainingAssetVersion).order_by(desc(TrainingAssetVersion.created_at)).limit(100)).all()
    logs = session.exec(select(PipelineRunLog).order_by(desc(PipelineRunLog.created_at)).limit(50)).all()

    status_counts = {"draft": 0, "reviewed": 0, "published": 0, "rejected": 0}
    category_counts: dict[str, int] = {}
    quality_distribution = {
        "excellent": 0,
        "strong": 0,
        "usable": 0,
        "needs_review": 0,
    }
    quality_total = 0.0
    last_item_at: datetime | None = None

    items_by_source_id: dict[int, int] = {}
    for item in items:
        status_counts[item.status] = status_counts.get(item.status, 0) + 1
        category_counts[item.category] = category_counts.get(item.category, 0) + 1
        quality_total += item.quality_score
        if item.source_id is not None:
            items_by_source_id[item.source_id] = items_by_source_id.get(item.source_id, 0) + 1
        if last_item_at is None or item.created_at > last_item_at:
            last_item_at = item.created_at

        if item.quality_score >= 90:
            quality_distribution["excellent"] += 1
        elif item.quality_score >= 75:
            quality_distribution["strong"] += 1
        elif item.quality_score >= 60:
            quality_distribution["usable"] += 1
        else:
            quality_distribution["needs_review"] += 1

    source_type_counts: dict[str, int] = {}
    source_cards = []
    active_sources = 0
    for source in sources:
        source_type_counts[source.source_type] = source_type_counts.get(source.source_type, 0) + 1
        if source.active:
            active_sources += 1
        source_cards.append({
            "id": source.id,
            "name": source.name,
            "source_type": source.source_type,
            "trust_score": source.trust_score,
            "active": source.active,
            "items_count": items_by_source_id.get(source.id or 0, 0),
            "update_frequency": source.update_frequency,
        })

    total_items = len(items)
    candidate_count = status_counts.get("draft", 0) + status_counts.get("reviewed", 0)
    published_count = status_counts.get("published", 0)
    rejected_count = status_counts.get("rejected", 0)
    average_quality = round(quality_total / total_items, 1) if total_items else 0
    publish_rate = round(published_count / total_items, 3) if total_items else 0
    review_pressure = candidate_count + quality_distribution["needs_review"]

    return {
        "heartbeat": _pipeline_heartbeat(
            total_items=total_items,
            active_sources=active_sources,
            candidate_count=candidate_count,
            review_pressure=review_pressure,
        ),
        "totals": {
            "sources": len(sources),
            "active_sources": active_sources,
            "items": total_items,
            "candidates": candidate_count,
            "published": published_count,
            "rejected": rejected_count,
        },
        "status_counts": status_counts,
        "category_counts": category_counts,
        "source_type_counts": source_type_counts,
        "sources": sorted(source_cards, key=lambda item: (-item["items_count"], item["name"]))[:12],
        "quality": {
            "average_score": average_quality,
            "publish_rate": publish_rate,
            "distribution": quality_distribution,
        },
        "next_actions": _next_actions(
            total_items=total_items,
            active_sources=active_sources,
            candidate_count=candidate_count,
            published_count=published_count,
            rejected_count=rejected_count,
            average_quality=average_quality,
            needs_review_count=quality_distribution["needs_review"],
        ),
        "visual_metrics": _build_evolution_visual_metrics(registry_sources, raw_items, jobs, assets, logs),
        "last_item_at": last_item_at.isoformat() if last_item_at else None,
    }


def _item_to_dict(item: EvolutionItem) -> dict:
    tags = []
    if item.tags_json:
        try:
            tags = json.loads(item.tags_json)
        except Exception:
            tags = []
    return {
        "id": item.id,
        "source_id": item.source_id,
        "title": item.title,
        "content": item.content,
        "summary": item.summary,
        "category": item.category,
        "tags": tags,
        "quality_score": item.quality_score,
        "status": item.status,
        "created_at": item.created_at.isoformat(),
    }


def _report_to_dict(report: EvolutionReport) -> dict:
    insights = []
    if report.key_insights_json:
        try:
            insights = json.loads(report.key_insights_json)
        except Exception:
            insights = []
    return {
        "id": report.id,
        "period_type": report.period_type,
        "title": report.title,
        "summary": report.summary,
        "new_items_count": report.new_items_count,
        "promoted_samples_count": report.promoted_samples_count,
        "key_insights": insights,
        "created_at": report.created_at.isoformat(),
    }


def _source_registry_to_dict(source: SourceRegistry) -> dict:
    return {
        "id": source.id,
        "source_uuid": source.source_uuid,
        "name": source.name,
        "source_type": source.source_type,
        "url": source.url,
        "trust_score": source.trust_score,
        "update_frequency": source.update_frequency,
        "allowed_use": _loads_list(source.allowed_use_json),
        "disallowed_use": _loads_list(source.disallowed_use_json),
        "active": source.active,
        "last_checked_at": source.last_checked_at.isoformat() if source.last_checked_at else None,
        "created_at": source.created_at.isoformat(),
    }


def _raw_item_to_dict(item: RawContentItem) -> dict:
    return {
        "id": item.id,
        "raw_uuid": item.raw_uuid,
        "source_id": item.source_id,
        "title": item.title,
        "url": item.url,
        "content_hash": item.content_hash,
        "raw_storage_policy": item.raw_storage_policy,
        "privacy_risk": item.privacy_risk,
        "copyright_risk": item.copyright_risk,
        "consent_status": item.consent_status,
        "processing_status": item.processing_status,
        "collected_at": item.collected_at.isoformat(),
    }


def _annotation_job_to_dict(job: AnnotationJob) -> dict:
    return {
        "id": job.id,
        "target_type": job.target_type,
        "target_id": job.target_id,
        "annotator_type": job.annotator_type,
        "annotator_version": job.annotator_version,
        "schema_version": job.schema_version,
        "result": _loads_dict(job.result_json),
        "confidence": job.confidence,
        "status": job.status,
        "created_at": job.created_at.isoformat(),
    }


def _asset_version_to_dict(asset: TrainingAssetVersion) -> dict:
    return {
        "id": asset.id,
        "asset_type": asset.asset_type,
        "asset_id": asset.asset_id,
        "version": asset.version,
        "source_trace": _loads_dict(asset.source_trace_json),
        "quality": _loads_dict(asset.quality_json),
        "review_status": asset.review_status,
        "published_at": asset.published_at.isoformat() if asset.published_at else None,
        "created_at": asset.created_at.isoformat(),
    }


def _build_evolution_visual_metrics(
    sources: list[SourceRegistry],
    raw_items: list[RawContentItem],
    jobs: list[AnnotationJob],
    assets: list[TrainingAssetVersion],
    logs: list[PipelineRunLog],
) -> dict:
    """数图结合的进化中心指标：数负责入微，图负责直觉。"""
    source_quality_matrix = [_source_quality_cell(source, raw_items, jobs, assets) for source in sources[:24]]
    review_funnel = _review_publish_funnel(sources, raw_items, jobs, assets)
    safety_risk_trend = _safety_risk_trend(logs)
    learning_increment = _learning_increment(jobs, assets, logs)
    return {
        "source_quality_matrix": source_quality_matrix,
        "review_publish_funnel": review_funnel,
        "safety_risk_trend": safety_risk_trend,
        "learning_increment": learning_increment,
        "principle": "数负责频率、风险、质量和转化率；图负责来源分布、漏斗流动、安全趋势和学习增量。",
    }


def _source_quality_cell(
    source: SourceRegistry,
    raw_items: list[RawContentItem],
    jobs: list[AnnotationJob],
    assets: list[TrainingAssetVersion],
) -> dict:
    source_raw = [item for item in raw_items if item.source_id == source.id]
    raw_ids = {item.id for item in source_raw}
    source_jobs = [job for job in jobs if job.target_type == "raw_content" and job.target_id in raw_ids]
    job_ids = {job.id for job in source_jobs}
    source_assets = [asset for asset in assets if asset.asset_type == "annotation" and asset.asset_id in job_ids]
    avg_privacy = _average([item.privacy_risk for item in source_raw])
    avg_copyright = _average([item.copyright_risk for item in source_raw])
    avg_confidence = _average([job.confidence for job in source_jobs])
    published_assets = sum(1 for asset in source_assets if asset.review_status == "published")
    conversion_rate = round(published_assets / len(source_raw), 3) if source_raw else 0
    health_score = round(
        max(
            0,
            min(
                100,
                source.trust_score * 45
                + avg_confidence * 35
                + conversion_rate * 20
                - avg_privacy * 20
                - avg_copyright * 15,
            ),
        ),
        1,
    )
    return {
        "id": source.id,
        "name": source.name,
        "source_type": source.source_type,
        "trust_score": round(source.trust_score * 100, 1),
        "raw_count": len(source_raw),
        "annotation_count": len(source_jobs),
        "asset_count": len(source_assets),
        "published_assets": published_assets,
        "avg_privacy_risk": round(avg_privacy * 100, 1),
        "avg_copyright_risk": round(avg_copyright * 100, 1),
        "avg_confidence": round(avg_confidence * 100, 1),
        "conversion_rate": conversion_rate,
        "health_score": health_score,
        "quadrant": _source_quality_quadrant(health_score, avg_privacy + avg_copyright),
    }


def _source_quality_quadrant(health_score: float, combined_risk: float) -> str:
    if health_score >= 75 and combined_risk <= 0.5:
        return "high_quality_low_risk"
    if health_score >= 60:
        return "promising_needs_review"
    if combined_risk > 0.9:
        return "risk_quarantine"
    return "low_signal"


def _review_publish_funnel(
    sources: list[SourceRegistry],
    raw_items: list[RawContentItem],
    jobs: list[AnnotationJob],
    assets: list[TrainingAssetVersion],
) -> list[dict]:
    source_count = len(sources)
    raw_count = len(raw_items)
    sanitized_count = sum(1 for item in raw_items if item.processing_status in {"sanitized", "deduped", "annotated", "reviewed", "published"})
    annotated_count = len(jobs)
    reviewed_count = sum(1 for job in jobs if job.status in {"reviewed", "published"})
    asset_count = len(assets)
    published_count = sum(1 for asset in assets if asset.review_status == "published")
    stages = [
        ("sources", "来源登记", source_count),
        ("raw", "候选元数据", raw_count),
        ("sanitized", "脱敏可用", sanitized_count),
        ("annotated", "关系标注", annotated_count),
        ("reviewed", "质量评审", reviewed_count),
        ("asset", "训练资产", asset_count),
        ("published", "发布训练", published_count),
    ]
    previous = stages[0][2] or 1
    funnel = []
    for stage_id, label, count in stages:
        funnel.append({
            "id": stage_id,
            "label": label,
            "count": count,
            "percent_of_start": round(count / max(stages[0][2], 1) * 100, 1),
            "conversion_from_previous": round(count / max(previous, 1) * 100, 1),
        })
        previous = count
    return funnel


def _safety_risk_trend(logs: list[PipelineRunLog]) -> list[dict]:
    buckets: dict[str, dict[str, int]] = {}
    for log in logs:
        day = log.created_at.date().isoformat()
        bucket = buckets.setdefault(day, {"total": 0, "blocked": 0, "risk_events": 0, "sanitized": 0})
        result = _loads_dict(log.result_json)
        bucket["total"] += 1
        if log.to_status == "rejected":
            bucket["blocked"] += 1
        if log.action == "sanitize":
            bucket["sanitized"] += 1
        if _log_has_risk(result):
            bucket["risk_events"] += 1
    if not buckets:
        return [{"date": "暂无", "total": 0, "blocked": 0, "risk_events": 0, "sanitized": 0, "risk_rate": 0}]
    return [
        {
            "date": day,
            **values,
            "risk_rate": round(values["risk_events"] / max(values["total"], 1), 3),
        }
        for day, values in sorted(buckets.items())[-14:]
    ]


def _log_has_risk(result: dict) -> bool:
    text = json.dumps(result, ensure_ascii=False)
    if any(key in text for key in ["duplicate_review_needed", "privacy_risk", "copyright_risk", "rejected"]):
        return True
    effects = result.get("effects")
    if isinstance(effects, list):
        for effect in effects:
            if isinstance(effect, dict) and (
                float(effect.get("privacy_risk", 0) or 0) >= 0.2
                or float(effect.get("copyright_risk", 0) or 0) >= 0.35
                or effect.get("decision") == "duplicate_review_needed"
            ):
                return True
    return False


def _learning_increment(
    jobs: list[AnnotationJob],
    assets: list[TrainingAssetVersion],
    logs: list[PipelineRunLog],
) -> dict:
    axes: dict[str, int] = {}
    primitive_layers: dict[str, int] = {}
    for job in jobs:
        result = _loads_dict(job.result_json)
        for axis in result.get("classification_axes", []):
            axes[str(axis)] = axes.get(str(axis), 0) + 1
        for layer in result.get("primitive_layers", []):
            primitive_layers[str(layer)] = primitive_layers.get(str(layer), 0) + 1
    published_assets = sum(1 for asset in assets if asset.review_status == "published")
    automation_events = sum(1 for log in logs if log.action in {"sanitize", "dedupe", "annotate", "publish"})
    return {
        "new_annotations": len(jobs),
        "published_assets": published_assets,
        "automation_events": automation_events,
        "axis_coverage": [{"name": key, "count": value} for key, value in sorted(axes.items(), key=lambda item: (-item[1], item[0]))[:12]],
        "primitive_layer_coverage": [
            {"name": key, "count": value}
            for key, value in sorted(primitive_layers.items(), key=lambda item: (-item[1], item[0]))[:12]
        ],
        "learning_velocity": round((len(jobs) * 0.45 + published_assets * 0.35 + automation_events * 0.2), 1),
    }


def _average(values: list[float]) -> float:
    return sum(values) / len(values) if values else 0.0


def _pipeline_log_to_dict(log: PipelineRunLog) -> dict:
    return {
        "id": log.id,
        "target_type": log.target_type,
        "target_id": log.target_id,
        "action": log.action,
        "from_status": log.from_status,
        "to_status": log.to_status,
        "result": _loads_dict(log.result_json),
        "message": log.message,
        "created_at": log.created_at.isoformat(),
    }


def _resolve_pipeline_target(target_type: str, target_id: int, session: Session):
    if target_type == "raw_content":
        target = session.exec(select(RawContentItem).where(RawContentItem.id == target_id)).first()
        if not target:
            raise HTTPException(status_code=404, detail="候选内容不存在")
        return target, target.processing_status
    if target_type == "annotation_job":
        target = session.exec(select(AnnotationJob).where(AnnotationJob.id == target_id)).first()
        if not target:
            raise HTTPException(status_code=404, detail="标注任务不存在")
        return target, target.status
    if target_type == "asset_version":
        target = session.exec(select(TrainingAssetVersion).where(TrainingAssetVersion.id == target_id)).first()
        if not target:
            raise HTTPException(status_code=404, detail="训练资产版本不存在")
        return target, target.review_status
    raise HTTPException(status_code=400, detail="不支持的流水线目标类型")


def _next_pipeline_status(target_type: str, action: str) -> str:
    transitions = {
        "raw_content": {
            "sanitize": "sanitized",
            "dedupe": "deduped",
            "annotate": "annotated",
            "review": "reviewed",
            "publish": "published",
            "reject": "rejected",
        },
        "annotation_job": {
            "start": "running",
            "review": "reviewed",
            "publish": "published",
            "reject": "rejected",
        },
        "asset_version": {
            "review": "reviewed",
            "publish": "published",
            "reject": "rejected",
        },
    }
    target_transitions = transitions.get(target_type)
    if not target_transitions or action not in target_transitions:
        raise HTTPException(status_code=400, detail="不支持的流水线动作")
    return target_transitions[action]


def _apply_pipeline_status(target, target_type: str, status: str) -> None:
    if target_type == "raw_content":
        target.processing_status = status
    elif target_type == "annotation_job":
        target.status = status
    elif target_type == "asset_version":
        target.review_status = status


def _default_pipeline_message(action: str, from_status: str | None, to_status: str) -> str:
    return f"{action}: {from_status or 'unknown'} -> {to_status}"


def _run_pipeline_side_effects(
    *,
    target,
    target_type: str,
    action: str,
    to_status: str,
    result: dict,
    session: Session,
) -> list[dict]:
    """把流水线推进变成可审计的自动处理器，只生成抽象资产，不复刻原文。"""
    if target_type == "raw_content" and action == "sanitize":
        return [_sanitize_raw_content(target, result)]
    if target_type == "raw_content" and action == "dedupe":
        return [_dedupe_raw_content(target, session)]
    if target_type == "raw_content" and action == "annotate":
        job = _ensure_annotation_job_for_raw(target, result, session)
        return [{"type": "annotation_job", "id": job.id, "status": job.status}]
    if target_type == "annotation_job" and action == "publish":
        asset = _ensure_asset_version_for_annotation(target, result, session)
        return [{"type": "training_asset_version", "id": asset.id, "status": asset.review_status}]
    if target_type == "asset_version" and to_status == "published":
        return [{"type": "published_training_asset", "id": target.id, "status": "published"}]
    return []


def _sanitize_raw_content(item: RawContentItem, result: dict) -> dict:
    item.raw_storage_policy = "metadata_only"
    item.privacy_risk = min(float(result.get("privacy_risk", item.privacy_risk)), 0.2)
    item.copyright_risk = min(float(result.get("copyright_risk", item.copyright_risk)), 0.35)
    item.consent_status = result.get("consent_status") or item.consent_status or "abstract_only"
    return {
        "type": "sanitized_metadata",
        "raw_storage_policy": item.raw_storage_policy,
        "privacy_risk": item.privacy_risk,
        "copyright_risk": item.copyright_risk,
        "consent_status": item.consent_status,
    }


def _batch_sanitize_result(item: RawContentItem) -> dict:
    return {
        "privacy_risk": min(item.privacy_risk, 0.12),
        "copyright_risk": min(item.copyright_risk, 0.24),
        "consent_status": item.consent_status or "abstract_only",
    }


def _batch_annotation_result(item: RawContentItem, min_confidence: float) -> dict:
    confidence = max(min_confidence, 0.65)
    title = item.title or "未命名候选关系素材"
    scene_axis = _infer_scene_axis(title)
    return {
        "confidence": confidence,
        "status": "reviewed",
        "annotator_type": "rule",
        "annotator_version": "batch-pipeline-v1",
        "primitive_layers": [
            "source_meta",
            "observable_signal",
            "emotion_flow",
            "hidden_need",
            "boundary_safety",
            "response_pattern",
        ],
        "classification_axes": [
            scene_axis,
            "relationship_stage",
            "attachment_signal",
            "boundary_pressure",
            "safety_risk",
            "training_transfer",
        ],
    }


def _infer_scene_axis(text: str) -> str:
    if any(key in text for key in ["冲突", "吵架", "修复"]):
        return "conflict_repair"
    if any(key in text for key in ["约会", "暧昧", "邀请"]):
        return "dating_invitation"
    if any(key in text for key in ["边界", "拒绝", "越界"]):
        return "boundary_signal"
    if any(key in text for key in ["情绪", "委屈", "难过"]):
        return "emotion_validation"
    return "relationship_micro_signal"


def _dedupe_raw_content(item: RawContentItem, session: Session) -> dict:
    duplicate_count = 0
    if item.content_hash:
        duplicate_count = len(session.exec(
            select(RawContentItem)
            .where(RawContentItem.content_hash == item.content_hash)
            .where(RawContentItem.id != item.id)
        ).all())
    title_similarity_count = _title_similarity_count(item, session)
    duplicate_count += title_similarity_count
    return {
        "type": "dedupe_check",
        "duplicate_count": duplicate_count,
        "title_similarity_count": title_similarity_count,
        "decision": "duplicate_review_needed" if duplicate_count else "unique_enough",
    }


def _title_similarity_count(item: RawContentItem, session: Session) -> int:
    if not item.title:
        return 0
    tokens = _semantic_tokens(item.title)
    if not tokens:
        return 0
    peers = session.exec(
        select(RawContentItem)
        .where(RawContentItem.id != item.id)
        .where(RawContentItem.title.is_not(None))
        .limit(200)
    ).all()
    similar = 0
    for peer in peers:
        peer_tokens = _semantic_tokens(peer.title or "")
        if not peer_tokens:
            continue
        overlap = len(tokens & peer_tokens) / max(len(tokens | peer_tokens), 1)
        if overlap >= 0.72:
            similar += 1
    return similar


def _semantic_tokens(text: str) -> set[str]:
    return semantic_tokens(text)


def _ensure_annotation_job_for_raw(item: RawContentItem, result: dict, session: Session) -> AnnotationJob:
    existing = session.exec(
        select(AnnotationJob)
        .where(AnnotationJob.target_type == "raw_content")
        .where(AnnotationJob.target_id == item.id)
        .where(AnnotationJob.schema_version == "relationship-primitives-v1")
    ).first()
    if existing:
        existing.result_json = json.dumps(_annotation_result_for_raw(item, result), ensure_ascii=False)
        existing.confidence = float(result.get("confidence", existing.confidence or 0.65))
        existing.status = result.get("status", "draft")
        session.add(existing)
        return existing

    job = AnnotationJob(
        target_type="raw_content",
        target_id=item.id or 0,
        annotator_type=result.get("annotator_type", "rule"),
        annotator_version=result.get("annotator_version", "pipeline-v1"),
        schema_version="relationship-primitives-v1",
        result_json=json.dumps(_annotation_result_for_raw(item, result), ensure_ascii=False),
        confidence=float(result.get("confidence", 0.65)),
        status=result.get("status", "draft"),
    )
    session.add(job)
    session.flush()
    return job


def _annotation_result_for_raw(item: RawContentItem, result: dict) -> dict:
    return {
        "source_trace": {
            "raw_id": item.id,
            "raw_uuid": item.raw_uuid,
            "source_id": item.source_id,
            "content_hash": item.content_hash,
            "storage_policy": item.raw_storage_policy,
        },
        "primitive_layers": result.get("primitive_layers") or [
            "source_meta",
            "observable_signal",
            "emotion_hypothesis",
            "need_boundary",
            "response_pattern",
        ],
        "classification_axes": result.get("classification_axes") or [
            "scene",
            "relationship_stage",
            "emotion_flow",
            "attachment_signal",
            "boundary_pressure",
            "safety_risk",
        ],
        "quality_gates": {
            "privacy_risk": item.privacy_risk,
            "copyright_risk": item.copyright_risk,
            "confidence": result.get("confidence", 0.65),
        },
    }


def _ensure_asset_version_for_annotation(job: AnnotationJob, result: dict, session: Session) -> TrainingAssetVersion:
    existing = session.exec(
        select(TrainingAssetVersion)
        .where(TrainingAssetVersion.asset_type == "annotation")
        .where(TrainingAssetVersion.asset_id == job.id)
        .where(TrainingAssetVersion.version == result.get("version", "v1"))
    ).first()
    source_trace = {
        "annotation_job_id": job.id,
        "target_type": job.target_type,
        "target_id": job.target_id,
        "schema_version": job.schema_version,
    }
    quality = {
        "confidence": job.confidence,
        "review_status": job.status,
        "privacy": "abstract_only",
        "anti_manipulation": "required",
    }
    if existing:
        existing.source_trace_json = json.dumps(source_trace, ensure_ascii=False)
        existing.quality_json = json.dumps(quality, ensure_ascii=False)
        existing.review_status = result.get("review_status", "reviewed")
        session.add(existing)
        return existing

    asset = TrainingAssetVersion(
        asset_type="annotation",
        asset_id=job.id or 0,
        version=result.get("version", "v1"),
        source_trace_json=json.dumps(source_trace, ensure_ascii=False),
        quality_json=json.dumps(quality, ensure_ascii=False),
        review_status=result.get("review_status", "reviewed"),
    )
    session.add(asset)
    session.flush()
    return asset


def _create_batch_evolution_report(period_type: str, summary: dict, session: Session) -> EvolutionReport:
    pipeline_data = pipeline(session)
    key_insights = [
        f"本轮处理候选 {summary['raw_seen']} 条，完成脱敏 {summary['sanitized']} 条，去重 {summary['deduped']} 条。",
        f"自动标注 {summary['annotated']} 条，生成训练资产 {summary['asset_versions']} 个，发布资产 {summary['published_assets']} 个。",
        f"重复复核 {summary['duplicate_review_needed']} 条，跳过 {summary['skipped']} 条。",
        "下一步应把批处理结果接入样本多粒度标注和训练推荐权重。",
    ]
    report = EvolutionReport(
        period_type=period_type,
        title=f"数据生命体批量进化报告 {datetime.now().strftime('%Y-%m-%d %H:%M')}",
        summary=(
            "批量流水线已完成 sanitize、dedupe、annotate、publish 与报告沉淀；"
            f"当前发布训练资产数 {pipeline_data['stages'][4]['count']}。"
        ),
        new_items_count=summary["annotated"],
        promoted_samples_count=summary["published_assets"],
        key_insights_json=json.dumps(key_insights, ensure_ascii=False),
    )
    session.add(report)
    session.commit()
    session.refresh(report)
    return report


def _run_scheduled_evolution(data: ScheduledEvolutionRunRequest, session: Session) -> dict:
    batch_request = PipelineBatchRunRequest(
        limit=data.batch_limit,
        actions=["sanitize", "dedupe", "annotate", "publish", "report"],
        dry_run=data.dry_run,
        duplicate_policy=data.duplicate_policy,
        min_confidence=data.min_confidence,
        publish_review_status="published",
        report_period_type=data.period_type,
    )
    batch_result = _run_pipeline_batch(batch_request, session)
    dedupe = _build_dedupe_report(_recent_raw_items(session, data.batch_limit))
    import_quality = _build_import_quality_report(session)
    safety = _build_safety_events_report(_recent_safety_events(session, data.batch_limit))

    if data.dry_run:
        return {
            "dry_run": True,
            "period_type": data.period_type,
            "lookback_days": data.lookback_days,
            "batch": batch_result,
            "dedupe_report": dedupe,
            "import_quality": import_quality,
            "safety_events": safety,
            "next_actions": _scheduler_next_actions(batch_result, dedupe, import_quality, safety),
        }

    report = _create_scheduled_report(data, batch_result, dedupe, import_quality, safety, session)
    return {
        "dry_run": False,
        "period_type": data.period_type,
        "lookback_days": data.lookback_days,
        "batch": batch_result,
        "dedupe_report": dedupe,
        "import_quality": import_quality,
        "safety_events": safety,
        "report": _report_to_dict(report),
        "next_actions": _scheduler_next_actions(batch_result, dedupe, import_quality, safety),
    }


def _create_scheduled_report(
    data: ScheduledEvolutionRunRequest,
    batch_result: dict,
    dedupe: dict,
    import_quality: dict,
    safety: dict,
    session: Session,
) -> EvolutionReport:
    batch_summary = batch_result.get("summary", {}) if isinstance(batch_result.get("summary"), dict) else {}
    key_insights = [
        f"{data.period_type} 调度完成：新增标注 {batch_summary.get('annotated', 0)}，发布资产 {batch_summary.get('published_assets', 0)}。",
        f"去重报告发现相似簇 {dedupe['summary']['clusters']} 个，需复核候选 {dedupe['summary']['duplicate_review_needed']} 条。",
        f"导入质量：样本 {import_quality['totals']['samples']} 条，资源 {import_quality['totals']['resources']} 条，知识 {import_quality['totals']['knowledge_entries']} 条。",
        f"安全审计：阻断事件 {safety['summary']['blocked']} 条，主要风险 {safety['summary']['top_flags'][:3]}。",
    ]
    report = EvolutionReport(
        period_type=data.period_type,
        title=f"动态进化调度报告 {datetime.now().strftime('%Y-%m-%d %H:%M')}",
        summary=(
            "本地指挥官已完成周期性数据生命体检查：批量处理、语义去重、导入质量和安全事件均已纳入报告。"
        ),
        new_items_count=int(batch_summary.get("annotated", 0) or 0),
        promoted_samples_count=int(batch_summary.get("published_assets", 0) or 0),
        key_insights_json=json.dumps(key_insights, ensure_ascii=False),
    )
    session.add(report)
    session.commit()
    session.refresh(report)
    return report


def _recent_raw_items(session: Session, limit: int) -> list[RawContentItem]:
    return list(session.exec(select(RawContentItem).order_by(desc(RawContentItem.collected_at)).limit(limit)).all())


def _recent_safety_events(session: Session, limit: int) -> list[SafetyEvent]:
    return list(session.exec(select(SafetyEvent).order_by(desc(SafetyEvent.created_at)).limit(limit)).all())


def _build_dedupe_report(items: list[RawContentItem]) -> dict:
    return build_typed_dedupe_report([_raw_dedupe_candidate(item) for item in items])


def _semantic_dedupe_clusters(items: list[RawContentItem]) -> list[dict]:
    clusters = build_typed_dedupe_report([_raw_dedupe_candidate(item) for item in items])["clusters"]
    return [cluster for cluster in clusters if cluster.get("kind") == "semantic_title"]


def _dedupe_cluster(kind: str, items: list[RawContentItem]) -> dict:
    return _dedupe_cluster_from_candidates(kind, [_raw_dedupe_candidate(item) for item in items])


def _raw_dedupe_candidate(item: RawContentItem) -> RawDedupeCandidate:
    return RawDedupeCandidate(
        id=item.id,
        raw_uuid=item.raw_uuid,
        title=item.title,
        content_hash=item.content_hash,
        processing_status=item.processing_status,
        url=item.url,
        source_id=item.source_id,
    )


def _dedupe_cluster_from_candidates(kind: str, items: list[RawDedupeCandidate]) -> dict:
    return {
        "kind": kind,
        "item_ids": [item.id for item in items if item.id is not None],
        "raw_uuids": [item.raw_uuid for item in items],
        "titles": [item.title for item in items],
        "statuses": [item.processing_status for item in items],
        "recommendation": "merge_or_keep_best_metadata",
    }


def _build_import_quality_report(session: Session) -> dict:
    samples = list(session.exec(select(InteractionSample).limit(5000)).all())
    resources = list(session.exec(select(ResourceLibrary).limit(5000)).all())
    knowledge_entries = list(session.exec(select(KnowledgeEntry).limit(5000)).all())
    batches = list(session.exec(select(ContentImportBatch).order_by(desc(ContentImportBatch.created_at)).limit(20)).all())
    issues = list(session.exec(select(ContentImportIssue).order_by(desc(ContentImportIssue.created_at)).limit(100)).all())
    active_issues = _active_import_issues(issues)
    repair_plan = _import_quality_repair_preview(samples, resources, knowledge_entries)
    quality_debt = _import_quality_debt_summary(repair_plan, issues)
    issue_triage = _import_issue_triage(issues, samples, resources, knowledge_entries)
    return {
        "principle": "导入质量不是数量崇拜，而是来源可追踪、字段完整、JSON 合法、重复可控、问题可复盘。",
        "totals": {
            "samples": len(samples),
            "resources": len(resources),
            "knowledge_entries": len(knowledge_entries),
            "batches": len(batches),
            "issues": len(issues),
            "active_issues": len(active_issues),
        },
        "field_completeness": {
            "samples": _sample_completeness(samples),
            "resources": _resource_completeness(resources),
            "knowledge_entries": _knowledge_completeness(knowledge_entries),
        },
        "source_distribution": {
            "samples": _count_by(samples, "source"),
            "resources": _count_by(resources, "source"),
            "knowledge_entries": _count_by(knowledge_entries, "source"),
        },
        "issue_summary": {
            "by_severity": _count_by(issues, "severity"),
            "by_status": _count_import_issue_statuses(issues),
            "open": len(active_issues),
            "resolved": sum(1 for issue in issues if _normalized_import_issue_status(issue) == "resolved"),
            "recent": [_import_issue_to_dict(issue) for issue in issues[:10]],
        },
        "latest_batches": [_import_batch_to_dict(batch) for batch in batches[:5]],
        "quality_score": _import_quality_score(samples, resources, knowledge_entries, active_issues),
        "repair_plan": repair_plan,
        "quality_debt": quality_debt,
        "issue_triage": issue_triage,
    }


def _run_import_quality_repair(data: ImportQualityRepairRequest, session: Session) -> dict:
    samples = list(session.exec(select(InteractionSample).order_by(desc(InteractionSample.updated_at), desc(InteractionSample.id)).limit(data.limit)).all())
    resources = list(session.exec(select(ResourceLibrary).order_by(desc(ResourceLibrary.created_at), desc(ResourceLibrary.id)).limit(data.limit)).all())
    knowledge_entries = list(session.exec(select(KnowledgeEntry).order_by(desc(KnowledgeEntry.updated_at), desc(KnowledgeEntry.id)).limit(data.limit)).all())
    plan = _import_quality_repair_preview(samples, resources, knowledge_entries)
    if data.dry_run:
        return {
            "dry_run": True,
            "plan": plan,
            "quality_before": _import_quality_score(samples, resources, knowledge_entries, []),
            "principle": "补全计划只写来源、标签、摘要、质量等元数据，不生成或保存第三方全文。",
        }
    updated = {
        "samples": _repair_sample_metadata(samples, session),
        "resources": _repair_resource_metadata(resources, session),
        "knowledge_entries": _repair_knowledge_metadata(knowledge_entries, session),
    }
    session.commit()
    refreshed_samples = list(session.exec(select(InteractionSample).limit(data.limit)).all())
    refreshed_resources = list(session.exec(select(ResourceLibrary).limit(data.limit)).all())
    refreshed_knowledge = list(session.exec(select(KnowledgeEntry).limit(data.limit)).all())
    return {
        "dry_run": False,
        "updated": updated,
        "quality_after": _import_quality_score(refreshed_samples, refreshed_resources, refreshed_knowledge, []),
        "plan": _import_quality_repair_preview(refreshed_samples, refreshed_resources, refreshed_knowledge),
        "principle": "已补全的仅是可审计元数据与训练辅助字段，未写入敏感原文或第三方全文。",
    }


def _import_quality_repair_preview(
    samples: list[InteractionSample],
    resources: list[ResourceLibrary],
    knowledge_entries: list[KnowledgeEntry],
) -> dict:
    return {
        "samples": _missing_field_counts(samples, ["source_trace_json", "quality_json"]),
        "resources": _missing_field_counts(resources, ["applicable_scene", "usage_tip", "emotional_tone_json"]),
        "knowledge_entries": _missing_field_counts(knowledge_entries, ["summary", "tags_json", "source_metadata_json"]),
        "strategy": [
            "samples: derive source_trace/quality metadata from existing sample fields",
            "resources: derive usage tips, scene fallback, and tone tags from category/type",
            "knowledge: derive summary, tags, and source metadata from existing structured fields",
        ],
    }


def _missing_field_counts(items: list, fields: list[str]) -> dict[str, int]:
    return {field: sum(1 for item in items if not _has_value(getattr(item, field, None))) for field in fields}


def _import_quality_debt_summary(repair_plan: dict, issues: list[ContentImportIssue]) -> dict:
    auto_repairable = sum(
        count
        for section in ("samples", "resources", "knowledge_entries")
        for count in repair_plan.get(section, {}).values()
        if isinstance(count, int)
    )
    active_issues = _active_import_issues(issues)
    manual_review = len(active_issues)
    resolved = sum(1 for issue in issues if _normalized_import_issue_status(issue) == "resolved")
    return {
        "auto_repairable_fields": auto_repairable,
        "manual_review_issues": manual_review,
        "resolved_issues": resolved,
        "issue_status": _count_import_issue_statuses(issues),
        "status": "auto_repair_available" if auto_repairable else ("manual_review_required" if manual_review else "clean"),
        "next_actions": _import_quality_debt_actions(auto_repairable, manual_review),
    }


def _import_issue_triage(
    issues: list[ContentImportIssue],
    samples: list[InteractionSample],
    resources: list[ResourceLibrary],
    knowledge_entries: list[KnowledgeEntry],
) -> dict:
    active = _active_import_issues(issues)
    grouped: dict[str, list[ContentImportIssue]] = {}
    for issue in active:
        grouped.setdefault(issue.source_name or "unknown", []).append(issue)

    buckets: dict[str, list[dict]] = {
        "batch_closable": [],
        "source_review_required": [],
        "manual_reimport_required": [],
    }
    closable_ids: set[int] = set()
    for source_name, rows in grouped.items():
        bucket = _import_issue_triage_bucket(rows)
        issue_ids = [int(issue.id or 0) for issue in rows]
        if bucket == "batch_closable":
            closable_ids.update(issue_ids)
        buckets[bucket].append({
            "source_name": source_name,
            "issue_count": len(rows),
            "sample_issue_ids": issue_ids[:5],
            "by_severity": _count_by(rows, "severity"),
            "by_status": _count_import_issue_statuses(rows),
            "recommended_action": _import_issue_triage_action(bucket),
        })

    for rows in buckets.values():
        rows.sort(key=lambda item: (-int(item["issue_count"]), str(item["source_name"])))

    remaining = [issue for issue in active if int(issue.id or 0) not in closable_ids]
    current_score = _import_quality_score(samples, resources, knowledge_entries, active)
    projected_score = _import_quality_score(samples, resources, knowledge_entries, remaining)
    return {
        "summary": {
            "active_issue_count": len(active),
            "batch_closable_sources": len(buckets["batch_closable"]),
            "batch_closable_issues": sum(int(item["issue_count"]) for item in buckets["batch_closable"]),
            "source_review_required_sources": len(buckets["source_review_required"]),
            "source_review_required_issues": sum(int(item["issue_count"]) for item in buckets["source_review_required"]),
            "manual_reimport_required_sources": len(buckets["manual_reimport_required"]),
            "manual_reimport_required_issues": sum(int(item["issue_count"]) for item in buckets["manual_reimport_required"]),
            "current_score": current_score,
            "projected_score_after_batch_closable": projected_score,
        },
        "buckets": buckets,
        "next_actions": _import_issue_triage_next_actions(buckets),
        "quality_gate": {
            "auto_close_allowed": False,
            "requires_reviewer": True,
            "requires_resolution_reason": True,
        },
    }


def _import_issue_triage_bucket(issues: list[ContentImportIssue]) -> str:
    severity_counts = _count_by(issues, "severity")
    statuses = {_normalized_import_issue_status(issue) for issue in issues}
    messages = " ".join((issue.message or "").lower() for issue in issues)
    reimport_markers = ("格式", "解析", "导入失败", "schema", "contract", "json", "reimport")
    if severity_counts.get("error", 0) > 0 or "reopened" in statuses:
        return "source_review_required"
    if any(marker in messages for marker in reimport_markers):
        return "manual_reimport_required"
    return "batch_closable"


def _import_issue_triage_action(bucket: str) -> str:
    if bucket == "batch_closable":
        return "batch review source evidence, then resolve with shared reviewer note"
    if bucket == "manual_reimport_required":
        return "repair import format or rerun source import before closure"
    return "review source contract, license, and error evidence before closure"


def _import_issue_triage_next_actions(buckets: dict[str, list[dict]]) -> list[str]:
    actions: list[str] = []
    if buckets["manual_reimport_required"]:
        actions.append("fix malformed or contract-mismatched imports first")
    if buckets["source_review_required"]:
        actions.append("review error or reopened source groups before resolving")
    if buckets["batch_closable"]:
        actions.append("batch close warning-only sources after reviewer evidence is written")
    if not actions:
        actions.append("keep import issue queue under regression monitoring")
    return actions


def _active_import_issues(issues: list[ContentImportIssue]) -> list[ContentImportIssue]:
    return [issue for issue in issues if _normalized_import_issue_status(issue) in {"open", "review_requested", "reopened"}]


def _count_import_issue_statuses(issues: list[ContentImportIssue]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for issue in issues:
        status = _normalized_import_issue_status(issue)
        counts[status] = counts.get(status, 0) + 1
    return counts


def _import_issue_governance_summary(session: Session) -> dict:
    issues = list(session.exec(select(ContentImportIssue).limit(5000)).all())
    active = _active_import_issues(issues)
    return {
        "total": len(issues),
        "active": len(active),
        "resolved": sum(1 for issue in issues if _normalized_import_issue_status(issue) == "resolved"),
        "by_status": _count_import_issue_statuses(issues),
        "by_severity": _count_by(active, "severity"),
        "quality_gate": {
            "requires_resolution_reason": True,
            "requires_reviewer": True,
            "auto_close_allowed": False,
        },
    }


def _import_issue_audit_history(session: Session, limit: int) -> dict:
    logs = list(session.exec(
        select(PipelineRunLog)
        .where(PipelineRunLog.target_type == "content_import_issue")
        .order_by(desc(PipelineRunLog.created_at), desc(PipelineRunLog.id))
        .limit(limit)
    ).all())
    items = [_import_issue_audit_log_to_dict(log) for log in logs]
    return {
        "items": items,
        "total": len(items),
        "summary": _import_issue_audit_summary(items),
        "quality_gate": {
            "raw_source_text_saved": False,
            "resolution_text_returned": False,
            "requires_pipeline_log": True,
            "auto_close_allowed": False,
        },
        "principle": "导入 issue 审计历史只返回元数据、状态、哈希与安全标记，不回显人工说明全文或任何来源原文。",
    }


def _import_issue_audit_log_to_dict(log: PipelineRunLog) -> dict:
    result = _loads_dict(log.result_json)
    resolution_hash = result.get("resolution_hash")
    if not resolution_hash and _has_value(result.get("resolution")):
        resolution_hash = "sha256:" + hashlib.sha256(str(result["resolution"]).encode("utf-8")).hexdigest()
    safety = result.get("safety") if isinstance(result.get("safety"), dict) else {}
    return {
        "id": log.id,
        "issue_id": log.target_id,
        "action": log.action.replace("import_issue_", ""),
        "source_name": result.get("source_name"),
        "source_id": result.get("source_id"),
        "severity": result.get("severity"),
        "from_status": log.from_status or result.get("from_status"),
        "to_status": log.to_status or result.get("to_status"),
        "reviewer_id": result.get("reviewer_id"),
        "resolution_hash": resolution_hash,
        "safety": {
            "raw_source_text_saved": bool(safety.get("raw_source_text_saved", False)),
            "resolution_text_returned": False,
            "auto_close_allowed": bool(safety.get("auto_close_allowed", False)),
        },
        "created_at": log.created_at.isoformat(),
    }


def _import_issue_audit_summary(items: list[dict]) -> dict:
    return {
        "actions": _count_dict_field(items, "action"),
        "to_status": _count_dict_field(items, "to_status"),
        "sources": _count_dict_field(items, "source_name"),
        "severity": _count_dict_field(items, "severity"),
        "reviewers": _count_dict_field(items, "reviewer_id"),
        "unsafe_log_count": sum(
            1
            for item in items
            if item["safety"]["raw_source_text_saved"] or item["safety"]["resolution_text_returned"] or item["safety"]["auto_close_allowed"]
        ),
    }


def _count_dict_field(items: list[dict], field: str) -> dict[str, int]:
    counts: dict[str, int] = {}
    for item in items:
        key = str(item.get(field) or "unknown")
        counts[key] = counts.get(key, 0) + 1
    return counts


def _import_issue_source_groups(session: Session, limit: int = 20) -> list[dict]:
    issues = list(session.exec(select(ContentImportIssue).limit(5000)).all())
    grouped: dict[str, list[ContentImportIssue]] = {}
    for issue in issues:
        grouped.setdefault(issue.source_name or "unknown", []).append(issue)
    groups = [_import_issue_source_group(source_name, rows) for source_name, rows in grouped.items()]
    groups.sort(key=lambda item: (-int(item["active_issues"]), -int(item["severity_weight"]), str(item["source_name"])))
    return groups[:limit]


def _import_issue_source_group(source_name: str, issues: list[ContentImportIssue]) -> dict:
    active = _active_import_issues(issues)
    severity_counts = _count_by(active, "severity")
    severity_weight = severity_counts.get("error", 0) * 3 + severity_counts.get("warning", 0) * 2 + severity_counts.get("info", 0)
    oldest = min((issue.created_at for issue in active), default=None)
    newest = max((issue.updated_at for issue in active), default=None)
    return {
        "source_name": source_name,
        "total_issues": len(issues),
        "active_issues": len(active),
        "resolved_issues": sum(1 for issue in issues if _normalized_import_issue_status(issue) == "resolved"),
        "by_status": _count_import_issue_statuses(issues),
        "by_severity": severity_counts,
        "severity_weight": severity_weight,
        "oldest_active_at": oldest.isoformat() if oldest else None,
        "latest_active_at": newest.isoformat() if newest else None,
        "sample_issue_ids": [int(issue.id or 0) for issue in active[:5]],
        "recommended_action": _import_issue_group_action(len(active), severity_counts),
        "review_packet": _import_issue_source_review_packet(source_name, issues, active, severity_counts),
    }


def _import_issue_group_action(active_count: int, severity_counts: dict[str, int]) -> str:
    if active_count == 0:
        return "keep under regression monitoring"
    if severity_counts.get("error", 0) > 0:
        return "review source contract and resolve error-level import defects first"
    if active_count >= 10:
        return "batch review source metadata and close with shared resolution evidence"
    return "review issue evidence and close or request re-review"


def _import_issue_source_review_packet(
    source_name: str,
    issues: list[ContentImportIssue],
    active: list[ContentImportIssue],
    severity_counts: dict[str, int],
) -> dict:
    action = _import_issue_group_action(len(active), severity_counts)
    can_close_batch = bool(active) and severity_counts.get("error", 0) == 0
    return {
        "source_name": source_name,
        "scope": {
            "total_issues": len(issues),
            "active_issues": len(active),
            "resolved_issues": sum(1 for issue in issues if _normalized_import_issue_status(issue) == "resolved"),
            "status_counts": _count_import_issue_statuses(issues),
            "severity_counts": severity_counts,
        },
        "evidence_checklist": _import_issue_evidence_checklist(severity_counts),
        "sample_evidence": [_import_issue_review_sample(issue) for issue in active[:3]],
        "batch_action": {
            "recommended_action": action,
            "candidate_issue_ids": [int(issue.id or 0) for issue in active[:20]],
            "can_close_batch": can_close_batch,
            "default_action": "resolve" if can_close_batch else "request_review",
            "requires_resolution": True,
            "requires_reviewer": True,
            "auto_close_allowed": False,
        },
        "quality_gate": {
            "has_active_issues": bool(active),
            "error_level_requires_source_contract_review": severity_counts.get("error", 0) > 0,
            "resolution_text_returned": False,
            "raw_source_text_returned": False,
            "third_party_full_text_returned": False,
        },
        "principle": "来源复核包只提供聚合指标、短消息样例和证据清单；关闭仍必须由人工 reviewer 写入 resolution。",
    }


def _import_issue_evidence_checklist(severity_counts: dict[str, int]) -> list[dict[str, str]]:
    items = [
        {
            "id": "source_registry",
            "label": "核对来源登记",
            "required_for": "all",
            "evidence": "source_name/source_id 与 content_sources 或导入批次记录一致。",
        },
        {
            "id": "batch_report",
            "label": "核对导入批次报告",
            "required_for": "all",
            "evidence": "确认 imported/skipped/issues 数与当前 issue 分布一致。",
        },
        {
            "id": "resolution_note",
            "label": "写入人工处理说明",
            "required_for": "resolve",
            "evidence": "说明只写处理证据，不粘贴第三方全文或敏感原文。",
        },
    ]
    if severity_counts.get("error", 0) > 0:
        items.insert(1, {
            "id": "source_contract",
            "label": "复核来源契约",
            "required_for": "error",
            "evidence": "确认许可、字段契约、隐私/版权边界和导入格式后再关闭 error issue。",
        })
    return items


def _import_issue_review_sample(issue: ContentImportIssue) -> dict:
    message = issue.message or ""
    return {
        "issue_id": issue.id,
        "source_id": issue.source_id,
        "severity": issue.severity,
        "status": _normalized_import_issue_status(issue),
        "message_summary": message[:140],
        "message_hash": "sha256:" + hashlib.sha256(message.encode("utf-8")).hexdigest(),
        "updated_at": issue.updated_at.isoformat(),
    }


def _import_quality_debt_actions(auto_repairable: int, manual_review: int) -> list[str]:
    actions: list[str] = []
    if auto_repairable:
        actions.append("run import-quality repair plan before manual review")
    if manual_review:
        actions.append("review historical import issues and resolve source-level defects")
    if not actions:
        actions.append("keep import quality under regression monitoring")
    return actions


def _apply_import_issue_action(data: ImportIssueActionRequest, session: Session) -> dict:
    issues = list(session.exec(select(ContentImportIssue).where(ContentImportIssue.id.in_(data.issue_ids))).all())
    found_ids = {issue.id for issue in issues}
    missing_ids = [issue_id for issue_id in data.issue_ids if issue_id not in found_ids]
    if missing_ids:
        raise HTTPException(status_code=404, detail={"missing_issue_ids": missing_ids})
    if data.action == "resolve" and not _has_value(data.resolution):
        raise HTTPException(status_code=422, detail="resolve 必须提供 resolution，说明来源问题如何被人工确认或关闭")
    transitions = [_import_issue_transition(issue, data) for issue in issues]
    if data.dry_run:
        return {
            "dry_run": True,
            "action": data.action,
            "transitions": transitions,
            "governance_report": _import_issue_governance_action_report(data, issues, transitions, []),
            "summary": _import_issue_governance_summary(session),
            "principle": "dry-run 只预演状态变更；真实执行会写 issue 字段和 pipeline_run_logs。",
        }
    now = datetime.now()
    logs: list[PipelineRunLog] = []
    for issue in issues:
        before = _normalized_import_issue_status(issue)
        after = _target_import_issue_status(data.action)
        issue.status = after
        issue.reviewer_id = data.reviewer_id
        issue.updated_at = now
        if data.action == "resolve":
            issue.resolution = data.resolution
            issue.resolved_at = now
        elif data.action == "request_review":
            issue.resolution = data.resolution
            issue.resolved_at = None
        elif data.action == "reopen":
            issue.resolution = data.resolution or f"reopened by {data.reviewer_id}"
            issue.resolved_at = None
        session.add(issue)
        log = PipelineRunLog(
            target_type="content_import_issue",
            target_id=issue.id or 0,
            action=f"import_issue_{data.action}",
            from_status=before,
            to_status=after,
            result_json=json.dumps(_import_issue_audit_payload(issue, data, before, after), ensure_ascii=False),
            message=_import_issue_log_message(data),
        )
        session.add(log)
        logs.append(log)
    session.commit()
    for issue in issues:
        session.refresh(issue)
    for log in logs:
        session.refresh(log)
    return {
        "dry_run": False,
        "action": data.action,
        "transitions": [_import_issue_transition(issue, data) for issue in issues],
        "audit_logs": [
            {"id": log.id, "target_id": log.target_id, "action": log.action, "created_at": log.created_at.isoformat()}
            for log in logs
        ],
        "governance_report": _import_issue_governance_action_report(data, issues, [_import_issue_transition(issue, data) for issue in issues], logs),
        "summary": _import_issue_governance_summary(session),
        "principle": "历史导入 issue 的关闭、复审和重开均以 SQLite 状态字段和 pipeline_run_logs 为审计主真源。",
    }


def _import_issue_transition(issue: ContentImportIssue, data: ImportIssueActionRequest) -> dict:
    return {
        "issue_id": issue.id,
        "from_status": _normalized_import_issue_status(issue),
        "to_status": _target_import_issue_status(data.action),
        "reviewer_id": data.reviewer_id,
        "requires_resolution": data.action == "resolve",
    }


def _import_issue_governance_action_report(
    data: ImportIssueActionRequest,
    issues: list[ContentImportIssue],
    transitions: list[dict],
    logs: list[PipelineRunLog],
) -> dict:
    source_counts: dict[str, int] = {}
    severity_counts: dict[str, int] = {}
    for issue in issues:
        source_counts[issue.source_name] = source_counts.get(issue.source_name, 0) + 1
        severity_counts[issue.severity] = severity_counts.get(issue.severity, 0) + 1
    return {
        "action": data.action,
        "issue_count": len(issues),
        "reviewer_id": data.reviewer_id,
        "resolution_hash": "sha256:" + hashlib.sha256((data.resolution or "").encode("utf-8")).hexdigest() if data.resolution else None,
        "source_counts": source_counts,
        "severity_counts": severity_counts,
        "from_status_counts": _count_transition_statuses(transitions, "from_status"),
        "to_status_counts": _count_transition_statuses(transitions, "to_status"),
        "audit_log_ids": [int(log.id or 0) for log in logs],
        "next_action": _import_issue_action_next_step(data.action, len(issues)),
        "safety": {
            "raw_source_text_saved": False,
            "resolution_text_returned": False,
            "auto_close_allowed": False,
        },
    }


def _count_transition_statuses(transitions: list[dict], field: str) -> dict[str, int]:
    counts: dict[str, int] = {}
    for item in transitions:
        status = str(item.get(field) or "unknown")
        counts[status] = counts.get(status, 0) + 1
    return counts


def _import_issue_action_next_step(action: str, issue_count: int) -> str:
    if action == "resolve":
        return f"record closure evidence and re-run regression audit for {issue_count} issue(s)"
    if action == "request_review":
        return f"assign reviewer and collect source evidence for {issue_count} issue(s)"
    return f"re-triage reopened source defects for {issue_count} issue(s)"


def _import_issue_log_message(data: ImportIssueActionRequest) -> str:
    resolution_hash = "sha256:" + hashlib.sha256((data.resolution or "").encode("utf-8")).hexdigest() if data.resolution else "none"
    return f"import issue governance action: {data.action}; resolution_hash={resolution_hash}"


def _target_import_issue_status(action: str) -> str:
    return {
        "resolve": "resolved",
        "request_review": "review_requested",
        "reopen": "reopened",
    }[action]


def _import_issue_audit_payload(
    issue: ContentImportIssue,
    data: ImportIssueActionRequest,
    before: str,
    after: str,
) -> dict:
    return {
        "issue_id": issue.id,
        "source_name": issue.source_name,
        "source_id": issue.source_id,
        "severity": issue.severity,
        "action": data.action,
        "from_status": before,
        "to_status": after,
        "reviewer_id": data.reviewer_id,
        "resolution_hash": "sha256:" + hashlib.sha256((data.resolution or "").encode("utf-8")).hexdigest() if data.resolution else None,
        "safety": {
            "raw_source_text_saved": False,
            "resolution_text_returned": False,
            "auto_close_allowed": False,
        },
    }


def _repair_sample_metadata(samples: list[InteractionSample], session: Session) -> int:
    updated = 0
    for sample in samples:
        changed = False
        if not _has_value(sample.source_trace_json):
            sample.source_trace_json = json.dumps({
                "source": sample.source or "sqlite_sample",
                "source_url": sample.source_url,
                "sample_uuid": sample.sample_uuid,
            }, ensure_ascii=False)
            changed = True
        if not _has_value(sample.quality_json):
            sample.quality_json = json.dumps({
                "relationship_realism": 0.74,
                "training_value": 0.76,
                "safety_score": 0.9 if (sample.boundary_test_level or 1) <= 7 else 0.78,
                "repair_source": "import_quality_repair",
            }, ensure_ascii=False)
            changed = True
        if changed:
            sample.updated_at = datetime.now()
            session.add(sample)
            updated += 1
    return updated


def _repair_resource_metadata(resources: list[ResourceLibrary], session: Session) -> int:
    updated = 0
    for resource in resources:
        changed = False
        if not _has_value(resource.applicable_scene):
            resource.applicable_scene = _resource_scene_fallback(resource)
            changed = True
        if not _has_value(resource.usage_tip):
            resource.usage_tip = f"用于{resource.applicable_scene or resource.category}场景，保持轻量、尊重边界。"
            changed = True
        if not _has_value(resource.emotional_tone_json):
            resource.emotional_tone_json = json.dumps([resource.category, resource.type], ensure_ascii=False)
            changed = True
        if changed:
            session.add(resource)
            updated += 1
    return updated


def _repair_knowledge_metadata(entries: list[KnowledgeEntry], session: Session) -> int:
    updated = 0
    for entry in entries:
        changed = False
        if not _has_value(entry.summary):
            entry.summary = entry.content[:160]
            changed = True
        if not _has_value(entry.tags_json):
            entry.tags_json = json.dumps([entry.category, entry.source], ensure_ascii=False)
            changed = True
        if not _has_value(entry.source_metadata_json):
            entry.source_metadata_json = json.dumps({
                "source": entry.source,
                "source_id": entry.source_id,
                "entry_uuid": entry.entry_uuid,
                "repair_source": "import_quality_repair",
            }, ensure_ascii=False)
            changed = True
        if changed:
            entry.updated_at = datetime.now()
            session.add(entry)
            updated += 1
    return updated


def _resource_scene_fallback(resource: ResourceLibrary) -> str:
    if resource.type in {"joke", "riddle", "game"}:
        return "初识"
    if resource.type in {"flirty", "phrase"}:
        return "暧昧"
    if resource.type == "story":
        return "修复"
    return resource.category or "通用"


def _sample_completeness(samples: list[InteractionSample]) -> dict:
    required = ["context", "their_words", "emotion_tags_json", "bad_response", "good_response_soft"]
    enriched = [
        "five_w_two_h_json",
        "signal_highlights_json",
        "emotion_flow_json",
        "need_radar_json",
        "boundary_state_json",
        "source_trace_json",
        "quality_json",
    ]
    return {
        "required": _field_fill_rates(samples, required),
        "enriched": _field_fill_rates(samples, enriched),
        "json_invalid": _json_invalid_count(samples, ["emotion_tags_json", *enriched]),
    }


def _resource_completeness(resources: list[ResourceLibrary]) -> dict:
    fields = ["content", "category", "applicable_scene", "usage_tip", "emotional_tone_json"]
    return {
        "required": _field_fill_rates(resources, fields),
        "json_invalid": _json_invalid_count(resources, ["emotional_tone_json"]),
    }


def _knowledge_completeness(entries: list[KnowledgeEntry]) -> dict:
    fields = ["title", "content", "summary", "tags_json", "source_metadata_json"]
    return {
        "required": _field_fill_rates(entries, fields),
        "json_invalid": _json_invalid_count(entries, ["tags_json", "source_metadata_json"]),
    }


def _field_fill_rates(items: list, fields: list[str]) -> dict[str, float]:
    rates: dict[str, float] = {}
    for field in fields:
        filled = sum(1 for item in items if _has_value(getattr(item, field, None)))
        rates[field] = round(filled / max(len(items), 1), 3)
    return rates


def _has_value(value) -> bool:
    if value is None:
        return False
    if isinstance(value, str):
        return bool(value.strip())
    return True


def _json_invalid_count(items: list, fields: list[str]) -> int:
    invalid = 0
    for item in items:
        for field in fields:
            value = getattr(item, field, None)
            if not _has_value(value):
                continue
            try:
                json.loads(str(value))
            except json.JSONDecodeError:
                invalid += 1
    return invalid


def _import_quality_score(
    samples: list[InteractionSample],
    resources: list[ResourceLibrary],
    knowledge_entries: list[KnowledgeEntry],
    issues: list[ContentImportIssue],
) -> float:
    sample_core = _average(list(_sample_completeness(samples)["required"].values()))
    resource_core = _average(list(_resource_completeness(resources)["required"].values()))
    knowledge_core = _average(list(_knowledge_completeness(knowledge_entries)["required"].values()))
    issue_penalty = min(25, len(issues) * 1.5)
    return round(max(0, min(100, (sample_core + resource_core + knowledge_core) / 3 * 100 - issue_penalty)), 1)


def _import_issue_to_dict(issue: ContentImportIssue) -> dict:
    resolution_hash = "sha256:" + hashlib.sha256(issue.resolution.encode("utf-8")).hexdigest() if _has_value(issue.resolution) else None
    return {
        "id": issue.id,
        "batch_id": issue.batch_id,
        "source_name": issue.source_name,
        "source_id": issue.source_id,
        "severity": issue.severity,
        "message": issue.message,
        "status": _normalized_import_issue_status(issue),
        "reviewer_id": issue.reviewer_id,
        "resolution_hash": resolution_hash,
        "resolved_at": issue.resolved_at.isoformat() if issue.resolved_at else None,
        "created_at": issue.created_at.isoformat(),
        "updated_at": issue.updated_at.isoformat(),
    }


def _normalized_import_issue_status(issue: ContentImportIssue) -> str:
    status = (issue.status or "").strip()
    return status if status else "open"


def _import_batch_to_dict(batch: ContentImportBatch) -> dict:
    return {
        "id": batch.id,
        "source_name": batch.source_name,
        "source_type": batch.source_type,
        "imported_sections": batch.imported_sections,
        "imported_entries": batch.imported_entries,
        "skipped_entries": batch.skipped_entries,
        "issues_count": batch.issues_count,
        "status": batch.status,
        "report": _loads_dict(batch.report_json),
        "created_at": batch.created_at.isoformat(),
    }


def _hash_text(value: str) -> str:
    return "sha256:" + hashlib.sha256(value.encode("utf-8")).hexdigest()


def _safe_ratio(numerator: int | float, denominator: int | float) -> float:
    if not denominator:
        return 0.0
    return round(float(numerator) / float(denominator), 4)


def _build_safety_events_report(events: list[SafetyEvent]) -> dict:
    return build_typed_safety_events_report([_safety_event_snapshot(event) for event in events])


def _safety_event_to_dict(event: SafetyEvent) -> dict:
    return build_typed_safety_events_report([_safety_event_snapshot(event)])["events"][0]


def _safety_event_snapshot(event: SafetyEvent) -> SafetyEventSnapshot:
    return SafetyEventSnapshot(
        id=event.id,
        task_type=event.task_type,
        source=event.source,
        risk_level=event.risk_level,
        flags_json=event.flags_json,
        payload_hash=event.payload_hash,
        payload_preview=event.payload_preview,
        message=event.message,
        alternatives_json=event.alternatives_json,
        blocked=event.blocked,
        created_at_iso=event.created_at.isoformat(),
    )


def _scheduler_next_actions(batch_result: dict, dedupe: dict, import_quality: dict, safety: dict) -> list[dict]:
    return typed_scheduler_next_actions(batch_result, dedupe, import_quality, safety)


def _loads_list(text: str | None) -> list:
    return typed_loads_list(text)


def _loads_dict(text: str | None) -> dict:
    return typed_loads_dict(text)


def _count_by(items: list, field: str) -> dict:
    counts: dict[str, int] = {}
    for item in items:
        key = str(getattr(item, field, "unknown") or "unknown")
        counts[key] = counts.get(key, 0) + 1
    return counts


def _count_published_assets(assets: list[TrainingAssetVersion]) -> int:
    return sum(1 for asset in assets if asset.review_status == "published")


def _reviewed_asset_inventory(
    samples: list[InteractionSample],
    resources: list[ResourceLibrary],
    knowledge_entries: list[KnowledgeEntry],
) -> dict:
    sample_status = _status_counts(samples, "review_status")
    resource_status = _status_counts(resources, "review_status")
    knowledge_status = _status_counts(knowledge_entries, "review_status")
    return {
        "samples": sample_status,
        "resources": resource_status,
        "knowledge_entries": knowledge_status,
        "draft": _status_total(samples, "draft") + _status_total(resources, "draft") + _status_total(knowledge_entries, "draft"),
        "reviewed": _status_total(samples, "reviewed") + _status_total(resources, "reviewed") + _status_total(knowledge_entries, "reviewed"),
        "published": _status_total(samples, "published") + _status_total(resources, "published") + _status_total(knowledge_entries, "published"),
        "gold": _status_total(samples, "gold"),
    }


def _reviewed_asset_next_actions(inventory: dict) -> list[dict]:
    actions: list[dict] = []
    if inventory["draft"] > 0:
        actions.append({
            "priority": "high",
            "action": "推进 draft 资产到 reviewed",
            "reason": f"仍有 {inventory['draft']} 条资产停留在 draft。",
        })
    if inventory["reviewed"] > 0 and inventory["published"] == 0:
        actions.append({
            "priority": "high",
            "action": "发布 reviewed 资产",
            "reason": "已有 reviewed 资产，但尚未进入 published。",
        })
    if not actions:
        actions.append({
            "priority": "low",
            "action": "维持发布治理",
            "reason": "三类资产都已进入稳定状态。",
        })
    return actions


def _backfill_resource_review_status(resources: list[ResourceLibrary], force: bool, session: Session) -> int:
    updated = 0
    for resource in resources:
        candidate = _resource_publish_candidate(resource)
        target_status = "published" if candidate["publish_ready"] else "reviewed"
        if not force and resource.review_status == target_status and resource.reviewed_at is not None:
            continue
        resource.review_status = target_status
        resource.reviewed_at = resource.reviewed_at or datetime.now()
        if target_status == "published" and resource.published_at is None:
            resource.published_at = datetime.now()
        session.add(resource)
        updated += 1
    return updated


def _backfill_knowledge_review_status(entries: list[KnowledgeEntry], force: bool, session: Session) -> int:
    updated = 0
    for entry in entries:
        target_status = "published" if entry.quality_score >= 80 else "reviewed"
        if not force and entry.review_status == target_status and entry.reviewed_at is not None:
            continue
        entry.review_status = target_status
        entry.reviewed_at = entry.reviewed_at or datetime.now()
        if target_status == "published" and entry.published_at is None:
            entry.published_at = datetime.now()
        session.add(entry)
        updated += 1
    return updated


def _resource_publish_candidate(resource: ResourceLibrary) -> dict:
    score = int(resource.effectiveness_rating or 0) * 10
    reasons = []
    blocks: list[str] = []
    if resource.effectiveness_rating and resource.effectiveness_rating >= 8:
        reasons.append("高效果评分")
    if _has_value(resource.applicable_scene):
        score += 8
        reasons.append("有适用场景")
    if _has_value(resource.usage_tip):
        score += 8
        reasons.append("有使用提示")
    if _has_value(resource.emotional_tone_json):
        score += 4
        reasons.append("有情绪基调")
    if _resource_needs_manual_curation(resource):
        score = min(score, 79)
        blocks.append("resource lacks concrete scenario/practice evidence for publish")
        reasons.append("需补充具体案例与练习结构")
    if _resource_has_legacy_enrichment_debt(resource):
        score = min(score, 79)
        blocks.append("legacy enrichment debt requires case-level curation before publish")
        reasons.append("历史补全债需先完成案例级策展")
    if _resource_lacks_boundary_evidence_for_high_tension(resource):
        score = min(score, 79)
        blocks.append("high-tension content requires explicit boundary/consent evidence")
        reasons.append("高张力内容需明确边界、同意和可拒绝退路")
    score = min(100, score)
    return {
        "asset_type": "resource",
        "id": resource.id,
        "uuid": resource.resource_uuid,
        "title": resource.title or resource.content[:40],
        "category": resource.category,
        "review_status": resource.review_status,
        "reviewed_at": resource.reviewed_at.isoformat() if resource.reviewed_at else None,
        "published_at": resource.published_at.isoformat() if resource.published_at else None,
        "quality_signal": {
            "effectiveness_rating": resource.effectiveness_rating,
            "quality_score": resource.quality_score,
            "blocks": blocks,
        },
        "publish_ready": score >= 85 and not blocks,
        "priority": {"score": score, "reasons": reasons or ["常规 reviewed 候选"]},
    }


def _knowledge_publish_candidate(entry: KnowledgeEntry) -> dict:
    score = int(entry.quality_score)
    reasons = ["高知识质量"] if entry.quality_score >= 80 else []
    blocks: list[str] = []
    if entry.quality_score < 80:
        score = min(score, 79)
        blocks.append("knowledge quality_score below publish baseline")
        reasons.append("知识质量分低于发布基线")
    if _has_value(entry.summary):
        score += 6
        reasons.append("有摘要")
    if _has_value(entry.tags_json):
        score += 5
        reasons.append("有标签")
    if _has_value(entry.source_metadata_json):
        score += 4
        reasons.append("有来源元数据")
    if _knowledge_needs_manual_curation(entry):
        score = min(score, 79)
        blocks.append("legacy/manual generic content requires curation before publish")
        reasons.append("需人工内容策展")
    score = min(100, score)
    return {
        "asset_type": "knowledge_entry",
        "id": entry.id,
        "uuid": entry.entry_uuid,
        "title": entry.title,
        "category": entry.category,
        "review_status": entry.review_status,
        "reviewed_at": entry.reviewed_at.isoformat() if entry.reviewed_at else None,
        "published_at": entry.published_at.isoformat() if entry.published_at else None,
        "quality_signal": {"quality_score": entry.quality_score, "blocks": blocks},
        "publish_ready": score >= 85 and not blocks,
        "priority": {"score": score, "reasons": reasons or ["常规 reviewed 候选"]},
    }


def _boutique_resource_specs() -> list[dict]:
    base = [
        ("micro_signal", "story", "微关系信号", "电梯里突然安静后的轻验证", "初识", "情绪标注", "把沉默从拒绝解释成可验证信号"),
        ("emotion_flow", "game", "情绪流动", "失望变冷淡时的三句修复", "修复", "共情反射", "让情绪从防御回到可对话"),
        ("boundary_consent", "knowledge_card", "边界与同意", "暧昧升级前的可退出邀请", "暧昧", "退路设计", "让靠近不变成压力"),
        ("flirty_tension", "flirty", "暧昧张力", "轻挑战玩笑后的安全落点", "暧昧", "低压幽默", "制造张力但保留尊重"),
        ("conflict_repair", "game", "冲突修复", "迟到后的责任承担与补偿", "冲突修复", "道歉结构", "把解释冲动改成可靠行动"),
        ("long_connection", "story", "长期连接", "异地周末安排的期待校准", "长期", "ORID复盘", "把隐形期待变成可协商约定"),
        ("humor_interaction", "joke", "幽默互动", "自嘲破冰但不贬低自己", "初识", "幽默自嘲", "降低紧张而不降低自尊"),
        ("mistake_rewrite", "knowledge_card", "错题改写", "把审问式关心改成选择题", "热恋", "选择式提问", "从控制感改成被尊重感"),
    ]
    return [
        {
            "resource_uuid": f"boutique_resource_{axis}_20260524_v1",
            "type": resource_type,
            "category": category,
            "title": title,
            "scene": scene,
            "tool": tool,
            "goal": goal,
            "axis": axis,
        }
        for axis, resource_type, category, title, scene, tool, goal in base
    ]


def _boutique_resource_from_spec(spec: dict, reviewer_id: str, now: datetime) -> ResourceLibrary:
    title = str(spec["title"])
    scene = str(spec["scene"])
    tool = str(spec["tool"])
    goal = str(spec["goal"])
    category = str(spec["category"])
    content = (
        f"场景：{title}。你们正处在{scene}阶段，对方的反应比平时慢半拍，关系里出现一个需要轻轻验证的信号。"
        f"TA说：我也不知道怎么讲，刚才那一下有点怪。"
        f"常见失误：立刻追问“你是不是不喜欢我了”，把一个微小信号放大成人格审判。"
        f"更好回应：我刚才也感觉节奏有点变了。我不急着下结论，只想确认一下，是我哪句话让你不舒服，还是你现在只是需要缓一缓。"
        f"边界与同意：如果对方说不想继续聊，就先停下；不把沉默当成必须立刻破解的谜题。"
        f"练习任务：用{tool}写三句回应，第一句只描述事实，第二句命名可能感受，第三句给对方一个可拒绝的选择。"
    )
    return ResourceLibrary(
        resource_uuid=str(spec["resource_uuid"]),
        type=str(spec["type"]),
        category=category,
        title=title,
        content=content,
        emotional_tone_json=json.dumps(["具体案例", category, scene], ensure_ascii=False),
        emotional_intensity=7,
        applicable_scene=scene,
        difficulty_level=2,
        gender_target="通用",
        attachment_suitability="通用",
        usage_tip=f"用于{scene}阶段的{goal}训练；重点是先观察、再验证、再行动，不替对方做决定。",
        effectiveness_rating=9,
        review_status="reviewed",
        reviewer_id=reviewer_id,
        reviewed_at=now,
        source="project_original_boutique_batch",
        source_url="local_anchor:project_original_boutique_batch",
        source_title="项目原创精品训练卡批次",
        source_summary="围绕微关系信号、情绪流动、边界同意、暧昧张力、冲突修复、长期连接、幽默互动、错题改写生成的原创练习卡。",
        source_license="project_original",
        content_fingerprint="sha256:" + hashlib.sha256(content.encode("utf-8")).hexdigest(),
        quality_score=92,
        tags="具体案例,精品训练卡,场景,TA说,常见失误,更好回应,边界与同意,练习任务," + category,
        expression_goal=goal,
        expression_level="D2",
        speech_act=tool,
        mistake_pattern="过早下结论",
        recommended_drills_json=json.dumps(["事实句", "感受句", "可退出选择句"], ensure_ascii=False),
    )


def _knowledge_needs_manual_curation(entry: KnowledgeEntry) -> bool:
    generic_titles = {"旧手册章节", "子章节", "untitled", "section"}
    title = str(entry.title or "").strip().lower()
    category = str(entry.category or "").strip().lower()
    source = str(entry.source or "").strip().lower()
    if title in generic_titles:
        return True
    if category == "legacy_manual":
        return True
    return source in {"legacy_manual", "manual_import"} and float(entry.quality_score or 0) < 85


def _resource_needs_manual_curation(resource: ResourceLibrary) -> bool:
    title = str(resource.title or "").strip()
    category = str(resource.category or "").strip()
    content = str(resource.content or "").strip()
    usage_tip = str(resource.usage_tip or "").strip()
    tags = str(resource.tags or "").strip()
    source = str(resource.source or "").strip().lower()
    source_url = str(resource.source_url or "").strip().lower()
    text = "\n".join([title, category, content, usage_tip, tags])
    concrete_markers = (
        "场景",
        "ta说",
        "对方说",
        "常见失误",
        "更好回应",
        "边界",
        "同意",
        "练习任务",
        "复盘",
        "事实",
        "感受",
        "期待",
    )
    concrete_marker_count = sum(1 for marker in concrete_markers if marker in text.lower())
    has_concrete_structure = concrete_marker_count >= 3
    has_enough_detail = len(content) >= 120 or (len(content) >= 80 and len(usage_tip) >= 30)
    short_generic_title = len(title) <= 4 and (not category or title == category)
    generic_titles = {
        "土味",
        "含蓄",
        "傲娇",
        "幽默",
        "直接",
        "调侃",
        "深情",
        "情话",
        "故事",
        "游戏",
        "模板",
    }
    if int(resource.effectiveness_rating or 0) < 8 and float(resource.quality_score or 0) < 85:
        return True
    if short_generic_title or title in generic_titles:
        return not has_concrete_structure
    if source.startswith("rewrite:similarity-rewrite-") or source_url.startswith("rewrite:similarity-rewrite-"):
        return False
    return not (has_concrete_structure or has_enough_detail)


def _resource_has_legacy_enrichment_debt(resource: ResourceLibrary) -> bool:
    text = "\n".join([
        str(resource.tags or ""),
        str(resource.source or ""),
        str(resource.source_summary or ""),
        str(resource.case_blueprint_json or ""),
    ]).lower()
    debt_markers = (
        "needs_enrichment",
        "legacy_no_case_blueprint",
        "legacy_enrichment",
        "旧急转弯素材",
    )
    return any(marker in text for marker in debt_markers)


def _resource_lacks_boundary_evidence_for_high_tension(resource: ResourceLibrary) -> bool:
    text = "\n".join([
        str(resource.title or ""),
        str(resource.category or ""),
        str(resource.content or ""),
        str(resource.usage_tip or ""),
        str(resource.tags or ""),
        str(resource.expression_goal or ""),
    ]).lower()
    high_tension_terms = ("暧昧", "调情", "撩", "成人", "亲密", "推拉", "黄段子", "flirty", "tension")
    boundary_terms = ("边界", "同意", "可拒绝", "退路", "停止", "不施压", "尊重", "舒服", "慢下来", "选择")
    if not any(term in text for term in high_tension_terms):
        return False
    return not any(term in text for term in boundary_terms)


def _load_reviewed_asset(asset_type: str, asset_id: int, session: Session) -> ResourceLibrary | KnowledgeEntry:
    if asset_type == "resource":
        target = session.exec(select(ResourceLibrary).where(ResourceLibrary.id == asset_id)).first()
    else:
        target = session.exec(select(KnowledgeEntry).where(KnowledgeEntry.id == asset_id)).first()
    if not target:
        raise HTTPException(status_code=404, detail="发布治理资产不存在")
    return target


def _reviewed_asset_target_status(action: str, from_status: str) -> str:
    if action == "confirm_publish":
        return "published"
    if action == "withdraw":
        return "reviewed"
    if action == "request_review":
        return "reviewed" if from_status == "published" else "draft"
    return from_status


def _reviewed_asset_candidate_card(target: ResourceLibrary | KnowledgeEntry, asset_type: str) -> dict:
    if asset_type == "resource" and isinstance(target, ResourceLibrary):
        return _resource_publish_candidate(target)
    if isinstance(target, KnowledgeEntry):
        return _knowledge_publish_candidate(target)
    raise HTTPException(status_code=400, detail="资产类型与记录不匹配")


def _reviewed_asset_audit_payload(
    data: ReviewedAssetActionRequest,
    candidate: dict,
    from_status: str,
    to_status: str,
) -> dict:
    return {
        "asset_type": data.asset_type,
        "asset_id": data.asset_id,
        "action": data.action,
        "from_status": from_status,
        "to_status": to_status,
        "reviewer_id": data.reviewer_id,
        "reason": data.reason,
        "publish_ready": candidate.get("publish_ready"),
        "priority": candidate.get("priority"),
        "quality_signal": candidate.get("quality_signal"),
    }


def _auto_review_decision(candidate: dict, data: ReviewedAssetAutoReviewRequest) -> dict:
    score = int(candidate.get("priority", {}).get("score") or 0)
    blocks = candidate.get("quality_signal", {}).get("blocks", [])
    publish_ready = bool(candidate.get("publish_ready"))
    can_publish = data.publish_ready_assets and publish_ready and score >= data.min_priority_score and not blocks
    if can_publish:
        action = "confirm_publish"
        reason = "自动审核通过：发布候选满足质量阈值且无阻断项。"
    elif data.request_review_blocked_assets and str(candidate.get("review_status") or "") == "reviewed":
        action = "request_review"
        reason = "自动审核退回复审：候选未满足发布阈值或存在阻断项。"
    else:
        action = "hold"
        reason = "自动审核保留：未满足自动发布条件，等待人工复审。"
    return {
        "asset_type": candidate.get("asset_type"),
        "id": candidate.get("id"),
        "title": candidate.get("title"),
        "review_status": candidate.get("review_status"),
        "publish_ready": publish_ready,
        "priority": candidate.get("priority"),
        "quality_signal": candidate.get("quality_signal"),
        "action": action,
        "reason": reason,
    }


def _auto_review_summary(decisions: list[dict]) -> dict:
    return {
        "scanned": len(decisions),
        "publish": sum(1 for item in decisions if item["action"] == "confirm_publish"),
        "request_review": sum(1 for item in decisions if item["action"] == "request_review"),
        "hold": sum(1 for item in decisions if item["action"] == "hold"),
    }


def _auto_review_audit_payload(
    decision: dict,
    data: ReviewedAssetAutoReviewRequest,
    from_status: str,
    to_status: str,
) -> dict:
    return {
        "asset_type": decision.get("asset_type"),
        "asset_id": decision.get("id"),
        "action": decision.get("action"),
        "from_status": from_status,
        "to_status": to_status,
        "reviewer_id": data.reviewer_id,
        "reason": decision.get("reason"),
        "publish_ready": decision.get("publish_ready"),
        "priority": decision.get("priority"),
        "quality_signal": decision.get("quality_signal"),
        "auto_review": True,
    }


def _publish_candidate_next_actions(candidates: list[dict]) -> list[dict]:
    ready = sum(1 for item in candidates if item["publish_ready"])
    if ready:
        return [{
            "priority": "high",
            "action": "人工确认并发布高优先级 reviewed 资产",
            "reason": f"{ready} 条 reviewed 资产达到发布候选阈值。",
        }]
    if candidates:
        return [{
            "priority": "medium",
            "action": "补充 reviewed 资产质量信号",
            "reason": f"{len(candidates)} 条 reviewed 资产尚未达到发布候选阈值。",
        }]
    return [{
        "priority": "low",
        "action": "维持发布治理",
        "reason": "当前没有 reviewed 发布候选。",
    }]


def _status_counts(items: list, field: str) -> dict[str, int]:
    counts: dict[str, int] = {}
    for item in items:
        value = str(getattr(item, field, "draft") or "draft")
        counts[value] = counts.get(value, 0) + 1
    return counts


def _status_total(items: list, status: str) -> int:
    return sum(1 for item in items if str(getattr(item, "review_status", "") or "") == status)


def _content_hash(content: str) -> str:
    return f"sha256:{hashlib.sha256(content.encode('utf-8')).hexdigest()}"


def _slug_uuid(prefix: str, *parts: str) -> str:
    raw = "|".join(parts)
    digest = hashlib.sha256(raw.encode("utf-8")).hexdigest()[:16]
    return f"{prefix}_{digest}"


def _pipeline_metadata_actions(
    sources: list[SourceRegistry],
    raw_items: list[RawContentItem],
    jobs: list[AnnotationJob],
    assets: list[TrainingAssetVersion],
    samples: list[InteractionSample],
    resources: list[ResourceLibrary],
    knowledge_entries: list[KnowledgeEntry],
) -> list[dict]:
    actions: list[dict] = []
    actions.extend(_source_actions(sources, raw_items))
    actions.extend(_annotation_actions(raw_items, jobs, assets))
    actions.extend(_reviewed_asset_actions(samples, resources, knowledge_entries, assets))
    if not actions:
        actions.append({"priority": "low", "action": "生成进化周报", "reason": "元数据流水线完整，可以沉淀本周新增洞察。"})
    return actions[:6]


def _source_actions(sources: list[SourceRegistry], raw_items: list[RawContentItem]) -> list[dict]:
    actions: list[dict] = []
    if not sources:
        actions.append({"priority": "high", "action": "登记首批权威来源", "reason": "缺少 source registry，无法追踪内容许可和可信度。"})
    if sources and not raw_items:
        actions.append({"priority": "high", "action": "抓取候选元数据", "reason": "已有来源但没有 raw candidate，进化流水线没有输入。"})
    risky_raw = [item for item in raw_items if item.privacy_risk >= 0.5 or item.copyright_risk >= 0.5]
    if risky_raw:
        actions.append({"priority": "high", "action": "隔离高风险候选", "reason": f"{len(risky_raw)} 条候选内容隐私或版权风险偏高。"})
    return actions


def _annotation_actions(
    raw_items: list[RawContentItem],
    jobs: list[AnnotationJob],
    assets: list[TrainingAssetVersion],
) -> list[dict]:
    actions: list[dict] = []
    if raw_items and not jobs:
        actions.append({"priority": "medium", "action": "启动关系元标注", "reason": "候选内容需要标注信号、情绪流、需求、边界和安全风险。"})
    draft_jobs = [job for job in jobs if job.status in {"draft", "running"}]
    if draft_jobs:
        actions.append({"priority": "medium", "action": "收敛标注任务", "reason": f"{len(draft_jobs)} 个标注任务尚未 reviewed。"})
    if jobs and not assets:
        actions.append({"priority": "medium", "action": "生成训练资产版本", "reason": "标注结果尚未沉淀为可回归、可发布的训练资产。"})
    if not any(asset.review_status == "published" for asset in assets):
        actions.append({"priority": "low", "action": "发布首个训练资产版本", "reason": "前端训练仍缺少带来源追踪的资产版本。"})
    return actions


def _reviewed_asset_actions(
    samples: list[InteractionSample],
    resources: list[ResourceLibrary],
    knowledge_entries: list[KnowledgeEntry],
    assets: list[TrainingAssetVersion],
) -> list[dict]:
    actions: list[dict] = []
    asset_inventory = _reviewed_asset_inventory(samples, resources, knowledge_entries)
    if asset_inventory["draft"] > 0:
        actions.append({"priority": "high", "action": "推进 reviewed/published 资产", "reason": f"仍有 {asset_inventory['draft']} 条资产停留在 draft。"})
    if asset_inventory["reviewed"] > 0 and asset_inventory["published"] == 0:
        actions.append({"priority": "medium", "action": "发布 reviewed 资产", "reason": "已经有 reviewed 资产，可以进入 published。"})
    if not any(asset.review_status == "published" for asset in assets) and asset_inventory["published"] == 0:
        actions.append({"priority": "low", "action": "发布首个训练资产版本", "reason": "前端训练仍缺少带来源追踪的资产版本。"})
    return actions


def _pipeline_heartbeat(
    *,
    total_items: int,
    active_sources: int,
    candidate_count: int,
    review_pressure: int,
) -> dict:
    if total_items == 0:
        return {
            "state": "empty",
            "label": "等待第一批进化素材",
            "message": "尚未形成采集、评审、发布循环。",
        }
    if active_sources == 0:
        return {
            "state": "stalled",
            "label": "来源休眠",
            "message": "已有进化条目，但没有活跃来源在供给新素材。",
        }
    if review_pressure >= 8:
        return {
            "state": "congested",
            "label": "评审堆积",
            "message": "候选和低质量条目偏多，需要人工或 AI 评审清理。",
        }
    if candidate_count > 0:
        return {
            "state": "learning",
            "label": "正在吸收新素材",
            "message": "流水线已有候选条目，下一步是评审、去重和发布。",
        }
    return {
        "state": "stable",
        "label": "稳定运行",
        "message": "来源、发布和质量分布处于可展示状态。",
    }


def _next_actions(
    *,
    total_items: int,
    active_sources: int,
    candidate_count: int,
    published_count: int,
    rejected_count: int,
    average_quality: float,
    needs_review_count: int,
) -> list[dict]:
    actions: list[dict] = []
    if active_sources < 3:
        actions.append({
            "priority": "high",
            "action": "补充稳定来源",
            "reason": "活跃来源少于 3 个，进化中心还缺少多源交叉验证。",
        })
    if candidate_count:
        actions.append({
            "priority": "high",
            "action": "评审候选条目",
            "reason": f"当前有 {candidate_count} 条候选内容等待发布或拒绝。",
        })
    if needs_review_count:
        actions.append({
            "priority": "medium",
            "action": "复核低质量内容",
            "reason": f"{needs_review_count} 条内容质量分低于 60，需要重写、降权或拒绝。",
        })
    if total_items and published_count == 0:
        actions.append({
            "priority": "high",
            "action": "发布首批进化成果",
            "reason": "已有素材但尚无发布条目，前端只能看到空状态。",
        })
    if total_items >= 5 and rejected_count == 0:
        actions.append({
            "priority": "low",
            "action": "建立拒绝样本",
            "reason": "流水线需要保留被拒案例，帮助校准质量边界。",
        })
    if total_items and average_quality < 70:
        actions.append({
            "priority": "medium",
            "action": "提升平均质量分",
            "reason": f"当前平均质量分为 {average_quality}，建议优先处理证据不足条目。",
        })
    if not actions:
        actions.append({
            "priority": "low",
            "action": "生成本周进化报告",
            "reason": "流水线状态健康，可以沉淀为周报和训练资产更新记录。",
        })
    return actions[:5]
