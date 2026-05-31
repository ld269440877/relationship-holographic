"""数据模型。

集中导入所有 SQLModel table，确保 create_all 能发现元数据。
"""

from backend.models.ai import AIPromptVersion, AIProviderProbeLog, AIRunLog
from backend.models.emotion import EmotionSpectrum, MixedEmotion
from backend.models.evolution import (
    AnnotationJob,
    EvolutionItem,
    EvolutionReport,
    EvolutionSource,
    MetadataVectorIndex,
    PipelineRunLog,
    RawContentItem,
    SourceRegistry,
    TrainingAssetVersion,
)
from backend.models.expression import ExpressionTool, ExpressionToolChain
from backend.models.knowledge import ContentImportBatch, ContentImportIssue, KnowledgeEntry, KnowledgeSection
from backend.models.resource import ResourceLibrary
from backend.models.runtime import RuntimeEvent
from backend.models.sample import InteractionSample, SampleAnnotationVersion
from backend.models.training import AbilitySnapshot, PracticeEvent, PracticeSession, SafetyEvent, TrainingAttempt
from backend.models.user import DailyReview, MistakeLog, UserProfile

__all__ = [
    "EmotionSpectrum",
    "MixedEmotion",
    "AIPromptVersion",
    "AIRunLog",
    "AIProviderProbeLog",
    "ExpressionTool",
    "ExpressionToolChain",
    "EvolutionItem",
    "EvolutionReport",
    "EvolutionSource",
    "PipelineRunLog",
    "MetadataVectorIndex",
    "SourceRegistry",
    "RawContentItem",
    "AnnotationJob",
    "TrainingAssetVersion",
    "KnowledgeSection",
    "KnowledgeEntry",
    "ContentImportBatch",
    "ContentImportIssue",
    "ResourceLibrary",
    "RuntimeEvent",
    "InteractionSample",
    "SampleAnnotationVersion",
    "AbilitySnapshot",
    "TrainingAttempt",
    "PracticeSession",
    "PracticeEvent",
    "SafetyEvent",
    "DailyReview",
    "MistakeLog",
    "UserProfile",
]
