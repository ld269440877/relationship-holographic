"""Enrich resource case blueprints with concrete learning scaffolds.

The enrichment is project-original analysis derived from each row's existing
case blueprint. It does not fetch or store third-party full text.
"""

from __future__ import annotations

import argparse
import json
import sqlite3
from datetime import datetime
from pathlib import Path
from shutil import copy2
from typing import Any

from backend.database.connection import DB_PATH

ENRICHMENT_VERSION = "case_blueprint_enrichment_v1"


def _text(value: Any, fallback: str = "") -> str:
    if value is None:
        return fallback
    text = str(value).strip()
    return text or fallback


def _short(value: str, limit: int = 72) -> str:
    value = " ".join(value.split())
    if len(value) <= limit:
        return value
    return value[: limit - 1].rstrip() + "…"


def _sentence(value: str) -> str:
    return value.rstrip("。！？!?；;，, ")


def _append_missing(target: dict[str, Any], key: str, value: Any) -> None:
    if key not in target or target[key] in ("", None, [], {}):
        target[key] = value


def _base_context(blueprint: dict[str, Any]) -> dict[str, str]:
    axis = _text(blueprint.get("axis_label") or blueprint.get("axis"), "关系回应")
    setting = _text(blueprint.get("setting") or blueprint.get("scene"), "一个具体互动片段")
    their_words = _text(blueprint.get("their_words"), "我不知道该怎么说。")
    deeper_need = _text(blueprint.get("deeper_need"), "被看见、被尊重，并保留选择空间")
    better = _text(
        blueprint.get("better_response"),
        "我先听见你的感受，不急着判断。你愿意说一个最具体的细节吗？",
    )
    boundary = _text(
        blueprint.get("boundary_note"),
        "你可以只说愿意说的部分，也可以先停在这里。",
    )
    mistake = _text(
        blueprint.get("common_mistake"),
        "急着评价、建议或追问，让对方感觉自己又被审视了一次。",
    )
    transfer = _text(blueprint.get("transfer_scene"), "换到一个相邻真实场景再练一次。")
    return {
        "axis": axis,
        "setting": setting,
        "their_words": their_words,
        "deeper_need": deeper_need,
        "better": better,
        "boundary": boundary,
        "mistake": mistake,
        "transfer": transfer,
    }


def build_response_variants(blueprint: dict[str, Any]) -> list[dict[str, str]]:
    ctx = _base_context(blueprint)
    quoted_words = _short(ctx["their_words"], 36)
    setting = _short(ctx["setting"], 54)
    need = _short(ctx["deeper_need"], 46)
    return [
        {
            "label": "轻量承接版",
            "perspective": "先让对方感觉被听见，不立刻深入。",
            "response": f"我听见你说“{quoted_words}”。我先不急着评价，你愿意从一个最具体的小细节讲起吗？",
            "why_it_works": "它先接住原话，再把问题缩小到一个细节，降低被盘问感。",
            "best_when": "对方刚开口、能量低、还没有准备好深聊时。",
        },
        {
            "label": "现实-感受交替版",
            "perspective": "事实问题和感受问题交替，避免像审问，也避免空泛共情。",
            "response": f"当时具体发生了什么？你那一刻更像是委屈、累，还是有点失望？",
            "why_it_works": "先问可回答的现实，再给情绪选项，让对方更容易进入真实经验。",
            "best_when": "需要把聊天从表面信息带到情绪流动时。",
        },
        {
            "label": "深层共情版",
            "perspective": "尝试说出话语背后的关系需要，但保留校正空间。",
            "response": f"我猜这件事难受的地方不只是表面那句话，而是你希望{_sentence(need)}。我这样理解对吗？",
            "why_it_works": "它把深层需要作为假设，而不是替对方下结论。",
            "best_when": "对方已经说了几轮，愿意让你靠近一点理解时。",
        },
        {
            "label": "边界稳态版",
            "perspective": "把选择权还给对方，避免把深聊变成索取隐私。",
            "response": f"{ctx['boundary']} 如果继续聊，我们就只聊你现在最想被理解的一点。",
            "why_it_works": "先给退出权，再邀请继续，关系张力会更稳。",
            "best_when": "对方沉默、防御、话题变重或需要安全感时。",
        },
        {
            "label": "场景化表达版",
            "perspective": "用具体画面替代抽象结论，让共情更有落点。",
            "response": f"我脑子里有个画面：{setting}。如果我是你，可能也会有点乱，所以我想先听你说那一刻最明显的感受。",
            "why_it_works": "它让对方进入具体经验，而不是被灌输一个判断。",
            "best_when": "对方讲得很抽象、需要把话题落回真实片段时。",
        },
    ]


