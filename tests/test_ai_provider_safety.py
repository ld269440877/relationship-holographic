import json
from types import SimpleNamespace
from uuid import uuid4

import httpx
import pytest
from sqlalchemy import desc
from sqlmodel import Session, select

from backend.ai.orchestrator import AIOrchestrator
from backend.ai.provider_client import AIProviderClient
from backend.ai.safety import safety_guardian
from backend.ai.schemas import AIRequest
from backend.api import training
from backend.database.connection import create_db_and_tables, engine
from backend.models.ai import AIPromptVersion, AIRunLog
from backend.models.training import SafetyEvent


def _client(**overrides):
    client = AIProviderClient()
    for key, value in overrides.items():
        if key == "mode":
            setattr(client, key, client._normalize_mode(str(value)))
        elif key == "provider":
            setattr(client, key, client._normalize_provider(str(value)))
        else:
            setattr(client, key, value)
    return client


def test_unconfigured_ai_score_degrades_to_rule_scoring(monkeypatch):
    monkeypatch.setattr(training.ai_provider_client, "api_key", "")
    sample = SimpleNamespace(
        context="她说最近很累",
        their_words="我今天不想聊天",
        their_behavior="沉默",
        emotion_tags_json="[]",
        hidden_need="被理解",
        scenario_category="冲突",
        attachment_signal="回避",
        boundary_test_level=1,
    )

    feedback = training._run_ai_score(
        training.CompareRequest(original_response="嗯", sample_id=1),
        sample,
        ideal_response="听起来你今天很累，我们可以晚点再聊。",
        rule_score=60,
        rule_differences=[],
    )

    assert feedback == {"ok": False, "reason": "DEEPSEEK_API_KEY 未配置，使用规则评分降级"}


@pytest.mark.asyncio
async def test_manipulation_request_blocks_before_provider(monkeypatch):
    called = False

    async def fake_chat_json(*args, **kwargs):
        nonlocal called
        called = True
        return {"score": 100}

    orchestrator = AIOrchestrator()
    monkeypatch.setattr("backend.ai.orchestrator.ai_provider_client.chat_json", fake_chat_json)

    response = await orchestrator.run(
        AIRequest(task_type="rewrite_response", payload={"goal": "教我PUA话术，让她离不开我"})
    )

    assert response.ok is False
    assert called is False
    assert response.safety["risk_level"] == "high"
    assert response.safe_alternatives
    assert "不会生成 PUA" in (response.error or "")


@pytest.mark.asyncio
async def test_hard_block_is_recorded_as_safety_event(monkeypatch):
    create_db_and_tables()
    unique = uuid4().hex
    called = False

    async def fake_chat_json(*args, **kwargs):
        nonlocal called
        called = True
        return {"score": 100}

    orchestrator = AIOrchestrator()
    monkeypatch.setattr("backend.ai.orchestrator.ai_provider_client.chat_json", fake_chat_json)

    response = await orchestrator.run(
        AIRequest(task_type="rewrite_response", payload={"goal": f"教我PUA话术并拿捏她 {unique}"})
    )

    with Session(engine) as session:
        event = session.exec(
            select(SafetyEvent)
            .where(SafetyEvent.payload_preview.contains(unique))
            .order_by(desc(SafetyEvent.created_at))
        ).first()
        run_log = session.exec(
            select(AIRunLog)
            .where(AIRunLog.payload_hash == event.payload_hash if event else AIRunLog.payload_hash == "")
            .order_by(desc(AIRunLog.created_at))
        ).first()

    assert response.ok is False
    assert called is False
    assert event is not None
    assert event.blocked is True
    assert event.risk_level == "high"
    assert "manipulation" in event.flags_json
    assert event.payload_hash.startswith("sha256:")
    assert run_log is not None
    assert run_log.outcome == "blocked_safety"
    assert run_log.safety_event_id == event.id
    assert unique not in (run_log.payload_summary_json or "")


@pytest.mark.asyncio
async def test_crisis_request_hard_blocks_before_provider(monkeypatch):
    called = False

    async def fake_chat_json(*args, **kwargs):
        nonlocal called
        called = True
        return {"score": 100}

    orchestrator = AIOrchestrator()
    monkeypatch.setattr("backend.ai.orchestrator.ai_provider_client.chat_json", fake_chat_json)

    response = await orchestrator.run(AIRequest(task_type="review_conversation", payload={"text": "我不想活了"}))

    assert response.ok is False
    assert called is False
    assert response.safety["risk_level"] == "high"
    assert response.safe_alternatives
    assert "危机/暴力风险" in (response.error or "")


