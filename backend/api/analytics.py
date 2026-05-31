"""Analytics API for AI quality and cross-session relationship trends."""
import hashlib
import json
import re
from collections import Counter, defaultdict
from importlib import import_module
from typing import Any, cast

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.sql.elements import ColumnElement
from sqlmodel import Session, desc, select

from backend.ai.provider_client import ai_provider_client
from backend.database.connection import get_session
from backend.models.ai import AIProviderProbeLog, AIRunLog
from backend.models.evolution import PipelineRunLog
from backend.models.knowledge import KnowledgeEntry
from backend.models.resource import ResourceLibrary
from backend.models.runtime import RuntimeEvent
from backend.models.training import PracticeEvent, PracticeSession

router = APIRouter(prefix="/api/analytics", tags=["分析"])


class RuntimeEventCreate(BaseModel):
    source: str = Field(default="frontend", max_length=40)
    event_type: str = Field(min_length=2, max_length=80)
    severity: str = Field(default="medium", max_length=20)
    route: str | None = Field(default=None, max_length=240)
    method: str | None = Field(default=None, max_length=12)
    endpoint: str | None = Field(default=None, max_length=240)
    http_status: int | None = Field(default=None, ge=100, le=599)
    message: str = Field(min_length=1, max_length=1000)
    context: dict[str, Any] = Field(default_factory=dict)


def _sql_column(value: Any) -> ColumnElement[Any]:
    return cast(ColumnElement[Any], value)


@router.post("/runtime-events")
def create_runtime_event(payload: RuntimeEventCreate, session: Session = Depends(get_session)) -> dict[str, Any]:
    """Record a runtime error or API failure as an operational audit event."""
    event = RuntimeEvent(
        source=_bounded_label(payload.source, "frontend"),
        event_type=_bounded_label(payload.event_type, "runtime_event"),
        severity=_runtime_severity(payload.severity, payload.http_status),
        route=_safe_runtime_path(payload.route),
        method=_safe_runtime_method(payload.method),
        endpoint=_safe_runtime_path(payload.endpoint),
        http_status=payload.http_status,
        message_hash=_audit_digest(payload.message) or "sha256:unknown",
        message_preview=_message_preview(payload.message),
        context_json=json.dumps(_safe_runtime_context(payload.context), ensure_ascii=False, sort_keys=True),
    )
    session.add(event)
    session.commit()
    session.refresh(event)
    return {
        "id": event.id,
        "status": "recorded",
        "event_type": event.event_type,
        "severity": event.severity,
        "message_hash": event.message_hash,
        "created_at": event.created_at.isoformat(),
        "principle": "Runtime events store route, endpoint, status, derived hash, and short sanitized previews; they do not store form bodies, tokens, or full user text.",
    }


@router.get("/ai-quality")
def get_ai_quality_report(limit: int = 200, session: Session = Depends(get_session)) -> dict[str, Any]:
    """Aggregate AI run logs into operational quality signals."""
    safe_limit = max(1, min(limit, 1000))
    logs = list(session.exec(select(AIRunLog).order_by(desc(AIRunLog.created_at)).limit(safe_limit)).all())
    total = len(logs)
    outcomes = Counter(log.outcome for log in logs)
    task_types = Counter(log.task_type for log in logs)
    providers = Counter(log.provider for log in logs)
    fallback_reasons = Counter(log.fallback_reason for log in logs if log.fallback_reason)
    safety_flags: Counter[str] = Counter()
    latencies = [log.latency_ms for log in logs if log.latency_ms >= 0]
    provider_attempts = [log for log in logs if log.outcome != "blocked_safety"]
    safety_alternative_coverage = _safety_alternative_coverage(session)

    for log in logs:
        for flag in _loads_json_list(log.safety_flags_json):
            safety_flags[str(flag)] += 1

    success = outcomes.get("success", 0) + outcomes.get("success_raw_text", 0)
    blocked = outcomes.get("blocked_safety", 0)
    provider_failures = outcomes.get("provider_failure", 0)
    fallback = sum(count for outcome, count in outcomes.items() if outcome not in {"success", "success_raw_text"})
    provider_attempt_total = len(provider_attempts)
    provider_success_rate = _percent(success, provider_attempt_total)

    return {
        "summary": {
            "runs": total,
            "success_rate": _percent(success, total),
            "provider_attempts": provider_attempt_total,
            "provider_success_rate": provider_success_rate,
            "fallback_rate": _percent(fallback, total),
            "safety_block_rate": _percent(blocked, total),
            "provider_failure_rate": _percent(provider_failures, total),
            "avg_latency_ms": round(sum(latencies) / len(latencies), 1) if latencies else 0,
        },
        "outcome_breakdown": _counter_items(outcomes),
        "task_type_breakdown": _counter_items(task_types),
        "provider_breakdown": _counter_items(providers),
        "fallback_reasons": _counter_items(fallback_reasons),
        "safety_flags": _counter_items(safety_flags),
        "safety_alternative_coverage": safety_alternative_coverage,
        "trend": _ai_quality_trend(logs),
        "recent_runs": [
            {
                "id": log.id,
                "task_type": log.task_type,
                "provider": log.provider,
                "model": log.model,
                "outcome": log.outcome,
                "fallback_reason": log.fallback_reason,
                "safety_risk_level": log.safety_risk_level,
                "latency_ms": log.latency_ms,
                "created_at": log.created_at.isoformat(),
            }
            for log in logs[:12]
        ],
        "next_actions": _ai_quality_next_actions(
            total,
            success,
            blocked,
            provider_failures,
            fallback_reasons,
            safety_flags,
            provider_attempt_total,
            provider_success_rate,
            safety_alternative_coverage,
        ),
        "principle": "AI 质量分开看 provider 调用成功率与安全阻断率；安全阻断是保护动作，不计入 provider 失败。",
    }


@router.get("/ai-failure-analysis")
def get_ai_failure_analysis(limit: int = 300, session: Session = Depends(get_session)) -> dict[str, Any]:
    """Cluster AI failures into audit-friendly root-cause buckets."""
    safe_limit = max(1, min(limit, 1000))
    logs = list(session.exec(select(AIRunLog).order_by(desc(AIRunLog.created_at)).limit(safe_limit)).all())
    failures = [log for log in logs if log.outcome not in {"success", "success_raw_text", "blocked_safety"}]
    provider_failures = [log for log in failures if log.outcome == "provider_failure"]
    safety_blocks = [log for log in logs if log.outcome == "blocked_safety"]
    fallback_reasons = Counter(log.fallback_reason or "unknown" for log in failures)
    by_task = Counter(log.task_type for log in failures)
    by_provider = Counter(log.provider for log in failures)
    by_model = Counter(log.model or "unknown" for log in failures)
    flags: Counter[str] = Counter()
    for log in safety_blocks:
        for flag in _loads_json_list(log.safety_flags_json):
            flags[str(flag)] += 1
    safety_alternative_coverage = _safety_alternative_coverage(session)
    clusters = _ai_failure_clusters(
        provider_failures,
        safety_blocks,
        fallback_reasons,
        by_task,
        by_provider,
        by_model,
        flags,
        safety_alternative_coverage,
    )
    return {
        "summary": {
            "runs_scanned": len(logs),
            "failures": len(failures),
            "provider_failures": len(provider_failures),
            "safety_blocks": len(safety_blocks),
            "failure_rate": _percent(len(failures), len(logs)),
            "safety_block_rate": _percent(len(safety_blocks), len(logs)),
        },
        "clusters": clusters,
        "fallback_reasons": _counter_items(fallback_reasons),
        "task_breakdown": _counter_items(by_task),
        "provider_breakdown": _counter_items(by_provider),
        "model_breakdown": _counter_items(by_model),
        "safety_flags": _counter_items(flags),
        "safety_alternative_coverage": safety_alternative_coverage,
        "next_actions": _ai_failure_next_actions(clusters),
        "principle": "失败分析只聚合 outcome、provider、任务、fallback reason 和安全 flags；不返回敏感原文或 payload 内容。",
    }


@router.get("/ai-provider-diagnostics")
def get_ai_provider_diagnostics(limit: int = 300, session: Session = Depends(get_session)) -> dict[str, Any]:
    """Diagnose provider configuration and recent failure patterns without exposing secrets."""
    safe_limit = max(1, min(limit, 1000))
    logs = list(session.exec(select(AIRunLog).order_by(desc(AIRunLog.created_at)).limit(safe_limit)).all())
    provider_logs = [log for log in logs if log.provider == ai_provider_client.provider]
    failures = [log for log in provider_logs if log.outcome == "provider_failure"]
    failure_reasons = Counter(log.fallback_reason or "unknown" for log in failures)
    http_statuses: Counter[str] = Counter()
    for log in failures:
        status = _extract_http_status(log.fallback_reason)
        if status:
            http_statuses[status] += 1
    return {
        "request_shape": _provider_request_shape(),
        "provider": {
            "name": ai_provider_client.provider,
            "configured": ai_provider_client.configured,
            "mode": _provider_mode_value(ai_provider_client.mode),
            "model": ai_provider_client.model,
            "base_url": _redact_url(ai_provider_client.base_url),
            "chat_path": ai_provider_client._path(),
            "timeout_seconds": ai_provider_client.timeout,
            "api_key_present": ai_provider_client.configured,
            "compatibility": _provider_config_compatibility(
                ai_provider_client.provider,
                _provider_mode_value(ai_provider_client.mode),
                ai_provider_client.model,
                ai_provider_client.base_url,
                ai_provider_client._path(),
            ),
        },
        "local_remediation": _provider_local_remediation(
            ai_provider_client.provider,
            _provider_mode_value(ai_provider_client.mode),
        ),
        "recent": {
            "runs": len(provider_logs),
            "provider_failures": len(failures),
            "provider_failure_rate": _percent(len(failures), len(provider_logs)),
            "fallback_reasons": _counter_items(failure_reasons, limit=8),
            "http_statuses": _counter_items(http_statuses, limit=8),
        },
        "risk_level": _provider_risk_level(len(provider_logs), len(failures), ai_provider_client.configured),
        "diagnostics": _provider_diagnostic_items(
            failure_reasons,
            http_statuses,
            ai_provider_client.configured,
            ai_provider_client.provider,
            _provider_mode_value(ai_provider_client.mode),
            ai_provider_client.model,
            ai_provider_client.base_url,
            ai_provider_client._path(),
        ),
        "failure_playbook": _provider_failure_playbook(
            failure_reasons,
            http_statuses,
            ai_provider_client.configured,
            _provider_request_shape(),
            _provider_config_compatibility(
                ai_provider_client.provider,
                _provider_mode_value(ai_provider_client.mode),
                ai_provider_client.model,
                ai_provider_client.base_url,
                ai_provider_client._path(),
            ),
        ),
        "next_actions": _provider_next_actions(
            failure_reasons,
            http_statuses,
            ai_provider_client.configured,
            ai_provider_client.provider,
            _provider_mode_value(ai_provider_client.mode),
            ai_provider_client.model,
            ai_provider_client.base_url,
            ai_provider_client._path(),
        ),
        "principle": "Provider 诊断只暴露配置形态、脱敏 URL、失败模式和处置建议；不返回 API key、payload 原文或响应全文。",
    }


