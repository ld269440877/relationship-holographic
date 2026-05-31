import json
from uuid import uuid4

import httpx
from fastapi.testclient import TestClient
from sqlmodel import Session, select

from backend.api.evolution import (
    BatchRollbackPlanRequest,
    ImportIssueActionRequest,
    ImportQualityRepairRequest,
    PipelineAdvanceRequest,
    PipelineBatchRunRequest,
    RawContentCreate,
    ScheduledEvolutionRunRequest,
    SourceFetchRequest,
    SourceRegistryCreate,
    _build_import_quality_report,
    _build_safety_events_report,
    _loads_dict,
    _loads_list,
    _recent_safety_events,
    advance_pipeline,
    create_raw_item,
    create_source_registry,
    dedupe_report,
    fetch_registered_sources,
    import_batch_rollback_plan,
    import_quality_issue_action,
    import_quality_repair_plan,
    pipeline,
    run_pipeline_batch,
    run_weekly_scheduler,
)
from backend.api.learning import curriculum_graph, framework
from backend.database.connection import create_db_and_tables, engine
from backend.main import app
from backend.models.evolution import PipelineRunLog
from backend.models.knowledge import ContentImportBatch, ContentImportIssue, KnowledgeEntry, KnowledgeSection
from backend.models.resource import ResourceLibrary
from backend.models.sample import InteractionSample
from backend.models.training import SafetyEvent


def test_learning_framework_exposes_primitive_and_visual_layers():
    data = framework()

    assert data["primitive_ladder"][0]["name"] == "元事实"
    assert len(data["classification_tree"]) >= 12
    assert any(item["label"] == "How much" for item in data["five_w_two_h"])
    assert any(item["id"] == "emotion_flow_curve" for item in data["visual_components"])
    assert any(item["nature"] == "恶" for item in data["three_natures_management"])
    assert {item["id"] for item in data["material_library"]} >= {
        "micro_signal",
        "emotion_flow",
        "boundary_consent",
        "flirty_tension",
        "conflict_repair",
        "long_connection",
        "humor_interaction",
        "nvc_choice",
        "deep_emotional_connection",
        "self_disclosure_depth",
        "relationship_need_calibration",
        "developmental_emotion_transition",
    }
    first_material = data["material_library"][0]
    assert first_material["scene_example"]["better_response"]
    assert len(first_material["degree_scale"]) == 5
    assert len(first_material["dialogue_template"]) >= 4
    deep_material = next(item for item in data["material_library"] if item["id"] == "deep_emotional_connection")
    assert len(deep_material["technique_cards"]) == 6
    assert {card["id"] for card in deep_material["technique_cards"]} == {
        "open_question",
        "closed_question",
        "keyword_capture",
        "fact_emotion_split",
        "feeling_identification",
        "mirror_technique",
    }
    assert deep_material["technique_cards"][0]["name"] == "开放式提问"
    assert deep_material["technique_cards"][1]["name"] == "封闭式问题"
    assert len(deep_material["technique_cards"][0]["comparisons"]) == 4
    assert deep_material["technique_cards"][3]["degree_scale"][0]["label"]
    feeling_card = deep_material["technique_cards"][4]
    assert feeling_card["name"] == "感受识别与命名"
    assert len(feeling_card["feeling_spectrum"]) == 4
    assert feeling_card["feeling_spectrum"][0]["body_cues"]
    assert any("这个理解接近吗" in pattern for pattern in deep_material["technique_cards"][5]["sentence_patterns"])
    disclosure_material = next(item for item in data["material_library"] if item["id"] == "self_disclosure_depth")
    assert disclosure_material["name"] == "自我表露深度"
    assert disclosure_material["technique_cards"][0]["name"] == "自我表露五级刻度"
    assert disclosure_material["technique_cards"][0]["degree_scale"][4]["label"] == "存在层"
    assert len(disclosure_material["technique_cards"][0]["feeling_spectrum"]) == 4
    need_material = next(item for item in data["material_library"] if item["id"] == "relationship_need_calibration")
    assert need_material["name"] == "关系需求校准"
    assert need_material["technique_cards"][0]["name"] == "需求去偏五步法"
    assert len(need_material["technique_cards"][0]["comparisons"]) == 4
    assert "女人都这样" in need_material["technique_cards"][0]["bad_patterns"]
    transition_material = next(item for item in data["material_library"] if item["id"] == "developmental_emotion_transition")
    assert transition_material["name"] == "发展性情绪跃迁"
    assert {card["id"] for card in transition_material["technique_cards"]} == {
        "three_layer_model",
        "four_dimension_locator",
        "transition_mechanism",
        "age_scaffold",
    }
    assert transition_material["technique_cards"][1]["name"] == "情绪四维定位"
    assert transition_material["technique_cards"][2]["degree_scale"][2]["label"] == "翻译"
    assert any(item["name"] == "定位情绪四维" for item in data["learning_map"])
    assert any(gate["gate"] == "发展适配" for gate in data["quality_gates"])
    assert any(template["module"] == "资源海洋" for template in data["module_templates"])
    assert any(gate["gate"] == "上下文一致" for gate in data["quality_gates"])
    assert data["learning_map"][0]["name"] == "看见事实"


