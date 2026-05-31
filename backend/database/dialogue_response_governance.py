"""Repair resource blueprints so better responses are real dialogue."""

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

from backend.database.connection import DB_PATH

REPAIR_VERSION = "dialogue_response_governance_v1"

META_RESPONSE_MARKERS = (
    "我的下一步是",
    "直接说清影响和下一步",
    "先降低不确定性",
    "给空间和时间窗口",
    "保持事实清楚、情绪可承接、边界可退出",
)


def backup_database(db_path: Path = DB_PATH) -> Path:
    backup_dir = db_path.parent / "backups"
    backup_dir.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    backup_path = backup_dir / f"{db_path.stem}-before-dialogue-response-governance-{timestamp}{db_path.suffix}"
    copy2(db_path, backup_path)
    return backup_path


def needs_dialogue_repair(blueprint: dict[str, Any]) -> bool:
    raw = json.dumps(
        {
            "better_response": blueprint.get("better_response"),
            "response_variants": blueprint.get("response_variants"),
        },
        ensure_ascii=False,
    )
    return any(marker in raw for marker in META_RESPONSE_MARKERS)


def needs_punctuation_repair(blueprint: dict[str, Any]) -> bool:
    raw = json.dumps(
        {
            "better_response": blueprint.get("better_response"),
            "dialogue_script": blueprint.get("dialogue_script"),
            "response_variants": blueprint.get("response_variants"),
        },
        ensure_ascii=False,
    )
    return "。”。" in raw


def repair_blueprint(blueprint: dict[str, Any]) -> tuple[dict[str, Any], bool]:
    original = json.dumps(blueprint, ensure_ascii=False, sort_keys=True)
    repaired = dict(blueprint)
    if not needs_dialogue_repair(repaired) and not needs_punctuation_repair(repaired):
        return blueprint, False

    repaired["better_response"] = build_better_response(repaired)
    repaired["dialogue_script"] = build_dialogue_script(repaired)
    repaired["response_variants"] = build_response_variants(repaired)
    repaired["response_steps"] = build_response_steps(repaired)
    notes = dict(repaired.get("quality_notes") or {})
    notes["dialogue_response_governance"] = REPAIR_VERSION
    notes["rule"] = "better_response_and_variants_must_be_direct_contextual_dialogue"
    repaired["quality_notes"] = notes
    current = json.dumps(repaired, ensure_ascii=False, sort_keys=True)
    return repaired, current != original


def build_better_response(blueprint: dict[str, Any]) -> str:
    axis = str(blueprint.get("axis") or "")
    scene = str(blueprint.get("scene") or "")
    their_words = _quote_text(blueprint.get("their_words")) or "你刚才那句话"
    transfer = _text(blueprint.get("transfer_scene")) or "晚一点"
    setting = _short_setting(blueprint)

    if axis == "micro_signal":
        return f"我听见你说“{their_words}”。我先不猜你是不是在拒绝我，只想确认一下：你是有点紧张，还是需要一点时间慢慢熟？"
    if axis == "emotion_flow":
        return f"你说“{their_words}”的时候，我感觉这里不只是事情本身，还有一点累或委屈。你愿意先说最重的那一点吗？"
    if axis == "boundary_consent":
        return f"听到你说“{their_words}”，我们可以慢一点。你不用为了照顾我勉强答应，舒服和不舒服都可以直接说。"
    if axis == "flirty_tension":
        return f"这句我有接到一点靠近，也不会逼你表态。我们就轻轻聊到这里，你想接梗再接也可以。"
    if axis == "conflict_repair":
        return f"你说“{their_words}”，我先承认这件事让你不好受。我不急着解释，先听你最在意的是哪一段。"
    if axis == "long_connection":
        return f"这听起来不像一次小事，更像我们节奏需要重新对齐。我们今晚先定一个小约定，不把问题拖到下次爆发。"
    if axis == "humor_interaction":
        return f"我想轻一点接住，但不拿你的不舒服开玩笑。你愿意的话，我先陪你把这件事说轻一点。"
    if axis == "mistake_rewrite":
        return f"我把刚才那句收回来。更准确地说，我在意你刚才这句话，也愿意按你的节奏慢慢听。"
    if scene == "亲密推进":
        return f"听到你说“{their_words}”，我会先停一下。喜欢可以慢慢来，你不用现在证明什么。"
    return f"我听见你说“{their_words}”。结合刚才{setting}，我先不评价，只想问一个小问题；不想答也可以，我们可以{transfer}再聊。"


