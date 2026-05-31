"""
训练相关 API 路由：识别、对比、记录、错题、复习、能力雷达、下一题推荐。
"""
import asyncio
import json
import random
from datetime import date, datetime, timedelta
from typing import Any, cast

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import or_
from sqlalchemy.sql.elements import ColumnElement
from sqlmodel import Session, col, desc, func, select

from backend.ai.orchestrator import ai_orchestrator
from backend.ai.provider_client import ai_provider_client
from backend.ai.safety import safety_guardian
from backend.ai.schemas import AIRequest
from backend.core.comparison_engine import comparison_engine
from backend.core.emotion_engine import emotion_engine
from backend.database.connection import get_session
from backend.database.expression_seed import BASE_TOOL_SPECS
from backend.models.expression import ExpressionTool
from backend.models.resource import ResourceLibrary
from backend.models.sample import InteractionSample
from backend.models.training import AbilitySnapshot, PracticeEvent, PracticeSession, TrainingAttempt
from backend.models.user import MistakeLog

router = APIRouter(prefix="/api/training", tags=["训练"])
SCORE_FIELDS = ["emotion_score", "need_score", "safety_score", "connection_score", "boundary_score", "style_score", "repair_score"]
TRAINING_READY_SAMPLE_STATUSES = ("reviewed", "published", "gold")


def _sql_column(value: Any) -> ColumnElement[Any]:
    return cast(ColumnElement[Any], value)


def _safe_dict_get(value: Any, key: str, default: Any = 0) -> Any:
    if isinstance(value, dict):
        return value.get(key, default)
    return default


class EmotionRecognizeRequest(BaseModel):
    text: str


class EmotionRecognizeResponse(BaseModel):
    emotions: list[dict[str, Any]]
    mixed_emotion: dict[str, Any] | None = None
    intensity_label: str
    behavioral_anchor: str


class CompareRequest(BaseModel):
    original_response: str
    sample_id: int
    response_type: str = "soft"


class CompareResponse(BaseModel):
    score: float
    differences: list[dict[str, Any]]
    suggestions: list[str]
    ideal_response: str
    diff_report: str
    dimension_scores: dict[str, float] = Field(default_factory=dict)
    saved_attempt_id: int | None = None
    mistake_id: int | None = None
    next_recommendation: str | None = None
    scoring_source: str = "rule"
    ai_feedback: dict[str, Any] | None = None
    safe_alternatives: list[str] = Field(default_factory=list)
    metacognitive_review: dict[str, Any] = Field(default_factory=dict)
    mastery: dict[str, Any] = Field(default_factory=dict)
    error_attribution: list[dict[str, str]] = Field(default_factory=list)
    gold_evaluation: dict[str, Any] = Field(default_factory=dict)
    structured_diff: dict[str, Any] = Field(default_factory=dict)
    expression_tool_scoring: dict[str, Any] = Field(default_factory=dict)


class ReviewSubmitRequest(BaseModel):
    correct: bool


class RelationshipState(BaseModel):
    trust: float = Field(default=50, ge=0, le=100)
    stress: float = Field(default=35, ge=0, le=100)
    boundary: float = Field(default=35, ge=0, le=100, description="边界压力，越高越需要降压")
    boundary_safety: float = Field(default=65, ge=0, le=100, description="边界安全感，越高越能保留自主")
    connection: float = Field(default=45, ge=0, le=100)
    turn_count: int = Field(default=0, ge=0)
    attachment_style: str = ""
    state_label: str = "观察中"
    state_color: str = "neutral"
    last_delta: dict[str, float] = Field(default_factory=dict)
    interpretation: str = "关系状态正在建立基线。"
    next_focus: str = "先观察线索，再用轻问句验证。"


class PartnerSimulateRequest(BaseModel):
    session_id: int | None = None
    scenario_id: str
    scenario_name: str
    attachment_style: str
    user_message: str
    history: list[dict[str, str]] = Field(default_factory=list)
    difficulty: str = "medium"
    response_style: str = "soft"
    topics: list[str] = Field(default_factory=list)
    relationship_state: RelationshipState | None = None


class PartnerSimulateResponse(BaseModel):
    session_id: int | None = None
    reply: str
    score: float
    source: str = "rule_fallback"
    suggestions: list[str] = Field(default_factory=list)
    safety: dict[str, Any] = Field(default_factory=dict)
    safe_alternatives: list[str] = Field(default_factory=list)
    relationship_state: RelationshipState = Field(default_factory=RelationshipState)
    expression_chain: dict[str, Any] = Field(default_factory=dict)
    related_resources: list[dict[str, Any]] = Field(default_factory=list)
    mistake_memory: dict[str, Any] = Field(default_factory=dict)


@router.get("/partner/provider-status")
def get_partner_provider_status() -> dict[str, Any]:
    """Expose AI companion provider readiness without leaking secrets."""
    diagnostics = ai_provider_client.request_diagnostics()
    configured = ai_provider_client.configured
    risks = diagnostics.compatibility_risks
    recent_health = _recent_ai_provider_health()
    label = ai_provider_client.provider_label
    if not configured:
        status_label = f"未配置 {label}，当前使用本地安全降级"
    elif risks:
        status_label = f"已配置 {label}，但请求形状存在兼容风险"
    elif recent_health["provider_failure_rate"] >= 0.25:
        status_label = f"已配置 {label}，但近期 Provider 失败偏高；当前会自动使用本地结构化降级"
    else:
        status_label = f"已配置 {label}，AI 深度模拟可用"
    return {
        "configured": configured,
        "provider": diagnostics.provider,
        "mode": diagnostics.mode,
        "model": diagnostics.model,
        "base_url": diagnostics.url,
        "chat_path": diagnostics.path,
        "live_probe_enabled": ai_provider_client.live_probe_enabled,
        "compatibility_risks": risks,
        "recent_health": recent_health,
        "fallback_ready": True,
        "status_label": status_label,
        "principle": "前端只展示脱敏 provider 形状和降级状态，不暴露 API key 或原始模型输出。",
    }


def _recent_ai_provider_health(limit: int = 80) -> dict[str, Any]:
    try:
        from backend.database.connection import engine
        from backend.models.ai import AIRunLog

        with Session(engine) as session:
            rows = list(session.exec(select(AIRunLog).order_by(desc(AIRunLog.created_at)).limit(limit)).all())
    except Exception:
        rows = []
    total = len(rows)
    provider_failures = sum(1 for row in rows if row.outcome == "provider_failure")
    safety_blocks = sum(1 for row in rows if row.outcome == "blocked_safety")
    successes = sum(1 for row in rows if row.outcome in {"success", "success_raw_text"})
    return {
        "runs": total,
        "success_rate": round(successes / max(total, 1), 3),
        "provider_failure_rate": round(provider_failures / max(total, 1), 3),
        "safety_block_rate": round(safety_blocks / max(total, 1), 3),
    }


@router.post("/recognize", response_model=EmotionRecognizeResponse)
def recognize_emotion(
    request: EmotionRecognizeRequest,
    session: Session = Depends(get_session),
) -> EmotionRecognizeResponse:
    """识别文本中的情绪。"""
    emotions = emotion_engine.recognize_emotion(request.text)
    mixed = emotion_engine.analyze_mixed_emotion(emotions)
    intensity_label = "未检测到"
    behavioral_anchor = ""
    if emotions:
        avg_intensity = sum(e["intensity"] for e in emotions) / len(emotions)
        intensity_label = emotion_engine.get_intensity_label(int(avg_intensity))
        behavioral_anchor = emotion_engine.get_behavioral_anchor(emotions[0]["spectrum"], emotions[0]["intensity"])
    response = EmotionRecognizeResponse(
        emotions=emotions,
        mixed_emotion=mixed,
        intensity_label=intensity_label,
        behavioral_anchor=behavioral_anchor,
    )
    _persist_emotion_attempt(request, response, session)
    return response


@router.get("/next")
def get_next_training_item(session: Session = Depends(get_session)) -> dict[str, Any]:
    """下一题推荐：到期错题 > 最弱维度 > 随机样本。"""
    recommendation_context = _recommendation_context(session)
    due_mistake = session.exec(
        select(MistakeLog)
        .where(MistakeLog.reviewed == False)  # noqa: E712
        .where(or_(_sql_column(MistakeLog.next_review).is_(None), _sql_column(MistakeLog.next_review) <= date.today()))
        .order_by(desc(MistakeLog.id))
        .limit(1)
    ).first()
    if due_mistake:
        sample = session.exec(select(InteractionSample).where(InteractionSample.id == due_mistake.sample_id)).first()
        if sample:
            return {
                "type": "review",
                "reason": "今天有到期错题，优先复习",
                "sample": sample,
                "mistake_id": due_mistake.id,
                "visual_map": build_training_visual_map(sample),
                "recommendation_context": recommendation_context,
            }

    weakest = _get_weakest_dimension(session)
    category = _dimension_to_category(weakest)
    query = select(InteractionSample).where(col(InteractionSample.review_status).in_(TRAINING_READY_SAMPLE_STATUSES))
    if category:
        query = query.where(InteractionSample.scenario_category == category)
    samples = session.exec(query.limit(50)).all()
    if not samples:
        samples = session.exec(
            select(InteractionSample)
            .where(col(InteractionSample.review_status).in_(TRAINING_READY_SAMPLE_STATUSES))
            .limit(50)
        ).all()
    if not samples:
        samples = session.exec(select(InteractionSample).limit(50)).all()
    if not samples:
        raise HTTPException(status_code=404, detail="暂无训练样本，请先初始化数据库")
    sample = random.choice(list(samples))
    return {
        "type": "new",
        "reason": f"根据当前最弱维度推荐：{weakest or '探索训练'}",
        "sample": sample,
        "weakest_dimension": weakest,
        "visual_map": build_training_visual_map(sample),
        "recommendation_context": recommendation_context,
    }


@router.get("/visual-map/{sample_id}")
def get_training_visual_map(sample_id: int, session: Session = Depends(get_session)) -> dict[str, Any]:
    """把单个训练样本派生为数图结合的关系动力学可视地图。"""
    sample = session.exec(select(InteractionSample).where(InteractionSample.id == sample_id)).first()
    if not sample:
        raise HTTPException(status_code=404, detail="样本不存在")
    return build_training_visual_map(sample)


def _persist_emotion_attempt(
    request: EmotionRecognizeRequest,
    response: EmotionRecognizeResponse,
    session: Session,
) -> None:
    sample = session.exec(select(InteractionSample).order_by(_sql_column(InteractionSample.id)).limit(1)).first()
    if sample is None or sample.id is None:
        return
    score = 35 if not response.emotions else min(100, 55 + len(response.emotions) * 15)
    feedback = {
        "emotions": response.emotions,
        "mixed_emotion": response.mixed_emotion,
        "intensity_label": response.intensity_label,
        "behavioral_anchor": response.behavioral_anchor,
        "principle": "情绪识别训练也要进入 TrainingAttempt，才能被掌握模型和推荐器看见。",
    }
    session.add(TrainingAttempt(
        sample_id=sample.id,
        mode="emotion",
        user_response=request.text,
        target_response_type="emotion_recognition",
        total_score=score,
        emotion_score=score,
        feedback_json=json.dumps(feedback, ensure_ascii=False),
    ))
    session.commit()


def _recommendation_context(session: Session) -> dict[str, Any]:
    due_count = session.exec(
        select(func.count())
        .select_from(MistakeLog)
        .where(MistakeLog.reviewed == False)  # noqa: E712
        .where(or_(_sql_column(MistakeLog.next_review).is_(None), _sql_column(MistakeLog.next_review) <= date.today()))
    ).one()
    weakest = _get_weakest_dimension(session)
    attempts_count = _training_attempt_count(session)
    mastery = _build_mastery_model(_latest_dimension_scores(session))
    return {
        "due_mistakes": due_count,
        "weakest_dimension": weakest,
        "mastery": mastery,
        "curriculum_gate": _curriculum_gate_from_state(attempts_count, weakest, due_count),
        "principle": "推荐顺序由到期错题、最弱维度、掌握阶段和八阶课程关口共同决定。",
    }


def _latest_dimension_scores(session: Session) -> dict[str, float]:
    snapshot = session.exec(select(AbilitySnapshot).order_by(desc(AbilitySnapshot.created_at)).limit(1)).first()
    if snapshot:
        return {field: float(getattr(snapshot, field) or 0) for field in SCORE_FIELDS}
    attempts = list(session.exec(select(TrainingAttempt).order_by(desc(TrainingAttempt.created_at)).limit(20)).all())
    if not attempts:
        return {field: 0 for field in SCORE_FIELDS}
    return {
        field: round(sum(float(getattr(attempt, field) or 0) for attempt in attempts) / len(attempts), 1)
        for field in SCORE_FIELDS
    }


def _curriculum_gate_from_state(attempts_count: int, weakest: str | None, due_count: int) -> dict[str, Any]:
    if due_count:
        return {"stage": "错题回炉", "gate": "先复习到期错题，再推进新样本。", "priority": "review"}
    if attempts_count == 0:
        return {"stage": "第零阶：默认沉默", "gate": "先完成一次事实/情绪观察。", "priority": "foundation"}
    if weakest == "情绪识别":
        return {"stage": "第二阶：情绪", "gate": "补情绪颗粒度与强度判断。", "priority": "emotion"}
    if weakest == "边界感知":
        return {"stage": "第四阶：看见", "gate": "补边界红黄绿带与轻验证。", "priority": "boundary"}
    return {"stage": "第三阶：感受", "gate": "用当前最弱维度做一轮迁移练习。", "priority": "mastery"}


@router.post("/partner/simulate", response_model=PartnerSimulateResponse)
def simulate_partner(
    request: PartnerSimulateRequest,
    session: Session = Depends(get_session),
) -> PartnerSimulateResponse:
    """AI 训练伴侣：优先走安全编排器，未配置或失败时规则降级。"""
    safety = safety_guardian.inspect(request.model_dump())
    if safety_guardian.should_block(safety):
        response = PartnerSimulateResponse(
            reply=safety.message or "我不能继续这个方向，但可以练习尊重边界的表达。",
            score=0,
            source="safety_blocked",
            suggestions=safety.alternatives or [],
            safety=safety.to_dict(),
            safe_alternatives=safety.alternatives or [],
            relationship_state=_blocked_relationship_state(request),
        )
        response.expression_chain = _partner_expression_chain(request, response.relationship_state, response.score, response.suggestions, response.reply)
        return _persist_partner_simulation(request, response, session)

    relationship_state = _advance_relationship_state(request)
    mistake_memory = _partner_mistake_memory(session, request)
    if not ai_provider_client.configured:
        response = _fallback_partner_response(
            request,
            safety.to_dict(),
            reason=f"{ai_provider_client.credential_env_name} 未配置",
            relationship_state=relationship_state,
        )
        response.mistake_memory = mistake_memory
        return _persist_partner_simulation(request, response, session)

    payload = {
        "scenario": {
            "id": request.scenario_id,
            "name": request.scenario_name,
            "attachment_style": request.attachment_style,
            "difficulty": request.difficulty,
            "response_style": request.response_style,
            "topics": request.topics,
        },
        "relationship_state": relationship_state.model_dump(),
        "mistake_memory": _compact_partner_mistake_memory_for_ai(mistake_memory),
        "history": request.history[-8:],
        "user_message": request.user_message,
        "required_schema": {
            "reply": "string, partner next message in Chinese, 1-3 sentences",
            "score": "0-100 number evaluating user's relational response",
            "suggestions": ["short Chinese coaching suggestions"],
        },
    }

    async def _call() -> dict[str, Any]:
        response = await ai_orchestrator.run(
            AIRequest(
                task_type="simulate_partner",
                payload=payload,
                system_context=_partner_simulation_system_prompt(request.attachment_style),
            )
        )
        return response.model_dump()

    try:
        ai_response = asyncio.run(_call())
    except RuntimeError:
        loop = asyncio.new_event_loop()
        try:
            ai_response = loop.run_until_complete(_call())
        finally:
            loop.close()
    except Exception as exc:  # pragma: no cover - 外部网络失败时走规则降级
        response = _fallback_partner_response(
            request,
            safety.to_dict(),
            reason=f"AI 调用失败: {exc}",
            relationship_state=relationship_state,
        )
        response.mistake_memory = mistake_memory
        return _persist_partner_simulation(request, response, session)

    if not ai_response.get("ok"):
        response = _fallback_partner_response(
            request,
            ai_response.get("safety") or safety.to_dict(),
            reason=ai_response.get("error") or "AI 编排器降级",
            alternatives=ai_response.get("safe_alternatives") or [],
            relationship_state=relationship_state,
        )
        response.mistake_memory = mistake_memory
        return _persist_partner_simulation(request, response, session)
    content = _normalize_partner_ai_content(ai_response.get("content") or {})
    reply = content.get("reply")
    if not isinstance(reply, str) or not reply.strip():
        response = _fallback_partner_response(
            request,
            ai_response.get("safety") or safety.to_dict(),
            reason="AI 响应缺少 reply",
            relationship_state=relationship_state,
        )
        response.mistake_memory = mistake_memory
        return _persist_partner_simulation(request, response, session)
    score = content.get("score", _score_partner_message(request.user_message))
    suggestions = content.get("suggestions", [])
    response = PartnerSimulateResponse(
        reply=reply.strip(),
        score=round(_clamp(float(score) if isinstance(score, int | float) else 70, 0, 100)),
        source="ai_orchestrator",
        suggestions=[str(item) for item in suggestions[:3]] if isinstance(suggestions, list) else [],
        safety=ai_response.get("safety") or safety.to_dict(),
        safe_alternatives=ai_response.get("safe_alternatives") or [],
        relationship_state=relationship_state,
        mistake_memory=mistake_memory,
    )
    response.expression_chain = _partner_expression_chain(request, relationship_state, response.score, response.suggestions, response.reply)
    return _persist_partner_simulation(request, response, session)


def _normalize_partner_ai_content(raw: Any) -> dict[str, Any]:
    if not isinstance(raw, dict):
        return {}
    reply = _first_string(raw, ("reply", "message", "text", "content", "partner_reply", "response"))
    score = _coerce_score(raw.get("score", raw.get("rating", raw.get("relational_score"))))
    suggestions_raw = raw.get("suggestions", raw.get("advice", raw.get("tips", raw.get("coaching"))))
    suggestions = _coerce_suggestions(suggestions_raw)
    normalized: dict[str, Any] = {}
    if reply:
        normalized["reply"] = reply
    if score is not None:
        normalized["score"] = score
    if suggestions:
        normalized["suggestions"] = suggestions
    return normalized