def test_curriculum_graph_exposes_stage_tasks_evidence_and_edges():
    create_db_and_tables()
    with Session(engine) as session:
        graph = curriculum_graph(session)

        assert graph["version"].startswith("2026-05-21.curriculum")
        assert len(graph["nodes"]) == 9
        assert len(graph["edges"]) == 8
        assert graph["current_node_id"]
        assert 0 <= graph["overall_progress"] <= 100
        assert graph["nodes"][0]["primitive"] == "注意力转向外部"
        assert graph["nodes"][2]["tools"]
        assert graph["nodes"][2]["tasks"]
        assert graph["nodes"][2]["promotion_rule"]
        assert "attempts_count" in graph["nodes"][2]["evidence"]
        assert graph["practice_plan"]["minimum_action"]
        assert graph["evidence_summary"]["principle"].startswith("晋级必须看证据")
        assert graph["visual_layers"][0]["id"] == "path_graph"


def test_evolution_pipeline_metadata_flow():
    create_db_and_tables()
    unique = uuid4().hex
    with Session(engine) as session:
        source = create_source_registry(
            SourceRegistryCreate(
                source_uuid=f"source_pytest_{unique}",
                name=f"pytest 元数据来源 {unique}",
                source_type="manual",
                url=f"https://example.com/relationship-source/{unique}",
            ),
            session,
        )
        raw = create_raw_item(
            RawContentCreate(
                raw_uuid=f"raw_pytest_{unique}",
                source_id=source["id"],
                title="pytest 候选关系模式",
                url=f"https://example.com/relationship-source/{unique}/item",
                content="公开摘要：连接请求应被转向而不是忽略。",
                processing_status="annotated",
            ),
            session,
        )

        assert source["source_uuid"].startswith("source_")
        assert raw["content_hash"].startswith("sha256:")

        data = pipeline(session)
        assert data["stages"][0]["id"] == "source_registry"
        assert data["stages"][0]["count"] >= 1
        assert data["stages"][1]["count"] >= 1
        assert data["visual_metrics"]["review_publish_funnel"][0]["id"] == "sources"
        assert "source_quality_matrix" in data["visual_metrics"]
        assert "learning_increment" in data["visual_metrics"]
        assert "source_type" in data["classification_axes"]
        assert data["next_actions"]

        advanced = advance_pipeline(
            PipelineAdvanceRequest(
                target_type="raw_content",
                target_id=raw["id"],
                action="review",
                result={"quality_score": 86, "safety_score": 0.97},
                message="pytest 审核通过",
            ),
            session,
        )
        assert advanced["from_status"] == "annotated"
        assert advanced["to_status"] == "reviewed"

        after = pipeline(session)
        assert after["recent_logs"][0]["message"] == "pytest 审核通过"


def test_evolution_pipeline_handlers_create_annotation_and_asset_versions():
    create_db_and_tables()
    unique = uuid4().hex
    with Session(engine) as session:
        raw = create_raw_item(
            RawContentCreate(
                raw_uuid=f"raw_handler_{unique}",
                title="pytest 自动处理器候选",
                content="公开摘要：用合规抽象生成训练资产。",
                privacy_risk=0.7,
                copyright_risk=0.8,
            ),
            session,
        )

        sanitized = advance_pipeline(
            PipelineAdvanceRequest(
                target_type="raw_content",
                target_id=raw["id"],
                action="sanitize",
                result={"privacy_risk": 0.12, "copyright_risk": 0.22},
            ),
            session,
        )
        deduped = advance_pipeline(
            PipelineAdvanceRequest(target_type="raw_content", target_id=raw["id"], action="dedupe"),
            session,
        )
        annotated = advance_pipeline(
            PipelineAdvanceRequest(
                target_type="raw_content",
                target_id=raw["id"],
                action="annotate",
                result={"confidence": 0.82, "status": "reviewed"},
            ),
            session,
        )
        annotation_effect = annotated["effects"][0]
        published = advance_pipeline(
            PipelineAdvanceRequest(
                target_type="annotation_job",
                target_id=annotation_effect["id"],
                action="publish",
                result={"version": "v-test", "review_status": "reviewed"},
            ),
            session,
        )

        assert sanitized["effects"][0]["raw_storage_policy"] == "metadata_only"
        assert sanitized["effects"][0]["privacy_risk"] == 0.12
        assert deduped["effects"][0]["decision"] in {"unique_enough", "duplicate_review_needed"}
        assert annotation_effect["type"] == "annotation_job"
        assert annotation_effect["status"] == "reviewed"
        assert published["effects"][0]["type"] == "training_asset_version"

        data = pipeline(session)
        assert data["stages"][2]["count"] >= 1
        assert data["stages"][3]["count"] >= 1
        assert data["annotation_jobs"][0]["result"]["source_trace"]["raw_uuid"].startswith("raw_handler_")
        assert data["asset_versions"][0]["source_trace"]["annotation_job_id"] == annotation_effect["id"]


