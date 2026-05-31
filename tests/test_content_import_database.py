import json
from pathlib import Path

from sqlmodel import Session, select

from backend.database.connection import create_db_and_tables, engine
from backend.database.content_sources import audit_content_sources, resolve_source_path
from backend.database.import_json_content import import_resource_file, import_samples
from backend.models.resource import ResourceLibrary
from backend.models.sample import InteractionSample


def test_json_sample_and_resource_imports_are_idempotent(tmp_path: Path):
    create_db_and_tables()
    unique = str(abs(hash(str(tmp_path))))
    sample_file = tmp_path / "samples.json"
    sample_file.write_text(
        json.dumps(
            {
                "samples": [
                    {
                        "id": f"sample_{unique}",
                        "category": "暧昧",
                        "difficulty_level": 2,
                        "situation": "线上聊天，对方用轻松语气试探邀约。",
                        "her_words": "今天外面好舒服，适合出去走走。",
                        "her_behavior": "语气轻快，带一点期待。",
                        "her_emotion": "期待",
                        "emotion_intensity": 6,
                        "her_need": "希望你承接邀请信号",
                        "attachment_style": "安全型",
                        "wrong_response": "嗯。",
                        "ideal_response": "听起来你今天挺想出去透透气，要不要一起走走？",
                    }
                ]
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )
    resource_file = tmp_path / "resources.json"
    resource_file.write_text(
        json.dumps(
            {
                "items": [
                    {
                        "id": f"resource_{unique}",
                        "category": "破冰",
                        "title": f"轻邀请{unique}",
                        "content": "把天气线索转成低压力邀请。",
                        "tags": ["轻松", "邀约"],
                        "rating": 8,
                        "when_to_use": "初识或暧昧早期",
                    }
                ]
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )

    with Session(engine) as session:
        first_samples = import_samples(session, sample_file)
        first_resources = import_resource_file(session, resource_file, "flirty")
        session.commit()
        second_samples = import_samples(session, sample_file)
        second_resources = import_resource_file(session, resource_file, "flirty")
        session.commit()

        imported_sample = session.exec(
            select(InteractionSample).where(InteractionSample.sample_uuid == f"json:sample_{unique}")
        ).first()
        imported_resource = session.exec(
            select(ResourceLibrary).where(ResourceLibrary.resource_uuid == f"json:flirty:resource_{unique}")
        ).first()

    assert first_samples == 1
    assert first_resources == 1
    assert second_samples == 0
    assert second_resources == 0
    assert imported_sample is not None
    assert imported_sample.hidden_need == "希望你承接邀请信号"
    assert imported_resource is not None
    assert imported_resource.effectiveness_rating == 8


def test_json_importers_skip_missing_files(tmp_path: Path):
    create_db_and_tables()
    with Session(engine) as session:
        assert import_samples(session, tmp_path / "missing_samples.json") == 0
        assert import_resource_file(session, tmp_path / "missing_resources.json", "joke") == 0


def test_content_source_audit_prefers_structured_assets_with_legacy_fallback(tmp_path: Path):
    content_sources = tmp_path / "content_sources"
    raw_json = content_sources / "raw_json"
    raw_json.mkdir(parents=True)
    structured = raw_json / "知识库.json"
    structured.write_text("{}", encoding="utf-8")
    fallback = tmp_path / "话术库.json"
    fallback.write_text("{}", encoding="utf-8")

    assert resolve_source_path(
        "知识库.json",
        "raw_json",
        content_sources_dir=content_sources,
        project_root=tmp_path,
    ) == structured
    assert resolve_source_path(
        "话术库.json",
        "raw_json",
        content_sources_dir=content_sources,
        project_root=tmp_path,
    ) == fallback

    audit = audit_content_sources(content_sources_dir=content_sources, project_root=tmp_path)

    assert audit["structured_count"] >= 1
    assert audit["fallback_count"] >= 1
    assert audit["by_subdir"]["raw_json"]["structured"] >= 1
    assert audit["by_subdir"]["raw_json"]["fallback"] >= 1
