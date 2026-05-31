"""Content source discovery and legacy fallback helpers."""
from __future__ import annotations

from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parents[2]
CONTENT_SOURCES_DIR = PROJECT_ROOT / "content_sources"

LEGACY_CONTENT_CATALOG: list[dict[str, str]] = [
    {"filename": "场景样本库完整版.json", "subdir": "raw_json", "kind": "sample_json"},
    {"filename": "话术库.json", "subdir": "raw_json", "kind": "resource_json"},
    {"filename": "段子库.json", "subdir": "raw_json", "kind": "resource_json"},
    {"filename": "故事库.json", "subdir": "raw_json", "kind": "resource_json"},
    {"filename": "游戏库.json", "subdir": "raw_json", "kind": "resource_json"},
    {"filename": "知识库.json", "subdir": "raw_json", "kind": "knowledge_json"},
    {"filename": "对话语料库.json", "subdir": "raw_json", "kind": "dialogue_json"},
    {"filename": "情绪词典完整版.json", "subdir": "raw_json", "kind": "emotion_json"},
    {"filename": "从默认沉默到无话不谈：完整深度互动手册.md", "subdir": "raw_markdown", "kind": "legacy_manual"},
    {"filename": "世界顶级参考方案.md", "subdir": "raw_markdown", "kind": "reference_plan"},
    {"filename": "系统架构文档.md", "subdir": "raw_markdown", "kind": "architecture"},
    {"filename": "实施路线图.md", "subdir": "raw_markdown", "kind": "roadmap"},
    {"filename": "对比引擎使用指南.md", "subdir": "raw_markdown", "kind": "legacy_guide"},
    {"filename": "从默认沉默到无话不谈：完整深度互动手册.html", "subdir": "raw_html", "kind": "legacy_manual_html"},
    {"filename": "对比引擎核心.js", "subdir": "legacy_js", "kind": "legacy_engine"},
    {"filename": "定时调度器.js", "subdir": "legacy_js", "kind": "legacy_scheduler"},
]


def resolve_source_path(
    filename: str,
    subdir: str,
    *,
    content_sources_dir: Path | None = None,
    project_root: Path | None = None,
) -> Path:
    """Prefer structured content_sources assets and fall back to legacy root files."""
    base_dir = content_sources_dir or CONTENT_SOURCES_DIR
    root_dir = project_root or PROJECT_ROOT
    preferred = base_dir / subdir / filename
    if preferred.exists():
        return preferred
    return root_dir / filename


def audit_content_sources(
    *,
    content_sources_dir: Path | None = None,
    project_root: Path | None = None,
) -> dict[str, Any]:
    """Return structured-vs-legacy status for known source assets."""
    base_dir = content_sources_dir or CONTENT_SOURCES_DIR
    root_dir = project_root or PROJECT_ROOT
    assets: list[dict[str, Any]] = []
    by_subdir: dict[str, dict[str, int]] = {}

    for item in LEGACY_CONTENT_CATALOG:
        subdir = item["subdir"]
        structured_path = base_dir / subdir / item["filename"]
        legacy_path = root_dir / item["filename"]
        structured_exists = structured_path.exists()
        legacy_exists = legacy_path.exists()
        status = "structured" if structured_exists else "fallback" if legacy_exists else "missing"
        by_subdir.setdefault(subdir, {"structured": 0, "fallback": 0, "missing": 0})
        by_subdir[subdir][status] += 1
        assets.append({
            "filename": item["filename"],
            "kind": item["kind"],
            "subdir": subdir,
            "status": status,
            "structured_exists": structured_exists,
            "legacy_fallback_exists": legacy_exists,
            "active_path": str(structured_path if structured_exists else legacy_path),
        })

    structured_count = sum(1 for asset in assets if asset["status"] == "structured")
    fallback_count = sum(1 for asset in assets if asset["status"] == "fallback")
    missing_count = sum(1 for asset in assets if asset["status"] == "missing")
    return {
        "principle": "content_sources is the preferred source root; project-root files remain a compatibility fallback until each asset is migrated.",
        "content_sources_dir": str(base_dir),
        "total_known_assets": len(assets),
        "structured_count": structured_count,
        "fallback_count": fallback_count,
        "missing_count": missing_count,
        "completion_ratio": round(structured_count / max(len(assets), 1), 3),
        "by_subdir": by_subdir,
        "assets": assets,
    }
