"""Repair legacy case blueprints whose better response ignores context."""

from __future__ import annotations

import argparse
import json
import sqlite3
from datetime import datetime
from pathlib import Path
from shutil import copy2
from typing import Any

from backend.database.case_blueprint_enrichment import enrich_blueprint
from backend.database.connection import DB_PATH
from backend.database.psychological_communication_ladder_seed import SOURCE, _content, _non_judgment_response

LEGACY_NON_JUDGMENT = "我不会急着判断你这样对不对。换成我在这个处境里，也可能会很乱。"
REPAIR_VERSION = "contextual_response_repair_v1"


def backup_database(db_path: Path = DB_PATH) -> Path:
    backup_dir = db_path.parent / "backups"
    backup_dir.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    backup_path = backup_dir / f"{db_path.stem}-before-contextual-response-repair-{timestamp}{db_path.suffix}"
    copy2(db_path, backup_path)
    return backup_path


def _context_from_blueprint(blueprint: dict[str, Any]) -> dict[str, str]:
    return {
        "key": str(blueprint.get("scene") or ""),
        "their_words": str(blueprint.get("their_words") or ""),
        "deeper_need": str(blueprint.get("deeper_need") or ""),
        "transfer": str(blueprint.get("transfer_scene") or ""),
    }


def _difficulty(blueprint: dict[str, Any]) -> int:
    value = blueprint.get("difficulty_contract") or ""
    if "D3" in str(value):
        return 3
    if "D2" in str(value):
        return 2
    return int(blueprint.get("difficulty_level") or 1)


def contextual_better_response(blueprint: dict[str, Any]) -> str:
    base = _non_judgment_response(_context_from_blueprint(blueprint))
    difficulty = _difficulty(blueprint)
    if difficulty == 1:
        return base
    if difficulty == 2:
        return f"{base} 如果你愿意，我想听听这个小选择背后最具体的一点感受。"
    return f"{base} 你不用现在讲完整；如果继续说太累，我们可以只停在这个细节上。"


def _repair_blueprint(blueprint: dict[str, Any]) -> tuple[dict[str, Any], bool]:
    better = str(blueprint.get("better_response") or "")
    if LEGACY_NON_JUDGMENT not in better:
        return blueprint, False
    repaired = dict(blueprint)
    _ensure_content_defaults(repaired)
    repaired["better_response"] = contextual_better_response(repaired)
    notes = dict(repaired.get("quality_notes") or {})
    notes["contextual_response_repair"] = REPAIR_VERSION
    notes["repaired_at"] = datetime.now().isoformat(timespec="seconds")
    notes["reason"] = "legacy_non_judgment_template_was_too_generic_for_scene"
    repaired["quality_notes"] = notes
    for generated_key in (
        "response_variants",
        "perspective_examples",
        "transfer_analysis",
        "misread_risks",
        "practice_ladder",
    ):
        repaired.pop(generated_key, None)
    enriched, _ = enrich_blueprint(repaired)
    return enriched, True


def _ensure_content_defaults(blueprint: dict[str, Any]) -> None:
    blueprint.setdefault("ladder_index", 3)
    blueprint.setdefault("axis_label", "拒绝评判")
    blueprint.setdefault("difficulty_contract", "D1：完成当前阶的一句话回应。")
    blueprint.setdefault("setting", "一个具体互动片段")
    blueprint.setdefault("relation_stage", "日常关系互动")
    blueprint.setdefault("their_words", "我不知道该怎么说。")
    blueprint.setdefault("surface_signal", "对方正在释放一个需要被安全承接的信号。")
    blueprint.setdefault("deeper_need", "希望被看见、被理解，并保留选择空间。")
    blueprint.setdefault("common_mistake", "急着评价、建议或追问。")
    blueprint.setdefault("why_wrong", "安全表达环境来自不被审判，而不是被纠正。")
    blueprint.setdefault("response_steps", ["先不评价", "接住一个具体信号", "给出可退出空间"])
    blueprint.setdefault("boundary_note", "允许对方不说、少说或晚点再说。")
    blueprint.setdefault("practice_task", "把旧回应改成一句不评判、可退出的新回应。")
    blueprint.setdefault("transfer_scene", "换到一个相邻真实场景再练一次。")
    blueprint.setdefault("variant_deltas", ["本记录由历史通用回应修复为贴合语境回应。"])


def repair_database(db_path: Path = DB_PATH, *, dry_run: bool = False) -> dict[str, Any]:
    scanned = 0
    updated = 0
    invalid_json = 0
    backup_path: Path | None = None
    if not dry_run:
        backup_path = backup_database(db_path)
    with sqlite3.connect(db_path) as connection:
        connection.row_factory = sqlite3.Row
        rows = connection.execute(
            """
            SELECT id, content, case_blueprint_json
            FROM resource_library
            WHERE source = ?
              AND case_blueprint_json LIKE ?
            ORDER BY id
            """,
            (SOURCE, f"%{LEGACY_NON_JUDGMENT}%"),
        ).fetchall()
        for row in rows:
            scanned += 1
            try:
                blueprint = json.loads(row["case_blueprint_json"])
            except json.JSONDecodeError:
                invalid_json += 1
                continue
            if not isinstance(blueprint, dict):
                invalid_json += 1
                continue
            repaired, changed = _repair_blueprint(blueprint)
            if not changed:
                continue
            updated += 1
            if dry_run:
                continue
            content = _content(repaired)
            connection.execute(
                """
                UPDATE resource_library
                SET case_blueprint_json = ?,
                    content = ?,
                    content_fingerprint = ?
                WHERE id = ?
                """,
                (
                    json.dumps(repaired, ensure_ascii=False, sort_keys=True),
                    content,
                    "sha256:" + __import__("hashlib").sha256(content.encode("utf-8")).hexdigest(),
                    row["id"],
                ),
            )
        if dry_run:
            connection.rollback()
        else:
            connection.commit()
    return {
        "dry_run": dry_run,
        "scanned": scanned,
        "updated": updated,
        "invalid_json": invalid_json,
        "backup_path": str(backup_path) if backup_path else None,
        "version": REPAIR_VERSION,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Repair context-mismatched better responses.")
    parser.add_argument("--db", type=Path, default=DB_PATH)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    print(json.dumps(repair_database(args.db, dry_run=args.dry_run), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
