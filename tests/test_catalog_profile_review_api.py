from datetime import date
from uuid import uuid4

from fastapi.testclient import TestClient
from sqlmodel import Session, select

from backend.api.evolution import _knowledge_publish_candidate, _resource_publish_candidate
from backend.api.resources import check_source_link_health
from backend.database.connection import create_db_and_tables, engine
from backend.database.seed import seed_all
from backend.main import app
from backend.models.evolution import PipelineRunLog
from backend.models.knowledge import KnowledgeEntry, KnowledgeSection
from backend.models.resource import ResourceLibrary
from backend.models.user import DailyReview, UserProfile


def test_sample_and_resource_catalog_contracts_match_frontend():
    create_db_and_tables()
    seed_all()
    client = TestClient(app)

    samples = client.get("/api/samples", params={"limit": 1})
    assert samples.status_code == 200
    samples_data = samples.json()
    assert set(samples_data) == {"items", "total"}
    assert samples_data["total"] >= 1
    assert len(samples_data["items"]) <= 1

    random_sample = client.get("/api/samples/random")
    assert random_sample.status_code == 200
    assert random_sample.json()["sample_uuid"]

    assert client.get("/api/samples/categories").json() == ["初识", "暧昧", "热恋", "冲突", "平淡", "修复"]
    assert "安全型" in client.get("/api/samples/attachments").json()

    resources = client.get("/api/resources", params={"limit": 1, "type": "joke"})
    assert resources.status_code == 200
    resources_data = resources.json()
    assert set(resources_data) == {"items", "total", "page", "limit", "offset"}
    assert resources_data["total"] >= 1
    assert resources_data["page"] == 1
    assert resources_data["limit"] == 1
    assert resources_data["offset"] == 0
    resource_item = resources_data["items"][0]
    assert "expression_tool_ids_json" in resource_item
    assert "expression_goal" in resource_item
    assert "speech_act" in resource_item
    assert "mistake_pattern" in resource_item
    assert "recommended_drills_json" in resource_item

    expression_filtered_resources = client.get(
        "/api/resources",
        params={"expression_tool": "expr_tool_041", "limit": 3},
    )
    assert expression_filtered_resources.status_code == 200
    expression_filtered_data = expression_filtered_resources.json()
    assert expression_filtered_data["total"] >= 1
    for item in expression_filtered_data["items"]:
        assert "expr_tool_041" in (item["expression_tool_ids_json"] or "")
        assert item["expression_goal"]
        assert item["recommended_drills_json"]

    resource_sources = client.get("/api/resources/sources", params={"limit": 5})
    assert resource_sources.status_code == 200
    source_data = resource_sources.json()
    assert set(source_data) == {"items", "total"}
    assert source_data["total"] <= 5

    resource_filters = client.get("/api/resources/filters", params={"limit": 20})
    assert resource_filters.status_code == 200
    filters_data = resource_filters.json()
    assert {"types", "scenes", "tags", "sources", "expression_goals", "expression_tools", "keywords"} <= set(filters_data)
    assert filters_data["types"]
    assert filters_data["keywords"]
    assert all(item["count"] > 0 for group in ("types", "scenes", "tags", "sources", "expression_goals", "keywords") for item in filters_data[group])
    if filters_data["expression_tools"]:
        first_tool = filters_data["expression_tools"][0]
        assert {"id", "name", "count"} <= set(first_tool)
        assert first_tool["count"] > 0
        by_tool_name = client.get("/api/resources", params={"expression_tool": first_tool["name"], "limit": 3})
        assert by_tool_name.status_code == 200
        assert by_tool_name.json()["total"] >= 1

    knowledge_filters = client.get("/api/knowledge/filters", params={"limit": 20})
    assert knowledge_filters.status_code == 200
    knowledge_filter_data = knowledge_filters.json()
    assert {"sections", "categories", "tags", "sources", "keywords", "principle"} <= set(knowledge_filter_data)
    assert knowledge_filter_data["categories"]
    assert knowledge_filter_data["keywords"]
    assert all(item["count"] > 0 for group in ("categories", "tags", "sources", "keywords") for item in knowledge_filter_data[group])

    random_resource = client.get("/api/resources/random", params={"type": "joke"})
    assert random_resource.status_code == 200
    assert random_resource.json()["type"] == "joke"
    assert "joke" in client.get("/api/resources/types").json()

    filtered_samples = client.get(
        "/api/samples",
        params={"scenario_category": "暧昧", "difficulty_level": 1, "attachment_signal": "安全型", "limit": 5},
    )
    assert filtered_samples.status_code == 200
    for item in filtered_samples.json()["items"]:
        assert item["scenario_category"] == "暧昧"
        assert item["difficulty_level"] == 1
        assert item["attachment_signal"] == "安全型"

    first_sample_id = samples_data["items"][0]["id"]
    sample_detail = client.get(f"/api/samples/{first_sample_id}")
    assert sample_detail.status_code == 200
    assert sample_detail.json()["id"] == first_sample_id
    assert client.get("/api/samples/999999999").status_code == 404

    first_resource_id = resources_data["items"][0]["id"]
    resource_detail = client.get(f"/api/resources/{first_resource_id}")
    assert resource_detail.status_code == 200
    assert resource_detail.json()["id"] == first_resource_id
    assert client.get("/api/resources/999999999").status_code == 404

    assert client.get("/api/resources/random", params={"type": "not-a-real-type"}).json() is None


