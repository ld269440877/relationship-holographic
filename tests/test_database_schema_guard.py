from fastapi.testclient import TestClient
from sqlalchemy import create_engine, text
from sqlmodel import Session, SQLModel
from sqlmodel.pool import StaticPool

from backend.database.connection import create_db_and_tables, engine
from backend.database.migration_runner import migration_plan, run_formal_migrations
from backend.database.schema_guard import SCHEMA_REVISION, audit_schema, ensure_schema_compatibility
from backend.main import app
from backend.models.knowledge import ContentImportBatch, ContentImportIssue
from backend.models.sample import InteractionSample


def test_schema_guard_adds_missing_columns_to_existing_sqlite_table():
    old_engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    with old_engine.begin() as connection:
        connection.execute(text("CREATE TABLE user_profile (id INTEGER PRIMARY KEY, attachment_style VARCHAR)"))

    # Import all model metadata, then run the schema guard against a deliberately old table.
    from backend.models import user  # noqa: F401

    SQLModel.metadata.create_all(old_engine)
    audit = ensure_schema_compatibility(old_engine)

    columns = {
        row[1]
        for row in old_engine.connect().execute(text("PRAGMA table_info(user_profile)")).fetchall()
    }
    assert "core_wound" in columns
    assert "progress_json" in columns
    assert audit["status"] == "ok"
    assert audit["revision"] == SCHEMA_REVISION
    assert any(item["table"] == "user_profile" for item in audit["migration"]["added_columns"])


def test_database_health_and_migrate_routes_are_registered():
    create_db_and_tables()
    client = TestClient(app)

    health = client.get("/api/database/health")
    migrated = client.post("/api/database/migrate")

    assert health.status_code == 200
    assert health.json()["status"] == "ok"
    assert health.json()["integrity_check"] == "ok"
    assert "interaction_samples" in health.json()["row_counts"]
    assert health.json()["schema_evolution"]["current_revision"] == SCHEMA_REVISION
    assert health.json()["content_sources"]["total_known_assets"] >= 1
    assert health.json()["content_import_status"]["available"] is True
    assert "formal_migration_status" in health.json()
    assert "ai_provider_probe_logs" in health.json()["row_counts"]
    assert migrated.status_code == 200
    assert migrated.json()["revision"] == SCHEMA_REVISION
    assert migrated.json()["missing_tables"] == []
    assert migrated.json()["missing_columns"] == {}


def test_real_engine_schema_audit_has_no_missing_columns():
    create_db_and_tables()

    audit = audit_schema(engine)

    assert audit["status"] == "ok"
    assert audit["missing_tables"] == []
    assert audit["missing_columns"] == {}
    assert audit["migration_count"] >= 1
    assert audit["schema_evolution"]["latest_recorded"]["revision"] == SCHEMA_REVISION
    assert any(item["revision"] == "2026_05_21_content_sources_v1" for item in audit["schema_evolution"]["plan"])


def test_formal_migration_runner_dry_run_and_apply_are_auditable():
    test_engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    SQLModel.metadata.create_all(test_engine)
    ensure_schema_compatibility(test_engine)

    dry_run = run_formal_migrations(test_engine, dry_run=True)
    before_plan = migration_plan(test_engine)
    applied = run_formal_migrations(test_engine, dry_run=False, create_backup=False)
    after_plan = migration_plan(test_engine)
    audit = audit_schema(test_engine)

    assert dry_run["status"] == "dry_run"
    assert dry_run["would_run"] == [
        "2026_05_21_formal_runner_v1",
        "2026_05_21_metadata_vector_index_rebuild_v1",
        "2026_05_22_import_issue_status_normalization_v1",
    ]
    assert before_plan["pending"][0]["revision"] == "2026_05_21_formal_runner_v1"
    assert applied["status"] == "applied"
    assert applied["applied"] == [
        "2026_05_21_formal_runner_v1",
        "2026_05_21_metadata_vector_index_rebuild_v1",
        "2026_05_22_import_issue_status_normalization_v1",
    ]
    assert applied["backup"]["created"] is False
    assert after_plan["pending"] == []
    assert after_plan["runner"]["latest_run"]["status"] == "applied"
    assert audit["formal_migration_status"]["available"] is True
    assert audit["formal_migration_status"]["runs"] >= 2
    with test_engine.connect() as connection:
        result_count = connection.execute(text("SELECT count(*) FROM formal_migration_revision_results")).scalar()
    assert result_count == 2


