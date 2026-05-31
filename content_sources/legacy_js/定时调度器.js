/**
 * 微关系动力学全息系统 - 定时调度器
 * 
 * 核心功能：
 * - 每日任务（凌晨2:00）：采集新样本、检测更新、清理过期
 * - 每周任务（周日3:00）：全量去重、标签补全、生成报告
 * - 每月任务（1号4:00）：错题本统计、能力雷达更新
 * 
 * 使用方法：
 * node scheduler/index.js
 */

const fs = require('fs');
const path = require('path');
const crypto = require('crypto');

// 日志记录
function log(message, type = 'INFO') {
    const timestamp = new Date().toISOString();
    console.log(`[${timestamp}] [${type}] ${message}`);
}

// 数据库模拟（实际项目中应连接真实数据库）
class Database {
    constructor() {
        this.samples = [];
        this.users = [];
        this.tracking = [];
    }

    // 检查样本是否存在
    exists(hash) {
        return this.samples.some(s => s.contentHash === hash);
    }

    // 保存样本
    save(sample) {
        this.samples.push(sample);
        log(`样本已保存: ${sample.id}`, 'DATABASE');
    }

    // 质量检查
    qualityCheck() {
        let issues = 0;
        this.samples.forEach(s => {
            if (!s.emotion || !s.emotion.trim()) issues++;
            if (!s.idealResponse || !s.idealResponse.trim()) issues++;
        });
        return issues;
    }
}

// 定时任务基类
class ScheduledTask {
    constructor(name, schedule, handler) {
        this.name = name;
        this.schedule = schedule;
        this.handler = handler;
        this.lastRun = null;
        this.enabled = true;
    }

    async execute() {
        if (!this.enabled) {
            log(`${this.name} 已禁用，跳过执行`, 'SKIP');
            return;
        }

        log(`开始执行任务: ${this.name}`, 'TASK');
        try {
            const startTime = Date.now();
            await this.handler();
            const duration = ((Date.now() - startTime) / 1000).toFixed(2);
            this.lastRun = new Date();
            log(`任务完成: ${this.name} (耗时: ${duration}秒)`, 'COMPLETE');
        } catch (error) {
            log(`任务失败: ${this.name} - ${error.message}`, 'ERROR');
        }
    }
}

// 每日任务：数据采集
const dailyHarvestTask = new ScheduledTask(
    '每日数据采集',
    '0 2 * * *', // 每天凌晨2:00
    async () => {
        log('开始采集新数据...', 'CRAWLER');
        
        // 模拟数据源
        const sources = [
            { name: '知乎', url: 'https://www.zhihu.com', weight: 30 },
            { name: 'B站', url: 'https://www.bilibili.com', weight: 25 },
            { name: '小红书', url: 'https://www.xiaohongshu.com', weight: 25 },
            { name: '豆瓣', url: 'https://www.douban.com', weight: 20 }
        ];

        const db = new Database();
        let totalNew = 0;
        let duplicates = 0;

        for (const source of sources) {
            log(`正在采集: ${source.name}`, 'CRAWLER');
            
            // 模拟采集的数据
            const mockData = generateMockData(source.name, Math.floor(Math.random() * 5) + 1);
            
            for (const item of mockData) {
                // 内容哈希
                const contentHash = crypto.createHash('sha256')
                    .update(item.content)
                    .digest('hex');
                
                // 去重检查
                if (db.exists(contentHash)) {
                    duplicates++;
                    continue;
                }

                // 生成对比数据
                const sample = {
                    id: `sample_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`,
                    content: item.content,
                    contentHash: contentHash,
                    source: source.name,
                    emotion: item.emotion,
                    emotionIntensity: item.intensity,
                    need: item.need,
                    idealResponse: item.idealResponse,
                    wrongResponse: item.wrongResponse,
                    difficultyLevel: item.difficultyLevel,
                    tags: item.tags,
                    createdAt: new Date().toISOString(),
                    contrast: generateContrast(item)
                };

                db.save(sample);
                totalNew++;
            }
        }

        // 生成更新报告
        const report = {
            date: new Date().toISOString(),
            newSamples: totalNew,
            duplicatesRemoved: duplicates,
            totalSamples: db.samples.length,
            sources: sources.map(s => ({ name: s.name, weight: s.weight }))
        };

        log(`采集完成: 新增${totalNew}条, 去除重复${duplicates}条`, 'CRAWLER');
        saveReport(report, 'daily');
        
        return report;
    }
);

