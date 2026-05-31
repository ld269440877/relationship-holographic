"""Seed deep-comfort chat resources.

This pack turns "ask details, alternate reality and feeling questions" into
project-original knowledge, expression chains, and practice cards.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sqlite3
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any

from backend.database.connection import DB_PATH, create_db_and_tables

SOURCE = "project_original:deep_comfort_chat_v1"
SOURCE_URL = "local_anchor:深度舒适聊天与现实感受交替提问标准流程"
DOC_PATH = Path(__file__).resolve().parents[2] / "docs" / "深度舒适聊天与现实感受交替提问标准流程.md"

CAPABILITIES: list[dict[str, Any]] = [
    {
        "key": "value_quieting",
        "name": "价值降噪",
        "concept": "暂时不急着展示自己的外在价值，把注意力还给对方的体验。",
        "principle": "让人回味的不是你多可图，而是他在你面前感到自己被看见。",
        "method": ["少自证", "少炫耀资源", "把话题还给对方细节", "用好奇替代表现"],
        "mistake": "把聊天变成自我推销，或用优秀感压住对方。",
        "tools": ["expr_tool_019", "expr_tool_042"],
        "tags": ["价值降噪", "舒适感", "深聊"],
    },
    {
        "key": "detail_question",
        "name": "问细节",
        "concept": "通过时间、地点、动作、选择和转折点进入对方的真实世界。",
        "principle": "细节会让对方感觉你在认真听，而不是只在收集标签。",
        "method": ["抓一个关键词", "问一个具体细节", "复述你听见的画面", "停下等对方展开"],
        "mistake": "只问职业、收入、家庭、资源等评估型问题。",
        "tools": ["expr_tool_011", "expr_tool_027", "expr_tool_019"],
        "tags": ["问细节", "关键词延展", "微关系信号"],
    },
    {
        "key": "reality_feeling_alternation",
        "name": "现实-感受交替提问",
        "concept": "现实层问题和感受层问题轮流出现，让理性叙述和情绪流动都有呼吸空间。",
        "principle": "只问现实像盘查，只问感受会太重；交替提问才舒服。",
        "method": ["先问现实事实", "再问当时感受", "回到后续行动", "再问轻一点的体验变化"],
        "mistake": "连续盘问现实信息，或连续逼对方交代感受。",
        "tools": ["expr_tool_027", "expr_tool_041", "expr_tool_019", "expr_tool_056"],
        "tags": ["现实感受交替", "提问结构", "深聊"],
    },
    {
        "key": "emotion_resonance",
        "name": "情绪共振",
        "concept": "先回应对方的感受强度，再处理事实内容。",
        "principle": "情绪先被接住，内容才愿意继续展开。",
        "method": ["捕捉情绪词", "用轻微画面化语言回应", "校准是否说中", "再问一个小问题"],
        "mistake": "对方说累，你直接分析原因或给方案。",
        "tools": ["expr_tool_041", "expr_tool_042", "expr_tool_050"],
        "tags": ["情绪共振", "共情", "情绪流动"],
    },
    {
        "key": "deep_emotion_feedback",
        "name": "深层情绪反馈",
        "concept": "尝试说出抱怨背后的孤独、挫败、期待或不被支持。",
        "principle": "深层反馈要温柔猜测，不能把猜测当诊断。",
        "method": ["听见表面抱怨", "猜一个更深感受", "加上不确定语气", "邀请对方修正"],
        "mistake": "机械说我懂你，或直接替对方下结论。",
        "tools": ["expr_tool_041", "expr_tool_042", "expr_tool_050"],
        "tags": ["深层情绪", "深度共情", "校准理解"],
    },
    {
        "key": "nonverbal_empathy",
        "name": "非语言共情",
        "concept": "用眼神、点头、身体前倾、语速和停顿传达专注。",
        "principle": "身体语言会决定同一句话是温柔还是压迫。",
        "method": ["短注视后移开", "轻点头", "身体微微前倾", "关键句后停顿"],
        "mistake": "凝视过久、身体逼近、用表演式反应制造压力。",
        "tools": ["expr_tool_035", "expr_tool_037", "expr_tool_019"],
        "tags": ["非语言", "身体语言", "舒适感"],
    },
]

SCENARIOS: list[dict[str, str]] = [
    {
        "key": "初识工作",
        "scene": "初识",
        "stage": "刚认识，正在从寒暄进入真实分享",
        "setting": "对方说自己最近换了岗位，但语气里既有兴奋也有疲惫。",
        "their_words": "我现在做运营，刚换岗没多久。",
        "keyword": "换岗",
        "bad": "你工资怎么样？有发展吗？",
        "better_question": "刚换过去的第一周，最让你觉得新鲜的是哪一件小事？那种新鲜感更多是兴奋，还是有点紧绷？",
        "need": "希望被当作一个有体验的人，而不是一份条件表。",
    },
    {
        "key": "暧昧兴趣",
        "scene": "暧昧",
        "stage": "互有好感，正在建立更舒服的靠近感",
        "setting": "对方说最近开始学摄影，语气轻松但明显愿意展开。",
        "their_words": "我最近在学摄影。",
        "keyword": "摄影",
        "bad": "你拍得好吗？花了多少钱？",
        "better_question": "你第一次觉得想把一个画面拍下来的时候，是因为它很好看，还是因为那一刻让你安静下来了？",
        "need": "希望自己的兴趣被细致看见，而不是被技术或消费评价。",
    },
    {
        "key": "朋友低落",
        "scene": "社交",
        "stage": "朋友分享低落和疲惫",
        "setting": "朋友下班后说今天很累，整个人像被抽空。",
        "their_words": "今天真的好累。",
        "keyword": "累",
        "bad": "早点睡吧，大家都累。",
        "better_question": "天呐，听起来像快被榨干了。今天最耗你的，是事情太多，还是一直没人能接住你？",
        "need": "希望疲惫被理解，而不是被普通化或打发。",
    },
    {
        "key": "伴侣挫败",
        "scene": "长期",
        "stage": "伴侣谈到关系里的无力感",
        "setting": "对方说自己想不出办法，对伴侣很挫败。",
        "their_words": "我真的想不出办法了，对他很挫败。",
        "keyword": "挫败",
        "bad": "那你就直接跟他说啊。",
        "better_question": "除了挫败，我好像还听见一点孤独：你是不是很希望他能主动看见你在撑？",
        "need": "希望深层孤独被看见，而不是只收到解决方案。",
    },
    {
        "key": "职场压力",
        "scene": "职场",
        "stage": "同事或朋友承受项目压力",
        "setting": "对方说项目又延期，自己已经不知道怎么推进。",
        "their_words": "项目又延期了，我有点扛不住。",
        "keyword": "扛不住",
        "bad": "你再坚持一下，职场都这样。",
        "better_question": "听起来不是单纯忙，是那种责任一直压在你身上的累。现在最卡的是任务本身，还是没人一起分担？",
        "need": "希望压力被看见，同时需要一个不被评判的整理空间。",
    },
]

DIFFICULTIES = {
    1: "D1：完成现实层一问和感受层一问。",
    2: "D2：加入关键词延展和情绪共振。",
    3: "D3：在对方沉默、防御或疲惫时保留边界出口。",
}


def _dumps(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True)


def _hash(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _now() -> str:
    return datetime.now().isoformat()


def seed(dry_run: bool = False) -> dict[str, Any]:
    create_db_and_tables()
    with sqlite3.connect(DB_PATH) as con:
        con.row_factory = sqlite3.Row
        result = {
            "dry_run": dry_run,
            "knowledge_entries_created": 0,
            "knowledge_entries_updated": 0,
            "chains_created": 0,
            "chains_updated": 0,
            "resources_created": 0,
            "resources_skipped": 0,
        }
        section_id = _upsert_section(con, dry_run)
        for capability in CAPABILITIES:
            created = _upsert_knowledge_entry(con, section_id, capability, dry_run)
            result["knowledge_entries_created" if created else "knowledge_entries_updated"] += 1
        for chain in _chain_specs():
            created = _upsert_chain(con, chain, dry_run)
            result["chains_created" if created else "chains_updated"] += 1
        for capability in CAPABILITIES:
            for scenario in SCENARIOS:
                for difficulty in DIFFICULTIES:
                    created = _insert_resource(con, capability, scenario, difficulty, dry_run)
                    result["resources_created" if created else "resources_skipped"] += 1
        if not dry_run:
            con.commit()
    return result


def _upsert_section(con: sqlite3.Connection, dry_run: bool) -> int:
    now = _now()
    section_uuid = "knowledge_deep_comfort_chat_v1"
    existing = con.execute("SELECT id FROM knowledge_sections WHERE section_uuid=?", (section_uuid,)).fetchone()
    payload = (
        "深度舒适聊天与现实感受交替提问",
        "把问细节、现实-感受交替、情绪共振、关键词延展和非语言共情组织成可练路径。",
        "🌊",
        13,
        SOURCE,
        SOURCE_URL,
        now,
        section_uuid,
    )
    if existing:
        if not dry_run:
            con.execute(
                """
                UPDATE knowledge_sections
                SET name=?, description=?, icon=?, sort_order=?, source=?, source_id=?, updated_at=?
                WHERE section_uuid=?
                """,
                payload,
            )
        return int(existing["id"])
    if dry_run:
        row = con.execute("SELECT max(id) AS max_id FROM knowledge_sections").fetchone()
        return int(row["max_id"] or 0) + 1
    cur = con.execute(
        """
        INSERT INTO knowledge_sections (
          name, description, icon, sort_order, source, source_id, updated_at, section_uuid, created_at
        ) VALUES (?,?,?,?,?,?,?,?,?)
        """,
        (*payload, now),
    )
    return int(cur.lastrowid)


def _upsert_knowledge_entry(
    con: sqlite3.Connection,
    section_id: int,
    capability: dict[str, Any],
    dry_run: bool,
) -> bool:
    now = _now()
    entry_uuid = f"knowledge:deep-comfort-chat:{capability['key']}"
    content = "\n".join(
        [
            f"定义：{capability['concept']}",
            f"核心原则：{capability['principle']}",
            "执行步骤：" + " -> ".join(capability["method"]),
            f"常见误区：{capability['mistake']}",
            "推荐工具：" + "、".join(capability["tools"]),
            "练习：选一个对方说过的关键词，写出一个现实层问题、一个感受层问题和一个可退出句。",
        ]
    )
    metadata = {
        "doc": str(DOC_PATH),
        "learning": {
            "concept": capability["concept"],
            "principle": capability["principle"],
            "method": capability["method"],
            "scene": "适用于初识、暧昧、朋友低落、伴侣复盘和职场压力等深聊场景。",
            "drill": "用“现实问题 -> 感受问题 -> 关键词延展 -> 边界出口”改写一次生硬追问。",
        },
        "tools": capability["tools"],
        "source_policy": "project_original_structured_analysis_no_third_party_fulltext",
    }
    payload = (
        section_id,
        f"深度舒适聊天：{capability['name']}",
        "让对方在被看见、被好奇、可退出的节奏里自然展开。",
        content,
        capability["concept"],
        "深度舒适聊天",
        _dumps([*capability["tags"], "现实感受交替", "情绪共鸣", "可退出"]),
        97,
        "published",
        "deep_comfort_chat_seed",
        now,
        now,
        SOURCE,
        SOURCE_URL,
        _dumps(metadata),
        now,
        entry_uuid,
    )
    existing = con.execute("SELECT id FROM knowledge_entries WHERE entry_uuid=?", (entry_uuid,)).fetchone()
    if existing:
        if not dry_run:
            con.execute(
                """
                UPDATE knowledge_entries
                SET section_id=?, title=?, subtitle=?, content=?, summary=?, category=?,
                    tags_json=?, quality_score=?, review_status=?, reviewer_id=?,
                    reviewed_at=?, published_at=?, source=?, source_id=?,
                    source_metadata_json=?, updated_at=?
                WHERE entry_uuid=?
                """,
                payload,
            )
        return False
    if not dry_run:
        con.execute(
            """
            INSERT INTO knowledge_entries (
              section_id, title, subtitle, content, summary, category, tags_json, quality_score,
              review_status, reviewer_id, reviewed_at, published_at, source, source_id,
              source_metadata_json, updated_at, entry_uuid, created_at
            ) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
            """,
            (*payload, now),
        )
    return True


def _chain_specs() -> list[dict[str, Any]]:
    return [
        {
            "chain_uuid": "expr_chain_reality_feeling_alternation_v1",
            "name": "现实感受交替深聊链",
            "goal": "引导深聊",
            "scene": "初识/暧昧/社交",
            "stage": "D2 舒适深聊",
            "tool_ids": ["expr_tool_027", "expr_tool_041", "expr_tool_042", "expr_tool_019", "expr_tool_056"],
            "sequence": ["请求结构", "情绪标注", "共情反射", "留白沉默", "边界声明"],
            "before": "你是做什么的？收入怎么样？以后想去哪？",
            "after": "你现在做哪一块？刚开始做这件事时，最明显的感受是兴奋，还是有点被推着走？不想聊工作也可以，我们换轻松点的。",
        },
        {
            "chain_uuid": "expr_chain_keyword_resonance_v1",
            "name": "关键词情绪延展链",
            "goal": "命名感受",
            "scene": "兴趣/社交/暧昧",
            "stage": "D2 关键词延展",
            "tool_ids": ["expr_tool_011", "expr_tool_041", "expr_tool_027", "expr_tool_019"],
            "sequence": ["场景化表达", "情绪标注", "请求结构", "留白沉默"],
            "before": "哦，摄影啊，挺好的。",
            "after": "摄影这个词很有画面感。你是因为喜欢记录，还是它刚好给了你一个能安静下来的出口？",
        },
        {
            "chain_uuid": "expr_chain_deep_emotion_feedback_v1",
            "name": "深层情绪反馈链",
            "goal": "降低防御",
            "scene": "低落/伴侣复盘/长期",
            "stage": "D3 深层校准",
            "tool_ids": ["expr_tool_041", "expr_tool_042", "expr_tool_050", "expr_tool_056"],
            "sequence": ["情绪标注", "共情反射", "承接再转向", "边界声明"],
            "before": "那你就直接解决啊。",
            "after": "除了挫败，我好像还听见一点孤独：你是不是很希望有人能主动看见你在撑？如果我理解错了你可以纠正我。",
        },
        {
            "chain_uuid": "expr_chain_nonverbal_comfort_v1",
            "name": "非语言舒适承接链",
            "goal": "保留退路",
            "scene": "线下约会/安抚/冲突后",
            "stage": "D2 身体降压",
            "tool_ids": ["expr_tool_035", "expr_tool_037", "expr_tool_019", "expr_tool_042"],
            "sequence": ["眼神注视", "开放姿态", "留白沉默", "共情反射"],
            "before": "一直盯着对方追问：你说啊。",
            "after": "短暂看着对方、放慢语速，轻轻说：我听见你刚才那句有点重。你不用马上讲完整，我在。",
        },
    ]


def _upsert_chain(con: sqlite3.Connection, chain: dict[str, Any], dry_run: bool) -> bool:
    now = _now()
    payload = (
        chain["name"],
        chain["goal"],
        chain["scene"],
        chain["stage"],
        _dumps(chain["tool_ids"]),
        _dumps([{"order": index + 1, "tool": tool} for index, tool in enumerate(chain["sequence"])]),
        _dumps(["连续盘查", "连续逼问感受", "虚假共情", "凝视压迫", "以深聊之名操控"]),
        _dumps({"before": chain["before"], "after": chain["after"]}),
        "published",
        97,
        now,
        chain["chain_uuid"],
    )
    existing = con.execute("SELECT id FROM expression_tool_chains WHERE chain_uuid=?", (chain["chain_uuid"],)).fetchone()
    if existing:
        if not dry_run:
            con.execute(
                """
                UPDATE expression_tool_chains
                SET name=?, goal=?, scene=?, stage=?, tool_ids_json=?, sequence_json=?,
                    forbidden_tools_json=?, example_dialogue_json=?, review_status=?,
                    quality_score=?, updated_at=?
                WHERE chain_uuid=?
                """,
                payload,
            )
        return False
    if not dry_run:
        con.execute(
            """
            INSERT INTO expression_tool_chains (
              name, goal, scene, stage, tool_ids_json, sequence_json, forbidden_tools_json,
              example_dialogue_json, review_status, quality_score, updated_at, chain_uuid, created_at
            ) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)
            """,
            (*payload, now),
        )
    return True


def _insert_resource(
    con: sqlite3.Connection,
    capability: dict[str, Any],
    scenario: dict[str, str],
    difficulty: int,
    dry_run: bool,
) -> bool:
    blueprint = _resource_blueprint(capability, scenario, difficulty)
    content = _resource_content(blueprint)
    signature = _hash("|".join([capability["key"], scenario["key"], str(difficulty), content]))
    resource_uuid = f"deep-comfort-chat:{uuid.uuid5(uuid.NAMESPACE_URL, signature)}"
    if con.execute("SELECT id FROM resource_library WHERE resource_uuid=?", (resource_uuid,)).fetchone():
        return False
    if dry_run:
        return True
    now = _now()
    con.execute(
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
        ) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
        """,
        (
            resource_uuid,
            "game",
            f"深度舒适聊天·{capability['name']}",
            f"{scenario['key']}｜{capability['name']}｜D{difficulty}",
            content,
            _dumps({"primary": capability["name"], "scene": scenario["scene"], "generator": SOURCE}),
            5 + difficulty,
            scenario["scene"],
            difficulty,
            "通用",
            "通用",
            "按现实-感受交替练习，问细节但不盘查，深挖但保留退出权。",
            9,
            SOURCE,
            SOURCE_URL,
            ",".join(["具体案例", "深度舒适聊天", capability["name"], scenario["scene"], f"difficulty:{difficulty}"]),
            now,
            "published",
            "deep_comfort_chat_seed",
            now,
            now,
            "深度舒适聊天与现实感受交替提问",
            "项目原创训练资源；不搬运第三方全文。",
            "把问细节、现实感受交替、情绪共振和非语言共情组织为可练案例。",
            "project_original",
            "sha256:" + _hash(content),
            96 + difficulty,
            _dumps(capability["tools"]),
            f"{capability['name']}：{capability['principle']}",
            f"D{difficulty} 深度舒适聊天",
            capability["principle"],
            capability["mistake"],
            _dumps(
                [
                    {"type": "reality", "prompt": "写一个只问现实、不评估条件的问题。"},
                    {"type": "feeling", "prompt": "接着写一个感受层问题，但必须允许跳过。"},
                    {"type": "rewrite", "prompt": blueprint["practice_task"]},
                ]
            ),
            _dumps(blueprint),
            signature,
            f"{capability['key']}::{scenario['key']}",
            capability["key"],
            "deep_comfort_chat_v1",
            99,
        ),
    )
    return True


