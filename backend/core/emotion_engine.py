"""
情绪识别引擎
"""
from typing import Any, ClassVar

from loguru import logger


class EmotionEngine:
    """情绪识别引擎 - 基于规则的情绪分析"""

    # 情绪谱系定义
    SPECTRUMS: ClassVar[dict[str, list[str]]] = {
        "喜": ["满足", "愉悦", "雀跃", "兴奋", "狂喜"],
        "怒": ["微烦", "烦躁", "恼火", "愤怒", "暴怒"],
        "哀": ["失落", "悲伤", "沮丧", "绝望", "崩溃"],
        "惧": ["紧张", "焦虑", "恐惧", "惊恐", "恐慌"],
        "爱": ["好感", "依恋", "温柔", "心动", "痴迷"],
        "惊": ["意外", "惊讶", "震惊", "目瞪口呆", "惊骇"],
        "羞": ["不好意思", "惭愧", "羞耻", "无地自容", "羞辱"],
    }

    # 混合情绪定义
    MIXED_EMOTIONS: ClassVar[dict[str, dict[str, str | int]]] = {
        "酸楚": {"spect1": "哀", "word1": "委屈", "int1": 6, "spect2": "哀", "word2": "羡慕", "int2": 5},
        "纠结": {"spect1": "爱", "word1": "想要", "int1": 7, "spect2": "惧", "word2": "害怕", "int2": 6},
        "心酸": {"spect1": "哀", "word1": "心疼", "int1": 7, "spect2": "哀", "word2": "无奈", "int2": 5},
        "忐忑": {"spect1": "惊", "word1": "期待", "int1": 6, "spect2": "惧", "word2": "不安", "int2": 7},
        "释然": {"spect1": "喜", "word1": "放下", "int1": 8, "spect2": "喜", "word2": "轻松", "int2": 7},
        "欣慰": {"spect1": "喜", "word1": "满足", "int1": 6, "spect2": "哀", "word2": "心疼", "int2": 4},
        "委屈": {"spect1": "哀", "word1": "委屈", "int1": 7, "spect2": "怒", "word2": "不甘", "int2": 5},
        "失落": {"spect1": "哀", "word1": "失落", "int1": 6, "spect2": "惧", "word2": "不安", "int2": 4},
    }

    def __init__(self) -> None:
        logger.info("情绪识别引擎初始化完成")

    def recognize_emotion(self, text: str) -> list[dict[str, Any]]:
        """识别文本中的情绪

        Args:
            text: 输入文本

        Returns:
            识别的情绪列表 [{"spectrum": "喜", "word": "愉悦", "intensity": 6}]
        """
        results: list[dict[str, Any]] = []

        # 简单关键词匹配
        for spectrum, words in self.SPECTRUMS.items():
            for word in words:
                if word in text:
                    # 根据词汇位置推断强度
                    intensity = self._estimate_intensity(word, text)
                    results.append({
                        "spectrum": spectrum,
                        "word": word,
                        "intensity": intensity,
                    })

        # 去除重复
        seen: set[str] = set()
        unique_results: list[dict[str, Any]] = []
        for r in results:
            key = f"{r['spectrum']}:{r['word']}"
            if key not in seen:
                seen.add(key)
                unique_results.append(r)

        logger.debug(f"识别到情绪: {unique_results}")
        return unique_results

    def _estimate_intensity(self, word: str, text: str) -> int:
        """根据词汇在文本中的上下文估计强度"""
        # 默认强度
        base_intensity = 5

        # 否定词降低强度
        negations = ["不", "没", "不太", "不是很"]
        for neg in negations:
            if neg in text:
                base_intensity -= 1

        # 程度副词调整
        amplifiers = ["非常", "特别", "超级", "极其", "太", "好"]
        for amp in amplifiers:
            if amp in text:
                base_intensity += 1

        # 标点符号
        if "!!" in text or "！！" in text:
            base_intensity += 2

        # 限制范围
        return max(1, min(10, base_intensity))

    def analyze_mixed_emotion(self, emotions: list[dict[str, Any]]) -> dict[str, Any] | None:
        """分析混合情绪

        Args:
            emotions: 识别到的情绪列表

        Returns:
            混合情绪信息
        """
        if len(emotions) < 2:
            return None

        # 检查是否匹配已知混合情绪
        for mixed_name, components in self.MIXED_EMOTIONS.items():
            match_count = 0
            for emp in emotions:
                if emp["word"] in [components["word1"], components["word2"]]:
                    match_count += 1

            if match_count >= 2:
                return {
                    "name": mixed_name,
                    "components": [
                        {
                            "spectrum": components["spect1"],
                            "word": components["word1"],
                            "intensity": components["int1"]
                        },
                        {
                            "spectrum": components["spect2"],
                            "word": components["word2"],
                            "intensity": components["int2"]
                        }
                    ],
                    "response_principle": f"承认{mixed_name}的感觉，引导表达"
                }

        return None

    def get_intensity_label(self, intensity: int) -> str:
        """获取强度标签"""
        if intensity <= 2:
            return "几乎察觉不到"
        elif intensity <= 4:
            return "轻微"
        elif intensity <= 6:
            return "中等"
        elif intensity <= 8:
            return "强烈"
        else:
            return "极度"

    def get_behavioral_anchor(self, spectrum: str, intensity: int) -> str:
        """获取行为锚定描述"""
        anchors = {
            1: "无明显变化",
            3: "语气轻微变化",
            5: "语速变化，表情明显",
            7: "身体动作明显",
            9: "面部表情强烈，难以控制"
        }

        # 找到最近的锚点
        levels = [1, 3, 5, 7, 9]
        closest = min(levels, key=lambda x: abs(x - intensity))

        return anchors[closest]


# 全局实例
emotion_engine = EmotionEngine()
