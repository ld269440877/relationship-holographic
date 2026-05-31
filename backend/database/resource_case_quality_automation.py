"""Automated resource case quality audit and safe repair helpers."""

from __future__ import annotations

import argparse
import hashlib
import json
import sqlite3
from datetime import datetime
from pathlib import Path
from shutil import copy2
from typing import Any

from backend.database.connection import DB_PATH
from backend.database.contextual_case_blueprint_repair import rebuild_blueprint, render_content

AUTOMATION_VERSION = "resource_case_quality_automation_v1"
REQUIRED_MARKERS = (
    "场景",
    "TA说",
    "完整对话",
    "常见失误",
    "更好回应",
    "边界",
    "练习任务",
)
STEREOTYPE_MARKERS = (
    "女人的底层逻辑",
    "受虐癖",
    "恋恶癖",
    "慕强癖",
    "认同癖",
    "拿捏",
    "让她离不开",
    "无视她拒绝",
)


def backup_database(db_path: Path = DB_PATH) -> Path:
    backup_dir = db_path.parent / "backups"
    backup_dir.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    backup_path = backup_dir / f"{db_path.stem}-before-resource-case-quality-automation-{timestamp}{db_path.suffix}"
    copy2(db_path, backup_path)
    return backup_path


def audit_case_quality(db_path: Path = DB_PATH, *, limit: int = 5000) -> dict[str, Any]:
    with sqlite3.connect(db_path) as connection:
        connection.row_factory = sqlite3.Row
        rows = _fetch_candidate_rows(
            connection,
            "id, type, title, content, tags, review_status, case_blueprint_json, case_completeness_score, coverage_axis",
            limit,
        )

    scanned = len(rows)
    incomplete: list[dict[str, Any]] = []
    mismatched: list[dict[str, Any]] = []
    stereotype: list[dict[str, Any]] = []
    for row in rows:
        content = str(row["content"] or "")
        blueprint = _loads_dict(row["case_blueprint_json"])
        markers = [marker for marker in STEREOTYPE_MARKERS if marker in content or marker in str(row["title"] or "")]
        if markers:
            stereotype.append(_issue(row, "stereotype_or_manipulation_risk", markers))
        if not _is_training_case_row(row):
            continue
        missing = _missing_markers(content, blueprint)
        if missing or float(row["case_completeness_score"] or 0) < 85:
            incomplete.append(_issue(row, "incomplete_case", missing))
        if _better_response_mismatch(content, blueprint):
            mismatched.append(_issue(row, "context_mismatch", ["better_response_not_grounded"]))

    return {
        "version": AUTOMATION_VERSION,
        "scanned": scanned,
        "quality_gate": {
            "minimum_case_completeness": 85,
            "required_markers": list(REQUIRED_MARKERS),
            "stereotype_markers_quarantined": list(STEREOTYPE_MARKERS),
        },
        "summary": {
            "incomplete": len(incomplete),
            "context_mismatch": len(mismatched),
            "stereotype_or_manipulation_risk": len(stereotype),
            "estimated_repairable": len(_repairable_ids(incomplete + mismatched)),
        },
        "samples": {
            "incomplete": incomplete[:12],
            "context_mismatch": mismatched[:12],
            "stereotype_or_manipulation_risk": stereotype[:12],
        },
        "next_actions": _next_actions(incomplete, mismatched, stereotype),
        "principle": "案例质量审计只检查本地资源结构，不抓取第三方全文；风险性别泛化和操控化内容默认进入隔离或去偏改写。",
    }


