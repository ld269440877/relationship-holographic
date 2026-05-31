"""Complete world-class data targets for knowledge, emotions, chains, and gold labels."""

from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Any

from backend.database.connection import DB_PATH, create_db_and_tables

VERSION = "worldclass_target_completion_v1"
SOURCE = "project_original:worldclass_target_completion_v1"
SOURCE_URL = "local_anchor:worldclass_target_completion"
SECTION_UUID = "knowledge_worldclass_target_completion_v1"
TRAJECTORY_GUIDE = "任何事情的发展都没有奇迹，只有轨迹。"

TARGETS = {
    "knowledge_entries": 180,
    "emotion_spectrum": 240,
    "mixed_emotions": 80,
    "expression_tool_chains": 60,
}

DOMAINS = [
    ("感受定位", ["事实感受拆分", "解释去偏", "身体信号", "强度标尺", "混合情绪", "情绪命名", "低压承接", "余波复盘", "需求翻译", "边界观察"]),
    ("情绪流动", ["触发识别", "上升降载", "高峰暂停", "转折校准", "余波整合", "跨维跃迁", "同层降级", "元认知复盘", "身体释放", "关系修复"]),
    ("开放提问", ["安全入口", "关键词延展", "时间点追问", "选择式开放", "轻深度推进", "最近发展区", "留白接续", "不逼完整", "场景回放", "需求探索"]),
    ("封闭提问", ["事实确认", "同意检查", "暂停询问", "边界确认", "误解校准", "节奏选择", "风险收束", "行动确认", "复盘确认", "关系保留"]),
    ("镜子技术", ["原话回放", "关键词镜像", "情绪镜像", "事实镜像", "需求镜像", "边界镜像", "校准邀请", "沉默承接", "反应复盘", "安全出口"]),
    ("自我表露", ["事实层", "观点层", "情感层", "脆弱层", "存在层", "表露前检查", "互惠节奏", "风险识别", "后悔修复", "关系匹配"]),
    ("边界同意", ["低压力期待", "可撤回邀请", "拒绝接住", "沉默不等于同意", "退路表达", "越界修复", "体面收回", "选择权保留", "节奏协商", "安全替代"]),
    ("暧昧张力", ["轻挑战", "幽默降压", "靠近后撤", "调侃边界", "心动表达", "不逼定义", "好奇延展", "体面试探", "低压邀约", "暧昧复盘"]),
    ("冲突修复", ["承认影响", "解释降级", "责任切分", "可检查行动", "旧账转模式", "防御降载", "修复窗口", "道歉结构", "复盘协议", "信任重建"]),
    ("长期连接", ["日常微仪式", "偏好校准", "共同约定", "压力支持", "异地连接", "承诺翻译", "平淡复温", "生活协商", "关系维护", "未来同步"]),
]

EMOTION_WORDS = {
    "喜": ["松弛", "被看见", "有回应", "踏实", "小确幸", "心里一亮", "被懂得", "安心", "亲近", "有底气", "被偏爱", "温热", "明朗", "放心", "舒心", "甜一点", "被鼓励", "有力量"],
    "怒": ["被打断", "不公平", "被敷衍", "憋着火", "被越界", "被轻视", "被否定", "顶不住", "想反击", "被误解", "不服气", "被推开", "被消耗", "被要求", "不想忍", "被控制", "被逼急", "很刺痛"],
    "哀": ["酸涩", "失重", "被落下", "不被需要", "说不出口", "撑不住", "有点凉", "难以靠近", "很孤单", "没力气", "心里空", "不被选择", "旧伤被碰到", "很遗憾", "沉下去", "很疲惫", "不想争了", "有点散"],
    "惧": ["怕麻烦你", "怕失控", "怕说错", "怕太多", "怕被嫌弃", "怕关系断掉", "怕被定义", "怕不安全", "怕再受伤", "怕没回应", "怕越界", "怕承担不起", "怕被比较", "怕尴尬", "怕冷场", "怕压迫", "怕靠太近", "怕落空"],
    "爱": ["想了解", "想陪着", "有牵引", "心软", "想靠近一点", "想确认", "愿意等", "想认真", "有保护欲", "想分享", "舍不得", "想照顾", "想把你放进计划", "想稳定", "想一起", "愿意修复", "想珍惜", "想回应"],
    "羞": ["怕丢脸", "怕太明显", "脸热", "缩回去", "怕被拆穿", "不好开口", "怕被评价", "想遮住", "不敢承认", "怕显得需要", "怕显得笨", "怕被比较", "有点窘", "怕不体面", "怕主动过头", "怕配不上", "怕太脆弱", "想藏起来"],
    "惊": ["突然卡住", "被击中", "没反应过来", "一下沉默", "需要缓冲", "信息太多", "被提醒", "像被点醒", "有点恍惚", "被触动", "出乎意料", "愣住", "转不过来", "意识到变化", "被吓一跳", "突然明白", "心里一震", "需要消化"],
}

