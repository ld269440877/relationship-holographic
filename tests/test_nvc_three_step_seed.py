import json
import sqlite3
from pathlib import Path

from backend.database.nvc_three_step_seed import SOURCE, TOOL_UUID, seed


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
            CREATE TABLE expression_tools (
              id INTEGER PRIMARY KEY,
              tool_uuid TEXT UNIQUE,
              name TEXT,
              layer TEXT,
              category TEXT,
              formula TEXT,
              description TEXT,
              best_scenes_json TEXT,
              relationship_fit_json TEXT,
              emotion_fit_json TEXT,
              risk_flags_json TEXT,
              micro_steps_json TEXT,
              learning_blueprint_json TEXT,
              example_before TEXT,
              example_after TEXT,
              mastery_stage TEXT,
              source TEXT,
              source_url TEXT,
              review_status TEXT,
              quality_score REAL,
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


def test_nvc_three_step_dry_run_does_not_mutate(tmp_path: Path) -> None:
    db_path = tmp_path / "nvc.db"
    _create_tables(db_path)

    result = seed(db_path, dry_run=True)
    with sqlite3.connect(db_path) as connection:
        resources = connection.execute("SELECT count(*) FROM resource_library").fetchone()[0]
        tools = connection.execute("SELECT count(*) FROM expression_tools").fetchone()[0]

    assert result["dry_run"] is True
    assert result["created_resources"] == 18
    assert resources == 0
    assert tools == 0


def test_nvc_three_step_creates_complete_learning_records(tmp_path: Path) -> None:
    db_path = tmp_path / "nvc.db"
    _create_tables(db_path)

    result = seed(db_path)
    with sqlite3.connect(db_path) as connection:
        section_count = connection.execute("SELECT count(*) FROM knowledge_sections").fetchone()[0]
        entry_count = connection.execute("SELECT count(*) FROM knowledge_entries").fetchone()[0]
        tool_row = connection.execute(
            "SELECT learning_blueprint_json FROM expression_tools WHERE tool_uuid = ?",
            (TOOL_UUID,),
        ).fetchone()
        resource_row = connection.execute(
            "SELECT case_blueprint_json, content FROM resource_library WHERE source = ? ORDER BY id LIMIT 1",
            (SOURCE,),
        ).fetchone()

    tool_blueprint = json.loads(tool_row[0])
    case_blueprint = json.loads(resource_row[0])

    assert result["created_sections"] == 1
    assert result["created_entries"] == 1
    assert result["created_tools"] == 1
    assert result["created_chains"] == 1
    assert result["created_resources"] == 18
    assert section_count == 1
    assert entry_count == 1
    assert "非暴力沟通三步法" in tool_blueprint["concept"]
    assert case_blueprint["method"] == "非暴力沟通三步法"
    assert len(case_blueprint["dialogue_script"]) >= 4
    assert "我的期待" in resource_row[1]
    assert "你的选择" in resource_row[1]
    assert "完整对话：" in resource_row[1]


def test_nvc_three_step_is_idempotent(tmp_path: Path) -> None:
    db_path = tmp_path / "nvc.db"
    _create_tables(db_path)

    seed(db_path)
    second = seed(db_path)
    with sqlite3.connect(db_path) as connection:
        total, distinct_units = connection.execute(
            "SELECT count(*), count(distinct content_unit) FROM resource_library WHERE source = ?",
            (SOURCE,),
        ).fetchone()

    assert second["created_resources"] == 0
    assert second["skipped_resources"] == 18
    assert total == 18
    assert distinct_units == 18
