"""Seed four-step psychological communication ladder resources."""

from __future__ import annotations

import argparse
import hashlib
import json
import sqlite3
import uuid
from datetime import datetime

from backend.database.connection import DB_PATH, create_db_and_tables

SOURCE = "project_original:psychological_communication_ladder_v1"
SOURCE_URL = "local_anchor:四阶心理沟通阶梯"

STEPS = [
    {
        "key": "receive_emotion",
        "label": "接住情绪",
        "axis": "emotion_flow",
        "goal": "先共情、少讲道理、不否定",
        "tools": ["expr_tool_041", "expr_tool_042", "expr_tool_019"],
        "mistake": "急着讲道理、纠正感受或给方案",
        "principle": "情绪先被接住，人才会愿意继续把事情说完整。",
        "ladder_index": 1,
    },
    {
        "key": "curious_expand",
        "label": "保持好奇",
        "axis": "micro_signal",
        "goal": "用开放问题让对方愿意继续分享",
        "tools": ["expr_tool_027", "expr_tool_050", "expr_tool_019"],
        "mistake": "用敷衍短句结束话题，或像审问一样连续追问",
        "principle": "好奇传递的是我在意你，不是我要挖你的隐私。",
        "ladder_index": 2,
    },
    {
        "key": "non_judgment",
        "label": "拒绝评判",
        "axis": "boundary_consent",
        "goal": "不反驳、不挑剔、不秀优越感",
        "tools": ["expr_tool_056", "expr_tool_044", "expr_tool_042"],
        "mistake": "我早说过、你就是不够努力、这有什么好难过",
        "principle": "安全表达环境来自不被审判，而不是被纠正。",
        "ladder_index": 3,
    },
    {
        "key": "deep_empathy",
        "label": "深度共情",
        "axis": "conflict_repair",
        "goal": "听见内容、情绪和更深处的难",
        "tools": ["expr_tool_041", "expr_tool_042", "expr_tool_050"],
        "mistake": "只复述表面内容，或者催对方快点开心",
        "principle": "深度共情是陪对方面对情绪，而不是催对方离开情绪。",
        "ladder_index": 4,
    },
]

CONTEXTS = [
    {
        "key": "暧昧",
        "stage": "互有好感但还没确定关系",
        "setting": "晚上聊天，对方发来一句“今天突然有点不想说话”。",
        "their_words": "我也不知道怎么了，可能就是有点累。",
        "surface_signal": "对方没有断开连接，但表达能量变低。",
        "deeper_need": "希望被理解，又不想被逼着解释清楚。",
        "bad": "你是不是对我没兴趣了？",
        "transfer": "换成对方说“你刚才那句话让我有点不知道怎么接”。",
    },
    {
        "key": "社交",
        "stage": "朋友、同学或同事间的日常分享",
        "setting": "朋友说今天特意买了一块蛋糕，但语气不像单纯开心。",
        "their_words": "我今天下班路上突然很想吃甜的，就买了蛋糕。",
        "surface_signal": "日常小事背后可能有疲惫、奖励自己或需要安慰。",
        "deeper_need": "希望有人对自己的小情绪保持兴趣。",
        "bad": "挺好，少吃点别胖了。",
        "transfer": "换成朋友说“我今天突然想一个人走很远”。",
    },
    {
        "key": "职场",
        "stage": "同事或下属处在压力和责任中",
        "setting": "项目延期后，同事盯着屏幕很久，说自己已经不知道怎么推进。",
        "their_words": "我真的有点扛不住了，但又不能掉链子。",
        "surface_signal": "对方在表达压力，也在担心自己不够可靠。",
        "deeper_need": "希望压力被看见，同时需要实际支持和不被评判。",
        "bad": "大家都忙，你再坚持一下。",
        "transfer": "换成销售同事半夜处理客户系统崩溃后的复盘。",
    },
]

DIFFICULTIES = {
    1: "D1：完成当前阶的一句话回应。",
    2: "D2：在回应里加入开放问题，推动对方继续说。",
    3: "D3：在对方沉默或防御时仍保留边界，不逼深聊。",
}


def _json(data: object) -> str:
    return json.dumps(data, ensure_ascii=False, sort_keys=True)