def test_evolution_batch_pipeline_runs_life_cycle_and_report():
    create_db_and_tables()
    unique = uuid4().hex
    with Session(engine) as session:
        source = create_source_registry(
            SourceRegistryCreate(
                source_uuid=f"source_batch_{unique}",
                name=f"pytest 批量来源 {unique}",
                source_type="manual",
                url=f"https://example.com/batch/{unique}",
            ),
            session,
        )
        raw = create_raw_item(
            RawContentCreate(
                raw_uuid=f"raw_batch_{unique}",
                source_id=source["id"],
                title=f"pytest 批量约会邀请样本 {unique}",
                content="公开摘要：对方发出低压力邀约信号，需要承接情绪和给退路。",
                privacy_risk=0.8,
                copyright_risk=0.7,
            ),
            session,
        )

        dry = run_pipeline_batch(PipelineBatchRunRequest(limit=5, raw_ids=[raw["id"]], dry_run=True), session)
        result = run_pipeline_batch(
            PipelineBatchRunRequest(
                limit=10,
                raw_ids=[raw["id"]],
                actions=["sanitize", "dedupe", "annotate", "publish", "report"],
                duplicate_policy="annotate_duplicates",
                publish_review_status="published",
            ),
            session,
        )

        assert dry["dry_run"] is True
        assert raw["id"] is not None
        assert result["summary"]["sanitized"] >= 1
        assert result["summary"]["deduped"] >= 1
        assert result["summary"]["annotated"] >= 1
        assert result["summary"]["asset_versions"] >= 1
        assert result["summary"]["published_assets"] >= 1
        assert result["report"]["promoted_samples_count"] >= 1
        assert result["pipeline"]["stages"][3]["count"] >= 1
        assert any(event["target_type"] == "annotation_job" for event in result["events"])

        after = pipeline(session)
        raw_card = next(item for item in after["raw_items"] if item["raw_uuid"] == f"raw_batch_{unique}")
        assert raw_card["privacy_risk"] <= 0.2
        assert raw_card["copyright_risk"] <= 0.35
        funnel = after["visual_metrics"]["review_publish_funnel"]
        assert funnel[-1]["id"] == "published"
        assert after["visual_metrics"]["learning_increment"]["published_assets"] >= 1
        assert after["visual_metrics"]["safety_risk_trend"]


def test_evolution_batch_pipeline_skips_semantic_duplicates():
    create_db_and_tables()
    unique = uuid4().hex
    with Session(engine) as session:
        raw_a = create_raw_item(
            RawContentCreate(
                raw_uuid=f"raw_duplicate_a_{unique}",
                title=f"pytest 重复 情绪 修复 样本 {unique}",
                content="公开摘要：重复候选 A。",
            ),
            session,
        )
        raw_b = create_raw_item(
            RawContentCreate(
                raw_uuid=f"raw_duplicate_b_{unique}",
                title=f"pytest 重复 情绪 修复 样本 {unique}",
                content="公开摘要：重复候选 B。",
            ),
            session,
        )

        result = run_pipeline_batch(
            PipelineBatchRunRequest(
                limit=20,
                raw_ids=[raw_a["id"], raw_b["id"]],
                actions=["sanitize", "dedupe", "annotate"],
                duplicate_policy="skip_annotate",
            ),
            session,
        )

        assert result["summary"]["duplicate_review_needed"] >= 1
        assert result["summary"]["skipped"] >= 1


def test_evolution_dedupe_report_groups_hash_and_semantic_duplicates():
    create_db_and_tables()
    unique = uuid4().hex
    with Session(engine) as session:
        create_raw_item(
            RawContentCreate(
                raw_uuid=f"raw_pipeline_hash_a_{unique}",
                title=f"同一来源复核候选 {unique}",
                content=f"同一段公开摘要 {unique}",
            ),
            session,
        )
        create_raw_item(
            RawContentCreate(
                raw_uuid=f"raw_pipeline_hash_b_{unique}",
                title=f"同一来源复核候选副本 {unique}",
                content=f"同一段公开摘要 {unique}",
            ),
            session,
        )
        create_raw_item(
            RawContentCreate(
                raw_uuid=f"raw_pipeline_sem_a_{unique}",
                title=f"情绪 修复 边界 低压力 邀请 {unique}",
                content=f"语义重复 A {unique}",
            ),
            session,
        )
        create_raw_item(
            RawContentCreate(
                raw_uuid=f"raw_pipeline_sem_b_{unique}",
                title=f"情绪 修复 边界 低压力 邀请 {unique}",
                content=f"语义重复 B {unique}",
            ),
            session,
        )

        report = dedupe_report(limit=500, session=session)

        assert report["summary"]["clusters"] >= 2
        assert report["summary"]["exact_clusters"] >= 1
        assert report["summary"]["semantic_clusters"] >= 1
        assert report["summary"]["duplicate_review_needed"] >= 4


