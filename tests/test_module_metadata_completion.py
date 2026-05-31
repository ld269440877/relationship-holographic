import json
import sqlite3
from pathlib import Path

from backend.database.module_metadata_completion import complete_database


def _create_resource_table(db_path: Path) -> None:
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
            INSERT INTO resource_library (
              resource_uuid, type, category, title, content, applicable_scene,
              tags, created_at, review_status, quality_score, recommended_drills_json,
              expression_tool_ids_json, expression_goal
            )
            VALUES (
              'legacy-1', 'joke', '破冰', '经典开场',
              'TA说：我不太会聊天。\\n常见失误：你太慢热了。\\n更好回应：没关系，我们慢慢来。',
              '', '', '2026-05-24T00:00:00',
              'published', 80, '[]', '[]', ''
            );
            """
        )
        connection.commit()


def test_module_metadata_completion_dry_run_does_not_mutate(tmp_path: Path) -> None:
    db_path = tmp_path / "metadata.db"
    _create_resource_table(db_path)

    result = complete_database(db_path, dry_run=True)
    with sqlite3.connect(db_path) as connection:
        row = connection.execute(
            "SELECT source, case_blueprint_json, applicable_scene, tags, expression_tool_ids_json, expression_goal FROM resource_library WHERE resource_uuid='legacy-1'"
        ).fetchone()

    assert result["dry_run"] is True
    assert result["updated"] == 1
    assert row == (None, None, "", "", "[]", "")


def test_module_metadata_completion_fills_learning_fields(tmp_path: Path) -> None:
    db_path = tmp_path / "metadata.db"
    _create_resource_table(db_path)

    result = complete_database(db_path)
    with sqlite3.connect(db_path) as connection:
        row = connection.execute(
            """
            SELECT source, source_url, source_title, source_summary, source_license,
                   case_blueprint_json, content_unit, coverage_axis, variant_family,
                   case_completeness_score, applicable_scene, tags, expression_tool_ids_json,
                   expression_goal
            FROM resource_library
            WHERE resource_uuid='legacy-1'
            """
        ).fetchone()
        batch_count = connection.execute("SELECT count(*) FROM content_import_batches").fetchone()[0]

    blueprint = json.loads(row[5])

    assert result["updated"] == 1
    assert row[0] == "project_original:legacy_metadata_completion_v1"
    assert row[1] == "local_anchor:legacy_resource_metadata_completion"
    assert "本地资源补全" in row[2]
    assert row[3]
    assert row[4] == "project_original_metadata_completion_no_third_party_full_text"
    assert blueprint["their_words"] == "我不太会聊天。"
    assert blueprint["dialogue_script"]
    assert row[6]
    assert row[7] == "micro_signal"
    assert row[8]
    assert row[9] == 92
    assert row[10] == "初识"
    assert "具体案例" in row[11]
    assert json.loads(row[12])
    assert row[13]
    assert batch_count == 1
