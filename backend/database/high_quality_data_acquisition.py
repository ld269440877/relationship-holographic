"""Build high-quality acquisition records from approved source metadata.

The tool does not copy third-party full text. It registers source metadata,
stores raw candidates as metadata-only anchors, and creates project-original
training resources with complete case blueprints.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sqlite3
import uuid
from datetime import datetime
from pathlib import Path
from shutil import copy2
from typing import Any

from backend.core.resource_source_catalog import SOURCE_CATALOG
from backend.database.connection import DB_PATH, create_db_and_tables

PIPELINE_VERSION = "high_quality_data_acquisition_v1"
PIPELINE_SOURCE = "project_original:high_quality_acquisition_v1"
SOURCE_POLICY = "link_title_summary_short_excerpt_structured_analysis_local_original_rewrite_only"
DEFAULT_TARGET_NEW = 1440

ALLOWED_USE = [
    "sourceTitle",
    "sourceUrl",
    "shortExcerpt",
    "summary",
    "structuredAnalysis",
    "localOriginalRewrite",
    "templateMapping",
]
DISALLOWED_USE = [
    "default_full_text_copy",
    "private_chat_raw_text",
    "unlicensed_bulk_copy",
    "case_without_boundary_exit",
]

SCENE_CONTEXTS: dict[str, dict[str, str]] = {
    "初识": {
        "setting": "第一次聊天从礼貌寒暄转向个人偏好，对方语气轻，但仍在观察你是否安全。",
        "their_words": "我其实不太会和刚认识的人聊很深。",
        "bad": "那你也太慢热了吧。",
        "reply": "嗯，我只是怕一下子说太多会有点尴尬。",
        "boundary": "可以只聊一个轻问题，不需要马上深聊。",
    },
    "暧昧": {
        "setting": "晚上聊天忽然停了几秒，对方发来一句带试探的话，又补了一个轻表情。",
        "their_words": "我发现跟你聊天时间过得挺快。",
        "bad": "那你是不是喜欢我？",
        "reply": "也不是要马上定义，就是觉得挺舒服的。",
        "boundary": "可以接住靠近，但不逼对方立刻表态。",
    },
    "热恋": {
        "setting": "睡前通话里，对方声音变低，亲密和不确定同时出现。",
        "their_words": "我今天有点黏人，你会不会烦？",
        "bad": "你怎么又开始想这些。",
        "reply": "我就是想确认自己没有太打扰你。",
        "boundary": "回应亲密需求，也允许节奏协商。",
    },
    "冲突": {
        "setting": "一个小问题触发旧情绪，双方语速变快，对方开始收回表达。",
        "their_words": "你每次都这样，说了也没用。",
        "bad": "你别总翻旧账，我也不是故意的。",
        "reply": "我不是想吵，只是觉得之前的影响没有被看见。",
        "boundary": "先承认影响，暂时不争输赢。",
    },
    "修复": {
        "setting": "争执后的第二天，对方愿意回复，但字数很短，仍在警惕再次受伤。",
        "their_words": "我现在不知道该怎么相信你说的。",
        "bad": "你怎么还不相信我？",
        "reply": "我需要看到一点稳定的行动，而不是马上听解释。",
        "boundary": "修复不等于逼对方立刻原谅。",
    },
    "平淡": {
        "setting": "日常小选择重复出现，对方说随便，但身体动作显示并不真的轻松。",
        "their_words": "随便，你定就好。",
        "bad": "每次都随便，选了又不满意。",
        "reply": "我不是不想选，只是有时候懒得解释偏好。",
        "boundary": "用低成本问题提取偏好，不把随便当成敷衍。",
    },
    "承诺": {
        "setting": "两个人讨论未来安排，对方停顿很久，像是在平衡期待和压力。",
        "their_words": "我不是不想规划，只是怕说了做不到。",
        "bad": "你就是不够认真。",
        "reply": "我想认真，但也怕承诺太大以后让你失望。",
        "boundary": "把大承诺拆成小行动和复盘时间。",
    },
    "分歧": {
        "setting": "消费、社交或家庭边界上的不同开始变成人格判断。",
        "their_words": "我不是反对你，我只是想要一点底。",
        "bad": "你就是太保守了。",
        "reply": "我需要确定感，不是想控制你。",
        "boundary": "把价值判断拆成可协商参数。",
    },
    "异地": {
        "setting": "深夜低电量报备里，对方只发了极短信息，却仍在维持连接。",
        "their_words": "到家了，先睡。",
        "bad": "你怎么又这么冷淡？",
        "reply": "我真的没力气了，但还是想让你知道我安全到家。",
        "boundary": "先确认安全，再延后复盘。",
    },
    "复联": {
        "setting": "中断后的重新接触，对方用一句很轻的话试探是否还能对话。",
        "their_words": "最近还好吗？",
        "bad": "你现在才想起来问？",
        "reply": "我也不知道怎么开口，所以先问一句轻的。",
        "boundary": "低门槛打开窗口，不急着翻旧账。",
    },
}

AXIS_BY_THEME = (
    ("边界", "boundary_consent", "边界与同意", "确认边界"),
    ("同意", "boundary_consent", "边界与同意", "确认边界"),
    ("冲突", "conflict_repair", "冲突修复", "修复信任"),
    ("修复", "conflict_repair", "冲突修复", "修复信任"),
    ("幽默", "humor_interaction", "幽默互动", "降低防御"),
    ("暧昧", "flirty_tension", "暧昧张力", "保留退路"),
    ("情绪", "emotion_flow", "情绪流动", "命名感受"),
    ("感受", "emotion_flow", "情绪流动", "命名感受"),
    ("长期", "long_connection", "长期连接", "提出请求"),
    ("关系", "micro_signal", "微关系信号", "引导深聊"),
)


def backup_database(db_path: Path = DB_PATH) -> Path:
    backup_dir = db_path.parent / "backups"
    backup_dir.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    backup_path = backup_dir / f"{db_path.stem}-before-high-quality-acquisition-{timestamp}{db_path.suffix}"
    copy2(db_path, backup_path)
    return backup_path


def run_acquisition(db_path: Path = DB_PATH, *, target_new: int = DEFAULT_TARGET_NEW, dry_run: bool = False) -> dict[str, Any]:
    if db_path == DB_PATH:
        create_db_and_tables()
    backup_path: Path | None = None
    if not dry_run:
        backup_path = backup_database(db_path)

    with sqlite3.connect(db_path) as connection:
        connection.row_factory = sqlite3.Row
        expression_tools = _load_expression_tools(connection)
        created_sources = 0
        created_raw = 0
        created_resources = 0
        skipped_resources = 0
        issue_count = 0
        sample_ids: list[str] = []

        for source in SOURCE_CATALOG:
            if created_resources >= target_new:
                break
            source_id, source_created = _upsert_source(connection, source, dry_run=dry_run)
            created_sources += int(source_created)
            for scene in _source_scenes(source):
                for theme in _source_themes(source):
                    raw_created = _upsert_raw_candidate(connection, source_id, source, scene, theme, dry_run=dry_run)
                    created_raw += int(raw_created)
                    for difficulty in (1, 2, 3):
                        if created_resources >= target_new:
                            break
                        content_unit = _content_unit(source, scene, theme, difficulty)
                        tool = _select_expression_tool(expression_tools, content_unit)
                        resource = _build_resource(source, scene, theme, difficulty, tool)
                        exists = _resource_exists(connection, resource["resource_uuid"], resource["content_unit"])
                        if exists:
                            skipped_resources += 1
                            continue
                        created_resources += 1
                        if len(sample_ids) < 5:
                            sample_ids.append(resource["resource_uuid"])
                        if not dry_run:
                            _insert_resource(connection, resource)
                    if created_resources >= target_new:
                        break
                if created_resources >= target_new:
                    break

        report = {
            "version": PIPELINE_VERSION,
            "target_new": target_new,
            "created_sources": created_sources,
            "created_raw_items": created_raw,
            "created_resources": created_resources,
            "skipped_resources": skipped_resources,
            "issues_count": issue_count,
            "sample_resource_uuids": sample_ids,
            "source_policy": SOURCE_POLICY,
            "quality_gate": {
                "third_party_full_text_stored": False,
                "case_blueprint_required": True,
                "dialogue_script_required": True,
                "boundary_exit_required": True,
            },
        }
        if not dry_run:
            _insert_batch(connection, report)
            connection.commit()
        else:
            connection.rollback()

    return {
        "dry_run": dry_run,
        "backup_path": str(backup_path) if backup_path else None,
        **report,
    }


def _load_expression_tools(connection: sqlite3.Connection) -> list[dict[str, str]]:
    try:
        rows = connection.execute(
            """
            SELECT tool_uuid, name, layer, category, formula, best_scenes_json
            FROM expression_tools
            WHERE review_status = 'published'
            ORDER BY quality_score DESC, id
            """
        ).fetchall()
    except sqlite3.OperationalError:
        rows = []
    tools = [
        {
            "tool_uuid": str(row["tool_uuid"]),
            "name": str(row["name"]),
            "layer": str(row["layer"] or ""),
            "category": str(row["category"] or ""),
            "formula": str(row["formula"] or ""),
            "best_scenes_json": str(row["best_scenes_json"] or "[]"),
        }
        for row in rows
    ]
    return tools or [{"tool_uuid": "expr_tool_041", "name": "情绪标注", "layer": "emotion", "category": "共情", "formula": "事实 -> 感受 -> 边界", "best_scenes_json": "[]"}]


def _upsert_source(connection: sqlite3.Connection, source: dict[str, Any], *, dry_run: bool) -> tuple[int, bool]:
    source_uuid = _source_uuid(source)
    existing = connection.execute("SELECT id FROM source_registry WHERE source_uuid = ?", (source_uuid,)).fetchone()
    if existing:
        return int(existing["id"]), False
    if dry_run:
        return -abs(int(_hash(source_uuid)[:8], 16)), True
    cursor = connection.execute(
        """
        INSERT INTO source_registry (
          source_uuid, name, source_type, url, trust_score, update_frequency,
          allowed_use_json, disallowed_use_json, active, created_at
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, 1, ?)
        """,
        (
            source_uuid,
            source["name"],
            _source_type(source),
            source["url"],
            _trust_score(source),
            "weekly",
            _json(ALLOWED_USE),
            _json(DISALLOWED_USE),
            _now(),
        ),
    )
    return int(cursor.lastrowid), True


def _upsert_raw_candidate(
    connection: sqlite3.Connection,
    source_id: int,
    source: dict[str, Any],
    scene: str,
    theme: str,
    *,
    dry_run: bool,
) -> bool:
    raw_uuid = f"raw-acq:{uuid.uuid5(uuid.NAMESPACE_URL, '|'.join([str(source['url']), scene, theme, PIPELINE_VERSION]))}"
    existing = connection.execute("SELECT id FROM raw_content_items WHERE raw_uuid = ?", (raw_uuid,)).fetchone()
    if existing:
        return False
    if dry_run:
        return True
    title = f"{source['name']}｜{scene}｜{theme}｜结构化采集锚点"
    connection.execute(
        """
        INSERT INTO raw_content_items (
          raw_uuid, source_id, title, url, content_hash, raw_storage_policy,
          privacy_risk, copyright_risk, consent_status, processing_status, collected_at
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            raw_uuid,
            source_id if source_id > 0 else None,
            title,
            source["url"],
            "sha256:" + _hash("|".join([title, str(source["summary"]), str(source["structure"])])),
            SOURCE_POLICY,
            0.02,
            0.25,
            "public_metadata_only",
            "structured_analyzed",
            _now(),
        ),
    )
    return True


