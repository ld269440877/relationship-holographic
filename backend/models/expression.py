"""Expression toolbox data models."""
from datetime import datetime

from sqlmodel import Field, SQLModel


class ExpressionTool(SQLModel, table=True):
    """Atomic expression tool used by resources, trainer, AI partner, and mistakes."""

    __tablename__ = "expression_tools"

    id: int | None = Field(default=None, primary_key=True)
    tool_uuid: str = Field(unique=True, index=True)
    name: str = Field(index=True)
    layer: str = Field(index=True, description="logic/ammo/structure/nonverbal/emotion/relationship")
    category: str = Field(index=True)
    formula: str | None = None
    description: str
    best_scenes_json: str | None = None
    relationship_fit_json: str | None = None
    emotion_fit_json: str | None = None
    risk_flags_json: str | None = None
    micro_steps_json: str | None = None
    learning_blueprint_json: str | None = Field(default=None, description="工具学习蓝图 JSON")
    example_before: str | None = None
    example_after: str | None = None
    mastery_stage: str = Field(default="recognition", index=True)
    source: str = Field(default="project_expression_toolbox", index=True)
    source_url: str | None = None
    review_status: str = Field(default="published", index=True)
    quality_score: float = Field(default=85, ge=0, le=100, index=True)
    created_at: datetime = Field(default_factory=datetime.now, index=True)
    updated_at: datetime = Field(default_factory=datetime.now, index=True)


class ExpressionToolChain(SQLModel, table=True):
    """Recommended sequence of expression tools for a scene and goal."""

    __tablename__ = "expression_tool_chains"

    id: int | None = Field(default=None, primary_key=True)
    chain_uuid: str = Field(unique=True, index=True)
    name: str = Field(index=True)
    goal: str = Field(index=True)
    scene: str = Field(index=True)
    stage: str | None = Field(default=None, index=True)
    tool_ids_json: str
    sequence_json: str | None = None
    forbidden_tools_json: str | None = None
    example_dialogue_json: str | None = None
    review_status: str = Field(default="published", index=True)
    quality_score: float = Field(default=85, ge=0, le=100, index=True)
    created_at: datetime = Field(default_factory=datetime.now, index=True)
    updated_at: datetime = Field(default_factory=datetime.now, index=True)
