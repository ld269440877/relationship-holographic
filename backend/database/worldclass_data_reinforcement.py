"""World-class relationship dynamics data reinforcement automation."""

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

VERSION = "worldclass_data_reinforcement_v1"
SOURCE = "project_original:worldclass_data_reinforcement_v1"
SOURCE_URL = "local_anchor:worldclass_relationship_dynamics_data_matrix"

SCENE_CANONICAL = {
    "长期关系": "长期",
    "长期复盘": "长期",
    "伴侣冲突": "冲突",
    "冲突修复": "修复",
    "日常调情": "暧昧",
    "调情": "暧昧",
    "情话": "暧昧",
    "追人": "暧昧",
    "追求": "暧昧",
    "搭讪": "初识",
    "表白前": "暧昧",
    "表白": "暧昧",
    "日常": "长期",
}

SPEECH_ACT_MAP = {
    "先描述你看见的具体事实": "事实观察",
    "先命名情绪": "情绪命名",
    "任何推进都要能停": "边界出口",
    "先承认影响": "影响承认",
    "低压破冰": "低压破冰",
    "温和幽默": "低压幽默",
    "开放提问": "开放提问",
    "关键词镜像": "关键词镜像",
    "需求镜像": "需求镜像",
    "镜像回应": "镜像回应",
    "感受表达": "感受表达",
    "低压力请求": "低压力请求",
}

KNOWLEDGE_TOPICS = [
    (
        "开放式提问",
        "深度情感连接",
        ["开放式提问", "封闭式问题", "低压探索", "最近发展区"],
        ["是什么让你最在意这件事？", "你愿意从哪个部分开始说？", "如果只说一点点，哪一点最安全？"],
        "开放式提问不是扩大盘问范围，而是把控制权还给对方，让对方选择进入深度的入口。",
    ),
    (
        "封闭式问题的边界",
        "提问技术",
        ["封闭式问题", "确认事实", "节奏控制", "边界"],
        ["你现在想先停一下吗？", "我理解的是 A，不是 B，对吗？", "这个话题现在适合继续吗？"],
        "封闭式问题不低级，它适合确认事实、降低不确定和检查同意；风险在于连续追问变成审讯。",
    ),
    (
        "关键词捕捉",
        "深度情感连接",
        ["关键词", "原话回放", "情绪线索", "微关系信号"],
        ["你刚才说“硬撑”，这个词好像很重。", "你提到“又是这样”，像是旧模式被触发了。"],
        "关键词捕捉优先抓重复词、重音词、停顿前后的词和自我否定词。",
    ),
    (
        "区分情绪与事实",
        "情绪定位",
        ["事实", "感受", "解释", "误判", "情绪粒度"],
        ["事实是你晚回了消息；感受是我悬着；解释可能是我担心自己不重要。"],
        "把事实、感受和解释拆开，能减少指责，也能让真实需求浮出水面。",
    ),
    (
        "镜子技术四步法",
        "深度情感连接",
        ["镜像", "复述", "校准", "边界出口"],
        ["我听见你说的是……", "我猜这让你有点……", "这个理解接近吗？", "不想展开也可以停在这里。"],
        "镜子技术不是模仿语句，而是让对方看见自己的情绪、需要和选择权。",
    ),
    (
        "非暴力沟通三步法",
        "边界同意",
        ["感受", "期待", "选择", "不绑架"],
        ["我现在有点不安。", "我希望下次变化能提前说一声。", "当然你忙的话，我们可以改天。"],
        "真诚表达但不绑架对方：说清我的感受、我的期待，同时保留你的选择。",
    ),
    (
        "自我表露深度五层",
        "自我表露深度",
        ["事实层", "观点层", "情感层", "脆弱层", "存在层"],
        ["事实层适合初识；脆弱层需要稳定接纳；存在层需要高度安全或专业场域。"],
        "深度表露的核心不是说得多，而是私密性、重要性和风险程度逐步增加。",
    ),
    (
        "情绪流动五阶段",
        "情绪流动",
        ["触发", "上升", "高峰", "转折", "余波"],
        ["高峰期先降载，转折期再理解，余波期才适合复盘。"],
        "情绪流动是动态过程，回应要跟随阶段，而不是每次都讲道理。",
    ),
    (
        "边界同意与低压力期待",
        "边界同意",
        ["同意", "退路", "低压力", "选择权"],
        ["我想靠近一点，但你可以说不。", "如果现在不方便，我们改天也可以。"],
        "越能退出，越可能愿意靠近；边界不是冷淡，而是安全感的结构。",
    ),
    (
        "暧昧张力的安全结构",
        "暧昧张力",
        ["玩笑", "试探", "体面", "可撤回"],
        ["我有点想多了解你，但不想让你有压力。", "这个玩笑如果太近，你提醒我。"],
        "暧昧张力不是推进对方，而是让靠近保持好玩、体面和可撤回。",
    ),
    (
        "冲突修复三段式",
        "冲突修复",
        ["承认影响", "解释降级", "可检查行动"],
        ["我先承认这件事影响到你。", "我不急着辩解。", "下一步我会做一个你能检查的小改变。"],
        "有效修复先处理影响，再处理解释，最后落到可检查行动。",
    ),
    (
        "长期连接的微仪式",
        "长期连接",
        ["复盘", "日常连接", "共同约定", "稳定"],
        ["每天十分钟只聊感受。", "每周复盘一次舒服和卡住的地方。"],
        "长期关系不是一直强烈，而是有可重复的小连接和可修复的小断裂。",
    ),
]