def test_source_link_health_check_records_metadata_and_downgrades_invalid_links(monkeypatch):
    create_db_and_tables()
    client = TestClient(app)
    unique = uuid4().hex
    bad_url = f"https://example.invalid/source/{unique}"
    with Session(engine) as session:
        resource = ResourceLibrary(
            resource_uuid=f"health-resource-{unique}",
            type="story",
            category="测试来源",
            title="失效来源资源",
            content="场景：测试。TA说：你好。常见失误：忽略。更好回应：尊重边界。练习任务：复述。",
            source="pytest_link_health",
            source_url=bad_url,
            review_status="published",
            quality_score=90,
            effectiveness_rating=9,
            tags="具体案例,边界",
        )
        session.add(resource)
        session.commit()
        session.refresh(resource)
        resource_id = resource.id

    def fake_health(source_url: str, timeout_seconds: float = 4.0) -> dict:
        return {
            "source_url": source_url,
            "status": "invalid",
            "http_code": 404,
            "redirect_url": None,
            "redirected": False,
            "last_checked_at": "2026-05-24T01:30:00",
            "error_type": None,
        }

    monkeypatch.setattr("backend.api.resources.check_source_link_health", fake_health)
    result = client.post(
        "/api/resources/sources/health-check",
        json={"source_urls": [bad_url], "dry_run": False},
    )
    sources = client.get("/api/resources/sources", params={"limit": 200})

    assert check_source_link_health("synthetic://bad")["status"] == "invalid"
    assert result.status_code == 200
    data = result.json()
    assert data["dry_run"] is False
    assert data["summary"]["invalid"] == 1
    assert data["audit_log_id"]
    assert "网页正文" in data["principle"]
    with Session(engine) as session:
        stored = session.exec(select(ResourceLibrary).where(ResourceLibrary.id == resource_id)).one()
        logs = session.exec(select(PipelineRunLog).where(PipelineRunLog.action == "source_link_health_check")).all()
    assert stored.review_status == "draft"
    assert logs
    assert '"body_saved": false' in (logs[-1].result_json or "")
    source = next(item for item in sources.json()["items"] if item["source_url"] == bad_url)
    assert source["health"]["http_code"] == 404
    assert source["health"]["status"] == "invalid"


def test_reviewed_asset_governance_summary_exposes_published_states():
    create_db_and_tables()
    seed_all()
    client = TestClient(app)

    response = client.get("/api/evolution/pipeline")
    assert response.status_code == 200
    data = response.json()
    assert "reviewed_assets" in data
    assert data["reviewed_assets"]["published"] >= 1
    assert data["status_counts"]["resources"]
    assert data["status_counts"]["knowledge"]

    promoted = client.post("/api/evolution/reviewed-assets/promote")
    assert promoted.status_code == 200
    promoted_data = promoted.json()
    assert promoted_data["inventory"]["published"] >= 1
    assert promoted_data["next_actions"]


