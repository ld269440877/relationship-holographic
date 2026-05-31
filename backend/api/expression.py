"""Expression toolbox API."""
import json
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy import or_
from sqlmodel import Session, col, func, select

from backend.database.connection import get_session
from backend.database.expression_seed import GOAL_LIBRARY, SCENE_LIBRARY, TOOL_LAYER_LABELS, seed_expression_tools
from backend.models.expression import ExpressionTool, ExpressionToolChain

router = APIRouter(prefix="/api/expression", tags=["表达工具箱"])


class ExpressionRecommendRequest(BaseModel):
    scene: str = Field(default="", max_length=80)
    goal: str = Field(default="", max_length=80)
    emotion: str = Field(default="", max_length=80)
    limit: int = Field(default=3, ge=1, le=8)


@router.post("/seed")
def seed_expression_toolbox(session: Session = Depends(get_session)) -> dict[str, Any]:
    """Seed the foundational expression toolbox into SQLite."""
    return seed_expression_tools(session)


@router.get("/tools")
def list_expression_tools(
    layer: str | None = None,
    category: str | None = None,
    scene: str | None = None,
    goal: str | None = None,
    q: str | None = None,
    limit: int = Query(default=80, ge=1, le=200),
    session: Session = Depends(get_session),
) -> dict[str, Any]:
    """List expression tools with optional layer/category/scene/goal filters."""
    _ensure_seeded(session)
    facets = _expression_facets(session)
    query = select(ExpressionTool)
    count_query = select(func.count()).select_from(ExpressionTool)
    if layer:
        query = query.where(ExpressionTool.layer == layer)
        count_query = count_query.where(ExpressionTool.layer == layer)
    if category:
        query = query.where(ExpressionTool.category == category)
        count_query = count_query.where(ExpressionTool.category == category)
    if scene:
        keyword = f"%{scene.strip()}%"
        query = query.where(col(ExpressionTool.best_scenes_json).like(keyword))
        count_query = count_query.where(col(ExpressionTool.best_scenes_json).like(keyword))
    if goal:
        keyword = f"%{goal.strip()}%"
        query = query.where(
            col(ExpressionTool.description).like(keyword) | col(ExpressionTool.micro_steps_json).like(keyword)
        )
        count_query = count_query.where(
            col(ExpressionTool.description).like(keyword) | col(ExpressionTool.micro_steps_json).like(keyword)
        )
    if q:
        keyword = f"%{q.strip()}%"
        query = query.where(or_(
            col(ExpressionTool.name).like(keyword),
            col(ExpressionTool.tool_uuid).like(keyword),
            col(ExpressionTool.layer).like(keyword),
            col(ExpressionTool.category).like(keyword),
            col(ExpressionTool.description).like(keyword),
            col(ExpressionTool.formula).like(keyword),
            col(ExpressionTool.best_scenes_json).like(keyword),
            col(ExpressionTool.relationship_fit_json).like(keyword),
            col(ExpressionTool.emotion_fit_json).like(keyword),
            col(ExpressionTool.micro_steps_json).like(keyword),
            col(ExpressionTool.risk_flags_json).like(keyword),
            col(ExpressionTool.learning_blueprint_json).like(keyword),
            col(ExpressionTool.example_before).like(keyword),
            col(ExpressionTool.example_after).like(keyword),
        ))
        count_query = count_query.where(or_(
            col(ExpressionTool.name).like(keyword),
            col(ExpressionTool.tool_uuid).like(keyword),
            col(ExpressionTool.layer).like(keyword),
            col(ExpressionTool.category).like(keyword),
            col(ExpressionTool.description).like(keyword),
            col(ExpressionTool.formula).like(keyword),
            col(ExpressionTool.best_scenes_json).like(keyword),
            col(ExpressionTool.relationship_fit_json).like(keyword),
            col(ExpressionTool.emotion_fit_json).like(keyword),
            col(ExpressionTool.micro_steps_json).like(keyword),
            col(ExpressionTool.risk_flags_json).like(keyword),
            col(ExpressionTool.learning_blueprint_json).like(keyword),
            col(ExpressionTool.example_before).like(keyword),
            col(ExpressionTool.example_after).like(keyword),
        ))
    rows = session.exec(query.order_by(ExpressionTool.quality_score.desc(), ExpressionTool.updated_at.desc(), ExpressionTool.id).limit(limit)).all()
    total = session.exec(count_query).one()
    return {
        "items": [_tool_to_dict(row, include_examples=True) for row in rows],
        "total": total,
        "layers": facets["layers"],
        "scenes": facets["scenes"],
        "goals": facets["goals"],
        "layer_counts": facets["layer_counts"],
        "scene_counts": facets["scene_counts"],
        "goal_counts": facets["goal_counts"],
        "principle": "表达工具箱从 SQLite 读取；工具用于选择表达结构，不用于操控、施压或替对方做决定。",
    }


