"""
资源库模型
"""
from datetime import datetime
from typing import Optional

from sqlmodel import Field, JSON, SQLModel


class ResourceLibrary(SQLModel, table=True):
    """资源库 - 段子/故事/话术/急转弯/游戏"""

    __tablename__ = "resource_library"

    id: Optional[int] = Field(default=None, primary_key=True)
    resource_uuid: str = Field(unique=True, index=True)
    
    # 基本信息
    type: str = Field(index=True, description="joke/story/flirty/riddle/game/media")
    category: str = Field(index=True, description="细分分类")
    title: Optional[str] = Field(default=None)
    content: str = Field(description="主要内容")
    
    # 情感标注
    emotional_tone_json: Optional[str] = Field(default=None, description="情绪基调JSON")
    emotional_intensity: Optional[int] = Field(default=None, ge=1, le=10)
    
    # 适用信息
    applicable_scene: Optional[str] = Field(default=None, description="适用场景")
    difficulty_level: Optional[int] = Field(default=None, ge=1, le=3)
    gender_target: Optional[str] = Field(default=None, description="男→女/女→男/通用")
    attachment_suitability: Optional[str] = Field(default=None, description="适合的依恋类型")
    
    # 使用信息
    usage_tip: Optional[str] = Field(default=None, description="使用技巧")
    effectiveness_rating: Optional[int] = Field(default=None, ge=1, le=10, description="专家评分")
    
    # 来源
    source: Optional[str] = Field(default=None)
    source_url: Optional[str] = Field(default=None)
    tags: Optional[str] = Field(default=None, description="逗号分隔标签")
    
    # 时间戳
    created_at: datetime = Field(default_factory=datetime.now)


class ResponseStrategy(SQLModel, table=True):
    """回应策略库 - 专家系统"""

    __tablename__ = "response_strategies"

    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(unique=True, description="共情反射/推拉/偷换概念/状态表达等")
    principle: Optional[str] = Field(default=None, description="心理学原理")
    definition: Optional[str] = Field(default=None)
    example_json: Optional[str] = Field(default=None, description="多个示例JSON")
    applicable_situation: Optional[str] = Field(default=None)
    effectiveness: Optional[int] = Field(default=None, ge=1, le=10)