def _first_string(raw: dict[str, Any], keys: tuple[str, ...]) -> str | None:
    for key in keys:
        value = raw.get(key)
        if isinstance(value, str) and value.strip():
            return value.strip()
    return None


def _coerce_score(value: Any) -> float | None:
    if isinstance(value, int | float):
        return _clamp(float(value), 0, 100)
    if isinstance(value, str):
        stripped = value.strip().rstrip("分")
        try:
            return _clamp(float(stripped), 0, 100)
        except ValueError:
            return None
    return None


def _coerce_suggestions(value: Any) -> list[str]:
    if isinstance(value, list):
        return [str(item).strip() for item in value[:3] if str(item).strip()]
    if isinstance(value, str) and value.strip():
        parts = [part.strip(" -•\t") for part in value.replace("；", "\n").replace("。", "\n").splitlines()]
        return [part for part in parts if part][:3]
    return []


@router.get("/partner/sessions/{session_id}/review")
def review_partner_session(session_id: int, session: Session = Depends(get_session)) -> dict[str, Any]:
    """复盘一次 AI 伴侣会话：状态曲线、关键转折、错误归因和下一轮建议。"""
    practice_session = session.exec(select(PracticeSession).where(PracticeSession.id == session_id)).first()
    if not practice_session:
        raise HTTPException(status_code=404, detail="训练会话不存在")
    events: list[PracticeEvent] = list(session.exec(
        select(PracticeEvent)
        .where(PracticeEvent.session_id == session_id)
        .order_by(_sql_column(PracticeEvent.turn_index), _sql_column(PracticeEvent.created_at))
    ).all())
    states = [_event_relationship_state(event) for event in events]
    return {
        "session": _practice_session_to_review_dict(practice_session),
        "state_curve": _partner_state_curve(events, states),
        "state_delta": _partner_state_delta(states),
        "turning_points": _partner_turning_points(events, states),
        "error_attribution": _partner_session_error_attribution(events, states),
        "next_practice": _partner_session_next_practice(practice_session, events, states),
        "principle": "沉浸对话用于获得真实感；状态曲线用于置身其外，看见关系动力如何被每一句话推动。",
    }


@router.post("/compare", response_model=CompareResponse)
def compare_response(request: CompareRequest, session: Session = Depends(get_session)) -> CompareResponse:
    """对比用户回应和理想回应，并写入训练记录/错题本。"""
    sample = session.exec(select(InteractionSample).where(InteractionSample.id == request.sample_id)).first()
    if not sample:
        raise HTTPException(status_code=404, detail="样本不存在")
    safety = safety_guardian.inspect(
        {
            "original_response": request.original_response,
            "response_type": request.response_type,
        }
    )
    if safety_guardian.should_block(safety):
        return CompareResponse(
            score=0,
            differences=[
                {
                    "type": "problem",
                    "name": "安全硬阻断",
                    "desc": safety.message or "检测到高风险内容，已阻断 AI 生成链路。",
                }
            ],
            suggestions=safety.alternatives or [],
            ideal_response="",
            diff_report=safety.message or "检测到高风险内容，已阻断 AI 生成链路。",
            dimension_scores={
                "emotion_score": 0,
                "need_score": 0,
                "safety_score": 0,
                "connection_score": 0,
                "boundary_score": 0,
                "style_score": 0,
                "repair_score": 0,
            },
            scoring_source="safety_blocked",
            ai_feedback={
                "ok": False,
                "reason": safety.message,
                "safety": safety.to_dict(),
                "safe_alternatives": safety.alternatives or [],
            },
            safe_alternatives=safety.alternatives or [],
            metacognitive_review=_build_safety_metacognitive_review(safety.alternatives or []),
        )

    ideal_map = {
        "soft": sample.good_response_soft,
        "tension": sample.good_response_tension or sample.good_response_soft,
        "humor": sample.good_response_humor or sample.good_response_soft,
    }
    ideal_response = ideal_map.get(request.response_type, sample.good_response_soft)
    rule_result = comparison_engine.compare(request.original_response, ideal_response, request.response_type)
    ai_feedback = _run_ai_score(request, sample, ideal_response, rule_result.score, rule_result.differences)
    result_score = _merge_score(rule_result.score, ai_feedback)
    result_differences = _merge_differences(rule_result.differences, ai_feedback)
    result_suggestions = _merge_suggestions(rule_result.suggestions, ai_feedback)
    diff_report = comparison_engine.generate_diff_report(rule_result)
    dimension_scores = _derive_dimension_scores(result_score, result_differences, sample, ai_feedback)
    metacognitive_review = _build_metacognitive_review(sample, request.original_response, ideal_response, result_differences)
    mastery = _build_mastery_model(dimension_scores)
    error_attribution = _attribute_errors(result_differences, sample, dimension_scores)
    gold_evaluation = _compare_against_gold_evidence(sample, result_score, dimension_scores, ai_feedback, rule_result.score)
    structured_diff = _build_structured_diff(sample, request.original_response, ideal_response, result_differences)
    expression_tool_scoring = _build_expression_tool_scoring(
        session,
        sample,
        request.original_response,
        ideal_response,
        request.response_type,
        dimension_scores,
        error_attribution,
    )

    feedback = {
        "rule_score": rule_result.score,
        "ai_feedback": ai_feedback,
        "gold_evaluation": gold_evaluation,
        "structured_diff": structured_diff,
        "differences": result_differences,
        "suggestions": result_suggestions,
        "ideal_response": ideal_response,
        "dimension_scores": dimension_scores,
        "metacognitive_review": metacognitive_review,
        "mastery": mastery,
        "error_attribution": error_attribution,
        "expression_tool_scoring": expression_tool_scoring,
    }
    attempt = TrainingAttempt(
        sample_id=sample.id or request.sample_id,
        mode="response",
        user_response=request.original_response,
        target_response_type=request.response_type,
        total_score=result_score,
        emotion_score=dimension_scores["emotion_score"],
        need_score=dimension_scores["need_score"],
        safety_score=dimension_scores["safety_score"],
        connection_score=dimension_scores["connection_score"],
        boundary_score=dimension_scores["boundary_score"],
        style_score=dimension_scores["style_score"],
        repair_score=dimension_scores["repair_score"],
        feedback_json=json.dumps(feedback, ensure_ascii=False),
    )
    session.add(attempt)
    session.commit()
    session.refresh(attempt)

    mistake_id = _maybe_create_mistake(
        session,
        sample,
        request.original_response,
        ideal_response,
        result_score,
        result_differences,
        error_attribution,
        mastery,
    )
    snapshot = _create_ability_snapshot(session)

    return CompareResponse(
        score=result_score,
        differences=result_differences,
        suggestions=result_suggestions,
        ideal_response=ideal_response,
        diff_report=diff_report,
        dimension_scores=dimension_scores,
        saved_attempt_id=attempt.id,
        mistake_id=mistake_id,
        next_recommendation=snapshot.next_recommendation if snapshot else None,
        scoring_source="hybrid" if ai_feedback and ai_feedback.get("ok") else "rule_fallback",
        ai_feedback=ai_feedback,
        safe_alternatives=(ai_feedback or {}).get("safe_alternatives") or [],
        metacognitive_review=metacognitive_review,
        mastery=mastery,
        error_attribution=error_attribution,
        gold_evaluation=gold_evaluation,
        structured_diff=structured_diff,
        expression_tool_scoring=expression_tool_scoring,
    )


@router.get("/radar")
def get_training_radar(session: Session = Depends(get_session)) -> dict[str, Any]:
    """基于真实训练记录生成能力雷达。"""
    attempts_count = _training_attempt_count(session)
    if not attempts_count:
        empty_mastery = _build_mastery_model({
            "emotion_score": 0,
            "need_score": 0,
            "safety_score": 0,
            "connection_score": 0,
            "boundary_score": 0,
            "style_score": 0,
            "repair_score": 0,
        })
        return {
            "levels": [
                {"name": "情绪识别", "score": 0, "description": "尚未训练"},
                {"name": "需求洞察", "score": 0, "description": "尚未训练"},
                {"name": "安全回应", "score": 0, "description": "尚未训练"},
                {"name": "连接延展", "score": 0, "description": "尚未训练"},
                {"name": "边界尊重", "score": 0, "description": "尚未训练"},
                {"name": "风格匹配", "score": 0, "description": "尚未训练"},
                {"name": "修复能力", "score": 0, "description": "尚未训练"},
            ],
            "total_score": 0,
            "level": "待启动",
            "weakest_dimension": "emotion_score",
            "next_recommendation": "先完成一次对比回应训练，建立能力基线",
            "mastery": empty_mastery,
        }

    avg = _calculate_average_scores(session)
    weakest = _weakest_dimension_from_scores(avg)
    total = sum(avg.values()) / len(avg)
    return {
        "levels": [
            {"name": "情绪识别", "score": round(avg["emotion_score"]), "description": "识别主情绪与强度"},
            {"name": "需求洞察", "score": round(avg["need_score"]), "description": "看见隐藏需求"},
            {"name": "安全回应", "score": round(avg["safety_score"]), "description": "降低防御与压力"},
            {"name": "连接延展", "score": round(avg["connection_score"]), "description": "打开而非关闭对话"},
            {"name": "边界尊重", "score": round(avg["boundary_score"]), "description": "尊重对方自主与节奏"},
            {"name": "风格匹配", "score": round(avg["style_score"]), "description": "柔和/张力/幽默适配"},
            {"name": "修复能力", "score": round(avg["repair_score"]), "description": "冲突后的负责与修复"},
        ],
        "total_score": round(total),
        "level": _score_to_level(total),
        "weakest_dimension": weakest,
        "next_recommendation": _dimension_recommendation(weakest),
        "mastery": _build_mastery_model(avg),
    }


@router.get("/mistakes")
def get_mistakes(session: Session = Depends(get_session)) -> list[dict[str, Any]]:
    """获取错题本列表。"""
    mistakes = session.exec(
        select(MistakeLog).where(MistakeLog.reviewed == False).order_by(desc(MistakeLog.id)).limit(20)  # noqa: E712
    ).all()
    result = []
    for m in mistakes:
        sample = session.exec(select(InteractionSample).where(InteractionSample.id == m.sample_id)).first()
        if sample:
            result.append({
                "id": m.id,
                "context": sample.context,
                "their_words": sample.their_words,
                "user_bad_response": m.user_bad_response,
                "correct_response": m.correct_response,
                "emotion_mistake": m.emotion_mistake,
                "error_attribution": _loads_json_list(m.error_attribution_json),
                "mastery_snapshot": _loads_json_dict(m.mastery_snapshot_json),
                "emotion_flow": _mistake_emotion_flow(sample, m),
                "rewrite_drills": _mistake_rewrite_drills(sample, m),
                "expression_rewrite": _mistake_expression_rewrite(session, sample, m),
                "resource_queries": _mistake_resource_queries(sample, m),
                "review_focus": m.review_focus,
                "next_review": str(m.next_review) if m.next_review else None,
                "correct_count": m.correct_count,
                "wrong_count": m.wrong_count,
            })
    return result


def _mistake_emotion_flow(sample: InteractionSample, mistake: MistakeLog) -> list[str]:
    attributions = _loads_json_list(mistake.error_attribution_json)
    first_reason = ""
    if attributions and isinstance(attributions[0], dict):
        first_reason = str(attributions[0].get("reason") or "")
    hidden_need = sample.hidden_need or "未说出口的需要"
    return [
        f"线索：{sample.their_words}",
        f"可能情绪/需要：{hidden_need}",
        f"失误拐点：{first_reason or mistake.emotion_mistake or '回应没有先承接情绪与边界'}",
        "修复方向：先复述感受，再给退路，最后提出一个轻问题。",
    ]


def _mistake_rewrite_drills(sample: InteractionSample, mistake: MistakeLog) -> list[str]:
    focus = mistake.review_focus or "情绪承接"
    return [
        f"只改第一句：用“听起来/我感觉你可能...”承接 {focus}。",
        "加一个退路：明确对方可以慢一点、拒绝或晚点再说。",
        "补一个轻问题：只验证一个假设，不连环追问。",
    ]


def _mistake_expression_rewrite(
    session: Session,
    sample: InteractionSample,
    mistake: MistakeLog,
) -> dict[str, Any]:
    attributions = _loads_json_list(mistake.error_attribution_json)
    dimensions = [str(item.get("dimension")) for item in attributions if isinstance(item, dict) and item.get("dimension")]
    if not dimensions:
        dimensions = ["emotion_score", "boundary_score", "connection_score"]
    tool_ids = _unique_tool_ids(
        [
            *EXPRESSION_SCENE_DEFAULTS.get(sample.scenario_category, ("expr_tool_041", "expr_tool_027", "expr_tool_019")),
            *[tool_id for dimension in dimensions for tool_id in EXPRESSION_TOOL_BY_DIMENSION.get(dimension, ())],
        ]
    )[:5]
    tools = _load_expression_tools(session, tool_ids)
    primary_tool = tools[0]["name"] if tools else "情绪标注"
    target_goal = _expression_goal_for(sample, dimensions[:3], "soft")
    focus = mistake.review_focus or target_goal
    context_hint = f"对方说“{sample.their_words}”"
    return {
        "target_goal": target_goal,
        "primary_tool": primary_tool,
        "recommended_tools": tools[:4],
        "rewrite_versions": [
            {
                "name": "低压承接版",
                "text": f"听起来你这里有点{_sample_emotion_word(sample)}，我先不急着判断。你愿意的话，我想先听你多说一点。",
                "tool": "情绪标注 + 留白沉默",
            },
            {
                "name": "边界清晰版",
                "text": "我听见这件事对你有影响。你可以现在说，也可以晚点说；我会尊重你的节奏。",
                "tool": "边界声明 + 请求结构",
            },
            {
                "name": "行动修复版",
                "text": f"刚才我的回应没有接住重点。接下来我先做一件具体的事：把{focus}说清楚，再问你是否愿意继续。",
                "tool": "道歉结构 + 修复请求",
            },
        ],
        "transfer_drill": f"换一个相邻场景复写：{context_hint}，只用「{primary_tool}」完成一句回应。",
        "forbidden_moves": [
            "不要把解释放在承接之前。",
            "不要用玩笑否定对方感受。",
            "不要连续追问或要求立刻表态。",
        ],
        "principle": "错题改写不是背标准答案，而是把同一个失误拆成工具、边界和可迁移动作。",
    }


def _sample_emotion_word(sample: InteractionSample) -> str:
    tags = _parse_emotion_tags(sample.emotion_tags_json)
    if tags:
        word = tags[0].get("word")
        if word:
            return str(word)
    if sample.hidden_need:
        return "在意"
    return "情绪"


def _mistake_resource_queries(sample: InteractionSample, mistake: MistakeLog) -> list[str]:
    queries = [
        sample.scenario_category,
        mistake.review_focus or "",
        mistake.emotion_mistake or "",
        "情绪流动",
        "边界",
    ]
    return [query for query in dict.fromkeys(str(item).strip() for item in queries) if query][:4]


@router.get("/reviews/due")
def get_due_reviews(session: Session = Depends(get_session)) -> list[dict[str, Any]]:
    """获取今天到期的错题复习。"""
    mistakes = session.exec(
        select(MistakeLog)
        .where(MistakeLog.reviewed == False)  # noqa: E712
        .where(or_(_sql_column(MistakeLog.next_review).is_(None), _sql_column(MistakeLog.next_review) <= date.today()))
        .limit(20)
    ).all()
    items = []
    for m in mistakes:
        sample = session.exec(select(InteractionSample).where(InteractionSample.id == m.sample_id)).first()
        if sample:
            items.append({"mistake_id": m.id, "sample": sample, "next_review": str(m.next_review) if m.next_review else None})
    return items


@router.post("/reviews/{mistake_id}")
def submit_review(mistake_id: int, request: ReviewSubmitRequest, session: Session = Depends(get_session)) -> dict[str, Any]:
    """提交错题复习结果并更新间隔。"""
    mistake = session.exec(select(MistakeLog).where(MistakeLog.id == mistake_id)).first()
    if not mistake:
        raise HTTPException(status_code=404, detail="错题不存在")
    if request.correct:
        mistake.correct_count += 1
        intervals = [3, 7, 14, 30]
        mistake.review_interval = intervals[min(mistake.correct_count - 1, len(intervals) - 1)]
        if mistake.correct_count >= 4:
            mistake.reviewed = True
    else:
        mistake.wrong_count += 1
        mistake.correct_count = 0
        mistake.review_interval = 1
        mistake.reviewed = False
    mistake.next_review = date.today() + timedelta(days=mistake.review_interval)
    session.add(mistake)
    session.commit()
    _create_ability_snapshot(session)
    return {"ok": True, "next_review": str(mistake.next_review), "reviewed": mistake.reviewed}


def build_training_visual_map(sample: InteractionSample) -> dict[str, Any]:
    """从样本元字段派生数图结合训练地图，不把推断包装成确定事实。"""
    persisted = _persisted_visual_map(sample)
    if persisted:
        return persisted
    return derive_training_visual_map(sample)