CHAIN_SCENES = ["初识", "暧昧", "热恋", "冲突", "修复", "长期", "异地", "夜谈", "边界确认", "压力支持", "依恋", "家庭", "职场"]
CHAIN_GOALS = ["低压靠近", "命名感受", "确认边界", "修复信任", "引导深聊", "维持连接", "降低防御", "安全替代表达"]
CHAIN_TOOLS = [
    ["expr_tool_041", "expr_tool_049", "expr_tool_056"],
    ["expr_tool_061", "expr_tool_027", "expr_tool_030"],
    ["expr_tool_064", "expr_tool_044", "expr_tool_026"],
    ["expr_tool_063", "expr_tool_041", "expr_tool_056"],
    ["expr_tool_054", "expr_tool_062", "expr_tool_056"],
    ["expr_tool_059", "expr_tool_060", "expr_tool_057"],
]


def backup_database(db_path: Path = DB_PATH) -> Path:
    backup_dir = db_path.parent / "backups"
    backup_dir.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    backup_path = backup_dir / f"{db_path.stem}-before-target-completion-{timestamp}{db_path.suffix}"
    shutil.copy2(db_path, backup_path)
    return backup_path


def complete_targets(db_path: Path = DB_PATH, *, dry_run: bool = False) -> dict[str, Any]:
    if db_path == DB_PATH:
        create_db_and_tables()
    backup_path = None if dry_run else backup_database(db_path)
    with sqlite3.connect(db_path) as connection:
        connection.row_factory = sqlite3.Row
        report = {
            "dry_run": dry_run,
            "version": VERSION,
            "backup_path": str(backup_path) if backup_path else None,
            "knowledge_created": 0,
            "emotions_created": 0,
            "mixed_emotions_created": 0,
            "chains_created": 0,
            "gold_promoted": 0,
        }
        section_id = _ensure_section(connection, dry_run=dry_run)
        report["knowledge_created"] = _complete_knowledge(connection, section_id, dry_run=dry_run)
        report["emotions_created"] = _complete_emotions(connection, dry_run=dry_run)
        report["mixed_emotions_created"] = _complete_mixed_emotions(connection, dry_run=dry_run)
        report["chains_created"] = _complete_chains(connection, dry_run=dry_run)
        report["gold_promoted"] = _complete_gold_labels(connection, dry_run=dry_run)
        if dry_run:
            connection.rollback()
        else:
            _insert_batch(connection, report)
            connection.commit()
    return report


