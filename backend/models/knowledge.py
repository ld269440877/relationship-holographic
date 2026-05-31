"""结构化知识库模型。

用于把历史 JSON / Markdown / HTML 手册从静态文件拆分为 SQLite 单一数据源。
"""
from datetime import datetime

from sqlmodel import Field, SQLModel


class KnowledgeSection(SQLModel, table=True):
    """知识分区，例如八阶路径、依恋类型、冲突修复。"""

    __tablename__ = "knowledge_sections"

    id: int | None = Field(default=None, primary_key=True)
    section_uuid: str = Field(unique=True, index=True)
    name: str = Field(index=True)
    description: str | None = None
    icon: str | None = None
    sort_order: int = Field(default=0, index=True)
    source: str = Field(default="knowledge_json", index=True)
    source_id: str | None = Field(default=None, index=True)
    created_at: datetime = Field(default_factory=datetime.now, index=True)
    updated_at: datetime = Field(default_factory=datetime.now)


class KnowledgeEntry(SQLModel, table=True):
    """结构化知识条目。"""

    __tablename__ = "knowledge_entries"

    id: int | None = Field(default=None, primary_key=True)
    entry_uuid: str = Field(unique=True, index=True)
    section_id: int = Field(foreign_key="knowledge_sections.id", index=True)
    title: str = Field(index=True)
    subtitle: str | None = None
    content: str
    summary: str | None = None
    category: str = Field(default="knowledge", index=True)
    tags_json: str | None = None
    quality_score: float = Field(default=70, ge=0, le=100, index=True)
    review_status: str = Field(default="draft", index=True)
    reviewer_id: str | None = Field(default=None, index=True)
    reviewed_at: datetime | None = Field(default=None, index=True)
    published_at: datetime | None = Field(default=None, index=True)
    source: str = Field(default="knowledge_json", index=True)
    source_id: str | None = Field(default=None, index=True)
    source_metadata_json: str | None = None
    created_at: datetime = Field(default_factory=datetime.now, index=True)
    updated_at: datetime = Field(default_factory=datetime.now)


class ContentImportBatch(SQLModel, table=True):
    """内容导入批次，用于追踪 JSON/Markdown/HTML 迁移质量。"""

    __tablename__ = "content_import_batches"

    id: int | None = Field(default=None, primary_key=True)
    source_name: str = Field(index=True)
    source_type: str = Field(default="json", index=True)
    imported_sections: int = 0
    imported_entries: int = 0
    skipped_entries: int = 0
    issues_count: int = 0
    status: str = Field(default="completed", index=True)
    report_json: str | None = None
    created_at: datetime = Field(default_factory=datetime.now, index=True)


class ContentImportIssue(SQLModel, table=True):
    """导入质量问题。"""

    __tablename__ = "content_import_issues"

    id: int | None = Field(default=None, primary_key=True)
    batch_id: int | None = Field(default=None, foreign_key="content_import_batches.id", index=True)
    source_name: str = Field(index=True)
    source_id: str | None = Field(default=None, index=True)
    severity: str = Field(default="warning", index=True)
    message: str
    status: str = Field(default="open", index=True)
    reviewer_id: str | None = Field(default=None, index=True)
    resolution: str | None = None
    resolved_at: datetime | None = Field(default=None, index=True)
    created_at: datetime = Field(default_factory=datetime.now, index=True)
    updated_at: datetime = Field(default_factory=datetime.now)
