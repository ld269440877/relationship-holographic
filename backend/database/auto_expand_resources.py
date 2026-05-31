"""自动派生资源库内容。

该脚本只生成本项目原创训练资源，不抓取或保存第三方全文。公开来源只作为
source_url 透明锚点，帮助用户跳到原始信息渠道继续阅读。
"""

from __future__ import annotations

import argparse
import json
import uuid
from collections.abc import Iterable
from dataclasses import dataclass
from datetime import datetime
from itertools import zip_longest

from sqlmodel import Session, func, select

from backend.database.connection import create_db_and_tables, engine
from backend.models.resource import ResourceLibrary

TARGET_DEFAULT = 10000
SOURCE = "synthetic:auto_expand_resources:v1"
SYNTHETIC_URL = "synthetic://relationship-training/resource-expander/v1"


@dataclass(frozen=True)
class ResourceBlueprint:
    resource_type: str
    category: str
    scene: str
    difficulty: int
    attachment: str
    tone: str
    title: str
    content: str
    usage_tip: str
    tags: tuple[str, ...]
    source_name: str = SOURCE
    source_url: str = SYNTHETIC_URL


SCENES = ("初识", "暧昧", "热恋", "冲突", "平淡", "修复", "复联", "异地", "承诺", "分歧")
ATTACHMENTS = ("安全型", "焦虑型", "回避型", "恐惧-回避型", "通用")
TONES = ("轻松", "温柔", "坦诚", "幽默", "克制", "坚定", "好奇", "修复", "暧昧", "亲密", "自嘲", "热烈")

RESOURCE_PATTERNS = [
    (
        "flirty",
        "情绪流动话术",
        "{scene}里的轻张力回应",
        "我听见你话里有一点{tone}，也有一点试探。我们可以慢慢靠近，不急着把答案说死。",
        "用于承接暧昧或靠近信号，重点是让对方感觉被看见，同时保留退路。",
        ("情绪流动", "暧昧识别", "退路表达"),
    ),
    (
        "story",
        "关系微故事",
        "{scene}场景的三秒停顿",
        "对方说完后没有马上追问，只是把杯子推近一点：'我在听，你可以说完整一点。' 这一秒，紧绷从对抗变成了可对话。",
        "适合训练把动作、沉默和一句轻回应组合起来观察。",
        ("微动作", "关系叙事", "场景感"),
    ),
    (
        "phrase",
        "边界确认句",
        "{scene}里的同意确认",
        "我想靠近一点，但我也想确认这对你是舒服的。如果你想慢一点，我会尊重。",
        "用于成人亲密或情绪推进前，明确同意、节奏和可退出空间。",
        ("边界", "同意", "成人关系"),
    ),
    (
        "game",
        "关系练习",
        "{scene}信号三选一",
        "把对方这句话拆成三个可能信号：想靠近、想确认、想保护自己。先选一个最轻的假设，再问一句验证问题。",
        "用于训练不把猜测当事实，避免过度解读。",
        ("5W2H", "轻验证", "训练任务"),
    ),
    (
        "joke",
        "轻幽默",
        "{scene}里的低压幽默",
        "你这句话让我有点想认真回答，又有点想假装自己很淡定。那我先认真一半：我确实在意。",
        "只在气氛安全、对方没有明显受伤时使用，避免用幽默逃避情绪。",
        ("幽默", "低压力", "气氛修复"),
    ),
    (
        "media",
        "知识卡片",
        "{scene}关系动力观察卡",
        "观察顺序：事实发生了什么；情绪正在往哪里流；谁在靠近或后退；边界是否清楚；下一句怎样既真实又不施压。",
        "用于资源页知识化阅读，也可转成训练前提示。",
        ("知识卡片", "观察框架", "关系动力"),
    ),
]