def repair_case_quality(
    db_path: Path = DB_PATH,
    *,
    dry_run: bool = True,
    limit: int = 200,
    reviewer_id: str = "case-quality-automation",
) -> dict[str, Any]:
    backup_path: Path | None = None
    if not dry_run:
        backup_path = backup_database(db_path)
    with sqlite3.connect(db_path) as connection:
        connection.row_factory = sqlite3.Row
        rows = _fetch_candidate_rows(connection, "*", limit)
        scanned = len(rows)
        repaired = 0
        quarantined = 0
        skipped = 0
        repaired_items: list[dict[str, Any]] = []
        quarantined_items: list[dict[str, Any]] = []
        for row in rows:
            content = str(row["content"] or "")
            title = str(row["title"] or "")
            risk_markers = [marker for marker in STEREOTYPE_MARKERS if marker in content or marker in title]
            if risk_markers:
                quarantined += 1
                quarantined_items.append(_issue(row, "stereotype_or_manipulation_risk", risk_markers))
                if not dry_run:
                    connection.execute(
                        """
                        UPDATE resource_library
                        SET review_status = 'quarantine',
                            published_at = NULL,
                            tags = ?
                        WHERE id = ?
                        """,
                        (_append_tag(row["tags"], "需去偏复审"), row["id"]),
                    )
                    _insert_log(connection, row, reviewer_id, "quarantine_stereotype_or_manipulation_risk", risk_markers)
                continue

            blueprint = _loads_dict(row["case_blueprint_json"])
            missing = _missing_markers(content, blueprint)
            should_repair = (
                _is_training_case_row(row)
                and (bool(missing) or _better_response_mismatch(content, blueprint) or float(row["case_completeness_score"] or 0) < 85)
            )
            if not should_repair:
                skipped += 1
                continue
            rebuilt = rebuild_blueprint(row)
            new_content = render_content(content, rebuilt)
            repaired += 1
            repaired_items.append({
                "id": row["id"],
                "title": row["title"],
                "missing": missing,
                "new_score": 94,
            })
            if not dry_run:
                connection.execute(
                    """
                    UPDATE resource_library
                    SET case_blueprint_json = ?,
                        content = ?,
                        content_fingerprint = ?,
                        case_completeness_score = CASE
                          WHEN case_completeness_score IS NULL OR case_completeness_score < 94 THEN 94
                          ELSE case_completeness_score
                        END,
                        tags = ?
                    WHERE id = ?
                    """,
                    (
                        json.dumps(rebuilt, ensure_ascii=False, sort_keys=True),
                        new_content,
                        "sha256:" + hashlib.sha256(new_content.encode("utf-8")).hexdigest(),
                        _append_tag(row["tags"], "案例质量自动修复"),
                        row["id"],
                    ),
                )
                _insert_log(connection, row, reviewer_id, "repair_case_blueprint_context", missing)
        if dry_run:
            connection.rollback()
        else:
            connection.commit()
    return {
        "dry_run": dry_run,
        "version": AUTOMATION_VERSION,
        "scanned": scanned,
        "repaired": repaired,
        "quarantined": quarantined,
        "skipped": skipped,
        "backup_path": str(backup_path) if backup_path else None,
        "samples": {
            "repaired": repaired_items[:12],
            "quarantined": quarantined_items[:12],
        },
        "quality_gate": {
            "content_deleted": False,
            "third_party_full_text_saved": False,
            "risk_content_default_hidden": True,
        },
    }


def _fetch_candidate_rows(connection: sqlite3.Connection, columns: str, limit: int) -> list[sqlite3.Row]:
    column_names = _table_columns(connection, "resource_library")
    pytest_filters = [
        "lower(coalesce(resource_uuid, '')) NOT LIKE '%pytest%'",
    ]
    if "source" in column_names:
        pytest_filters.append("lower(coalesce(source, '')) NOT LIKE '%pytest%'")
    if "source_url" in column_names:
        pytest_filters.append("lower(coalesce(source_url, '')) NOT LIKE '%pytest%'")
    sql = f"""
        SELECT {columns}
        FROM resource_library
        WHERE review_status IN ('reviewed', 'published')
          AND {" AND ".join(pytest_filters)}
        ORDER BY id DESC
        LIMIT ?
    """
    return list(connection.execute(sql, (limit,)).fetchall())


def _table_columns(connection: sqlite3.Connection, table_name: str) -> set[str]:
    rows = connection.execute(f"PRAGMA table_info({table_name})").fetchall()
    return {str(row[1]) for row in rows}


def _loads_dict(raw: str | None) -> dict[str, Any]:
    if not raw:
        return {}
    try:
        value = json.loads(raw)
    except json.JSONDecodeError:
        return {}
    return value if isinstance(value, dict) else {}


def _missing_markers(content: str, blueprint: dict[str, Any]) -> list[str]:
    missing: list[str] = []
    for marker in REQUIRED_MARKERS:
        if marker == "TA说":
            present = any(label in content for label in ("TA说", "TA原话", "对方说")) or bool(blueprint.get("their_words"))
        elif marker == "边界":
            present = any(label in content for label in ("边界", "退路", "可拒绝", "同意")) or bool(blueprint.get("boundary_note"))
        elif marker == "常见失误":
            present = any(label in content for label in ("常见失误", "低质量回应")) or bool(blueprint.get("common_mistake"))
        elif marker == "完整对话":
            present = marker in content or bool(blueprint.get("dialogue_script"))
        else:
            present = marker in content or bool(blueprint.get(_marker_to_blueprint_key(marker)))
        if not present:
            missing.append(marker)
    return missing