def test_registered_source_fetch_creates_metadata_only_raw_candidate(monkeypatch):
    create_db_and_tables()
    unique = uuid4().hex

    def fake_get(url: str, *, timeout: float, follow_redirects: bool) -> httpx.Response:
        assert timeout == 5.0
        assert follow_redirects is True
        return httpx.Response(
            200,
            text="<html><title>pytest 世界级关系研究摘要</title></html>",
            request=httpx.Request("GET", url),
            headers={"etag": f"pytest-{unique}"},
        )

    monkeypatch.setattr("backend.api.evolution.httpx.get", fake_get)

    with Session(engine) as session:
        source = create_source_registry(
            SourceRegistryCreate(
                source_uuid=f"source_fetch_{unique}",
                name=f"pytest 合规来源 {unique}",
                source_type="research",
                url=f"https://example.com/research/{unique}",
            ),
            session,
        )

        result = fetch_registered_sources(
            SourceFetchRequest(source_ids=[source["id"]], dry_run=False),
            session,
        )

        assert result["dry_run"] is False
        assert result["sources_scanned"] == 1
        assert result["candidates"][0]["raw_item"]["title"] == "pytest 世界级关系研究摘要"
        assert result["candidates"][0]["raw_item"]["raw_storage_policy"] == "metadata_only"
        assert result["candidates"][0]["raw_item"]["copyright_risk"] == 0.18
        assert "不保存第三方全文" in result["principle"]


def test_import_quality_and_safety_reports_are_auditable():
    create_db_and_tables()
    unique = uuid4().hex
    with Session(engine) as session:
        batch = ContentImportBatch(
            source_name=f"pytest_import_{unique}.json",
            source_type="json",
            imported_sections=1,
            imported_entries=2,
            skipped_entries=1,
            issues_count=1,
            report_json='{"entries":2}',
        )
        session.add(batch)
        session.commit()
        session.refresh(batch)
        session.add(
            ContentImportIssue(
                batch_id=batch.id,
                source_name=batch.source_name,
                source_id=f"issue_{unique}",
                severity="warning",
                message="字段缺失",
            )
        )
        session.add(
            SafetyEvent(
                task_type=f"pytest_safety_{unique}",
                risk_level="high",
                flags_json='["manipulation"]',
                payload_hash=f"sha256:{unique}",
                payload_preview="测试安全事件",
                alternatives_json='["尊重边界"]',
                blocked=True,
            )
        )
        session.commit()

        quality = _build_import_quality_report(session)
        safety = _build_safety_events_report(_recent_safety_events(session, 50))

        assert quality["totals"]["batches"] >= 1
        assert quality["totals"]["issues"] >= 1
        assert "samples" in quality["field_completeness"]
        assert quality["quality_score"] >= 0
        assert safety["summary"]["blocked"] >= 1
        assert "manipulation" in safety["summary"]["top_flags"]


def test_import_batch_rollback_plan_is_non_destructive_and_auditable():
    create_db_and_tables()
    unique = uuid4().hex
    source_name = f"pytest_rollback_{unique}.json"
    with Session(engine) as session:
        section = KnowledgeSection(section_uuid=f"rollback_section_{unique}", name="rollback")
        session.add(section)
        session.commit()
        session.refresh(section)
        batch = ContentImportBatch(
            source_name=source_name,
            source_type="json",
            imported_sections=1,
            imported_entries=2,
            skipped_entries=1,
            issues_count=1,
            status="completed",
            report_json='{"rule_version":"import-v1","prompt_version":"none"}',
        )
        session.add(batch)
        session.commit()
        session.refresh(batch)
        issue = ContentImportIssue(
            batch_id=batch.id,
            source_name=source_name,
            source_id=f"rollback_issue_{unique}",
            severity="warning",
            message="回滚计划测试 issue",
        )
        entry = KnowledgeEntry(
            entry_uuid=f"rollback_entry_{unique}",
            section_id=section.id or 0,
            title="回滚知识",
            content="用于回滚计划测试。",
            source=source_name,
            review_status="published",
        )
        resource = ResourceLibrary(
            resource_uuid=f"rollback_resource_{unique}",
            type="story",
            category="回滚",
            title="回滚资源",
            content="场景：测试。TA说：你好。常见失误：忽略。更好回应：尊重边界。练习任务：复述。",
            source=source_name,
            review_status="published",
            tags="具体案例,边界",
            effectiveness_rating=9,
            quality_score=90,
        )
        session.add(issue)
        session.add(entry)
        session.add(resource)
        session.commit()
        session.refresh(batch)
        plan = import_batch_rollback_plan(BatchRollbackPlanRequest(batch_id=batch.id or 0), session)
        session.refresh(entry)
        session.refresh(resource)
        session.refresh(issue)

    assert plan["dry_run"] is True
    assert plan["impact"]["issues"] == 1
    assert plan["impact"]["knowledge_entries"] == 1
    assert plan["impact"]["resources"] == 1
    assert plan["planned_transitions"]["batch_status"]["to"] == "rollback_review"
    assert plan["quality_summary"]["duplicate_rate"] > 0
    assert plan["audit_payload"]["content_deleted"] is False
    assert plan["audit_payload"]["rule_version"] == "batch-rollback-plan-v1"
    assert entry.review_status == "published"
    assert resource.review_status == "published"
    assert issue.status == "open"


