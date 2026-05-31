"""Seed self-disclosure depth, intimacy, and emotional-flow materials."""

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

SOURCE = "user_provided:self_disclosure_intimacy_emotion_flow_v1"
SOURCE_URL = "local_anchor:自我表露深度_亲密关系_情绪流动"
SECTION_UUID = "knowledge_self_disclosure_intimacy_flow_v1"
TOOL_UUID = "expr_tool_062"
CHAIN_UUID = "expr_chain_self_disclosure_depth_v1"

DEPTH_LEVELS = [
    ("D1 事实层", "姓名、职业、兴趣、一般经历；低风险，适合初识。"),
    ("D2 观点层", "喜好、价值判断、非核心立场；适合轻度熟悉。"),
    ("D3 情感层", "开心、失落、恐惧、喜欢等真实感受；需要基本信任。"),
    ("D4 脆弱层", "不安全感、羞耻、创伤、核心失败；需要稳定接纳和边界。"),
    ("D5 存在层", "终极恐惧、深层渴望、无条件被爱的需要；需要高度安全关系或专业场域。"),
]

CONCEPTS = [
    {
        "entry_uuid": "knowledge:self_disclosure_depth:v1",
        "title": "自我表露深度：从事实到存在层的五级刻度",
        "category": "自我表露深度",
        "tags": ["自我表露深度", "脆弱性", "亲密关系", "边界同意", "关系风险"],
        "summary": "根据关系亲密度、内容私密性和风险程度，决定说到哪一层、何时停、如何互惠。",
        "content": [
            "核心定义：自我表露深度是个体在人际互动中自愿透露个人信息的私密性、重要性和风险程度。",
            "日常理解：不是交浅言深，而是根据关系亲密度说出相应私密程度的心里话。",
            "五级刻度：" + "；".join(f"{name}：{desc}" for name, desc in DEPTH_LEVELS),
            "风险类型：社会风险、关系风险、心理风险。越深的表露越需要安全环境、互惠节奏和可退出边界。",
            "易混淆：深度不同于广度。什么都聊可能只是广度大；能否谈羞耻、恐惧、渴望，才是深度。",
        ],
    },
    {
        "entry_uuid": "knowledge:intimate_relationship:v1",
        "title": "亲密关系：长期互动、相互依赖与深度知识",
        "category": "亲密关系",
        "tags": ["亲密关系", "依恋关系", "长期连接", "关系满意度", "相互依赖"],
        "summary": "亲密关系由长期互动、情感联结、相互依赖、深度知识和承诺共同构成。",
        "content": [
            "核心定义：亲密关系是高度相互依赖、长期互动、情感联结和深度知识的关系。",
            "对象类型：浪漫亲密关系、家庭亲密关系、友谊亲密关系、治疗或支持性亲密关系。",
            "程度谱系：初步联结、核心亲密、依恋层、合一层。健康亲密不是共生，而是自主中的依赖。",
            "依恋风格：安全型能平衡依赖和独立；焦虑型需要反复确认；回避型害怕依赖并保持距离。",
            "功能：提供安全基地、情绪调节、身份认同、危机缓冲和长期意义感。",
        ],
    },
    {
        "entry_uuid": "knowledge:emotional_flow:v1",
        "title": "情绪流动：触发、表达、转折与消解",
        "category": "情绪流动",
        "tags": ["情绪流动", "情绪调节", "身体线索", "亲密修复", "情绪冻结"],
        "summary": "情绪流动描述情绪从产生、体验、表达、传递到消退的动态过程。",
        "content": [
            "核心定义：情绪流动是情绪能量在身体和心理层面自然产生、表达、传递并最终消解的过程。",
            "强度谱系：微动、涌动、波动、奔流、洪流、澄澈流动。",
            "健康方向：顺畅流动会从触发进入表达、被承接、转折、余波；阻滞会压抑、反刍、冻结或爆发。",
            "身体线索：胸口发紧、喉咙堵、眼眶热、肩颈僵、呼吸变浅、哭后变松。",
            "关系应用：伴侣或朋友间的情绪流动顺畅时，冲突更容易从指责转向脆弱分享和修复。",
        ],
    },
]

