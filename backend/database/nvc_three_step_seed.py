"""Seed the NVC three-step choice pattern across knowledge, tools, and resources."""

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

SOURCE = "project_original:nvc_three_step_choice_v1"
SOURCE_URL = "local_anchor:非暴力沟通三步法_感受期待选择"
SECTION_UUID = "knowledge_nvc_three_step_choice_v1"
ENTRY_UUID = "knowledge_entry_nvc_three_step_choice_v1"
TOOL_UUID = "expr_tool_061"
CHAIN_UUID = "expr_chain_nvc_choice_001"

STEPS = (
    ("我的感受", "只说自己的身体、情绪和状态，不评价对方人格。"),
    ("我的期待", "用“希望/会更安心/我会更容易”替代“必须/你应该”。"),
    ("你的选择", "明确对方可以拒绝、改天、纠正你或选择别的节奏。"),
)

SCENARIOS: tuple[dict[str, str], ...] = (
    {
        "key": "暧昧表达",
        "scene": "暧昧",
        "setting": "晚上散步结束后，你想表达靠近，但不想把对方逼到必须回应。",
        "their_words": "今天跟你待着还挺轻松的。",
        "bad": "那你是不是也喜欢我？你要给我一个答案。",
        "feeling": "你这样说的时候，我心跳有点快，也会很想多了解你。",
        "expectation": "如果之后我们还能这样慢慢相处，我会很开心。",
        "choice": "当然你不用现在回应，想先当朋友慢慢来，也完全可以。",
        "need": "靠近被看见，同时不被要求立刻定义关系。",
    },
    {
        "key": "行程变化",
        "scene": "分歧",
        "setting": "对方临时改了约会时间，你有不安，但不想把需求说成命令。",
        "their_words": "我今天可能又要晚一点，临时有事。",
        "bad": "你必须提前告诉我，不然就是不重视我。",
        "feeling": "听到又要改时间时，我会有点悬着，像不知道自己该怎么安排。",
        "expectation": "如果行程有变化能提前说一声，我会更安心，也更好调整。",
        "choice": "如果你今天确实忙，我们可以改天；我只是想提前知道节奏。",
        "need": "确定感、被尊重、安排可预期。",
    },
    {
        "key": "冲突修复",
        "scene": "修复",
        "setting": "争执后你想修复关系，但不想要求对方马上原谅。",
        "their_words": "我现在还不太想聊昨天的事。",
        "bad": "我都道歉了，你为什么还这样？",
        "feeling": "听到你还不想聊，我有点难受，也意识到昨天确实让你受影响了。",
        "expectation": "我希望能找一个你比较有余力的时候，把影响认真听完。",
        "choice": "你可以决定今晚不聊；如果愿意，我们只约十分钟也可以。",
        "need": "修复窗口、影响被承认、节奏被尊重。",
    },
    {
        "key": "拒绝帮忙",
        "scene": "边界确认",
        "setting": "朋友临时请求你今晚帮他改方案，但你自己的项目已经压线。",
        "their_words": "你就帮我这一次吧，真的很急。",
        "bad": "我不想帮，你别来烦我。",
        "feeling": "我听到你很急时会想帮，但我也有点紧，因为我自己的项目今晚必须收尾。",
        "expectation": "我希望既不敷衍你，也不把自己的事情拖垮。",
        "choice": "我今晚不能完整接手，但可以帮你看十分钟结构；如果不够，你可以找更有空的人。",
        "need": "互相体谅、边界清楚、替代方案真实。",
    },
    {
        "key": "深聊邀请",
        "scene": "初识",
        "setting": "第一次见面聊到价值观，你想继续了解，但要避免审问感。",
        "their_words": "我其实不太习惯一开始就聊很深。",
        "bad": "这有什么，你放松点就好了。",
        "feeling": "听你这样说，我会放慢一点，也有点珍惜你愿意提醒我节奏。",
        "expectation": "我希望我们可以从一个轻一点的问题开始，而不是一下子挖太深。",
        "choice": "如果你不想聊这个，我们换个轻松话题也行。",
        "need": "安全感、节奏自主、被好奇但不被逼问。",
    },
    {
        "key": "异地报备",
        "scene": "异地",
        "setting": "对方深夜只发“到了”，你想表达想要连接，但不把报备变成控制。",
        "their_words": "到家了，先睡。",
        "bad": "你就不能多说两句吗？",
        "feeling": "看到你安全到家我会松一口气，也会有一点想念，想多听你一句。",
        "expectation": "如果以后还有力气，多发一句今天累不累，我会更有连接感。",
        "choice": "但你很困的话先睡最重要，明天再说也可以。",
        "need": "安全确认、连接感、不过度消耗。",
    },
)


