"""Expand world-class relationship dynamics knowledge and material matrices."""

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

VERSION = "worldclass_material_matrix_expansion_v1"
SOURCE = "project_original:worldclass_material_matrix_expansion_v1"
SOURCE_URL = "local_anchor:worldclass_material_matrix"
TRAJECTORY_GUIDE = "任何事情的发展都没有奇迹，只有轨迹。"

SECTION_UUID = "knowledge_worldclass_material_matrix_v1"

SCENE_CANONICAL = {
    "冲突后破冰": "修复",
    "冲突场景": "冲突",
    "冲突解决": "修复",
    "初识或暧昧早期": "初识",
    "异地恋": "异地",
    "情侣日常": "长期",
    "表达想念": "长期",
    "破冰": "初识",
    "女撩男": "暧昧",
    "撩人": "暧昧",
    "玩笑越界": "边界确认",
    "睡前": "夜谈",
    "家务分工": "长期",
    "家庭话题": "家庭",
}

KNOWLEDGE_MATRIX = [
    ("感受定位", "事实-感受-解释三分法", "把发生了什么、我感觉什么、我解释成什么拆开，降低误判。", ["事实", "感受", "解释", "误判"]),
    ("感受定位", "身体信号词库", "用胸口紧、喉咙堵、胃悬着、肩颈硬等身体词辅助命名情绪。", ["身体", "情绪粒度", "微表情"]),
    ("感受定位", "轻中重强度标尺", "把情绪从有点、明显、快撑不住分级，帮助回应选择合适力度。", ["强度", "程度", "降载"]),
    ("感受定位", "混合情绪拆分", "允许又喜欢又害怕、心疼又生气、开心又心酸同时存在。", ["混合情绪", "矛盾感", "接纳"]),
    ("提问技术", "开放式问题入口", "用怎么、哪一刻、哪个部分、你愿意从哪说打开空间。", ["开放式提问", "低压探索", "选择权"]),
    ("提问技术", "封闭式问题边界", "用对吗、现在适合吗、要停一下吗确认事实与同意。", ["封闭式问题", "确认", "同意"]),
    ("提问技术", "追问密度控制", "连续三个问题会像审讯，提问后要有复述、留白和退路。", ["追问", "节奏", "留白"]),
    ("提问技术", "最近发展区提问", "问题只比对方当前表达深一小格，让对方够得着。", ["支架", "最近发展区", "发展性"]),
    ("镜子技术", "原话回放", "先把对方原词照回来，让他知道你听见的不是你的投射。", ["镜像", "关键词", "原话"]),
    ("镜子技术", "情绪猜测校准", "任何情绪猜测都要用可能、像是、接近吗，允许纠正。", ["校准", "不诊断", "可纠正"]),
    ("镜子技术", "事实情绪双层镜像", "一层说事实，一层说感受，避免把解释当真相。", ["事实层", "情绪层", "镜子"]),
    ("镜子技术", "边界出口镜像", "镜像之后补一句不想展开也可以停，避免深聊变逼供。", ["边界出口", "安全", "深聊"]),
    ("自我表露", "事实层表露", "分享公开事实和轻度偏好，适合初识与低安全场景。", ["自我表露", "事实层", "初识"]),
    ("自我表露", "观点层表露", "分享判断、偏好和价值排序，但先观察关系承接能力。", ["观点层", "价值观", "关系风险"]),
    ("自我表露", "情感层表露", "表达开心、失落、心动、不安等感受，需要低压回应。", ["情感层", "感受", "低压力"]),
    ("自我表露", "脆弱层表露", "涉及自卑、羞耻、创伤和重要失败，需要明确安全边界。", ["脆弱层", "羞耻", "安全"]),
    ("自我表露", "存在层表露", "涉及生命意义、终极恐惧和最深渴望，多数需要稳定关系或专业场域。", ["存在层", "深度", "稳定"]),
    ("边界同意", "低压力期待", "表达我希望，但不把希望包装成你必须。", ["期待", "选择", "不绑架"]),
    ("边界同意", "可撤回表达", "暧昧、玩笑、邀请都要有撤回空间，体面比推进更重要。", ["可撤回", "体面", "暧昧"]),
    ("边界同意", "拒绝后的修复", "听见拒绝后先承认，再收回压力，最后给关系保留句。", ["拒绝", "修复", "关系保留"]),
    ("边界同意", "沉默同意误区", "沉默不是同意，高压下的顺从也不是同意。", ["同意", "沉默", "安全"]),
    ("冲突修复", "承认影响", "先说我看到这件事影响到你，再解释原因。", ["影响", "承认", "修复"]),
    ("冲突修复", "解释降级", "解释只能降低误会，不能抵消对方已经受到的影响。", ["解释", "责任", "降级"]),
    ("冲突修复", "可检查行动", "修复要落到下一次可观察的小动作，而不是抽象保证。", ["行动", "承诺", "可检查"]),
    ("冲突修复", "旧账转模式", "不要反复判案，改成识别反复触发的关系模式。", ["旧账", "模式", "复盘"]),
    ("暧昧张力", "轻挑战安全线", "轻挑战要接住意图、保留体面，并允许对方不接。", ["轻挑战", "调侃", "体面"]),
    ("暧昧张力", "幽默降压", "幽默是降压和共同感，不是逃避真实议题。", ["幽默", "降压", "真实"]),
    ("暧昧张力", "靠近后撤节奏", "靠近一句后给对方选择，不连续推进。", ["靠近", "节奏", "选择"]),
    ("暧昧张力", "好玩与冒犯分界", "好玩让双方更轻松，冒犯让一方必须防御。", ["好玩", "冒犯", "边界"]),
    ("长期连接", "日常微仪式", "长期关系靠可重复的小连接维持温度。", ["微仪式", "长期", "稳定"]),
    ("长期连接", "偏好校准", "把抱怨改成偏好，把偏好改成可执行约定。", ["偏好", "共同约定", "复盘"]),
    ("长期连接", "压力支持", "支持不是立刻解决，而是先问要陪伴、建议还是实际帮忙。", ["支持", "压力", "选择"]),
    ("长期连接", "异地连接", "异地关系要区分安全确认、情绪陪伴和控制性报备。", ["异地", "连接", "报备"]),
    ("依恋信号", "焦虑型靠近", "焦虑信号常见于确认需求高、消息不回时反复追问。", ["焦虑型", "确认", "怕失去"]),
    ("依恋信号", "回避型撤退", "回避信号常见于压力升高时转移话题、沉默或说没事。", ["回避型", "撤退", "空间"]),
    ("依恋信号", "安全型协商", "安全型不是没有情绪，而是能同时表达需要和尊重边界。", ["安全型", "协商", "稳定"]),
    ("学习地图", "从识别到迁移", "D1识别概念，D2拆信号，D3改回应，D4处理高压，D5迁移到关系模式。", ["学习路径", "D1-D5", "迁移"]),
    ("学习地图", "轨迹复盘原则", TRAJECTORY_GUIDE, ["轨迹", "复盘", "项目指南"]),
]

