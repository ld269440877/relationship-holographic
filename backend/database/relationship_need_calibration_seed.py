"""Seed relationship-need calibration materials from user-provided notes."""

from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import sqlite3
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any

from backend.database.connection import DB_PATH, create_db_and_tables

SOURCE = "user_provided:relationship_need_calibration_v1"
SOURCE_URL = "local_anchor:关系需求校准_性别刻板印象去偏"
SECTION_UUID = "knowledge_relationship_need_calibration_v1"
TOOL_UUID = "expr_tool_063"
CHAIN_UUID = "expr_chain_relationship_need_calibration_v1"

NEED_AXES = [
    {
        "key": "情绪承接",
        "scene": "暧昧",
        "need": "对方在关系里先要确认情绪是否被接住，而不是先听一套逻辑证明。",
        "signal": "她说“你讲得都对，但我还是觉得不舒服。”",
        "bad": "我不是已经解释清楚了吗？你怎么还不懂？",
        "better": "我先不急着证明谁对。听起来你不是缺解释，而是希望我知道这件事让你心里不舒服，对吗？",
        "risk": "只讲逻辑会让对方感到自己的感受被否定。",
    },
    {
        "key": "安全归属",
        "scene": "长期",
        "need": "安全感不是控制对方，而是用稳定行动、偏爱信号和可兑现承诺降低不确定。",
        "signal": "她说“我不是要你随时报备，只是临时变动太多我会很没底。”",
        "bad": "你就是不信任我，管太多了。",
        "better": "我听见的是没底，不是想控制我。以后行程有变我提前说一声；如果我忘了，你可以提醒我，我们一起把规则调轻一点。",
        "risk": "把安全需求误判为控制，会让关系进入防御。",
    },
    {
        "key": "价值认同",
        "scene": "压力支持",
        "need": "被需要、被认可、能共同成长，是很多亲密关系里的价值确认机制。",
        "signal": "她说“你什么都自己扛，好像我在你生活里没什么用。”",
        "bad": "我这是不想麻烦你，你还不满意？",
        "better": "我之前把独立做成了疏远。其实我也需要你，只是没说出来。这个方案你愿意帮我看一眼吗？",
        "risk": "长期不表达需要，会让对方的参与感和价值感下降。",
    },
    {
        "key": "能力感吸引",
        "scene": "初识",
        "need": "所谓“慕强”更专业地说，是对稳定、决策力、边界感和资源组织能力的吸引。",
        "signal": "她说“我喜欢有主见的人，但不喜欢被安排。”",
        "bad": "那你听我的就行，我来决定。",
        "better": "我可以拿主意，但不替你做主。我们先定两个选项，你选舒服的那个，我负责把细节安排好。",
        "risk": "把能力感做成控制欲，会从吸引变成压迫。",
    },
    {
        "key": "认同位置",
        "scene": "社交",
        "need": "人在关系中会在意自己是否被公开尊重、被放在合适位置、被重要他人认可。",
        "signal": "她说“你在朋友面前开那个玩笑，我知道你没恶意，但我挺尴尬的。”",
        "bad": "开个玩笑而已，大家都没当真。",
        "better": "我懂了，问题不是玩笑本身，而是你在那个场合被放到了不舒服的位置。下次我不拿你做梗，刚才这点我认。",
        "risk": "忽略公开场合的面子和位置，会让亲密感变成不安全。",
    },
]


def backup_database(db_path: Path = DB_PATH) -> Path:
    backup_dir = db_path.parent / "backups"
    backup_dir.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    backup_path = backup_dir / f"{db_path.stem}-before-relationship-need-calibration-{timestamp}{db_path.suffix}"
    shutil.copy2(db_path, backup_path)
    return backup_path


