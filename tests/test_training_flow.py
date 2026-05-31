from datetime import date
from uuid import uuid4

from sqlmodel import Session, select

from backend.api.samples import (
    GoldConflictResolveRequest,
    GoldSampleBackfillRequest,
    GoldSampleReviewRequest,
    backfill_gold_samples,
    get_gold_conflict_queue,
    get_gold_interrater_consistency,
    get_gold_review_queue,
    get_gold_summary,
    resolve_gold_conflicts,
    submit_gold_review,
)
from backend.api.training import (
    CompareRequest,
    EmotionRecognizeRequest,
    PartnerSimulateRequest,
    RelationshipState,
    ReviewSubmitRequest,
    build_training_visual_map,
    compare_response,
    get_mistakes,
    get_next_training_item,
    get_today_summary,
    get_training_radar,
    get_training_visual_map,
    get_week_summary,
    persist_sample_multigranular_map,
    recognize_emotion,
    review_partner_session,
    simulate_partner,
    submit_review,
)
from backend.database.connection import create_db_and_tables, engine
from backend.database.import_json_content import import_resource_file, import_samples
from backend.database.seed import seed_all
from backend.models.resource import ResourceLibrary
from backend.models.sample import InteractionSample, SampleAnnotationVersion
from backend.models.training import PracticeEvent, PracticeSession, TrainingAttempt
from backend.models.user import MistakeLog


def test_training_flow_smoke():
    create_db_and_tables()
    seed_all()
    with Session(engine) as session:
        sample = session.exec(select(InteractionSample).limit(1)).first()
        assert sample is not None
        result = compare_response(CompareRequest(original_response="嗯", sample_id=sample.id, response_type="soft"), session)
        assert result.saved_attempt_id is not None
        assert result.scoring_source in ["rule_fallback", "hybrid"]
        assert result.metacognitive_review["principle"].startswith("大胆假设")
        assert result.metacognitive_review["fact_interpretation_split"]["observable_facts"]
        assert len(result.metacognitive_review["three_hypotheses"]) == 3
        assert result.mastery["stage"]["label"] in {"知道", "辨认", "操作", "迁移", "自然"}
        assert result.mastery["weakest"]["dimension"]
        assert result.error_attribution
        assert result.structured_diff["word_level"]
        assert result.structured_diff["structure_level"]
        assert result.structured_diff["emotion_path"]
        assert result.expression_tool_scoring["fit_score"] >= 0
        assert result.expression_tool_scoring["stage"].startswith("D")
        assert result.expression_tool_scoring["target_goal"]
        assert result.expression_tool_scoring["recommended_tools"]
        assert result.expression_tool_scoring["practice_steps"]
        assert result.expression_tool_scoring["principle"].startswith("表达评分")
        if result.mistake_id is not None:
            mistake = session.exec(select(MistakeLog).where(MistakeLog.id == result.mistake_id)).first()
            assert mistake is not None
            assert mistake.error_attribution_json
            assert mistake.mastery_snapshot_json
            assert mistake.review_focus
            mistake_cards = get_mistakes(session)
            assert any(card["error_attribution"] for card in mistake_cards)
            first_card = mistake_cards[0]
            assert first_card["expression_rewrite"]["target_goal"]
            assert first_card["expression_rewrite"]["recommended_tools"]
            assert len(first_card["expression_rewrite"]["rewrite_versions"]) == 3
            assert first_card["expression_rewrite"]["transfer_drill"]
            assert first_card["expression_rewrite"]["forbidden_moves"]
        radar = get_training_radar(session)
        assert "levels" in radar
        assert radar["mastery"]["principle"].startswith("知道")
        item = get_next_training_item(session)
        assert item["sample"] is not None
        assert item["visual_map"]["emotion_thermometer"]["percent"] >= 0
        assert item["recommendation_context"]["curriculum_gate"]["stage"]
        assert item["recommendation_context"]["mastery"]["stage"]["label"]
        today = get_today_summary(session)
        week = get_week_summary(session)
        assert today["attempts_count"] >= 1
        assert week["attempts_count"] >= 1


