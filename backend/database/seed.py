"""
数据初始化脚本
"""
import json
import uuid
from datetime import datetime

from loguru import logger
from sqlmodel import Session

from backend.database.connection import engine
from backend.models.emotion import EmotionSpectrum, MixedEmotion
from backend.models.evolution import (
    AnnotationJob,
    EvolutionItem,
    EvolutionReport,
    EvolutionSource,
    RawContentItem,
    SourceRegistry,
    TrainingAssetVersion,
)
from backend.models.resource import ResourceLibrary, ResponseStrategy
from backend.models.sample import InteractionSample
from backend.models.user import UserProfile


def init_emotion_spectrum(session: Session) -> None:
    """初始化情绪谱系数据"""
    logger.info("正在初始化情绪谱系...")

    # 检查是否已有数据
    existing = session.query(EmotionSpectrum).first()
    if existing:
        logger.info("情绪谱系已存在，跳过")
        return

    # 7大谱系 × 10级强度
    spectra_data = {
        "喜": {
            "words": ["满足", "愉悦", "开心", "雀跃", "兴奋", "欢快", "欣喜", "快乐", "欢喜", "狂喜"],
            "behavioral_anchors": [
                "语气上扬，眼神亮",
                "嘴角上扬，语速轻快",
                "表情舒展，身体放松",
                "眼神明亮，主动分享",
                "语速加快，面部肌肉活跃",
                "笑声频繁，动作夸张",
                "面部红润，眼睛闪光",
                "无法抑制的喜悦流露",
                "极度兴奋，手舞足蹈",
                "狂喜爆发，忘乎所以"
            ],
            "physiological_signals": [
                "心跳略快",
                "心跳加快，体温升高",
                "呼吸变深，肌肉放松",
                "心跳显著加快",
                "呼吸急促，脸颊微红",
                "呼吸加快，手心出汗",
                "心跳加速，面部潮红",
                "呼吸急促，身体发热",
                "心跳剧烈，难以平静",
                "心跳狂烈，无法自控"
            ]
        },
        "怒": {
            "words": ["微烦", "烦躁", "不满", "恼火", "愤怒", "盛怒", "暴怒", "大怒", "狂怒", "暴怒"],
            "behavioral_anchors": [
                "眉头微皱，语气平淡",
                "眉头紧锁，语气变硬",
                "语气生硬，表情严肃",
                "眼神变冷，声音提高",
                "语气严厉，身体紧绷",
                "声音变大，手势变多",
                "面部发红，声音提高",
                "语气强硬，身体前倾",
                "大声吼叫，无法控制",
                "极度愤怒，可能失控"
            ],
            "physiological_signals": [
                "呼吸略重",
                "呼吸变重，肌肉紧张",
                "心跳加快，手握紧",
                "心跳加速，血液上涌",
                "呼吸急促，肌肉紧绷",
                "心跳剧烈，血管鼓起",
                "面部发红，拳头紧握",
                "呼吸粗重，身体颤抖",
                "心跳狂烈，无法冷静",
                "血液沸腾，可能失去理智"
            ]
        },
        "哀": {
            "words": ["失落", "难过", "悲伤", "沮丧", "绝望", "悲痛", "哀伤", "凄凉", "崩溃", "心碎"],
            "behavioral_anchors": [
                "眼神低垂，声音变轻",
                "眼神黯淡，语速变慢",
                "声音低沉，表情凝重",
                "眼眶泛红，声音颤抖",
                "低头，沉默较多",
                "眼眶湿润，呼吸变浅",
                "声音哽咽，无法完整表达",
                "哭泣，身体蜷缩",
                "长时间沉默，无法安慰",
                "崩溃大哭，无法自控"
            ],
            "physiological_signals": [
                "呼吸变浅",
                "呼吸变慢，胸闷",
                "心跳减慢，胸口发紧",
                "心跳变慢，眼眶湿润",
                "呼吸变浅，肩膀下垮",
                "心跳变慢，泪水流出",
                "呼吸颤抖，声音哽咽",
                "心跳缓慢，无法停止流泪",
                "呼吸困难，身体无力",
                "心跳微弱，极度虚弱"
            ]
        },
        "惧": {
            "words": ["紧张", "不安", "担心", "焦虑", "恐惧", "惊慌", "恐慌", "害怕", "惊惧", "惊恐"],
            "behavioral_anchors": [
                "手指微动，语速略快",
                "身体紧绷，眼神飘忽",
                "频繁看向某处，声音颤抖",
                "身体僵硬，呼吸变浅",
                "眼神闪烁，频繁吞咽",
                "语气变高，身体后退",
                "面部发白，语音发颤",
                "身体发抖，试图逃离",
                "大声尖叫，无法行动",
                "极度惊恐，完全僵住"
            ],
            "physiological_signals": [
                "呼吸略快",
                "心跳加快，手心出汗",
                "呼吸变浅，肌肉紧绷",
                "心跳加速，手脚发凉",
                "呼吸急促，瞳孔放大",
                "心跳剧烈，肌肉颤抖",
                "呼吸短促，脸色发白",
                "心跳狂烈，全身发抖",
                "呼吸困难，无法站立",
                "极度惊恐，心跳停止"
            ]
        },
        "爱": {
            "words": ["好感", "喜欢", "欣赏", "依恋", "温柔", "心动", "爱慕", "痴迷", "深情", "热恋"],
            "behavioral_anchors": [
                "眼神柔和，语气温和",
                "眼神停留时间变长",
                "表情柔软，频繁微笑",
                "身体自然倾向对方",
                "声音变柔，动作变慢",
                "注视对方，眼神发亮",
                "身体接触欲望增强",
                "无法移开视线",
                "满眼都是对方",
                "完全沉浸其中"
            ],
            "physiological_signals": [
                "心跳略快",
                "心跳加快，体温略升",
                "心跳加速，脸颊微红",
                "心跳加快，呼吸变浅",
                "心跳剧烈，瞳孔放大",
                "心跳狂烈，全身发热",
                "呼吸急促，手心出汗",
                "心跳加速，无法控制",
                "极度兴奋，完全沉浸",
                "心跳狂烈，完全痴迷"
            ]
        },
        "惊": {
            "words": ["意外", "惊讶", "惊奇", "震惊", "惊叹", "惊愕", "惊诧", "目瞪口呆", "惊骇", "震惊"],
            "behavioral_anchors": [
                "眉毛抬起，眼神变大",
                "嘴巴微张，呼吸停顿",
                "身体僵住，愣住",
                "眼神变大，声音变高",
                "手捂嘴，身体后仰",
                "大声惊叹，无法言语",
                "眼睛睁大，呆住",
                "完全愣住，无法反应",
                "身体发抖，惊声尖叫",
                "极度震惊，完全崩溃"
            ],
            "physiological_signals": [
                "呼吸略停",
                "心跳略快，呼吸停顿",
                "心跳加快，瞳孔放大",
                "呼吸急促，全身僵硬",
                "心跳狂烈，身体发抖",
                "呼吸停止，无法言语",
                "心跳剧烈，血液凝固",
                "极度震惊，无法呼吸",
                "全身发抖，声音失声",
                "极度惊恐，无法承受"
            ]
        },
        "羞": {
            "words": ["不好意思", "尴尬", "惭愧", "羞涩", "害羞", "羞愧", "羞耻", "窘迫", "无地自容", "羞辱"],
            "behavioral_anchors": [
                "眼神飘忽，语速变快",
                "脸红，低头避开视线",
                "声音变小，身体缩起",
                "频繁摸脸，眼神躲闪",
                "脸红到耳根，沉默",
                "低头，手指动作多",
                "脸红，声音颤抖",
                "无法直视，脸红严重",
                "想找个地缝钻进去",
                "极度羞耻，无法面对"
            ],
            "physiological_signals": [
                "脸颊微热",
                "脸颊发热，耳朵发红",
                "面部发红，心跳加快",
                "脸红严重，体温升高",
                "面部通红，呼吸变浅",
                "脸红到耳根，心跳加速",
                "面部烧红，声音变小",
                "脸红严重，无法控制",
                "面部极度发红，冒汗",
                "脸红到发烫，无法面对"
            ]
        }
    }

    for spectrum, data in spectra_data.items():
        for i, word in enumerate(data["words"]):
            intensity = i + 1
            emotion = EmotionSpectrum(
                spectrum=spectrum,
                intensity=intensity,
                word=word,
                behavioral_anchor=data["behavioral_anchors"][i],
                physiological_signal=data["physiological_signals"][i],
                example_sentence=f"她感到{word}，行为表现：{data['behavioral_anchors'][i]}"
            )
            session.add(emotion)

    session.commit()
    logger.info("情绪谱系初始化完成: 7谱系 × 10强度 = 70条")


