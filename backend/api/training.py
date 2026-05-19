"""
训练相关API路由
"""
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlmodel import Session, select

from backend.core.comparison_engine import comparison_engine, ComparisonResult
from backend.core.emotion_engine import emotion_engine
from backend.database.connection import get_session
from backend.models.sample import InteractionSample
from backend.models.user import MistakeLog

router = APIRouter(prefix="/api/training", tags=["训练"])


class EmotionRecognizeRequest(BaseModel):
    """情绪识别请求"""
    text: str


class EmotionRecognizeResponse(BaseModel):
    """情绪识别响应"""
    emotions: list[dict]
    mixed_emotion: Optional[dict] = None
    intensity_label: str
    behavioral_anchor: str


class CompareRequest(BaseModel):
    """对比请求"""
    original_response: str
    sample_id: int
    response_type: str = "soft"  # soft/tension/humor


class CompareResponse(BaseModel):
    """对比响应"""
    score: float
    differences: list[dict]
    suggestions: list[str]
    ideal_response: str
    diff_report: str


@router.post("/recognize", response_model=EmotionRecognizeResponse)
def recognize_emotion(request: EmotionRecognizeRequest) -> EmotionRecognizeResponse:
    """识别文本中的情绪"""
    # 识别情绪
    emotions = emotion_engine.recognize_emotion(request.text)
    
    # 分析混合情绪
    mixed = emotion_engine.analyze_mixed_emotion(emotions)
    
    # 获取强度标签
    intensity_label = "未检测到"
    behavioral_anchor = ""
    
    if emotions:
        avg_intensity = sum(e["intensity"] for e in emotions) / len(emotions)
        intensity_label = emotion_engine.get_intensity_label(int(avg_intensity))
        
        # 获取行为锚定
        spectrum = emotions[0]["spectrum"]
        intensity = emotions[0]["intensity"]
        behavioral_anchor = emotion_engine.get_behavioral_anchor(spectrum, intensity)
    
    return EmotionRecognizeResponse(
        emotions=emotions,
        mixed_emotion=mixed,
        intensity_label=intensity_label,
        behavioral_anchor=behavioral_anchor
    )


@router.post("/compare", response_model=CompareResponse)
def compare_response(
    request: CompareRequest,
    session: Session = Depends(get_session)
) -> CompareResponse:
    """对比用户回应和理想回应"""
    # 获取样本
    sample = session.exec(
        select(InteractionSample).where(InteractionSample.id == request.sample_id)
    ).first()
    
    if not sample:
        raise HTTPException(status_code=404, detail="样本不存在")
    
    # 获取理想回应
    ideal_map = {
        "soft": sample.good_response_soft,
        "tension": sample.good_response_tension or sample.good_response_soft,
        "humor": sample.good_response_humor or sample.good_response_soft,
    }
    ideal_response = ideal_map.get(request.response_type, sample.good_response_soft)
    
    # 对比
    result = comparison_engine.compare(
        original_response=request.original_response,
        ideal_response=ideal_response,
        response_type=request.response_type
    )
    
    # 生成报告
    diff_report = comparison_engine.generate_diff_report(result)
    
    return CompareResponse(
        score=result.score,
        differences=result.differences,
        suggestions=result.suggestions,
        ideal_response=ideal_response,
        diff_report=diff_report
    )


@router.get("/radar")
def get_training_radar() -> dict:
    """获取八阶能力雷达图数据"""
    # 八阶进度（示例数据）
    return {
        "levels": [
            {"name": "第零阶：沉默", "score": 85, "description": "默认状态"},
            {"name": "第一阶：信息", "score": 70, "description": "交换基本信息"},
            {"name": "第二阶：情绪", "score": 55, "description": "识别情绪标签"},
            {"name": "第三阶：感受", "score": 40, "description": "让她感到在一起"},
            {"name": "第四阶：看见", "score": 30, "description": "照出细微状态"},
            {"name": "第五阶：欣赏", "score": 25, "description": "具体真诚的光"},
            {"name": "第六阶：理解", "score": 15, "description": "建立内在模型"},
            {"name": "第七阶：爱", "score": 10, "description": "稳定的行动"},
            {"name": "第八阶：被爱", "score": 5, "description": "安心接收回馈"},
        ],
        "total_score": 335,
        "level": "第二阶中期"
    }


@router.get("/mistakes")
def get_mistakes(
    session: Session = Depends(get_session)
) -> list[dict]:
    """获取错题本列表"""
    mistakes = session.exec(
        select(MistakeLog).where(MistakeLog.reviewed == False).limit(10)
    ).all()
    
    result = []
    for m in mistakes:
        sample = session.exec(
            select(InteractionSample).where(InteractionSample.id == m.sample_id)
        ).first()
        
        if sample:
            result.append({
                "id": m.id,
                "context": sample.context,
                "their_words": sample.their_words,
                "user_bad_response": m.user_bad_response,
                "correct_response": m.correct_response,
                "emotion_mistake": m.emotion_mistake,
            })
    
    return result