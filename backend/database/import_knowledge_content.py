"""知识内容结构化导入脚本。

把 `知识库.json` 与旧 Markdown 手册拆分为 SQLite 知识分区/条目。
HTML 文件仅保留 legacy 托管，不再作为主要数据源。
"""
from __future__ import annotations

import argparse
import json
import re
from datetime import datetime
from pathlib import Path
from typing import Any

from loguru import logger
from sqlmodel import Session, select

from backend.database.connection import PROJECT_ROOT, create_db_and_tables, engine
from backend.database.content_sources import CONTENT_SOURCES_DIR, resolve_source_path
from backend.models.knowledge import ContentImportBatch, ContentImportIssue, KnowledgeEntry, KnowledgeSection


def _source_path(filename: str, subdir: str) -> Path:
    return resolve_source_path(
        filename,
        subdir,
        content_sources_dir=CONTENT_SOURCES_DIR,
        project_root=PROJECT_ROOT,
    )


KNOWLEDGE_JSON = _source_path("知识库.json", "raw_json")
LEGACY_MARKDOWN = _source_path("从默认沉默到无话不谈：完整深度互动手册.md", "raw_markdown")


def import_all(dry_run: bool = False) -> dict[str, int]:
    create_db_and_tables()
    with Session(engine) as session:
        json_summary = import_knowledge_json(session, KNOWLEDGE_JSON, dry_run=dry_run)
        md_summary = import_markdown_manual(session, LEGACY_MARKDOWN, dry_run=dry_run)
        total = {
            "sections": json_summary["sections"] + md_summary["sections"],
            "entries": json_summary["entries"] + md_summary["entries"],
            "skipped": json_summary["skipped"] + md_summary["skipped"],
            "issues": json_summary["issues"] + md_summary["issues"],
        }
        if not dry_run:
            session.commit()
    logger.info(f"知识内容导入完成: {total}, dry_run={dry_run}")
    return total


def import_knowledge_json(session: Session, path: Path, dry_run: bool = False) -> dict[str, int]:
    summary = {"sections": 0, "entries": 0, "skipped": 0, "issues": 0}
    issues: list[tuple[str, str, str]] = []
    if not path.exists():
        return _record_batch(session, path.name, "json", summary, [("file", "error", "知识库 JSON 不存在")], dry_run)

    data = json.loads(path.read_text(encoding="utf-8"))
    for index, section_data in enumerate(data.get("sections", [])):
        source_id = str(section_data.get("id") or f"section_{index}")
        section_uuid = f"knowledge:json:{source_id}"
        section = _get_or_create_section(
            session,
            section_uuid=section_uuid,
            name=str(section_data.get("name") or "未命名分区"),
            description=section_data.get("description"),
            icon=section_data.get("icon"),
            sort_order=index,
            source="知识库.json",
            source_id=source_id,
            dry_run=dry_run,
        )
        if section is None:
            summary["skipped"] += 1
            continue
        summary["sections"] += 1
        for item_index, item in enumerate(section_data.get("items", [])):
            item_source_id = str(item.get("id") or f"{source_id}_{item_index}")
            entry_uuid = f"knowledge:json:{item_source_id}"
            if _entry_exists(session, entry_uuid):
                summary["skipped"] += 1
                continue
            content = _stringify_knowledge_item(item)
            if not content.strip():
                issues.append((item_source_id, "warning", "知识条目内容为空"))
                summary["issues"] += 1
                continue
            if not dry_run:
                session.add(KnowledgeEntry(
                    entry_uuid=entry_uuid,
                    section_id=section.id or 0,
                    title=str(item.get("name") or item.get("title") or item_source_id),
                    subtitle=item.get("subtitle"),
                    content=content,
                    summary=item.get("definition") or item.get("key_insight") or item.get("description"),
                    category=str(section_data.get("name") or "knowledge"),
                    tags_json=json.dumps(item.get("tools") or item.get("tags") or [], ensure_ascii=False),
                    quality_score=85,
                    review_status="published",
                    published_at=datetime.now(),
                    source="知识库.json",
                    source_id=item_source_id,
                    source_metadata_json=json.dumps(item, ensure_ascii=False),
                ))
            summary["entries"] += 1
    return _record_batch(session, path.name, "json", summary, issues, dry_run)