PUBLIC_SOURCE_ANCHORS = [
    {
        "name": "Gottman Institute",
        "url": "https://www.gottman.com/blog/",
        "themes": ("冲突修复", "情绪承接", "长期关系", "信任维护"),
        "scenes": ("冲突", "修复", "承诺", "平淡"),
    },
    {
        "name": "Gottman Research",
        "url": "https://www.gottman.com/about/research/",
        "themes": ("关系观察", "互动模式", "稳定关系", "负面循环识别"),
        "scenes": ("热恋", "冲突", "平淡", "承诺"),
    },
    {
        "name": "CNVC Feelings Inventory",
        "url": "https://www.capitalnvc.org/feelings-inventory",
        "themes": ("情绪词汇", "感受命名", "内在体验", "情绪流动"),
        "scenes": ("初识", "暧昧", "冲突", "修复"),
    },
    {
        "name": "CNVC Needs Inventory",
        "url": "https://www.capitalnvc.org/needs-inventory",
        "themes": ("需求识别", "非暴力沟通", "请求表达", "边界协商"),
        "scenes": ("冲突", "修复", "分歧", "承诺"),
    },
    {
        "name": "Greater Good Science Center",
        "url": "https://greatergood.berkeley.edu/topic/relationships",
        "themes": ("共情", "亲密关系", "善意沟通", "连接感"),
        "scenes": ("初识", "热恋", "平淡", "修复"),
    },
    {
        "name": "APA Relationships",
        "url": "https://www.apa.org/topics/marriage-relationships",
        "themes": ("健康关系", "沟通习惯", "压力管理", "关系维护"),
        "scenes": ("热恋", "冲突", "平淡", "承诺"),
    },
    {
        "name": "HelpGuide Effective Communication",
        "url": "https://www.helpguide.org/relationships/social-connection/effective-communication",
        "themes": ("有效沟通", "倾听", "非语言信号", "冲突降温"),
        "scenes": ("初识", "冲突", "修复", "分歧"),
    },
    {
        "name": "HelpGuide Conflict Resolution",
        "url": "https://www.helpguide.org/relationships/communication/conflict-resolution-skills",
        "themes": ("冲突解决", "情绪调节", "共同问题", "修复尝试"),
        "scenes": ("冲突", "修复", "分歧", "承诺"),
    },
    {
        "name": "Harvard Study of Adult Development",
        "url": "https://www.adultdevelopmentstudy.org/",
        "themes": ("长期幸福", "关系质量", "陪伴", "人生发展"),
        "scenes": ("平淡", "承诺", "修复", "异地"),
    },
    {
        "name": "Nonviolent Communication",
        "url": "https://www.nonviolentcommunication.com/learn-nonviolent-communication/4-part-nvc/",
        "themes": ("观察感受需求请求", "表达结构", "减少指责", "协商"),
        "scenes": ("冲突", "修复", "分歧", "承诺"),
    },
    {
        "name": "Kinsey Institute",
        "url": "https://kinseyinstitute.org/",
        "themes": ("亲密研究", "成人关系", "性健康", "身心因素"),
        "scenes": ("热恋", "承诺", "分歧", "修复"),
    },
    {
        "name": "Kinsey Confidential",
        "url": "https://kinseyconfidential.org/",
        "themes": ("性教育科普", "亲密问题", "身体边界", "健康沟通"),
        "scenes": ("暧昧", "热恋", "承诺", "分歧"),
    },
    {
        "name": "Kinsey Reporter",
        "url": "http://kinseyreporter.org/",
        "themes": ("众包数据", "亲密行为", "匿名报告", "数据可视化"),
        "scenes": ("初识", "暧昧", "热恋", "承诺"),
    },
    {
        "name": "Love Matters China",
        "url": "https://lovematters.cn/",
        "themes": ("中文性教育", "亲密科普", "关系边界", "身体自主"),
        "scenes": ("初识", "暧昧", "热恋", "分歧"),
    },
    {
        "name": "Guokr",
        "url": "https://www.guokr.com/",
        "themes": ("泛科技科普", "性健康", "亲密知识", "反迷思"),
        "scenes": ("初识", "暧昧", "热恋", "平淡"),
    },
    {
        "name": "Kaohsiung Medical University LIR",
        "url": "https://lir.kmu.edu.tw/",
        "themes": ("情爱困境", "性别视角", "关系教育", "法律社会视角"),
        "scenes": ("冲突", "分歧", "修复", "承诺"),
    },
    {
        "name": "Berkeley Gender and Women's Studies",
        "url": "https://womensstudies.berkeley.edu/",
        "themes": ("性别研究", "权力结构", "亲密伦理", "社会文化"),
        "scenes": ("分歧", "承诺", "冲突", "修复"),
    },
    {
        "name": "CDC National Survey of Family Growth",
        "url": "https://www.cdc.gov/nchs/nsfg/",
        "themes": ("家庭成长数据", "婚育史", "性健康统计", "人口研究"),
        "scenes": ("承诺", "平淡", "分歧", "修复"),
    },
    {
        "name": "WHO Sexual and Reproductive Health",
        "url": "https://www.who.int/health-topics/sexual-health",
        "themes": ("性健康", "生殖健康", "健康指南", "公共卫生"),
        "scenes": ("热恋", "承诺", "分歧", "修复"),
    },
    {
        "name": "UK Office for National Statistics",
        "url": "https://www.ons.gov.uk/",
        "themes": ("官方统计", "婚姻家庭", "人口结构", "性取向数据"),
        "scenes": ("承诺", "平淡", "分歧", "修复"),
    },
    {
        "name": "Youth Risk Behavior Survey",
        "url": "https://www.cdc.gov/yrbs/",
        "themes": ("青年健康", "风险行为", "性教育", "群体趋势"),
        "scenes": ("初识", "暧昧", "分歧", "修复"),
    },
    {
        "name": "Zenodo GLAD",
        "url": "https://zenodo.org/",
        "themes": ("开放数据", "家庭结构", "居住安排", "婚姻状态"),
        "scenes": ("承诺", "平淡", "分歧", "异地"),
    },
    {
        "name": "TalkingData",
        "url": "https://mi.talkingdata.com/",
        "themes": ("行业数据", "社交应用", "用户画像", "婚恋社交"),
        "scenes": ("初识", "暧昧", "复联", "异地"),
    },
    {
        "name": "Chinaooc Intimate Relationship Course",
        "url": "https://www.chinaooc.com.cn/",
        "themes": ("亲密关系课程", "恋爱观", "边界教育", "失恋应对"),
        "scenes": ("初识", "暧昧", "冲突", "修复"),
    },
    {
        "name": "Zhihuishu Intimate Relationship Course",
        "url": "https://coursehome.zhihuishu.com/",
        "themes": ("吸引力", "友谊爱情", "沟通认知", "婚恋观"),
        "scenes": ("初识", "暧昧", "热恋", "承诺"),
    },
    {
        "name": "Dibble Institute",
        "url": "https://dibbleinstitute.org/",
        "themes": ("关系教育", "青少年课程", "健康关系", "沟通训练"),
        "scenes": ("初识", "暧昧", "冲突", "修复"),
    },
    {
        "name": "UGA ELEVATE",
        "url": "https://www.fcs.uga.edu/extension/elevate-couples-georgia",
        "themes": ("伴侣教育", "冲突管理", "压力应对", "家庭沟通"),
        "scenes": ("冲突", "修复", "承诺", "平淡"),
    },
    {
        "name": "MotherWise",
        "url": "https://www.motherwise.org/",
        "themes": ("家庭关系", "孕产支持", "压力缓冲", "健康伴侣"),
        "scenes": ("承诺", "分歧", "修复", "平淡"),
    },
    {
        "name": "Genderless Book Club RSS",
        "url": "https://feeds.fireside.fm/genderless/rss",
        "themes": ("播客学习", "女性主义", "关系文化", "声音资源"),
        "scenes": ("初识", "分歧", "平淡", "修复"),
    },
]

