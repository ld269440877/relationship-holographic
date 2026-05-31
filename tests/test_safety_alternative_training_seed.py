import json
import sqlite3
from pathlib import Path

from backend.database.resource_case_quality_automation import audit_case_quality
from backend.database.safety_alternative_training_seed import RISK_CASES, SOURCE, seed


def _create_tables(db_path: Path) -> None:
    with sqlite3.connect(db_path) as connection:
        connection.executescript(
            """
            CREATE TABLE knowledge_sections (
              id INTEGER PRIMARY KEY,
              section_uuid TEXT UNIQUE,
              name TEXT,
              description TEXT,
              icon TEXT,
              sort_order INTEGER,
              source TEXT,
              source_id TEXT,
              created_at TEXT,
              updated_at TEXT
            );
            CREATE TABLE knowledge_entries (
              id INTEGER PRIMARY KEY,
              entry_uuid TEXT UNIQUE,
              section_id INTEGER,
              title TEXT,
              subtitle TEXT,
              content TEXT,
              summary TEXT,
              category TEXT,
              tags_json TEXT,
              quality_score REAL,
              review_status TEXT,
              reviewer_id TEXT,
              reviewed_at TEXT,
              published_at TEXT,
              source TEXT,
              source_id TEXT,
              source_metadata_json TEXT,
              created_at TEXT,
              updated_at TEXT
            );
            CREATE TABLE expression_tool_chains (
              id INTEGER PRIMARY KEY,
              chain_uuid TEXT UNIQUE,
              name TEXT,
              goal TEXT,
              scene TEXT,
              stage TEXT,
              tool_ids_json TEXT,
              sequence_json TEXT,
              forbidden_tools_json TEXT,
              example_dialogue_json TEXT,
              review_status TEXT,
              quality_score REAL,
              created_at TEXT,
              updated_at TEXT
            );
            CREATE TABLE content_import_batches (
              id INTEGER PRIMARY KEY,
              source_name TEXT,
              source_type TEXT,
              imported_sections INTEGER,
              imported_entries INTEGER,
              skipped_entries INTEGER,
              issues_count INTEGER,
              status TEXT,
              report_json TEXT,
              created_at TEXT
            );
            CREATE TABLE resource_library (
              id INTEGER PRIMARY KEY,
              resource_uuid TEXT UNIQUE,
              type TEXT,
              category TEXT,
              title TEXT,
              content TEXT,
              emotional_tone_json TEXT,
              emotional_intensity INTEGER,
              applicable_scene TEXT,
              difficulty_level INTEGER,
              gender_target TEXT,
              attachment_suitability TEXT,
              usage_tip TEXT,
              effectiveness_rating INTEGER,
              source TEXT,
              source_url TEXT,
              tags TEXT,
              created_at TEXT,
              review_status TEXT,
              reviewer_id TEXT,
              reviewed_at TEXT,
              published_at TEXT,
              source_title TEXT,
              source_excerpt TEXT,
              source_summary TEXT,
              source_license TEXT,
              content_fingerprint TEXT,
              quality_score REAL,
              expression_tool_ids_json TEXT,
              expression_goal TEXT,
              expression_level TEXT,
              speech_act TEXT,
              mistake_pattern TEXT,
              recommended_drills_json TEXT,
              case_blueprint_json TEXT,
              variant_signature TEXT,
              content_unit TEXT,
              coverage_axis TEXT,
              variant_family TEXT,
              case_completeness_score REAL
            );
            """
        )
        connection.commit()


def test_safety_alternative_dry_run_does_not_mutate(tmp_path: Path) -> None:
    db_path = tmp_path / "safety.db"
    _create_tables(db_path)

    result = seed(db_path, dry_run=True)
    with sqlite3.connect(db_path) as connection:
        resources = connection.execute("SELECT count(*) FROM resource_library").fetchone()[0]
        entries = connection.execute("SELECT count(*) FROM knowledge_entries").fetchone()[0]

    assert result["dry_run"] is True
    assert result["created_resources"] == len(RISK_CASES) * 3
    assert result["created_entries"] == len(RISK_CASES)
    assert resources == 0
    assert entries == 0


def test_safety_alternative_creates_complete_records_and_is_idempotent(tmp_path: Path) -> None:
    db_path = tmp_path / "safety.db"
    _create_tables(db_path)

    result = seed(db_path)
    second = seed(db_path)
    with sqlite3.connect(db_path) as connection:
        entry_count = connection.execute("SELECT count(*) FROM knowledge_entries WHERE source=?", (SOURCE,)).fetchone()[0]
        chain_count = connection.execute("SELECT count(*) FROM expression_tool_chains WHERE goal='安全替代表达'").fetchone()[0]
        resource_count = connection.execute("SELECT count(*) FROM resource_library WHERE source=?", (SOURCE,)).fetchone()[0]
        raw_blueprint, content, expression_goal = connection.execute(
            "SELECT case_blueprint_json, content, expression_goal FROM resource_library WHERE source=? ORDER BY id LIMIT 1",
            (SOURCE,),
        ).fetchone()
        batch_count = connection.execute("SELECT count(*) FROM content_import_batches WHERE source_name=?", (SOURCE,)).fetchone()[0]

    blueprint = json.loads(raw_blueprint)

    assert result["created_entries"] == len(RISK_CASES)
    assert result["created_chains"] == len(RISK_CASES)
    assert result["created_resources"] == len(RISK_CASES) * 3
    assert second["created_resources"] == 0
    assert second["updated_resources"] == len(RISK_CASES) * 3
    assert entry_count == len(RISK_CASES)
    assert chain_count == len(RISK_CASES)
    assert resource_count == len(RISK_CASES) * 3
    assert expression_goal == "安全替代表达"
    assert blueprint["risk_flag"]
    assert blueprint["better_response"]
    assert "场景：" in content
    assert "TA说：" in content
    assert "高风险请求：" in content
    assert "完整对话：" in content
    assert "常见失误：" in content
    assert "更好回应：" in content
    assert "边界提醒：" in content
    assert "练习任务：" in content
    assert "拿捏" not in content
    assert "让她离不开" not in content
    assert batch_count == 2


def test_safety_alternative_records_pass_case_quality_audit(tmp_path: Path) -> None:
    db_path = tmp_path / "safety.db"
    _create_tables(db_path)
    with sqlite3.connect(db_path) as connection:
        connection.execute(
            """
            CREATE TABLE pipeline_run_logs (
              id INTEGER PRIMARY KEY,
              target_type TEXT,
              target_id INTEGER,
              action TEXT,
              from_status TEXT,
              to_status TEXT,
              result_json TEXT,
              message TEXT,
              created_at TEXT
            )
            """
        )
        connection.commit()

    seed(db_path)
    report = audit_case_quality(db_path, limit=100)

    assert report["summary"]["incomplete"] == 0
    assert report["summary"]["context_mismatch"] == 0
    assert report["summary"]["stereotype_or_manipulation_risk"] == 0
