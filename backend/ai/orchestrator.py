"""AI 指挥编排器：统一安全检查、Prompt 组装、Provider 调用与降级。"""
from __future__ import annotations

import hashlib
import json
from time import perf_counter
from typing import Any

from sqlmodel import Session

from backend.ai.audit import record_ai_run
from backend.ai.provider_client import ai_provider_client
from backend.ai.safety import safety_guardian
from backend.ai.schemas import AIRequest, AIResponse
from backend.database.connection import create_db_and_tables, engine
from backend.models.training import SafetyEvent


class AIOrchestrator:
    async def run(self, request: AIRequest) -> AIResponse:
        started = perf_counter()
        safety = safety_guardian.inspect(request.payload)
        safety_payload = safety.to_dict()
        system_prompt = request.system_context or self._default_system_prompt()
        if safety_guardian.should_block(safety):
            safety_event_id = self._record_safety_event(request.task_type, request.payload, safety_payload)
            record_ai_run(
                task_type=request.task_type,
                system_prompt=system_prompt,
                payload=request.payload,
                provider=ai_provider_client.provider,
                model=ai_provider_client.model,
                outcome="blocked_safety",
                safety=safety_payload,
                latency_ms=_elapsed_ms(started),
                fallback_reason=safety.message,
                safety_event_id=safety_event_id,
            )
            return AIResponse(
                ok=False,
                task_type=request.task_type,
                safety=safety_payload,
                safe_alternatives=safety.alternatives or [],
                error=safety.message,
            )

        user_prompt = self._build_user_prompt(request)

        result = await ai_provider_client.chat_json(
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ]
        )

        if result.get("ok") is False:
            error = str(result.get("error", "AI 调用失败"))
            record_ai_run(
                task_type=request.task_type,
                system_prompt=system_prompt,
                payload=request.payload,
                provider=ai_provider_client.provider,
                model=ai_provider_client.model,
                outcome="provider_failure",
                safety=safety_payload,
                latency_ms=_elapsed_ms(started),
                fallback_reason=error,
                response=result,
            )
            return AIResponse(
                ok=False,
                task_type=request.task_type,
                safety=safety_payload,
                safe_alternatives=safety.alternatives or [],
                error=error,
            )

        raw_text = result.get("raw_text")
        record_ai_run(
            task_type=request.task_type,
            system_prompt=system_prompt,
            payload=request.payload,
            provider=ai_provider_client.provider,
            model=ai_provider_client.model,
            outcome="success_raw_text" if raw_text else "success",
            safety=safety_payload,
            latency_ms=_elapsed_ms(started),
            response=result,
            raw_text=raw_text if isinstance(raw_text, str) else None,
        )
        return AIResponse(
            ok=True,
            task_type=request.task_type,
            content=result if "raw_text" not in result else {},
            raw_text=raw_text if isinstance(raw_text, str) else None,
            safety=safety_payload,
            safe_alternatives=safety.alternatives or [],
        )

    def _default_system_prompt(self) -> str:
        return (
            "你是关系动力学训练系统的结构化 AI 子模块。"
            "你不是心理治疗师，不能做诊断。"
            "必须尊重边界，拒绝操控、PUA、欺骗、威胁和侵犯。"
            "所有输出必须是 JSON 对象。"
        )

    def _build_user_prompt(self, request: AIRequest) -> str:
        return f"任务类型：{request.task_type}\n输入数据：{request.payload}\n请输出严格 JSON。"

    def _record_safety_event(self, task_type: str, payload: Any, safety: dict[str, Any]) -> int | None:
        create_db_and_tables()
        text = _safe_payload_text(payload)
        event = SafetyEvent(
            task_type=task_type,
            risk_level=str(safety.get("risk_level") or "unknown"),
            flags_json=json.dumps(safety.get("flags") or [], ensure_ascii=False),
            payload_hash=f"sha256:{hashlib.sha256(text.encode('utf-8')).hexdigest()}",
            payload_preview=text[:240],
            message=safety.get("message"),
            alternatives_json=json.dumps(safety.get("alternatives") or [], ensure_ascii=False),
            blocked=True,
        )
        with Session(engine) as session:
            session.add(event)
            session.commit()
            session.refresh(event)
            return event.id


def _safe_payload_text(payload: Any) -> str:
    try:
        return json.dumps(payload, ensure_ascii=False, sort_keys=True)
    except TypeError:
        return str(payload)


def _elapsed_ms(started: float) -> int:
    return max(0, int((perf_counter() - started) * 1000))


ai_orchestrator = AIOrchestrator()
