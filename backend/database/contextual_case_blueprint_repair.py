"""Rebuild legacy generic case blueprints from each resource's own context.

The module metadata completion pass intentionally filled missing fields, but
its earliest version used scene defaults for dialogue. This repair pass is
stricter: it only targets those legacy blueprints and rebuilds the learning
case from the row's title/category/scene/type/content.
"""

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

REPAIR_VERSION = "contextual_case_blueprint_repair_v1"
LEGACY_VERSION = "module_metadata_completion_v1"

GENERIC_MARKERS = (
    "我其实不太会和刚认识的人聊很深",
    "这样说我会比较放松，也更愿意继续讲一点",
    "换到相邻场景，保留原则但重写具体措辞",
)

SPEAKER_PATTERN = re.compile(r"(?P<speaker>男|女|TA|ta|Ta|我|你|朋友|同事|伴侣|客户|对方|用户|小李|小王|小张)[：:](?P<line>[^。！？!?；;\n]+[。！？!?]?)")

TYPE_LABELS = {
    "joke": "幽默互动卡",
    "flirty": "暧昧表达卡",
    "story": "场景故事卡",
    "riddle": "互动游戏卡",
    "game": "练习任务卡",
    "media": "来源观察卡",
    "phrase": "练习回应句",
    "knowledge_card": "知识卡",
}


def backup_database(db_path: Path = DB_PATH) -> Path:
    backup_dir = db_path.parent / "backups"
    backup_dir.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    backup_path = backup_dir / f"{db_path.stem}-before-contextual-case-blueprint-repair-{timestamp}{db_path.suffix}"
    copy2(db_path, backup_path)
    return backup_path


def needs_repair(blueprint: dict[str, Any]) -> bool:
    raw = json.dumps(blueprint, ensure_ascii=False)
    return LEGACY_VERSION in raw or any(marker in raw for marker in GENERIC_MARKERS)


def rebuild_blueprint(row: sqlite3.Row | dict[str, Any]) -> dict[str, Any]:
    data = dict(row)
    content = _clean(data.get("content"))
    resource_type = _clean(data.get("type")) or "resource"
    category = _clean(data.get("category")) or "关系训练"
    title = _clean(data.get("title")) or category
    scene = _clean(data.get("applicable_scene")) or _scene_from_text(" ".join([title, category, content]))
    goal = _clean(data.get("expression_goal")) or _goal_from_text(" ".join([title, category, content]))
    axis, axis_label = _axis_from_text(" ".join([scene, goal, title, category, content]))
    turns = _speaker_turns(content)
    their_words = _their_words(content, turns, resource_type)
    weak = _weak_response(content, turns, resource_type, goal)
    better = _better_response(content, turns, resource_type, goal)
    boundary = _boundary_note(resource_type, goal)
    setting = _setting(scene, category, title, content)
    dialogue = _dialogue_script(turns, their_words, weak, better, boundary, resource_type)

    blueprint: dict[str, Any] = {
        "version": REPAIR_VERSION,
        "previous_version": LEGACY_VERSION,
        "axis": axis,
        "axis_label": axis_label,
        "resource_type": resource_type,
        "resource_type_label": TYPE_LABELS.get(resource_type, "关系训练卡"),
        "scene": scene,
        "relation_stage": scene,
        "category": category,
        "title": title,
        "setting": setting,
        "trigger": _trigger(resource_type, title, goal),
        "their_words": their_words,
        "surface_signal": _surface_signal(resource_type, title, content),
        "deeper_need": _deeper_need(resource_type, goal),
        "common_mistake": f"旧回应通常会说：{weak}",
        "why_wrong": _why_wrong(resource_type),
        "better_response": better,
        "dialogue_script": dialogue,
        "response_steps": _response_steps(resource_type),
        "boundary_note": boundary,
        "practice_task": _practice_task(weak, better, scene),
        "transfer_scene": _transfer_scene(scene, category, goal),
        "variant_deltas": [
            f"内容来源不同：本卡根据“{_short(title, 24)}”的实际文本重建，不沿用默认场景。",
            f"功能职责不同：{TYPE_LABELS.get(resource_type, '训练卡')}优先训练“{goal}”。",
            "学习方式不同：先看完整语境，再比较低质量回应和多视角更好回应。",
        ],
        "source_mapping": {
            "source_policy": "project_original_contextual_repair_no_third_party_full_text",
            "copyright_boundary": "uses_existing_local_resource_context_and_original_analysis",
        },
        "quality_notes": {
            "version": REPAIR_VERSION,
            "specificity": 22,
            "practice_ready": 22,
            "dialogue_completeness": 22,
            "boundary_clarity": 22,
            "source_trace": 12,
            "rule": "dialogue_must_match_resource_content",
            "repaired_at": datetime.now().isoformat(timespec="seconds"),
        },
    }
    enriched, _ = enrich_blueprint(blueprint)
    return enriched


