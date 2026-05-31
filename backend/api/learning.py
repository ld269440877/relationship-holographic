"""分类学习、元认知与数图结合框架 API。"""
from itertools import pairwise
from typing import Any, cast

from fastapi import APIRouter, Depends
from sqlalchemy.sql.elements import ColumnElement
from sqlmodel import Session, select

from backend.database.connection import get_session
from backend.models.training import PracticeEvent, PracticeSession, TrainingAttempt
from backend.models.user import MistakeLog

router = APIRouter(prefix="/api/learning", tags=["学习框架"])


def _sql_column(value: Any) -> ColumnElement[Any]:
    return cast(ColumnElement[Any], value)


@router.get("/framework")
def framework() -> dict[str, Any]:
    """返回元基础、分类树、5W2H、数图组件与掌握阶段。"""
    return {
        "version": "2026-05-21",
        "axiom": "人性无限，学习必须分类；数字入微，图形给直觉，文字给意义。",
        "primitive_ladder": [
            {"level": 0, "name": "元事实", "unit": "Human Primitive", "question": "什么是不再能拆的关系事实？", "visual": "安全-边界-连接三角基座"},
            {"level": 1, "name": "原子信号", "unit": "Signal", "question": "可观察线索是什么？", "visual": "文本/表情/语气信号高亮"},
            {"level": 2, "name": "微状态", "unit": "State", "question": "当下身体和心理状态如何？", "visual": "状态卡片"},
            {"level": 3, "name": "情绪流", "unit": "EmotionFlow", "question": "情绪从哪来、到哪高、如何转折？", "visual": "情绪曲线"},
            {"level": 4, "name": "感受评价", "unit": "Feeling", "question": "她如何体验自己和这段关系？", "visual": "被看见/被忽略象限"},
            {"level": 5, "name": "需求边界", "unit": "NeedBoundary", "question": "核心需求与不可侵犯边界是什么？", "visual": "需求雷达 + 边界色带"},
            {"level": 6, "name": "互动动作", "unit": "Move", "question": "每个人正在靠近、撤退、试探还是修复？", "visual": "箭头序列"},
            {"level": 7, "name": "互动回路", "unit": "Loop", "question": "双方如何互相触发并重复？", "visual": "循环图"},
            {"level": 8, "name": "阶段叙事", "unit": "Narrative", "question": "这件事在关系阶段和自我故事里意味着什么？", "visual": "阶段地图"},
            {"level": 9, "name": "系统审视", "unit": "System", "question": "高维关系动力和演化方向是什么？", "visual": "系统动力面板"},
        ],
        "classification_tree": _classification_tree(),
        "five_w_two_h": [
            {"key": "what", "label": "What", "question": "这是什么事实、信号、情绪或模式？"},
            {"key": "why", "label": "Why", "question": "为什么重要，背后有什么需求、边界或关系任务？"},
            {"key": "who", "label": "Who", "question": "涉及谁，谁主动，谁回应，谁被触发？"},
            {"key": "when", "label": "When", "question": "发生在什么关系阶段和时间点？"},
            {"key": "where", "label": "Where", "question": "出现在线上、线下、公共、私密或压力场景中？"},
            {"key": "how", "label": "How", "question": "如何识别、验证、回应、训练和复盘？"},
            {"key": "how_much", "label": "How much", "question": "强度、风险、置信度、边界等级和优先级是多少？"},
        ],
        "visual_components": _visual_components(),
        "mastery_stages": [
            {"level": 0, "name": "知道", "definition": "能说出概念", "test": "能复述定义和边界"},
            {"level": 1, "name": "辨认", "definition": "能在案例中看见", "test": "能指出信号和情绪标签"},
            {"level": 2, "name": "操作", "definition": "能生成安全回应", "test": "能写出轻验证和共情回应"},
            {"level": 3, "name": "迁移", "definition": "能跨场景使用", "test": "能从暧昧迁移到冲突修复"},
            {"level": 4, "name": "自然", "definition": "不靠模板也能稳定做对", "test": "真实复盘中重复稳定出现"},
        ],
        "three_natures_management": [
            {"nature": "善", "management": "文化管理", "relationship_use": "鼓励主动表达、欣赏、照顾、修复，把好意变成可持续习惯。"},
            {"nature": "恶", "management": "制度管理", "relationship_use": "对操控、胁迫、跟踪、羞辱、越界设置硬阻断和安全规则。"},
            {"nature": "非善非恶", "management": "绩效管理", "relationship_use": "对模糊、懒惰、习惯、能力不足使用指标、反馈、复盘和训练迭代。"},
        ],
        "question_templates": [
            {"scene": "情绪模糊", "template": "我不确定自己理解得对不对，你是更失落，还是更有点被忽略？"},
            {"scene": "边界试探", "template": "我想靠近一点，但如果你现在需要空间，我也尊重。"},
            {"scene": "冲突修复", "template": "我先不解释，我听见的是你刚才很委屈，对吗？"},
            {"scene": "高维复盘", "template": "这次互动里，我们各自触发了什么旧模式？下一次最小修正动作是什么？"},
        ],
        "material_library": _material_library(),
        "module_templates": _module_templates(),
        "learning_map": _learning_map(),
        "quality_gates": _quality_gates(),
    }


@router.get("/curriculum-graph")
def curriculum_graph(session: Session = Depends(get_session)) -> dict[str, Any]:
    """返回八阶路径课程图谱：任务、评分、证据、晋级条件和可视化边。"""
    attempts = list(session.exec(select(TrainingAttempt).order_by(_sql_column(TrainingAttempt.created_at).desc()).limit(120)).all())
    mistakes = list(session.exec(select(MistakeLog).order_by(_sql_column(MistakeLog.created_at).desc()).limit(80)).all())
    sessions = list(session.exec(select(PracticeSession).order_by(_sql_column(PracticeSession.updated_at).desc()).limit(30)).all())
    events = list(session.exec(select(PracticeEvent).order_by(_sql_column(PracticeEvent.created_at).desc()).limit(120)).all())
    nodes = _curriculum_nodes(attempts, mistakes, sessions, events)
    current = _current_curriculum_node(nodes)
    return {
        "version": "2026-05-21.curriculum-v1",
        "axiom": "八阶路径不是静态清单，而是从元基础到自然能力的课程图谱：每个节点都有任务、证据、评分和晋级门槛。",
        "current_node_id": current["id"],
        "current_stage": current,
        "overall_progress": round(sum(float(node["progress"]) for node in nodes) / len(nodes), 1),
        "nodes": nodes,
        "edges": _curriculum_edges(nodes),
        "practice_plan": _curriculum_practice_plan(current),
        "evidence_summary": _curriculum_evidence_summary(attempts, mistakes, sessions, events),
        "visual_layers": [
            {"id": "path_graph", "name": "阶段路径图", "use": "看见从默认沉默到被爱的完整路线。"},
            {"id": "mastery_bars", "name": "掌握进度条", "use": "用数字判断每阶是否只是知道，还是能操作和迁移。"},
            {"id": "evidence_cards", "name": "晋级证据卡", "use": "把抽象能力落到训练次数、分数、错题和会话轨迹。"},
            {"id": "next_gate", "name": "下一关口", "use": "每次只推进一个最小可执行动作。"},
        ],
    }


