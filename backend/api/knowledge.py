"""结构化知识库 API。"""
import json
import re

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import or_
from sqlmodel import Session, col, desc, select

from backend.database.connection import get_session
from backend.models.knowledge import ContentImportBatch, KnowledgeEntry, KnowledgeSection

router = APIRouter(prefix="/api/knowledge", tags=["知识库"])


@router.get("/sections")
def list_sections(session: Session = Depends(get_session)) -> list[dict]:
    sections = session.exec(select(KnowledgeSection).order_by(KnowledgeSection.sort_order, KnowledgeSection.id)).all()
    return [_section_to_dict(section) for section in sections]


@router.get("/entries")
def list_entries(
    section_id: int | None = None,
    category: str | None = None,
    tag: str | None = None,
    source: str | None = None,
    q: str | None = None,
    limit: int = 50,
    session: Session = Depends(get_session),
) -> list[dict]:
    query = select(KnowledgeEntry)
    if section_id:
        query = query.where(KnowledgeEntry.section_id == section_id)
    if category:
        query = query.where(KnowledgeEntry.category == category)
    if tag:
        query = query.where(col(KnowledgeEntry.tags_json).like(f"%{tag.strip()}%"))
    if source:
        keyword = f"%{source.strip()}%"
        query = query.where(or_(
            col(KnowledgeEntry.source).like(keyword),
            col(KnowledgeEntry.source_id).like(keyword),
            col(KnowledgeEntry.source_metadata_json).like(keyword),
        ))
    if q:
        keyword = f"%{q.strip()}%"
        query = query.where(or_(
            col(KnowledgeEntry.title).like(keyword),
            col(KnowledgeEntry.subtitle).like(keyword),
            col(KnowledgeEntry.summary).like(keyword),
            col(KnowledgeEntry.content).like(keyword),
            col(KnowledgeEntry.category).like(keyword),
            col(KnowledgeEntry.tags_json).like(keyword),
            col(KnowledgeEntry.source).like(keyword),
            col(KnowledgeEntry.source_metadata_json).like(keyword),
        ))
    safe_limit = max(1, min(200, int(limit)))
    scan_limit = min(1000, max(safe_limit * 6, safe_limit))
    candidates = session.exec(query.order_by(desc(KnowledgeEntry.quality_score), KnowledgeEntry.id).limit(scan_limit)).all()
    entries = _dedupe_knowledge_entries(candidates, safe_limit)
    return [_entry_to_dict(entry, include_content=False) for entry in entries]


@router.get("/entries/{entry_id}")
def get_entry(entry_id: int, session: Session = Depends(get_session)) -> dict:
    entry = session.exec(select(KnowledgeEntry).where(KnowledgeEntry.id == entry_id)).first()
    if not entry:
        raise HTTPException(status_code=404, detail="知识条目不存在")
    return _entry_to_dict(entry, include_content=True)


@router.get("/filters")
def knowledge_filters(limit: int = 80, session: Session = Depends(get_session)) -> dict:
    """Return database-backed filter options for the knowledge center."""
    safe_limit = max(10, min(200, int(limit)))
    sections = session.exec(select(KnowledgeSection).order_by(KnowledgeSection.sort_order, KnowledgeSection.id)).all()
    entries = session.exec(select(KnowledgeEntry).order_by(desc(KnowledgeEntry.quality_score), KnowledgeEntry.id).limit(1000)).all()
    visible_entries = _dedupe_knowledge_entries(entries, 1000)
    section_counts: dict[int, int] = {}
    categories: dict[str, int] = {}
    tags: dict[str, int] = {}
    sources: dict[str, int] = {}
    keywords: dict[str, int] = {}
    for entry in visible_entries:
        section_counts[entry.section_id] = section_counts.get(entry.section_id, 0) + 1
        _count_text(categories, _display_knowledge_text(entry.category))
        _count_text(sources, _display_source_name(entry.source))
        for tag in _loads_tags(entry.tags_json):
            display_tag = _display_knowledge_text(tag)
            _count_text(tags, display_tag)
            _count_text(keywords, display_tag)
        for token in (entry.title, entry.subtitle, entry.summary, entry.category):
            _count_text(keywords, _display_knowledge_text(token or ""))
    section_options = [
        {"id": section.id, "value": str(section.id), "label": _display_knowledge_text(section.name), "count": section_counts.get(section.id or 0, 0)}
        for section in sections
        if section.id is not None and section_counts.get(section.id, 0) > 0 and not _is_internal_section(section)
    ]
    section_options.sort(key=lambda item: (-int(item["count"]), str(item["label"])))
    return {
        "sections": section_options[:safe_limit],
        "categories": _option_list(categories, safe_limit),
        "tags": _option_list(tags, safe_limit),
        "sources": _option_list(sources, safe_limit),
        "keywords": _option_list(keywords, safe_limit),
        "principle": "知识中枢筛选项来自当前 SQLite 条目，隐藏内部导入分区和机器编号；用户仍可手动搜索。",
    }