@router.get("/ai-provider-success-contract")
def get_ai_provider_success_contract(limit: int = 500, session: Session = Depends(get_session)) -> dict[str, Any]:
    """Measure provider success shape quality after JSON recovery and response alias normalization."""
    safe_limit = max(1, min(limit, 1500))
    logs = list(session.exec(select(AIRunLog).order_by(desc(AIRunLog.created_at)).limit(safe_limit)).all())
    provider_logs = [log for log in logs if log.provider == ai_provider_client.provider]
    outcomes = Counter(log.outcome for log in provider_logs)
    fallback_reasons = Counter(log.fallback_reason for log in provider_logs if log.fallback_reason)
    task_matrix = _provider_success_task_matrix(provider_logs)
    contract_gaps = _provider_success_contract_gaps(provider_logs, fallback_reasons)
    total = len(provider_logs)
    structured_success = outcomes.get("success", 0)
    raw_text_success = outcomes.get("success_raw_text", 0)
    provider_failure = outcomes.get("provider_failure", 0)
    return {
        "summary": {
            "runs": total,
            "structured_success_rate": _percent(structured_success, total),
            "raw_text_rate": _percent(raw_text_success, total),
            "provider_failure_rate": _percent(provider_failure, total),
            "recoverable_success_rate": _percent(structured_success + raw_text_success, total),
            "post_fix_target": {
                "structured_success_rate": 80,
                "raw_text_rate_max": 15,
                "provider_failure_rate_max": 10,
            },
        },
        "outcomes": _counter_items(outcomes),
        "fallback_reasons": _counter_items(fallback_reasons, limit=8),
        "task_matrix": task_matrix,
        "contract_gaps": contract_gaps,
        "quality_gate": {
            "has_enough_runs": total >= 20,
            "structured_success_ok": _percent(structured_success, total) >= 80 if total else False,
            "raw_text_needs_review": _percent(raw_text_success, total) > 15 if total else False,
            "provider_failure_needs_review": _percent(provider_failure, total) > 10 if total else False,
        },
        "next_actions": _provider_success_contract_next_actions(total, outcomes, fallback_reasons, contract_gaps),
        "principle": "Success contract report aggregates provider outcomes, response summary keys, and fallback reasons only; it never returns payload text, raw model text, API keys, or user messages.",
    }


@router.get("/ai-provider-probe-readiness")
def get_ai_provider_probe_readiness(session: Session = Depends(get_session)) -> dict[str, Any]:
    """Return a safe live-probe runbook without performing an external call."""
    return _provider_probe_readiness(session)


@router.post("/ai-provider-probe")
async def run_ai_provider_probe(dry_run: bool = True, session: Session = Depends(get_session)) -> dict[str, Any]:
    """Preview or run a minimal provider probe while storing only redacted audit facts."""
    result = await ai_provider_client.probe(dry_run=dry_run)
    request_shape = _ensure_dict(result.get("request_shape"))
    if not request_shape:
        raise HTTPException(status_code=500, detail="Provider probe did not return request_shape")
    log = AIProviderProbeLog(
        provider=str(request_shape.get("provider") or ai_provider_client.provider),
        mode=str(request_shape.get("mode") or _provider_mode_value(ai_provider_client.mode)),
        model=str(request_shape.get("model") or ai_provider_client.model),
        request_shape_json=json.dumps(request_shape, ensure_ascii=False, sort_keys=True),
        dry_run=bool(result.get("dry_run")),
        outcome=str(result.get("outcome") or "unknown"),
        http_status=_optional_int(result.get("http_status")),
        error_type=str(result.get("error_type")) if result.get("error_type") else None,
        latency_ms=int(result.get("latency_ms") or 0),
    )
    session.add(log)
    session.commit()
    session.refresh(log)
    if not log.dry_run and log.outcome == "blocked_by_policy":
        raise HTTPException(
            status_code=409,
            detail={
                "outcome": log.outcome,
                "error_type": log.error_type,
                "audit_log": {"id": log.id, "created_at": log.created_at.isoformat()},
                "principle": f"Live provider probe is disabled unless {_provider_live_probe_env_name()}=true.",
            },
        )
    return {
        "dry_run": log.dry_run,
        "outcome": log.outcome,
        "http_status": log.http_status,
        "error_type": log.error_type,
        "latency_ms": log.latency_ms,
        "request_shape": request_shape,
        "audit_log": {"id": log.id, "created_at": log.created_at.isoformat()},
        "principle": "Provider probe only stores redacted request_shape, status, error class, and latency; it never stores prompt text, API keys, or response bodies.",
    }


@router.get("/relationship-trends")
def get_relationship_trends(limit: int = 50, session: Session = Depends(get_session)) -> dict[str, Any]:
    """Aggregate AI partner sessions into a long-term relationship capability trend."""
    safe_limit = max(1, min(limit, 200))
    sessions = list(session.exec(select(PracticeSession).order_by(desc(PracticeSession.updated_at)).limit(safe_limit)).all())
    if not sessions:
        return _empty_relationship_trends()

    session_ids = [item.id for item in sessions if item.id is not None]
    events = list(session.exec(
        select(PracticeEvent)
        .where(PracticeEvent.session_id.in_(session_ids))  # type: ignore[attr-defined]
        .order_by(_sql_column(PracticeEvent.created_at))
    ).all()) if session_ids else []
    events_by_session: dict[int, list[PracticeEvent]] = defaultdict(list)
    for event in events:
        events_by_session[event.session_id].append(event)

    session_summaries = [_relationship_session_summary(item, events_by_session.get(int(item.id or 0), [])) for item in sessions]
    completed = [item for item in session_summaries if item["turns"] > 0]
    total_turns = sum(item["turns"] for item in completed)
    avg_score = round(sum(item["average_score"] for item in completed) / len(completed), 1) if completed else 0
    deltas = _average_state_delta(completed)
    attachment_counts = Counter(item["attachment_style"] for item in session_summaries if item["attachment_style"])
    blocked_sessions = sum(1 for item in session_summaries if item["status"] == "blocked" or item["safety_blocks"] > 0)

    return {
        "summary": {
            "sessions": len(sessions),
            "sessions_with_events": len(completed),
            "turns": total_turns,
            "average_score": avg_score,
            "blocked_sessions": blocked_sessions,
            "repair_index": _repair_index(deltas, avg_score),
        },
        "average_state_delta": deltas,
        "attachment_distribution": _counter_items(attachment_counts),
        "session_trend": list(reversed(session_summaries[:20])),
        "focus_distribution": _focus_distribution(completed),
        "next_actions": _relationship_next_actions(completed, deltas, blocked_sessions),
        "principle": "单次会话看转折，跨会话趋势看能力是否在长期推高信任、连接和边界安全，同时降低压力。",
    }


@router.get("/center")
def get_analytics_center(limit: int = 120, session: Session = Depends(get_session)) -> dict[str, Any]:
    """Aggregate world-class quality signals into one auditable analysis center."""
    safe_limit = max(20, min(limit, 500))
    ai_quality = get_ai_quality_report(limit=safe_limit, session=session)
    ai_failures = get_ai_failure_analysis(limit=safe_limit, session=session)
    provider = get_ai_provider_diagnostics(limit=safe_limit, session=session)
    provider_success_contract = get_ai_provider_success_contract(limit=safe_limit, session=session)
    relationship = get_relationship_trends(limit=80, session=session)
    scheduler = _analytics_center_scheduler_health()
    gold, conflict_queue, import_quality, vector = _analytics_center_external_reports(session)
    scorecard = _analytics_center_scorecard(
        ai_quality,
        provider,
        relationship,
        gold,
        conflict_queue,
        import_quality,
        vector,
        scheduler,
    )
    alerts = _analytics_center_alerts(scorecard, ai_failures, import_quality, scheduler)
    return {
        "scorecard": scorecard,
        "alerts": alerts,
        "timeline": _analytics_center_timeline(ai_quality, relationship, gold, import_quality, vector, scheduler),
        "sections": {
            "ai_quality": {
                "summary": ai_quality.get("summary", {}),
                "trend": ai_quality.get("trend", [])[-14:],
                "next_actions": ai_quality.get("next_actions", [])[:4],
            },
            "ai_failures": {
                "summary": ai_failures.get("summary", {}),
                "clusters": ai_failures.get("clusters", [])[:5],
            },
            "provider": {
                "provider": provider.get("provider", {}),
                "recent": provider.get("recent", {}),
                "risk_level": provider.get("risk_level"),
                "diagnostics": provider.get("diagnostics", [])[:5],
                "success_contract": provider_success_contract,
                "probe_readiness": _provider_probe_readiness(session),
                "failure_playbook": provider.get("failure_playbook", {}),
            },
            "gold_set": {
                "summary": gold.get("summary", {}),
                "quality_gates": gold.get("quality_gates", {}),
                "open_conflicts": conflict_queue.get("total", 0),
                "next_actions": gold.get("next_actions", [])[:4],
            },
            "import_quality": {
                "quality_score": import_quality.get("quality_score"),
                "quality_debt": import_quality.get("quality_debt", {}),
                "totals": import_quality.get("totals", {}),
            },
            "vector_recall": {
                "summary": vector.get("summary", {}),
                "recommendation": vector.get("recommendation", {}),
            },
            "training_trends": {
                "summary": relationship.get("summary", {}),
                "average_state_delta": relationship.get("average_state_delta", {}),
                "session_trend": relationship.get("session_trend", [])[-20:],
            },
            "scheduler": scheduler,
        },
        "principle": "分析中心聚合质量指标和告警，不返回 AI payload、私密原文或第三方全文。",
    }