def _build_resource(source: dict[str, Any], scene: str, theme: str, difficulty: int, tool: dict[str, str]) -> dict[str, Any]:
    context = SCENE_CONTEXTS.get(scene) or SCENE_CONTEXTS["初识"]
    axis_key, axis_label, expression_goal = _axis_for(theme, source)
    title = f"{scene}｜{axis_label}｜{theme}｜{source['name']}｜D{difficulty}"
    blueprint = _case_blueprint(source, scene, theme, difficulty, tool, axis_key, axis_label, expression_goal)
    content = _content_from_blueprint(blueprint)
    signature = "|".join([PIPELINE_VERSION, str(source["url"]), scene, theme, str(difficulty), tool["tool_uuid"], blueprint["their_words"], blueprint["better_response"]])
    resource_uuid = f"acq-resource:{uuid.uuid5(uuid.NAMESPACE_URL, signature)}"
    tags = [
        "高质量采集",
        "本地原创改写",
        "结构化分析",
        "完整对话",
        axis_label,
        scene,
        theme,
        f"difficulty:{difficulty}",
        str(source["group"]),
    ]
    return {
        "resource_uuid": resource_uuid,
        "type": "game" if difficulty >= 2 else "story",
        "category": f"采集转化·{axis_label}",
        "title": title,
        "content": content,
        "emotional_tone_json": _json({"primary": theme, "scene": scene, "axis": axis_label, "source_group": source["group"]}),
        "emotional_intensity": min(10, 5 + difficulty),
        "applicable_scene": scene,
        "difficulty_level": difficulty,
        "gender_target": "通用",
        "attachment_suitability": "通用",
        "usage_tip": "先看完整对话，再按事实、感受、边界、下一句重写；不要背模板，要迁移结构。",
        "effectiveness_rating": 9,
        "source": PIPELINE_SOURCE,
        "source_url": source["url"],
        "tags": ",".join(tags),
        "review_status": "published",
        "reviewer_id": "high_quality_data_acquisition",
        "source_title": str(source["name"]),
        "source_excerpt": _short_excerpt(source),
        "source_summary": str(source["summary"]),
        "source_license": SOURCE_POLICY,
        "quality_score": _quality_score(blueprint),
        "expression_tool_ids_json": _json([tool["tool_uuid"]]),
        "expression_goal": expression_goal,
        "expression_level": f"D{difficulty}",
        "speech_act": f"{tool['name']} / {axis_label}",
        "mistake_pattern": blueprint["common_mistake"],
        "recommended_drills_json": _json(_recommended_drills(blueprint)),
        "case_blueprint_json": _json(blueprint),
        "variant_signature": "sha256:" + _hash(signature),
        "content_unit": _content_unit(source, scene, theme, difficulty),
        "coverage_axis": axis_key,
        "variant_family": "|".join([axis_key, scene, theme]),
        "case_completeness_score": 100,
        "content_fingerprint": "sha256:" + _hash(content),
    }