def _hash(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _better_response(step: dict[str, object], context: dict[str, str], difficulty: int) -> str:
    label = str(step["label"])
    if label == "接住情绪":
        base = f"听起来你不是单纯说这件事，而是真的有点撑着。{context['deeper_need']}"
    elif label == "保持好奇":
        base = f"我想多懂一点：你说“{context['their_words']}”的时候，是更想被陪一下，还是更想安静一会儿？"
    elif label == "拒绝评判":
        base = _non_judgment_response(context)
    else:
        base = f"我听见的是“{context['their_words']}”，更深一点好像是：{context['deeper_need']}这部分确实不轻。"
    if difficulty == 1:
        return base
    if difficulty == 2:
        return f"{base} 如果你愿意，我想听听最让你卡住的是哪一小段。"
    return f"{base} 你不用现在讲完整；如果继续说太累，我们可以先停在这里。"


def _non_judgment_response(context: dict[str, str]) -> str:
    if context["key"] == "社交":
        return "你突然想吃甜的，听起来像是在给自己一个小小的安慰。我不会拿身材或对错评价这件事。"
    if context["key"] == "职场":
        return "你说扛不住但又不能掉链子，我听到的是压力已经很满了。我不会先评价你够不够坚强。"
    if context["key"] == "暧昧":
        return "你说有点累，我不会把它直接理解成你不想理我。人有时候就是会没电。"
    return f"我先不评价这件事对不对，只想听懂你说“{context['their_words']}”时的真实感受。"


def _blueprint(step: dict[str, object], context: dict[str, str], difficulty: int) -> dict[str, object]:
    return {
        "axis": step["axis"],
        "axis_label": step["label"],
        "ladder_index": step["ladder_index"],
        "resource_type": "game",
        "resource_type_label": "四阶心理沟通训练卡",
        "scene": context["key"],
        "relation_stage": context["stage"],
        "trigger": f"{context['key']}场景里，对方露出一点真实情绪，需要用第 {step['ladder_index']} 阶：{step['label']}。",
        "setting": context["setting"],
        "their_words": context["their_words"],
        "surface_signal": context["surface_signal"],
        "deeper_need": context["deeper_need"],
        "common_mistake": f"{step['mistake']}；旧回应通常会说：{context['bad']}",
        "why_wrong": step["principle"],
        "better_response": _better_response(step, context, difficulty),
        "response_steps": _steps_for(step, difficulty),
        "boundary_note": "让对方敞开心扉不等于逼对方交代隐私；任何阶段都要允许停下、跳过或晚点再说。",
        "practice_task": f"把“{context['bad']}”改成符合“{step['label']}”的一句话，再补一个不逼迫的后续问题。",
        "transfer_scene": context["transfer"],
        "variant_deltas": [
            f"递进阶层不同：第 {step['ladder_index']} 阶 {step['label']}。",
            f"适用场景不同：{context['key']} / {context['stage']}。",
            f"难度不同：{DIFFICULTIES[difficulty]}",
            "训练目标不同：让对方从愿意回应，逐步走向愿意主动说心里话。",
        ],
        "difficulty_contract": DIFFICULTIES[difficulty],
    }


def _steps_for(step: dict[str, object], difficulty: int) -> list[str]:
    steps = [
        f"先完成本阶目标：{step['goal']}。",
        "只回应一个情绪点，不同时处理所有问题。",
    ]
    if difficulty >= 2:
        steps.append("加入一个开放问题，但不连续追问。")
    if difficulty >= 3:
        steps.append("明确对方可以不说、晚点说或只说一部分。")
    return steps


def _content(blueprint: dict[str, object]) -> str:
    return "\n".join(
        [
            f"案例定位：四阶心理沟通 / 第 {blueprint['ladder_index']} 阶 {blueprint['axis_label']} / {blueprint['difficulty_contract']}",
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
    now = datetime.now().isoformat()
    created = 0
    skipped = 0
    with sqlite3.connect(DB_PATH) as con:
        for step in STEPS:
            for context in CONTEXTS:
                for difficulty in DIFFICULTIES:
                    blueprint = _blueprint(step, context, difficulty)
                    content = _content(blueprint)
                    signature = _hash("|".join([str(step["key"]), context["key"], str(difficulty), content]))
                    resource_uuid = f"psych-ladder:{uuid.uuid5(uuid.NAMESPACE_URL, signature)}"
                    if con.execute("SELECT id FROM resource_library WHERE resource_uuid=?", (resource_uuid,)).fetchone():
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
                            f"四阶心理沟通·{step['label']}",
                            f"{context['key']}｜第{step['ladder_index']}阶{step['label']}｜D{difficulty}",
                            content,
                            _json({"primary": step["label"], "scene": context["key"], "generator": SOURCE}),
                            5 + difficulty,
                            context["key"],
                            difficulty,
                            "通用",
                            "通用",
                            "按四阶递进练习：先接住情绪，再好奇深挖，再拒绝评判，最后进入深度共情。",
                            9,
                            SOURCE,
                            SOURCE_URL,
                            ",".join(["具体案例", "四阶心理沟通", str(step["label"]), context["key"], f"difficulty:{difficulty}"]),
                            now,
                            "published",
                            "psychological_ladder_seed",
                            now,
                            now,
                            "四阶心理沟通阶梯",
                            "项目原创训练资源；用于暧昧、社交、职场中的敞开心扉训练。",
                            "按接住情绪、保持好奇、拒绝评判、深度共情四阶递进组织。",
                            "project_original",
                            "sha256:" + _hash(content),
                            96 + difficulty,
                            _json(step["tools"]),
                            step["goal"],
                            f"D{difficulty} 四阶递进",
                            step["principle"],
                            step["mistake"],
                            _json(
                                [
                                    {"type": "observe", "prompt": "先判断对方现在停留在哪一阶：需要被接住、被好奇、被安全对待，还是被深度理解。"},
                                    {"type": "rewrite", "prompt": blueprint["practice_task"]},
                                    {"type": "transfer", "prompt": f"迁移到“{context['transfer']}”，保持同一阶目标。"},
                                ]
                            ),
                            _json(blueprint),
                            signature,
                            "|".join(["psychological_ladder", str(step["key"]), context["key"], f"D{difficulty}"]),
                            step["axis"],
                            f"{context['key']}|{step['key']}",
                            100,
                        ),
                    )
        con.commit()
    return {"dry_run": dry_run, "created": created, "skipped": skipped}


def main() -> None:
    parser = argparse.ArgumentParser(description="Seed four-step psychological communication ladder resources.")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    print(_json(seed(dry_run=args.dry_run)))


if __name__ == "__main__":
    main()
