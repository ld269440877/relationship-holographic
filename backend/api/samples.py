"""
互动样本API路由
"""
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlmodel import Session, select

from backend.database.connection import get_session
from backend.models.sample import InteractionSample

router = APIRouter(prefix="/api/samples", tags=["样本"])


@router.get("", response_model=list[InteractionSample])
def get_samples(
    scenario_category: Optional[str] = None,
    difficulty_level: Optional[int] = None,
    attachment_signal: Optional[str] = None,
    limit: int = Query(default=20, le=100),
    offset: int = Query(default=0, ge=0),
    session: Session = Depends(get_session)
) -> list[InteractionSample]:
    """获取互动样本列表"""
    query = select(InteractionSample)
    
    if scenario_category:
        query = query.where(InteractionSample.scenario_category == scenario_category)
    if difficulty_level:
        query = query.where(InteractionSample.difficulty_level == difficulty_level)
    if attachment_signal:
        query = query.where(InteractionSample.attachment_signal == attachment_signal)
    
    query = query.offset(offset).limit(limit)
    results = session.exec(query).all()
    return list(results)


@router.get("/{sample_id}", response_model=InteractionSample)
def get_sample(
    sample_id: int,
    session: Session = Depends(get_session)
) -> InteractionSample:
    """获取单个样本详情"""
    result = session.exec(
        select(InteractionSample).where(InteractionSample.id == sample_id)
    ).first()
    
    if not result:
        raise HTTPException(status_code=404, detail="样本不存在")
    
    return result


@router.get("/random")
def get_random_sample(
    scenario_category: Optional[str] = None,
    difficulty_level: Optional[int] = None,
    session: Session = Depends(get_session)
) -> Optional[InteractionSample]:
    """随机获取一个样本用于训练"""
    query = select(InteractionSample)
    
    if scenario_category:
        query = query.where(InteractionSample.scenario_category == scenario_category)
    if difficulty_level:
        query = query.where(InteractionSample.difficulty_level == difficulty_level)
    
    # SQLite不支持OFFSET与随机组合，使用Python随机
    results = session.exec(query).all()
    if results:
        import random
        return random.choice(list(results))
    return None


@router.get("/categories")
def get_categories() -> dict:
    """获取所有场景分类"""
    return {
        "categories": ["初识", "暧昧", "热恋", "冲突", "平淡", "修复"],
        "description": "6大场景分类"
    }


@router.get("/attachments")
def get_attachments() -> dict:
    """获取所有依恋类型"""
    return {
        "attachments": ["安全型", "焦虑型", "回避型", "恐惧-回避型"],
        "description": "4种依恋类型"
    }