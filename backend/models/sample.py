"""
互动样本模型
"""
from datetime import datetime
from typing import Optional

from sqlmodel import Field, JSON, SQLModel


class InteractionSample(SQLModel, table=True):
    """互动样本库 - 核心训练表"""

    __tablename__ = "interaction_samples"

    id: Optional[int] = Field(default=None, primary_key=True)
    sample_uuid: str = Field(unique=True, index=True)
    
    # 场景信息
    scenario_category: str = Field(index=True, description="初识/暧昧/热恋/冲突/平淡/修复")
    difficulty_level: int = Field(ge=1, le=3, description="1初级2中级3高级")
    
    # 上下文
    context: str = Field(description="场景描述（50-200字）")
    
    # 对方表现
    their_words: str = Field(description="对方原话或行为描述")
    their_behavior: Optional[str] = Field(default=None, description="非语言行为")
    
    # 情绪标注（JSON）
    emotion_tags_json: str = Field(description="情绪标签JSON")
    
    # 需求标注
    hidden_need: Optional[str] = Field(default=None, description="隐藏需求")
    need_urgency: Optional[int] = Field(default=None, ge=1, le=10)
    
    # 依恋与边界
    attachment_signal: Optional[str] = Field(default=None, description="安全/焦虑/回避/恐惧-回避")
    boundary_test_level: Optional[int] = Field(default=None, ge=1, le=10)
    
    # 回应对比
    bad_response: str = Field(description="错误回应示例")
    bad_response_reason: Optional[str] = Field(default=None, description="为什么错")
    good_response_soft: str = Field(description="理想回应（柔和版）")
    good_response_tension: Optional[str] = Field(default=None, description="理想回应（张力版）")
    good_response_humor: Optional[str] = Field(default=None, description="理想回应（幽默版）")
    
    # 元数据
    principle_ref: Optional[str] = Field(default=None, description="引用原则ID")
    source: Optional[str] = Field(default=None, description="来源")
    source_url: Optional[str] = Field(default=None)
    
    # 时间戳
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)