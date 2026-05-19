"""
情绪相关API路由
"""
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select

from backend.database.connection import get_session
from backend.models.emotion import EmotionSpectrum, MixedEmotion

router = APIRouter(prefix="/api/emotions", tags=["情绪"])


@router.get("/spectrum", response_model=list[EmotionSpectrum])
def get_emotion_spectrum(
    spectrum: Optional[str] = None,
    intensity: Optional[int] = None,
    session: Session = Depends(get_session)
) -> list[EmotionSpectrum]:
    """获取情绪谱系列表"""
    query = select(EmotionSpectrum)
    
    if spectrum:
        query = query.where(EmotionSpectrum.spectrum == spectrum)
    if intensity:
        query = query.where(EmotionSpectrum.intensity == intensity)
    
    results = session.exec(query).all()
    return list(results)


@router.get("/spectrum/{spectrum}", response_model=list[EmotionSpectrum])
def get_spectrum_emotions(
    spectrum: str,
    session: Session = Depends(get_session)
) -> list[EmotionSpectrum]:
    """获取特定谱系的所有情绪"""
    results = session.exec(
        select(EmotionSpectrum).where(EmotionSpectrum.spectrum == spectrum)
    ).all()
    return list(results)


@router.get("/mixed", response_model=list[MixedEmotion])
def get_mixed_emotions(session: Session = Depends(get_session)) -> list[MixedEmotion]:
    """获取所有混合情绪"""
    results = session.exec(select(MixedEmotion)).all()
    return list(results)


@router.get("/mixed/{name}", response_model=MixedEmotion)
def get_mixed_emotion(
    name: str,
    session: Session = Depends(get_session)
) -> MixedEmotion:
    """获取特定混合情绪"""
    result = session.exec(
        select(MixedEmotion).where(MixedEmotion.name == name)
    ).first()
    
    if not result:
        raise HTTPException(status_code=404, detail="混合情绪不存在")
    
    return result


@router.get("/spectra-list")
def get_spectra_list() -> dict:
    """获取所有谱系列表"""
    return {
        "spectra": ["喜", "怒", "哀", "惧", "爱", "惊", "羞"],
        "description": "7大情绪谱系"
    }