FEELING_EXPANSION = [
    ("喜", 1, "安稳"), ("喜", 2, "舒展"), ("喜", 3, "被回应"), ("喜", 4, "有盼头"), ("喜", 6, "被珍视"), ("喜", 7, "很投缘"),
    ("怒", 1, "别扭"), ("怒", 2, "不被尊重"), ("怒", 3, "被忽视"), ("怒", 4, "委屈发火"), ("怒", 6, "被踩线"), ("怒", 7, "忍到顶点"),
    ("哀", 1, "空落"), ("哀", 2, "没被接住"), ("哀", 3, "低落"), ("哀", 4, "委屈"), ("哀", 6, "无力"), ("哀", 7, "心灰"),
    ("惧", 1, "有点慌"), ("惧", 2, "没底"), ("惧", 3, "怕打扰"), ("惧", 4, "怕被拒绝"), ("惧", 6, "怕关系变冷"), ("惧", 7, "不敢开口"),
    ("爱", 1, "有好奇"), ("爱", 2, "想靠近"), ("爱", 3, "被吸引"), ("爱", 4, "想保护"), ("爱", 6, "放在心上"), ("爱", 7, "难以割舍"),
    ("羞", 1, "怕尴尬"), ("羞", 2, "怕唐突"), ("羞", 3, "怕暴露"), ("羞", 4, "自我怀疑"), ("羞", 6, "怕不配"), ("羞", 7, "想躲起来"),
    ("惊", 1, "没想到"), ("惊", 2, "愣了一下"), ("惊", 3, "措手不及"), ("惊", 4, "需要确认"), ("惊", 6, "冲击很大"), ("惊", 7, "一时失语"),
]