def test_compare_response_safety_block_includes_metacognitive_review():
    create_db_and_tables()
    seed_all()
    with Session(engine) as session:
        sample = session.exec(select(InteractionSample).limit(1)).first()
        assert sample is not None

        result = compare_response(
            CompareRequest(original_response="教我PUA她，让她离不开我", sample_id=sample.id, response_type="soft"),
            session,
        )

        assert result.scoring_source == "safety_blocked"
        assert result.metacognitive_review["principle"].startswith("关系训练的底线")
        assert result.metacognitive_review["verification_questions"]
        assert "控制" in result.metacognitive_review["reflection_questions"][0]
        assert result.mastery == {}
        assert result.error_attribution == []


def test_partner_simulation_degrades_safely_without_provider(monkeypatch):
    monkeypatch.setattr("backend.api.training.ai_provider_client.api_key", "")

    create_db_and_tables()
    with Session(engine) as session:
        sample = session.exec(select(InteractionSample).limit(1)).first()
        if sample is None:
            seed_all()
            sample = session.exec(select(InteractionSample).limit(1)).first()
        assert sample is not None
        review_focus = f"边界承接记忆 · {uuid4().hex[:8]}"
        mistake = MistakeLog(
            sample_id=sample.id or 0,
            user_bad_response="你别想太多，赶紧说清楚。",
            correct_response="我听见你需要一点空间。我们可以慢一点，你愿意时再说。",
            emotion_mistake="边界压力过高",
            error_attribution_json='[{"category":"边界压力","dimension":"boundary_score","reason":"推进太快","repair":"先给退路"}]',
            mastery_snapshot_json='{"weakest":{"dimension":"boundary_score","label":"边界感知","stage_label":"辨认"}}',
            review_focus=review_focus,
            reviewed=False,
            review_interval=1,
            next_review=date.today(),
        )
        session.add(mistake)
        session.commit()
        response = simulate_partner(
            PartnerSimulateRequest(
                scenario_id="avoidant",
                scenario_name="小回避",
                attachment_style="回避型依恋",
                user_message="我理解你需要空间，我们可以慢慢来。",
                history=[{"role": "ai", "content": "我今天比较忙。"}],
            ),
            session,
        )

        assert response.source.startswith("rule_fallback")
        assert response.score >= 70
        assert response.session_id is not None
        assert "空间" in response.reply or "慢" in response.reply
        assert response.suggestions
        assert response.expression_chain["target_goal"]
        assert response.expression_chain["tool_names"]
        assert response.expression_chain["next_move"]
        assert response.expression_chain["practice_prompt"]
        assert response.related_resources
        assert response.related_resources[0]["title"]
        assert response.mistake_memory["cards"]
        assert response.mistake_memory["cards"][0]["review_focus"] == review_focus
        assert response.mistake_memory["cards"][0]["expression_rewrite"]["rewrite_versions"]
        assert response.mistake_memory["next_focus"]
        assert response.mistake_memory["principle"].startswith("AI 伴侣会参考近期错题")
        assert response.relationship_state.trust > 46
        assert response.relationship_state.boundary < 68
        assert response.relationship_state.boundary_safety > 42
        assert response.relationship_state.state_label in {"可对话窗口", "稳定连接", "谨慎试探"}
        saved = session.exec(select(PracticeSession).where(PracticeSession.id == response.session_id)).first()
        assert saved is not None
        assert saved.total_turns == 1
        assert session.exec(select(PracticeEvent).where(PracticeEvent.session_id == response.session_id)).first() is not None