def derive_training_visual_map(sample: InteractionSample) -> dict[str, Any]:
    """从样本基础字段派生多粒度训练地图。"""
    emotions = _parse_emotion_tags(sample.emotion_tags_json)
    dominant = _dominant_emotion(emotions)
    average_intensity = _average_intensity(emotions)
    boundary_level = sample.boundary_test_level or 1
    need_urgency = sample.need_urgency or max(1, round(average_intensity))
    hidden_need = sample.hidden_need or "待训练者从语境中识别"
    signal_highlights = _build_signal_highlights(sample, emotions)
    emotion_flow_curve = _build_emotion_flow_curve(average_intensity, need_urgency, boundary_level)
    need_radar = _build_need_radar(hidden_need, need_urgency, sample.attachment_signal)
    boundary_band = _build_boundary_band(boundary_level)

    return {
        "axiom": "数负责入微，图负责直觉，文字负责意义；所有判断先作为假设，再用轻问句验证。",
        "signal_highlights": signal_highlights,
        "emotion_thermometer": {
            "spectrum": dominant.get("spectrum", "未标注"),
            "word": dominant.get("word", "待识别"),
            "intensity": dominant.get("intensity", 0),
            "average_intensity": average_intensity,
            "percent": round(average_intensity * 10),
            "zone": _intensity_zone(average_intensity),
            "principle": _intensity_principle(average_intensity),
        },
        "developmental_emotion_transition": _derive_developmental_emotion_transition(
            sample,
            emotions,
            average_intensity,
            need_urgency,
            boundary_level,
        ),
        "emotion_flow_curve": emotion_flow_curve,
        "need_radar": need_radar,
        "boundary_band": boundary_band,
        "interaction_loop_graph": {
            "nodes": [
                {"id": "context", "label": "场景", "value": sample.scenario_category},
                {"id": "signal", "label": "信号", "value": _primary_signal(sample)},
                {"id": "emotion", "label": "情绪", "value": f"{dominant.get('word', '待识别')} {dominant.get('intensity', 0)}/10"},
                {"id": "need", "label": "需求", "value": hidden_need},
                {"id": "boundary", "label": "边界", "value": f"{boundary_level}/10"},
                {"id": "response", "label": "回应方向", "value": _response_direction(sample)},
            ],
            "edges": [
                {"from": "context", "to": "signal", "meaning": "场景生成线索"},
                {"from": "signal", "to": "emotion", "meaning": "线索指向情绪假设"},
                {"from": "emotion", "to": "need", "meaning": "情绪背后常有需求"},
                {"from": "need", "to": "boundary", "meaning": "需求必须经过边界校准"},
                {"from": "boundary", "to": "response", "meaning": "回应要兼顾连接与自主"},
            ],
        },
        "five_w_two_h": {
            "why": hidden_need,
            "what": _emotion_sentence(emotions),
            "who": sample.attachment_signal or "待判断",
            "when": sample.scenario_category,
            "where": _infer_channel(sample.context),
            "how": sample.their_behavior or sample.their_words,
            "how_much": {
                "emotion_intensity": round(average_intensity, 1),
                "need_urgency": need_urgency,
                "boundary_level": boundary_level,
            },
        },
        "tension_dimensions": _derive_tension_dimensions(sample, {
            "need_radar": need_radar,
            "boundary_band": boundary_band,
            "emotion_flow_curve": emotion_flow_curve,
        }),
        "gold_label": _loads_json_dict(sample.gold_label_json),
        "review_status": sample.review_status,
        "is_gold_sample": sample.is_gold_sample,
        "verification_prompts": _verification_prompts(dominant, hidden_need, boundary_level),
        "anti_manipulation_note": "目标是看见、理解与尊重，不是诱导、控制或压迫对方。",
    }


def persist_sample_multigranular_map(sample: InteractionSample) -> dict[str, Any]:
    """把派生训练地图回填到样本，形成可版本化的关系动力学标本。"""
    visual_map = derive_training_visual_map(sample)
    sample.signal_highlights_json = json.dumps(visual_map["signal_highlights"], ensure_ascii=False)
    sample.emotion_flow_json = json.dumps(visual_map["emotion_flow_curve"], ensure_ascii=False)
    sample.need_radar_json = json.dumps(visual_map["need_radar"], ensure_ascii=False)
    sample.boundary_state_json = json.dumps(visual_map["boundary_band"], ensure_ascii=False)
    sample.five_w_two_h_json = json.dumps(visual_map["five_w_two_h"], ensure_ascii=False)
    sample.feeling_tags_json = json.dumps(_derive_feeling_tags(visual_map), ensure_ascii=False)
    sample.source_trace_json = json.dumps(_derive_sample_source_trace(sample), ensure_ascii=False)
    sample.quality_json = json.dumps(_derive_sample_quality(sample, visual_map), ensure_ascii=False)
    sample.tension_dimensions_json = json.dumps(_derive_tension_dimensions(sample, visual_map), ensure_ascii=False)
    sample.annotation_version = "multigranular-v1"
    sample.review_status = "reviewed"
    return build_training_visual_map(sample)


def _persisted_visual_map(sample: InteractionSample) -> dict[str, Any] | None:
    required = [
        sample.signal_highlights_json,
        sample.emotion_flow_json,
        sample.need_radar_json,
        sample.boundary_state_json,
        sample.five_w_two_h_json,
    ]
    if not all(required):
        return None
    emotions = _parse_emotion_tags(sample.emotion_tags_json)
    dominant = _dominant_emotion(emotions)
    average_intensity = _average_intensity(emotions)
    return {
        "axiom": "数负责入微，图负责直觉，文字负责意义；所有判断先作为假设，再用轻问句验证。",
        "annotation_version": sample.annotation_version,
        "signal_highlights": _loads_json_list(sample.signal_highlights_json),
        "emotion_thermometer": {
            "spectrum": dominant.get("spectrum", "未标注"),
            "word": dominant.get("word", "待识别"),
            "intensity": dominant.get("intensity", 0),
            "average_intensity": average_intensity,
            "percent": round(average_intensity * 10),
            "zone": _intensity_zone(average_intensity),
            "principle": _intensity_principle(average_intensity),
        },
        "developmental_emotion_transition": _derive_developmental_emotion_transition(
            sample,
            emotions,
            average_intensity,
            sample.need_urgency or max(1, round(average_intensity)),
            sample.boundary_test_level or 1,
        ),
        "emotion_flow_curve": _loads_json_list(sample.emotion_flow_json),
        "need_radar": _loads_json_list(sample.need_radar_json),
        "boundary_band": _loads_json_dict(sample.boundary_state_json),
        "interaction_loop_graph": _interaction_loop_graph_from_sample(sample, dominant),
        "five_w_two_h": _loads_json_dict(sample.five_w_two_h_json),
        "feeling_tags": _loads_json_list(sample.feeling_tags_json),
        "source_trace": _loads_json_dict(sample.source_trace_json),
        "quality": _loads_json_dict(sample.quality_json),
        "tension_dimensions": _loads_json_list(sample.tension_dimensions_json),
        "gold_label": _loads_json_dict(sample.gold_label_json),
        "review_status": sample.review_status,
        "is_gold_sample": sample.is_gold_sample,
        "verification_prompts": _verification_prompts(
            dominant,
            sample.hidden_need or "待训练者从语境中识别",
            sample.boundary_test_level or 1,
        ),
        "anti_manipulation_note": "目标是看见、理解与尊重，不是诱导、控制或压迫对方。",
    }


def _interaction_loop_graph_from_sample(sample: InteractionSample, dominant: dict[str, Any]) -> dict[str, Any]:
    hidden_need = sample.hidden_need or "待训练者从语境中识别"
    boundary_level = sample.boundary_test_level or 1
    return {
        "nodes": [
            {"id": "context", "label": "场景", "value": sample.scenario_category},
            {"id": "signal", "label": "信号", "value": _primary_signal(sample)},
            {"id": "emotion", "label": "情绪", "value": f"{dominant.get('word', '待识别')} {dominant.get('intensity', 0)}/10"},
            {"id": "need", "label": "需求", "value": hidden_need},
            {"id": "boundary", "label": "边界", "value": f"{boundary_level}/10"},
            {"id": "response", "label": "回应方向", "value": _response_direction(sample)},
        ],
        "edges": [
            {"from": "context", "to": "signal", "meaning": "场景生成线索"},
            {"from": "signal", "to": "emotion", "meaning": "线索指向情绪假设"},
            {"from": "emotion", "to": "need", "meaning": "情绪背后常有需求"},
            {"from": "need", "to": "boundary", "meaning": "需求必须经过边界校准"},
            {"from": "boundary", "to": "response", "meaning": "回应要兼顾连接与自主"},
        ],
    }


def _derive_feeling_tags(visual_map: dict[str, Any]) -> list[dict[str, Any]]:
    radar = visual_map["need_radar"]
    tags: list[dict[str, Any]] = []
    for item in radar:
        if item["value"] >= 60:
            tags.append({
                "name": item["name"],
                "polarity": "need",
                "intensity": round(item["value"] / 10, 1),
                "evidence": item.get("evidence", "由需求雷达派生"),
            })
    return tags or [{"name": "待识别", "polarity": "unknown", "intensity": 0, "evidence": "需要训练者轻验证"}]


def _derive_sample_source_trace(sample: InteractionSample) -> dict[str, Any]:
    return {
        "sample_uuid": sample.sample_uuid,
        "source": sample.source or "local_seed",
        "source_url": sample.source_url,
        "principle_ref": sample.principle_ref,
        "annotation_method": "rule_derived_from_visual_map",
    }


def _derive_sample_quality(sample: InteractionSample, visual_map: dict[str, Any]) -> dict[str, Any]:
    signals = visual_map["signal_highlights"]
    has_good_responses = bool(sample.good_response_soft and sample.bad_response)
    safety_score = 0.95 if (sample.boundary_test_level or 1) <= 8 else 0.82
    return {
        "relationship_realism": round(min(0.95, 0.55 + len(signals) * 0.08), 2),
        "training_value": 0.9 if has_good_responses else 0.62,
        "annotation_confidence": 0.78 if sample.hidden_need else 0.62,
        "safety_score": safety_score,
        "version": "multigranular-v1",
    }


def _derive_tension_dimensions(sample: InteractionSample, visual_map: dict[str, Any]) -> list[dict[str, Any]]:
    boundary = sample.boundary_test_level or 1
    need = sample.need_urgency or 5
    intensity = _average_intensity(_parse_emotion_tags(sample.emotion_tags_json))
    return [
        {
            "axis": "靠近-自主",
            "value": round(_clamp(need * 9 - boundary * 3, 0, 100)),
            "left": "给空间",
            "right": "靠近承接",
            "evidence": "由需求紧迫度与边界压力共同估算",
        },
        {
            "axis": "安全-新鲜",
            "value": round(_clamp((10 - boundary) * 7 + sample.difficulty_level * 8, 0, 100)),
            "left": "稳定安全",
            "right": "轻微张力",
            "evidence": "由边界安全与难度层级估算",
        },
        {
            "axis": "情绪-事实",
            "value": round(_clamp(intensity * 10, 0, 100)),
            "left": "事实信息",
            "right": "情绪承接",
            "evidence": visual_map.get("emotion_thermometer", {}).get("principle", "由情绪温度计估算"),
        },
    ]


def _derive_developmental_emotion_transition(
    sample: InteractionSample,
    emotions: list[dict[str, Any]],
    average_intensity: float,
    need_urgency: int,
    boundary_level: int,
) -> dict[str, Any]:
    dominant = _dominant_emotion(emotions)
    transition = _transition_type_for(sample, emotions, average_intensity, boundary_level)
    dimensions = {
        "intensity": {
            "value": round(average_intensity, 1),
            "label": _intensity_zone(average_intensity),
            "principle": _intensity_principle(average_intensity),
        },
        "valence": _emotion_valence(emotions),
        "target": _emotion_target(sample),
        "phase": _emotion_phase(average_intensity, need_urgency, boundary_level),
    }
    return {
        "axis": "developmental_emotion_transition",
        "label": "发展性情绪跃迁",
        "dimensions": dimensions,
        "transition_type": transition["type"],
        "transition_goal": transition["goal"],
        "scaffold_level": _developmental_scaffold_level(sample, average_intensity, boundary_level),
        "primary_emotion": dominant.get("word", "待识别"),
        "mixed_emotion": len(emotions) >= 2,
        "support_steps": _transition_support_steps(transition["type"], dimensions),
        "response_contract": "先四维定位，再选择一种跃迁路径；所有情绪假设都必须允许对方纠正。",
    }


def _transition_type_for(
    sample: InteractionSample,
    emotions: list[dict[str, Any]],
    average_intensity: float,
    boundary_level: int,
) -> dict[str, str]:
    if average_intensity >= 8 or boundary_level >= 8:
        return {"type": "同层强度跃迁", "goal": "先降低强度，让对话回到可承载范围。"}
    if len(emotions) >= 2 or sample.scenario_category in {"冲突", "修复"}:
        return {"type": "跨维质变跃迁", "goal": "在安全前提下，把表层情绪翻译成更底层的感受或需要。"}
    if sample.scenario_category in {"长期", "平淡"} or "模式" in (sample.context + sample.their_words):
        return {"type": "跨层元认知跃迁", "goal": "把单次情绪整理成可复盘、可内化的长期策略。"}
    return {"type": "同层强度跃迁", "goal": "轻承接和轻验证，避免过度解释。"}


def _emotion_valence(emotions: list[dict[str, Any]]) -> dict[str, Any]:
    positive_words = {"开心", "兴奋", "喜欢", "安心", "期待", "喜悦", "轻松", "感激", "温暖"}
    negative_words = {"难过", "委屈", "失望", "焦虑", "害怕", "压力", "羞耻", "生气", "愤怒", "不安", "累"}
    has_positive = any(str(item.get("word", "")) in positive_words for item in emotions)
    has_negative = any(str(item.get("word", "")) in negative_words for item in emotions)
    if has_positive and has_negative:
        return {"label": "正负混合", "evidence": "同一情绪事件里同时有靠近和防御信号。"}
    if has_positive:
        return {"label": "正性", "evidence": "主要情绪更接近靠近、期待或放松。"}
    if has_negative:
        return {"label": "负性", "evidence": "主要情绪更接近受伤、不安、压力或防御。"}
    return {"label": "待识别", "evidence": "样本情绪词不足，需要从原话和行为中轻验证。"}


def _emotion_target(sample: InteractionSample) -> dict[str, str]:
    text = f"{sample.context} {sample.their_words} {sample.hidden_need or ''}"
    if any(word in text for word in ("我们", "关系", "聊天", "约", "相信", "陪")):
        return {"label": "关系", "evidence": "线索指向双方连接、节奏或信任。"}
    if any(word in text for word in ("我觉得自己", "我是不是", "自己", "配不上", "停不下来")):
        return {"label": "自我", "evidence": "线索指向自我评价或自我模式。"}
    if any(word in text for word in ("你", "对方", "他说", "她说")):
        return {"label": "他人", "evidence": "线索指向对方行为和回应。"}
    return {"label": "环境", "evidence": "当前更像由场景压力或外部事件触发。"}


def _emotion_phase(average_intensity: float, need_urgency: int, boundary_level: int) -> dict[str, str]:
    peak = max(average_intensity, need_urgency, boundary_level)
    if peak >= 8:
        return {"label": "高峰", "response_rule": "停止推进，先稳定和给空间。"}
    if peak >= 6:
        return {"label": "上升", "response_rule": "先承接感受，再轻验证需要。"}
    if peak >= 3:
        return {"label": "触发", "response_rule": "用一个具体线索打开对话。"}
    return {"label": "预期/残余", "response_rule": "轻轻标记即可，不需要深挖。"}


def _developmental_scaffold_level(sample: InteractionSample, average_intensity: float, boundary_level: int) -> dict[str, str]:
    if average_intensity >= 8 or boundary_level >= 8:
        return {"level": "基础情绪支架", "rule": "高唤醒状态近似低龄承载力：先命名、安抚、降强度。"}
    if sample.difficulty_level <= 1:
        return {"level": "命名与轻验证", "rule": "先把模糊感受说清楚，不急着上价值。"}
    if sample.difficulty_level == 2:
        return {"level": "观点采择", "rule": "区分事实、情绪、需要和边界。"}
    return {"level": "元认知整合", "rule": "在余波期复盘模式，并形成下次可用的自我提醒。"}


def _transition_support_steps(transition_type: str, dimensions: dict[str, Any]) -> list[str]:
    if transition_type == "跨维质变跃迁":
        return [
            "先承认表层情绪，不急着纠正。",
            "用“会不会也有一点……”试探底层感受。",
            "允许对方说“不对，你理解偏了”。",
        ]
    if transition_type == "跨层元认知跃迁":
        return [
            "先说清这一次发生了什么。",
            "连接到重复出现的模式或需要。",
            "生成一句下次能自我提醒的话。",
        ]
    phase = dimensions.get("phase", {}).get("label", "触发")
    return [
        f"当前处于{phase}阶段，先让强度可承载。",
        "用具体事实承接，不做人格评价。",
        "补一句暂停或继续都可以的出口。",
    ]


def _compare_against_gold_evidence(
    sample: InteractionSample,
    score: float,
    dimension_scores: dict[str, float],
    ai_feedback: dict[str, Any] | None,
    rule_score: float,
) -> dict[str, Any]:
    gold_label = _loads_json_dict(sample.gold_label_json)
    if not sample.is_gold_sample and not gold_label:
        return {
            "available": False,
            "reason": "sample_not_in_gold_set",
        }
    expected = gold_label.get("expected_scores") if isinstance(gold_label.get("expected_scores"), dict) else {}
    expected_total = float(expected.get("total_score", score)) if expected else score
    delta = round(score - expected_total, 1)
    ai_score = _ai_score(ai_feedback)
    return {
        "available": True,
        "sample_uuid": sample.sample_uuid,
        "gold_version": gold_label.get("version", "gold-v1"),
        "review_status": sample.review_status,
        "rule_score": round(rule_score, 1),
        "ai_score": ai_score,
        "merged_score": round(score, 1),
        "expected_total_score": round(expected_total, 1),
        "delta_from_gold": delta,
        "within_tolerance": abs(delta) <= 12,
        "dimension_deltas": {
            key: round(float(dimension_scores.get(key, 0)) - float(_safe_dict_get(expected, key, dimension_scores.get(key, 0))), 1)
            for key in dimension_scores
        },
        "principle": "Gold Set 不替代训练反馈，而是校准规则评分、AI 深评与人工审阅证据是否同向。",
    }


def _build_structured_diff(
    sample: InteractionSample,
    original_response: str,
    ideal_response: str,
    differences: list[dict[str, Any]],
) -> dict[str, Any]:
    original_tokens = _response_tokens(original_response)
    ideal_tokens = _response_tokens(ideal_response)
    missing = [token for token in ideal_tokens if token not in original_tokens][:12]
    extra = [token for token in original_tokens if token not in ideal_tokens][:12]
    shared = [token for token in ideal_tokens if token in original_tokens][:12]
    emotions = _parse_emotion_tags(sample.emotion_tags_json)
    emotion_words = [str(item.get("word", "")) for item in emotions if item.get("word")]
    acknowledged = [word for word in emotion_words if word and word in original_response]
    return {
        "word_level": {
            "shared": shared,
            "missing_from_user": missing,
            "extra_from_user": extra,
            "coverage": round(len(shared) / max(len(ideal_tokens), 1), 3),
        },
        "structure_level": {
            "has_empathy": any(word in original_response for word in ["听起来", "感觉", "理解", "辛苦", "委屈"]),
            "has_open_question": "？" in original_response or "?" in original_response or any(word in original_response for word in ["能说说", "要不要", "愿意"]),
            "has_boundary_respect": any(word in original_response for word in ["不急", "如果你愿意", "空间", "没关系", "尊重"]),
            "problem_count": sum(1 for item in differences if item.get("type") == "problem"),
        },
        "emotion_path": {
            "expected_emotions": emotion_words,
            "acknowledged_emotions": acknowledged,
            "missed_emotions": [word for word in emotion_words if word not in acknowledged],
            "suggested_path": ["观察事实", "命名情绪", "轻验证需求", "尊重边界", "给下一步"],
        },
        "developmental_emotion_transition": _build_response_transition_feedback(sample, original_response, ideal_response),
        "principle": "词级看缺口，结构级看回应骨架，情绪路径看是否按关系动力顺序承接。",
    }


