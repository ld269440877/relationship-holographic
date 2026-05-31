from sqlalchemy import create_engine
from sqlmodel import Session, SQLModel, select
from sqlmodel.pool import StaticPool

from backend.database.seed import (
    init_emotion_spectrum,
    init_evolution_metadata_pipeline,
    init_evolution_pipeline,
    init_mixed_emotions,
    init_resources,
    init_response_strategies,
    init_samples,
    init_user_profile,
)
from backend.models.emotion import EmotionSpectrum, MixedEmotion
from backend.models.evolution import EvolutionItem, RawContentItem
from backend.models.resource import ResourceLibrary, ResponseStrategy
from backend.models.sample import InteractionSample
from backend.models.user import UserProfile


def test_seed_initializers_populate_empty_database_and_are_idempotent():
    seed_engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    SQLModel.metadata.create_all(seed_engine)

    with Session(seed_engine) as session:
        initializers = [
            init_emotion_spectrum,
            init_mixed_emotions,
            init_samples,
            init_resources,
            init_response_strategies,
            init_user_profile,
            init_evolution_pipeline,
            init_evolution_metadata_pipeline,
        ]
        for initializer in initializers:
            initializer(session)
        first_counts = _seed_counts(session)

        for initializer in initializers:
            initializer(session)
        second_counts = _seed_counts(session)

    assert first_counts["emotions"] == 70
    assert first_counts["mixed"] >= 4
    assert first_counts["samples"] >= 4
    assert first_counts["resources"] >= 4
    assert first_counts["strategies"] >= 3
    assert first_counts["profile"] == 1
    assert first_counts["evolution_items"] >= 3
    assert first_counts["raw_items"] >= 2
    assert second_counts == first_counts


def _seed_counts(session: Session) -> dict[str, int]:
    return {
        "emotions": len(session.exec(select(EmotionSpectrum)).all()),
        "mixed": len(session.exec(select(MixedEmotion)).all()),
        "samples": len(session.exec(select(InteractionSample)).all()),
        "resources": len(session.exec(select(ResourceLibrary)).all()),
        "strategies": len(session.exec(select(ResponseStrategy)).all()),
        "profile": len(session.exec(select(UserProfile)).all()),
        "evolution_items": len(session.exec(select(EvolutionItem)).all()),
        "raw_items": len(session.exec(select(RawContentItem)).all()),
    }
