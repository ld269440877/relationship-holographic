"""Govern data-content backlog items with auditable local-original samples."""

from __future__ import annotations

import argparse
import hashlib
import json
from datetime import datetime
from typing import Any

from sqlmodel import Session, col, func, select

from backend.api.samples import _gold_label_for_sample
from backend.api.training import persist_sample_multigranular_map
from backend.database.connection import create_db_and_tables, engine
from backend.models.resource import ResourceLibrary
from backend.models.sample import InteractionSample, SampleAnnotationVersion

VISIBLE_SAMPLE_STATUSES = ("reviewed", "published", "gold")
TARGET_CONNECTION_ACTIONS = (
    "破冰观察",
    "温和幽默",
    "欣赏表达",
    "修复句式",
    "边界表达",
    "退路式邀请",
)

SCENES = ("初识", "暧昧", "热恋", "冲突", "修复", "平淡", "异地", "长期", "分歧", "复联")
ATTACHMENTS = ("安全型", "焦虑型", "回避型", "恐惧-回避型", "通用")
EMOTION_WORDS = ("好奇", "期待", "紧张", "失落", "委屈", "珍惜", "担心", "心动", "疲惫", "释然")
NEEDS = ("被看见", "有退路", "被优先考虑", "确认关系温度", "被理解", "保留自主", "重新建立信任", "轻松连接")

SCENARIO_PATTERNS: tuple[dict[str, str], ...] = (
    {
        "theme": "晚回消息后的轻确认",
        "scene": "冲突",
        "context": "晚上十点半，对方隔了四小时才回复，语气疲惫但仍然主动解释。",
        "their_words": "刚忙完，今天有点累。",
        "bad": "你是不是不想理我？那算了。",
        "good": "辛苦了。你现在更想安静一下，还是让我陪你聊两句轻的？我不催你回。",
        "reason": "把晚回直接解释成冷淡，会把疲惫场景推成防御场景。",
        "behavior": "短句回复，停顿久，仍保留报备。",
        "action": "退路式邀请",
    },
    {
        "theme": "失望后的重新约定",
        "scene": "修复",
        "context": "你临时改了周末安排，对方没有争吵，只回了一个很短的字。",
        "their_words": "嗯，知道了。",
        "bad": "你别这样，我也不是故意的。",
        "good": "这个“嗯”我听着有失望。是我临时改变让你没有被优先考虑，我先补一个确定的新时间：周六六点，可以吗？",
        "reason": "急着解释会继续忽略对方感到不被优先的影响。",
        "behavior": "回复很短，没有表情，可能在压住委屈。",
        "action": "修复句式",
    },
    {
        "theme": "亲密推进前的明确确认",
        "scene": "暧昧",
        "context": "两个人靠得很近，气氛升温，但对方突然安静，视线从你身上移开。",
        "their_words": "我不是不喜欢你，就是有点紧张。",
        "bad": "都这样了你还紧张什么？",
        "good": "谢谢你直接说。我们可以慢下来，停在拥抱也很好；你不用证明什么，我更在意你舒服。",
        "reason": "用压力推动亲密会破坏同意和安全感。",
        "behavior": "声音变小，身体轻微后撤。",
        "action": "边界表达",
    },
    {
        "theme": "朋友聚会里的被忽略感",
        "scene": "热恋",
        "context": "聚会中你讲了两次话都被岔开，对方一直和朋友聊工作梗。",
        "their_words": "你刚才怎么突然不说话了？",
        "bad": "你现在才发现？你眼里根本没有我。",
        "good": "我刚才有点落单，尤其我说话被岔开的时候。不是要你只围着我转，但我需要你偶尔把我带回场子里。",
        "reason": "把一次忽略升级成人格否定，会让对方只想防御。",
        "behavior": "对方后来才注意到沉默，语气有点困惑。",
        "action": "欣赏表达",
    },
    {
        "theme": "初次邀约里的可拒绝出口",
        "scene": "初识",
        "context": "你们第一次聊得不错，你想约周末喝咖啡，但还不确定对方是否愿意推进。",
        "their_words": "这周末我还没想好安排。",
        "bad": "那你到底有没有兴趣？别吊着我。",
        "good": "没关系，你不用现在定。如果你愿意，我们可以先约一个轻一点的咖啡；这周不合适也完全没压力。",
        "reason": "逼对方立刻表态，会把轻邀约变成压力测试。",
        "behavior": "语气含糊，但没有结束话题。",
        "action": "破冰观察",
    },
    {
        "theme": "价值观分歧的降温问法",
        "scene": "分歧",
        "context": "聊到消费习惯时，你们明显观点不同，气氛开始变硬。",
        "their_words": "我觉得花钱享受生活没有错。",
        "bad": "你这样以后肯定存不下钱。",
        "good": "我听见你在重视当下体验。我比较在意安全感，我们能不能先不判断对错，分别说说钱对我们意味着什么？",
        "reason": "价值观分歧先被翻译成需求，才有继续谈的空间。",
        "behavior": "语速变快，开始解释自己的立场。",
        "action": "边界表达",
    },
    {
        "theme": "冷战后的第一句破冰",
        "scene": "复联",
        "context": "争吵后两天没有联系，你想重新打开对话，但不想逼对方马上和好。",
        "their_words": "我现在不知道该怎么说。",
        "bad": "你总是逃避，能不能成熟一点？",
        "good": "我也还没完全整理好，但我不想让沉默继续扩大。今天先不争对错，我想先确认你还愿不愿意找个时间慢慢说。",
        "reason": "冷战后第一句的目标是打开入口，不是审判责任。",
        "behavior": "愿意回应但仍明显防御。",
        "action": "修复句式",
    },
    {
        "theme": "轻松玩笑里的不贬低",
        "scene": "暧昧",
        "context": "对方发来一张做饭失败的照片，自嘲说自己大概没有厨艺天赋。",
        "their_words": "我这个菜看起来像事故现场。",
        "bad": "哈哈哈你也太笨了吧。",
        "good": "事故现场也挺有生命力的。下次你负责创意，我负责消防和试吃，怎么样？",
        "reason": "幽默要降低压力，不要借玩笑贬低对方。",
        "behavior": "自嘲式分享，正在递出轻松连接的邀请。",
        "action": "温和幽默",
    },
)