def _classification_tree() -> list[dict[str, Any]]:
    return [
        {"id": "scene", "name": "场景分类", "axis": ["Where", "When"], "children": ["初识", "破冰", "日常闲聊", "暧昧试探", "冲突爆发", "道歉修复", "边界协商"]},
        {"id": "relationship_stage", "name": "关系阶段分类", "axis": ["When"], "children": ["陌生", "初识", "熟悉", "暧昧", "确认关系", "稳定", "冲突期", "修复期"]},
        {"id": "signals", "name": "信息与信号分类", "axis": ["What"], "children": ["事实信息", "状态信息", "关系信息", "边界信息", "连接请求", "撤退信号", "修复信号"]},
        {"id": "emotion_feeling", "name": "情绪与感受分类", "axis": ["What", "How much"], "children": ["喜", "怒", "哀", "惧", "爱", "羞", "混合情绪", "被看见/被忽略"]},
        {"id": "need_boundary", "name": "需求与边界分类", "axis": ["Why", "How much"], "children": ["被理解", "被重视", "被安抚", "有空间", "时间边界", "情绪边界", "关系边界"]},
        {"id": "attachment", "name": "依恋与人格倾向分类", "axis": ["Who"], "children": ["安全型", "焦虑型", "回避型", "恐惧回避型", "未知型"]},
        {"id": "interaction_move", "name": "互动动作分类", "axis": ["How"], "children": ["打开", "靠近", "试探", "撤退", "攻击", "防御", "修复", "协商", "结束"]},
        {"id": "response_strategy", "name": "回应策略分类", "axis": ["How"], "children": ["共情反射", "情绪命名", "轻验证", "开放提问", "边界表达", "冲突降温", "负责式道歉"]},
        {"id": "risk_safety", "name": "风险与安全分类", "axis": ["How much"], "children": ["低风险", "中风险", "高风险", "危机风险"]},
        {"id": "learning_task", "name": "学习任务分类", "axis": ["How"], "children": ["观察题", "分类题", "情绪题", "需求题", "边界题", "回应题", "复盘题", "迁移题"]},
        {"id": "source_quality", "name": "数据来源与质量分类", "axis": ["What", "How much"], "children": ["权威研究", "公开论文", "用户本地提交", "AI 合成", "社交平台抽象模式"]},
        {"id": "high_dimensional_review", "name": "高维复盘分类", "axis": ["Why", "System"], "children": ["事实层", "信号层", "情绪层", "需求层", "边界层", "回路层", "叙事层", "行动层"]},
    ]


def _visual_components() -> list[dict[str, Any]]:
    return [
        {"id": "safety_base", "name": "安全-边界-连接三角", "numeric": ["safety_score", "boundary_score", "connection_score"], "visual": "三角基座图", "training_use": "先判断能不能继续推进。"},
        {"id": "signal_highlight", "name": "信号高亮图", "numeric": ["confidence"], "visual": "原话分层高亮", "training_use": "把事实、假设、风险分开。"},
        {"id": "emotion_thermometer", "name": "情绪温度计", "numeric": ["emotion_intensity"], "visual": "1-10 强度条", "training_use": "决定先共情还是先讨论事情。"},
        {"id": "emotion_flow_curve", "name": "情绪流曲线", "numeric": ["start", "peak", "turning_point", "afterglow"], "visual": "时间轴曲线", "training_use": "看见触发、升级、转折和修复。"},
        {"id": "need_radar", "name": "需求雷达", "numeric": ["understood", "valued", "soothed", "space", "certainty"], "visual": "多维雷达", "training_use": "识别最该回应的隐藏需求。"},
        {"id": "boundary_band", "name": "边界红黄绿带", "numeric": ["boundary_level"], "visual": "风险色带", "training_use": "避免把靠近变成入侵。"},
        {"id": "interaction_loop", "name": "互动回路图", "numeric": ["loop_strength"], "visual": "双方触发回路", "training_use": "找出打断负循环的最小动作。"},
        {"id": "toolbox_matrix", "name": "工具箱矩阵", "numeric": ["strategy_fit_score"], "visual": "场景 x 工具矩阵", "training_use": "按场景选择工具，而不是用一个规律解释所有事。"},
        {"id": "ability_radar", "name": "能力雷达", "numeric": ["mastery"], "visual": "技能结构图", "training_use": "把熟能生巧拆成可见进度。"},
        {"id": "evolution_panel", "name": "进化生命体面板", "numeric": ["sources", "raw_items", "annotations", "assets"], "visual": "流水线指标面板", "training_use": "确认系统有没有持续变聪明。"},
    ]


