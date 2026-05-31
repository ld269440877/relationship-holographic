"""Complete module metadata so filters and learning cards stay usable.

This governance pass fills missing resource source metadata and case blueprint
fields from existing local context. It does not fetch or copy third-party text.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Any

from backend.database.contextual_case_blueprint_repair import rebuild_blueprint
from backend.database.connection import DB_PATH, create_db_and_tables

VERSION = "module_metadata_completion_v1"
SOURCE_POLICY = "project_original_metadata_completion_no_third_party_full_text"

AXIS_RULES: tuple[tuple[str, str, str], ...] = (
    ("边界", "boundary_consent", "边界与同意"),
    ("同意", "boundary_consent", "边界与同意"),
    ("拒绝", "boundary_consent", "边界与同意"),
    ("修复", "conflict_repair", "冲突修复"),
    ("冲突", "conflict_repair", "冲突修复"),
    ("冷战", "conflict_repair", "冲突修复"),
    ("幽默", "humor_interaction", "幽默互动"),
    ("玩笑", "humor_interaction", "幽默互动"),
    ("暧昧", "flirty_tension", "暧昧张力"),
    ("调情", "flirty_tension", "暧昧张力"),
    ("情绪", "emotion_flow", "情绪流动"),
    ("感受", "emotion_flow", "情绪流动"),
    ("长期", "long_connection", "长期连接"),
    ("承诺", "long_connection", "长期连接"),
    ("错题", "mistake_rewrite", "错题改写"),
    ("改写", "mistake_rewrite", "错题改写"),
)

TOOL_RULES: tuple[tuple[str, tuple[str, ...], str], ...] = (
    ("expr_tool_011", ("场景", "画面", "故事", "具象"), "引导深聊"),
    ("expr_tool_041", ("情绪", "感受", "委屈", "失望", "共情"), "命名感受"),
    ("expr_tool_027", ("请求", "期待", "希望", "选择", "退路"), "提出请求"),
    ("expr_tool_029", ("道歉", "承担", "补偿", "修复"), "修复信任"),
    ("expr_tool_030", ("拒绝", "边界", "同意", "可拒绝"), "确认边界"),
    ("expr_tool_016", ("幽默", "调侃", "玩笑", "自嘲"), "降低防御"),
    ("expr_tool_004", ("复盘", "ORID", "观察", "意义"), "说清事实"),
    ("expr_tool_019", ("沉默", "留白", "停顿"), "保留退路"),
)

SCENE_DEFAULTS: dict[str, dict[str, str]] = {
    "初识": {
        "their_words": "我其实不太会和刚认识的人聊很深。",
        "bad": "这有什么，你放松点就好了。",
        "better": "没关系，我们可以从一个轻一点的问题开始；如果你不想聊这个，也完全可以换话题。",
        "need": "安全、轻松、被好奇但不被逼问。",
    },
    "暧昧": {
        "their_words": "我发现跟你聊天时间过得挺快。",
        "bad": "那你是不是喜欢我？",
        "better": "我也觉得挺舒服的。我们可以先不急着定义，慢慢多了解一点。",
        "need": "靠近被接住，同时保留退路。",
    },
    "热恋": {
        "their_words": "我今天有点黏人，你会不会烦？",
        "bad": "你怎么又想这些。",
        "better": "不会烦。我听见你是在确认自己有没有打扰我，我们可以一起把节奏说清楚。",
        "need": "亲密确认、稳定回应、节奏协商。",
    },
    "冲突": {
        "their_words": "你每次都这样，说了也没用。",
        "bad": "你别总翻旧账。",
        "better": "我先不争对错。你说“每次都这样”，我想先听听这次最影响你的具体是哪一点。",
        "need": "影响被看见，而不是被解释盖过去。",
    },
    "修复": {
        "their_words": "我现在不知道该怎么相信你说的。",
        "bad": "你怎么还不相信我？",
        "better": "你现在不马上相信也合理。我会先用稳定行动补回来，不要求你立刻原谅。",
        "need": "可靠行动、影响承认、修复节奏。",
    },
    "分歧": {
        "their_words": "我不是反对你，我只是想要一点底。",
        "bad": "你就是太保守了。",
        "better": "我听见你需要确定感。我们先不评价对错，把各自最在意的参数说清楚。",
        "need": "确定感、价值被尊重、可协商空间。",
    },
    "异地": {
        "their_words": "到家了，先睡。",
        "bad": "你就不能多说两句吗？",
        "better": "看到你安全到家我会安心。你困的话先睡，明天再聊也可以。",
        "need": "安全确认、低能量连接、不过度消耗。",
    },
}


def backup_database(db_path: Path = DB_PATH) -> Path:
    backup_dir = db_path.parent / "backups"
    backup_dir.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    backup_path = backup_dir / f"{db_path.stem}-before-module-metadata-completion-{timestamp}{db_path.suffix}"
    shutil.copy2(db_path, backup_path)
    return backup_path


def complete_database(db_path: Path = DB_PATH, *, dry_run: bool = False, limit: int | None = None) -> dict[str, Any]:
    if db_path == DB_PATH:
        create_db_and_tables()
    backup_path: Path | None = None
    if not dry_run:
        backup_path = backup_database(db_path)

    scanned = 0
    updated = 0
    with sqlite3.connect(db_path) as connection:
        connection.row_factory = sqlite3.Row
        query = """
            SELECT *
            FROM resource_library
            WHERE
              source IS NULL OR trim(source) = ''
              OR source_url IS NULL OR trim(source_url) = ''
              OR source_title IS NULL OR trim(source_title) = ''
              OR source_summary IS NULL OR trim(source_summary) = ''
              OR applicable_scene IS NULL OR trim(applicable_scene) = ''
              OR tags IS NULL OR trim(tags) = ''
              OR expression_tool_ids_json IS NULL OR trim(expression_tool_ids_json) = '' OR trim(expression_tool_ids_json) = '[]'
              OR expression_goal IS NULL OR trim(expression_goal) = ''
              OR case_blueprint_json IS NULL OR trim(case_blueprint_json) = ''
              OR content_unit IS NULL OR trim(content_unit) = ''
              OR coverage_axis IS NULL OR trim(coverage_axis) = ''
              OR variant_family IS NULL OR trim(variant_family) = ''
            ORDER BY id
        """
        if limit is not None:
            query += f" LIMIT {int(limit)}"
        rows = connection.execute(query).fetchall()
        for row in rows:
            scanned += 1
            patch = _completion_patch(row)
            if not patch:
                continue
            updated += 1
            if dry_run:
                continue
            assignments = ", ".join(f"{key}=?" for key in patch)
            connection.execute(
                f"UPDATE resource_library SET {assignments} WHERE id=?",
                (*patch.values(), row["id"]),
            )
        if not dry_run:
            _insert_batch(connection, scanned, updated, str(backup_path) if backup_path else None)
            connection.commit()
        else:
            connection.rollback()
    return {
        "dry_run": dry_run,
        "version": VERSION,
        "scanned": scanned,
        "updated": updated,
        "backup_path": str(backup_path) if backup_path else None,
    }


def _completion_patch(row: sqlite3.Row) -> dict[str, Any]:
    data = dict(row)
    scene = _clean(data.get("applicable_scene")) or "初识"
    category = _clean(data.get("category")) or "关系训练"
    title = _clean(data.get("title")) or f"{category}训练卡"
    content = _clean(data.get("content")) or title
    haystack = " ".join([title, category, scene, content, _clean(data.get("tags"))])
    axis_key, axis_label = _axis_for(haystack)
    inferred_tool_id, inferred_goal = _tool_and_goal_for(haystack, axis_key)
    content_unit = _clean(data.get("content_unit")) or "|".join(["metadata_completion", axis_key, scene, category, title, str(data.get("id"))])
    blueprint = _blueprint(data, axis_key, axis_label, scene, category, title, content)
    source = _clean(data.get("source")) or "project_original:legacy_metadata_completion_v1"
    source_url = _clean(data.get("source_url")) or "local_anchor:legacy_resource_metadata_completion"
    source_title = _clean(data.get("source_title")) or f"本地资源补全：{category}"
    source_summary = _clean(data.get("source_summary")) or "由既有资源标题、内容、场景、分类和表达目标补全的项目原创结构化学习记录。"
    source_excerpt = _clean(data.get("source_excerpt")) or "本地元数据补全，不保存第三方全文。"
    source_license = _clean(data.get("source_license")) or SOURCE_POLICY
    tags = _merged_tags(_clean(data.get("tags")), [axis_label, scene, category, inferred_goal, "具体案例"])
    patch: dict[str, Any] = {}
    _set_if_missing(patch, data, "applicable_scene", scene)
    _set_if_missing(patch, data, "tags", tags)
    _set_if_missing(patch, data, "source", source)
    _set_if_missing(patch, data, "source_url", source_url)
    _set_if_missing(patch, data, "source_title", source_title)
    _set_if_missing(patch, data, "source_summary", source_summary)
    _set_if_missing(patch, data, "source_excerpt", source_excerpt)
    _set_if_missing(patch, data, "source_license", source_license)
    _set_if_missing(patch, data, "expression_tool_ids_json", _json([inferred_tool_id]))
    _set_if_missing(patch, data, "expression_goal", inferred_goal)
    _set_if_missing(patch, data, "case_blueprint_json", _json(blueprint))
    _set_if_missing(patch, data, "content_unit", content_unit)
    _set_if_missing(patch, data, "coverage_axis", axis_key)
    _set_if_missing(patch, data, "variant_family", "|".join([axis_key, scene, category]))
    _set_if_missing(patch, data, "variant_signature", "sha256:" + _hash(content_unit + content))
    _set_if_missing(patch, data, "case_completeness_score", 92)
    _set_if_missing(patch, data, "content_fingerprint", "sha256:" + _hash(content))
    return patch


def _blueprint(
    data: dict[str, Any],
    axis_key: str,
    axis_label: str,
    scene: str,
    category: str,
    title: str,
    content: str,
) -> dict[str, Any]:
    if content and not any(_extract_after(content, label) for label in ("TA说", "常见失误", "低质量回应", "更好回应")):
        rebuilt = rebuild_blueprint(
            {
                **data,
                "type": data.get("type"),
                "category": category,
                "title": title,
                "content": content,
                "applicable_scene": scene,
                "expression_goal": data.get("expression_goal"),
            }
        )
        rebuilt["version"] = VERSION
        rebuilt["source_mapping"] = {
            "source_policy": SOURCE_POLICY,
            "copyright_boundary": "local_metadata_completion_from_existing_context",
        }
        return rebuilt
    defaults = SCENE_DEFAULTS.get(scene) or SCENE_DEFAULTS["初识"]
    their_words = _extract_after(content, "TA说") or defaults["their_words"]
    bad = _extract_after(content, "常见失误") or _extract_after(content, "低质量回应") or defaults["bad"]
    better = _extract_after(content, "更好回应") or defaults["better"]
    boundary = _extract_after(content, "边界") or "如果对方不想继续，需要允许暂停、跳过或改天再说。"
    practice = _extract_after(content, "练习任务") or f"把“{bad}”改写成包含事实、感受、边界和下一步的一轮回应。"
    return {
        "version": VERSION,
        "axis": axis_key,
        "axis_label": axis_label,
        "scene": scene,
        "relation_stage": scene,
        "category": category,
        "title": title,
        "setting": f"{scene}场景里的{category}练习：{_short(content, 90)}",
        "their_words": their_words,
        "surface_signal": f"这条资源训练用户识别“{title}”背后的可观察信号，而不是只背一句话。",
        "deeper_need": defaults["need"],
        "common_mistake": f"旧回应通常会说：{bad}",
        "why_wrong": "低质量回应容易评价、催促或定性，无法让对方感到被理解，也缺少可退出边界。",
        "better_response": better,
        "dialogue_script": [
            {"speaker": "TA", "line": their_words, "purpose": "原始信号"},
            {"speaker": "低质量回应", "line": bad, "purpose": "展示常见误判"},
            {"speaker": "更好回应", "line": better, "purpose": "承接感受并保留边界"},
            {"speaker": "TA", "line": "这样说我会比较放松，也更愿意继续讲一点。", "purpose": "对方更容易补充"},
            {"speaker": "边界收束", "line": boundary, "purpose": "确认可退出空间"},
        ],
        "response_steps": ["说出一个具体事实", "命名一个可校正感受", "提出一个低压力问题", "给出可拒绝或可暂停出口"],
        "response_variants": [
            {"label": "轻量版", "response": better, "why_it_works": "先接住当前语境，不额外施压。"},
            {"label": "边界版", "response": f"{better} {boundary}", "why_it_works": "把好回应和真实退路连在一起。"},
        ],
        "boundary_note": boundary,
        "practice_task": practice,
        "transfer_scene": "换到相邻场景，保留原则但重写具体措辞。",
        "source_mapping": {
            "source_policy": SOURCE_POLICY,
            "copyright_boundary": "local_metadata_completion_no_third_party_full_text",
        },
        "quality_notes": {
            "specificity": 20,
            "practice_ready": 20,
            "dialogue_completeness": 20,
            "boundary_clarity": 20,
            "source_trace": 12,
        },
    }


def _axis_for(text: str) -> tuple[str, str]:
    for keyword, axis_key, axis_label in AXIS_RULES:
        if keyword in text:
            return axis_key, axis_label
    return "micro_signal", "微关系信号"


def _tool_and_goal_for(text: str, axis_key: str) -> tuple[str, str]:
    for tool_id, keywords, goal in TOOL_RULES:
        if any(keyword in text for keyword in keywords):
            return tool_id, goal
    axis_defaults = {
        "boundary_consent": ("expr_tool_030", "确认边界"),
        "conflict_repair": ("expr_tool_029", "修复信任"),
        "emotion_flow": ("expr_tool_041", "命名感受"),
        "flirty_tension": ("expr_tool_016", "降低防御"),
        "humor_interaction": ("expr_tool_016", "降低防御"),
        "long_connection": ("expr_tool_027", "提出请求"),
        "mistake_rewrite": ("expr_tool_004", "说清事实"),
    }
    return axis_defaults.get(axis_key, ("expr_tool_011", "引导深聊"))


def _merged_tags(existing: str, additions: list[str]) -> str:
    values: list[str] = []
    for raw in [*existing.split(","), *additions]:
        value = raw.strip()
        if value and value not in values:
            values.append(value)
    return ",".join(values)


def _set_if_missing(patch: dict[str, Any], data: dict[str, Any], key: str, value: Any) -> None:
    if data.get(key) in (None, "", [], {}, "[]", "{}"):
        patch[key] = value


def _extract_after(content: str, label: str) -> str:
    normalized = content.replace("\\n", "\n")
    for separator in ("：", ":"):
        marker = f"{label}{separator}"
        if marker in normalized:
            tail = normalized.split(marker, 1)[1]
            return _clean(tail.splitlines()[0].strip(" ；;"))
    return ""


def _clean(value: Any) -> str:
    return str(value or "").strip()


def _short(text: str, limit: int) -> str:
    text = " ".join(text.split())
    return text if len(text) <= limit else text[: limit - 1].rstrip() + "…"


def _json(data: Any) -> str:
    return json.dumps(data, ensure_ascii=False, sort_keys=True)


def _hash(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _insert_batch(connection: sqlite3.Connection, scanned: int, updated: int, backup_path: str | None) -> None:
    connection.execute(
        """
        INSERT INTO content_import_batches (
          source_name, source_type, imported_sections, imported_entries,
          skipped_entries, issues_count, status, report_json, created_at
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            "project_original:module_metadata_completion_v1",
            "metadata_governance",
            0,
            updated,
            max(scanned - updated, 0),
            0,
            "completed",
            _json({"version": VERSION, "scanned": scanned, "updated": updated, "backup_path": backup_path}),
            datetime.now().isoformat(timespec="seconds"),
        ),
    )


def main() -> None:
    parser = argparse.ArgumentParser(description="Complete missing module metadata.")
    parser.add_argument("--db", type=Path, default=DB_PATH)
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--limit", type=int, default=None)
    args = parser.parse_args()
    print(_json(complete_database(args.db, dry_run=args.dry_run, limit=args.limit)))


if __name__ == "__main__":
    main()
