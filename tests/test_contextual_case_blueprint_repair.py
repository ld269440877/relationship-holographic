import json
import sqlite3
from pathlib import Path

from backend.database.contextual_case_blueprint_repair import repair_database, rebuild_blueprint


def test_rebuild_blueprint_uses_actual_joke_dialogue() -> None:
    row = {
        "id": 47,
        "type": "joke",
        "category": "互怼",
        "title": "互怼",
        "content": "男：你做饭真好吃。女：那当然，我可是有天赋的。男：天赋是有的，就是差点运气把饭做熟。",
        "applicable_scene": "互怼",
        "expression_goal": "确认边界",
    }

    blueprint = rebuild_blueprint(row)
    raw = json.dumps(blueprint, ensure_ascii=False)

    assert "做饭真好吃" in raw
    assert "天赋" in raw
    assert "刚认识的人聊很深" not in raw
    assert "玩笑必须可撤回" in blueprint["boundary_note"]
    assert len(blueprint["dialogue_script"]) >= 5
    assert blueprint["dialogue_script"][0]["line"] == "你做饭真好吃。"


def test_repair_database_updates_only_legacy_blueprints(tmp_path: Path) -> None:
    db_path = tmp_path / "resources.db"
    legacy_blueprint = {
        "version": "module_metadata_completion_v1",
        "their_words": "我其实不太会和刚认识的人聊很深。",
        "dialogue_script": [{"speaker": "TA", "line": "我其实不太会和刚认识的人聊很深。"}],
    }
    current_blueprint = {
        "version": "case_matrix_v1",
        "their_words": "今天想吃蛋糕。",
        "better_response": "你今天是想奖励自己一下吗？",
    }
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
            CREATE TABLE resource_library (
              id INTEGER PRIMARY KEY,
              review_status TEXT,
              type TEXT,
              category TEXT,
              title TEXT,
              content TEXT,
              applicable_scene TEXT,
              expression_goal TEXT,
              case_blueprint_json TEXT,
              content_fingerprint TEXT,
              case_completeness_score REAL
            );
            """
        )
        connection.execute(
            """
            INSERT INTO resource_library
              (id, review_status, type, category, title, content, applicable_scene, expression_goal, case_blueprint_json)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                1,
                "published",
                "joke",
                "互怼",
                "互怼",
                "男：你做饭真好吃。女：那当然，我可是有天赋的。男：天赋是有的，就是差点运气把饭做熟。",
                "互怼",
                "确认边界",
                json.dumps(legacy_blueprint, ensure_ascii=False),
            ),
        )
        connection.execute(
            """
            INSERT INTO resource_library
              (id, review_status, type, category, title, content, applicable_scene, expression_goal, case_blueprint_json)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                2,
                "published",
                "game",
                "四阶心理沟通",
                "拒绝评判",
                "TA说：今天想吃蛋糕。",
                "社交",
                "拒绝评判",
                json.dumps(current_blueprint, ensure_ascii=False),
            ),
        )
        connection.commit()

    dry_run = repair_database(db_path, dry_run=True)
    assert dry_run["updated"] == 1
    with sqlite3.connect(db_path) as connection:
        raw_before = connection.execute("SELECT case_blueprint_json FROM resource_library WHERE id=1").fetchone()[0]
    assert "刚认识的人聊很深" in raw_before

    result = repair_database(db_path)
    with sqlite3.connect(db_path) as connection:
        raw_legacy = connection.execute("SELECT case_blueprint_json FROM resource_library WHERE id=1").fetchone()[0]
        raw_current = connection.execute("SELECT case_blueprint_json FROM resource_library WHERE id=2").fetchone()[0]
    repaired = json.loads(raw_legacy)

    assert result["updated"] == 1
    assert "刚认识的人聊很深" not in raw_legacy
    assert "做饭真好吃" in raw_legacy
    assert repaired["version"] == "contextual_case_blueprint_repair_v1"
    assert json.loads(raw_current) == current_blueprint
