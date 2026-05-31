"""
互动样本模型
"""
from datetime import datetime

from sqlmodel import Field, SQLModel


class InteractionSample(SQLModel, table=True):
    """互动样本库 - 核心训练表"""

    __tablename__ = "interaction_samples"

    id: int | None = Field(default=None, primary_key=True)
    sample_uuid: str = Field(unique=True, index=True)

    # 场景信息
    scenario_category: str = Field(index=True, description="初识/暧昧/热恋/冲突/平淡/修复")
    difficulty_level: int = Field(ge=1, le=3, description="1初级2中级3高级")

    # 上下文
    context: str = Field(description="场景描述（50-200字）")

    # 对方表现
    their_words: str = Field(description="对方原话或行为描述")
    their_behavior: str | None = Field(default=None, description="非语言行为")

    # 情绪标注（JSON）
    emotion_tags_json: str = Field(description="情绪标签JSON")

    # 需求标注
    hidden_need: str | None = Field(default=None, description="隐藏需求")
    need_urgency: int | None = Field(default=None, ge=1, le=10)

    # 依恋与边界
    attachment_signal: str | None = Field(default=None, description="安全/焦虑/回避/恐惧-回避")
    boundary_test_level: int | None = Field(default=None, ge=1, le=10)

    # 回应对比
    bad_response: str = Field(description="错误回应示例")
    bad_response_reason: str | None = Field(default=None, description="为什么错")
    good_response_soft: str = Field(description="理想回应（柔和版）")
    good_response_tension: str | None = Field(default=None, description="理想回应（张力版）")
    good_response_humor: str | None = Field(default=None, description="理想回应（幽默版）")

    # 元数据
    principle_ref: str | None = Field(default=None, description="引用原则ID")
    source: str | None = Field(default=None, description="来源")
    source_url: str | None = Field(default=None)

    # 多粒度关系动力学标注（可由训练视觉地图派生，也可由进化流水线覆盖）
    five_w_two_h_json: str | None = Field(default=None, description="5W2H 元认知标注")
    signal_highlights_json: str | None = Field(default=None, description="语言/行为/需求/情绪信号")
    emotion_flow_json: str | None = Field(default=None, description="情绪流曲线")
    feeling_tags_json: str | None = Field(default=None, description="意识化感受标签")
    need_radar_json: str | None = Field(default=None, description="需求雷达")
    boundary_state_json: str | None = Field(default=None, description="边界状态与风险带")
    source_trace_json: str | None = Field(default=None, description="来源追踪")
    quality_json: str | None = Field(default=None, description="真实性/训练价值/安全性/置信度")
    tension_dimensions_json: str | None = Field(default=None, description="关系张力维度：靠近/自主、安全/新鲜等")
    gold_label_json: str | None = Field(default=None, description="Gold Set 校准标签")
    review_status: str = Field(default="draft", index=True, description="draft/reviewed/published/gold")
    is_gold_sample: bool = Field(default=False, index=True)
    annotation_version: str = Field(default="legacy-v0", index=True)

    # 时间戳
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)


class SampleAnnotationVersion(SQLModel, table=True):
    """样本多版本标注与 Gold Set 校准槽位。"""

    __tablename__ = "sample_annotation_versions"

    id: int | None = Field(default=None, primary_key=True)
    sample_id: int = Field(foreign_key="interaction_samples.id", index=True)
    version: str = Field(index=True)
    annotator_type: str = Field(default="rule", index=True, description="rule/ai/human/gold_scaffold")
    schema_version: str = Field(default="sample-annotation-v1", index=True)
    tension_dimensions_json: str | None = None
    source_trace_json: str | None = None
    quality_json: str | None = None
    safety_json: str | None = None
    gold_label_json: str | None = None
    review_status: str = Field(default="draft", index=True)
    is_gold: bool = Field(default=False, index=True)
    created_at: datetime = Field(default_factory=datetime.now, index=True)