def backup_database(db_path: Path = DB_PATH) -> Path:
    backup_dir = db_path.parent / "backups"
    backup_dir.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    backup_path = backup_dir / f"{db_path.stem}-before-nvc-three-step-{timestamp}{db_path.suffix}"
    shutil.copy2(db_path, backup_path)
    return backup_path


def seed(db_path: Path = DB_PATH, *, dry_run: bool = False) -> dict[str, Any]:
    if db_path == DB_PATH:
        create_db_and_tables()
    backup_path: Path | None = None
    if not dry_run:
        backup_path = backup_database(db_path)

    with sqlite3.connect(db_path) as connection:
        connection.row_factory = sqlite3.Row
        report = {
            "dry_run": dry_run,
            "source": SOURCE,
            "created_sections": 0,
            "created_entries": 0,
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
        report["created_entries"] += int(_upsert_knowledge_entry(connection, section_id, dry_run=dry_run))
        tool_created, tool_updated = _upsert_tool(connection, dry_run=dry_run)
        report["created_tools"] += int(tool_created)
        report["updated_tools"] += int(tool_updated)
        chain_created, chain_updated = _upsert_chain(connection, dry_run=dry_run)
        report["created_chains"] += int(chain_created)
        report["updated_chains"] += int(chain_updated)
        created_resources, skipped_resources = _seed_resources(connection, dry_run=dry_run)
        report["created_resources"] += created_resources
        report["skipped_resources"] += skipped_resources
        if not dry_run:
            _insert_batch(connection, report)
            connection.commit()
        else:
            connection.rollback()
    return report


def _upsert_section(connection: sqlite3.Connection, *, dry_run: bool) -> tuple[int, bool]:
    existing = connection.execute("SELECT id FROM knowledge_sections WHERE section_uuid = ?", (SECTION_UUID,)).fetchone()
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
            "非暴力沟通三步法",
            "真诚表达但不绑架对方：我的感受、我的期待、你的选择。",
            "🫶",
            32,
            SOURCE,
            SOURCE_URL,
            _now(),
            _now(),
        ),
    )
    return int(cursor.lastrowid), True


