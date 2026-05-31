import json
import sqlite3
from pathlib import Path

from fastapi.testclient import TestClient
from sqlmodel import Session, create_engine

from backend.database.connection import get_session
from backend.database.self_disclosure_intimacy_seed import SOURCE, TOOL_UUID, seed
from backend.main import app


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


def test_self_disclosure_dry_run_does_not_mutate(tmp_path: Path) -> None:
    db_path = tmp_path / "self_disclosure.db"
    _create_tables(db_path)

    result = seed(db_path, dry_run=True)
    with sqlite3.connect(db_path) as connection:
        resources = connection.execute("SELECT count(*) FROM resource_library").fetchone()[0]
        tools = connection.execute("SELECT count(*) FROM expression_tools").fetchone()[0]

    assert result["dry_run"] is True
    assert result["created_entries"] == 3
    assert result["created_resources"] == 12
    assert resources == 0
    assert tools == 0


def test_self_disclosure_creates_complete_records(tmp_path: Path) -> None:
    db_path = tmp_path / "self_disclosure.db"
    _create_tables(db_path)

    result = seed(db_path)
    with sqlite3.connect(db_path) as connection:
        entry_count = connection.execute("SELECT count(*) FROM knowledge_entries WHERE source=?", (SOURCE,)).fetchone()[0]
        tool = connection.execute(
            "SELECT learning_blueprint_json FROM expression_tools WHERE tool_uuid=?",
            (TOOL_UUID,),
        ).fetchone()
        chain = connection.execute("SELECT sequence_json FROM expression_tool_chains LIMIT 1").fetchone()
        resource = connection.execute(
            "SELECT case_blueprint_json, content FROM resource_library WHERE source=? ORDER BY id LIMIT 1",
            (SOURCE,),
        ).fetchone()

    tool_blueprint = json.loads(tool[0])
    sequence = json.loads(chain[0])
    case_blueprint = json.loads(resource[0])

    assert result["created_sections"] == 1
    assert result["created_entries"] == 3
    assert result["created_tools"] == 1
    assert result["created_chains"] == 1
    assert result["created_resources"] == 12
    assert entry_count == 3
    assert tool_blueprint["depth_levels"][0]["level"] == "D1 事实层"
    assert sequence[0]["tool"] == "自我表露深度校准"
    assert case_blueprint["axis"] == "self_disclosure_depth"
    assert len(case_blueprint["dialogue_script"]) >= 4
    assert "风险矩阵：" in resource[1]
    assert "完整对话：" in resource[1]


def test_self_disclosure_seed_is_idempotent(tmp_path: Path) -> None:
    db_path = tmp_path / "self_disclosure.db"
    _create_tables(db_path)

    seed(db_path)
    second = seed(db_path)
    with sqlite3.connect(db_path) as connection:
        total, distinct_units = connection.execute(
            "SELECT count(*), count(distinct content_unit) FROM resource_library WHERE source=?",
            (SOURCE,),
        ).fetchone()

    assert second["created_resources"] == 0
    assert second["skipped_resources"] == 12
    assert total == 12
    assert distinct_units == 12


def test_self_disclosure_resources_are_available_by_mission_axis(tmp_path: Path) -> None:
    db_path = tmp_path / "self_disclosure.db"
    _create_tables(db_path)
    seed(db_path)

    test_engine = create_engine(f"sqlite:///{db_path}", connect_args={"check_same_thread": False})

    def override_session():
        with Session(test_engine) as session:
            yield session

    app.dependency_overrides[get_session] = override_session
    try:
        client = TestClient(app)
        response = client.get("/api/resources", params={"mission_axis": "self_disclosure_depth", "limit": 20})
    finally:
        app.dependency_overrides.clear()

    data = response.json()
    titles = [item["title"] for item in data["items"]]
    assert response.status_code == 200
    assert data["total"] == 12
    assert any("初识节奏" in title for title in titles)
    assert all(item["coverage_axis"] == "self_disclosure_depth" for item in data["items"])
