from fastapi.testclient import TestClient
from sqlmodel import Session, select

from backend.database.connection import create_db_and_tables, engine
from backend.database.expression_seed import seed_expression_tools
from backend.main import app
from backend.models.expression import ExpressionTool, ExpressionToolChain

client = TestClient(app)


def test_expression_seed_is_idempotent_and_structured():
    create_db_and_tables()
    with Session(engine) as session:
        first = seed_expression_tools(session)
        second = seed_expression_tools(session)
        tools = session.exec(select(ExpressionTool)).all()
        chains = session.exec(select(ExpressionToolChain)).all()

    assert first["total_tools"] >= 60
    assert second["created"] == 0
    assert second["updated"] >= 60
    assert len(tools) >= 60
    assert len(chains) >= 5
    assert {tool.layer for tool in tools} >= {"logic", "ammo", "structure", "nonverbal", "emotion", "relationship"}
    assert all(tool.risk_flags_json for tool in tools)
    assert all(tool.example_after for tool in tools)


def test_expression_routes_list_detail_and_recommend():
    create_db_and_tables()

    seed = client.post("/api/expression/seed")
    tools = client.get("/api/expression/tools?layer=emotion&limit=20")
    scene_search = client.get("/api/expression/tools?q=冲突&limit=20")
    step_search = client.get("/api/expression/tools?q=退路&limit=20")
    detail = client.get("/api/expression/tools/expr_tool_041")
    chains = client.get("/api/expression/chains?scene=修复")
    recommendation = client.post("/api/expression/recommend", json={"scene": "修复", "goal": "修复信任", "limit": 3})

    assert seed.status_code == 200
    assert seed.json()["total_tools"] >= 60
    assert tools.status_code == 200
    assert tools.json()["total"] >= 10
    assert all(item["layer"] == "emotion" for item in tools.json()["items"])
    assert set(tools.json()["layers"]) >= {"logic", "ammo", "structure", "nonverbal", "emotion", "relationship"}
    assert {"初识", "暧昧", "热恋", "冲突", "修复", "长期", "亲密推进", "边界确认"} <= set(tools.json()["scenes"])
    assert {"说清事实", "命名感受", "确认边界", "降低防御", "提出请求", "修复信任", "引导深聊", "保留退路"} <= set(tools.json()["goals"])
    assert scene_search.status_code == 200
    assert scene_search.json()["items"]
    assert any("冲突" in item["best_scenes"] or "冲突" in item["description"] for item in scene_search.json()["items"])
    assert step_search.status_code == 200
    assert step_search.json()["items"]
    assert any("退路" in item["description"] or "退路" in "".join(item["micro_steps"]) for item in step_search.json()["items"])
    assert detail.status_code == 200
    assert detail.json()["name"] == "情绪标注"
    assert detail.json()["example_after"]
    assert chains.status_code == 200
    assert chains.json()["items"]
    assert recommendation.status_code == 200
    assert recommendation.json()["chains"] or recommendation.json()["tools"]
    assert "边界" in recommendation.json()["principle"]
