-- ========================================
-- 微关系动力学全息系统 - 数据库Schema
-- 版本: 1.0.0
-- 日期: 2026-05-19
-- ========================================

-- ========================================
-- 1. 用户画像表
-- ========================================
CREATE TABLE IF NOT EXISTS user_profile (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name VARCHAR(50),
    avatar_url TEXT,
    
    -- 人格特质
    personality_type VARCHAR(20), -- INTJ/INFP/ENFP/ESFJ等
    personality_desc TEXT,
    
    -- 依恋风格
    attachment_style VARCHAR(20), -- 安全型/焦虑型/回避型
    attachment_desc TEXT,
    
    -- 爱的语言
    love_language VARCHAR(50), -- 肯定的话语/精心时刻/礼物/服务的行动/身体接触
    love_language_desc TEXT,
    
    -- 沟通风格
    communication_style VARCHAR(30), -- 直接型/委婉型/分析型/感受型
    communication_desc TEXT,
    
    -- 能力指标 (1-10)
    emotional_granularity INTEGER DEFAULT 5, -- 情绪颗粒度
    perception_ability INTEGER DEFAULT 5, -- 感知能力
    interaction_confidence INTEGER DEFAULT 5, -- 互动信心
    empathy_accuracy INTEGER DEFAULT 5, -- 共情准确度
    expression_warmth INTEGER DEFAULT 5, -- 表达温度
    
    -- 当前阶段
    current_phase INTEGER DEFAULT 0, -- 0-8阶
    learning_speed VARCHAR(20), -- 快/中/慢
    main_blockers TEXT, -- 主要卡点
    
    -- 时间戳
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- ========================================
-- 2. 情绪谱系表
-- ========================================
CREATE TABLE IF NOT EXISTS emotion_spectra (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    category VARCHAR(20) NOT NULL, -- 喜/怒/哀/惧/爱/惊/羞
    level INTEGER NOT NULL, -- 1-5强度
    name VARCHAR(50) NOT NULL,
    description TEXT,
    synonyms TEXT, -- 同义词列表
    associated_behaviors TEXT, -- 相关行为
    physical_signs TEXT, -- 身体表现
    response_strategy TEXT -- 应对策略
);

-- 插入七大谱系数据
INSERT INTO emotion_spectra (category, level, name, description, synonyms, response_strategy) VALUES
-- 喜
('喜', 1, '满足', '基本满足感', '还行,还好,过得去', '可以简单回应'),
('喜', 2, '愉悦', '比满足更进一步', '开心,高兴,不错', '分享她的愉悦'),
('喜', 3, '雀跃', '轻快的开心', '兴奋,雀跃,心情好', '积极回应'),
('喜', 4, '兴奋', '较强的积极情绪', '很兴奋,激动,期待', '同频共振'),
('喜', 5, '狂喜', '极度的快乐', '太开心了,幸福,高潮', '共同庆祝'),
-- 怒
('怒', 1, '微烦', '轻微的不悦', '有点烦,不太舒服', '忽略或轻问'),
('怒', 2, '烦躁', '明显的不耐烦', '烦,闹心,烦躁', '安抚情绪'),
('怒', 3, '恼火', '较强烈的不满', '很烦,恼火,生气', '先降强度'),
('怒', 4, '愤怒', '强烈的敌意', '愤怒,火大,气死了', '先稳定再处理'),
('怒', 5, '暴怒', '极度的愤怒', '暴怒,崩溃,想打人', '完全稳定,暂不解决'),
-- 哀
('哀', 1, '失落', '轻微的悲伤', '有点失落,遗憾', '轻问'),
('哀', 2, '悲伤', '明显的伤心', '难过,伤心,悲伤', '共情陪伴'),
('哀', 3, '沮丧', '低落无力的感觉', '沮丧,泄气,灰心', '鼓励支持'),
('哀', 4, '绝望', '强烈的无助感', '绝望,没希望,崩溃', '先稳定情绪'),
('哀', 5, '崩溃', '极度的悲伤', '崩溃,哭,无法承受', '完全陪伴,不解决问题'),
-- 惧
('惧', 1, '紧张', '轻微的不安', '有点紧张,担心', '安抚'),
('惧', 2, '焦虑', '明显的不确定', '焦虑,不安,害怕', '给确定性'),
('惧', 3, '恐惧', '较强的害怕', '害怕,恐惧,担心', '安全感建立'),
('惧', 4, '惊恐', '强烈的恐惧', '惊恐,慌张,害怕极了', '先稳定'),
('惧', 5, '恐慌', '极度的恐惧', '恐慌,吓坏了,完全失控', '完全稳定'),
-- 爱
('爱', 1, '好感', '基本的好感', '还行,不错,有好感', '正向回应'),
('爱', 2, '依恋', '想要靠近的感觉', '喜欢,依恋,想见', '表达在意'),
('爱', 3, '温柔', '柔和的情感', '温柔,心软,心动', '温柔回应'),
('爱', 4, '心动', '心跳加速的感觉', '心动,心跳,小鹿乱撞', '浪漫回应'),
('爱', 5, '痴迷', '极度的喜欢', '痴迷,疯狂,完全沦陷', '真诚表达'),
-- 惊
('惊', 1, '意外', '轻微的惊讶', '有点意外,没想到', '正常回应'),
('惊', 2, '惊讶', '明显的意外', '惊讶,没想到,吃惊', '共情惊讶'),
('惊', 3, '震惊', '较强的冲击', '震惊,惊呆了,不敢相信', '给时间消化'),
('惊', 4, '目瞪口呆', '非常震惊', '目瞪口呆,彻底震惊', '先稳定'),
('惊', 5, '惊骇', '极度的震惊', '惊骇,完全吓到了', '完全稳定'),
-- 羞
('羞', 1, '不好意思', '轻微的尴尬', '有点不好意思,尴尬', '忽略'),
('羞', 2, '惭愧', '有些不好意思', '惭愧,不好意思,脸红', '安慰'),
('羞', 3, '羞耻', '较强的尴尬感', '羞耻,丢脸,不好意思', '共情'),
('羞', 4, '无地自容', '非常尴尬', '无地自容,太丢人了', '接纳'),
('羞', 5, '羞辱', '极度的羞耻', '羞辱,彻底崩溃,无脸见人', '完全接纳');

-- ========================================
-- 3. 混合情绪表
-- ========================================
CREATE TABLE IF NOT EXISTS mixed_emotions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name VARCHAR(50) NOT NULL,
    component_1 VARCHAR(30),
    component_2 VARCHAR(30),
    description TEXT,
    common_scenarios TEXT,
    identification_tips TEXT,
    response_approach TEXT
);