def test_reviewed_asset_backfill_promotes_quality_based_states():
    create_db_and_tables()
    seed_all()
    client = TestClient(app)

    before = client.post("/api/evolution/reviewed-assets/backfill", json={"limit": 50, "force": False})
    assert before.status_code == 200
    before_data = before.json()
    assert before_data["updated"]["resources"] >= 0
    assert before_data["updated"]["knowledge_entries"] >= 0

    after = client.get("/api/evolution/pipeline")
    assert after.status_code == 200
    data = after.json()
    assert data["reviewed_assets"]["reviewed"] + data["reviewed_assets"]["published"] >= 1
    assert data["next_actions"]


def test_reviewed_asset_publish_candidates_are_auditable():
    create_db_and_tables()
    seed_all()
    client = TestClient(app)

    client.post("/api/evolution/reviewed-assets/backfill", json={"limit": 100, "force": True})
    response = client.get("/api/evolution/reviewed-assets/publish-candidates", params={"limit": 10})

    assert response.status_code == 200
    data = response.json()
    assert "items" in data
    assert "quality_gates" in data
    assert data["quality_gates"]["requires_manual_confirmation"] is True
    assert data["next_actions"]
    if data["items"]:
        first = data["items"][0]
        assert {"asset_type", "id", "review_status", "publish_ready", "priority"} <= set(first)
        assert first["review_status"] == "reviewed"


def test_boutique_resource_batch_creates_publish_ready_project_original_cards():
    create_db_and_tables()
    seed_all()
    client = TestClient(app)

    dry = client.post("/api/evolution/reviewed-assets/boutique-batch", json={"limit": 3, "dry_run": True})
    created = client.post("/api/evolution/reviewed-assets/boutique-batch", json={"limit": 3, "dry_run": False})
    candidates = client.get("/api/evolution/reviewed-assets/publish-candidates", params={"limit": 50})

    assert dry.status_code == 200
    assert dry.json()["dry_run"] is True
    assert dry.json()["created"] == 0
    assert dry.json()["publish_ready"] == 3
    assert created.status_code == 200
    created_data = created.json()
    assert created_data["dry_run"] is False
    assert created_data["created"] + created_data["skipped_existing"] >= 3
    assert created_data["publish_ready"] == 3
    assert all(item["publish_ready"] for item in created_data["items"])
    assert candidates.status_code == 200
    assert candidates.json()["publish_ready"] >= 3
    assert "第三方全文" in created_data["principle"]


def test_legacy_generic_knowledge_is_not_publish_ready_without_curation():
    create_db_and_tables()
    seed_all()
    client = TestClient(app)
    unique = uuid4().hex
    with Session(engine) as session:
        section = KnowledgeSection(section_uuid=f"legacy-generic-section-{unique}", name="legacy", source="pytest")
        session.add(section)
        session.commit()
        session.refresh(section)
        entry = KnowledgeEntry(
            entry_uuid=f"legacy-generic-entry-{unique}",
            section_id=section.id or 0,
            title="旧手册章节",
            content="只有泛化章节内容。",
            summary="泛化章节摘要。",
            category="legacy_manual",
            tags_json='["legacy"]',
            source="legacy_manual",
            quality_score=90,
            review_status="reviewed",
            source_metadata_json='{"source":"legacy_manual"}',
        )
        session.add(entry)
        session.commit()
        session.refresh(entry)
        legacy = _knowledge_publish_candidate(entry)

    response = client.get("/api/evolution/reviewed-assets/publish-candidates", params={"limit": 100})

    assert response.status_code == 200
    assert legacy["publish_ready"] is False
    assert legacy["priority"]["score"] < 85
    assert legacy["quality_signal"]["blocks"]
    assert response.json()["quality_gates"]["requires_manual_confirmation"] is True