MISSION_PUBLIC_SOURCE_NAMES = {
    "Gottman Institute",
    "Gottman Research",
    "CNVC Feelings Inventory",
    "CNVC Needs Inventory",
    "Greater Good Science Center",
    "APA Relationships",
    "HelpGuide Effective Communication",
    "HelpGuide Conflict Resolution",
    "Harvard Study of Adult Development",
    "Nonviolent Communication",
    "Kinsey Institute",
    "Kinsey Confidential",
    "Love Matters China",
    "Chinaooc Intimate Relationship Course",
    "Zhihuishu Intimate Relationship Course",
    "Dibble Institute",
}

MISSION_CORE_AXES = (
    "微关系信号",
    "情绪流动",
    "边界与同意",
    "暧昧张力",
    "冲突修复",
    "长期连接",
    "幽默互动",
    "错题改写",
)

CONVERSATION_RESOURCE_SEEDS = [
    {
        "source": "local_anchor:深度聊天话题库",
        "url": "synthetic://relationship-training/deep-conversation-topics",
        "themes": ("童年回忆", "关系期待", "价值观试探", "未来想象", "亲密边界", "生活节奏", "信任证据", "脆弱表达"),
        "scenes": ("初识", "暧昧", "热恋", "平淡", "承诺"),
        "kind": "game",
    },
    {
        "source": "local_anchor:情绪流动故事库",
        "url": "synthetic://relationship-training/emotion-flow-stories",
        "themes": ("初遇心动", "日常温柔", "裂痕和解", "失去成长", "激情亲密", "复联试探", "异地牵挂", "长期陪伴"),
        "scenes": ("初识", "暧昧", "热恋", "冲突", "修复", "复联", "异地", "平淡"),
        "kind": "story",
    },
    {
        "source": "local_anchor:成人暧昧语言游戏库",
        "url": "synthetic://relationship-training/adult-flirty-language-games",
        "themes": ("双关幽默", "低压调情", "睡前暧昧", "远距离牵挂", "亲密确认", "坏笑提问", "自嘲暖场", "挑战回应"),
        "scenes": ("初识", "暧昧", "热恋", "异地", "承诺"),
        "kind": "joke",
    },
    {
        "source": "local_anchor:从之前到之后对话诊断库",
        "url": "synthetic://relationship-training/before-after-dialogue-diagnosis",
        "themes": ("加班报备转行动", "接纳沉默", "梦想支持", "冲突降温", "冷淡复联", "失望修复", "边界协商", "承诺澄清"),
        "scenes": ("冲突", "修复", "平淡", "复联", "分歧", "承诺"),
        "kind": "flirty",
    },
]