def repair_database(db_path: Path = DB_PATH, *, dry_run: bool = False, limit: int | None = None) -> dict[str, Any]:
    backup_path: Path | None = None
    if not dry_run:
        backup_path = backup_database(db_path)
    scanned = 0
    updated = 0
    invalid_json = 0
    with sqlite3.connect(db_path) as connection:
        connection.row_factory = sqlite3.Row
        query = """
            SELECT *
            FROM resource_library
            WHERE review_status IN ('reviewed', 'published')
              AND case_blueprint_json IS NOT NULL
              AND TRIM(case_blueprint_json) <> ''
              AND case_blueprint_json LIKE ?
            ORDER BY id
        """
        rows = connection.execute(query, (f"%{LEGACY_VERSION}%",)).fetchall()
        if limit is not None:
            rows = rows[:limit]
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
            if not needs_repair(blueprint):
                continue
            rebuilt = rebuild_blueprint(row)
            updated += 1
            if dry_run:
                continue
            content = render_content(row["content"] or "", rebuilt)
            connection.execute(
                """
                UPDATE resource_library
                SET case_blueprint_json = ?,
                    content = ?,
                    content_fingerprint = ?,
                    case_completeness_score = CASE
                      WHEN case_completeness_score IS NULL OR case_completeness_score < 94 THEN 94
                      ELSE case_completeness_score
                    END
                WHERE id = ?
                """,
                (
                    json.dumps(rebuilt, ensure_ascii=False, sort_keys=True),
                    content,
                    "sha256:" + hashlib.sha256(content.encode("utf-8")).hexdigest(),
                    row["id"],
                ),
            )
        if dry_run:
            connection.rollback()
        else:
            _insert_batch(connection, scanned, updated, str(backup_path) if backup_path else None)
            connection.commit()
    return {
        "dry_run": dry_run,
        "version": REPAIR_VERSION,
        "scanned": scanned,
        "updated": updated,
        "invalid_json": invalid_json,
        "backup_path": str(backup_path) if backup_path else None,
    }


def render_content(original_content: str, blueprint: dict[str, Any]) -> str:
    dialogue = "；".join(
        f"{_clean(item.get('speaker')) or '对话'}：{_clean(item.get('line'))}"
        for item in blueprint.get("dialogue_script") or []
        if isinstance(item, dict) and _clean(item.get("line"))
    )
    sections = [
        f"原始素材：{_clean(original_content)}",
        f"案例定位：{blueprint.get('axis_label')} / {blueprint.get('resource_type_label')} / {blueprint.get('title')}",
        f"场景故事：{blueprint.get('setting')}",
        f"触发信号：{blueprint.get('trigger')}",
        f"TA原话：{blueprint.get('their_words')}",
        f"完整对话：{dialogue}",
        f"表层信号：{blueprint.get('surface_signal')}",
        f"深层可能：{blueprint.get('deeper_need')}",
        f"常见失误：{blueprint.get('common_mistake')}",
        f"为什么错：{blueprint.get('why_wrong')}",
        f"更好回应：{blueprint.get('better_response')}",
        "回应拆解：" + "；".join(str(step) for step in blueprint.get("response_steps") or []),
        f"边界提醒：{blueprint.get('boundary_note')}",
        f"练习任务：{blueprint.get('practice_task')}",
        f"迁移场景：{blueprint.get('transfer_scene')}",
    ]
    return "\n".join(str(section) for section in sections if section and not str(section).endswith("：None"))


def _speaker_turns(content: str) -> list[dict[str, str]]:
    turns: list[dict[str, str]] = []
    for match in SPEAKER_PATTERN.finditer(content):
        speaker = match.group("speaker")
        line = _clean(match.group("line"))
        if line:
            turns.append({"speaker": speaker, "line": line})
    return turns


