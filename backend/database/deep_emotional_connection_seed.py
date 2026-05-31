"""Seed deep emotional connection materials.

This pack extends the existing deep-comfort chat system with a four-step
mirror technique: open question, keyword capture, fact/emotion split, and
calibrated reflection. It creates project-original knowledge, one expression
chain, and practice resources.
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

from backend.database.connection import DB_PATH, create_db_and_tables

SOURCE = "project_original:deep_emotional_connection_v1"
SOURCE_URL = "local_anchor:深度情感连接_镜子技术四步法"
SECTION_UUID = "knowledge_deep_emotional_connection_v1"
CHAIN_UUID = "expr_chain_deep_emotional_connection_mirror_v1"
PIPELINE_VERSION = "deep_emotional_connection_v1"

FOUR_STEPS = [
    ("开放式提问", "用“怎么、哪一刻、什么变化”打开空间，避免是非题和审问感。"),
    ("捕捉关键词", "抓住对方重复、加重、停顿前后的词，把注意力放回他的真实世界。"),
    ("区分事实与情绪", "先说事实层，再说感受层，避免把解释、评价和诊断混在一起。"),
    ("镜子校准", "像镜子一样照回你听见的层次，并邀请对方纠正你。"),
]

SCENARIOS: list[dict[str, str]] = [
    {
        "key": "硬撑感",
        "scene": "社交",
        "setting": "朋友说最近总觉得自己在硬撑，语气很轻，但说完停了两秒。",
        "their_words": "我最近总觉得自己在硬撑。",
        "keyword": "硬撑",
        "fact": "事情还在继续推进，他没有完全停下来。",
        "emotion": "疲惫、孤独、希望有人真正看见。",
        "bad": "别想太多，你已经很棒了。",
        "better": "我听见你说“硬撑”。事实上你还在把事情往前推，但感受上像一直没人真正接住你。这个理解接近吗？你愿意从最累的一个细节说起吗？",
    },
    {
        "key": "突然安静",
        "scene": "暧昧",
        "setting": "暧昧聊天里，对方说今天突然很安静，不像平时那么活跃。",
        "their_words": "我今天突然很安静，也不知道为什么。",
        "keyword": "安静",
        "fact": "聊天输出变少，主动分享降低。",
        "emotion": "可能是低能量、想被陪着、又怕扫兴。",
        "bad": "那你开心点嘛，别这么丧。",
        "better": "我听见的是“安静”，不是你不想理人。现实上是你今天能量低了一点，感受上可能想有人陪着但不被要求活跃。这个说法贴近吗？",
    },
    {
        "key": "工作卡住",
        "scene": "职场",
        "setting": "同事说项目卡住，反复提到“没人对齐”。",
        "their_words": "项目不是做不动，是一直没人对齐。",
        "keyword": "没人对齐",
        "fact": "项目推进受阻，协作信息不同步。",
        "emotion": "无力、烦躁、承担过多责任。",
        "bad": "那你开个会不就好了。",
        "better": "我抓到你反复说“没人对齐”。事实层是协作没有同步，情绪层更像你一个人在兜底，所以才会累。是这个感觉吗？",
    },
    {
        "key": "关系不确定",
        "scene": "长期",
        "setting": "伴侣说不是不喜欢，只是不确定未来能不能一起走下去。",
        "their_words": "我不是不喜欢你，只是有时候会不确定。",
        "keyword": "不确定",
        "fact": "喜欢仍在，但未来图景不稳定。",
        "emotion": "在意、害怕承诺落空、需要更稳的节奏。",
        "bad": "你不确定就是不够爱。",
        "better": "我听见两个层次：事实上你不是否定喜欢，感受上是对未来节奏有点悬。我们可以先不逼结论，只看哪一件事最让你不确定。",
    },
    {
        "key": "冲突后沉默",
        "scene": "修复",
        "setting": "争执后对方说自己不知道该怎么开口，明显还在防御。",
        "their_words": "我不知道怎么开口，怕一说又吵起来。",
        "keyword": "怕又吵",
        "fact": "对方没有关闭关系，但害怕再次升级。",
        "emotion": "害怕、谨慎、想修复但缺安全感。",
        "bad": "你不说怎么解决？",
        "better": "我听见你不是不想说，而是怕一开口又变成争吵。事实层是你还在这里，情绪层是需要一个不会升级的空间。我们可以先只说十分钟。",
    },
]


def backup_database(db_path: Path = DB_PATH) -> Path:
    backup_dir = db_path.parent / "backups"
    backup_dir.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    backup_path = backup_dir / f"{db_path.stem}-before-deep-emotional-connection-{timestamp}{db_path.suffix}"
    copy2(db_path, backup_path)
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
            "created_chains": 0,
            "updated_chains": 0,
            "created_resources": 0,
            "skipped_resources": 0,
            "backup_path": str(backup_path) if backup_path else None,
        }
        section_id, section_created = _upsert_section(connection, dry_run=dry_run)
        report["created_sections"] += int(section_created)
        entry_created, entry_updated = _upsert_entry(connection, section_id, dry_run=dry_run)
        report["created_entries"] += int(entry_created)
        report["updated_entries"] += int(entry_updated)
        chain_created, chain_updated = _upsert_chain(connection, dry_run=dry_run)
        report["created_chains"] += int(chain_created)
        report["updated_chains"] += int(chain_updated)
        created, skipped = _seed_resources(connection, dry_run=dry_run)
        report["created_resources"] += created
        report["skipped_resources"] += skipped
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
            "深度情感连接与镜子技术",
            "通过开放式提问、关键词捕捉、事实情绪区分和镜子校准，让对方感到被真正理解。",
            "🪞",
            14,
            SOURCE,
            SOURCE_URL,
            _now(),
            _now(),
        ),
    )
    return int(cursor.lastrowid), True


def _upsert_entry(connection: sqlite3.Connection, section_id: int, *, dry_run: bool) -> tuple[bool, bool]:
    entry_uuid = "knowledge:deep-emotional-connection:mirror-four-step"
    content = _entry_content()
    metadata = {
        "template_version": PIPELINE_VERSION,
        "steps": [{"name": name, "description": description} for name, description in FOUR_STEPS],
        "quality_contract": "每次镜像都必须允许对方纠正；不得把猜测伪装成诊断。",
    }
    payload = (
        section_id,
        "深度情感连接：镜子技术四步法",
        "开放式提问 -> 捕捉关键词 -> 区分事实与情绪 -> 镜子校准。",
        content,
        "帮助对方感到被真正理解，而不是被盘问、被分析或被套话术。",
        "深度情感连接",
        _json(["深度情感连接", "镜子技术", "开放式提问", "关键词捕捉", "事实情绪区分", "情绪共鸣"]),
        99,
        "published",
        "deep_emotional_connection_seed",
        _now(),
        _now(),
        SOURCE,
        SOURCE_URL,
        _json(metadata),
        _now(),
        entry_uuid,
    )
    existing = connection.execute("SELECT id FROM knowledge_entries WHERE entry_uuid=?", (entry_uuid,)).fetchone()
    if dry_run:
        return (not bool(existing), bool(existing))
    if existing:
        connection.execute(
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
        return False, True
    connection.execute(
        """
        INSERT INTO knowledge_entries (
          section_id, title, subtitle, content, summary, category, tags_json,
          quality_score, review_status, reviewer_id, reviewed_at, published_at,
          source, source_id, source_metadata_json, updated_at, entry_uuid, created_at
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (*payload, _now()),
    )
    return True, False