CONCRETE_SCENARIO_CASES = [
    {
        "axis": ("game", "story", "flirty"),
        "theme": "晚回消息后的轻确认",
        "scene": "暧昧",
        "situation": "晚上十点半，对方隔了四小时回你：刚忙完，脑子有点空。",
        "their_words": "刚忙完，今天有点累。",
        "mistake": "你是不是不想理我？那算了。",
        "better": "辛苦了。你现在更想安静一下，还是让我陪你聊两句轻的？我不催你回。",
        "signal": "疲惫里带着报备，可能是在保留连接，也可能是在请求低压力空间。",
        "boundary": "不把晚回等同于冷淡，先给对方选择沉默或继续的权利。",
        "practice": "把追问改成一个二选一的轻确认，并允许对方明天再回。",
        "tags": ("晚回消息", "低压力陪伴", "暧昧确认"),
    },
    {
        "axis": ("flirty", "joke", "game"),
        "theme": "第一次约会迟到十分钟",
        "scene": "初识",
        "situation": "第一次线下见面，对方一路小跑进咖啡店，额头有汗，语速变快。",
        "their_words": "对不起，我迟到了十分钟，你等很久了吗？",
        "mistake": "我最讨厌不守时的人。",
        "better": "我有一点点等你，但看到你跑过来又觉得这十分钟有画面了。先坐下喘口气？下次你请我选座位。",
        "signal": "对方在道歉，也在观察你会不会把小失误升级成审判。",
        "boundary": "可以表达守时期待，但不借题羞辱；把规则留到轻松时刻说清楚。",
        "practice": "写一句既承认自己等待、又能让对方放松的回应。",
        "tags": ("初次约会", "低压幽默", "规则表达"),
    },
    {
        "axis": ("story", "flirty", "phrase"),
        "theme": "关系定义的温柔试探",
        "scene": "暧昧",
        "situation": "散步到路口，对方突然慢下来，没看你，踢了一下路边的小石子。",
        "their_words": "所以我们现在到底算什么关系啊？",
        "mistake": "你想太多了，顺其自然呗。",
        "better": "我不想用模糊感吊着你。我喜欢现在的靠近，也愿意认真了解你；如果你需要更清楚的节奏，我们可以今晚说透一点。",
        "signal": "表面问身份，底层是在要安全感、可预期和不被消耗的承诺边界。",
        "boundary": "不能用暧昧逃避责任，也不要被迫立刻承诺超出真实程度的关系。",
        "practice": "把“顺其自然”改写成包含真实程度、下一步和可协商边界的三句。",
        "tags": ("关系定义", "安全感", "承诺澄清"),
    },
    {
        "axis": ("flirty", "joke"),
        "theme": "坏笑提问后的退路",
        "scene": "热恋",
        "situation": "睡前语音里，对方故意压低声音，问了一个带双关的问题，然后自己先笑了。",
        "their_words": "你刚刚是不是想歪了？",
        "mistake": "你别装了，你就是那个意思。",
        "better": "我承认我脑子跑偏了一秒，但我也会乖乖停在你觉得舒服的位置。你想继续逗我，还是换个纯洁一点的话题？",
        "signal": "对方在制造暧昧张力，也在测试你是否懂得停在安全距离。",
        "boundary": "成人暧昧要保留退出按钮，不能把玩笑变成逼迫或羞辱。",
        "practice": "写一句带玩味、带同意确认、带可退出选择的回应。",
        "tags": ("成人暧昧", "双关幽默", "同意确认"),
    },
    {
        "axis": ("story", "game"),
        "theme": "异地凌晨的低电量连接",
        "scene": "异地",
        "situation": "凌晨一点半，对方发来一张加班路上的空街照片，只配了三个字：回去了。",
        "their_words": "回去了。",
        "mistake": "你怎么又这么晚？不是说早点睡吗？",
        "better": "看到这条街我有点心疼你。到家给我一个句号就好，今晚不复盘，明天我再听你讲。",
        "signal": "极简报备不是冷淡，可能是把最后一点能量留给你。",
        "boundary": "关心不变成审问；先守住安全到家，再安排后续沟通。",
        "practice": "把控制式关心改成“安全确认 + 延后复盘”的一句话。",
        "tags": ("异地", "低电量沟通", "安全确认"),
    },
    {
        "axis": ("flirty", "story", "game"),
        "theme": "争吵后三天的复联",
        "scene": "复联",
        "situation": "冷战第三天，对方在朋友圈发了一首你们都听过的歌，没有私聊你。",
        "their_words": "（朋友圈）这首还是好听。",
        "mistake": "你有话就直说，别阴阳怪气。",
        "better": "我看见那首歌了，也想起那天我们没说完的话。如果你愿意，我今晚只先听十分钟，不急着争输赢。",
        "signal": "间接信号可能是在试水，核心是既想靠近又怕再次受伤。",
        "boundary": "不把朋友圈当证据审判；复联要给低门槛、短时长和不争输赢的约定。",
        "practice": "设计一条不翻旧账、能开启十分钟修复窗口的消息。",
        "tags": ("复联", "冷战修复", "间接信号"),
    },
    {
        "axis": ("game", "phrase"),
        "theme": "亲密推进前的明确确认",
        "scene": "热恋",
        "situation": "两个人靠得很近，气氛升温，但对方突然安静，眼神从你身上移开。",
        "their_words": "我不是不喜欢你，就是有点紧张。",
        "mistake": "都这样了你还紧张什么？",
        "better": "谢谢你直接说。我们可以慢下来，停在拥抱也很好；你不用证明什么，我更在意你舒服。",
        "signal": "喜欢和紧张可以同时存在，沉默可能是需要确认节奏。",
        "boundary": "任何亲密推进都要以清晰同意和可随时停止为前提。",
        "practice": "写一句让对方不用解释、也不用迎合的降速回应。",
        "tags": ("边界与同意", "亲密节奏", "成人关系"),
    },
    {
        "axis": ("story", "flirty"),
        "theme": "礼物没被喜欢时的修复",
        "scene": "平淡",
        "situation": "纪念日你准备了礼物，对方拆开后笑了一下，但很快放回盒子。",
        "their_words": "谢谢你，我知道你花心思了。",
        "mistake": "你就是不喜欢，我以后不送了。",
        "better": "我听出来你在照顾我的心情，也可能不是最合你。你愿意告诉我哪一类更贴近你吗？我想学会送到你心里。",
        "signal": "礼貌感谢背后可能有失落，也可能是在避免伤害你。",
        "boundary": "不把对方不喜欢礼物解读成否定自己；允许真实反馈。",
        "practice": "把防御式受伤改成一次偏好校准。",
        "tags": ("长期连接", "偏好校准", "礼物修复"),
    },
    {
        "axis": ("game", "story"),
        "theme": "朋友聚会里的被忽略感",
        "scene": "分歧",
        "situation": "聚会中你讲了两次话都被岔开，对方一直和朋友聊工作梗。",
        "their_words": "你刚才怎么突然不说话了？",
        "mistake": "你现在才发现？你眼里根本没有我。",
        "better": "我刚才有点落单，尤其我说话被岔开的时候。不是要你只围着我转，但我需要你偶尔把我带回场子里。",
        "signal": "沉默不是作，可能是在社交场里失去位置感。",
        "boundary": "表达需要时只描述具体场景，不把一次忽略升级成人格否定。",
        "practice": "写出“事实 + 感受 + 具体请求”，不使用绝对化词。",
        "tags": ("社交场景", "被忽略感", "具体请求"),
    },
    {
        "axis": ("flirty", "joke"),
        "theme": "土味情话的高级收束",
        "scene": "初识",
        "situation": "聊天刚热起来，对方发来一句很土的情话，后面跟了一个捂脸表情。",
        "their_words": "你知道我最近为什么睡不好吗？因为脑子里总出现你。",
        "mistake": "哈哈好油。",
        "better": "油是有一点，但你敢发出来还挺可爱。奖励你一个不油的机会：说说今天最想让我知道的一件小事。",
        "signal": "尴尬表达里有靠近意图，也有怕被嫌弃的自我保护。",
        "boundary": "可以调侃表达方式，但不否定对方靠近的勇气。",
        "practice": "把吐槽改成“轻调侃 + 接住意图 + 打开新话题”。",
        "tags": ("土味情话", "幽默互动", "初识破冰"),
    },
    {
        "axis": ("story", "game", "phrase"),
        "theme": "失望后的重新约定",
        "scene": "修复",
        "situation": "你答应周末一起吃饭，却临时改了安排。对方没有吵，只回了一个“嗯”。",
        "their_words": "嗯，知道了。",
        "mistake": "你别这样，我也不是故意的。",
        "better": "这个“嗯”我听着有失望。是我临时改变让你没有被优先考虑。今晚我先不解释，先补一个确定的新时间：周六六点，可以吗？",
        "signal": "短回复可能是在压住委屈，不代表事情已经过去。",
        "boundary": "修复不是逼对方马上原谅，而是先承担影响并给出可靠行动。",
        "practice": "写一句包含影响承认、少解释、具体补偿时间的回应。",
        "tags": ("失望修复", "可靠行动", "承诺重建"),
    },
    {
        "axis": ("game", "story"),
        "theme": "价值观分歧不变辩论赛",
        "scene": "分歧",
        "situation": "你们聊到消费观。你重视体验，对方更重视储蓄，气氛开始发紧。",
        "their_words": "我不是舍不得花钱，我只是觉得未来要有底。",
        "mistake": "你就是太保守了，活得一点都不松弛。",
        "better": "我听到你在要确定感，不只是反对花钱。我们能不能分两层谈：哪些钱是安全底线，哪些钱是让生活有光的体验？",
        "signal": "分歧背后不是谁高级，而是安全感和生命感的优先级不同。",
        "boundary": "不嘲笑对方价值观；把对错争夺改成双层预算协商。",
        "practice": "把一个价值判断改成两个可协商的问题。",
        "tags": ("价值观", "长期连接", "协商"),
    },
    {
        "axis": ("flirty", "story"),
        "theme": "被夸后不逃跑",
        "scene": "暧昧",
        "situation": "对方认真看着你，说你刚才处理事情的样子很好看。",
        "their_words": "你刚刚那一下挺迷人的。",
        "mistake": "没有没有，你别乱夸。",
        "better": "这句我收下了，而且有点开心。你夸得这么认真，我会想再表现好一点。",
        "signal": "直接赞美是在递出靠近，也是在看你能不能承接正向情绪。",
        "boundary": "承接赞美不等于立刻升级亲密；可以表达开心并停在当下。",
        "practice": "写一句不否认、不转移、能让气氛继续升温的回应。",
        "tags": ("赞美承接", "暧昧张力", "正向情绪"),
    },
    {
        "axis": ("story", "game"),
        "theme": "对方说随便时的真实偏好",
        "scene": "平淡",
        "situation": "晚饭选择上，对方连续第三次说随便，但最后又对餐厅不太满意。",
        "their_words": "随便，你定就好。",
        "mistake": "每次都随便，选了又不满意。",
        "better": "我可以定，但我想少猜一点。你给我两个不要踩的雷区，我从剩下的里面选，怎么样？",
        "signal": "随便可能是省事，也可能是怕表达偏好带来冲突。",
        "boundary": "不强迫对方立刻给完整答案，先用排除法降低表达成本。",
        "practice": "把抱怨改成一个低成本偏好提取问题。",
        "tags": ("日常选择", "偏好表达", "低成本沟通"),
    },
    {
        "axis": ("flirty", "joke", "story"),
        "theme": "轻挑战里的互相靠近",
        "scene": "热恋",
        "situation": "对方发自拍问你今天好不好看，语气明显是在等你接梗。",
        "their_words": "今天这张能不能打八分？",
        "mistake": "十分享受你的自恋。",
        "better": "八分太保守了，扣一分是因为你明知道我会心软还来问。剩下九分，等见面补给你。",
        "signal": "这不是单纯求评价，而是在邀请你参与暧昧游戏。",
        "boundary": "轻挑战要让对方更有魅力感，不用贬低制造控制感。",
        "practice": "写一句带轻挑战、赞美和见面期待的回应。",
        "tags": ("自拍回应", "轻挑战", "热恋互动"),
    },
    {
        "axis": ("game", "phrase"),
        "theme": "不舒服玩笑的即时止损",
        "scene": "冲突",
        "situation": "朋友面前，对方拿你的一个敏感点开玩笑，大家笑了，你也跟着笑了一下。",
        "their_words": "你不会介意吧，我开玩笑的。",
        "mistake": "你有病吧，能不能闭嘴？",
        "better": "我知道你可能想活跃气氛，但这个点我不舒服。我们先不在这里展开，回去我想认真跟你说一下边界。",
        "signal": "“开玩笑”可能是在试图减轻责任，但你的不舒服需要被命名。",
        "boundary": "现场先止损，私下再谈规则；不忍下去，也不当场羞辱升级。",
        "practice": "写一句公开场合可用的短边界句。",
        "tags": ("边界与同意", "公开玩笑", "即时止损"),
    },
]


