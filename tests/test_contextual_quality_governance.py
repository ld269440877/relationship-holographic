import json
import sqlite3
from pathlib import Path

from backend.database.contextual_quality_governance import clean_text, repair_blueprint, repair_database


def test_clean_text_removes_generated_artifacts() -> None:
    assert clean_text("我希望希望被理解。。") == "我希望被理解。"


def test_repair_blueprint_reanchors_response_variants() -> None:
    blueprint = {
        "setting": "朋友说今天特意买了一块蛋糕，但语气不像单纯开心。",
        "their_words": "我今天下班路上突然很想吃甜的，就买了蛋糕。",
        "deeper_need": "希望希望有人对自己的小情绪保持兴趣。。",
        "better_response": "你突然想吃甜的，听起来像是在给自己一个小小的安慰。",
        "boundary_note": "可以只说愿意说的部分。",
        "response_variants": [{"label": "深层共情版", "response": "我猜你希望希望有人懂你。。"}],
    }

    repaired, changed = repair_blueprint(blueprint)
    variants = repaired["response_variants"]

    assert changed is True
    assert "希望希望" not in json.dumps(repaired, ensure_ascii=False)
    assert variants[0]["response"].startswith("我听见你说")
    assert "蛋糕" in variants[-1]["response"]


def test_repair_database_cleans_rows(tmp_path: Path) -> None:
    db_path = tmp_path / "resources.db"
    blueprint = {
        "setting": "朋友说今天特意买了一块蛋糕，但语气不像单纯开心。",
        "their_words": "我今天下班路上突然很想吃甜的，就买了蛋糕。",
        "deeper_need": "希望希望有人对自己的小情绪保持兴趣。。",
        "better_response": "你突然想吃甜的，听起来像是在给自己一个小小的安慰。",
        "response_variants": [{"label": "深层共情版", "response": "我猜你希望希望被理解。。"}],
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
        raw = connection.execute("SELECT case_blueprint_json FROM resource_library WHERE id=1").fetchone()[0]

    assert result["updated"] == 1
    assert "希望希望" not in raw
    assert "response_variants" in json.loads(raw)