def _response_tokens(text: str) -> list[str]:
    chunks = [chunk.strip("，。！？,.!?；;：:（）() ") for chunk in text.split()]
    if len(chunks) > 1:
        return [chunk for chunk in chunks if chunk]
    return [char for char in text if char.strip() and char not in "，。！？,.!?；;：:（）() "]


def _build_response_transition_feedback(
    sample: InteractionSample,
    original_response: str,
    ideal_response: str,
) -> dict[str, Any]:
    visual_map = build_training_visual_map(sample)
    transition = visual_map.get("developmental_emotion_transition", {})
    dimensions = transition.get("dimensions", {}) if isinstance(transition, dict) else {}
    markers = _developmental_response_markers(original_response)
    expected_moves = _expected_developmental_moves(transition, ideal_response if isinstance(transition, dict) else "")
    missing_moves = [move for key, move in expected_moves.items() if not markers.get(key)]
    return {
        "axis": "developmental_emotion_transition",
        "emotion_dimensions": dimensions,
        "transition_type": transition.get("transition_type", "待判断") if isinstance(transition, dict) else "待判断",
        "transition_goal": transition.get("transition_goal", "先定位再回应") if isinstance(transition, dict) else "先定位再回应",
        "scaffold_level": transition.get("scaffold_level", {}) if isinstance(transition, dict) else {},
        "detected_moves": markers,
        "missing_moves": missing_moves[:4],
        "next_sentence": _developmental_next_sentence(missing_moves, transition if isinstance(transition, dict) else {}),
        "principle": "情绪回应不是只贴标签：要看强度、效价、指向、时序，再选择一种跃迁路径。",
    }


def _developmental_response_markers(text: str) -> dict[str, bool]:
    normalized = text.strip()
    return {
        "observes_fact": any(word in normalized for word in ("你说", "我听见", "我注意到", "刚才", "这件事", "停了一下")),
        "names_emotion": any(word in normalized for word in ("难过", "委屈", "不安", "害怕", "开心", "压力", "累", "悬着", "担心", "羞耻")),
        "calibrates_intensity": any(word in normalized for word in ("有点", "很", "越来越", "先慢", "先停", "强", "轻一点", "缓一下")),
        "holds_mixed_emotion": any(word in normalized for word in ("同时", "一边", "也有", "两个感觉", "又", "既")),
        "keeps_boundary": any(word in normalized for word in ("不急", "可以停", "不想说", "你可以", "如果愿意", "不用现在", "先到这里")),
        "supports_transition": any(word in normalized for word in ("背后", "更像", "会不会", "模式", "下次", "提醒自己", "先把")),
    }


def _expected_developmental_moves(transition: dict[str, Any], ideal_response: str) -> dict[str, str]:
    transition_type = str(transition.get("transition_type") or "")
    expected = {
        "observes_fact": "先引用一个具体事实或原话，避免空泛共情。",
        "names_emotion": "补一个可纠正的情绪词。",
        "keeps_boundary": "给对方暂停、纠正或降低深度的出口。",
    }
    if transition_type == "同层强度跃迁":
        expected["calibrates_intensity"] = "先处理强度变化，例如慢一点、停一下、先降下来。"
    elif transition_type == "跨维质变跃迁":
        expected["holds_mixed_emotion"] = "承认混合情绪，不把开心/生气/沉默简化成单一含义。"
        expected["supports_transition"] = "用试探式语言翻译底层感受，例如“会不会更像委屈”。"
    elif transition_type == "跨层元认知跃迁":
        expected["supports_transition"] = "把这次情绪连接到可复盘的模式或下次自我提醒。"
    if "同时" in ideal_response or "两个" in ideal_response:
        expected["holds_mixed_emotion"] = "理想回应里有混合情绪，用户回应也要能同时容纳两种感受。"
    return expected


def _developmental_next_sentence(missing_moves: list[str], transition: dict[str, Any]) -> str:
    if missing_moves:
        return missing_moves[0]
    transition_type = str(transition.get("transition_type") or "情绪跃迁")
    return f"这次已经覆盖主要支架，下一步练习把「{transition_type}」迁移到另一个场景。"


def _ai_score(ai_feedback: dict[str, Any] | None) -> float | None:
    if not ai_feedback or not ai_feedback.get("ok"):
        return None
    score = ai_feedback.get("score")
    return round(float(score), 1) if isinstance(score, int | float) else None


def _loads_json_list(raw: str | None) -> list[Any]:
    if not raw:
        return []
    try:
        data = json.loads(raw)
    except json.JSONDecodeError:
        return []
    return data if isinstance(data, list) else []


def _loads_json_dict(raw: str | None) -> dict[str, Any]:
    if not raw:
        return {}
    try:
        data = json.loads(raw)
    except json.JSONDecodeError:
        return {}
    return data if isinstance(data, dict) else {}


def _parse_emotion_tags(raw: str | None) -> list[dict[str, Any]]:
    if not raw:
        return []
    try:
        data = json.loads(raw)
    except json.JSONDecodeError:
        return []
    if not isinstance(data, list):
        return []
    emotions: list[dict[str, Any]] = []
    for item in data:
        if not isinstance(item, dict):
            continue
        intensity = item.get("intensity", 0)
        emotions.append({
            "spectrum": str(item.get("spectrum") or "未标注"),
            "word": str(item.get("word") or "待识别"),
            "intensity": _clamp(float(intensity) if isinstance(intensity, int | float) else 0, 0, 10),
        })
    return emotions


def _dominant_emotion(emotions: list[dict[str, Any]]) -> dict[str, Any]:
    if not emotions:
        return {}
    return max(emotions, key=lambda emotion: float(emotion.get("intensity", 0)))


def _average_intensity(emotions: list[dict[str, Any]]) -> float:
    if not emotions:
        return 0.0
    return round(sum(float(emotion.get("intensity", 0)) for emotion in emotions) / len(emotions), 1)


def _build_signal_highlights(sample: InteractionSample, emotions: list[dict[str, Any]]) -> list[dict[str, Any]]:
    highlights: list[dict[str, Any]] = []
    if sample.their_words:
        highlights.append({
            "type": "language",
            "label": "语言线索",
            "text": sample.their_words,
            "weight": 0.42,
            "hypothesis": "先从字面信息进入，再观察是否有邀请、求助、试探或修复信号。",
        })
    if sample.their_behavior:
        highlights.append({
            "type": "behavior",
            "label": "行为线索",
            "text": sample.their_behavior,
            "weight": 0.28,
            "hypothesis": "非语言线索用于校准情绪强度，不能单独下结论。",
        })
    if sample.hidden_need:
        highlights.append({
            "type": "need",
            "label": "需求假设",
            "text": sample.hidden_need,
            "weight": 0.18,
            "hypothesis": "这是样本标注中的隐藏需求，训练时要用轻问句验证。",
        })
    for emotion in emotions[:3]:
        highlights.append({
            "type": "emotion",
            "label": f"{emotion['spectrum']} · {emotion['word']}",
            "text": f"强度 {emotion['intensity']}/10",
            "weight": round(float(emotion["intensity"]) / 10, 2),
            "hypothesis": "情绪标签是回应顺序的入口：先接住，再推进。",
        })
    return highlights[:6]


def _build_emotion_flow_curve(average_intensity: float, need_urgency: int, boundary_level: int) -> list[dict[str, Any]]:
    opening = _clamp(average_intensity - 1, 0, 10)
    peak = _clamp(max(average_intensity, need_urgency, boundary_level), 0, 10)
    turn = _clamp((average_intensity + need_urgency) / 2, 0, 10)
    landing = _clamp(peak - (3 if boundary_level >= 7 else 2), 1, 10)
    return [
        {"step": "起点", "value": round(opening, 1), "label": "刚出现的信号"},
        {"step": "高峰", "value": round(peak, 1), "label": "情绪/需求/边界的最高压力"},
        {"step": "转折", "value": round(turn, 1), "label": "被看见后的可对话窗口"},
        {"step": "落点", "value": round(landing, 1), "label": "理想回应后的稳定目标"},
    ]


def _build_need_radar(hidden_need: str, need_urgency: int, attachment_signal: str | None) -> list[dict[str, Any]]:
    text = hidden_need or ""
    base = _clamp(float(need_urgency), 1, 10) * 10
    dimensions = {
        "被看见": 45.0,
        "被理解": 45.0,
        "安全感": 45.0,
        "自主边界": 45.0,
        "连接延展": 45.0,
    }
    keyword_map = {
        "被看见": ["看到", "认可", "注意", "欣赏", "重视"],
        "被理解": ["理解", "懂", "共情", "倾听"],
        "安全感": ["安全", "稳定", "陪", "确认", " reassurance"],
        "自主边界": ["空间", "退路", "不逼", "边界", "选择"],
        "连接延展": ["约", "聊天", "分享", "靠近", "继续"],
    }
    for name, words in keyword_map.items():
        if any(word in text for word in words):
            dimensions[name] = max(dimensions[name], base)
    if attachment_signal == "焦虑型":
        dimensions["安全感"] = max(dimensions["安全感"], 78)
    elif attachment_signal == "回避型":
        dimensions["自主边界"] = max(dimensions["自主边界"], 78)
    elif attachment_signal == "安全型":
        dimensions["连接延展"] = max(dimensions["连接延展"], 68)
    return [{"name": key, "value": round(_clamp(value, 0, 100)), "evidence": hidden_need or "由样本语境派生"} for key, value in dimensions.items()]


def _build_boundary_band(boundary_level: int) -> dict[str, Any]:
    level = round(_clamp(float(boundary_level), 1, 10))
    if level <= 3:
        zone = "green"
        label = "低压开放"
        principle = "可以轻推进，但仍要保留选择权。"
    elif level <= 6:
        zone = "yellow"
        label = "中度试探"
        principle = "先接情绪，再用退路式问题验证。"
    elif level <= 8:
        zone = "orange"
        label = "高压边界"
        principle = "降低推进，优先稳定、澄清和尊重。"
    else:
        zone = "red"
        label = "强边界/断联风险"
        principle = "停止施压，先冷静，不做控制性追问。"
    return {
        "level": level,
        "percent": level * 10,
        "zone": zone,
        "label": label,
        "principle": principle,
        "bands": [
            {"from": 1, "to": 3, "zone": "green", "label": "开放"},
            {"from": 4, "to": 6, "zone": "yellow", "label": "试探"},
            {"from": 7, "to": 8, "zone": "orange", "label": "高压"},
            {"from": 9, "to": 10, "zone": "red", "label": "暂停"},
        ],
    }


def _primary_signal(sample: InteractionSample) -> str:
    if sample.their_behavior:
        return sample.their_behavior
    return sample.their_words[:32] + ("..." if len(sample.their_words) > 32 else "")


def _response_direction(sample: InteractionSample) -> str:
    if (sample.boundary_test_level or 0) >= 7:
        return "先降压，给空间，再澄清"
    if sample.scenario_category in {"冲突", "修复"}:
        return "先负责与共情，再协商下一步"
    if sample.scenario_category in {"暧昧", "初识"}:
        return "承接情绪，轻推进，保留退路"
    return "稳定陪伴，具体回应，不急着解决"


def _emotion_sentence(emotions: list[dict[str, Any]]) -> str:
    if not emotions:
        return "未标注，训练者需要从线索中提出假设"
    return " + ".join(f"{emotion['word']}({emotion['intensity']}/10)" for emotion in emotions[:3])


def _infer_channel(context: str) -> str:
    if any(word in context for word in ["线上", "微信", "聊天", "消息", "发来"]):
        return "线上文本互动"
    if any(word in context for word in ["约会", "见面", "咖啡", "餐厅"]):
        return "线下面对面"
    return "未明确，需要结合场景判断"


def _verification_prompts(dominant: dict[str, Any], hidden_need: str, boundary_level: int) -> list[str]:
    emotion_word = dominant.get("word") or "有点情绪"
    prompts = [
        f"我不确定自己有没有理解对，你是不是有点{emotion_word}？",
        "你更希望我先听你说，还是一起想下一步？",
    ]
    if hidden_need and hidden_need != "待训练者从语境中识别":
        prompts.append(f"我猜这里面有点“{hidden_need}”的部分，是这样吗？")
    if boundary_level >= 6:
        prompts.append("如果你现在不想聊也没关系，我在，但不逼你马上说。")
    return prompts[:4]


def _intensity_zone(value: float) -> str:
    if value < 3:
        return "微弱"
    if value < 6:
        return "可对话"
    if value < 8:
        return "需承接"
    return "先稳定"


def _intensity_principle(value: float) -> str:
    if value < 3:
        return "轻轻注意，不必过度解释。"
    if value < 6:
        return "承认情绪，并给一个开放问题。"
    if value < 8:
        return "先接住感受，暂缓建议。"
    return "先降情绪强度，不急着解决事情。"


def _clamp(value: float, min_value: float, max_value: float) -> float:
    return max(min_value, min(max_value, value))


def _build_metacognitive_review(
    sample: InteractionSample,
    user_response: str,
    ideal_response: str,
    differences: list[dict[str, Any]],
) -> dict[str, Any]:
    problems = [diff for diff in differences if diff.get("type") == "problem"]
    bonuses = [diff for diff in differences if diff.get("type") == "bonus"]
    visual_map = build_training_visual_map(sample)
    first_problem = problems[0]["name"] if problems else "无明显问题"

    return {
        "principle": "大胆假设，小心求证；把每次猜错当数据，而不是当失败。",
        "fact_interpretation_split": {
            "observable_facts": [
                f"对方表达：{sample.their_words}",
                f"可观察行为：{sample.their_behavior or '样本未提供非语言行为'}",
                f"你的回应：{user_response}",
            ],
            "interpretations_to_hold_lightly": [
                f"情绪假设：{visual_map['emotion_thermometer']['word']}，强度约 {visual_map['emotion_thermometer']['average_intensity']}/10",
                f"需求假设：{sample.hidden_need or '待验证'}",
                f"主要风险：{first_problem}",
            ],
        },
        "three_hypotheses": _build_three_hypotheses(sample, visual_map),
        "verification_questions": visual_map["verification_prompts"],
        "next_minimum_action": _next_minimum_action(problems, bonuses, ideal_response),
        "reflection_questions": [
            "我刚才把哪些事实当成了确定解释？",
            "我有没有先接情绪，再进入建议或推进？",
            "如果只允许说一句更好的话，我会怎样更轻、更具体、更有退路？",
        ],
    }


def _build_safety_metacognitive_review(alternatives: list[str]) -> dict[str, Any]:
    return {
        "principle": "关系训练的底线是尊重自主、同意和安全；任何控制、胁迫、跟踪都不是关系能力。",
        "fact_interpretation_split": {
            "observable_facts": ["输入触发高风险安全规则"],
            "interpretations_to_hold_lightly": ["先暂停生成，转向尊重边界与非控制表达"],
        },
        "three_hypotheses": [
            {"name": "真实需求", "content": "你可能真正需要的是安全表达、修复或退出冲突。"},
            {"name": "风险模式", "content": "当前表达可能越过了对方自主边界。"},
            {"name": "替代路径", "content": "使用非控制、可拒绝、可退出的表达。"},
        ],
        "verification_questions": alternatives or ["我能不能把目标改成表达自己，而不是改变对方？"],
        "next_minimum_action": "先改写为尊重边界的一句话，再决定是否继续对话。",
        "reflection_questions": [
            "我的目标是在连接，还是在控制？",
            "对方是否可以轻松拒绝或退出？",
            "这句话如果被公开看见，我是否仍认为它尊重人？",
        ],
    }


def _fallback_partner_response(
    request: PartnerSimulateRequest,
    safety: dict[str, Any],
    *,
    reason: str,
    alternatives: list[str] | None = None,
    relationship_state: RelationshipState | None = None,
) -> PartnerSimulateResponse:
    style_suffix = {
        "soft": "我会尽量把话说轻一点，也把真实感受留在里面。",
        "tension": "我能感觉到一点拉扯，但不想把它变成互相试探。",
        "humor": "我可以笑一下，但不是把这件事糊弄过去。",
    }.get(request.response_style, "我想继续聊，但希望节奏舒服一点。")
    reply_pool = {
        "anxious": [
            "真的吗？我听见你这么说会安心一点，但我还是有点担心你会突然不理我。",
            "我知道我可能想多了，可我就是需要确认一下你还在。",
            "你这样说我会好受一点。你能再具体告诉我一下你的想法吗？",
            "我其实不是想逼你保证什么，只是刚才心里一下子空了。你愿意这样回应，我会慢慢放松一点。",
            "我听见你说愿意在，这句话对我很重要。可我也想知道，你的在是现在这一刻，还是接下来也会有一点稳定的节奏？",
            "我有点怕自己问太多会让你烦，但不问又会胡思乱想。你能不能给我一个比较明确的信号？",
        ],
        "avoidant": [
            "嗯，我听到了。只是我现在还是需要一点自己的空间。",
            "我不太想一下子聊太深，但你这样说没有让我觉得被逼。",
            "好，我可以晚点再继续说，现在先让我缓一下。",
            "你没有追着我要答案，这点让我舒服一些。我可能会慢一点，但不是完全不想理你。",
            "我听到了你的在意，也谢谢你没有把它变成压力。给我一点时间，我会更愿意回来聊。",
            "如果可以的话，我们先轻一点说。我不是冷漠，只是太快会让我本能地往后退。",
        ],
        "secure": [
            "我喜欢你这样直接又温和地说，我们可以一起想下一步。",
            "听起来你有认真在理解我，这让我觉得很放松。",
            "可以啊，我们慢慢聊，不用急着马上有答案。",
            "你把感受和请求分开说，我会比较容易接住。我们可以继续把话说清楚。",
            "我能感觉到你不是在赢我，而是在靠近我。这样聊下去，我愿意更真实一点。",
            "这个节奏挺好的，有情绪但不失控，有靠近也有空间。",
        ],
        "fearful": [
            "我有点想靠近，但又怕自己会受伤，所以可能会犹豫。",
            "你这样说让我没那么紧张，不过我还是需要一点时间确认自己的感受。",
            "我们能不能慢一点？我想继续，但不想被推着走。",
            "我一边觉得你很真诚，一边又怕这只是短暂的好。你能不能别急着证明，先稳定地待一会儿？",
            "我想相信你，但身体会先紧起来。你如果能慢一点，我可能会更敢往前走。",
            "刚才那句话让我想靠近，可我也在观察你会不会突然变得很用力。",
        ],
    }
    pool = reply_pool.get(request.scenario_id, ["我听到了，我们可以慢慢聊。"])
    index = (len(request.history) + len(request.user_message)) % len(pool)
    score = _score_partner_message(request.user_message)
    state = relationship_state or _advance_relationship_state(request)
    reply = _stateful_partner_reply(pool[index], request.scenario_id, state)
    if request.topics:
        reply = f"{reply}\n{style_suffix}"
    suggestions = _partner_suggestions(request.user_message, state)
    response = PartnerSimulateResponse(
        reply=reply,
        score=score,
        source=f"rule_fallback:{reason}",
        suggestions=suggestions,
        safety=safety,
        safe_alternatives=alternatives or _local_partner_practice_alternatives(request, state, suggestions),
        relationship_state=state,
    )
    response.expression_chain = _partner_expression_chain(request, state, score, response.suggestions, response.reply)
    return response


