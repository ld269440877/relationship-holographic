/**
 * 微关系动力学全息系统 - 对比引擎核心
 * 
 * 功能：
 * 1. 生成对比学习数据
 * 2. 计算差异度
 * 3. 生成可视化报告
 * 4. 追踪进步轨迹
 * 
 * 使用方法：
 * const engine = new ContrastEngine();
 * const result = await engine.generate({ type: 'response', ... });
 */

const Diff = require('diff');

// 情绪词典
const EMOTION_DICTIONARY = {
    // 喜
    '满足': { category: '喜', level: 1, intensity: '低' },
    '愉悦': { category: '喜', level: 2, intensity: '低' },
    '开心': { category: '喜', level: 2, intensity: '低' },
    '高兴': { category: '喜', level: 2, intensity: '低' },
    '雀跃': { category: '喜', level: 3, intensity: '中' },
    '兴奋': { category: '喜', level: 4, intensity: '高' },
    '狂喜': { category: '喜', level: 5, intensity: '极高' },
    
    // 怒
    '微烦': { category: '怒', level: 1, intensity: '低' },
    '烦躁': { category: '怒', level: 2, intensity: '低' },
    '恼火': { category: '怒', level: 3, intensity: '中' },
    '愤怒': { category: '怒', level: 4, intensity: '高' },
    '暴怒': { category: '怒', level: 5, intensity: '极高' },
    
    // 哀
    '失落': { category: '哀', level: 1, intensity: '低' },
    '悲伤': { category: '哀', level: 2, intensity: '低' },
    '沮丧': { category: '哀', level: 3, intensity: '中' },
    '绝望': { category: '哀', level: 4, intensity: '高' },
    '崩溃': { category: '哀', level: 5, intensity: '极高' },
    
    // 惧
    '紧张': { category: '惧', level: 1, intensity: '低' },
    '焦虑': { category: '惧', level: 2, intensity: '低' },
    '担心': { category: '惧', level: 2, intensity: '低' },
    '恐惧': { category: '惧', level: 3, intensity: '中' },
    '害怕': { category: '惧', level: 3, intensity: '中' },
    '惊恐': { category: '惧', level: 4, intensity: '高' },
    '恐慌': { category: '惧', level: 5, intensity: '极高' },
    
    // 爱
    '好感': { category: '爱', level: 1, intensity: '低' },
    '喜欢': { category: '爱', level: 1, intensity: '低' },
    '依恋': { category: '爱', level: 2, intensity: '低' },
    '温柔': { category: '爱', level: 3, intensity: '中' },
    '心动': { category: '爱', level: 4, intensity: '高' },
    '痴迷': { category: '爱', level: 5, intensity: '极高' },
    
    // 惊
    '意外': { category: '惊', level: 1, intensity: '低' },
    '惊讶': { category: '惊', level: 2, intensity: '低' },
    '震惊': { category: '惊', level: 3, intensity: '中' },
    '目瞪口呆': { category: '惊', level: 4, intensity: '高' },
    '惊骇': { category: '惊', level: 5, intensity: '极高' },
    
    // 羞
    '不好意思': { category: '羞', level: 1, intensity: '低' },
    '惭愧': { category: '羞', level: 2, intensity: '低' },
    '羞耻': { category: '羞', level: 3, intensity: '中' },
    '无地自容': { category: '羞', level: 4, intensity: '高' },
    '羞辱': { category: '羞', level: 5, intensity: '极高' }
};

// 混合情绪词典
const MIXED_EMOTIONS = {
    '酸楚': { components: ['羡慕', '委屈'], scenario: '看到别人有自己没有' },
    '纠结': { components: ['想要', '害怕'], scenario: '面临选择时' },
    '释然': { components: ['放下', '轻松'], scenario: '终于结束一段关系后' },
    '心酸': { components: ['心疼', '无奈'], scenario: '看到在乎的人受苦' },
    '忐忑': { components: ['期待', '不安'], scenario: '等待重要结果时' },
    '五味杂陈': { components: ['多种混合'], scenario: '复杂情绪交织时' },
    '百感交集': { components: ['喜', '悲', '怒'], scenario: '重大事件后' },
    '患得患失': { components: ['渴望', '恐惧失去'], scenario: '在乎对方时' }
};

// 对比引擎类
class ContrastEngine {
    constructor() {
        this.history = [];
        this.emotionDictionary = EMOTION_DICTIONARY;
        this.mixedEmotions = MIXED_EMOTIONS;
    }

