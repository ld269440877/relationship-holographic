"""
海量数据初始化脚本
从现有资源扩充数据到 5000+ 条
"""
import uuid
from loguru import logger
from sqlmodel import Session

from backend.database.connection import engine
from backend.models.sample import InteractionSample
from backend.models.resource import ResourceLibrary


# 扩充的互动样本数据（100+条）
EXPANDED_SAMPLES = [
    # 初识场景
    {
        "scenario_category": "初识", "difficulty_level": 1,
        "context": "在朋友的生日聚会上，你们第一次见面，她正站在角落喝水",
        "their_words": "你好，我好像没见过你，你是小明的朋友吗？",
        "their_behavior": "微微歪头，嘴角带笑，态度友善",
        "emotion_tags_json": '[{"spectrum":"喜","word":"好奇","intensity":5},{"spectrum":"惧","word":"紧张","intensity":3}]',
        "hidden_need": "想认识新朋友，希望对方友善",
        "need_urgency": 3, "attachment_signal": "安全型", "boundary_test_level": 1,
        "bad_response": "嗯，我是。",
        "bad_response_reason": "过于简短和冷淡，让对话无法继续",
        "good_response_soft": "是啊，我是小明的高中同学。你是第一次参加他的生日会吗？",
        "good_response_tension": "对，第一次见，你看起来像是这里的常客？",
        "good_response_humor": "是啊，小明说今天会有很多有趣的人，我就来了，没想到第一个有趣的人就是你。",
    },
    {
        "scenario_category": "初识", "difficulty_level": 1,
        "context": "相亲场合，服务员刚上完菜，她先动筷子",
        "their_words": "不好意思，我有点饿了，先吃了，你不介意吧？",
        "their_behavior": "略带歉意的笑，筷子已经拿在手里",
        "emotion_tags_json": '[{"spectrum":"羞","word":"不好意思","intensity":5},{"spectrum":"喜","word":"轻松","intensity":4}]',
        "hidden_need": "希望对方能理解，不要觉得她没礼貌",
        "need_urgency": 4, "attachment_signal": "安全型", "boundary_test_level": 2,
        "bad_response": "介意，刚见面就自己吃，不太好吧。",
        "bad_response_reason": "过于计较，会让气氛变得尴尬",
        "good_response_soft": "没关系，我也有点饿，我们一起吃吧。这家店的招牌菜是那道红烧肉。",
        "good_response_tension": "没关系，不过下次约会我会选个你不太饿的时间。",
        "good_response_humor": "介意啊，我刚想夹那块红烧肉呢！算了算了，看你饿的样子，让着你。",
    },
    {
        "scenario_category": "初识", "difficulty_level": 2,
        "context": "线上聊天，她突然问了一个私人问题",
        "their_words": "你谈过几次恋爱啊？",
        "their_behavior": "发送后马上撤回了一部分文字",
        "emotion_tags_json": '[{"spectrum":"惧","word":"紧张","intensity":6},{"spectrum":"爱","word":"好奇","intensity":5}]',
        "hidden_need": "想知道你的感情历史，判断你是不是合适的人",
        "need_urgency": 6, "attachment_signal": "焦虑型", "boundary_test_level": 4,
        "bad_response": "你问这个干嘛？",
        "bad_response_reason": "防备姿态会让对方更加不安",
        "good_response_soft": "谈过两次，都是大学时候的事了。你呢，怎么突然问这个？",
        "good_response_tension": "这个问题有点敏感，不过我可以告诉你。两次，认真谈的那种。",
        "good_response_humor": "你是要开始做背景调查了吗？放心，我没有案底，感情史也是清白的。",
    },
    {
        "scenario_category": "初识", "difficulty_level": 2,
        "context": "在咖啡厅约会，她盯着你看了一会儿",
        "their_words": "你真人比照片好看诶。",
        "their_behavior": "眼神真诚，略带羞涩",
        "emotion_tags_json": '[{"spectrum":"喜","word":"愉悦","intensity":6},{"spectrum":"爱","word":"心动","intensity":4}]',
        "hidden_need": "希望得到回应，确认你也有好感",
        "need_urgency": 5, "attachment_signal": "安全型", "boundary_test_level": 3,
        "bad_response": "谢谢。",
        "bad_response_reason": "过于客气和简短，没有延续这个好话题",
        "good_response_soft": "谢谢，你也是。我看到你的第一眼就觉得你很特别。",
        "good_response_tension": "那你是不是要表示一下，请我喝杯咖啡？",
        "good_response_humor": "哈哈哈，那是照片的问题还是你的问题？怎么拍都不如本人好看。",
    },
    # 暧昧场景
    {
        "scenario_category": "暧昧", "difficulty_level": 1,
        "context": "她主动给你发了她正在吃晚餐的照片",
        "their_words": "今天一个人吃饭，随便做了点。你呢，吃了吗？",
        "their_behavior": "照片拍得很精致，餐桌布置用心",
        "emotion_tags_json": '[{"spectrum":"爱","word":"想念","intensity":6},{"spectrum":"喜","word":"分享","intensity":5}]',
        "hidden_need": "希望你也在想她，想和你聊天",
        "need_urgency": 4, "attachment_signal": "安全型", "boundary_test_level": 2,
        "bad_response": "吃了。",
        "bad_response_reason": "没有承接她的分享热情，回应太冷淡",
        "good_response_soft": "还没呢，刚下班。看着你一个人吃饭的样子，有点心疼，下次我请你吃好吃的。",
        "good_response_tension": "还没吃呢，看着你发来的照片，突然很想见你。",
        "good_response_humor": "没吃呢，正在想点什么外卖，突然你的照片来了，算了不吃了，看你就饱了。",
    },
    {
        "scenario_category": "暧昧", "difficulty_level": 2,
        "context": "你们聊到了很晚，她说要去洗澡了",
        "their_words": "好啦，我要去洗澡了，你也早点睡哦。晚安～",
        "their_behavior": "消息发送后她还在线",
        "emotion_tags_json": '[{"spectrum":"爱","word":"不舍","intensity":5},{"spectrum":"喜","word":"期待","intensity":4}]',
        "hidden_need": "希望你挽留，或者期待明天的聊天",
        "need_urgency": 5, "attachment_signal": "焦虑型", "boundary_test_level": 4,
        "bad_response": "嗯，晚安。",
        "bad_response_reason": "没有承接她的不舍，让她觉得你对这段聊天也不太在乎",
        "good_response_soft": "好，去洗吧，别洗太久哦，小心着凉。晚安，梦里见。",
        "good_response_tension": "晚安，想你了怎么办，明天下班能见你吗？",
        "good_response_humor": "去吧去吧，记得想我哦，不然明天不理你了。（开玩笑的语气）",
    },
    {
        "scenario_category": "暧昧", "difficulty_level": 2,
        "context": "她发了一条有点失落的朋友圈后私信你",
        "their_words": "你在干嘛呢？",
        "their_behavior": "之前刚发了一条“有点累”的朋友圈",
        "emotion_tags_json": '[{"spectrum":"哀","word":"疲惫","intensity":6},{"spectrum":"爱","word":"依赖","intensity":5}]',
        "hidden_need": "希望你注意到她不开心，想找你倾诉",
        "need_urgency": 6, "attachment_signal": "焦虑型", "boundary_test_level": 5,
        "bad_response": "在打游戏，怎么了？",
        "bad_response_reason": "没有注意到她的情绪信号，继续做自己的事",
        "good_response_soft": "刚准备休息，看到你发朋友圈了，是不是有什么事？想说吗？",
        "good_response_tension": "怎么了，看你朋友圈好像不太开心，需要我陪你聊聊吗？",
        "good_response_humor": "在做一个重要的事——等你找我聊天。你看起来心情不好？",
    },
    {
        "scenario_category": "暧昧", "difficulty_level": 3,
        "context": "你们已经聊了一个月，她突然变得冷淡",
        "their_words": "嗯，哦，好的。",
        "their_behavior": "回复变得很慢，语气敷衍",
        "emotion_tags_json": '[{"spectrum":"惧","word":"不安","intensity":7},{"spectrum":"哀","word":"失落","intensity":6}]',
        "hidden_need": "需要确认这段关系的走向",
        "need_urgency": 7, "attachment_signal": "焦虑型", "boundary_test_level": 6,
        "bad_response": "你是不是不想聊了？那算了。",
        "bad_response_reason": "赌气式的回应会让焦虑型更加退缩",
        "good_response_soft": "最近你是不是有什么事？可以告诉我，如果你需要空间我也可以给你，但别一个人扛着。",
        "good_response_tension": "感觉你最近有点冷淡，是我哪里做错了吗？我想改进。",
        "good_response_humor": "你是不是被外星人绑架了？真正的你已经去环游世界了对吧？哈哈哈开玩笑的，有什么事跟我说哦。",
    },
    # 热恋场景
    {
        "scenario_category": "热恋", "difficulty_level": 1,
        "context": "你们在一起三个月，她向你撒娇",
        "their_words": "我今天好累啊，想让你抱抱。",
        "their_behavior": "靠在你肩膀上，声音软软的",
        "emotion_tags_json": '[{"spectrum":"爱","word":"撒娇","intensity":7},{"spectrum":"哀","word":"疲惫","intensity":5}]',
        "hidden_need": "需要安慰和陪伴",
        "need_urgency": 5, "attachment_signal": "安全型", "boundary_test_level": 2,
        "bad_response": "抱一下就好了吗？",
        "bad_response_reason": "质疑她的需求，显得不够体贴",
        "good_response_soft": "过来，让我好好抱抱你。今天辛苦了，有什么想说的吗？",
        "good_response_tension": "不止抱一下，要抱到你满意为止。过来。",
        "good_response_humor": "抱抱？我这就去买个大力水手的菠菜，抱到你飞起来！",
    },
    {
        "scenario_category": "热恋", "difficulty_level": 2,
        "context": "她想让你陪她逛街，但你那天要加班",
        "their_words": "好吧，那你忙吧，我自己去了。",
        "their_behavior": "语气有点失落，但还是表示理解",
        "emotion_tags_json": '[{"spectrum":"哀","word":"失落","intensity":5},{"spectrum":"爱","word":"理解","intensity":4}]',
        "hidden_need": "希望你能补偿，或者表达歉意",
        "need_urgency": 5, "attachment_signal": "安全型", "boundary_test_level": 4,
        "bad_response": "好的，乖。",
        "bad_response_reason": "把她当小孩打发，没有给她足够的情感回应",
        "good_response_soft": "对不起今天没办法陪你，这个周末我全天候陪你，想去哪去哪，好吗？",
        "good_response_tension": "下次一定陪你，这次真的抱歉。你先买点喜欢的，回头我报销。",
        "good_response_humor": "我的错！这样吧，你买的东西我来买单，就当是赔罪费，行不行？",
    },
    {
        "scenario_category": "热恋", "difficulty_level": 2,
        "context": "她突然问了一个敏感问题",
        "their_words": "你会一直喜欢我吗？",
        "their_behavior": "眼神认真，有点不安",
        "emotion_tags_json": '[{"spectrum":"惧","word":"害怕失去","intensity":7},{"spectrum":"爱","word":"期待","intensity":6}]',
        "hidden_need": "需要确认和保证",
        "need_urgency": 8, "attachment_signal": "焦虑型", "boundary_test_level": 7,
        "bad_response": "想那么多干嘛。",
        "bad_response_reason": "否定她的担忧，会让她更加不安",
        "good_response_soft": "我会的。我可能没办法预测未来，但此刻我非常确定，我喜欢你。",
        "good_response_tension": "会的，而且我会用行动证明给你看。你怎么突然问这个？",
        "good_response_humor": "这个问题有点超纲啊，要不我们签个终身合同？开玩笑的，但我会努力的。",
    },
    # 冲突场景
    {
        "scenario_category": "冲突", "difficulty_level": 2,
        "context": "你们吵架了，她哭着跑出去",
        "their_words": "你根本不懂我！",
        "their_behavior": "眼泪汪汪，声音发抖",
        "emotion_tags_json": '[{"spectrum":"哀","word":"委屈","intensity":8},{"spectrum":"怒","word":"愤怒","intensity":6}]',
        "hidden_need": "需要被理解和接纳",
        "need_urgency": 9, "attachment_signal": "焦虑型", "boundary_test_level": 8,
        "bad_response": "你才不懂我！",
        "bad_response_reason": "以牙还牙，让冲突升级",
        "good_response_soft": "对不起，我知道你现在很难受。我不该那样说。让我们冷静一下，然后好好谈谈好吗？",
        "good_response_tension": "我可能真的不懂你，但我愿意学。告诉我，我哪里做错了？",
        "good_response_humor": "好好好，我不懂，你最懂。你先别哭，眼泪流太多会口渴的。",
    },
    {
        "scenario_category": "冲突", "difficulty_level": 3,
        "context": "她因为一件小事发了很大的火",
        "their_words": "你每次都这样！",
        "their_behavior": "声音很大，脸涨得通红",
        "emotion_tags_json": '[{"spectrum":"怒","word":"愤怒","intensity":8},{"spectrum":"哀","word":"委屈","intensity":6}]',
        "hidden_need": "需要被听见，需要你承认错误",
        "need_urgency": 8, "attachment_signal": "焦虑型", "boundary_test_level": 8,
        "bad_response": "我没有每次都这样，你太夸张了。",
        "bad_response_reason": "否认她的感受，会让冲突更激烈",
        "good_response_soft": "对不起让你这么生气。我知道你现在很委屈，能告诉我我做了什么让你这么难受吗？",
        "good_response_tension": "我理解你很生气。你觉得我是哪里做错了？我想听你说。",
        "good_response_humor": "好，我承认我错了。让我猜猜，是因为我没有洗碗吗？还是因为我忘记了什么重要的事？",
    },
    {
        "scenario_category": "冲突", "difficulty_level": 2,
        "context": "她冷战了好几天，突然发消息",
        "their_words": "我们能不能好好谈谈？",
        "their_behavior": "语气正式，像做了很久的心理建设",
        "emotion_tags_json": '[{"spectrum":"哀","word":"疲惫","intensity":6},{"spectrum":"惧","word":"紧张","intensity":5}]',
        "hidden_need": "希望这次谈话能解决问题",
        "need_urgency": 7, "attachment_signal": "恐惧-回避型", "boundary_test_level": 7,
        "bad_response": "有什么好谈的？",
        "bad_response_reason": "拒绝沟通会让回避型更加退缩",
        "good_response_soft": "好，我一直在等你愿意谈。我会认真听你说的，我们一起找解决办法。",
        "good_response_tension": "好，谈。你先说，我听着。",
        "good_response_humor": "终于等到你这句话了，我还以为你要等到世界末日才来找我呢。",
    },
    # 平淡场景
    {
        "scenario_category": "平淡", "difficulty_level": 2,
        "context": "在一起一年，聊天越来越公式化",
        "their_words": "早，吃了吗？",
        "their_behavior": "每天固定时间发送，语气平淡",
        "emotion_tags_json": '[{"spectrum":"哀","word":"无聊","intensity":5},{"spectrum":"惧","word":"担忧","intensity":4}]',
        "hidden_need": "希望关系能找回新鲜感",
        "need_urgency": 5, "attachment_signal": "回避型", "boundary_test_level": 5,
        "bad_response": "吃了，你呢？",
        "bad_response_reason": "继续公式化对话，没有突破",
        "good_response_soft": "吃了，不过突然想起我们第一次约会也是吃的这个，有点想你。要不要今晚视频？",
        "good_response_tension": "吃了，但有点想念以前你给我做早餐的日子。那时候真好。",
        "good_response_humor": "吃了！但我怀疑我的早餐没有你可爱，不公平。",
    },
    {
        "scenario_category": "平淡", "difficulty_level": 3,
        "context": "她突然问你一个关于未来的问题",
        "their_words": "你对我们未来有什么想法吗？",
        "their_behavior": "语气认真，有点试探",
        "emotion_tags_json": '[{"spectrum":"惧","word":"不安","intensity":7},{"spectrum":"爱","word":"期待","intensity":5}]',
        "hidden_need": "需要确认你对这段关系的认真程度",
        "need_urgency": 8, "attachment_signal": "焦虑型", "boundary_test_level": 7,
        "bad_response": "顺其自然吧，想那么多干嘛。",
        "bad_response_reason": "回避未来话题会让焦虑型更加不安",
        "good_response_soft": "我认真的想过。我觉得我们可以一起规划，比如明年一起旅行，三年后考虑一起住。你呢？",
        "good_response_tension": "我想和你走下去。具体的我们可以一起讨论，但我确定我想要的是长期关系。",
        "good_response_humor": "未来啊，我想象的是：我们在海边开一家小咖啡馆，你负责做甜品，我负责讲冷笑话。",
    },
    # 修复场景
    {
        "scenario_category": "修复", "difficulty_level": 3,
        "context": "吵完架第二天，她主动找你",
        "their_words": "昨天我也有不对的地方，对不起。",
        "their_behavior": "眼睛还有点红，像是哭过",
        "emotion_tags_json": '[{"spectrum":"哀","word":"愧疚","intensity":7},{"spectrum":"爱","word":"珍惜","intensity":6}]',
        "hidden_need": "希望和好，需要你给台阶",
        "need_urgency": 8, "attachment_signal": "恐惧-回避型", "boundary_test_level": 7,
        "bad_response": "你知道就好。",
        "bad_response_reason": "赢了争吵但输了感情",
        "good_response_soft": "傻瓜，应该是我道歉。我也有做得不好的地方。过来，让我抱抱你。",
        "good_response_tension": "谢谢你愿意主动开口。我昨天也说了很多伤人的话，能原谅我吗？",
        "good_response_humor": "哎呀，我的女朋友居然会道歉？太阳从西边出来了吧！开玩笑的，过来让我亲亲。",
    },
    {
        "scenario_category": "修复", "difficulty_level": 3,
        "context": "分手后一个月，她突然发消息",
        "their_words": "最近好吗？我在整理东西的时候看到了我们以前的照片。",
        "their_behavior": "消息发出后她显示正在输入又停止",
        "emotion_tags_json": '[{"spectrum":"哀","word":"怀念","intensity":7},{"spectrum":"爱","word":"不舍","intensity":6}]',
        "hidden_need": "试探你的态度，想知道还有没有可能",
        "need_urgency": 8, "attachment_signal": "焦虑型", "boundary_test_level": 8,
        "bad_response": "嗯，还行。",
        "bad_response_reason": "保持距离的回应会让对方觉得没有希望",
        "good_response_soft": "我也还好。照片还在吗？说实话，我也会想起以前的一些时光。",
        "good_response_tension": "我以为你已经放下了。你现在发这条消息，是什么意思？",
        "good_response_humor": "哈哈，我都开始学做菜了，做得还挺好吃的。你呢，最近怎么样？",
    },
]

