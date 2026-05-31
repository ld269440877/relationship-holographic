import json
import sqlite3
from pathlib import Path

from backend.database.riddle_interaction_seed import SOURCE, seed


def _create_tables(db_path: Path) -> None:
    with sqlite3.connect(db_path) as connection:
        connection.executescript(
            """
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


def test_riddle_seed_dry_run_does_not_mutate(tmp_path: Path) -> None:
    db_path = tmp_path / "riddles.db"
    _create_tables(db_path)

    result = seed(db_path, dry_run=True)
    with sqlite3.connect(db_path) as connection:
        total = connection.execute("SELECT count(*) FROM resource_library").fetchone()[0]

    assert result["dry_run"] is True
    assert result["created_resources"] == 144
    assert total == 0


def test_riddle_seed_creates_complete_cards(tmp_path: Path) -> None:
    db_path = tmp_path / "riddles.db"
    _create_tables(db_path)

    result = seed(db_path)
    with sqlite3.connect(db_path) as connection:
        total, distinct_units = connection.execute(
            "SELECT count(*), count(distinct content_unit) FROM resource_library WHERE source = ?",
            (SOURCE,),
        ).fetchone()
        raw, content = connection.execute(
            "SELECT case_blueprint_json, content FROM resource_library WHERE source = ? ORDER BY id LIMIT 1",
            (SOURCE,),
        ).fetchone()

    blueprint = json.loads(raw)

    assert result["created_resources"] == 144
    assert total == 144
    assert distinct_units == 144
    assert blueprint["version"] == "riddle_interaction_seed_v1"
    assert blueprint["resource_type"] == "riddle"
    assert blueprint["riddle"]
    assert blueprint["answer"]
    assert len(blueprint["dialogue_script"]) >= 4
    assert "完整对话：" in content
    assert "边界提醒：" in content


def test_riddle_seed_is_idempotent(tmp_path: Path) -> None:
    db_path = tmp_path / "riddles.db"
    _create_tables(db_path)

    seed(db_path)
    second = seed(db_path)
    with sqlite3.connect(db_path) as connection:
        total, distinct_units = connection.execute(
            "SELECT count(*), count(distinct content_unit) FROM resource_library WHERE source = ?",
            (SOURCE,),
        ).fetchone()

    assert second["created_resources"] == 0
    assert second["skipped_resources"] == 144
    assert second["updated_resources"] == 144
    assert total == 144
    assert distinct_units == 144