def _resource_blueprint(capability: dict[str, Any], scenario: dict[str, str], difficulty: int) -> dict[str, Any]:
    steps = [
        f"先抓关键词：{scenario['keyword']}。",
        "问一个现实层细节，不评价条件。",
        "再问一个感受层问题，让情绪有出口。",
    ]
    if difficulty >= 2:
        steps.append("用情绪共振回应一句，再继续轻问。")
    if difficulty >= 3:
        steps.append("明确对方可以不答、换话题或晚点再说。")
    return {
        "axis": capability["key"],
        "axis_label": capability["name"],
        "resource_type": "game",
        "resource_type_label": "深度舒适聊天训练卡",
        "scene": scenario["scene"],
        "relation_stage": scenario["stage"],
        "trigger": f"{scenario['key']}中，对方给出关键词“{scenario['keyword']}”，适合练习{capability['name']}。",
        "setting": scenario["setting"],
        "their_words": scenario["their_words"],
        "surface_signal": f"关键词：{scenario['keyword']}；对方愿意展开，但需要舒服节奏。",
        "deeper_need": scenario["need"],
        "common_mistake": f"{capability['mistake']}；旧回应通常会说：{scenario['bad']}",
        "why_wrong": capability["principle"],
        "better_response": _better_response(capability, scenario, difficulty),
        "response_steps": steps,
        "boundary_note": "深聊不是逼对方暴露；问细节要允许不答，感受问题要允许跳过。",
        "practice_task": f"把“{scenario['bad']}”改写成一个现实层问题、一个感受层问题和一个边界出口。",
        "transfer_scene": f"把同样结构迁移到另一个关键词：把“{scenario['keyword']}”换成“压力”或“开心”。",
        "variant_deltas": [
            f"能力点不同：{capability['name']}。",
            f"场景不同：{scenario['key']} / {scenario['stage']}。",
            f"难度不同：{DIFFICULTIES[difficulty]}",
            "输出不同：必须体现现实层和感受层的交替，而不是换标签。",
        ],
        "difficulty_contract": DIFFICULTIES[difficulty],
    }