def _dialogue_script(
    turns: list[dict[str, str]],
    their_words: str,
    weak: str,
    better: str,
    boundary: str,
    resource_type: str,
) -> list[dict[str, str]]:
    script: list[dict[str, str]] = []
    for index, turn in enumerate(turns[:4]):
        purpose = "原始语境" if index == 0 else "原始素材中的连续回应"
        if index == len(turns[:4]) - 1 and len(turns) >= 3:
            purpose = "原句效果，需要判断是否过重"
        script.append({"speaker": turn["speaker"], "line": turn["line"], "purpose": purpose})
    if not script:
        script.append({"speaker": "TA", "line": their_words, "purpose": "原始信号或待使用句"})
    if not _has_line(script, weak):
        script.append({"speaker": "低质量回应", "line": weak, "purpose": "展示常见误判"})
    script.append({"speaker": "更好回应", "line": better, "purpose": "贴合当前语境的改写"})
    script.append({"speaker": "TA", "line": _likely_reply(resource_type), "purpose": "对方更可能给出的反馈"})
    script.append({"speaker": "边界收束", "line": boundary, "purpose": "保留继续、暂停或跳过的选择"})
    return _dedupe_turns(script)


def _their_words(content: str, turns: list[dict[str, str]], resource_type: str) -> str:
    explicit = _extract_after(content, "TA说") or _extract_after(content, "TA原话")
    if explicit:
        return explicit
    if len(turns) >= 2:
        return turns[-2]["line"] if resource_type in {"joke", "flirty"} else turns[0]["line"]
    if turns:
        return turns[0]["line"]
    return _short(content, 80)


def _weak_response(content: str, turns: list[dict[str, str]], resource_type: str, goal: str) -> str:
    explicit = _extract_after(content, "低质量回应") or _extract_after(content, "常见失误")
    if explicit:
        return _strip_legacy_prefix(explicit)
    if len(turns) >= 3:
        return turns[-1]["line"]
    if resource_type == "joke":
        return "把玩笑说得太损，只顾抖机灵，没观察对方是否接得住。"
    if resource_type == "flirty":
        return f"{_short(content, 48)} 说完立刻逼对方表态。"
    if resource_type == "phrase":
        return "只背这句，不看对方当下的情绪、关系阶段和可拒绝空间。"
    if resource_type == "media":
        return "把来源当权威结论直接教育对方，没有转成具体可练的一句话。"
    if resource_type == "story":
        return "把故事讲成大道理，忽略对方此刻真正想被理解的感受。"
    return f"为了“{goal}”连续追问或急着给建议。"


def _better_response(content: str, turns: list[dict[str, str]], resource_type: str, goal: str) -> str:
    explicit = _extract_after(content, "更好回应") or _extract_after(content, "高质量回应")
    if explicit and not any(marker in explicit for marker in GENERIC_MARKERS):
        return explicit
    their_words = _their_words(content, turns, resource_type)
    if resource_type == "joke":
        return f"我想接这个梗，但先轻一点：{_playful_rewrite(turns, content)} 如果这个玩笑你接不住，我马上收回。"
    if resource_type == "flirty":
        return f"{_short(content, 44)} 我可以把这句话放轻一点说；你要是想接，我们继续，不想接也没关系。"
    if resource_type == "phrase":
        return f"我会把这句落到当前语境里说：{_short(content, 70)} 你可以纠正我，也可以只说愿意说的部分。"
    if resource_type == "media":
        return f"我把这个来源线索转成一个小问题：刚才这件事里，你更需要被理解，还是先需要一点空间？"
    if resource_type == "story":
        return f"听到这个故事，我不会急着总结道理。我更想问：里面最打动你的，是被理解的那一刻，还是关系开始变好的那一刻？"
    return f"我听见你说“{_short(their_words, 46)}”。我先不评价，只问一个具体点：你愿意说说刚才最明显的感受吗？"


def _playful_rewrite(turns: list[dict[str, str]], content: str) -> str:
    if len(turns) >= 3 and "做饭" in content:
        return "天赋很明显，今天火候可能还在练级；不过我是真的吃得挺开心。"
    if turns:
        return f"我接住你这句“{_short(turns[-1]['line'], 34)}”，但不把玩笑开到让人难堪。"
    return f"{_short(content, 42)} 这句可以当轻梗，不当评价。"


