from uuid import uuid4

from fastapi.testclient import TestClient
from sqlmodel import Session, select

from backend.core.vector_index import (
    evaluate_vector_recall,
    metadata_vector_index_report,
    rebuild_metadata_vector_index,
    resource_similarity_queue,
    search_metadata_vectors,
)
from backend.database.connection import create_db_and_tables, engine
from backend.database.resource_quality_governance import (
    resource_quality_report,
    soft_hide_legacy_generated_variants,
    soft_hide_off_mission_resources,
    soft_hide_resource_family_over_cap,
)
from backend.database.schema_guard import audit_schema
from backend.main import app
from backend.models.evolution import MetadataVectorIndex, PipelineRunLog, RawContentItem
from backend.models.knowledge import KnowledgeEntry, KnowledgeSection
from backend.models.resource import ResourceLibrary
from backend.models.sample import InteractionSample

client = TestClient(app)


def test_metadata_vector_index_rebuild_search_and_audit():
    create_db_and_tables()
    unique = uuid4().hex
    with Session(engine) as session:
        section = KnowledgeSection(section_uuid=f"vector-section-{unique}", name="向量测试", source="pytest")
        session.add(section)
        session.commit()
        session.refresh(section)
        raw = RawContentItem(
            raw_uuid=f"vector-raw-{unique}",
            title=f"边界 修复 低压力 邀请 {unique}",
            url=f"https://example.com/vector/{unique}",
            content_hash=f"sha256:{unique}",
        )
        knowledge = KnowledgeEntry(
            entry_uuid=f"vector-knowledge-{unique}",
            section_id=section.id or 0,
            title=f"边界修复与低压力邀请 {unique}",
            summary="先承接空间，再提出轻验证问题。",
            content="边界不是拒绝，低压力邀请能保护连接。",
            category="boundary",
            tags_json='["边界","修复"]',
            quality_score=91,
            source="pytest",
        )
        sample = InteractionSample(
            sample_uuid=f"vector-sample-{unique}",
            scenario_category="冲突",
            difficulty_level=3,
            context=f"对方说需要空间，适合低压力边界修复 {unique}",
            their_words="我现在不想一直聊。",
            emotion_tags_json="[]",
            hidden_need="边界安全",
            attachment_signal="回避型",
            bad_response="你必须说清楚。",
            good_response_soft="我听见你想先缓一缓，我们晚点再聊。",
        )
        resource = ResourceLibrary(
            resource_uuid=f"vector-resource-{unique}",
            type="phrase",
            category="边界",
            title=f"低压力边界邀请 {unique}",
            content="你想晚点聊也可以，我会在。",
            tags="边界,修复,低压力",
            source="pytest",
        )
        session.add(raw)
        session.add(knowledge)
        session.add(sample)
        session.add(resource)
        session.commit()

        rebuilt = rebuild_metadata_vector_index(session, target_types=["raw_content", "knowledge", "sample", "resource"], limit_per_type=1000)
        report = metadata_vector_index_report(session)
        search = search_metadata_vectors(session, f"边界 修复 低压力 {unique}", limit=20, threshold=0.2)
        evaluation = evaluate_vector_recall(session, limit_per_type=4, thresholds=[0.2, 0.35, 0.5])
        rows = session.exec(select(MetadataVectorIndex).where(MetadataVectorIndex.target_uuid == f"vector-raw-{unique}")).all()
        audit = audit_schema(engine)

    assert rebuilt["rebuilt"]["raw_content"] >= 1
    assert rebuilt["total_vectors"] >= 4
    assert rebuilt["backend"] == "sqlite_vec"
    assert rebuilt["sqlite_vec"]["available"] is True
    assert report["summary"]["sqlite_vec_ready"] is True
    assert report["summary"]["backend"] == "sqlite_vec"
    assert report["by_type"]["raw_content"] >= 1
    assert search["backend"] == "sqlite_vec"
    assert any(item["target_uuid"] == f"vector-raw-{unique}" for item in search["results"])
    assert any(item["target_uuid"] == f"vector-knowledge-{unique}" for item in search["results"])
    assert evaluation["summary"]["backend"] == "sqlite_vec"
    assert evaluation["summary"]["probes"] >= 4
    assert evaluation["summary"]["top10_recall"] >= 0.65
    assert evaluation["thresholds"][0]["threshold"] == 0.2
    assert "weak_spots" in evaluation
    assert rows and rows[0].dimensions == 64
    assert audit["json_quality"]["metadata_vector_index.vector_json"]["invalid"] == 0