def _better_response(capability: dict[str, Any], scenario: dict[str, str], difficulty: int) -> str:
    if capability["key"] == "value_quieting":
        base = f"我先不急着讲我怎么看，想多听你一点：{scenario['better_question']}"
    elif capability["key"] == "detail_question":
        base = f"我抓到你刚才说的“{scenario['keyword']}”。{scenario['better_question']}"
    elif capability["key"] == "reality_feeling_alternation":
        base = f"现实上我想问一个小细节：{scenario['better_question']}"
    elif capability["key"] == "emotion_resonance":
        base = f"听起来“{scenario['keyword']}”这部分不只是事实，还有一点被耗住的感觉。{scenario['better_question']}"
    elif capability["key"] == "deep_emotion_feedback":
        base = f"除了你说的“{scenario['keyword']}”，我好像还听见更深一点的需要：{scenario['need']}如果我理解错了你可以纠正我。"
    else:
        base = f"我会先放慢一点听你说。{scenario['better_question']}"
    if difficulty == 1:
        return base
    if difficulty == 2:
        return f"{base} 你可以从最容易说的那一小段开始。"
    return f"{base} 如果我问得太细，你可以只说想说的部分，或者我们换个轻松话题。"


def _resource_content(blueprint: dict[str, Any]) -> str:
    return "\n".join(
        [
            f"案例定位：{blueprint['axis_label']} / {blueprint['resource_type_label']} / {blueprint['difficulty_contract']}",
            f"场景：{blueprint['setting']}",
            f"关系阶段：{blueprint['relation_stage']}",
            f"TA说：{blueprint['their_words']}",
            f"表层信号：{blueprint['surface_signal']}",
            f"深层可能：{blueprint['deeper_need']}",
            f"常见失误：{blueprint['common_mistake']}",
            f"为什么错：{blueprint['why_wrong']}",
            f"更好回应：{blueprint['better_response']}",
            "回应拆解：" + "；".join(str(item) for item in blueprint["response_steps"]),
            f"边界提醒：{blueprint['boundary_note']}",
            f"练习任务：{blueprint['practice_task']}",
            f"迁移场景：{blueprint['transfer_scene']}",
            "变体差异：" + "；".join(str(item) for item in blueprint["variant_deltas"]),
        ]
    )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    print(json.dumps(seed(dry_run=args.dry_run), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