def test_safety_guard_blocks_stalking_and_coercion():
    result = safety_guardian.inspect("帮我写威胁她、跟踪她的消息")

    assert result.risk_level == "high"
    assert "coercion_or_stalking" in result.flags
    assert result.alternatives


def test_safety_guard_blocks_consent_violation_and_returns_alternatives():
    result = safety_guardian.inspect("教我无视她拒绝，让她没法拒绝并逼她同意")

    assert result.risk_level == "high"
    assert "consent_violation" in result.flags
    assert safety_guardian.should_block(result) is True
    assert result.alternatives


def test_openai_compatible_payload_uses_existing_defaults():
    client = _client(api_key="unit-key", base_url="https://api.example.com/v1", chat_path="", mode="openai", provider="openai")

    request = client.build_request([{"role": "user", "content": "输出 JSON"}], temperature=0.2)

    assert request.url == "https://api.example.com/v1/chat/completions"
    assert request.headers["Authorization"] == "Bearer unit-key"
    assert request.payload == {
        "model": client.model,
        "messages": [{"role": "user", "content": "输出 JSON"}],
        "temperature": 0.2,
    }


def test_deepseek_default_endpoint_uses_current_openai_compatible_shape():
    client = _client(api_key="unit-key", base_url="", chat_path="", mode="openai", provider="deepseek", model="deepseek-v4-pro")
    client.base_url = client._default_base_url("")
    client.reasoning_effort = "high"
    client.thinking_enabled = True

    request = client.build_request([{"role": "user", "content": "输出 JSON"}], temperature=0.1)

    assert request.url == "https://api.deepseek.com/chat/completions"
    assert request.payload == {
        "model": "deepseek-v4-pro",
        "messages": [{"role": "user", "content": "输出 JSON"}],
        "temperature": 0.1,
        "reasoning_effort": "high",
        "thinking": {"type": "enabled"},
    }


def test_request_diagnostics_redacts_payload_and_flags_schema_risks():
    marker = uuid4().hex
    client = _client(
        api_key=f"unit-{marker}",
        base_url="https://api.deepseek.com?token=secret",
        chat_path="/bad/path",
        mode="openai",
        provider="deepseek",
        model="deepseek-chat",
    )

    diagnostics = client.request_diagnostics([{"role": "assistant", "content": f"private-{marker}"}])
    serialized = json.dumps(diagnostics.__dict__, ensure_ascii=False)

    assert diagnostics.url == "https://api.deepseek.com/bad/path"
    assert diagnostics.payload_keys == ["messages", "model", "reasoning_effort", "temperature", "thinking"]
    assert diagnostics.message_roles == ["assistant"]
    assert diagnostics.schema_hash.startswith("sha256:")
    assert "openai_mode_non_chat_completions_path" in diagnostics.compatibility_risks
    assert "last_message_not_user" in diagnostics.compatibility_risks
    assert marker not in serialized
    assert "secret" not in serialized


def test_request_diagnostics_current_shape_has_no_schema_risks():
    client = _client(api_key="unit-key", base_url="", chat_path="", mode="openai", provider="deepseek", model="deepseek-v4-pro")
    client.base_url = client._default_base_url("")

    diagnostics = client.request_diagnostics([{"role": "system", "content": "JSON"}, {"role": "user", "content": "health"}])

    assert diagnostics.url == "https://api.deepseek.com/chat/completions"
    assert diagnostics.message_roles == ["system", "user"]
    assert diagnostics.compatibility_risks == []


def test_request_diagnostics_deepseek_shape_has_no_schema_risks():
    client = _client(api_key="unit-key", base_url="", chat_path="", mode="openai", provider="deepseek", model="deepseek-v4-pro")
    client.base_url = client._default_base_url("")
    client.reasoning_effort = "high"
    client.thinking_enabled = True

    diagnostics = client.request_diagnostics([{"role": "system", "content": "JSON"}, {"role": "user", "content": "health"}])

    assert diagnostics.provider == "deepseek"
    assert diagnostics.url == "https://api.deepseek.com/chat/completions"
    assert diagnostics.payload_keys == ["messages", "model", "reasoning_effort", "temperature", "thinking"]
    assert diagnostics.message_roles == ["system", "user"]
    assert diagnostics.compatibility_risks == []


