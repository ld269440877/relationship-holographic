"""
训练闭环数据模型

这些表把系统从“展示型题库”推进到“可追踪、可复习、可推荐”的训练系统。
"""
from datetime import datetime

from sqlmodel import Field, SQLModel


class TrainingAttempt(SQLModel, table=True):
    """每一次训练提交记录。"""

    __tablename__ = "training_attempts"

    id: int | None = Field(default=None, primary_key=True)
    user_id: int = Field(default=1, index=True)
    sample_id: int = Field(foreign_key="interaction_samples.id", index=True)
    mode: str = Field(default="response", index=True)

    user_response: str
    target_response_type: str = Field(default="soft")

    total_score: float = Field(default=0, ge=0, le=100)
    emotion_score: float | None = Field(default=None, ge=0, le=100)
    need_score: float | None = Field(default=None, ge=0, le=100)
    safety_score: float | None = Field(default=None, ge=0, le=100)
    connection_score: float | None = Field(default=None, ge=0, le=100)
    boundary_score: float | None = Field(default=None, ge=0, le=100)
    style_score: float | None = Field(default=None, ge=0, le=100)
    repair_score: float | None = Field(default=None, ge=0, le=100)

    feedback_json: str | None = Field(default=None)
    created_at: datetime = Field(default_factory=datetime.now, index=True)


class AbilitySnapshot(SQLModel, table=True):
    """训练后的能力快照，用于雷达图和趋势图。"""

    __tablename__ = "ability_snapshots"

    id: int | None = Field(default=None, primary_key=True)
    user_id: int = Field(default=1, index=True)

    emotion_score: float = Field(default=0, ge=0, le=100)
    need_score: float = Field(default=0, ge=0, le=100)
    safety_score: float = Field(default=0, ge=0, le=100)
    connection_score: float = Field(default=0, ge=0, le=100)
    boundary_score: float = Field(default=0, ge=0, le=100)
    style_score: float = Field(default=0, ge=0, le=100)
    repair_score: float = Field(default=0, ge=0, le=100)
    total_score: float = Field(default=0, ge=0, le=100)

    weakest_dimension: str | None = Field(default=None)
    next_recommendation: str | None = Field(default=None)
    created_at: datetime = Field(default_factory=datetime.now, index=True)


class PracticeSession(SQLModel, table=True):
    """一次连续训练会话，保存 AI 伴侣/训练模式的上下文。"""

    __tablename__ = "practice_sessions"

    id: int | None = Field(default=None, primary_key=True)
    user_id: int = Field(default=1, index=True)
    mode: str = Field(default="partner_ai", index=True)
    scenario_id: str = Field(index=True)
    scenario_name: str
    attachment_style: str = Field(index=True)
    difficulty: str = Field(default="medium")
    response_style: str = Field(default="soft")
    topics_json: str | None = Field(default=None)
    current_state_json: str | None = Field(default=None)
    safety_summary_json: str | None = Field(default=None)
    total_turns: int = Field(default=0, ge=0)
    average_score: float = Field(default=0, ge=0, le=100)
    status: str = Field(default="active", index=True)
    started_at: datetime = Field(default_factory=datetime.now, index=True)
    updated_at: datetime = Field(default_factory=datetime.now, index=True)
    ended_at: datetime | None = Field(default=None)


class PracticeEvent(SQLModel, table=True):
    """会话内的一轮训练事件，记录输入、回复、评分和状态轨迹。"""

    __tablename__ = "practice_events"

    id: int | None = Field(default=None, primary_key=True)
    session_id: int = Field(foreign_key="practice_sessions.id", index=True)
    turn_index: int = Field(default=0, ge=0)
    role: str = Field(default="partner_simulation", index=True)
    user_message: str
    partner_reply: str
    score: float = Field(default=0, ge=0, le=100)
    source: str = Field(default="rule_fallback")
    suggestions_json: str | None = Field(default=None)
    relationship_state_json: str | None = Field(default=None)
    safety_json: str | None = Field(default=None)
    safe_alternatives_json: str | None = Field(default=None)
    created_at: datetime = Field(default_factory=datetime.now, index=True)


class SafetyEvent(SQLModel, table=True):
    """高风险关系请求审计事件，只保存摘要、哈希和安全处置结果。"""

    __tablename__ = "safety_events"

    id: int | None = Field(default=None, primary_key=True)
    task_type: str = Field(index=True)
    source: str = Field(default="ai_orchestrator", index=True)
    risk_level: str = Field(index=True)
    flags_json: str
    payload_hash: str = Field(index=True)
    payload_preview: str | None = Field(default=None)
    message: str | None = Field(default=None)
    alternatives_json: str | None = Field(default=None)
    blocked: bool = Field(default=True, index=True)
    created_at: datetime = Field(default_factory=datetime.now, index=True)
