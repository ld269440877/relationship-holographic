import json
import sqlite3
from pathlib import Path

from backend.database.case_blueprint_enrichment import enrich_blueprint, enrich_database


def test_enrich_blueprint_adds_multiview_learning_fields() -> None:
    blueprint = {
        "axis_label": "拒绝评判",
        "setting": "朋友买了一块蛋糕，但语气不像单纯开心。",
        "their_words": "我今天特意买了块蛋糕。",
        "common_mistake": "挺好，少吃点别胖了。",
        "better_response": "你今天突然想吃甜的，是想奖励自己一下吗？",
        "boundary_note": "允许对方只说愿意说的部分。",
        "deeper_need": "希望有人对自己的小情绪保持兴趣。",
        "transfer_scene": "换成同事说下班后一个人去看电影。",
    }

    enriched, changed = enrich_blueprint(blueprint)

    assert changed is True
    assert len(enriched["response_variants"]) >= 5
    assert len(enriched["perspective_examples"]) >= 4
    assert len(enriched["misread_risks"]) >= 4
    assert len(enriched["practice_ladder"]) >= 4
    assert "stable_principles" in enriched["transfer_analysis"]
    assert enriched["quality_notes"]["copyright_boundary"] == "project_original_structured_analysis_no_third_party_full_text"


def test_enrich_blueprint_preserves_existing_fields() -> None:
    blueprint = {
        "setting": "测试场景",
        "response_variants": [{"label": "自定义", "response": "保留我"}],
    }

    enriched, changed = enrich_blueprint(blueprint)

    assert changed is True
    assert enriched["response_variants"] == [{"label": "自定义", "response": "保留我"}]
    assert "perspective_examples" in enriched


def test_enrich_database_dry_run_does_not_modify(tmp_path: Path) -> None:
    db_path = tmp_path / "resources.db"
    with sqlite3.connect(db_path) as connection:
        connection.execute("CREATE TABLE resource_library (id INTEGER PRIMARY KEY, case_blueprint_json TEXT)")
        connection.execute(
            "INSERT INTO resource_library (id, case_blueprint_json) VALUES (?, ?)",
            (1, json.dumps({"setting": "测试场景", "their_words": "好累"}, ensure_ascii=False)),
        )
        connection.commit()

    result = enrich_database(db_path, dry_run=True)
    with sqlite3.connect(db_path) as connection:
        raw = connection.execute("SELECT case_blueprint_json FROM resource_library WHERE id=1").fetchone()[0]

    assert result["updated"] == 1
    assert "response_variants" not in raw


def test_enrich_database_updates_rows(tmp_path: Path) -> None:
    db_path = tmp_path / "resources.db"
    with sqlite3.connect(db_path) as connection:
        connection.execute("CREATE TABLE resource_library (id INTEGER PRIMARY KEY, case_blueprint_json TEXT)")
        connection.execute(
            "INSERT INTO resource_library (id, case_blueprint_json) VALUES (?, ?)",
            (1, json.dumps({"setting": "测试场景", "their_words": "好累"}, ensure_ascii=False)),
        )
        connection.commit()

    result = enrich_database(db_path)
    with sqlite3.connect(db_path) as connection:
        raw = connection.execute("SELECT case_blueprint_json FROM resource_library WHERE id=1").fetchone()[0]

    assert result["updated"] == 1
    assert result["backup_path"]
    assert "response_variants" in json.loads(raw)