def test_vector_index_routes_are_registered():
    create_db_and_tables()

    report = client.get("/api/evolution/vector-index/report")
    rebuilt = client.post("/api/evolution/vector-index/rebuild", json={"target_types": ["raw_content"], "limit_per_type": 20})
    search = client.post("/api/evolution/vector-index/search", json={"query": "边界 修复", "limit": 5, "threshold": 0.0})
    evaluation = client.post("/api/evolution/vector-index/evaluate", json={"limit_per_type": 2, "thresholds": [0.2, 0.35]})

    assert report.status_code == 200
    assert "summary" in report.json()
    assert rebuilt.status_code == 200
    assert rebuilt.json()["backend"] == "sqlite_vec"
    assert rebuilt.json()["sqlite_vec"]["active_backend"] == "sqlite_vec"
    assert search.status_code == 200
    assert "results" in search.json()
    assert search.json()["backend"] == "sqlite_vec"
    assert evaluation.status_code == 200
    assert evaluation.json()["summary"]["backend"] == "sqlite_vec"
    assert "thresholds" in evaluation.json()


def test_resource_similarity_queue_groups_review_candidates():
    create_db_and_tables()
    unique = uuid4().hex
    with Session(engine) as session:
        for index, style in enumerate(["温柔", "轻松", "坦诚", "幽默"], start=1):
            session.add(
                ResourceLibrary(
                    resource_uuid=f"similarity-resource-{unique}-{index}",
                    type="game",
                    category=f"近重复治理{unique}",
                    title=f"失望后的重新约定｜三步训练｜{style}D{index}",
                    content=(
                        "场景：你答应周末一起吃饭，却临时改了安排。对方只回了一个嗯。"
                        f"更好回应：先承认影响，再给出新时间。语气={style}。"
                    ),
                    applicable_scene="修复",
                    tags=f"具体案例,失望修复,可靠行动,{unique}",
                    source="pytest",
                    quality_score=990 + index,
                    review_status="reviewed",
                )
            )
        session.commit()

        report = resource_similarity_queue(session, limit=2000, threshold=0.7, max_clusters=2000)

    assert report["summary"]["scanned"] >= 4
    assert report["summary"]["clusters"] >= 1
    assert any(unique in cluster["family_key"] for cluster in report["clusters"])
    cluster = next(cluster for cluster in report["clusters"] if unique in cluster["family_key"])
    assert cluster["size"] >= 4
    assert cluster["recommended_action"] in {
        "merge_or_hide_variants",
        "rewrite_family_with_distinct_cases",
        "keep_but_diversify_sorting",
    }
    assert cluster["items"][0]["title"]
    assert report["next_actions"]

    with Session(engine) as session:
        cleanup_resources = session.exec(
            select(ResourceLibrary).where(ResourceLibrary.resource_uuid.like(f"%{unique}%"))
        ).all()
        for resource in cleanup_resources:
            resource.review_status = "quarantine"
            session.add(resource)
        session.commit()


def test_resource_similarity_queue_ignores_draft_and_quarantine_noise():
    create_db_and_tables()
    unique = uuid4().hex
    with Session(engine) as session:
        for index, status in enumerate(["draft", "quarantine", "reviewed"], start=1):
            session.add(
                ResourceLibrary(
                    resource_uuid=f"similarity-visible-window-{unique}-{index}",
                    type="game",
                    category=f"可见窗口{unique}",
                    title=f"失望后的重新约定｜窗口D{index}",
                    content=f"场景：对方失望。更好回应：先承接，再约定。状态 {status}",
                    applicable_scene="修复",
                    tags=f"具体案例,可见窗口,{unique}",
                    source="project_original_similarity_test",
                    quality_score=90,
                    review_status=status,
                )
            )
        session.commit()

        report = resource_similarity_queue(session, limit=2000, threshold=0.7, max_clusters=2000)

    assert all(unique not in cluster["family_key"] for cluster in report["clusters"])