def build_dialogue_script(blueprint: dict[str, Any]) -> list[dict[str, str]]:
    their_words = _text(blueprint.get("their_words")) or "我现在不知道怎么说。"
    bad = _extract_bad_response(_text(blueprint.get("common_mistake")))
    better = build_better_response(blueprint)
    follow_up = _follow_up_response(blueprint)
    closing = _closing_response(blueprint)
    return [
        {"speaker": "TA", "line": their_words, "purpose": "原始信号"},
        {"speaker": "低质量回应", "line": bad, "purpose": "触发防御或压力"},
        {"speaker": "更好回应", "line": better, "purpose": "先承接语境，再给低压力出口"},
        {"speaker": "TA", "line": _likely_reply(blueprint), "purpose": "对方更可能继续补充"},
        {"speaker": "继续回应", "line": follow_up, "purpose": "现实细节和感受交替推进"},
        {"speaker": "边界收束", "line": closing, "purpose": "把连接落回可退出、可复盘"},
    ]


def build_response_variants(blueprint: dict[str, Any]) -> list[dict[str, str]]:
    their_words = _quote_text(blueprint.get("their_words")) or "你刚才那句话"
    deeper_need = _text(blueprint.get("deeper_need")) or "被看见，也能保留选择空间"
    boundary = _text(blueprint.get("boundary_note")) or "你可以只说愿意说的部分，也可以先停。"
    setting = _short_setting(blueprint)
    return [
        {
            "label": "轻量承接版",
            "perspective": "只接住原话，不抢结论。",
            "response": f"我听见你说“{their_words}”。我先不评价，你愿意说说刚才最明显的感受吗？",
            "why_it_works": "它把回应锚定到 TA 原话，而不是输出课程说明。",
            "best_when": "对方刚开始试探性表达时。",
        },
        {
            "label": "现实-感受交替版",
            "perspective": "先问一个现实细节，再问一个感受。",
            "response": f"刚才具体是哪一刻让你有这个感觉？那一刻更像是紧张、累，还是想被确认一下？",
            "why_it_works": "问题有层次，但不会连续追问。",
            "best_when": "需要把话题从表层寒暄带入真实经验时。",
        },
        {
            "label": "深层共情版",
            "perspective": "把深层需要作为可校正假设。",
            "response": f"我猜这句话背后可能有一点“{deeper_need}”。如果我理解偏了，你可以直接纠正我。",
            "why_it_works": "它给出理解，也把解释权留给对方。",
            "best_when": "对方已经愿意多说几句时。",
        },
        {
            "label": "边界稳态版",
            "perspective": "明确继续、暂停、跳过都可以。",
            "response": f"{boundary} 如果你愿意继续，我们只聊“{their_words}”里最具体的一点。",
            "why_it_works": "边界出口和当前对话绑定，不是空泛提醒。",
            "best_when": "对方犹豫、防御、沉默或话题变重时。",
        },
        {
            "label": "场景化表达版",
            "perspective": "用当前画面承接，而不是泛泛说我懂。",
            "response": f"我脑子里看到的是：{setting}。如果我是你，也会想先被轻轻听见，而不是马上被判断。",
            "why_it_works": "它让学习者看见同一句话为什么要在这个场景这样说。",
            "best_when": "需要训练画面感和具体共情时。",
        },
    ]


def build_response_steps(blueprint: dict[str, Any]) -> list[str]:
    return [
        "先复述 TA 的一句原话，不把它判成拒绝、冷淡或矫情。",
        "只提出一个可回答的小问题，让对方能继续也能停。",
        "把深层理解说成假设句，允许对方纠正。",
        "最后补一个边界出口：可以不答、晚点说或只说一部分。",
    ]


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
            content = render_content(row["content"] or "", repaired)
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