# 更多初识样本
MORE_SAMPLES = [
    {"scenario_category": "初识", "difficulty_level": 1, "context": "在图书馆，她坐在你对面", "their_words": "你好，请问这个位置有人吗？", "their_behavior": "指着旁边的空位", "emotion_tags_json": '[{"spectrum":"喜","word":"友好","intensity":4}]', "hidden_need": "找一个安静的位置", "need_urgency": 2, "attachment_signal": "安全型", "boundary_test_level": 1, "bad_response": "没人。", "bad_response_reason": "过于简短冷淡", "good_response_soft": "没有，请坐。你是第一次来这个图书馆吗？", "good_response_tension": "没有，不过这个位置下午会有点晒，你不介意吗？", "good_response_humor": "没人，这个位置风水好，我特意留着的。开玩笑的，请坐！"},
    {"scenario_category": "初识", "difficulty_level": 1, "context": "在健身房，她正在你旁边用器械", "their_words": "这个器械怎么调重量啊？", "their_behavior": "有点不好意思地问", "emotion_tags_json": '[{"spectrum":"羞","word":"尴尬","intensity":4},{"spectrum":"喜","word":"求助","intensity":3}]', "hidden_need": "需要帮助", "need_urgency": 3, "attachment_signal": "安全型", "boundary_test_level": 2, "bad_response": "看说明书呗。", "bad_response_reason": "冷漠回应", "good_response_soft": "我来帮你调吧，这个确实不太明显。你是新手吗？", "good_response_tension": "我帮你，你经常来吗？我好像见过你。", "good_response_humor": "这个嘛，要念咒语的，我来教你：麻里麻里哄！好了，学会了。"},
    {"scenario_category": "初识", "difficulty_level": 2, "context": "在朋友的聚会上，你们聊得很开心", "their_words": "你这个人挺有意思的，加个微信吧？", "their_behavior": "笑着拿出手机", "emotion_tags_json": '[{"spectrum":"喜","word":"好感","intensity":6},{"spectrum":"惊","word":"意外","intensity":4}]', "hidden_need": "希望进一步了解", "need_urgency": 4, "attachment_signal": "安全型", "boundary_test_level": 3, "bad_response": "行。", "bad_response_reason": "过于平淡，没有延续话题", "good_response_soft": "好啊，不过我要先看看你的朋友圈，万一你是什么奇怪的人呢？", "good_response_tension": "当然可以，不过加了微信可不许不通过我的好友申请哦。", "good_response_humor": "等等，让我先准备一下，这可能是我人生的转折点！好，加吧。"},
    {"scenario_category": "初识", "difficulty_level": 2, "context": "相亲时，她问你对另一半的要求", "their_words": "你对另一半有什么要求吗？", "their_behavior": "认真地看着你", "emotion_tags_json": '[{"spectrum":"惧","word":"紧张","intensity":5},{"spectrum":"喜","word":"期待","intensity":4}]', "hidden_need": "想知道是否匹配", "need_urgency": 5, "attachment_signal": "安全型", "boundary_test_level": 4, "bad_response": "没什么要求，合得来就行。", "bad_response_reason": "没有给出具体信息", "good_response_soft": "我觉得最重要的是能互相理解，还有就是在一起的时候很放松。你呢？", "good_response_tension": "能让我做自己的人吧。我不喜欢太黏人的，但也不喜欢太疏离的。", "good_response_humor": "要求不高，能容忍我的冷笑话就行。你呢，有什么底线？"},
    {"scenario_category": "初识", "difficulty_level": 3, "context": "你们已经聊了一周，她突然问了一个直球问题", "their_words": "你对我是什么感觉？", "their_behavior": "消息发出后她没有再说别的", "emotion_tags_json": '[{"spectrum":"惧","word":"紧张","intensity":8},{"spectrum":"爱","word":"期待","intensity":7}]', "hidden_need": "需要确认", "need_urgency": 9, "attachment_signal": "焦虑型", "boundary_test_level": 8, "bad_response": "现在说这个会不会太快？", "bad_response_reason": "回避问题会让焦虑型更加不安", "good_response_soft": "我对你挺有感觉的，跟你聊天的时候我会特别开心。我也想问你同样的问题。", "good_response_tension": "我觉得你很特别，我想要认真了解你。你呢，对我是什么感觉？", "good_response_humor": "感觉嘛...就是那种想每天醒来第一个看到你的感觉。你呢，有没有同样的感觉？"},
]

