"""AI prompt registry and privacy-preserving run audit helpers."""
from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from typing import Any

from sqlmodel import Session, select

from backend.database.connection import create_db_and_tables, engine
from backend.models.ai import AIPromptVersion, AIRunLog

PROMPT_VERSION = "relationship-ai-orchestrator.v1"
SCHEMA_VERSION = "ai-response.v1"
SAFETY_POLICY_VERSION = "relationship-safety.v1"
USER_PROMPT_TEMPLATE = "任务类型：{task_type}\n输入数据：<payload redacted in audit>\n请输出严格 JSON。"
RESPONSE_CONTRACT: dict[str, Any] = {
    "type": "object",
    "required": ["ok"],
    "privacy": "run logs store payload hashes and structural summaries only",
}


@dataclass(frozen=True)
class PromptAuditSpec:
    prompt_id: str
    task_type: str
    version: str
    schema_version: str
    system_prompt_hash: str
    user_prompt_template_hash: str
    response_contract_json: str
    safety_policy_version: str


def prompt_spec(task_type: str, system_prompt: str) -> PromptAuditSpec:
    return PromptAuditSpec(
        prompt_id=f"{task_type}:{PROMPT_VERSION}",
        task_type=task_type,
        version=PROMPT_VERSION,
        schema_version=SCHEMA_VERSION,
        system_prompt_hash=_sha256(system_prompt),
        user_prompt_template_hash=_sha256(USER_PROMPT_TEMPLATE),
        response_contract_json=json.dumps(RESPONSE_CONTRACT, ensure_ascii=False, sort_keys=True),
        safety_policy_version=SAFETY_POLICY_VERSION,
    )


def payload_hash(payload: Any) -> str:
    return f"sha256:{_sha256(_safe_payload_text(payload))}"


def payload_summary(payload: Any) -> dict[str, Any]:
    if isinstance(payload, dict):
        return {
            "kind": "dict",
            "keys": sorted(str(key) for key in payload.keys()),
            "field_count": len(payload),
            "text_chars": _text_chars(payload),
        }
    if isinstance(payload, list):
        return {"kind": "list", "items": len(payload), "text_chars": _text_chars(payload)}
    return {"kind": type(payload).__name__, "text_chars": _text_chars(payload)}


def response_summary(result: dict[str, Any] | None, raw_text: str | None = None) -> dict[str, Any]:
    if result is None:
        return {"kind": "none"}
    summary: dict[str, Any] = {
        "kind": "dict",
        "keys": sorted(str(key) for key in result.keys()),
        "field_count": len(result),
    }
    if raw_text is not None:
        summary["raw_text_chars"] = len(raw_text)
    return summary


def ensure_prompt_version(session: Session, spec: PromptAuditSpec) -> None:
    existing = session.exec(
        select(AIPromptVersion).where(
            AIPromptVersion.prompt_id == spec.prompt_id,
            AIPromptVersion.version == spec.version,
            AIPromptVersion.schema_version == spec.schema_version,
        )
    ).first()
    if existing:
        return
    session.add(
        AIPromptVersion(
            prompt_id=spec.prompt_id,
            task_type=spec.task_type,
            version=spec.version,
            schema_version=spec.schema_version,
            system_prompt_hash=spec.system_prompt_hash,
            user_prompt_template_hash=spec.user_prompt_template_hash,
            response_contract_json=spec.response_contract_json,
            safety_policy_version=spec.safety_policy_version,
        )
    )


def record_ai_run(
    *,
    task_type: str,
    system_prompt: str,
    payload: Any,
    provider: str,
    model: str | None,
    outcome: str,
    safety: dict[str, Any],
    latency_ms: int,
    fallback_reason: str | None = None,
    response: dict[str, Any] | None = None,
    raw_text: str | None = None,
    safety_event_id: int | None = None,
) -> AIRunLog:
    create_db_and_tables()
    spec = prompt_spec(task_type, system_prompt)
    safety_flags = safety.get("flags") if isinstance(safety, dict) else []
    event = AIRunLog(
        task_type=task_type,
        prompt_id=spec.prompt_id,
        prompt_version=spec.version,
        schema_version=spec.schema_version,
        provider=provider,
        model=model,
        outcome=outcome,
        fallback_reason=fallback_reason,
        safety_risk_level=str(safety.get("risk_level") or "unknown"),
        safety_flags_json=json.dumps(safety_flags or [], ensure_ascii=False),
        payload_hash=payload_hash(payload),
        payload_summary_json=json.dumps(payload_summary(payload), ensure_ascii=False, sort_keys=True),
        response_summary_json=json.dumps(response_summary(response, raw_text), ensure_ascii=False, sort_keys=True),
        safety_event_id=safety_event_id,
        latency_ms=max(0, latency_ms),
    )
    with Session(engine) as session:
        ensure_prompt_version(session, spec)
        session.add(event)
        session.commit()
        session.refresh(event)
        return event


def _sha256(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _safe_payload_text(payload: Any) -> str:
    try:
        return json.dumps(payload, ensure_ascii=False, sort_keys=True)
    except TypeError:
        return str(payload)


def _text_chars(value: Any) -> int:
    if isinstance(value, str):
        return len(value)
    if isinstance(value, dict):
        return sum(_text_chars(item) for item in value.values())
    if isinstance(value, list):
        return sum(_text_chars(item) for item in value)
    return 0