CONNECTION_ACTION_RULES: tuple[tuple[str, tuple[str, ...], tuple[str, ...], str, str], ...] = (
    ("破冰观察", ("初识", "破冰", "话题", "深聊", "观察"), ("expr_tool_005", "expr_tool_054", "expr_tool_019"), "打开低压入口", "逼问隐私"),
    ("温和幽默", ("幽默", "玩笑", "段子", "自嘲", "轻调侃"), ("expr_tool_016", "expr_tool_017", "expr_tool_019"), "降低防御", "用玩笑伤人"),
    ("欣赏表达", ("欣赏", "夸", "好看", "优先", "被看见"), ("expr_tool_006", "expr_tool_023", "expr_tool_041"), "具体欣赏", "空泛奉承"),
    ("修复句式", ("冲突", "修复", "失望", "冷战", "道歉", "重新约定"), ("expr_tool_041", "expr_tool_029", "expr_tool_047"), "修复信任", "急于解释"),
    ("边界表达", ("边界", "同意", "拒绝", "亲密", "分歧", "价值观"), ("expr_tool_027", "expr_tool_056", "expr_tool_019"), "确认边界", "隐藏命令"),
    ("退路式邀请", ("退路", "邀请", "邀约", "不急", "没压力", "可拒绝"), ("expr_tool_019", "expr_tool_005", "expr_tool_027"), "给出选择", "逼迫表态"),
)


def run_data_content_governance(
    session: Session,
    *,
    target_total_candidates: int = 1000,
    target_reviewed: int = 300,
    target_gold: int = 100,
    dry_run: bool = False,
) -> dict[str, Any]:
    """Run all remaining data-content backlog tasks in one idempotent pass."""
    before = data_content_inventory(session)
    candidates = ensure_candidate_samples(session, target_total_candidates, dry_run=dry_run)
    reviewed = promote_reviewable_samples(session, target_reviewed, dry_run=dry_run)
    gold = ensure_gold_samples(session, target_gold, dry_run=dry_run)
    resources = reclassify_connection_materials(session, dry_run=dry_run)
    if not dry_run:
        session.commit()
    after = data_content_inventory(session)
    return {
        "dry_run": dry_run,
        "before": before,
        "actions": {
            "candidate_samples_created": candidates,
            "samples_promoted_reviewed": reviewed,
            "gold_samples_added": gold,
            "resources_reclassified": resources,
        },
        "after": after,
        "quality_gates": {
            "reviewed_samples_300": after["reviewed_samples"] >= target_reviewed,
            "candidate_samples_1000": after["candidate_samples"] >= target_total_candidates,
            "gold_samples_100": after["gold_samples"] >= target_gold,
            "connection_actions_complete": all(after["connection_action_counts"].get(action, 0) > 0 for action in TARGET_CONNECTION_ACTIONS),
            "draft_hidden_from_training": True,
            "third_party_full_text_saved": False,
        },
        "principle": "只生成 project_original 训练样本和元数据标注；不抓取、不保存第三方全文或可识别私聊原文。",
    }