@router.get("/imports/latest")
def latest_import_batch(session: Session = Depends(get_session)) -> dict:
    batch = session.exec(select(ContentImportBatch).order_by(desc(ContentImportBatch.created_at)).limit(1)).first()
    if not batch:
        return {"latest": None, "principle": "SQLite 是知识内容唯一数据源；HTML 仅作为 legacy source。"}
    return {"latest": _batch_to_dict(batch), "principle": "SQLite 是知识内容唯一数据源；HTML 仅作为 legacy source。"}


@router.get("/visual-map")
def visual_map(session: Session = Depends(get_session)) -> dict:
    """把知识库转成数图结合视图：概念图谱、分类树、5W2H 和工具适用地图。"""
    sections = session.exec(select(KnowledgeSection).order_by(KnowledgeSection.sort_order, KnowledgeSection.id)).all()
    candidates = session.exec(select(KnowledgeEntry).order_by(desc(KnowledgeEntry.quality_score), KnowledgeEntry.id).limit(1000)).all()
    entries = _dedupe_knowledge_entries(candidates, 240)
    return _build_knowledge_visual_map(list(sections), list(entries))


def _section_to_dict(section: KnowledgeSection) -> dict:
    return {
        "id": section.id,
        "section_uuid": section.section_uuid,
        "name": section.name,
        "description": section.description,
        "icon": section.icon,
        "sort_order": section.sort_order,
        "source": section.source,
        "source_id": section.source_id,
    }


def _entry_to_dict(entry: KnowledgeEntry, include_content: bool) -> dict:
    tags = _loads_tags(entry.tags_json)
    data = {
        "id": entry.id,
        "entry_uuid": entry.entry_uuid,
        "section_id": entry.section_id,
        "title": _display_knowledge_text(entry.title),
        "subtitle": entry.subtitle,
        "summary": _display_knowledge_text(entry.summary or ""),
        "category": _display_knowledge_text(entry.category),
        "tags": tags,
        "quality_score": entry.quality_score,
        "source": _display_source_name(entry.source),
        "source_id": _display_source_id(entry.source_id),
        "created_at": entry.created_at.isoformat(),
        "learning": _knowledge_learning_payload(entry, tags),
    }
    if include_content:
        data["content"] = _display_knowledge_text(entry.content)
    return data


def _batch_to_dict(batch: ContentImportBatch) -> dict:
    report = {}
    if batch.report_json:
        try:
            report = json.loads(batch.report_json)
        except Exception:
            report = {}
    return {
        "id": batch.id,
        "source_name": batch.source_name,
        "source_type": batch.source_type,
        "imported_sections": batch.imported_sections,
        "imported_entries": batch.imported_entries,
        "skipped_entries": batch.skipped_entries,
        "issues_count": batch.issues_count,
        "status": batch.status,
        "report": report,
        "created_at": batch.created_at.isoformat(),
    }


def _build_knowledge_visual_map(sections: list[KnowledgeSection], entries: list[KnowledgeEntry]) -> dict:
    section_by_id = {section.id: section for section in sections}
    category_counts = _entry_counts(entries, "category")
    tag_counts = _tag_counts(entries)
    concept_graph = _knowledge_concept_graph(sections, entries, category_counts, tag_counts)
    return {
        "principle": "数负责入微：条目数、质量分、标签频次、分类覆盖；图负责直觉：概念连接、工具适配、问题路径。",
        "concept_graph": concept_graph,
        "classification_tree": _knowledge_classification_tree(sections, entries, section_by_id, category_counts),
        "five_w_two_h_cards": _knowledge_five_w_two_h(entries, category_counts, tag_counts),
        "tool_fit_map": _knowledge_tool_fit_map(entries, tag_counts),
        "coverage": {
            "sections": len(sections),
            "entries": len(entries),
            "categories": len(category_counts),
            "tags": len(tag_counts),
            "average_quality": _average_quality(entries),
        },
    }


