"""
资源库模型
"""
from datetime import datetime

from sqlmodel import Field, SQLModel


class ResourceLibrary(SQLModel, table=True):
    """资源库 - 段子/故事/话术/急转弯/游戏"""

    __tablename__ = "resource_library"

    id: int | None = Field(default=None, primary_key=True)
    resource_uuid: str = Field(unique=True, index=True)

    # 基本信息
    type: str = Field(index=True, description="joke/story/flirty/riddle/game/media")
    category: str = Field(index=True, description="细分分类")
    title: str | None = Field(default=None)
    content: str = Field(description="主要内容")

    # 情感标注
    emotional_tone_json: str | None = Field(default=None, description="情绪基调JSON")
    emotional_intensity: int | None = Field(default=None, ge=1, le=10)

    # 适用信息
    applicable_scene: str | None = Field(default=None, description="适用场景")
    difficulty_level: int | None = Field(default=None, ge=1, le=3)
    gender_target: str | None = Field(default=None, description="男→女/女→男/通用")
    attachment_suitability: str | None = Field(default=None, description="适合的依恋类型")

    # 使用信息
    usage_tip: str | None = Field(default=None, description="使用技巧")
    effectiveness_rating: int | None = Field(default=None, ge=1, le=10, description="专家评分")
    review_status: str = Field(default="draft", index=True)
    reviewer_id: str | None = Field(default=None, index=True)
    reviewed_at: datetime | None = Field(default=None, index=True)
    published_at: datetime | None = Field(default=None, index=True)

    # 来源
    source: str | None = Field(default=None)
    source_url: str | None = Field(default=None)
    source_title: str | None = Field(default=None, description="外部来源标题或入口名称")
    source_excerpt: str | None = Field(default=None, description="合规短摘录或原文级导读片段")
    source_summary: str | None = Field(default=None, description="来源内容结构化摘要")
    source_license: str | None = Field(default=None, description="许可/使用边界说明")
    content_fingerprint: str | None = Field(default=None, index=True, description="内容去重指纹")
    quality_score: float | None = Field(default=None, index=True, description="资源质量评分")
    tags: str | None = Field(default=None, description="逗号分隔标签")
    expression_tool_ids_json: str | None = Field(default=None, description="推荐表达工具 uuid JSON")
    expression_goal: str | None = Field(default=None, index=True, description="表达目标")
    expression_level: str | None = Field(default=None, index=True, description="D1-D5 表达训练等级")
    speech_act: str | None = Field(default=None, index=True, description="语言行为")
    mistake_pattern: str | None = Field(default=None, index=True, description="常见错题模式")
    recommended_drills_json: str | None = Field(default=None, description="推荐练习 JSON")
    case_blueprint_json: str | None = Field(default=None, description="案例蓝图 JSON")
    variant_signature: str | None = Field(default=None, index=True, description="真实变体签名")
    content_unit: str | None = Field(default=None, index=True, description="最小内容单元")
    coverage_axis: str | None = Field(default=None, index=True, description="项目主线覆盖轴")
    variant_family: str | None = Field(default=None, index=True, description="案例变体家族")
    case_completeness_score: float | None = Field(default=None, index=True, description="案例结构完整度")

    # 时间戳
    created_at: datetime = Field(default_factory=datetime.now)


class ResponseStrategy(SQLModel, table=True):
    """回应策略库 - 专家系统"""

    __tablename__ = "response_strategies"

    id: int | None = Field(default=None, primary_key=True)
    name: str = Field(unique=True, description="共情反射/推拉/偷换概念/状态表达等")
    principle: str | None = Field(default=None, description="心理学原理")
    definition: str | None = Field(default=None)
    example_json: str | None = Field(default=None, description="多个示例JSON")
    applicable_situation: str | None = Field(default=None)
    effectiveness: int | None = Field(default=None, ge=1, le=10)