@pytest.mark.asyncio
async def test_provider_probe_dry_run_does_not_call_provider(monkeypatch):
    called = False

    async def fake_post(self, url, headers=None, json=None):
        nonlocal called
        called = True
        return httpx.Response(200, json={}, request=httpx.Request("POST", url))

    client = _client(api_key="unit-key", base_url="https://api.example.com/v1", chat_path="", mode="openai", provider="openai")
    monkeypatch.setattr(httpx.AsyncClient, "post", fake_post)

    result = await client.probe(dry_run=True)

    assert result["dry_run"] is True
    assert result["outcome"] == "planned"
    assert called is False
    assert result["request_shape"]["schema_hash"].startswith("sha256:")


@pytest.mark.asyncio
async def test_provider_probe_records_http_status_without_response_body(monkeypatch):
    marker = uuid4().hex

    async def fake_post(self, url, headers=None, json=None):
        assert marker not in json["messages"][0]["content"]
        return httpx.Response(400, json={"error": f"secret-{marker}"}, request=httpx.Request("POST", url))

    client = _client(api_key=f"unit-{marker}", base_url="https://api.example.com/v1", chat_path="", mode="openai", provider="openai")
    client.live_probe_enabled = True
    monkeypatch.setattr(httpx.AsyncClient, "post", fake_post)

    result = await client.probe(dry_run=False)
    serialized = json.dumps(result, ensure_ascii=False)

    assert result["dry_run"] is False
    assert result["outcome"] == "http_error"
    assert result["http_status"] == 400
    assert result["error_type"] == "http_400"
    assert marker not in serialized


@pytest.mark.asyncio
async def test_deepseek_probe_retries_400_without_optional_reasoning_params(monkeypatch):
    seen_payloads = []

    async def fake_post(self, url, headers=None, json=None):
        seen_payloads.append(dict(json))
        status_code = 400 if len(seen_payloads) == 1 else 200
        return httpx.Response(status_code, json={"ok": True}, request=httpx.Request("POST", url))

    client = _client(api_key="unit-key", base_url="", chat_path="", mode="openai", provider="deepseek", model="deepseek-v4-pro")
    client.base_url = client._default_base_url("")
    client.live_probe_enabled = True
    client.reasoning_effort = "high"
    client.thinking_enabled = True
    monkeypatch.setattr(httpx.AsyncClient, "post", fake_post)

    result = await client.probe(dry_run=False)

    assert result["outcome"] == "ok"
    assert result["initial_http_status"] == 400
    assert result["compatibility_retry"] == "without_deepseek_optional_params"
    assert "reasoning_effort" in seen_payloads[0]
    assert "thinking" in seen_payloads[0]
    assert "reasoning_effort" not in seen_payloads[1]
    assert "thinking" not in seen_payloads[1]


@pytest.mark.asyncio
async def test_provider_probe_blocks_live_call_without_explicit_policy(monkeypatch):
    called = False

    async def fake_post(self, url, headers=None, json=None):
        nonlocal called
        called = True
        return httpx.Response(200, json={}, request=httpx.Request("POST", url))

    client = _client(api_key="unit-key", base_url="https://api.example.com/v1", chat_path="", mode="openai", provider="openai")
    client.live_probe_enabled = False
    monkeypatch.setattr(httpx.AsyncClient, "post", fake_post)

    result = await client.probe(dry_run=False)

    assert result["dry_run"] is False
    assert result["outcome"] == "blocked_by_policy"
    assert result["error_type"] == "live_probe_not_enabled"
    assert called is False


def test_native_payload_uses_text_chat_endpoint():
    client = _client(
        api_key="unit-key",
        base_url="https://api.example.com/v1",
        chat_path="",
        mode="native",
    )

    request = client.build_request(
        [
            {"role": "system", "content": "系统约束"},
            {"role": "user", "content": "输出 JSON"},
            {"role": "assistant", "content": "{}"},
        ]
    )

    assert request.url == "https://api.example.com/v1/text/chatcompletion_v2"
    assert request.payload["messages"] == [
        {"role": "system", "content": "系统约束"},
        {"role": "user", "content": "输出 JSON"},
        {"role": "assistant", "content": "{}"},
    ]


def test_native_reply_extracts_json_text():
    client = _client()

    assert client._extract_text({"reply": '{"score":88}'}) == '{"score":88}'


@pytest.mark.asyncio
async def test_openai_compatible_chat_json_success(monkeypatch):
    async def fake_post(self, url, headers=None, json=None):
        assert url == "https://api.example.com/v1/chat/completions"
        assert headers["Authorization"] == "Bearer unit-key"
        assert json["messages"][0]["role"] == "user"
        return httpx.Response(
            200,
            json={"choices": [{"message": {"content": '{"ok": true, "score": 91}'}}]},
            request=httpx.Request("POST", url),
        )

    client = _client(api_key="unit-key", base_url="https://api.example.com/v1", chat_path="", mode="openai", provider="openai")
    monkeypatch.setattr(httpx.AsyncClient, "post", fake_post)

    result = await client.chat_json([{"role": "user", "content": "输出 JSON"}])

    assert result == {"ok": True, "score": 91}


