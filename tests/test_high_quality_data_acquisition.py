import json
import sqlite3
from pathlib import Path

from backend.database.high_quality_data_acquisition import run_acquisition


def _create_tables(db_path: Path) -> None:
    with sqlite3.connect(db_path) as connection:
        connection.executescript(
            """
            CREATE TABLE source_registry (
              id INTEGER PRIMARY KEY,
              source_uuid TEXT UNIQUE,
              name TEXT,
              source_type TEXT,
              url TEXT,
              trust_score REAL,
              update_frequency TEXT,
              allowed_use_json TEXT,
              disallowed_use_json TEXT,
              active INTEGER,
              created_at TEXT,
              last_checked_at TEXT
            );
            CREATE TABLE raw_content_items (
              id INTEGER PRIMARY KEY,
              raw_uuid TEXT UNIQUE,
              source_id INTEGER,
              title TEXT,
              url TEXT,
              content_hash TEXT,
              raw_storage_policy TEXT,
              privacy_risk REAL,
              copyright_risk REAL,
              consent_status TEXT,
              processing_status TEXT,
              collected_at TEXT
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
            CREATE TABLE expression_tools (
              id INTEGER PRIMARY KEY,
              tool_uuid TEXT,
              name TEXT,
              layer TEXT,
              category TEXT,
              formula TEXT,
              best_scenes_json TEXT,
              review_status TEXT,
              quality_score REAL
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
        connection.execute(
            """
            INSERT INTO expression_tools (
              tool_uuid, name, layer, category, formula, best_scenes_json, review_status, quality_score
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            ("expr_tool_test", "现实感受交替", "emotion", "深聊", "事实 -> 感受 -> 边界", "[]", "published", 95),
        )
        connection.commit()


def test_run_acquisition_dry_run_does_not_mutate(tmp_path: Path) -> None:
    db_path = tmp_path / "acq.db"
    _create_tables(db_path)

    result = run_acquisition(db_path, target_new=5, dry_run=True)
    with sqlite3.connect(db_path) as connection:
        resource_count = connection.execute("SELECT count(*) FROM resource_library").fetchone()[0]
        source_count = connection.execute("SELECT count(*) FROM source_registry").fetchone()[0]

    assert result["dry_run"] is True
    assert result["created_resources"] == 5
    assert resource_count == 0
    assert source_count == 0


def test_run_acquisition_creates_complete_records(tmp_path: Path) -> None:
    db_path = tmp_path / "acq.db"
    _create_tables(db_path)

    result = run_acquisition(db_path, target_new=6)
    with sqlite3.connect(db_path) as connection:
        resource_count = connection.execute("SELECT count(*) FROM resource_library").fetchone()[0]
        source_count = connection.execute("SELECT count(*) FROM source_registry").fetchone()[0]
        raw_count = connection.execute("SELECT count(*) FROM raw_content_items").fetchone()[0]
        batch_count = connection.execute("SELECT count(*) FROM content_import_batches").fetchone()[0]
        row = connection.execute(
            "SELECT source_license, case_blueprint_json, content FROM resource_library ORDER BY id LIMIT 1"
        ).fetchone()

    blueprint = json.loads(row[1])

    assert result["created_resources"] == 6
    assert resource_count == 6
    assert source_count >= 1
    assert raw_count >= 1
    assert batch_count == 1
    assert row[0] == "link_title_summary_short_excerpt_structured_analysis_local_original_rewrite_only"
    assert blueprint["source_mapping"]["copyright_boundary"] == "no_third_party_full_text"
    assert len(blueprint["dialogue_script"]) >= 6
    assert blueprint["better_response"]
    assert "完整对话：" in row[2]


def test_run_acquisition_is_idempotent_by_content_unit(tmp_path: Path) -> None:
    db_path = tmp_path / "acq.db"
    _create_tables(db_path)

    first = run_acquisition(db_path, target_new=6)
    second = run_acquisition(db_path, target_new=6)
    with sqlite3.connect(db_path) as connection:
        total, distinct_units = connection.execute(
            """
            SELECT count(*), count(distinct content_unit)
            FROM resource_library
            WHERE source = 'project_original:high_quality_acquisition_v1'
            """
        ).fetchone()

    assert first["created_resources"] == 6
    assert second["skipped_resources"] >= 6
    assert total == distinct_units
