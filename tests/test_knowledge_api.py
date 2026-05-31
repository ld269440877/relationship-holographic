from pathlib import Path

from sqlmodel import Session, select

from backend.api.knowledge import get_entry, latest_import_batch, list_entries, list_sections, visual_map
from backend.database.connection import create_db_and_tables, engine
from backend.database.import_knowledge_content import import_knowledge_json, import_markdown_manual
from backend.models.knowledge import KnowledgeEntry


def test_knowledge_import_and_api_smoke(tmp_path: Path):
    create_db_and_tables()
    unique = str(abs(hash(str(tmp_path))))
    knowledge_file = tmp_path / "knowledge.json"
    knowledge_file.write_text(
        f'{{"sections":[{{"id":"sec_{unique}","name":"单元知识{unique}","icon":"📚","description":"测试分区","items":[{{"id":"entry_{unique}","name":"共情原则{unique}","subtitle":"先接住情绪","definition":"先回应情绪，再处理事情。","common_mistakes":["急着讲道理"],"tools":["共情"]}}]}}]}}',
        encoding="utf-8",
    )
    markdown_file = tmp_path / f"manual_{unique}.md"
    markdown_file.write_text("# 旧手册章节\n\n这里是旧手册内容。\n\n## 子章节\n\n更多内容。", encoding="utf-8")

    with Session(engine) as session:
        summary = import_knowledge_json(session, knowledge_file)
        md_summary = import_markdown_manual(session, markdown_file)
        session.commit()
        assert summary["sections"] == 1
        assert summary["entries"] == 1
        assert md_summary["sections"] == 1
        assert md_summary["entries"] >= 1

        # 幂等：重复导入不应新增 entry。
        repeated = import_knowledge_json(session, knowledge_file)
        assert repeated["entries"] == 0
        assert repeated["skipped"] >= 1

        sections = list_sections(session)
        assert any(s["name"] == f"单元知识{unique}" for s in sections)
        entry = session.exec(select(KnowledgeEntry).where(KnowledgeEntry.entry_uuid == f"knowledge:json:entry_{unique}")).first()
        assert entry is not None
        entries = list_entries(section_id=entry.section_id, q=f"共情原则{unique}", session=session)
        assert any(e["title"] == "共情原则" for e in entries)
        assert all(unique not in e["title"] for e in entries)
        assert all(e.get("learning") for e in entries)
        detail = get_entry(entry.id, session)
        assert "先回应情绪" in detail["content"]
        latest = latest_import_batch(session)
        assert latest["principle"].startswith("SQLite")
        visual = visual_map(session)
        assert visual["concept_graph"]["nodes"]
        assert visual["classification_tree"]
        assert len(visual["five_w_two_h_cards"]) == 7
        assert any(item["tool"] == "5W2H" for item in visual["tool_fit_map"])
        assert visual["coverage"]["entries"] >= 1


def test_content_sources_path_prefers_structured_directory(tmp_path: Path, monkeypatch):
    import backend.database.import_knowledge_content as importer

    content_sources = tmp_path / "content_sources"
    structured = content_sources / "raw_json"
    structured.mkdir(parents=True)
    preferred = structured / "知识库.json"
    preferred.write_text("{}", encoding="utf-8")
    monkeypatch.setattr(importer, "CONTENT_SOURCES_DIR", content_sources)
    monkeypatch.setattr(importer, "PROJECT_ROOT", tmp_path)

    assert importer._source_path("知识库.json", "raw_json") == preferred
