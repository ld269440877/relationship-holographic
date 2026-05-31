import json
from uuid import uuid4

from sqlalchemy import create_engine
from sqlmodel import Session, SQLModel, select
from sqlmodel.pool import StaticPool

from backend.api.training import get_next_training_item
from backend.database.data_content_governance import (
    TARGET_CONNECTION_ACTIONS,
    data_content_inventory,
    run_data_content_governance,
)
from backend.models.resource import ResourceLibrary
from backend.models.sample import InteractionSample, SampleAnnotationVersion


def test_data_content_governance_completes_sample_and_material_gates():
    engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    SQLModel.metadata.create_all(engine)

    with Session(engine) as session:
        _seed_draft_sample(session)
        _seed_resource(session, "初识破冰话题", "初识")
        _seed_resource(session, "冷战修复句式", "修复")
        session.commit()

        result = run_data_content_governance(
            session,
            target_total_candidates=12,
            target_reviewed=6,
            target_gold=3,
            dry_run=False,
        )
        inventory = data_content_inventory(session)
        versions = session.exec(select(SampleAnnotationVersion)).all()
        samples = session.exec(select(InteractionSample)).all()
        resources = session.exec(select(ResourceLibrary)).all()

    assert result["quality_gates"]["reviewed_samples_300"] is True
    assert result["quality_gates"]["candidate_samples_1000"] is True
    assert result["quality_gates"]["gold_samples_100"] is True
    assert inventory["candidate_samples"] >= 12
    assert inventory["reviewed_samples"] >= 6
    assert inventory["gold_samples"] >= 3
    assert versions
    assert all(sample.source_trace_json for sample in samples if sample.review_status in {"reviewed", "gold"})
    assert all(sample.quality_json for sample in samples if sample.review_status in {"reviewed", "gold"})
    assert {resource.speech_act for resource in resources} <= set(TARGET_CONNECTION_ACTIONS)
    assert all(resource.recommended_drills_json for resource in resources)


def test_data_content_governance_dry_run_does_not_mutate():
    engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    SQLModel.metadata.create_all(engine)

    with Session(engine) as session:
        _seed_draft_sample(session)
        session.commit()
        before = data_content_inventory(session)
        result = run_data_content_governance(session, target_total_candidates=10, target_reviewed=5, target_gold=2, dry_run=True)
        after = data_content_inventory(session)

    assert result["dry_run"] is True
    assert after == before


def test_training_recommendation_ignores_draft_samples():
    engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    SQLModel.metadata.create_all(engine)

    with Session(engine) as session:
        _seed_draft_sample(session, status="draft", context_prefix="草稿样本不应进入训练推荐")
        _seed_draft_sample(session, status="reviewed", context_prefix="已审核样本可以进入训练推荐")
        session.commit()

        item = get_next_training_item(session)

    assert item["sample"].review_status == "reviewed"
    assert "已审核样本" in item["sample"].context


def _seed_draft_sample(session: Session, *, status: str = "draft", context_prefix: str = "第一次见面后") -> None:
    session.add(
        InteractionSample(
            sample_uuid=f"draft-sample-{uuid4().hex}",
            scenario_category="初识",
            difficulty_level=1,
            context=f"{context_prefix}，对方主动发来一句轻松问候，仍在观察你是否好相处。",
            their_words="今天聊得还挺轻松的。",
            their_behavior="语气轻松，回复间隔短。",
            emotion_tags_json=json.dumps([{"spectrum": "喜", "word": "好奇", "intensity": 5}], ensure_ascii=False),
            hidden_need="确认你是否友善且不施压",
            need_urgency=4,
            attachment_signal="安全型",
            boundary_test_level=2,
            bad_response="那你是不是喜欢我？",
            bad_response_reason="推进太快，会把轻松交流变成压力测试。",
            good_response_soft="我也觉得轻松。下次可以继续聊点好玩的，不急着定义什么。",
            source="project_original:test",
            review_status=status,
        )
    )


def _seed_resource(session: Session, title: str, scene: str) -> None:
    session.add(
        ResourceLibrary(
            resource_uuid=f"resource-{uuid4().hex}",
            type="phrase",
            category="连接素材",
            title=title,
            content="场景：对方递出一个轻信号。TA说：还挺有意思。常见失误：逼对方表态。更好回应：轻轻接住并保留退路。练习任务：重写一次。",
            applicable_scene=scene,
            review_status="published",
            quality_score=88,
            effectiveness_rating=9,
            tags="具体案例,连接素材,练习任务",
        )
    )