def test_high_tension_resource_requires_boundary_evidence_before_publish():
    create_db_and_tables()
    unique = uuid4().hex
    with Session(engine) as session:
        unsafe = ResourceLibrary(
            resource_uuid=f"unsafe-flirty-{unique}",
            type="flirty",
            category="暧昧张力",
            title="暧昧推拉话术",
            content="场景：初次约会后。TA说：今天挺开心。常见失误：冷一下她。更好回应：晚点再说。练习任务：制造张力。",
            applicable_scene="暧昧",
            usage_tip="制造暧昧张力。",
            emotional_tone_json='["暧昧"]',
            effectiveness_rating=9,
            quality_score=92,
            review_status="reviewed",
            tags="具体案例,暧昧,调情",
        )
        safe = ResourceLibrary(
            resource_uuid=f"safe-flirty-{unique}",
            type="flirty",
            category="暧昧张力",
            title="可退出的轻挑战",
            content="场景：初次约会后。TA说：今天挺开心。常见失误：冷处理。更好回应：我也开心，但你可以慢慢决定要不要继续约。边界与同意：允许拒绝和停止。练习任务：写一句不施压的轻挑战。",
            applicable_scene="暧昧",
            usage_tip="制造张力时给出可拒绝退路，尊重对方舒服程度。",
            emotional_tone_json='["暧昧"]',
            effectiveness_rating=9,
            quality_score=92,
            review_status="reviewed",
            tags="具体案例,暧昧,调情,边界与同意,可拒绝",
        )
        session.add(unsafe)
        session.add(safe)
        session.commit()
        session.refresh(unsafe)
        session.refresh(safe)
        unsafe_candidate = _resource_publish_candidate(unsafe)
        safe_candidate = _resource_publish_candidate(safe)

    assert unsafe_candidate["publish_ready"] is False
    assert "high-tension content requires explicit boundary/consent evidence" in unsafe_candidate["quality_signal"]["blocks"]
    assert safe_candidate["publish_ready"] is True


def test_short_generic_resource_is_not_publish_ready_without_concrete_practice_evidence():
    create_db_and_tables()
    seed_all()
    client = TestClient(app)
    unique = uuid4().hex
    with Session(engine) as session:
        resource = ResourceLibrary(
            resource_uuid=f"generic-resource-{unique}",
            type="flirty",
            category="土味",
            title="土味",
            content="我想牵着你的手，因为我想让我的手找到它的幸福。",
            emotional_tone_json='["暧昧"]',
            applicable_scene="撩人",
            usage_tip="用于撩人场景，保持轻量、尊重边界。",
            effectiveness_rating=7,
            quality_score=70,
            review_status="reviewed",
        )
        session.add(resource)
        session.commit()
        session.refresh(resource)
        candidate = _resource_publish_candidate(resource)

    response = client.get("/api/evolution/reviewed-assets/publish-candidates", params={"limit": 100})

    assert response.status_code == 200
    assert candidate["publish_ready"] is False
    assert candidate["priority"]["score"] < 85
    assert candidate["quality_signal"]["blocks"]


def test_legacy_enrichment_debt_resource_is_not_publish_ready():
    create_db_and_tables()
    unique = uuid4().hex
    with Session(engine) as session:
        resource = ResourceLibrary(
            resource_uuid=f"legacy-enrichment-resource-{unique}",
            type="riddle",
            category="浪漫急转弯",
            title="情话版",
            content=(
                "场景故事：暧昧场景里，学习者想把旧急转弯素材改成低压力、可退出的互动。"
                "TA说：你这个脑筋急转弯想怎么接才不尴尬？"
                "完整对话：TA：你这个脑筋急转弯想怎么接才不尴尬？；低质量回应：这都猜不到？"
                "更好回应：我来一个很轻的玩笑，猜不到也没关系。"
            ),
            emotional_tone_json='["暧昧"]',
            applicable_scene="暧昧",
            usage_tip="用于暧昧场景，保持轻量、尊重边界。",
            effectiveness_rating=7,
            quality_score=94,
            review_status="reviewed",
            tags="needs_enrichment,legacy_no_case_blueprint",
            source="project_original:legacy_riddle_upgrade_v1",
        )
        session.add(resource)
        session.commit()
        session.refresh(resource)
        candidate = _resource_publish_candidate(resource)

    assert candidate["publish_ready"] is False
    assert "legacy enrichment debt requires case-level curation before publish" in candidate["quality_signal"]["blocks"]