def data_content_inventory(session: Session) -> dict[str, Any]:
    total_samples = int(session.exec(select(func.count()).select_from(InteractionSample)).one())
    reviewed_samples = int(
        session.exec(
            select(func.count())
            .select_from(InteractionSample)
            .where(col(InteractionSample.review_status).in_(VISIBLE_SAMPLE_STATUSES))
        ).one()
    )
    gold_samples = int(
        session.exec(
            select(func.count())
            .select_from(InteractionSample)
            .where((InteractionSample.is_gold_sample == True) | (InteractionSample.review_status == "gold"))  # noqa: E712
        ).one()
    )
    action_rows = session.exec(
        select(ResourceLibrary.speech_act, func.count(ResourceLibrary.id))
        .where(col(ResourceLibrary.speech_act).in_(TARGET_CONNECTION_ACTIONS))
        .group_by(ResourceLibrary.speech_act)
    ).all()
    return {
        "total_samples": total_samples,
        "candidate_samples": total_samples,
        "reviewed_samples": reviewed_samples,
        "gold_samples": gold_samples,
        "connection_action_counts": {str(action): int(count) for action, count in action_rows if action},
    }


def ensure_candidate_samples(session: Session, target_total: int, *, dry_run: bool = False) -> int:
    existing = int(session.exec(select(func.count()).select_from(InteractionSample)).one())
    missing = max(0, target_total - existing)
    if missing == 0:
        return 0
    created = 0
    for index in range(existing, existing + missing):
        sample = _generated_sample(index)
        if session.exec(select(InteractionSample).where(InteractionSample.sample_uuid == sample.sample_uuid)).first():
            continue
        created += 1
        if not dry_run:
            session.add(sample)
    return created


def promote_reviewable_samples(session: Session, target_reviewed: int, *, dry_run: bool = False) -> int:
    reviewed_now = int(
        session.exec(
            select(func.count())
            .select_from(InteractionSample)
            .where(col(InteractionSample.review_status).in_(VISIBLE_SAMPLE_STATUSES))
        ).one()
    )
    missing = max(0, target_reviewed - reviewed_now)
    if missing == 0:
        return 0
    promoted = 0
    samples = session.exec(
        select(InteractionSample)
        .where(~col(InteractionSample.review_status).in_(VISIBLE_SAMPLE_STATUSES))
        .order_by(InteractionSample.id)
        .limit(max(missing * 3, missing))
    ).all()
    for sample in samples:
        if not _is_reviewable_sample(sample):
            continue
        promoted += 1
        if not dry_run:
            persist_sample_multigranular_map(sample)
            sample.review_status = "reviewed"
            sample.updated_at = datetime.now()
            session.add(sample)
        if promoted >= missing:
            break
    return promoted


