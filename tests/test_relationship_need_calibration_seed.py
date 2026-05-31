import json
import sqlite3
from pathlib import Path

from fastapi.testclient import TestClient
from sqlmodel import Session, create_engine

from backend.database.connection import get_session
from backend.database.relationship_need_calibration_seed import SOURCE, TOOL_UUID, seed
from backend.main import app
from tests.test_self_disclosure_intimacy_seed import _create_tables


def test_relationship_need_calibration_seed_creates_complete_records(tmp_path: Path) -> None:
    db_path = tmp_path / "relationship_need.db"
    _create_tables(db_path)

    result = seed(db_path)

    with sqlite3.connect(db_path) as connection:
        entry_count = connection.execute("SELECT count(*) FROM knowledge_entries WHERE source=?", (SOURCE,)).fetchone()[0]
        tool_blueprint = connection.execute(
            "SELECT learning_blueprint_json FROM expression_tools WHERE tool_uuid=?",
            (TOOL_UUID,),
        ).fetchone()
        resource = connection.execute(
            "SELECT case_blueprint_json, content FROM resource_library WHERE source=? ORDER BY id LIMIT 1",
            (SOURCE,),
        ).fetchone()

    blueprint = json.loads(tool_blueprint[0])
    case_blueprint = json.loads(resource[0])

    assert result["created_entries"] == 2
    assert result["created_tools"] == 1
    assert result["created_chains"] == 1
    assert result["created_resources"] == 15
    assert entry_count == 2
    assert blueprint["forbidden_labels"][0]["rewrite"]
    assert case_blueprint["axis"] == "relationship_need_calibration"
    assert "去偏提醒：" in resource[1]
    assert "女人都这样" not in resource[1]


def test_relationship_need_resources_are_available_by_mission_axis(tmp_path: Path) -> None:
    db_path = tmp_path / "relationship_need.db"
    _create_tables(db_path)
    seed(db_path)

    test_engine = create_engine(f"sqlite:///{db_path}", connect_args={"check_same_thread": False})

    def override_session():
        with Session(test_engine) as session:
            yield session

    app.dependency_overrides[get_session] = override_session
    try:
        client = TestClient(app)
        response = client.get("/api/resources", params={"mission_axis": "relationship_need_calibration", "limit": 20})
    finally:
        app.dependency_overrides.clear()

    data = response.json()
    titles = [item["title"] for item in data["items"]]
    assert response.status_code == 200
    assert data["total"] == 15
    assert any("情绪承接" in title for title in titles)
    assert all(item["coverage_axis"] == "relationship_need_calibration" for item in data["items"])