@router.get("/tools/{tool_id}")
def get_expression_tool(tool_id: int | str, session: Session = Depends(get_session)) -> dict[str, Any]:
    """Get an expression tool by numeric id or stable uuid."""
    _ensure_seeded(session)
    query = select(ExpressionTool)
    if isinstance(tool_id, int) or str(tool_id).isdigit():
        query = query.where(ExpressionTool.id == int(tool_id))
    else:
        query = query.where(ExpressionTool.tool_uuid == str(tool_id))
    tool = session.exec(query).first()
    if not tool:
        raise HTTPException(status_code=404, detail="表达工具不存在")
    return _tool_to_dict(tool, include_examples=True)


@router.get("/chains")
def list_expression_chains(
    scene: str | None = None,
    goal: str | None = None,
    q: str | None = None,
    limit: int = Query(default=20, ge=1, le=100),
    session: Session = Depends(get_session),
) -> dict[str, Any]:
    """List expression tool chains."""
    _ensure_seeded(session)
    query = select(ExpressionToolChain)
    if scene:
        query = query.where(ExpressionToolChain.scene.contains(scene.strip()))
    if goal:
        query = query.where(ExpressionToolChain.goal.contains(goal.strip()))
    if q:
        keyword = f"%{q.strip()}%"
        query = query.where(or_(
            col(ExpressionToolChain.name).like(keyword),
            col(ExpressionToolChain.goal).like(keyword),
            col(ExpressionToolChain.scene).like(keyword),
            col(ExpressionToolChain.stage).like(keyword),
            col(ExpressionToolChain.sequence_json).like(keyword),
            col(ExpressionToolChain.example_dialogue_json).like(keyword),
            col(ExpressionToolChain.forbidden_tools_json).like(keyword),
        ))
    rows = session.exec(query.order_by(ExpressionToolChain.scene, ExpressionToolChain.goal, ExpressionToolChain.id).limit(limit)).all()
    return {"items": [_chain_to_dict(row) for row in rows], "total": len(rows)}


@router.post("/recommend")
def recommend_expression_tools(
    data: ExpressionRecommendRequest,
    session: Session = Depends(get_session),
) -> dict[str, Any]:
    """Recommend a small tool chain for a scene and goal."""
    _ensure_seeded(session)
    chains = _matching_chains(session, data.scene, data.goal, data.limit)
    if chains:
        return {
            "scene": data.scene,
            "goal": data.goal,
            "chains": [_chain_to_dict(chain) for chain in chains],
            "tools": _tools_for_chains(session, chains),
            "principle": "优先推荐已有工具链；所有建议必须保留可拒绝、可退出、可复盘的边界。",
        }
    tools = _matching_tools(session, data.scene, data.goal or data.emotion, data.limit)
    return {
        "scene": data.scene,
        "goal": data.goal,
        "chains": [],
        "tools": [_tool_to_dict(tool, include_examples=True) for tool in tools],
        "principle": "未命中固定工具链时，按场景、目标和情绪从工具本体中保守推荐。",
    }


def _ensure_seeded(session: Session) -> None:
    if session.exec(select(func.count()).select_from(ExpressionTool)).one() < 60:
        seed_expression_tools(session)


def _matching_chains(session: Session, scene: str, goal: str, limit: int) -> list[ExpressionToolChain]:
    query = select(ExpressionToolChain)
    filters = []
    if scene:
        filters.append(col(ExpressionToolChain.scene).like(f"%{scene.strip()}%"))
    if goal:
        filters.append(col(ExpressionToolChain.goal).like(f"%{goal.strip()}%"))
    if filters:
        query = query.where(or_(*filters))
    return list(session.exec(query.order_by(ExpressionToolChain.quality_score.desc(), ExpressionToolChain.id).limit(limit)).all())


def _matching_tools(session: Session, scene: str, goal: str, limit: int) -> list[ExpressionTool]:
    query = select(ExpressionTool)
    filters = []
    if scene:
        filters.append(col(ExpressionTool.best_scenes_json).like(f"%{scene.strip()}%"))
    if goal:
        filters.append(col(ExpressionTool.description).like(f"%{goal.strip()}%"))
        filters.append(col(ExpressionTool.micro_steps_json).like(f"%{goal.strip()}%"))
    if filters:
        query = query.where(or_(*filters))
    return list(session.exec(query.order_by(ExpressionTool.quality_score.desc(), ExpressionTool.id).limit(limit)).all())