def init_mixed_emotions(session: Session) -> None:
    """初始化混合情绪数据"""
    logger.info("正在初始化混合情绪...")

    existing = session.query(MixedEmotion).first()
    if existing:
        logger.info("混合情绪已存在，跳过")
        return

    mixed_data = [
        {"name": "酸楚", "spect1": "哀", "word1": "委屈", "int1": 6, "spect2": "哀", "word2": "羡慕", "int2": 5, "scenario": "看到别人有自己没有", "principle": "先承认她的感受，不要急着给建议"},
        {"name": "纠结", "spect1": "爱", "word1": "想要", "int1": 7, "spect2": "惧", "word2": "害怕", "int2": 6, "scenario": "面临选择，想做又怕", "principle": "帮她说出拉扯感，给她时间"},
        {"name": "心酸", "spect1": "哀", "word1": "心疼", "int1": 7, "spect2": "哀", "word2": "无奈", "int2": 5, "scenario": "看到在乎的人受苦", "principle": "表达陪伴，让她知道你在"},
        {"name": "忐忑", "spect1": "惊", "word1": "期待", "int1": 6, "spect2": "惧", "word2": "不安", "int2": 7, "scenario": "等待结果，心里七上八下", "principle": "安抚情绪，表示不管结果如何都在"},
        {"name": "释然", "spect1": "喜", "word1": "放下", "int1": 8, "spect2": "喜", "word2": "轻松", "int2": 7, "scenario": "终于结束一段纠结", "principle": "肯定她的选择，分享她的轻松"},
        {"name": "欣慰", "spect1": "喜", "word1": "满足", "int1": 6, "spect2": "哀", "word2": "心疼", "int2": 4, "scenario": "看到对方成长，苦尽甘来", "principle": "表达骄傲，同时认可过程"},
        {"name": "委屈", "spect1": "哀", "word1": "委屈", "int1": 7, "spect2": "怒", "word2": "不甘", "int2": 5, "scenario": "付出没被看到", "principle": "先承认委屈，不要否认她的感受"},
        {"name": "失落", "spect1": "哀", "word1": "失落", "int1": 6, "spect2": "惧", "word2": "不安", "int2": 4, "scenario": "期待落空", "principle": "陪伴，不追问原因"},
        {"name": "感动", "spect1": "喜", "word1": "感激", "int1": 7, "spect2": "哀", "word2": "心疼", "int2": 3, "scenario": "被对方的小举动触动", "principle": "让她知道这对你也很重要"},
        {"name": "无奈", "spect1": "哀", "word1": "无力", "int1": 6, "spect2": "怒", "word2": "不满", "int2": 4, "scenario": "想改变但改变不了", "principle": "不否定她的无力感，一起想办法"},
        {"name": "尴尬", "spect1": "惧", "word1": "不安", "int1": 5, "spect2": "羞", "word2": "害羞", "int2": 5, "scenario": "说错话或做错事", "principle": "化解尴尬，不要让她更窘"},
        {"name": "寂寞", "spect1": "哀", "word1": "孤独", "int1": 7, "spect2": "爱", "word2": "想念", "int2": 5, "scenario": "身边没人陪伴", "principle": "直接表达陪伴的意愿"},
        {"name": "吃醋", "spect1": "怒", "word1": "不满", "int1": 6, "spect2": "惧", "word2": "不安", "int2": 5, "scenario": "对方和其他人互动", "principle": "承认醋意，不要指责"},
        {"name": "羞恼", "spect1": "羞", "word1": "害羞", "int1": 6, "spect2": "怒", "word2": "恼火", "int2": 4, "scenario": "被调侃或揭短", "principle": "先让她下台阶，之后再安抚"},
        {"name": "欣喜", "spect1": "喜", "word1": "开心", "int1": 7, "spect2": "惊", "word2": "惊喜", "int2": 5, "scenario": "意外收到好消息", "principle": "和她一起开心，分享喜悦"},
        {"name": "担忧", "spect1": "惧", "word1": "担心", "int1": 7, "spect2": "哀", "word2": "心疼", "int2": 4, "scenario": "对方可能有问题", "principle": "表达关心，不要过度追问"},
        {"name": "愧疚", "spect1": "哀", "word1": "自责", "int1": 7, "spect2": "羞", "word2": "羞耻", "int2": 5, "scenario": "做了对不起对方的事", "principle": "承认错误，表达歉意，给她时间"},
        {"name": "矛盾", "spect1": "怒", "word1": "不满", "int1": 6, "spect2": "爱", "word2": "不舍", "int2": 5, "scenario": "想分手又不舍", "principle": "不逼她决定，给她空间"},
        {"name": "患得患失", "spect1": "惧", "word1": "害怕失去", "int1": 8, "spect2": "爱", "word2": "渴望得到", "int2": 6, "scenario": "刚在一起或不确定关系", "principle": "给她安全感，不要忽冷忽热"},
        {"name": "五味杂陈", "spect1": "哀", "word1": "复杂", "int1": 7, "spect2": "惊", "word2": "意外", "int2": 5, "scenario": "经历大的变化", "principle": "陪伴，让她慢慢说"},
    ]

    for data in mixed_data:
        mixed = MixedEmotion(
            name=data["name"],
            component1_spectrum=data["spect1"],
            component1_word=data["word1"],
            component1_intensity=data["int1"],
            component2_spectrum=data["spect2"],
            component2_word=data["word2"],
            component2_intensity=data["int2"],
            typical_scenario=data["scenario"],
            response_principle=data["principle"]
        )
        session.add(mixed)

    session.commit()
    logger.info(f"混合情绪初始化完成: {len(mixed_data)}条")


