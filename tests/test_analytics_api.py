import json
from uuid import uuid4

from fastapi.testclient import TestClient
from sqlmodel import Session, text

from backend.database.connection import create_db_and_tables, engine
from backend.database.safety_alternative_training_seed import SOURCE as SAFETY_ALTERNATIVE_SOURCE
from backend.database.safety_alternative_training_seed import seed as seed_safety_alternatives
from backend.main import app
from backend.models.ai import AIProviderProbeLog, AIRunLog
from backend.models.evolution import PipelineRunLog
from backend.models.training import PracticeEvent, PracticeSession
from tests.conftest import TEST_DB_PATH

client = TestClient(app)


def _clear_safety_alternative_training() -> None:
    with engine.begin() as connection:
        connection.execute(text("DELETE FROM resource_library WHERE source = :source"), {"source": SAFETY_ALTERNATIVE_SOURCE})
        connection.execute(text("DELETE FROM knowledge_entries WHERE source = :source"), {"source": SAFETY_ALTERNATIVE_SOURCE})
        connection.execute(text("DELETE FROM expression_tool_chains WHERE chain_uuid LIKE 'expr_chain_safety_alternative_%'"))
        connection.execute(text("DELETE FROM knowledge_sections WHERE section_uuid = 'knowledge_safety_alternative_training_v1'"))
        connection.execute(text("DELETE FROM content_import_batches WHERE source_name = :source"), {"source": SAFETY_ALTERNATIVE_SOURCE})


def test_ai_quality_report_aggregates_run_logs_without_raw_payload():
    create_db_and_tables()
    marker = uuid4().hex
    with Session(engine) as session:
        session.add(AIRunLog(
            task_type="partner_simulation",
            prompt_id="partner.v1",
            prompt_version="2026-05-21",
            schema_version="v1",
            provider="deepseek",
            model="abab",
            outcome="success",
            payload_hash=f"sha256:{marker}",
            payload_summary_json=json.dumps({"keys": ["user_message"], "text_lengths": {"secret": len(marker)}}),
            response_summary_json=json.dumps({"keys": ["reply"], "raw_text_chars": 0}),
            latency_ms=240,
        ))
        session.add(AIRunLog(
            task_type="partner_simulation",
            prompt_id="partner.v1",
            prompt_version="2026-05-21",
            schema_version="v1",
            provider="deepseek",
            outcome="blocked_safety",
            fallback_reason="安全硬阻断",
            safety_risk_level="high",
            safety_flags_json=json.dumps(["manipulation"]),
            payload_hash=f"sha256:block-{marker}",
            latency_ms=0,
        ))
        session.commit()

    response = client.get("/api/analytics/ai-quality?limit=20")

    assert response.status_code == 200
    data = response.json()
    assert data["summary"]["runs"] >= 2
    assert data["summary"]["provider_attempts"] >= 1
    assert data["summary"]["provider_success_rate"] == 100
    assert data["summary"]["safety_block_rate"] > 0
    assert any(item["name"] == "blocked_safety" for item in data["outcome_breakdown"])
    assert any(item["name"] == "manipulation" for item in data["safety_flags"])
    assert marker not in json.dumps(data, ensure_ascii=False)


def test_ai_quality_safety_blocks_close_after_alternative_training_seeded():
    create_db_and_tables()
    _clear_safety_alternative_training()
    marker = uuid4().hex
    with Session(engine) as session:
        session.add(AIRunLog(
            task_type="rewrite_response",
            prompt_id="rewrite.v1",
            prompt_version="2026-05-31",
            schema_version="v1",
            provider="deepseek",
            outcome="blocked_safety",
            fallback_reason="安全硬阻断",
            safety_risk_level="high",
            safety_flags_json=json.dumps(["manipulation"]),
            payload_hash=f"sha256:safety-gap-{marker}",
            latency_ms=0,
        ))
        session.commit()

    before = client.get("/api/analytics/ai-quality?limit=20").json()
    assert before["safety_alternative_coverage"]["ready"] is False
    assert any(item["action"] == "扩充安全替代表达训练" for item in before["next_actions"])

    seed_safety_alternatives(TEST_DB_PATH)

    after = client.get("/api/analytics/ai-quality?limit=20").json()
    assert after["safety_alternative_coverage"]["ready"] is True
    assert not any(item["action"] == "扩充安全替代表达训练" for item in after["next_actions"])