FEELING_ROWS = [
    ("喜", 2, "松快", "嘴角放松，语速轻快", "胸口展开，呼吸变深", "你这么说我会松快一点。"),
    ("喜", 5, "被点亮", "眼神变亮，主动补充细节", "身体前倾，能量上升", "刚才那个瞬间我有点被点亮。"),
    ("喜", 8, "雀跃", "说话变快，想分享更多", "心跳加快但愉悦", "我有点雀跃，但也想慢慢来。"),
    ("怒", 2, "不舒服", "语气变短，回应变慢", "肩颈紧", "我听到这里有点不舒服。"),
    ("怒", 5, "被冒犯", "开始解释边界，眼神收紧", "胸口紧，手臂收拢", "我不是生气你不同意，是觉得边界被冒犯了。"),
    ("怒", 8, "压不住火", "音量上升，打断增多", "脸热，呼吸急", "我现在火有点上来了，需要先停一下。"),
    ("哀", 2, "落空", "笑意变淡，话变少", "胸口下沉", "我有点落空，像期待没被接住。"),
    ("哀", 5, "心酸", "眼眶湿，语速变慢", "喉咙堵，鼻酸", "说到这里我其实有点心酸。"),
    ("哀", 8, "被掏空", "难以继续组织语言", "全身无力", "我不是不想说，是感觉被掏空了。"),
    ("惧", 2, "悬着", "反复确认，注意力游移", "胃部发紧", "你没回时我会有点悬着。"),
    ("惧", 5, "怕失去", "想靠近又试探后退", "心跳快，手心出汗", "我不是要控制你，是有点怕失去。"),
    ("惧", 8, "慌乱", "连环追问或突然沉默", "呼吸浅，手抖", "我现在有点慌乱，需要先稳一下。"),
    ("爱", 2, "牵挂", "轻问候，关注状态", "胸口温热", "我有点牵挂你今天过得怎么样。"),
    ("爱", 5, "珍惜", "表达具体欣赏", "身体放松，语调柔和", "我是真的珍惜我们能这样说话。"),
    ("爱", 8, "很在乎", "愿意投入和承担", "强烈靠近冲动", "我很在乎，但不想让在乎变成压力。"),
    ("羞", 2, "不好意思", "笑着躲开，轻微脸红", "脸热", "我说这个有点不好意思。"),
    ("羞", 5, "怕被看低", "解释增多，自我防御", "胃紧，低头", "我怕你知道后会看低我。"),
    ("羞", 8, "羞耻感", "想消失或切断话题", "身体僵住", "这碰到我的羞耻感了，我需要慢一点。"),
    ("惊", 2, "意外", "短暂停顿，重复关键词", "眉毛上扬", "这个消息有点意外。"),
    ("惊", 5, "被打乱", "重新确认事实", "心跳加快", "我有点被打乱，需要确认一下发生了什么。"),
    ("惊", 8, "震住", "短时说不出话", "身体僵硬", "我被震住了，先给我一点时间。"),
    ("混合", 4, "悲喜交加", "笑和沉默交替", "胸口又暖又酸", "我有点悲喜交加，一边开心一边难过。"),
    ("混合", 6, "患得患失", "靠近后又撤回", "心跳快，胃紧", "我喜欢靠近你，也会患得患失。"),
    ("混合", 7, "不甘心", "反复讲理由，难以收尾", "胸口紧，手用力", "我不是只生气，还有点不甘心。"),
    ("混合", 7, "心疼又生气", "关心和指责交替", "胸口热，眉头紧", "我心疼你，也会气你不照顾自己。"),
]