def test_import_quality_repair_plan_dry_run_and_apply():
    create_db_and_tables()
    unique = uuid4().hex
    with Session(engine) as session:
        section = KnowledgeSection(section_uuid=f"repair_section_{unique}", name="修复测试")
        session.add(section)
        session.commit()
        session.refresh(section)
        sample = InteractionSample(
            sample_uuid=f"repair_sample_{unique}",
            scenario_category="初识",
            difficulty_level=1,
            context="她说今天刚到新城市。",
            their_words="这里我还不太熟。",
            emotion_tags_json="[]",
            bad_response="那你自己查。",
            good_response_soft="刚来会有点陌生，我可以陪你慢慢熟悉。",
        )
        resource = ResourceLibrary(
            resource_uuid=f"repair_resource_{unique}",
            type="joke",
            category="破冰",
            title="轻松开场",
            content="今天的空气都适合认识新朋友。",
        )
        knowledge = KnowledgeEntry(
            entry_uuid=f"repair_knowledge_{unique}",
            section_id=section.id or 0,
            title="轻验证",
            content="把判断变成可被修正的问题。",
            category="沟通",
            source="pytest",
        )
        session.add(sample)
        session.add(resource)
        session.add(knowledge)
        session.commit()

        dry = import_quality_repair_plan(ImportQualityRepairRequest(limit=200, dry_run=True), session)
        assert dry["dry_run"] is True
        assert dry["plan"]["resources"]["usage_tip"] >= 1

        applied = import_quality_repair_plan(ImportQualityRepairRequest(limit=200, dry_run=False), session)
        session.refresh(sample)
        session.refresh(resource)
        session.refresh(knowledge)

        assert applied["dry_run"] is False
        assert applied["updated"]["samples"] >= 1
        assert sample.source_trace_json
        assert resource.usage_tip
        assert knowledge.source_metadata_json
        report = _build_import_quality_report(session)
        assert "repair_plan" in report
        assert report["quality_debt"]["auto_repairable_fields"] == 0
        assert report["quality_debt"]["status"] in {"clean", "manual_review_required"}


