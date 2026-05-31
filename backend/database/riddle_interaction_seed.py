"""Seed project-original riddle interaction resources.

These are not scraped joke collections. Each item is a small relationship
training card: a low-pressure riddle, the risky way to use it, a better
contextual delivery, boundary notes, and transfer practice.
"""

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

SOURCE = "project_original:riddle_interaction_seed_v1"
SOURCE_URL = "local_anchor:脑筋急转弯低压互动训练卡"
VERSION = "riddle_interaction_seed_v1"

SCENE_PACKS: tuple[dict[str, str], ...] = (
    {
        "key": "轻破冰",
        "scene": "初识",
        "setting": "刚认识的聊天开始变安静，你想用一个很轻的急转弯降低尴尬。",
        "their_words": "你来一个不尴尬的脑筋急转弯吧。",
        "need": "轻松、可接可不接，不被考验智商。",
        "goal": "打开低压入口",
    },
    {
        "key": "暧昧试探",
        "scene": "暧昧",
        "setting": "聊天有一点靠近，但你不确定对方愿不愿意接暧昧梗。",
        "their_words": "你最近说话怎么老是拐弯？",
        "need": "一点靠近感，同时保留退路。",
        "goal": "低压靠近",
    },
    {
        "key": "低压赞美",
        "scene": "社交",
        "setting": "你想夸对方，但不想让赞美显得油腻或像套路。",
        "their_words": "你别突然夸我，我会不知道怎么回。",
        "need": "被看见，但不被迫回应。",
        "goal": "具体欣赏",
    },
    {
        "key": "冲突降温",
        "scene": "冲突",
        "setting": "气氛有点紧，你想用轻问答降温，但不能逃避问题。",
        "their_words": "你是不是又想用玩笑带过去？",
        "need": "影响被承认，气氛能慢慢降下来。",
        "goal": "降低防御",
    },
    {
        "key": "修复开口",
        "scene": "修复",
        "setting": "争执后你想重新开口，但对方还没有完全放松。",
        "their_words": "我现在还没那么想聊。",
        "need": "被尊重节奏，不被催着和好。",
        "goal": "修复信任",
    },
    {
        "key": "边界确认",
        "scene": "分歧",
        "setting": "对方不确定要不要继续这个话题，你想保留轻松，也说明可以停。",
        "their_words": "这个问题我不太想继续答。",
        "need": "选择权清楚，不被继续追问。",
        "goal": "确认边界",
    },
    {
        "key": "异地连接",
        "scene": "异地",
        "setting": "异地聊天只剩报平安，你想补一点轻松连接。",
        "their_words": "到家了，我有点困。",
        "need": "被惦记，但不被额外消耗。",
        "goal": "维持连接",
    },
    {
        "key": "长期保鲜",
        "scene": "长期",
        "setting": "长期关系里日常变得很熟，你想用小谜题制造一点新鲜感。",
        "their_words": "我们最近好像每天都在聊同样的事。",
        "need": "熟悉里有新鲜，稳定里有一点玩心。",
        "goal": "增加新鲜感",
    },
)

MECHANISMS: tuple[dict[str, str], ...] = (
    {"key": "留门", "category": "低压急转弯", "riddle": "什么门最适合刚认识的人？", "answer": "留一扇小门，想聊就进来，不想聊也能轻轻出去。"},
    {"key": "天气", "category": "场景急转弯", "riddle": "哪种天气最适合把话说轻一点？", "answer": "微风，因为它靠近你，但不会把你吹倒。"},
    {"key": "灯光", "category": "观察急转弯", "riddle": "什么灯最会聊天？", "answer": "小夜灯，只照亮一点点，不逼人马上看清全部。"},
    {"key": "地图", "category": "关系急转弯", "riddle": "什么地图最适合两个人一起看？", "answer": "可以折起来的地图，走累了就先停在这里。"},
    {"key": "钥匙", "category": "边界急转弯", "riddle": "什么钥匙最安全？", "answer": "只开自己的门，不偷偷替别人决定要不要打开。"},
    {"key": "回声", "category": "共情急转弯", "riddle": "什么回声最让人舒服？", "answer": "不是重复你的话，而是让我知道你真的听见了。"},
)


def backup_database(db_path: Path = DB_PATH) -> Path:
    backup_dir = db_path.parent / "backups"
    backup_dir.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    backup_path = backup_dir / f"{db_path.stem}-before-riddle-interaction-seed-{timestamp}{db_path.suffix}"
    shutil.copy2(db_path, backup_path)
    return backup_path