def test_formal_migration_normalizes_import_issue_status_and_audits_result():
    test_engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    SQLModel.metadata.create_all(test_engine)
    ensure_schema_compatibility(test_engine)
    with Session(test_engine) as session:
        session.add(ContentImportIssue(
            source_name="pytest_legacy_import.json",
            source_id="legacy_blank_status",
            severity="warning",
            message="legacy row without normalized status",
            status="",
        ))
        session.add(ContentImportIssue(
            source_name="pytest_legacy_import.json",
            source_id="legacy_resolved_status",
            severity="warning",
            message="legacy row already resolved",
            status="resolved",
        ))
        session.commit()

    result = run_formal_migrations(test_engine, dry_run=False, create_backup=False)

    assert "2026_05_22_import_issue_status_normalization_v1" in result["applied"]
    with test_engine.connect() as connection:
        blank_status = connection.execute(
            text("SELECT count(*) FROM content_import_issues WHERE status IS NULL OR trim(status) = ''")
        ).scalar()
        normalized_status = connection.execute(
            text("SELECT status FROM content_import_issues WHERE source_id = 'legacy_blank_status'")
        ).scalar()
        audit_json = connection.execute(
            text(
                "SELECT result_json FROM formal_migration_revision_results "
                "WHERE revision = '2026_05_22_import_issue_status_normalization_v1' "
                "ORDER BY id DESC LIMIT 1"
            )
        ).scalar()

    assert blank_status == 0
    assert normalized_status == "open"
    assert audit_json is not None
    assert "normalized_blank_status_rows" in str(audit_json)
    assert "raw_source_text_saved" in str(audit_json)


def test_database_formal_migration_routes_are_registered():
    create_db_and_tables()
    client = TestClient(app)

    plan = client.get("/api/database/migration-plan")
    dry_run = client.post("/api/database/migration-run?dry_run=true")

    assert plan.status_code == 200
    assert plan.json()["runner"]["table"] == "formal_migration_runs"
    assert "pending" in plan.json()
    assert dry_run.status_code == 200
    assert dry_run.json()["status"] == "dry_run"
    assert "schema_before" in dry_run.json()


def test_schema_audit_reports_old_json_columns_without_crashing():
    old_engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    with old_engine.begin() as connection:
        connection.execute(text("CREATE TABLE user_profile (id INTEGER PRIMARY KEY, attachment_style VARCHAR)"))

    audit = audit_schema(old_engine)

    assert audit["status"] == "needs_attention"
    assert "progress_json" in audit["missing_columns"]["user_profile"]
    assert audit["json_quality"]["user_profile.progress_json"]["skipped"] == "missing_column"


def test_schema_audit_flags_invalid_json_content():
    bad_engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    from backend.models import emotion, evolution, knowledge, resource, sample, training, user  # noqa: F401

    SQLModel.metadata.create_all(bad_engine)
    ensure_schema_compatibility(bad_engine)
    with Session(bad_engine) as session:
        session.add(InteractionSample(
            sample_uuid="bad-json-sample",
            scenario_category="冲突",
            difficulty_level=1,
            context="用于验证 JSON 健康检查的样本",
            their_words="随便你。",
            emotion_tags_json="{not-json",
            bad_response="好吧。",
            good_response_soft="我不确定理解得对不对，你是不是有点不舒服？",
        ))
        session.commit()

    audit = audit_schema(bad_engine)

    assert audit["status"] == "needs_attention"
    assert audit["json_quality"]["interaction_samples.emotion_tags_json"]["invalid"] == 1
    assert audit["json_quality"]["interaction_samples.emotion_tags_json"]["examples"][0]["id"] == 1


def test_schema_audit_reports_content_import_status():
    create_db_and_tables()
    with Session(engine) as session:
        batch = ContentImportBatch(
            source_name="pytest_content_source.json",
            source_type="json",
            imported_sections=1,
            imported_entries=2,
            skipped_entries=0,
            issues_count=1,
            report_json='{"ok": true}',
        )
        session.add(batch)
        session.commit()
        session.refresh(batch)
        session.add(ContentImportIssue(
            batch_id=batch.id,
            source_name=batch.source_name,
            source_id="pytest",
            severity="warning",
            message="测试问题",
        ))
        session.commit()

    audit = audit_schema(engine)

    assert audit["content_import_status"]["available"] is True
    assert audit["content_import_status"]["batches"] >= 1
    assert audit["content_import_status"]["issues"] >= 1
    assert any(
        item["source_name"] == "pytest_content_source.json"
        for item in audit["content_import_status"]["latest_batches"]
    )