def test_import_issue_governance_resolve_reopen_and_audit_log():
    create_db_and_tables()
    unique = uuid4().hex
    with Session(engine) as session:
        batch = ContentImportBatch(
            source_name=f"pytest_issue_governance_{unique}.json",
            source_type="json",
            imported_sections=1,
            imported_entries=1,
            issues_count=1,
        )
        session.add(batch)
        session.commit()
        session.refresh(batch)
        issue = ContentImportIssue(
            batch_id=batch.id,
            source_name=batch.source_name,
            source_id=f"issue_governance_{unique}",
            severity="warning",
            message="历史来源缺少 reviewed 标记",
        )
        session.add(issue)
        session.commit()
        session.refresh(issue)

        before = _build_import_quality_report(session)
        assert before["quality_debt"]["manual_review_issues"] >= 1

        dry = import_quality_issue_action(
            ImportIssueActionRequest(
                issue_ids=[issue.id or 0],
                action="resolve",
                reviewer_id="pytest-reviewer",
                resolution="已核对来源登记与批次报告，确认为历史迁移告警。",
                dry_run=True,
            ),
            session,
        )
        session.refresh(issue)
        assert dry["dry_run"] is True
        assert dry["transitions"][0]["to_status"] == "resolved"
        assert issue.status == "open"

        resolved = import_quality_issue_action(
            ImportIssueActionRequest(
                issue_ids=[issue.id or 0],
                action="resolve",
                reviewer_id="pytest-reviewer",
                resolution="已核对来源登记与批次报告，确认为历史迁移告警。",
                dry_run=False,
            ),
            session,
        )
        session.refresh(issue)
        after_resolve = _build_import_quality_report(session)
        assert resolved["dry_run"] is False
        assert resolved["governance_report"]["issue_count"] == 1
        assert resolved["governance_report"]["resolution_hash"].startswith("sha256:")
        assert resolved["governance_report"]["safety"]["raw_source_text_saved"] is False
        assert resolved["governance_report"]["safety"]["resolution_text_returned"] is False
        assert issue.status == "resolved"
        assert issue.reviewer_id == "pytest-reviewer"
        assert issue.resolution
        assert issue.resolved_at is not None
        assert after_resolve["quality_debt"]["resolved_issues"] >= 1

        reopen = import_quality_issue_action(
            ImportIssueActionRequest(
                issue_ids=[issue.id or 0],
                action="reopen",
                reviewer_id="pytest-reviewer",
                resolution="复审发现该来源还需要补充许可元数据。",
                dry_run=False,
            ),
            session,
        )
        session.refresh(issue)
        after_reopen = _build_import_quality_report(session)
        logs = session.exec(
            select(PipelineRunLog)
            .where(PipelineRunLog.target_type == "content_import_issue")
            .where(PipelineRunLog.target_id == (issue.id or 0))
        ).all()

        assert reopen["transitions"][0]["to_status"] == "reopened"
        assert reopen["governance_report"]["to_status_counts"]["reopened"] == 1
        assert reopen["governance_report"]["audit_log_ids"]
        assert issue.status == "reopened"
        assert issue.resolved_at is None
        assert after_reopen["quality_debt"]["manual_review_issues"] >= 1
        assert len(logs) >= 2
        assert all("raw_source_text_saved" in (log.result_json or "") for log in logs)
        assert all("sha256:" in (log.message or "") for log in logs)
        assert all("已核对来源登记" not in (log.message or "") for log in logs)


def test_import_issue_governance_route_requires_resolution_to_resolve():
    create_db_and_tables()
    unique = uuid4().hex
    with Session(engine) as session:
        issue = ContentImportIssue(
            source_name=f"pytest_issue_route_{unique}.json",
            source_id=f"issue_route_{unique}",
            severity="warning",
            message="需要人工说明的历史导入问题",
        )
        session.add(issue)
        session.commit()
        session.refresh(issue)

    client = TestClient(app)
    missing_resolution = client.post(
        "/api/evolution/import-quality/issues/action",
        json={"issue_ids": [issue.id], "action": "resolve", "reviewer_id": "pytest-reviewer", "dry_run": False},
    )
    listed = client.get("/api/evolution/import-quality/issues?status=active&limit=20")

    assert missing_resolution.status_code == 422
    assert listed.status_code == 200
    assert listed.json()["summary"]["quality_gate"]["requires_resolution_reason"] is True


def test_import_issue_queue_groups_by_source_for_batch_governance():
    create_db_and_tables()
    unique = uuid4().hex
    source_name = f"pytest_source_group_{unique}.json"
    with Session(engine) as session:
        session.add(ContentImportIssue(
            source_name=source_name,
            source_id=f"group_error_{unique}",
            severity="error",
            message="来源许可字段缺失",
        ))
        session.add(ContentImportIssue(
            source_name=source_name,
            source_id=f"group_warning_{unique}",
            severity="warning",
            message="reviewed 状态缺失",
        ))
        session.add(ContentImportIssue(
            source_name=source_name,
            source_id=f"group_resolved_{unique}",
            severity="warning",
            message="已关闭样例",
            status="resolved",
            resolution="已核对来源登记",
        ))
        session.commit()

    client = TestClient(app)
    response = client.get("/api/evolution/import-quality/issues?status=active&limit=200")

    assert response.status_code == 200
    data = response.json()
    group = next(item for item in data["source_groups"] if item["source_name"] == source_name)
    assert group["active_issues"] == 2
    assert group["resolved_issues"] == 1
    assert group["by_severity"]["error"] == 1
    assert group["severity_weight"] >= 5
    assert "source contract" in group["recommended_action"]
    assert len(group["sample_issue_ids"]) == 2
    packet = group["review_packet"]
    assert packet["batch_action"]["default_action"] == "request_review"
    assert packet["batch_action"]["can_close_batch"] is False
    assert packet["batch_action"]["auto_close_allowed"] is False
    assert packet["quality_gate"]["error_level_requires_source_contract_review"] is True
    assert packet["quality_gate"]["raw_source_text_returned"] is False
    assert packet["quality_gate"]["resolution_text_returned"] is False
    assert any(item["id"] == "source_contract" for item in packet["evidence_checklist"])
    assert packet["sample_evidence"][0]["message_hash"].startswith("sha256:")