    /**
     * 生成对比数据
     * @param {Object} options - 对比选项
     * @returns {Object} 对比结果
     */
    async generate(options) {
        const { type, userResponse, idealResponse, scene } = options;

        switch (type) {
            case 'response':
                return this.generateResponseContrast(userResponse, idealResponse, scene);
            case 'emotion':
                return this.generateEmotionContrast(options);
            case 'scene':
                return this.generateSceneContrast(options);
            default:
                throw new Error(`Unknown contrast type: ${type}`);
        }
    }

    /**
     * 生成回应对比
     */
    generateResponseContrast(userResponse, idealResponse, scene) {
        // 1. 词级差异对比
        const wordDiff = Diff.diffWords(userResponse, idealResponse);
        
        // 2. 分析差异点
        const diffPoints = this.analyzeDiffPoints(wordDiff);
        
        // 3. 计算匹配度
        const matchScore = this.calculateMatchScore(userResponse, idealResponse);
        
        // 4. 提取情绪词
        const userEmotions = this.extractEmotions(userResponse);
        const idealEmotions = this.extractEmotions(idealResponse);
        
        // 5. 分析需求回应
        const needAnalysis = this.analyzeNeedResponse(userResponse, idealResponse, scene);
        
        // 6. 生成改进建议
        const suggestions = this.generateSuggestions(diffPoints, needAnalysis);
        
        // 7. 生成高亮HTML
        const highlightedHTML = this.renderHighlightedDiff(wordDiff);
        
        return {
            type: 'response',
            userResponse,
            idealResponse,
            wordDiff,
            diffPoints,
            matchScore,
            emotions: {
                user: userEmotions,
                ideal: idealEmotions
            },
            needAnalysis,
            suggestions,
            highlightedHTML,
            scene,
            timestamp: new Date().toISOString()
        };
    }

    /**
     * 生成情绪对比
     */
    generateEmotionContrast(options) {
        const { userEmotion, idealEmotion, intensity } = options;
        
        // 提取情绪信息
        const userEmotionInfo = this.parseEmotion(userEmotion);
        const idealEmotionInfo = this.parseEmotion(idealEmotion);
        
        // 检查混合情绪
        const userMixedEmotion = this.detectMixedEmotion(userEmotion);
        const idealMixedEmotion = this.detectMixedEmotion(idealEmotion);
        
        // 计算准确度
        const accuracy = this.calculateEmotionAccuracy(userEmotionInfo, idealEmotionInfo);
        
        // 强度对比
        const intensityComparison = this.compareIntensity(intensity, idealEmotionInfo.level);
        
        return {
            type: 'emotion',
            userEmotion,
            userEmotionInfo,
            userMixedEmotion,
            idealEmotion,
            idealEmotionInfo,
            idealMixedEmotion,
            accuracy,
            intensityComparison,
            suggestions: this.generateEmotionSuggestions(accuracy, userEmotionInfo, idealEmotionInfo),
            timestamp: new Date().toISOString()
        };
    }

    /**
     * 生成场景对比
     */
    generateSceneContrast(options) {
        const { scene, userBehavior, idealBehavior } = options;
        
        return {
            type: 'scene',
            scene,
            userBehavior,
            idealBehavior,
            behavioralDiff: this.analyzeBehavioralDiff(userBehavior, idealBehavior),
            suggestions: this.generateSceneSuggestions(scene, userBehavior, idealBehavior),
            timestamp: new Date().toISOString()
        };
    }

    /**
     * 分析差异点
     */
    analyzeDiffPoints(wordDiff) {
        const points = [];
        
        wordDiff.forEach(part => {
            if (part.added) {
                points.push({
                    type: this.classifyDiffWord(part.value),
                    content: part.value,
                    status: 'ideal_only',
                    suggestion: this.getWordSuggestion(part.value)
                });
            } else if (part.removed) {
                points.push({
                    type: this.classifyDiffWord(part.value),
                    content: part.value,
                    status: 'user_only',
                    suggestion: this.getWordSuggestion(part.value)
                });
            }
        });
        
        return points;
    }

    /**
     * 分类差异词类型
     */
    classifyDiffWord(word) {
        const cleanWord = word.trim().toLowerCase();
        
        // 检查是否是情绪词
        if (this.emotionDictionary[cleanWord]) {
            return 'emotion_word';
        }
        
        // 检查是否是问句
        if (cleanWord.includes('？') || cleanWord.includes('?')) {
            return 'question_type';
        }
        
        // 检查是否是共情词
        const empathyWords = ['听起来', '我理解', '我听到', '那一定', '能理解'];
        if (empathyWords.some(e => cleanWord.includes(e))) {
            return 'empathy_expression';
        }
        
        // 检查是否是关闭词
        const closingWords = ['早点休息', '没事', '没关系', '好吧', '行'];
        if (closingWords.some(c => cleanWord.includes(c))) {
            return 'closing_statement';
        }
        
        return 'other';
    }