def test_ai_failure_analysis_clusters_without_payload_leakage():
    create_db_and_tables()
    _clear_safety_alternative_training()
    marker = uuid4().hex
    with Session(engine) as session:
        session.add(AIRunLog(
            task_type="partner_simulation",
            prompt_id="partner.v1",
            prompt_version="2026-05-21",
            schema_version="v1",
            provider="deepseek",
            model="abab",
            outcome="provider_failure",
            fallback_reason="provider unavailable",
            payload_hash=f"sha256:failure-{marker}",
            payload_summary_json=json.dumps({"private_marker": marker}),
            latency_ms=5000,
        ))
        session.add(AIRunLog(
            task_type="partner_simulation",
            prompt_id="partner.v1",
            prompt_version="2026-05-21",
            schema_version="v1",
            provider="deepseek",
            model="abab",
            outcome="blocked_safety",
            fallback_reason="安全硬阻断",
            safety_risk_level="high",
            safety_flags_json=json.dumps(["coercion", "manipulation"]),
            payload_hash=f"sha256:safety-{marker}",
            latency_ms=0,
        ))
        session.commit()

    response = client.get("/api/analytics/ai-failure-analysis?limit=50")

    assert response.status_code == 200
    data = response.json()
    cluster_ids = {item["id"] for item in data["clusters"]}
    assert "provider_failure" in cluster_ids
    assert "safety_blocked" in cluster_ids
    assert data["summary"]["provider_failures"] >= 1
    assert data["summary"]["safety_blocks"] >= 1
    assert data["summary"]["failures"] >= 1
    assert any(item["name"] == "manipulation" for item in data["safety_flags"])
    assert marker not in json.dumps(data, ensure_ascii=False)


def test_ai_provider_diagnostics_redacts_secret_and_flags_http_400(monkeypatch):
    create_db_and_tables()
    marker = uuid4().hex
    monkeypatch.setattr("backend.api.analytics.ai_provider_client.api_key", f"secret-{marker}")
    monkeypatch.setattr("backend.api.analytics.ai_provider_client.provider", "deepseek")
    monkeypatch.setattr("backend.api.analytics.ai_provider_client.model", "deepseek-chat")
    monkeypatch.setattr("backend.api.analytics.ai_provider_client.base_url", "https://api.deepseek.com?token=secret")
    monkeypatch.setattr("backend.api.analytics.ai_provider_client.chat_path", "/chat/completions")
    with Session(engine) as session:
        session.add(AIRunLog(
            task_type="score_response",
            prompt_id="score.v1",
            prompt_version="2026-05-21",
            schema_version="v1",
            provider="deepseek",
            model="deepseek-chat",
            outcome="provider_failure",
            fallback_reason="Provider HTTP 错误: 400",
            payload_hash=f"sha256:provider-{marker}",
            payload_summary_json=json.dumps({"private_marker": marker}),
            latency_ms=100,
        ))
        session.commit()

    response = client.get("/api/analytics/ai-provider-diagnostics?limit=50")

    assert response.status_code == 200
    data = response.json()
    serialized = json.dumps(data, ensure_ascii=False)
    assert data["provider"]["configured"] is True
    assert data["provider"]["api_key_present"] is True
    assert data["provider"]["base_url"] == "https://api.deepseek.com"
    assert data["request_shape"]["url"] == "https://api.deepseek.com/chat/completions"
    assert data["request_shape"]["schema_hash"].startswith("sha256:")
    assert "deepseek_deprecated_model" in {item["check"] for item in data["provider"]["compatibility"]}
    assert data["risk_level"] in {"medium", "high"}
    assert any(item["name"] == "400" for item in data["recent"]["http_statuses"])
    assert any(item["check"] == "http_400" for item in data["diagnostics"])
    assert any(item["check"] == "deepseek_deprecated_model" for item in data["diagnostics"])
    assert data["failure_playbook"]["risk_level"] == "high"
    assert any(item["id"] == "local_request_shape" for item in data["failure_playbook"]["root_cause_matrix"])
    assert data["failure_playbook"]["quality_gate"]["request_shape_has_known_risks"] is True
    assert marker not in serialized
    assert f"secret-{marker}" not in serialized
    assert "token=secret" not in serialized