def seed(db_path: Path = DB_PATH, *, dry_run: bool = False) -> dict[str, Any]:
    if db_path == DB_PATH:
        create_db_and_tables()
    backup_path: Path | None = None
    if not dry_run:
        backup_path = backup_database(db_path)
    report = {
        "dry_run": dry_run,
        "source": SOURCE,
        "created_resources": 0,
        "updated_resources": 0,
        "skipped_resources": 0,
        "backup_path": str(backup_path) if backup_path else None,
    }
    with sqlite3.connect(db_path) as connection:
        connection.row_factory = sqlite3.Row
        for resource in _resources():
            existing = connection.execute(
                "SELECT id FROM resource_library WHERE resource_uuid = ? OR content_unit = ?",
                (resource["resource_uuid"], resource["content_unit"]),
            ).fetchone()
            if existing:
                report["skipped_resources"] += 1
                if not dry_run:
                    _update_resource(connection, int(existing["id"]), resource)
                    report["updated_resources"] += 1
                continue
            report["created_resources"] += 1
            if not dry_run:
                _insert_resource(connection, resource)
        if not dry_run:
            _insert_batch(connection, report)
            connection.commit()
        else:
            connection.rollback()
    return report


def _resources() -> list[dict[str, Any]]:
    resources: list[dict[str, Any]] = []
    for scene in SCENE_PACKS:
        for mechanism in MECHANISMS:
            for difficulty in (1, 2, 3):
                resources.append(_resource_payload(scene, mechanism, difficulty))
    return resources


def _resource_payload(scene: dict[str, str], mechanism: dict[str, str], difficulty: int) -> dict[str, Any]:
    blueprint = _blueprint(scene, mechanism, difficulty)
    content = _content(blueprint)
    content_unit = "|".join(["riddle_interaction", scene["key"], mechanism["key"], f"D{difficulty}"])
    signature = "|".join([SOURCE, content_unit, blueprint["riddle"], blueprint["answer"]])
    return {
        "resource_uuid": f"riddle-interaction:{uuid.uuid5(uuid.NAMESPACE_URL, signature)}",
        "type": "riddle",
        "category": mechanism["category"],
        "title": f"{scene['scene']}｜{scene['key']}｜{mechanism['key']}｜D{difficulty}",
        "content": content,
        "emotional_tone_json": _json({"primary": "低压幽默", "scene": scene["scene"], "mechanism": mechanism["key"]}),
        "emotional_intensity": 3 + difficulty,
        "applicable_scene": scene["scene"],
        "difficulty_level": difficulty,
        "gender_target": "通用",
        "attachment_suitability": "通用",
        "usage_tip": "急转弯不是考倒对方，而是给聊天一个可轻松接住的小入口；对方不接就收回。",
        "effectiveness_rating": 8 + min(difficulty, 2),
        "source": SOURCE,
        "source_url": SOURCE_URL,
        "tags": ",".join(["脑筋急转弯", "低压幽默", "可拒绝出口", "完整对话", scene["scene"], scene["goal"], f"difficulty:{difficulty}"]),
        "review_status": "published",
        "reviewer_id": "riddle_interaction_seed",
        "source_title": "脑筋急转弯低压互动训练卡",
        "source_excerpt": "项目原创结构化训练卡；不保存第三方谜题全文。",
        "source_summary": "把脑筋急转弯转化为低压力破冰、暧昧试探、冲突降温和长期保鲜的可练习互动素材。",
        "source_license": "project_original_no_third_party_full_text",
        "content_fingerprint": "sha256:" + _hash(content),
        "quality_score": 96,
        "expression_tool_ids_json": _json(["expr_tool_016", "expr_tool_011", "expr_tool_019"]),
        "expression_goal": scene["goal"],
        "expression_level": f"D{difficulty}",
        "speech_act": "低压破冰 / 幽默试探 / 边界收束",
        "mistake_pattern": blueprint["common_mistake"],
        "recommended_drills_json": _json(_drills(blueprint)),
        "case_blueprint_json": _json(blueprint),
        "variant_signature": "sha256:" + _hash(signature),
        "content_unit": content_unit,
        "coverage_axis": blueprint["axis"],
        "variant_family": f"riddle_interaction|{scene['key']}|{mechanism['category']}",
        "case_completeness_score": 98,
    }


