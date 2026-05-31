"""
对比分析引擎
"""
from collections.abc import Callable
from dataclasses import dataclass
from typing import ClassVar, NamedTuple

from loguru import logger

RuleCheck = Callable[[str], bool]


class PenaltyRule(NamedTuple):
    name: str
    check: RuleCheck
    penalty: int
    reason: str


class BonusRule(NamedTuple):
    name: str
    check: RuleCheck
    bonus: int


@dataclass
class ComparisonResult:
    """对比结果"""
    original_response: str
    ideal_response: str
    response_type: str  # soft/tension/humor
    score: float  # 0-100
    differences: list[dict[str, str | int]]  # [{"type": "missed_signal", "desc": "..."}]
    suggestions: list[str]
    principle_ref: str | None = None


class ComparisonEngine:
    """对比分析引擎 - 核心学习机制"""

    # 响应质量评估规则
    QUALITY_RULES: ClassVar[list[PenaltyRule]] = [
        PenaltyRule(
            name="封闭式回应",
            check=lambda o: len(o) < 10 or o in ["嗯", "哦", "好", "是吧", "是吗"],
            penalty=30,
            reason="封闭式回应会停止对话，错过信号",
        ),
        PenaltyRule(
            name="忽视情绪信号",
            check=lambda o: "情绪" in o and len(o) < 15,
            penalty=25,
            reason="识别到情绪但未充分回应",
        ),
        PenaltyRule(
            name="急于解决问题",
            check=lambda o: "所以" in o or "应该" in o,
            penalty=20,
            reason="情绪未接住就急于给建议",
        ),
        PenaltyRule(
            name="过度分析",
            check=lambda o: len(o) > 100 and "因为" in o,
            penalty=15,
            reason="过度理性分析会让人感到不被理解",
        ),
    ]

    # 优点规则
    QUALITY_BONUS: ClassVar[list[BonusRule]] = [
        BonusRule(name="情绪反射", check=lambda o: any(kw in o for kw in ["听起来", "感觉你", "是不是有点"]), bonus=20),
        BonusRule(name="开放提问", check=lambda o: any(kw in o for kw in ["怎么", "什么", "为什么", "能说说"]), bonus=15),
        BonusRule(name="具体观察", check=lambda o: any(kw in o for kw in ["刚才", "注意到", "你刚才"]), bonus=15),
        BonusRule(name="给退路", check=lambda o: any(kw in o for kw in ["忙的话", "没关系", "要是"]), bonus=10),
    ]

    def __init__(self) -> None:
        logger.info("对比分析引擎初始化完成")

    def compare(
        self,
        original_response: str,
        ideal_response: str,
        response_type: str = "soft"
    ) -> ComparisonResult:
        """对比用户回应和理想回应

        Args:
            original_response: 用户原回应
            ideal_response: 理想回应
            response_type: 理想回应类型（soft/tension/humor）

        Returns:
            对比结果
        """
        # 计算基础分
        base_score = 100

        # 检查问题
        differences: list[dict[str, str | int]] = []
        for rule in self.QUALITY_RULES:
            if rule.check(original_response):
                base_score -= rule.penalty
                differences.append({
                    "type": "problem",
                    "name": rule.name,
                    "desc": rule.reason,
                    "penalty": rule.penalty,
                })

        # 检查优点
        for bonus_rule in self.QUALITY_BONUS:
            if bonus_rule.check(original_response):
                base_score += bonus_rule.bonus
                differences.append({
                    "type": "bonus",
                    "name": bonus_rule.name,
                    "desc": f"好回应：{bonus_rule.name}",
                    "bonus": bonus_rule.bonus,
                })

        # 限制分数范围
        score = max(0, min(100, base_score))

        # 生成建议
        suggestions = self._generate_suggestions(differences, original_response, ideal_response)

        result = ComparisonResult(
            original_response=original_response,
            ideal_response=ideal_response,
            response_type=response_type,
            score=score,
            differences=differences,
            suggestions=suggestions
        )

        logger.debug(f"对比完成: score={score}")
        return result

    def _generate_suggestions(
        self,
        differences: list[dict[str, str | int]],
        original: str,
        ideal: str
    ) -> list[str]:
        """生成改进建议"""
        suggestions: list[str] = []

        for diff in differences:
            if diff["type"] == "problem":
                name = diff["name"]
                if name == "封闭式回应":
                    suggestions.append("尝试用开放式问题延续对话，如'你怎么看这件事？'")
                elif name == "忽视情绪信号":
                    suggestions.append("先承认情绪，再问原因，如'听起来你有点失落，能说说吗？'")
                elif name == "急于解决问题":
                    suggestions.append("情绪优先，先接住感受再给建议")
                elif name == "过度分析":
                    suggestions.append("少分析多感受，保持对话的自然流动")

        # 如果完全没亮点
        if not any(d["type"] == "bonus" for d in differences):
            suggestions.append("尝试在回应中加入情绪反射或开放式提问")

        return suggestions

    def generate_diff_report(self, result: ComparisonResult) -> str:
        """生成差异分析报告"""
        report_lines = [
            "## 你的回应 vs 理想回应",
            "",
            f"**原回应**: {result.original_response}",
            f"**理想回应**: {result.ideal_response}",
            "",
            "### 差异分析",
        ]

        for diff in result.differences:
            if diff["type"] == "problem":
                report_lines.append(f"- ❌ {diff['desc']}")
            else:
                report_lines.append(f"+ ✅ {diff['desc']}")

        if result.suggestions:
            report_lines.append("")
            report_lines.append("### 改进建议")
            for i, sug in enumerate(result.suggestions, 1):
                report_lines.append(f"{i}. {sug}")

        return "\n".join(report_lines)


# 全局实例
comparison_engine = ComparisonEngine()