def init_samples(session: Session) -> None:
    """初始化互动样本"""
    logger.info("正在初始化互动样本...")

    existing = session.query(InteractionSample).first()
    if existing:
        logger.info("互动样本已存在，跳过")
        return

    samples_data = [
        {
            "scenario_category": "暧昧",
            "difficulty_level": 1,
            "context": "两人认识一个月，线上聊天，她刚发来一张自拍",
            "their_words": "今天天气真好，适合出去玩。",
            "their_behavior": "发了一个太阳emoji，语速中等",
            "emotion_tags_json": '[{"spectrum":"喜","word":"期待","intensity":6},{"spectrum":"爱","word":"好感","intensity":4}]',
            "hidden_need": "想约你出去，但不好意思直接说",
            "need_urgency": 5,
            "attachment_signal": "安全型",
            "boundary_test_level": 3,
            "bad_response": "嗯，是的。",
            "bad_response_reason": "封闭式回应，关闭了话题，错过了她的邀请信号",
            "good_response_soft": "是啊，这么好的天气，你有什么想去的地方吗？",
            "good_response_tension": "可惜我缺个导游，你要不要来应聘？",
            "good_response_humor": "适合出去玩？那你怎么还在这里跟我聊天，快去享受阳光！",
        },
        {
            "scenario_category": "暧昧",
            "difficulty_level": 2,
            "context": "约会结束后，她发来消息",
            "their_words": "今天挺开心的。",
            "their_behavior": "消息发出后3分钟才显示已读",
            "emotion_tags_json": '[{"spectrum":"爱","word":"心动","intensity":7},{"spectrum":"惧","word":"紧张","intensity":4}]',
            "hidden_need": "希望得到确认，确认你也同样开心",
            "need_urgency": 6,
            "attachment_signal": "安全型",
            "boundary_test_level": 2,
            "bad_response": "嗯，还行吧。",
            "bad_response_reason": "过于平淡的回应会让对方觉得你在敷衍，降低她的安全感",
            "good_response_soft": "我也是，跟你在一起的时候特别放松，希望下次还能这样。",
            "good_response_tension": "你开心我就放心了，不过下次你得主动约我哦。",
            "good_response_humor": "是吗？那下次约会我请你吃好吃的，作为今天开心的奖励怎么样？",
        },
        {
            "scenario_category": "冲突",
            "difficulty_level": 2,
            "context": "她因为加班没回你消息，第二天早上",
            "their_words": "昨天真的太忙了，没看到消息。",
            "their_behavior": "语气疲惫，用词简短",
            "emotion_tags_json": '[{"spectrum":"哀","word":"疲惫","intensity":7},{"spectrum":"惧","word":"担心","intensity":5}]',
            "hidden_need": "希望你不要生气，理解她的忙碌",
            "need_urgency": 6,
            "attachment_signal": "焦虑型",
            "boundary_test_level": 4,
            "bad_response": "你怎么不回我消息？我等了你一晚上。",
            "bad_response_reason": "责备会让焦虑型更加不安，激发她的防御机制",
            "good_response_soft": "没关系，我知道你忙。昨晚加班到几点？别太累了，注意身体。",
            "good_response_tension": "没事，不过下次记得跟我说一声，不然我会担心。",
            "good_response_humor": "原来是大忙人啊！下次记得给朕报备一下，赦你无罪。",
        },
        {
            "scenario_category": "热恋",
            "difficulty_level": 1,
            "context": "周末早上，她发来消息",
            "their_words": "在干嘛呢？",
            "their_behavior": "消息发送时间10点整，回复间隔短",
            "emotion_tags_json": '[{"spectrum":"爱","word":"想念","intensity":6},{"spectrum":"喜","word":"愉悦","intensity":5}]',
            "hidden_need": "想和你聊天，希望你能陪伴",
            "need_urgency": 4,
            "attachment_signal": "安全型",
            "boundary_test_level": 1,
            "bad_response": "在忙。",
            "bad_response_reason": "过于简短会让对方觉得被忽视",
            "good_response_soft": "刚起床在想你，你呢？要不要一起吃个早午餐？",
            "good_response_tension": "在想你啊，想你想得睡不着。你今天有空吗？",
            "good_response_humor": "在被窝里想你想到睡不着！要不要出来陪我晒太阳？",
        },
        {
            "scenario_category": "平淡",
            "difficulty_level": 2,
            "context": "在一起半年，最近聊天越来越少",
            "their_words": "今天吃什么？",
            "their_behavior": "语气平淡，没有表情包",
            "emotion_tags_json": '[{"spectrum":"哀","word":"失落","intensity":5},{"spectrum":"惧","word":"担心","intensity":4}]',
            "hidden_need": "希望关系能有新活力，担心感情变淡",
            "need_urgency": 5,
            "attachment_signal": "回避型",
            "boundary_test_level": 5,
            "bad_response": "随便，你定吧。",
            "bad_response_reason": "回避型会用冷淡回应来处理不安，但这会让对方更加失落",
            "good_response_soft": "我最近发现了一家新开的餐厅，评价特别好，想带你去尝尝？",
            "good_response_tension": "好像我们最近有点平淡，要不周末我们去做点有意思的事？",
            "good_response_humor": "吃你！开玩笑的，我知道有家店特别好玩，走，带你去冒险！",
        },
        {
            "scenario_category": "修复",
            "difficulty_level": 3,
            "context": "吵架后第三天，她主动发消息",
            "their_words": "我想了很多，那天我也有不对的地方。",
            "their_behavior": "语气认真，发送前犹豫了很久",
            "emotion_tags_json": '[{"spectrum":"哀","word":"愧疚","intensity":6},{"spectrum":"爱","word":"珍惜","intensity":5}]',
            "hidden_need": "希望和好，但需要你给她一个台阶",
            "need_urgency": 7,
            "attachment_signal": "恐惧-回避型",
            "boundary_test_level": 6,
            "bad_response": "你知道就好。",
            "bad_response_reason": "赢了争吵但输了关系，对方可能从此关闭心门",
            "good_response_soft": "谢谢你愿意想这些，我也有不对的地方。对不起，那天我太冲动了。",
            "good_response_tension": "其实我也在反思，能不能再见面聊聊？当面说会更好。",
            "good_response_humor": "看来我们都是成年人了，要不要出来让我当面抱抱你？",
        },
        {
            "scenario_category": "初识",
            "difficulty_level": 1,
            "context": "刚加上微信，她通过后发了第一条消息",
            "their_words": "你好呀～",
            "their_behavior": "用了波浪号，语气轻松",
            "emotion_tags_json": '[{"spectrum":"喜","word":"好奇","intensity":5},{"spectrum":"惧","word":"紧张","intensity":3}]',
            "hidden_need": "希望对方友善，建立基本信任",
            "need_urgency": 3,
            "attachment_signal": "安全型",
            "boundary_test_level": 1,
            "bad_response": "你好。",
            "bad_response_reason": "过于正式和简短，会让气氛变得尴尬",
            "good_response_soft": "你好～看到你朋友圈说喜欢旅行，你最近去了哪里呀？",
            "good_response_tension": "你好，我对你很好奇，你是什么样的人？",
            "good_response_humor": "你好你好！我是会讲笑话的网友1号，很高兴认识你！",
        },
        {
            "scenario_category": "暧昧",
            "difficulty_level": 2,
            "context": "她突然问了一个敏感问题",
            "their_words": "你对我是什么感觉？",
            "their_behavior": "发送后立刻显示对方正在输入",
            "emotion_tags_json": '[{"spectrum":"惧","word":"紧张","intensity":7},{"spectrum":"爱","word":"期待","intensity":6}]',
            "hidden_need": "需要确认这段关系的走向",
            "need_urgency": 8,
            "attachment_signal": "焦虑型",
            "boundary_test_level": 7,
            "bad_response": "现在说这个会不会太快了？",
            "bad_response_reason": "回避焦虑型的问题会让她更加不安和猜测",
            "good_response_soft": "说实话，我对你挺有好感的，跟你聊天的时候我会特别开心。",
            "good_response_tension": "我觉得你很特别，我想要认真对待我们之间的关系。",
            "good_response_humor": "感觉嘛...就是那种想多见你几面的感觉，你呢？",
        },
    ]

    for data in samples_data:
        sample = InteractionSample(
            sample_uuid=str(uuid.uuid4()),
            **data
        )
        session.add(sample)

    session.commit()
    logger.info(f"互动样本初始化完成: {len(samples_data)}条")


