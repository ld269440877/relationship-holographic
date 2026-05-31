"""
回应策略专家系统 API
"""
from fastapi import APIRouter, Depends
from sqlmodel import Session, select

from backend.database.connection import get_session
from backend.models.resource import ResponseStrategy

router = APIRouter(prefix="/api/strategies", tags=["策略"])


@router.get("")
def list_strategies(session: Session = Depends(get_session)) -> list[dict]:
    """获取所有回应策略"""
    strategies = session.exec(select(ResponseStrategy)).all()
    return [_s_to_dict(s) for s in strategies]


@router.get("/{name}")
def get_strategy(name: str, session: Session = Depends(get_session)) -> dict | None:
    strategy = session.exec(
        select(ResponseStrategy).where(ResponseStrategy.name == name)
    ).first()
    if not strategy:
        return None
    return _s_to_dict(strategy)


def _s_to_dict(s: ResponseStrategy) -> dict:
    import json
    examples = []
    if s.example_json:
        try:
            examples = json.loads(s.example_json)
        except Exception:
            examples = []
    return {
        "id": s.id,
        "name": s.name,
        "principle": s.principle,
        "definition": s.definition,
        "examples": examples,
        "applicable_situation": s.applicable_situation,
        "effectiveness": s.effectiveness,
    }