def _blueprint(scene: dict[str, str], mechanism: dict[str, str], difficulty: int) -> dict[str, Any]:
    riddle = mechanism["riddle"]
    answer = _answer_for(scene, mechanism)
    better = _better_response(scene, riddle, answer, difficulty)
    return {
        "version": VERSION,
        "axis": _axis_for(scene["goal"]),
        "axis_label": _axis_label_for(scene["goal"]),
        "resource_type": "riddle",
        "resource_type_label": "脑筋急转弯训练卡",
        "scene": scene["scene"],
        "relation_stage": scene["key"],
        "category": mechanism["category"],
        "title": f"{scene['key']} / {mechanism['key']}",
        "setting": scene["setting"],
        "trigger": scene["their_words"],
        "riddle": riddle,
        "answer": answer,
        "their_words": scene["their_words"],
        "surface_signal": "对方给了一个可轻松互动的入口，但也可能是在测试你会不会有压迫感。",
        "deeper_need": scene["need"],
        "common_mistake": f"把急转弯当智商测试或强行撩；旧回应通常会说：这都猜不到？你也太没默契了吧。",
        "why_wrong": "急转弯的价值是降低压力，不是让对方难堪；一旦变成考试、嘲笑或强撩，就会破坏安全感。",
        "better_response": better,
        "dialogue_script": _dialogue_script(scene, riddle, answer, better, difficulty),
        "response_steps": _response_steps(difficulty),
        "response_variants": _response_variants(scene, riddle, answer),
        "perspective_examples": _perspective_examples(scene),
        "transfer_analysis": _transfer_analysis(scene),
        "boundary_note": "对方猜不出、没兴趣、沉默或转移话题时，立刻把谜底说轻，并允许换话题。",
        "practice_task": f"把“{riddle}”换到一个真实聊天场景里，写出 D{difficulty} 版本：谜面、谜底、轻解释、可退出句。",
        "transfer_scene": f"迁移到另一个{scene['scene']}片段，保留低压、可退出、不过度解释三条原则。",
        "quality_notes": {
            "version": VERSION,
            "specificity": 24,
            "playfulness": 22,
            "boundary_clarity": 22,
            "practice_ready": 22,
            "source_trace": 10,
        },
    }


def _answer_for(scene: dict[str, str], mechanism: dict[str, str]) -> str:
    answer = mechanism["answer"]
    if scene["scene"] in {"冲突", "修复"}:
        return f"{answer} 放在这里就是：先让气氛松一点，再回到真正要处理的事。"
    if scene["scene"] in {"暧昧", "社交"}:
        return f"{answer} 放在这里就是：有一点靠近，但不逼对方接梗。"
    if scene["scene"] == "异地":
        return f"{answer} 放在这里就是：给一点连接，不额外消耗对方。"
    return answer


def _better_response(scene: dict[str, str], riddle: str, answer: str, difficulty: int) -> str:
    base = f"我来一个很轻的：{riddle} 答案是：{answer}"
    if difficulty == 1:
        return f"{base} 猜不到也没关系，我只是想让气氛松一点。"
    if difficulty == 2:
        return f"{base} 如果这个梗你接不住，我马上收回；你也可以出一个更冷的给我。"
    return f"{base} 我想用它轻轻开个口，不是把刚才的话题带过去；如果你愿意，我们等下再回到你真正想说的部分。"


def _dialogue_script(scene: dict[str, str], riddle: str, answer: str, better: str, difficulty: int) -> list[dict[str, str]]:
    script = [
        {"speaker": "TA", "line": scene["their_words"], "purpose": "原始信号"},
        {"speaker": "低质量回应", "line": "这都猜不到？你也太没默契了吧。", "purpose": "把轻互动变成压力"},
        {"speaker": "更好回应", "line": better, "purpose": "低压抛出谜面并保留退路"},
        {"speaker": "TA", "line": "这样还挺轻松的，我可以接一下。", "purpose": "对方愿意继续互动"},
        {"speaker": "继续回应", "line": f"那我把谜底说完就停：{answer}。我们不用硬聊，舒服就好。", "purpose": "解释但不过度推进"},
        {"speaker": "边界收束", "line": "如果你现在没兴趣，我们换个话题也完全可以。", "purpose": "确认退出空间"},
    ]
    return script[: 3 + difficulty]


def _response_steps(difficulty: int) -> list[str]:
    steps = ["先判断气氛是否能接梗", "用一句短谜面降低进入成本", "立刻说明猜不到也没关系"]
    if difficulty >= 2:
        steps.append("补一个可反击或可换题的出口")
    if difficulty >= 3:
        steps.append("承认真正议题没有被玩笑取消，必要时回到正题")
    return steps


def _response_variants(scene: dict[str, str], riddle: str, answer: str) -> list[dict[str, str]]:
    return [
        {"label": "轻量破冰版", "response": f"{riddle} 猜不到也没事，我只是想开个很轻的小口。", "why_it_works": "降低答题压力。"},
        {"label": "暧昧低压版", "response": f"{riddle} 答案有点靠近，但你不想接我也会收住。", "why_it_works": "有张力，也有退路。"},
        {"label": "冲突降温版", "response": f"我先用一个小谜题把气氛放轻，不代表我想逃避刚才的问题。", "why_it_works": "幽默服务修复，不遮盖影响。"},
        {"label": "边界稳态版", "response": f"答案是：{answer} 如果你没兴趣，我们停在这里就好。", "why_it_works": "谜底和退出权一起给出。"},
        {"label": "迁移练习版", "response": f"把这个梗换到“{scene['key']}”，重写一句不让人有压力的开场。", "why_it_works": "训练结构迁移，而不是背谜底。"},
    ]


