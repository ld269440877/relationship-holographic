import sqlite3
from pathlib import Path

from backend.database.worldclass_target_completion import SOURCE, TARGETS, complete_targets


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
            CREATE TABLE interaction_samples (
              id INTEGER PRIMARY KEY,
              scenario_category TEXT,
              principle_ref TEXT,
              tension_dimensions_json TEXT,
              source_trace_json TEXT,
              quality_json TEXT,
              gold_label_json TEXT,
              is_gold_sample INTEGER,
              review_status TEXT,
              annotation_version TEXT,
              updated_at TEXT
            );
            CREATE TABLE sample_annotation_versions (
              id INTEGER PRIMARY KEY,
              sample_id INTEGER,
              version TEXT,
              annotator_type TEXT,
              schema_version TEXT,
              tension_dimensions_json TEXT,
              source_trace_json TEXT,
              quality_json TEXT,
              safety_json TEXT,
              gold_label_json TEXT,
              review_status TEXT,
              is_gold INTEGER,
              created_at TEXT
            );
            """
        )
        for index in range(400):
            connection.execute(
                """
                INSERT INTO interaction_samples (
                  id, scenario_category, principle_ref, tension_dimensions_json, source_trace_json,
                  quality_json, is_gold_sample, review_status, annotation_version
                )
                VALUES (?, '暧昧', '低压力期待', '{}', '{}', '{}', 0, 'reviewed', 'test')
                """,
                (index + 1,),
            )
        connection.commit()


def test_target_completion_reaches_thresholds_and_is_idempotent(tmp_path: Path) -> None:
    db_path = tmp_path / "targets.db"
    _create_tables(db_path)

    result = complete_targets(db_path)
    second = complete_targets(db_path)

    with sqlite3.connect(db_path) as connection:
        knowledge = connection.execute("SELECT count(*) FROM knowledge_entries").fetchone()[0]
        emotions = connection.execute("SELECT count(*) FROM emotion_spectrum").fetchone()[0]
        mixed = connection.execute("SELECT count(*) FROM mixed_emotions").fetchone()[0]
        chains = connection.execute("SELECT count(*) FROM expression_tool_chains").fetchone()[0]
        gold = connection.execute("SELECT count(*) FROM interaction_samples WHERE gold_label_json IS NOT NULL").fetchone()[0]
        versions = connection.execute("SELECT count(*) FROM sample_annotation_versions").fetchone()[0]
        batches = connection.execute("SELECT count(*) FROM content_import_batches WHERE source_name=?", (SOURCE,)).fetchone()[0]

    assert result["knowledge_created"] == TARGETS["knowledge_entries"]
    assert result["emotions_created"] == TARGETS["emotion_spectrum"]
    assert result["mixed_emotions_created"] == TARGETS["mixed_emotions"]
    assert result["chains_created"] == TARGETS["expression_tool_chains"]
    assert result["gold_promoted"] == 300
    assert second["knowledge_created"] == 0
    assert second["emotions_created"] == 0
    assert second["mixed_emotions_created"] == 0
    assert second["chains_created"] == 0
    assert second["gold_promoted"] == 0
    assert knowledge == TARGETS["knowledge_entries"]
    assert emotions == TARGETS["emotion_spectrum"]
    assert mixed == TARGETS["mixed_emotions"]
    assert chains == TARGETS["expression_tool_chains"]
    assert gold == 300
    assert versions == 300
    assert batches == 2
