"""Enrich expression tools with concrete learning blueprints."""

from __future__ import annotations

import argparse
import json
import sqlite3
from datetime import datetime
from pathlib import Path
from shutil import copy2
from typing import Any

from backend.database.connection import DB_PATH, create_db_and_tables

ENRICHMENT_VERSION = "expression_tool_enrichment_v1"

SCENE_CONTEXTS = {
    "初识": {
        "story": "刚认识的人聊到周末安排，对方只说“还行吧”，语气礼貌但没有展开。",
        "their_words": "我周末一般就随便待着。",
        "bad": "那你也太无聊了吧。",
        "goal": "把表层寒暄带到低压力分享。",
    },
    "暧昧": {
        "story": "对方回复慢了一些，又补了一句“刚才有点累”。",
        "their_words": "我刚才有点累，不是不想回。",
        "bad": "你是不是对我没兴趣了？",
        "goal": "承接情绪，同时保留轻松张力。",
    },
    "冲突": {
        "story": "你临时改了约定，对方只回“知道了”。",
        "their_words": "知道了。",
        "bad": "你别这样，我也不是故意的。",
        "goal": "承认影响，降低防御。",
    },
    "修复": {
        "story": "上次争执后，对方说自己还没完全缓过来。",
        "their_words": "我不是不想聊，只是还没缓过来。",
        "bad": "都过去了，你怎么还提？",
        "goal": "给出可靠下一步，不逼对方立刻原谅。",
    },
    "长期": {
        "story": "长期相处里，对方说最近总觉得两个人节奏不太一致。",
        "their_words": "我们最近好像总是错开。",
        "bad": "你想太多了吧。",
        "goal": "把抱怨改成可复盘的共同约定。",
    },
    "边界确认": {
        "story": "你想推进一次更私密的聊天，但不确定对方是否舒服。",
        "their_words": "这个话题我还不知道怎么说。",
        "bad": "这有什么不能说的？",
        "goal": "把选择权还给对方。",
    },
}


def _json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True)


def _loads(raw: str | None, fallback: Any) -> Any:
    if not raw:
        return fallback
    try:
        value = json.loads(raw)
    except json.JSONDecodeError:
        return fallback
    return value


def backup_database(db_path: Path = DB_PATH) -> Path:
    backup_dir = db_path.parent / "backups"
    backup_dir.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    backup_path = backup_dir / f"{db_path.stem}-before-expression-tool-enrichment-{timestamp}{db_path.suffix}"
    copy2(db_path, backup_path)
    return backup_path


def build_learning_blueprint(tool: sqlite3.Row) -> dict[str, Any]:
    scenes = _loads(tool["best_scenes_json"], []) or ["初识", "冲突", "修复"]
    micro_steps = _loads(tool["micro_steps_json"], [])
    risk_flags = _loads(tool["risk_flags_json"], [])
    name = str(tool["name"])
    formula = str(tool["formula"] or "")
    category = str(tool["category"] or "")
    description = str(tool["description"] or "")
    selected_scenes = list(dict.fromkeys([str(scene) for scene in scenes if str(scene).strip()]))[:3]
    if len(selected_scenes) < 3:
        for scene in ["初识", "暧昧", "冲突", "修复", "长期", "边界确认"]:
            if scene not in selected_scenes:
                selected_scenes.append(scene)
            if len(selected_scenes) >= 3:
                break
    return {
        "version": ENRICHMENT_VERSION,
        "definition": f"{name}不是一句固定话术，而是一种“{category}”工具：在具体情境里用 {formula or '事实、感受、边界、下一步'} 组织表达，让对方更容易理解你的意思。",
        "core_principles": [
            "先锚定当前场景和对方原话，再使用工具公式。",
            "工具服务于清晰、尊重和可退出，不服务于操控或压迫。",
            "同一工具在不同场景要换内容，不复读同一句。",
        ],
        "when_to_use": selected_scenes,
        "when_not_to_use": [
            "对方已经明确拒绝继续聊时。",
            "你只是想赢、想证明自己对时。",
            "你没有足够事实，只是在猜测对方动机时。",
        ],
        "risk_boundaries": risk_flags or ["保留退路", "不替对方做决定", "不连续追问"],
        "micro_steps": micro_steps or ["观察事实", "选择公式", "写一句旧回应", "改成可退出的新回应"],
        "dialogue_cases": [_case_for_scene(name, formula, scene) for scene in selected_scenes],
        "transfer_practice": [
            f"把{name}从“{selected_scenes[0]}”迁移到“{selected_scenes[-1]}”，只保留公式，不复读原句。",
            "写出一个低质量回应，再按工具公式改写成更好回应。",
            "检查新回应是否包含具体事实、感受/影响、边界出口和下一小步。",
        ],
        "quality_notes": {
            "source": "project_original_structured_learning_blueprint",
            "generated_at": datetime.now().isoformat(timespec="seconds"),
            "base_description": description,
        },
    }