def test_import_issue_source_review_packet_allows_batch_closure_for_warning_only_source():
    create_db_and_tables()
    unique = uuid4().hex
    source_name = f"pytest_source_review_packet_{unique}.json"
    secret_resolution = f"不可泄露的人工说明 {unique}"
    with Session(engine) as session:
        session.add(ContentImportIssue(
            source_name=source_name,
            source_id=f"packet_warning_a_{unique}",
            severity="warning",
            message="字段已补齐但需要人工确认",
            resolution=secret_resolution,
        ))
        session.add(ContentImportIssue(
            source_name=source_name,
            source_id=f"packet_warning_b_{unique}",
            severity="warning",
            message="来源元数据已登记但状态待关闭",
        ))
        session.commit()

    client = TestClient(app)
    response = client.get("/api/evolution/import-quality/issues?status=active&limit=200")

    assert response.status_code == 200
    data = response.json()
    serialized = json.dumps(data, ensure_ascii=False)
    group = next(item for item in data["source_groups"] if item["source_name"] == source_name)
    packet = group["review_packet"]
    assert packet["batch_action"]["default_action"] == "resolve"
    assert packet["batch_action"]["can_close_batch"] is True
    assert packet["batch_action"]["requires_resolution"] is True
    assert packet["batch_action"]["requires_reviewer"] is True
    assert packet["batch_action"]["auto_close_allowed"] is False
    assert len(packet["batch_action"]["candidate_issue_ids"]) == 2
    assert packet["quality_gate"]["third_party_full_text_returned"] is False
    assert packet["sample_evidence"][0]["message_summary"]
    assert secret_resolution not in serialized


def test_import_issue_triage_separates_batch_closure_from_source_review():
    create_db_and_tables()
    unique = uuid4().hex
    warning_source = f"pytest_triage_warning_{unique}.json"
    error_source = f"pytest_triage_error_{unique}.json"
    with Session(engine) as session:
        session.add(ContentImportIssue(
            source_name=warning_source,
            source_id=f"triage_warning_a_{unique}",
            severity="warning",
            message="来源元数据已登记，等待人工确认",
        ))
        session.add(ContentImportIssue(
            source_name=warning_source,
            source_id=f"triage_warning_b_{unique}",
            severity="warning",
            message="字段已补齐，需要批量关闭证据",
        ))
        session.add(ContentImportIssue(
            source_name=error_source,
            source_id=f"triage_error_{unique}",
            severity="error",
            message="来源许可字段缺失",
        ))
        session.commit()

        report = _build_import_quality_report(session)

    client = TestClient(app)
    response = client.get("/api/evolution/import-quality/issues?status=active&limit=300")

    assert response.status_code == 200
    data = response.json()
    triage = report["issue_triage"]
    assert triage["summary"]["batch_closable_issues"] >= 2
    assert triage["summary"]["source_review_required_issues"] >= 1
    assert triage["summary"]["projected_score_after_batch_closable"] >= triage["summary"]["current_score"]
    assert triage["quality_gate"]["auto_close_allowed"] is False
    assert any(item["source_name"] == warning_source for item in triage["buckets"]["batch_closable"])
    assert any(item["source_name"] == error_source for item in triage["buckets"]["source_review_required"])
    assert data["triage"]["summary"]["active_issue_count"] >= 3
    assert "triage" in data


def test_import_issue_audit_history_redacts_resolution_text():
    create_db_and_tables()
    unique = uuid4().hex
    resolution = "已核对来源登记与批次报告，确认为历史迁移告警。"
    with Session(engine) as session:
        issue = ContentImportIssue(
            source_name=f"pytest_issue_audit_{unique}.json",
            source_id=f"issue_audit_{unique}",
            severity="warning",
            message="需要进入审计历史的历史导入问题",
        )
        session.add(issue)
        session.commit()
        session.refresh(issue)

        result = import_quality_issue_action(
            ImportIssueActionRequest(
                issue_ids=[issue.id or 0],
                action="resolve",
                reviewer_id="pytest-audit-reviewer",
                resolution=resolution,
                dry_run=False,
            ),
            session,
        )

    client = TestClient(app)
    response = client.get("/api/evolution/import-quality/issues/audit?limit=20")

    assert result["governance_report"]["resolution_hash"].startswith("sha256:")
    assert response.status_code == 200
    data = response.json()
    item = next(row for row in data["items"] if row["issue_id"] == issue.id)
    assert item["action"] == "resolve"
    assert item["to_status"] == "resolved"
    assert item["reviewer_id"] == "pytest-audit-reviewer"
    assert item["resolution_hash"] == result["governance_report"]["resolution_hash"]
    assert item["safety"]["raw_source_text_saved"] is False
    assert item["safety"]["resolution_text_returned"] is False
    assert data["summary"]["unsafe_log_count"] == 0
    assert resolution not in json.dumps(data, ensure_ascii=False)

    with Session(engine) as session:
        logs = session.exec(
            select(PipelineRunLog)
            .where(PipelineRunLog.target_type == "content_import_issue")
            .where(PipelineRunLog.target_id == (issue.id or 0))
        ).all()
        assert logs
        assert all(resolution not in (log.result_json or "") for log in logs)
        assert all(resolution not in (log.message or "") for log in logs)


