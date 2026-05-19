"""
用户画像模型
"""
from datetime import date, datetime
from typing import Optional

from sqlmodel import Field, JSON, SQLModel


class UserProfile(SQLModel, table=True):
    """用户画像表"""

    __tablename__ = "user_profile"

    id: Optional[int] = Field(default=None, primary_key=True)
    
    # 依恋类型
    attachment_style: Optional[str] = Field(default=None, description="安全/焦虑/回避/恐惧-回避")
    
    # 核心创伤
    core_wound: Optional[str] = Field(default=None, description="被抛弃/被忽视/被否定")
    
    # 爱语
    love_language: Optional[str] = Field(default=None, description="肯定/服务/礼物/时间/接触")
    
    # 感知基线
    perception_baseline: Optional[int] = Field(default=None, ge=0, le=100)
    
    # 情绪词汇量
    emotion_vocab_size: Optional[int] = Field(default=None)
    
    # 能力进度
    progress_json: Optional[str] = Field(default=None, description="八阶进度JSON")
    
    # 时间戳
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)


class MistakeLog(SQLModel, table=True):
    """错题本 - 间隔重复"""

    __tablename__ = "mistake_log"

    id: Optional[int] = Field(default=None, primary_key=True)
    sample_id: int = Field(foreign_key="interaction_samples.id")
    
    # 用户表现
    user_bad_response: str = Field(description="用户错误回应")
    correct_response: str = Field(description="正确回应")
    emotion_mistake: Optional[str] = Field(default=None, description="错标的情绪")
    
    # 复习状态
    reviewed: bool = Field(default=False)
    review_interval: int = Field(default=1, description="间隔天数")
    next_review: Optional[date] = Field(default=None)
    
    # 统计
    correct_count: int = Field(default=0)
    wrong_count: int = Field(default=0)
    
    # 时间戳
    created_at: datetime = Field(default_factory=datetime.now)


class DailyReview(SQLModel, table=True):
    """每日复盘"""

    __tablename__ = "daily_review"

    id: Optional[int] = Field(default=None, primary_key=True)
    review_date: date = Field(unique=True)
    
    # 5W2H复盘
    five_whys_json: Optional[str] = Field(default=None)
    
    # 准确率
    emotion_accuracy: Optional[float] = Field(default=None, ge=0, le=100)
    
    # 内容
    highlight: Optional[str] = Field(default=None)
    improvement: Optional[str] = Field(default=None)
    
    # 使用资源
    resource_used_id: Optional[int] = Field(default=None, foreign_key="resource_library.id")
    
    # 时间戳
    created_at: datetime = Field(default_factory=datetime.now)