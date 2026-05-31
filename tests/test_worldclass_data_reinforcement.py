import json
import sqlite3
from pathlib import Path

from backend.database.worldclass_data_reinforcement import SOURCE, VERSION, reinforce_database


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
            CREATE TABLE interaction_samples (
              id INTEGER PRIMARY KEY,
              sample_uuid TEXT UNIQUE,
              scenario_category TEXT,
              difficulty_level INTEGER,
              context TEXT,
              their_words TEXT,
              their_behavior TEXT,
              emotion_tags_json TEXT,
              hidden_need TEXT,
              need_urgency INTEGER,
              attachment_signal TEXT,
              boundary_test_level INTEGER,
              bad_response TEXT,
              bad_response_reason TEXT,
              good_response_soft TEXT,
              good_response_tension TEXT,
              good_response_humor TEXT,
              principle_ref TEXT,
              source TEXT,
              source_url TEXT,
              five_w_two_h_json TEXT,
              signal_highlights_json TEXT,
              emotion_flow_json TEXT,
              feeling_tags_json TEXT,
              need_radar_json TEXT,
              boundary_state_json TEXT,
              source_trace_json TEXT,
              quality_json TEXT,
              tension_dimensions_json TEXT,
              gold_label_json TEXT,
              review_status TEXT,
              is_gold_sample INTEGER,
              annotation_version TEXT,
              created_at TEXT,
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
              applicable_scene TEXT,
              speech_act TEXT,
              expression_goal TEXT,
              difficulty_level
            );
            INSERT INTO interaction_samples (
              id, sample_uuid, scenario_category, difficulty_level, context, their_words,
              emotion_tags_json, boundary_test_level, bad_response, good_response_soft,
              review_status, is_gold_sample, annotation_version
            )
            VALUES (
              7, 'sample-7', '伴侣冲突', 3, '对方临时取消约会，你感到不被重视。',
              '我今天真的太累了，不想去了。', '[{"word":"失落","intensity":6}]',
              6, '你每次都这样。', '我会有点失落，也想先知道你现在最需要什么。',
              'draft', 0, 'legacy-v0'
            );
            INSERT INTO resource_library (
              id, applicable_scene, speech_act, expression_goal, difficulty_level
            )
            VALUES (
              1, '伴侣冲突', '先描述你看见的具体事实，不急着判断对方动机', '帮助用户在高压冲突中先把事实和情绪拆开再修复信任', '高级'
            );
            """
        )
        connection.commit()


def test_reinforcement_dry_run_does_not_mutate(tmp_path: Path) -> None:
    db_path = tmp_path / "worldclass.db"
    _create_tables(db_path)

    result = reinforce_database(db_path, dry_run=True, sample_limit=10)
    with sqlite3.connect(db_path) as connection:
        sample_row = connection.execute(
            "SELECT five_w_two_h_json, annotation_version FROM interaction_samples WHERE id=7"
        ).fetchone()
        batch_count = connection.execute("SELECT count(*) FROM content_import_batches").fetchone()[0]

    assert result["dry_run"] is True
    assert result["samples_updated"] == 1
    assert sample_row == (None, "legacy-v0")
    assert batch_count == 0


def test_reinforcement_fills_core_dimensions_and_is_idempotent(tmp_path: Path) -> None:
    db_path = tmp_path / "worldclass.db"
    _create_tables(db_path)

    result = reinforce_database(db_path, sample_limit=10)
    second = reinforce_database(db_path, sample_limit=10)

    with sqlite3.connect(db_path) as connection:
        connection.row_factory = sqlite3.Row
        sample = connection.execute("SELECT * FROM interaction_samples WHERE id=7").fetchone()
        annotation_count = connection.execute("SELECT count(*) FROM sample_annotation_versions").fetchone()[0]
        knowledge_count = connection.execute("SELECT count(*) FROM knowledge_entries WHERE source=?", (SOURCE,)).fetchone()[0]
        emotion_count = connection.execute("SELECT count(*) FROM emotion_spectrum").fetchone()[0]
        chain_count = connection.execute("SELECT count(*) FROM expression_tool_chains").fetchone()[0]
        resource = connection.execute("SELECT applicable_scene, speech_act, expression_goal, difficulty_level FROM resource_library").fetchone()
        batch_count = connection.execute("SELECT count(*) FROM content_import_batches WHERE source_name=?", (SOURCE,)).fetchone()[0]

    flow = json.loads(sample["emotion_flow_json"])
    radar = json.loads(sample["need_radar_json"])
    gold = json.loads(sample["gold_label_json"])

    assert result["samples_updated"] == 1
    assert result["gold_promoted"] == 1
    assert second["samples_updated"] == 0
    assert sample["scenario_category"] == "冲突"
    assert sample["annotation_version"] == VERSION
    assert flow["turning_point"]
    assert radar["repair"] >= 8
    assert gold["decision"] == "gold_scaffold"
    assert annotation_count == 1
    assert knowledge_count == 12
    assert emotion_count == 25
    assert chain_count == 5
    assert tuple(resource) == ("冲突", "事实观察", "修复信任", 2)
    assert batch_count == 2