def current_resource_count(session: Session) -> int:
    return int(session.exec(select(func.count()).select_from(ResourceLibrary)).one())


def build_blueprints() -> Iterable[ResourceBlueprint]:
    yield from build_public_source_blueprints()
    yield from build_conversation_seed_blueprints()
    yield from build_synthetic_blueprints()


def build_public_source_blueprints() -> Iterable[ResourceBlueprint]:
    for anchor in PUBLIC_SOURCE_ANCHORS:
        source_name = str(anchor["name"])
        if source_name not in MISSION_PUBLIC_SOURCE_NAMES:
            continue
        source_url = str(anchor["url"])
        themes = tuple(str(theme) for theme in anchor["themes"])
        scenes = tuple(str(scene) for scene in anchor["scenes"])
        for scene in scenes:
            for theme in themes:
                for attachment in ATTACHMENTS:
                    for difficulty in (1, 2):
                        axis = MISSION_CORE_AXES[(len(source_name) + len(theme) + difficulty) % len(MISSION_CORE_AXES)]
                        yield ResourceBlueprint(
                            resource_type="media",
                            category=f"公开来源观察卡·{source_name}",
                            scene=scene,
                            difficulty=difficulty,
                            attachment=attachment,
                            tone=theme,
                            title=f"{theme}：{scene}训练卡",
                            content=(
                                f"以 {source_name} 为原站阅读入口，只抽取和“{axis}”直接相关的关系训练线索。"
                                f"面向{attachment}、难度{difficulty}的{scene}场景，围绕“{theme}”完成四步："
                                "先看一句话里的微表情/停顿/语气，再命名情绪流向，再确认边界和同意，"
                                "最后写出一句可拒绝、可继续的回应。偏宏观的数据、公共卫生或纯理论内容不进入本卡主线。"
                            ),
                            usage_tip=(
                                "点击信息源阅读原始公开资料；本卡只保存本项目派生训练摘要，"
                                "不保存第三方全文。"
                            ),
                            tags=(
                                "公开来源",
                                "透明信息源",
                                theme,
                                scene,
                                attachment,
                                f"difficulty:{difficulty}",
                            ),
                            source_name=f"public_anchor:{source_name}",
                            source_url=source_url,
                        )
                        yield ResourceBlueprint(
                            resource_type="phrase",
                            category=f"公开来源练习句·{source_name}",
                            scene=scene,
                            difficulty=difficulty,
                            attachment=attachment,
                            tone=theme,
                            title=f"{scene}里的{theme}回应句",
                            content=(
                                f"读完 {source_name} 的相关入口后，只把它转成一句可用在{scene}里的训练回应："
                                f"“我先听见你这里有一点{theme}，也可能有一点想靠近又想保护自己的拉扯。"
                                "如果我理解错了你可以直接纠正我；你现在更需要我靠近一点，还是慢一点？”"
                                f"这句用于{attachment}、难度{difficulty}，核心训练轴是{axis}。"
                            ),
                            usage_tip="用于把公开知识转化成一句可练习、可拒绝、可继续的关系回应。",
                            tags=(
                                "公开来源",
                                "回应句",
                                theme,
                                scene,
                                attachment,
                                f"difficulty:{difficulty}",
                            ),
                            source_name=f"public_anchor:{source_name}",
                            source_url=source_url,
                        )
                        yield ResourceBlueprint(
                            resource_type="story",
                            category=f"公开来源情绪流·{source_name}",
                            scene=scene,
                            difficulty=difficulty,
                            attachment=attachment,
                            tone=theme,
                            title=f"{scene}中的{theme}微故事",
                            content=(
                                f"这是以 {source_name} 为阅读锚点的{scene}微故事，主线只服务{axis}。"
                                f"{attachment}的一方先把“{theme}”藏在一句看似普通的话里，另一方没有急着分析，"
                                "而是先接住停顿、语气和退后半步的身体信号。关系从泛泛道理回到当下："
                                "我有没有听见你，我有没有给你退路，我们还能不能用一句更柔软的话继续。"
                            ),
                            usage_tip="用于训练看见一段对话背后的情绪流，而不是只抓表层台词。",
                            tags=(
                                "公开来源",
                                "情绪流动故事",
                                theme,
                                scene,
                                attachment,
                                f"difficulty:{difficulty}",
                            ),
                            source_name=f"public_anchor:{source_name}",
                            source_url=source_url,
                        )