def render_content(content: str, blueprint: dict[str, Any]) -> str:
    if _is_case_matrix_blueprint(blueprint):
        dialogue = "；".join(f"{item['speaker']}：{item['line']}" for item in blueprint.get("dialogue_script") or [])
        return "\n".join(
            [
                f"案例定位：{blueprint.get('axis_label')} / {blueprint.get('resource_type_label')} / {blueprint.get('difficulty_contract')}",
                f"场景：{blueprint.get('setting')}；{blueprint.get('trigger')}",
                f"关系阶段：{blueprint.get('relation_stage')}",
                f"TA说：{blueprint.get('their_words')}",
                f"完整对话：{dialogue}",
                f"表层信号：{blueprint.get('surface_signal')}",
                f"深层可能：{blueprint.get('deeper_need')}",
                f"常见失误：{blueprint.get('common_mistake')}",
                f"为什么错：{blueprint.get('why_wrong')}",
                f"更好回应：{blueprint.get('better_response')}",
                "回应拆解：" + "；".join(str(item) for item in blueprint.get("response_steps") or []),
                f"边界提醒：{blueprint.get('boundary_note')}",
                f"练习任务：{blueprint.get('practice_task')}",
                f"迁移场景：{blueprint.get('transfer_scene')}",
                "变体差异：" + "；".join(str(item) for item in blueprint.get("variant_deltas") or []),
            ]
        )
    better = _text(blueprint.get("better_response"))
    if not better:
        return content
    return re.sub(r"更好回应[：:].*", f"更好回应：{better}", content)


def _is_case_matrix_blueprint(blueprint: dict[str, Any]) -> bool:
    return bool(blueprint.get("axis") and blueprint.get("resource_type_label") and blueprint.get("difficulty_contract"))


def _extract_bad_response(common_mistake: str) -> str:
    match = re.search(r"旧回应通常会说[：:](.+)$", common_mistake)
    if match:
        return match.group(1).strip()
    return common_mistake or "你到底什么意思？别让我猜。"


def _likely_reply(blueprint: dict[str, Any]) -> str:
    scene = str(blueprint.get("scene") or "")
    if scene == "亲密推进":
        return "嗯，我是喜欢的，只是一下子太快会有点慌。"
    if scene in {"冲突", "修复"}:
        return "我不是不想聊，只是怕又变成争谁对谁错。"
    if scene == "压力支持":
        return "我现在脑子很乱，可能只能说一点点。"
    return "我也不是不想说，就是怕说出来会有点奇怪。"


def _follow_up_response(blueprint: dict[str, Any]) -> str:
    their_words = _quote_text(blueprint.get("their_words")) or "这句话"
    return f"那我们就只从一个小地方开始：你说“{their_words}”的时候，身体更像是放松、紧绷，还是想往后退一点？"


def _closing_response(blueprint: dict[str, Any]) -> str:
    transfer = _text(blueprint.get("transfer_scene")) or "晚一点"
    return f"谢谢你愿意说到这里。我们先停在这个程度就好，剩下的可以等到{transfer}再慢慢补。"


def _short_setting(blueprint: dict[str, Any]) -> str:
    setting = _text(blueprint.get("setting")) or "刚才那个片段"
    trigger = _text(blueprint.get("trigger"))
    text = f"{setting}，{trigger}" if trigger and trigger not in setting else setting
    return re.sub(r"[。！？.!?]+$", "", text)


def _text(value: Any) -> str:
    return str(value or "").strip()


def _quote_text(value: Any) -> str:
    return re.sub(r"[。！？.!?]+$", "", _text(value))


def main() -> None:
    parser = argparse.ArgumentParser(description="Repair better responses into direct contextual dialogue.")
    parser.add_argument("--db", type=Path, default=DB_PATH)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    print(json.dumps(repair_database(args.db, dry_run=args.dry_run), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