// 每周任务：全量去重和优化
const weeklyOptimizationTask = new ScheduledTask(
    '每周优化任务',
    '0 3 * * 0', // 每周日凌晨3:00
    async () => {
        log('开始每周优化...', 'OPTIMIZE');
        
        const db = new Database();
        
        // 1. 全量质量检验
        log('执行质量检验...', 'OPTIMIZE');
        const qualityIssues = db.qualityCheck();
        log(`发现质量问题: ${qualityIssues}条`, 'OPTIMIZE');
        
        // 2. 情绪标签标准化
        log('标准化情绪标签...', 'OPTIMIZE');
        const standardizedEmotions = standardizeEmotions();
        log(`标准化完成: ${standardizedEmotions}个情绪词`, 'OPTIMIZE');
        
        // 3. 更新用户推荐模型
        log('更新推荐模型...', 'OPTIMIZE');
        updateRecommendationModel();
        
        // 4. 生成周报
        const report = {
            date: new Date().toISOString(),
            type: 'weekly',
            qualityIssues: qualityIssues,
            standardizedEmotions: standardizedEmotions,
            totalSamples: db.samples.length,
            recommendations: generateWeeklyRecommendations()
        };

        saveReport(report, 'weekly');
        log('每周优化完成', 'OPTIMIZE');
        
        return report;
    }
);

// 每月任务：深度分析和规划
const monthlyAnalysisTask = new ScheduledTask(
    '每月分析任务',
    '0 4 1 * *', // 每月1号凌晨4:00
    async () => {
        log('开始每月分析...', 'ANALYSIS');
        
        // 1. 错题本统计
        log('分析错题本...', 'ANALYSIS');
        const errorAnalysis = analyzeErrorBook();
        
        // 2. 能力雷达更新
        log('更新能力雷达...', 'ANALYSIS');
        const abilityRadar = updateAbilityRadar();
        
        // 3. 新维度推荐
        log('推荐新维度...', 'ANALYSIS');
        const newDimensions = recommendNewDimensions();
        
        // 生成月报
        const report = {
            date: new Date().toISOString(),
            type: 'monthly',
            errorAnalysis: errorAnalysis,
            abilityRadar: abilityRadar,
            newDimensions: newDimensions,
            recommendations: generateMonthlyRecommendations()
        };

        saveReport(report, 'monthly');
        log('每月分析完成', 'ANALYSIS');
        
        return report;
    }
);

// 生成对比数据
function generateContrast(item) {
    return {
        vs_similar: findSimilarSamples(item),
        emotional_anchors: extractEmotionalAnchors(item),
        expert_annotation: getExpertAnnotation(item),
        difficulty_level: item.difficultyLevel || 3,
        key_diff_points: identifyKeyDifferences(item)
    };
}

// 查找相似样本
function findSimilarSamples(item) {
    // 模拟返回相似样本
    return [
        { 
            id: 'sample_001', 
            similarity: 0.85,
            diff_points: ['情绪词', '问句类型']
        }
    ];
}

// 提取情绪锚点
function extractEmotionalAnchors(item) {
    const anchors = [];
    
    if (item.emotion) {
        anchors.push({
            type: 'primary_emotion',
            value: item.emotion,
            intensity: item.intensity || 5
        });
    }
    
    // 添加混合情绪检测
    const mixedEmotions = detectMixedEmotions(item.content);
    if (mixedEmotions.length > 0) {
        anchors.push({
            type: 'mixed_emotions',
            value: mixedEmotions
        });
    }
    
    return anchors;
}

// 检测混合情绪
function detectMixedEmotions(text) {
    const mixedPatterns = {
        '酸楚': ['羡慕', '委屈'],
        '纠结': ['想要', '害怕'],
        '释然': ['放下', '轻松'],
        '心酸': ['心疼', '无奈'],
        '忐忑': ['期待', '不安']
    };
    
    const detected = [];
    for (const [name, keywords] of Object.entries(mixedPatterns)) {
        if (keywords.some(k => text.includes(k))) {
            detected.push(name);
        }
    }
    
    return detected;
}