def build_conversation_seed_blueprints() -> Iterable[ResourceBlueprint]:
    seed_streams = [_build_single_conversation_seed_blueprints(seed) for seed in CONVERSATION_RESOURCE_SEEDS]
    for bundle in zip_longest(*seed_streams):
        for blueprint in bundle:
            if blueprint is not None:
                yield blueprint


def _build_single_conversation_seed_blueprints(seed: dict[str, object]) -> Iterable[ResourceBlueprint]:
    source = str(seed["source"])
    source_url = str(seed["url"])
    kind = str(seed["kind"])
    for case in CONCRETE_SCENARIO_CASES:
        if kind not in case["axis"]:
            continue
        theme = str(case["theme"])
        scene = str(case["scene"])
        for attachment in ATTACHMENTS:
            for tone in TONES:
                for difficulty in (1, 2, 3):
                    if kind == "joke":
                        title = f"{theme}｜{tone}轻幽默｜{attachment}D{difficulty}"
                        usage = "用于练习成人世界里的好玩、张力和退路：可以暧昧，但必须能停、能拒绝、能不尴尬。"
                    elif kind == "game":
                        title = f"{theme}｜三步训练｜{attachment}D{difficulty}"
                        usage = "用于课堂、错题本或 AI 伴侣追问，把真实场景拆成事实、情绪和下一句。"
                    elif kind == "flirty":
                        title = f"{theme}｜情绪流回应｜{attachment}D{difficulty}"
                        usage = "用于把暧昧、失望或修复场景改写成既有张力又不操控的回应。"
                    elif kind == "phrase":
                        title = f"{theme}｜边界确认句｜{attachment}D{difficulty}"
                        usage = "用于亲密推进、冲突止损或关系定义前的一句清晰确认。"
                    else:
                        title = f"{theme}｜具体故事卡｜{attachment}D{difficulty}"
                        usage = "用于训练从动作、停顿和原话里读懂情绪流，而不是背抽象模板。"
                    role = {
                        "joke": "本卡重点：把紧张场景改成低压幽默，笑点必须服务连接，不能羞辱或逼近。",
                        "game": "本卡重点：拆成事实、感受、边界三步，让用户能直接做一轮练习。",
                        "flirty": "本卡重点：保留暧昧张力，同时把退路、节奏和真实意图说清楚。",
                        "phrase": "本卡重点：沉淀一句可以直接说出口的边界确认句。",
                        "story": "本卡重点：呈现动作、停顿和语气如何推动情绪流变化。",
                    }.get(kind, "本卡重点：把场景转化成可练习、可复盘的关系训练素材。")
                    content = (
                        f"{role}\n"
                        f"场景：{case['situation']}\n"
                        f"TA说：{case['their_words']}\n"
                        f"常见失误：{case['mistake']}\n"
                        f"更好回应（{tone}版）：{case['better']}\n"
                        f"情绪信号：{case['signal']}\n"
                        f"边界与同意：{case['boundary']}\n"
                        f"练习任务：{case['practice']}\n"
                        f"适配提示：面向{attachment}，难度{difficulty}；如果对方沉默、拒绝或转移话题，"
                        "默认降速，不追问、不逼供、不把暧昧当作授权。"
                    )
                    yield ResourceBlueprint(
                        resource_type=kind,
                        category=f"{source.replace('local_anchor:', '')}·{attachment}",
                        scene=scene,
                        difficulty=difficulty,
                        attachment=attachment,
                        tone=tone,
                        title=title,
                        content=content,
                        usage_tip=usage,
                        tags=(
                            "本地派生素材",
                            "具体案例",
                            "非模板化训练",
                            theme,
                            scene,
                            attachment,
                            tone,
                            *tuple(str(tag) for tag in case["tags"]),
                            f"difficulty:{difficulty}",
                        ),
                        source_name=source,
                        source_url=source_url,
                    )