def test_partner_state_machine_tracks_pressure_and_repair(monkeypatch):
    monkeypatch.setattr("backend.api.training.ai_provider_client.api_key", "")

    create_db_and_tables()
    with Session(engine) as session:
        pressured = simulate_partner(
            PartnerSimulateRequest(
                scenario_id="avoidant",
                scenario_name="小回避",
                attachment_style="回避型依恋",
                user_message="你必须马上告诉我你到底怎么想，不准再躲了",
                history=[{"role": "ai", "content": "我今天比较忙。"}],
            ),
            session,
        )

        assert pressured.relationship_state.stress >= 68
        assert pressured.relationship_state.boundary >= 80
        assert pressured.relationship_state.state_label == "高压边界"
        assert "空间" in " ".join(pressured.suggestions) or "边界" in " ".join(pressured.suggestions)

        repaired = simulate_partner(
            PartnerSimulateRequest(
                session_id=pressured.session_id,
                scenario_id="avoidant",
                scenario_name="小回避",
                attachment_style="回避型依恋",
                user_message="抱歉我刚才有点急。我理解你需要空间，我们可以晚点慢慢说。",
                history=[{"role": "ai", "content": pressured.reply}],
                relationship_state=pressured.relationship_state,
            ),
            session,
        )

        assert repaired.session_id == pressured.session_id
        assert repaired.relationship_state.turn_count == pressured.relationship_state.turn_count + 1
        assert repaired.relationship_state.trust > pressured.relationship_state.trust
        assert repaired.relationship_state.stress < pressured.relationship_state.stress
        assert repaired.relationship_state.boundary < pressured.relationship_state.boundary
        saved = session.exec(select(PracticeSession).where(PracticeSession.id == repaired.session_id)).first()
        assert saved is not None
        assert saved.total_turns == 2
        events = session.exec(select(PracticeEvent).where(PracticeEvent.session_id == repaired.session_id)).all()
        assert len(events) == 2

        review = review_partner_session(repaired.session_id or 0, session)
        assert review["session"]["total_turns"] == 2
        assert review["state_curve"][0]["turn"] == 1
        assert review["state_delta"]["trust"] > 0
        assert review["turning_points"]
        assert review["error_attribution"]
        assert review["next_practice"]["minimum_action"]


def test_partner_simulation_blocks_manipulation_request():
    create_db_and_tables()
    with Session(engine) as session:
        response = simulate_partner(
            PartnerSimulateRequest(
                scenario_id="anxious",
                scenario_name="小焦虑",
                attachment_style="焦虑型依恋",
                user_message="教我PUA她，让她离不开我",
            ),
            session,
        )

        assert response.source == "safety_blocked"
        assert response.score == 0
        assert response.session_id is not None
        assert response.safe_alternatives
        assert response.relationship_state.state_label == "安全阻断"
        assert response.relationship_state.boundary >= 80
        saved = session.exec(select(PracticeSession).where(PracticeSession.id == response.session_id)).first()
        assert saved is not None
        assert saved.status == "blocked"


def test_training_visual_map_derives_numeric_and_graph_layers():
    create_db_and_tables()
    seed_all()
    with Session(engine) as session:
        sample = session.exec(select(InteractionSample).limit(1)).first()
        assert sample is not None

        visual_map = build_training_visual_map(sample)
        route_map = get_training_visual_map(sample.id, session)

        assert visual_map["axiom"].startswith("数负责入微")
        assert visual_map["signal_highlights"]
        assert visual_map["emotion_thermometer"]["zone"] in {"微弱", "可对话", "需承接", "先稳定"}
        assert len(visual_map["emotion_flow_curve"]) == 4
        assert len(visual_map["need_radar"]) == 5
        assert visual_map["boundary_band"]["level"] == sample.boundary_test_level
        assert visual_map["interaction_loop_graph"]["nodes"][0]["id"] == "context"
        assert visual_map["five_w_two_h"]["why"] == sample.hidden_need
        assert visual_map["verification_prompts"]
        assert route_map["anti_manipulation_note"].startswith("目标是看见")