def _expression_facets(session: Session) -> dict[str, Any]:
    """Build filter options from SQLite, with seed constants only as fallback labels."""
    tools = session.exec(select(ExpressionTool)).all()
    chains = session.exec(select(ExpressionToolChain)).all()
    layer_counts: dict[str, int] = {}
    scene_counts: dict[str, int] = {}
    goal_counts: dict[str, int] = {}
    for tool in tools:
        if tool.layer:
            layer_counts[tool.layer] = layer_counts.get(tool.layer, 0) + 1
        for scene in _loads_list(tool.best_scenes_json):
            scene_text = str(scene).strip()
            if scene_text:
                scene_counts[scene_text] = scene_counts.get(scene_text, 0) + 1
        combined = f"{tool.description or ''} {tool.micro_steps_json or ''} {tool.learning_blueprint_json or ''}"
        for goal in GOAL_LIBRARY:
            if goal in combined:
                goal_counts[goal] = goal_counts.get(goal, 0) + 1
    for chain in chains:
        if chain.scene:
            scene_counts[chain.scene] = scene_counts.get(chain.scene, 0) + 1
        if chain.goal:
            goal_counts[chain.goal] = goal_counts.get(chain.goal, 0) + 1

    layer_keys = [key for key in layer_counts if key]
    layer_order = list(TOOL_LAYER_LABELS)
    layers = {
        key: TOOL_LAYER_LABELS.get(key, key)
        for key in sorted(layer_keys, key=lambda item: (layer_order.index(item) if item in layer_order else 99, item))
    }
    if not layers:
        layers = TOOL_LAYER_LABELS

    scenes = set(scene_counts)
    goals = set(goal_counts)
    if not scenes:
        scenes.update(SCENE_LIBRARY)
    if not goals:
        goals.update(GOAL_LIBRARY)

    return {
        "layers": layers,
        "scenes": sorted(scenes, key=lambda item: (SCENE_LIBRARY.index(item) if item in SCENE_LIBRARY else 99, item)),
        "goals": sorted(goals, key=lambda item: (GOAL_LIBRARY.index(item) if item in GOAL_LIBRARY else 99, item)),
        "layer_counts": layer_counts,
        "scene_counts": scene_counts,
        "goal_counts": goal_counts,
    }


def _tools_for_chains(session: Session, chains: list[ExpressionToolChain]) -> list[dict[str, Any]]:
    uuids: list[str] = []
    for chain in chains:
        for tool_uuid in _loads_list(chain.tool_ids_json):
            if tool_uuid not in uuids:
                uuids.append(tool_uuid)
    if not uuids:
        return []
    rows = session.exec(select(ExpressionTool).where(col(ExpressionTool.tool_uuid).in_(uuids))).all()
    rows_by_uuid = {row.tool_uuid: row for row in rows}
    return [_tool_to_dict(rows_by_uuid[tool_uuid], include_examples=True) for tool_uuid in uuids if tool_uuid in rows_by_uuid]


def _tool_to_dict(tool: ExpressionTool, *, include_examples: bool) -> dict[str, Any]:
    data: dict[str, Any] = {
        "id": tool.id,
        "tool_uuid": tool.tool_uuid,
        "name": tool.name,
        "layer": tool.layer,
        "layer_label": TOOL_LAYER_LABELS.get(tool.layer, tool.layer),
        "category": tool.category,
        "formula": tool.formula,
        "description": tool.description,
        "best_scenes": _loads_list(tool.best_scenes_json),
        "relationship_fit": _loads_list(tool.relationship_fit_json),
        "emotion_fit": _loads_list(tool.emotion_fit_json),
        "risk_flags": _loads_list(tool.risk_flags_json),
        "micro_steps": _loads_list(tool.micro_steps_json),
        "learning_blueprint": _loads_dict(tool.learning_blueprint_json),
        "mastery_stage": tool.mastery_stage,
        "review_status": tool.review_status,
        "quality_score": tool.quality_score,
        "source": tool.source,
        "source_url": tool.source_url,
    }
    if include_examples:
        data["example_before"] = tool.example_before
        data["example_after"] = tool.example_after
    return data


def _chain_to_dict(chain: ExpressionToolChain) -> dict[str, Any]:
    return {
        "id": chain.id,
        "chain_uuid": chain.chain_uuid,
        "name": chain.name,
        "goal": chain.goal,
        "scene": chain.scene,
        "stage": chain.stage,
        "tool_ids": _loads_list(chain.tool_ids_json),
        "sequence": _loads_list(chain.sequence_json),
        "forbidden_tools": _loads_list(chain.forbidden_tools_json),
        "example_dialogue": _loads_dict(chain.example_dialogue_json),
        "review_status": chain.review_status,
        "quality_score": chain.quality_score,
    }


def _loads_list(raw: str | None) -> list[Any]:
    if not raw:
        return []
    try:
        value = json.loads(raw)
    except json.JSONDecodeError:
        return []
    return value if isinstance(value, list) else []


def _loads_dict(raw: str | None) -> dict[str, Any]:
    if not raw:
        return {}
    try:
        value = json.loads(raw)
    except json.JSONDecodeError:
        return {}
    return value if isinstance(value, dict) else {}