def _upsert_knowledge_entry(connection: sqlite3.Connection, section_id: int, *, dry_run: bool) -> bool:
    existing = connection.execute("SELECT id FROM knowledge_entries WHERE entry_uuid = ?", (ENTRY_UUID,)).fetchone()
    if existing:
        return False
    if dry_run:
        return True
    content = _knowledge_content()
    connection.execute(
        """
        INSERT INTO knowledge_entries (
          entry_uuid, section_id, title, subtitle, content, summary, category, tags_json,
          quality_score, review_status, reviewer_id, reviewed_at, published_at,
          source, source_id, source_metadata_json, created_at, updated_at
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            ENTRY_UUID,
            section_id,
            "非暴力沟通三步法：我的感受、我的期待、你的选择",
            "真诚表达，但不把回应变成对方必须完成的任务。",
            content,
            "把喜欢、不安、请求、拒绝和修复拆成感受、期待、选择三步，既说清自己，也保留对方退路。",
            "表达工具 / 边界同意 / 情绪流动",
            _json(["非暴力沟通", "我的感受", "我的期待", "你的选择", "边界与同意", "真诚表达", "低压力请求"]),
            98,
            "published",
            "nvc_three_step_seed",
            _now(),
            _now(),
            SOURCE,
            SOURCE_URL,
            _json({"copyright_boundary": "project_original_from_user_provided_pattern", "template_version": "nvc_three_step_choice_v1"}),
            _now(),
            _now(),
        ),
    )
    return True


def _upsert_tool(connection: sqlite3.Connection, *, dry_run: bool) -> tuple[bool, bool]:
    existing = connection.execute("SELECT id FROM expression_tools WHERE tool_uuid = ?", (TOOL_UUID,)).fetchone()
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


def _upsert_chain(connection: sqlite3.Connection, *, dry_run: bool) -> tuple[bool, bool]:
    existing = connection.execute("SELECT id FROM expression_tool_chains WHERE chain_uuid = ?", (CHAIN_UUID,)).fetchone()
    payload = (
        "非暴力三步低压表达链",
        "真诚表达但不绑架",
        "暧昧/冲突/边界确认",
        "D2-D3 场景迁移",
        _json([TOOL_UUID, "expr_tool_041", "expr_tool_056"]),
        _json([
            {"order": 1, "tool": "我的感受", "action": "说自己的状态，不评价对方。"},
            {"order": 2, "tool": "我的期待", "action": "用希望表达请求，不伪装成命令。"},
            {"order": 3, "tool": "你的选择", "action": "给对方可拒绝、可改期、可纠正的出口。"},
        ]),
        _json(["必须", "你应该", "如果你不答应就是不在乎", "用退路包装施压"]),
        _json({
            "before": "你必须提前告诉我，不然就是不重视我。",
            "after": "行程变化时我会有点悬着。如果能提前说一声，我会更安心；你今天忙的话我们也可以改天。",
        }),
        "published",
        98,
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
    for scenario in SCENARIOS:
        for difficulty in (1, 2, 3):
            resource = _resource_payload(scenario, difficulty)
            exists = connection.execute(
                "SELECT id FROM resource_library WHERE resource_uuid = ? OR content_unit = ?",
                (resource["resource_uuid"], resource["content_unit"]),
            ).fetchone()
            if exists:
                skipped += 1
                if not dry_run:
                    _update_resource(connection, int(exists["id"]), resource)
                continue
            created += 1
            if dry_run:
                continue
            _insert_resource(connection, resource)
    return created, skipped


def _resource_payload(scenario: dict[str, str], difficulty: int) -> dict[str, Any]:
    blueprint = _blueprint(scenario, difficulty)
    content = _content(blueprint)
    content_unit = "|".join(["nvc_three_step", scenario["key"], scenario["scene"], f"D{difficulty}"])
    signature = "|".join([SOURCE, content_unit, blueprint["better_response"]])
    return {
        "resource_uuid": f"nvc-three-step:{uuid.uuid5(uuid.NAMESPACE_URL, signature)}",
        "type": "game",
        "category": "非暴力沟通三步法",
        "title": f"{scenario['key']}｜感受-期待-选择｜D{difficulty}",
        "content": content,
        "emotional_tone_json": _json({"primary": "真诚表达", "scene": scenario["scene"], "method": "感受-期待-选择"}),
        "emotional_intensity": min(10, 5 + difficulty),
        "applicable_scene": scenario["scene"],
        "difficulty_level": difficulty,
        "gender_target": "通用",
        "attachment_suitability": "通用",
        "usage_tip": "先说我的感受，再说我的期待，最后给你的选择；任何一步都不能变成命令或情绪勒索。",
        "effectiveness_rating": 9,
        "source": SOURCE,
        "source_url": SOURCE_URL,
        "tags": ",".join(["非暴力沟通", "感受期待选择", "边界同意", "真诚表达", scenario["scene"], f"difficulty:{difficulty}"]),
        "review_status": "published",
        "reviewer_id": "nvc_three_step_seed",
        "source_title": "非暴力沟通三步法：感受、期待、选择",
        "source_excerpt": "项目原创结构化训练卡；由用户提供模式转化，不保存第三方全文。",
        "source_summary": "真诚表达自己的喜欢、不安和请求，同时保留对方不接受、不回应、改天再说的选择。",
        "source_license": "project_original_from_user_provided_pattern",
        "quality_score": 98,
        "expression_tool_ids_json": _json([TOOL_UUID, "expr_tool_041", "expr_tool_056"]),
        "expression_goal": "真诚表达但不绑架",
        "expression_level": f"D{difficulty}",
        "speech_act": "感受表达 / 低压力请求 / 边界出口",
        "mistake_pattern": blueprint["common_mistake"],
        "recommended_drills_json": _json(_drills(blueprint)),
        "case_blueprint_json": _json(blueprint),
        "variant_signature": "sha256:" + _hash(signature),
        "content_unit": content_unit,
        "coverage_axis": "boundary_consent",
        "variant_family": f"nvc_three_step|{scenario['key']}",
        "case_completeness_score": 100,
        "content_fingerprint": "sha256:" + _hash(content),
    }


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


def _update_resource(connection: sqlite3.Connection, resource_id: int, resource: dict[str, Any]) -> None:
    now = _now()
    connection.execute(
        """
        UPDATE resource_library
        SET type=?, category=?, title=?, content=?, emotional_tone_json=?,
            emotional_intensity=?, applicable_scene=?, difficulty_level=?,
            gender_target=?, attachment_suitability=?, usage_tip=?,
            effectiveness_rating=?, source=?, source_url=?, tags=?,
            review_status=?, reviewer_id=?, reviewed_at=?, published_at=?,
            source_title=?, source_excerpt=?, source_summary=?, source_license=?,
            content_fingerprint=?, quality_score=?, expression_tool_ids_json=?,
            expression_goal=?, expression_level=?, speech_act=?, mistake_pattern=?,
            recommended_drills_json=?, case_blueprint_json=?, variant_signature=?,
            content_unit=?, coverage_axis=?, variant_family=?, case_completeness_score=?
        WHERE id=?
        """,
        (
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
            resource_id,
        ),
    )


def _tool_payload() -> tuple[Any, ...]:
    return (
        "非暴力沟通三步法",
        "relationship",
        "边界请求",
        "我的感受 -> 我的期待 -> 你的选择",
        "把真诚表达拆成自己的状态、低压力期待和对方选择，适合暧昧表达、行程变化、修复请求和拒绝帮忙。",
        _json(["暧昧", "修复", "分歧", "边界确认", "异地", "初识"]),
        _json(["边界与同意", "情绪流动", "长期连接", "暧昧张力"]),
        _json(["心跳加快", "不安", "想靠近", "担心打扰", "需要确定感"]),
        _json(["不得用退路包装施压", "不得把希望说成必须", "不得用喜欢要求对方回应"]),
        _json([step for step, _ in STEPS]),
        _json(_tool_blueprint()),
        "你必须告诉我，不然就是不重视我。",
        "行程变化时我会有点悬着。如果能提前说一声，我会更安心；你今天忙的话我们也可以改天。",
        "operation",
        SOURCE,
        SOURCE_URL,
        "published",
        99,
        _now(),
    )


def _tool_blueprint() -> dict[str, Any]:
    return {
        "concept": "非暴力沟通三步法不是让表达变软弱，而是把自己的真实说清楚，同时不剥夺对方选择。",
        "core_principles": [
            "感受只归属于我，不把对方定义成错的人。",
            "期待是可协商请求，不是伪装后的命令。",
            "选择必须真实存在，对方拒绝后关系仍然有尊严。",
            "价值不由对方回应决定；表达完成后，把结果交还给现实。",
        ],
        "micro_steps": [{"name": name, "rule": rule} for name, rule in STEPS],
        "anti_patterns": ["你必须", "你怎么能", "如果你不答应就是不在乎", "我都这么说了你还不懂吗"],
        "dialogue_cases": [
            {
                "scene": item["scene"],
                "story": item["setting"],
                "their_words": item["their_words"],
                "poor_response": item["bad"],
                "better_response": f"{item['feeling']} {item['expectation']} {item['choice']}",
                "why_it_works": "三句话分别承担感受、期待和选择，既真诚又不围堵。",
            }
            for item in SCENARIOS[:4]
        ],
        "practice_ladder": [
            "D1：把一句指责改成我的感受。",
            "D2：加入一个可协商期待。",
            "D3：补上真实退路，并接受对方不按你期待回应。",
        ],
    }


def _blueprint(scenario: dict[str, str], difficulty: int) -> dict[str, Any]:
    better = _better_response(scenario, difficulty)
    return {
        "version": "nvc_three_step_choice_v1",
        "axis": "boundary_consent",
        "axis_label": "边界与同意",
        "method": "非暴力沟通三步法",
        "steps": [{"name": name, "rule": rule} for name, rule in STEPS],
        "scene": scenario["scene"],
        "relation_stage": scenario["key"],
        "setting": scenario["setting"],
        "their_words": scenario["their_words"],
        "surface_signal": "对方给出一个可继续的信号，但仍需要你尊重节奏和选择。",
        "deeper_need": scenario["need"],
        "common_mistake": f"把期待说成命令，或用关系价值逼对方回应；旧回应通常会说：{scenario['bad']}",
        "why_wrong": "旧回应把你的不安转嫁成对方必须解决的任务，会让对方防御、逃开或被迫答应。",
        "better_response": better,
        "dialogue_script": _dialogue_script(scenario, difficulty, better),
        "response_variants": _response_variants(scenario),
        "response_steps": [
            f"我的感受：{scenario['feeling']}",
            f"我的期待：{scenario['expectation']}",
            f"你的选择：{scenario['choice']}",
        ],
        "boundary_note": "退路必须是真的；如果对方选择改天、不回应或保持朋友，你不能再用这套话继续追压。",
        "practice_task": f"把“{scenario['bad']}”改写成三句：我的感受、我的期待、你的选择。",
        "transfer_scene": "迁移到喜欢表达、行程变动、拒绝帮忙、冲突修复、异地报备等所有容易把期待说成命令的场景。",
        "five_w_two_h": {
            "why": "让真实表达不再变成控制。",
            "what": "感受、期待、选择三段式表达。",
            "who": "表达者负责说清自己，接收者保留选择权。",
            "when": "喜欢、不安、请求、拒绝、修复和边界确认时。",
            "where": "资源海洋、表达工具箱、知识中枢、训练中心和错题改写。",
            "how": "先写三句，再检查是否含有必须、应该、道德绑架和虚假退路。",
            "howMuch": "每条训练记录至少包含完整对话、坏回应、好回应、边界出口和迁移练习。",
        },
        "quality_notes": {"specificity": 25, "choice_realness": 25, "emotion_ownership": 20, "practice_ready": 20, "boundary_clarity": 10},
    }


def _better_response(scenario: dict[str, str], difficulty: int) -> str:
    return f"{scenario['feeling']} {scenario['expectation']} {scenario['choice']}"


def _dialogue_script(scenario: dict[str, str], difficulty: int, better: str) -> list[dict[str, str]]:
    return [
        {"speaker": "TA", "line": scenario["their_words"], "purpose": "原始信号"},
        {"speaker": "低质量回应", "line": scenario["bad"], "purpose": "把期待变成对方必须完成的任务"},
        {"speaker": "更好回应", "line": better, "purpose": "按感受、期待、选择表达"},
        {"speaker": "TA", "line": "这样说我会比较放松，至少不用马上给标准答案。", "purpose": "对方更容易保留真实反应"},
        {"speaker": "继续回应", "line": "嗯，我想要的是把我的状态说清楚，不是要你立刻照做。", "purpose": "澄清非操控意图"},
        {"speaker": "边界收束", "line": "如果你现在不方便回应，我们就先停在这里。", "purpose": "确认退路真实存在"},
    ][: 3 + difficulty]


def _response_variants(scenario: dict[str, str]) -> list[dict[str, str]]:
    return [
        {"label": "轻量版", "response": f"{scenario['feeling']} {scenario['choice']}", "why_it_works": "先表达状态，再给退路。"},
        {"label": "完整三步版", "response": f"{scenario['feeling']} {scenario['expectation']} {scenario['choice']}", "why_it_works": "感受、请求和选择边界都清楚。"},
        {"label": "更克制版", "response": f"{scenario['feeling']} 我先不要求你回应，只想把这部分说清楚。", "why_it_works": "适合对方压力较高时。"},
        {"label": "修复版", "response": f"{scenario['feeling']} 我希望先听你的节奏；如果不适合继续，我们晚点再聊。", "why_it_works": "把修复主动权还给关系双方。"},
    ]


def _content(blueprint: dict[str, Any]) -> str:
    dialogue = "；".join(f"{turn['speaker']}：{turn['line']}" for turn in blueprint["dialogue_script"])
    return "\n".join(
        [
            f"方法：{blueprint['method']} / {blueprint['relation_stage']} / {blueprint['scene']}",
            f"场景故事：{blueprint['setting']}",
            f"TA说：{blueprint['their_words']}",
            f"完整对话：{dialogue}",
            f"深层需要：{blueprint['deeper_need']}",
            f"常见失误：{blueprint['common_mistake']}",
            f"为什么错：{blueprint['why_wrong']}",
            f"更好回应：{blueprint['better_response']}",
            "三步拆解：" + "；".join(blueprint["response_steps"]),
            f"边界提醒：{blueprint['boundary_note']}",
            f"练习任务：{blueprint['practice_task']}",
        ]
    )


def _drills(blueprint: dict[str, Any]) -> list[dict[str, str]]:
    return [
        {"type": "mark", "prompt": "标出旧回应里哪一句把期待说成了命令。"},
        {"type": "rewrite", "prompt": blueprint["practice_task"]},
        {"type": "boundary", "prompt": "检查你的“选择”是否真实，还是另一种施压。"},
    ]


def _knowledge_content() -> str:
    return "\n".join(
        [
            "# 非暴力沟通三步法",
            "",
            "核心：真诚表达但不绑架对方。你的价值不由别人是否回应来决定。",
            "",
            "## 1. 我的感受",
            "只说自己的身体、情绪和状态，不说对方错在哪。例：你说话时我心跳加快，特别想多了解你。",
            "",
            "## 2. 我的期待",
            "用“希望”代替“必须”。例：如果能提前说行程变化，我会更安心。",
            "",
            "## 3. 你的选择",
            "给对方真实退路。例：当然你忙的话，我们改天再约也行。",
            "",
            "## 适用场景",
            "暧昧表达、行程变化、冲突修复、拒绝帮忙、初识深聊、异地报备。",
            "",
            "## 禁用边界",
            "不要用“我都这么真诚了”要求对方接受；不要把“你可以拒绝”说成表面退路；不要用喜欢证明自我价值。",
        ]
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
            "project_original_seed",
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
    parser = argparse.ArgumentParser(description="Seed NVC three-step choice resources.")
    parser.add_argument("--db", type=Path, default=DB_PATH)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    print(_json(seed(args.db, dry_run=args.dry_run)))


if __name__ == "__main__":
    main()