def import_markdown_manual(session: Session, path: Path, dry_run: bool = False) -> dict[str, int]:
    summary = {"sections": 0, "entries": 0, "skipped": 0, "issues": 0}
    if not path.exists():
        return _record_batch(session, path.name, "markdown", summary, [("file", "warning", "旧 Markdown 手册不存在")], dry_run)
    text = path.read_text(encoding="utf-8")
    manual_key = re.sub(r"[^a-zA-Z0-9_\-]+", "_", path.stem)
    section_uuid = f"knowledge:markdown:{manual_key}"
    section = _get_or_create_section(
        session,
        section_uuid=section_uuid,
        name="旧版完整互动手册",
        description="从旧 Markdown 手册结构化迁移而来，HTML 仅作为 legacy 展示。",
        icon="📘",
        sort_order=999,
        source=path.name,
        source_id=manual_key,
        dry_run=dry_run,
    )
    if section is None:
        summary["skipped"] += 1
        return _record_batch(session, path.name, "markdown", summary, [], dry_run)
    summary["sections"] += 1
    chunks = _split_markdown_by_heading(text)
    for index, (title, content) in enumerate(chunks):
        entry_uuid = f"knowledge:markdown:{manual_key}:{index}"
        if _entry_exists(session, entry_uuid):
            summary["skipped"] += 1
            continue
        if not dry_run:
            session.add(KnowledgeEntry(
                entry_uuid=entry_uuid,
                section_id=section.id or 0,
                title=title,
                content=content,
                summary=content[:180],
                category="legacy_manual",
                tags_json=json.dumps(["legacy", "manual"], ensure_ascii=False),
                quality_score=75,
                review_status="reviewed",
                reviewed_at=datetime.now(),
                source=path.name,
                source_id=f"{manual_key}:{index}",
                source_metadata_json=json.dumps({"heading_index": index}, ensure_ascii=False),
            ))
        summary["entries"] += 1
    return _record_batch(session, path.name, "markdown", summary, [], dry_run)


def _get_or_create_section(
    session: Session,
    *,
    section_uuid: str,
    name: str,
    description: str | None,
    icon: str | None,
    sort_order: int,
    source: str,
    source_id: str,
    dry_run: bool,
) -> KnowledgeSection | None:
    existing = session.exec(select(KnowledgeSection).where(KnowledgeSection.section_uuid == section_uuid)).first()
    if existing:
        return existing
    if dry_run:
        return KnowledgeSection(id=0, section_uuid=section_uuid, name=name)
    section = KnowledgeSection(
        section_uuid=section_uuid,
        name=name,
        description=description,
        icon=icon,
        sort_order=sort_order,
        source=source,
        source_id=source_id,
    )
    session.add(section)
    session.commit()
    session.refresh(section)
    return section


def _entry_exists(session: Session, entry_uuid: str) -> bool:
    return session.exec(select(KnowledgeEntry).where(KnowledgeEntry.entry_uuid == entry_uuid)).first() is not None


def _stringify_knowledge_item(item: dict[str, Any]) -> str:
    ordered_keys = [
        "definition", "psychological_basis", "common_mistakes", "upgrade_checkpoints",
        "real_case", "practice", "key_insight", "description", "content", "moral",
        "q", "a", "chinese", "examples", "characteristics", "in_relationship",
        "triggers", "how_to_improve", "suitable_partner", "self_test", "quote",
        "what_it_looks_like", "why_happens", "替代方式", "early_signs",
        "techniques", "vs_complaint", "vs_criticism", "warning", "note",
        "three_responses", "research_finding", "types_of_bids", "how_to_respond",
        "increase_bids", "key_principles", "six_basic_emotions", "do", "dont",
        "de_escalation_script", "rest_rules",
    ]
    lines: list[str] = []
    for key in ordered_keys:
        value = item.get(key)
        if value is None:
            continue
        title = key.replace("_", " ").title()
        if isinstance(value, list):
            lines.append(f"## {title}\n" + "\n".join(f"- {_format_value(v)}" for v in value))
        elif isinstance(value, dict):
            lines.append(f"## {title}\n" + "\n".join(f"- {k}: {_format_value(v)}" for k, v in value.items()))
        else:
            lines.append(f"## {title}\n{value}")
    return "\n\n".join(lines)


def _format_value(value: Any) -> str:
    if isinstance(value, dict | list):
        return json.dumps(value, ensure_ascii=False)
    return str(value)


def _split_markdown_by_heading(text: str) -> list[tuple[str, str]]:
    matches = list(re.finditer(r"^#{1,3}\s+(.+)$", text, flags=re.MULTILINE))
    chunks: list[tuple[str, str]] = []
    for idx, match in enumerate(matches[:120]):
        start = match.end()
        end = matches[idx + 1].start() if idx + 1 < len(matches) else len(text)
        title = match.group(1).strip()
        content = text[start:end].strip()
        if title and content:
            chunks.append((title, content))
    if not chunks and text.strip():
        chunks.append(("旧版完整互动手册", text.strip()[:20000]))
    return chunks


def _record_batch(
    session: Session,
    source_name: str,
    source_type: str,
    summary: dict[str, int],
    issues: list[tuple[str, str, str]],
    dry_run: bool,
) -> dict[str, int]:
    summary["issues"] += len(issues)
    if dry_run:
        return summary
    batch = ContentImportBatch(
        source_name=source_name,
        source_type=source_type,
        imported_sections=summary["sections"],
        imported_entries=summary["entries"],
        skipped_entries=summary["skipped"],
        issues_count=summary["issues"],
        report_json=json.dumps(summary, ensure_ascii=False),
    )
    session.add(batch)
    session.commit()
    session.refresh(batch)
    for source_id, severity, message in issues:
        session.add(ContentImportIssue(batch_id=batch.id, source_name=source_name, source_id=source_id, severity=severity, message=message))
    return summary


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    print(json.dumps(import_all(dry_run=args.dry_run), ensure_ascii=False, indent=2))