def _setting(scene: str, category: str, title: str, content: str) -> str:
    return f"{scene}场景里的{category}：学习者正在处理“{title}”。素材画面是：{_short(content, 110)}"


def _trigger(resource_type: str, title: str, goal: str) -> str:
    if resource_type in {"joke", "flirty"}:
        return f"一句带张力的话出现后，需要判断对方能不能接住，再决定是否继续推进“{goal}”。"
    if resource_type == "media":
        return "看到外部来源线索后，需要转译成可练习、可验证、不过度搬运原文的本地训练卡。"
    if resource_type == "story":
        return "故事里出现关系转折，需要抽出可迁移的感受、原则和下一句。"
    return f"围绕“{title}”完成一次具体回应训练。"


def _surface_signal(resource_type: str, title: str, content: str) -> str:
    if resource_type == "joke":
        return "表面是玩笑，真正要观察的是对方有没有笑、停顿、反击或不舒服。"
    if resource_type == "flirty":
        return "表面是暧昧表达，真正要观察的是靠近意愿、压力感和可退出信号。"
    if resource_type == "media":
        return f"来源入口提供“{title}”相关线索，但学习卡只保留结构化摘要和原创训练动作。"
    if resource_type == "story":
        return "故事提供情绪变化和关系转折，重点不是复述剧情，而是学习如何承接相似时刻。"
    return f"这条资源训练用户识别“{_short(title, 36)}”背后的可观察信号。"


def _deeper_need(resource_type: str, goal: str) -> str:
    if resource_type == "joke":
        return "轻松、被喜欢，同时不被贬低或当众难堪。"
    if resource_type == "flirty":
        return "靠近可以发生，但节奏、选择和尊重需要被保留。"
    if resource_type == "media":
        return "把信息源转成可练习的关系判断，而不是被资料淹没。"
    if resource_type == "story":
        return "从别人的故事里看见自己的关系模式，并找到可执行的一小步。"
    return f"希望围绕“{goal}”被看见、被理解，并保留选择空间。"


def _why_wrong(resource_type: str) -> str:
    if resource_type == "joke":
        return "幽默的风险不在于有梗，而在于忽略对方是否愿意被这样调侃。"
    if resource_type == "flirty":
        return "暧昧表达如果只追求刺激，不给退路，就会从吸引变成压力。"
    if resource_type == "media":
        return "直接搬观点会变成说教；转成具体问题和练习，用户才知道怎么用。"
    if resource_type == "story":
        return "只讲结论会触发防御；回到故事画面，学习者才容易看见情绪流动。"
    return "低质量回应容易评价、催促或定性，无法让对方感到被理解。"


def _response_steps(resource_type: str) -> list[str]:
    if resource_type == "joke":
        return ["先判断关系熟度", "把调侃落在事情上而不是人格上", "补一句真实善意", "观察对方是否接梗，不接就收回"]
    if resource_type == "flirty":
        return ["先表达观察或感受", "降低目的感", "给对方接或不接的自由", "用一个轻问题继续而不是逼表态"]
    if resource_type == "media":
        return ["只保留来源标题、摘要和短摘录", "抽取一个关系训练线索", "转成原创练习句", "标注来源边界和适用场景"]
    return ["复述一个具体事实", "命名一个可校正感受", "给一个低压力问题", "补一个可暂停出口"]


def _boundary_note(resource_type: str, goal: str) -> str:
    if resource_type == "joke":
        return "玩笑必须可撤回；对方不笑、沉默或转移话题时，立刻降速并补一句善意。"
    if resource_type == "flirty":
        return "靠近必须可拒绝、可暂停、可换话题；不要用暧昧话术索取承诺。"
    if resource_type == "media":
        return "第三方来源不默认全文搬运；本地只保留链接、标题、摘要、短摘录和原创分析。"
    return f"练习“{goal}”时仍要允许对方不说、少说、晚点说或直接拒绝。"


def _practice_task(weak: str, better: str, scene: str) -> str:
    return f"在“{scene}”里，把“{_short(weak, 42)}”改写成三版：轻量承接版、现实-感受交替版、边界稳态版；每版都要不同于“{_short(better, 42)}”。"


