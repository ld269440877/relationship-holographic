"""Seed scene-based expression and deep empathy learning resources."""

from __future__ import annotations

import argparse
import hashlib
import json
import sqlite3
import uuid
from datetime import datetime

from backend.database.connection import DB_PATH, create_db_and_tables

SOURCE = "project_original:communication_upgrade_pack_v1"
SOURCE_URL = "local_anchor:场景化表达与深度共情世界级融合升级版"

CAPABILITIES = [
    {
        "key": "scene_concrete_entry",
        "label": "具象切入",
        "axis": "micro_signal",
        "goal": "把抽象结论改成可看见的画面",
        "tools": ["expr_tool_011", "expr_tool_015", "expr_tool_041"],
        "mistake": "直接讲道理，让对方感觉被教育",
        "principle": "具体画面先进入体验，结论才不会像压力。",
    },
    {
        "key": "story_proof",
        "label": "故事赋能",
        "axis": "long_connection",
        "goal": "用真实案例替代说教",
        "tools": ["expr_tool_014", "expr_tool_006", "expr_tool_023"],
        "mistake": "只说我需要、我认为、我建议，没有让对方看见后果",
        "principle": "故事让对方自己完成推理，比被要求接受观点更柔和。",
    },
    {
        "key": "contrast_perception",
        "label": "对比显效",
        "axis": "mistake_rewrite",
        "goal": "用前后反差制造直观感知",
        "tools": ["expr_tool_020", "expr_tool_012", "expr_tool_026"],
        "mistake": "只报百分比或结论，缺少人的状态变化",
        "principle": "反差让成果从数字变成感受，理解成本更低。",
    },
    {
        "key": "emotion_receive",
        "label": "接住情绪",
        "axis": "emotion_flow",
        "goal": "先共情、少讲道理、不否定",
        "tools": ["expr_tool_041", "expr_tool_042", "expr_tool_019"],
        "mistake": "催对方想开、讲道理或立刻给方案",
        "principle": "情绪被接住后，人才有余力讨论下一步。",
    },
    {
        "key": "curiosity_open",
        "label": "好奇深挖",
        "axis": "micro_signal",
        "goal": "用开放问题表达我在意你",
        "tools": ["expr_tool_027", "expr_tool_050", "expr_tool_019"],
        "mistake": "用挺好、哦、然后呢结束对方的分享",
        "principle": "好奇不是盘问，而是给对方继续展开的空间。",
    },
    {
        "key": "non_judgment",
        "label": "拒绝评判",
        "axis": "boundary_consent",
        "goal": "不反驳、不挑剔、不秀优越感",
        "tools": ["expr_tool_056", "expr_tool_044", "expr_tool_042"],
        "mistake": "我早说过、你就是不够努力、这有什么好难过",
        "principle": "安全表达环境来自不被审判，而不是被纠正。",
    },
    {
        "key": "deep_empathy",
        "label": "深度共情",
        "axis": "conflict_repair",
        "goal": "听见内容、委屈疲惫和更深处的难",
        "tools": ["expr_tool_041", "expr_tool_042", "expr_tool_050"],
        "mistake": "只复述表层内容，没有走进对方真正的难处",
        "principle": "深度共情是陪对方面对情绪，而不是催对方开心。",
    },
]

