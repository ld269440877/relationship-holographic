"""
情绪谱系模型
"""
from datetime import datetime
from typing import Optional

from sqlmodel import Field, JSON, Relationship, SQLModel


class EmotionSpectrum(SQLModel, table=True):
    """情绪谱系表 - 7大谱系 × 10级强度"""

    __tablename__ = "emotion_spectrum"

    id: Optional[int] = Field(default=None, primary_key=True)
    spectrum: str = Field(index=True, description="喜/怒/哀/惧/爱/惊/羞")
    intensity: int = Field(index=True, ge=1, le=10, description="强度1-10")
    word: str = Field(description="情绪词")
    behavioral_anchor: Optional[str] = Field(default=None, description="行为锚定描述")
    physiological_signal: Optional[str] = Field(default=None, description="生理信号")
    microexpression_desc: Optional[str] = Field(default=None, description="微表情特征")
    example_sentence: Optional[str] = Field(default=None, description="例句")


class MixedEmotion(SQLModel, table=True):
    """混合情绪表"""

    __tablename__ = "mixed_emotions"

    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(description="混合情绪名称")
    component1_spectrum: str = Field(description="成分1谱系")
    component1_word: str = Field(description="成分1情绪词")
    component1_intensity: int = Field(ge=1, le=10)
    component2_spectrum: str = Field(description="成分2谱系")
    component2_word: str = Field(description="成分2情绪词")
    component2_intensity: int = Field(ge=1, le=10)
    typical_scenario: Optional[str] = Field(default=None, description="典型场景")
    response_principle: Optional[str] = Field(default=None, description="回应原则")


class EmotionTag(SQLModel):
    """情绪标签（用于JSON序列化）"""

    spectrum: str
    word: str
    intensity: int = Field(ge=1, le=10)
    is_mixed: bool = False