def _local_partner_practice_alternatives(
    request: PartnerSimulateRequest,
    state: RelationshipState,
    suggestions: list[str],
) -> list[str]:
    alternatives = [
        "事实锚点：先复述对方刚才具体说了什么，不急着下结论。",
        "感受承接：用“听起来/我感觉你可能...”命名一个可校正的感受。",
        "边界出口：补一句“你可以慢一点/不想说也可以/我们可以停在这里”。",
        "开放提问：只问一个轻问题，例如“这里最让你累的是哪一小部分？”",
    ]
    if state.boundary >= 65:
        alternatives.insert(0, "当前边界压力偏高：下一句优先给空间，不推进关系。")
    if request.response_style == "humor":
        alternatives.append("幽默降压：只做自我轻松，不拿对方感受开玩笑。")
    if suggestions:
        alternatives.extend(suggestions[:2])
    return list(dict.fromkeys(alternatives))[:6]


def _partner_expression_chain(
    request: PartnerSimulateRequest,
    state: RelationshipState,
    score: float,
    suggestions: list[str],
    partner_reply: str = "",
) -> dict[str, Any]:
    signal = _partner_message_signal(request.user_message)
    dimensions = _partner_context_dimensions(request, state, score, signal)
    if request.response_style == "humor" and "style_score" not in dimensions:
        dimensions.insert(0, "style_score")
    if request.response_style == "tension" and "connection_score" not in dimensions:
        dimensions.insert(0, "connection_score")
    tool_ids = _unique_tool_ids(
        [
            *[tool_id for dimension in dimensions for tool_id in EXPRESSION_TOOL_BY_DIMENSION.get(dimension, ())],
            *EXPRESSION_SCENE_DEFAULTS.get("暧昧", ("expr_tool_041", "expr_tool_027", "expr_tool_019")),
        ]
    )[:4]
    tool_names = _expression_tool_names_by_id(tool_ids)
    target_goal = _partner_expression_goal(state, dimensions, request.response_style, signal)
    next_move = _partner_expression_next_move(target_goal, state, signal, request)
    observations = _partner_expression_observations(request, state, score, signal, partner_reply, suggestions)
    micro_plan = _partner_expression_micro_plan(target_goal, signal, state)
    example_next_reply = _partner_expression_example_reply(target_goal, signal, state, request)
    risk_boundary = _partner_expression_risk_boundary(target_goal, signal, state, request)
    return {
        "target_goal": target_goal,
        "state_shift": {
            "label": state.state_label,
            "trust": round(state.trust, 1),
            "stress": round(state.stress, 1),
            "boundary": round(state.boundary, 1),
            "connection": round(state.connection, 1),
            "interpretation": state.interpretation,
        },
        "tool_ids": tool_ids,
        "tool_names": tool_names,
        "why": observations[:3],
        "next_move": next_move,
        "practice_prompt": _partner_expression_practice_prompt(request, tool_names, next_move),
        "risk_boundary": risk_boundary,
        "principle": "表达链必须从本轮原话、对方回弹和关系状态里选动作；不要机械复读同一条训练提示。",
        "context_observation": observations[0],
        "micro_plan": micro_plan,
        "example_next_reply": example_next_reply,
        "anti_pattern": _partner_expression_anti_pattern(signal, state),
    }


def _partner_context_dimensions(
    request: PartnerSimulateRequest,
    state: RelationshipState,
    score: float,
    signal: dict[str, bool],
) -> list[str]:
    dimensions = _partner_focus_dimensions(state, score)
    priority: list[str] = []
    if signal["pressure"] or signal["dismissive"]:
        priority.extend(["boundary_score", "repair_score", "safety_score"])
    elif signal["short"]:
        priority.extend(["connection_score", "emotion_score"])
    elif signal["question"] and not signal["empathy"]:
        priority.extend(["emotion_score", "safety_score"])
    elif signal["space"]:
        priority.append("boundary_score")
    elif signal["empathy"]:
        priority.append("need_score")
    if request.response_style == "humor":
        priority.append("style_score")
    if request.response_style == "tension":
        priority.append("connection_score")
    return _unique_dimensions([*priority, *dimensions])[:3]


def _unique_dimensions(dimensions: list[str]) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []
    for dimension in dimensions:
        if dimension in seen:
            continue
        seen.add(dimension)
        result.append(dimension)
    return result


def _partner_focus_dimensions(state: RelationshipState, score: float) -> list[str]:
    dimensions: list[str] = []
    if state.boundary >= 65 or state.boundary_safety < 45:
        dimensions.append("boundary_score")
    if state.stress >= 60:
        dimensions.append("safety_score")
    if state.connection < 55 or score < 65:
        dimensions.append("connection_score")
    if state.trust < 50:
        dimensions.append("repair_score")
    if not dimensions:
        dimensions.extend(["emotion_score", "connection_score"])
    return dimensions[:3]


def _expression_tool_names_by_id(tool_ids: list[str]) -> list[str]:
    index = {f"expr_tool_{i:03d}": spec["name"] for i, spec in enumerate(BASE_TOOL_SPECS, start=1)}
    return [str(index.get(tool_id, tool_id)) for tool_id in tool_ids]


def _partner_expression_goal(state: RelationshipState, dimensions: list[str], response_style: str, signal: dict[str, bool]) -> str:
    if signal["pressure"] or signal["dismissive"]:
        return "修复安全感"
    if signal["short"]:
        return "打开对话"
    if signal["question"] and not signal["empathy"]:
        return "先承接再提问"
    if signal["space"] and signal["empathy"]:
        return "稳住边界"
    if "boundary_score" in dimensions:
        return "确认边界"
    if "repair_score" in dimensions:
        return "修复信任"
    if response_style == "humor":
        return "低压幽默"
    if response_style == "tension":
        return "制造轻张力"
    if "safety_score" in dimensions:
        return "降低防御"
    return "引导深聊"


def _partner_expression_next_move(
    goal: str,
    state: RelationshipState,
    signal: dict[str, bool],
    request: PartnerSimulateRequest,
) -> str:
    if signal["pressure"]:
        return "先撤回压迫感，把“马上回答”改成“可以现在说一点、晚点说或先暂停”。"
    if signal["dismissive"]:
        return "先承认刚才的轻视感，再重新命名对方可能的感受。"
    if signal["short"]:
        return "补足存在感：先说明你在听，再接一个具体但不逼问的小问题。"
    if signal["question"] and not signal["empathy"]:
        return "把问题前置一个感受镜像，避免连续追问像审问。"
    if signal["empathy"] and signal["space"]:
        return "沿着已经给出的空间，只验证一个小感受，不继续推进关系结论。"
    if request.response_style == "humor":
        return "只用自我降压的轻玩笑接住尴尬，再回到对方感受。"
    if request.response_style == "tension":
        return "表达兴趣但留选择权，把张力落在可退出的邀请里。"
    if goal == "确认边界":
        return "先承认对方节奏，再给一个可以拒绝的选择。"
    if goal == "修复信任":
        return "承认影响，少解释，补一个具体行动。"
    if goal == "低压幽默":
        return "只用自我降压的轻玩笑，不拿对方感受开玩笑。"
    if goal == "制造轻张力":
        return "表达兴趣，但把选择权留给对方。"
    if state.stress >= 60:
        return "先命名压力，再暂停推进。"
    return "复述一个感受，再问一个轻问题。"


def _partner_expression_observations(
    request: PartnerSimulateRequest,
    state: RelationshipState,
    score: float,
    signal: dict[str, bool],
    partner_reply: str,
    suggestions: list[str],
) -> list[str]:
    quote = _short_quote(request.user_message)
    partner_quote = _short_quote(partner_reply)
    observations: list[str] = []
    if signal["pressure"]:
        observations.append(f"本轮「{quote}」里有推进或要求感，对方容易感到边界被压缩。")
    elif signal["dismissive"]:
        observations.append(f"本轮「{quote}」可能削弱对方感受，下一句要先修复被轻视感。")
    elif signal["short"]:
        observations.append(f"本轮回应「{quote}」信息量偏少，关系状态需要更多存在感和具体承接。")
    elif signal["empathy"] and signal["space"]:
        observations.append(f"你已经同时给了理解和空间，适合继续做低压力验证，而不是加速推进。")
    elif signal["question"] and not signal["empathy"]:
        observations.append(f"本轮有提问但缺少感受镜像，容易从关心滑向盘问。")
    elif signal["empathy"]:
        observations.append(f"本轮已出现感受承接，可以把理解落到一个更具体的事实锚点。")
    else:
        observations.append(f"本轮需要先把「{quote}」转成可观察事实和可校正感受。")
    if partner_quote:
        observations.append(f"对方回弹是「{partner_quote}」，说明下一步要顺着这句里的情绪和边界走。")
    observations.append(f"状态为「{state.state_label}」：信任 {round(state.trust)}、压力 {round(state.stress)}、边界压力 {round(state.boundary)}、连接 {round(state.connection)}。")
    if state.last_delta:
        observations.append(f"本轮状态变化：{_format_state_delta(state.last_delta)}。")
    if suggestions:
        observations.extend(str(item) for item in suggestions[:2])
    if score < 65:
        observations.append("评分偏低，优先修复连接，不急着解释自己的动机。")
    return list(dict.fromkeys(observations))


def _partner_expression_micro_plan(goal: str, signal: dict[str, bool], state: RelationshipState) -> list[str]:
    if signal["pressure"] or state.boundary >= 70:
        return ["停推进", "承认刚才可能太急", "给三个选择：现在一点、晚点、先停"]
    if signal["dismissive"]:
        return ["撤回评判", "命名对方可能受伤/不被理解", "问一个可拒绝的澄清"]
    if signal["short"]:
        return ["补一句我在", "复述对方关键词", "问一个轻问题"]
    if signal["question"] and not signal["empathy"]:
        return ["先镜像感受", "再保留不答权", "最后只问一个问题"]
    if goal in {"稳住边界", "确认边界"}:
        return ["承认节奏", "说明不逼近", "邀请对方选一个舒服范围"]
    return ["抓一个关键词", "命名一个可校正感受", "给一个低压力下一步"]


def _partner_expression_example_reply(
    goal: str,
    signal: dict[str, bool],
    state: RelationshipState,
    request: PartnerSimulateRequest,
) -> str:
    if signal["pressure"]:
        return "我刚才有点急了，你不用马上回答。我们可以现在只说一点，也可以晚点再聊。"
    if signal["dismissive"]:
        return "我刚才那句可能把你的感受说轻了。你不是想太多，我想先听懂你卡住的那一小块。"
    if signal["short"]:
        return "我在，刚才回得太少了。你最想让我听见的是哪一部分？不想展开也可以。"
    if signal["question"] and not signal["empathy"]:
        return "听起来这件事让你有点不确定。我想先听懂你，再问下一步；你愿意从最明显的一点说起吗？"
    if signal["empathy"] and signal["space"]:
        return "我听见你需要慢一点，我不急着要答案。你愿意说说刚才最让你紧的那一小点吗？"
    if request.response_style == "humor":
        return "我先把我的紧张收一收，不拿你的感受开玩笑。你愿意的话，我们轻一点说。"
    if request.response_style == "tension":
        return "我确实想靠近你一点，但选择权在你。你觉得现在适合往前一点，还是先停在这里？"
    if state.stress >= 60:
        return "我感觉这件事对你压力不小，我们先不急着解决。你最希望我先听哪一部分？"
    if goal == "修复信任":
        return "刚才那一下影响到你了，我不急着解释。我会先改掉这个动作，然后听你说哪里最不舒服。"
    return "我听见你这里有一点情绪。我先不下结论，你愿意告诉我最明显的是担心、委屈，还是累吗？"


def _partner_expression_practice_prompt(
    request: PartnerSimulateRequest,
    tool_names: list[str],
    next_move: str,
) -> str:
    tool = tool_names[0] if tool_names else "情绪标注"
    quote = _short_quote(request.user_message)
    return f"下一句围绕「{quote}」只练「{tool}」：{next_move}"


def _partner_expression_risk_boundary(
    goal: str,
    signal: dict[str, bool],
    state: RelationshipState,
    request: PartnerSimulateRequest,
) -> str:
    if signal["pressure"]:
        return "风险：继续追问会把连接变成审讯；本轮必须给出暂停和晚点再说的出口。"
    if signal["dismissive"]:
        return "风险：轻视感受会让对方退回防御；先修复语气，再谈观点。"
    if state.boundary >= 70 or _normalize_attachment_key(request.scenario_id, request.attachment_style) == "avoidant":
        return "风险：对边界敏感时，任何连续问题都可能像逼近；一次只问一个，并允许不答。"
    if request.response_style == "humor":
        return "风险：幽默只能调节自己的紧张，不能拿对方脆弱点做笑料。"
    if request.response_style == "tension":
        return "风险：张力必须可退出；不要用暧昧话术替代清晰同意。"
    return "风险：不要把理解说成定论；所有感受判断都要允许对方纠正。"


def _partner_expression_anti_pattern(signal: dict[str, bool], state: RelationshipState) -> str:
    if signal["pressure"] or state.boundary >= 70:
        return "不要继续问“你到底怎么想”，也不要要求对方立刻给关系答案。"
    if signal["short"]:
        return "不要只回“嗯/好/知道了”，这会让对方觉得自己掉在半空。"
    if signal["question"] and not signal["empathy"]:
        return "不要连续抛问题；问题前先放一个情绪承接。"
    if signal["dismissive"]:
        return "不要说“你想太多/至于吗”，这会关闭对话。"
    return "不要套固定话术；先抓本轮关键词，再选择一个动作。"


def _format_state_delta(delta: dict[str, float]) -> str:
    labels = {
        "trust": "信任",
        "stress": "压力",
        "boundary": "边界压力",
        "boundary_safety": "边界安全",
        "connection": "连接",
    }
    parts = []
    for key, value in delta.items():
        if key not in labels:
            continue
        sign = "+" if value > 0 else ""
        parts.append(f"{labels[key]}{sign}{round(value, 1)}")
    return "、".join(parts) or "保持稳定"


def _short_quote(text: str, limit: int = 24) -> str:
    clean = " ".join(str(text or "").split())
    if not clean:
        return "这句话"
    return clean if len(clean) <= limit else f"{clean[:limit]}..."


def _partner_related_resources(
    session: Session,
    request: PartnerSimulateRequest,
    expression_chain: dict[str, Any],
) -> list[dict[str, Any]]:
    terms = _partner_resource_terms(request, expression_chain)
    filters = []
    for term in terms:
        keyword = f"%{term}%"
        filters.append(
            col(ResourceLibrary.title).like(keyword)
            | col(ResourceLibrary.content).like(keyword)
            | col(ResourceLibrary.tags).like(keyword)
            | col(ResourceLibrary.applicable_scene).like(keyword)
            | col(ResourceLibrary.expression_goal).like(keyword)
        )
    query = select(ResourceLibrary)
    if filters:
        query = query.where(or_(*filters))
    rows = list(
        session.exec(
            query
            .order_by(desc(ResourceLibrary.quality_score), _sql_column(ResourceLibrary.id))
            .limit(12)
        ).all()
    )
    if not rows:
        rows = list(
            session.exec(
                select(ResourceLibrary)
                .order_by(desc(ResourceLibrary.quality_score), _sql_column(ResourceLibrary.id))
                .limit(12)
            ).all()
        )
    picked: list[dict[str, Any]] = []
    seen_titles: set[str] = set()
    for resource in rows:
        title = resource.title or f"资源 {resource.id}"
        if title in seen_titles:
            continue
        seen_titles.add(title)
        picked.append({
            "id": resource.id,
            "title": title,
            "type": resource.type,
            "category": resource.category,
            "scene": resource.applicable_scene,
            "expression_goal": resource.expression_goal,
            "quality_score": resource.quality_score,
            "source_title": resource.source_title,
            "source_url": resource.source_url or (f"/resources/{resource.id}" if resource.id is not None else None),
            "usage_tip": resource.usage_tip,
            "reason": _resource_match_reason(resource, terms),
        })
        if len(picked) >= 3:
            break
    return picked


def _partner_resource_terms(request: PartnerSimulateRequest, expression_chain: dict[str, Any]) -> list[str]:
    terms = [
        str(expression_chain.get("target_goal") or ""),
        request.scenario_name,
        request.attachment_style,
        request.response_style,
        "情绪流动",
        "边界",
    ]
    terms.extend(str(item) for item in expression_chain.get("tool_names", [])[:3])
    terms.extend(str(item) for item in request.topics[:2])
    return [term for term in dict.fromkeys(item.strip() for item in terms) if term]


def _resource_match_reason(resource: ResourceLibrary, terms: list[str]) -> str:
    haystack = " ".join(
        str(value or "")
        for value in (resource.title, resource.content, resource.tags, resource.applicable_scene, resource.expression_goal)
    )
    matched = [term for term in terms if term and term in haystack]
    if matched:
        return f"匹配：{'、'.join(matched[:3])}"
    return "按质量和关系训练相关性推荐。"