def _material_library() -> list[dict[str, Any]]:
    """World-class but compact learning material contracts for core axes."""
    return [
        _axis_material(
            "micro_signal",
            "微关系信号",
            "看见对方没直接说出口的靠近、犹豫、退缩和求确认。",
            ["停顿变长", "补一句解释", "撤回消息", "语气变软", "从事实跳到感受", "用玩笑试探边界"],
            ["好奇", "轻松", "犹豫", "紧张", "被看见", "怕打扰"],
            "TA说“我其实不太会和刚认识的人聊很深”，表面是说明习惯，底层是在测试你会不会逼近。",
            "没关系，我们可以从轻一点的地方开始。你刚才愿意提醒节奏，我反而觉得挺安心的。",
            ["把沉默判成冷淡", "把试探判成表白", "连续追问让信号变压力"],
        ),
        _axis_material(
            "emotion_flow",
            "情绪流动",
            "识别情绪从触发、升高、转折到余波的全过程。",
            ["语速变快", "句子变短", "开始解释自己", "从抱怨转成沉默", "出现身体词"],
            ["委屈", "失落", "悬着", "松一口气", "羞耻", "被安抚"],
            "TA说“我也不是要你马上解决”，说明情绪需要先被承接，事情方案可以晚一点。",
            "我先不急着给办法。听起来你更需要我知道这件事让你有点撑不住，对吗？",
            ["只讲道理", "马上给建议", "复读情绪词但没有原因"],
        ),
        _axis_material(
            "boundary_consent",
            "边界同意",
            "让靠近、请求、拒绝和亲密节奏都有真实选择。",
            ["对方说先不了", "回复变慢", "用可能/也许", "身体后退", "补充条件"],
            ["安心", "被尊重", "压迫", "不确定", "想靠近", "需要空间"],
            "TA说“今天可能不太方便”，不等于考验诚意，而是给出边界信号。",
            "好，那我们不赶。你方便的时候再说；如果只是想换个轻松方式，我也可以配合。",
            ["把犹豫当同意", "用失望逼对方答应", "给退路但继续施压"],
        ),
        _axis_material(
            "flirty_tension",
            "暧昧张力",
            "在好奇、轻挑战和退路之间制造舒服的靠近感。",
            ["半开玩笑夸你", "分享小秘密", "延长聊天", "问你怎么看她", "用表情缓冲"],
            ["心动", "好玩", "紧张", "期待", "害羞", "怕太明显"],
            "TA说“跟你聊天时间过得挺快”，不是要求你立刻定义关系，而是给出低压力靠近。",
            "我也有这种感觉。先不急着定义，至少今晚这个聊天质量我想给高分。",
            ["逼问是不是喜欢", "油腻夸张", "只撩不接情绪"],
        ),
        _axis_material(
            "conflict_repair",
            "冲突修复",
            "从争输赢转向承认影响、修复信任和约定下一步。",
            ["你每次都这样", "说了也没用", "不想聊了", "旧事被带出", "解释被打断"],
            ["生气", "委屈", "失望", "不信任", "疲惫", "想被负责"],
            "TA说“我现在不知道该怎么相信你”，重点不是再解释一次，而是信任需要证据。",
            "你现在不信是合理的。我先承认这次影响，下一步我做一件可检查的小事，而不是让你马上原谅。",
            ["急着自证清白", "要求对方别翻旧账", "道歉后立刻索要原谅"],
        ),
        _axis_material(
            "long_connection",
            "长期连接",
            "把喜欢变成稳定节奏、共同约定和可复盘行动。",
            ["反复说随便", "对未来含糊", "日常报备减少", "小承诺落空", "偏好不再解释"],
            ["稳定", "安心", "疲惫", "被忽略", "确定感", "共同感"],
            "TA说“我不是不想规划，只是怕说了做不到”，说明承诺需要拆小。",
            "那我们先不做很大的承诺。只约一个本周能完成的小动作，周末再一起复盘。",
            ["只在爆发时谈规则", "把长期理解成控制", "承诺太大但无执行证据"],
        ),
        _axis_material(
            "humor_interaction",
            "幽默互动",
            "用低压力幽默降防御，但不羞辱、不躲避真实问题。",
            ["对方轻吐槽", "气氛变硬", "话题太正式", "需要破冰", "双方都还有余力"],
            ["轻松", "被逗笑", "尴尬缓解", "不被冒犯", "安全", "松动"],
            "TA说“我今天脑子像没开机”，可以用自嘲陪她放松，而不是评价她状态差。",
            "那我们今天先不开高性能模式，我也切到省电聊天档，慢慢来。",
            ["拿对方缺点开玩笑", "用笑话盖过边界", "在高压冲突中硬幽默"],
        ),
        _axis_material(
            "nvc_choice",
            "感受-期待-选择",
            "把真诚表达拆成我的状态、低压力期待和对方可选择的退路。",
            ["我会有点悬着", "我希望", "如果你忙也可以", "不用现在回答", "你可以纠正我"],
            ["喜欢", "不安", "期待", "安心", "想靠近", "怕绑架对方"],
            "TA临时改行程时，你既要说出不安，也不能把期待说成命令。",
            "听到又要改时间，我会有点悬着。如果能提前说一声，我会更安心；你今天忙的话我们改天也可以。",
            ["你必须", "如果你不答应就是不在乎", "假装给选择但实际逼迫"],
        ),
        _axis_material(
            "deep_emotional_connection",
            "深度情感连接",
            "通过开放式提问、关键词捕捉、事实情绪区分和镜子技术，让对方感到被真正理解。",
            ["对方给出关键词", "事实后面跟着情绪词", "重复强调某个细节", "说完后停顿", "用玩笑保护脆弱"],
            ["被理解", "被接住", "松动", "安心", "愿意展开", "独特连接"],
            "TA说“我最近总觉得自己在硬撑”，重点不是立刻安慰，而是先照见关键词、事实和情绪的层次。",
            "我听见你说“硬撑”。事实上是事情还在推进，感受上像一直没人真正接住你。这个理解接近吗？你愿意从最累的一个细节说起吗？",
            ["把开放式提问做成审问", "只复述文字不照见情绪", "把猜测说成诊断", "用深聊逼对方暴露隐私"],
            technique_cards=_deep_connection_technique_cards(),
        ),
        _axis_material(
            "self_disclosure_depth",
            "自我表露深度",
            "根据关系安全度选择事实、观点、情感、脆弱或存在层，推进亲密但不越界。",
            ["突然说很私密的事", "说完后后悔", "要求对方交换秘密", "对方沉默或退缩", "表露后情绪变强"],
            ["信任", "羞耻", "犹豫", "被接住", "后悔", "亲密"],
            "TA说“我不是不想说，是一说到这个我就觉得自己很糟”，这已经进入脆弱层，不能再催促解决。",
            "这已经不是事情本身了，更像碰到了羞耻感。我们可以慢一点，你不用把最深的部分一次说完。",
            ["把深度当亲密证明", "交浅言深", "逼问创伤", "单方面倾倒", "没有退路"],
            technique_cards=_self_disclosure_technique_cards(),
        ),
        _axis_material(
            "relationship_need_calibration",
            "关系需求校准",
            "把性别化、标签化判断转成可观察的情绪、安全、价值、能力和认同需求。",
            ["强调你讲得都对但我不舒服", "说临时变动让我没底", "觉得自己帮不上忙", "喜欢有主见但不想被安排", "公开玩笑后变沉默"],
            ["不舒服", "没底", "被需要", "安心", "尴尬", "被尊重"],
            "TA说“你讲得都对，但我还是觉得不舒服”，重点不是证明逻辑，而是先承接感受。",
            "我先不急着证明谁对。听起来你不是缺解释，而是希望我知道这件事让你心里不舒服，对吗？",
            ["女人都这样", "你就是情绪化", "把安全感污名化为控制", "用强势测试服从", "贴受虐/恋恶等病理标签"],
            technique_cards=_relationship_need_technique_cards(),
        ),
        _axis_material(
            "developmental_emotion_transition",
            "发展性情绪跃迁",
            "用教育发展理论把情绪识别、情绪流动、支架回应和元认知整合连成一条可训练路径。",
            ["情绪突然变强", "同一句话里有开心和害怕", "愤怒后露出委屈", "反复确认旧模式", "对方沉默或防御"],
            ["不安", "委屈", "羞耻", "悲欣交集", "悬着", "被接住"],
            "TA说“跟你聊天会有点开心，但我也怕太快”，不是单一喜欢或拒绝，而是正负混合情绪正在上升。",
            "我听见两个感觉同时在：开心，也有点怕节奏太快。我们可以先承认这份舒服，不急着把关系定义完。",
            ["只贴一个情绪标签", "强唤醒时过早反思", "把猜测当诊断", "忽略年龄阶段和承载力", "没有暂停出口"],
            technique_cards=_developmental_emotion_transition_cards(),
        ),
    ]


