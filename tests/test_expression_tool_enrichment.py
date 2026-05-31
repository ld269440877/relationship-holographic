import sqlite3
from pathlib import Path

from backend.database.expression_tool_enrichment import build_learning_blueprint, enrich_database


def test_build_learning_blueprint_contains_dialogue_cases() -> None:
    row = {
        "name": "对比表达",
        "category": "差异呈现",
        "formula": "过去 -> 现在 -> 想要",
        "description": "对比表达用于内容弹药层。",
        "best_scenes_json": '["初识", "暧昧", "冲突"]',
        "micro_steps_json": '["先给结构", "补一个具体事实"]',
        "risk_flags_json": '["翻旧账"]',
    }

    blueprint = build_learning_blueprint(row)  # type: ignore[arg-type]

    assert blueprint["definition"].startswith("对比表达不是一句固定话术")
    assert len(blueprint["dialogue_cases"]) == 3
    assert "之前" in blueprint["dialogue_cases"][0]["better_response"]
    assert "low_quality_response" in blueprint["dialogue_cases"][0]


def test_enrich_database_writes_learning_blueprint(tmp_path: Path) -> None:
    db_path = tmp_path / "expression.db"
    with sqlite3.connect(db_path) as connection:
        connection.execute(
            """
            CREATE TABLE expression_tools (
              id INTEGER PRIMARY KEY,
              tool_uuid TEXT,
              name TEXT,
              layer TEXT,
              category TEXT,
              formula TEXT,
              description TEXT,
              best_scenes_json TEXT,
              micro_steps_json TEXT,
              risk_flags_json TEXT,
              review_status TEXT,
              learning_blueprint_json TEXT,
              updated_at TEXT
            )
            """
        )
        connection.execute(
            """
            INSERT INTO expression_tools (
              id, tool_uuid, name, layer, category, formula, description,
              best_scenes_json, micro_steps_json, risk_flags_json, review_status
            ) VALUES (1, 'expr_tool_020', '对比表达', 'ammo', '差异呈现', '过去 -> 现在 -> 想要', '对比表达用于内容弹药层。', '["初识"]', '[]', '[]', 'published')
            """
        )
        connection.commit()

    result = enrich_database(db_path)
    with sqlite3.connect(db_path) as connection:
        raw = connection.execute("SELECT learning_blueprint_json FROM expression_tools WHERE id=1").fetchone()[0]

    assert result["updated"] == 1
    assert "dialogue_cases" in raw
    assert "对比表达" in raw