INSERT INTO mixed_emotions (name, component_1, component_2, description, common_scenarios, response_approach) VALUES
('酸楚', '羡慕', '委屈', '看到别人有自己没有时的复杂感受', '看到别人成功/得到/拥有自己想要的', '先共情「这确实让人难受」'),
('纠结', '想要', '害怕', '面临选择时的矛盾心理', '做决定/面临风险/不确定', '帮她理清「你想要什么？害怕什么？」'),
('释然', '放下', '轻松', '终于结束一段关系后的感受', '分手后/完成一件大事后/结束一段压力', '陪伴但不追问'),
('心酸', '心疼', '无奈', '看到在乎的人受苦', '看到亲人/爱人受苦', '先陪伴「我在这」'),
('忐忑', '期待', '不安', '等待重要结果时的复杂心情', '等面试结果/考试结果/表白回应', '给安慰「无论结果如何我都在」'),
('五味杂陈', '多种情绪', '混合', '复杂情绪交织', '重大事件/人生转折', '给空间「慢慢来」'),
('百感交集', '喜', '悲+怒', '重大事件后的复杂感受', '婚礼/葬礼/离别/重逢', '陪伴「我理解这很复杂」'),
('患得患失', '渴望', '恐惧失去', '在乎对方时的不确定感', '恋爱初期/重要关系中', '给安全感「我在」');

