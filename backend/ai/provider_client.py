"""OpenAI-compatible AI provider client.

默认只提供安全封装与结构化调用入口；没有配置 token 时会优雅降级。
"""
from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from enum import Enum
from time import perf_counter
from typing import Any

import httpx
from loguru import logger

from backend.database.connection import settings


class ProviderMode(str, Enum):
    OPENAI = "openai"
    NATIVE = "native"


@dataclass(frozen=True)
class AIProviderRequest:
    url: str
    headers: dict[str, str]
    payload: dict[str, Any]


@dataclass(frozen=True)
class AIProviderRequestDiagnostics:
    provider: str
    mode: str
    url: str
    path: str
    model: str
    payload_keys: list[str]
    message_roles: list[str]
    message_count: int
    content_chars: int
    schema_hash: str
    compatibility_risks: list[str]


class AIProviderClient:
    def __init__(self) -> None:
        requested_provider = self._normalize_provider(getattr(settings, "ai_provider", "deepseek"))
        self.api_key = getattr(settings, "deepseek_api_key", "")
        self.provider = requested_provider
        self.model = getattr(settings, "deepseek_model", "deepseek-v4-pro")
        self.base_url = self._default_base_url(getattr(settings, "deepseek_base_url", ""))
        self.mode = self._normalize_mode(getattr(settings, "deepseek_api_mode", "openai"))
        self.chat_path = getattr(settings, "deepseek_chat_path", "/chat/completions")
        self.timeout = getattr(settings, "deepseek_timeout", 60.0)
        self.live_probe_enabled = bool(getattr(settings, "deepseek_live_probe_enabled", False))
        self.reasoning_effort = getattr(settings, "deepseek_reasoning_effort", "high") if self.provider == "deepseek" else ""
        self.thinking_enabled = bool(getattr(settings, "deepseek_thinking_enabled", True)) if self.provider == "deepseek" else False

    @property
    def configured(self) -> bool:
        return bool(self.api_key)

    @property
    def credential_env_name(self) -> str:
        if self.provider == "deepseek":
            return "DEEPSEEK_API_KEY"
        return f"{self.provider.upper()}_API_KEY"

    @property
    def provider_label(self) -> str:
        labels = {
            "deepseek": "DeepSeek",
            "openai": "OpenAI",
        }
        return labels.get(self.provider, self.provider)

    async def chat_json(self, messages: list[dict[str, str]], temperature: float = 0.3) -> dict[str, Any]:
        """请求 AI provider 并尽量解析 JSON。"""
        if not self.configured:
            logger.warning("{} API key 未配置，返回空 AI 响应", self.provider_label)
            return {"ok": False, "error": f"{self.credential_env_name} 未配置"}

        request = self.build_request(messages, temperature)
        redacted_headers = {**request.headers, "Authorization": "Bearer ***"}
        logger.debug(
            "{} request provider={} mode={} url={} headers={}",
            self.provider_label,
            self.provider,
            self._mode_value(),
            request.url,
            redacted_headers,
        )

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await self._post_with_compatibility_retry(client, request)
                data = response.json()
        except httpx.TimeoutException:
            logger.warning("{} 请求超时", self.provider_label)
            return {"ok": False, "error": f"{self.provider_label} 请求超时"}
        except httpx.HTTPStatusError as exc:
            logger.warning("{} HTTP 错误: {}", self.provider_label, exc.response.status_code)
            return {"ok": False, "error": f"{self.provider_label} HTTP 错误: {exc.response.status_code}"}
        except httpx.HTTPError as exc:
            logger.warning("{} 网络错误: {}", self.provider_label, exc)
            return {"ok": False, "error": f"{self.provider_label} 网络错误: {exc}"}
        except json.JSONDecodeError:
            logger.warning("{} 响应体不是合法 JSON", self.provider_label)
            return {"ok": False, "error": f"{self.provider_label} 响应体不是合法 JSON"}

        text = self._extract_text(data)
        parsed = _parse_json_object_from_text(text)
        if parsed is None:
            logger.warning("{} 响应不是合法 JSON，返回 raw_text", self.provider_label)
            return {"ok": True, "raw_text": text}
        if isinstance(parsed, dict):
            return parsed
        return {"ok": True, "content": parsed}

    async def probe(self, *, dry_run: bool = True) -> dict[str, Any]:
        """Run or preview a minimal provider health probe without returning raw text."""
        diagnostics = self.request_diagnostics()
        if dry_run:
            return {
                "dry_run": True,
                "outcome": "planned",
                "request_shape": diagnostics.__dict__,
                "principle": "dry-run only reports the redacted request shape; it does not call the provider.",
            }
        if not self.live_probe_enabled:
            return {
                "dry_run": False,
                "outcome": "blocked_by_policy",
                "request_shape": diagnostics.__dict__,
                "error_type": "live_probe_not_enabled",
                "latency_ms": 0,
                "principle": f"live provider probes require {self._live_probe_env_name()}=true to avoid accidental external calls.",
            }
        if not self.configured:
            return {
                "dry_run": False,
                "outcome": "not_configured",
                "request_shape": diagnostics.__dict__,
                "error_type": "missing_api_key",
                "latency_ms": 0,
            }

        request = self.build_request(
            [
                {"role": "system", "content": "Return strict JSON."},
                {"role": "user", "content": "healthcheck"},
            ],
            temperature=0,
        )
        started = perf_counter()
        try:
            async with httpx.AsyncClient(timeout=min(float(self.timeout), 20.0)) as client:
                response = await client.post(request.url, headers=request.headers, json=request.payload)
                retry_payload = self._compatibility_retry_payload(request.payload, response.status_code)
                if retry_payload is not None:
                    initial_status = response.status_code
                    response = await client.post(request.url, headers=request.headers, json=retry_payload)
                else:
                    initial_status = None
            latency = _elapsed_ms(started)
            result = {
                "dry_run": False,
                "outcome": "ok" if 200 <= response.status_code < 300 else "http_error",
                "request_shape": diagnostics.__dict__,
                "http_status": response.status_code,
                "error_type": None if 200 <= response.status_code < 300 else f"http_{response.status_code}",
                "latency_ms": latency,
            }
            if initial_status is not None:
                result["initial_http_status"] = initial_status
                result["compatibility_retry"] = "without_deepseek_optional_params"
            return result
        except httpx.TimeoutException:
            return {"dry_run": False, "outcome": "timeout", "request_shape": diagnostics.__dict__, "error_type": "timeout", "latency_ms": _elapsed_ms(started)}
        except httpx.HTTPError as exc:
            return {
                "dry_run": False,
                "outcome": "network_error",
                "request_shape": diagnostics.__dict__,
                "error_type": type(exc).__name__,
                "latency_ms": _elapsed_ms(started),
            }

    def build_request(self, messages: list[dict[str, str]], temperature: float = 0.3) -> AIProviderRequest:
        """构造请求，便于测试 provider payload 且避免泄漏密钥。"""
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        path = self._path()
        payload = {
            "model": self.model,
            "messages": messages,
            "temperature": temperature,
        }
        if self.mode == ProviderMode.NATIVE:
            payload = {
                "model": self.model,
                "messages": self._native_messages(messages),
                "temperature": temperature,
            }
        elif self.provider == "deepseek":
            if self.reasoning_effort:
                payload["reasoning_effort"] = self.reasoning_effort
            if self.thinking_enabled:
                payload["thinking"] = {"type": "enabled"}
        return AIProviderRequest(url=f"{self.base_url}{path}", headers=headers, payload=payload)

    def request_diagnostics(
        self,
        messages: list[dict[str, str]] | None = None,
        temperature: float = 0.3,
    ) -> AIProviderRequestDiagnostics:
        """Return a redacted request-shape diagnostic for provider troubleshooting."""
        probe_messages = messages or [
            {"role": "system", "content": "Return strict JSON."},
            {"role": "user", "content": "healthcheck"},
        ]
        request = self.build_request(probe_messages, temperature)
        mode_value = self._mode_value()
        payload = request.payload
        payload_keys = sorted(str(key) for key in payload.keys())
        request_messages = payload.get("messages")
        message_rows = request_messages if isinstance(request_messages, list) else []
        message_roles = [str(item.get("role", "unknown")) for item in message_rows if isinstance(item, dict)]
        content_chars = sum(len(str(item.get("content", ""))) for item in message_rows if isinstance(item, dict))
        schema_fingerprint = {
            "mode": mode_value,
            "model": self.model,
            "payload_keys": payload_keys,
            "message_roles": message_roles,
            "temperature_type": type(payload.get("temperature")).__name__,
        }
        return AIProviderRequestDiagnostics(
            provider=self.provider,
            mode=mode_value,
            url=f"{_redact_url(self.base_url)}{self._path()}",
            path=self._path(),
            model=self.model,
            payload_keys=payload_keys,
            message_roles=message_roles,
            message_count=len(message_rows),
            content_chars=content_chars,
            schema_hash="sha256:" + hashlib.sha256(
                json.dumps(schema_fingerprint, ensure_ascii=False, sort_keys=True).encode("utf-8")
            ).hexdigest(),
            compatibility_risks=self._request_shape_risks(payload_keys, message_roles),
        )

    def _extract_text(self, data: dict[str, Any]) -> str:
        choices = data.get("choices") or []
        if choices:
            message = choices[0].get("message") or {}
            content = message.get("content")
            if isinstance(content, str):
                return content
        reply = data.get("reply")
        if isinstance(reply, str):
            return reply
        output_text = data.get("output_text")
        if isinstance(output_text, str):
            return output_text
        return json.dumps(data, ensure_ascii=False)

    def _path(self) -> str:
        if self.chat_path:
            return self.chat_path if self.chat_path.startswith("/") else f"/{self.chat_path}"
        if self.mode == ProviderMode.NATIVE:
            return "/text/chatcompletion_v2"
        return "/chat/completions"

    def _native_messages(self, messages: list[dict[str, str]]) -> list[dict[str, str]]:
        native_messages: list[dict[str, str]] = []
        for message in messages:
            native_messages.append({"role": message.get("role", "user"), "content": message.get("content", "")})
        return native_messages

    def _normalize_mode(self, mode: str) -> ProviderMode:
        normalized = (mode or "openai").strip().lower()
        if normalized in {"native", "text"}:
            return ProviderMode.NATIVE
        return ProviderMode.OPENAI

    def _normalize_provider(self, provider: str) -> str:
        normalized = (provider or "deepseek").strip().lower()
        if normalized in {"openai", "openai-compatible", "compatible"}:
            return "openai"
        if normalized in {"deepseek", "deepseek-v4"}:
            return "deepseek"
        return "deepseek"

    def _default_base_url(self, base_url: str) -> str:
        configured = (base_url or "").strip()
        if configured:
            return configured.rstrip("/")
        if self.provider == "deepseek":
            return "https://api.deepseek.com"
        if self.provider == "openai":
            return "https://api.openai.com/v1"
        return "https://api.deepseek.com"

    def _live_probe_env_name(self) -> str:
        if self.provider == "deepseek":
            return "DEEPSEEK_LIVE_PROBE_ENABLED"
        return f"{self.provider.upper()}_LIVE_PROBE_ENABLED"

    def _request_shape_risks(self, payload_keys: list[str], message_roles: list[str]) -> list[str]:
        risks: list[str] = []
        mode_value = self._mode_value()
        if mode_value == ProviderMode.OPENAI.value and self._path() != "/chat/completions":
            risks.append("openai_mode_non_chat_completions_path")
        if mode_value == ProviderMode.NATIVE.value and self._path() != "/text/chatcompletion_v2":
            risks.append("native_mode_non_native_chat_path")
        if "messages" not in payload_keys:
            risks.append("missing_messages_field")
        if "model" not in payload_keys:
            risks.append("missing_model_field")
        if not message_roles or message_roles[-1] != "user":
            risks.append("last_message_not_user")
        return risks

    async def _post_with_compatibility_retry(
        self,
        client: httpx.AsyncClient,
        request: AIProviderRequest,
    ) -> httpx.Response:
        response = await client.post(request.url, headers=request.headers, json=request.payload)
        try:
            response.raise_for_status()
            return response
        except httpx.HTTPStatusError as exc:
            retry_payload = self._compatibility_retry_payload(request.payload, exc.response.status_code)
            if retry_payload is None:
                raise
            logger.warning(
                "{} HTTP 错误: {}，移除可选推理参数后兼容重试",
                self.provider_label,
                exc.response.status_code,
            )

        response = await client.post(request.url, headers=request.headers, json=retry_payload)
        response.raise_for_status()
        return response

    def _compatibility_retry_payload(self, payload: dict[str, Any], status_code: int) -> dict[str, Any] | None:
        """Retry DeepSeek 400s without optional reasoning params for account/gateway compatibility."""
        if self.provider != "deepseek" or self._mode_value() != ProviderMode.OPENAI.value:
            return None
        if status_code != 400:
            return None
        optional_keys = {"reasoning_effort", "thinking"}
        if not optional_keys.intersection(payload):
            return None
        retry_payload = {key: value for key, value in payload.items() if key not in optional_keys}
        return retry_payload

    def _mode_value(self) -> str:
        value = getattr(self.mode, "value", self.mode)
        return str(value)


def _redact_url(url: str) -> str:
    return url.split("?")[0].rstrip("/")


def _elapsed_ms(started: float) -> int:
    return max(0, int((perf_counter() - started) * 1000))


def _parse_json_object_from_text(text: str) -> Any | None:
    """Parse strict JSON first, then one balanced JSON object embedded in provider prose."""
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass

    candidate = _extract_balanced_json_object(text)
    if candidate is None:
        return None
    try:
        return json.loads(candidate)
    except json.JSONDecodeError:
        return None


def _extract_balanced_json_object(text: str) -> str | None:
    start = text.find("{")
    if start < 0:
        return None
    depth = 0
    in_string = False
    escaped = False
    for index, char in enumerate(text[start:], start=start):
        if escaped:
            escaped = False
            continue
        if char == "\\" and in_string:
            escaped = True
            continue
        if char == '"':
            in_string = not in_string
            continue
        if in_string:
            continue
        if char == "{":
            depth += 1
        elif char == "}":
            depth -= 1
            if depth == 0:
                return text[start:index + 1]
    return None


ai_provider_client = AIProviderClient()