def test_resource_quality_report_exposes_duplicate_and_practice_debt():
    create_db_and_tables()
    unique = uuid4().hex
    with Session(engine) as session:
        for index in range(4):
            session.add(
                ResourceLibrary(
                    resource_uuid=f"quality-report-resource-{unique}-{index}",
                    type="game",
                    category=f"质量报告{unique}",
                    title=f"失望后的重新约定｜质量D{index}",
                    content=(
                        "场景：对方说你又忘了约定。TA说：我现在有点不想继续聊。"
                        "常见失误：马上解释自己很忙。更好回应：先承认影响，再给补救。"
                        "边界与同意：对方想暂停时先停下。练习任务：写事实、感受、补救三句。"
                    ),
                    applicable_scene="修复",
                    usage_tip="用于训练具体修复，不追问、不逼迫立刻原谅。",
                    tags=f"具体案例,场景,TA说,常见失误,更好回应,边界与同意,练习任务,{unique}",
                    source="project_original_quality_test",
                    quality_score=92,
                    review_status="reviewed",
                )
            )
        session.commit()

        report = resource_quality_report(session)

    assert report["perceived_duplicate_debt"]["duplicate_families"] >= 1
    assert report["perceived_duplicate_debt"]["largest_family_size"] >= 4
    assert report["practice_completeness"]["avg_score"] >= 0
    assert "练习任务" in report["practice_completeness"]["required_markers"]


def test_resource_quality_soft_hides_legacy_generated_variants_without_deleting_content():
    create_db_and_tables()
    unique = uuid4().hex
    with Session(engine) as session:
        keep = ResourceLibrary(
            resource_uuid=f"quality-soft-hide-keep-{unique}",
            type="story",
            category=f"软隐藏{unique}",
            title="正常原创故事",
            content="场景：对方想暂停。TA说：我想晚点聊。常见失误：继续追问。更好回应：我等你准备好。边界：可以不聊。练习任务：写三句低压力回应。",
            tags=f"具体案例,{unique}",
            source="project_original_quality_test",
            review_status="published",
            quality_score=95,
        )
        legacy = ResourceLibrary(
            resource_uuid=f"quality-soft-hide-legacy-{unique}",
            type="story",
            category=f"软隐藏{unique}",
            title="旧生成重复故事",
            content="场景：旧生成变体。TA说：我有点累。常见失误：继续堆内容。更好回应：先停下。边界：可以暂停。练习任务：改写。",
            tags=f"具体案例,legacy_generated_hidden,{unique}",
            source="public_anchor:quality_soft_hide",
            review_status="published",
            quality_score=99,
        )
        session.add(keep)
        session.add(legacy)
        session.commit()
        session.refresh(legacy)
        legacy_id = int(legacy.id or 0)

        dry = soft_hide_legacy_generated_variants(session, dry_run=True, reviewer_id="soft-hide-test")
        assert dry["matched"] >= 1
        assert dry["safety_flags"]["content_deleted"] is False

        result = soft_hide_legacy_generated_variants(session, dry_run=False, reviewer_id="soft-hide-test")
        session.refresh(keep)
        hidden = session.get(ResourceLibrary, legacy_id)
        logs = session.exec(
            select(PipelineRunLog).where(PipelineRunLog.action == "resource_quality_soft_hide_legacy_generated")
        ).all()

    assert result["affected"] >= 1
    assert keep.review_status == "published"
    assert hidden is not None
    assert hidden.review_status == "quarantine"
    assert "旧生成变体" in hidden.content
    assert any(log.target_id == legacy_id for log in logs)