SCENARIOS = [
    {
        "key": "失恋安抚",
        "scene": "修复",
        "stage": "朋友或暧昧对象正在失恋",
        "setting": "深夜聊天，对方反复说自己是不是不够好。",
        "their_words": "我就是想不通，为什么他可以那么快抽身。",
        "bad": "他不值得，你早该看清了。",
        "signal": "对方不是在要结论，而是在反复确认自己的价值有没有被否定。",
        "need": "被理解、被陪伴、被允许难过，而不是被催着清醒。",
        "transfer": "换成闺蜜失恋后复盘第一次约会迟到 40 分钟的细节。",
    },
    {
        "key": "拒绝请求",
        "scene": "边界确认",
        "stage": "熟人请求帮忙但你资源不足",
        "setting": "对方临时把方案丢给你，希望你今晚帮他改完。",
        "their_words": "你就帮我这一次吧，真的很急。",
        "bad": "我不想帮，你找别人。",
        "signal": "对方很急，但你的边界也需要被看见。",
        "need": "既不冷硬拒绝，也不牺牲自己的项目进度。",
        "transfer": "换成上次帮小王做方案导致自己项目延期被批的亲身经历。",
    },
    {
        "key": "化解矛盾",
        "scene": "冲突",
        "stage": "伴侣争吵后还在受伤",
        "setting": "家里灯很暗，对方提起发烧那晚你没有问候。",
        "their_words": "我发烧 39 度自己熬了一夜，你回来连一句问候都没有。",
        "bad": "你怎么又翻旧账，我那天也很累。",
        "signal": "对方在讲事实细节，底层是在说自己当时很孤单。",
        "need": "被承认影响，而不是被反驳记忆。",
        "transfer": "换成一次公开场合被忽略后的私下复盘。",
    },
    {
        "key": "职场说服",
        "scene": "分歧",
        "stage": "预算、销售或跨部门说服",
        "setting": "会议里对方质疑预算必要性，大家开始看数字表。",
        "their_words": "为什么不能再压一点预算？",
        "bad": "我们这个方案就是最优的，不能再砍。",
        "signal": "对方在要风险画面，而不是只要你的主观判断。",
        "need": "看见预算不足会带来的真实后果和人的压力。",
        "transfer": "换成客户凌晨三点系统崩溃、办公室来回踱步的痛点故事。",
    },
]

DIFFICULTIES = {
    1: "D1：把抽象结论改成一个具体画面。",
    2: "D2：加入对方情绪，并给一个开放问题。",
    3: "D3：在对方防御或沉默时仍保留边界和退路。",
}


def _json(data: object) -> str:
    return json.dumps(data, ensure_ascii=False, sort_keys=True)