def test_default_resource_catalog_hides_pytest_and_low_status_records():
    create_db_and_tables()
    seed_all()
    client = TestClient(app)
    unique = uuid4().hex
    with Session(engine) as session:
        visible = ResourceLibrary(
            resource_uuid=f"user-visible-resource-{unique}",
            type="game",
            category="冲突修复练习",
            title="可见的具体练习卡",
            content=(
                "场景：对方说你最近总是迟到。TA说：我觉得自己的时间不被尊重。"
                "常见失误：解释交通。更好回应：先承认影响，再给补救。"
                "边界与同意：对方暂时不想聊时先暂停。练习任务：写三句修复回应。"
            ),
            applicable_scene="冲突修复",
            usage_tip="用于具体冲突修复训练。",
            effectiveness_rating=9,
            quality_score=92,
            tags="具体案例,场景,TA说,常见失误,更好回应,练习任务",
            review_status="published",
            source="project_original",
        )
        hidden_pytest = ResourceLibrary(
            resource_uuid=f"pytest-hidden-resource-{unique}",
            type="game",
            category="测试资源",
            title="不应展示的测试资源",
            content="场景：pytest。TA说：pytest。常见失误：pytest。更好回应：pytest。练习任务：pytest。",
            applicable_scene="测试",
            usage_tip="pytest",
            effectiveness_rating=9,
            quality_score=92,
            tags="具体案例",
            review_status="published",
            source="pytest_fixture",
        )
        hidden_draft = ResourceLibrary(
            resource_uuid=f"draft-hidden-resource-{unique}",
            type="game",
            category="草稿资源",
            title="不应展示的草稿资源",
            content=visible.content,
            applicable_scene="冲突修复",
            usage_tip="仍在草稿状态。",
            effectiveness_rating=9,
            quality_score=92,
            tags="具体案例",
            review_status="draft",
            source="project_original",
        )
        session.add(visible)
        session.add(hidden_pytest)
        session.add(hidden_draft)
        session.commit()

    response = client.get("/api/resources", params={"q": "具体练习卡", "limit": 50})

    assert response.status_code == 200
    titles = {item["title"] for item in response.json()["items"]}
    assert "可见的具体练习卡" in titles
    assert "不应展示的测试资源" not in titles
    assert "不应展示的草稿资源" not in titles


def test_reviewed_asset_action_confirm_withdraw_and_request_review_are_audited():
    create_db_and_tables()
    seed_all()
    client = TestClient(app)

    unique = uuid4().hex
    with Session(engine) as session:
        resource = ResourceLibrary(
            resource_uuid=f"publishable-resource-{unique}",
            type="game",
            category="冲突修复练习",
            title="迟到后的修复三步练习",
            content=(
                "场景：你临时迟到二十分钟，对方说“算了，你总是这样”。"
                "TA说：你是不是根本不在乎我的时间。"
                "常见失误：马上辩解交通很堵，忽略对方被轻视的感受。"
                "更好回应：先承认影响，再说明补救：我迟到让你等了很久，这确实不尊重你的安排。"
                "我想先听你现在最介意的点，然后我重新约一个你舒服的时间。"
                "边界与同意：如果对方暂时不想聊，先给空间，不追问。"
                "练习任务：把回应改写成事实、感受、补救三句。"
            ),
            emotional_tone_json='["修复","真诚"]',
            applicable_scene="冲突修复",
            usage_tip="用于练习承认影响、表达补救和尊重对方暂停沟通的边界。",
            effectiveness_rating=9,
            quality_score=92,
            tags="场景,TA说,常见失误,更好回应,边界与同意,练习任务",
            review_status="reviewed",
            source="pytest",
        )
        session.add(resource)
        session.commit()

    with Session(engine) as session:
        inserted = session.exec(
            select(ResourceLibrary).where(ResourceLibrary.resource_uuid == f"publishable-resource-{unique}")
        ).one()
        assert _resource_publish_candidate(inserted)["publish_ready"] is True

    candidates = client.get("/api/evolution/reviewed-assets/publish-candidates", params={"limit": 20}).json()["items"]
    candidate = next(item for item in candidates if item["publish_ready"])
    payload = {
        "asset_type": candidate["asset_type"],
        "asset_id": candidate["id"],
        "reviewer_id": "release-manager-test",
        "reason": "quality gate accepted",
    }

    dry = client.post("/api/evolution/reviewed-assets/action", json={**payload, "action": "confirm_publish", "dry_run": True})
    assert dry.status_code == 200
    assert dry.json()["dry_run"] is True
    assert dry.json()["from_status"] == "reviewed"
    assert dry.json()["to_status"] == "published"

    published = client.post("/api/evolution/reviewed-assets/action", json={**payload, "action": "confirm_publish", "dry_run": False})
    assert published.status_code == 200
    published_data = published.json()
    assert published_data["asset"]["review_status"] == "published"
    assert published_data["asset"]["published_at"]
    assert published_data["audit_log"]["action"] == "confirm_publish"

    duplicate = client.post("/api/evolution/reviewed-assets/action", json={**payload, "action": "confirm_publish", "dry_run": False})
    assert duplicate.status_code == 409

    withdrawn = client.post("/api/evolution/reviewed-assets/action", json={**payload, "action": "withdraw", "dry_run": False, "reason": "needs second review"})
    assert withdrawn.status_code == 200
    withdrawn_data = withdrawn.json()
    assert withdrawn_data["from_status"] == "published"
    assert withdrawn_data["to_status"] == "reviewed"
    assert withdrawn_data["asset"]["published_at"] is None

    review = client.post("/api/evolution/reviewed-assets/action", json={**payload, "action": "request_review", "dry_run": False})
    assert review.status_code == 200
    assert review.json()["to_status"] == "draft"

    with Session(engine) as session:
        logs = session.exec(select(PipelineRunLog).where(PipelineRunLog.target_type == candidate["asset_type"]).where(PipelineRunLog.target_id == candidate["id"])).all()
    actions = {item.action for item in logs}
    assert {"confirm_publish", "withdraw", "request_review"} <= actions