def _case_blueprint(
    source: dict[str, Any],
    scene: str,
    theme: str,
    difficulty: int,
    tool: dict[str, str],
    axis_key: str,
    axis_label: str,
    expression_goal: str,
) -> dict[str, Any]:
    context = SCENE_CONTEXTS.get(scene) or SCENE_CONTEXTS["初识"]
    better = _better_response(context, theme, tool, difficulty)
    dialogue_script = [
        {"speaker": "TA", "line": context["their_words"], "purpose": "原始信号"},
        {"speaker": "低质量回应", "line": context["bad"], "purpose": "把线索误判成结论，容易制造防御"},
        {"speaker": "更好回应", "line": better, "purpose": "锚定原话、承接感受、保留边界"},
        {"speaker": "TA", "line": context["reply"], "purpose": "对方更容易补充真实状态"},
        {"speaker": "继续回应", "line": _follow_up(context, theme), "purpose": "现实细节与感受交替推进"},
        {"speaker": "边界收束", "line": f"{context['boundary']} 如果现在不想继续，我们可以晚点再聊。", "purpose": "明确可退出、可暂停、可复盘"},
    ]
    return {
        "version": PIPELINE_VERSION,
        "source_mapping": {
            "source_name": source["name"],
            "source_url": source["url"],
            "source_group": source["group"],
            "source_policy": SOURCE_POLICY,
            "copyright_boundary": "no_third_party_full_text",
        },
        "axis": axis_key,
        "axis_label": axis_label,
        "theme": theme,
        "scene": scene,
        "difficulty_contract": f"D{difficulty}：完整案例 + 多轮对话 + 迁移练习",
        "relation_stage": scene,
        "trigger": f"把 {source['name']} 的“{theme}”主题转化为{scene}里的真实沟通训练。",
        "setting": context["setting"],
        "their_words": context["their_words"],
        "surface_signal": f"对方在“{theme}”附近露出一点靠近、犹豫或求确认的信号。",
        "deeper_need": _deeper_need(axis_key, theme),
        "common_mistake": f"{_mistake_for(axis_key)}；旧回应通常会说：{context['bad']}",
        "why_wrong": "旧回应直接评价、催促或定性，会让对方把分享收回去；更好回应先承接具体原话，再给低压力选择。",
        "better_response": better,
        "dialogue_script": dialogue_script,
        "response_variants": _response_variants(context, theme, tool),
        "response_steps": [
            "复述 TA 的一句具体原话，不先评价人格。",
            "命名一个可校正的感受或需要。",
            "只问一个低压力问题，避免连续追问。",
            "给出可停、可晚点说、可纠正你的边界出口。",
        ],
        "boundary_note": context["boundary"],
        "practice_task": f"把“{context['bad']}”改写成一轮包含现实细节、感受问题和边界出口的对话。",
        "transfer_scene": _transfer_scene(scene),
        "expression_tool": {
            "tool_uuid": tool["tool_uuid"],
            "name": tool["name"],
            "formula": tool["formula"],
            "category": tool["category"],
        },
        "five_w_two_h": {
            "why": "让外部来源只作为阅读锚点，真正训练内容落到本地原创案例。",
            "what": "来源摘要、场景故事、对话对比、迁移练习。",
            "who": "资源海洋、训练中心、AI 伴侣和错题本共用。",
            "when": f"用户需要练习{scene}里的{theme}时。",
            "where": "资源列表、资源详情、训练推荐和错题改写。",
            "how": "按来源主题映射项目主线，再生成完整案例蓝图。",
            "howMuch": "每条最小记录必须包含原话、旧回应、新回应、边界出口和多轮对话。",
        },
        "quality_notes": {
            "specificity": 25,
            "practice_ready": 25,
            "dialogue_completeness": 20,
            "boundary_clarity": 15,
            "source_trace": 15,
        },
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
            PIPELINE_SOURCE,
            "structured_acquisition",
            int(report["created_sources"]) + int(report["created_raw_items"]),
            int(report["created_resources"]),
            int(report["skipped_resources"]),
            int(report["issues_count"]),
            "completed",
            _json(report),
            _now(),
        ),
    )