def build_perspective_examples(blueprint: dict[str, Any]) -> list[dict[str, str]]:
    ctx = _base_context(blueprint)
    return [
        {
            "label": "对方视角",
            "what_they_may_feel": f"我说“{_short(ctx['their_words'], 40)}”时，不一定是在要答案，也可能是在试探你会不会评判我。",
            "what_to_notice": "回复字数、停顿、是否继续补充细节、有没有转移话题。",
            "learning_point": "先证明你能安全地听，再决定是否推进深聊。",
        },
        {
            "label": "自己视角",
            "what_you_may_feel": "你可能急着证明自己有价值、很懂、能解决问题。",
            "what_to_notice": f"一旦想说“{_short(ctx['mistake'], 36)}”，先停一拍。",
            "learning_point": "把表现欲降噪，把注意力还给对方的真实经验。",
        },
        {
            "label": "关系视角",
            "what_is_happening": "这不是单句话术考试，而是在建立“我在你这里能不能安全表达”的关系证据。",
            "what_to_notice": "对方是否从简短回答变成主动补充、是否开始说感受而不只说事实。",
            "learning_point": "舒服感来自持续可预测的尊重，不来自一次完美回应。",
        },
        {
            "label": "边界视角",
            "what_must_stay_safe": ctx["boundary"],
            "what_to_notice": "对方含糊、沉默、笑着岔开、说“算了”时，都要允许暂停。",
            "learning_point": "让人愿意敞开，不等于让人必须交代完整故事。",
        },
    ]


def build_transfer_analysis(blueprint: dict[str, Any]) -> dict[str, Any]:
    ctx = _base_context(blueprint)
    return {
        "target_scene": ctx["transfer"],
        "stable_principles": [
            "先承接一个可观察信号，再提出一个低压力问题。",
            "现实层问题和感受层问题交替，不连续盘问。",
            "深层理解必须用“我猜/我理解得对吗”保留校正空间。",
            "任何推进都要保留跳过、暂停、晚点再说的出口。",
        ],
        "changeable_parameters": [
            "关系阶段：初识更轻，长期关系可以更具体。",
            "情绪强度：轻情绪问细节，强情绪先安抚和降速。",
            "场景媒介：文字要更短，面对面可加入停顿、眼神和身体朝向。",
            "目标动作：想靠近时问感受，想修复时先承认影响。",
        ],
        "self_check_questions": [
            "我有没有先看见对方，而不是急着展示自己？",
            "我的问题是否一现实一感受地交替，而不是连续审问？",
            "这句回应有没有给对方不说、少说、晚点说的自由？",
            "换到相邻场景时，我保留的是原则，还是只背了原句？",
        ],
    }


def build_misread_risks(blueprint: dict[str, Any]) -> list[dict[str, str]]:
    ctx = _base_context(blueprint)
    return [
        {
            "risk": "把沉默误读成冷淡",
            "correction": "沉默也可能是整理情绪、担心被评价或不知道从哪里说起。",
        },
        {
            "risk": "把提问做成审问",
            "correction": "每次只问一个问题，并用“可以不答”降低压力。",
        },
        {
            "risk": "把共情做成替对方下结论",
            "correction": "深层情绪反馈要用假设句，允许对方纠正你。",
        },
        {
            "risk": f"把技巧用于推进“{ctx['axis']}”而忽略边界",
            "correction": "所有技巧都要服务于安全、清晰和自愿，而不是操控对方继续聊。",
        },
    ]


