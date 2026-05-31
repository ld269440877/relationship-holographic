from backend.api.evolution import _dedupe_cluster, _semantic_dedupe_clusters
from backend.core.evolution_intelligence import (
    RawDedupeCandidate,
    SafetyEventSnapshot,
    build_dedupe_report,
    build_safety_events_report,
    loads_dict,
    loads_list,
    metadata_vector_similarity,
    scheduler_next_actions,
    semantic_tokens,
)
from backend.models.evolution import RawContentItem


def test_typed_dedupe_report_combines_hash_and_semantic_clusters():
    items = [
        RawDedupeCandidate(1, "raw-a", "情绪 修复 边界 低压力 邀请", "sha256:same", "raw"),
        RawDedupeCandidate(2, "raw-b", "情绪 修复 边界 低压力 邀请", "sha256:same", "raw"),
        RawDedupeCandidate(3, "raw-c", "完全不同的标题", "sha256:other", "raw"),
    ]

    report = build_dedupe_report(items)

    assert report["summary"]["scanned"] == 3
    assert report["summary"]["ignored"] == 0
    assert report["summary"]["exact_clusters"] == 1
    assert report["summary"]["semantic_clusters"] >= 1
    assert report["summary"]["duplicate_review_needed"] == 2
    assert {cluster["kind"] for cluster in report["clusters"]} >= {"hash", "semantic_title"}


def test_typed_dedupe_report_ignores_test_and_source_anchor_noise():
    items = [
        RawDedupeCandidate(1, "raw-pytest-a", "pytest 重复标题", "sha256:test", "raw"),
        RawDedupeCandidate(2, "raw-source-anchor-a", "TED Relationships｜浏览冲浪来源锚点", "sha256:a", "source_anchor_registered"),
        RawDedupeCandidate(3, "raw_dedupe_hash_a_real", "hash duplicate copy", "sha256:test-seed", "raw"),
        RawDedupeCandidate(4, "vector-raw-seed", "边界 修复 低压力 邀请 seed", "sha256:vector-seed", "raw", "https://example.com/vector/seed"),
        RawDedupeCandidate(5, "raw-acq:anchor", "ChatRel｜修复｜冲突修复｜结构化采集锚点", "sha256:anchor", "structured_analyzed"),
        RawDedupeCandidate(6, "raw-real-a", "情绪 修复 边界 低压力 邀请", "sha256:real", "raw"),
        RawDedupeCandidate(7, "raw-real-b", "情绪 修复 边界 低压力 邀请", "sha256:real", "raw"),
    ]

    report = build_dedupe_report(items)

    assert report["summary"]["scanned"] == 2
    assert report["summary"]["ignored"] == 5
    assert report["summary"]["duplicate_review_needed"] == 2


def test_evolution_api_dedupe_compatibility_helpers_keep_legacy_shape():
    raw_a = RawContentItem(
        id=1,
        raw_uuid="legacy-a",
        title="情绪 修复 边界 低压力 邀请",
        content_hash="sha256:same",
        processing_status="raw",
    )
    raw_b = RawContentItem(
        id=2,
        raw_uuid="legacy-b",
        title="情绪 修复 边界 低压力 邀请",
        content_hash="sha256:same",
        processing_status="raw",
    )

    hash_cluster = _dedupe_cluster("hash", [raw_a, raw_b])
    semantic_clusters = _semantic_dedupe_clusters([raw_a, raw_b])

    assert hash_cluster["kind"] == "hash"
    assert hash_cluster["item_ids"] == [1, 2]
    assert semantic_clusters
    assert {cluster["kind"] for cluster in semantic_clusters} == {"semantic_title"}


def test_typed_safety_report_and_scheduler_next_actions():
    event = SafetyEventSnapshot(
        id=1,
        task_type="simulate_partner",
        source="ai_orchestrator",
        risk_level="high",
        flags_json='["manipulation", "coercion"]',
        payload_hash="sha256:test",
        payload_preview="测试",
        message="已阻断",
        alternatives_json='["尊重边界"]',
        blocked=True,
        created_at_iso="2026-05-21T00:00:00",
    )
    safety = build_safety_events_report([event])
    dedupe = {"summary": {"duplicate_review_needed": 2}}
    import_quality = {"quality_score": 61}
    batch = {"summary": {"published_assets": 0}}

    actions = scheduler_next_actions(batch, dedupe, import_quality, safety)

    assert safety["summary"]["blocked"] == 1
    assert safety["summary"]["top_flags"] == ["coercion", "manipulation"]
    assert [item["action"] for item in actions] == [
        "复核语义重复候选",
        "提升导入字段完整度",
        "审计安全硬阻断样例",
        "增加 reviewed 标注并发布训练资产",
    ]


def test_typed_json_and_token_helpers_degrade_safely():
    assert loads_list('["a"]') == ["a"]
    assert loads_list("{bad") == []
    assert loads_dict('{"score": 1}') == {"score": 1}
    assert loads_dict("[1]") == {}
    assert {"情", "绪", "repair"} <= semantic_tokens("情绪 repair!")


def test_metadata_vector_similarity_is_local_and_deterministic():
    close = metadata_vector_similarity("情绪 修复 边界 低压力 邀请", "边界 情绪 修复 温和邀请")
    far = metadata_vector_similarity("情绪 修复 边界 低压力 邀请", "数据库 迁移 覆盖率 类型检查")

    assert close > far
    assert metadata_vector_similarity("固定标题", "固定标题") == 1.0