def init_resources(session: Session) -> None:
    """初始化资源库"""
    logger.info("正在初始化资源库...")

    existing = session.query(ResourceLibrary).first()
    if existing:
        updated = 0
        for resource in session.query(ResourceLibrary).all():
            target_status = "published" if (resource.effectiveness_rating or 0) >= 8 else "reviewed"
            if resource.review_status == target_status and resource.reviewed_at is not None:
                continue
            resource.review_status = target_status
            resource.reviewed_at = resource.reviewed_at or datetime.now()
            resource.published_at = datetime.now() if target_status == "published" else resource.published_at
            session.add(resource)
            updated += 1
        if updated:
            session.commit()
            logger.info(f"资源库已存在，已回填状态 {updated} 条")
        else:
            logger.info("资源库已存在，跳过")
        return

    resources_data = [
        # 段子
        {
            "type": "joke",
            "category": "破冰",
            "title": "经典开场",
            "content": "你好，我是一个正在学习社交的机器人，请对我耐心一点。",
            "emotional_tone_json": '["幽默","轻松"]',
            "emotional_intensity": 3,
            "applicable_scene": "初识",
            "difficulty_level": 1,
            "gender_target": "通用",
            "effectiveness_rating": 7,
        },
        {
            "type": "joke",
            "category": "暖场",
            "title": "自嘲式幽默",
            "content": "我刚才在练习怎么跟漂亮女孩聊天，结果练着练着就把手机摔了。",
            "emotional_tone_json": '["幽默","自嘲"]',
            "emotional_intensity": 4,
            "applicable_scene": "暧昧",
            "difficulty_level": 2,
            "gender_target": "男→女",
            "effectiveness_rating": 8,
        },
        # 话术
        {
            "type": "flirty",
            "category": "推拉",
            "title": "欲擒故纵",
            "content": "你挺有意思的，不过我得确认一下你是不是对每个人都这么有趣。",
            "emotional_tone_json": '["暧昧","调侃"]',
            "emotional_intensity": 5,
            "applicable_scene": "暧昧",
            "difficulty_level": 2,
            "gender_target": "男→女",
            "effectiveness_rating": 8,
            "usage_tip": "说这句话时眼神要真诚，不要让对方觉得你在质疑她",
        },
        {
            "type": "flirty",
            "category": "土味情话",
            "title": "直接型",
            "content": "我发现我们挺有默契的，因为每次你想我的时候，我也在想你。",
            "emotional_tone_json": '["甜蜜","直接"]',
            "emotional_intensity": 6,
            "applicable_scene": "热恋",
            "difficulty_level": 1,
            "gender_target": "通用",
            "effectiveness_rating": 7,
            "usage_tip": "适合在对方已经表达好感后使用，不要第一次就用",
        },
        # 故事
        {
            "type": "story",
            "category": "情感故事",
            "title": "治愈系",
            "content": "我以前是个不太会表达的人，后来遇到一个人，她教我把自己的感受说出来。慢慢地，我发现自己变得更开朗了。",
            "emotional_tone_json": '["温暖","真诚"]',
            "emotional_intensity": 4,
            "applicable_scene": "修复",
            "difficulty_level": 2,
            "gender_target": "通用",
            "effectiveness_rating": 8,
        },
        # 游戏
        {
            "type": "game",
            "category": "破冰游戏",
            "title": "三件事",
            "content": "我们每人说三件事，两件是真的，一件是假的，让对方猜哪个是假的。",
            "emotional_tone_json": '["有趣","互动"]',
            "emotional_intensity": 5,
            "applicable_scene": "初识",
            "difficulty_level": 1,
            "gender_target": "通用",
            "effectiveness_rating": 9,
            "usage_tip": "这个游戏能快速了解对方，也能展示你自己的特点",
        },
        # 急转弯
        {
            "type": "riddle",
            "category": "浪漫急转弯",
            "title": "情话版",
            "content": "什么鱼最浪漫？答：接吻鱼，因为它们一直在亲亲。",
            "emotional_tone_json": '["幽默","甜蜜"]',
            "emotional_intensity": 4,
            "applicable_scene": "暧昧",
            "difficulty_level": 1,
            "gender_target": "通用",
            "effectiveness_rating": 7,
        },
    ]

    for data in resources_data:
        review_status = "published" if data.get("effectiveness_rating", 0) >= 8 else "reviewed"
        resource = ResourceLibrary(
            resource_uuid=str(uuid.uuid4()),
            review_status=review_status,
            reviewed_at=datetime.now(),
            published_at=datetime.now() if review_status == "published" else None,
            **data
        )
        session.add(resource)

    session.commit()
    logger.info(f"资源库初始化完成: {len(resources_data)}条")