def build_practice_ladder(blueprint: dict[str, Any]) -> list[dict[str, str]]:
    ctx = _base_context(blueprint)
    return [
        {
            "level": "D1 观察",
            "task": f"圈出“{_short(ctx['their_words'], 36)}”里一个现实信息和一个可能感受。",
            "pass_rule": "能说清楚哪些是事实，哪些只是你的假设。",
        },
        {
            "level": "D2 改写",
            "task": "把低质量回应改成一句轻量承接版，不加建议。",
            "pass_rule": "句子里同时有听见、低压力问题和可退出空间。",
        },
        {
            "level": "D3 迁移",
            "task": f"换到“{_short(ctx['transfer'], 42)}”，保留原则但重写具体内容。",
            "pass_rule": "新句子不是复读原句，且仍符合边界安全。",
        },
        {
            "level": "D4 复盘",
            "task": "写下对方可能出现的三种反馈，并分别准备停下、继续、修复的下一句。",
            "pass_rule": "能根据反馈调整，而不是把一套话术硬推到底。",
        },
    ]


def enrich_blueprint(blueprint: dict[str, Any]) -> tuple[dict[str, Any], bool]:
    before = json.dumps(blueprint, ensure_ascii=False, sort_keys=True)
    enriched = dict(blueprint)
    _append_missing(enriched, "response_variants", build_response_variants(enriched))
    _append_missing(enriched, "perspective_examples", build_perspective_examples(enriched))
    _append_missing(enriched, "transfer_analysis", build_transfer_analysis(enriched))
    _append_missing(enriched, "misread_risks", build_misread_risks(enriched))
    _append_missing(enriched, "practice_ladder", build_practice_ladder(enriched))
    _append_missing(
        enriched,
        "quality_notes",
        {
            "version": ENRICHMENT_VERSION,
            "copyright_boundary": "project_original_structured_analysis_no_third_party_full_text",
            "learning_floor": "必须包含具体场景、完整对话、多视角回应、迁移分析和边界出口。",
            "generated_at": datetime.now().isoformat(timespec="seconds"),
        },
    )
    after = json.dumps(enriched, ensure_ascii=False, sort_keys=True)
    return enriched, before != after


def backup_database(db_path: Path = DB_PATH) -> Path:
    backup_dir = db_path.parent / "backups"
    backup_dir.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    backup_path = backup_dir / f"{db_path.stem}-before-case-blueprint-enrichment-{timestamp}{db_path.suffix}"
    copy2(db_path, backup_path)
    return backup_path


def enrich_database(db_path: Path = DB_PATH, *, dry_run: bool = False, limit: int | None = None) -> dict[str, Any]:
    updated = 0
    scanned = 0
    invalid_json = 0
    backup_path: Path | None = None
    if not dry_run:
        backup_path = backup_database(db_path)
    with sqlite3.connect(db_path) as connection:
        connection.row_factory = sqlite3.Row
        rows = connection.execute(
            """
            SELECT id, case_blueprint_json
            FROM resource_library
            WHERE case_blueprint_json IS NOT NULL
              AND TRIM(case_blueprint_json) <> ''
            ORDER BY id
            """
        ).fetchall()
        for row in rows[:limit]:
            scanned += 1
            try:
                blueprint = json.loads(row["case_blueprint_json"])
            except json.JSONDecodeError:
                invalid_json += 1
                continue
            if not isinstance(blueprint, dict):
                invalid_json += 1
                continue
            enriched, changed = enrich_blueprint(blueprint)
            if not changed:
                continue
            updated += 1
            if not dry_run:
                connection.execute(
                    "UPDATE resource_library SET case_blueprint_json = ? WHERE id = ?",
                    (json.dumps(enriched, ensure_ascii=False, sort_keys=True), row["id"]),
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
        "version": ENRICHMENT_VERSION,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Enrich resource case blueprints.")
    parser.add_argument("--db", type=Path, default=DB_PATH)
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--limit", type=int, default=None)
    args = parser.parse_args()
    print(json.dumps(enrich_database(args.db, dry_run=args.dry_run, limit=args.limit), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