@router.get("/audit-center")
def get_audit_center(limit: int = 80, module: str | None = None, session: Session = Depends(get_session)) -> dict[str, Any]:
    """Return a unified read-only audit stream for day-to-day operations."""
    safe_limit = max(10, min(limit, 300))
    normalized_module = module.strip().lower() if module else None
    events = _audit_center_events(session, safe_limit, normalized_module)
    total = len(events)
    status_counts = Counter(str(event["status"]) for event in events)
    module_counts = Counter(str(event["module"]) for event in events)
    severity_counts = Counter(str(event["severity"]) for event in events)
    needs_attention = sum(1 for event in events if event["status"] in {"failed", "needs_attention", "blocked"})
    return {
        "summary": {
            "events": total,
            "needs_attention": needs_attention,
            "latest_at": events[0]["created_at"] if events else None,
            "module_filter": normalized_module or "all",
        },
        "filters": {
            "modules": _counter_items(module_counts, limit=20),
            "statuses": _counter_items(status_counts, limit=20),
            "severities": _counter_items(severity_counts, limit=20),
        },
        "events": events,
        "next_actions": _audit_center_next_actions(events),
        "principle": "统一审计中心只聚合结构化状态、哈希、摘要和操作结果；不返回 AI payload、人工说明明文、第三方全文或密钥。",
    }


def _relationship_session_summary(practice_session: PracticeSession, events: list[PracticeEvent]) -> dict[str, Any]:
    states = [_loads_json_dict(event.relationship_state_json) for event in events]
    first = states[0] if states else {}
    last = states[-1] if states else _loads_json_dict(practice_session.current_state_json)
    return {
        "id": practice_session.id,
        "scenario_name": practice_session.scenario_name,
        "attachment_style": practice_session.attachment_style,
        "difficulty": practice_session.difficulty,
        "status": practice_session.status,
        "turns": len(events),
        "average_score": round(practice_session.average_score, 1),
        "safety_blocks": sum(1 for event in events if event.source == "safety_blocked"),
        "state_label": str(last.get("state_label") or "观察中"),
        "next_focus": str(last.get("next_focus") or "先观察线索，再用轻问句验证。"),
        "started_at": practice_session.started_at.isoformat(),
        "updated_at": practice_session.updated_at.isoformat(),
        "delta": {
            "trust": _state_delta(first, last, "trust"),
            "stress": _state_delta(first, last, "stress"),
            "boundary": _state_delta(first, last, "boundary"),
            "boundary_safety": _state_delta(first, last, "boundary_safety"),
            "connection": _state_delta(first, last, "connection"),
        },
    }


def _average_state_delta(items: list[dict[str, Any]]) -> dict[str, float]:
    if not items:
        return {"trust": 0, "stress": 0, "boundary": 0, "boundary_safety": 0, "connection": 0}
    fields = ["trust", "stress", "boundary", "boundary_safety", "connection"]
    return {
        field: round(sum(float(item["delta"].get(field, 0)) for item in items) / len(items), 1)
        for field in fields
    }


def _repair_index(deltas: dict[str, float], avg_score: float) -> int:
    raw = 50 + deltas["trust"] * 1.1 + deltas["connection"] * 1.2 + deltas["boundary_safety"] - deltas["stress"] * 0.8
    raw = (raw * 0.65) + (avg_score * 0.35)
    return int(max(0, min(100, round(raw))))


def _focus_distribution(items: list[dict[str, Any]]) -> list[dict[str, Any]]:
    focus_counts = Counter(str(item.get("next_focus") or "轻验证") for item in items)
    return _counter_items(focus_counts, limit=8)


def _relationship_next_actions(items: list[dict[str, Any]], deltas: dict[str, float], blocked_sessions: int) -> list[dict[str, str]]:
    actions: list[dict[str, str]] = []
    if not items:
        actions.append({"priority": "high", "action": "完成三轮 AI 伴侣训练", "reason": "跨会话趋势需要至少三轮真实轨迹。"})
        return actions
    if blocked_sessions:
        actions.append({"priority": "high", "action": "复盘安全阻断会话", "reason": f"{blocked_sessions} 个会话触发过安全阻断，需练习非控制表达。"})
    if deltas["stress"] > 5 or deltas["boundary"] > 5:
        actions.append({"priority": "high", "action": "降低推进速度", "reason": "跨会话压力或边界压力仍在上升。"})
    if deltas["trust"] < 2 or deltas["connection"] < 2:
        actions.append({"priority": "medium", "action": "强化情绪承接", "reason": "信任和连接增量偏低，优先训练确认感受和轻问句。"})
    if deltas["boundary_safety"] < 2:
        actions.append({"priority": "medium", "action": "增加退路式邀请", "reason": "边界安全感提升不足，需要给选择权和退出空间。"})
    if not actions:
        actions.append({"priority": "low", "action": "进入迁移练习", "reason": "长期趋势稳定，可切换不同依恋风格和高张力场景。"})
    return actions[:4]


def _ai_quality_trend(logs: list[AIRunLog]) -> list[dict[str, Any]]:
    buckets: dict[str, dict[str, int]] = defaultdict(lambda: {
        "runs": 0,
        "success": 0,
        "fallback": 0,
        "blocked": 0,
        "provider_attempts": 0,
    })
    for log in logs:
        day = log.created_at.date().isoformat()
        buckets[day]["runs"] += 1
        if log.outcome in {"success", "success_raw_text"}:
            buckets[day]["success"] += 1
        elif log.outcome != "blocked_safety":
            buckets[day]["fallback"] += 1
        if log.outcome == "blocked_safety":
            buckets[day]["blocked"] += 1
        else:
            buckets[day]["provider_attempts"] += 1
    return [
        {
            "date": day,
            **values,
            "success_rate": _percent(values["success"], values["runs"]),
            "provider_success_rate": _percent(values["success"], values["provider_attempts"]),
            "fallback_rate": _percent(values["fallback"], values["runs"]),
        }
        for day, values in sorted(buckets.items())[-14:]
    ]


def _ai_quality_next_actions(
    total: int,
    success: int,
    blocked: int,
    provider_failures: int,
    fallback_reasons: Counter[str],
    safety_flags: Counter[str],
    provider_attempts: int,
    provider_success_rate: float,
    safety_alternative_coverage: dict[str, Any],
) -> list[dict[str, str]]:
    actions: list[dict[str, str]] = []
    if total == 0:
        return [{"priority": "high", "action": "生成 AI 运行样本", "reason": "当前没有 AI run log，无法评估模型质量趋势。"}]
    if provider_attempts and provider_success_rate < 75:
        actions.append({"priority": "high", "action": "复核 Prompt 与 Provider 稳定性", "reason": "Provider 调用成功率低于 75%。"})
    if provider_failures:
        actions.append({"priority": "high", "action": "排查 Provider 失败", "reason": f"最近 {provider_failures} 次调用进入 provider_failure。"})
    if blocked and not safety_alternative_coverage.get("ready"):
        top = safety_flags.most_common(1)[0][0] if safety_flags else "高风险输入"
        actions.append({
            "priority": "medium",
            "action": "扩充安全替代表达训练",
            "reason": f"安全阻断 {blocked} 次，最高频风险为 {top}；当前替代训练覆盖未达标。",
        })
    provider_fallback_reasons = Counter({
        reason: count
        for reason, count in fallback_reasons.items()
        if "风险" not in reason and "阻断" not in reason
    })
    if provider_fallback_reasons:
        reason = provider_fallback_reasons.most_common(1)[0][0]
        actions.append({"priority": "medium", "action": "收敛降级原因", "reason": f"最高频降级原因：{reason}。"})
    if not actions:
        actions.append({"priority": "low", "action": "保持观察", "reason": "AI 质量指标稳定，继续积累样本和趋势。"})
    return actions[:4]


def _safety_alternative_coverage(session: Session) -> dict[str, Any]:
    required_flags = {"manipulation", "consent_violation", "coercion_or_stalking", "safety_evasion", "crisis_or_violence"}
    published_resources = session.exec(
        select(ResourceLibrary).where(
            ResourceLibrary.source == "project_original:safety_alternative_training_v1",
            ResourceLibrary.review_status == "published",
        )
    ).all()
    published_entries = session.exec(
        select(KnowledgeEntry).where(
            KnowledgeEntry.source == "project_original:safety_alternative_training_v1",
            KnowledgeEntry.review_status == "published",
        )
    ).all()
    resources = session.exec(
        select(ResourceLibrary).where(ResourceLibrary.source == "project_original:safety_alternative_training_v1")
    ).all()
    covered_flags = {
        str(resource.variant_family)
        for resource in resources
        if resource.variant_family in required_flags
    }
    return {
        "ready": len(published_resources) >= 15 and len(published_entries) >= 5 and required_flags.issubset(covered_flags),
        "resource_count": len(published_resources),
        "knowledge_count": len(published_entries),
        "required_flags": sorted(required_flags),
        "covered_flags": sorted(covered_flags),
        "target": {"resources": 15, "knowledge_entries": 5, "risk_flags": len(required_flags)},
    }


def _analytics_center_external_reports(session: Session) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any], dict[str, Any]]:
    evolution: Any = import_module("backend.api.evolution")
    samples: Any = import_module("backend.api.samples")

    gold = _ensure_dict(samples.get_gold_interrater_consistency(session=session))
    conflict_queue = _ensure_dict(samples.get_gold_conflict_queue(limit=5, session=session))
    import_quality = _ensure_dict(evolution.import_quality_report(session=session))
    vector_request = evolution.VectorRecallEvaluationRequest(limit_per_type=2, thresholds=[0.2, 0.35])
    vector = _ensure_dict(evolution.evaluate_vector_index(vector_request, session))
    return gold, conflict_queue, import_quality, vector