def test_resource_quality_soft_hides_off_mission_resources_and_excludes_media_from_practice_debt():
    create_db_and_tables()
    unique = uuid4().hex
    with Session(engine) as session:
        media = ResourceLibrary(
            resource_uuid=f"quality-media-anchor-{unique}",
            type="media",
            category=f"来源锚点{unique}",
            title="Open data 来源锚点",
            content="来源定位：开放数据。来源摘要：仅作为导航入口。采集边界：link_title_summary。",
            tags=f"来源锚点,{unique}",
            source="project_original_quality_test",
            review_status="published",
            quality_score=90,
        )
        off_mission = ResourceLibrary(
            resource_uuid=f"quality-off-mission-{unique}",
            type="story",
            category=f"偏题采集{unique}",
            title="人口研究数据转化卡",
            content=(
                "场景：讨论人口研究。TA说：这些统计和我们聊天有什么关系？"
                "常见失误：继续解释官方统计。更好回应：把它移出关系训练默认流。"
                "边界：不把人口结构数据伪装成亲密关系训练。练习任务：换成真实对话案例。"
            ),
            tags=f"具体案例,人口研究,官方统计,{unique}",
            source="project_original_quality_test",
            review_status="published",
            quality_score=91,
        )
        session.add(media)
        session.add(off_mission)
        session.commit()
        session.refresh(off_mission)
        off_mission_id = int(off_mission.id or 0)

        report = resource_quality_report(session)
        result = soft_hide_off_mission_resources(session, dry_run=False, reviewer_id="off-mission-test")
        hidden = session.get(ResourceLibrary, off_mission_id)
        logs = session.exec(
            select(PipelineRunLog).where(PipelineRunLog.action == "resource_quality_soft_hide_off_mission")
        ).all()

    assert report["practice_completeness"]["source_anchor_cards_excluded"] >= 1
    assert result["affected"] >= 1
    assert hidden is not None
    assert hidden.review_status == "quarantine"
    assert "人口研究" in hidden.content
    assert any(log.target_id == off_mission_id for log in logs)


def test_resource_similarity_route_is_registered():
    create_db_and_tables()

    response = client.get("/api/resources/similarity?limit=20&threshold=0.7&max_clusters=5")

    assert response.status_code == 200
    body = response.json()
    assert "summary" in body
    assert "clusters" in body
    assert body["summary"]["method"] == "title/scenario semantic family + local metadata vector cosine"


def test_resource_quality_soft_hides_family_members_over_cap_without_deleting_content():
    create_db_and_tables()
    unique = uuid4().hex
    with Session(engine) as session:
        for index in range(1, 6):
            session.add(
                ResourceLibrary(
                    resource_uuid=f"family-cap-{unique}-{index}",
                    type="story",
                    category=f"家族上限{unique}",
                    title="修复｜家族上限案例",
                    content=f"场景：第 {index} 个近似案例。TA说：我有点累。常见失误：你又这样。更好回应：我先不催你。边界：可以晚点说。练习任务：改写一句。",
                    applicable_scene="修复",
                    tags=f"具体案例,{unique}",
                    source="pytest",
                    quality_score=80 + index,
                    review_status="reviewed",
                )
            )
        session.commit()

        result = soft_hide_resource_family_over_cap(session, cap=3, dry_run=False, reviewer_id="family-cap-test")
        visible = session.exec(
            select(ResourceLibrary)
            .where(ResourceLibrary.resource_uuid.like(f"family-cap-{unique}-%"))
            .where(ResourceLibrary.review_status.in_(("reviewed", "published")))
        ).all()
        hidden = session.exec(
            select(ResourceLibrary)
            .where(ResourceLibrary.resource_uuid.like(f"family-cap-{unique}-%"))
            .where(ResourceLibrary.review_status == "quarantine")
        ).all()
        logs = session.exec(select(PipelineRunLog).where(PipelineRunLog.action == "resource_quality_soft_hide_family_over_cap")).all()

    assert result["affected"] == 2
    assert len(visible) == 3
    assert len(hidden) == 2
    assert all("family_over_cap_hidden" in (item.tags or "") for item in hidden)
    assert any(log.target_id in {item.id for item in hidden} for log in logs)