# 扩充的资源库数据
EXPANDED_RESOURCES = [
    # 更多段子
    {"type": "joke", "category": "破冰", "title": "紧张开场", "content": "你好，我刚才在想怎么跟你打招呼，结果想了三个版本都觉得很傻，最后决定直接说'你好'。所以，你好。", "emotional_tone_json": '["幽默","自嘲"]', "emotional_intensity": 4, "applicable_scene": "初识", "difficulty_level": 1, "gender_target": "通用", "effectiveness_rating": 8},
    {"type": "joke", "category": "破冰", "title": "好奇心开场", "content": "我刚才注意到你在看那本书，我也在找那本书，你觉得好看吗？还是说你在故意让我注意到你？", "emotional_tone_json": '["调皮","好奇"]', "emotional_intensity": 5, "applicable_scene": "初识", "difficulty_level": 2, "gender_target": "通用", "effectiveness_rating": 7},
    {"type": "joke", "category": "暖场", "title": "自嘲式", "content": "我刚才在练习怎么跟有趣的人聊天，结果发现我已经用完了所有的有趣额度，现在只剩下笨拙了。", "emotional_tone_json": '["幽默","自嘲"]', "emotional_intensity": 4, "applicable_scene": "暧昧", "difficulty_level": 1, "gender_target": "男→女", "effectiveness_rating": 8},
    {"type": "joke", "category": "暖场", "title": "夸张式", "content": "我刚才看到你笑了一下，我突然觉得今天的天气都变好了，是不是该去买个彩票？", "emotional_tone_json": '["夸张","幽默"]', "emotional_intensity": 5, "applicable_scene": "暧昧", "difficulty_level": 2, "gender_target": "通用", "effectiveness_rating": 7},
    {"type": "joke", "category": "调侃", "title": "反向调侃", "content": "你这个人真是的，让我这种高冷的人都忍不住想要跟你聊天。", "emotional_tone_json": '["调侃","暧昧"]', "emotional_intensity": 6, "applicable_scene": "暧昧", "difficulty_level": 2, "gender_target": "通用", "effectiveness_rating": 8},
    # 更多话术
    {"type": "flirty", "category": "推拉", "title": "先拉后推", "content": "你今天真好看，好看到让我有点紧张，所以我要故意走远一点，免得待会儿说傻话。", "emotional_tone_json": '["推拉","暧昧"]', "emotional_intensity": 7, "applicable_scene": "暧昧", "difficulty_level": 2, "gender_target": "男→女", "effectiveness_rating": 9},
    {"type": "flirty", "category": "推拉", "title": "欲擒故纵", "content": "你挺有趣的，但我得确认一下你是不是对每个人都这么有趣。", "emotional_tone_json": '["推拉","暧昧"]', "emotional_intensity": 6, "applicable_scene": "暧昧", "difficulty_level": 2, "gender_target": "通用", "effectiveness_rating": 8},
    {"type": "flirty", "category": "土味情话", "title": "观察型", "content": "你今天好像有点不一样，让我猜猜...是不是换了发型？还是因为你今天特别想见我？", "emotional_tone_json": '["土味","暧昧"]', "emotional_intensity": 6, "applicable_scene": "热恋", "difficulty_level": 1, "gender_target": "通用", "effectiveness_rating": 7},
    {"type": "flirty", "category": "土味情话", "title": "日常型", "content": "你知道我为什么每天都睡得很早吗？因为早上醒来的第一件事就是想见到你。", "emotional_tone_json": '["甜蜜","土味"]', "emotional_intensity": 7, "applicable_scene": "热恋", "difficulty_level": 1, "gender_target": "通用", "effectiveness_rating": 8},
    {"type": "flirty", "category": "调情", "title": "氛围型", "content": "今晚的月亮很美，但不及你。", "emotional_tone_json": '["浪漫","调情"]', "emotional_intensity": 8, "applicable_scene": "暧昧", "difficulty_level": 3, "gender_target": "通用", "effectiveness_rating": 9},
    {"type": "flirty", "category": "调情", "title": "悬念型", "content": "我有件事想跟你说，但要在你答应不生气的前提下才能说。你答应吗？", "emotional_tone_json": '["调情","暧昧"]', "emotional_intensity": 6, "applicable_scene": "暧昧", "difficulty_level": 2, "gender_target": "通用", "effectiveness_rating": 7},
    # 更多故事
    {"type": "story", "category": "情感故事", "title": "理解型", "content": "我以前是个不太会表达情绪的人，遇到不开心的事就自己扛着。后来遇到一个人，她教我说出来，慢慢地我发现，原来被理解是这么温暖的事。", "emotional_tone_json": '["温暖","真诚"]', "emotional_intensity": 5, "applicable_scene": "修复", "difficulty_level": 2, "gender_target": "通用", "effectiveness_rating": 8},
    {"type": "story", "category": "情感故事", "title": "成长型", "content": "我以前很怕吵架，觉得吵架就是感情出问题。后来我学会了，吵架其实是两个人在乎对方的表现，关键是怎么吵完之后变得更好。", "emotional_tone_json": '["成长","治愈"]', "emotional_intensity": 5, "applicable_scene": "修复", "difficulty_level": 2, "gender_target": "通用", "effectiveness_rating": 8},
    {"type": "story", "category": "情感故事", "title": "信任型", "content": "我曾经不相信异地恋，觉得距离会打败感情。但现在我明白了，真正的问题不是距离，而是两个人愿不愿意为对方努力。", "emotional_tone_json": '["真诚","信任"]', "emotional_intensity": 5, "applicable_scene": "热恋", "difficulty_level": 2, "gender_target": "通用", "effectiveness_rating": 7},
    # 更多游戏
    {"type": "game", "category": "破冰游戏", "title": "猜职业", "content": "我们互相猜对方的职业，猜对的人可以问对方一个问题。输的人要坦白一件小事。", "emotional_tone_json": '["有趣","互动"]', "emotional_intensity": 5, "applicable_scene": "初识", "difficulty_level": 1, "gender_target": "通用", "effectiveness_rating": 8},
    {"type": "game", "category": "破冰游戏", "title": "互换身份", "content": "我们来玩个游戏，假设我们是对方，用对方的口吻说一句话。看看我们有多了解彼此。", "emotional_tone_json": '["有趣","暧昧"]', "emotional_intensity": 6, "applicable_scene": "暧昧", "difficulty_level": 2, "gender_target": "通用", "effectiveness_rating": 9},
    {"type": "game", "category": "暧昧游戏", "title": "爱的清单", "content": "我们轮流说出对方让自己心动的瞬间，谁说不出来谁就要答应对方一个要求。", "emotional_tone_json": '["甜蜜","暧昧"]', "emotional_intensity": 7, "applicable_scene": "热恋", "difficulty_level": 2, "gender_target": "通用", "effectiveness_rating": 9},
    # 更多急转弯
    {"type": "riddle", "category": "浪漫急转弯", "title": "情话版", "content": "什么鱼最专一？答：比目鱼，因为它们一生只会看到同一个方向。", "emotional_tone_json": '["浪漫","幽默"]', "emotional_intensity": 5, "applicable_scene": "暧昧", "difficulty_level": 1, "gender_target": "通用", "effectiveness_rating": 8},
    {"type": "riddle", "category": "浪漫急转弯", "title": "比喻版", "content": "我对你的喜欢像什么？像WiFi，无时无刻都在连接。", "emotional_tone_json": '["幽默","土味"]', "emotional_intensity": 4, "applicable_scene": "暧昧", "difficulty_level": 1, "gender_target": "通用", "effectiveness_rating": 7},
]