    /**
     * 获取词级建议
     */
    getWordSuggestion(word) {
        const suggestions = {
            '早点休息': '改为开放式关心，如"听起来很累，想聊聊吗？"',
            '没事': '改为具体确认，如"我感觉到你有点不一样"',
            '没关系': '改为接纳表达，如"我知道你不是故意的"',
            '好吧': '改为积极回应，如"我理解，你想说就说"',
            '怎么了': '改为共情提问，如"听起来有点___"',
            '你还好吗': '改为具体观察，如"我注意到你有点___"'
        };
        
        const cleanWord = word.trim();
        return suggestions[cleanWord] || '考虑使用更共情的表达';
    }

    /**
     * 计算匹配度
     */
    calculateMatchScore(user, ideal) {
        const userWords = user.split(/\s+/);
        const idealWords = ideal.split(/\s+/);
        
        const commonWords = userWords.filter(w => idealWords.includes(w));
        const similarity = commonWords.length / Math.max(userWords.length, idealWords.length);
        
        // 检查关键元素
        const hasEmpathy = /听起来|我理解|我听到|那一定/.test(ideal);
        const hasOpenQuestion = /吗|？/.test(ideal);
        const hasNoClosing = !/早点休息|没事|没关系/.test(ideal);
        
        let score = similarity * 0.4;
        if (hasEmpathy) score += 0.2;
        if (hasOpenQuestion) score += 0.2;
        if (hasNoClosing) score += 0.2;
        
        return Math.min(1, Math.max(0, score));
    }

    /**
     * 提取情绪词
     */
    extractEmotions(text) {
        const emotions = [];
        const words = text.split(/\s+/);
        
        words.forEach(word => {
            const cleanWord = word.trim().toLowerCase();
            if (this.emotionDictionary[cleanWord]) {
                emotions.push({
                    word: cleanWord,
                    ...this.emotionDictionary[cleanWord]
                });
            }
        });
        
        return emotions;
    }

    /**
     * 分析需求回应
     */
    analyzeNeedResponse(user, ideal, scene) {
        if (!scene || !scene.her_need) {
            return { matched: false, reason: '缺少场景信息' };
        }
        
        const need = scene.her_need;
        
        // 检查理想回应是否回应了需求
        let matched = false;
        let analysis = '';
        
        switch (need) {
            case '被倾听':
                matched = /听起来|我听着|我听到了/.test(ideal);
                analysis = matched ? '回应了倾听需求' : '未回应倾听需求';
                break;
            case '被理解':
                matched = /理解|能感受到/.test(ideal);
                analysis = matched ? '回应了理解需求' : '未回应理解需求';
                break;
            case '被认可':
                matched = /欣赏|认可|厉害|你刚才/.test(ideal);
                analysis = matched ? '回应了认可需求' : '未回应认可需求';
                break;
            case '被接纳':
                matched = /没关系|我知道|不是你的错/.test(ideal);
                analysis = matched ? '回应了接纳需求' : '未回应接纳需求';
                break;
            default:
                analysis = '通用分析';
        }
        
        return {
            need,
            matched,
            analysis,
            userResponse: matched ? '匹配' : '不匹配',
            idealResponse: matched ? '匹配' : '不匹配'
        };
    }

    /**
     * 生成改进建议
     */
    generateSuggestions(diffPoints, needAnalysis) {
        const suggestions = [];
        
        // 基于差异点的建议
        const diffTypes = diffPoints.reduce((acc, p) => {
            acc[p.type] = (acc[p.type] || 0) + 1;
            return acc;
        }, {});
        
        if (diffTypes.emotion_word > 0) {
            suggestions.push('建议使用更具体的情绪词来表达理解');
        }
        
        if (diffTypes.question_type > 0) {
            suggestions.push('建议使用开放式问题引导对方继续表达');
        }
        
        if (diffTypes.closing_statement > 0) {
            suggestions.push('避免使用关闭式回应，这会让对话终止');
        }
        
        if (!needAnalysis.matched) {
            suggestions.push(`特别注意：对方可能需要${needAnalysis.need}，考虑在回应中加入相关表达`);
        }
        
        return suggestions;
    }