def seed(db_path: Path = DB_PATH, *, dry_run: bool = False) -> dict[str, Any]:
    if db_path == DB_PATH:
        create_db_and_tables()
    backup_path = None if dry_run else backup_database(db_path)
    with sqlite3.connect(db_path) as connection:
        connection.row_factory = sqlite3.Row
        report = {
            "dry_run": dry_run,
            "source": SOURCE,
            "created_sections": 0,
            "created_entries": 0,
            "updated_entries": 0,
            "created_tools": 0,
            "updated_tools": 0,
            "created_chains": 0,
            "updated_chains": 0,
            "created_resources": 0,
            "skipped_resources": 0,
            "backup_path": str(backup_path) if backup_path else None,
        }
        section_id, section_created = _upsert_section(connection, dry_run=dry_run)
        report["created_sections"] += int(section_created)
        created_entries, updated_entries = _upsert_entries(connection, section_id, dry_run=dry_run)
        report["created_entries"] += created_entries
        report["updated_entries"] += updated_entries
        tool_created, tool_updated = _upsert_tool(connection, dry_run=dry_run)
        report["created_tools"] += int(tool_created)
        report["updated_tools"] += int(tool_updated)
        chain_created, chain_updated = _upsert_chain(connection, dry_run=dry_run)
        report["created_chains"] += int(chain_created)
        report["updated_chains"] += int(chain_updated)
        created_resources, skipped_resources = _seed_resources(connection, dry_run=dry_run)
        report["created_resources"] += created_resources
        report["skipped_resources"] += skipped_resources
        if dry_run:
            connection.rollback()
        else:
            _insert_batch(connection, report)
            connection.commit()
    return report


