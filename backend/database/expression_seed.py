"""Seed and query helpers for the expression toolbox."""
from __future__ import annotations

import json
from datetime import datetime
from typing import Any

from sqlmodel import Session, select

from backend.models.expression import ExpressionTool, ExpressionToolChain

TOOL_LAYER_LABELS = {
    "logic": "核心逻辑层",
    "ammo": "内容弹药层",
    "structure": "结构设计层",
    "nonverbal": "非语言工具层",
    "emotion": "情绪调节层",
    "relationship": "关系管理层",
}

SCENE_LIBRARY = ["初识", "暧昧", "热恋", "冲突", "修复", "长期", "分歧", "公开场合"]
GOAL_LIBRARY = ["说清事实", "命名感受", "确认边界", "降低防御", "提出请求", "修复信任", "引导深聊", "保留退路"]

BASE_TOOL_SPECS: list[dict[str, Any]] = [
    *[
        {"name": "金字塔原理", "layer": "logic", "category": "逻辑框架", "formula": "结论 -> 理由 -> 证据", "risk": "忽视情绪"},
        {"name": "SCQA模型", "layer": "logic", "category": "逻辑框架", "formula": "情境 -> 冲突 -> 问题 -> 答案", "risk": "铺垫过长"},
        {"name": "PREP模型", "layer": "logic", "category": "逻辑框架", "formula": "观点 -> 理由 -> 例子 -> 重申", "risk": "显得说教"},
        {"name": "ORID聚焦法", "layer": "logic", "category": "复盘框架", "formula": "事实 -> 感受 -> 意义 -> 行动", "risk": "像访谈审问"},
        {"name": "FFC模型", "layer": "logic", "category": "感受表达", "formula": "感受 -> 事实 -> 比较", "risk": "比较失真"},
        {"name": "STAR结构", "layer": "logic", "category": "叙事框架", "formula": "情境 -> 任务 -> 行动 -> 结果", "risk": "过度汇报"},
        {"name": "MECE拆分", "layer": "logic", "category": "分析框架", "formula": "不重叠 -> 不遗漏", "risk": "过度理性"},
        {"name": "黄金圈", "layer": "logic", "category": "动机表达", "formula": "Why -> How -> What", "risk": "价值观压迫"},
        {"name": "利弊对比", "layer": "logic", "category": "决策框架", "formula": "收益 -> 代价 -> 权衡 -> 建议", "risk": "像算账"},
        {"name": "问题树", "layer": "logic", "category": "澄清框架", "formula": "主问题 -> 子问题 -> 最小行动", "risk": "拆太碎"},
    ],
    *[
        {"name": "场景化表达", "layer": "ammo", "category": "画面表达", "formula": "画面 -> 情绪 -> 轻行动", "risk": "戏剧化"},
        {"name": "数据实证", "layer": "ammo", "category": "证据表达", "formula": "数字 -> 解释 -> 限制", "risk": "压人"},
        {"name": "权威引用", "layer": "ammo", "category": "背书表达", "formula": "来源 -> 观点 -> 本场景边界", "risk": "借权威压制"},
        {"name": "故事叙述", "layer": "ammo", "category": "沉浸表达", "formula": "起 -> 承 -> 转 -> 合", "risk": "跑题"},
        {"name": "类比隐喻", "layer": "ammo", "category": "理解桥梁", "formula": "熟悉物 -> 相似点 -> 限制", "risk": "误导"},
        {"name": "幽默自嘲", "layer": "ammo", "category": "低压幽默", "formula": "自我降压 -> 不贬低对方", "risk": "逃避责任"},
        {"name": "轻调侃", "layer": "ammo", "category": "暧昧张力", "formula": "观察 -> 玩笑 -> 退路", "risk": "越界"},
        {"name": "设问反问", "layer": "ammo", "category": "思考触发", "formula": "问题 -> 留白 -> 回到对方", "risk": "咄咄逼人"},
        {"name": "留白沉默", "layer": "ammo", "category": "节奏工具", "formula": "关键句 -> 停顿 -> 观察", "risk": "冷处理"},
        {"name": "对比表达", "layer": "ammo", "category": "差异呈现", "formula": "过去 -> 现在 -> 想要", "risk": "翻旧账"},
    ],
    *[
        {"name": "时间轴结构", "layer": "structure", "category": "顺序设计", "formula": "过去 -> 现在 -> 未来", "risk": "旧事堆叠"},
        {"name": "空间轴结构", "layer": "structure", "category": "顺序设计", "formula": "我 -> 你 -> 我们", "risk": "边界混乱"},
        {"name": "问题解决结构", "layer": "structure", "category": "行动设计", "formula": "问题 -> 原因 -> 方案 -> 下一步", "risk": "急于解决"},
        {"name": "递进说服", "layer": "structure", "category": "请求设计", "formula": "共识 -> 小同意 -> 大请求", "risk": "操控感"},
        {"name": "悬念倒置", "layer": "structure", "category": "注意力设计", "formula": "反常结果 -> 原因 -> 启示", "risk": "卖关子"},
        {"name": "复盘结构", "layer": "structure", "category": "复盘设计", "formula": "发生了什么 -> 我学到什么 -> 下次怎么做", "risk": "自责循环"},
        {"name": "请求结构", "layer": "structure", "category": "边界请求", "formula": "事实 -> 影响 -> 请求 -> 可拒绝", "risk": "隐藏命令"},
        {"name": "反馈结构", "layer": "structure", "category": "反馈设计", "formula": "具体行为 -> 影响 -> 期待", "risk": "评价人格"},
        {"name": "道歉结构", "layer": "structure", "category": "修复设计", "formula": "承认影响 -> 少解释 -> 补偿行动", "risk": "求立刻原谅"},
        {"name": "拒绝结构", "layer": "structure", "category": "拒绝设计", "formula": "感谢 -> 边界 -> 可选替代", "risk": "模糊拖延"},
    ],
    *[
        {"name": "音量控制", "layer": "nonverbal", "category": "声音工具", "formula": "降低音量 -> 降低压迫", "risk": "听不清"},
        {"name": "语速控制", "layer": "nonverbal", "category": "声音工具", "formula": "放慢 -> 重复关键句", "risk": "显得端着"},
        {"name": "音调变化", "layer": "nonverbal", "category": "声音工具", "formula": "柔和起句 -> 稳定收束", "risk": "表演感"},
        {"name": "停顿", "layer": "nonverbal", "category": "节奏工具", "formula": "说完关键句 -> 停 2 秒", "risk": "施压沉默"},
        {"name": "眼神注视", "layer": "nonverbal", "category": "注意工具", "formula": "短注视 -> 移开 -> 回看", "risk": "凝视压迫"},
        {"name": "手势标记", "layer": "nonverbal", "category": "可视化工具", "formula": "一点一手势", "risk": "动作过多"},
        {"name": "开放姿态", "layer": "nonverbal", "category": "安全感工具", "formula": "手心开放 -> 身体放松", "risk": "不真诚"},
        {"name": "距离调节", "layer": "nonverbal", "category": "边界工具", "formula": "先保持距离 -> 获得同意再靠近", "risk": "误判亲密"},
        {"name": "道具辅助", "layer": "nonverbal", "category": "注意工具", "formula": "写下关键词 -> 共看", "risk": "转移情绪"},
        {"name": "环境选择", "layer": "nonverbal", "category": "场域工具", "formula": "低噪声 -> 可退出 -> 不围堵", "risk": "制造压力"},
    ],
    *[
        {"name": "情绪标注", "layer": "emotion", "category": "情绪承接", "formula": "听起来你有点...因为...", "risk": "贴标签"},
        {"name": "共情反射", "layer": "emotion", "category": "情绪承接", "formula": "复述感受 -> 复述原因", "risk": "复读机"},
        {"name": "换框重塑", "layer": "emotion", "category": "认知调整", "formula": "另一种解释 -> 轻验证", "risk": "否定感受"},
        {"name": "暂停协议", "layer": "emotion", "category": "冲突降温", "formula": "暂停时间 -> 回来时间 -> 议题保留", "risk": "逃避"},
        {"name": "降温命名", "layer": "emotion", "category": "冲突降温", "formula": "先命名升级 -> 降速", "risk": "居高临下"},
        {"name": "积极重构", "layer": "emotion", "category": "支持工具", "formula": "努力 -> 价值 -> 下一步", "risk": "鸡汤化"},
        {"name": "情绪对比", "layer": "emotion", "category": "选择澄清", "formula": "继续这样 -> 换一种做法", "risk": "二选一逼迫"},
        {"name": "身体觉察", "layer": "emotion", "category": "自我调节", "formula": "身体信号 -> 放慢 -> 再回应", "risk": "脱离对话"},
        {"name": "镜像回应", "layer": "emotion", "category": "同步工具", "formula": "匹配节奏 -> 轻微降速", "risk": "模仿感"},
        {"name": "承接再转向", "layer": "emotion", "category": "转向工具", "formula": "先接住 -> 再谈行动", "risk": "转太快"},
    ],
    *[
        {"name": "三明治反馈", "layer": "relationship", "category": "反馈工具", "formula": "肯定 -> 改进 -> 信任", "risk": "套路感"},
        {"name": "承诺一致", "layer": "relationship", "category": "行动工具", "formula": "对方目标 -> 对方下一步", "risk": "诱导承诺"},
        {"name": "互惠开口", "layer": "relationship", "category": "请求工具", "formula": "先提供价值 -> 再请求", "risk": "交易感"},
        {"name": "自我揭露", "layer": "relationship", "category": "亲近工具", "formula": "小真实 -> 邀请而非索取", "risk": "过度暴露"},
        {"name": "未来挂钩", "layer": "relationship", "category": "拒绝工具", "formula": "这次拒绝 -> 未来可能", "risk": "虚假希望"},
        {"name": "边界声明", "layer": "relationship", "category": "边界工具", "formula": "我可以 -> 我不可以 -> 替代", "risk": "冷硬"},
        {"name": "修复请求", "layer": "relationship", "category": "修复工具", "formula": "我想修复 -> 你可以拒绝 -> 下一小步", "risk": "求和施压"},
        {"name": "感谢具体化", "layer": "relationship", "category": "连接工具", "formula": "具体行为 -> 对我影响", "risk": "夸大"},
        {"name": "偏好校准", "layer": "relationship", "category": "长期工具", "formula": "我偏好 -> 你偏好 -> 共同约定", "risk": "控制日程"},
        {"name": "共同约定", "layer": "relationship", "category": "长期工具", "formula": "规则 -> 触发条件 -> 复盘时间", "risk": "过度制度化"},
    ],
]