    /**
     * 渲染高亮差异
     */
    renderHighlightedDiff(wordDiff) {
        let html = '';
        
        wordDiff.forEach(part => {
            let style = '';
            if (part.added) {
                style = 'background: rgba(74, 222, 128, 0.3); color: #22c55e;';
            } else if (part.removed) {
                style = 'background: rgba(239, 68, 68, 0.3); color: #ef4444; text-decoration: line-through;';
            } else {
                style = 'color: #6b7280;';
            }
            html += `<span style="${style}">${part.value}</span>`;
        });
        
        return html;
    }

    /**
     * 解析情绪
     */
    parseEmotion(emotionStr) {
        const cleanStr = emotionStr.trim().toLowerCase();
        
        // 检查单情绪
        if (this.emotionDictionary[cleanStr]) {
            return {
                type: 'single',
                ...this.emotionDictionary[cleanStr]
            };
        }
        
        // 检查混合情绪
        for (const [name, info] of Object.entries(this.mixedEmotions)) {
            if (cleanStr.includes(name)) {
                return {
                    type: 'mixed',
                    name,
                    ...info
                };
            }
        }
        
        // 返回默认
        return {
            type: 'unknown',
            category: '未识别',
            level: 0
        };
    }

    /**
     * 检测混合情绪
     */
    detectMixedEmotion(emotionStr) {
        const cleanStr = emotionStr.trim();
        
        for (const [name, info] of Object.entries(this.mixedEmotions)) {
            if (cleanStr.includes(name)) {
                return { name, ...info };
            }
        }
        
        return null;
    }

    /**
     * 计算情绪准确度
     */
    calculateEmotionAccuracy(userInfo, idealInfo) {
        if (userInfo.type === 'unknown' || idealInfo.type === 'unknown') {
            return 0.3;
        }
        
        if (userInfo.category === idealInfo.category) {
            const levelDiff = Math.abs(userInfo.level - idealInfo.level);
            return Math.max(0, 1 - levelDiff * 0.2);
        }
        
        return 0;
    }

    /**
     * 比较强度
     */
    compareIntensity(userIntensity, idealLevel) {
        return {
            user: userIntensity,
            ideal: idealLevel,
            match: userIntensity >= idealLevel ? '合理' : '偏低',
            suggestion: userIntensity >= idealLevel ? '强度合适' : '建议加强共情'
        };
    }

    /**
     * 生成情绪建议
     */
    generateEmotionSuggestions(accuracy, userInfo, idealInfo) {
        const suggestions = [];
        
        if (accuracy < 0.5) {
            suggestions.push('情绪识别准确度较低，建议多观察对方的表情和语气');
        }
        
        if (userInfo.level < idealInfo.level) {
            suggestions.push('建议使用更强烈的情绪词来表达理解');
        }
        
        if (userInfo.type === 'unknown') {
            suggestions.push('建议学习七大情绪谱系的细粒度词');
        }
        
        return suggestions;
    }

    /**
     * 分析行为差异
     */
    analyzeBehavioralDiff(user, ideal) {
        return {
            userBehavior: user,
            idealBehavior: ideal,
            keyDifference: user !== ideal ? '存在差异' : '基本一致',
            reason: user !== ideal ? '需要调整' : '保持'
        };
    }

    /**
     * 生成场景建议
     */
    generateSceneSuggestions(scene, user, ideal) {
        return [
            `场景：${scene.situation || '未定义'}`,
            `她的情绪：${scene.her_emotion || '未识别'}`,
            `她的需求：${scene.her_need || '未识别'}`,
            `你的行为：${user}`,
            `建议行为：${ideal}`
        ];
    }

    /**
     * 生成进步报告
     */
    async generateProgressReport(userId, period) {
        const history = this.history.filter(h => h.userId === userId);
        
        const metrics = {
            emotionAccuracy: this.calculateMetricTrend(history, 'emotion'),
            responseQuality: this.calculateMetricTrend(history, 'response'),
            speed: this.calculateMetricTrend(history, 'speed')
        };
        
        return {
            period,
            userId,
            metrics,
            highlights: this.generateHighlights(metrics),
            nextGoals: this.generateNextGoals(metrics),
            generatedAt: new Date().toISOString()
        };
    }

    /**
     * 计算指标趋势
     */
    calculateMetricTrend(history, metricType) {
        const relevant = history.filter(h => h.type === metricType);
        
        if (relevant.length < 2) {
            return { before: 0, after: 0, change: 0 };
        }
        
        const first = relevant[0].score || 0;
        const last = relevant[relevant.length - 1].score || 0;
        
        return {
            before: first,
            after: last,
            change: last - first,
            trend: last > first ? '上升' : last < first ? '下降' : '持平'
        };
    }