-- ========================================
-- 4. 场景样本库
-- ========================================
CREATE TABLE IF NOT EXISTS scenario_library (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    category VARCHAR(50), -- 信息/情绪/感受/看见/欣赏/理解/爱/被爱
    subcategory VARCHAR(50),
    
    -- 场景描述
    situation TEXT NOT NULL, -- 她说的话/做的事
    context TEXT, -- 背景/环境
    her_words TEXT, -- 她的原话
    her_behavior TEXT, -- 她的行为
    
    -- 情绪分析
    her_emotion VARCHAR(100), -- 可能的情绪
    her_emotion_intensity INTEGER, -- 1-10强度
    her_emotion_secondary VARCHAR(100), -- 次要情绪
    emotion_confidence FLOAT, -- 准确度置信度
    
    -- 需求分析
    her_need VARCHAR(100), -- 她真正的需求
    surface_need VARCHAR(100), -- 表面需求
    deep_need VARCHAR(100), -- 深层需求
    
    -- 回应对比
    wrong_response TEXT, -- 常见错误回应
    wrong_reason TEXT, -- 为什么错
    ideal_response TEXT, -- 理想回应
    ideal_response_style VARCHAR(30), -- 柔和版/张力版
    
    -- 效果分析
    emotional_flow_wrong TEXT, -- 错误回应的情绪流动
    emotional_flow_ideal TEXT, -- 理想回应的情绪流动
    
    -- 学习点
    analysis_points TEXT,
    key_insight TEXT,
    tool_used VARCHAR(50), -- 使用的工具
    
    -- 分类标签
    tags TEXT,
    difficulty_level INTEGER -- 1-5难度
);

-- 插入场景样本
INSERT INTO scenario_library (category, situation, her_emotion, her_emotion_intensity, her_need, wrong_response, ideal_response, tool_used, difficulty_level) VALUES
-- 信息阶
('信息', '「在吗？」', '有话想说', 3, '希望得到回应', '「在」', '「在呢，怎么了？」', '沟通', 1),
('信息', '「你在干嘛？」', '好奇/想聊天', 2, '想要连接', '「没干嘛」', '「在想你啊，你呢？」', '沟通', 1),
('信息', '「今天吃了什么？」', '日常关心', 2, '想要分享', '「随便吃了点」', '「吃了碗面，你呢？今天吃了什么好吃的？」', '沟通', 1),

-- 情绪阶
('情绪', '「唉」', '烦躁/累/委屈', 5, '被倾听', '「怎么了？」', '「听起来今天有点不太顺，想聊聊吗？」', '诗人', 2),
('情绪', '「烦死了」', '烦躁/愤怒', 6, '发泄', '「别烦了」', '「什么事让你这么烦？我听着。」', '共情', 2),
('情绪', '「好累啊」', '疲惫', 6, '被理解', '「那你早点休息」', '「听起来今天像背着一座山回来，发生什么了？」', '诗人', 2),
('情绪', '「算了，不说了」', '失望/委屈', 5, '想被挽留', '「好吧」', '「我感觉到你有点失望，是我说的话让你觉得没被理解吗？」', '共情', 3),

-- 感受阶
('感受', '「我没事」（明显不是）', '压抑/委屈', 6, '想被看穿', '「哦，那好吧」', '「我听到你说没事，但感觉你有点不一样。想说就说，不想说也没关系，我在这。」', '看见', 3),
('感受', '她突然沉默', '思考/压抑', 4, '给空间或轻问', '「你怎么不说话？」', '「不想说就先不说，我陪着你。」', '陪伴', 2),
('感受', '「你知道吗...」', '有话想说', 4, '想要表达', '「什么？」', '「我听着呢。」', '倾听', 2),

-- 看见阶
('看见', '她看手机又放下', '不确定/焦虑', 4, '需要确认', '「你老看手机干嘛」', '「手机响了吗？」', '侦探', 3),
('看见', '她抿了一下嘴', '压抑/紧张', 4, '被看见', '「你嘴怎么了？」', '「我注意到你抿了一下嘴，是不是有什么事压在心里？」', '侦探', 3),
('看见', '她眼睛红了', '感动/委屈', 5, '被理解', '「别哭啊」', '「我看到你眼睛红了，是什么事触动了你？」', '共情', 3),

-- 欣赏阶
('欣赏', '她做了一件事', '希望被认可', 4, '被欣赏', '「还行吧」', '「你刚才那样处理，既表达了立场又没有伤人，这很厉害。」', '欣赏', 3),
('欣赏', '她穿了新衣服', '希望被注意', 3, '被赞美', '「嗯」', '「你今天这条裙子很衬你，很有气质。」', '欣赏', 2),
('欣赏', '她帮了别人', '希望被认可', 4, '被欣赏', '「这是应该的」', '「你刚才帮那个人指路，很温暖，我觉得你是一个很善良的人。」', '欣赏', 3),