def seed_expression_tools(session: Session) -> dict[str, Any]:
    """Idempotently seed the 60 foundational expression tools and base chains."""
    created = 0
    updated = 0
    for index, spec in enumerate(BASE_TOOL_SPECS, start=1):
        tool_uuid = f"expr_tool_{index:03d}"
        existing = session.exec(select(ExpressionTool).where(ExpressionTool.tool_uuid == tool_uuid)).first()
        payload = _tool_payload(tool_uuid, spec, index)
        if existing:
            _apply_tool_payload(existing, payload)
            updated += 1
        else:
            session.add(ExpressionTool(**payload))
            created += 1
    session.flush()
    chain_result = _seed_base_chains(session)
    session.commit()
    return {
        "created": created,
        "updated": updated,
        "total_tools": _count_tools(session),
        "chains": chain_result,
        "principle": "表达工具箱以 SQLite 为主真源；种子可重复执行，保留工具来源、风险和示例供训练调用。",
    }


def _tool_payload(tool_uuid: str, spec: dict[str, Any], index: int) -> dict[str, Any]:
    name = str(spec["name"])
    layer = str(spec["layer"])
    scenes = _scenes_for_tool(name, layer)
    goals = _goals_for_tool(name, layer)
    return {
        "tool_uuid": tool_uuid,
        "name": name,
        "layer": layer,
        "category": str(spec["category"]),
        "formula": str(spec["formula"]),
        "description": f"{name}用于{TOOL_LAYER_LABELS[layer]}，帮助用户在{scenes[0]}等场景中完成{goals[0]}，并保留边界与退路。",
        "best_scenes_json": _dumps(scenes),
        "relationship_fit_json": _dumps(scenes[:4]),
        "emotion_fit_json": _dumps(["平静", "紧张", "委屈", "犹豫"] if layer in {"emotion", "relationship"} else ["需要清晰", "信息复杂"]),
        "risk_flags_json": _dumps([str(spec["risk"]), "不得施压、诱导或替对方做决定"]),
        "micro_steps_json": _dumps(_micro_steps(name, layer)),
        "example_before": "你别这样，我也不知道该怎么说。",
        "example_after": _example_after(name, layer),
        "mastery_stage": "operation" if index <= 20 else "recognition",
        "source": "project_expression_toolbox",
        "source_url": "local_anchor:表达工具箱贯通架构方案",
        "review_status": "published",
        "quality_score": 88 + (index % 10),
        "updated_at": datetime.now(),
    }