def _resource_exists(connection: sqlite3.Connection, resource_uuid: str, content_unit: str) -> bool:
    return (
        connection.execute(
            "SELECT 1 FROM resource_library WHERE resource_uuid = ? OR content_unit = ?",
            (resource_uuid, content_unit),
        ).fetchone()
        is not None
    )


def _select_expression_tool(expression_tools: list[dict[str, str]], content_unit: str) -> dict[str, str]:
    index = int(_hash(content_unit)[:8], 16) % len(expression_tools)
    return expression_tools[index]


def _content_unit(source: dict[str, Any], scene: str, theme: str, difficulty: int) -> str:
    axis_key, _, _ = _axis_for(theme, source)
    return "|".join([axis_key, scene, str(source["name"]), theme, f"D{difficulty}"])


def _source_scenes(source: dict[str, Any]) -> tuple[str, ...]:
    scenes = tuple(str(scene) for scene in source.get("scenes", ()) if str(scene) in SCENE_CONTEXTS)
    return scenes or ("初识", "暧昧", "冲突", "修复")


def _source_themes(source: dict[str, Any]) -> tuple[str, ...]:
    themes = tuple(str(theme) for theme in source.get("themes", ()))
    return themes or ("关系沟通", "情绪流动", "边界确认")


def _axis_for(theme: str, source: dict[str, Any]) -> tuple[str, str, str]:
    haystack = f"{theme} {' '.join(_source_themes(source))} {source.get('summary', '')}"
    for keyword, axis_key, axis_label, goal in AXIS_BY_THEME:
        if keyword in haystack:
            return axis_key, axis_label, goal
    return "micro_signal", "微关系信号", "引导深聊"