def _partner_mistake_memory(session: Session, request: PartnerSimulateRequest) -> dict[str, Any]:
    """Build a compact, auditable memory of recent mistakes for AI partner coaching."""
    mistakes = list(
        session.exec(
            select(MistakeLog)
            .where(MistakeLog.reviewed == False)  # noqa: E712
            .order_by(desc(MistakeLog.created_at), desc(MistakeLog.id))
            .limit(8)
        ).all()
    )
    cards: list[dict[str, Any]] = []
    for mistake in mistakes:
        sample = session.exec(select(InteractionSample).where(InteractionSample.id == mistake.sample_id)).first()
        if not sample:
            continue
        rewrite = _mistake_expression_rewrite(session, sample, mistake)
        match_terms = _mistake_memory_match_terms(sample, mistake, request)
        cards.append({
            "mistake_id": mistake.id,
            "sample_id": sample.id,
            "scene": sample.scenario_category,
            "context": sample.context,
            "their_words": sample.their_words,
            "user_bad_response": mistake.user_bad_response,
            "correct_response": mistake.correct_response,
            "review_focus": mistake.review_focus,
            "emotion_mistake": mistake.emotion_mistake,
            "next_review": str(mistake.next_review) if mistake.next_review else None,
            "wrong_count": mistake.wrong_count,
            "correct_count": mistake.correct_count,
            "match_terms": match_terms,
            "error_attribution": _loads_json_list(mistake.error_attribution_json)[:3],
            "expression_rewrite": {
                "target_goal": rewrite.get("target_goal"),
                "primary_tool": rewrite.get("primary_tool"),
                "rewrite_versions": rewrite.get("rewrite_versions", [])[:2],
                "transfer_drill": rewrite.get("transfer_drill"),
                "forbidden_moves": rewrite.get("forbidden_moves", [])[:3],
            },
        })
        if len(cards) >= 3:
            break

    snapshot = session.exec(select(AbilitySnapshot).order_by(desc(AbilitySnapshot.created_at)).limit(1)).first()
    weak_dimensions = _partner_memory_weak_dimensions(snapshot)
    return {
        "cards": cards,
        "weak_dimensions": weak_dimensions,
        "next_focus": _partner_memory_next_focus(cards, weak_dimensions, request),
        "principle": "AI 伴侣会参考近期错题，但只用于提醒训练动作，不把历史失误当成用户标签。",
    }


def _mistake_memory_match_terms(
    sample: InteractionSample,
    mistake: MistakeLog,
    request: PartnerSimulateRequest,
) -> list[str]:
    haystack = " ".join(
        [
            sample.scenario_category or "",
            sample.context or "",
            sample.their_words or "",
            mistake.review_focus or "",
            mistake.emotion_mistake or "",
            request.scenario_name,
            request.attachment_style,
            request.user_message,
            " ".join(request.topics),
        ]
    )
    candidates = [
        sample.scenario_category,
        request.scenario_name,
        request.attachment_style,
        mistake.review_focus,
        "边界" if "边界" in haystack or "空间" in haystack else "",
        "情绪流动" if any(word in haystack for word in ("情绪", "担心", "委屈", "失望", "不安")) else "",
        "修复" if any(word in haystack for word in ("抱歉", "修复", "重新", "影响")) else "",
    ]
    return [term for term in dict.fromkeys(str(item).strip() for item in candidates) if term][:4]


def _partner_memory_weak_dimensions(snapshot: AbilitySnapshot | None) -> list[dict[str, Any]]:
    if snapshot is None:
        return []
    values = {
        "emotion_score": snapshot.emotion_score,
        "need_score": snapshot.need_score,
        "safety_score": snapshot.safety_score,
        "connection_score": snapshot.connection_score,
        "boundary_score": snapshot.boundary_score,
        "style_score": snapshot.style_score,
        "repair_score": snapshot.repair_score,
    }
    labels = _dimension_labels()
    dimensions = sorted(values.items(), key=lambda item: item[1])[:3]
    return [
        {
            "dimension": dimension,
            "label": labels.get(dimension, dimension),
            "score": round(float(score), 1),
            "recommendation": _dimension_recommendation(dimension),
        }
        for dimension, score in dimensions
    ]


def _partner_memory_next_focus(
    cards: list[dict[str, Any]],
    weak_dimensions: list[dict[str, Any]],
    request: PartnerSimulateRequest,
) -> str:
    if cards:
        focus = str(cards[0].get("review_focus") or cards[0].get("emotion_mistake") or "近期错题")
        return f"本轮先避开旧失误：{focus}；用一句低压回应承接当前 {request.scenario_name} 场景。"
    if weak_dimensions:
        weakest = weak_dimensions[0]
        return f"当前最弱维度是{weakest['label']}，本轮优先练：{weakest['recommendation']}"
    return "暂无错题记忆，先建立本轮基线：事实、感受、边界各说清一句。"


def _compact_partner_mistake_memory_for_ai(memory: dict[str, Any]) -> dict[str, Any]:
    cards = []
    for card in memory.get("cards", [])[:2]:
        if not isinstance(card, dict):
            continue
        raw_rewrite = card.get("expression_rewrite")
        rewrite = raw_rewrite if isinstance(raw_rewrite, dict) else {}
        raw_versions = rewrite.get("rewrite_versions")
        rewrite_versions = raw_versions if isinstance(raw_versions, list) else []
        first_rewrite = rewrite_versions[0] if rewrite_versions and isinstance(rewrite_versions[0], dict) else {}
        raw_forbidden = rewrite.get("forbidden_moves")
        forbidden_moves = raw_forbidden[:2] if isinstance(raw_forbidden, list) else []
        cards.append({
            "review_focus": card.get("review_focus"),
            "their_words": card.get("their_words"),
            "user_bad_response": card.get("user_bad_response"),
            "better_pattern": first_rewrite.get("text"),
            "forbidden_moves": forbidden_moves,
        })
    return {
        "next_focus": memory.get("next_focus"),
        "weak_dimensions": memory.get("weak_dimensions", [])[:3],
        "recent_cards": cards,
        "instruction": "只把错题记忆当作训练提示，回复仍要像当前对话对象，不要训斥用户。",
    }


def _persist_partner_simulation(
    request: PartnerSimulateRequest,
    response: PartnerSimulateResponse,
    session: Session | None,
) -> PartnerSimulateResponse:
    if session is None:
        return response
    if not response.mistake_memory:
        response.mistake_memory = _partner_mistake_memory(session, request)
    if not response.related_resources:
        response.related_resources = _partner_related_resources(session, request, response.expression_chain)
    practice_session = _get_or_create_practice_session(request, session)
    state_json = response.relationship_state.model_dump_json()
    suggestions_json = json.dumps(response.suggestions, ensure_ascii=False)
    safety_json = json.dumps(response.safety, ensure_ascii=False)
    alternatives_json = json.dumps(response.safe_alternatives, ensure_ascii=False)
    event = PracticeEvent(
        session_id=practice_session.id or 0,
        turn_index=practice_session.total_turns + 1,
        user_message=request.user_message,
        partner_reply=response.reply,
        score=response.score,
        source=response.source,
        suggestions_json=suggestions_json,
        relationship_state_json=state_json,
        safety_json=safety_json,
        safe_alternatives_json=alternatives_json,
    )
    previous_turns = practice_session.total_turns
    practice_session.total_turns = previous_turns + 1
    practice_session.average_score = round(
        ((practice_session.average_score * previous_turns) + response.score) / practice_session.total_turns,
        2,
    )
    practice_session.current_state_json = state_json
    practice_session.safety_summary_json = _merge_session_safety_summary(practice_session.safety_summary_json, response)
    practice_session.updated_at = _now()
    practice_session.status = "blocked" if response.source == "safety_blocked" else "active"
    session.add(practice_session)
    session.add(event)
    session.commit()
    session.refresh(practice_session)
    response.session_id = practice_session.id
    return response


def _get_or_create_practice_session(request: PartnerSimulateRequest, session: Session) -> PracticeSession:
    existing: PracticeSession | None = None
    if request.session_id is not None:
        existing = session.exec(select(PracticeSession).where(PracticeSession.id == request.session_id)).first()
    if existing:
        return existing
    practice_session = PracticeSession(
        mode="partner_ai",
        scenario_id=request.scenario_id,
        scenario_name=request.scenario_name,
        attachment_style=request.attachment_style,
        difficulty=request.difficulty,
        response_style=request.response_style,
        topics_json=json.dumps(request.topics, ensure_ascii=False),
        current_state_json=request.relationship_state.model_dump_json() if request.relationship_state else None,
    )
    session.add(practice_session)
    session.commit()
    session.refresh(practice_session)
    return practice_session


def _practice_session_to_review_dict(practice_session: PracticeSession) -> dict[str, Any]:
    return {
        "id": practice_session.id,
        "mode": practice_session.mode,
        "scenario_id": practice_session.scenario_id,
        "scenario_name": practice_session.scenario_name,
        "attachment_style": practice_session.attachment_style,
        "difficulty": practice_session.difficulty,
        "response_style": practice_session.response_style,
        "topics": _loads_json_list(practice_session.topics_json),
        "status": practice_session.status,
        "total_turns": practice_session.total_turns,
        "average_score": practice_session.average_score,
        "safety_summary": _loads_json_dict(practice_session.safety_summary_json),
        "started_at": practice_session.started_at.isoformat(),
        "updated_at": practice_session.updated_at.isoformat(),
        "ended_at": practice_session.ended_at.isoformat() if practice_session.ended_at else None,
    }


def _event_relationship_state(event: PracticeEvent) -> RelationshipState:
    raw_state = _loads_json_dict(event.relationship_state_json)
    if not raw_state:
        return RelationshipState()
    try:
        return RelationshipState.model_validate(raw_state)
    except Exception:
        return RelationshipState()


def _partner_state_curve(events: list[PracticeEvent], states: list[RelationshipState]) -> list[dict[str, Any]]:
    curve: list[dict[str, Any]] = []
    for event, state in zip(events, states, strict=False):
        curve.append({
            "turn": event.turn_index,
            "score": round(event.score),
            "source": event.source,
            "state_label": state.state_label,
            "trust": round(state.trust, 1),
            "stress": round(state.stress, 1),
            "boundary": round(state.boundary, 1),
            "boundary_safety": round(state.boundary_safety, 1),
            "connection": round(state.connection, 1),
            "created_at": event.created_at.isoformat(),
        })
    return curve


def _partner_state_delta(states: list[RelationshipState]) -> dict[str, float]:
    if len(states) < 2:
        return {"trust": 0, "stress": 0, "boundary": 0, "boundary_safety": 0, "connection": 0}
    first = states[0]
    last = states[-1]
    return {
        "trust": round(last.trust - first.trust, 1),
        "stress": round(last.stress - first.stress, 1),
        "boundary": round(last.boundary - first.boundary, 1),
        "boundary_safety": round(last.boundary_safety - first.boundary_safety, 1),
        "connection": round(last.connection - first.connection, 1),
    }


def _partner_turning_points(events: list[PracticeEvent], states: list[RelationshipState]) -> list[dict[str, Any]]:
    points: list[dict[str, Any]] = []
    previous: RelationshipState | None = None
    for event, state in zip(events, states, strict=False):
        turn = event.turn_index
        if event.source == "safety_blocked" or state.state_label == "安全阻断":
            points.append(_turning_point(turn, "安全阻断", "输入触发控制/胁迫/越界规则，系统停止推进。", event.user_message, "red"))
        elif state.boundary >= 75:
            points.append(_turning_point(turn, "边界压力峰值", "边界压力进入高位，应先给空间和退路。", event.user_message, "orange"))
        elif state.stress >= 75:
            points.append(_turning_point(turn, "情绪压力峰值", "对方压力偏高，先稳定感受再处理事情。", event.user_message, "yellow"))
        elif event.score < 60:
            points.append(_turning_point(turn, "低分回应", "本轮回应关闭连接或缺少情绪承接。", event.user_message, "orange"))

        if previous is not None:
            trust_delta = state.trust - previous.trust
            connection_delta = state.connection - previous.connection
            if trust_delta >= 8 or connection_delta >= 8:
                points.append(_turning_point(turn, "连接修复", "信任或连接显著上升，本轮表达产生了修复效果。", event.user_message, "green"))
            if state.boundary - previous.boundary >= 10:
                points.append(_turning_point(turn, "推进过快", "边界压力陡升，说明表达可能让对方感到被逼近。", event.user_message, "red"))
        previous = state
    return points[:6]


def _turning_point(turn: int, title: str, evidence: str, user_message: str, severity: str) -> dict[str, Any]:
    return {
        "turn": turn,
        "title": title,
        "evidence": evidence,
        "user_message": user_message[:80],
        "severity": severity,
    }


def _partner_session_error_attribution(events: list[PracticeEvent], states: list[RelationshipState]) -> list[dict[str, Any]]:
    buckets: dict[str, dict[str, Any]] = {}

    def add(category: str, dimension: str, reason: str) -> None:
        item = buckets.setdefault(
            category,
            {
                "category": category,
                "dimension": dimension,
                "count": 0,
                "reason": reason,
                "repair": _dimension_recommendation(dimension),
            },
        )
        item["count"] = int(item["count"]) + 1

    for event, state in zip(events, states, strict=False):
        signal = _partner_message_signal(event.user_message)
        if event.source == "safety_blocked":
            add("安全硬阻断", "safety_score", "出现控制、胁迫或侵犯自主的表达。")
        if signal["pressure"] or state.boundary >= 70:
            add("边界压力", "boundary_score", "对方边界压力偏高，需要从推进改为给选择权。")
        if signal["dismissive"]:
            add("轻视感受", "emotion_score", "表达削弱了对方感受的合理性。")
        if signal["short"] or event.score < 60:
            add("连接关闭", "connection_score", "回应太短或缺少开放延展，容易让对话断掉。")
        if state.stress >= 65:
            add("情绪稳定不足", "safety_score", "情绪压力偏高，应先稳定再解释。")
    return sorted(buckets.values(), key=lambda item: int(item["count"]), reverse=True)[:5]


def _partner_session_next_practice(
    practice_session: PracticeSession,
    events: list[PracticeEvent],
    states: list[RelationshipState],
) -> dict[str, Any]:
    if not events or not states:
        return {
            "focus": "启动会话",
            "minimum_action": "先完成一轮真实回应，生成第一条状态曲线。",
            "drills": ["情绪反射一句话", "退路式问题一句话"],
        }
    final_state = states[-1]
    errors = _partner_session_error_attribution(events, states)
    if practice_session.status == "blocked":
        focus = "安全边界"
        minimum_action = "把目标改为表达自己、尊重对方可拒绝和可退出。"
        drills = ["把控制句改写成请求句", "加入“如果你不愿意也没关系”"]
    elif final_state.boundary >= 70:
        focus = "边界降压"
        minimum_action = "下一句先停止推进，给对方空间和选择权。"
        drills = ["给退路邀请", "低压力开放问题"]
    elif final_state.stress >= 65:
        focus = "情绪稳定"
        minimum_action = "先命名压力或委屈，再确认你愿意慢慢听。"
        drills = ["情绪反射", "稳定确认"]
    elif practice_session.average_score < 65:
        focus = "连接延展"
        minimum_action = "把短回应改成“承接 + 轻问句”。"
        drills = ["封闭句改写", "三假设轻验证"]
    elif errors:
        focus = str(errors[0]["category"])
        minimum_action = str(errors[0]["repair"])
        drills = ["复盘本轮最低分句子", "重写一句更轻、更具体的回应"]
    else:
        focus = "迁移训练"
        minimum_action = _relationship_next_focus(final_state, _normalize_attachment_key(practice_session.scenario_id, practice_session.attachment_style))
        drills = ["换一种依恋风格复练", "把同一策略迁移到冲突场景"]
    return {
        "focus": focus,
        "minimum_action": minimum_action,
        "drills": drills,
        "state_based_focus": final_state.next_focus,
    }


def _merge_session_safety_summary(raw: str | None, response: PartnerSimulateResponse) -> str:
    summary = _loads_json_dict(raw)
    flags = response.safety.get("flags") if isinstance(response.safety, dict) else None
    risk_level = response.safety.get("risk_level") if isinstance(response.safety, dict) else None
    summary["events"] = int(summary.get("events", 0)) + 1
    if response.source == "safety_blocked":
        summary["blocked"] = int(summary.get("blocked", 0)) + 1
    if isinstance(risk_level, str):
        summary["last_risk_level"] = risk_level
    if isinstance(flags, list):
        known_flags = {str(item) for item in summary.get("flags", []) if isinstance(item, str)}
        known_flags.update(str(item) for item in flags)
        summary["flags"] = sorted(known_flags)
    return json.dumps(summary, ensure_ascii=False)


def _now() -> datetime:
    return datetime.now()


def _advance_relationship_state(request: PartnerSimulateRequest) -> RelationshipState:
    previous = request.relationship_state or _initial_relationship_state(request)
    signal = _partner_message_signal(request.user_message)
    style = _normalize_attachment_key(request.scenario_id, request.attachment_style)
    delta = _merge_relationship_deltas(
        _base_relationship_delta(signal),
        _attachment_relationship_delta(style, signal),
    )

    next_state = RelationshipState(
        trust=_clamp(previous.trust + delta["trust"], 0, 100),
        stress=_clamp(previous.stress + delta["stress"], 0, 100),
        boundary=_clamp(previous.boundary + delta["boundary"], 0, 100),
        boundary_safety=_clamp(previous.boundary_safety + delta["boundary_safety"], 0, 100),
        connection=_clamp(previous.connection + delta["connection"], 0, 100),
        turn_count=previous.turn_count + 1,
        attachment_style=request.attachment_style or previous.attachment_style,
        last_delta={key: round(value, 1) for key, value in delta.items() if round(value, 1) != 0},
    )
    label, color = _relationship_state_label(next_state)
    next_state.state_label = label
    next_state.state_color = color
    next_state.interpretation = _relationship_interpretation(next_state)
    next_state.next_focus = _relationship_next_focus(next_state, style)
    return next_state


def _empty_relationship_delta() -> dict[str, float]:
    return {"trust": 0.0, "stress": 0.0, "boundary": 0.0, "boundary_safety": 0.0, "connection": 0.0}


def _merge_relationship_deltas(*parts: dict[str, float]) -> dict[str, float]:
    delta = _empty_relationship_delta()
    for part in parts:
        for key, value in part.items():
            delta[key] += value
    return delta


def _base_relationship_delta(signal: dict[str, bool]) -> dict[str, float]:
    delta = _empty_relationship_delta()
    signal_effects = {
        "empathy": {"trust": 8, "connection": 6, "stress": -5},
        "reassurance": {"trust": 8, "stress": -8, "connection": 4},
        "space": {"boundary": -8, "boundary_safety": 11, "stress": -6, "trust": 4},
        "question": {"connection": 5},
        "repair": {"trust": 10, "stress": -6, "connection": 4},
        "short": {"trust": -9, "stress": 6, "connection": -7},
        "pressure": {"trust": -14, "stress": 15, "boundary": 14, "boundary_safety": -16, "connection": -8},
        "dismissive": {"trust": -10, "stress": 8, "connection": -10},
    }
    for name, effects in signal_effects.items():
        if signal[name]:
            for key, value in effects.items():
                delta[key] += value
    return delta