MIXED_EXPANSION = [
    ("喜欢又怕唐突", "爱", "想靠近", 4, "羞", "怕唐突", 3, "暧昧初期表达好感", "先表达自己，再给对方退路。"),
    ("想靠近又怕失去", "爱", "想靠近", 5, "惧", "怕失去", 6, "关系不确定", "承接靠近愿望，同时降低确认压力。"),
    ("委屈发火", "哀", "委屈", 5, "怒", "被忽视", 5, "需求长期没被看见", "先看见落空，再讨论边界。"),
    ("被珍视又不好意思", "喜", "被珍视", 5, "羞", "怕暴露", 3, "收到具体赞美", "具体接住赞美，不用立刻反夸。"),
    ("轻松又警惕", "喜", "安稳", 3, "惧", "没底", 3, "初识关系变近", "承认舒服，也保留慢慢来。"),
    ("心动又没底", "爱", "心动", 6, "惧", "没底", 4, "暧昧升温", "低压表达，不逼定义。"),
    ("愧疚又防御", "羞", "惭愧", 5, "怒", "不被尊重", 4, "冲突后被追责", "先承认影响，再解释处境。"),
    ("想修复又害怕", "爱", "珍惜", 5, "惧", "怕被拒绝", 5, "争执后开口", "把修复请求做小，允许对方暂时不接。"),
    ("失望又还在乎", "哀", "失落", 6, "爱", "很在乎", 6, "长期关系降温", "不要把失望说成判决，说成仍想调整。"),
    ("释然又心酸", "喜", "松快", 4, "哀", "心酸", 5, "关系告一段落", "允许结束也有温度。"),
]

CHAIN_MATRIX = [
    ("开放提问到镜像校准链", "让对方愿意多说一点", "初识", ["expr_tool_041", "expr_tool_049", "expr_tool_056"]),
    ("感受期待选择链", "真诚表达但不绑架", "暧昧", ["expr_tool_061", "expr_tool_056", "expr_tool_019"]),
    ("自我表露深度校准链", "按关系安全度递进表露", "夜谈", ["expr_tool_062", "expr_tool_054", "expr_tool_056"]),
    ("冲突承认影响链", "从防御转向修复", "冲突", ["expr_tool_044", "expr_tool_041", "expr_tool_057"]),
    ("旧账模式复盘链", "把判案转成模式识别", "长期", ["expr_tool_026", "expr_tool_059", "expr_tool_060"]),
    ("异地低压连接链", "把报备变成连接而非控制", "异地", ["expr_tool_061", "expr_tool_059", "expr_tool_060"]),
    ("幽默边界修复链", "玩笑越界后的体面收回", "边界确认", ["expr_tool_016", "expr_tool_056", "expr_tool_057"]),
    ("压力支持选择链", "问清对方要陪伴还是建议", "压力支持", ["expr_tool_042", "expr_tool_027", "expr_tool_060"]),
    ("依恋去偏校准链", "把性别化判断改成可观察需求", "依恋", ["expr_tool_063", "expr_tool_041", "expr_tool_056"]),
    ("情绪跃迁支架链", "从高唤醒进入可复盘", "修复", ["expr_tool_064", "expr_tool_044", "expr_tool_026"]),
]