// 获取专家标注
function getExpertAnnotation(item) {
    return {
        emotion_analysis: `专家分析: ${item.emotion || '未标注'}`,
        need_analysis: `需求分析: ${item.need || '未标注'}`,
        response_strategy: `回应策略: 共情优先，注意节奏`,
        confidence: 0.85
    };
}

// 识别关键差异点
function identifyKeyDifferences(item) {
    const differences = [];
    
    if (item.wrongResponse && item.idealResponse) {
        differences.push({
            type: 'response_style',
            wrong: item.wrongResponse,
            ideal: item.idealResponse,
            reason: '封闭式 vs 开放式'
        });
    }
    
    if (item.emotionIntensity >= 7 && item.wrongResponse) {
        differences.push({
            type: 'intensity_handling',
            wrong: '直接给建议',
            ideal: '先共情降强度',
            reason: '高强度情绪需要先降温度'
        });
    }
    
    return differences;
}

// 标准化情绪词
function standardizeEmotions() {
    const emotionMap = {
        '开心': '愉悦',
        '高兴': '愉悦',
        '好开心': '雀跃',
        '很烦': '烦躁',
        '生气': '愤怒',
        '难过': '悲伤',
        '伤心': '悲伤',
        '没希望': '绝望',
        '崩溃': '崩溃',
        '担心': '焦虑',
        '害怕': '恐惧',
        '喜欢': '好感',
        '想见': '依恋',
        '心动': '心动'
    };
    
    return Object.keys(emotionMap).length;
}

// 更新推荐模型
function updateRecommendationModel() {
    // 模拟更新
    return {
        basedOn: '用户行为数据',
        recommendations: [
            { dimension: '情绪识别', priority: 'high' },
            { dimension: '共情表达', priority: 'medium' },
            { dimension: '提问技巧', priority: 'low' }
        ]
    };
}

// 分析错题本
function analyzeErrorBook() {
    return {
        totalErrors: Math.floor(Math.random() * 50) + 10,
        byEmotion: {
            '烦躁': 15,
            '委屈': 12,
            '愤怒': 8,
            '悲伤': 10,
            '其他': 5
        },
        byDifficulty: {
            'level1': 5,
            'level2': 15,
            'level3': 20,
            'level4': 10,
            'level5': 0
        },
        improvementRate: 0.65,
        weakestDimension: '情绪识别-混合情绪'
    };
}

// 更新能力雷达
function updateAbilityRadar() {
    return {
        dimensions: [
            { name: '反应延迟', value: 0.6, change: '+0.1' },
            { name: '情绪颗粒度', value: 0.45, change: '+0.05' },
            { name: '观察能力', value: 0.5, change: '+0.08' },
            { name: '身体觉察', value: 0.35, change: '+0.03' },
            { name: '共情准确', value: 0.55, change: '+0.1' },
            { name: '表达温度', value: 0.5, change: '+0.05' },
            { name: '复盘质量', value: 0.6, change: '+0.1' }
        ],
        overall: 0.5,
        trend: 'improving'
    };
}

// 推荐新维度
function recommendNewDimensions() {
    return [
        { name: '微表情识别', priority: 'high', reason: '观察能力需要强化' },
        { name: '沉默应对', priority: 'medium', reason: '常见场景但训练不足' },
        { name: '冲突处理', priority: 'medium', reason: '高难度但重要' }
    ];
}

// 生成模拟数据
function generateMockData(source, count) {
    const templates = [
        {
            content: '今天好累啊',
            emotion: '疲惫',
            intensity: 6,
            need: '被理解',
            idealResponse: '听起来今天像背着一座山回来，发生什么了？',
            wrongResponse: '那你早点休息',
            difficultyLevel: 2,
            tags: ['疲惫', '工作']
        },
        {
            content: '唉',
            emotion: '烦躁/累/委屈',
            intensity: 5,
            need: '被倾听',
            idealResponse: '听起来今天有点不太顺，想聊聊吗？',
            wrongResponse: '怎么了？',
            difficultyLevel: 2,
            tags: ['叹气', '需要倾听']
        },
        {
            content: '算了，不说了',
            emotion: '失望/委屈',
            intensity: 5,
            need: '被挽留',
            idealResponse: '我感觉到你有点失望，是我说的话让你觉得没被理解吗？',
            wrongResponse: '好吧',
            difficultyLevel: 3,
            tags: ['放弃表达', '防御']
        },
        {
            content: '我没事（但明显不是）',
            emotion: '压抑/委屈',
            intensity: 6,
            need: '被看穿',
            idealResponse: '我听到你说没事，但感觉你有点不一样。想说就说，不想说也没关系，我在这。',
            wrongResponse: '哦，那好吧',
            difficultyLevel: 3,
            tags: ['口是心非', '需要洞察']
        },
        {
            content: '那个同事真烦人',
            emotion: '愤怒/抱怨',
            intensity: 6,
            need: '发泄',
            idealResponse: '怎么了？她做什么了？',
            wrongResponse: '那你忍忍吧',
            difficultyLevel: 2,
            tags: ['抱怨', '需要倾听']
        }
    ];
    
    return templates.slice(0, count);
}

