"""系统进化中心数据模型。"""
from datetime import datetime

from sqlmodel import Field, SQLModel


class EvolutionSource(SQLModel, table=True):
    """研究、访谈、案例、手动录入等外部/内部知识来源。"""

    __tablename__ = "evolution_sources"

    id: int | None = Field(default=None, primary_key=True)
    name: str = Field(index=True)
    source_type: str = Field(index=True, description="gottman/esther_perel/paper/social_case/manual/json_import")
    url: str | None = None
    trust_score: float = Field(default=0.8, ge=0, le=1)
    update_frequency: str = Field(default="weekly")
    active: bool = Field(default=True, index=True)
    created_at: datetime = Field(default_factory=datetime.now)


class EvolutionItem(SQLModel, table=True):
    """采集或生成的研究洞察、互动案例、技术原则。"""

    __tablename__ = "evolution_items"
    id: int | None = Field(default=None, primary_key=True)
    source_id: int | None = Field(default=None, foreign_key="evolution_sources.id")
    title: str = Field(index=True)
    content: str
    summary: str | None = None
    category: str = Field(index=True, description="research/case/interview/technique/warning")
    tags_json: str | None = None
    quality_score: float = Field(default=0.0, ge=0, le=100)
    status: str = Field(default="draft", index=True, description="draft/reviewed/published/rejected")
    published_at: datetime | None = None
    created_at: datetime = Field(default_factory=datetime.now, index=True)


class EvolutionReport(SQLModel, table=True):
    """每日/每周/月度系统进化报告。"""

    __tablename__ = "evolution_reports"
    id: int | None = Field(default=None, primary_key=True)
    period_type: str = Field(index=True, description="daily/weekly/monthly")
    title: str
    summary: str
    new_items_count: int = Field(default=0)
    promoted_samples_count: int = Field(default=0)
    key_insights_json: str | None = None
    created_at: datetime = Field(default_factory=datetime.now, index=True)


class SourceRegistry(SQLModel, table=True):
    """合规来源登记表，作为进化流水线的源数据骨架。"""

    __tablename__ = "source_registry"

    id: int | None = Field(default=None, primary_key=True)
    source_uuid: str = Field(unique=True, index=True)
    name: str = Field(index=True)
    source_type: str = Field(index=True, description="research/expert_blog/podcast/book_note/user_submitted/synthetic/manual")
    url: str | None = None
    trust_score: float = Field(default=0.8, ge=0, le=1)
    update_frequency: str = Field(default="weekly")
    allowed_use_json: str | None = None
    disallowed_use_json: str | None = None
    active: bool = Field(default=True, index=True)
    last_checked_at: datetime | None = None
    created_at: datetime = Field(default_factory=datetime.now, index=True)


class RawContentItem(SQLModel, table=True):
    """原始候选内容元数据，只要求可追踪，不强制保存全文。"""

    __tablename__ = "raw_content_items"

    id: int | None = Field(default=None, primary_key=True)
    raw_uuid: str = Field(unique=True, index=True)
    source_id: int | None = Field(default=None, foreign_key="source_registry.id")
    title: str | None = Field(default=None, index=True)
    url: str | None = None
    content_hash: str | None = Field(default=None, index=True)
    raw_storage_policy: str = Field(default="metadata_only")
    privacy_risk: float = Field(default=0.0, ge=0, le=1)
    copyright_risk: float = Field(default=0.0, ge=0, le=1)
    consent_status: str | None = None
    processing_status: str = Field(default="raw", index=True)
    collected_at: datetime = Field(default_factory=datetime.now, index=True)


class AnnotationJob(SQLModel, table=True):
    """面向原始内容、样本或知识条目的标注任务骨架。"""

    __tablename__ = "annotation_jobs"

    id: int | None = Field(default=None, primary_key=True)
    target_type: str = Field(index=True, description="raw_content/evolution_item/sample/knowledge")
    target_id: int = Field(index=True)
    annotator_type: str = Field(index=True, description="human/ai/rule")
    annotator_version: str | None = None
    schema_version: str | None = None
    result_json: str | None = None
    confidence: float = Field(default=0.0, ge=0, le=1)
    status: str = Field(default="draft", index=True)
    created_at: datetime = Field(default_factory=datetime.now, index=True)


class TrainingAssetVersion(SQLModel, table=True):
    """训练资产版本，记录样本/知识/课程节点的来源追踪与质量状态。"""

    __tablename__ = "training_asset_versions"

    id: int | None = Field(default=None, primary_key=True)
    asset_type: str = Field(index=True, description="sample/knowledge/curriculum/evaluation")
    asset_id: int = Field(index=True)
    version: str = Field(index=True)
    source_trace_json: str | None = None
    quality_json: str | None = None
    review_status: str = Field(default="draft", index=True)
    published_at: datetime | None = None
    created_at: datetime = Field(default_factory=datetime.now, index=True)


class PipelineRunLog(SQLModel, table=True):
    """进化流水线处理日志，记录每次状态推进与质量门禁结果。"""

    __tablename__ = "pipeline_run_logs"

    id: int | None = Field(default=None, primary_key=True)
    target_type: str = Field(index=True, description="raw_content/annotation_job/asset_version")
    target_id: int = Field(index=True)
    action: str = Field(index=True, description="sanitize/dedupe/annotate/review/publish/reject")
    from_status: str | None = Field(default=None, index=True)
    to_status: str = Field(index=True)
    result_json: str | None = None
    message: str | None = None
    created_at: datetime = Field(default_factory=datetime.now, index=True)


class MetadataVectorIndex(SQLModel, table=True):
    """本地元数据向量索引，作为 sqlite-vec/ANN 的可替换持久化层。"""

    __tablename__ = "metadata_vector_index"

    id: int | None = Field(default=None, primary_key=True)
    target_type: str = Field(index=True, description="raw_content/knowledge/sample/resource")
    target_id: int = Field(index=True)
    target_uuid: str | None = Field(default=None, index=True)
    text_hash: str = Field(index=True)
    dimensions: int = Field(default=64)
    vector_json: str
    metadata_json: str | None = None
    built_by: str = Field(default="local_metadata_signature", index=True)
    created_at: datetime = Field(default_factory=datetime.now, index=True)
    updated_at: datetime = Field(default_factory=datetime.now, index=True)