SCENARIOS = [
    {
        "key": "初识节奏",
        "scene": "初识",
        "their_words": "我其实不太习惯一开始就聊很深。",
        "bad": "这有什么，真诚一点不好吗？",
        "better": "没关系，我们先停在轻一点的层次。你愿意说兴趣或最近的小事就够了，不需要一下子讲很私人的部分。",
        "level": 1,
        "risk": "过早推进会让好奇变成压力。",
    },
    {
        "key": "暧昧心动",
        "scene": "暧昧",
        "their_words": "跟你聊天会有点开心，但我也怕太快。",
        "bad": "那你就是喜欢我了吧？",
        "better": "我听见两个层次：有开心，也有怕太快。我们可以先承认这种感觉，不急着把关系定义完。",
        "level": 3,
        "risk": "把情感层误读成承诺，会压缩对方选择。",
    },
    {
        "key": "冲突后脆弱",
        "scene": "修复",
        "their_words": "我不是不想说，是一说到这个我就觉得自己很糟。",
        "bad": "你别想这么多，先说问题怎么解决。",
        "better": "这已经不是事情本身了，更像碰到了羞耻感。我们可以慢一点，你不用把最深的部分一次说完。",
        "level": 4,
        "risk": "在脆弱层催促解决，会造成二次受伤。",
    },
    {
        "key": "长期深层渴望",
        "scene": "长期",
        "their_words": "我最想要的是，有人能接住我所有崩溃，但我又觉得这样太贪心。",
        "bad": "谁能一直接住你啊，你要求太高了。",
        "better": "我听见的是一个很深的渴望：想被接住，也怕自己不配。这个层次很重要，我们可以先只陪它待一会儿，不急着评判。",
        "level": 5,
        "risk": "存在层表露需要高度安全，不适合用评判或玩笑回应。",
    },
]


def backup_database(db_path: Path = DB_PATH) -> Path:
    backup_dir = db_path.parent / "backups"
    backup_dir.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    backup_path = backup_dir / f"{db_path.stem}-before-self-disclosure-intimacy-{timestamp}{db_path.suffix}"
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
        if not dry_run:
            _insert_batch(connection, report)
            connection.commit()
        else:
            connection.rollback()
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
            "自我表露深度与亲密关系",
            "把自我表露深度、亲密关系和情绪流动组织成可训练的关系推进地图。",
            "🧭",
            36,
            SOURCE,
            SOURCE_URL,
            _now(),
            _now(),
        ),
    )
    return int(cursor.lastrowid), True


def _upsert_entries(connection: sqlite3.Connection, section_id: int, *, dry_run: bool) -> tuple[int, int]:
    created = 0
    updated = 0
    for item in CONCEPTS:
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
        "self_disclosure_intimacy_seed",
        _now(),
        _now(),
        SOURCE,
        SOURCE_URL,
        _json({"template_version": "self_disclosure_intimacy_flow_v1", "source_policy": "user_provided_structured_material"}),
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
        "自我表露深度校准",
        "relationship",
        "亲密推进",
        "关系安全度 -> 表露深度 -> 互惠程度 -> 边界出口",
        "判断一段话该停留在事实、观点、情感、脆弱还是存在层，避免交浅言深和深聊逼供。",
        _json(["初识", "暧昧", "修复", "长期", "心理支持", "社交"]),
        _json(["深度情感连接", "边界同意", "长期连接", "情绪流动"]),
        _json(["焦虑", "犹豫", "羞耻", "信任", "被接住", "后悔"]),
        _json(["过早深度表露", "单方面持续表露", "逼问创伤", "把脆弱当筹码", "没有退路"]),
        _json(["判断关系安全度", "选择表露深度", "观察互惠", "命名风险", "保留退出权"]),
        _json(_tool_blueprint()),
        "我小时候最糟的事都告诉你，你也必须告诉我一个秘密。",
        "我们先不用一下子聊到最深。如果你愿意，可以只说一个让你有点在意的小片段；不想说也完全可以。",
        "operation",
        SOURCE,
        SOURCE_URL,
        "published",
        99,
        _now(),
    )