-- 理解阶
('理解', '她每次提妈妈就语速变快', '关系紧张', 6, '被理解', '「你妈妈怎么了？」', '「我注意到你每次提妈妈语速会变快，是不是有什么让你不太舒服的地方？」', '理解', 4),
('理解', '她总是在道歉', '害怕被责怪', 5, '被接纳', '「没关系」', '「我知道你不是故意的，这种事我也会忘。」', '接纳', 3),
('理解', '她迟到10分钟', '内疚', 4, '被理解', '「你怎么又迟到？」', '「路上堵了吧？没事，我也刚到。」', '共情', 2),

-- 爱阶
('爱', '她很脆弱', '需要安全感', 7, '被陪伴', '「别哭了」', '（安静陪着，轻轻拍拍她的背）', '陪伴', 3),
('爱', '她说「我好害怕」', '恐惧/不安', 7, '被保护', '「怕什么」', '「我在这，不管发生什么我都在。告诉我，你在怕什么？」', '安全感', 4),
('爱', '她需要空间', '需要独立', 4, '被尊重', '「你怎么了？为什么不理我？」', '「我感觉到你需要一点空间，没关系，我就在这，想找我说的时候我在。」', '边界', 3),

-- 被爱阶
('被爱', '她记得你的喜好', '表达爱意', 5, '被感谢', '「哦」', '「你还记得我不吃香菜，你真的很细心，谢谢你。」', '感谢', 2),
('被爱', '她给你准备了礼物', '表达爱意', 5, '被珍惜', '「不用这么麻烦」', '「你特意准备的这个，我真的很感动，谢谢你。」', '被爱', 2),
('被爱', '她帮你做了件事', '表达爱意', 4, '被感谢', '「不用管」', '「你帮我做了这些，我心里暖暖的，下次我也帮你。」', '回馈', 2);

-- ========================================
-- 5. 对话记录表
-- ========================================
CREATE TABLE IF NOT EXISTS conversation_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER,
    date DATETIME DEFAULT CURRENT_TIMESTAMP,
    
    -- 场景描述
    situation TEXT NOT NULL,
    her_words TEXT,
    her_behavior TEXT,
    context TEXT,
    
    -- 分析
    observed_clues TEXT, -- 观察到的线索
    emotion_hypothesis TEXT, -- 情绪假设
    hypothesis_probability TEXT, -- 假设概率
    verification_method TEXT, -- 验证方式
    verification_result TEXT, -- 验证结果
    
    -- 回应
    my_response TEXT,
    ideal_response TEXT,
    difference_analysis TEXT,
    
    -- 效果
    her_reaction TEXT,
    emotional_change TEXT,
    interaction_result TEXT, -- 成功/失败/部分成功
    
    -- 反思
    self_reflection TEXT,
    learned_points TEXT,
    improvement_plan TEXT,
    
    -- 评估
    tool_used VARCHAR(50),
    effectiveness_score INTEGER, -- 1-5
    speed_score INTEGER, -- 反应速度
    accuracy_score INTEGER, -- 准确度
    
    FOREIGN KEY (user_id) REFERENCES user_profile(id)
);

-- ========================================
-- 6. 能力成长追踪表
-- ========================================
CREATE TABLE IF NOT EXISTS ability_tracking (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER,
    date DATE NOT NULL,
    
    -- 反应延迟（秒）
    pause_time FLOAT,
    pause_time_target FLOAT DEFAULT 1.0,
    pause_time_score INTEGER, -- 1-5分
    
    -- 情绪颗粒度（当天使用的不同情绪词数量）
    emotion_words_used TEXT, -- 用过的情绪词
    emotion_words_count INTEGER,
    emotion_granularity_score INTEGER, -- 1-5分
    
    -- 观察能力（观察到的线索数量）
    clues_observed TEXT, -- 观察到的线索
    clues_count INTEGER,
    observation_score INTEGER, -- 1-5分
    
    -- 身体觉察（自我感知次数/小时）
    body_awareness_count INTEGER,
    body_awareness_score INTEGER, -- 1-5分
    
    -- 复盘质量
    review_nodes INTEGER, -- 复盘的节点数
    review_depth TEXT, -- 复盘深度
    review_quality_score INTEGER, -- 1-5分
    
    -- 综合得分
    overall_score FLOAT,
    
    -- 备注
    notes TEXT,
    
    FOREIGN KEY (user_id) REFERENCES user_profile(id)
);