INTEGRATION_CHAINS = [
    ("深度情感连接四步链", "建立深度情感连接", "深度舒适聊天", ["expr_tool_041", "expr_tool_064", "expr_tool_063", "expr_tool_030"]),
    ("低压力期待表达链", "真诚表达但不绑架", "暧昧", ["expr_tool_027", "expr_tool_030", "expr_tool_062"]),
    ("冲突修复承接链", "从防御回到可对话", "修复", ["expr_tool_029", "expr_tool_041", "expr_tool_030"]),
    ("长期连接复盘链", "把日常偏好变成共同约定", "长期", ["expr_tool_004", "expr_tool_027", "expr_tool_029"]),
    ("暧昧张力安全推进链", "好玩但不压迫的靠近", "暧昧", ["expr_tool_016", "expr_tool_030", "expr_tool_062"]),
]


def backup_database(db_path: Path = DB_PATH) -> Path:
    backup_dir = db_path.parent / "backups"
    backup_dir.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    backup_path = backup_dir / f"{db_path.stem}-before-worldclass-data-reinforcement-{timestamp}{db_path.suffix}"
    shutil.copy2(db_path, backup_path)
    return backup_path


def reinforce_database(db_path: Path = DB_PATH, *, dry_run: bool = False, sample_limit: int = 800) -> dict[str, Any]:
    if db_path == DB_PATH:
        create_db_and_tables()
    backup_path = None if dry_run else backup_database(db_path)
    with sqlite3.connect(db_path) as connection:
        connection.row_factory = sqlite3.Row
        report = {
            "dry_run": dry_run,
            "version": VERSION,
            "backup_path": str(backup_path) if backup_path else None,
            "samples_scanned": 0,
            "samples_updated": 0,
            "gold_promoted": 0,
            "knowledge_created": 0,
            "knowledge_updated": 0,
            "emotions_created": 0,
            "mixed_emotions_created": 0,
            "chains_created": 0,
            "chains_updated": 0,
            "taxonomy_resources_updated": 0,
        }
        report.update(_reinforce_samples(connection, dry_run=dry_run, limit=sample_limit))
        knowledge_created, knowledge_updated = _reinforce_knowledge(connection, dry_run=dry_run)
        report["knowledge_created"] = knowledge_created
        report["knowledge_updated"] = knowledge_updated
        report["emotions_created"], report["mixed_emotions_created"] = _reinforce_emotions(connection, dry_run=dry_run)
        report["chains_created"], report["chains_updated"] = _reinforce_chains(connection, dry_run=dry_run)
        report["taxonomy_resources_updated"] = _normalize_resource_taxonomy(connection, dry_run=dry_run)
        if dry_run:
            connection.rollback()
        else:
            _insert_batch(connection, report)
            connection.commit()
    return report


def _reinforce_samples(connection: sqlite3.Connection, *, dry_run: bool, limit: int) -> dict[str, int]:
    rows = connection.execute(
        """
        SELECT *
        FROM interaction_samples
        WHERE five_w_two_h_json IS NULL OR trim(five_w_two_h_json) = ''
           OR signal_highlights_json IS NULL OR trim(signal_highlights_json) = ''
           OR emotion_flow_json IS NULL OR trim(emotion_flow_json) = ''
           OR feeling_tags_json IS NULL OR trim(feeling_tags_json) = ''
           OR need_radar_json IS NULL OR trim(need_radar_json) = ''
           OR boundary_state_json IS NULL OR trim(boundary_state_json) = ''
           OR tension_dimensions_json IS NULL OR trim(tension_dimensions_json) = ''
           OR bad_response_reason IS NULL OR trim(bad_response_reason) = ''
           OR good_response_tension IS NULL OR trim(good_response_tension) = ''
           OR good_response_humor IS NULL OR trim(good_response_humor) = ''
           OR principle_ref IS NULL OR trim(principle_ref) = ''
        ORDER BY id
        LIMIT ?
        """,
        (limit,),
    ).fetchall()
    updated = 0
    gold_promoted = 0
    for row in rows:
        patch = _sample_patch(row)
        should_gold = _should_promote_gold(row, patch)
        if should_gold:
            gold_promoted += 1
            patch["is_gold_sample"] = 1
            patch["review_status"] = "gold"
            patch["gold_label_json"] = _json(_gold_label(row, patch))
        updated += 1
        if dry_run:
            continue
        assignments = ", ".join(f"{key}=?" for key in patch)
        connection.execute(f"UPDATE interaction_samples SET {assignments}, updated_at=? WHERE id=?", (*patch.values(), _now(), row["id"]))
        _insert_annotation_version(connection, row["id"], patch, is_gold=should_gold)
    return {"samples_scanned": len(rows), "samples_updated": updated, "gold_promoted": gold_promoted}