def test_weekly_scheduler_generates_report_and_next_actions():
    create_db_and_tables()
    unique = uuid4().hex
    with Session(engine) as session:
        source = create_source_registry(
            SourceRegistryCreate(
                source_uuid=f"source_scheduler_{unique}",
                name=f"pytest 调度来源 {unique}",
                source_type="manual",
            ),
            session,
        )
        raw = create_raw_item(
            RawContentCreate(
                raw_uuid=f"raw_scheduler_{unique}",
                source_id=source["id"],
                title=f"pytest 周期调度 邀请 情绪 {unique}",
                content=f"公开摘要：周期调度生成训练资产 {unique}",
                privacy_risk=0.6,
                copyright_risk=0.6,
            ),
            session,
        )

        dry = run_weekly_scheduler(
            ScheduledEvolutionRunRequest(dry_run=True, batch_limit=5),
            session,
        )
        result = run_weekly_scheduler(
            ScheduledEvolutionRunRequest(
                dry_run=False,
                batch_limit=10,
                duplicate_policy="annotate_duplicates",
                period_type="weekly",
            ),
            session,
        )

        assert raw["id"] is not None
        assert dry["dry_run"] is True
        assert result["dry_run"] is False
        assert result["report"]["period_type"] == "weekly"
        assert result["batch"]["summary"]["annotated"] >= 1
        assert result["dedupe_report"]["summary"]["scanned"] >= 1
        assert "quality_score" in result["import_quality"]
        assert result["next_actions"]


def test_learning_and_pipeline_routes_registered_on_main_app():
    create_db_and_tables()
    client = TestClient(app)

    learning_response = client.get("/api/learning/framework")
    curriculum_response = client.get("/api/learning/curriculum-graph")
    pipeline_response = client.get("/api/evolution/pipeline")
    batch_response = client.post(
        "/api/evolution/pipeline/run-batch",
        json={"limit": 3, "dry_run": True},
    )
    scheduler_response = client.post(
        "/api/evolution/scheduler/run-weekly",
        json={"batch_limit": 3, "dry_run": True},
    )
    dedupe_response = client.get("/api/evolution/dedupe/report?limit=10")
    quality_response = client.get("/api/evolution/import-quality")

    assert learning_response.status_code == 200
    assert learning_response.json()["primitive_ladder"][0]["name"] == "元事实"
    assert curriculum_response.status_code == 200
    assert len(curriculum_response.json()["nodes"]) == 9
    assert pipeline_response.status_code == 200
    assert pipeline_response.json()["stages"][0]["id"] == "source_registry"
    assert batch_response.status_code == 200
    assert batch_response.json()["dry_run"] is True
    assert scheduler_response.status_code == 200
    assert scheduler_response.json()["dry_run"] is True
    assert dedupe_response.status_code == 200
    assert quality_response.status_code == 200


def test_evolution_pipeline_rejects_unknown_target_and_action():
    create_db_and_tables()
    unique = uuid4().hex
    with Session(engine) as session:
        raw = create_raw_item(
            RawContentCreate(
                raw_uuid=f"raw_negative_{unique}",
                title="pytest 负路径候选",
                content="公开摘要：用于验证流水线错误动作。",
            ),
            session,
        )

        client = TestClient(app)
        bad_target = client.post(
            "/api/evolution/pipeline/advance",
            json={"target_type": "unknown", "target_id": raw["id"], "action": "review"},
        )
        bad_action = client.post(
            "/api/evolution/pipeline/advance",
            json={"target_type": "raw_content", "target_id": raw["id"], "action": "teleport"},
        )
        missing_target = client.post(
            "/api/evolution/pipeline/advance",
            json={"target_type": "raw_content", "target_id": 999999999, "action": "review"},
        )

        assert bad_target.status_code == 400
        assert bad_target.json()["detail"] == "不支持的流水线目标类型"
        assert bad_action.status_code == 400
        assert bad_action.json()["detail"] == "不支持的流水线动作"
        assert missing_target.status_code == 404
        assert missing_target.json()["detail"] == "候选内容不存在"


def test_evolution_json_helpers_fall_back_safely():
    assert _loads_list(None) == []
    assert _loads_list("not-json") == []
    assert _loads_list('{"not":"list"}') == []
    assert _loads_list('["summary", "metadata"]') == ["summary", "metadata"]

    assert _loads_dict(None) == {}
    assert _loads_dict("not-json") == {}
    assert _loads_dict('["not", "dict"]') == {}
    assert _loads_dict('{"quality": 0.9}') == {"quality": 0.9}