-- ========================================
-- 7. 工具使用记录表
-- ========================================
CREATE TABLE IF NOT EXISTS tool_usage_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER,
    tool_name VARCHAR(50) NOT NULL, -- 侦探/诗人/5W2H/提问/沟通/心理/情感/人性/数据
    
    date DATETIME DEFAULT CURRENT_TIMESTAMP,
    situation TEXT,
    
    -- 输入
    input TEXT,
    observed_clues TEXT,
    hypothesis_list TEXT,
    
    -- 处理过程
    process TEXT,
    thinking_step TEXT,
    
    -- 输出
    output TEXT,
    response_used TEXT,
    
    -- 效果
    effectiveness INTEGER, -- 1-5
    her_reaction TEXT,
    learning_points TEXT,
    
    FOREIGN KEY (user_id) REFERENCES user_profile(id)
);

-- ========================================
-- 8. 样本库扩展表
-- ========================================
CREATE TABLE IF NOT EXISTS sample_library (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    category VARCHAR(50), -- 她他/自己/人性
    subcategory VARCHAR(50),
    
    question TEXT, -- 场景/问题
    emotion VARCHAR(100), -- 可能情绪
    emotion_intensity INTEGER, -- 强度1-10
    need VARCHAR(100), -- 需求
    
    -- 分析
    analysis TEXT,
    multiple_hypotheses TEXT, -- 多个假设
    response_strategy TEXT,
    
    -- 标签
    tags TEXT,
    difficulty_level INTEGER,
    
    -- 频率统计
    usage_count INTEGER DEFAULT 0,
    success_count INTEGER DEFAULT 0,
    success_rate FLOAT
);

-- 插入样本库扩展数据
INSERT INTO sample_library (category, question, emotion, need, analysis, difficulty_level) VALUES
-- 她/他的情绪样本
('她他', '她说「唉」', '烦躁/累/委屈', '被倾听', '叹气通常表示需要释放，可能是累了、烦了或委屈了', 1),
('她他', '她沉默', '压抑/思考', '给空间或轻问', '沉默可能是她在想事情，也可能是压抑某种情绪', 2),
('她他', '她突然客气', '防御', '降低压力', '突然客气可能是她在防御，避免被伤害', 2),
('她他', '她问「在吗」', '有话想说', '给开口机会', '她有话想说但不知道怎么开口', 1),
('她他', '她说「没事」', '压抑', '轻问确认', '「没事」很多时候不是真的没事', 2),
('她他', '她分享好消息', '希望被认可', '具体回应', '她希望和你分享快乐，需要同频共振', 1),
('她他', '她抱怨', '想发泄', '先共情', '她需要先发泄情绪，而不是给解决方案', 1),
('她他', '她道歉', '害怕被责怪', '先接纳', '她害怕被责怪，需要被接纳', 1),
('她他', '她迟到', '内疚', '先共情', '她可能已经很内疚了，不需要再加压', 1),
('她他', '她不回复', '可能有情绪/忙', '等或轻问', '可能是在消化情绪，也可能是真的忙', 2),

-- 自己的反应样本
('自己', '我急于给建议', '焦虑/想帮忙', '先倾听', '我急于给建议是因为我感到焦虑，其实她需要的是倾听', 2),
('自己', '我沉默', '不知道说什么', '准备话术', '我沉默是因为不知道说什么，需要提前准备一些话术', 2),
('自己', '我反驳', '防御/被误解', '先确认', '我反驳是因为感到被攻击，需要先确认对方的意图', 2),
('自己', '我逃避', '害怕冲突', '面对但温和', '我逃避是因为害怕冲突，但其实温和面对更好', 3),
('自己', '我讨好', '害怕不被喜欢', '真诚表达', '我讨好是因为害怕不被喜欢，但真诚表达更有效', 3),

-- 人性规律样本
('人性', '人在脆弱时', '希望被理解', '不说「别哭」', '人在脆弱时最需要被理解，不是被纠正', 1),
('人性', '人在被否定时', '容易防御', '先共情', '人在被否定时容易进入防御状态', 1),
('人性', '人在被认可时', '更有动力', '具体欣赏', '人在被认可时更有动力', 1),
('人性', '人在被接纳时', '愿意敞开', '无条件接纳', '人在感到被无条件接纳时愿意敞开', 1),
('人性', '人在感到安全时', '敢于表达', '创造安全环境', '人在感到安全时才会表达真实的自己', 2);