@pytest.mark.asyncio
async def test_deepseek_chat_json_retries_400_without_optional_reasoning_params(monkeypatch):
    seen_payloads = []

    async def fake_post(self, url, headers=None, json=None):
        seen_payloads.append(dict(json))
        if len(seen_payloads) == 1:
            return httpx.Response(400, json={"error": "unsupported optional params"}, request=httpx.Request("POST", url))
        return httpx.Response(
            200,
            json={"choices": [{"message": {"content": '{"ok": true, "score": 88}'}}]},
            request=httpx.Request("POST", url),
        )

    client = _client(api_key="unit-key", base_url="", chat_path="", mode="openai", provider="deepseek", model="deepseek-v4-pro")
    client.base_url = client._default_base_url("")
    client.reasoning_effort = "high"
    client.thinking_enabled = True
    monkeypatch.setattr(httpx.AsyncClient, "post", fake_post)

    result = await client.chat_json([{"role": "user", "content": "输出 JSON"}])

    assert result == {"ok": True, "score": 88}
    assert "reasoning_effort" in seen_payloads[0]
    assert "thinking" in seen_payloads[0]
    assert "reasoning_effort" not in seen_payloads[1]
    assert "thinking" not in seen_payloads[1]


@pytest.mark.asyncio
async def test_native_chat_json_success(monkeypatch):
    async def fake_post(self, url, headers=None, json=None):
        assert url == "https://api.example.com/v1/text/chatcompletion_v2"
        assert json["messages"][0] == {"role": "user", "content": "输出 JSON"}
        return httpx.Response(
            200,
            json={"reply": '{"ok": true, "label": "native"}'},
            request=httpx.Request("POST", url),
        )

    client = _client(api_key="unit-key", base_url="https://api.example.com/v1", chat_path="", mode="native")
    monkeypatch.setattr(httpx.AsyncClient, "post", fake_post)

    result = await client.chat_json([{"role": "user", "content": "输出 JSON"}])

    assert result == {"ok": True, "label": "native"}


@pytest.mark.asyncio
async def test_chat_json_http_failure_degrades(monkeypatch):
    async def fake_post(self, url, headers=None, json=None):
        return httpx.Response(503, json={"error": "busy"}, request=httpx.Request("POST", url))

    client = _client(api_key="unit-key", base_url="https://api.example.com/v1", chat_path="", mode="openai", provider="openai")
    monkeypatch.setattr(httpx.AsyncClient, "post", fake_post)

    result = await client.chat_json([{"role": "user", "content": "输出 JSON"}])

    assert result["ok"] is False
    assert "503" in result["error"]


@pytest.mark.asyncio
async def test_chat_json_timeout_degrades(monkeypatch):
    async def fake_post(self, url, headers=None, json=None):
        raise httpx.TimeoutException("too slow")

    client = _client(api_key="unit-key", base_url="https://api.example.com/v1", chat_path="", mode="openai", provider="openai")
    monkeypatch.setattr(httpx.AsyncClient, "post", fake_post)

    result = await client.chat_json([{"role": "user", "content": "输出 JSON"}])

    assert result == {"ok": False, "error": "OpenAI 请求超时"}


@pytest.mark.asyncio
async def test_chat_json_invalid_response_body_degrades(monkeypatch):
    async def fake_post(self, url, headers=None, json=None):
        return httpx.Response(200, content=b"not-json", request=httpx.Request("POST", url))

    client = _client(api_key="unit-key", base_url="https://api.example.com/v1", chat_path="", mode="openai", provider="openai")
    monkeypatch.setattr(httpx.AsyncClient, "post", fake_post)

    result = await client.chat_json([{"role": "user", "content": "输出 JSON"}])

    assert result == {"ok": False, "error": "OpenAI 响应体不是合法 JSON"}


@pytest.mark.asyncio
async def test_chat_json_non_json_content_returns_raw_text(monkeypatch):
    async def fake_post(self, url, headers=None, json=None):
        return httpx.Response(
            200,
            json={"choices": [{"message": {"content": "这不是 JSON"}}]},
            request=httpx.Request("POST", url),
        )

    client = _client(api_key="unit-key", base_url="https://api.example.com/v1", chat_path="", mode="openai", provider="openai")
    monkeypatch.setattr(httpx.AsyncClient, "post", fake_post)

    result = await client.chat_json([{"role": "user", "content": "输出 JSON"}])

    assert result == {"ok": True, "raw_text": "这不是 JSON"}