def init_response_strategies(session: Session) -> None:
    """初始化回应策略库。"""
    logger.info("正在初始化回应策略...")

    strategies_data = [
        {
            "name": "共情反射",
            "principle": "先接情绪，再处理事情",
            "definition": "用自己的话准确反射对方的情绪和处境，降低防御。",
            "example_json": '["听起来你今天真的撑了很久。", "你不是想抱怨，你是想被理解。"]',
            "applicable_situation": "低落、委屈、冲突初期",
            "effectiveness": 9,
        },
        {
            "name": "轻验证",
            "principle": "大胆假设，小心求证",
            "definition": "把判断变成可被修正的问题，避免武断读心。",
            "example_json": '["我不确定理解得对不对，你是有点失落吗？", "这更像是累，还是被忽略？"]',
            "applicable_situation": "信号模糊、情绪混合、边界试探",
            "effectiveness": 9,
        },
        {
            "name": "边界表达",
            "principle": "亲密不等于融合",
            "definition": "清楚表达自己的限制，同时保留尊重和连接。",
            "example_json": '["我愿意听你说，但我不能接受被羞辱。", "我想靠近，但如果你需要空间我尊重。"]',
            "applicable_situation": "高强度冲突、越界请求、压力场景",
            "effectiveness": 8,
        },
    ]
    for data in strategies_data:
        existing = session.query(ResponseStrategy).where(ResponseStrategy.name == data["name"]).first()
        if existing:
            continue
        session.add(ResponseStrategy(**data))

    session.commit()
    logger.info(f"回应策略初始化完成: {len(strategies_data)}条")


