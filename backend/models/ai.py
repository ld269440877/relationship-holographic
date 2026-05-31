"""AI prompt versioning and run audit models."""
from datetime import datetime

from sqlmodel import Field, SQLModel


class AIPromptVersion(SQLModel, table=True):
    """Versioned prompt/schema contract used by AI orchestration."""

    __tablename__ = "ai_prompt_versions"

    id: int | None = Field(default=None, primary_key=True)
    prompt_id: str = Field(index=True)
    task_type: str = Field(index=True)
    version: str = Field(index=True)
    schema_version: str = Field(index=True)
    system_prompt_hash: str
    user_prompt_template_hash: str
    response_contract_json: str | None = None
    safety_policy_version: str = Field(default="relationship-safety.v1", index=True)
    active: bool = Field(default=True, index=True)
    created_at: datetime = Field(default_factory=datetime.now, index=True)


class AIRunLog(SQLModel, table=True):
    """Auditable AI run outcome without storing sensitive raw payloads."""

    __tablename__ = "ai_run_logs"

    id: int | None = Field(default=None, primary_key=True)
    task_type: str = Field(index=True)
    prompt_id: str = Field(index=True)
    prompt_version: str = Field(index=True)
    schema_version: str = Field(index=True)
    provider: str = Field(default="deepseek", index=True)
    model: str | None = Field(default=None, index=True)
    outcome: str = Field(index=True, description="success/success_raw_text/provider_failure/blocked_safety")
    fallback_reason: str | None = None
    safety_risk_level: str | None = Field(default=None, index=True)
    safety_flags_json: str | None = None
    payload_hash: str = Field(index=True)
    payload_summary_json: str | None = None
    response_summary_json: str | None = None
    safety_event_id: int | None = Field(default=None, foreign_key="safety_events.id", index=True)
    latency_ms: int = Field(default=0, ge=0)
    created_at: datetime = Field(default_factory=datetime.now, index=True)


class AIProviderProbeLog(SQLModel, table=True):
    """Provider live probe audit without storing prompt or response text."""

    __tablename__ = "ai_provider_probe_logs"

    id: int | None = Field(default=None, primary_key=True)
    provider: str = Field(default="deepseek", index=True)
    mode: str = Field(index=True)
    model: str | None = Field(default=None, index=True)
    request_shape_json: str
    dry_run: bool = Field(default=True, index=True)
    outcome: str = Field(index=True)
    http_status: int | None = Field(default=None, index=True)
    error_type: str | None = Field(default=None, index=True)
    latency_ms: int = Field(default=0, ge=0)
    created_at: datetime = Field(default_factory=datetime.now, index=True)