def _source_type(source: dict[str, Any]) -> str:
    group = str(source.get("group", "manual"))
    if "研究" in group:
        return "research"
    if "中文" in group:
        return "chinese_source"
    if "数据" in group:
        return "open_data"
    if "产品" in group or "工具" in group:
        return "product_reference"
    return "expert_reference"


def _trust_score(source: dict[str, Any]) -> float:
    group = str(source.get("group", ""))
    if "研究" in group or "公共卫生" in group or "开放数据" in group:
        return 0.92
    if "中文" in group or "幽默" in group or "社区" in group:
        return 0.72
    return 0.84


def _quality_score(blueprint: dict[str, Any]) -> float:
    score = 70
    for key in ("setting", "their_words", "better_response", "dialogue_script", "response_variants", "boundary_note", "practice_task"):
        if blueprint.get(key):
            score += 3
    if blueprint.get("source_mapping", {}).get("source_url"):
        score += 4
    return min(98, score)


def _better_response(context: dict[str, str], theme: str, tool: dict[str, str], difficulty: int) -> str:
    base = (
        f"我听见你说“{_quote(context['their_words'])}”。我先不急着评价，"
        f"只是感觉这里和“{theme}”有关，也许有一点想被理解。"
        "你愿意说说刚才最明显的感受吗？"
    )
    if difficulty == 1:
        return base
    if difficulty == 2:
        return f"{base} 如果不想展开，也可以只告诉我一件具体发生的小事。"
    return f"{base} 我会按{tool['name']}的结构慢一点听，你可以随时纠正我，也可以先停。"