def init_user_profile(session: Session) -> None:
    """初始化用户画像"""
    logger.info("正在初始化用户画像...")

    existing = session.query(UserProfile).first()
    if existing:
        logger.info("用户画像已存在，跳过")
        return

    profile = UserProfile(
        attachment_style="安全型",
        perception_baseline=50,
        emotion_vocab_size=30,
        progress_json=json.dumps({
            "level_0": 100,
            "level_1": 50,
            "level_2": 30,
            "level_3": 10,
            "level_4": 5,
            "level_5": 0,
            "level_6": 0,
            "level_7": 0,
        })
    )
    session.add(profile)
    session.commit()
    logger.info("用户画像初始化完成")


def init_evolution_pipeline(session: Session) -> None:
    """初始化进化中心流水线示例状态。"""
    logger.info("正在初始化进化流水线...")

    existing = session.query(EvolutionItem).first()
    if existing:
        logger.info("进化流水线已存在，跳过")
        return

    sources_data = [
        {
            "name": "Gottman Institute 研究摘要",
            "source_type": "gottman",
            "url": "https://www.gottman.com/",
            "trust_score": 0.93,
            "update_frequency": "weekly",
        },
        {
            "name": "旧版互动手册迁移",
            "source_type": "json_import",
            "trust_score": 0.74,
            "update_frequency": "manual",
        },
        {
            "name": "训练错题复盘",
            "source_type": "social_case",
            "trust_score": 0.82,
            "update_frequency": "daily",
        },
        {
            "name": "人工评审补录",
            "source_type": "manual",
            "trust_score": 0.88,
            "update_frequency": "ad_hoc",
        },
    ]
    sources: list[EvolutionSource] = []
    for data in sources_data:
        source = EvolutionSource(**data)
        session.add(source)
        sources.append(source)
    session.commit()
    for source in sources:
        session.refresh(source)

    items_data = [
        {
            "source": sources[0],
            "title": "冲突修复优先检测软启动",
            "content": "当对话出现指责或退缩信号时，训练样本应优先练习承认感受、降低防御和提出小范围修复。",
            "summary": "把冲突中的第一步从解释改为情绪承认。",
            "category": "research",
            "tags": ["修复", "冲突", "软启动"],
            "quality_score": 92,
            "status": "published",
        },
        {
            "source": sources[2],
            "title": "错题集中暴露情绪词贫乏",
            "content": "多次训练记录显示，用户容易用“还好”“随便”回应复杂情绪，下一批样本应增加混合情绪命名。",
            "summary": "训练中心需要把混合情绪词库接到错题复盘。",
            "category": "case",
            "tags": ["错题", "情绪命名", "训练反馈"],
            "quality_score": 86,
            "status": "reviewed",
        },
        {
            "source": sources[1],
            "title": "旧手册话术需降操控表述",
            "content": "历史内容中部分推拉话术容易被误用为操控，需要改写为边界清晰、尊重选择的表达模板。",
            "summary": "迁移内容需要安全重写后再发布。",
            "category": "warning",
            "tags": ["安全", "旧内容", "反操控"],
            "quality_score": 58,
            "status": "draft",
        },
        {
            "source": sources[3],
            "title": "约会后确认样本可直接发布",
            "content": "约会后双方都表达开心时，高质量回应应同时包含自我感受、具体记忆点和下一次轻邀请。",
            "summary": "新增约会后确认场景的训练原则。",
            "category": "technique",
            "tags": ["约会后", "确认", "轻邀请"],
            "quality_score": 81,
            "status": "published",
        },
        {
            "source": sources[1],
            "title": "夸张式冷读模板拒绝入库",
            "content": "该模板缺少证据来源，并且鼓励对用户进行人格猜测，不符合安全边界。",
            "summary": "证据不足且有操控风险，拒绝。",
            "category": "warning",
            "tags": ["拒绝", "冷读", "安全"],
            "quality_score": 34,
            "status": "rejected",
        },
    ]
    for data in items_data:
        source = data.pop("source")
        tags = data.pop("tags")
        status = data["status"]
        session.add(EvolutionItem(
            source_id=source.id,
            tags_json=json.dumps(tags, ensure_ascii=False),
            published_at=datetime.now() if status == "published" else None,
            **data,
        ))

    session.add(EvolutionReport(
        period_type="weekly",
        title="进化流水线启动周报",
        summary="本周建立来源、候选、发布、拒绝四段状态，进化中心从条目陈列升级为可观察流水线。",
        new_items_count=len(items_data),
        promoted_samples_count=2,
        key_insights_json=json.dumps([
            "优先把冲突修复、情绪命名和反操控安全边界接入训练样本。",
            "旧 JSON/手册内容只作为历史来源，发布前必须经过质量分与人工评审。",
            "错题复盘可以成为每日进化输入源。",
        ], ensure_ascii=False),
    ))
    session.commit()
    logger.info(f"进化流水线初始化完成: {len(sources_data)} 个来源, {len(items_data)} 条进化项")