-- ========================================
-- 9. 每日复盘模板
-- ========================================
CREATE TABLE IF NOT EXISTS daily_review (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER,
    date DATE NOT NULL,
    
    -- 今日表现
    good_interactions TEXT, -- 做得好互动
    bad_interactions TEXT, -- 需要改进互动
    breakthroughs TEXT, -- 突破点
    
    -- 观察记录
    new_observations TEXT, -- 新观察
    patterns_identified TEXT, -- 识别模式
    insights TEXT, -- 洞察
    
    -- 工具使用
    tools_used TEXT,
    effective_tools TEXT,
    tools_to_improve TEXT,
    
    -- 自我觉察
    emotions_experienced TEXT, -- 体验到的情绪
    body_awareness_notes TEXT, -- 身体觉察记录
    automatic_thoughts TEXT, -- 自动思维
    
    -- 明日计划
    focus_areas TEXT,
    practice_goals TEXT,
    
    -- 总结
    overall_feelings TEXT,
    gratitude TEXT,
    
    FOREIGN KEY (user_id) REFERENCES user_profile(id)
);

-- ========================================
-- 10. 能力雷达图数据
-- ========================================
CREATE TABLE IF NOT EXISTS ability_radar (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER,
    date DATE NOT NULL,
    
    -- 七维能力
    reaction_delay FLOAT, -- 反应延迟（秒）- 越小越好
    emotion_granularity INTEGER, -- 情绪颗粒度
    observation_ability INTEGER, -- 观察能力
    body_awareness INTEGER, -- 身体觉察
    empathy_accuracy INTEGER, -- 共情准确度
    expression_warmth INTEGER, -- 表达温度
    review_quality INTEGER, -- 复盘质量
    
    -- 综合评分
    overall_score FLOAT,
    
    -- 对比
    vs_last_week TEXT,
    vs_last_month TEXT,
    progress_notes TEXT,
    
    FOREIGN KEY (user_id) REFERENCES user_profile(id)
);

-- ========================================
-- 索引
-- ========================================
CREATE INDEX IF NOT EXISTS idx_conversation_date ON conversation_logs(date);
CREATE INDEX IF NOT EXISTS idx_tracking_date ON ability_tracking(date);
CREATE INDEX IF NOT EXISTS idx_scenario_category ON scenario_library(category);
CREATE INDEX IF NOT EXISTS idx_sample_category ON sample_library(category);
CREATE INDEX IF NOT EXISTS idx_emotion_category ON emotion_spectra(category);

-- ========================================
-- 视图
-- ========================================

-- 用户能力趋势视图
CREATE VIEW IF NOT EXISTS v_user_ability_trend AS
SELECT 
    u.id as user_id,
    at.date,
    at.overall_score,
    at.emotion_words_count,
    at.clues_count,
    at.pause_time
FROM ability_tracking at
JOIN user_profile u ON at.user_id = u.id
ORDER BY at.date;

-- 场景使用统计视图
CREATE VIEW IF NOT EXISTS v_scenario_stats AS
SELECT 
    category,
    COUNT(*) as total_count,
    SUM(CASE WHEN effectiveness_score >= 4 THEN 1 ELSE 0 END) as good_count,
    AVG(effectiveness_score) as avg_effectiveness
FROM conversation_logs
GROUP BY category;

-- ========================================
-- 示例数据
-- ========================================

-- 插入示例用户
INSERT INTO user_profile (name, personality_type, attachment_style, love_language, emotional_granularity, perception_ability, current_phase) VALUES
('用户', 'INTJ', '焦虑型', '服务的行动', 5, 4, 1);

-- 插入示例能力追踪
INSERT INTO ability_tracking (user_id, date, pause_time, emotion_words_count, clues_count, body_awareness_count, review_nodes, overall_score) VALUES
(1, date('now'), 0.5, 8, 3, 2, 3, 6.5),
(1, date('now', '-1 day'), 0.6, 7, 2, 1, 2, 5.5),
(1, date('now', '-2 days'), 0.4, 6, 2, 1, 2, 5.0);