def _apply_tool_payload(tool: ExpressionTool, payload: dict[str, Any]) -> None:
    for key, value in payload.items():
        setattr(tool, key, value)


def _seed_base_chains(session: Session) -> dict[str, int]:
    chains = [
        ("失望修复三步链", "修复信任", "修复", ["情绪标注", "道歉结构", "具体补偿"]),
        ("边界确认低压链", "确认边界", "暧昧", ["请求结构", "边界声明", "留白沉默"]),
        ("冲突降温复盘链", "降低防御", "冲突", ["暂停协议", "ORID聚焦法", "承接再转向"]),
        ("初识深聊推进链", "引导深聊", "初识", ["FFC模型", "自我揭露", "保留退路"]),
        ("长期协商约定链", "提出请求", "长期", ["问题解决结构", "偏好校准", "共同约定"]),
    ]
    tool_by_name = {tool.name: tool for tool in session.exec(select(ExpressionTool)).all()}
    created = 0
    updated = 0
    for index, (name, goal, scene, tool_names) in enumerate(chains, start=1):
        chain_uuid = f"expr_chain_{index:03d}"
        tool_ids = [tool_by_name[item].tool_uuid for item in tool_names if item in tool_by_name]
        payload = {
            "chain_uuid": chain_uuid,
            "name": name,
            "goal": goal,
            "scene": scene,
            "stage": "D3 改写",
            "tool_ids_json": _dumps(tool_ids),
            "sequence_json": _dumps([{"order": i + 1, "tool": tool_name} for i, tool_name in enumerate(tool_names)]),
            "forbidden_tools_json": _dumps(["反问逼迫", "自我辩解", "冷处理"]),
            "example_dialogue_json": _dumps({"before": "你别这样。", "after": "我听见你有点失望，我先承担影响，再给一个具体补偿。"}),
            "review_status": "published",
            "quality_score": 92 + index,
            "updated_at": datetime.now(),
        }
        existing = session.exec(select(ExpressionToolChain).where(ExpressionToolChain.chain_uuid == chain_uuid)).first()
        if existing:
            for key, value in payload.items():
                setattr(existing, key, value)
            updated += 1
        else:
            session.add(ExpressionToolChain(**payload))
            created += 1
    return {"created": created, "updated": updated, "total": _count_chains(session)}


