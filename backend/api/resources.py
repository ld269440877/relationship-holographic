"""
资源库API路由
"""
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlmodel import Session, select

from backend.database.connection import get_session
from backend.models.resource import ResourceLibrary

router = APIRouter(prefix="/api/resources", tags=["资源"])


@router.get("", response_model=list[ResourceLibrary])
def get_resources(
    resource_type: Optional[str] = None,
    category: Optional[str] = None,
    applicable_scene: Optional[str] = None,
    limit: int = Query(default=20, le=100),
    offset: int = Query(default=0, ge=0),
    session: Session = Depends(get_session)
) -> list[ResourceLibrary]:
    """获取资源列表"""
    query = select(ResourceLibrary)
    
    if resource_type:
        query = query.where(ResourceLibrary.type == resource_type)
    if category:
        query = query.where(ResourceLibrary.category == category)
    if applicable_scene:
        query = query.where(ResourceLibrary.applicable_scene == applicable_scene)
    
    query = query.offset(offset).limit(limit)
    results = session.exec(query).all()
    return list(results)


@router.get("/{resource_id}", response_model=ResourceLibrary)
def get_resource(
    resource_id: int,
    session: Session = Depends(get_session)
) -> ResourceLibrary:
    """获取单个资源详情"""
    result = session.exec(
        select(ResourceLibrary).where(ResourceLibrary.id == resource_id)
    ).first()
    
    if not result:
        raise HTTPException(status_code=404, detail="资源不存在")
    
    return result


@router.get("/random")
def get_random_resource(
    resource_type: Optional[str] = None,
    applicable_scene: Optional[str] = None,
    session: Session = Depends(get_session)
) -> Optional[ResourceLibrary]:
    """随机获取一个资源"""
    query = select(ResourceLibrary)
    
    if resource_type:
        query = query.where(ResourceLibrary.type == resource_type)
    if applicable_scene:
        query = query.where(ResourceLibrary.applicable_scene == applicable_scene)
    
    results = session.exec(query).all()
    if results:
        import random
        return random.choice(list(results))
    return None


@router.get("/types")
def get_resource_types() -> dict:
    """获取所有资源类型"""
    return {
        "types": ["joke", "story", "flirty", "riddle", "game", "media"],
        "description": "资源类型"
    }