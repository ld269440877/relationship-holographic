"""
用户画像 API 路由
"""
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlmodel import Session, select

from backend.database.connection import get_session
from backend.models.user import UserProfile

router = APIRouter(prefix="/api/profile", tags=["用户"])


class ProfileOut(BaseModel):
    id: int
    attachment_style: str | None
    core_wound: str | None
    love_language: str | None
    perception_baseline: int | None
    emotion_vocab_size: int | None
    progress_json: str | None

    class Config:
        from_attributes = True


class ProfileUpdate(BaseModel):
    attachment_style: str | None = None
    core_wound: str | None = None
    love_language: str | None = None
    perception_baseline: int | None = None
    emotion_vocab_size: int | None = None
    progress_json: str | None = None


@router.get("", response_model=ProfileOut)
def get_profile(session: Session = Depends(get_session)) -> dict:
    """获取用户画像（单条记录）"""
    profile = session.exec(select(UserProfile)).first()
    if not profile:
        # 首次访问，创建默认画像
        profile = UserProfile(
            attachment_style="安全型",
            perception_baseline=50,
            emotion_vocab_size=35,
        )
        session.add(profile)
        session.commit()
        session.refresh(profile)
    return profile


@router.put("", response_model=ProfileOut)
def update_profile(data: ProfileUpdate, session: Session = Depends(get_session)) -> dict:
    """更新用户画像"""
    profile = session.exec(select(UserProfile)).first()
    if not profile:
        profile = UserProfile()
        session.add(profile)
    for field, value in data.model_dump(exclude_none=True).items():
        setattr(profile, field, value)
    session.add(profile)
    session.commit()
    session.refresh(profile)
    return profile