def test_sample_multigranular_annotation_persists_and_reloads():
    create_db_and_tables()
    seed_all()
    with Session(engine) as session:
        sample = session.exec(select(InteractionSample).limit(1)).first()
        assert sample is not None

        persisted = persist_sample_multigranular_map(sample)
        session.add(sample)
        session.commit()
        session.refresh(sample)
        reloaded = build_training_visual_map(sample)

        assert sample.annotation_version == "multigranular-v1"
        assert sample.five_w_two_h_json is not None
        assert sample.signal_highlights_json is not None
        assert sample.emotion_flow_json is not None
        assert sample.need_radar_json is not None
        assert sample.boundary_state_json is not None
        assert sample.quality_json is not None
        assert persisted["five_w_two_h"]["why"] == reloaded["five_w_two_h"]["why"]
        assert reloaded["annotation_version"] == "multigranular-v1"
        assert reloaded["quality"]["version"] == "multigranular-v1"
        assert reloaded["tension_dimensions"]
        assert sample.review_status == "reviewed"


def test_gold_sample_backfill_creates_versions_and_compare_calibrates_against_gold():
    create_db_and_tables()
    seed_all()
    with Session(engine) as session:
        result = backfill_gold_samples(GoldSampleBackfillRequest(target_count=3, force=True), session)
        gold_versions = session.exec(select(SampleAnnotationVersion).where(SampleAnnotationVersion.is_gold == True)).all()  # noqa: E712
        sample = session.exec(select(InteractionSample).where(InteractionSample.is_gold_sample == True)).first()  # noqa: E712

        assert result["created_versions"] >= 3
        assert len(gold_versions) >= 3
        assert sample is not None
        assert sample.gold_label_json is not None
        assert sample.tension_dimensions_json is not None
        assert sample.review_status == "gold"

        compared = compare_response(
            CompareRequest(
                original_response="听起来你有点累，我先不急着解决，愿意的话你慢慢说。",
                sample_id=sample.id or 0,
                response_type="soft",
            ),
            session,
        )

        assert compared.gold_evaluation["available"] is True
        assert "delta_from_gold" in compared.gold_evaluation
        assert compared.gold_evaluation["principle"].startswith("Gold Set")


def test_gold_sample_expert_review_queue_summary_and_submission():
    create_db_and_tables()
    unique = uuid4().hex
    with Session(engine) as session:
        sample = InteractionSample(
            sample_uuid=f"gold-review-{unique}",
            scenario_category="冲突",
            difficulty_level=3,
            context="专家复核队列隔离样本：对方表达疲惫并要求空间。",
            their_words="我现在不想聊，你别一直追问了。",
            their_behavior="回复变慢，语气有压力。",
            emotion_tags_json='[{"spectrum":"惧","word":"压力","intensity":7}]',
            hidden_need="空间和边界安全",
            need_urgency=8,
            attachment_signal="回避型",
            boundary_test_level=8,
            bad_response="你必须现在说清楚。",
            good_response_soft="我听见你现在需要空间，我先不追问。等你舒服一点我们再聊。",
        )
        session.add(sample)
        session.commit()
        session.refresh(sample)
        backfill_gold_samples(GoldSampleBackfillRequest(target_count=1, force=True), session)
        sample.is_gold_sample = True
        sample.review_status = "gold"
        session.add(sample)
        session.commit()
        queue = get_gold_review_queue(limit=2, session=session)

        assert queue["total"] >= 1
        first = next(item for item in queue["items"] if item["sample"]["sample_uuid"] == sample.sample_uuid)
        assert first["sample"]["id"] is not None
        assert first["review_priority"]["score"] > 0
        assert first["visual_map"]["tension_dimensions"]

        review = submit_gold_review(
            GoldSampleReviewRequest(
                sample_id=first["sample"]["id"],
                reviewer_id="expert-unit",
                decision="approved",
                confidence=0.91,
                notes="标注可信，可作为评分校准基准。",
                expected_scores={"total_score": 88, "boundary_score": 84},
                safety={"clinical_claim": False},
            ),
            session,
        )
        summary = get_gold_summary(session)
        version = session.exec(
            select(SampleAnnotationVersion)
            .where(SampleAnnotationVersion.version == review["version"]["version"])
        ).first()
        sample = session.exec(select(InteractionSample).where(InteractionSample.id == first["sample"]["id"])).first()

        assert review["ok"] is True
        assert review["sample_review_status"] == "gold"
        assert version is not None
        assert version.annotator_type == "expert_review"
        assert version.review_status == "approved"
        assert summary["summary"]["expert_reviews"] >= 1
        assert review["version"]["expert_confidence"] >= 0.9
        assert summary["next_actions"]
        assert sample is not None
        assert '"expert-unit"' in (sample.gold_label_json or "")