def _analytics_center_scheduler_health() -> dict[str, Any]:
    scheduler_module: Any = import_module("backend.core.production_scheduler")
    health = _ensure_dict(scheduler_module.scheduler_health())
    jobs = [
        {
            "id": str(job.get("id") or ""),
            "name": str(job.get("name") or job.get("id") or ""),
            "observed": bool(job.get("observed")),
            "stale": bool(job.get("stale")),
            "required": bool(job.get("required", True)),
            "latest_status": str(job.get("latest_status") or "missing"),
            "latest_run_at": job.get("latest_run_at"),
            "next_action": str(job.get("next_action") or ""),
        }
        for job in health.get("jobs", [])
        if isinstance(job, dict)
    ]
    alerts = [
        {
            "severity": str(alert.get("severity") or "medium"),
            "job_id": str(alert.get("job_id") or ""),
            "reason": str(alert.get("reason") or ""),
            "action": str(alert.get("action") or ""),
        }
        for alert in health.get("alerts", [])
        if isinstance(alert, dict)
    ]
    return {
        "status": str(health.get("status") or "needs_attention"),
        "checked_at": health.get("checked_at"),
        "state_path": health.get("state_path"),
        "jobs": jobs,
        "alerts": alerts,
        "recovery_runbook": health.get("recovery_runbook", []),
        "quality_gate": health.get("quality_gate", {}),
        "principle": "生产调度健康只展示任务状态、摘要、恢复命令和门禁，不暴露敏感原文。",
    }


def _analytics_center_scorecard(
    ai_quality: dict[str, Any],
    provider: dict[str, Any],
    relationship: dict[str, Any],
    gold: dict[str, Any],
    conflict_queue: dict[str, Any],
    import_quality: dict[str, Any],
    vector: dict[str, Any],
    scheduler: dict[str, Any],
) -> list[dict[str, Any]]:
    ai_summary = ai_quality.get("summary", {})
    provider_recent = provider.get("recent", {})
    relationship_summary = relationship.get("summary", {})
    gold_summary = gold.get("summary", {})
    return [
        _scorecard_item("ai_success", "Provider 成功率", float(ai_summary.get("provider_success_rate") or 0), 75, unit="%"),
        _scorecard_item("provider_failure", "Provider 失败率", 100 - float(provider_recent.get("provider_failure_rate") or 0), 75, unit="health"),
        _scorecard_item("gold_conflicts", "Gold 冲突关闭", 100 if int(conflict_queue.get("total") or 0) == 0 else 0, 100, unit="gate"),
        _scorecard_item("gold_agreement", "Gold 一致率", float(gold_summary.get("decision_agreement_rate") or 0) * 100, 80, unit="%"),
        _scorecard_item("import_quality", "导入质量", float(import_quality.get("quality_score") or 0), 85, unit="score"),
        _scorecard_item("vector_recall", "向量召回", float(vector.get("summary", {}).get("top10_recall") or 0) * 100, 80, unit="%"),
        _scorecard_item("repair_index", "训练修复指数", float(relationship_summary.get("repair_index") or 0), 70, unit="score"),
        _scorecard_item("scheduler_health", "调度健康", 100 if scheduler.get("status") == "healthy" else 0, 100, unit="gate"),
    ]


def _scorecard_item(metric_id: str, label: str, value: float, target: float, *, unit: str) -> dict[str, Any]:
    status = "passed" if value >= target else "needs_attention"
    return {
        "id": metric_id,
        "label": label,
        "value": round(value, 1),
        "target": target,
        "unit": unit,
        "status": status,
        "gap": round(max(0, target - value), 1),
    }


def _analytics_center_alerts(
    scorecard: list[dict[str, Any]],
    ai_failures: dict[str, Any],
    import_quality: dict[str, Any],
    scheduler: dict[str, Any],
) -> list[dict[str, Any]]:
    alerts: list[dict[str, Any]] = []
    for item in scorecard:
        if item["status"] == "needs_attention":
            alerts.append({
                "priority": "high" if item["id"] in {"ai_success", "provider_failure", "gold_conflicts"} else "medium",
                "metric": item["id"],
                "title": f"{item['label']} 未达标",
                "detail": f"当前 {item['value']}，目标 {item['target']}，差距 {item['gap']}。",
            })
    for cluster in ai_failures.get("clusters", [])[:3]:
        alerts.append({
            "priority": cluster.get("severity", "medium"),
            "metric": str(cluster.get("id", "ai_failure")),
            "title": "AI 失败簇",
            "detail": str(cluster.get("recommendation", "")),
        })
    debt = import_quality.get("quality_debt", {})
    if isinstance(debt, dict) and int(debt.get("manual_review_issues") or 0) > 0:
        alerts.append({
            "priority": "medium",
            "metric": "manual_import_debt",
            "title": "历史导入 issue 仍需人工治理",
            "detail": f"{debt.get('manual_review_issues')} 条来源/历史问题待复核。",
        })
    for alert in scheduler.get("alerts", [])[:3]:
        alerts.append({
            "priority": str(alert.get("severity") or "medium"),
            "metric": f"scheduler:{alert.get('job_id') or 'unknown'}",
            "title": "生产调度健康告警",
            "detail": f"{alert.get('reason', '')}；建议：{alert.get('action', '')}",
        })
    return alerts[:10]


def _analytics_center_timeline(
    ai_quality: dict[str, Any],
    relationship: dict[str, Any],
    gold: dict[str, Any],
    import_quality: dict[str, Any],
    vector: dict[str, Any],
    scheduler: dict[str, Any],
) -> list[dict[str, Any]]:
    items = [
        {
            "id": "scheduler_health",
            "label": "生产调度",
            "value": 100 if scheduler.get("status") == "healthy" else 0,
            "status": "passed" if scheduler.get("status") == "healthy" else "needs_attention",
        },
        {
            "id": "gold_set",
            "label": "Gold Set 校准",
            "value": gold.get("summary", {}).get("decision_agreement_rate"),
            "status": "passed" if gold.get("quality_gates", {}).get("ready_for_multi_reviewer_calibration") else "needs_attention",
        },
        {
            "id": "import_quality",
            "label": "导入质量",
            "value": import_quality.get("quality_score"),
            "status": "passed" if float(import_quality.get("quality_score") or 0) >= 85 else "needs_attention",
        },
        {
            "id": "vector_recall",
            "label": "向量召回",
            "value": vector.get("summary", {}).get("top10_recall"),
            "status": "passed" if float(vector.get("summary", {}).get("top10_recall") or 0) >= 0.8 else "needs_attention",
        },
        {
            "id": "training_repair",
            "label": "训练修复",
            "value": relationship.get("summary", {}).get("repair_index"),
            "status": "passed" if float(relationship.get("summary", {}).get("repair_index") or 0) >= 70 else "needs_attention",
        },
    ]
    for point in ai_quality.get("trend", [])[-6:]:
        items.append({
            "id": f"ai:{point.get('date')}",
            "label": f"AI {point.get('date')}",
            "value": point.get("provider_success_rate"),
            "status": "passed" if float(point.get("provider_success_rate") or 0) >= 75 else "needs_attention",
        })
    return items[-12:]


def _ai_failure_clusters(
    provider_failures: list[AIRunLog],
    safety_blocks: list[AIRunLog],
    fallback_reasons: Counter[str],
    by_task: Counter[str],
    by_provider: Counter[str],
    by_model: Counter[str],
    flags: Counter[str],
    safety_alternative_coverage: dict[str, Any],
) -> list[dict[str, Any]]:
    clusters: list[dict[str, Any]] = []
    if provider_failures:
        clusters.append({
            "id": "provider_failure",
            "severity": "high",
            "count": len(provider_failures),
            "top_provider": by_provider.most_common(1)[0][0] if by_provider else "unknown",
            "top_model": by_model.most_common(1)[0][0] if by_model else "unknown",
            "top_reason": _top_counter_name(fallback_reasons),
            "recommendation": "检查 Provider 配置、超时、响应 schema 与降级路径，必要时降低外部调用依赖。",
        })
    if safety_blocks and not safety_alternative_coverage.get("ready"):
        clusters.append({
            "id": "safety_blocked",
            "severity": "high" if len(safety_blocks) >= 5 else "medium",
            "count": len(safety_blocks),
            "top_flag": _top_counter_name(flags),
            "top_task": _top_counter_name(by_task),
            "recommendation": "扩充安全替代表达和红队样例，确保阻断后仍给出非操控、尊重边界的训练路径。",
        })
    for reason, count in fallback_reasons.most_common(5):
        if reason == "unknown":
            continue
        clusters.append({
            "id": f"fallback:{reason}",
            "severity": "medium",
            "count": count,
            "reason": reason,
            "recommendation": "把高频 fallback reason 收敛成可测试场景，并补 provider/orchestrator 回归断言。",
        })
    return clusters[:8]


def _ai_failure_next_actions(clusters: list[dict[str, Any]]) -> list[dict[str, str]]:
    if not clusters:
        return [{"priority": "low", "action": "保持观察", "reason": "最近 AI 运行未形成失败簇。"}]
    actions: list[dict[str, str]] = []
    for cluster in clusters[:4]:
        priority = "high" if cluster.get("severity") == "high" else "medium"
        actions.append({
            "priority": priority,
            "action": f"处理 {cluster['id']}",
            "reason": f"{cluster.get('count', 0)} 次命中；{cluster.get('recommendation', '')}",
        })
    return actions


