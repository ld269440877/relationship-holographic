"""
复盘日记 API 路由
"""
from datetime import date

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlmodel import Session, select

from backend.database.connection import get_session
from backend.models.user import DailyReview as DailyReviewModel

router = APIRouter(prefix="/api/reviews", tags=["复盘"])


class DailyReviewCreate(BaseModel):
    review_date: date
    five_whys_json: str | None = None
    emotion_accuracy: float | None = None
    highlight: str
    improvement: str | None = None
    resource_used_id: int | None = None


class DailyReviewOut(BaseModel):
    id: int
    review_date: str
    five_whys_json: str | None
    emotion_accuracy: float | None
    highlight: str
    improvement: str | None
    resource_used_id: int | None
    emotions: list[str] = []

    class Config:
        from_attributes = True


@router.get("", response_model=list[DailyReviewOut])
def list_reviews(session: Session = Depends(get_session)) -> list:
    """获取所有复盘历史"""
    reviews = session.exec(select(DailyReviewModel).order_by(DailyReviewModel.review_date.desc())).all()
    return [_to_out(r) for r in reviews]


@router.post("", response_model=DailyReviewOut)
def create_review(data: DailyReviewCreate, session: Session = Depends(get_session)) -> dict:
    """创建或更新今日复盘"""
    # 检查是否已存在该日期的复盘
    existing = session.exec(
        select(DailyReviewModel).where(DailyReviewModel.review_date == data.review_date)
    ).first()
    if existing:
        # 更新
        existing.highlight = data.highlight
        existing.improvement = data.improvement
        existing.emotion_accuracy = data.emotion_accuracy
        existing.five_whys_json = data.five_whys_json
        session.add(existing)
        session.commit()
        session.refresh(existing)
        return _to_out(existing)

    review = DailyReviewModel(**data.model_dump())
    session.add(review)
    session.commit()
    session.refresh(review)
    return _to_out(review)


@router.delete("/{review_id}")
def delete_review(review_id: int, session: Session = Depends(get_session)) -> dict:
    """删除复盘"""
    review = session.exec(select(DailyReviewModel).where(DailyReviewModel.id == review_id)).first()
    if not review:
        raise HTTPException(status_code=404, detail="复盘不存在")
    session.delete(review)
    session.commit()
    return {"ok": True}


def _to_out(r: DailyReviewModel) -> dict:
    emotions = []
    if r.five_whys_json:
        import json
        try:
            obj = json.loads(r.five_whys_json)
            emotions = obj.get("emotions", [])
        except Exception:
            pass
    return {
        "id": r.id,
        "review_date": r.review_date.isoformat(),
        "five_whys_json": r.five_whys_json,
        "emotion_accuracy": r.emotion_accuracy,
        "highlight": r.highlight,
        "improvement": r.improvement,
        "resource_used_id": r.resource_used_id,
        "emotions": emotions,
    }