def test_auto_review_publishes_ready_assets_and_can_request_review_blocked_assets():
    create_db_and_tables()
    seed_all()
    client = TestClient(app)
    unique = uuid4().hex
    with Session(engine) as session:
        section = KnowledgeSection(section_uuid=f"auto-review-section-{unique}", name="auto-review", source="pytest")
        session.add(section)
        session.commit()
        session.refresh(section)
        ready = ResourceLibrary(
            resource_uuid=f"auto-review-ready-{unique}",
            type="story",
            category="自动审核",
            title=f"自动审核可发布卡 {unique}",
            content=(
                "场景：初识聊天忽然变安静。"
                "TA说：我刚才有点不知道怎么接。"
                "完整对话：TA说不知道怎么接；我说我们可以慢一点。"
                "常见失误：立刻追问是不是不喜欢我。"
                "更好回应：我听到你说有点不知道怎么接，我们可以先停在轻一点的话题。"
                "边界：如果你想换话题也可以。"
                "练习任务：写三句事实、感受、选择。"
            ),
            applicable_scene="初识",
            usage_tip="用于练习低压力轻验证。",
            effectiveness_rating=9,
            quality_score=92,
            tags="场景,TA说,常见失误,更好回应,边界与同意,练习任务",
            review_status="reviewed",
            source="pytest",
        )
        blocked = KnowledgeEntry(
            entry_uuid=f"auto-review-blocked-{unique}",
            section_id=section.id or 0,
            title=f"低分知识 {unique}",
            content="只有简短说明。",
            summary="简短说明。",
            category="沟通",
            tags_json='["沟通"]',
            source_metadata_json='{"source":"pytest"}',
            quality_score=70,
            review_status="reviewed",
        )
        session.add(ready)
        session.add(blocked)
        session.commit()

    dry = client.post(
        "/api/evolution/reviewed-assets/auto-review",
        json={"limit": 100, "dry_run": True, "request_review_blocked_assets": True},
    )
    assert dry.status_code == 200
    assert dry.json()["summary"]["publish"] >= 1
    assert dry.json()["summary"]["request_review"] >= 1

    applied = client.post(
        "/api/evolution/reviewed-assets/auto-review",
        json={"limit": 100, "dry_run": False, "request_review_blocked_assets": True},
    )
    assert applied.status_code == 200
    data = applied.json()
    assert any(item["action"] == "confirm_publish" and item["to_status"] == "published" for item in data["applied"])
    assert any(item["action"] == "request_review" and item["to_status"] == "draft" for item in data["applied"])

    with Session(engine) as session:
        ready_after = session.exec(select(ResourceLibrary).where(ResourceLibrary.resource_uuid == f"auto-review-ready-{unique}")).one()
        blocked_after = session.exec(select(KnowledgeEntry).where(KnowledgeEntry.entry_uuid == f"auto-review-blocked-{unique}")).one()
        logs = session.exec(select(PipelineRunLog).where(PipelineRunLog.action.startswith("auto_review:"))).all()
    assert ready_after.review_status == "published"
    assert blocked_after.review_status == "draft"
    assert logs