def test_resource_similarity_action_quarantines_variants_without_deleting_content():
    create_db_and_tables()
    unique = uuid4().hex
    with Session(engine) as session:
        resources: list[ResourceLibrary] = []
        for index, quality in enumerate([97, 91, 76], start=1):
            resource = ResourceLibrary(
                resource_uuid=f"similarity-action-{unique}-{index}",
                type="game",
                category=f"近重复动作{unique}",
                title=f"失望后的重新约定｜动作验证D{index}",
                content=f"场景：对方失望。更好回应：先承接，再约定。变体 {index}",
                applicable_scene="修复",
                tags=f"具体案例,近重复动作,{unique}",
                source="project_original_similarity_test",
                quality_score=quality,
                review_status="reviewed",
            )
            session.add(resource)
            resources.append(resource)
        session.commit()
        resource_ids = [int(item.id or 0) for item in resources[1:]]

    payload = {
        "resource_ids": resource_ids,
        "action": "quarantine_variants",
        "reviewer_id": "similarity-test",
        "reason": "same family variants are too similar for default browsing",
        "dry_run": True,
    }
    dry = client.post("/api/resources/similarity/action", json=payload)
    assert dry.status_code == 200
    assert dry.json()["dry_run"] is True
    assert dry.json()["governance_report"]["safety_flags"]["content_deleted"] is False

    visible_before = client.get("/api/resources", params={"q": unique, "limit": 10}).json()
    assert visible_before["total"] == 3

    applied = client.post("/api/resources/similarity/action", json={**payload, "dry_run": False})
    assert applied.status_code == 200
    applied_data = applied.json()
    assert applied_data["dry_run"] is False
    assert applied_data["governance_report"]["resource_count"] == 2
    assert applied_data["governance_report"]["to_status_counts"]["quarantine"] == 2
    assert applied_data["governance_report"]["safety_flags"]["reason_text_returned"] is False
    assert all(item["to_status"] == "quarantine" for item in applied_data["transitions"])

    visible_after = client.get("/api/resources", params={"q": unique, "limit": 10}).json()
    assert visible_after["total"] == 1

    with Session(engine) as session:
        quarantined = session.exec(select(ResourceLibrary).where(ResourceLibrary.id.in_(resource_ids))).all()
        logs = session.exec(select(PipelineRunLog).where(PipelineRunLog.action == "resource_similarity_quarantine_variants")).all()

    assert len(quarantined) == 2
    assert {item.review_status for item in quarantined} == {"quarantine"}
    assert len(logs) >= 2
    assert all("same family variants" not in (item.result_json or "") for item in logs)

    with Session(engine) as session:
        cleanup_resources = session.exec(
            select(ResourceLibrary).where(ResourceLibrary.resource_uuid.like(f"%{unique}%"))
        ).all()
        for resource in cleanup_resources:
            resource.review_status = "quarantine"
            session.add(resource)
        session.commit()


