import json
import sqlite3
from pathlib import Path

from backend.database.deep_emotional_connection_seed import SOURCE, seed


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


def test_deep_emotional_connection_dry_run_does_not_mutate(tmp_path: Path) -> None:
    db_path = tmp_path / "mirror.db"
    _create_tables(db_path)

    result = seed(db_path, dry_run=True)
    with sqlite3.connect(db_path) as connection:
        resources = connection.execute("SELECT count(*) FROM resource_library").fetchone()[0]
        entries = connection.execute("SELECT count(*) FROM knowledge_entries").fetchone()[0]

    assert result["dry_run"] is True
    assert result["created_resources"] == 15
    assert resources == 0
    assert entries == 0


def test_deep_emotional_connection_creates_complete_records(tmp_path: Path) -> None:
    db_path = tmp_path / "mirror.db"
    _create_tables(db_path)

    result = seed(db_path)
    with sqlite3.connect(db_path) as connection:
        chain = connection.execute("SELECT sequence_json FROM expression_tool_chains LIMIT 1").fetchone()
        entry = connection.execute("SELECT content, source_metadata_json FROM knowledge_entries LIMIT 1").fetchone()
        resource = connection.execute(
            "SELECT case_blueprint_json, content FROM resource_library WHERE source=? ORDER BY id LIMIT 1",
            (SOURCE,),
        ).fetchone()

    sequence = json.loads(chain[0])
    metadata = json.loads(entry[1])
    blueprint = json.loads(resource[0])

    assert result["created_entries"] == 1
    assert result["created_chains"] == 1
    assert result["created_resources"] == 15
    assert sequence[0]["tool"] == "开放式提问"
    assert metadata["steps"][3]["name"] == "镜子校准"
    assert "事实层" in entry[0]
    assert blueprint["keyword"]
    assert blueprint["fact_layer"]
    assert blueprint["emotion_layer"]
    assert len(blueprint["dialogue_script"]) >= 5
    assert "完整对话：" in resource[1]
    assert "四步拆解：" in resource[1]


def test_deep_emotional_connection_is_idempotent(tmp_path: Path) -> None:
    db_path = tmp_path / "mirror.db"
    _create_tables(db_path)

    seed(db_path)
    second = seed(db_path)
    with sqlite3.connect(db_path) as connection:
        total, distinct_units = connection.execute(
            "SELECT count(*), count(distinct content_unit) FROM resource_library WHERE source=?",
            (SOURCE,),
        ).fetchone()

    assert second["created_resources"] == 0
    assert second["skipped_resources"] == 15
    assert total == 15
    assert distinct_units == 15