def _provider_success_task_matrix(logs: list[AIRunLog]) -> list[dict[str, Any]]:
    buckets: dict[str, dict[str, Any]] = defaultdict(lambda: {
        "runs": 0,
        "success": 0,
        "success_raw_text": 0,
        "provider_failure": 0,
        "blocked_safety": 0,
        "response_keys": Counter(),
        "fallback_reasons": Counter(),
    })
    for log in logs:
        bucket = buckets[log.task_type]
        bucket["runs"] += 1
        bucket[log.outcome] = int(bucket.get(log.outcome, 0)) + 1
        for key in _response_summary_keys(log):
            bucket["response_keys"][key] += 1
        if log.fallback_reason:
            bucket["fallback_reasons"][log.fallback_reason] += 1
    rows = []
    for task_type, bucket in buckets.items():
        runs = int(bucket["runs"])
        rows.append({
            "task_type": task_type,
            "runs": runs,
            "structured_success_rate": _percent(int(bucket["success"]), runs),
            "raw_text_rate": _percent(int(bucket["success_raw_text"]), runs),
            "provider_failure_rate": _percent(int(bucket["provider_failure"]), runs),
            "safety_block_rate": _percent(int(bucket["blocked_safety"]), runs),
            "top_response_keys": _counter_items(bucket["response_keys"], limit=8),
            "top_fallback_reasons": _counter_items(bucket["fallback_reasons"], limit=5),
        })
    return sorted(rows, key=lambda item: (-_safe_int(item.get("runs")), str(item["task_type"])))[:12]


def _provider_success_contract_gaps(logs: list[AIRunLog], fallback_reasons: Counter[str]) -> list[dict[str, Any]]:
    gaps: list[dict[str, Any]] = []
    raw_text_logs = [log for log in logs if log.outcome == "success_raw_text"]
    if raw_text_logs:
        keys = Counter(key for log in raw_text_logs for key in _response_summary_keys(log))
        gaps.append({
            "id": "raw_text_contract_gap",
            "severity": "medium" if len(raw_text_logs) < 5 else "high",
            "count": len(raw_text_logs),
            "evidence": _counter_items(keys, limit=6),
            "fix": "继续扩大 JSON 提取和字段归一化回归，确认 raw_text 是否已能恢复为结构化对象。",
        })
    missing_reply = sum(count for reason, count in fallback_reasons.items() if "缺少 reply" in reason or "missing reply" in reason.lower())
    if missing_reply:
        gaps.append({
            "id": "missing_reply_alias_gap",
            "severity": "high",
            "count": missing_reply,
            "fix": "扩充 reply 字段别名、provider prompt schema 和 partner response normalization 测试。",
        })
    http_400 = sum(count for reason, count in fallback_reasons.items() if "400" in reason)
    if http_400:
        gaps.append({
            "id": "http_400_external_or_shape_gap",
            "severity": "high",
            "count": http_400,
            "fix": "若本地 request_shape 已通过，进入受控 live probe 排查账号区域/模型授权；否则先修 mode/base_url/chat_path/model。",
        })
    if not gaps:
        gaps.append({
            "id": "no_dominant_contract_gap",
            "severity": "low",
            "count": 0,
            "fix": "继续积累真实调用样本，并保持 fallback 可用。",
        })
    return gaps[:6]


def _provider_success_contract_next_actions(
    total: int,
    outcomes: Counter[str],
    fallback_reasons: Counter[str],
    gaps: list[dict[str, Any]],
) -> list[dict[str, str]]:
    if total == 0:
        return [{"priority": "high", "action": "生成真实 AI run log", "reason": "当前没有 provider 运行样本，无法评估成功契约。"}]
    actions: list[dict[str, str]] = []
    if outcomes.get("success_raw_text", 0):
        actions.append({"priority": "high", "action": "复核 raw_text 样本形态", "reason": "仍有 provider 返回文本成功但未进入结构化 success。"})
    if any("缺少 reply" in reason for reason in fallback_reasons):
        actions.append({"priority": "high", "action": "扩充 reply 字段兼容", "reason": "近期仍有缺 reply 降级，继续固化 provider response alias。"})
    if outcomes.get("provider_failure", 0):
        actions.append({"priority": "high", "action": "排查 provider_failure", "reason": f"{outcomes.get('provider_failure', 0)} 次 provider_failure 仍需诊断。"})
    for gap in gaps:
        if gap["id"] == "no_dominant_contract_gap":
            continue
        actions.append({"priority": str(gap["severity"]), "action": f"处理 {gap['id']}", "reason": str(gap["fix"])})
    if not actions:
        actions.append({"priority": "low", "action": "保持成功契约观测", "reason": "当前没有明显 provider 成功契约缺口。"})
    return actions[:4]


def _response_summary_keys(log: AIRunLog) -> list[str]:
    summary = _loads_json_dict(log.response_summary_json)
    keys = summary.get("keys")
    if not isinstance(keys, list):
        return []
    return [str(key) for key in keys if str(key)]


def _provider_diagnostic_items(
    failure_reasons: Counter[str],
    http_statuses: Counter[str],
    configured: bool,
    provider: str,
    mode: str,
    model: str,
    base_url: str,
    chat_path: str,
) -> list[dict[str, str]]:
    items: list[dict[str, str]] = []
    for check in _provider_config_compatibility(provider, mode, model, base_url, chat_path):
        if check["status"] != "passed":
            items.append(check)
    if not configured:
        items.append({"status": "needs_attention", "check": "api_key", "detail": f"{_provider_api_key_env_name()} is not configured."})
    if http_statuses.get("400"):
        items.append({
            "status": "needs_attention",
            "check": "http_400",
            "detail": "HTTP 400 usually points to endpoint, mode, model, request schema, or account capability mismatch.",
        })
    items.extend(_provider_status_diagnostic_items(http_statuses))
    request_shape = _provider_request_shape()
    if request_shape.get("compatibility_risks"):
        items.append({
            "status": "needs_attention",
            "check": "request_shape",
            "detail": ", ".join(str(item) for item in request_shape["compatibility_risks"]),
        })
    top_reason = _top_counter_name(failure_reasons)
    if top_reason != "unknown":
        items.append({"status": "observed", "check": "top_fallback_reason", "detail": top_reason})
    if not items:
        items.append({"status": "passed", "check": "provider_failure_pattern", "detail": "No dominant provider failure pattern in recent logs."})
    return items


def _provider_next_actions(
    failure_reasons: Counter[str],
    http_statuses: Counter[str],
    configured: bool,
    provider: str,
    mode: str,
    model: str,
    base_url: str,
    chat_path: str,
) -> list[dict[str, str]]:
    actions: list[dict[str, str]] = []
    compatibility = _provider_config_compatibility(provider, mode, model, base_url, chat_path)
    if any(item["status"] != "passed" for item in compatibility):
        actions.append({
            "priority": "high",
            "action": "修正 Provider 配置兼容性",
            "reason": "Provider mode、base_url、chat_path 或 model 与 OpenAI-compatible/native 约定不一致。",
        })
    if not configured:
        actions.append({"priority": "high", "action": f"配置 {_provider_api_key_env_name()}", "reason": "Provider 未配置时所有外部 AI 调用都会降级。"})
    if http_statuses.get("400"):
        request_shape = _provider_request_shape()
        has_local_risk = any(item["status"] != "passed" for item in compatibility) or bool(request_shape.get("compatibility_risks"))
        if has_local_risk:
            actions.append({
                "priority": "high",
                "action": "核对 Provider mode/base_url/chat_path/model",
                "reason": "HTTP 400 高频出现，且本地配置或请求形态仍有兼容风险。",
            })
        else:
            actions.append({
                "priority": "high",
                "action": "验证账号区域、模型授权和服务侧约束",
                "reason": "HTTP 400 高频出现，但本地请求形态已通过兼容性检查，应通过受控 live probe 排查外部授权/区域问题。",
            })
        actions.append({
            "priority": "medium",
            "action": "为 provider_failure:400 固化回归样例",
            "reason": "把高频失败收敛为可测试配置诊断，避免静默降级。",
        })
    actions.extend(_provider_status_next_actions(http_statuses))
    request_shape = _provider_request_shape()
    if request_shape.get("compatibility_risks"):
        actions.append({
            "priority": "high",
            "action": "修正 Provider 请求 schema",
            "reason": f"请求形态存在 {len(request_shape['compatibility_risks'])} 个可诊断风险。",
        })
    if failure_reasons and not actions:
        actions.append({"priority": "medium", "action": "复核 Provider fallback reason", "reason": _top_counter_name(failure_reasons)})
    if not actions:
        actions.append({"priority": "low", "action": "保持 Provider 观测", "reason": "最近日志没有形成高风险 Provider 失败模式。"})
    return actions[:4]