def test_resource_similarity_rewrite_batch_creates_project_original_replacements():
    create_db_and_tables()
    unique = uuid4().hex
    with Session(engine) as session:
        originals: list[ResourceLibrary] = []
        for index in range(1, 3):
            resource = ResourceLibrary(
                resource_uuid=f"similarity-rewrite-{unique}-{index}",
                type="phrase",
                category=f"重复补位{unique}",
                title=f"修复里的沟通训练回应句｜重复D{index}",
                content="抽象总结：先承接情绪，再表达请求。",
                applicable_scene="修复",
                tags=f"具体案例,重复补位,{unique}",
                source="pytest",
                quality_score=88,
                review_status="published",
            )
            session.add(resource)
            originals.append(resource)
        session.commit()
        resource_ids = [int(item.id or 0) for item in originals]

    payload = {
        "resource_ids": resource_ids,
        "reviewer_id": "rewrite-test",
        "reason": "near duplicate family needs concrete replacement cases",
        "dry_run": True,
        "mark_originals_quarantine": True,
    }
    dry = client.post("/api/resources/similarity/rewrite-batch", json=payload)
    assert dry.status_code == 200
    dry_data = dry.json()
    assert dry_data["dry_run"] is True
    assert dry_data["created"] == 0
    assert len(dry_data["drafts"]) == 2
    assert "TA说" in dry_data["drafts"][0]["content"]
    assert "完整对话" in dry_data["drafts"][0]["content"]
    assert dry_data["drafts"][0]["case_blueprint_json"]
    assert dry_data["drafts"][0]["case_completeness_score"] == 100.0
    assert dry_data["governance_report"]["safety_flags"]["project_original_only"] is True
    assert dry_data["governance_report"]["safety_flags"]["third_party_full_text_saved"] is False

    applied = client.post("/api/resources/similarity/rewrite-batch", json={**payload, "dry_run": False})
    assert applied.status_code == 200
    applied_data = applied.json()
    assert applied_data["dry_run"] is False
    assert applied_data["created"] == 2
    assert applied_data["governance_report"]["replacement_count"] == 2
    assert applied_data["governance_report"]["safety_flags"]["original_content_deleted"] is False

    with Session(engine) as session:
        replacements = session.exec(
            select(ResourceLibrary).where(ResourceLibrary.source == "project_original:resource_similarity_rewrite")
        ).all()
        quarantined = session.exec(select(ResourceLibrary).where(ResourceLibrary.id.in_(resource_ids))).all()
        logs = session.exec(
            select(PipelineRunLog).where(PipelineRunLog.action == "resource_similarity_rewrite_and_quarantine_original")
        ).all()

    matching_replacements = [item for item in replacements if unique in (item.category or "")]
    assert len(matching_replacements) >= 2
    assert all(item.review_status == "reviewed" for item in matching_replacements)
    assert all("常见失误" in item.content and "更好回应" in item.content for item in matching_replacements)
    assert all(item.case_blueprint_json for item in matching_replacements)
    assert all(item.case_completeness_score == 100.0 for item in matching_replacements)
    assert {item.review_status for item in quarantined} == {"quarantine"}
    assert len(logs) >= 2
    assert all("near duplicate family" not in (item.result_json or "") for item in logs)

    with Session(engine) as session:
        cleanup_resources = session.exec(
            select(ResourceLibrary).where(ResourceLibrary.resource_uuid.like(f"%{unique}%"))
        ).all()
        for resource in cleanup_resources:
            resource.review_status = "quarantine"
            session.add(resource)
        session.commit()


def test_resource_similarity_rewrite_batch_uses_diverse_scenarios_for_larger_batches():
    create_db_and_tables()
    unique = uuid4().hex
    scenes = ["暧昧", "冲突", "热恋", "分歧", "异地", "家务分工", "玩笑越界", "表白前"]
    with Session(engine) as session:
        originals: list[ResourceLibrary] = []
        for index, scene in enumerate(scenes, start=1):
            resource = ResourceLibrary(
                resource_uuid=f"similarity-diverse-rewrite-{unique}-{index}",
                type="phrase",
                category=f"多样补位{unique}",
                title=f"{scene}里的抽象回应｜重复D{index}",
                content="抽象总结：先承接情绪，再表达请求。",
                applicable_scene=scene,
                tags=f"重复补位,{unique}",
                source="pytest",
                quality_score=70,
                review_status="reviewed",
            )
            session.add(resource)
            originals.append(resource)
        session.commit()
        resource_ids = [int(item.id or 0) for item in originals]

    response = client.post(
        "/api/resources/similarity/rewrite-batch",
        json={
            "resource_ids": resource_ids,
            "reviewer_id": "rewrite-diversity-test",
            "reason": "larger duplicate family needs diverse concrete practice cases",
            "dry_run": True,
            "mark_originals_quarantine": True,
        },
    )

    assert response.status_code == 200
    drafts = response.json()["drafts"]
    themes = {item["title"].split("｜", 1)[0] for item in drafts}
    assert len(drafts) == len(scenes)
    assert len(themes) >= 6
    assert any("可拒绝出口" in theme for theme in themes)
    assert any("不操控表达" in theme or "即时修复" in theme for theme in themes)

    with Session(engine) as session:
        cleanup_resources = session.exec(
            select(ResourceLibrary).where(ResourceLibrary.resource_uuid.like(f"%{unique}%"))
        ).all()
        for resource in cleanup_resources:
            resource.review_status = "quarantine"
            session.add(resource)
        session.commit()