def _knowledge_concept_graph(
    sections: list[KnowledgeSection],
    entries: list[KnowledgeEntry],
    category_counts: dict[str, int],
    tag_counts: dict[str, int],
) -> dict:
    nodes: list[dict] = [
        {"id": "root", "label": "关系动力学", "type": "root", "weight": max(len(entries), 1), "x": 50, "y": 50},
    ]
    edges: list[dict] = []
    section_positions = [(18, 24), (48, 18), (78, 28), (22, 66), (52, 76), (82, 64)]
    meaningful_sections = [
        section
        for section in sections
        if any(entry.section_id == section.id for entry in entries) and not _is_internal_section(section)
    ]
    for index, section in enumerate(meaningful_sections[:8]):
        x, y = section_positions[index % len(section_positions)]
        nodes.append({
            "id": f"section:{section.id}",
            "label": _display_knowledge_text(section.name),
            "type": "section",
            "weight": sum(1 for entry in entries if entry.section_id == section.id),
            "x": x,
            "y": y,
        })
        edges.append({"from": "root", "to": f"section:{section.id}", "label": "包含"})

    for index, (category, count) in enumerate(sorted(category_counts.items(), key=lambda item: (-item[1], item[0]))[:8]):
        nodes.append({
            "id": f"category:{category}",
            "label": _display_knowledge_text(category),
            "type": "category",
            "weight": count,
            "x": 15 + (index % 4) * 22,
            "y": 86 + (index // 4) * 8,
        })
        edges.append({"from": "root", "to": f"category:{category}", "label": "分类轴"})

    for tag, count in sorted(tag_counts.items(), key=lambda item: (-item[1], item[0]))[:10]:
        nodes.append({"id": f"tag:{tag}", "label": _display_knowledge_text(tag), "type": "tag", "weight": count})
        matched = next((entry for entry in entries if tag in _loads_tags(entry.tags_json)), None)
        if matched and matched.section_id:
            edges.append({"from": f"section:{matched.section_id}", "to": f"tag:{tag}", "label": "高频概念"})
    return {"nodes": nodes[:32], "edges": edges[:42]}


def _knowledge_classification_tree(
    sections: list[KnowledgeSection],
    entries: list[KnowledgeEntry],
    section_by_id: dict[int | None, KnowledgeSection],
    category_counts: dict[str, int],
) -> list[dict]:
    tree: list[dict] = []
    for section in sections:
        section_entries = [entry for entry in entries if entry.section_id == section.id]
        if not section_entries or _is_internal_section(section):
            continue
        categories = _entry_counts(section_entries, "category")
        tree.append({
            "id": f"section:{section.id}",
            "name": _display_knowledge_text(section.name),
            "kind": "section",
            "count": len(section_entries),
            "quality": _average_quality(section_entries),
            "children": [
                {"id": f"{section.id}:{category}", "name": _display_knowledge_text(category), "kind": "category", "count": count}
                for category, count in sorted(categories.items(), key=lambda item: (-item[1], item[0]))[:6]
            ],
        })
        if len(tree) >= 12:
            break
    if not tree and category_counts:
        tree.append({
            "id": "categories",
            "name": "分类总览",
            "kind": "fallback",
            "count": sum(category_counts.values()),
            "quality": _average_quality(entries),
            "children": [
                {"id": f"category:{category}", "name": _display_knowledge_text(category), "kind": "category", "count": count}
                for category, count in sorted(category_counts.items(), key=lambda item: (-item[1], item[0]))[:8]
            ],
        })
    for entry in entries[:20]:
        if entry.section_id not in section_by_id:
            continue
    return tree


def _is_internal_section(section: KnowledgeSection) -> bool:
    haystack = " ".join([
        section.name or "",
        section.source or "",
        section.source_id or "",
        section.section_uuid or "",
    ]).lower()
    return "测试" in haystack or "pytest" in haystack or "vector" in haystack


def _count_text(target: dict[str, int], value: str) -> None:
    clean = value.strip()
    if not clean:
        return
    target[clean] = target.get(clean, 0) + 1


def _option_list(values: dict[str, int], limit: int) -> list[dict]:
    return [
        {"value": value, "label": value, "count": count}
        for value, count in sorted(values.items(), key=lambda item: (-item[1], item[0]))[:limit]
    ]


def _knowledge_five_w_two_h(entries: list[KnowledgeEntry], category_counts: dict[str, int], tag_counts: dict[str, int]) -> list[dict]:
    top_category = _display_knowledge_text(next(iter(sorted(category_counts.items(), key=lambda item: (-item[1], item[0]))), ("暂无分类", 0))[0])
    top_tags = [tag for tag, _count in sorted(tag_counts.items(), key=lambda item: (-item[1], item[0]))[:5]]
    return [
        {"key": "why", "label": "Why", "question": "为什么学这一块？", "answer": "把关系互动从模糊感觉转为可观察、可复盘、可训练。"},
        {"key": "what", "label": "What", "question": "核心对象是什么？", "answer": f"当前知识主分类是“{top_category}”，围绕信号、情绪、需求、边界和回应策略。"},
        {"key": "who", "label": "Who", "question": "适用于谁？", "answer": "训练者、对话对象、不同依恋风格与不同关系阶段。"},
        {"key": "when", "label": "When", "question": "何时使用？", "answer": "冷场、暧昧、冲突、修复、复盘、边界表达和被爱接收时。"},
        {"key": "where", "label": "Where", "question": "发生在哪里？", "answer": "线上聊天、线下约会、长期关系、群体互动和自我复盘场景。"},
        {"key": "how", "label": "How", "question": "如何进入？", "answer": f"先分类，再用工具箱。高频概念：{'、'.join(top_tags) if top_tags else '等待知识导入'}。"},
        {"key": "how_much", "label": "How much", "question": "掌握到什么程度？", "answer": f"当前可视化覆盖 {len(entries)} 条知识，平均质量 {_average_quality(entries)} 分。"},
    ]


def _knowledge_tool_fit_map(entries: list[KnowledgeEntry], tag_counts: dict[str, int]) -> list[dict]:
    tool_rules = [
        ("侦探", "观察线索", ["观察", "线索", "微表情", "环境", "行为"]),
        ("诗人", "表达感受", ["共情", "表达", "感受", "欣赏", "画面"]),
        ("5W2H", "结构分析", ["5W2H", "分类", "问题", "结构", "复盘"]),
        ("提问", "轻验证", ["提问", "开放", "验证", "需求", "探索"]),
        ("边界", "安全降压", ["边界", "安全", "拒绝", "退路", "同意"]),
    ]
    maps: list[dict] = []
    for name, use, keywords in tool_rules:
        matched = 0
        examples: list[str] = []
        for entry in entries:
            haystack = f"{entry.title} {entry.subtitle or ''} {entry.summary or ''} {' '.join(_loads_tags(entry.tags_json))}"
            if any(keyword in haystack for keyword in keywords):
                matched += 1
                if len(examples) < 3:
                    examples.append(_display_knowledge_text(entry.title))
        tag_signal = sum(tag_counts.get(keyword, 0) for keyword in keywords)
        maps.append({
            "tool": name,
            "use": use,
            "matched_entries": matched,
            "signal": matched + tag_signal,
            "fit_score": min(100, round((matched * 8 + tag_signal * 5), 1)),
            "examples": examples,
        })
    return sorted(maps, key=lambda item: (-item["fit_score"], item["tool"]))


def _entry_counts(entries: list[KnowledgeEntry], field: str) -> dict[str, int]:
    counts: dict[str, int] = {}
    for entry in entries:
        key = str(getattr(entry, field, "") or "未分类")
        counts[key] = counts.get(key, 0) + 1
    return counts


def _tag_counts(entries: list[KnowledgeEntry]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for entry in entries:
        for tag in _loads_tags(entry.tags_json):
            counts[tag] = counts.get(tag, 0) + 1
    return counts


def _loads_tags(raw: str | None) -> list[str]:
    if not raw:
        return []
    try:
        data = json.loads(raw)
    except Exception:
        return []
    if not isinstance(data, list):
        return []
    return [
        str(item)
        for item in data
        if str(item).strip() and not str(item).lower().startswith("pytest")
    ]


def _dedupe_knowledge_entries(entries: list[KnowledgeEntry], limit: int) -> list[KnowledgeEntry]:
    unique: list[KnowledgeEntry] = []
    seen: set[str] = set()
    for entry in entries:
        if _is_internal_test_knowledge(entry):
            continue
        key = _knowledge_duplicate_key(entry)
        if key in seen:
            continue
        seen.add(key)
        unique.append(entry)
        if len(unique) >= limit:
            break
    return unique


def _knowledge_duplicate_key(entry: KnowledgeEntry) -> str:
    title = _normalize_knowledge_text(entry.title)
    summary = _normalize_knowledge_text(entry.summary or "")
    content = _normalize_knowledge_text(entry.content)
    if entry.source == "legacy_manual" or _normalize_knowledge_text(entry.category) == "旧版手册":
        return f"legacy|{title}"
    return f"{title}|{summary or content[:120]}"


def _is_internal_test_knowledge(entry: KnowledgeEntry) -> bool:
    haystack = " ".join([
        entry.source or "",
        entry.source_id or "",
        entry.entry_uuid or "",
        entry.title or "",
        entry.tags_json or "",
    ]).lower()
    return "pytest_rollback" in haystack or "用于回滚计划测试" in haystack


def _normalize_knowledge_text(value: str) -> str:
    text = _display_knowledge_text(value)
    return re.sub(r"\s+", "", text).lower()


def _display_knowledge_text(value: str) -> str:
    text = str(value or "")
    text = re.sub(r"[a-f0-9]{16,}", "", text, flags=re.IGNORECASE)
    text = re.sub(r"单元知识\d+", "单元知识", text)
    text = re.sub(r"legacy_manual", "旧版手册", text, flags=re.IGNORECASE)
    text = re.sub(r"^legacy$", "旧版迁移", text, flags=re.IGNORECASE)
    text = re.sub(r"^manual$", "手册", text, flags=re.IGNORECASE)
    text = re.sub(r"^boundary$", "边界与修复", text, flags=re.IGNORECASE)
    text = re.sub(r"\s{2,}", " ", text)
    return text.strip()


def _display_source_name(value: str) -> str:
    if str(value or "").lower().startswith("pytest"):
        return "治理样本"
    return _display_knowledge_text(value)


def _display_source_id(value: str | None) -> str | None:
    if not value:
        return None
    cleaned = _display_knowledge_text(value)
    return cleaned or None


def _knowledge_learning_payload(entry: KnowledgeEntry, tags: list[str]) -> dict:
    metadata_learning = _metadata_learning_payload(entry.source_metadata_json)
    if metadata_learning:
        return metadata_learning
    title = _display_knowledge_text(entry.title)
    summary = _display_knowledge_text(entry.summary or "")
    content = _display_knowledge_text(entry.content)
    category = _display_knowledge_text(entry.category)
    tag_text = "、".join(tags) if tags else category
    concept = summary or _first_sentence(content) or f"{title} 是关系学习中的一个结构化知识点。"
    if "边界" in tag_text or "边界" in title:
        principle = "先承接对方的空间与选择权，再提出轻量、可拒绝的验证问题。"
        method = ["说出观察到的事实", "承认对方可能需要空间", "用轻问句确认需求", "给出可退出的下一步"]
        scene = "适用于失望、冷淡、沉默、拒绝、冲突后重新靠近等场景。"
        drill = "把一句“你为什么这样”改写成“我注意到...你是需要空间，还是想让我换一种方式？”"
    elif "共情" in tag_text or "共情" in title:
        principle = "先接住情绪，再处理事情；先让人被看见，再讨论对错。"
        method = ["复述处境", "命名可能情绪", "用轻问句校准", "询问想要陪伴还是建议"]
        scene = "适用于倾诉、委屈、压力支持、低落和修复开场。"
        drill = "把一句建议型回应改写成“处境 + 感受 + 选择权”。"
    elif "修复" in tag_text or "修复" in title:
        principle = "修复不是辩解，而是承担影响、确认边界、给出具体补偿。"
        method = ["确认对方受影响的点", "承担自己可承担的部分", "说明下一次如何避免", "给一个具体补偿"]
        scene = "适用于迟到、失约、误会、冷战、争吵后的重新连接。"
        drill = "写一版“我错了”的升级版：影响 + 承担 + 改法 + 补偿。"
    else:
        principle = "把概念落到可观察事实、可练动作和可复盘证据上。"
        method = ["先定义概念", "找一个真实场景", "拆成一句可说的话", "记录结果并复盘"]
        scene = "适用于知识学习、表达训练、关系复盘和错题改写。"
        drill = f"用自己的经历写一个“{title}”的正例和反例。"
    return {
        "concept": concept,
        "principle": principle,
        "method": method,
        "scene": scene,
        "drill": drill,
    }


def _metadata_learning_payload(raw: str | None) -> dict:
    if not raw:
        return {}
    try:
        metadata = json.loads(raw)
    except Exception:
        return {}
    if not isinstance(metadata, dict):
        return {}
    learning = metadata.get("learning")
    if not isinstance(learning, dict):
        return {}
    method = learning.get("method")
    if not isinstance(method, list):
        method = []
    payload = {
        "concept": str(learning.get("concept") or ""),
        "principle": str(learning.get("principle") or ""),
        "method": [str(item) for item in method if str(item).strip()],
        "scene": str(learning.get("scene") or ""),
        "drill": str(learning.get("drill") or ""),
    }
    required = ["concept", "principle", "scene", "drill"]
    if all(payload[key] for key in required) and payload["method"]:
        return payload
    return {}


def _first_sentence(value: str) -> str:
    parts = re.split(r"[。！？\n]", value)
    return next((part.strip() for part in parts if part.strip()), "")


def _average_quality(entries: list[KnowledgeEntry]) -> float:
    if not entries:
        return 0.0
    return round(sum(entry.quality_score for entry in entries) / len(entries), 1)
