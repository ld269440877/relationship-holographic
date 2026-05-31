import sqlite3
from pathlib import Path

from backend.database.worldclass_material_matrix_expansion import SOURCE, expand_database


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
            CREATE TABLE emotion_spectrum (
              id INTEGER PRIMARY KEY,
              spectrum TEXT,
              intensity INTEGER,
              word TEXT,
              behavioral_anchor TEXT,
              physiological_signal TEXT,
              microexpression_desc TEXT,
              example_sentence TEXT
            );
            CREATE TABLE mixed_emotions (
              id INTEGER PRIMARY KEY,
              name TEXT,
              component1_spectrum TEXT,
              component1_word TEXT,
              component1_intensity INTEGER,
              component2_spectrum TEXT,
              component2_word TEXT,
              component2_intensity INTEGER,
              typical_scenario TEXT,
              response_principle TEXT
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
            CREATE TABLE resource_library (
              id INTEGER PRIMARY KEY,
              applicable_scene TEXT
            );
            INSERT INTO knowledge_entries (
              entry_uuid, section_id, title, content, summary, category, quality_score, review_status,
              source, created_at, updated_at
            )
            VALUES (
              'placeholder-1', 0, '低分知识 abc', '只有简短说明。', '简短说明。', '沟通', 70, 'draft',
              'legacy', '2026-05-30', '2026-05-30'
            );
            INSERT INTO resource_library (id, applicable_scene) VALUES (1, '冲突后破冰'), (2, '异地恋');
            """
        )
        connection.commit()


def test_material_matrix_dry_run_does_not_mutate(tmp_path: Path) -> None:
    db_path = tmp_path / "materials.db"
    _create_tables(db_path)

    result = expand_database(db_path, dry_run=True)
    with sqlite3.connect(db_path) as connection:
        title = connection.execute("SELECT title FROM knowledge_entries WHERE entry_uuid='placeholder-1'").fetchone()[0]
        batch_count = connection.execute("SELECT count(*) FROM content_import_batches").fetchone()[0]

    assert result["dry_run"] is True
    assert result["knowledge_created"] == 38
    assert result["placeholder_repaired"] == 1
    assert title == "低分知识 abc"
    assert batch_count == 0


def test_material_matrix_expands_core_tables_and_is_idempotent(tmp_path: Path) -> None:
    db_path = tmp_path / "materials.db"
    _create_tables(db_path)

    result = expand_database(db_path)
    second = expand_database(db_path)
    with sqlite3.connect(db_path) as connection:
        repaired = connection.execute("SELECT title, review_status, source FROM knowledge_entries WHERE entry_uuid='placeholder-1'").fetchone()
        knowledge_count = connection.execute("SELECT count(*) FROM knowledge_entries WHERE source=?", (SOURCE,)).fetchone()[0]
        emotion_count = connection.execute("SELECT count(*) FROM emotion_spectrum").fetchone()[0]
        mixed_count = connection.execute("SELECT count(*) FROM mixed_emotions").fetchone()[0]
        chain_count = connection.execute("SELECT count(*) FROM expression_tool_chains").fetchone()[0]
        scenes = [row[0] for row in connection.execute("SELECT applicable_scene FROM resource_library ORDER BY id").fetchall()]
        batch_count = connection.execute("SELECT count(*) FROM content_import_batches WHERE source_name=?", (SOURCE,)).fetchone()[0]

    assert result["knowledge_created"] == 38
    assert result["placeholder_repaired"] == 1
    assert second["knowledge_created"] == 0
    assert second["placeholder_repaired"] == 0
    assert repaired == ("关系信号最低可用分析模板", "published", SOURCE)
    assert knowledge_count == 39
    assert emotion_count == 42
    assert mixed_count == 10
    assert chain_count == 10
    assert scenes == ["修复", "异地"]
    assert batch_count == 2
