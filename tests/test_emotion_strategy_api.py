from fastapi.testclient import TestClient
from sqlmodel import Session, select

from backend.database.connection import create_db_and_tables, engine
from backend.database.seed import seed_all
from backend.main import app
from backend.models.resource import ResponseStrategy


def test_emotion_api_filters_and_static_routes():
    create_db_and_tables()
    seed_all()
    client = TestClient(app)

    spectrum = client.get("/api/emotions/spectrum", params={"spectrum": "喜", "intensity": 1})
    assert spectrum.status_code == 200
    data = spectrum.json()
    assert len(data) == 1
    assert data[0]["spectrum"] == "喜"

    all_love = client.get("/api/emotions/spectrum/爱")
    assert all_love.status_code == 200
    assert len(all_love.json()) >= 10

    mixed = client.get("/api/emotions/mixed/纠结")
    assert mixed.status_code == 200
    assert mixed.json()["name"] == "纠结"

    mixed_list = client.get("/api/emotions/mixed")
    assert mixed_list.status_code == 200
    assert len(mixed_list.json()) >= 20

    missing_spectrum = client.get("/api/emotions/spectrum/不存在的谱系")
    assert missing_spectrum.status_code == 200
    assert missing_spectrum.json() == []

    missing = client.get("/api/emotions/mixed/不存在的混合情绪")
    assert missing.status_code == 404

    assert client.get("/api/emotions/spectra-list").json() == ["喜", "怒", "哀", "惧", "爱", "惊", "羞"]


def test_strategy_api_lists_details_and_missing_shape():
    create_db_and_tables()
    seed_all()
    client = TestClient(app)

    strategies = client.get("/api/strategies")
    assert strategies.status_code == 200
    names = {item["name"] for item in strategies.json()}
    assert "共情反射" in names

    detail = client.get("/api/strategies/轻验证")
    assert detail.status_code == 200
    assert detail.json()["examples"]
    assert detail.json()["effectiveness"] >= 8

    missing = client.get("/api/strategies/不存在的策略")
    assert missing.status_code == 200
    assert missing.json() is None


def test_strategy_api_tolerates_invalid_example_json():
    create_db_and_tables()
    unique_name = "pytest坏JSON策略"
    with Session(engine) as session:
        existing = session.exec(select(ResponseStrategy).where(ResponseStrategy.name == unique_name)).first()
        if existing:
            session.delete(existing)
            session.commit()
        session.add(
            ResponseStrategy(
                name=unique_name,
                principle="测试坏 JSON 降级",
                definition="example_json 损坏时应返回空 examples。",
                example_json="not-json",
                applicable_situation="测试",
                effectiveness=5,
            )
        )
        session.commit()

    client = TestClient(app)
    detail = client.get(f"/api/strategies/{unique_name}")

    assert detail.status_code == 200
    assert detail.json()["examples"] == []
    assert detail.json()["principle"] == "测试坏 JSON 降级"

    with Session(engine) as session:
        created = session.exec(select(ResponseStrategy).where(ResponseStrategy.name == unique_name)).first()
        if created:
            session.delete(created)
            session.commit()