def _case_for_scene(tool_name: str, formula: str, scene: str) -> dict[str, Any]:
    context = SCENE_CONTEXTS.get(scene) or SCENE_CONTEXTS["初识"]
    after = _better_response(tool_name, formula, context)
    return {
        "scene": scene,
        "story": context["story"],
        "their_words": context["their_words"],
        "low_quality_response": context["bad"],
        "better_response": after,
        "why_it_works": f"它把{tool_name}落到当前场景：先接住具体原话，再按“{formula or '事实 -> 感受 -> 边界 -> 下一步'}”组织，不让工具停留在名词解释。",
        "transfer_hint": f"换到相邻场景时，保留{tool_name}的顺序，但替换事实、感受和下一步。",
    }


def _better_response(tool_name: str, formula: str, context: dict[str, str]) -> str:
    if "对比" in tool_name:
        return f"之前我们聊这类话题会很快跳过；现在你说“{context['their_words']}”，我想先停一下听懂；我希望接下来只问一个小问题，不让你有压力。"
    if "场景" in tool_name:
        return f"我脑子里看到的是：{context['story'].rstrip('。')}。所以我先不下结论，只想确认你那一刻更像是累、失落，还是想被安慰？"
    if "情绪" in tool_name or "共情" in tool_name:
        return f"你说“{context['their_words']}”，我听起来有一点没被轻轻接住的感觉。我这样理解对吗？"
    if "边界" in tool_name or "请求" in tool_name or "拒绝" in tool_name:
        return f"我想继续听，但也尊重你的节奏。这个话题你可以只说愿意说的部分，也可以先停。"
    if "幽默" in tool_name or "调侃" in tool_name:
        return f"我先不把气氛弄重。听起来你今天的小电量只剩一点点了，我可以轻轻陪你聊，不追问。"
    if "道歉" in tool_name or "修复" in tool_name:
        return f"这件事对你有影响，我先承认这一点，不急着解释。下一步我会补一个确定安排，你可以决定要不要继续聊。"
    return f"我用“{tool_name}”整理一下：事实是你说“{context['their_words']}”；我听到的影响是{context['goal']}；下一步我只问一个低压力问题，你可以不答。"


def enrich_database(db_path: Path = DB_PATH, *, dry_run: bool = False) -> dict[str, Any]:
    if db_path == DB_PATH:
        create_db_and_tables()
    backup_path: Path | None = None
    if not dry_run:
        backup_path = backup_database(db_path)
    scanned = 0
    updated = 0
    with sqlite3.connect(db_path) as connection:
        connection.row_factory = sqlite3.Row
        rows = connection.execute(
            """
            SELECT *
            FROM expression_tools
            WHERE review_status = 'published'
            ORDER BY id
            """
        ).fetchall()
        for row in rows:
            scanned += 1
            blueprint = build_learning_blueprint(row)
            current = row["learning_blueprint_json"] if "learning_blueprint_json" in row.keys() else None
            if current == _json(blueprint):
                continue
            updated += 1
            if dry_run:
                continue
            connection.execute(
                """
                UPDATE expression_tools
                SET learning_blueprint_json = ?,
                    updated_at = ?
                WHERE id = ?
                """,
                (_json(blueprint), datetime.now().isoformat(), row["id"]),
            )
        if dry_run:
            connection.rollback()
        else:
            connection.commit()
    return {
        "dry_run": dry_run,
        "scanned": scanned,
        "updated": updated,
        "backup_path": str(backup_path) if backup_path else None,
        "version": ENRICHMENT_VERSION,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Enrich expression tools with learning blueprints.")
    parser.add_argument("--db", type=Path, default=DB_PATH)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    print(json.dumps(enrich_database(args.db, dry_run=args.dry_run), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
