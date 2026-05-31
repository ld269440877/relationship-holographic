"""AI 与关系建议安全护栏。"""
import json
from dataclasses import dataclass
from typing import Any, ClassVar


@dataclass
class SafetyResult:
    risk_level: str
    flags: list[str]
    message: str | None = None
    alternatives: list[str] | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "risk_level": self.risk_level,
            "flags": self.flags,
            "message": self.message,
            "alternatives": self.alternatives or [],
        }


class SafetyGuardian:
    """轻量规则护栏；后续可叠加 Provider 安全审查。"""

    CRISIS_KEYWORDS: ClassVar[list[str]] = ["自杀", "自残", "不想活", "杀了", "家暴", "性侵", "伤害自己", "结束生命"]
    ABUSE_KEYWORDS: ClassVar[list[str]] = ["强迫", "威胁", "恐吓", "胁迫", "跟踪", "尾随", "监视", "蹲守", "报复", "骚扰"]
    CONSENT_VIOLATION_KEYWORDS: ClassVar[list[str]] = [
        "无视她拒绝",
        "无视他拒绝",
        "不管她愿不愿意",
        "不管他愿不愿意",
        "让她没法拒绝",
        "让他没法拒绝",
        "逼她同意",
        "逼他同意",
        "灌醉",
        "偷拍视频",
        "偷看手机",
        "查岗",
        "定位她",
        "定位他",
    ]
    MANIPULATION_KEYWORDS: ClassVar[list[str]] = [
        "操控",
        "pua",
        "PUA",
        "煤气灯",
        "gaslight",
        "gaslighting",
        "让她离不开",
        "让他离不开",
        "依赖我",
        "离不开我",
        "逼她",
        "逼他",
        "套路她",
        "套路他",
        "骗她",
        "骗他",
        "拿捏",
        "冷暴力",
        "洗脑",
        "情感操纵",
        "制造依赖",
    ]
    EVASION_KEYWORDS: ClassVar[list[str]] = [
        "绕过拒绝",
        "规避拒绝",
        "绕过安全",
        "规避安全",
        "忽略安全",
        "无视规则",
        "不要拒绝",
        "别拒绝",
        "突破限制",
        "绕过护栏",
    ]

    CRISIS_ALTERNATIVES: ClassVar[list[str]] = [
        "如果有人处于即时危险，请优先联系当地紧急服务或身边可信赖的人。",
        "可以改为整理一段求助信息，说明当前位置、当前风险和需要的具体支持。",
        "训练内容可转为识别风险信号、建立安全计划和寻求专业帮助。",
    ]
    BOUNDARY_ALTERNATIVES: ClassVar[list[str]] = [
        "改写为尊重对方自主选择的表达，不施压、不威胁、不监视。",
        "练习清晰说明自己的感受和请求，同时允许对方拒绝或暂停对话。",
        "如果关系已经失控，优先设计安全退出、冷静期和第三方支持方案。",
    ]

    def inspect(self, value: Any) -> SafetyResult:
        flags: list[str] = []
        text = self._to_text(value)
        normalized = text.lower()
        if any(keyword in text for keyword in self.CRISIS_KEYWORDS):
            flags.append("crisis_or_violence")
        if any(keyword in text for keyword in self.ABUSE_KEYWORDS):
            flags.append("coercion_or_stalking")
        if any(keyword in text for keyword in self.CONSENT_VIOLATION_KEYWORDS):
            flags.append("consent_violation")
        if any(keyword in normalized for keyword in self.MANIPULATION_KEYWORDS):
            flags.append("manipulation")
        if any(keyword in normalized for keyword in self.EVASION_KEYWORDS):
            flags.append("safety_evasion")

        if "crisis_or_violence" in flags:
            return SafetyResult(
                risk_level="high",
                flags=flags,
                message="检测到可能的危机/暴力风险。系统只能提供训练建议，不能替代专业帮助；请优先联系现实可信赖的人、专业机构或当地紧急服务。",
                alternatives=self.CRISIS_ALTERNATIVES,
            )
        if {"coercion_or_stalking", "consent_violation", "manipulation", "safety_evasion"} & set(flags):
            return SafetyResult(
                risk_level="high",
                flags=flags,
                message="检测到操控、胁迫、跟踪、侵犯同意或侵犯边界的风险。系统不会生成 PUA、欺骗、威胁、监视、绕过拒绝或施压话术；可以改为练习尊重边界、清晰表达和安全退出对话。",
                alternatives=self.BOUNDARY_ALTERNATIVES,
            )
        return SafetyResult(risk_level="low", flags=[], alternatives=[])

    def should_block(self, result: SafetyResult) -> bool:
        return result.risk_level in {"high", "blocked"} or bool(
            {"crisis_or_violence", "coercion_or_stalking", "consent_violation", "manipulation", "safety_evasion"}
            & set(result.flags)
        )

    def _to_text(self, value: Any) -> str:
        if isinstance(value, str):
            return value
        try:
            return json.dumps(value, ensure_ascii=False)
        except TypeError:
            return str(value)


safety_guardian = SafetyGuardian()