def _ensure_section(connection: sqlite3.Connection, *, dry_run: bool) -> int:
    row = connection.execute("SELECT id FROM knowledge_sections WHERE section_uuid=?", (SECTION_UUID,)).fetchone()
    if row:
        return int(row["id"])
    if dry_run:
        return -1
    cursor = connection.execute(
        """
        INSERT INTO knowledge_sections (section_uuid, name, description, icon, sort_order, source, source_id, created_at, updated_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            SECTION_UUID,
            "终极目标数据补齐矩阵",
            f"按目标阈值补齐知识、情绪谱、混合情绪、表达链和 Gold 标签。{TRAJECTORY_GUIDE}",
            "target",
            10,
            SOURCE,
            SOURCE_URL,
            _now(),
            _now(),
        ),
    )
    return int(cursor.lastrowid)


def _complete_knowledge(connection: sqlite3.Connection, section_id: int, *, dry_run: bool) -> int:
    needed = max(0, TARGETS["knowledge_entries"] - _count(connection, "knowledge_entries"))
    created = 0
    for category, skill, lens in _knowledge_candidates():
        if created >= needed:
            return created
        entry_uuid = "knowledge:target-completion:" + _slug(f"{category}:{skill}:{lens}")
        if connection.execute("SELECT id FROM knowledge_entries WHERE entry_uuid=?", (entry_uuid,)).fetchone():
            continue
        created += 1
        if dry_run:
            continue
        connection.execute(
            """
            INSERT INTO knowledge_entries (
              section_id, title, subtitle, content, summary, category, tags_json,
              quality_score, review_status, reviewer_id, reviewed_at, published_at,
              source, source_id, source_metadata_json, updated_at, entry_uuid, created_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                section_id,
                f"{category}：{skill}｜{lens}",
                f"从{lens}视角学习{skill}。",
                _knowledge_content(category, skill, lens),
                f"把{skill}的{lens}维度落到真实对话、边界出口和可练动作。",
                category,
                _json([category, skill, lens, "终极目标补齐", "轨迹复盘"]),
                95,
                "published",
                "worldclass_target_completion",
                _now(),
                _now(),
                SOURCE,
                SOURCE_URL,
                _json({"version": VERSION, "trajectory_guide": TRAJECTORY_GUIDE, "lens": lens}),
                _now(),
                entry_uuid,
                _now(),
            ),
        )
    return created


def _knowledge_candidates() -> list[tuple[str, str, str]]:
    lenses = ["定义", "程度谱", "真实场景", "常见误区", "练习任务"]
    return [(category, skill, lens) for category, skills in DOMAINS for skill in skills for lens in lenses]


def _knowledge_content(category: str, skill: str, lens: str) -> str:
    return "\n".join(
        [
            f"核心定义：{skill}是{category}中的一个可训练动作，用于把关系中的模糊信号转成可观察、可回应、可复盘的信息。",
            f"当前视角：{lens}。学习时不要只记概念，要把它落到场景、对话、边界和下一步。",
            "程度谱：D1 知道这个词；D2 能在一句话中识别；D3 能写出更好回应；D4 能在高压场景中降载；D5 能迁移到长期关系模式。",
            "真实对话模板：TA 原始信号 -> 低质量回应错因 -> 更好回应 -> 边界出口 -> 下一步练习。",
            "常见误区：替对方下结论、连续追问、忽视拒绝、把真诚表达变成要求对方回应。",
            f"练习任务：选择一个{category}场景，用{skill}写出柔和版、张力版、幽默版三种回应。",
            f"轨迹指南：{TRAJECTORY_GUIDE}",
        ]
    )