def _scenes_for_tool(name: str, layer: str) -> list[str]:
    if layer == "emotion":
        return ["冲突", "修复", "失望表达", "压力支持"]
    if layer == "relationship":
        return ["长期", "修复", "边界确认", "价值观分歧"]
    if "暧昧" in name or "调侃" in name:
        return ["暧昧", "初识", "约会邀约", "公开场合"]
    if layer == "nonverbal":
        return ["初识", "冲突", "公开场合", "亲密推进"]
    return SCENE_LIBRARY[:4]


def _goals_for_tool(name: str, layer: str) -> list[str]:
    if layer == "emotion":
        return ["命名感受", "降低防御", "修复信任"]
    if layer == "relationship":
        return ["保留退路", "确认边界", "修复信任"]
    if "请求" in name or "边界" in name:
        return ["提出请求", "确认边界", "保留退路"]
    return GOAL_LIBRARY[:3]


def _micro_steps(name: str, layer: str) -> list[str]:
    if layer == "emotion":
        return ["先慢半拍", "命名一个可能情绪", "用轻问句校准", "给对方退路"]
    if layer == "relationship":
        return ["先说明善意", "说清自己的边界或请求", "确认对方选择", "约定下一小步"]
    if layer == "nonverbal":
        return ["观察对方状态", "降低压迫感", "只强化一个关键信号", "保留可退出空间"]
    return ["先给结构", "补一个具体事实", "说出影响", "收束成下一步"]


def _example_after(name: str, layer: str) -> str:
    if layer == "emotion":
        return f"我先不急着解释。用{name}看，我猜你刚才有点失望；如果我猜错了你可以纠正我。"
    if layer == "relationship":
        return f"我想把连接保住，也把边界说清楚。用{name}说：这件事我愿意继续聊，但今晚我需要先缓一缓。"
    if layer == "nonverbal":
        return f"我会先放慢语速、停一下，再说：这句话我想认真说，不是逼你马上回答。这里用的是{name}。"
    return f"我想说清楚一点。用{name}整理：事实是刚才临时改变安排，影响是你可能没被优先考虑，下一步我补一个确定时间。"


def _count_tools(session: Session) -> int:
    return len(session.exec(select(ExpressionTool.id)).all())


def _count_chains(session: Session) -> int:
    return len(session.exec(select(ExpressionToolChain.id)).all())


def _dumps(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False)