PLACEHOLDER_REPAIRS = [
    ("关系信号最低可用分析模板", "从一句话里提取事实、情绪、需求、边界和下一步。", "学习地图"),
    ("安全替代表达模板", "把操控、性别化判断或高压推进改写为尊重边界的表达。", "边界同意"),
    ("案例质量复核模板", "检查场景故事、完整对话、低质量回应、更好回应是否语境一致。", "数据治理"),
]


def backup_database(db_path: Path = DB_PATH) -> Path:
    backup_dir = db_path.parent / "backups"
    backup_dir.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    backup_path = backup_dir / f"{db_path.stem}-before-material-matrix-expansion-{timestamp}{db_path.suffix}"
    shutil.copy2(db_path, backup_path)
    return backup_path


def expand_database(db_path: Path = DB_PATH, *, dry_run: bool = False) -> dict[str, Any]:
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
            "knowledge_updated": 0,
            "placeholder_repaired": 0,
            "emotions_created": 0,
            "mixed_emotions_created": 0,
            "chains_created": 0,
            "chains_updated": 0,
            "resources_normalized": 0,
        }
        section_id = _ensure_section(connection, dry_run=dry_run)
        created, updated = _upsert_knowledge(connection, section_id, dry_run=dry_run)
        report["knowledge_created"] = created
        report["knowledge_updated"] = updated
        report["placeholder_repaired"] = _repair_placeholders(connection, section_id, dry_run=dry_run)
        report["emotions_created"], report["mixed_emotions_created"] = _expand_emotions(connection, dry_run=dry_run)
        report["chains_created"], report["chains_updated"] = _upsert_chains(connection, dry_run=dry_run)
        report["resources_normalized"] = _normalize_long_tail_scenes(connection, dry_run=dry_run)
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
            "世界级材料矩阵",
            f"面向感受、提问、镜像、边界、修复、暧昧张力和长期连接的结构化学习地图。{TRAJECTORY_GUIDE}",
            "matrix",
            9,
            SOURCE,
            SOURCE_URL,
            _now(),
            _now(),
        ),
    )
    return int(cursor.lastrowid)