def _tool_blueprint() -> dict[str, Any]:
    return {
        "concept": "自我表露深度校准用于决定说到哪一层、何时停、如何互惠，而不是鼓励越深越好。",
        "depth_levels": [{"level": name, "rule": rule} for name, rule in DEPTH_LEVELS],
        "core_principles": [
            "深度必须匹配关系安全度。",
            "深度表露必须自愿，不可被逼问或交换。",
            "对方没有互惠时，应降深度而不是继续加码。",
            "创伤、核心羞耻和存在层恐惧需要更高安全度，必要时转向专业支持。",
        ],
        "dialogue_cases": [
            {
                "scene": item["scene"],
                "story": item["their_words"],
                "poor_response": item["bad"],
                "better_response": item["better"],
                "why_it_works": item["risk"],
            }
            for item in SCENARIOS
        ],
        "practice_ladder": ["D1：只识别表露层级。", "D2：给出匹配层级的回应。", "D3：能在脆弱层保留边界出口。"],
    }


def _upsert_chain(connection: sqlite3.Connection, *, dry_run: bool) -> tuple[bool, bool]:
    existing = connection.execute("SELECT id FROM expression_tool_chains WHERE chain_uuid=?", (CHAIN_UUID,)).fetchone()
    payload = (
        "自我表露深度安全推进链",
        "亲密推进但不越界",
        "初识/暧昧/修复/长期",
        "D1-D5 深度校准",
        _json([TOOL_UUID, "expr_tool_056", "expr_tool_061"]),
        _json([
            {"order": 1, "tool": "自我表露深度校准", "action": "判断当前内容处于事实、观点、情感、脆弱还是存在层。"},
            {"order": 2, "tool": "边界出口", "action": "允许对方不说、少说、晚点说或纠正你。"},
            {"order": 3, "tool": "感受-期待-选择", "action": "表达自己的感受和期待，但不绑架对方回应。"},
        ]),
        _json(["交浅言深", "逼问创伤", "把秘密当筹码", "单向倾倒", "无边界共生"]),
        _json({"before": "你都跟我聊这么深了，肯定要给我同等回应。", "after": "我们先确认这个话题对你是否安全；如果太深，可以停在这里。"}),
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
    for scenario in SCENARIOS:
        for difficulty in (1, 2, 3):
            resource = _resource_payload(scenario, difficulty)
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


def _resource_payload(scenario: dict[str, Any], difficulty: int) -> dict[str, Any]:
    blueprint = _blueprint(scenario, difficulty)
    content = _content(blueprint)
    content_unit = f"self_disclosure_depth::{scenario['key']}::D{difficulty}"
    signature = "|".join([SOURCE, content_unit, blueprint["better_response"]])
    return {
        "resource_uuid": f"self-disclosure-depth:{uuid.uuid5(uuid.NAMESPACE_URL, signature)}",
        "type": "game",
        "category": "自我表露深度校准",
        "title": f"{scenario['key']}｜自我表露深度校准｜D{difficulty}",
        "content": content,
        "emotional_tone_json": _json({"primary": "亲密推进", "depth": scenario["level"], "scene": scenario["scene"]}),
        "emotional_intensity": min(10, 4 + scenario["level"]),
        "applicable_scene": scenario["scene"],
        "difficulty_level": difficulty,
        "gender_target": "通用",
        "attachment_suitability": "通用",
        "usage_tip": "先判断表露深度，再匹配回应强度；越深越要给退路。",
        "effectiveness_rating": 9,
        "source": SOURCE,
        "source_url": SOURCE_URL,
        "tags": ",".join(["自我表露深度", "亲密关系", "情绪流动", "边界同意", scenario["scene"], f"difficulty:{difficulty}"]),
        "review_status": "published",
        "reviewer_id": "self_disclosure_intimacy_seed",
        "source_title": "自我表露深度、亲密关系与情绪流动融合包",
        "source_excerpt": "用户提供结构化素材转化为项目原创训练卡，不保存第三方全文。",
        "source_summary": "围绕自我表露深度、亲密关系安全度和情绪流动，构建可练习的亲密推进路径。",
        "source_license": "user_provided_structured_material",
        "quality_score": 98,
        "expression_tool_ids_json": _json([TOOL_UUID, "expr_tool_061"]),
        "expression_goal": "亲密推进但不越界",
        "expression_level": f"D{difficulty}",
        "speech_act": "深度校准 / 镜像回应 / 边界出口",
        "mistake_pattern": blueprint["common_mistake"],
        "recommended_drills_json": _json([
            {"type": "depth_mark", "prompt": "标出 TA 的表露处于 D1-D5 哪一层。"},
            {"type": "risk_check", "prompt": "写出社会、关系、心理三类风险中最明显的一类。"},
            {"type": "rewrite", "prompt": "补一句不逼迫对方继续表露的边界出口。"},
        ]),
        "case_blueprint_json": _json(blueprint),
        "variant_signature": "sha256:" + _hash(signature),
        "content_unit": content_unit,
        "coverage_axis": "self_disclosure_depth",
        "variant_family": "self_disclosure_depth_calibration",
        "case_completeness_score": 100,
        "content_fingerprint": "sha256:" + _hash(content),
    }


def _blueprint(scenario: dict[str, Any], difficulty: int) -> dict[str, Any]:
    return {
        "version": "self_disclosure_intimacy_flow_v1",
        "axis": "self_disclosure_depth",
        "axis_label": "自我表露深度",
        "scene": scenario["scene"],
        "depth_level": scenario["level"],
        "depth_label": DEPTH_LEVELS[scenario["level"] - 1][0],
        "their_words": scenario["their_words"],
        "common_mistake": f"把深度推进当成亲密证明；旧回应通常会说：{scenario['bad']}",
        "why_wrong": scenario["risk"],
        "better_response": scenario["better"],
        "dialogue_script": _dialogue_script(scenario, difficulty),
        "response_steps": [
            "识别表露深度：先判断是事实、观点、情感、脆弱还是存在层。",
            "匹配关系安全度：确认关系是否足够承载该层级。",
            "观察互惠：对方是否也愿意、是否有余力继续。",
            "保留出口：允许不说、少说、晚点说或纠正理解。",
        ],
        "risk_matrix": {
            "social": "内容是否可能影响声誉、职场或社会评价。",
            "relationship": "内容是否可能改变对方看法或带来拒绝风险。",
            "psychological": "表露是否可能触发羞耻、闪回或长时间崩溃。",
        },
        "practice_task": "把旧回应改成：深度识别 + 承接一句 + 边界出口一句。",
    }


def _dialogue_script(scenario: dict[str, Any], difficulty: int) -> list[dict[str, str]]:
    script = [
        {"speaker": "TA", "line": scenario["their_words"], "purpose": "原始表露"},
        {"speaker": "低质量回应", "line": scenario["bad"], "purpose": "越界推进或评判"},
        {"speaker": "更好回应", "line": scenario["better"], "purpose": "匹配深度并保留边界"},
        {"speaker": "TA", "line": "这样说我会比较有安全感，不用一下子把所有东西都倒出来。", "purpose": "关系安全度上升"},
        {"speaker": "继续回应", "line": "我们就停在你觉得安全的地方，不需要证明什么。", "purpose": "确认退出权"},
    ]
    return script[: 3 + difficulty]


def _content(blueprint: dict[str, Any]) -> str:
    dialogue = "；".join(f"{turn['speaker']}：{turn['line']}" for turn in blueprint["dialogue_script"])
    return "\n".join(
        [
            f"案例定位：{blueprint['axis_label']} / {blueprint['depth_label']} / {blueprint['scene']}",
            f"TA说：{blueprint['their_words']}",
            f"完整对话：{dialogue}",
            f"常见失误：{blueprint['common_mistake']}",
            f"为什么错：{blueprint['why_wrong']}",
            f"更好回应：{blueprint['better_response']}",
            "四步拆解：" + "；".join(blueprint["response_steps"]),
            f"风险矩阵：社会风险={blueprint['risk_matrix']['social']}；关系风险={blueprint['risk_matrix']['relationship']}；心理风险={blueprint['risk_matrix']['psychological']}",
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
    parser = argparse.ArgumentParser(description="Seed self-disclosure depth and intimacy materials.")
    parser.add_argument("--db", type=Path, default=DB_PATH)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    print(_json(seed(args.db, dry_run=args.dry_run)))


if __name__ == "__main__":
    main()
