"""Audit and repair generated-looking text inside resource case blueprints."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sqlite3
from datetime import datetime
from pathlib import Path
from shutil import copy2
from typing import Any

from backend.database.case_blueprint_enrichment import enrich_blueprint
from backend.database.connection import DB_PATH
from backend.database.psychological_communication_ladder_seed import _content

REPAIR_VERSION = "contextual_quality_governance_v1"


def backup_database(db_path: Path = DB_PATH) -> Path:
    backup_dir = db_path.parent / "backups"
    backup_dir.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    backup_path = backup_dir / f"{db_path.stem}-before-contextual-quality-governance-{timestamp}{db_path.suffix}"
    copy2(db_path, backup_path)
    return backup_path


def clean_text(value: Any) -> str:
    text = str(value or "").strip()
    text = text.replace("希望希望", "希望")
    text = re.sub(r"([。！？])\1+", r"\1", text)
    text = re.sub(r"([。！？])\s+([。！？])", r"\1", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text


def contextual_response_variants(blueprint: dict[str, Any]) -> list[dict[str, str]]:
    their_words = clean_text(blueprint.get("their_words"))
    setting = _strip_sentence_end(clean_text(blueprint.get("setting")))
    deeper_need = clean_text(blueprint.get("deeper_need")) or "被看见、被尊重，并保留选择空间"
    boundary = clean_text(blueprint.get("boundary_note")) or "你可以只说愿意说的部分，也可以先停在这里。"
    return [
        {
            "label": "轻量承接版",
            "perspective": "先接住对方说出的具体内容，不评价、不抢结论。",
            "response": f"我听见你说“{their_words}”。我先不评价这件事，你愿意说说当时最明显的感受吗？",
            "why_it_works": "回应直接锚定原话，避免漂到无关大道理。",
            "best_when": "对方刚试探性分享，还不确定你是否安全时。",
        },
        {
            "label": "现实-感受交替版",
            "perspective": "先问现实细节，再问感受，避免审问或空泛共情。",
            "response": f"当时是发生了什么让你有这个念头？那一刻更像是累、想安慰自己，还是有点失落？",
            "why_it_works": "它从具体事实进入情绪，不靠模板硬套。",
            "best_when": "需要把话题从表层信息带入真实体验时。",
        },
        {
            "label": "深层共情版",
            "perspective": "把深层需要作为可校正的假设，而不是替对方定性。",
            "response": f"我猜这不只是表面这件小事，可能还有一点“{deeper_need}”。我这样理解对吗？",
            "why_it_works": "它贴合当前蓝图的深层需要，并留出纠正空间。",
            "best_when": "对方已经多说了几句，愿意被更深地理解时。",
        },
        {
            "label": "边界稳态版",
            "perspective": "给对方继续或停下的选择权。",
            "response": f"{boundary} 如果你愿意继续，我们就只聊“{their_words}”里最具体的一点。",
            "why_it_works": "它把边界出口和当前原话绑定，避免边界说明变成空话。",
            "best_when": "对方犹豫、停顿、防御或话题变重时。",
        },
        {
            "label": "场景化表达版",
            "perspective": "用当前场景画面承接，而不是泛泛说“我懂”。",
            "response": f"我脑子里看到的是：{setting}。如果我是你，也可能想先被轻轻听见，而不是马上被评价。",
            "why_it_works": "它把共情落回具体场景，学习者能看见句子为什么这样写。",
            "best_when": "卡片需要训练场景化表达和具体画面感时。",
        },
    ]


def repair_blueprint(blueprint: dict[str, Any]) -> tuple[dict[str, Any], bool]:
    original = json.dumps(blueprint, ensure_ascii=False, sort_keys=True)
    original_needs_variant_repair = _needs_variant_repair(blueprint)
    repaired = _clean_nested(blueprint)
    if isinstance(repaired, dict) and (original_needs_variant_repair or _needs_variant_repair(repaired)):
        repaired["response_variants"] = contextual_response_variants(repaired)
    current_without_notes = json.dumps(repaired, ensure_ascii=False, sort_keys=True)
    if current_without_notes == original:
        return blueprint, False
    if isinstance(repaired, dict):
        notes = dict(repaired.get("quality_notes") or {})
        notes["contextual_quality_governance"] = REPAIR_VERSION
        notes["rule"] = "clean_repeated_phrases_and_anchor_variants_to_setting_their_words_deeper_need"
        repaired["quality_notes"] = notes
        repaired, _ = enrich_blueprint(repaired)
    current = json.dumps(repaired, ensure_ascii=False, sort_keys=True)
    return repaired, current != original


def _clean_nested(value: Any) -> Any:
    if isinstance(value, str):
        return clean_text(value) if _has_text_artifact(value) else value
    if isinstance(value, list):
        return [_clean_nested(item) for item in value]
    if isinstance(value, dict):
        return {key: _clean_nested(item) for key, item in value.items()}
    return value


def _needs_variant_repair(blueprint: dict[str, Any]) -> bool:
    raw = json.dumps(blueprint.get("response_variants") or [], ensure_ascii=False)
    return (
        "希望希望" in raw
        or "。。" in raw
        or "？。" in raw
        or "！。" in raw
        or "脑子里有个画面" in raw
        or "当时具体发生了什么？" in raw
    )


def _has_text_artifact(text: str) -> bool:
    return (
        "希望希望" in text
        or "。。" in text
        or "？。" in text
        or "！。" in text
        or "。 。" in text
        or "[object Object]" in text
        or re.search(r"([。！？])\1+", text) is not None
    )


def _strip_sentence_end(text: str) -> str:
    return re.sub(r"[。！？.!?]+$", "", text.strip())


def _render_content(row_content: str, blueprint: dict[str, Any]) -> str:
    required = {"ladder_index", "axis_label", "difficulty_contract", "setting", "relation_stage", "their_words", "surface_signal", "deeper_need", "common_mistake", "why_wrong", "better_response", "response_steps", "boundary_note", "practice_task", "transfer_scene", "variant_deltas"}
    if required.issubset(blueprint):
        return _content(blueprint)
    content = row_content
    better = clean_text(blueprint.get("better_response"))
    if better:
        content = re.sub(r"更好回应[：:].*", f"更好回应：{better}", content)
    return clean_text(content)


def audit_database(db_path: Path = DB_PATH) -> dict[str, Any]:
    total = 0
    flagged = 0
    with sqlite3.connect(db_path) as connection:
        connection.row_factory = sqlite3.Row
        rows = connection.execute(
            """
            SELECT id, case_blueprint_json
            FROM resource_library
            WHERE review_status IN ('reviewed', 'published')
              AND case_blueprint_json IS NOT NULL
              AND TRIM(case_blueprint_json) <> ''
            """
        ).fetchall()
        for row in rows:
            total += 1
            try:
                blueprint = json.loads(row["case_blueprint_json"])
            except json.JSONDecodeError:
                flagged += 1
                continue
            if not isinstance(blueprint, dict):
                flagged += 1
                continue
            _, changed = repair_blueprint(blueprint)
            if changed:
                flagged += 1
    return {"scanned": total, "flagged": flagged, "version": REPAIR_VERSION}


def repair_database(db_path: Path = DB_PATH, *, dry_run: bool = False) -> dict[str, Any]:
    backup_path: Path | None = None
    if not dry_run:
        backup_path = backup_database(db_path)
    scanned = 0
    updated = 0
    invalid_json = 0
    with sqlite3.connect(db_path) as connection:
        connection.row_factory = sqlite3.Row
        rows = connection.execute(
            """
            SELECT id, content, case_blueprint_json
            FROM resource_library
            WHERE review_status IN ('reviewed', 'published')
              AND case_blueprint_json IS NOT NULL
              AND TRIM(case_blueprint_json) <> ''
            ORDER BY id
            """
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
            repaired, changed = repair_blueprint(blueprint)
            if not changed:
                continue
            updated += 1
            if dry_run:
                continue
            content = _render_content(row["content"] or "", repaired)
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
                    "sha256:" + hashlib.sha256(content.encode("utf-8")).hexdigest(),
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
    parser = argparse.ArgumentParser(description="Audit or repair contextual resource quality.")
    parser.add_argument("--db", type=Path, default=DB_PATH)
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--audit", action="store_true")
    args = parser.parse_args()
    result = audit_database(args.db) if args.audit else repair_database(args.db, dry_run=args.dry_run)
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
