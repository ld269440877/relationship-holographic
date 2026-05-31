import json
import sqlite3
from pathlib import Path

from backend.database.resource_case_quality_automation import audit_case_quality, repair_case_quality


def _create_db(path: Path) -> None:
    with sqlite3.connect(path) as connection:
        connection.execute(
            """
            CREATE TABLE resource_library (
              id INTEGER PRIMARY KEY,
              resource_uuid TEXT,
              type TEXT,
              category TEXT,
              title TEXT,
              content TEXT,
              tags TEXT,
              review_status TEXT,
              published_at TEXT,
              case_blueprint_json TEXT,
              case_completeness_score REAL,
              coverage_axis TEXT,
              content_fingerprint TEXT
            )
            """
        )
        connection.execute(
            """
            CREATE TABLE pipeline_run_logs (
              id INTEGER PRIMARY KEY,
              target_type TEXT,
              target_id INTEGER,
              action TEXT,
              from_status TEXT,
              to_status TEXT,
              result_json TEXT,
              message TEXT,
              created_at TEXT
            )
            """
        )
        connection.commit()


def test_audit_case_quality_detects_incomplete_mismatch_and_stereotype(tmp_path: Path) -> None:
    db_path = tmp_path / "quality.db"
    _create_db(db_path)
    blueprint = {
        "their_words": "我今天很累。",
        "better_response": "我先不急着判断。我的下一步是：看见一句话背后的靠近。",
    }
    with sqlite3.connect(db_path) as connection:
        connection.execute(
            """
            INSERT INTO resource_library
            (id, resource_uuid, type, category, title, content, tags, review_status, case_blueprint_json, case_completeness_score, coverage_axis)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                1,
                "r1",
                "story",
                "测试",
                "女人的底层逻辑测试",
                "场景：她说累。更好回应：我先不急着判断。我的下一步是：看见一句话背后的靠近。",
                "具体案例",
                "published",
                json.dumps(blueprint, ensure_ascii=False),
                40,
                "emotion_flow",
            ),
        )
        connection.commit()

    report = audit_case_quality(db_path, limit=10)

    assert report["summary"]["incomplete"] == 1
    assert report["summary"]["context_mismatch"] == 1
    assert report["summary"]["stereotype_or_manipulation_risk"] == 1
    assert report["quality_gate"]["minimum_case_completeness"] == 85


def test_repair_case_quality_rebuilds_or_quarantines_without_deleting(tmp_path: Path) -> None:
    db_path = tmp_path / "quality.db"
    _create_db(db_path)
    with sqlite3.connect(db_path) as connection:
        connection.execute(
            """
            INSERT INTO resource_library
            (id, resource_uuid, type, category, title, content, tags, review_status, case_blueprint_json, case_completeness_score, coverage_axis)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                1,
                "r1",
                "story",
                "测试",
                "普通案例",
                "TA说：我今天很累。更好回应：我先不急着判断。我的下一步是：看见一句话背后的靠近。",
                "具体案例",
                "published",
                json.dumps({"their_words": "我今天很累。", "better_response": "我先不急着判断。我的下一步是：看见一句话背后的靠近。"}, ensure_ascii=False),
                40,
                "emotion_flow",
            ),
        )
        connection.execute(
            """
            INSERT INTO resource_library
            (id, resource_uuid, type, category, title, content, tags, review_status, case_blueprint_json, case_completeness_score, coverage_axis)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                2,
                "r2",
                "story",
                "测试",
                "女人的底层逻辑风险",
                "女人的底层逻辑：慕强癖。",
                "具体案例",
                "published",
                "{}",
                90,
                "relationship_need_calibration",
            ),
        )
        connection.commit()

    result = repair_case_quality(db_path, dry_run=False, limit=10)
    with sqlite3.connect(db_path) as connection:
        rows = connection.execute("SELECT id, review_status, content, tags, case_completeness_score FROM resource_library ORDER BY id").fetchall()
        logs = connection.execute("SELECT action, result_json FROM pipeline_run_logs ORDER BY id").fetchall()

    assert result["repaired"] == 1
    assert result["quarantined"] == 1
    assert rows[0][1] == "published"
    assert "完整对话" in rows[0][2]
    assert "案例质量自动修复" in rows[0][3]
    assert rows[0][4] >= 94
    assert rows[1][1] == "quarantine"
    assert "需去偏复审" in rows[1][3]
    assert len(logs) == 2
    assert all("女人的底层逻辑" not in row[1] for row in logs)