def _axis_material(
    axis_id: str,
    name: str,
    purpose: str,
    signals: list[str],
    emotion_words: list[str],
    scene: str,
    better_response: str,
    anti_patterns: list[str],
    technique_cards: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    material = {
        "id": axis_id,
        "name": name,
        "purpose": purpose,
        "beginner_definition": f"先学会在真实对话里认出{name}，再决定要不要回应。",
        "expert_definition": f"{name}不是一个词，而是一组事实、情绪、边界、节奏和互动后果的组合判断。",
        "signals": signals,
        "emotion_words": emotion_words,
        "degree_scale": [
            {"level": 1, "label": "微弱", "cue": "只是一点语气变化，先观察。"},
            {"level": 2, "label": "轻度", "cue": "出现一句可回应线索，用轻验证。"},
            {"level": 3, "label": "中度", "cue": "情绪或边界已影响聊天节奏，先承接。"},
            {"level": 4, "label": "强烈", "cue": "对方开始防御、沉默或明显靠近，需要明确选择。"},
            {"level": 5, "label": "高风险", "cue": "出现压迫、羞辱、胁迫或危机信号，停止推进。"},
        ],
        "scene_example": {
            "context": scene,
            "poor_response": "你想太多了，放轻松就行。",
            "better_response": better_response,
            "why": "更好回应必须贴合当前原话、命名可校正感受、保留边界出口。",
        },
        "dialogue_template": [
            {"speaker": "TA", "line": "先复述真实原话或关键动作。"},
            {"speaker": "我", "line": "我听见/注意到的是一个具体线索，不急着评价。"},
            {"speaker": "我", "line": "用一个感受词或需要假设轻轻校准。"},
            {"speaker": "我", "line": "给对方继续、暂停、纠正你的选择。"},
        ],
        "practice_drills": [
            "从一段对话里圈出 3 个事实信号，不写解释。",
            "给每个信号配 1 个情绪词和 1 个边界可能。",
            "写出低质量回应和更好回应，并说明为什么。",
            "迁移到初识、暧昧、冲突、修复各 1 个场景。",
        ],
        "anti_patterns": anti_patterns,
        "quality_contract": "每张卡必须有场景故事、完整对话、低质量回应、更好回应、原因拆解、边界出口和迁移练习。",
    }
    if technique_cards:
        material["technique_cards"] = technique_cards
    return material


def _deep_connection_technique_cards() -> list[dict[str, Any]]:
    return [
        {
            "id": "open_question",
            "name": "开放式提问",
            "goal": "打开空间，而不是逼对方交代。",
            "terms": ["开放题", "轻入口", "单点问题", "低压力邀请", "可退出问题"],
            "keywords": ["哪一刻", "怎么发生的", "你当时", "后来呢", "对你来说", "如果愿意"],
            "steps": [
                "先接住原话，不立刻问第二个问题。",
                "只选一个入口：时间、动作、转折或感受。",
                "用“哪一刻/怎么/什么变化”提问。",
                "补一个退出权：不想展开也可以。",
            ],
            "degree_scale": [
                {"level": 1, "label": "轻入口", "cue": "问一个具体但不私密的问题。"},
                {"level": 2, "label": "展开", "cue": "围绕一个关键词追问一层。"},
                {"level": 3, "label": "深聊", "cue": "进入意义和感受，但允许跳过。"},
                {"level": 4, "label": "脆弱", "cue": "对方开始说害怕、委屈、孤独等核心感受。"},
                {"level": 5, "label": "停止", "cue": "对方沉默、防御、转移或明确不想说。"},
            ],
            "sentence_patterns": [
                "你愿意说说，刚才哪个细节让你最有感觉吗？",
                "这件事对你来说，最卡住的是哪一刻？",
                "如果只说一点点，你最想先说哪部分？",
            ],
            "bad_patterns": ["为什么你会这样？", "你到底怎么想的？", "然后呢然后呢？"],
            "comparisons": [
                {
                    "axis": "功能目标",
                    "open_question": "打开叙述空间，让对方补充事实、感受、意义和细节。",
                    "closed_question": "确认一个判断点，让对方用是/否/选项快速校准。",
                    "use_rule": "先开放获取材料，再封闭确认理解；顺序反了容易像盘问。",
                },
                {
                    "axis": "典型句式",
                    "open_question": "那一刻你心里发生了什么？这件事对你最重的部分是哪一段？",
                    "closed_question": "我理解成你更在意被忽略，而不是事情本身，对吗？",
                    "use_rule": "开放题用“什么/怎么/哪一刻”，封闭题用“是不是/对吗/更像A还是B”。",
                },
                {
                    "axis": "关系效果",
                    "open_question": "让对方感到你愿意听完整的人，而不是只要答案。",
                    "closed_question": "让对方感到你在认真校准，不把猜测伪装成懂他。",
                    "use_rule": "对方刚打开时少封闭；对方说乱了、累了、沉默时用封闭题减负。",
                },
                {
                    "axis": "风险边界",
                    "open_question": "连续开放追问会变成深聊逼供，让对方觉得没有退路。",
                    "closed_question": "连续封闭提问会变成审问，让对方只想防御或敷衍。",
                    "use_rule": "最多两问一停顿；每次深入都补一句“你不想说也可以”。",
                },
            ],
        },
        {
            "id": "closed_question",
            "name": "封闭式问题",
            "goal": "用低负担确认帮助对方校准，而不是用是非题控制对话。",
            "terms": ["确认题", "校准题", "二选一", "是非题", "收束问题", "低负担回应"],
            "keywords": ["是不是", "对吗", "更像A还是B", "能不能这样理解", "我有没有听偏", "要不要先停"],
            "steps": [
                "先说明你是在校准，不是在下结论。",
                "只确认一个点：事实、情绪、需要或边界。",
                "给出可纠正选项：对、不对、接近、我听偏了。",
                "确认后立刻放慢，不连续追问。",
            ],
            "degree_scale": [
                {"level": 1, "label": "轻确认", "cue": "确认一个事实点，例如时间、选择或是否愿意继续。"},
                {"level": 2, "label": "感受校准", "cue": "确认感受假设，例如更像委屈还是累。"},
                {"level": 3, "label": "需要校准", "cue": "确认对方是否需要理解、空间、支持或确定感。"},
                {"level": 4, "label": "边界确认", "cue": "确认是否继续、暂停、换话题或降低深度。"},
                {"level": 5, "label": "停止推进", "cue": "对方只回嗯、随便、算了，说明封闭题也要停。"},
            ],
            "sentence_patterns": [
                "我这样理解接近吗：你不是不想聊，是有点不知道怎么开口？",
                "这更像是累，还是有点被忽略的感觉？",
                "我们先停在这里，会不会更舒服一点？",
            ],
            "bad_patterns": ["你是不是就是不想说？", "你到底爱不爱我？", "所以你承认你错了？", "我说得对吧？"],
        },
        {
            "id": "keyword_capture",
            "name": "捕捉关键词",
            "goal": "从对方自己的词进入他的世界。",
            "terms": ["核心词", "重复词", "停顿词", "情绪词", "隐喻词", "转折词"],
            "keywords": ["硬撑", "突然", "其实", "算了", "没事", "有点", "不知道为什么", "没人"],
            "steps": [
                "标出对方重复或加重的词。",
                "判断它更像事实词、情绪词、关系词还是边界词。",
                "用对方原词复述，不急着替换成你的解释。",
                "围绕这个词问一个现实层或感受层问题。",
            ],
            "degree_scale": [
                {"level": 1, "label": "事实词", "cue": "工作、时间、地点、动作。"},
                {"level": 2, "label": "状态词", "cue": "累、空、乱、卡、悬。"},
                {"level": 3, "label": "关系词", "cue": "没人、被忽略、不确定、靠不住。"},
                {"level": 4, "label": "核心词", "cue": "反复出现且伴随停顿或情绪变化。"},
                {"level": 5, "label": "红线词", "cue": "害怕、控制、威胁、伤害，进入安全优先。"},
            ],
            "sentence_patterns": [
                "我注意到你用了“{关键词}”这个词。",
                "你说“{关键词}”的时候，我感觉它好像挺重的。",
                "这个“{关键词}”更像事情本身，还是它带来的感受？",
            ],
            "bad_patterns": ["抓错词只为转话题", "把对方的词改成自己的诊断", "一次抓三四个词连续追问"],
        },
        {
            "id": "fact_emotion_split",
            "name": "区分事实与情绪",
            "goal": "让对方感觉你既听懂事情，也听见情绪。",
            "terms": ["事实层", "解释层", "情绪层", "需要层", "边界层"],
            "keywords": ["事实是", "我猜感受是", "这不是结论", "你可以纠正我", "更像是"],
            "steps": [
                "事实层只说可观察内容：发生了什么。",
                "解释层先悬置：不要马上判断谁对谁错。",
                "情绪层用可校正词：可能、有点、更像。",
                "需要层只轻轻点到，不替对方下结论。",
            ],
            "degree_scale": [
                {"level": 1, "label": "事实清楚", "cue": "能复述发生了什么。"},
                {"level": 2, "label": "解释分离", "cue": "不把猜测当事实。"},
                {"level": 3, "label": "情绪命名", "cue": "能说出委屈、悬着、孤独等词。"},
                {"level": 4, "label": "需要浮现", "cue": "能看见被理解、确定感、支持等需要。"},
                {"level": 5, "label": "边界优先", "cue": "情绪强烈或风险出现，先暂停推进。"},
            ],
            "sentence_patterns": [
                "事实上是……；感受上可能是……",
                "我先把事情和感受分开说，你看对不对。",
                "这件事本身是……，它带给你的感觉更像……吗？",
            ],
            "bad_patterns": ["事实没听清就共情", "把情绪当矫情", "用分析覆盖感受"],
        },
        {
            "id": "feeling_identification",
            "name": "感受识别与命名",
            "goal": "把模糊情绪拆成身体线索、情绪词、强度和需要，不把解释误当感受。",
            "terms": ["感受词", "身体线索", "强度词", "复合情绪", "伪感受", "需要信号"],
            "keywords": ["有点", "说不上来", "心里堵", "悬着", "松了一口气", "委屈", "紧张", "被看见"],
            "steps": [
                "先找身体线索：胸口、喉咙、胃、肩颈、呼吸、眼眶。",
                "把解释句改写成感受词：不是“你不重视我”，而是“我有点失落”。",
                "用强度词校准：一点、明显、很、快撑不住、已经超界。",
                "把感受连接到需要：理解、确定感、空间、支持、尊重或选择权。",
            ],
            "degree_scale": [
                {"level": 1, "label": "轻微波动", "cue": "有点在意、轻微紧张、短暂失落，还能继续对话。"},
                {"level": 2, "label": "可命名", "cue": "能说出委屈、担心、期待、尴尬、安心等单一感受。"},
                {"level": 3, "label": "复合情绪", "cue": "同时有喜欢和害怕、期待和不安、愤怒和委屈。"},
                {"level": 4, "label": "身体化", "cue": "出现心跳快、胸口堵、喉咙紧、胃沉、想躲等身体信号。"},
                {"level": 5, "label": "超出承载", "cue": "对话会加重崩溃、羞耻、恐惧或安全风险，应暂停并转向支持。"},
            ],
            "sentence_patterns": [
                "我不确定对不对，你刚才更像是有点失落，而不是单纯生气？",
                "这句话听起来，事实是一件小事，但身体上好像让你悬了一下。",
                "如果把它说成感受，可能是委屈、紧张，还是更接近不被重视？",
            ],
            "bad_patterns": ["你太敏感了", "这有什么好难过的", "你就是焦虑型", "别情绪化", "我知道你就是吃醋"],
            "feeling_spectrum": [
                {
                    "family": "靠近",
                    "words": ["安心", "被看见", "心动", "期待", "亲近", "踏实"],
                    "body_cues": ["呼吸变顺", "身体前倾", "语速变柔", "愿意多说"],
                    "need_signal": "希望连接被接住，但仍需要节奏和选择权。",
                },
                {
                    "family": "不安",
                    "words": ["紧张", "悬着", "怕打扰", "不确定", "患得患失", "没底"],
                    "body_cues": ["心跳快", "反复看消息", "胸口发紧", "想确认"],
                    "need_signal": "需要确定感、节奏说明和不被嘲笑的安全感。",
                },
                {
                    "family": "受伤",
                    "words": ["失落", "委屈", "被忽略", "酸", "难堪", "孤单"],
                    "body_cues": ["喉咙紧", "眼眶热", "沉默变长", "想退开"],
                    "need_signal": "需要被承认影响，而不是被教育应该大度。",
                },
                {
                    "family": "防御",
                    "words": ["烦", "抗拒", "被逼", "羞耻", "想躲", "不耐烦"],
                    "body_cues": ["身体后撤", "短句回应", "语气变硬", "转移话题"],
                    "need_signal": "需要边界、空间、停止追问和可退出选择。",
                },
            ],
        },
        {
            "id": "mirror_technique",
            "name": "镜子技术",
            "goal": "把听见的层次照回去，并邀请对方校准。",
            "terms": ["镜像", "校准", "照回", "可纠正理解", "不诊断"],
            "keywords": ["我听见的是", "我不确定对不对", "像是", "这个理解接近吗", "你可以纠正我"],
            "steps": [
                "照关键词：复述对方自己的词。",
                "照事实：简短说出可观察事实。",
                "照情绪：说一个可校正的感受假设。",
                "照选择：允许对方纠正、暂停或只说一小段。",
            ],
            "degree_scale": [
                {"level": 1, "label": "复述", "cue": "能准确照回关键词。"},
                {"level": 2, "label": "双层镜像", "cue": "能分开事实和情绪。"},
                {"level": 3, "label": "深层镜像", "cue": "能轻轻点到需要。"},
                {"level": 4, "label": "关系镜像", "cue": "能照见这句话对关系的意义。"},
                {"level": 5, "label": "安全收束", "cue": "对方承受不了时停止深挖。"},
            ],
            "sentence_patterns": [
                "我听见你说“{关键词}”。事实层是……，感受层可能是……。这个理解接近吗？",
                "我不确定说得准不准，你像是在……，也有一点……？",
                "如果我理解偏了，你可以直接纠正我。",
            ],
            "bad_patterns": ["我完全懂你", "你就是缺爱", "你其实是在逃避", "我来告诉你真正原因"],
        },
    ]


def _self_disclosure_technique_cards() -> list[dict[str, Any]]:
    return [
        {
            "id": "disclosure_depth_scale",
            "name": "自我表露五级刻度",
            "goal": "识别当前分享处于哪一层，避免把越深误当越亲密。",
            "terms": ["表露深度", "表露广度", "脆弱性", "私密性", "互惠性", "关系安全度"],
            "keywords": ["事实", "观点", "情感", "脆弱", "羞耻", "创伤", "终极渴望"],
            "steps": [
                "先判断内容层级：事实、观点、情感、脆弱或存在。",
                "再判断关系安全度：是否有信任、保密、接纳和时间空间。",
                "观察互惠：对方是否有余力继续，而不是被迫交换秘密。",
                "补边界出口：可以停、可以晚点说、可以只说一小段。",
            ],
            "degree_scale": [
                {"level": 1, "label": "事实层", "cue": "公开事实、兴趣、一般经历，适合初识。"},
                {"level": 2, "label": "观点层", "cue": "喜好、立场、评价，适合轻度熟悉。"},
                {"level": 3, "label": "情感层", "cue": "喜欢、害怕、失落、愤怒，需要基本信任。"},
                {"level": 4, "label": "脆弱层", "cue": "不安全感、羞耻、创伤，需要稳定接纳。"},
                {"level": 5, "label": "存在层", "cue": "终极恐惧、深层渴望，适合高度安全关系或专业场域。"},
            ],
            "sentence_patterns": [
                "这个话题好像已经有点深了，我们可以慢一点。",
                "你不用一次讲完，只说你觉得安全的一小段就够了。",
                "我会认真听，但你可以随时停下来或纠正我。",
            ],
            "bad_patterns": ["你都说到这了就继续说完", "我也告诉你一个秘密，你必须也说", "这有什么好羞耻的", "你太脆弱了"],
            "feeling_spectrum": [
                {
                    "family": "表露前",
                    "words": ["犹豫", "焦虑", "害怕", "期待", "试探"],
                    "body_cues": ["停顿", "笑着带过", "声音变轻", "反复确认"],
                    "need_signal": "需要安全、节奏和不被嘲笑。",
                },
                {
                    "family": "表露中",
                    "words": ["羞耻", "释放", "悲伤", "紧张", "松动"],
                    "body_cues": ["眼眶热", "喉咙紧", "手抖", "深呼吸"],
                    "need_signal": "需要被接住、被保密和被允许不完整。",
                },
                {
                    "family": "被接纳后",
                    "words": ["轻松", "温暖", "感激", "联结", "安心"],
                    "body_cues": ["肩膀放松", "语速变慢", "愿意补充", "靠近"],
                    "need_signal": "需要稳定回应和不被拿来要挟。",
                },
                {
                    "family": "被拒绝后",
                    "words": ["后悔", "羞耻加剧", "自我否定", "退缩", "防御"],
                    "body_cues": ["沉默", "身体后撤", "短句", "转移话题"],
                    "need_signal": "需要停止追问、修复安全或离开不安全场域。",
                },
            ],
        }
    ]


def _module_templates() -> list[dict[str, Any]]:
    return [
        {
            "module": "资源海洋",
            "tabs": ["概念", "场景故事", "完整对话", "对比回应", "举一反三", "练习任务", "来源边界"],
            "required_fields": ["title", "scene", "dialogue_script", "poor_response", "better_response", "practice_task", "source_policy"],
            "design_rule": "卡片只展示学习入口，详情页承载完整案例；列表不得用同一段话套不同标签伪装变体。",
        },
        {
            "module": "表达工具箱",
            "tabs": ["定义", "机制", "适用场景", "微步骤", "真实对话", "反模式", "练习阶梯"],
            "required_fields": ["name", "formula", "description", "micro_steps", "example_before", "example_after", "risk_flags"],
            "design_rule": "工具必须解释为什么有效、什么时候禁用、如何从 D1 练到 D5。",
        },
        {
            "module": "知识中枢",
            "tabs": ["概念定义", "原则规律", "5W2H", "图谱位置", "案例证据", "应用建议", "相关资源"],
            "required_fields": ["title", "summary", "content", "tags", "source_metadata", "quality_score"],
            "design_rule": "知识条目不能只是一段摘要，必须说明它在关系动力学地图中的位置。",
        },
        {
            "module": "训练中心",
            "tabs": ["原始信号", "我的回应", "系统评分", "更好版本", "能力归因", "下一题"],
            "required_fields": ["sample", "user_response", "ideal_response", "scores", "attribution", "next_drill"],
            "design_rule": "训练反馈要指出具体哪句话错位，而不是只给总分。",
        },
        {
            "module": "错题本",
            "tabs": ["原题", "错误模式", "重写三版", "关联工具", "迁移场景", "复习计划"],
            "required_fields": ["mistake_pattern", "rewrite_versions", "expression_tools", "review_interval"],
            "design_rule": "错题必须变成下一次可操作动作，而不是情绪化自责。",
        },
    ]


def _relationship_need_technique_cards() -> list[dict[str, Any]]:
    return [
        {
            "id": "need_debias_calibration",
            "name": "需求去偏五步法",
            "goal": "把“女人/男人都怎样”的判断改写成可观察、可验证、可行动的需求假设。",
            "terms": ["需求假设", "去偏改写", "轻验证", "情绪价值", "安全归属", "认同位置"],
            "keywords": ["不舒服", "没底", "被需要", "有主见", "被尊重", "不是要控制", "你可以纠正我"],
            "steps": [
                "只提取原话和动作，不先解释人格或性别。",
                "判断需求轴：情绪承接、安全归属、价值认同、能力感吸引或认同位置。",
                "删除标签：把“情绪化/慕强/认同癖”等词改成具体需求。",
                "轻验证：用“更像是…对吗”邀请对方纠正。",
                "落到行动：给一个可兑现、可检查的小动作。",
            ],
            "degree_scale": [
                {"level": 1, "label": "情绪承接", "cue": "先回应感受是否被看见。"},
                {"level": 2, "label": "安全归属", "cue": "降低不确定，给稳定行动。"},
                {"level": 3, "label": "价值认同", "cue": "表达需要、欣赏和共同成长。"},
                {"level": 4, "label": "能力感", "cue": "展现稳定决策，但不替对方做主。"},
                {"level": 5, "label": "认同位置", "cue": "公开尊重、玩笑边界和社交位置。"},
            ],
            "sentence_patterns": [
                "我先不把它理解成你想太多，更像是这件事让你有点没底，对吗？",
                "你要的可能不是解释，而是我先承认这件事确实让你不舒服。",
                "我可以拿主意，但不替你做主；我们先定两个选项，你选舒服的那个。",
            ],
            "bad_patterns": ["女人都这样", "你就是情绪化", "你是慕强所以听我的", "别作", "我这是为你好"],
            "comparisons": [
                {
                    "axis": "情绪承接",
                    "label_based": "她就是情绪化。",
                    "need_based": "她需要先确认感受被看见，再一起看事实。",
                    "action": "先复述感受，再问是否要方案。",
                },
                {
                    "axis": "安全归属",
                    "label_based": "她控制欲太强。",
                    "need_based": "她对不确定很敏感，需要更稳定的信息和可兑现承诺。",
                    "action": "提前说明变化，约定轻量报备边界。",
                },
                {
                    "axis": "能力感吸引",
                    "label_based": "她慕强，所以要压住她。",
                    "need_based": "她被稳定、决策力和边界感吸引，但仍需要选择权。",
                    "action": "给清晰方案和可选项，不替她决定。",
                },
                {
                    "axis": "认同位置",
                    "label_based": "她太在乎别人怎么看。",
                    "need_based": "她在意公开场合是否被尊重、被放在合适位置。",
                    "action": "修复公开玩笑边界，明确下次不拿她做梗。",
                },
            ],
        }
    ]


def _developmental_emotion_transition_cards() -> list[dict[str, Any]]:
    return [
        {
            "id": "three_layer_model",
            "name": "三层嵌套模型",
            "goal": "把情绪能力从基本反应、社会情绪能力推进到元调节和关系信念。",
            "terms": ["基本情绪", "社会情绪能力", "元情绪", "自我调节", "关系信念", "内化"],
            "steps": [
                "第一层看表达和轮流反应：哭、笑、退缩、靠近、停顿。",
                "第二层看共情、命名、观点采择和调节策略。",
                "第三层看自我模式、价值系统和关系信念。",
                "回应只推进到对方当前能承载的一层。",
            ],
            "degree_scale": [
                {"level": 1, "label": "基本反应", "cue": "先安抚、命名、降低强度。"},
                {"level": 2, "label": "情绪命名", "cue": "能说出开心、难过、生气、害怕等基础词。"},
                {"level": 3, "label": "观点采择", "cue": "能理解自己和对方可能感受不同。"},
                {"level": 4, "label": "元情绪", "cue": "能谈论自己如何看待自己的情绪。"},
                {"level": 5, "label": "人格整合", "cue": "能把情绪模式纳入价值、边界和长期行动。"},
            ],
            "sentence_patterns": [
                "我们先不急着分析原因，只把现在这个感觉说清楚。",
                "这像是一个旧模式被触发了，但我们可以先从这一刻开始。",
                "如果下次这种感觉再出现，你想先怎么提醒自己？",
            ],
            "bad_patterns": ["你太幼稚了", "你应该成熟点", "我来告诉你真正原因", "你就是这种人格"],
        },
        {
            "id": "four_dimension_locator",
            "name": "情绪四维定位",
            "goal": "在回应前先判断强度、效价、指向和时序。",
            "terms": ["强度", "效价", "指向", "时序", "混合情绪", "情绪粒度"],
            "steps": [
                "强度：轻微、中度、强烈、超出承载。",
                "效价：正性、负性、中性、正负混合。",
                "指向：自我、他人、环境、关系。",
                "时序：预期、触发、上升、高峰、下降、残余。",
            ],
            "degree_scale": [
                {"level": 1, "label": "轻微", "cue": "可以轻验证，不需要深挖。"},
                {"level": 2, "label": "可命名", "cue": "用一两个情绪词校准。"},
                {"level": 3, "label": "混合", "cue": "同时承认两种相反感受。"},
                {"level": 4, "label": "高峰", "cue": "先降温和承接，暂停复杂分析。"},
                {"level": 5, "label": "残余模式", "cue": "进入复盘、内化和下一步策略。"},
            ],
            "sentence_patterns": [
                "我先分开说：事情上是……，感受上可能是……",
                "这不是单纯生气，好像也有一点被忽略的委屈，对吗？",
                "现在像是在高峰，我们先把节奏放慢。",
            ],
            "bad_patterns": ["你就是生气了", "这明明是小事", "别矫情", "你到底要怎样"],
        },
        {
            "id": "transition_mechanism",
            "name": "三种跃迁机制",
            "goal": "根据承载力选择同层降级、跨维翻译或跨层整合。",
            "terms": ["同层强度跃迁", "跨维质变跃迁", "跨层元认知跃迁", "同化", "顺应", "支架内化"],
            "steps": [
                "同层强度：先让强度可承载，例如从崩溃到能说一句话。",
                "跨维质变：安全后试探背后的另一种情绪，例如愤怒下的伤心。",
                "跨层整合：在余波期复盘模式和下一步自我提醒。",
                "每次只做一种主跃迁，避免把对话做成分析课。",
            ],
            "degree_scale": [
                {"level": 1, "label": "降级", "cue": "先呼吸、停顿、承认影响。"},
                {"level": 2, "label": "稳定", "cue": "情绪能被命名，开始可对话。"},
                {"level": 3, "label": "翻译", "cue": "从表层情绪转向隐藏情绪或需求。"},
                {"level": 4, "label": "模式", "cue": "看见重复出现的触发回路。"},
                {"level": 5, "label": "内化", "cue": "形成下次能自己使用的提醒句。"},
            ],
            "sentence_patterns": [
                "我们先不解决，先让这股劲降一点。",
                "听起来很生气，但底下会不会也有点伤心？我不确定，你可以纠正。",
                "如果下次这种悬着又出现，你可以先说“我现在需要确定感”。",
            ],
            "bad_patterns": ["你别生气了", "其实你就是缺爱", "这说明你人格有问题", "以后你就按我说的做"],
        },
        {
            "id": "age_scaffold",
            "name": "年龄与承载力支架",
            "goal": "按发展阶段和当前唤醒水平选择词汇、问题和反思深度。",
            "terms": ["最近发展区", "适龄回应", "情绪词汇", "承载力", "支架", "敏感期"],
            "steps": [
                "0-6岁或高唤醒状态：简单命名和安抚，不做抽象解释。",
                "7-11岁：加入规则、因果和我信息。",
                "12-18岁：允许矛盾和身份探索，不急着否定叛逆或迷茫。",
                "18岁+：用元沟通、留白和共同复盘支持自主调节。",
            ],
            "degree_scale": [
                {"level": 1, "label": "命名", "cue": "你现在很难过/害怕/生气。"},
                {"level": 2, "label": "因果", "cue": "你难过是因为刚才那件事。"},
                {"level": 3, "label": "观点采择", "cue": "你和对方可能看见了不同部分。"},
                {"level": 4, "label": "身份", "cue": "这件事碰到了你怎么看自己。"},
                {"level": 5, "label": "价值", "cue": "把情绪转成边界、选择和长期行动。"},
            ],
            "sentence_patterns": [
                "这个感觉有名字，它可能叫委屈。",
                "你可以先只说一小段，不用把全部想明白。",
                "这份情绪在提醒你一个需要：被确认、被尊重，还是有空间？",
            ],
            "bad_patterns": ["你这个年龄不该这样", "小孩子懂什么", "成熟的人不会这样", "你想太多"],
        },
    ]


def _learning_map() -> list[dict[str, str]]:
    return [
        {"step": "1", "name": "看见事实", "action": "只圈可观察线索：原话、停顿、表情、时间、动作。"},
        {"step": "2", "name": "命名状态", "action": "用情绪词、程度词、身体感受描述当下，不评价人格。"},
        {"step": "3", "name": "定位情绪四维", "action": "判断强度、效价、指向和时序，特别标出混合情绪和高峰期。"},
        {"step": "4", "name": "选择跃迁路径", "action": "在同层降级、跨维翻译和跨层整合中只选择一个主动作。"},
        {"step": "5", "name": "识别关系任务", "action": "判断这是靠近、退缩、边界、修复、长期约定还是幽默降压。"},
        {"step": "6", "name": "选择工具", "action": "从表达工具箱选择 1 个主工具和 1 个边界出口。"},
        {"step": "7", "name": "生成回应", "action": "回应必须包含具体原话、感受校准、低压力问题和选择。"},
        {"step": "8", "name": "观察反馈", "action": "看对方是打开、放松、纠正、沉默还是防御。"},
        {"step": "9", "name": "复盘迁移", "action": "把同一结构迁移到另一个场景，形成真正掌握。"},
    ]


def _quality_gates() -> list[dict[str, str]]:
    return [
        {"gate": "上下文一致", "rule": "更好回应必须引用当前场景故事或原始对话，不能套用通用句。"},
        {"gate": "完整对话", "rule": "每个训练卡至少包含 TA 原话、低质量回应、更好回应、TA 反馈和边界收束。"},
        {"gate": "真实变体", "rule": "变体必须改变场景、触发点、情绪流或关系任务，不能只换标签。"},
        {"gate": "边界出口", "rule": "所有靠近、邀请、暧昧、请求类回应都必须给对方选择。"},
        {"gate": "发展适配", "rule": "情绪支架必须匹配年龄阶段、当前唤醒水平和承载力；高峰期先降级，余波期再反思。"},
        {"gate": "合规来源", "rule": "第三方来源只存链接、标题、摘要、短摘录、结构化分析和本地原创改写。"},
        {"gate": "可练习", "rule": "素材必须有练习任务、迁移场景和评分关注点，否则不进入默认展示。"},
    ]


def _curriculum_nodes(
    attempts: list[TrainingAttempt],
    mistakes: list[MistakeLog],
    sessions: list[PracticeSession],
    events: list[PracticeEvent],
) -> list[dict[str, Any]]:
    specs = _curriculum_specs()
    return [_curriculum_node(spec, attempts, mistakes, sessions, events) for spec in specs]


def _curriculum_specs() -> list[dict[str, Any]]:
    return [
        {
            "id": "stage_0_silence",
            "index": 0,
            "name": "第零阶：默认沉默",
            "primitive": "注意力转向外部",
            "description": "从没话题、注意力内缩，进入可观察世界。",
            "tools": ["侦探", "元事实"],
            "tasks": ["记录 3 个环境线索", "把事实和解释分开", "完成一次基础训练"],
            "promotion_rule": "至少完成 1 次训练，并能说出一个可观察事实。",
            "base": 35,
        },
        {
            "id": "stage_1_information",
            "index": 1,
            "name": "第一阶：信息",
            "primitive": "事实交换",
            "description": "交换基本信息，建立初步连接，不连续审问。",
            "tools": ["侦探", "提问 L1"],
            "tasks": ["用环境线索开场", "开放式事实问题", "一次轻自我暴露"],
            "promotion_rule": "能交换 5 个以上事实，并保持对话不关闭。",
            "base": 28,
        },
        {
            "id": "stage_2_emotion",
            "index": 2,
            "name": "第二阶：情绪",
            "primitive": "情绪识别",
            "description": "识别主情绪、强度和混合情绪，先接住再推进。",
            "tools": ["情绪温度计", "诗人"],
            "tasks": ["标注主情绪", "估计 1-10 强度", "写一句情绪反射"],
            "promotion_rule": "连续多次回应能命名情绪且总分稳定超过 65。",
            "base": 18,
        },
        {
            "id": "stage_3_feeling",
            "index": 3,
            "name": "第三阶：感受",
            "primitive": "主体体验",
            "description": "让对方感到你和她站在同一边，而不是评判她。",
            "tools": ["共情", "退路式提问"],
            "tasks": ["命名被忽略/被理解等感受", "给继续说的空间", "避免急着解决"],
            "promotion_rule": "安全回应和情绪识别平均分超过 70，错题减少。",
            "base": 12,
        },
        {
            "id": "stage_4_seeing",
            "index": 4,
            "name": "第四阶：看见",
            "primitive": "未明说线索",
            "description": "捕捉话到嘴边、停顿、姿态、边界试探等微信号。",
            "tools": ["信号高亮", "轻验证"],
            "tasks": ["列出 3 个信号假设", "用轻问句验证", "不把猜测当事实"],
            "promotion_rule": "能把信号、情绪、需求和边界串成一张图。",
            "base": 8,
        },
        {
            "id": "stage_5_appreciation",
            "index": 5,
            "name": "第五阶：欣赏",
            "primitive": "具体照亮",
            "description": "用具体、真实、不讨好的欣赏照亮行为、过程和特质。",
            "tools": ["诗人", "具体化"],
            "tasks": ["写行为欣赏", "写过程欣赏", "写存在欣赏但不越界"],
            "promotion_rule": "风格匹配和连接延展稳定超过 75。",
            "base": 5,
        },
        {
            "id": "stage_6_understanding",
            "index": 6,
            "name": "第六阶：理解",
            "primitive": "内在模型",
            "description": "从单次互动进入模式识别，理解来源、重复回路和未来需求。",
            "tools": ["5W2H", "互动回路图"],
            "tasks": ["完成一次 5W2H 复盘", "识别一个重复模式", "预测一个下一需求"],
            "promotion_rule": "能跨样本稳定预测需求，并在 AI 伴侣中修复状态。",
            "base": 3,
        },
        {
            "id": "stage_7_love",
            "index": 7,
            "name": "第七阶：爱",
            "primitive": "稳定行动",
            "description": "把理解变成稳定、尊重边界、不忽冷忽热的行动。",
            "tools": ["框架", "行动翻译"],
            "tasks": ["设置内核底线", "做一个稳定行动", "在压力中不控制"],
            "promotion_rule": "边界尊重、安全回应、修复能力均超过 80。",
            "base": 1,
        },
        {
            "id": "stage_8_being_loved",
            "index": 8,
            "name": "第八阶：被爱",
            "primitive": "接收与回馈",
            "description": "识别并接收爱意，不因亏欠感、控制欲或麻木把爱推开。",
            "tools": ["被爱日记", "自然回馈"],
            "tasks": ["记录被爱的瞬间", "表达接收感受", "自然回馈而非还债"],
            "promotion_rule": "能稳定接收、表达和回馈爱，不把被爱变成压力。",
            "base": 0,
        },
    ]


def _curriculum_node(
    spec: dict[str, Any],
    attempts: list[TrainingAttempt],
    mistakes: list[MistakeLog],
    sessions: list[PracticeSession],
    events: list[PracticeEvent],
) -> dict[str, Any]:
    score = _stage_score(spec["index"], spec["base"], attempts, mistakes, sessions, events)
    status = "completed" if score >= 85 else "current" if score >= 45 else "locked"
    evidence = _stage_evidence(spec["index"], attempts, mistakes, sessions, events, score)
    return {
        "id": spec["id"],
        "index": spec["index"],
        "name": spec["name"],
        "primitive": spec["primitive"],
        "description": spec["description"],
        "tools": spec["tools"],
        "tasks": spec["tasks"],
        "promotion_rule": spec["promotion_rule"],
        "progress": score,
        "status": status,
        "is_completed": status == "completed",
        "is_current": status == "current",
        "difficulty": "foundation" if spec["index"] <= 2 else "integration" if spec["index"] <= 5 else "advanced",
        "score_formula": "基础分 + 训练次数 + 平均分 + 会话证据 - 未复习错题惩罚，按阶段递减权重。",
        "evidence": evidence,
        "next_action": _stage_next_action(spec["index"], spec["tasks"], evidence, score),
    }


def _stage_score(
    index: int,
    base: int,
    attempts: list[TrainingAttempt],
    mistakes: list[MistakeLog],
    sessions: list[PracticeSession],
    events: list[PracticeEvent],
) -> int:
    attempt_count = len(attempts)
    avg_score = sum(attempt.total_score for attempt in attempts) / attempt_count if attempt_count else 0
    open_mistakes = sum(1 for mistake in mistakes if not mistake.reviewed)
    session_turns = sum(session.total_turns for session in sessions)
    avg_partner_score = sum(session.average_score for session in sessions) / len(sessions) if sessions else 0
    safety_blocks = sum(1 for event in events if event.source == "safety_blocked")

    attempt_weight = max(0.25, 1 - index * 0.08)
    score = float(base)
    score += min(24, attempt_count * 3.5 * attempt_weight)
    score += min(28, avg_score * (0.22 + max(0, 3 - index) * 0.035))
    score += min(18, session_turns * max(0.4, index / 6))
    score += min(18, avg_partner_score * max(0, index - 3) * 0.035)
    score -= min(16, open_mistakes * max(0.4, 1.1 - index * 0.07))
    score -= min(14, safety_blocks * 4)
    if index == 0 and attempt_count:
        score = max(score, 90)
    if index == 1 and attempt_count >= 2:
        score = max(score, 72)
    return round(max(0, min(100, score)))


def _stage_evidence(
    index: int,
    attempts: list[TrainingAttempt],
    mistakes: list[MistakeLog],
    sessions: list[PracticeSession],
    events: list[PracticeEvent],
    score: int,
) -> dict[str, Any]:
    attempts_count = len(attempts)
    avg_score = round(sum(attempt.total_score for attempt in attempts) / attempts_count, 1) if attempts_count else 0
    open_mistakes = sum(1 for mistake in mistakes if not mistake.reviewed)
    session_turns = sum(session.total_turns for session in sessions)
    return {
        "attempts_count": attempts_count,
        "average_training_score": avg_score,
        "open_mistakes": open_mistakes,
        "partner_sessions": len(sessions),
        "partner_turns": session_turns,
        "safety_blocks": sum(1 for event in events if event.source == "safety_blocked"),
        "evidence_label": _stage_evidence_label(index, score, attempts_count, open_mistakes, session_turns),
    }


def _stage_evidence_label(index: int, score: int, attempts_count: int, open_mistakes: int, session_turns: int) -> str:
    if score >= 85:
        return "已有足够晋级证据，可以进入下一阶迁移。"
    if attempts_count == 0:
        return "还没有训练证据，先完成一次对比回应。"
    if open_mistakes >= 5 and index >= 2:
        return "错题积压偏多，先复习再推进。"
    if index >= 4 and session_turns < 3:
        return "高阶需要 AI 伴侣会话轨迹作为证据。"
    return "已有初步证据，继续补齐本阶任务。"


def _stage_next_action(index: int, tasks: list[str], evidence: dict[str, Any], score: int) -> str:
    if score >= 85:
        return "进入下一阶，用不同场景做迁移练习。"
    if evidence["open_mistakes"] >= 3:
        return "先完成到期错题复习，消除同类错误。"
    if index >= 4 and evidence["partner_turns"] < 3:
        return "完成一轮 AI 伴侣对话，生成状态曲线证据。"
    return tasks[0]


def _current_curriculum_node(nodes: list[dict[str, Any]]) -> dict[str, Any]:
    for node in nodes:
        if not node["is_completed"]:
            node["is_current"] = True
            node["status"] = "current"
            return node
    nodes[-1]["is_current"] = True
    return nodes[-1]


def _curriculum_edges(nodes: list[dict[str, Any]]) -> list[dict[str, Any]]:
    edges: list[dict[str, Any]] = []
    for previous, current in pairwise(nodes):
        edges.append({
            "from": previous["id"],
            "to": current["id"],
            "label": "晋级",
            "gate": current["promotion_rule"],
            "unlocked": previous["is_completed"] or previous["is_current"],
        })
    return edges


def _curriculum_practice_plan(current: dict[str, Any]) -> dict[str, Any]:
    return {
        "focus_node_id": current["id"],
        "focus": current["name"],
        "minimum_action": current["next_action"],
        "drills": current["tasks"][:3],
        "reflection": "今天我在哪一刻把事实、解释、情绪、需求和边界分清了？",
    }


def _curriculum_evidence_summary(
    attempts: list[TrainingAttempt],
    mistakes: list[MistakeLog],
    sessions: list[PracticeSession],
    events: list[PracticeEvent],
) -> dict[str, Any]:
    return {
        "training_attempts": len(attempts),
        "open_mistakes": sum(1 for mistake in mistakes if not mistake.reviewed),
        "partner_sessions": len(sessions),
        "partner_events": len(events),
        "safety_blocks": sum(1 for event in events if event.source == "safety_blocked"),
        "principle": "晋级必须看证据：训练提交、错题复习、AI 伴侣状态轨迹和安全边界记录共同构成掌握证明。",
    }
