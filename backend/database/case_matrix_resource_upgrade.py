"""Build a quota-based resource case matrix.

The upgrade keeps old rows for audit, but hides legacy generated rows that do
not have a real case blueprint. New rows are project-original learning samples.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import uuid
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from shutil import copy2
from typing import Any

from sqlalchemy import text
from sqlmodel import Session, select

from backend.database.connection import DB_PATH, create_db_and_tables, engine
from backend.models.resource import ResourceLibrary

CASE_SOURCE = "project_original:case_matrix_v1"
CASE_SOURCE_URL = "synthetic://relationship-training/case-matrix/v1"
MIN_RECORDS_PER_CELL = 2


@dataclass(frozen=True)
class AxisSpec:
    key: str
    label: str
    goal: str
    signal_focus: str
    common_mistake: str
    why_wrong: str
    principle: str
    tools: tuple[str, str, str]


@dataclass(frozen=True)
class SceneSpec:
    key: str
    stage: str
    trigger: str
    setting_a: str
    setting_b: str
    their_words_a: str
    their_words_b: str
    surface_signal: str
    deeper_need: str
    transfer_scene: str


AXES = (
    AxisSpec(
        "micro_signal",
        "微关系信号",
        "看见一句话背后的靠近、后退、试探或求助",
        "语速、停顿、表情、字数变化和是否留了退路",
        "把一个小信号立刻判成冷淡、拒绝或敷衍",
        "微小信号只是线索，不是证据；直接定性会制造压力和误判。",
        "先描述你看见的具体事实，再用轻问句验证，不把猜测当结论。",
        ("expr_tool_011", "expr_tool_019", "expr_tool_041"),
    ),
    AxisSpec(
        "emotion_flow",
        "情绪流动",
        "读懂情绪从紧绷到松动、从委屈到愿意说的变化",
        "情绪词、身体动作、回复节奏和话题转向",
        "只解决事情，不承接当下情绪",
        "情绪没有被看见时，方案会被听成辩解或控制。",
        "先命名情绪，再处理事实；让对方知道你听见了影响。",
        ("expr_tool_041", "expr_tool_042", "expr_tool_050"),
    ),
    AxisSpec(
        "boundary_consent",
        "边界与同意",
        "让靠近、玩笑、请求和亲密推进都保留可拒绝出口",
        "迟疑、沉默、转移话题、身体后退和模糊答应",
        "把对方没有明确拒绝当成同意",
        "没有清晰同意的推进会让关系从靠近变成压力。",
        "任何推进都要能停、能慢、能改期，并把选择权还给对方。",
        ("expr_tool_027", "expr_tool_056", "expr_tool_030"),
    ),
    AxisSpec(
        "flirty_tension",
        "暧昧张力",
        "制造好玩但不压迫的靠近感",
        "玩笑、双关、轻挑战、赞美和对方是否愿意接梗",
        "为了显得有张力而贬低、逼近或开过界玩笑",
        "暧昧的张力来自可选择，不来自让对方尴尬。",
        "轻挑战要接住意图、保留体面，并允许对方不接。",
        ("expr_tool_016", "expr_tool_017", "expr_tool_019"),
    ),
    AxisSpec(
        "conflict_repair",
        "冲突修复",
        "把受伤、失望和争执转回可对话状态",
        "短回复、冷淡、讽刺、旧账和是否愿意给窗口",
        "急着解释自己不是故意的",
        "解释太早会让对方觉得影响被轻描淡写。",
        "先承认影响，少辩解，再给一个具体、可靠、可检查的下一步。",
        ("expr_tool_029", "expr_tool_044", "expr_tool_057"),
    ),
    AxisSpec(
        "long_connection",
        "长期连接",
        "把日常偏好、承诺、压力和未来安排变成共同约定",
        "重复小摩擦、生活节奏、期待落差和是否可持续",
        "只在爆发时谈规则，平时靠猜",
        "长期关系靠可复用的约定，不靠每次临场发挥。",
        "把抱怨改成偏好校准，把承诺改成具体动作和复盘时间。",
        ("expr_tool_059", "expr_tool_060", "expr_tool_026"),
    ),
    AxisSpec(
        "humor_interaction",
        "幽默互动",
        "用低压幽默松动气氛，同时不逃避真实议题",
        "对方是否笑、是否继续、是否变沉默和玩笑是否踩到痛点",
        "用玩笑盖过对方的不舒服",
        "幽默如果要求对方配合，就会变成二次伤害。",
        "先确认安全，再轻轻转向；一旦对方不接，就收回并修复。",
        ("expr_tool_016", "expr_tool_017", "expr_tool_045"),
    ),
    AxisSpec(
        "mistake_rewrite",
        "错题改写",
        "把旧回应拆成错因，再改成可以练的新回应",
        "旧句子里的评判、追问、讨好、冷处理和越界点",
        "只背一句正确话术，不知道旧句子错在哪里",
        "不知道错因就无法迁移，只会在新场景复读模板。",
        "先标错因，再补事实、感受、边界和下一步。",
        ("expr_tool_003", "expr_tool_026", "expr_tool_057"),
    ),
)

SCENES = (
    SceneSpec("初识", "刚认识", "第一次聊天从礼貌寒暄转向私人偏好", "下班路上语音断了一下", "咖啡店排队时对方看了你一眼又移开", "我其实不太会跟刚认识的人聊天。", "你平时和朋友也这么安静吗？", "试探、谨慎和一点想继续", "安全感、低压力入口和可退出感", "换成第一次约周末咖啡"),
    SceneSpec("暧昧", "互有好感但未确定", "对方丢出一句带玩笑的靠近", "晚上聊天忽然停了十秒", "散步到路口时对方放慢脚步", "你刚刚那句是不是有点认真？", "我发现跟你聊天时间过得挺快。", "靠近里带着怕被拒绝", "被接住、被尊重和不被逼表态", "换成一次轻邀约"),
    SceneSpec("热恋", "稳定靠近", "亲密互动里出现节奏差", "睡前电话里对方声音变低", "见面分别前对方没有马上松手", "我今天有点黏人，你会不会烦？", "你刚才为什么突然不说话？", "需要确认自己被欢迎", "被选择、被回应和节奏可协商", "换成周末相处安排"),
    SceneSpec("冲突", "出现争执", "一个小问题触发旧情绪", "饭桌上双方声音都变快", "消息框里对方删删改改才发出来", "你每次都这样，说了也没用。", "算了，我不想吵了。", "防御、失望和想停止升级", "被认真对待、被理解影响和不再循环", "换成公开场合的短边界"),
    SceneSpec("修复", "争执之后", "你想重新打开对话但对方还在受伤", "冷战第二天晚上", "楼下碰面时对方只点了点头", "我现在不知道该怎么相信你说的。", "你不用解释了。", "受伤、警惕和仍留一点窗口", "可靠行动、时间感和不被逼原谅", "换成一次具体补偿安排"),
    SceneSpec("长期", "共同生活或长期相处", "日常小事暴露重复期待差", "周日晚上整理下周安排", "厨房里对方把水杯放重了一点", "这些事为什么总要我提醒？", "我不是要管你，我只是很累。", "疲惫、期待落空和想要共同承担", "分工、稳定和可复盘的约定", "换成家务或财务偏好校准"),
    SceneSpec("异地", "空间分离", "低电量报备让人不确定", "凌晨一点半的地铁口", "视频通话里信号卡了两次", "我到家了，先睡。", "今天真的没力气讲了。", "疲惫里仍在维持连接", "被信任、被关心且不被审问", "换成周末视频约定"),
    SceneSpec("复联", "中断后重新接触", "对方通过间接动作试探是否还能说话", "朋友圈出现共同回忆", "旧聊天窗口停在上次争吵后", "最近还好吗？", "那天的事我也想过。", "靠近、试水和怕再次受伤", "低门槛窗口、不翻旧账和可暂停", "换成十分钟通话邀请"),
    SceneSpec("分歧", "价值观不同", "观点差异开始变成人格判断", "讨论消费、社交或家庭边界时", "对方沉默后把手机扣在桌上", "我不是反对你，我只是想要一点底。", "你这样说让我像个很糟糕的人。", "被误解和想维护自我价值", "不被评判、需求被拆开讨论", "换成预算或社交边界协商"),
    SceneSpec("亲密推进", "亲密节奏协商", "气氛升温但对方信号变慢", "沙发上两人靠得很近", "拥抱之后对方轻轻后退", "我有点紧张，不是不喜欢。", "我们能不能慢一点？", "喜欢、紧张和请求确认", "节奏自主、身体边界和安全感", "换成约会后的亲密确认"),
    SceneSpec("公开场合", "有旁人在场", "玩笑或忽略发生在别人面前", "朋友聚会的餐桌边", "同事活动结束后的走廊", "你不会介意吧，我开玩笑的。", "刚才我有点接不上话。", "尴尬、体面和希望被保护", "现场止损、私下复盘和不羞辱", "换成朋友聚会后的复盘"),
    SceneSpec("压力支持", "一方压力很高", "对方想被支持但没力气解释", "加班回家后灯还没开", "考试或项目截止前的深夜", "我脑子已经转不动了。", "你别问了，我现在只想安静。", "耗竭、求空间和仍希望被在意", "低成本陪伴、空间和延后复盘", "换成第二天的支持计划"),
)

RESOURCE_TYPES = ("story", "game", "flirty", "phrase", "joke")
DIFFICULTIES = (1, 2, 3)
ATTACHMENTS = ("安全型", "焦虑型", "回避型", "通用")

TYPE_LABELS = {
    "story": "具体故事卡",
    "game": "三步训练卡",
    "flirty": "张力回应卡",
    "phrase": "边界短句卡",
    "joke": "低压幽默卡",
}

ATTACHMENT_STRATEGY = {
    "安全型": "直接说清影响和下一步，同时允许对方补充或修正。",
    "焦虑型": "先降低不确定性，不连环追问，不把沉默解读成抛弃。",
    "回避型": "给空间和时间窗口，不逼即时回应，也不冷处理。",
    "通用": "保持事实清楚、情绪可承接、边界可退出。",
}

DIFFICULTY_CONTRACT = {
    1: "D1 只要求照结构完成：事实一句、感受一句、边界一句。",
    2: "D2 要迁移到相邻场景，并自己补一个可执行下一步。",
    3: "D3 要加入干扰条件：对方冷淡、旁人在场或旧账未清，仍保持不施压。",
}


def _json(data: Any) -> str:
    return json.dumps(data, ensure_ascii=False, sort_keys=True)


def _hash(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def _case_blueprint(axis: AxisSpec, scene: SceneSpec, resource_type: str, difficulty: int, attachment: str, variant_index: int) -> dict[str, Any]:
    their_words = scene.their_words_a if variant_index % 2 else scene.their_words_b
    setting = scene.setting_a if variant_index % 2 else scene.setting_b
    extra_pressure = {
        1: "对方愿意继续聊，只是需要你说得更清楚。",
        2: "对方没有立刻回应，你需要给出可暂停的空间。",
        3: "现场还有旁人或旧情绪残留，你需要短句止损，之后再复盘。",
    }[difficulty]
    mistake = f"{axis.common_mistake}；旧回应通常会说：{_bad_response(axis, scene, attachment)}"
    better = _better_response(axis, scene, attachment, difficulty, variant_index)
    return {
        "axis": axis.key,
        "axis_label": axis.label,
        "resource_type": resource_type,
        "resource_type_label": TYPE_LABELS[resource_type],
        "scene": scene.key,
        "relation_stage": scene.stage,
        "trigger": scene.trigger,
        "setting": setting,
        "their_words": their_words,
        "surface_signal": scene.surface_signal,
        "deeper_need": scene.deeper_need,
        "signal_focus": axis.signal_focus,
        "common_mistake": mistake,
        "why_wrong": axis.why_wrong,
        "better_response": better,
        "response_steps": _response_steps(axis, difficulty, attachment),
        "boundary_note": _boundary_note(axis, scene, attachment),
        "practice_task": _practice_task(axis, scene, resource_type, difficulty),
        "transfer_scene": scene.transfer_scene,
        "variant_deltas": _variant_deltas(axis, scene, resource_type, difficulty, attachment, variant_index),
        "difficulty_contract": DIFFICULTY_CONTRACT[difficulty],
        "attachment_strategy": ATTACHMENT_STRATEGY[attachment],
        "quality_dimensions": {
            "specificity": 25,
            "practice_ready": 20,
            "emotion_flow": 15,
            "boundary_clarity": 15,
            "variant_difference": 15,
            "source_trace": 10,
        },
        "extra_pressure": extra_pressure,
    }


def _bad_response(axis: AxisSpec, scene: SceneSpec, attachment: str) -> str:
    if axis.key == "conflict_repair":
        return "你别这样，我也不是故意的，你能不能别总翻旧账？"
    if axis.key == "boundary_consent":
        return "都这样了你还紧张什么，别想太多。"
    if axis.key == "humor_interaction":
        return "开个玩笑而已，你怎么这么敏感？"
    if attachment == "焦虑型":
        return "你是不是不想理我？你直接说清楚。"
    if attachment == "回避型":
        return "算了，不说了，反正说了也麻烦。"
    return f"你这句话到底什么意思？别让我猜。"


def _better_response(axis: AxisSpec, scene: SceneSpec, attachment: str, difficulty: int, variant_index: int) -> str:
    their_words = _strip_sentence_end(scene.their_words_a if variant_index % 2 else scene.their_words_b)
    opener = {
        "micro_signal": f"我听见你说“{their_words}”。我先不猜结论，只想确认一下：你是有点紧张，还是只是需要一点时间慢慢熟？",
        "emotion_flow": f"你说“{their_words}”的时候，我感觉这里不只是事情本身，还有一点累或委屈。你愿意先说最重的那一点吗？",
        "boundary_consent": f"听到你说“{their_words}”，我们可以慢一点。你不用为了照顾我勉强答应，舒服和不舒服都可以直接说。",
        "flirty_tension": f"这句我有接收到一点靠近，也不会逼你表态。我们就轻轻聊到这里，你想接梗再接也可以。",
        "conflict_repair": f"你说“{their_words}”，我先承认这件事让你不好受。我不急着解释，先听你最在意的是哪一段。",
        "long_connection": f"这听起来不像一次小事，更像我们节奏需要重新对齐。我们今晚先定一个小约定，不把问题拖到下次爆发。",
        "humor_interaction": f"我想轻一点接住，但不拿你的不舒服开玩笑。你愿意的话，我先陪你把这件事说轻一点。",
        "mistake_rewrite": f"我把刚才那句收回来。更准确地说，我在意你刚才这句话，也愿意按你的节奏慢慢听。",
    }[axis.key]
    if difficulty == 1:
        return opener
    if difficulty == 2:
        return f"{opener} 如果现在不方便，我们也可以换到{scene.transfer_scene}再说。"
    return f"{opener} 我先不追问，也不在这里拉长争辩；等我们都缓一点，再完整复盘。"


def _response_steps(axis: AxisSpec, difficulty: int, attachment: str) -> list[str]:
    base = [
        "复述一个可观察事实，不评价人格。",
        f"点出本轴重点：{axis.signal_focus}。",
        "给对方一个可以拒绝、改期或纠正你的出口。",
    ]
    if difficulty >= 2:
        base.append(f"加入依恋适配：{ATTACHMENT_STRATEGY[attachment]}")
    if difficulty >= 3:
        base.append("在干扰条件下只保留一句核心修复话，不拉长争辩。")
    return base


def _boundary_note(axis: AxisSpec, scene: SceneSpec, attachment: str) -> str:
    if axis.key == "flirty_tension":
        return "张力只在对方愿意接的时候成立；一旦对方沉默或后退，立即降速。"
    if axis.key == "boundary_consent":
        return "没有明确、持续、可撤回的同意，就不继续推进。"
    if scene.key in {"公开场合", "亲密推进"}:
        return "先保护体面和身体/情绪边界，再约私下复盘。"
    return f"边界不是拒绝连接，而是让{attachment}也能安全地继续。"


def _practice_task(axis: AxisSpec, scene: SceneSpec, resource_type: str, difficulty: int) -> str:
    if resource_type == "game":
        return f"按事实、感受、边界三栏重写“{scene.their_words_a}”的回应，最后补一个可拒绝下一步。"
    if resource_type == "story":
        return f"写出{scene.key}里三个动作细节，再判断情绪从哪里开始松动。"
    if resource_type == "joke":
        return "写一句低压幽默，然后写一句当对方不接梗时的收回话。"
    if resource_type == "phrase":
        return "压缩成一句可以直接说出口的短句，必须包含可慢、可停或可改期。"
    return f"保留一点张力，但用一句话说明退路和真实意图；难度 {difficulty} 要避免操控感。"


def _variant_deltas(axis: AxisSpec, scene: SceneSpec, resource_type: str, difficulty: int, attachment: str, variant_index: int) -> list[str]:
    return [
        f"主线不同：本卡训练{axis.label}，不是泛泛聊天建议。",
        f"场景锚点不同：{scene.key}/{scene.stage}/{scene.trigger}。",
        f"类型任务不同：{TYPE_LABELS[resource_type]}要求的输出格式不同。",
        f"难度变化：{DIFFICULTY_CONTRACT[difficulty]}",
        f"依恋适配：{attachment}需要{ATTACHMENT_STRATEGY[attachment]}",
        f"同单元第 {variant_index} 个样本使用不同原话、地点或干扰条件。",
    ]


def _strip_sentence_end(text: str) -> str:
    return text.strip().rstrip("。！？.!?")


def _content_from_blueprint(blueprint: dict[str, Any]) -> str:
    steps = "；".join(str(item) for item in blueprint["response_steps"])
    deltas = "；".join(str(item) for item in blueprint["variant_deltas"])
    return (
        f"案例定位：{blueprint['axis_label']} / {blueprint['resource_type_label']} / {blueprint['difficulty_contract']}\n"
        f"场景：{blueprint['setting']}；{blueprint['trigger']}\n"
        f"关系阶段：{blueprint['relation_stage']}\n"
        f"TA说：{blueprint['their_words']}\n"
        f"表层信号：{blueprint['surface_signal']}\n"
        f"深层可能：{blueprint['deeper_need']}\n"
        f"常见失误：{blueprint['common_mistake']}\n"
        f"为什么错：{blueprint['why_wrong']}\n"
        f"更好回应：{blueprint['better_response']}\n"
        f"回应拆解：{steps}\n"
        f"边界提醒：{blueprint['boundary_note']}\n"
        f"练习任务：{blueprint['practice_task']}\n"
        f"迁移场景：{blueprint['transfer_scene']}\n"
        f"变体差异：{deltas}"
    )


def _resource_uuid(signature: str) -> str:
    return f"case-matrix:{uuid.uuid5(uuid.NAMESPACE_URL, signature)}"


def _recommended_drills(blueprint: dict[str, Any]) -> str:
    return _json(
        [
            {"type": "observe", "prompt": f"标出“{blueprint['their_words']}”里的事实、情绪和边界信号。"},
            {"type": "rewrite", "prompt": blueprint["practice_task"]},
            {"type": "transfer", "prompt": f"把回应迁移到“{blueprint['transfer_scene']}”，但保留同一个边界原则。"},
        ]
    )


def _make_resource(axis: AxisSpec, scene: SceneSpec, resource_type: str, difficulty: int, attachment: str, variant_index: int) -> ResourceLibrary:
    blueprint = _case_blueprint(axis, scene, resource_type, difficulty, attachment, variant_index)
    content = _content_from_blueprint(blueprint)
    variant_signature = _hash(
        "|".join([axis.key, scene.key, resource_type, str(difficulty), attachment, str(variant_index), blueprint["their_words"], blueprint["better_response"]])
    )
    resource = ResourceLibrary(
        resource_uuid=_resource_uuid(variant_signature),
        type=resource_type,
        category=f"{axis.label}·{TYPE_LABELS[resource_type]}",
        title=f"{scene.key}｜{axis.label}｜{TYPE_LABELS[resource_type]}｜{attachment}D{difficulty}-{variant_index}",
        content=content,
        emotional_tone_json=_json({"primary": axis.label, "scene": scene.key, "attachment": attachment, "generator": CASE_SOURCE}),
        emotional_intensity=min(10, 4 + difficulty + (1 if scene.key in {"冲突", "修复", "亲密推进"} else 0)),
        applicable_scene=scene.key,
        difficulty_level=difficulty,
        gender_target="通用",
        attachment_suitability=attachment,
        usage_tip="先看完整案例蓝图，再完成练习任务；不要背句子，要学会迁移到相邻场景。",
        effectiveness_rating=9,
        review_status="published",
        reviewer_id="case_matrix_upgrade",
        reviewed_at=datetime.now(),
        published_at=datetime.now(),
        source=CASE_SOURCE,
        source_url=CASE_SOURCE_URL,
        source_title="项目原创案例矩阵",
        source_excerpt="本地原创训练样本，按主线、场景、类型、难度和依恋配额生成。",
        source_summary="每条资源必须包含场景、原话、信号、错因、更好回应、边界和迁移练习。",
        source_license="project_original",
        tags=",".join([axis.label, scene.key, TYPE_LABELS[resource_type], attachment, f"difficulty:{difficulty}", "具体案例", "案例蓝图", "真实变体", "可迁移练习"]),
        expression_tool_ids_json=_json(axis.tools),
        expression_goal=axis.goal,
        expression_level=f"D{difficulty} {'照结构' if difficulty == 1 else '迁移' if difficulty == 2 else '复杂改写'}",
        speech_act=axis.principle,
        mistake_pattern=axis.common_mistake,
        recommended_drills_json=_recommended_drills(blueprint),
        case_blueprint_json=_json(blueprint),
        variant_signature=variant_signature,
        content_unit="|".join([axis.key, scene.key, resource_type, f"D{difficulty}", attachment]),
        coverage_axis=axis.key,
        variant_family=f"{scene.key}|{axis.key}|{resource_type}",
        case_completeness_score=100,
    )
    resource.content_fingerprint = "sha256:" + _hash(content)
    resource.quality_score = 94 + min(3, difficulty)
    return resource


def _ensure_coverage_tables(session: Session) -> None:
    session.execute(
        text(
            """
            CREATE TABLE IF NOT EXISTS resource_coverage_requirements (
              id INTEGER PRIMARY KEY AUTOINCREMENT,
              requirement_uuid TEXT UNIQUE NOT NULL,
              coverage_axis TEXT NOT NULL,
              scene TEXT NOT NULL,
              resource_type TEXT NOT NULL,
              difficulty_level INTEGER NOT NULL,
              attachment_suitability TEXT NOT NULL,
              minimum_records INTEGER NOT NULL,
              active INTEGER NOT NULL DEFAULT 1,
              created_at TEXT NOT NULL,
              updated_at TEXT NOT NULL
            )
            """
        )
    )
    session.execute(
        text(
            """
            CREATE TABLE IF NOT EXISTS resource_coverage_audit (
              id INTEGER PRIMARY KEY AUTOINCREMENT,
              requirement_uuid TEXT NOT NULL,
              current_records INTEGER NOT NULL,
              deficit INTEGER NOT NULL,
              status TEXT NOT NULL,
              audited_at TEXT NOT NULL
            )
            """
        )
    )
    session.commit()


def _upsert_requirement(session: Session, axis: AxisSpec, scene: SceneSpec, resource_type: str, difficulty: int, attachment: str) -> str:
    requirement_uuid = _hash("|".join([axis.key, scene.key, resource_type, str(difficulty), attachment]))[:32]
    now = datetime.now().isoformat()
    session.execute(
        text(
            """
            INSERT INTO resource_coverage_requirements (
              requirement_uuid, coverage_axis, scene, resource_type, difficulty_level,
              attachment_suitability, minimum_records, active, created_at, updated_at
            )
            VALUES (:uuid, :axis, :scene, :type, :difficulty, :attachment, :minimum, 1, :now, :now)
            ON CONFLICT(requirement_uuid) DO UPDATE SET
              minimum_records = excluded.minimum_records,
              active = 1,
              updated_at = excluded.updated_at
            """
        ),
        {
            "uuid": requirement_uuid,
            "axis": axis.key,
            "scene": scene.key,
            "type": resource_type,
            "difficulty": difficulty,
            "attachment": attachment,
            "minimum": MIN_RECORDS_PER_CELL,
            "now": now,
        },
    )
    return requirement_uuid


def _current_cell_count(session: Session, axis: AxisSpec, scene: SceneSpec, resource_type: str, difficulty: int, attachment: str) -> int:
    return int(
        session.execute(
            text(
                """
                SELECT count(*) FROM resource_library
                WHERE source = :source
                  AND review_status IN ('reviewed', 'published')
                  AND coverage_axis = :axis
                  AND applicable_scene = :scene
                  AND type = :type
                  AND difficulty_level = :difficulty
                  AND attachment_suitability = :attachment
                """
            ),
            {
                "source": CASE_SOURCE,
                "axis": axis.key,
                "scene": scene.key,
                "type": resource_type,
                "difficulty": difficulty,
                "attachment": attachment,
            },
        ).scalar_one()
    )


def _audit_requirement(session: Session, requirement_uuid: str, current: int) -> None:
    deficit = max(0, MIN_RECORDS_PER_CELL - current)
    session.execute(
        text(
            """
            INSERT INTO resource_coverage_audit (requirement_uuid, current_records, deficit, status, audited_at)
            VALUES (:uuid, :current, :deficit, :status, :now)
            """
        ),
        {
            "uuid": requirement_uuid,
            "current": current,
            "deficit": deficit,
            "status": "ok" if deficit == 0 else "deficit",
            "now": datetime.now().isoformat(),
        },
    )


def _quarantine_legacy_generated(session: Session, dry_run: bool) -> int:
    resources = session.exec(
        select(ResourceLibrary).where(ResourceLibrary.review_status.in_(("reviewed", "published")))
    ).all()
    changed = 0
    for resource in resources:
        source = resource.source or ""
        source_url = resource.source_url or ""
        is_legacy_generated = (
            source.startswith("synthetic:")
            or source.startswith("public_anchor:")
            or source.startswith("local_anchor:")
            or source == "project_original:resource_similarity_rewrite"
            or source_url.startswith("synthetic://relationship-training/")
        )
        if source == CASE_SOURCE:
            continue
        if not is_legacy_generated:
            continue
        changed += 1
        if not dry_run:
            resource.review_status = "quarantine"
            resource.published_at = None
            resource.tags = ",".join([resource.tags or "", "needs_enrichment", "legacy_generated_hidden"]).strip(",")
            session.add(resource)
    if changed and not dry_run:
        session.commit()
    return changed


def _backup_database() -> str:
    backup_dir = DB_PATH.parent / "backups"
    backup_dir.mkdir(exist_ok=True)
    backup_path = backup_dir / f"relationship_training-before-case-matrix-{datetime.now().strftime('%Y%m%d%H%M%S')}.db"
    copy2(DB_PATH, backup_path)
    return str(backup_path)


def upgrade_case_matrix(dry_run: bool = False, backup: bool = True) -> dict[str, Any]:
    if backup and not dry_run and Path(DB_PATH).exists():
        backup_path = _backup_database()
    else:
        backup_path = ""
    create_db_and_tables()
    with Session(engine) as session:
        _ensure_coverage_tables(session)
        hidden = _quarantine_legacy_generated(session, dry_run=dry_run)
        created = 0
        skipped = 0
        requirements = 0
        deficits_before = 0
        for axis in AXES:
            for scene in SCENES:
                for resource_type in RESOURCE_TYPES:
                    for difficulty in DIFFICULTIES:
                        for attachment in ATTACHMENTS:
                            requirements += 1
                            requirement_uuid = _upsert_requirement(session, axis, scene, resource_type, difficulty, attachment)
                            current = _current_cell_count(session, axis, scene, resource_type, difficulty, attachment)
                            deficit = max(0, MIN_RECORDS_PER_CELL - current)
                            deficits_before += deficit
                            for offset in range(deficit):
                                variant_index = current + offset + 1
                                resource = _make_resource(axis, scene, resource_type, difficulty, attachment, variant_index)
                                exists = session.exec(
                                    select(ResourceLibrary.id).where(ResourceLibrary.resource_uuid == resource.resource_uuid)
                                ).first()
                                if exists:
                                    skipped += 1
                                    continue
                                created += 1
                                if not dry_run:
                                    session.add(resource)
                            final_count = current + deficit
                            if not dry_run:
                                _audit_requirement(session, requirement_uuid, final_count)
        if not dry_run:
            session.commit()
        visible_case_rows = _case_row_count(session)
        audit = _coverage_summary(session)
    return {
        "dry_run": dry_run,
        "backup_path": backup_path,
        "requirements": requirements,
        "minimum_records_per_cell": MIN_RECORDS_PER_CELL,
        "deficits_before": deficits_before,
        "created": created,
        "skipped": skipped,
        "legacy_generated_hidden": hidden,
        "visible_case_rows": visible_case_rows,
        "coverage": audit,
    }


def _case_row_count(session: Session) -> int:
    return int(session.execute(text("SELECT count(*) FROM resource_library WHERE source = :source"), {"source": CASE_SOURCE}).scalar_one())


def _coverage_summary(session: Session) -> dict[str, Any]:
    row = session.execute(
        text(
            """
            SELECT count(*) AS cells,
                   sum(CASE WHEN current_records >= :minimum THEN 1 ELSE 0 END) AS ok_cells,
                   sum(CASE WHEN current_records < :minimum THEN 1 ELSE 0 END) AS deficit_cells,
                   coalesce(sum(deficit), 0) AS total_deficit
            FROM (
              SELECT requirement_uuid, current_records, deficit
              FROM resource_coverage_audit
              WHERE id IN (SELECT max(id) FROM resource_coverage_audit GROUP BY requirement_uuid)
            )
            """
        ),
        {"minimum": MIN_RECORDS_PER_CELL},
    ).first()
    return {
        "cells": int(row[0] or 0),
        "ok_cells": int(row[1] or 0),
        "deficit_cells": int(row[2] or 0),
        "total_deficit": int(row[3] or 0),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Upgrade resources into a quota-based concrete case matrix.")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--no-backup", action="store_true")
    args = parser.parse_args()
    print(_json(upgrade_case_matrix(dry_run=args.dry_run, backup=not args.no_backup)))


if __name__ == "__main__":
    main()