def test_ai_provider_diagnostics_accepts_current_deepseek_openai_shape(monkeypatch):
    create_db_and_tables()
    monkeypatch.setattr("backend.api.analytics.ai_provider_client.api_key", "unit-key")
    monkeypatch.setattr("backend.api.analytics.ai_provider_client.provider", "deepseek")
    monkeypatch.setattr("backend.api.analytics.ai_provider_client.mode", "openai")
    monkeypatch.setattr("backend.api.analytics.ai_provider_client.model", "deepseek-v4-pro")
    monkeypatch.setattr("backend.api.analytics.ai_provider_client.base_url", "https://api.deepseek.com")
    monkeypatch.setattr("backend.api.analytics.ai_provider_client.chat_path", "")
    monkeypatch.setattr("backend.api.analytics.ai_provider_client.reasoning_effort", "")
    monkeypatch.setattr("backend.api.analytics.ai_provider_client.thinking_enabled", False)

    response = client.get("/api/analytics/ai-provider-diagnostics?limit=1")

    assert response.status_code == 200
    data = response.json()
    assert data["provider"]["base_url"] == "https://api.deepseek.com"
    assert data["provider"]["chat_path"] == "/chat/completions"
    assert data["request_shape"]["payload_keys"] == ["messages", "model", "temperature"]
    assert data["request_shape"]["compatibility_risks"] == []
    assert any(item["check"] == "provider_config_shape" and item["status"] == "passed" for item in data["provider"]["compatibility"])
    assert not any(item["check"] == "deepseek_deprecated_model" for item in data["diagnostics"])


def test_ai_provider_diagnostics_accepts_current_deepseek_shape(monkeypatch):
    create_db_and_tables()
    monkeypatch.setattr("backend.api.analytics.ai_provider_client.api_key", "unit-key")
    monkeypatch.setattr("backend.api.analytics.ai_provider_client.provider", "deepseek")
    monkeypatch.setattr("backend.api.analytics.ai_provider_client.mode", "openai")
    monkeypatch.setattr("backend.api.analytics.ai_provider_client.model", "deepseek-v4-pro")
    monkeypatch.setattr("backend.api.analytics.ai_provider_client.base_url", "https://api.deepseek.com")
    monkeypatch.setattr("backend.api.analytics.ai_provider_client.chat_path", "/chat/completions")
    monkeypatch.setattr("backend.api.analytics.ai_provider_client.reasoning_effort", "high")
    monkeypatch.setattr("backend.api.analytics.ai_provider_client.thinking_enabled", True)

    response = client.get("/api/analytics/ai-provider-diagnostics?limit=1")

    assert response.status_code == 200
    data = response.json()
    assert data["provider"]["name"] == "deepseek"
    assert data["provider"]["base_url"] == "https://api.deepseek.com"
    assert data["provider"]["chat_path"] == "/chat/completions"
    assert data["request_shape"]["url"] == "https://api.deepseek.com/chat/completions"
    assert data["request_shape"]["payload_keys"] == ["messages", "model", "reasoning_effort", "temperature", "thinking"]
    assert data["request_shape"]["compatibility_risks"] == []
    assert any(item["check"] == "provider_config_shape" and item["status"] == "passed" for item in data["provider"]["compatibility"])