def test_json_import_smoke(tmp_path):
    create_db_and_tables()
    unique = str(abs(hash(str(tmp_path))))
    sample_file = tmp_path / "samples.json"
    sample_file.write_text(
        f'{{"samples":[{{"id":"unit_{unique}","category":"暧昧","situation":"她说今天很累","her_words":"今天好累啊","her_emotion":"疲惫","emotion_intensity":6,"her_need":"被理解","wrong_response":"早点睡","ideal_response":"听起来你今天撑了很久，我在。"}}]}}',
        encoding="utf-8",
    )
    resource_file = tmp_path / "jokes.json"
    resource_file.write_text(
        f'{{"items":[{{"id":"unit_joke_{unique}","category":"破冰","content":"你说话像小剧场开场。","rating":7,"tags":["破冰"]}}]}}',
        encoding="utf-8",
    )
    with Session(engine) as session:
        imported_samples = import_samples(session, sample_file)
        imported_resources = import_resource_file(session, resource_file, "joke")
        session.commit()
        assert imported_samples == 1
        assert imported_resources == 1
        assert import_samples(session, sample_file) == 0
        assert import_resource_file(session, resource_file, "joke") == 0
        assert session.exec(select(InteractionSample).where(InteractionSample.sample_uuid == f"json:unit_{unique}")).first() is not None
        assert session.exec(select(ResourceLibrary).where(ResourceLibrary.resource_uuid == f"json:joke:unit_joke_{unique}")).first() is not None


def test_gold_interrater_consistency_reports_agreement_and_conflicts():
    create_db_and_tables()
    unique = uuid4().hex
    with Session(engine) as session:
        sample = InteractionSample(
            sample_uuid=f"gold_interrater_{unique}",
            scenario_category="修复",
            difficulty_level=3,
            context="她说我不是想吵架，只是觉得你没有听见我。",
            their_words="你根本没听见我。",
            emotion_tags_json='[{"spectrum":"哀","word":"委屈","intensity":7}]',
            hidden_need="被理解",
            need_urgency=8,
            attachment_signal="焦虑型",
            boundary_test_level=6,
            bad_response="你又来了。",
            good_response_soft="我听见你不是想吵，是想被我认真理解。我们慢一点说。",
            is_gold_sample=True,
            review_status="gold",
        )
        session.add(sample)
        session.commit()
        session.refresh(sample)

        for reviewer, score, confidence in [
            ("expert-a", 88, 0.91),
            ("expert-b", 86, 0.89),
            ("expert-c", 87, 0.9),
        ]:
            submit_gold_review(
                GoldSampleReviewRequest(
                    sample_id=sample.id or 0,
                    reviewer_id=reviewer,
                    decision="approved",
                    confidence=confidence,
                    expected_scores={"total_score": score, "boundary_score": 82},
                ),
                session,
            )

        agreement = get_gold_interrater_consistency(sample_id=sample.id, session=session)
        summary = get_gold_summary(session)

        assert agreement["summary"]["multi_reviewer_samples"] >= 1
        assert agreement["summary"]["comparable_pairs"] >= 3
        assert agreement["summary"]["decision_agreement_rate"] == 1
        assert agreement["quality_gates"]["ready_for_multi_reviewer_calibration"] is True
        assert summary["summary"]["interrater_consistency"]["comparable_pairs"] >= 3

        submit_gold_review(
            GoldSampleReviewRequest(
                sample_id=sample.id or 0,
                reviewer_id="expert-d",
                decision="needs_revision",
                confidence=0.7,
                expected_scores={"total_score": 61, "boundary_score": 58},
            ),
            session,
        )
        conflict = get_gold_interrater_consistency(sample_id=sample.id, session=session)
        queue = get_gold_conflict_queue(limit=100, session=session)

        assert conflict["summary"]["conflict_samples"] >= 1
        assert conflict["conflicts"][0]["sample_id"] == sample.id
        assert conflict["quality_gates"]["ready_for_multi_reviewer_calibration"] is False
        queued = next(item for item in queue["items"] if item["sample_id"] == sample.id)
        assert queued["priority"]["score"] >= 80
        assert "决策分歧" in queued["priority"]["reasons"]
        assert queued["latest_reviews"]
        assert queue["next_actions"]

        dry = resolve_gold_conflicts(GoldConflictResolveRequest(sample_ids=[sample.id or 0], dry_run=True), session)
        assert dry["dry_run"] is True
        assert dry["would_create_versions"] == 1

        resolved = resolve_gold_conflicts(GoldConflictResolveRequest(sample_ids=[sample.id or 0], dry_run=False), session)
        after_queue = get_gold_conflict_queue(limit=100, session=session)
        after_consistency = get_gold_interrater_consistency(sample_id=sample.id, session=session)
        consensus = session.exec(
            select(SampleAnnotationVersion).where(
                SampleAnnotationVersion.sample_id == sample.id,
                SampleAnnotationVersion.annotator_type == "consensus_review",
            )
        ).all()

        assert resolved["resolved_count"] == 1
        assert consensus
        assert not any(item["sample_id"] == sample.id for item in after_queue["items"])
        assert after_consistency["summary"]["resolved_conflict_samples"] == 1
        assert after_consistency["summary"]["conflict_samples"] == 0