def _provider_failure_playbook(
    failure_reasons: Counter[str],
    http_statuses: Counter[str],
    configured: bool,
    request_shape: dict[str, Any],
    compatibility: list[dict[str, str]],
) -> dict[str, Any]:
    """Turn provider failures into an auditable, non-secret remediation matrix."""
    compatibility_risks = [
        str(item.get("check") or "provider_compatibility")
        for item in compatibility
        if item.get("status") != "passed"
    ]
    request_risks = [str(item) for item in request_shape.get("compatibility_risks", []) if item]
    matrix: list[dict[str, Any]] = []
    if not configured:
        matrix.append(_provider_failure_case(
            "missing_api_key",
            "high",
            "Provider 凭证缺失",
            f"配置 {_provider_api_key_env_name()}，并先运行 dry-run 探针确认只写入脱敏审计。",
            "dry_run_probe",
        ))
    if compatibility_risks or request_risks:
        matrix.append(_provider_failure_case(
            "local_request_shape",
            "high",
            "本地 mode/base_url/chat_path/model 或请求 schema 存在兼容风险",
            "修正兼容性检查中列出的配置项，再运行 provider diagnostics 回归。",
            "request_shape_regression",
            evidence=compatibility_risks + request_risks,
        ))
    if http_statuses.get("400") and not compatibility_risks and not request_risks:
        matrix.append(_provider_failure_case(
            "account_or_service_http_400",
            "high",
            "本地请求形态无明显风险，HTTP 400 更可能来自账号区域、模型授权、服务侧参数约束或供应商策略",
            "保持 fallback 生效；用受控 live probe 验证账号/模型授权，不保存请求正文或响应体。",
            "controlled_live_probe",
            evidence=["http_status=400", "request_shape_compatibility=passed"],
        ))
    matrix.extend(_provider_status_failure_cases(http_statuses))
    if any("timeout" in reason.lower() for reason in failure_reasons):
        matrix.append(_provider_failure_case(
            "timeout",
            "medium",
            "Provider 超时或网络链路不稳定",
            "保留降级路径，审查 timeout 设置与重试策略，只记录错误类别和延迟。",
            "timeout_fallback_regression",
        ))
    if any("network" in reason.lower() or "网络" in reason for reason in failure_reasons):
        matrix.append(_provider_failure_case(
            "network_error",
            "medium",
            "网络错误或供应商连接异常",
            "确认本地网络与供应商连通性，保持安全 fallback，不记录响应原文。",
            "network_fallback_regression",
        ))
    if not matrix and failure_reasons:
        matrix.append(_provider_failure_case(
            "unknown_provider_failure",
            "medium",
            "Provider 失败已出现但未命中特定根因",
            "把最高频 fallback reason 固化为测试样例，并补充诊断分类。",
            "fallback_reason_regression",
            evidence=[_top_counter_name(failure_reasons)],
        ))
    if not matrix:
        matrix.append(_provider_failure_case(
            "no_dominant_failure",
            "low",
            "近期未形成主导 Provider 失败模式",
            "继续观测成功率、失败率、延迟和 fallback reason。",
            "quality_observation",
        ))
    return {
        "risk_level": "high" if any(item["severity"] == "high" for item in matrix) else "medium" if any(item["severity"] == "medium" for item in matrix) else "low",
        "dominant_failure_reason": _top_counter_name(failure_reasons),
        "http_statuses": _counter_items(http_statuses, limit=6),
        "root_cause_matrix": matrix[:6],
        "regression_cases": [
            {
                "id": item["regression_case"],
                "assertion": _provider_regression_assertion(str(item["id"])),
            }
            for item in matrix[:6]
        ],
        "runbook": [
            {
                "step": "1",
                "title": "Confirm local request shape",
                "command": "GET /api/analytics/ai-provider-diagnostics",
            },
            {
                "step": "2",
                "title": "Keep safe fallback active",
                "command": "verify outcome=provider_failure falls back without saving prompt or response body",
            },
            {
                "step": "3",
                "title": "Run dry-run probe before any live call",
                "command": "POST /api/analytics/ai-provider-probe?dry_run=true",
            },
            {
                "step": "4",
                "title": "Only with explicit authorization, run minimal live probe",
                "command": f"{_provider_live_probe_env_name()}=true POST /api/analytics/ai-provider-probe?dry_run=false",
            },
        ],
        "quality_gate": {
            "request_shape_has_known_risks": bool(compatibility_risks or request_risks),
            "http_400_without_local_shape_risk": bool(http_statuses.get("400") and not compatibility_risks and not request_risks),
            "auth_or_permission_error": bool(http_statuses.get("401") or http_statuses.get("403")),
            "endpoint_or_model_not_found": bool(http_statuses.get("404")),
            "rate_limit_or_quota": bool(http_statuses.get("429")),
            "fallback_required_until_live_probe_passes": bool(matrix and matrix[0]["id"] != "no_dominant_failure"),
            "stores_prompt_or_response_text": False,
            "stores_api_key": False,
        },
        "principle": "Provider 失败处置矩阵只返回聚合根因、回归样例和安全 runbook；不返回 prompt、响应体、API key 或 URL query secret。",
    }


def _provider_failure_case(
    case_id: str,
    severity: str,
    root_cause: str,
    action: str,
    regression_case: str,
    *,
    evidence: list[str] | None = None,
) -> dict[str, Any]:
    return {
        "id": case_id,
        "severity": severity,
        "root_cause": root_cause,
        "evidence": evidence or [],
        "operator_action": action,
        "regression_case": regression_case,
    }


def _provider_status_diagnostic_items(http_statuses: Counter[str]) -> list[dict[str, str]]:
    items: list[dict[str, str]] = []
    for status in ("401", "403", "404", "429"):
        if http_statuses.get(status):
            items.append({
                "status": "needs_attention",
                "check": f"http_{status}",
                "detail": _provider_http_status_detail(status),
            })
    if any(int(status) >= 500 for status in http_statuses if status.isdigit()):
        items.append({
            "status": "needs_attention",
            "check": "http_5xx",
            "detail": "Provider returned 5xx errors; keep fallback active and retry only through controlled probes.",
        })
    return items


def _provider_status_next_actions(http_statuses: Counter[str]) -> list[dict[str, str]]:
    actions: list[dict[str, str]] = []
    if http_statuses.get("401") or http_statuses.get("403"):
        actions.append({
            "priority": "high",
            "action": "验证 Provider 凭证、账号区域和模型授权",
            "reason": "HTTP 401/403 指向鉴权或授权问题，本地 fallback 必须保持可用。",
        })
    if http_statuses.get("404"):
        actions.append({
            "priority": "high",
            "action": "核对 Provider endpoint 与模型名称",
            "reason": "HTTP 404 更可能是路径、区域域名或模型名称不可用。",
        })
    if http_statuses.get("429"):
        actions.append({
            "priority": "medium",
            "action": "降低外部调用频率并保持本地降级",
            "reason": "HTTP 429 表示限流或配额不足，应避免重试风暴。",
        })
    return actions


def _provider_status_failure_cases(http_statuses: Counter[str]) -> list[dict[str, Any]]:
    cases: list[dict[str, Any]] = []
    if http_statuses.get("401") or http_statuses.get("403"):
        cases.append(_provider_failure_case(
            "auth_or_model_permission",
            "high",
            "Provider 返回鉴权或授权错误，常见原因是 API key 无效、账号区域不匹配或模型未授权",
            "检查 API key、账号区域、模型授权和供应商控制台；保持本地 fallback，不记录请求正文或响应体。",
            "auth_permission_regression",
            evidence=_provider_status_evidence(http_statuses, ("401", "403")),
        ))
    if http_statuses.get("404"):
        cases.append(_provider_failure_case(
            "endpoint_or_model_not_found",
            "high",
            "Provider 返回 404，常见原因是 endpoint、区域域名、chat_path 或模型名称不可用",
            "核对 base_url、chat_path 和 model；先用 dry-run request_shape 回归，再用受控 live probe 验证。",
            "endpoint_model_regression",
            evidence=["http_status=404"],
        ))
    if http_statuses.get("429"):
        cases.append(_provider_failure_case(
            "rate_limit_or_quota",
            "medium",
            "Provider 返回限流或配额不足",
            "降低外部调用频率，保留安全 fallback，并把配额状态纳入运营告警。",
            "rate_limit_fallback_regression",
            evidence=["http_status=429"],
        ))
    server_statuses = [status for status in http_statuses if status.isdigit() and int(status) >= 500]
    if server_statuses:
        cases.append(_provider_failure_case(
            "provider_server_error",
            "medium",
            "Provider 服务端错误或临时不可用",
            "保持 fallback，避免保存响应体；只记录状态码、延迟和错误类别。",
            "provider_5xx_fallback_regression",
            evidence=[f"http_status={status}" for status in server_statuses[:3]],
        ))
    return cases


def _provider_local_remediation(provider: str, mode: str) -> dict[str, Any]:
    deepseek_optional_retry = provider == "deepseek" and mode == "openai"
    return {
        "deepseek_400_optional_param_retry": deepseek_optional_retry,
        "detail": (
            "DeepSeek OpenAI-compatible calls retry HTTP 400 once without optional reasoning_effort/thinking params."
            if deepseek_optional_retry
            else "No provider-specific local compatibility retry is active."
        ),
        "safety_hard_blocks_preserved": True,
    }


def _provider_regression_assertion(case_id: str) -> str:
    assertions = {
        "missing_api_key": "diagnostics risk_level=high and live probe remains blocked without API key",
        "local_request_shape": "compatibility risks appear in diagnostics and live probe readiness blockers",
        "account_or_service_http_400": "HTTP 400 is classified as account/service risk when request_shape compatibility passes",
        "auth_or_model_permission": "HTTP 401/403 is classified as credential, region, or model permission risk",
        "endpoint_or_model_not_found": "HTTP 404 is classified as endpoint, region domain, or model-name risk",
        "rate_limit_or_quota": "HTTP 429 keeps fallback active and avoids retry storms",
        "provider_server_error": "HTTP 5xx failures return fallback without storing response body",
        "timeout": "timeout failures return fallback without storing prompt or response body",
        "network_error": "network failures return fallback without storing prompt or response body",
        "unknown_provider_failure": "fallback reason is aggregated without leaking payload summaries",
        "no_dominant_failure": "provider diagnostics reports low risk when no dominant failures exist",
    }
    return assertions.get(case_id, "provider failure remains aggregated and redacted")


def _provider_config_compatibility(
    provider: str,
    mode: str,
    model: str,
    base_url: str,
    chat_path: str,
) -> list[dict[str, str]]:
    checks: list[dict[str, str]] = []
    normalized_url = (base_url or "").rstrip("/")
    normalized_path = chat_path if chat_path.startswith("/") else f"/{chat_path}" if chat_path else ""
    if provider == "deepseek":
        if mode != "openai":
            checks.append({
                "status": "needs_attention",
                "check": "deepseek_api_mode",
                "detail": "DeepSeek should use the OpenAI-compatible chat completions API mode.",
            })
        if normalized_url != "https://api.deepseek.com":
            checks.append({
                "status": "needs_attention",
                "check": "deepseek_base_url",
                "detail": "DeepSeek OpenAI-compatible requests should use https://api.deepseek.com.",
            })
        if normalized_path != "/chat/completions":
            checks.append({
                "status": "needs_attention",
                "check": "deepseek_chat_path",
                "detail": "DeepSeek chat requests should use /chat/completions.",
            })
        if model.strip().lower() in {"deepseek-chat", "deepseek-reasoner"}:
            checks.append({
                "status": "needs_attention",
                "check": "deepseek_deprecated_model",
                "detail": "Use deepseek-v4-flash or deepseek-v4-pro; deepseek-chat and deepseek-reasoner are scheduled for deprecation.",
            })
    if not checks:
        checks.append({"status": "passed", "check": "provider_config_shape", "detail": "Provider mode, endpoint path, and model naming are internally consistent."})
    return checks