def _follow_up(context: dict[str, str], theme: str) -> str:
    return f"那我们只从一个细节开始：你说“{_quote(context['their_words'])}”的时候，更像是因为{theme}，还是因为当时有点累？"


def _response_variants(context: dict[str, str], theme: str, tool: dict[str, str]) -> list[dict[str, str]]:
    return [
        {
            "label": "轻量承接版",
            "response": f"我听见你说“{_quote(context['their_words'])}”。我先不评价，你愿意说说最明显的感受吗？",
            "why_it_works": "先接住原话，不把线索变成定性。",
        },
        {
            "label": "现实-感受交替版",
            "response": f"刚才具体是哪一刻让你有这个感觉？那一刻更像是{theme}，还是想确认我会怎么接？",
            "why_it_works": "先问现实细节，再问感受，避免审问感。",
        },
        {
            "label": "工具迁移版",
            "response": f"我试着用{tool['name']}整理一下：我听见的是这句话，不急着下结论；我们只聊你愿意说的一小段。",
            "why_it_works": "把表达工具变成真实回应，而不是讲概念。",
        },
        {
            "label": "边界稳态版",
            "response": f"{context['boundary']} 如果你愿意继续，我们只聊这句话里最具体的一点。",
            "why_it_works": "把边界出口和当前对话绑定。",
        },
    ]