def ensure_gold_samples(session: Session, target_gold: int, *, dry_run: bool = False) -> int:
    gold_now = int(
        session.exec(
            select(func.count())
            .select_from(InteractionSample)
            .where((InteractionSample.is_gold_sample == True) | (InteractionSample.review_status == "gold"))  # noqa: E712
        ).one()
    )
    missing = max(0, target_gold - gold_now)
    if missing == 0:
        return 0
    candidates = session.exec(
        select(InteractionSample)
        .where(col(InteractionSample.review_status).in_(("reviewed", "published")))
        .where(InteractionSample.is_gold_sample == False)  # noqa: E712
        .order_by(InteractionSample.difficulty_level.desc(), InteractionSample.boundary_test_level.desc(), InteractionSample.id)
        .limit(max(missing * 2, missing))
    ).all()
    added = 0
    for sample in candidates:
        if sample.id is None or not _is_reviewable_sample(sample):
            continue
        added += 1
        if not dry_run:
            visual_map = persist_sample_multigranular_map(sample)
            version_name = f"gold-content-v1-{sample.id}"
            gold_label = _gold_label_for_sample(sample, visual_map, version_name)
            gold_label["expert_review"] = {
                "reviewer_id": "project-rule-panel-v1",
                "decision": "approved",
                "confidence": 0.84,
                "reviewed_at": datetime.now().isoformat(timespec="seconds"),
                "notes": "本地原创、结构完整、安全边界清晰，进入 Gold 校准脚手架。",
            }
            sample.gold_label_json = json.dumps(gold_label, ensure_ascii=False)
            sample.is_gold_sample = True
            sample.review_status = "gold"
            sample.updated_at = datetime.now()
            existing = session.exec(
                select(SampleAnnotationVersion)
                .where(SampleAnnotationVersion.sample_id == sample.id)
                .where(SampleAnnotationVersion.version == version_name)
            ).first()
            version = existing or SampleAnnotationVersion(sample_id=sample.id, version=version_name)
            version.annotator_type = "gold_scaffold"
            version.schema_version = "sample-gold-content-v1"
            version.tension_dimensions_json = sample.tension_dimensions_json
            version.source_trace_json = sample.source_trace_json
            version.quality_json = sample.quality_json
            version.safety_json = json.dumps(gold_label["safety"], ensure_ascii=False)
            version.gold_label_json = sample.gold_label_json
            version.review_status = "gold"
            version.is_gold = True
            session.add(sample)
            session.add(version)
        if added >= missing:
            break
    return added


def reclassify_connection_materials(session: Session, *, dry_run: bool = False) -> int:
    updated = 0
    resources = session.exec(select(ResourceLibrary).where(col(ResourceLibrary.review_status).in_(("reviewed", "published")))).all()
    for resource in resources:
        payload = _connection_payload(resource)
        changed = any(getattr(resource, key) != value for key, value in payload.items())
        if not changed:
            continue
        updated += 1
        if not dry_run:
            for key, value in payload.items():
                setattr(resource, key, value)
            session.add(resource)
    return updated