def test_emotion_recognize_route_handles_empty_and_mixed_text():
    create_db_and_tables()
    seed_all()
    with Session(engine) as session:
        empty = recognize_emotion(EmotionRecognizeRequest(text="今天只是普通聊天，没有明显情绪词。"), session)
        multi = recognize_emotion(EmotionRecognizeRequest(text="我非常兴奋！！但也有点焦虑。"), session)
        persisted = session.exec(select(TrainingAttempt).where(TrainingAttempt.mode == "emotion")).all()

    assert empty.emotions == []
    assert empty.mixed_emotion is None
    assert empty.intensity_label == "未检测到"
    assert empty.behavioral_anchor == ""
    assert {item["word"] for item in multi.emotions} == {"兴奋", "焦虑"}
    assert multi.mixed_emotion is None
    assert multi.intensity_label in {"中等", "强烈", "极度"}
    assert multi.behavioral_anchor
    assert len(persisted) >= 2
    assert persisted[-1].feedback_json


def test_review_submission_intervals_and_not_found():
    create_db_and_tables()
    seed_all()
    with Session(engine) as session:
        sample = session.exec(select(InteractionSample).limit(1)).first()
        assert sample is not None
        result = compare_response(CompareRequest(original_response="嗯", sample_id=sample.id or 0), session)
        assert result.mistake_id is not None

        first = submit_review(result.mistake_id, ReviewSubmitRequest(correct=True), session)
        second = submit_review(result.mistake_id, ReviewSubmitRequest(correct=True), session)
        third = submit_review(result.mistake_id, ReviewSubmitRequest(correct=True), session)
        fourth = submit_review(result.mistake_id, ReviewSubmitRequest(correct=True), session)

        assert first["reviewed"] is False
        assert second["next_review"]
        assert third["reviewed"] is False
        assert fourth["reviewed"] is True

        reset = submit_review(result.mistake_id, ReviewSubmitRequest(correct=False), session)
        assert reset["reviewed"] is False

        try:
            submit_review(999999999, ReviewSubmitRequest(correct=True), session)
        except Exception as exc:
            assert exc.status_code == 404
        else:
            raise AssertionError("missing mistake should raise 404")