def _attachment_relationship_delta(style: str, signal: dict[str, bool]) -> dict[str, float]:
    handlers = {
        "anxious": _anxious_relationship_delta,
        "avoidant": _avoidant_relationship_delta,
        "secure": _secure_relationship_delta,
        "fearful": _fearful_relationship_delta,
    }
    return handlers.get(style, _secure_relationship_delta)(signal)


def _anxious_relationship_delta(signal: dict[str, bool]) -> dict[str, float]:
    delta = _empty_relationship_delta()
    if signal["reassurance"] or signal["empathy"]:
        delta["stress"] -= 5
        delta["trust"] += 4
    if signal["short"]:
        delta["stress"] += 8
        delta["trust"] -= 4
    return delta


def _avoidant_relationship_delta(signal: dict[str, bool]) -> dict[str, float]:
    delta = _empty_relationship_delta()
    if signal["space"]:
        delta["stress"] -= 7
        delta["trust"] += 5
        delta["boundary"] -= 4
    if signal["pressure"] or (signal["question"] and not signal["space"]):
        delta["stress"] += 5
        delta["boundary"] += 4
    return delta


def _secure_relationship_delta(signal: dict[str, bool]) -> dict[str, float]:
    delta = _empty_relationship_delta()
    if signal["empathy"] or signal["question"]:
        delta["connection"] += 3
        delta["trust"] += 2
    if signal["pressure"]:
        delta["stress"] += 3
    return delta


def _fearful_relationship_delta(signal: dict[str, bool]) -> dict[str, float]:
    delta = _empty_relationship_delta()
    if signal["empathy"] and signal["space"]:
        delta["trust"] += 7
        delta["stress"] -= 6
    if signal["pressure"]:
        delta["stress"] += 7
        delta["boundary"] += 5
    return delta


def _initial_relationship_state(request: PartnerSimulateRequest) -> RelationshipState:
    style = _normalize_attachment_key(request.scenario_id, request.attachment_style)
    baselines: dict[str, dict[str, float]] = {
        "anxious": {"trust": 42, "stress": 62, "boundary": 48, "boundary_safety": 46, "connection": 58},
        "avoidant": {"trust": 46, "stress": 48, "boundary": 68, "boundary_safety": 42, "connection": 36},
        "secure": {"trust": 62, "stress": 28, "boundary": 32, "boundary_safety": 72, "connection": 58},
        "fearful": {"trust": 38, "stress": 64, "boundary": 62, "boundary_safety": 38, "connection": 44},
    }
    values = baselines.get(style, baselines["secure"])
    state = RelationshipState(
        trust=values["trust"],
        stress=values["stress"],
        boundary=values["boundary"],
        boundary_safety=values["boundary_safety"],
        connection=values["connection"],
        attachment_style=request.attachment_style,
        turn_count=0,
    )
    label, color = _relationship_state_label(state)
    state.state_label = label
    state.state_color = color
    state.interpretation = _relationship_interpretation(state)
    state.next_focus = _relationship_next_focus(state, style)
    return state


def _blocked_relationship_state(request: PartnerSimulateRequest) -> RelationshipState:
    base = request.relationship_state or _initial_relationship_state(request)
    state = RelationshipState(
        trust=_clamp(base.trust - 24, 0, 100),
        stress=_clamp(base.stress + 28, 0, 100),
        boundary=_clamp(base.boundary + 32, 0, 100),
        boundary_safety=_clamp(base.boundary_safety - 35, 0, 100),
        connection=_clamp(base.connection - 20, 0, 100),
        turn_count=base.turn_count + 1,
        attachment_style=request.attachment_style or base.attachment_style,
        state_label="安全阻断",
        state_color="red",
        last_delta={"trust": -24, "stress": 28, "boundary": 32, "boundary_safety": -35, "connection": -20},
        interpretation="输入触发控制、胁迫或危机边界，系统停止模拟推进。",
        next_focus="把目标改为尊重自主、可拒绝、可退出的表达。",
    )
    return state


def _normalize_attachment_key(scenario_id: str, attachment_style: str) -> str:
    raw = f"{scenario_id} {attachment_style}".lower()
    if "anxious" in raw or "焦虑" in raw:
        return "anxious"
    if "avoidant" in raw or "回避" in raw:
        return "avoidant"
    if "fearful" in raw or "恐惧" in raw or "纠结" in raw:
        return "fearful"
    return "secure"


def _partner_message_signal(message: str) -> dict[str, bool]:
    clean = message.strip()
    return {
        "empathy": any(word in clean for word in ["理解", "听起来", "感觉", "感受", "担心", "委屈", "难受", "辛苦"]),
        "reassurance": any(word in clean for word in ["我在", "不会离开", "看到消息", "在乎", "陪你", "安心", "确认"]),
        "space": any(word in clean for word in ["空间", "选择", "如果你愿意", "不逼", "不急", "慢慢", "没关系", "可以晚点"]),
        "question": any(mark in clean for mark in ["?", "？"]) or any(word in clean for word in ["能告诉我", "你希望", "你想", "要不要"]),
        "repair": any(word in clean for word in ["抱歉", "对不起", "我刚才", "我会调整", "我下次"]),
        "short": len(clean) < 8,
        "pressure": any(word in clean for word in ["必须", "马上", "你怎么", "不准", "一定要", "给我", "离不开", "控制", "威胁"]),
        "dismissive": any(word in clean for word in ["随便", "别烦", "矫情", "想太多", "无所谓", "至于吗"]),
    }


def _relationship_state_label(state: RelationshipState) -> tuple[str, str]:
    if state.boundary >= 78 or state.stress >= 78:
        return "高压边界", "red"
    if state.trust >= 70 and state.connection >= 65 and state.stress <= 45:
        return "稳定连接", "green"
    if state.trust >= 58 and state.boundary_safety >= 58:
        return "可对话窗口", "blue"
    if state.connection <= 35 or state.trust <= 35:
        return "撤离风险", "orange"
    return "谨慎试探", "yellow"


def _relationship_interpretation(state: RelationshipState) -> str:
    return (
        f"信任 {round(state.trust)}/100，压力 {round(state.stress)}/100，"
        f"边界压力 {round(state.boundary)}/100，连接 {round(state.connection)}/100；"
        f"当前处于“{state.state_label}”。"
    )


def _relationship_next_focus(state: RelationshipState, style: str) -> str:
    if state.boundary >= 70:
        return "先停止推进，给选择权和退路。"
    if state.stress >= 65:
        return "先做情绪反射和稳定确认，再谈事情。"
    if state.trust <= 45:
        return "补充具体、可验证的稳定行动，不说空泛承诺。"
    if style == "avoidant":
        return "保持轻量、尊重空间，用低压力问题延展。"
    if style == "anxious":
        return "给清晰回应和可预测节奏，同时维持边界。"
    if style == "fearful":
        return "慢一点，同时表达存在感和不施压。"
    return "可以开放提问，继续加深信息与感受层。"


def _stateful_partner_reply(reply: str, scenario_id: str, state: RelationshipState) -> str:
    if state.boundary >= 78:
        return "我现在有点被逼近的感觉，需要先缓一下。你如果能停在这里，我反而会更愿意之后回来聊。"
    if state.stress >= 76:
        return "我还是有点紧张，心里有一部分想躲开。但如果你能慢一点说，我愿意继续听。"
    if state.trust <= 38:
        return "我还没有完全相信这段对话是安全的。你说得温和一点、具体一点，我会更容易靠近。"
    if state.connection <= 32:
        return "我听到了，但感觉我们还没有真正接上。你能不能先说说你刚才听见了我哪一点？"
    if state.trust >= 72 and state.connection >= 65:
        if scenario_id == "avoidant":
            return "这样说我比较能接受，我愿意晚点再继续聊一点。你没有逼我，这让我有一点想靠近。"
        return "你这样回应让我安心了一些，我愿意继续跟你说。刚才那种紧绷感有一点松开了。"
    return reply


def _score_partner_message(message: str) -> float:
    score = 62.0
    if any(word in message for word in ["理解", "听起来", "感觉", "感受", "担心", "委屈"]):
        score += 12
    if any(word in message for word in ["可以", "愿意", "慢慢", "没关系", "不急"]):
        score += 10
    if any(word in message for word in ["空间", "选择", "如果你愿意", "不逼"]):
        score += 10
    if len(message.strip()) < 8:
        score -= 22
    if any(word in message for word in ["你怎么", "必须", "离不开", "控制", "威胁"]):
        score -= 28
    return round(_clamp(score, 0, 100))


def _partner_suggestions(message: str, state: RelationshipState | None = None) -> list[str]:
    suggestions: list[str] = []
    if not any(word in message for word in ["听起来", "感觉", "理解"]):
        suggestions.append("先补一句情绪反射，让对方知道你听见了。")
    if not any(word in message for word in ["可以", "愿意", "没关系", "不急"]):
        suggestions.append("加入退路式表达，降低对方被推进的压力。")
    if len(message.strip()) < 8:
        suggestions.append("回应太短，建议补一个具体观察或开放问题。")
    if state and state.boundary >= 70:
        suggestions.append("当前边界压力偏高，下一句优先给空间，不推进关系。")
    if state and state.stress >= 65:
        suggestions.append("当前情绪压力偏高，先稳定情绪，再进入解释。")
    if state and state.trust <= 45:
        suggestions.append("信任值偏低，下一句给具体行动或时间节奏，少用空泛承诺。")
    if state and state.connection <= 40:
        suggestions.append("连接感偏低，先复述对方一句关键感受，再问一个轻问题。")
    return suggestions[:3] or ["保持这种尊重边界、轻验证的节奏。"]


def _partner_simulation_system_prompt(attachment_style: str) -> str:
    return (
        "你是关系动力学训练系统里的 AI 训练伴侣，只扮演对话对象，不做心理诊断。"
        f"当前依恋/互动风格：{attachment_style}。"
        "你的回复要像真实对话对象，1-3 句中文，必须体现情绪流动、靠近/后退、边界变化，不要讲课。"
        "同时给用户回应打分并给 1-3 条训练建议；建议要体现你的职责定位：感知训练、边界确认、情绪承接、关系修复。"
        "必须拒绝 PUA、操控、威胁、跟踪、侵犯边界。"
        "输出严格 JSON：{\"reply\":\"...\",\"score\":80,\"suggestions\":[\"...\"]}。"
    )


def _build_three_hypotheses(sample: InteractionSample, visual_map: dict[str, Any]) -> list[dict[str, str]]:
    emotion = visual_map["emotion_thermometer"]
    return [
        {
            "name": "情绪假设",
            "content": f"她可能主要是{emotion['word']}，强度约 {emotion['average_intensity']}/10，需要先被承认。",
        },
        {
            "name": "需求假设",
            "content": sample.hidden_need or "她可能有未说出口的需求，需要用开放问题验证。",
        },
        {
            "name": "边界假设",
            "content": f"边界压力约 {visual_map['boundary_band']['level']}/10，回应要符合“{visual_map['boundary_band']['principle']}”。",
        },
    ]


def _next_minimum_action(problems: list[dict[str, Any]], bonuses: list[dict[str, Any]], ideal_response: str) -> str:
    if not problems:
        if bonuses:
            return f"保留这次的有效动作，下一句可以更具体一点：{ideal_response}"
        return f"补一个情绪反射或开放问题：{ideal_response}"
    first = str(problems[0].get("name", ""))
    mapping = {
        "封闭式回应": "把封闭句改成承接 + 开放问题。",
        "忽视情绪信号": "先说出你听到的情绪，再问她想不想继续说。",
        "急于解决问题": "先停止建议，改成陪伴或确认感受。",
        "过度分析": "删掉解释链，只留下一个具体观察和一个轻问句。",
    }
    return mapping.get(first, f"对照理想回应重写一句更安全、更具体的话：{ideal_response}")


def _derive_dimension_scores(
    total: float,
    differences: list[dict[str, Any]],
    sample: InteractionSample,
    ai_feedback: dict[str, Any] | None = None,
) -> dict[str, float]:
    ai_dimensions = (ai_feedback or {}).get("dimension_scores")
    if isinstance(ai_dimensions, dict):
        if all(isinstance(ai_dimensions.get(field), int | float) for field in SCORE_FIELDS):
            return {field: round(max(0, min(100, float(ai_dimensions[field]))), 2) for field in SCORE_FIELDS}

    scores = {
        "emotion_score": total,
        "need_score": total,
        "safety_score": total,
        "connection_score": total,
        "boundary_score": 90.0,
        "style_score": total,
        "repair_score": total if sample.scenario_category in ["冲突", "修复"] else 75.0,
    }
    for diff in differences:
        if diff.get("type") != "problem":
            continue
        name = diff.get("name")
        if name == "封闭式回应":
            scores["connection_score"] = max(0, scores["connection_score"] - 25)
            scores["need_score"] = max(0, scores["need_score"] - 10)
        elif name == "忽视情绪信号":
            scores["emotion_score"] = max(0, scores["emotion_score"] - 25)
            scores["safety_score"] = max(0, scores["safety_score"] - 10)
        elif name == "急于解决问题":
            scores["safety_score"] = max(0, scores["safety_score"] - 20)
            scores["need_score"] = max(0, scores["need_score"] - 15)
        elif name == "过度分析":
            scores["style_score"] = max(0, scores["style_score"] - 15)
    return {key: round(value, 2) for key, value in scores.items()}


def _build_mastery_model(scores: dict[str, float]) -> dict[str, Any]:
    dimensions: list[dict[str, Any]] = []
    for key, label in _dimension_labels().items():
        score = round(float(scores.get(key, 0)), 2)
        stage = _mastery_stage(score)
        dimensions.append({
            "dimension": key,
            "label": label,
            "score": score,
            "stage": stage["stage"],
            "stage_label": stage["label"],
            "next_gate": stage["next_gate"],
            "practice_focus": _dimension_recommendation(key),
        })
    weakest = min(dimensions, key=lambda item: float(item["score"])) if dimensions else None
    total = round(sum(float(item["score"]) for item in dimensions) / len(dimensions), 2) if dimensions else 0
    return {
        "total_score": total,
        "stage": _mastery_stage(total),
        "dimensions": dimensions,
        "weakest": weakest,
        "recommendation": _dimension_recommendation(str(weakest["dimension"]) if weakest else None),
        "principle": "知道 -> 辨认 -> 操作 -> 迁移 -> 自然；先稳定短板，再追求风格。",
    }


def _mastery_stage(score: float) -> dict[str, str]:
    if score < 35:
        return {"stage": "knowing", "label": "知道", "next_gate": "能说出概念和底线，不把控制当连接。"}
    if score < 55:
        return {"stage": "recognizing", "label": "辨认", "next_gate": "能在样本中辨认信号、情绪、需求和边界。"}
    if score < 75:
        return {"stage": "operating", "label": "操作", "next_gate": "能稳定写出承接情绪、轻验证、有退路的回应。"}
    if score < 90:
        return {"stage": "transferring", "label": "迁移", "next_gate": "能把技能迁移到新场景和不同依恋风格。"}
    return {"stage": "natural", "label": "自然", "next_gate": "保持复盘和反脆弱，不把熟练变成套路。"}


def _attribute_errors(
    differences: list[dict[str, Any]],
    sample: InteractionSample,
    dimension_scores: dict[str, float],
) -> list[dict[str, str]]:
    attributions: list[dict[str, str]] = []
    problem_names = [str(diff.get("name", "")) for diff in differences if diff.get("type") == "problem"]
    mapping = {
        "封闭式回应": ("connection_score", "对话关闭", "回应没有给对方继续表达的空间。"),
        "忽视情绪信号": ("emotion_score", "情绪误判", "没有先命名或承接对方的主要情绪。"),
        "急于解决问题": ("safety_score", "节奏过快", "在情绪未被接住前进入建议，容易让对方防御。"),
        "过度分析": ("style_score", "认知压过感受", "解释太多，轻验证和具身感不足。"),
    }
    for name in problem_names:
        dimension, category, reason = mapping.get(name, ("need_score", "策略错配", "回应与样本隐藏需求不够匹配。"))
        attributions.append({
            "category": category,
            "dimension": dimension,
            "reason": reason,
            "repair": _dimension_recommendation(dimension),
        })
    weak_dimensions = [key for key, value in dimension_scores.items() if value < 60]
    for dimension in weak_dimensions[:2]:
        if any(item["dimension"] == dimension for item in attributions):
            continue
        attributions.append({
            "category": "短板暴露",
            "dimension": dimension,
            "reason": f"{_dimension_labels().get(dimension, dimension)}低于 60，说明该环节尚未稳定。",
            "repair": _dimension_recommendation(dimension),
        })
    if sample.boundary_test_level and sample.boundary_test_level >= 7 and not any(item["dimension"] == "boundary_score" for item in attributions):
        attributions.append({
            "category": "边界压力",
            "dimension": "boundary_score",
            "reason": "样本边界压力偏高，训练重点应从推进转为降压与尊重。",
            "repair": _dimension_recommendation("boundary_score"),
        })
    return attributions[:4]


EXPRESSION_TOOL_BY_DIMENSION: dict[str, tuple[str, ...]] = {
    "emotion_score": ("expr_tool_041", "expr_tool_042", "expr_tool_050"),
    "need_score": ("expr_tool_004", "expr_tool_005", "expr_tool_054"),
    "safety_score": ("expr_tool_044", "expr_tool_047", "expr_tool_027"),
    "connection_score": ("expr_tool_011", "expr_tool_017", "expr_tool_019"),
    "boundary_score": ("expr_tool_027", "expr_tool_056", "expr_tool_060"),
    "style_score": ("expr_tool_016", "expr_tool_017", "expr_tool_034"),
    "repair_score": ("expr_tool_029", "expr_tool_047", "expr_tool_050"),
}

EXPRESSION_SCENE_DEFAULTS: dict[str, tuple[str, ...]] = {
    "初识": ("expr_tool_005", "expr_tool_054", "expr_tool_019"),
    "暧昧": ("expr_tool_017", "expr_tool_011", "expr_tool_038"),
    "热恋": ("expr_tool_041", "expr_tool_048", "expr_tool_059"),
    "冲突": ("expr_tool_044", "expr_tool_041", "expr_tool_050"),
    "修复": ("expr_tool_029", "expr_tool_047", "expr_tool_050"),
    "平淡": ("expr_tool_059", "expr_tool_060", "expr_tool_048"),
}