def _provider_http_status_detail(status: str) -> str:
    details = {
        "401": "HTTP 401 points to invalid or missing credentials.",
        "403": "HTTP 403 points to account region, permission, or model authorization constraints.",
        "404": "HTTP 404 points to endpoint, region domain, chat path, or model-name mismatch.",
        "429": "HTTP 429 points to rate limit or quota exhaustion.",
    }
    return details.get(status, f"HTTP {status} needs provider-specific investigation.")


def _provider_status_evidence(http_statuses: Counter[str], statuses: tuple[str, ...]) -> list[str]:
    return [f"http_status={status}" for status in statuses if http_statuses.get(status)]


def _safe_int(value: Any) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return 0


def _provider_request_shape() -> dict[str, Any]:
    diagnostics = ai_provider_client.request_diagnostics()
    return {
        "provider": diagnostics.provider,
        "mode": diagnostics.mode,
        "url": diagnostics.url,
        "path": diagnostics.path,
        "model": diagnostics.model,
        "payload_keys": diagnostics.payload_keys,
        "message_roles": diagnostics.message_roles,
        "message_count": diagnostics.message_count,
        "content_chars": diagnostics.content_chars,
        "schema_hash": diagnostics.schema_hash,
        "compatibility_risks": diagnostics.compatibility_risks,
    }


def _provider_probe_readiness(session: Session) -> dict[str, Any]:
    diagnostics = get_ai_provider_diagnostics(limit=120, session=session)
    provider = _ensure_dict(diagnostics.get("provider"))
    request_shape = _ensure_dict(diagnostics.get("request_shape"))
    recent_logs = list(session.exec(select(AIProviderProbeLog).order_by(desc(AIProviderProbeLog.created_at)).limit(8)).all())
    blockers = _provider_probe_blockers(provider, request_shape)
    status = "ready_for_live_probe" if not blockers else "blocked"
    if not bool(provider.get("configured")):
        status = "not_configured"
    elif not ai_provider_client.live_probe_enabled:
        status = "policy_blocked"
    return {
        "status": status,
        "live_probe_enabled": ai_provider_client.live_probe_enabled,
        "configured": bool(provider.get("configured")),
        "request_shape": request_shape,
        "blockers": blockers,
        "runbook": _provider_probe_runbook(status, blockers),
        "recent_probe_logs": [_probe_log_to_dict(log) for log in recent_logs],
        "quality_gate": {
            "dry_run_required_first": True,
            "explicit_live_enable_required": True,
            "stores_prompt_or_response_text": False,
            "stores_api_key": False,
            "stores_url_query_secret": False,
        },
        "principle": "Provider live probe readiness never performs an external call; it only reports redacted prerequisites, blockers, and safe run steps.",
    }


def _provider_probe_blockers(provider: dict[str, Any], request_shape: dict[str, Any]) -> list[dict[str, str]]:
    blockers: list[dict[str, str]] = []
    if not bool(provider.get("configured")):
        blockers.append({"id": "missing_api_key", "severity": "high", "detail": f"{_provider_api_key_env_name()} is not configured."})
    if not ai_provider_client.live_probe_enabled:
        blockers.append({
            "id": "live_probe_disabled",
            "severity": "high",
            "detail": f"Set {_provider_live_probe_env_name()}=true only in a controlled environment before non-dry-run probing.",
        })
    compatibility = provider.get("compatibility")
    if isinstance(compatibility, list):
        for item in compatibility:
            if isinstance(item, dict) and item.get("status") != "passed":
                blockers.append({
                    "id": str(item.get("check") or "provider_compatibility"),
                    "severity": "high",
                    "detail": str(item.get("detail") or "Provider compatibility check needs attention."),
                })
    risks = request_shape.get("compatibility_risks")
    if isinstance(risks, list):
        for risk in risks:
            blockers.append({"id": str(risk), "severity": "medium", "detail": "Request shape risk must be resolved before live probing."})
    return blockers


def _provider_probe_runbook(status: str, blockers: list[dict[str, str]]) -> list[dict[str, str]]:
    steps = [
        {
            "step": "1",
            "title": "Run dry-run probe",
            "command": "POST /api/analytics/ai-provider-probe?dry_run=true",
            "expected": "outcome=planned and a redacted ai_provider_probe_logs row is written.",
        },
        {
            "step": "2",
            "title": "Resolve readiness blockers",
            "command": "GET /api/analytics/ai-provider-probe-readiness",
            "expected": "status becomes ready_for_live_probe with no compatibility blockers.",
        },
        {
            "step": "3",
            "title": "Enable live probe explicitly",
            "command": f"{_provider_live_probe_env_name()}=true",
            "expected": "live probes are allowed only for this controlled environment.",
        },
        {
            "step": "4",
            "title": "Run minimal live probe",
            "command": "POST /api/analytics/ai-provider-probe?dry_run=false",
            "expected": "stores status/error class and latency only; no prompt, response body, API key, or URL query secret.",
        },
    ]
    if status != "ready_for_live_probe":
        steps.append({
            "step": "gate",
            "title": "Do not call provider yet",
            "command": "keep dry_run=true",
            "expected": f"{len(blockers)} blocker(s) remain; live probe must stay blocked.",
        })
    return steps


def _probe_log_to_dict(log: AIProviderProbeLog) -> dict[str, Any]:
    request_shape = _loads_json_dict(log.request_shape_json)
    return {
        "id": log.id,
        "provider": log.provider,
        "mode": log.mode,
        "model": log.model,
        "dry_run": log.dry_run,
        "outcome": log.outcome,
        "http_status": log.http_status,
        "error_type": log.error_type,
        "latency_ms": log.latency_ms,
        "schema_hash": request_shape.get("schema_hash"),
        "created_at": log.created_at.isoformat(),
    }


def _audit_center_events(session: Session, limit: int, module: str | None) -> list[dict[str, Any]]:
    per_source_limit = max(20, limit)
    events: list[dict[str, Any]] = []
    pipeline_logs = list(session.exec(
        select(PipelineRunLog).order_by(desc(PipelineRunLog.created_at)).limit(per_source_limit)
    ).all())
    ai_logs = list(session.exec(select(AIRunLog).order_by(desc(AIRunLog.created_at)).limit(per_source_limit)).all())
    probe_logs = list(session.exec(
        select(AIProviderProbeLog).order_by(desc(AIProviderProbeLog.created_at)).limit(per_source_limit)
    ).all())
    runtime_logs = list(session.exec(
        select(RuntimeEvent).order_by(desc(RuntimeEvent.created_at)).limit(per_source_limit)
    ).all())
    events.extend(_pipeline_log_audit_event(log) for log in pipeline_logs)
    events.extend(_ai_run_audit_event(log) for log in ai_logs)
    events.extend(_probe_log_audit_event(log) for log in probe_logs)
    events.extend(_runtime_event_audit_event(log) for log in runtime_logs)
    events.extend(_scheduler_audit_events())
    if module and module != "all":
        events = [event for event in events if event["module"] == module]
    events.sort(key=lambda event: str(event["created_at"]), reverse=True)
    return events[:limit]


def _pipeline_log_audit_event(log: PipelineRunLog) -> dict[str, Any]:
    result = _loads_json_dict(log.result_json)
    module = _pipeline_module(log)
    status = _audit_status_from_pipeline(log)
    return {
        "id": f"pipeline:{log.id}",
        "module": module,
        "source": "pipeline_run_logs",
        "action": log.action,
        "status": status,
        "severity": _audit_severity(status, result),
        "target": {"type": log.target_type, "id": log.target_id},
        "summary": _pipeline_audit_summary(log, result),
        "created_at": log.created_at.isoformat(),
        "actor": _safe_text(result.get("reviewer_id")) or _safe_text(result.get("operator")) or "system",
        "details": {
            "from_status": log.from_status,
            "to_status": log.to_status,
            "reviewer_id": _safe_text(result.get("reviewer_id")),
            "resolution_hash": _audit_digest(result.get("resolution_hash")),
            "affected_count": result.get("affected_count") or result.get("issue_count"),
            "quality_gate": result.get("quality_gate"),
            "safety_flags": _audit_safety_flags(result),
        },
    }


def _ai_run_audit_event(log: AIRunLog) -> dict[str, Any]:
    status = {
        "success": "passed",
        "success_raw_text": "passed",
        "blocked_safety": "blocked",
        "provider_failure": "failed",
    }.get(log.outcome, "needs_attention")
    return {
        "id": f"ai_run:{log.id}",
        "module": "ai",
        "source": "ai_run_logs",
        "action": log.task_type,
        "status": status,
        "severity": _audit_severity(status, {"safety_risk_level": log.safety_risk_level}),
        "target": {"type": "ai_run", "id": log.id},
        "summary": log.fallback_reason or log.outcome,
        "created_at": log.created_at.isoformat(),
        "actor": "ai-orchestrator",
        "details": {
            "provider": log.provider,
            "model": log.model,
            "outcome": log.outcome,
            "prompt_id": log.prompt_id,
            "prompt_version": log.prompt_version,
            "schema_version": log.schema_version,
            "payload_hash": _audit_digest(log.payload_hash),
            "safety_risk_level": log.safety_risk_level,
            "safety_flags": _loads_json_list(log.safety_flags_json),
            "latency_ms": log.latency_ms,
        },
    }


def _probe_log_audit_event(log: AIProviderProbeLog) -> dict[str, Any]:
    request_shape = _loads_json_dict(log.request_shape_json)
    status = "planned" if log.outcome == "planned" else "passed" if log.outcome == "success" else "blocked" if log.outcome == "blocked_by_policy" else "failed"
    return {
        "id": f"provider_probe:{log.id}",
        "module": "provider",
        "source": "ai_provider_probe_logs",
        "action": "provider_probe",
        "status": status,
        "severity": _audit_severity(status, {}),
        "target": {"type": "provider_probe", "id": log.id},
        "summary": log.error_type or log.outcome,
        "created_at": log.created_at.isoformat(),
        "actor": "analytics-probe",
        "details": {
            "provider": log.provider,
            "mode": log.mode,
            "model": log.model,
            "dry_run": log.dry_run,
            "http_status": log.http_status,
            "error_type": log.error_type,
            "schema_hash": _audit_digest(request_shape.get("schema_hash")),
            "latency_ms": log.latency_ms,
        },
    }


