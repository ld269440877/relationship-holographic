"""Runtime operational event models."""
from datetime import datetime

from sqlmodel import Field, SQLModel


class RuntimeEvent(SQLModel, table=True):
    """Frontend/backend runtime event without storing raw user input."""

    __tablename__ = "runtime_events"

    id: int | None = Field(default=None, primary_key=True)
    source: str = Field(index=True, description="frontend/backend")
    event_type: str = Field(index=True, description="api_error/vue_error/window_error/unhandled_rejection")
    severity: str = Field(default="medium", index=True)
    status: str = Field(default="open", index=True)
    route: str | None = Field(default=None, index=True)
    method: str | None = Field(default=None, index=True)
    endpoint: str | None = Field(default=None, index=True)
    http_status: int | None = Field(default=None, index=True)
    message_hash: str = Field(index=True)
    message_preview: str | None = None
    context_json: str | None = None
    created_at: datetime = Field(default_factory=datetime.now, index=True)