def test_ai_provider_failure_playbook_classifies_http_400_without_local_shape_risk(monkeypatch):
    create_db_and_tables()
    marker = uuid4().hex
    monkeypatch.setattr("backend.api.analytics.ai_provider_client.api_key", f"secret-{marker}")
    monkeypatch.setattr("backend.api.analytics.ai_provider_client.provider", "deepseek")
    monkeypatch.setattr("backend.api.analytics.ai_provider_client.mode", "openai")
    monkeypatch.setattr("backend.api.analytics.ai_provider_client.model", "deepseek-v4-pro")
    monkeypatch.setattr("backend.api.analytics.ai_provider_client.base_url", "https://api.deepseek.com")
    monkeypatch.setattr("backend.api.analytics.ai_provider_client.chat_path", "")
    with Session(engine) as session:
        session.add(AIRunLog(
            task_type="score_response",
            prompt_id="score.v1",
            prompt_version="2026-05-22",
            schema_version="v1",
            provider="deepseek",
            model="deepseek-v4-pro",
            outcome="provider_failure",
            fallback_reason="Provider HTTP 错误: 400",
            payload_hash=f"sha256:http400-{marker}",
            payload_summary_json=json.dumps({"private_marker": marker}),
            response_summary_json=json.dumps({"private_response": marker}),
            latency_ms=120,
        ))
        session.commit()

    response = client.get("/api/analytics/ai-provider-diagnostics?limit=50")

    assert response.status_code == 200
    data = response.json()
    serialized = json.dumps(data, ensure_ascii=False)
    playbook = data["failure_playbook"]
    assert data["request_shape"]["compatibility_risks"] == []
    assert playbook["risk_level"] == "high"
    assert data["local_remediation"]["deepseek_400_optional_param_retry"] is True
    assert data["local_remediation"]["safety_hard_blocks_preserved"] is True
    assert playbook["quality_gate"]["http_400_without_local_shape_risk"] is True
    assert playbook["quality_gate"]["stores_prompt_or_response_text"] is False
    assert any(item["id"] == "account_or_service_http_400" for item in playbook["root_cause_matrix"])
    assert any(item["id"] == "controlled_live_probe" for item in playbook["regression_cases"])
    assert marker not in serialized
    assert f"secret-{marker}" not in serialized
    assert "token=secret" not in serialized
    assert "private_response" not in serialized


def test_ai_provider_failure_playbook_classifies_auth_permission_status(monkeypatch):
    create_db_and_tables()
    marker = uuid4().hex
    monkeypatch.setattr("backend.api.analytics.ai_provider_client.api_key", f"secret-{marker}")
    monkeypatch.setattr("backend.api.analytics.ai_provider_client.provider", "deepseek")
    monkeypatch.setattr("backend.api.analytics.ai_provider_client.mode", "openai")
    monkeypatch.setattr("backend.api.analytics.ai_provider_client.model", "deepseek-v4-pro")
    monkeypatch.setattr("backend.api.analytics.ai_provider_client.base_url", "https://api.deepseek.com")
    monkeypatch.setattr("backend.api.analytics.ai_provider_client.chat_path", "")
    with Session(engine) as session:
        session.add(AIRunLog(
            task_type="simulate_partner",
            prompt_id="partner.v1",
            prompt_version="2026-05-23",
            schema_version="v1",
            provider="deepseek",
            model="deepseek-v4-pro",
            outcome="provider_failure",
            fallback_reason="Provider HTTP 错误: 403",
            payload_hash=f"sha256:http403-{marker}",
            payload_summary_json=json.dumps({"private_marker": marker}),
            response_summary_json=json.dumps({"private_response": marker}),
            latency_ms=160,
        ))
        session.commit()

    response = client.get("/api/analytics/ai-provider-diagnostics?limit=50")

    assert response.status_code == 200
    data = response.json()
    serialized = json.dumps(data, ensure_ascii=False)
    playbook = data["failure_playbook"]
    assert any(item["check"] == "http_403" for item in data["diagnostics"])
    assert any(item["id"] == "auth_or_model_permission" for item in playbook["root_cause_matrix"])
    assert any(item["id"] == "auth_permission_regression" for item in playbook["regression_cases"])
    assert playbook["quality_gate"]["auth_or_permission_error"] is True
    assert marker not in serialized
    assert f"secret-{marker}" not in serialized
    assert "private_response" not in serialized