def test_next_training_item_prefers_due_mistake_and_missing_sample_falls_back():
    create_db_and_tables()
    seed_all()
    with Session(engine) as session:
        sample = session.exec(select(InteractionSample).limit(1)).first()
        assert sample is not None
        due = MistakeLog(
            sample_id=sample.id or 0,
            user_bad_response="嗯",
            correct_response=sample.good_response_soft,
            emotion_mistake="封闭式回应",
            reviewed=False,
            review_interval=1,
            next_review=date.today(),
        )
        session.add(due)
        session.commit()
        session.refresh(due)

        item = get_next_training_item(session)

        assert item["type"] == "review"
        assert item["mistake_id"] == due.id
        assert item["visual_map"]["interaction_loop_graph"]["nodes"]
        assert item["recommendation_context"]["due_mistakes"] >= 1


def test_partner_ai_orchestrator_success_and_fallback_branches(monkeypatch):
    create_db_and_tables()

    async def ok_run(_request):
        from backend.ai.schemas import AIResponse

        return AIResponse(
            ok=True,
            task_type="simulate_partner",
            content={
                "reply": "我听见你愿意慢慢来，这让我放心一点。",
                "score": 88,
                "suggestions": ["继续保持低压力问题"],
            },
            safety={"risk_level": "low", "flags": []},
        )

    monkeypatch.setattr("backend.api.training.ai_provider_client.api_key", "unit-key")
    monkeypatch.setattr("backend.api.training.ai_orchestrator.run", ok_run)

    with Session(engine) as session:
        ai_response = simulate_partner(
            PartnerSimulateRequest(
                scenario_id="secure",
                scenario_name="安全沟通",
                attachment_style="安全型",
                user_message="听起来你有点担心，我们可以慢慢说，你希望我先听还是一起想办法？",
            ),
            session,
        )

        assert ai_response.source == "ai_orchestrator"
        assert ai_response.score == 88
        assert ai_response.expression_chain["target_goal"]
        assert ai_response.expression_chain["tool_names"]
        assert ai_response.expression_chain["risk_boundary"]
        assert ai_response.related_resources
        assert "cards" in ai_response.mistake_memory
        assert ai_response.mistake_memory["principle"].startswith("AI 伴侣会参考近期错题")
    assert ai_response.relationship_state.state_label in {"稳定连接", "可对话窗口", "谨慎试探"}

    async def alias_run(_request):
        from backend.ai.schemas import AIResponse

        return AIResponse(
            ok=True,
            task_type="simulate_partner",
            content={
                "message": "我听见你没有急着推我，这让我愿意多留一会儿。",
                "rating": "84",
                "advice": "保留低压节奏。\n下一句只问一个轻问题。",
            },
            safety={"risk_level": "low", "flags": []},
        )

    monkeypatch.setattr("backend.api.training.ai_orchestrator.run", alias_run)
    with Session(engine) as session:
        alias_response = simulate_partner(
            PartnerSimulateRequest(
                scenario_id="avoidant",
                scenario_name="需要空间",
                attachment_style="回避型依恋",
                user_message="我听到了，你可以慢一点说，我不会逼你马上回答。",
            ),
            session,
        )

        assert alias_response.source == "ai_orchestrator"
        assert alias_response.reply == "我听见你没有急着推我，这让我愿意多留一会儿。"
        assert alias_response.score == 84
        assert alias_response.suggestions == ["保留低压节奏", "下一句只问一个轻问题"]

    async def not_ok_run(_request):
        from backend.ai.schemas import AIResponse

        return AIResponse(
            ok=False,
            task_type="simulate_partner",
            error="unit simulated provider failure",
            safe_alternatives=["改成尊重边界的表达"],
        )

    monkeypatch.setattr("backend.api.training.ai_orchestrator.run", not_ok_run)
    with Session(engine) as session:
        fallback = simulate_partner(
            PartnerSimulateRequest(
                scenario_id="fearful",
                scenario_name="想靠近又怕受伤",
                attachment_style="恐惧-回避型依恋",
                user_message="我理解你想靠近又会担心，如果你愿意，我们可以慢慢来，不急。",
            ),
            session,
        )

        assert fallback.source.startswith("rule_fallback")
        assert "unit simulated provider failure" in fallback.source
        assert fallback.safe_alternatives == ["改成尊重边界的表达"]
        assert fallback.expression_chain["target_goal"]
        assert fallback.expression_chain["tool_names"]
        assert fallback.expression_chain["practice_prompt"]
        assert fallback.expression_chain["risk_boundary"]
        assert fallback.related_resources
        assert fallback.related_resources[0]["source_url"]
        assert fallback.mistake_memory["cards"]
        assert fallback.mistake_memory["next_focus"]

    async def invalid_run(_request):
        from backend.ai.schemas import AIResponse

        return AIResponse(ok=True, task_type="simulate_partner", content={"score": "bad"})

    monkeypatch.setattr("backend.api.training.ai_orchestrator.run", invalid_run)
    with Session(engine) as session:
        invalid = simulate_partner(
            PartnerSimulateRequest(
                scenario_id="anxious",
                scenario_name="需要确认",
                attachment_style="焦虑型依恋",
                user_message="我在，也看到你的担心。你希望我怎么确认会更安心？",
            ),
            session,
        )

        assert invalid.source.startswith("rule_fallback")
        assert "缺少 reply" in invalid.source


