from sqlmodel import Session

from backend.api.evolution import EvolutionItemCreate, build_pipeline_summary, create_item, latest, summary
from backend.database.connection import create_db_and_tables, engine


def test_evolution_summary_and_latest_include_pipeline_state():
    create_db_and_tables()
    with Session(engine) as session:
        published = create_item(
            EvolutionItemCreate(
                title="测试发布条目",
                content="系统应持续进化",
                category="technique",
                quality_score=91,
                status="published",
                source_name="pytest source",
                source_type="manual",
            ),
            session,
        )
        create_item(
            EvolutionItemCreate(
                title="测试候选条目",
                content="等待评审的进化候选",
                category="case",
                quality_score=67,
                status="draft",
                source_name="pytest source",
                source_type="manual",
            ),
            session,
        )
        create_item(
            EvolutionItemCreate(
                title="测试拒绝条目",
                content="质量不足的进化素材",
                category="warning",
                quality_score=42,
                status="rejected",
                source_name="pytest rejected",
                source_type="social_case",
            ),
            session,
        )

        assert published["title"] == "测试发布条目"

        pipeline = summary(session)
        assert pipeline["totals"]["items"] >= 3
        assert pipeline["totals"]["candidates"] >= 1
        assert pipeline["totals"]["published"] >= 1
        assert pipeline["totals"]["rejected"] >= 1
        assert pipeline["status_counts"]["draft"] >= 1
        assert pipeline["quality"]["distribution"]["excellent"] >= 1
        assert pipeline["quality"]["distribution"]["needs_review"] >= 1
        assert "source_quality_matrix" in pipeline["visual_metrics"]
        assert "review_publish_funnel" in pipeline["visual_metrics"]
        assert "learning_increment" in pipeline["visual_metrics"]
        assert pipeline["next_actions"]

        data = latest(session)
        assert "items" in data
        assert "summary" in data
        assert data["summary"]["totals"]["published"] >= 1
        assert any(item["title"] == "测试发布条目" for item in data["items"])


def test_build_pipeline_summary_empty_database_shape():
    create_db_and_tables()
    with Session(engine) as session:
        pipeline = build_pipeline_summary(session)
        assert pipeline["heartbeat"]["state"] in {"empty", "learning", "stable", "congested", "stalled"}
        assert "sources" in pipeline["totals"]
        assert "average_score" in pipeline["quality"]
        assert pipeline["visual_metrics"]["review_publish_funnel"][0]["label"] == "来源登记"