def test_ai_provider_success_contract_reports_shape_gaps_without_payload_leakage(monkeypatch):
    create_db_and_tables()
    marker = uuid4().hex
    monkeypatch.setattr("backend.api.analytics.ai_provider_client.provider", "deepseek")
    monkeypatch.setattr("backend.api.analytics.ai_provider_client.model", "deepseek-v4-pro")
    with Session(engine) as session:
        session.add(AIRunLog(
            task_type="simulate_partner",
            prompt_id="partner.v1",
            prompt_version="2026-05-23",
            schema_version="v1",
            provider="deepseek",
            model="deepseek-v4-pro",
            outcome="success",
            payload_hash=f"sha256:ok-{marker}",
            payload_summary_json=json.dumps({"private_marker": marker}),
            response_summary_json=json.dumps({"keys": ["reply", "score", "suggestions"], "private_response": marker}),
            latency_ms=240,
        ))
        session.add(AIRunLog(
            task_type="simulate_partner",
            prompt_id="partner.v1",
            prompt_version="2026-05-23",
            schema_version="v1",
            provider="deepseek",
            model="deepseek-v4-pro",
            outcome="success_raw_text",
            payload_hash=f"sha256:raw-{marker}",
            response_summary_json=json.dumps({"keys": ["raw_text"], "raw_text_chars": 88, "private_response": marker}),
            latency_ms=300,
        ))
        session.add(AIRunLog(
            task_type="simulate_partner",
            prompt_id="partner.v1",
            prompt_version="2026-05-23",
            schema_version="v1",
            provider="deepseek",
            model="deepseek-v4-pro",
            outcome="provider_failure",
            fallback_reason="AI 响应缺少 reply",
            payload_hash=f"sha256:missing-{marker}",
            payload_summary_json=json.dumps({"private_marker": marker}),
            latency_ms=120,
        ))
        session.commit()

    response = client.get("/api/analytics/ai-provider-success-contract?limit=80")

    assert response.status_code == 200
    data = response.json()
    serialized = json.dumps(data, ensure_ascii=False)
    assert data["summary"]["runs"] >= 3
    assert data["summary"]["raw_text_rate"] > 0
    assert data["summary"]["provider_failure_rate"] > 0
    assert any(item["task_type"] == "simulate_partner" for item in data["task_matrix"])
    gap_ids = {item["id"] for item in data["contract_gaps"]}
    assert "raw_text_contract_gap" in gap_ids
    assert "missing_reply_alias_gap" in gap_ids
    assert isinstance(data["quality_gate"]["raw_text_needs_review"], bool)
    assert any("reply" in item["reason"] or "raw_text" in item["reason"] for item in data["next_actions"])
    assert marker not in serialized
    assert "private_response" not in serialized


def test_ai_provider_probe_dry_run_records_redacted_audit(monkeypatch):
    create_db_and_tables()
    marker = uuid4().hex
    monkeypatch.setattr("backend.api.analytics.ai_provider_client.api_key", f"secret-{marker}")
    monkeypatch.setattr("backend.api.analytics.ai_provider_client.provider", "deepseek")
    monkeypatch.setattr("backend.api.analytics.ai_provider_client.mode", "openai")
    monkeypatch.setattr("backend.api.analytics.ai_provider_client.model", "deepseek-v4-pro")
    monkeypatch.setattr("backend.api.analytics.ai_provider_client.base_url", "https://irrelevant.example/v1?token=secret")
    monkeypatch.setattr("backend.api.analytics.ai_provider_client.chat_path", "")

    response = client.post("/api/analytics/ai-provider-probe?dry_run=true")

    assert response.status_code == 200
    data = response.json()
    serialized = json.dumps(data, ensure_ascii=False)
    assert data["dry_run"] is True
    assert data["outcome"] == "planned"
    assert data["request_shape"]["schema_hash"].startswith("sha256:")
    assert marker not in serialized
    assert "secret" not in serialized
    with Session(engine) as session:
        log = session.get(AIProviderProbeLog, data["audit_log"]["id"])
    assert log is not None
    assert log.dry_run is True
    assert log.outcome == "planned"
    assert marker not in (log.request_shape_json or "")