def _runtime_event_audit_event(log: RuntimeEvent) -> dict[str, Any]:
    status = "failed" if log.severity in {"high", "critical"} else "needs_attention"
    return {
        "id": f"runtime:{log.id}",
        "module": "runtime",
        "source": "runtime_events",
        "action": log.event_type,
        "status": status,
        "severity": log.severity,
        "target": {"type": "runtime_event", "id": log.id},
        "summary": _message_preview(log.message_preview or log.event_type),
        "created_at": log.created_at.isoformat(),
        "actor": log.source,
        "details": {
            "route": log.route,
            "method": log.method,
            "endpoint": log.endpoint,
            "http_status": log.http_status,
            "message_hash": log.message_hash,
            "context": _loads_json_dict(log.context_json),
        },
    }


def _scheduler_audit_events() -> list[dict[str, Any]]:
    scheduler = _analytics_center_scheduler_health()
    checked_at = scheduler.get("checked_at")
    events: list[dict[str, Any]] = []
    for job in scheduler.get("jobs", []):
        if not isinstance(job, dict):
            continue
        status = "passed"
        if not bool(job.get("observed")):
            status = "needs_attention"
        if bool(job.get("stale")) or str(job.get("latest_status")) in {"failed", "needs_attention"}:
            status = "failed"
        events.append({
            "id": f"scheduler:{job.get('id')}",
            "module": "scheduler",
            "source": "production_scheduler_state",
            "action": str(job.get("id") or "scheduler_job"),
            "status": status,
            "severity": _audit_severity(status, {}),
            "target": {"type": "scheduler_job", "id": job.get("id")},
            "summary": str(job.get("next_action") or job.get("latest_status") or "scheduler health observed"),
            "created_at": str(job.get("latest_run_at") or checked_at or ""),
            "actor": "production-scheduler",
            "details": {
                "observed": job.get("observed"),
                "stale": job.get("stale"),
                "required": job.get("required"),
                "latest_status": job.get("latest_status"),
            },
        })
    return events


def _pipeline_module(log: PipelineRunLog) -> str:
    target = log.target_type
    action = log.action
    if target == "content_import_issue" or action.startswith("import_issue"):
        return "import"
    if target in {"resource", "knowledge_entry"} or action in {"confirm_publish", "withdraw", "request_review"}:
        return "governance"
    if "migration" in action or target == "migration":
        return "migration"
    return "pipeline"


def _audit_status_from_pipeline(log: PipelineRunLog) -> str:
    if log.to_status in {"failed", "error"}:
        return "failed"
    if log.to_status in {"review_requested", "needs_attention", "reopened"}:
        return "needs_attention"
    if log.to_status in {"blocked", "blocked_by_policy"}:
        return "blocked"
    return "passed"


def _audit_severity(status: str, details: dict[str, Any]) -> str:
    if status in {"failed", "blocked"}:
        return "high"
    if status == "needs_attention":
        return "medium"
    if str(details.get("safety_risk_level") or "").lower() == "high":
        return "high"
    return "low"


def _audit_safety_flags(result: dict[str, Any]) -> list[Any]:
    flags = result.get("safety_flags")
    if isinstance(flags, list):
        return flags
    safety = result.get("safety")
    if isinstance(safety, dict) and isinstance(safety.get("flags"), list):
        value = safety["flags"]
        return list(value) if isinstance(value, list) else []
    return []


def _pipeline_audit_summary(log: PipelineRunLog, result: dict[str, Any]) -> str:
    pieces = [f"{log.from_status or 'unknown'} -> {log.to_status}"]
    resolution_hash = _audit_digest(result.get("resolution_hash"))
    if resolution_hash:
        pieces.append(f"resolution {resolution_hash}")
    affected = result.get("affected_count") or result.get("issue_count")
    if affected is not None:
        pieces.append(f"affected {affected}")
    return " · ".join(pieces)


def _audit_center_next_actions(events: list[dict[str, Any]]) -> list[dict[str, str]]:
    actions: list[dict[str, str]] = []
    by_module = Counter(str(event["module"]) for event in events if event["status"] in {"failed", "needs_attention", "blocked"})
    if by_module:
        module, count = by_module.most_common(1)[0]
        actions.append({"priority": "high", "action": f"处理 {module} 审计异常", "reason": f"最近审计流中 {module} 有 {count} 条需要关注。"})
    if any(event["module"] == "ai" and event["status"] == "failed" for event in events):
        actions.append({"priority": "high", "action": "复核 AI Provider 与 fallback", "reason": "最近 AI run log 出现失败，先保持可用降级并定位 provider 根因。"})
    if any(event["module"] == "runtime" for event in events):
        actions.append({"priority": "high", "action": "修复前端/API 运行时错误", "reason": "审计流中出现 runtime 事件，优先处理影响用户使用的页面或接口失败。"})
    if any(event["module"] == "import" and event["status"] == "needs_attention" for event in events):
        actions.append({"priority": "medium", "action": "推进来源级导入复核", "reason": "导入 issue 仍处于复核/重开状态，需要按来源分批关闭。"})
    if not actions:
        actions.append({"priority": "low", "action": "保持运营观察", "reason": "最近审计事件没有明显阻塞，继续积累趋势即可。"})
    return actions[:4]


def _safe_text(value: Any) -> str | None:
    if value is None:
        return None
    text = str(value)
    return text[:220]


def _bounded_label(value: str | None, fallback: str) -> str:
    text_value = (value or fallback).strip().lower().replace(" ", "_")
    return text_value[:80] or fallback


def _runtime_severity(severity: str | None, http_status: int | None) -> str:
    requested = _bounded_label(severity, "medium")
    if http_status is not None and http_status >= 500:
        return "high"
    if http_status is not None and http_status >= 400:
        return "medium"
    if requested in {"low", "medium", "high", "critical"}:
        return requested
    return "medium"


def _safe_runtime_method(method: str | None) -> str | None:
    if not method:
        return None
    return method.upper()[:12]


def _safe_runtime_path(value: str | None) -> str | None:
    if not value:
        return None
    return value.split("?")[0][:240]


def _message_preview(message: str) -> str:
    text = " ".join(message.split())
    redacted = re.sub(r"Bearer\s+\S+", "Bearer [redacted]", text, flags=re.IGNORECASE)
    redacted = re.sub(r"secret-[A-Za-z0-9._:-]+", "secret-[redacted]", redacted, flags=re.IGNORECASE)
    return redacted


def _safe_runtime_context(context: dict[str, Any]) -> dict[str, Any]:
    allowed = {
        "status_text",
        "component",
        "info",
        "browser",
        "online",
        "retryable",
        "duration_ms",
    }
    safe: dict[str, Any] = {}
    for key, value in context.items():
        if key not in allowed:
            continue
        if isinstance(value, str | int | float | bool) or value is None:
            safe[key] = str(value)[:160] if isinstance(value, str) else value
    return safe


def _audit_digest(value: Any) -> str | None:
    if value is None:
        return None
    digest = hashlib.sha256(str(value).encode("utf-8")).hexdigest()[:16]
    return f"sha256:{digest}"


def _provider_mode_value(mode: Any) -> str:
    value = getattr(mode, "value", mode)
    return str(value)


def _provider_api_key_env_name() -> str:
    return getattr(ai_provider_client, "credential_env_name", "PROVIDER_API_KEY")


def _provider_live_probe_env_name() -> str:
    if ai_provider_client.provider == "deepseek":
        return "DEEPSEEK_LIVE_PROBE_ENABLED"
    return f"{ai_provider_client.provider.upper()}_LIVE_PROBE_ENABLED"


def _optional_int(value: Any) -> int | None:
    if value is None:
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def _provider_risk_level(total: int, failures: int, configured: bool) -> str:
    if not configured or _percent(failures, total) >= 25:
        return "high"
    if failures:
        return "medium"
    return "low"


def _extract_http_status(reason: str | None) -> str | None:
    if not reason:
        return None
    for token in reason.replace(":", " ").split():
        if token.isdigit() and len(token) == 3:
            return token
    return None


def _redact_url(url: str) -> str:
    return url.split("?")[0].rstrip("/")


def _top_counter_name(counter: Counter[str]) -> str:
    return counter.most_common(1)[0][0] if counter else "unknown"


def _ensure_dict(value: Any) -> dict[str, Any]:
    return value if isinstance(value, dict) else {}


def _empty_relationship_trends() -> dict[str, Any]:
    return {
        "summary": {
            "sessions": 0,
            "sessions_with_events": 0,
            "turns": 0,
            "average_score": 0,
            "blocked_sessions": 0,
            "repair_index": 0,
        },
        "average_state_delta": {"trust": 0, "stress": 0, "boundary": 0, "boundary_safety": 0, "connection": 0},
        "attachment_distribution": [],
        "session_trend": [],
        "focus_distribution": [],
        "next_actions": [{"priority": "high", "action": "完成三轮 AI 伴侣训练", "reason": "跨会话趋势需要至少三轮真实轨迹。"}],
        "principle": "单次会话看转折，跨会话趋势看能力是否在长期推高信任、连接和边界安全，同时降低压力。",
    }


def _state_delta(first: dict[str, Any], last: dict[str, Any], key: str) -> float:
    if not first or not last:
        return 0
    return round(float(last.get(key, 0) or 0) - float(first.get(key, 0) or 0), 1)


def _counter_items(counter: Counter[Any], limit: int = 10) -> list[dict[str, Any]]:
    total = sum(counter.values())
    return [
        {"name": str(name), "count": count, "rate": _percent(count, total)}
        for name, count in counter.most_common(limit)
    ]


def _percent(value: int | float, total: int | float) -> float:
    return round((float(value) / float(total)) * 100, 1) if total else 0.0


def _loads_json_list(raw: str | None) -> list[Any]:
    if not raw:
        return []
    try:
        value = json.loads(raw)
    except json.JSONDecodeError:
        return []
    return value if isinstance(value, list) else []


def _loads_json_dict(raw: str | None) -> dict[str, Any]:
    if not raw:
        return {}
    try:
        value = json.loads(raw)
    except json.JSONDecodeError:
        return {}
    return value if isinstance(value, dict) else {}