def _upsert_knowledge(connection: sqlite3.Connection, section_id: int, *, dry_run: bool) -> tuple[int, int]:
    created = 0
    updated = 0
    for category, title, principle, tags in KNOWLEDGE_MATRIX:
        entry_uuid = "knowledge:material-matrix:" + _slug(f"{category}:{title}")
        content = _knowledge_content(category, title, principle, tags)
        payload = (
            section_id,
            title,
            principle,
            content,
            principle,
            category,
            _json([*tags, "世界级材料矩阵"]),
            96,
            "published",
            "worldclass_material_matrix_expansion",
            _now(),
            _now(),
            SOURCE,
            SOURCE_URL,
            _json({"version": VERSION, "trajectory_guide": TRAJECTORY_GUIDE}),
            _now(),
        )
        row = connection.execute("SELECT id FROM knowledge_entries WHERE entry_uuid=?", (entry_uuid,)).fetchone()
        if row:
            updated += 1
            if not dry_run:
                connection.execute(
                    """
                    UPDATE knowledge_entries
                    SET section_id=?, title=?, subtitle=?, content=?, summary=?, category=?, tags_json=?,
                        quality_score=?, review_status=?, reviewer_id=?, reviewed_at=?, published_at=?,
                        source=?, source_id=?, source_metadata_json=?, updated_at=?
                    WHERE entry_uuid=?
                    """,
                    (*payload, entry_uuid),
                )
        else:
            created += 1
            if not dry_run:
                connection.execute(
                    """
                    INSERT INTO knowledge_entries (
                      section_id, title, subtitle, content, summary, category, tags_json,
                      quality_score, review_status, reviewer_id, reviewed_at, published_at,
                      source, source_id, source_metadata_json, updated_at, entry_uuid, created_at
                    )
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (*payload, entry_uuid, _now()),
                )
    return created, updated


def _knowledge_content(category: str, title: str, principle: str, tags: list[str]) -> str:
    return "\n".join(
        [
            f"定位：{title}是{category}模块的关键训练材料，用来把抽象关系判断转成可观察、可练习、可迁移的动作。",
            f"核心原则：{principle}",
            f"关键词：{'、'.join(tags)}。",
            "五级学习：D1 识别概念；D2 从真实句子里标出信号；D3 写出柔和版、张力版、幽默版；D4 在冲突或高唤醒场景中降载；D5 迁移到长期关系模式。",
            "场景模板：先写场景故事，再写 TA 原始信号，再写低质量回应错因，再写更好回应与边界出口，最后补一个可练任务。",
            f"轨迹指南：{TRAJECTORY_GUIDE}",
        ]
    )


def _repair_placeholders(connection: sqlite3.Connection, section_id: int, *, dry_run: bool) -> int:
    rows = connection.execute(
        """
        SELECT id
        FROM knowledge_entries
        WHERE title LIKE '低分知识%' OR content='只有简短说明。' OR summary='简短说明。'
        ORDER BY id
        LIMIT ?
        """,
        (len(PLACEHOLDER_REPAIRS),),
    ).fetchall()
    repaired = 0
    for row, (title, principle, category) in zip(rows, PLACEHOLDER_REPAIRS, strict=False):
        repaired += 1
        if dry_run:
            continue
        connection.execute(
            """
            UPDATE knowledge_entries
            SET section_id=?, title=?, subtitle=?, content=?, summary=?, category=?,
                tags_json=?, quality_score=?, review_status=?, reviewer_id=?,
                reviewed_at=?, published_at=?, source=?, source_id=?, source_metadata_json=?, updated_at=?
            WHERE id=?
            """,
            (
                section_id,
                title,
                principle,
                _knowledge_content(category, title, principle, ["质量治理", "模板", "可复盘"]),
                principle,
                category,
                _json(["质量治理", "历史占位修复", "可复盘"]),
                93,
                "published",
                "worldclass_material_matrix_expansion",
                _now(),
                _now(),
                SOURCE,
                SOURCE_URL,
                _json({"version": VERSION, "repair": "placeholder_knowledge_rewrite"}),
                _now(),
                row["id"],
            ),
        )
    return repaired


def _expand_emotions(connection: sqlite3.Connection, *, dry_run: bool) -> tuple[int, int]:
    created = 0
    for spectrum, intensity, word in FEELING_EXPANSION:
        row = connection.execute("SELECT id FROM emotion_spectrum WHERE spectrum=? AND word=?", (spectrum, word)).fetchone()
        if row:
            continue
        created += 1
        if not dry_run:
            connection.execute(
                """
                INSERT INTO emotion_spectrum (spectrum, intensity, word, behavioral_anchor, physiological_signal, microexpression_desc, example_sentence)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    spectrum,
                    intensity,
                    word,
                    _behavioral_anchor(word, intensity),
                    _body_anchor(intensity),
                    "眼神、停顿、语速或姿态出现细微变化。",
                    f"我现在有点{word}，想先把这个感觉说清楚。",
                ),
            )
    mixed_created = 0
    for item in MIXED_EXPANSION:
        name = item[0]
        row = connection.execute("SELECT id FROM mixed_emotions WHERE name=?", (name,)).fetchone()
        if row:
            continue
        mixed_created += 1
        if not dry_run:
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
    return created, mixed_created