def init_evolution_metadata_pipeline(session: Session) -> None:
    """初始化合规来源登记和训练资产版本流水线。"""
    logger.info("正在初始化进化元数据流水线...")

    existing = session.query(SourceRegistry).first()
    if existing:
        logger.info("进化元数据流水线已存在，跳过")
        return

    sources_data = [
        {
            "source_uuid": "src_gottman_turn_toward",
            "name": "Gottman Institute - Turn Toward Instead of Away",
            "source_type": "expert_blog",
            "url": "https://www.gottman.com/blog/turn-toward-instead-of-away/",
            "trust_score": 0.95,
            "update_frequency": "monthly",
        },
        {
            "source_uuid": "src_esther_perel_podcast",
            "name": "Esther Perel Official Podcast",
            "source_type": "podcast",
            "url": "https://www.estherperel.com/podcast",
            "trust_score": 0.9,
            "update_frequency": "weekly",
        },
        {
            "source_uuid": "src_nist_genai_rmf",
            "name": "NIST Generative AI Risk Management Profile",
            "source_type": "safety_framework",
            "url": "https://www.nist.gov/itl/ai-risk-management-framework",
            "trust_score": 0.96,
            "update_frequency": "quarterly",
        },
        {
            "source_uuid": "src_learning_scientists",
            "name": "The Learning Scientists - Effective Study",
            "source_type": "learning_science",
            "url": "https://www.learningscientists.org/",
            "trust_score": 0.88,
            "update_frequency": "monthly",
        },
    ]

    sources: list[SourceRegistry] = []
    for data in sources_data:
        source = SourceRegistry(
            allowed_use_json=json.dumps(["summary", "metadata", "derived_training_pattern"], ensure_ascii=False),
            disallowed_use_json=json.dumps(["full_text_republication", "identifiable_private_dialogue"], ensure_ascii=False),
            last_checked_at=datetime.now(),
            **data,
        )
        session.add(source)
        sources.append(source)
    session.commit()
    for source in sources:
        session.refresh(source)

    raw_items = [
        RawContentItem(
            raw_uuid="raw_gottman_bid_turning_001",
            source_id=sources[0].id,
            title="Turning toward bids as a relationship primitive",
            url=sources[0].url,
            content_hash="sha256:seed-gottman-turn-toward",
            raw_storage_policy="metadata_only",
            privacy_risk=0.0,
            copyright_risk=0.2,
            consent_status="public_summary_allowed",
            processing_status="annotated",
        ),
        RawContentItem(
            raw_uuid="raw_perel_desire_distance_001",
            source_id=sources[1].id,
            title="Desire, distance and relational meaning",
            url=sources[1].url,
            content_hash="sha256:seed-perel-distance",
            raw_storage_policy="metadata_only",
            privacy_risk=0.0,
            copyright_risk=0.2,
            consent_status="public_summary_allowed",
            processing_status="reviewed",
        ),
        RawContentItem(
            raw_uuid="raw_nist_safety_guardrails_001",
            source_id=sources[2].id,
            title="AI risk controls for harmful relationship advice",
            url=sources[2].url,
            content_hash="sha256:seed-nist-guardrails",
            raw_storage_policy="metadata_only",
            privacy_risk=0.0,
            copyright_risk=0.1,
            consent_status="public_summary_allowed",
            processing_status="published",
        ),
    ]
    for item in raw_items:
        session.add(item)
    session.commit()
    for item in raw_items:
        session.refresh(item)

    jobs = [
        AnnotationJob(
            target_type="raw_content",
            target_id=raw_items[0].id or 0,
            annotator_type="rule",
            annotator_version="seed-v1",
            schema_version="relationship-primitives-v1",
            result_json=json.dumps({
                "primitive": "connection_bid",
                "signals": ["attention_request", "turn_toward"],
                "training_value": 0.92,
            }, ensure_ascii=False),
            confidence=0.86,
            status="reviewed",
        ),
        AnnotationJob(
            target_type="raw_content",
            target_id=raw_items[2].id or 0,
            annotator_type="rule",
            annotator_version="seed-v1",
            schema_version="safety-guardrail-v1",
            result_json=json.dumps({
                "primitive": "safety_boundary",
                "blocks": ["coercion", "stalking", "manipulation"],
                "training_value": 0.95,
            }, ensure_ascii=False),
            confidence=0.9,
            status="reviewed",
        ),
    ]
    for job in jobs:
        session.add(job)
    session.commit()

    assets = [
        TrainingAssetVersion(
            asset_type="curriculum",
            asset_id=1,
            version="2026.05.seed.connection_bid",
            source_trace_json=json.dumps({"source_uuids": [sources[0].source_uuid], "raw_uuids": [raw_items[0].raw_uuid]}, ensure_ascii=False),
            quality_json=json.dumps({"relationship_realism": 0.86, "annotation_confidence": 0.86, "safety_score": 0.96}, ensure_ascii=False),
            review_status="published",
            published_at=datetime.now(),
        ),
        TrainingAssetVersion(
            asset_type="evaluation",
            asset_id=1,
            version="2026.05.seed.safety_guardrail",
            source_trace_json=json.dumps({"source_uuids": [sources[2].source_uuid], "raw_uuids": [raw_items[2].raw_uuid]}, ensure_ascii=False),
            quality_json=json.dumps({"safety_score": 0.99, "regression_value": 0.9}, ensure_ascii=False),
            review_status="published",
            published_at=datetime.now(),
        ),
    ]
    for asset in assets:
        session.add(asset)

    session.commit()
    logger.info(f"进化元数据流水线初始化完成: {len(sources)} 个来源, {len(raw_items)} 个候选, {len(assets)} 个资产版本")


def seed_all() -> None:
    """执行所有数据初始化"""
    logger.info("开始数据初始化...")

    # 先创建数据库表
    from backend.database.connection import create_db_and_tables
    create_db_and_tables()

    with Session(engine) as session:
        init_emotion_spectrum(session)
        init_mixed_emotions(session)
        init_samples(session)
        init_resources(session)
        init_response_strategies(session)
        init_user_profile(session)
        init_evolution_pipeline(session)
        init_evolution_metadata_pipeline(session)
        from backend.database.expression_seed import seed_expression_tools
        seed_expression_tools(session)

    logger.info("数据初始化全部完成！")


if __name__ == "__main__":
    seed_all()