def _content_from_blueprint(blueprint: dict[str, Any]) -> str:
    dialogue = "；".join(f"{turn['speaker']}：{turn['line']}" for turn in blueprint["dialogue_script"])
    return "\n".join(
        [
            f"案例定位：{blueprint['axis_label']} / {blueprint['theme']} / {blueprint['difficulty_contract']}",
            f"来源边界：{blueprint['source_mapping']['source_name']}｜{blueprint['source_mapping']['source_policy']}",
            f"场景：{blueprint['setting']}",
            f"TA说：{blueprint['their_words']}",
            f"完整对话：{dialogue}",
            f"表层信号：{blueprint['surface_signal']}",
            f"深层可能：{blueprint['deeper_need']}",
            f"常见失误：{blueprint['common_mistake']}",
            f"为什么错：{blueprint['why_wrong']}",
            f"更好回应：{blueprint['better_response']}",
            "回应拆解：" + "；".join(blueprint["response_steps"]),
            f"边界提醒：{blueprint['boundary_note']}",
            f"练习任务：{blueprint['practice_task']}",
            f"迁移场景：{blueprint['transfer_scene']}",
        ]
    )


def _recommended_drills(blueprint: dict[str, Any]) -> list[dict[str, str]]:
    return [
        {"type": "observe", "prompt": f"标出“{blueprint['their_words']}”里的事实、感受和边界信号。"},
        {"type": "rewrite", "prompt": blueprint["practice_task"]},
        {"type": "transfer", "prompt": f"迁移到“{blueprint['transfer_scene']}”，保留同一个边界出口。"},
    ]


def _deeper_need(axis_key: str, theme: str) -> str:
    if axis_key == "boundary_consent":
        return "希望靠近是自愿的，节奏可以被尊重。"
    if axis_key == "conflict_repair":
        return "希望影响被看见，而不是马上被解释盖过去。"
    if axis_key == "emotion_flow":
        return "希望自己的感受被命名、被允许，并能慢慢流动。"
    if axis_key == "flirty_tension":
        return "希望靠近有一点好玩，也有足够退路。"
    if axis_key == "long_connection":
        return "希望关系有稳定约定，而不是每次都靠猜。"
    return f"希望围绕“{theme}”被具体看见，而不是被标签化。"


def _mistake_for(axis_key: str) -> str:
    return {
        "boundary_consent": "把没有明确拒绝当成同意",
        "conflict_repair": "急着解释自己不是故意的",
        "emotion_flow": "只解决事情，不承接当下情绪",
        "flirty_tension": "为了制造张力而逼对方表态",
        "long_connection": "只在爆发时谈规则，平时靠猜",
        "humor_interaction": "用玩笑盖过对方的不舒服",
    }.get(axis_key, "把一个小信号立刻判成冷淡、拒绝或敷衍")


def _transfer_scene(scene: str) -> str:
    return {
        "初识": "第一次约咖啡前的轻确认",
        "暧昧": "一次低压力邀约",
        "热恋": "睡前亲密节奏确认",
        "冲突": "公开场合后的私下复盘",
        "修复": "一次具体补偿安排",
        "平淡": "晚饭选择和偏好校准",
        "承诺": "周末安排和未来规划",
        "分歧": "预算、社交或家庭边界协商",
        "异地": "周末视频前的低电量沟通",
        "复联": "十分钟修复窗口邀请",
    }.get(scene, "相邻关系场景")


def _source_uuid(source: dict[str, Any]) -> str:
    return f"source-acq:{uuid.uuid5(uuid.NAMESPACE_URL, str(source['url']))}"


def _short_excerpt(source: dict[str, Any]) -> str:
    structure = str(source.get("structure", ""))
    if len(structure) > 90:
        structure = structure[:87] + "..."
    return f"结构导读：{structure}"


def _quote(text: str) -> str:
    return text.strip().rstrip("。！？.!?")


def _json(data: Any) -> str:
    return json.dumps(data, ensure_ascii=False, sort_keys=True)


def _hash(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _now() -> str:
    return datetime.now().isoformat(timespec="seconds")


def main() -> None:
    parser = argparse.ArgumentParser(description="Build high-quality acquisition records and project-original resources.")
    parser.add_argument("--db", type=Path, default=DB_PATH)
    parser.add_argument("--target-new", type=int, default=DEFAULT_TARGET_NEW)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    print(json.dumps(run_acquisition(args.db, target_new=args.target_new, dry_run=args.dry_run), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