def _upsert_chains(connection: sqlite3.Connection, *, dry_run: bool) -> tuple[int, int]:
    created = 0
    updated = 0
    for name, goal, scene, tools in CHAIN_MATRIX:
        chain_uuid = "expr_chain_material_" + _slug(name)
        payload = (
            name,
            goal,
            scene,
            "integration",
            _json(tools),
            _json([{"step": index + 1, "tool_id": tool, "instruction": _chain_instruction(index)} for index, tool in enumerate(tools)]),
            _json(["高压推进", "性别化判断", "操控式确认", "把沉默当同意"]),
            _json(_chain_dialogue(scene, goal)),
            "published",
            97,
            _now(),
        )
        row = connection.execute("SELECT id FROM expression_tool_chains WHERE chain_uuid=?", (chain_uuid,)).fetchone()
        if row:
            updated += 1
            if not dry_run:
                connection.execute(
                    """
                    UPDATE expression_tool_chains
                    SET name=?, goal=?, scene=?, stage=?, tool_ids_json=?, sequence_json=?, forbidden_tools_json=?,
                        example_dialogue_json=?, review_status=?, quality_score=?, updated_at=?
                    WHERE chain_uuid=?
                    """,
                    (*payload, chain_uuid),
                )
        else:
            created += 1
            if not dry_run:
                connection.execute(
                    """
                    INSERT INTO expression_tool_chains (
                      chain_uuid, name, goal, scene, stage, tool_ids_json, sequence_json, forbidden_tools_json,
                      example_dialogue_json, review_status, quality_score, created_at, updated_at
                    )
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (chain_uuid, *payload[:-1], _now(), _now()),
                )
    return created, updated


def _normalize_long_tail_scenes(connection: sqlite3.Connection, *, dry_run: bool) -> int:
    rows = connection.execute(
        "SELECT id, applicable_scene FROM resource_library WHERE applicable_scene IN ({})".format(
            ",".join("?" for _ in SCENE_CANONICAL)
        ),
        tuple(SCENE_CANONICAL),
    ).fetchall()
    if not dry_run:
        for row in rows:
            connection.execute(
                "UPDATE resource_library SET applicable_scene=? WHERE id=?",
                (SCENE_CANONICAL[str(row["applicable_scene"])], row["id"]),
            )
    return len(rows)


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
            "worldclass_material_matrix",
            int(report.get("knowledge_created", 0)) + int(report.get("knowledge_updated", 0)),
            (
                int(report.get("emotions_created", 0))
                + int(report.get("mixed_emotions_created", 0))
                + int(report.get("chains_created", 0))
                + int(report.get("placeholder_repaired", 0))
                + int(report.get("resources_normalized", 0))
            ),
            0,
            0,
            "completed",
            _json(report),
            _now(),
        ),
    )


def _behavioral_anchor(word: str, intensity: int) -> str:
    if intensity >= 6:
        return f"{word}较明显，可能出现停顿、解释增多或靠近后撤。"
    if intensity >= 3:
        return f"{word}开始影响表达节奏，需要被轻轻命名。"
    return f"{word}处在低强度，适合用轻问和留白承接。"


def _body_anchor(intensity: int) -> str:
    if intensity >= 6:
        return "心跳、呼吸、胸口或胃部紧绷感明显。"
    if intensity >= 3:
        return "肩颈、喉咙、眼神或语速有可觉察变化。"
    return "身体信号轻微，通常只表现为短暂停顿或表情变化。"


def _chain_instruction(index: int) -> str:
    return ["先降载并命名", "再校准事实与感受", "最后给选择和下一步"][min(index, 2)]


def _chain_dialogue(scene: str, goal: str) -> list[dict[str, str]]:
    return [
        {"speaker": "TA", "line": "我不是不想说，只是有点不知道怎么开口。"},
        {"speaker": "你", "line": f"我们先不用急着讲完整。在{scene}里，我更想先做到：{goal}。你只说最安全的一小块就好。"},
    ]


def _slug(text: str) -> str:
    return hashlib.sha1(text.encode("utf-8")).hexdigest()[:12]


def _json(data: Any) -> str:
    return json.dumps(data, ensure_ascii=False, sort_keys=True)


def _now() -> str:
    return datetime.now().isoformat(sep=" ", timespec="seconds")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Expand world-class material matrices")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args(argv)
    print(json.dumps(expand_database(dry_run=args.dry_run), ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