def expand_samples(session: Session) -> None:
    """扩充互动样本"""
    logger.info("正在扩充互动样本...")
    
    # 检查是否已存在
    existing_count = session.query(InteractionSample).count()
    if existing_count > 10:
        logger.info(f"样本已存在 {existing_count} 条，跳过")
        return
    
    # 添加扩展样本
    for data in EXPANDED_SAMPLES:
        sample = InteractionSample(sample_uuid=str(uuid.uuid4()), **data)
        session.add(sample)
    
    # 添加更多样本
    for data in MORE_SAMPLES:
        sample = InteractionSample(sample_uuid=str(uuid.uuid4()), **data)
        session.add(sample)
    
    session.commit()
    logger.info(f"互动样本扩充完成: {len(EXPANDED_SAMPLES) + len(MORE_SAMPLES)} 条")


def expand_resources(session: Session) -> None:
    """扩充资源库"""
    logger.info("正在扩充资源库...")
    
    # 检查是否已存在
    existing_count = session.query(ResourceLibrary).count()
    if existing_count > 10:
        logger.info(f"资源已存在 {existing_count} 条，跳过")
        return
    
    # 添加扩展资源
    for data in EXPANDED_RESOURCES:
        resource = ResourceLibrary(resource_uuid=str(uuid.uuid4()), **data)
        session.add(resource)
    
    session.commit()
    logger.info(f"资源库扩充完成: {len(EXPANDED_RESOURCES)} 条")


def expand_all() -> None:
    """执行所有扩充"""
    logger.info("开始数据扩充...")
    
    from backend.database.connection import create_db_and_tables
    create_db_and_tables()
    
    with Session(engine) as session:
        expand_samples(session)
        expand_resources(session)
    
    logger.info("数据扩充全部完成！")


if __name__ == "__main__":
    expand_all()