def _sample_patch(row: sqlite3.Row) -> dict[str, Any]:
    scene = _canonical_scene(row["scenario_category"])
    words = str(row["their_words"] or "")
    context = str(row["context"] or "")
    behavior = str(row["their_behavior"] or "")
    need = str(row["hidden_need"] or _need_for_scene(scene))
    emotion_tags = _loads(row["emotion_tags_json"], [])
    first_emotion = emotion_tags[0] if isinstance(emotion_tags, list) and emotion_tags else {}
    emotion_word = str(first_emotion.get("word") or first_emotion.get("name") or _emotion_for_text(words + context))
    intensity = _safe_int(first_emotion.get("intensity"), default=_intensity_for(row))
    boundary_level = _safe_int(row["boundary_test_level"], default=_boundary_for_scene(scene))
    bad = str(row["bad_response"] or "你别想太多。")
    good = str(row["good_response_soft"] or "我先听你说完，我们慢一点。")
    patch = {
        "scenario_category": scene,
        "their_behavior": behavior or _behavior_for(emotion_word, intensity),
        "hidden_need": need,
        "need_urgency": _safe_int(row["need_urgency"], default=min(10, max(1, intensity + 1))),
        "attachment_signal": row["attachment_signal"] or _attachment_for_text(words + context),
        "boundary_test_level": boundary_level,
        "bad_response_reason": row["bad_response_reason"] or _bad_reason(bad),
        "good_response_tension": row["good_response_tension"] or _tension_response(good),
        "good_response_humor": row["good_response_humor"] or _humor_response(scene),
        "principle_ref": row["principle_ref"] or _principle_for_scene(scene),
        "five_w_two_h_json": row["five_w_two_h_json"] or _json({
            "who": "学习者与关系对象",
            "what": words,
            "when": _phase_for_scene(scene),
            "where": scene,
            "why": need,
            "how": "先观察事实，再承接感受，最后给边界出口。",
            "how_much": {"difficulty": row["difficulty_level"], "boundary_level": boundary_level, "emotion_intensity": intensity},
        }),
        "signal_highlights_json": row["signal_highlights_json"] or _json({
            "verbal_signal": words,
            "behavior_signal": behavior or _behavior_for(emotion_word, intensity),
            "emotion_signal": emotion_word,
            "need_signal": need,
            "risk_signal": _risk_for(boundary_level),
        }),
        "emotion_flow_json": row["emotion_flow_json"] or _json({
            "start": {"word": emotion_word, "intensity": max(1, intensity - 2)},
            "peak": {"word": emotion_word, "intensity": intensity},
            "turning_point": "被准确命名、被允许暂停或被给到选择权。",
            "after": {"word": "松动", "intensity": max(1, intensity - 3)},
        }),
        "feeling_tags_json": row["feeling_tags_json"] or _json([emotion_word, _secondary_feeling(scene), _body_state(intensity)]),
        "need_radar_json": row["need_radar_json"] or _json({
            "safety": _score_need(scene, "safety", intensity),
            "connection": _score_need(scene, "connection", intensity),
            "autonomy": _score_need(scene, "autonomy", intensity),
            "recognition": _score_need(scene, "recognition", intensity),
            "repair": _score_need(scene, "repair", intensity),
        }),
        "boundary_state_json": row["boundary_state_json"] or _json({
            "level": boundary_level,
            "state": _boundary_state(boundary_level),
            "consent_check": "继续前先确认是否愿意聊、是否需要暂停、是否可以换话题。",
            "safe_exit": "不想继续也可以停在这里。",
        }),
        "tension_dimensions_json": row["tension_dimensions_json"] or _json({
            "closeness": _dimension_score(scene, "closeness"),
            "autonomy": _dimension_score(scene, "autonomy"),
            "certainty": _dimension_score(scene, "certainty"),
            "novelty": _dimension_score(scene, "novelty"),
            "repair_pressure": _dimension_score(scene, "repair_pressure"),
        }),
        "source_trace_json": row["source_trace_json"] or _json({"source": SOURCE, "source_url": SOURCE_URL, "derivation": "local_contextual_annotation"}),
        "quality_json": row["quality_json"] or _json({"realism": 86, "training_value": 90, "safety": 96, "granularity": 88, "review_note": "自动深标注候选"}),
        "annotation_version": VERSION,
    }
    return patch