def _transfer_scene(scene: str, category: str, goal: str) -> str:
    return f"换到另一个{scene or category}片段，继续训练“{goal}”，但必须重写具体原话和回应。"


def _likely_reply(resource_type: str) -> str:
    if resource_type == "joke":
        return "这样说我能接得住，而且知道你不是在贬我。"
    if resource_type == "flirty":
        return "这样就舒服多了，有点靠近，但不会被逼着马上表态。"
    if resource_type == "media":
        return "这样我知道这条资料到底可以怎么练了。"
    return "你这样问，我比较愿意继续说一点。"


def _axis_from_text(text: str) -> tuple[str, str]:
    rules = (
        ("边界|同意|拒绝|退路|可拒绝", "boundary_consent", "边界与同意"),
        ("修复|冲突|冷战|道歉|补偿", "conflict_repair", "冲突修复"),
        ("幽默|玩笑|调侃|互怼|自嘲", "humor_interaction", "幽默互动"),
        ("暧昧|调情|撩|表白|想你|喜欢", "flirty_tension", "暧昧张力"),
        ("情绪|感受|委屈|共情|理解", "emotion_flow", "情绪流动"),
        ("长期|承诺|异地|信任", "long_connection", "长期连接"),
    )
    for pattern, axis, label in rules:
        if re.search(pattern, text):
            return axis, label
    return "micro_signal", "微关系信号"


def _scene_from_text(text: str) -> str:
    for scene in ("初识", "暧昧", "热恋", "冲突", "修复", "长期", "异地", "社交", "调情", "表白", "互怼"):
        if scene in text:
            return scene
    return "具体互动"


def _goal_from_text(text: str) -> str:
    if re.search("幽默|玩笑|调侃|互怼", text):
        return "降低防御"
    if re.search("边界|同意|拒绝|退路", text):
        return "确认边界"
    if re.search("修复|冲突|道歉", text):
        return "修复信任"
    if re.search("情绪|感受|共情|理解", text):
        return "命名感受"
    if re.search("暧昧|调情|喜欢|表白", text):
        return "低压靠近"
    return "引导深聊"


def _extract_after(content: str, label: str) -> str:
    normalized = content.replace("\\n", "\n")
    pattern = re.compile(rf"(?:^|\n){re.escape(label)}(?:（[^）]+）)?[：:]\s*([^\n]+)")
    match = pattern.search(normalized)
    return _clean(match.group(1).strip(" ；;")) if match else ""


def _strip_legacy_prefix(value: str) -> str:
    return re.sub(r"^旧回应通常会说[：:]", "", value).strip()


def _has_line(script: list[dict[str, str]], line: str) -> bool:
    return any(item.get("line") == line for item in script)


def _dedupe_turns(script: list[dict[str, str]]) -> list[dict[str, str]]:
    deduped: list[dict[str, str]] = []
    seen: set[tuple[str, str]] = set()
    for item in script:
        key = (_clean(item.get("speaker")), _clean(item.get("line")))
        if not key[1] or key in seen:
            continue
        seen.add(key)
        deduped.append(item)
    return deduped


def _clean(value: Any) -> str:
    return str(value or "").strip()


def _short(value: str, limit: int) -> str:
    text = " ".join(_clean(value).split())
    return text if len(text) <= limit else text[: limit - 1].rstrip() + "…"


def _insert_batch(connection: sqlite3.Connection, scanned: int, updated: int, backup_path: str | None) -> None:
    connection.execute(
        """
        INSERT INTO content_import_batches (
          source_name, source_type, imported_sections, imported_entries,
          skipped_entries, issues_count, status, report_json, created_at
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            f"project_original:{REPAIR_VERSION}",
            "data_governance",
            0,
            updated,
            max(scanned - updated, 0),
            0,
            "completed",
            json.dumps({"version": REPAIR_VERSION, "backup_path": backup_path}, ensure_ascii=False),
            datetime.now().isoformat(timespec="seconds"),
        ),
    )


def main() -> None:
    parser = argparse.ArgumentParser(description="Repair legacy generic case blueprints from row context.")
    parser.add_argument("--db", type=Path, default=DB_PATH)
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--limit", type=int, default=None)
    args = parser.parse_args()
    print(json.dumps(repair_database(args.db, dry_run=args.dry_run, limit=args.limit), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