def _hash(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _better_response(capability: dict[str, object], scenario: dict[str, str], difficulty: int) -> str:
    label = str(capability["label"])
    if label == "具象切入":
        return f"我不急着下结论，我先说一个画面：{scenario['setting']}你说“{scenario['their_words']}”时，其实已经把最难受的地方露出来了。"
    if label == "故事赋能":
        transfer = str(scenario["transfer"]).rstrip("。")
        return f"我想到一个很像的经历：{transfer}。那次真正让人改变的不是道理，而是看见后果已经发生。"
    if label == "对比显效":
        return f"我们可以看前后差别：旧回应会变成“{scenario['bad']}”，新回应先承认你经历的细节，再谈下一步。"
    if label == "接住情绪":
        return f"听起来你现在最难的不是这句话本身，而是那种没人站在你这边的感觉。你可以慢慢说，我先不评判。"
    if label == "好奇深挖":
        return f"我想更懂一点：你刚才说“{scenario['their_words']}”时，最刺痛你的是事情本身，还是那一刻没人理解你？"
    if label == "拒绝评判":
        return f"我不会急着说你该怎样，也不替你下判断。我先确认：这件事里你最不能接受的是哪一部分？"
    base = f"我先听见内容：{scenario['their_words']}；也听见背后的难：{scenario['need']}。我会陪你看这部分，不急着催你好起来。"
    if difficulty >= 3:
        return f"{base} 如果现在继续说太重，我们可以先停在这里，等你愿意再往下讲。"
    return base


def _blueprint(capability: dict[str, object], scenario: dict[str, str], difficulty: int) -> dict[str, object]:
    better = _better_response(capability, scenario, difficulty)
    return {
        "axis": capability["axis"],
        "axis_label": capability["label"],
        "resource_type": "game",
        "resource_type_label": "表达融合训练卡",
        "scene": scenario["scene"],
        "relation_stage": scenario["stage"],
        "trigger": f"{scenario['key']}中需要从说教切换为画面与共情。",
        "setting": scenario["setting"],
        "their_words": scenario["their_words"],
        "surface_signal": scenario["signal"],
        "deeper_need": scenario["need"],
        "signal_focus": "具体画面、情绪词、停顿、旧回应里的防御点。",
        "common_mistake": f"{capability['mistake']}；旧回应通常会说：{scenario['bad']}",
        "why_wrong": capability["principle"],
        "better_response": better,
        "response_steps": [
            "先还原一个具体画面，不直接塞结论。",
            "标出对方当前情绪，不急着讲道理。",
            "用好奇问题邀请对方继续，而不是盘问。",
            "保留对方不想继续说的边界。",
        ][: 2 + difficulty],
        "boundary_note": "表达好听不是操控对方接受观点；如果对方沉默、拒绝或转移话题，先停下。",
        "practice_task": f"把“{scenario['bad']}”改写为一段包含画面、情绪承接和可拒绝出口的回应。",
        "transfer_scene": scenario["transfer"],
        "variant_deltas": [
            f"能力点不同：本卡训练{capability['label']}。",
            f"场景不同：{scenario['key']} / {scenario['stage']}。",
            f"难度不同：{DIFFICULTIES[difficulty]}",
            "输出不同：必须把结论改成画面，再接住情绪。",
        ],
        "difficulty_contract": DIFFICULTIES[difficulty],
        "quality_dimensions": {
            "scene_specificity": 25,
            "emotion_holding": 20,
            "non_judgment": 15,
            "boundary_exit": 15,
            "transfer_practice": 15,
            "source_compliance": 10,
        },
    }


def _content(blueprint: dict[str, object]) -> str:
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


def seed(dry_run: bool = False) -> dict[str, int | bool]:
    create_db_and_tables()
    created = 0
    skipped = 0
    now = datetime.now().isoformat()
    with sqlite3.connect(DB_PATH) as con:
        for capability in CAPABILITIES:
            for scenario in SCENARIOS:
                for difficulty in DIFFICULTIES:
                    blueprint = _blueprint(capability, scenario, difficulty)
                    content = _content(blueprint)
                    signature = _hash("|".join([str(capability["key"]), scenario["key"], str(difficulty), content]))
                    resource_uuid = f"communication-upgrade:{uuid.uuid5(uuid.NAMESPACE_URL, signature)}"
                    exists = con.execute("SELECT id FROM resource_library WHERE resource_uuid=?", (resource_uuid,)).fetchone()
                    if exists:
                        skipped += 1
                        continue
                    created += 1
                    if dry_run:
                        continue
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
                        )
                        VALUES (
                          ?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?
                        )
                        """,
                        (
                            resource_uuid,
                            "game",
                            f"场景化表达与深度共情·{capability['label']}",
                            f"{scenario['key']}｜{capability['label']}｜D{difficulty}",
                            content,
                            _json({"primary": capability["label"], "scene": scenario["scene"], "generator": SOURCE}),
                            min(10, 5 + difficulty),
                            scenario["scene"],
                            difficulty,
                            "通用",
                            "通用",
                            "先让对方进入画面，再接住情绪，最后用开放问题和边界出口推动继续表达。",
                            9,
                            SOURCE,
                            SOURCE_URL,
                            ",".join(["具体案例", "场景化表达", "深度共情", str(capability["label"]), scenario["scene"], f"difficulty:{difficulty}"]),
                            now,
                            "published",
                            "communication_upgrade_seed",
                            now,
                            now,
                            "场景化表达与深度共情世界级融合升级版",
                            "项目原创训练资源；第三方内容只作为用户提供素材的结构化吸收，不保存外部全文。",
                            "把场景化表达、故事赋能、对比显效、接住情绪、好奇深挖、拒绝评判和深度共情融入项目训练链路。",
                            "project_original",
                            "sha256:" + _hash(content),
                            96 + min(3, difficulty),
                            _json(capability["tools"]),
                            capability["goal"],
                            f"D{difficulty} 融合表达",
                            capability["principle"],
                            capability["mistake"],
                            _json(
                                [
                                    {"type": "scene", "prompt": "把抽象结论改成一个具体画面。"},
                                    {"type": "emotion", "prompt": "说出对方此刻可能的情绪和原因。"},
                                    {"type": "rewrite", "prompt": blueprint["practice_task"]},
                                ]
                            ),
                            _json(blueprint),
                            signature,
                            "|".join(["communication_upgrade", str(capability["key"]), scenario["key"], f"D{difficulty}"]),
                            capability["axis"],
                            f"{scenario['key']}|{capability['key']}",
                            100,
                        ),
                    )
        con.commit()
    return {"dry_run": dry_run, "created": created, "skipped": skipped}


def main() -> None:
    parser = argparse.ArgumentParser(description="Seed communication upgrade learning resources.")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    print(_json(seed(dry_run=args.dry_run)))


if __name__ == "__main__":
    main()
