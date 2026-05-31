"""AI 结构化任务类型。"""
from typing import Any, Literal

from pydantic import BaseModel, Field

AITaskType = Literal[
    "analyze_emotion",
    "score_response",
    "generate_scenario",
    "simulate_partner",
    "review_conversation",
    "generate_weekly_report",
    "annotate_sample",
    "rewrite_response",
]


class AIRequest(BaseModel):
    task_type: AITaskType
    payload: dict[str, Any]
    system_context: str | None = None


class AIResponse(BaseModel):
    ok: bool = True
    task_type: AITaskType
    content: dict[str, Any] = Field(default_factory=dict)
    raw_text: str | None = None
    safety: dict[str, Any] = Field(default_factory=dict)
    safe_alternatives: list[str] = Field(default_factory=list)
    error: str | None = None