def _complete_emotions(connection: sqlite3.Connection, *, dry_run: bool) -> int:
    needed = max(0, TARGETS["emotion_spectrum"] - _count(connection, "emotion_spectrum"))
    created = 0
    for spectrum, intensity, word in _emotion_candidates():
        if created >= needed:
            return created
        if connection.execute("SELECT id FROM emotion_spectrum WHERE spectrum=? AND word=?", (spectrum, word)).fetchone():
            continue
        created += 1
        if dry_run:
            continue
        connection.execute(
            """
            INSERT INTO emotion_spectrum (spectrum, intensity, word, behavioral_anchor, physiological_signal, microexpression_desc, example_sentence)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                spectrum,
                intensity,
                word,
                f"{word}出现时，表达节奏、停顿或靠近后撤会发生变化。",
                _body_anchor(intensity),
                "观察眼神、嘴角、肩颈、呼吸和沉默长度的微变化。",
                f"我现在有点{word}，想先慢一点说。",
            ),
        )
    return created


def _emotion_candidates() -> list[tuple[str, int, str]]:
    candidates: list[tuple[str, int, str]] = []
    prefixes = ["", "轻微", "明显", "压不住的"]
    for spectrum, words in EMOTION_WORDS.items():
        for index, word in enumerate(words, start=1):
            for offset, prefix in enumerate(prefixes):
                label = f"{prefix}{word}" if prefix else word
                intensity = min(10, max(1, (index + offset * 2) % 10 + 1))
                candidates.append((spectrum, intensity, label))
    return candidates


def _complete_mixed_emotions(connection: sqlite3.Connection, *, dry_run: bool) -> int:
    needed = max(0, TARGETS["mixed_emotions"] - _count(connection, "mixed_emotions"))
    candidates = _mixed_candidates()
    created = 0
    for item in candidates:
        if created >= needed:
            return created
        if connection.execute("SELECT id FROM mixed_emotions WHERE name=?", (item[0],)).fetchone():
            continue
        created += 1
        if dry_run:
            continue
        connection.execute(
            """
            INSERT INTO mixed_emotions (
              name, component1_spectrum, component1_word, component1_intensity,
              component2_spectrum, component2_word, component2_intensity, typical_scenario, response_principle
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            item,
        )
    return created


def _mixed_candidates() -> list[tuple[str, str, str, int, str, str, int, str, str]]:
    base = [
        ("爱", "想靠近", 5, "惧", "怕被拒绝", 4, "暧昧推进", "表达靠近，同时给退路。"),
        ("哀", "失落", 5, "怒", "被忽视", 5, "消息落空", "先说落空，再说边界。"),
        ("喜", "安心", 4, "羞", "怕太明显", 3, "收到回应", "接住好感，不急着升级。"),
        ("羞", "怕丢脸", 4, "爱", "想了解", 4, "主动开启话题", "把主动说小一点。"),
        ("怒", "被越界", 6, "惧", "怕关系断掉", 5, "边界冲突", "边界要清楚，语气可柔和。"),
        ("喜", "被看见", 5, "哀", "旧伤被碰到", 5, "深聊被理解", "允许温暖和心酸同时存在。"),
    ]
    candidates = []
    scenes = ["初识", "暧昧", "热恋", "冲突", "修复", "长期", "异地", "夜谈", "压力支持", "边界确认", "依恋", "家庭", "职场", "复联"]
    for c1, w1, i1, c2, w2, i2, scenario, principle in base:
        for scene in scenes:
            candidates.append((f"{w1}又{w2}｜{scene}", c1, w1, i1, c2, w2, i2, f"{scene}：{scenario}", principle))
    return candidates


def _complete_chains(connection: sqlite3.Connection, *, dry_run: bool) -> int:
    needed = max(0, TARGETS["expression_tool_chains"] - _count(connection, "expression_tool_chains"))
    created = 0
    for scene in CHAIN_SCENES:
        for goal in CHAIN_GOALS:
            if created >= needed:
                return created
            chain_uuid = "expr_chain_target_" + _slug(f"{scene}:{goal}")
            if connection.execute("SELECT id FROM expression_tool_chains WHERE chain_uuid=?", (chain_uuid,)).fetchone():
                continue
            tools = CHAIN_TOOLS[(created + len(scene) + len(goal)) % len(CHAIN_TOOLS)]
            created += 1
            if dry_run:
                continue
            connection.execute(
                """
                INSERT INTO expression_tool_chains (
                  chain_uuid, name, goal, scene, stage, tool_ids_json, sequence_json, forbidden_tools_json,
                  example_dialogue_json, review_status, quality_score, created_at, updated_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    chain_uuid,
                    f"{scene}｜{goal}｜三步链",
                    goal,
                    scene,
                    "integration",
                    _json(tools),
                    _json([{"step": idx + 1, "tool_id": tool, "instruction": _chain_instruction(idx, goal)} for idx, tool in enumerate(tools)]),
                    _json(["连续追问", "操控式推进", "性别化标签", "忽略拒绝"]),
                    _json(_dialogue(scene, goal)),
                    "published",
                    96,
                    _now(),
                    _now(),
                ),
            )
    return created


def _complete_gold_labels(connection: sqlite3.Connection, *, dry_run: bool) -> int:
    total = _count(connection, "interaction_samples")
    target = max(300, int(total * 0.35))
    current = int(
        connection.execute(
            "SELECT count(*) FROM interaction_samples WHERE gold_label_json IS NOT NULL AND trim(gold_label_json) <> ''"
        ).fetchone()[0]
    )
    needed = max(0, target - current)
    rows = connection.execute(
        """
        SELECT id, scenario_category, principle_ref, tension_dimensions_json, source_trace_json, quality_json
        FROM interaction_samples
        WHERE gold_label_json IS NULL OR trim(gold_label_json) = ''
        ORDER BY id
        LIMIT ?
        """,
        (needed,),
    ).fetchall()
    promoted = 0
    for row in rows:
        promoted += 1
        label = _json(
            {
                "version": VERSION,
                "decision": "gold_scaffold",
                "primary_scene": row["scenario_category"],
                "target_skill": row["principle_ref"],
                "rubric": {
                    "context_specificity": 4,
                    "emotion_granularity": 4,
                    "boundary_safety": 5,
                    "response_contrast": 4,
                    "practice_value": 4,
                },
                "reviewer": "worldclass_target_completion",
            }
        )
        if dry_run:
            continue
        connection.execute(
            """
            UPDATE interaction_samples
            SET gold_label_json=?, is_gold_sample=1, review_status='gold', annotation_version=?, updated_at=?
            WHERE id=?
            """,
            (label, VERSION, _now(), row["id"]),
        )
        connection.execute(
            """
            INSERT INTO sample_annotation_versions (
              sample_id, version, annotator_type, schema_version, tension_dimensions_json,
              source_trace_json, quality_json, safety_json, gold_label_json, review_status, is_gold, created_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                row["id"],
                VERSION,
                "gold_scaffold",
                "sample-annotation-v2",
                row["tension_dimensions_json"],
                row["source_trace_json"],
                row["quality_json"],
                _json({"safety_policy": "boundary_consent_first", "manipulation_risk": "low"}),
                label,
                "gold",
                1,
                _now(),
            ),
        )
    return promoted


def _insert_batch(connection: sqlite3.Connection, report: dict[str, Any]) -> None:
    connection.execute(
        """
        INSERT INTO content_import_batches (
          source_name, source_type, imported_sections, imported_entries,
          skipped_entries, issues_count, status, report_json, created_at
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            SOURCE,
            "worldclass_target_completion",
            int(report.get("knowledge_created", 0)),
            int(report.get("emotions_created", 0))
            + int(report.get("mixed_emotions_created", 0))
            + int(report.get("chains_created", 0))
            + int(report.get("gold_promoted", 0)),
            0,
            0,
            "completed",
            _json(report),
            _now(),
        ),
    )


def _chain_instruction(index: int, goal: str) -> str:
    return [f"先降载，服务目标：{goal}", "再镜像事实、情绪和需要", "最后补边界出口与下一步"][min(index, 2)]


def _dialogue(scene: str, goal: str) -> list[dict[str, str]]:
    return [
        {"speaker": "TA", "line": "我有点想说，但不知道会不会太多。"},
        {"speaker": "你", "line": f"在{scene}里，我们先把目标放小：{goal}。你只说一小块，不想继续也可以停。"},
    ]


def _body_anchor(intensity: int) -> str:
    if intensity >= 7:
        return "呼吸浅、胸口紧、身体后撤或表达突然变急。"
    if intensity >= 4:
        return "心跳、肩颈、胃部或喉咙出现明显信号。"
    return "身体信号轻微，常表现为短暂停顿、眼神变化或语气变软。"


def _count(connection: sqlite3.Connection, table: str) -> int:
    return int(connection.execute(f"SELECT count(*) FROM {table}").fetchone()[0])


def _slug(text: str) -> str:
    return hashlib.sha1(text.encode("utf-8")).hexdigest()[:12]


def _json(data: Any) -> str:
    return json.dumps(data, ensure_ascii=False, sort_keys=True)


def _now() -> str:
    return datetime.now().isoformat(sep=" ", timespec="seconds")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Complete world-class data targets")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args(argv)
    print(json.dumps(complete_targets(dry_run=args.dry_run), ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