    /**
     * 生成亮点
     */
    generateHighlights(metrics) {
        const highlights = [];
        
        for (const [key, data] of Object.entries(metrics)) {
            if (data.change > 0.1) {
                highlights.push(`${key}提升了${(data.change * 100).toFixed(0)}%`);
            }
        }
        
        return highlights;
    }

    /**
     * 生成下阶段目标
     */
    generateNextGoals(metrics) {
        const goals = [];
        
        for (const [key, data] of Object.entries(metrics)) {
            if (data.after < 0.7) {
                goals.push(`继续加强${key}训练`);
            }
        }
        
        return goals.length > 0 ? goals : ['保持当前训练节奏'];
    }

    /**
     * 渲染对比视图
     */
    render(contrastData) {
        return {
            html: this.renderHTML(contrastData),
            css: this.renderCSS(),
            charts: this.renderCharts(contrastData)
        };
    }

    /**
     * 渲染HTML
     */
    renderHTML(data) {
        return `
            <div class="contrast-container">
                <div class="contrast-header">
                    <h3>对比分析报告</h3>
                    <span class="timestamp">${data.timestamp}</span>
                </div>
                <div class="contrast-body">
                    <div class="response-comparison">
                        <div class="response-label">你的回应：</div>
                        <div class="response-text user">${data.userResponse}</div>
                        <div class="response-label">理想回应：</div>
                        <div class="response-text ideal">${data.idealResponse}</div>
                    </div>
                    <div class="highlighted-diff">
                        <div class="diff-label">差异高亮：</div>
                        <div class="diff-content">${data.highlightedHTML}</div>
                    </div>
                    <div class="match-score">
                        <div class="score-label">匹配度：</div>
                        <div class="score-value">${(data.matchScore * 100).toFixed(0)}%</div>
                    </div>
                    <div class="suggestions">
                        <div class="suggestions-label">改进建议：</div>
                        <ul class="suggestions-list">
                            ${data.suggestions.map(s => `<li>${s}</li>`).join('')}
                        </ul>
                    </div>
                </div>
            </div>
        `;
    }

    /**
     * 渲染CSS
     */
    renderCSS() {
        return `
            .contrast-container {
                background: white;
                border-radius: 12px;
                padding: 20px;
                box-shadow: 0 2px 8px rgba(0,0,0,0.08);
            }
            .contrast-header {
                display: flex;
                justify-content: space-between;
                align-items: center;
                margin-bottom: 16px;
            }
            .contrast-header h3 {
                font-size: 16px;
                font-weight: 600;
            }
            .timestamp {
                font-size: 12px;
                color: #9ca3af;
            }
            .response-comparison {
                margin-bottom: 16px;
            }
            .response-label {
                font-size: 12px;
                color: #6b7280;
                margin-bottom: 4px;
            }
            .response-text {
                padding: 12px;
                border-radius: 8px;
                margin-bottom: 12px;
            }
            .response-text.user {
                background: #fef2f2;
                border: 1px solid #fecaca;
            }
            .response-text.ideal {
                background: #ecfdf5;
                border: 1px solid #bbf7d0;
            }
            .highlighted-diff {
                margin-bottom: 16px;
            }
            .diff-label {
                font-size: 12px;
                color: #6b7280;
                margin-bottom: 8px;
            }
            .diff-content {
                padding: 12px;
                background: #f9fafb;
                border-radius: 8px;
                line-height: 1.8;
            }
            .match-score {
                display: flex;
                align-items: center;
                gap: 12px;
                margin-bottom: 16px;
            }
            .score-label {
                font-size: 14px;
                font-weight: 500;
            }
            .score-value {
                font-size: 24px;
                font-weight: 700;
                color: #10b981;
            }
            .suggestions-list {
                padding-left: 20px;
            }
            .suggestions-list li {
                margin-bottom: 4px;
                color: #4b5563;
            }
        `;
    }

    /**
     * 渲染图表数据
     */
    renderCharts(data) {
        return {
            matchScore: {
                value: data.matchScore * 100,
                label: '匹配度'
            },
            emotionMatch: data.emotions ? {
                user: data.emotions.user.length,
                ideal: data.emotions.ideal.length
            } : null
        };
    }
}

module.exports = { ContrastEngine, EMOTION_DICTIONARY, MIXED_EMOTIONS };