def build_synthetic_blueprints() -> Iterable[ResourceBlueprint]:
    for case in CONCRETE_SCENARIO_CASES:
        theme = str(case["theme"])
        scene = str(case["scene"])
        for attachment in ATTACHMENTS:
            for tone in TONES:
                for difficulty in (1, 2, 3):
                    for resource_type, category, _, _, _, base_tags in RESOURCE_PATTERNS:
                        title = f"{theme}｜{category}｜{tone}｜{attachment}D{difficulty}"
                        type_focus = {
                            "flirty": "训练目标：把暧昧张力落到一句可继续、可拒绝的回应。",
                            "story": "训练目标：阅读一个具体片段，标出靠近、后退、停顿和修复点。",
                            "phrase": "训练目标：提炼一句边界清晰、不施压的短句。",
                            "game": "训练目标：完成一轮事实观察、情绪命名、下一句改写。",
                            "joke": "训练目标：用低压幽默缓和气氛，但不逃避真实情绪。",
                            "media": "训练目标：把案例抽象成可复用的观察框架和复盘清单。",
                        }.get(resource_type, "训练目标：把案例转成可操作练习。")
                        content = (
                            f"{type_focus}\n"
                            f"场景：{case['situation']}\n"
                            f"TA说：{case['their_words']}\n"
                            f"常见失误：{case['mistake']}\n"
                            f"更好回应（{tone}版）：{case['better']}\n"
                            f"情绪流：先识别“{case['signal']}”，再把自己的下一句从评判改成邀请。\n"
                            f"边界点：{case['boundary']}\n"
                            f"练习：{case['practice']}\n"
                            f"难度变化：难度{difficulty}要求补充一个事实观察、一个感受词、一个可拒绝请求；"
                            f"对{attachment}要尤其注意不催促、不冷处理、不用玩笑覆盖真实需求。"
                        )
                        if resource_type == "media":
                            usage_tip = "作为知识卡阅读：先看具体场景，再回到微关系信号、情绪流动和边界判断。"
                        elif resource_type == "phrase":
                            usage_tip = "作为短句练习：从内容里抽取一句可以真实说出口、且不操控对方的话。"
                        elif resource_type == "joke":
                            usage_tip = "作为幽默练习：只使用低压玩笑，保留对方不接梗的退路。"
                        else:
                            usage_tip = "作为训练卡使用：先复述事实，再改写回应，最后检查边界是否清楚。"
                        yield ResourceBlueprint(
                            resource_type=resource_type,
                            category=f"{category}·{attachment}",
                            scene=scene,
                            difficulty=difficulty,
                            attachment=attachment,
                            tone=tone,
                            title=title,
                            content=content,
                            usage_tip=usage_tip,
                            tags=(
                                *base_tags,
                                "具体案例",
                                "非模板化训练",
                                theme,
                                scene,
                                attachment,
                                tone,
                                *tuple(str(tag) for tag in case["tags"]),
                                f"difficulty:{difficulty}",
                            ),
                        )