def test_ai_provider_probe_live_call_requires_explicit_enable(monkeypatch):
    create_db_and_tables()
    marker = uuid4().hex
    monkeypatch.setattr("backend.api.analytics.ai_provider_client.api_key", f"secret-{marker}")
    monkeypatch.setattr("backend.api.analytics.ai_provider_client.live_probe_enabled", False)
    monkeypatch.setattr("backend.api.analytics.ai_provider_client.provider", "deepseek")
    monkeypatch.setattr("backend.api.analytics.ai_provider_client.mode", "openai")
    monkeypatch.setattr("backend.api.analytics.ai_provider_client.model", "deepseek-v4-pro")
    monkeypatch.setattr("backend.api.analytics.ai_provider_client.base_url", "https://irrelevant.example/v1")
    monkeypatch.setattr("backend.api.analytics.ai_provider_client.chat_path", "")

    response = client.post("/api/analytics/ai-provider-probe?dry_run=false")

    assert response.status_code == 409
    data = response.json()
    serialized = json.dumps(data, ensure_ascii=False)
    assert data["detail"]["outcome"] == "blocked_by_policy"
    assert data["detail"]["error_type"] == "live_probe_not_enabled"
    assert marker not in serialized
    with Session(engine) as session:
        log = session.get(AIProviderProbeLog, data["detail"]["audit_log"]["id"])
    assert log is not None
    assert log.dry_run is False
    assert log.outcome == "blocked_by_policy"


def test_ai_provider_probe_readiness_returns_safe_runbook_without_calling_provider(monkeypatch):
    create_db_and_tables()
    marker = uuid4().hex
    monkeypatch.setattr("backend.api.analytics.ai_provider_client.api_key", f"secret-{marker}")
    monkeypatch.setattr("backend.api.analytics.ai_provider_client.live_probe_enabled", False)
    monkeypatch.setattr("backend.api.analytics.ai_provider_client.provider", "deepseek")
    monkeypatch.setattr("backend.api.analytics.ai_provider_client.mode", "openai")
    monkeypatch.setattr("backend.api.analytics.ai_provider_client.model", "deepseek-v4-pro")
    monkeypatch.setattr("backend.api.analytics.ai_provider_client.base_url", "https://irrelevant.example/v1?token=secret")
    monkeypatch.setattr("backend.api.analytics.ai_provider_client.chat_path", "")

    dry = client.post("/api/analytics/ai-provider-probe?dry_run=true")
    response = client.get("/api/analytics/ai-provider-probe-readiness")

    assert dry.status_code == 200
    assert response.status_code == 200
    data = response.json()
    serialized = json.dumps(data, ensure_ascii=False)
    assert data["status"] == "policy_blocked"
    assert data["configured"] is True
    assert data["live_probe_enabled"] is False
    assert any(item["id"] == "live_probe_disabled" for item in data["blockers"])
    assert data["quality_gate"]["dry_run_required_first"] is True
    assert data["quality_gate"]["stores_prompt_or_response_text"] is False
    assert data["recent_probe_logs"]
    assert data["recent_probe_logs"][0]["schema_hash"].startswith("sha256:")
    assert marker not in serialized
    assert f"secret-{marker}" not in serialized
    assert "token=secret" not in serialized
    assert "healthcheck" not in serialized


def test_analytics_center_includes_provider_probe_readiness(monkeypatch):
    create_db_and_tables()
    monkeypatch.setattr("backend.api.analytics.ai_provider_client.api_key", "unit-key")
    monkeypatch.setattr("backend.api.analytics.ai_provider_client.live_probe_enabled", False)
    monkeypatch.setattr("backend.api.analytics.ai_provider_client.provider", "deepseek")
    monkeypatch.setattr("backend.api.analytics.ai_provider_client.mode", "openai")
    monkeypatch.setattr("backend.api.analytics.ai_provider_client.model", "deepseek-v4-pro")
    monkeypatch.setattr("backend.api.analytics.ai_provider_client.base_url", "https://irrelevant.example/v1")
    monkeypatch.setattr("backend.api.analytics.ai_provider_client.chat_path", "")

    response = client.get("/api/analytics/center?limit=30")

    assert response.status_code == 200
    readiness = response.json()["sections"]["provider"]["probe_readiness"]
    assert readiness["status"] == "policy_blocked"
    assert readiness["quality_gate"]["explicit_live_enable_required"] is True
    assert any(step["command"] == "keep dry_run=true" for step in readiness["runbook"])