def test_sample_annotation_backfill_routes():
    create_db_and_tables()
    seed_all()
    client = TestClient(app)

    backfill = client.post("/api/samples/annotations/backfill", json={"limit": 3, "force": True})
    samples = client.get("/api/samples", params={"limit": 1})
    sample_id = samples.json()["items"][0]["id"]
    annotation_map = client.get(f"/api/samples/{sample_id}/annotation-map")

    assert backfill.status_code == 200
    assert backfill.json()["updated"] >= 1
    assert "five_w_two_h_json" in backfill.json()["fields"]
    assert annotation_map.status_code == 200
    assert annotation_map.json()["annotation_version"] == "multigranular-v1"
    assert annotation_map.json()["quality"]["version"] == "multigranular-v1"
    assert client.get("/api/samples/999999999/annotation-map").status_code == 404


def test_profile_and_daily_review_smoke_flow():
    create_db_and_tables()
    client = TestClient(app)

    profile = client.get("/api/profile")
    assert profile.status_code == 200
    assert profile.json()["id"] >= 1

    updated = client.put(
        "/api/profile",
        json={"attachment_style": "安全型", "emotion_vocab_size": 12, "perception_baseline": 60},
    )
    assert updated.status_code == 200
    assert updated.json()["emotion_vocab_size"] == 12

    today = date.today().isoformat()
    created = client.post(
        "/api/reviews",
        json={
            "review_date": today,
            "five_whys_json": '{"emotions":["平静","期待"]}',
            "emotion_accuracy": 78,
            "highlight": "今天能区分事实和解释。",
            "improvement": "下一次先轻验证。",
        },
    )
    assert created.status_code == 200
    assert created.json()["emotions"] == ["平静", "期待"]

    listed = client.get("/api/reviews")
    assert listed.status_code == 200
    review_id = listed.json()[0]["id"]

    deleted = client.delete(f"/api/reviews/{review_id}")
    assert deleted.status_code == 200
    assert deleted.json() == {"ok": True}

    assert client.delete("/api/reviews/999999999").status_code == 404


def test_profile_default_creation_and_review_update_paths():
    create_db_and_tables()
    with Session(engine) as session:
        for profile in session.exec(select(UserProfile)).all():
            session.delete(profile)
        session.commit()

    client = TestClient(app)
    profile = client.get("/api/profile")

    assert profile.status_code == 200
    assert profile.json()["attachment_style"] == "安全型"
    assert profile.json()["perception_baseline"] == 50

    with Session(engine) as session:
        for profile_row in session.exec(select(UserProfile)).all():
            session.delete(profile_row)
        session.commit()

    updated = client.put(
        "/api/profile",
        json={
            "core_wound": "被忽视",
            "love_language": "高质量陪伴",
            "progress_json": '{"stage":"emotion"}',
        },
    )

    assert updated.status_code == 200
    assert updated.json()["core_wound"] == "被忽视"
    assert updated.json()["progress_json"] == '{"stage":"emotion"}'

    today = date.today().isoformat()
    first = client.post(
        "/api/reviews",
        json={
            "review_date": today,
            "five_whys_json": "not-json",
            "emotion_accuracy": 51,
            "highlight": "第一次复盘",
            "improvement": "记录事实",
        },
    )
    second = client.post(
        "/api/reviews",
        json={
            "review_date": today,
            "five_whys_json": '{"emotions":["踏实"]}',
            "emotion_accuracy": 86,
            "highlight": "更新同一天复盘",
            "improvement": "轻验证",
        },
    )

    assert first.status_code == 200
    assert first.json()["emotions"] == []
    assert second.status_code == 200
    assert second.json()["highlight"] == "更新同一天复盘"
    assert second.json()["emotions"] == ["踏实"]

    with Session(engine) as session:
        same_day_reviews = session.exec(select(DailyReview).where(DailyReview.review_date == date.fromisoformat(today))).all()

    assert len(same_day_reviews) == 1