def blueprint_uuid(blueprint: ResourceBlueprint) -> str:
    stable_parts = [
        blueprint.resource_type,
        blueprint.category,
        blueprint.scene,
        str(blueprint.difficulty),
        blueprint.attachment,
        blueprint.tone,
        blueprint.title,
        blueprint.content,
    ]
    if blueprint.source_url != SYNTHETIC_URL:
        stable_parts.append(blueprint.source_url)
    stable = "|".join(stable_parts)
    return f"synthetic:resource:{uuid.uuid5(uuid.NAMESPACE_URL, stable)}"


def create_resource(blueprint: ResourceBlueprint) -> ResourceLibrary:
    from backend.database.resource_quality_governance import _guide_for, _quality_score, content_fingerprint

    emotional_tone = {
        "primary": blueprint.tone,
        "scene": blueprint.scene,
        "attachment": blueprint.attachment,
        "generator": SOURCE,
    }
    resource = ResourceLibrary(
        resource_uuid=blueprint_uuid(blueprint),
        type=blueprint.resource_type,
        category=blueprint.category,
        title=blueprint.title,
        content=blueprint.content,
        emotional_tone_json=json.dumps(emotional_tone, ensure_ascii=False),
        emotional_intensity=min(10, 4 + blueprint.difficulty),
        applicable_scene=blueprint.scene,
        difficulty_level=blueprint.difficulty,
        gender_target="通用",
        attachment_suitability=blueprint.attachment,
        usage_tip=blueprint.usage_tip,
        effectiveness_rating=8 if blueprint.difficulty < 3 else 9,
        review_status="published",
        reviewer_id="auto_resource_expander",
        reviewed_at=datetime.now(),
        published_at=datetime.now(),
        source=blueprint.source_name,
        source_url=blueprint.source_url,
        tags=",".join([*blueprint.tags]),
    )
    guide = _guide_for(resource)
    resource.source_title = guide.title
    resource.source_summary = guide.summary
    resource.source_excerpt = guide.excerpt
    resource.source_license = guide.license_note
    resource.content_fingerprint = content_fingerprint(resource)
    resource.quality_score = _quality_score(resource, guide)
    return resource


def _is_generated_resource(resource: ResourceLibrary) -> bool:
    source = resource.source or ""
    source_url = resource.source_url or ""
    return (
        source == SOURCE
        or source.startswith("public_anchor:")
        or source.startswith("local_anchor:")
        or source_url.startswith("synthetic://relationship-training/")
    )


def _delete_generated_resources(session: Session, dry_run: bool) -> int:
    deleted = 0
    generated = list(session.exec(select(ResourceLibrary)).all())
    for resource in generated:
        if _is_generated_resource(resource):
            deleted += 1
            if not dry_run:
                session.delete(resource)
    if not dry_run and deleted:
        session.commit()
    return deleted


def expand_resources(
    target_total: int = TARGET_DEFAULT,
    dry_run: bool = False,
    rebuild_generated: bool = False,
) -> dict[str, int | bool]:
    create_db_and_tables()
    with Session(engine) as session:
        deleted = 0
        if rebuild_generated:
            deleted = _delete_generated_resources(session, dry_run)
        actual_before = current_resource_count(session)
        before = actual_before - deleted if dry_run and rebuild_generated else actual_before
        needed = max(0, target_total - before)
        created = 0
        skipped = 0
        for blueprint in build_blueprints():
            resource_uuid = blueprint_uuid(blueprint)
            exists = session.exec(
                select(ResourceLibrary.id).where(ResourceLibrary.resource_uuid == resource_uuid)
            ).first()
            if exists:
                skipped += 1
                continue
            created += 1
            if not dry_run:
                session.add(create_resource(blueprint))
            if created >= needed:
                break
        if not dry_run:
            session.commit()
        after = before if dry_run else current_resource_count(session)
    return {
        "dry_run": dry_run,
        "before": before,
        "target_total": target_total,
        "created": created,
        "skipped": skipped,
        "deleted": deleted,
        "after": after,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="自动派生扩充资源库")
    parser.add_argument("--target-total", type=int, default=TARGET_DEFAULT)
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--rebuild-generated", action="store_true")
    args = parser.parse_args()
    result = expand_resources(
        target_total=args.target_total,
        dry_run=args.dry_run,
        rebuild_generated=args.rebuild_generated,
    )
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