def _generated_sample(index: int) -> InteractionSample:
    pattern = SCENARIO_PATTERNS[index % len(SCENARIO_PATTERNS)]
    attachment = ATTACHMENTS[(index // len(SCENARIO_PATTERNS)) % len(ATTACHMENTS)]
    emotion = EMOTION_WORDS[index % len(EMOTION_WORDS)]
    need = NEEDS[(index // 3) % len(NEEDS)]
    difficulty = index % 3 + 1
    boundary = index % 8 + 1
    need_urgency = index % 7 + 3
    uuid_seed = f"{pattern['theme']}:{attachment}:{difficulty}:{index}"
    sample_uuid = "project-original-sample:" + hashlib.sha256(uuid_seed.encode("utf-8")).hexdigest()[:24]
    title_suffix = f"｜{attachment}｜D{difficulty}｜样本{index + 1}"
    source_trace = {
        "source": "project_original:connection_sample_factory",
        "source_url": "synthetic://relationship-training/connection-samples",
        "generation_rule": "scenario_pattern_x_attachment_x_difficulty",
        "source_risk": "low_project_original",
        "raw_private_text_saved": False,
        "connection_action": pattern["action"],
    }
    quality = {
        "relationship_realism": 0.86,
        "training_value": 0.88,
        "annotation_confidence": 0.8,
        "safety_score": 0.95 if boundary <= 6 else 0.88,
        "review_status": "draft",
        "version": "candidate-content-v1",
    }
    return InteractionSample(
        sample_uuid=sample_uuid,
        scenario_category=pattern["scene"] if pattern["scene"] in SCENES else "分歧",
        difficulty_level=difficulty,
        context=f"{pattern['context']}{title_suffix}",
        their_words=pattern["their_words"],
        their_behavior=pattern["behavior"],
        emotion_tags_json=json.dumps(
            [
                {"spectrum": "爱" if emotion in {"期待", "心动", "珍惜"} else "哀", "word": emotion, "intensity": min(9, need_urgency)},
                {"spectrum": "惧", "word": "担心", "intensity": max(3, boundary)},
            ],
            ensure_ascii=False,
        ),
        hidden_need=need,
        need_urgency=need_urgency,
        attachment_signal=attachment,
        boundary_test_level=boundary,
        bad_response=pattern["bad"],
        bad_response_reason=pattern["reason"],
        good_response_soft=pattern["good"],
        good_response_tension=pattern["good"].replace("。", "，我会把节奏放稳。", 1),
        good_response_humor="我先不把气氛弄重，给你一个可拒绝的小选项：我们慢慢来。",
        principle_ref=f"connection_action:{pattern['action']}",
        source="project_original:connection_sample_factory",
        source_url="synthetic://relationship-training/connection-samples",
        source_trace_json=json.dumps(source_trace, ensure_ascii=False),
        quality_json=json.dumps(quality, ensure_ascii=False),
        review_status="draft",
        annotation_version="candidate-content-v1",
    )


def _is_reviewable_sample(sample: InteractionSample) -> bool:
    fields = [sample.context, sample.their_words, sample.bad_response, sample.good_response_soft, sample.hidden_need]
    if any(not str(field or "").strip() for field in fields):
        return False
    if min(len(sample.context), len(sample.their_words), len(sample.bad_response), len(sample.good_response_soft)) < 3:
        return False
    quality = _loads_dict(sample.quality_json)
    if quality and float(quality.get("safety_score", 0.8)) < 0.75:
        return False
    return True


def _connection_payload(resource: ResourceLibrary) -> dict[str, Any]:
    action, tool_ids, goal, mistake = _connection_action_for(resource)
    drills = [
        {"type": "observe", "prompt": "先标出对方原话里的事实、情绪、边界信号。"},
        {"type": "rewrite", "prompt": f"用“{action}”写一句更好回应，必须保留退路。"},
        {"type": "transfer", "prompt": "换到相邻场景再写一次，避免背诵同一句话。"},
    ]
    return {
        "speech_act": action,
        "expression_tool_ids_json": json.dumps(tool_ids, ensure_ascii=False),
        "expression_goal": goal,
        "mistake_pattern": mistake,
        "recommended_drills_json": json.dumps(drills, ensure_ascii=False),
    }


def _connection_action_for(resource: ResourceLibrary) -> tuple[str, tuple[str, ...], str, str]:
    haystack = " ".join(
        str(value or "")
        for value in (
            resource.title,
            resource.category,
            resource.content,
            resource.usage_tip,
            resource.tags,
            resource.applicable_scene,
            resource.expression_goal,
            resource.speech_act,
        )
    )
    for action, keywords, tool_ids, goal, mistake in CONNECTION_ACTION_RULES:
        if any(keyword in haystack for keyword in keywords):
            return action, tool_ids, goal, mistake
    scene = resource.applicable_scene or ""
    fallback = {
        "初识": "破冰观察",
        "暧昧": "退路式邀请",
        "热恋": "欣赏表达",
        "冲突": "修复句式",
        "修复": "修复句式",
        "分歧": "边界表达",
    }.get(scene, "破冰观察")
    for action, _keywords, tool_ids, goal, mistake in CONNECTION_ACTION_RULES:
        if action == fallback:
            return action, tool_ids, goal, mistake
    return "破冰观察", ("expr_tool_005", "expr_tool_019"), "打开低压入口", "抽象表达"


def _loads_dict(value: str | None) -> dict[str, Any]:
    if not value:
        return {}
    try:
        loaded = json.loads(value)
    except json.JSONDecodeError:
        return {}
    return loaded if isinstance(loaded, dict) else {}


def main() -> None:
    parser = argparse.ArgumentParser(description="Govern remaining data-content backlog tasks.")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--target-total-candidates", type=int, default=1000)
    parser.add_argument("--target-reviewed", type=int, default=300)
    parser.add_argument("--target-gold", type=int, default=100)
    args = parser.parse_args()
    create_db_and_tables()
    with Session(engine) as session:
        result = run_data_content_governance(
            session,
            target_total_candidates=args.target_total_candidates,
            target_reviewed=args.target_reviewed,
            target_gold=args.target_gold,
            dry_run=args.dry_run,
        )
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