def test_relationship_trends_aggregate_cross_session_state_changes():
    create_db_and_tables()
    marker = uuid4().hex
    with Session(engine) as session:
        practice = PracticeSession(
            scenario_id=f"trend-{marker}",
            scenario_name="跨会话趋势测试",
            attachment_style="avoidant",
            difficulty="medium",
            response_style="soft",
            total_turns=2,
            average_score=78,
            current_state_json=json.dumps({
                "trust": 62,
                "stress": 28,
                "boundary": 30,
                "boundary_safety": 76,
                "connection": 61,
                "state_label": "连接修复",
                "next_focus": "继续轻验证",
            }),
        )
        session.add(practice)
        session.commit()
        session.refresh(practice)
        session.add(PracticeEvent(
            session_id=int(practice.id or 0),
            turn_index=1,
            user_message="我听见你现在想先安静一下。",
            partner_reply="谢谢你没有逼我。",
            score=72,
            relationship_state_json=json.dumps({
                "trust": 50,
                "stress": 40,
                "boundary": 38,
                "boundary_safety": 60,
                "connection": 45,
                "state_label": "观察中",
                "next_focus": "先观察线索",
            }),
        ))
        session.add(PracticeEvent(
            session_id=int(practice.id or 0),
            turn_index=2,
            user_message="你想晚点聊也可以，我会在。",
            partner_reply="这样我舒服很多。",
            score=84,
            relationship_state_json=json.dumps({
                "trust": 62,
                "stress": 28,
                "boundary": 30,
                "boundary_safety": 76,
                "connection": 61,
                "state_label": "连接修复",
                "next_focus": "继续轻验证",
            }),
        ))
        session.commit()

    response = client.get("/api/analytics/relationship-trends?limit=20")

    assert response.status_code == 200
    data = response.json()
    assert data["summary"]["sessions"] >= 1
    assert data["summary"]["repair_index"] > 50
    assert data["average_state_delta"]["trust"] > 0
    assert data["average_state_delta"]["stress"] < 0
    assert any(item["scenario_name"] == "跨会话趋势测试" for item in data["session_trend"])


def test_analytics_center_aggregates_quality_domains_without_payload_leakage():
    create_db_and_tables()
    marker = uuid4().hex
    with Session(engine) as session:
        session.add(AIRunLog(
            task_type="analysis_center",
            prompt_id="center.v1",
            prompt_version="2026-05-21",
            schema_version="v1",
            provider="deepseek",
            model="deepseek-v4-pro",
            outcome="provider_failure",
            fallback_reason="Provider HTTP 错误: 400",
            payload_hash=f"sha256:center-{marker}",
            payload_summary_json=json.dumps({"private_marker": marker}),
            latency_ms=80,
        ))
        session.commit()

    response = client.get("/api/analytics/center?limit=50")

    assert response.status_code == 200
    data = response.json()
    serialized = json.dumps(data, ensure_ascii=False)
    assert {"scorecard", "alerts", "timeline", "sections"} <= set(data)
    score_ids = {item["id"] for item in data["scorecard"]}
    assert {"ai_success", "provider_failure", "gold_conflicts", "import_quality", "vector_recall", "repair_index", "scheduler_health"} <= score_ids
    assert "ai_quality" in data["sections"]
    assert "gold_set" in data["sections"]
    assert "training_trends" in data["sections"]
    scheduler = data["sections"]["scheduler"]
    assert scheduler["status"] in {"healthy", "needs_attention"}
    assert scheduler["jobs"]
    assert {"state_file_exists", "all_jobs_observed", "no_failed_latest_runs", "no_stale_required_jobs"} <= set(scheduler["quality_gate"])
    assert isinstance(scheduler["recovery_runbook"], list)
    assert marker not in serialized
    assert "private_marker" not in serialized


