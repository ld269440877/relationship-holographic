"""JSON 内容迁入 SQLite 的一次性/可重复执行脚本。

目标：把项目根目录中的大型 JSON 内容库迁入 SQLite，继续坚持
“SQLite 单一数据源 / API 唯一出口”的演进原则。

用法：
    .venv/bin/python -m backend.database.import_json_content
"""
from __future__ import annotations

import json
import uuid
from pathlib import Path
from typing import Any

from loguru import logger
from sqlmodel import Session, select

from backend.database.connection import PROJECT_ROOT, create_db_and_tables, engine
from backend.database.content_sources import CONTENT_SOURCES_DIR, resolve_source_path
from backend.models.resource import ResourceLibrary
from backend.models.sample import InteractionSample


def _source_path(filename: str, subdir: str = "raw_json") -> Path:
    return resolve_source_path(
        filename,
        subdir,
        content_sources_dir=CONTENT_SOURCES_DIR,
        project_root=PROJECT_ROOT,
    )


SAMPLE_FILE = _source_path("场景样本库完整版.json")
RESOURCE_FILES = [
    ("话术库.json", "flirty"),
    ("段子库.json", "joke"),
    ("故事库.json", "story"),
    ("游戏库.json", "game"),
]


def import_all() -> dict[str, int]:
    """导入所有已知 JSON 内容库，返回新增数量。"""
    create_db_and_tables()
    with Session(engine) as session:
        imported_samples = import_samples(session, SAMPLE_FILE)
        imported_resources = 0
        for filename, resource_type in RESOURCE_FILES:
            imported_resources += import_resource_file(session, _source_path(filename), resource_type)
        session.commit()
    summary = {"samples": imported_samples, "resources": imported_resources}
    logger.info(f"JSON 内容导入完成: {summary}")
    return summary


def import_samples(session: Session, path: Path) -> int:
    if not path.exists():
        logger.warning(f"样本文件不存在，跳过: {path}")
        return 0
    data = _load_json(path)
    count = 0
    for item in data.get("samples", []):
        source_id = str(item.get("id") or uuid.uuid4())
        sample_uuid = f"json:{source_id}"
        if _sample_exists(session, sample_uuid):
            continue
        sample = InteractionSample(
            sample_uuid=sample_uuid,
            scenario_category=str(item.get("category") or _phase_to_category(item.get("phase"))),
            difficulty_level=_clamp_int(item.get("difficulty_level"), 1, 3, default=1),
            context=str(item.get("situation") or item.get("context") or item.get("her_words") or "关系互动场景"),
            their_words=str(item.get("her_words") or item.get("their_words") or item.get("situation") or ""),
            their_behavior=item.get("her_behavior") or item.get("their_behavior"),
            emotion_tags_json=json.dumps([
                {
                    "spectrum": _emotion_to_spectrum(str(item.get("her_emotion") or "")),
                    "word": str(item.get("her_emotion") or "情绪线索"),
                    "intensity": _clamp_int(item.get("emotion_intensity"), 1, 10, default=5),
                }
            ], ensure_ascii=False),
            hidden_need=item.get("her_need") or item.get("hidden_need"),
            need_urgency=_clamp_int(item.get("need_urgency"), 1, 10, default=5),
            attachment_signal=item.get("attachment_style") or item.get("attachment_signal"),
            boundary_test_level=_clamp_int(item.get("boundary_test_level"), 1, 10, default=3),
            bad_response=str(item.get("wrong_response") or item.get("bad_response") or "嗯"),
            bad_response_reason=item.get("wrong_reason") or item.get("bad_response_reason"),
            good_response_soft=str(item.get("ideal_response") or item.get("better_response") or "我听到了，你愿意多说一点吗？"),
            good_response_tension=item.get("better_response") or item.get("good_response_tension"),
            good_response_humor=item.get("humor_response") or item.get("good_response_humor"),
            principle_ref=item.get("tool_used") or item.get("principle_ref"),
            source=path.name,
        )
        session.add(sample)
        count += 1
    logger.info(f"导入样本 {count} 条: {path.name}")
    return count


def import_resource_file(session: Session, path: Path, resource_type: str) -> int:
    if not path.exists():
        logger.warning(f"资源文件不存在，跳过: {path}")
        return 0
    data = _load_json(path)
    count = 0
    for item in data.get("items", []):
        source_id = str(item.get("id") or uuid.uuid4())
        resource_uuid = f"json:{resource_type}:{source_id}"
        if _resource_exists(session, resource_uuid):
            continue
        resource = ResourceLibrary(
            resource_uuid=resource_uuid,
            type=resource_type,
            category=str(item.get("category") or item.get("subcategory") or "未分类"),
            title=item.get("title") or item.get("name") or item.get("subcategory"),
            content=str(item.get("content") or item.get("description") or ""),
            emotional_tone_json=json.dumps(item.get("tags") or [], ensure_ascii=False),
            emotional_intensity=_clamp_int(item.get("rating") or item.get("danger_level"), 1, 10, default=5),
            applicable_scene=item.get("when_to_use") or item.get("trigger_situation") or item.get("applicable_scenario"),
            difficulty_level=_danger_to_difficulty(item.get("danger_level")),
            usage_tip=item.get("moral") or item.get("variation") or item.get("example_context"),
            effectiveness_rating=_clamp_int(item.get("rating"), 1, 10, default=7),
            review_status="published" if _clamp_int(item.get("rating"), 1, 10, default=7) >= 7 else "reviewed",
            source=path.name,
            tags=",".join(str(tag) for tag in item.get("tags", [])) if isinstance(item.get("tags"), list) else None,
        )
        session.add(resource)
        count += 1
    logger.info(f"导入资源 {count} 条: {path.name}")
    return count


def _load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _sample_exists(session: Session, sample_uuid: str) -> bool:
    return session.exec(select(InteractionSample).where(InteractionSample.sample_uuid == sample_uuid)).first() is not None


def _resource_exists(session: Session, resource_uuid: str) -> bool:
    return session.exec(select(ResourceLibrary).where(ResourceLibrary.resource_uuid == resource_uuid)).first() is not None


def _clamp_int(value: Any, low: int, high: int, default: int) -> int:
    try:
        number = int(value)
    except (TypeError, ValueError):
        number = default
    return max(low, min(high, number))


def _danger_to_difficulty(value: Any) -> int:
    danger = _clamp_int(value, 1, 10, default=3)
    if danger <= 3:
        return 1
    if danger <= 7:
        return 2
    return 3


def _phase_to_category(phase: Any) -> str:
    mapping = {0: "初识", 1: "初识", 2: "暧昧", 3: "暧昧", 4: "热恋", 5: "平淡", 6: "冲突", 7: "修复", 8: "热恋"}
    return mapping.get(_clamp_int(phase, 0, 8, default=1), "暧昧")


def _emotion_to_spectrum(emotion: str) -> str:
    if any(key in emotion for key in ["喜", "开心", "期待", "好奇", "愉悦"]):
        return "喜"
    if any(key in emotion for key in ["爱", "心动", "喜欢", "依恋"]):
        return "爱"
    if any(key in emotion for key in ["怕", "焦虑", "担心", "紧张"]):
        return "惧"
    if any(key in emotion for key in ["怒", "不满", "生气"]):
        return "怒"
    if any(key in emotion for key in ["羞", "尴尬", "愧疚"]):
        return "羞"
    if any(key in emotion for key in ["惊", "意外"]):
        return "惊"
    return "哀"


if __name__ == "__main__":
    import_all()