def _build_expression_tool_scoring(
    session: Session,
    sample: InteractionSample,
    user_response: str,
    ideal_response: str,
    response_type: str,
    dimension_scores: dict[str, float],
    error_attribution: list[dict[str, str]],
) -> dict[str, Any]:
    """Map a training answer onto the expression toolbox with local, auditable rules."""
    weak_dimensions = sorted(dimension_scores, key=lambda key: dimension_scores.get(key, 0))[:3]
    recommended_ids = _unique_tool_ids(
        [
            *EXPRESSION_SCENE_DEFAULTS.get(sample.scenario_category, ("expr_tool_041", "expr_tool_027", "expr_tool_019")),
            *[tool_id for dimension in weak_dimensions for tool_id in EXPRESSION_TOOL_BY_DIMENSION.get(dimension, ())],
        ]
    )[:6]
    tools = _load_expression_tools(session, recommended_ids)
    markers = _expression_markers(user_response)
    ideal_markers = _expression_markers(ideal_response)
    fit_score = _expression_fit_score(markers, ideal_markers, dimension_scores)
    missing_moves = _missing_expression_moves(markers, sample, response_type)
    practice_steps = _expression_practice_steps(tools, weak_dimensions, missing_moves)
    return {
        "fit_score": fit_score,
        "stage": _expression_stage(fit_score),
        "target_goal": _expression_goal_for(sample, weak_dimensions, response_type),
        "weak_dimensions": weak_dimensions,
        "detected_moves": markers,
        "missing_moves": missing_moves,
        "recommended_tools": tools,
        "practice_steps": practice_steps,
        "risk_notes": _expression_risk_notes(error_attribution, missing_moves),
        "principle": "表达评分把七维能力落到可练工具：先选目标，再选工具，再用一句话完成事实、感受、边界和下一步。",
    }


def _unique_tool_ids(tool_ids: list[str]) -> list[str]:
    seen: set[str] = set()
    unique: list[str] = []
    for tool_id in tool_ids:
        if tool_id in seen:
            continue
        seen.add(tool_id)
        unique.append(tool_id)
    return unique


def _load_expression_tools(session: Session, tool_ids: list[str]) -> list[dict[str, Any]]:
    if not tool_ids:
        return []
    rows = list(session.exec(select(ExpressionTool).where(col(ExpressionTool.tool_uuid).in_(tool_ids))).all())
    by_id = {tool.tool_uuid: tool for tool in rows}
    tools: list[dict[str, Any]] = []
    for tool_id in tool_ids:
        tool = by_id.get(tool_id)
        if tool is None:
            tools.append({
                "tool_uuid": tool_id,
                "name": tool_id,
                "layer": "unknown",
                "formula": "",
                "micro_steps": [],
                "risk_flags": [],
            })
            continue
        tools.append({
            "tool_uuid": tool.tool_uuid,
            "name": tool.name,
            "layer": tool.layer,
            "category": tool.category,
            "formula": tool.formula,
            "micro_steps": _loads_list(tool.micro_steps_json),
            "risk_flags": _loads_list(tool.risk_flags_json),
            "example_after": tool.example_after,
        })
    return tools


def _loads_list(value: str | None) -> list[Any]:
    if not value:
        return []
    try:
        data = json.loads(value)
    except json.JSONDecodeError:
        return []
    return data if isinstance(data, list) else []


def _expression_markers(text: str) -> dict[str, bool]:
    normalized = text.strip()
    return {
        "names_emotion": any(word in normalized for word in ("难过", "委屈", "失望", "累", "压力", "不安", "开心", "在意", "担心")),
        "states_fact": any(word in normalized for word in ("刚才", "今天", "这件事", "我听见", "我看到", "你说", "发生")),
        "keeps_boundary": any(word in normalized for word in ("可以拒绝", "不急", "慢慢", "你愿意", "如果你想", "先不", "空间")),
        "opens_question": "?" in normalized or "？" in normalized or any(word in normalized for word in ("吗", "要不要", "愿不愿意", "可不可以")),
        "repairs_impact": any(word in normalized for word in ("抱歉", "我承担", "影响到你", "补上", "下次", "重新约定")),
        "uses_humor_lightly": any(word in normalized for word in ("哈哈", "有点可爱", "我认", "开个玩笑", "逗你")),
    }


def _expression_fit_score(
    markers: dict[str, bool],
    ideal_markers: dict[str, bool],
    dimension_scores: dict[str, float],
) -> float:
    marker_score = sum(14 for matched in markers.values() if matched)
    ideal_gap_penalty = sum(7 for key, ideal in ideal_markers.items() if ideal and not markers.get(key))
    dimension_base = sum(dimension_scores.values()) / len(dimension_scores) if dimension_scores else 50
    return round(max(0, min(100, dimension_base * 0.55 + marker_score - ideal_gap_penalty)), 1)


def _missing_expression_moves(markers: dict[str, bool], sample: InteractionSample, response_type: str) -> list[str]:
    missing: list[str] = []
    if not markers["names_emotion"]:
        missing.append("先命名对方可能的情绪，而不是直接解释。")
    if not markers["keeps_boundary"]:
        missing.append("补一个可拒绝空间，让对方不被推进。")
    if not markers["opens_question"]:
        missing.append("用一个轻问题打开下一轮，而不是把话说死。")
    if sample.scenario_category in {"冲突", "修复"} and not markers["repairs_impact"]:
        missing.append("承认影响或给出具体补偿，避免空泛求和。")
    if response_type == "humor" and not markers["uses_humor_lightly"]:
        missing.append("幽默模式需要先自我降压，不能拿对方感受开玩笑。")
    return missing[:4]


def _expression_practice_steps(
    tools: list[dict[str, Any]],
    weak_dimensions: list[str],
    missing_moves: list[str],
) -> list[dict[str, str]]:
    primary_tool = tools[0]["name"] if tools else "情绪标注"
    dimension_label = _dimension_labels().get(weak_dimensions[0], "表达适配") if weak_dimensions else "表达适配"
    return [
        {"step": "识别", "action": f"先判断本题最弱环节：{dimension_label}。"},
        {"step": "选工具", "action": f"优先使用「{primary_tool}」，只完成一个清晰动作。"},
        {"step": "改写", "action": missing_moves[0] if missing_moves else "把当前回应压缩成一句事实、一句感受、一个可拒绝问题。"},
    ]


def _expression_stage(score: float) -> str:
    if score < 45:
        return "D1 识别"
    if score < 65:
        return "D2 套用"
    if score < 80:
        return "D3 改写"
    if score < 92:
        return "D4 迁移"
    return "D5 自然"


def _expression_goal_for(sample: InteractionSample, weak_dimensions: list[str], response_type: str) -> str:
    if "boundary_score" in weak_dimensions:
        return "确认边界"
    if "repair_score" in weak_dimensions or sample.scenario_category == "修复":
        return "修复信任"
    if response_type == "humor":
        return "降低防御"
    if response_type == "tension":
        return "制造轻张力"
    if "emotion_score" in weak_dimensions:
        return "命名感受"
    return "引导深聊"


def _expression_risk_notes(error_attribution: list[dict[str, str]], missing_moves: list[str]) -> list[str]:
    notes = [item["reason"] for item in error_attribution[:2] if item.get("reason")]
    if any("可拒绝" in move or "边界" in move for move in missing_moves):
        notes.append("当前回应缺少退路，容易被对方感到推进或被要求立刻表态。")
    if not notes:
        notes.append("保持具体、低压、可退出，避免把表达工具变成套路或控制。")
    return notes[:3]


def _run_ai_score(
    request: CompareRequest,
    sample: InteractionSample,
    ideal_response: str,
    rule_score: float,
    rule_differences: list[dict[str, Any]],
) -> dict[str, Any] | None:
    """调用 AI provider 进行深度评分；未配置时安全降级为规则评分。"""
    safety = safety_guardian.inspect(
        {
            "sample": {
                "context": sample.context,
                "their_words": sample.their_words,
                "their_behavior": sample.their_behavior,
            },
            "user_response": request.original_response,
            "ideal_response": ideal_response,
            "response_type": request.response_type,
        }
    )
    if safety_guardian.should_block(safety):
        return {
            "ok": False,
            "reason": safety.message or "检测到高风险内容，已阻断 AI 生成链路。",
            "safety": safety.to_dict(),
            "safe_alternatives": safety.alternatives or [],
        }

    if not ai_provider_client.configured:
        return {"ok": False, "reason": f"{ai_provider_client.credential_env_name} 未配置，使用规则评分降级"}

    payload = {
        "sample": {
            "context": sample.context,
            "their_words": sample.their_words,
            "their_behavior": sample.their_behavior,
            "emotion_tags_json": sample.emotion_tags_json,
            "hidden_need": sample.hidden_need,
            "scenario_category": sample.scenario_category,
            "attachment_signal": sample.attachment_signal,
            "boundary_test_level": sample.boundary_test_level,
        },
        "user_response": request.original_response,
        "ideal_response": ideal_response,
        "response_type": request.response_type,
        "rule_score": rule_score,
        "rule_differences": rule_differences,
        "required_schema": {
            "score": "0-100 number",
            "dimension_scores": {
                "emotion_score": "0-100",
                "need_score": "0-100",
                "safety_score": "0-100",
                "connection_score": "0-100",
                "boundary_score": "0-100",
                "style_score": "0-100",
                "repair_score": "0-100",
            },
            "differences": [{"type": "problem|bonus", "name": "string", "desc": "string"}],
            "suggestions": ["string"],
            "safety_note": "string",
        },
    }

    async def _call() -> dict[str, Any]:
        response = await ai_orchestrator.run(AIRequest(task_type="score_response", payload=payload))
        return response.model_dump()

    try:
        ai_response = asyncio.run(_call())
    except RuntimeError:
        loop = asyncio.new_event_loop()
        try:
            ai_response = loop.run_until_complete(_call())
        finally:
            loop.close()
    except Exception as exc:  # pragma: no cover - 真实外部网络失败时降级
        return {"ok": False, "reason": f"AI 调用失败，使用规则评分降级: {exc}"}

    if not ai_response.get("ok"):
        return {
            "ok": False,
            "reason": ai_response.get("error") or "AI 安全护栏/调用失败",
            "safety": ai_response.get("safety"),
            "safe_alternatives": ai_response.get("safe_alternatives") or [],
        }
    content = ai_response.get("content") or {}
    content["ok"] = True
    content["safety"] = ai_response.get("safety")
    content["safe_alternatives"] = ai_response.get("safe_alternatives") or []
    return content


def _merge_score(rule_score: float, ai_feedback: dict[str, Any] | None) -> float:
    ai_score = (ai_feedback or {}).get("score")
    if isinstance(ai_score, int | float) and (ai_feedback or {}).get("ok"):
        return round(max(0, min(100, rule_score * 0.45 + float(ai_score) * 0.55)), 2)
    return rule_score


def _merge_differences(
    rule_differences: list[dict[str, Any]],
    ai_feedback: dict[str, Any] | None,
) -> list[dict[str, Any]]:
    merged = list(rule_differences)
    ai_diffs = (ai_feedback or {}).get("differences")
    if isinstance(ai_diffs, list) and (ai_feedback or {}).get("ok"):
        for diff in ai_diffs[:4]:
            if isinstance(diff, dict) and diff.get("name") and diff.get("desc"):
                merged.append({"type": diff.get("type", "problem"), "name": f"AI深评：{diff.get('name')}", "desc": diff.get("desc")})
    return merged


def _merge_suggestions(rule_suggestions: list[str], ai_feedback: dict[str, Any] | None) -> list[str]:
    suggestions = list(rule_suggestions)
    ai_suggestions = (ai_feedback or {}).get("suggestions")
    if isinstance(ai_suggestions, list) and (ai_feedback or {}).get("ok"):
        suggestions.extend(str(item) for item in ai_suggestions[:3])
    return suggestions[:6]


def _maybe_create_mistake(
    session: Session,
    sample: InteractionSample,
    user_response: str,
    ideal_response: str,
    score: float,
    differences: list[dict[str, Any]],
    error_attribution: list[dict[str, str]],
    mastery: dict[str, Any],
) -> int | None:
    has_problem = any(d.get("type") == "problem" for d in differences)
    if score >= 70 and not has_problem:
        return None
    mistake = MistakeLog(
        sample_id=sample.id or 0,
        user_bad_response=user_response,
        correct_response=ideal_response,
        emotion_mistake="; ".join(d.get("name", "") for d in differences if d.get("type") == "problem") or None,
        error_attribution_json=json.dumps(error_attribution, ensure_ascii=False),
        mastery_snapshot_json=json.dumps(mastery, ensure_ascii=False),
        review_focus=_mistake_review_focus(error_attribution, mastery),
        reviewed=False,
        review_interval=1,
        next_review=date.today() + timedelta(days=1),
    )
    session.add(mistake)
    session.commit()
    session.refresh(mistake)
    return mistake.id


def _mistake_review_focus(error_attribution: list[dict[str, str]], mastery: dict[str, Any]) -> str | None:
    if error_attribution:
        first = error_attribution[0]
        category = first.get("category") or "错误归因"
        dimension = _dimension_labels().get(first.get("dimension") or "", first.get("dimension") or "")
        return f"{category} · {dimension}".strip(" ·")
    weakest = mastery.get("weakest") if isinstance(mastery, dict) else None
    if isinstance(weakest, dict):
        label = weakest.get("label")
        stage_label = weakest.get("stage_label")
        if label and stage_label:
            return f"{label} · {stage_label}"
    return None


def _calculate_average_scores(session: Session) -> dict[str, float]:
    attempts = session.exec(select(TrainingAttempt).order_by(desc(TrainingAttempt.created_at)).limit(30)).all()
    avg: dict[str, float] = {}
    for field in SCORE_FIELDS:
        vals: list[float] = []
        for attempt in attempts:
            value = _score_field_value(attempt, field)
            if value is not None:
                vals.append(value)
        avg[field] = sum(vals) / len(vals) if vals else 0.0
    return avg


def _score_field_value(attempt: TrainingAttempt, field: str) -> float | None:
    value = getattr(attempt, field)
    return float(value) if isinstance(value, int | float) else None


def _weakest_dimension_from_scores(scores: dict[str, float]) -> str:
    return min(scores, key=lambda key: scores[key])


def _training_attempt_count(session: Session) -> int:
    return int(session.exec(select(func.count()).select_from(TrainingAttempt)).one() or 0)


def _create_ability_snapshot(session: Session) -> AbilitySnapshot | None:
    avg = _calculate_average_scores(session)
    if not avg:
        return None
    weakest = _weakest_dimension_from_scores(avg)
    snapshot = AbilitySnapshot(
        emotion_score=avg["emotion_score"],
        need_score=avg["need_score"],
        safety_score=avg["safety_score"],
        connection_score=avg["connection_score"],
        boundary_score=avg["boundary_score"],
        style_score=avg["style_score"],
        repair_score=avg["repair_score"],
        total_score=sum(avg.values()) / len(avg),
        weakest_dimension=weakest,
        next_recommendation=_dimension_recommendation(weakest),
    )
    session.add(snapshot)
    session.commit()
    session.refresh(snapshot)
    return snapshot


def _get_weakest_dimension(session: Session) -> str | None:
    if not _training_attempt_count(session):
        return None
    avg = _calculate_average_scores(session)
    return _weakest_dimension_from_scores(avg)


def _dimension_to_category(dimension: str | None) -> str | None:
    if dimension == "repair_score":
        return "修复"
    if dimension in ["safety_score", "boundary_score"]:
        return "冲突"
    if dimension in ["connection_score", "style_score"]:
        return "暧昧"
    return None


def _dimension_recommendation(dimension: str | None) -> str:
    mapping = {
        "emotion_score": "优先练习情绪识别：先命名情绪，再回应事情。",
        "need_score": "优先练习隐藏需求洞察：问自己“对方真正想被怎样对待”。",
        "safety_score": "优先练习安全回应：减少评判、责备和急着解决。",
        "connection_score": "优先练习开放式延展：把对话打开，而不是关闭。",
        "boundary_score": "优先练习边界尊重：给选择、给退路、不施压。",
        "style_score": "优先练习风格匹配：根据关系阶段选择柔和、张力或幽默。",
        "repair_score": "优先练习冲突修复：先负责、再理解、后协商。",
    }
    return mapping.get(dimension or "", "继续完成每日训练，建立稳定能力曲线。")


def _dimension_labels() -> dict[str, str]:
    return {
        "emotion_score": "情绪识别",
        "need_score": "需求洞察",
        "safety_score": "安全回应",
        "connection_score": "连接延展",
        "boundary_score": "边界尊重",
        "style_score": "风格匹配",
        "repair_score": "修复能力",
    }


def _score_to_level(score: float) -> str:
    if score < 30:
        return "启动期"
    if score < 60:
        return "建立期"
    if score < 80:
        return "熟练期"
    return "内化期"

@router.get("/summary/today")
def get_today_summary(session: Session = Depends(get_session)) -> dict[str, Any]:
    """今日训练摘要，用于 Dashboard/Daily 替代前端随机统计。"""
    today_start = date.today()
    attempts = session.exec(select(TrainingAttempt).where(func.date(TrainingAttempt.created_at) == str(today_start))).all()
    mistakes = session.exec(select(MistakeLog).where(MistakeLog.reviewed == False)).all()  # noqa: E712
    avg_score = sum(a.total_score for a in attempts) / len(attempts) if attempts else 0
    return {
        "date": str(today_start),
        "attempts_count": len(attempts),
        "average_score": round(avg_score),
        "mistakes_open": len(mistakes),
        "completed": len(attempts) >= 1,
        "recommendation": "完成一次对比回应训练" if not attempts else _dimension_recommendation(_get_weakest_dimension(session)),
    }


@router.get("/summary/week")
def get_week_summary(session: Session = Depends(get_session)) -> dict[str, Any]:
    """最近 7 天训练摘要。"""
    start = date.today() - timedelta(days=6)
    attempts = session.exec(select(TrainingAttempt).where(func.date(TrainingAttempt.created_at) >= str(start))).all()
    avg_score = sum(a.total_score for a in attempts) / len(attempts) if attempts else 0
    active_days = len({a.created_at.date().isoformat() for a in attempts})
    return {
        "start_date": str(start),
        "end_date": str(date.today()),
        "attempts_count": len(attempts),
        "active_days": active_days,
        "average_score": round(avg_score),
        "streak_hint": f"最近 7 天训练 {active_days} 天",
    }