def _perspective_examples(scene: dict[str, str]) -> list[dict[str, str]]:
    return [
        {"label": "对方视角", "what_they_may_feel": f"我需要的是{scene['need']}，不是被考验反应速度。", "learning_point": "看对方是否愿意接梗，而不是看自己梗多不多。"},
        {"label": "自己视角", "what_you_may_feel": "你可能想靠幽默证明自己有趣。", "learning_point": "先降表现欲，幽默才会变成舒服感。"},
        {"label": "关系视角", "what_is_happening": "急转弯是在制造一个小共同注意点。", "learning_point": "共同轻松比谜底本身更重要。"},
        {"label": "边界视角", "what_must_stay_safe": "任何玩笑都必须可撤回、可跳过、可换话题。", "learning_point": "对方不接梗不是失败，是边界信号。"},
    ]


def _transfer_analysis(scene: dict[str, str]) -> dict[str, Any]:
    return {
        "target_scene": f"{scene['scene']}中的另一个真实聊天片段",
        "stable_principles": ["低压力", "可退出", "不过度解释", "不把猜不到当失败"],
        "changeable_parameters": ["谜面长度", "暧昧浓度", "是否回到正题", "文字或面对面语气"],
        "self_check_questions": [
            "这句谜面会不会让对方像在考试？",
            "我有没有给出猜不到也没关系？",
            "如果对方不接，我能不能自然收回？",
            "这个梗是否符合当前关系熟度？",
        ],
    }


def _content(blueprint: dict[str, Any]) -> str:
    dialogue = "；".join(f"{turn['speaker']}：{turn['line']}" for turn in blueprint["dialogue_script"])
    return "\n".join(
        [
            f"类型：脑筋急转弯 / {blueprint['category']} / {blueprint['scene']}",
            f"场景故事：{blueprint['setting']}",
            f"TA说：{blueprint['their_words']}",
            f"谜面：{blueprint['riddle']}",
            f"谜底：{blueprint['answer']}",
            f"完整对话：{dialogue}",
            f"深层需要：{blueprint['deeper_need']}",
            f"常见失误：{blueprint['common_mistake']}",
            f"为什么错：{blueprint['why_wrong']}",
            f"更好回应：{blueprint['better_response']}",
            "回应拆解：" + "；".join(blueprint["response_steps"]),
            f"边界提醒：{blueprint['boundary_note']}",
            f"练习任务：{blueprint['practice_task']}",
            f"迁移场景：{blueprint['transfer_scene']}",
        ]
    )


def _drills(blueprint: dict[str, Any]) -> list[dict[str, str]]:
    return [
        {"type": "observe", "prompt": "判断当前气氛是否适合抛出谜面。"},
        {"type": "rewrite", "prompt": blueprint["practice_task"]},
        {"type": "boundary", "prompt": "写一句对方不接梗时的自然收回句。"},
    ]


def _axis_for(goal: str) -> str:
    if "修复" in goal:
        return "conflict_repair"
    if "边界" in goal:
        return "boundary_consent"
    if "连接" in goal or "新鲜" in goal:
        return "long_connection"
    if "靠近" in goal or "欣赏" in goal:
        return "flirty_tension"
    return "humor_interaction"


def _axis_label_for(goal: str) -> str:
    return {
        "conflict_repair": "冲突修复",
        "boundary_consent": "边界与同意",
        "long_connection": "长期连接",
        "flirty_tension": "暧昧张力",
        "humor_interaction": "幽默互动",
    }[_axis_for(goal)]


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
        _resource_values(resource, now),
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
        _resource_values(resource, now, for_update=True) + (resource_id,),
    )


def _resource_values(resource: dict[str, Any], now: str, *, for_update: bool = False) -> tuple[Any, ...]:
    values = (
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
    )
    if for_update:
        return values
    return (resource["resource_uuid"],) + values[:15] + (now,) + values[15:]


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
            "resource_seed",
            0,
            report["created_resources"],
            report["skipped_resources"],
            0,
            "completed",
            _json(report),
            _now(),
        ),
    )


def _now() -> str:
    return datetime.now().isoformat(timespec="seconds")


def _hash(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _json(data: Any) -> str:
    return json.dumps(data, ensure_ascii=False, sort_keys=True)


def main() -> None:
    parser = argparse.ArgumentParser(description="Seed project-original riddle interaction resources.")
    parser.add_argument("--db", type=Path, default=DB_PATH)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    print(json.dumps(seed(args.db, dry_run=args.dry_run), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