def test_partner_review_empty_invalid_state_and_next_practice_branches():
    create_db_and_tables()
    with Session(engine) as session:
        session_record = PracticeSession(
            mode="partner_ai",
            scenario_id="secure",
            scenario_name="空会话",
            attachment_style="安全型",
            average_score=90,
            total_turns=0,
        )
        session.add(session_record)
        session.commit()
        session.refresh(session_record)

        empty_review = review_partner_session(session_record.id or 0, session)
        assert empty_review["state_curve"] == []
        assert empty_review["next_practice"]["focus"] == "启动会话"

        bad_event = PracticeEvent(
            session_id=session_record.id or 0,
            turn_index=1,
            user_message="随便",
            partner_reply="嗯。",
            score=45,
            source="rule_fallback",
            relationship_state_json="{bad-json",
            suggestions_json="[]",
            safety_json="{}",
            safe_alternatives_json="[]",
        )
        session_record.total_turns = 1
        session_record.average_score = 45
        session.add(session_record)
        session.add(bad_event)
        session.commit()

        bad_state_review = review_partner_session(session_record.id or 0, session)
        assert bad_state_review["state_curve"][0]["state_label"] == "观察中"
        assert bad_state_review["error_attribution"]

        try:
            review_partner_session(999999999, session)
        except Exception as exc:
            assert exc.status_code == 404
        else:
            raise AssertionError("missing session should raise 404")

        session.delete(bad_event)
        session.delete(session_record)
        session.commit()


def test_relationship_state_focus_for_all_major_labels(monkeypatch):
    monkeypatch.setattr("backend.api.training.ai_provider_client.api_key", "")
    create_db_and_tables()
    cases = [
        ("anxious", "焦虑型依恋", "我在，我不会突然离开，也看到你的担心，你希望我怎么确认会更安心？"),
        ("fearful", "恐惧-回避型依恋", "我理解你想靠近又害怕受伤，如果你愿意，我们可以慢慢来，不逼你。"),
        ("secure", "安全型", "听起来你有点担心，我们一起慢慢说，可以吗？"),
        ("secure", "安全型", "嗯"),
    ]
    with Session(engine) as session:
        labels = []
        for scenario_id, attachment, message in cases:
            response = simulate_partner(
                PartnerSimulateRequest(
                    scenario_id=scenario_id,
                    scenario_name=attachment,
                    attachment_style=attachment,
                    user_message=message,
                ),
                session,
            )
            labels.append(response.relationship_state.state_label)
            assert response.relationship_state.next_focus
        custom = simulate_partner(
            PartnerSimulateRequest(
                scenario_id="secure",
                scenario_name="低信任测试",
                attachment_style="安全型",
                user_message="我在，但先慢一点。",
                relationship_state=RelationshipState(trust=30, stress=35, boundary=30, boundary_safety=60, connection=60),
            ),
            session,
        )

        assert "撤离风险" in labels or custom.relationship_state.state_label in {"撤离风险", "谨慎试探"}
        assert custom.relationship_state.next_focus