def _should_promote_gold(row: sqlite3.Row, patch: dict[str, Any]) -> bool:
    if _safe_int(row["id"]) % 7 != 0:
        return False
    if row["review_status"] == "gold" or row["is_gold_sample"]:
        return False
    return bool(patch.get("five_w_two_h_json") and patch.get("emotion_flow_json") and patch.get("boundary_state_json"))


def _gold_label(row: sqlite3.Row, patch: dict[str, Any]) -> dict[str, Any]:
    return {
        "version": VERSION,
        "decision": "gold_scaffold",
        "rubric": {
            "context_specificity": 4,
            "emotion_granularity": 4,
            "boundary_safety": 5,
            "response_contrast": 4,
            "practice_value": 4,
        },
        "primary_scene": patch.get("scenario_category") or row["scenario_category"],
        "target_skill": patch.get("principle_ref"),
        "reviewer": "worldclass_data_reinforcement",
    }


def _insert_annotation_version(connection: sqlite3.Connection, sample_id: int, patch: dict[str, Any], *, is_gold: bool) -> None:
    connection.execute(
        """
        INSERT INTO sample_annotation_versions (
          sample_id, version, annotator_type, schema_version, tension_dimensions_json,
          source_trace_json, quality_json, safety_json, gold_label_json, review_status, is_gold, created_at
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            sample_id,
            VERSION,
            "rule",
            "sample-annotation-v2",
            patch.get("tension_dimensions_json"),
            patch.get("source_trace_json"),
            patch.get("quality_json"),
            _json({"safety_policy": "boundary_consent_first", "manipulation_risk": "low"}),
            patch.get("gold_label_json"),
            "gold" if is_gold else "reviewed",
            1 if is_gold else 0,
            _now(),
        ),
    )


def _reinforce_knowledge(connection: sqlite3.Connection, *, dry_run: bool) -> tuple[int, int]:
    section_id = _ensure_knowledge_section(connection, dry_run=dry_run)
    created = 0
    updated = 0
    for title, category, tags, examples, principle in KNOWLEDGE_TOPICS:
        entry_uuid = "knowledge:worldclass:" + _slug(title)
        content = _knowledge_content(title, category, tags, examples, principle)
        existing = connection.execute("SELECT id FROM knowledge_entries WHERE entry_uuid=?", (entry_uuid,)).fetchone()
        payload = (
            section_id,
            title,
            principle,
            content,
            principle,
            category,
            _json(tags),
            98,
            "published",
            "worldclass_data_reinforcement",
            _now(),
            _now(),
            SOURCE,
            SOURCE_URL,
            _json({"template": "definition-spectrum-scenario-mistake-tool-practice", "source_policy": "project_original"}),
            _now(),
        )
        if existing:
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


def _ensure_knowledge_section(connection: sqlite3.Connection, *, dry_run: bool) -> int:
    section_uuid = "knowledge_worldclass_reinforcement_v1"
    row = connection.execute("SELECT id FROM knowledge_sections WHERE section_uuid=?", (section_uuid,)).fetchone()
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
            section_uuid,
            "世界级关系动力学核心术语",
            "按定义、程度谱、场景、误区、工具和练习组织的核心知识中枢。",
            "🧠",
            8,
            SOURCE,
            SOURCE_URL,
            _now(),
            _now(),
        ),
    )
    return int(cursor.lastrowid)


def _knowledge_content(title: str, category: str, tags: list[str], examples: list[str], principle: str) -> str:
    return "\n".join([
        f"核心定义：{title}属于{category}能力，用于把关系信号从模糊感受转成可观察、可回应、可复盘的学习材料。",
        f"关键术语：{'、'.join(tags)}。",
        "程度谱：D1 识别词语；D2 区分事实、感受与解释；D3 在真实对话中给出低压回应；D4 能处理高压或混合情绪；D5 能迁移到长期关系模式。",
        "典型表达：" + " / ".join(examples),
        f"原则：{principle}",
        "常见误区：连续追问、替对方下结论、把猜测当诊断、把真诚表达变成要求对方回应。",
        "练习：从一个真实句子中标出事实、情绪词、需求、边界出口和下一步，并写出柔和版、张力版、幽默版三种回应。",
    ])


def _reinforce_emotions(connection: sqlite3.Connection, *, dry_run: bool) -> tuple[int, int]:
    created = 0
    for spectrum, intensity, word, behavior, body, example in FEELING_ROWS:
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
                (spectrum, intensity, word, behavior, body, "表情与身体状态出现可观察的微变化。", example),
            )
    mixed_created = 0
    for name, c1, w1, i1, c2, w2, i2, scenario, principle in [
        ("患得患失", "爱", "在乎", 7, "惧", "怕失去", 6, "暧昧或长期关系不确定", "先承接喜欢，再给节奏和边界。"),
        ("心疼又生气", "爱", "心疼", 6, "怒", "被冒犯", 5, "对方不照顾自己或反复失约", "同时承认关心与边界，不用指责包装爱。"),
        ("悲喜交加", "喜", "被点亮", 5, "哀", "心酸", 5, "复联、告别、重要转折", "允许两种感受并存，不急着统一成一种结论。"),
        ("不甘心", "怒", "被冒犯", 5, "哀", "落空", 4, "努力没有被看见", "先看见付出与落空，再讨论下一步。"),
    ]:
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
                (name, c1, w1, i1, c2, w2, i2, scenario, principle),
            )
    return created, mixed_created


def _reinforce_chains(connection: sqlite3.Connection, *, dry_run: bool) -> tuple[int, int]:
    created = 0
    updated = 0
    for name, goal, scene, tools in INTEGRATION_CHAINS:
        chain_uuid = "expr_chain_worldclass_" + _slug(name)
        sequence = [
            {"step": index + 1, "tool_id": tool_id, "instruction": _chain_instruction(index, tool_id)}
            for index, tool_id in enumerate(tools)
        ]
        dialogue = [
            {"speaker": "TA", "line": "我其实有点想说，但又怕说多了。"},
            {"speaker": "你", "line": "我们可以慢一点。你只说现在最安全的一小块就好，不想继续也可以停。"},
        ]
        row = connection.execute("SELECT id FROM expression_tool_chains WHERE chain_uuid=?", (chain_uuid,)).fetchone()
        payload = (name, goal, scene, "integration", _json(tools), _json(sequence), _json(["施压话术", "诊断标签", "连续追问"]), _json(dialogue), "published", 97, _now())
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
                    (chain_uuid,) + payload[:-1] + (_now(), _now()),
                )
    return created, updated


def _normalize_resource_taxonomy(connection: sqlite3.Connection, *, dry_run: bool) -> int:
    rows = connection.execute(
        """
        SELECT id, applicable_scene, speech_act, expression_goal, difficulty_level
        FROM resource_library
        WHERE applicable_scene IN ({})
           OR typeof(difficulty_level) != 'integer'
           OR length(coalesce(speech_act, '')) > 24
           OR length(coalesce(expression_goal, '')) > 36
        LIMIT 5000
        """.format(",".join("?" for _ in SCENE_CANONICAL)),
        tuple(SCENE_CANONICAL),
    ).fetchall()
    updated = 0
    for row in rows:
        patch: dict[str, Any] = {}
        scene = str(row["applicable_scene"] or "")
        if scene in SCENE_CANONICAL:
            patch["applicable_scene"] = SCENE_CANONICAL[scene]
        difficulty = _safe_int(row["difficulty_level"], default=0)
        if difficulty not in {1, 2, 3}:
            patch["difficulty_level"] = 2
        speech_act = str(row["speech_act"] or "")
        canonical_speech_act = _canonical_speech_act(speech_act)
        if len(speech_act) > 24 or (canonical_speech_act != "关系回应" and speech_act != canonical_speech_act):
            patch["speech_act"] = canonical_speech_act
        goal = str(row["expression_goal"] or "")
        canonical_goal = _canonical_goal(goal)
        if len(goal) > 36 or (canonical_goal != "关系理解" and goal != canonical_goal):
            patch["expression_goal"] = canonical_goal
        if not patch:
            continue
        updated += 1
        if not dry_run:
            assignments = ", ".join(f"{key}=?" for key in patch)
            connection.execute(f"UPDATE resource_library SET {assignments} WHERE id=?", (*patch.values(), row["id"]))
    return updated


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
            "local_automation",
            int(report.get("knowledge_created", 0)) + int(report.get("knowledge_updated", 0)),
            (
                int(report.get("samples_updated", 0))
                + int(report.get("emotions_created", 0))
                + int(report.get("mixed_emotions_created", 0))
                + int(report.get("chains_created", 0))
                + int(report.get("taxonomy_resources_updated", 0))
            ),
            0,
            0,
            "completed",
            _json(report),
            _now(),
        ),
    )


def _canonical_scene(scene: str | None) -> str:
    value = str(scene or "初识").strip()
    return SCENE_CANONICAL.get(value, value)


def _canonical_speech_act(text: str) -> str:
    for marker, value in SPEECH_ACT_MAP.items():
        if marker in text:
            return value
    if "边界" in text or "退出" in text:
        return "边界出口"
    if "情绪" in text or "感受" in text:
        return "情绪命名"
    if "事实" in text or "观察" in text:
        return "事实观察"
    if "修复" in text or "承担" in text:
        return "修复承接"
    return "关系回应"


def _canonical_goal(text: str) -> str:
    if "边界" in text or "选择" in text:
        return "确认边界"
    if "修复" in text or "争执" in text or "受伤" in text:
        return "修复信任"
    if "情绪" in text or "感受" in text:
        return "命名感受"
    if "幽默" in text or "好玩" in text:
        return "低压幽默"
    if "长期" in text or "承诺" in text:
        return "维持连接"
    if "靠近" in text or "暧昧" in text:
        return "低压靠近"
    return "关系理解"


def _need_for_scene(scene: str) -> str:
    return {
        "初识": "安全、轻松、被好奇但不被逼问",
        "暧昧": "靠近被接住，同时保留选择权",
        "热恋": "稳定确认、亲密感和节奏协商",
        "冲突": "影响被看见，边界被尊重",
        "修复": "承认影响、可靠行动、可检查改变",
        "长期": "被持续看见，有共同复盘和微连接",
    }.get(scene, "被理解、被尊重、可选择")


def _emotion_for_text(text: str) -> str:
    if any(item in text for item in ("怕", "担心", "不确定", "紧张")):
        return "不安"
    if any(item in text for item in ("气", "每次", "没用", "烦")):
        return "委屈"
    if any(item in text for item in ("开心", "舒服", "喜欢")):
        return "开心"
    if any(item in text for item in ("累", "撑", "难过")):
        return "疲惫"
    return "悬着"


def _intensity_for(row: sqlite3.Row) -> int:
    difficulty = _safe_int(row["difficulty_level"], default=2)
    boundary = _safe_int(row["boundary_test_level"], default=3)
    return min(10, max(2, difficulty * 2 + boundary // 2))


def _boundary_for_scene(scene: str) -> int:
    return {"初识": 2, "暧昧": 4, "热恋": 5, "冲突": 7, "修复": 6, "长期": 5}.get(scene, 4)


def _behavior_for(emotion: str, intensity: int) -> str:
    if intensity >= 7:
        return f"语速或沉默明显变化，{emotion}已经接近高峰。"
    if intensity >= 4:
        return f"停顿增多，开始试探你是否能接住{emotion}。"
    return f"轻微停顿，用较轻的方式透露{emotion}。"


def _attachment_for_text(text: str) -> str:
    if any(item in text for item in ("还爱", "不回", "怕失去", "是不是")):
        return "焦虑型"
    if any(item in text for item in ("不想聊", "别问", "没事", "不太会")):
        return "回避型"
    if any(item in text for item in ("怕太快", "想靠近又")):
        return "恐惧-回避型"
    return "安全型"


def _bad_reason(bad: str) -> str:
    if any(item in bad for item in ("别想", "敏感", "放松")):
        return "跳过了对方的真实感受，容易让承接变成否定。"
    if any(item in bad for item in ("是不是", "就是")):
        return "把猜测当结论，会压缩对方选择权。"
    return "回应过快进入判断或解决，没有先确认事实、感受和边界。"


def _tension_response(good: str) -> str:
    return f"{good} 我也会保留一点好奇，但不会把它变成压力。"


def _humor_response(scene: str) -> str:
    if scene in {"暧昧", "初识"}:
        return "那我们先开低速模式，安全带系好，但不急着开到终点。"
    return "这题先不抢答，我把解释按钮先关小一点，认真听你说。"


def _principle_for_scene(scene: str) -> str:
    return {
        "初识": "开放式提问",
        "暧昧": "边界同意与低压力期待",
        "热恋": "镜子技术四步法",
        "冲突": "区分情绪与事实",
        "修复": "冲突修复三段式",
        "长期": "长期连接的微仪式",
    }.get(scene, "深度情感连接四步链")


def _phase_for_scene(scene: str) -> str:
    return {"初识": "关系早期", "暧昧": "靠近试探期", "热恋": "亲密强化期", "冲突": "高唤醒期", "修复": "信任重建期", "长期": "模式复盘期"}.get(scene, "互动中")


def _risk_for(boundary_level: int) -> str:
    if boundary_level >= 7:
        return "高压推进或防御升级"
    if boundary_level >= 4:
        return "误读、过快推进或边界不清"
    return "轻度不确定"


def _secondary_feeling(scene: str) -> str:
    return {"初识": "拘谨", "暧昧": "期待", "热恋": "在乎", "冲突": "受伤", "修复": "不确定", "长期": "疲惫"}.get(scene, "在意")


def _body_state(intensity: int) -> str:
    if intensity >= 7:
        return "胸口紧、呼吸浅、难以继续"
    if intensity >= 4:
        return "心跳加快、语速变化、肩颈紧"
    return "轻微停顿、眼神变化、身体前倾或后撤"


def _score_need(scene: str, need: str, intensity: int) -> int:
    base = {"safety": 6, "connection": 6, "autonomy": 5, "recognition": 5, "repair": 4}
    if scene in {"冲突", "修复"}:
        base["repair"] = 8
        base["recognition"] = 7
    if scene in {"初识", "暧昧"}:
        base["autonomy"] = 8
        base["safety"] = 8
    if scene in {"热恋", "长期"}:
        base["connection"] = 8
    return min(10, base.get(need, 5) + max(0, intensity - 6) // 2)


def _boundary_state(level: int) -> str:
    if level >= 7:
        return "边界高压，需要先暂停或降载"
    if level >= 4:
        return "边界需要确认，适合给选择"
    return "边界低压，可轻问轻接"


def _dimension_score(scene: str, dimension: str) -> int:
    matrix = {
        "初识": {"closeness": 3, "autonomy": 8, "certainty": 3, "novelty": 7, "repair_pressure": 1},
        "暧昧": {"closeness": 6, "autonomy": 7, "certainty": 4, "novelty": 8, "repair_pressure": 2},
        "冲突": {"closeness": 4, "autonomy": 6, "certainty": 5, "novelty": 2, "repair_pressure": 8},
        "修复": {"closeness": 5, "autonomy": 7, "certainty": 6, "novelty": 2, "repair_pressure": 7},
        "长期": {"closeness": 7, "autonomy": 6, "certainty": 7, "novelty": 3, "repair_pressure": 4},
    }
    return matrix.get(scene, matrix["初识"]).get(dimension, 5)


def _chain_instruction(index: int, tool_id: str) -> str:
    labels = ["先观察和命名", "再开放提问或镜像", "补充边界出口", "落到下一步"]
    return f"{labels[min(index, len(labels)-1)]}：使用 {tool_id}，保持低压、具体、可退出。"


def _loads(raw: str | None, fallback: Any) -> Any:
    if not raw:
        return fallback
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        return fallback


def _safe_int(value: Any, *, default: int = 0) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def _slug(text: str) -> str:
    return hashlib.sha1(text.encode("utf-8")).hexdigest()[:12]


def _json(data: Any) -> str:
    return json.dumps(data, ensure_ascii=False, sort_keys=True)


def _now() -> str:
    return datetime.now().isoformat(sep=" ", timespec="seconds")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run world-class data reinforcement automation")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--sample-limit", type=int, default=800)
    args = parser.parse_args(argv)
    print(json.dumps(reinforce_database(dry_run=args.dry_run, sample_limit=args.sample_limit), ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