def _upsert_chain(connection: sqlite3.Connection, *, dry_run: bool) -> tuple[bool, bool]:
    payload = (
        "深度情感连接镜子链",
        "建立深度情感连接",
        "社交/暧昧/长期/修复",
        "D3 镜子校准",
        _json(["expr_tool_027", "expr_tool_011", "expr_tool_041", "expr_tool_042", "expr_tool_056"]),
        _json([
            {"order": 1, "tool": "开放式提问", "action": "用一个不逼迫的开放问题打开空间。"},
            {"order": 2, "tool": "关键词捕捉", "action": "抓住对方重复或停顿前后的核心词。"},
            {"order": 3, "tool": "事实情绪区分", "action": "先照事实，再照感受，不混成评判。"},
            {"order": 4, "tool": "镜子校准", "action": "把理解照回去，并邀请对方纠正。"},
        ]),
        _json(["审问式追问", "心理诊断", "把猜测当结论", "深聊逼供", "没有退出权"]),
        _json({
            "before": "你怎么会这样想？具体说说，为什么不开心？",
            "after": "我听见你反复说“硬撑”。事实上你还在推进，感受上像没人接住你。这个理解接近吗？不想展开也可以。",
        }),
        "published",
        99,
        _now(),
        CHAIN_UUID,
    )
    existing = connection.execute("SELECT id FROM expression_tool_chains WHERE chain_uuid=?", (CHAIN_UUID,)).fetchone()
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
            payload,
        )
        return False, True
    connection.execute(
        """
        INSERT INTO expression_tool_chains (
          name, goal, scene, stage, tool_ids_json, sequence_json, forbidden_tools_json,
          example_dialogue_json, review_status, quality_score, updated_at, chain_uuid, created_at
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (*payload, _now()),
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


def _resource_payload(scenario: dict[str, str], difficulty: int) -> dict[str, Any]:
    blueprint = _blueprint(scenario, difficulty)
    content = _content(blueprint)
    content_unit = f"deep_emotional_connection::{scenario['key']}::D{difficulty}"
    signature = "|".join([SOURCE, content_unit, blueprint["better_response"]])
    return {
        "resource_uuid": f"deep-emotional-connection:{uuid.uuid5(uuid.NAMESPACE_URL, signature)}",
        "type": "game",
        "category": "深度情感连接·镜子技术",
        "title": f"{scenario['key']}｜镜子技术四步法｜D{difficulty}",
        "content": content,
        "emotional_tone_json": _json({"primary": "深度情感连接", "scene": scenario["scene"], "keyword": scenario["keyword"]}),
        "emotional_intensity": min(10, 5 + difficulty),
        "applicable_scene": scenario["scene"],
        "difficulty_level": difficulty,
        "gender_target": "通用",
        "attachment_suitability": "通用",
        "usage_tip": "先照见关键词，再区分事实和情绪，最后邀请对方纠正；不要把镜像变成诊断。",
        "effectiveness_rating": 9,
        "source": SOURCE,
        "source_url": SOURCE_URL,
        "tags": ",".join(["具体案例", "深度情感连接", "镜子技术", "开放式提问", "关键词捕捉", scenario["scene"], f"difficulty:{difficulty}"]),
        "review_status": "published",
        "reviewer_id": "deep_emotional_connection_seed",
        "source_title": "深度情感连接：镜子技术四步法",
        "source_excerpt": "项目原创训练卡；由用户提供模式转化，不保存第三方全文。",
        "source_summary": "开放式提问、关键词捕捉、事实情绪区分和镜子校准组成深度情感连接路径。",
        "source_license": "project_original_from_user_provided_pattern",
        "quality_score": 98,
        "expression_tool_ids_json": _json(["expr_tool_027", "expr_tool_011", "expr_tool_041", "expr_tool_042", "expr_tool_056"]),
        "expression_goal": "建立深度情感连接",
        "expression_level": f"D{difficulty}",
        "speech_act": "开放提问 / 关键词镜像 / 情绪校准 / 边界出口",
        "mistake_pattern": blueprint["common_mistake"],
        "recommended_drills_json": _json([
            {"type": "open_question", "prompt": "把封闭问题改成一个开放式问题。"},
            {"type": "mirror", "prompt": "写出事实层和情绪层各一句镜像。"},
            {"type": "boundary", "prompt": "补一句允许对方不答或纠正你的出口。"},
        ]),
        "case_blueprint_json": _json(blueprint),
        "variant_signature": "sha256:" + _hash(signature),
        "content_unit": content_unit,
        "coverage_axis": "deep_emotional_connection",
        "variant_family": "deep_emotional_connection_mirror",
        "case_completeness_score": 100,
        "content_fingerprint": "sha256:" + _hash(content),
    }


def _blueprint(scenario: dict[str, str], difficulty: int) -> dict[str, Any]:
    mirror = _mirror_response(scenario, difficulty)
    return {
        "version": PIPELINE_VERSION,
        "axis": "deep_emotional_connection",
        "axis_label": "深度情感连接",
        "scene": scenario["scene"],
        "setting": scenario["setting"],
        "their_words": scenario["their_words"],
        "keyword": scenario["keyword"],
        "fact_layer": scenario["fact"],
        "emotion_layer": scenario["emotion"],
        "common_mistake": f"把深聊做成盘问或诊断；旧回应通常会说：{scenario['bad']}",
        "why_wrong": "深度连接来自被准确照见，而不是被迫暴露；必须允许对方纠正你的理解。",
        "better_response": mirror,
        "dialogue_script": [
            {"speaker": "TA", "line": scenario["their_words"], "purpose": "原始信号"},
            {"speaker": "低质量回应", "line": scenario["bad"], "purpose": "打断情绪或催促解决"},
            {"speaker": "更好回应", "line": mirror, "purpose": "开放提问、关键词捕捉、事实情绪区分、镜子校准"},
            {"speaker": "TA", "line": "嗯，差不多，就是那种没人真的接住的感觉。", "purpose": "被理解后补充深层状态"},
            {"speaker": "继续回应", "line": "那我们先不急着解决，只从最明显的一件事开始。", "purpose": "保留节奏和边界"},
        ],
        "response_steps": [f"{name}：{description}" for name, description in FOUR_STEPS],
        "boundary_note": "镜子技术不是读心术；每一次镜像都要允许“不对，你理解偏了”。",
        "practice_task": f"把“{scenario['bad']}”改写为：开放式问题 + 关键词“{scenario['keyword']}” + 事实层 + 情绪层 + 校准出口。",
        "transfer_scene": "迁移到暧昧、职场压力、冲突修复或长期关系不确定感。",
        "difficulty_contract": {
            1: "D1：能问开放问题并抓关键词。",
            2: "D2：能区分事实层和情绪层。",
            3: "D3：能完成镜子校准并保留边界出口。",
        }[difficulty],
    }


def _mirror_response(scenario: dict[str, str], difficulty: int) -> str:
    base = (
        f"我听见你说“{scenario['keyword']}”。事实层是：{scenario['fact']}；"
        f"感受层可能是：{scenario['emotion']}。这个理解接近吗？"
    )
    if difficulty == 1:
        return f"你愿意说说“{scenario['keyword']}”最明显出现在哪一刻吗？"
    if difficulty == 2:
        return base
    return f"{base} 如果我问得太深，你可以纠正我，或者我们先停在这里。"


def _content(blueprint: dict[str, Any]) -> str:
    dialogue = "；".join(f"{turn['speaker']}：{turn['line']}" for turn in blueprint["dialogue_script"])
    return "\n".join(
        [
            f"案例定位：{blueprint['axis_label']} / 镜子技术四步法 / {blueprint['difficulty_contract']}",
            f"场景：{blueprint['setting']}",
            f"TA说：{blueprint['their_words']}",
            f"关键词：{blueprint['keyword']}",
            f"事实层：{blueprint['fact_layer']}",
            f"情绪层：{blueprint['emotion_layer']}",
            f"完整对话：{dialogue}",
            f"常见失误：{blueprint['common_mistake']}",
            f"为什么错：{blueprint['why_wrong']}",
            f"更好回应：{blueprint['better_response']}",
            "四步拆解：" + "；".join(blueprint["response_steps"]),
            f"边界提醒：{blueprint['boundary_note']}",
            f"练习任务：{blueprint['practice_task']}",
            f"迁移场景：{blueprint['transfer_scene']}",
        ]
    )


def _entry_content() -> str:
    return "\n".join(
        [
            "深度情感连接的目标不是让对方暴露更多，而是让对方感到：我在这里可以更接近真实的自己。",
            "",
            "四步法：",
            *[f"{index}. {name}：{description}" for index, (name, description) in enumerate(FOUR_STEPS, start=1)],
            "",
            "标准句式：我听见你反复说“关键词”。事实层像是……；感受层可能是……。这个理解接近吗？如果不对你可以纠正我。",
            "",
            "质量边界：不诊断、不逼供、不把猜测当真相、不用深聊套取隐私。真正的镜子会照见，也允许对方说“不是这样”。",
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
            "project_original_seed",
            int(report["created_sections"]),
            int(report["created_entries"]) + int(report["created_chains"]) + int(report["created_resources"]),
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
    parser = argparse.ArgumentParser(description="Seed deep emotional connection mirror materials.")
    parser.add_argument("--db", type=Path, default=DB_PATH)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    print(json.dumps(seed(args.db, dry_run=args.dry_run), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
