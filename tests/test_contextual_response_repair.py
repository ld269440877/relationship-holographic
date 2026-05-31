import json
import sqlite3
from pathlib import Path

from backend.database.contextual_response_repair import (
    LEGACY_NON_JUDGMENT,
    contextual_better_response,
    repair_database,
)
from backend.database.psychological_communication_ladder_seed import SOURCE


def test_contextual_better_response_matches_social_cake_scene() -> None:
    blueprint = {
        "scene": "社交",
        "their_words": "我今天下班路上突然很想吃甜的，就买了蛋糕。",
        "deeper_need": "希望有人对自己的小情绪保持兴趣。",
        "difficulty_contract": "D3：在对方沉默或防御时仍保留边界，不逼深聊。",
    }

    response = contextual_better_response(blueprint)

    assert "吃甜的" in response
    assert "小小的安慰" in response
    assert "判断你这样对不对" not in response


def test_repair_database_updates_content_and_blueprint(tmp_path: Path) -> None:
    db_path = tmp_path / "resources.db"
    blueprint = {
        "axis_label": "拒绝评判",
        "scene": "社交",
        "setting": "朋友说今天特意买了一块蛋糕，但语气不像单纯开心。",
        "their_words": "我今天下班路上突然很想吃甜的，就买了蛋糕。",
        "deeper_need": "希望有人对自己的小情绪保持兴趣。",
        "common_mistake": "挺好，少吃点别胖了。",
        "why_wrong": "安全表达环境来自不被审判，而不是被纠正。",
        "better_response": f"{LEGACY_NON_JUDGMENT} 你不用现在讲完整；如果继续说太累，我们可以先停在这里。",
        "response_steps": ["先完成本阶目标：不反驳、不挑剔、不秀优越感。"],
        "boundary_note": "让对方敞开心扉不等于逼对方交代隐私。",
        "practice_task": "改写一句。",
        "transfer_scene": "换成朋友说想一个人走很远。",
        "variant_deltas": ["难度不同：D3"],
        "difficulty_contract": "D3：在对方沉默或防御时仍保留边界，不逼深聊。",
        "relation_stage": "朋友间日常分享",
        "ladder_index": 3,
    }
    with sqlite3.connect(db_path) as connection:
        connection.execute(
            """
            CREATE TABLE resource_library (
              id INTEGER PRIMARY KEY,
              source TEXT,
              content TEXT,
              case_blueprint_json TEXT,
              content_fingerprint TEXT
            )
            """
        )
        connection.execute(
            "INSERT INTO resource_library (id, source, content, case_blueprint_json) VALUES (?, ?, ?, ?)",
            (1, SOURCE, "旧内容", json.dumps(blueprint, ensure_ascii=False)),
        )
        connection.commit()

    result = repair_database(db_path)
    with sqlite3.connect(db_path) as connection:
        content, raw = connection.execute("SELECT content, case_blueprint_json FROM resource_library WHERE id=1").fetchone()
    repaired = json.loads(raw)

    assert result["updated"] == 1
    assert "小小的安慰" in repaired["better_response"]
    assert "小小的安慰" in content
    assert "response_variants" in repaired