def _marker_to_blueprint_key(marker: str) -> str:
    return {
        "场景": "setting",
        "更好回应": "better_response",
        "练习任务": "practice_task",
    }.get(marker, marker)


def _better_response_mismatch(content: str, blueprint: dict[str, Any]) -> bool:
    better = str(blueprint.get("better_response") or "")
    their_words = str(blueprint.get("their_words") or "")
    if not better:
        return True
    if "我先不急着判断" in better and not any(token in better for token in _grounding_tokens(their_words, content)):
        return True
    if "我的下一步是" in better and "TA说" in content:
        return True
    return False


def _is_training_case_row(row: sqlite3.Row) -> bool:
    resource_type = str(row["type"] or "")
    tags = str(row["tags"] or "")
    title = str(row["title"] or "")
    if resource_type == "media" or "来源锚点" in title:
        return False
    return "具体案例" in tags or resource_type in {"game", "story", "phrase", "flirty", "joke", "riddle"}


def _grounding_tokens(their_words: str, content: str) -> list[str]:
    source = their_words or content[:120]
    tokens = [token for token in source.replace("，", " ").replace("。", " ").replace("“", " ").replace("”", " ").split() if len(token) >= 2]
    return tokens[:8]


def _issue(row: sqlite3.Row, issue_type: str, evidence: list[str]) -> dict[str, Any]:
    return {
        "id": row["id"],
        "title": row["title"],
        "type": row["type"],
        "review_status": row["review_status"],
        "coverage_axis": row["coverage_axis"] if "coverage_axis" in row.keys() else None,
        "issue_type": issue_type,
        "evidence": evidence,
    }


def _repairable_ids(issues: list[dict[str, Any]]) -> set[int]:
    return {int(item["id"]) for item in issues if item.get("id") is not None}


def _append_tag(raw: str | None, tag: str) -> str:
    tags = [item.strip() for item in str(raw or "").split(",") if item.strip()]
    if tag not in tags:
        tags.append(tag)
    return ",".join(tags)


def _insert_log(
    connection: sqlite3.Connection,
    row: sqlite3.Row,
    reviewer_id: str,
    action: str,
    evidence: list[str],
) -> None:
    connection.execute(
        """
        INSERT INTO pipeline_run_logs
          (target_type, target_id, action, from_status, to_status, result_json, message, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            "resource",
            row["id"],
            action,
            row["review_status"],
            "quarantine" if action.startswith("quarantine") else row["review_status"],
            json.dumps({
                "version": AUTOMATION_VERSION,
                "reviewer_id": reviewer_id,
                "evidence_hashes": [
                    "sha256:" + hashlib.sha256(str(item).encode("utf-8")).hexdigest()
                    for item in evidence
                ],
                "evidence_count": len(evidence),
                "title_hash": hashlib.sha256(str(row["title"] or "").encode("utf-8")).hexdigest(),
                "raw_source_text_saved": False,
                "content_deleted": False,
            }, ensure_ascii=False),
            f"{AUTOMATION_VERSION}:{action}",
            datetime.now().isoformat(timespec="seconds"),
        ),
    )


def _next_actions(
    incomplete: list[dict[str, Any]],
    mismatched: list[dict[str, Any]],
    stereotype: list[dict[str, Any]],
) -> list[dict[str, str]]:
    actions: list[dict[str, str]] = []
    if incomplete:
        actions.append({"priority": "high", "action": "运行 case-quality repair", "reason": f"{len(incomplete)} 条资源缺少完整案例结构。"})
    if mismatched:
        actions.append({"priority": "high", "action": "重建更好回应", "reason": f"{len(mismatched)} 条资源的更好回应疑似未贴合当前语境。"})
    if stereotype:
        actions.append({"priority": "high", "action": "隔离并去偏改写", "reason": f"{len(stereotype)} 条资源包含性别刻板或操控化风险标记。"})
    if not actions:
        actions.append({"priority": "low", "action": "保持每日抽样审计", "reason": "当前扫描窗口未发现 P0 案例质量问题。"})
    return actions


def main() -> None:
    parser = argparse.ArgumentParser(description="Audit and repair resource case quality.")
    parser.add_argument("--db", type=Path, default=DB_PATH)
    parser.add_argument("--limit", type=int, default=5000)
    parser.add_argument("--repair", action="store_true")
    parser.add_argument("--apply", action="store_true")
    parser.add_argument("--reviewer-id", default="case-quality-automation")
    args = parser.parse_args()
    if args.repair:
        result = repair_case_quality(args.db, dry_run=not args.apply, limit=args.limit, reviewer_id=args.reviewer_id)
    else:
        result = audit_case_quality(args.db, limit=args.limit)
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
