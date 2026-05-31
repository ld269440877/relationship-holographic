import json
import sqlite3
from pathlib import Path

from backend.database.dialogue_response_governance import repair_blueprint, repair_database


def test_repair_blueprint_turns_meta_response_into_dialogue() -> None:
    blueprint = {
        "axis": "boundary_consent",
        "axis_label": "边界与同意",
        "resource_type_label": "具体故事卡",
        "difficulty_contract": "D3",
        "scene": "亲密推进",
        "setting": "沙发上两人靠得很近",
        "trigger": "气氛升温但对方信号变慢",
        "relation_stage": "亲密节奏协商",
        "their_words": "我有点紧张，不是不喜欢。",
        "surface_signal": "喜欢、紧张和请求确认",
        "deeper_need": "节奏自主、身体边界和安全感",
        "common_mistake": "把对方没有明确拒绝当成同意；旧回应通常会说：都这样了你还紧张什么，别想太多。",
        "why_wrong": "没有清晰同意的推进会让关系从靠近变成压力。",
        "better_response": "我先不急着判断，我注意到你刚才说“我有点紧张，不是不喜欢。”时停了一下。我的下一步是：让靠近、玩笑、请求和亲密推进都保留可拒绝出口。",
        "boundary_note": "没有明确、持续、可撤回的同意，就不继续推进。",
        "transfer_scene": "约会后的亲密确认",
    }

    repaired, changed = repair_blueprint(blueprint)
    raw = json.dumps(repaired, ensure_ascii=False)

    assert changed is True
    assert "我的下一步是" not in raw
    assert "不用为了照顾我勉强答应" in repaired["better_response"]
    assert len(repaired["dialogue_script"]) >= 6
    assert repaired["dialogue_script"][2]["speaker"] == "更好回应"
    assert len(repaired["response_variants"]) >= 5


def test_repair_database_updates_content_and_blueprint(tmp_path: Path) -> None:
    db_path = tmp_path / "resources.db"
    blueprint = {
        "axis": "micro_signal",
        "axis_label": "微关系信号",
        "resource_type_label": "具体故事卡",
        "difficulty_contract": "D1",
        "setting": "咖啡店排队时对方看了你一眼又移开",
        "relation_stage": "刚认识",
        "their_words": "我其实不太会跟刚认识的人聊天。",
        "common_mistake": "把一个小信号立刻判成冷淡；旧回应通常会说：你是不是不想理我？",
        "better_response": "我先不急着判断。先降低不确定性。我的下一步是：看见一句话背后的靠近。",
    }
    with sqlite3.connect(db_path) as connection:
        connection.execute(
            """
            CREATE TABLE resource_library (
              id INTEGER PRIMARY KEY,
              review_status TEXT,
              content TEXT,
              case_blueprint_json TEXT,
              content_fingerprint TEXT
            )
            """
        )
        connection.execute(
            "INSERT INTO resource_library (id, review_status, content, case_blueprint_json) VALUES (?, ?, ?, ?)",
            (1, "published", "更好回应：旧内容", json.dumps(blueprint, ensure_ascii=False)),
        )
        connection.commit()

    result = repair_database(db_path)
    with sqlite3.connect(db_path) as connection:
        content, raw = connection.execute("SELECT content, case_blueprint_json FROM resource_library WHERE id=1").fetchone()
    repaired = json.loads(raw)

    assert result["updated"] == 1
    assert "我的下一步是" not in raw
    assert "我听见你说" in repaired["better_response"]
    assert "完整对话：" in content
