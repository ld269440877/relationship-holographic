import json
import sqlite3
from pathlib import Path

from backend.database.source_surf_expansion_seed import SOURCE_POLICY, TRAJECTORY_PHRASE, seed


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
              last_checked_at TEXT,
              created_at TEXT
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
            """
        )
        connection.commit()


def test_source_surf_seed_dry_run_does_not_mutate(tmp_path: Path) -> None:
    db_path = tmp_path / "surf.db"
    _create_tables(db_path)

    result = seed(db_path, dry_run=True)
    with sqlite3.connect(db_path) as connection:
        source_count = connection.execute("SELECT count(*) FROM source_registry").fetchone()[0]
        resource_count = connection.execute("SELECT count(*) FROM resource_library").fetchone()[0]

    assert result["dry_run"] is True
    assert result["created_sources"] >= 20
    assert source_count == 0
    assert resource_count == 0


def test_source_surf_seed_creates_metadata_anchors_and_trajectory(tmp_path: Path) -> None:
    db_path = tmp_path / "surf.db"
    _create_tables(db_path)

    result = seed(db_path)
    with sqlite3.connect(db_path) as connection:
        source_count = connection.execute("SELECT count(*) FROM source_registry").fetchone()[0]
        raw_count = connection.execute("SELECT count(*) FROM raw_content_items").fetchone()[0]
        resource_count = connection.execute("SELECT count(*) FROM resource_library").fetchone()[0]
        entry = connection.execute("SELECT title, content FROM knowledge_entries LIMIT 1").fetchone()
        source = connection.execute("SELECT allowed_use_json FROM source_registry ORDER BY id LIMIT 1").fetchone()
        resource = connection.execute(
            "SELECT source_license, case_blueprint_json, content FROM resource_library ORDER BY id LIMIT 1"
        ).fetchone()

    allowed = json.loads(source[0])
    blueprint = json.loads(resource[1])

    assert result["created_sources"] == source_count
    assert raw_count == source_count
    assert resource_count == source_count
    assert entry[0] == TRAJECTORY_PHRASE
    assert TRAJECTORY_PHRASE in entry[1]
    assert allowed["source_policy"] == SOURCE_POLICY
    assert allowed["surf_metadata"]["themes"]
    assert resource[0] == SOURCE_POLICY
    assert blueprint["source_mapping"]["copyright_boundary"] == "no_third_party_full_text"
    assert "转化路径：" in resource[2]


def test_source_surf_seed_is_idempotent_and_updates(tmp_path: Path) -> None:
    db_path = tmp_path / "surf.db"
    _create_tables(db_path)

    first = seed(db_path)
    second = seed(db_path)
    with sqlite3.connect(db_path) as connection:
        source_count = connection.execute("SELECT count(*) FROM source_registry").fetchone()[0]
        resource_count = connection.execute("SELECT count(*) FROM resource_library").fetchone()[0]
        entry_count = connection.execute("SELECT count(*) FROM knowledge_entries").fetchone()[0]

    assert first["created_sources"] >= 20
    assert second["created_sources"] == 0
    assert second["updated_sources"] == source_count
    assert second["updated_resource_anchors"] == resource_count
    assert entry_count == 1