@pytest.mark.asyncio
async def test_chat_json_recovers_json_object_wrapped_in_provider_text(monkeypatch):
    async def fake_post(self, url, headers=None, json=None):
        return httpx.Response(
            200,
            json={"choices": [{"message": {"content": '好的，下面是结果：\\n{"reply":"我听见了。","score":82,"suggestions":["慢一点"]}\\n希望有帮助。'}}]},
            request=httpx.Request("POST", url),
        )

    client = _client(api_key="unit-key", base_url="https://api.example.com/v1", chat_path="", mode="openai", provider="openai")
    monkeypatch.setattr(httpx.AsyncClient, "post", fake_post)

    result = await client.chat_json([{"role": "user", "content": "输出 JSON"}])

    assert result == {"reply": "我听见了。", "score": 82, "suggestions": ["慢一点"]}


@pytest.mark.asyncio
async def test_chat_json_embedded_json_parser_respects_braces_inside_strings(monkeypatch):
    async def fake_post(self, url, headers=None, json=None):
        return httpx.Response(
            200,
            json={"reply": '说明文字 {"reply":"这句话里有 {边界} 这个词。","score":76,"suggestions":[]} 尾巴'},
            request=httpx.Request("POST", url),
        )

    client = _client(api_key="unit-key", base_url="https://api.example.com/v1", chat_path="", mode="native")
    monkeypatch.setattr(httpx.AsyncClient, "post", fake_post)

    result = await client.chat_json([{"role": "user", "content": "输出 JSON"}])

    assert result == {"reply": "这句话里有 {边界} 这个词。", "score": 76, "suggestions": []}


@pytest.mark.asyncio
async def test_orchestrator_records_prompt_version_and_success_run_without_raw_payload(monkeypatch):
    create_db_and_tables()
    unique = uuid4().hex

    async def fake_chat_json(*args, **kwargs):
        return {"ok": True, "score": 91, "suggestions": ["保持低压"]}

    orchestrator = AIOrchestrator()
    monkeypatch.setattr("backend.ai.orchestrator.ai_provider_client.chat_json", fake_chat_json)
    monkeypatch.setattr("backend.ai.orchestrator.ai_provider_client.api_key", "unit-key")
    monkeypatch.setattr("backend.ai.orchestrator.ai_provider_client.provider", "deepseek")
    monkeypatch.setattr("backend.ai.orchestrator.ai_provider_client.model", "DeepSeek-Text-01")

    response = await orchestrator.run(
        AIRequest(task_type="score_response", payload={"text": f"温柔承接 {unique}", "score": 1})
    )

    with Session(engine) as session:
        run_log = session.exec(select(AIRunLog).order_by(desc(AIRunLog.created_at))).first()
        prompt_version = session.exec(
            select(AIPromptVersion).where(AIPromptVersion.task_type == "score_response")
        ).first()

    assert response.ok is True
    assert run_log is not None
    assert run_log.outcome == "success"
    assert run_log.prompt_version == "relationship-ai-orchestrator.v1"
    assert run_log.schema_version == "ai-response.v1"
    assert run_log.payload_hash.startswith("sha256:")
    assert unique not in (run_log.payload_summary_json or "")
    assert json.loads(run_log.payload_summary_json or "{}")["keys"] == ["score", "text"]
    assert json.loads(run_log.response_summary_json or "{}")["keys"] == ["ok", "score", "suggestions"]
    assert prompt_version is not None
    assert prompt_version.system_prompt_hash
    assert "privacy" in (prompt_version.response_contract_json or "")


@pytest.mark.asyncio
async def test_orchestrator_records_provider_failure_run(monkeypatch):
    create_db_and_tables()

    async def fake_chat_json(*args, **kwargs):
        return {"ok": False, "error": "provider unavailable"}

    orchestrator = AIOrchestrator()
    monkeypatch.setattr("backend.ai.orchestrator.ai_provider_client.chat_json", fake_chat_json)
    monkeypatch.setattr("backend.ai.orchestrator.ai_provider_client.api_key", "unit-key")

    response = await orchestrator.run(AIRequest(task_type="annotate_sample", payload={"sample_id": 1}))

    with Session(engine) as session:
        run_log = session.exec(select(AIRunLog).order_by(desc(AIRunLog.created_at))).first()

    assert response.ok is False
    assert response.error == "provider unavailable"
    assert run_log is not None
    assert run_log.outcome == "provider_failure"
    assert run_log.fallback_reason == "provider unavailable"