// 生成周建议
function generateWeeklyRecommendations() {
    return [
        '本周情绪识别准确率提升8%，继续保持',
        '建议加强混合情绪的训练',
        '观察到在「她说算了」场景中仍需提升'
    ];
}

// 生成月建议
function generateMonthlyRecommendations() {
    return [
        '本月整体进步明显，尤其是复盘质量提升25%',
        '建议下月重点关注「微表情识别」维度',
        '错题本显示「愤怒情绪处理」需要加强'
    ];
}

// 保存报告
function saveReport(report, type) {
    const filename = `${type}_report_${Date.now()}.json`;
    const filepath = path.join(__dirname, 'reports', filename);
    
    // 确保目录存在
    const reportsDir = path.join(__dirname, 'reports');
    if (!fs.existsSync(reportsDir)) {
        fs.mkdirSync(reportsDir, { recursive: true });
    }
    
    fs.writeFileSync(filepath, JSON.stringify(report, null, 2));
    log(`报告已保存: ${filename}`, 'REPORT');
}

// 调度器主类
class Scheduler {
    constructor() {
        this.tasks = [];
        this.running = false;
    }

    addTask(task) {
        this.tasks.push(task);
        log(`任务已添加: ${task.name}`, 'SCHEDULER');
    }

    start() {
        log('调度器启动', 'SCHEDULER');
        this.running = true;
        
        // 添加所有任务
        this.addTask(dailyHarvestTask);
        this.addTask(weeklyOptimizationTask);
        this.addTask(monthlyAnalysisTask);

        // 模拟调度循环
        this.runLoop();
    }

    async runLoop() {
        while (this.running) {
            const now = new Date();
            const currentMinute = `${now.getHours().toString().padStart(2, '0')} ${now.getMinutes().toString().padStart(2, '0')}`;
            
            // 检查每个任务
            for (const task of this.tasks) {
                // 简化的调度检查（实际应该用 cron-parser）
                if (this.shouldRun(task, now)) {
                    await task.execute();
                }
            }

            // 每分钟检查一次
            await this.sleep(60000);
        }
    }

    shouldRun(task, now) {
        // 简化逻辑：如果是新的一天且任务从未执行过
        if (!task.lastRun) return true;
        
        const lastRunDate = new Date(task.lastRun);
        const daysSinceLastRun = Math.floor((now - lastRunDate) / (1000 * 60 * 60 * 24));
        
        if (task.schedule.includes('* * *')) return daysSinceLastRun >= 1;
        if (task.schedule.includes('* 0')) return daysSinceLastRun >= 7;
        if (task.schedule.includes('1 *')) return daysSinceLastRun >= 30;
        
        return false;
    }

    sleep(ms) {
        return new Promise(resolve => setTimeout(resolve, ms));
    }

    stop() {
        log('调度器停止', 'SCHEDULER');
        this.running = false;
    }
}

// 手动触发任务（用于测试）
async function runManually(taskName) {
    const taskMap = {
        'daily': dailyHarvestTask,
        'weekly': weeklyOptimizationTask,
        'monthly': monthlyAnalysisTask
    };

    const task = taskMap[taskName];
    if (task) {
        await task.execute();
    } else {
        log(`未知任务: ${taskName}`, 'ERROR');
    }
}

// 主入口
if (require.main === module) {
    const args = process.argv.slice(2);
    
    if (args.length > 0) {
        // 手动执行指定任务
        runManually(args[0]);
    } else {
        // 启动调度器
        const scheduler = new Scheduler();
        scheduler.start();
    }
}

module.exports = { Scheduler, runManually };