def _upsert_section(connection: sqlite3.Connection, *, dry_run: bool) -> tuple[int, bool]:
    existing = connection.execute("SELECT id FROM knowledge_sections WHERE section_uuid=?", (SECTION_UUID,)).fetchone()
    if existing:
        return int(existing["id"]), False
    if dry_run:
        return -1, True
    cursor = connection.execute(
        """
        INSERT INTO knowledge_sections (
          section_uuid, name, description, icon, sort_order, source, source_id, created_at, updated_at
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            SECTION_UUID,
            "关系需求校准",
            "把情绪价值、安全感、归属、成长、能力感和认同位置转成可观察、可回应、可去偏的关系训练材料。",
            "🧩",
            37,
            SOURCE,
            SOURCE_URL,
            _now(),
            _now(),
        ),
    )
    return int(cursor.lastrowid), True


def _upsert_entries(connection: sqlite3.Connection, section_id: int, *, dry_run: bool) -> tuple[int, int]:
    entries = _knowledge_entries()
    created = 0
    updated = 0
    for item in entries:
        existing = connection.execute("SELECT id FROM knowledge_entries WHERE entry_uuid=?", (item["entry_uuid"],)).fetchone()
        if existing:
            updated += 1
            if not dry_run:
                connection.execute(
                    """
                    UPDATE knowledge_entries
                    SET section_id=?, title=?, subtitle=?, content=?, summary=?, category=?,
                        tags_json=?, quality_score=?, review_status=?, reviewer_id=?,
                        reviewed_at=?, published_at=?, source=?, source_id=?, source_metadata_json=?, updated_at=?
                    WHERE entry_uuid=?
                    """,
                    _entry_payload(section_id, item) + (item["entry_uuid"],),
                )
            continue
        created += 1
        if not dry_run:
            connection.execute(
                """
                INSERT INTO knowledge_entries (
                  section_id, title, subtitle, content, summary, category,
                  tags_json, quality_score, review_status, reviewer_id, reviewed_at,
                  published_at, source, source_id, source_metadata_json, updated_at,
                  entry_uuid, created_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                _entry_payload(section_id, item) + (item["entry_uuid"], _now()),
            )
    return created, updated


def _knowledge_entries() -> list[dict[str, Any]]:
    return [
        {
            "entry_uuid": "knowledge:relationship_need_calibration:v1",
            "title": "关系需求校准：从性别化判断到可观察需求",
            "category": "关系需求校准",
            "tags": ["关系需求校准", "情绪价值", "安全感", "归属感", "性别刻板印象去偏"],
            "summary": "把“女人的底层逻辑”这类粗糙说法改写成可观察的情绪、关系、安全、成长和认同需求。",
            "content": [
                "核心原则：不要把任何需求写成某个性别的固定本质。更专业的做法是看见当下的人、关系阶段和互动信号。",
                "可保留的信息：情绪承接、安全归属、价值认同、共同成长、能力感吸引、公开尊重和社交位置。",
                "去偏规则：把“她就是情绪化”改成“对方需要先被承接感受”；把“她慕强”改成“她被稳定、决策力和边界感吸引”。",
                "高风险标签处理：受虐、恋恶、认同癖等词不作为事实诊断，只能转译为未修复委屈、拯救幻想、能力吸引或认同位置需求。",
                "训练目标：用户要学会从信号 -> 需求假设 -> 轻验证 -> 具体行动，而不是从标签 -> 评价 -> 操控。",
            ],
        },
        {
            "entry_uuid": "knowledge:relationship_need_axes:v1",
            "title": "五类关系需求：情绪、安全、价值、能力、认同",
            "category": "关系需求校准",
            "tags": ["情绪承接", "安全感", "价值认同", "能力感", "认同位置"],
            "summary": "五类常见关系需求可以作为观察坐标，但每次都要回到具体语境校准。",
            "content": [
                "情绪承接：先让对方知道感受被看见，再讨论事实和方案。",
                "安全归属：用稳定行动、提前说明、可兑现承诺和偏爱信号降低不确定。",
                "价值认同：表达需要、求助、欣赏和共同成长，避免把独立做成疏远。",
                "能力感吸引：稳定、决策力、资源组织和边界感会带来吸引，但不能滑向控制。",
                "认同位置：公开场合的尊重、介绍、玩笑边界和社交位置会影响亲密安全感。",
            ],
        },
    ]


def _entry_payload(section_id: int, item: dict[str, Any]) -> tuple[Any, ...]:
    return (
        section_id,
        item["title"],
        item["summary"],
        "\n".join(item["content"]),
        item["summary"],
        item["category"],
        _json(item["tags"]),
        98,
        "published",
        "relationship_need_calibration_seed",
        _now(),
        _now(),
        SOURCE,
        SOURCE_URL,
        _json({"template_version": "relationship_need_calibration_v1", "source_policy": "user_provided_structured_material_non_essentialist_rewrite"}),
        _now(),
    )


def _upsert_tool(connection: sqlite3.Connection, *, dry_run: bool) -> tuple[bool, bool]:
    existing = connection.execute("SELECT id FROM expression_tools WHERE tool_uuid=?", (TOOL_UUID,)).fetchone()
    payload = _tool_payload()
    if dry_run:
        return (not bool(existing), bool(existing))
    if existing:
        connection.execute(
            """
            UPDATE expression_tools
            SET name=?, layer=?, category=?, formula=?, description=?, best_scenes_json=?,
                relationship_fit_json=?, emotion_fit_json=?, risk_flags_json=?,
                micro_steps_json=?, learning_blueprint_json=?, example_before=?,
                example_after=?, mastery_stage=?, source=?, source_url=?,
                review_status=?, quality_score=?, updated_at=?
            WHERE tool_uuid=?
            """,
            (*payload, TOOL_UUID),
        )
        return False, True
    connection.execute(
        """
        INSERT INTO expression_tools (
          tool_uuid, name, layer, category, formula, description, best_scenes_json,
          relationship_fit_json, emotion_fit_json, risk_flags_json, micro_steps_json,
          learning_blueprint_json, example_before, example_after, mastery_stage,
          source, source_url, review_status, quality_score, created_at, updated_at
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (TOOL_UUID, *payload, _now()),
    )
    return True, False


def _tool_payload() -> tuple[Any, ...]:
    return (
        "关系需求去偏校准",
        "relationship",
        "需求识别",
        "信号 -> 需求假设 -> 去偏改写 -> 轻验证 -> 具体行动",
        "把性别化、标签化判断转成可观察需求和可执行回应，避免本质化、诊断化和操控化。",
        _json(["初识", "暧昧", "长期", "社交", "压力支持", "修复"]),
        _json(["情绪流动", "边界同意", "长期连接", "深度情感连接"]),
        _json(["不安", "委屈", "被忽略", "被认可", "没底", "安心"]),
        _json(["性别本质论", "贴病理标签", "用强势压迫", "把安全感污名化为控制", "用技巧操控对方"]),
        _json(["提取原话信号", "命名可能需求", "去掉性别标签", "用轻验证确认", "给出可兑现小行动"]),
        _json(_tool_blueprint()),
        "女人就是情绪化，你顺着哄就行。",
        "我先不把这理解成情绪化。更像是她需要先确认感受被接住，再一起看事实和下一步。",
        "operation",
        SOURCE,
        SOURCE_URL,
        "published",
        99,
        _now(),
    )


def _tool_blueprint() -> dict[str, Any]:
    return {
        "concept": "关系需求去偏校准不是教用户给某个性别下结论，而是教用户把粗糙标签转译为可观察信号和可验证需求。",
        "need_axes": [{"axis": item["key"], "need": item["need"], "risk": item["risk"]} for item in NEED_AXES],
        "forbidden_labels": [
            {"label": "受虐癖", "rewrite": "未修复委屈、补偿期待或冲突闭环需求，需要边界和修复证据。"},
            {"label": "恋恶癖", "rewrite": "拯救幻想、成就感投射或熟悉的关系脚本，需要识别风险。"},
            {"label": "慕强癖", "rewrite": "对稳定、决策力、担当和边界感的吸引，不等于接受控制。"},
            {"label": "认同癖", "rewrite": "公开尊重、社交位置和被重要他人认可的需求。"},
        ],
        "practice_ladder": ["D1：从原话提取需求信号。", "D2：把标签改写成需求假设。", "D3：写出轻验证和可兑现行动。"],
    }


def _upsert_chain(connection: sqlite3.Connection, *, dry_run: bool) -> tuple[bool, bool]:
    existing = connection.execute("SELECT id FROM expression_tool_chains WHERE chain_uuid=?", (CHAIN_UUID,)).fetchone()
    payload = (
        "关系需求去偏回应链",
        "把粗糙性别判断转成具体理解和行动",
        "暧昧/长期/社交/压力支持/修复",
        "D1-D3 去偏校准",
        _json([TOOL_UUID, "expr_tool_061", "expr_tool_062"]),
        _json([
            {"order": 1, "tool": "关系需求去偏校准", "action": "从原话识别情绪、安全、价值、能力或认同需求。"},
            {"order": 2, "tool": "感受-期待-选择", "action": "表达理解和期待，但保留对方选择。"},
            {"order": 3, "tool": "自我表露深度校准", "action": "判断是否需要更深表露或先停在安全层。"},
        ]),
        _json(["女人都这样", "贴病理标签", "用强势测试服从", "把情绪承接做成哄骗", "以成长为名控制对方"]),
        _json({"before": "你们女生就是想太多。", "after": "我先不把它简化成想太多。你更像是需要我看见这件事给你的不安，对吗？"}),
        "published",
        99,
        _now(),
    )
    if dry_run:
        return (not bool(existing), bool(existing))
    if existing:
        connection.execute(
            """
            UPDATE expression_tool_chains
            SET name=?, goal=?, scene=?, stage=?, tool_ids_json=?, sequence_json=?,
                forbidden_tools_json=?, example_dialogue_json=?, review_status=?,
                quality_score=?, updated_at=?
            WHERE chain_uuid=?
            """,
            (*payload, CHAIN_UUID),
        )
        return False, True
    connection.execute(
        """
        INSERT INTO expression_tool_chains (
          chain_uuid, name, goal, scene, stage, tool_ids_json, sequence_json,
          forbidden_tools_json, example_dialogue_json, review_status, quality_score,
          created_at, updated_at
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (CHAIN_UUID, *payload, _now()),
    )
    return True, False


def _seed_resources(connection: sqlite3.Connection, *, dry_run: bool) -> tuple[int, int]:
    created = 0
    skipped = 0
    for axis in NEED_AXES:
        for difficulty in (1, 2, 3):
            resource = _resource_payload(axis, difficulty)
            existing = connection.execute(
                "SELECT id FROM resource_library WHERE resource_uuid=? OR content_unit=?",
                (resource["resource_uuid"], resource["content_unit"]),
            ).fetchone()
            if existing:
                skipped += 1
                continue
            created += 1
            if not dry_run:
                _insert_resource(connection, resource)
    return created, skipped


def _resource_payload(axis: dict[str, str], difficulty: int) -> dict[str, Any]:
    blueprint = _blueprint(axis, difficulty)
    content = _content(blueprint)
    content_unit = f"relationship_need_calibration::{axis['key']}::D{difficulty}"
    signature = "|".join([SOURCE, content_unit, blueprint["better_response"]])
    return {
        "resource_uuid": f"relationship-need-calibration:{uuid.uuid5(uuid.NAMESPACE_URL, signature)}",
        "type": "game",
        "category": "关系需求校准",
        "title": f"{axis['key']}｜关系需求校准｜D{difficulty}",
        "content": content,
        "emotional_tone_json": _json({"primary": axis["key"], "scene": axis["scene"], "debiased": True}),
        "emotional_intensity": 6,
        "applicable_scene": axis["scene"],
        "difficulty_level": difficulty,
        "gender_target": "通用",
        "attachment_suitability": "通用",
        "usage_tip": "先去掉性别标签，再回到具体原话、需求假设和可兑现行动。",
        "effectiveness_rating": 9,
        "source": SOURCE,
        "source_url": SOURCE_URL,
        "tags": ",".join(["关系需求校准", "情绪价值", "安全感", "归属感", "性别刻板印象去偏", axis["key"], f"difficulty:{difficulty}"]),
        "review_status": "published",
        "reviewer_id": "relationship_need_calibration_seed",
        "source_title": "关系需求校准与性别刻板印象去偏融合包",
        "source_excerpt": "用户提供观点转化为项目原创去偏训练卡，不保存第三方全文。",
        "source_summary": "围绕情绪承接、安全归属、价值认同、能力感吸引和认同位置，构建非本质化回应训练。",
        "source_license": "user_provided_structured_material",
        "quality_score": 98,
        "expression_tool_ids_json": _json([TOOL_UUID, "expr_tool_061"]),
        "expression_goal": "识别需求但不标签化",
        "expression_level": f"D{difficulty}",
        "speech_act": "需求镜像 / 去偏改写 / 轻验证",
        "mistake_pattern": blueprint["common_mistake"],
        "recommended_drills_json": _json([
            {"type": "signal", "prompt": "标出原话里可观察的需求信号。"},
            {"type": "de_bias", "prompt": "把一句性别化判断改写成需求假设。"},
            {"type": "action", "prompt": "写一个可兑现的小行动，不用宏大承诺。"},
        ]),
        "case_blueprint_json": _json(blueprint),
        "variant_signature": "sha256:" + _hash(signature),
        "content_unit": content_unit,
        "coverage_axis": "relationship_need_calibration",
        "variant_family": "relationship_need_calibration",
        "case_completeness_score": 100,
        "content_fingerprint": "sha256:" + _hash(content),
    }


def _blueprint(axis: dict[str, str], difficulty: int) -> dict[str, Any]:
    return {
        "version": "relationship_need_calibration_v1",
        "axis": "relationship_need_calibration",
        "axis_label": "关系需求校准",
        "scene": axis["scene"],
        "need_axis": axis["key"],
        "need": axis["need"],
        "their_words": axis["signal"],
        "common_mistake": f"把需求性别化或标签化；旧回应通常会说：{axis['bad']}",
        "why_wrong": axis["risk"],
        "better_response": axis["better"],
        "dialogue_script": _dialogue_script(axis, difficulty),
        "response_steps": [
            "提取原话信号：只写对方说了什么，不先解释人格。",
            "命名需求假设：情绪、安全、价值、能力或认同位置。",
            "去偏改写：删除“女人都/她就是/某某癖”等标签。",
            "轻验证：用“更像是…对吗”邀请对方纠正。",
            "具体行动：给一个可检查的小动作。",
        ],
        "de_bias_note": "这张卡讨论的是关系互动中的可观察需求，不把任何特征归因给所有女性或所有男性。",
        "practice_task": "把旧回应改成：信号复述 + 需求假设 + 轻验证 + 小行动。",
    }


def _dialogue_script(axis: dict[str, str], difficulty: int) -> list[dict[str, str]]:
    script = [
        {"speaker": "TA", "line": axis["signal"], "purpose": "原始需求信号"},
        {"speaker": "低质量回应", "line": axis["bad"], "purpose": "标签化或防御"},
        {"speaker": "更好回应", "line": axis["better"], "purpose": "去偏后校准需求"},
        {"speaker": "TA", "line": "你这样说我比较能听进去，因为不是在给我扣帽子。", "purpose": "防御降低"},
        {"speaker": "继续回应", "line": "如果我理解偏了你可以纠正我；我先做一件具体的小事，而不是要求你马上放心。", "purpose": "允许校准并落到行动"},
    ]
    return script[: 3 + difficulty]


def _content(blueprint: dict[str, Any]) -> str:
    dialogue = "；".join(f"{turn['speaker']}：{turn['line']}" for turn in blueprint["dialogue_script"])
    return "\n".join(
        [
            f"案例定位：{blueprint['axis_label']} / {blueprint['need_axis']} / {blueprint['scene']}",
            f"需求说明：{blueprint['need']}",
            f"TA说：{blueprint['their_words']}",
            f"完整对话：{dialogue}",
            f"常见失误：{blueprint['common_mistake']}",
            f"为什么错：{blueprint['why_wrong']}",
            f"更好回应：{blueprint['better_response']}",
            "五步拆解：" + "；".join(blueprint["response_steps"]),
            f"去偏提醒：{blueprint['de_bias_note']}",
            f"练习任务：{blueprint['practice_task']}",
        ]
    )


def _insert_resource(connection: sqlite3.Connection, resource: dict[str, Any]) -> None:
    now = _now()
    connection.execute(
        """
        INSERT INTO resource_library (
          resource_uuid, type, category, title, content, emotional_tone_json,
          emotional_intensity, applicable_scene, difficulty_level, gender_target,
          attachment_suitability, usage_tip, effectiveness_rating, source, source_url,
          tags, created_at, review_status, reviewer_id, reviewed_at, published_at,
          source_title, source_excerpt, source_summary, source_license, content_fingerprint,
          quality_score, expression_tool_ids_json, expression_goal, expression_level,
          speech_act, mistake_pattern, recommended_drills_json, case_blueprint_json,
          variant_signature, content_unit, coverage_axis, variant_family,
          case_completeness_score
        )
        VALUES (
          ?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?
        )
        """,
        (
            resource["resource_uuid"],
            resource["type"],
            resource["category"],
            resource["title"],
            resource["content"],
            resource["emotional_tone_json"],
            resource["emotional_intensity"],
            resource["applicable_scene"],
            resource["difficulty_level"],
            resource["gender_target"],
            resource["attachment_suitability"],
            resource["usage_tip"],
            resource["effectiveness_rating"],
            resource["source"],
            resource["source_url"],
            resource["tags"],
            now,
            resource["review_status"],
            resource["reviewer_id"],
            now,
            now,
            resource["source_title"],
            resource["source_excerpt"],
            resource["source_summary"],
            resource["source_license"],
            resource["content_fingerprint"],
            resource["quality_score"],
            resource["expression_tool_ids_json"],
            resource["expression_goal"],
            resource["expression_level"],
            resource["speech_act"],
            resource["mistake_pattern"],
            resource["recommended_drills_json"],
            resource["case_blueprint_json"],
            resource["variant_signature"],
            resource["content_unit"],
            resource["coverage_axis"],
            resource["variant_family"],
            resource["case_completeness_score"],
        ),
    )


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
            "user_provided_seed",
            int(report["created_sections"]),
            int(report["created_entries"]) + int(report["created_tools"]) + int(report["created_chains"]) + int(report["created_resources"]),
            int(report["skipped_resources"]),
            0,
            "completed",
            _json(report),
            _now(),
        ),
    )


def _json(data: Any) -> str:
    return json.dumps(data, ensure_ascii=False, sort_keys=True)


def _hash(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _now() -> str:
    return datetime.now().isoformat(timespec="seconds")


def main() -> None:
    parser = argparse.ArgumentParser(description="Seed relationship need calibration materials.")
    parser.add_argument("--db", type=Path, default=DB_PATH)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    print(_json(seed(args.db, dry_run=args.dry_run)))


if __name__ == "__main__":
    main()