def test_audit_center_aggregates_recent_events_without_sensitive_text():
    create_db_and_tables()
    marker = uuid4().hex
    with Session(engine) as session:
        session.add(PipelineRunLog(
            target_type="content_import_issue",
            target_id=991,
            action="import_issue.resolve",
            from_status="open",
            to_status="resolved",
            result_json=json.dumps({
                "reviewer_id": "ops-reviewer",
                "resolution_hash": f"sha256:{marker}",
                "resolution": f"private-resolution-{marker}",
                "issue_count": 1,
            }, ensure_ascii=False),
            message=f"resolved with private-resolution-{marker}",
        ))
        session.add(AIRunLog(
            task_type="audit_center_probe",
            prompt_id="audit.v1",
            prompt_version="2026-05-22",
            schema_version="v1",
            provider="deepseek",
            model="deepseek-v4-pro",
            outcome="provider_failure",
            fallback_reason="Provider HTTP 错误: 400",
            payload_hash=f"sha256:audit-{marker}",
            payload_summary_json=json.dumps({"private_marker": marker}),
            latency_ms=120,
        ))
        session.add(AIProviderProbeLog(
            provider="deepseek",
            mode="openai",
            model="deepseek-v4-pro",
            request_shape_json=json.dumps({"schema_hash": f"sha256:shape-{marker}", "url": "https://api.example/v1/chat/completions"}),
            dry_run=True,
            outcome="planned",
            latency_ms=0,
        ))
        session.commit()

    response = client.get("/api/analytics/audit-center?limit=50")

    assert response.status_code == 200
    data = response.json()
    serialized = json.dumps(data, ensure_ascii=False)
    assert data["summary"]["events"] >= 3
    modules = {item["name"] for item in data["filters"]["modules"]}
    assert {"import", "ai", "provider"} <= modules
    event_ids = {item["id"].split(":")[0] for item in data["events"]}
    assert {"pipeline", "ai_run", "provider_probe"} <= event_ids
    assert any(item["module"] == "ai" and item["status"] == "failed" for item in data["events"])
    assert any(item["module"] == "import" and item["actor"] == "ops-reviewer" for item in data["events"])
    assert marker not in serialized
    assert "private_marker" not in serialized
    assert "private-resolution" not in serialized


def test_runtime_event_records_frontend_errors_and_appears_in_audit_center():
    create_db_and_tables()
    marker = uuid4().hex

    response = client.post("/api/analytics/runtime-events", json={
        "source": "frontend",
        "event_type": "api_error",
        "severity": "medium",
        "route": f"/trainer?token={marker}",
        "method": "GET",
        "endpoint": f"/training/next?secret={marker}",
        "http_status": 502,
        "message": f"Bearer secret-{marker} upstream failed",
        "context": {
            "status_text": "Bad Gateway",
            "online": True,
            "request_body": f"private-{marker}",
        },
    })

    assert response.status_code == 200
    data = response.json()
    serialized = json.dumps(data, ensure_ascii=False)
    assert data["status"] == "recorded"
    assert data["severity"] == "high"
    assert data["message_hash"].startswith("sha256:")
    assert marker not in serialized
    assert "secret-" not in serialized

    audit_response = client.get("/api/analytics/audit-center?limit=30&module=runtime")

    assert audit_response.status_code == 200
    audit = audit_response.json()
    audit_serialized = json.dumps(audit, ensure_ascii=False)
    assert audit["summary"]["events"] >= 1
    assert audit["summary"]["module_filter"] == "runtime"
    assert any(item["module"] == "runtime" and item["status"] == "failed" for item in audit["events"])
    runtime_event = next(item for item in audit["events"] if item["module"] == "runtime")
    assert runtime_event["details"]["route"] == "/trainer"
    assert runtime_event["details"]["endpoint"] == "/training/next"
    assert runtime_event["details"]["context"]["status_text"] == "Bad Gateway"
    assert "request_body" not in runtime_event["details"]["context"]
    assert marker not in audit_serialized
    assert "secret-" not in audit_serialized
