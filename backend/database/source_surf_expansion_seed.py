"""Seed curated source-surf anchors and the project trajectory guide.

The seed is metadata-first: it stores links, titles, summaries, short excerpts,
structured analysis, and project-original source cards. It never stores
third-party full text.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import sqlite3
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any

from backend.database.connection import DB_PATH, create_db_and_tables

PIPELINE_VERSION = "source_surf_expansion_v1"
PIPELINE_SOURCE = "project_original:source_surf_expansion_v1"
SOURCE_POLICY = "link_title_summary_short_excerpt_structured_analysis_local_original_rewrite_only"
TRAJECTORY_PHRASE = "任何事情的发展都没有奇迹，只有轨迹"
TRAJECTORY_SECTION_UUID = "knowledge_project_trajectory_guide_v1"
TRAJECTORY_ENTRY_UUID = "knowledge_entry_no_miracle_only_trajectory_v1"

ALLOWED_USE = [
    "sourceTitle",
    "sourceUrl",
    "shortExcerpt",
    "summary",
    "structuredAnalysis",
    "localOriginalRewrite",
    "templateMapping",
]
DISALLOWED_USE = [
    "default_full_text_copy",
    "private_chat_raw_text",
    "unlicensed_bulk_copy",
    "paywalled_bulk_copy",
    "case_without_boundary_exit",
]

EXPANSION_SOURCES: tuple[dict[str, Any], ...] = (
    {
        "name": "One Love Foundation",
        "url": "https://www.joinonelove.org/learn/",
        "group": "健康关系教育",
        "summary": "健康与不健康关系信号教育入口，适合训练边界、警讯识别、同意与安全退出。",
        "structure": "关系教育文章、警讯清单、课程活动、校园教育资源。",
        "quality_notes": "公益教育来源；只提炼信号分类与本地原创训练案例，不复制原文清单。",
        "themes": ("健康关系", "危险信号", "边界同意", "安全退出"),
        "scenes": ("初识", "暧昧", "冲突", "修复"),
    },
    {
        "name": "Relate UK",
        "url": "https://www.relate.org.uk/",
        "group": "伴侣与家庭支持",
        "summary": "英国关系支持机构，覆盖伴侣沟通、家庭压力、分离与修复等议题。",
        "structure": "咨询服务、关系建议、主题文章、课程与支持入口。",
        "quality_notes": "适合做关系压力和修复路径参考；医疗/咨询替代性需明确排除。",
        "themes": ("伴侣沟通", "家庭压力", "分离修复", "长期连接"),
        "scenes": ("冲突", "修复", "承诺", "平淡"),
    },
    {
        "name": "Esther Perel",
        "url": "https://www.estherperel.com/",
        "group": "关系访谈与课程",
        "summary": "关系治疗师 Esther Perel 的文章、播客和课程入口，适合学习欲望、亲密、背叛修复和叙事视角。",
        "structure": "文章、播客、课程、关系卡牌、公开访谈。",
        "quality_notes": "作为叙事和关系语言参考；不保存播客逐字稿全文。",
        "themes": ("欲望", "亲密叙事", "背叛修复", "关系语言"),
        "scenes": ("热恋", "承诺", "冲突", "修复"),
    },
    {
        "name": "Where Should We Begin?",
        "url": "https://www.estherperel.com/podcast",
        "group": "关系播客",
        "summary": "真实伴侣会谈式播客入口，适合抽象出冲突循环、深层需要和修复转折。",
        "structure": "播客分集、主题导读、关系困境叙事。",
        "quality_notes": "只记录分集链接和结构化观察，不搬运逐字内容。",
        "themes": ("真实对话", "冲突循环", "深层情绪", "修复转折"),
        "scenes": ("冲突", "修复", "承诺", "复联"),
    },
    {
        "name": "The School of Life Relationships",
        "url": "https://www.theschooloflife.com/article-categories/relationships/",
        "group": "关系哲学与心理科普",
        "summary": "以关系心理、亲密困境和自我理解为核心的短文与课程入口。",
        "structure": "关系文章、课程、书籍、视频和练习材料。",
        "quality_notes": "适合做概念解释和反思问题，不作为实证研究主证据。",
        "themes": ("自我理解", "亲密困境", "沟通反思", "关系哲学"),
        "scenes": ("初识", "热恋", "平淡", "承诺"),
    },
    {
        "name": "NVC Academy",
        "url": "https://nvctraining.com/",
        "group": "沟通与情绪教育",
        "summary": "非暴力沟通课程和训练资源入口，适合扩展感受、需要、请求和选择出口模板。",
        "structure": "课程、文章、训练材料、公开活动。",
        "quality_notes": "适合方法论映射；项目只保存原创改写案例和来源链接。",
        "themes": ("非暴力沟通", "感受需要", "请求表达", "同理倾听"),
        "scenes": ("初识", "冲突", "修复", "分歧"),
    },
    {
        "name": "Mediation Center NVC Resources",
        "url": "https://www.mediateyourlife.com/resources/",
        "group": "冲突调解训练",
        "summary": "冲突调解和非暴力沟通资源入口，适合训练共同问题定义、降温和多方视角。",
        "structure": "资源清单、训练材料、调解方法、课程入口。",
        "quality_notes": "适合修复和分歧场景；需避免把调解话术包装成操控。",
        "themes": ("冲突调解", "多方视角", "降温", "共同问题"),
        "scenes": ("冲突", "修复", "分歧", "承诺"),
    },
    {
        "name": "Love Is Respect",
        "url": "https://www.loveisrespect.org/",
        "group": "安全关系教育",
        "summary": "面向亲密关系安全、尊重、边界和求助的教育入口。",
        "structure": "安全指南、边界说明、求助资源、关系测评。",
        "quality_notes": "适合作为安全红线来源；涉及危机场景时必须提示寻求现实支持。",
        "themes": ("尊重", "安全关系", "红线识别", "求助资源"),
        "scenes": ("初识", "暧昧", "冲突", "分歧"),
    },
    {
        "name": "Verywell Mind Relationships",
        "url": "https://www.verywellmind.com/relationships-4157190",
        "group": "心理科普平台",
        "summary": "关系、依恋、沟通和心理健康科普入口，适合作为用户友好解释和练习主题来源。",
        "structure": "主题文章、心理健康导读、关系建议、专家审阅内容。",
        "quality_notes": "适合做科普层摘要；诊断性内容必须降级为非医疗学习。",
        "themes": ("依恋", "沟通", "心理健康", "关系维护"),
        "scenes": ("初识", "热恋", "冲突", "平淡"),
    },
    {
        "name": "Psychology Today Relationships",
        "url": "https://www.psychologytoday.com/us/basics/relationships",
        "group": "心理科普平台",
        "summary": "关系基础主题入口，覆盖吸引、沟通、伴侣和心理机制等大众科普。",
        "structure": "主题百科、博客、专家文章和实践建议。",
        "quality_notes": "作者质量不均，采集时需逐条审查；只作主题导航和结构参考。",
        "themes": ("关系基础", "吸引", "伴侣沟通", "心理机制"),
        "scenes": ("初识", "暧昧", "热恋", "承诺"),
    },
    {
        "name": "Greater Good in Action",
        "url": "https://ggia.berkeley.edu/",
        "group": "心理练习库",
        "summary": "伯克利 Greater Good 的练习库，适合把感恩、同理、积极倾听转化为训练任务。",
        "structure": "练习卡、时间成本、研究依据、操作步骤。",
        "quality_notes": "适合练习设计；不复制练习全文，转为项目原创任务。",
        "themes": ("积极倾听", "感恩", "同理", "连接练习"),
        "scenes": ("初识", "热恋", "平淡", "修复"),
    },
    {
        "name": "Hidden Brain Relationships",
        "url": "https://hiddenbrain.org/",
        "group": "心理播客",
        "summary": "心理学播客入口，部分分集涉及关系、偏见、沟通和自我叙事。",
        "structure": "播客分集、文字导读、主题分类、研究采访。",
        "quality_notes": "只登记分集链接和结构化观察，不存逐字稿全文。",
        "themes": ("心理机制", "自我叙事", "沟通偏差", "关系选择"),
        "scenes": ("初识", "分歧", "冲突", "承诺"),
    },
    {
        "name": "OpenStax Psychology 2e",
        "url": "https://openstax.org/details/books/psychology-2e",
        "group": "开放教材",
        "summary": "开放心理学教材，可作为情绪、学习、社会心理和发展心理的基础知识锚点。",
        "structure": "开放教材、章节、术语、测验、教师资源。",
        "quality_notes": "开放许可教材，仍需按章节引用并避免无边界复制。",
        "themes": ("社会心理", "情绪", "学习机制", "发展心理"),
        "scenes": ("初识", "冲突", "平淡", "承诺"),
    },
    {
        "name": "Hugging Face Emotion Datasets",
        "url": "https://huggingface.co/datasets?search=emotion",
        "group": "开放数据导航",
        "summary": "情绪识别数据集导航入口，适合寻找可许可的情绪分类和对话情绪样本。",
        "structure": "数据集索引、许可证、字段说明、下载与使用示例。",
        "quality_notes": "只作为导航；实际入库前逐项核对 license、隐私和语言适配。",
        "themes": ("情绪识别", "开放数据", "语义检索", "模型评估"),
        "scenes": ("初识", "冲突", "修复", "平淡"),
    },
    {
        "name": "EmpatheticDialogues Dataset",
        "url": "https://github.com/facebookresearch/EmpatheticDialogues",
        "group": "开放对话数据",
        "summary": "共情对话研究数据入口，适合研究情绪标签、回应策略和对话评价。",
        "structure": "论文链接、数据说明、代码仓库、许可说明。",
        "quality_notes": "使用前必须核对许可证和数据适用范围；不直接展示原始对话为训练卡。",
        "themes": ("共情对话", "情绪标签", "回应策略", "数据评估"),
        "scenes": ("初识", "冲突", "修复", "复联"),
    },
    {
        "name": "KnowYourself 亲密关系",
        "url": "https://www.knowyourself.cc/",
        "group": "中文心理科普",
        "summary": "中文心理科普平台，适合参考亲密关系、依恋、边界和自我成长议题组织方式。",
        "structure": "文章、测评、课程、心理词典和社群内容。",
        "quality_notes": "中文语境友好；采集时只保留标题、链接、摘要和本地原创转化。",
        "themes": ("亲密关系", "依恋", "边界", "自我成长"),
        "scenes": ("初识", "暧昧", "热恋", "修复"),
    },
    {
        "name": "简单心理",
        "url": "https://www.jiandanxinli.com/",
        "group": "中文心理科普",
        "summary": "中文心理服务与科普平台，可作为情绪、压力、关系和咨询边界教育入口。",
        "structure": "心理科普、课程、咨询服务、测评和专题内容。",
        "quality_notes": "不替代专业咨询；用于科普摘要和训练主题映射。",
        "themes": ("情绪压力", "关系困扰", "心理科普", "求助边界"),
        "scenes": ("冲突", "修复", "平淡", "承诺"),
    },
    {
        "name": "壹心理",
        "url": "https://www.xinli001.com/",
        "group": "中文心理科普",
        "summary": "中文心理内容、课程和问答平台，可用于发现关系困惑、情绪流动和自我成长主题。",
        "structure": "文章、问答、课程、测评、心理咨询入口。",
        "quality_notes": "用户内容需严格隐私和版权过滤；默认只做来源导航和原创训练转化。",
        "themes": ("关系困惑", "情绪流动", "自我成长", "沟通练习"),
        "scenes": ("初识", "冲突", "修复", "平淡"),
    },
    {
        "name": "TED Relationships",
        "url": "https://www.ted.com/topics/relationships",
        "group": "公开视频与演讲",
        "summary": "关系主题演讲入口，适合提炼价值观、长期连接和公共表达中的故事结构。",
        "structure": "视频演讲、主题集合、演讲摘要、推荐列表。",
        "quality_notes": "只记录链接和结构化导读，不搬运字幕或逐字稿。",
        "themes": ("故事表达", "价值观", "长期连接", "公共表达"),
        "scenes": ("初识", "承诺", "平淡", "修复"),
    },
    {
        "name": "Coursera Positive Psychology",
        "url": "https://www.coursera.org/specializations/positivepsychology",
        "group": "课程入口",
        "summary": "积极心理学课程入口，可作为幸福感、关系质量和练习设计参考。",
        "structure": "课程模块、视频、测验、作业和证书路径。",
        "quality_notes": "课程内容有平台版权；本项目只存课程入口和原创学习路径映射。",
        "themes": ("积极心理", "幸福感", "练习设计", "关系质量"),
        "scenes": ("热恋", "平淡", "承诺", "修复"),
    },
    {
        "name": "MIT OpenCourseWare Social Psychology",
        "url": "https://ocw.mit.edu/search/?q=social%20psychology",
        "group": "开放课程导航",
        "summary": "社会心理学开放课程搜索入口，适合补强吸引、群体、态度和互动机制的理论背景。",
        "structure": "课程搜索、讲义、阅读材料、作业和课程页。",
        "quality_notes": "开放课程仍需按具体许可使用；这里只做导航锚点。",
        "themes": ("社会心理", "态度改变", "群体互动", "吸引机制"),
        "scenes": ("初识", "暧昧", "分歧", "承诺"),
    },
)


def backup_database(db_path: Path = DB_PATH) -> Path:
    backup_dir = db_path.parent / "backups"
    backup_dir.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    backup_path = backup_dir / f"{db_path.stem}-before-source-surf-expansion-{timestamp}{db_path.suffix}"
    shutil.copy2(db_path, backup_path)
    return backup_path


def seed(db_path: Path = DB_PATH, *, dry_run: bool = False) -> dict[str, Any]:
    if db_path == DB_PATH:
        create_db_and_tables()
    backup_path: Path | None = None
    if not dry_run:
        backup_path = backup_database(db_path)

    with sqlite3.connect(db_path) as connection:
        connection.row_factory = sqlite3.Row
        report = {
            "dry_run": dry_run,
            "version": PIPELINE_VERSION,
            "created_sources": 0,
            "updated_sources": 0,
            "created_raw_items": 0,
            "created_resource_anchors": 0,
            "updated_resource_anchors": 0,
            "created_sections": 0,
            "created_entries": 0,
            "updated_entries": 0,
            "skipped_resource_anchors": 0,
            "source_policy": SOURCE_POLICY,
            "trajectory_phrase": TRAJECTORY_PHRASE,
            "backup_path": str(backup_path) if backup_path else None,
            "sample_sources": [item["name"] for item in EXPANSION_SOURCES[:5]],
        }
        for source in EXPANSION_SOURCES:
            source_id, created, updated = _upsert_source(connection, source, dry_run=dry_run)
            report["created_sources"] += int(created)
            report["updated_sources"] += int(updated)
            report["created_raw_items"] += int(_upsert_raw_item(connection, source_id, source, dry_run=dry_run))
            anchor_created, anchor_updated, anchor_skipped = _upsert_source_anchor(connection, source, dry_run=dry_run)
            report["created_resource_anchors"] += int(anchor_created)
            report["updated_resource_anchors"] += int(anchor_updated)
            report["skipped_resource_anchors"] += int(anchor_skipped)

        section_id, section_created = _upsert_trajectory_section(connection, dry_run=dry_run)
        report["created_sections"] += int(section_created)
        entry_created, entry_updated = _upsert_trajectory_entry(connection, section_id, dry_run=dry_run)
        report["created_entries"] += int(entry_created)
        report["updated_entries"] += int(entry_updated)

        if not dry_run:
            _insert_batch(connection, report)
            connection.commit()
        else:
            connection.rollback()
    return report


def _upsert_source(connection: sqlite3.Connection, source: dict[str, Any], *, dry_run: bool) -> tuple[int, bool, bool]:
    source_uuid = _source_uuid(source)
    existing = connection.execute("SELECT id FROM source_registry WHERE source_uuid = ?", (source_uuid,)).fetchone()
    metadata = {
        "allowed": ALLOWED_USE,
        "surf_metadata": _surf_metadata(source),
        "template_version": PIPELINE_VERSION,
        "source_policy": SOURCE_POLICY,
    }
    if dry_run:
        return (-1, True, False) if not existing else (int(existing["id"]), False, True)
    if existing:
        connection.execute(
            """
            UPDATE source_registry
            SET name=?, source_type=?, url=?, trust_score=?, update_frequency=?,
                allowed_use_json=?, disallowed_use_json=?, active=1
            WHERE source_uuid=?
            """,
            (
                source["name"],
                _source_type(source),
                source["url"],
                _trust_score(source),
                "weekly",
                _json(metadata),
                _json(DISALLOWED_USE),
                source_uuid,
            ),
        )
        return int(existing["id"]), False, True
    cursor = connection.execute(
        """
        INSERT INTO source_registry (
          source_uuid, name, source_type, url, trust_score, update_frequency,
          allowed_use_json, disallowed_use_json, active, created_at
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, 1, ?)
        """,
        (
            source_uuid,
            source["name"],
            _source_type(source),
            source["url"],
            _trust_score(source),
            "weekly",
            _json(metadata),
            _json(DISALLOWED_USE),
            _now(),
        ),
    )
    return int(cursor.lastrowid), True, False


def _upsert_raw_item(connection: sqlite3.Connection, source_id: int, source: dict[str, Any], *, dry_run: bool) -> bool:
    raw_uuid = f"raw-source-surf:{uuid.uuid5(uuid.NAMESPACE_URL, source['url'] + PIPELINE_VERSION)}"
    existing = connection.execute("SELECT id FROM raw_content_items WHERE raw_uuid = ?", (raw_uuid,)).fetchone()
    if existing:
        return False
    if dry_run:
        return True
    title = f"{source['name']}｜浏览冲浪来源锚点"
    connection.execute(
        """
        INSERT INTO raw_content_items (
          raw_uuid, source_id, title, url, content_hash, raw_storage_policy,
          privacy_risk, copyright_risk, consent_status, processing_status, collected_at
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            raw_uuid,
            source_id if source_id > 0 else None,
            title,
            source["url"],
            "sha256:" + _hash("|".join([title, source["summary"], source["structure"]])),
            SOURCE_POLICY,
            _privacy_risk(source),
            _copyright_risk(source),
            "public_metadata_only",
            "source_anchor_registered",
            _now(),
        ),
    )
    return True


def _upsert_source_anchor(connection: sqlite3.Connection, source: dict[str, Any], *, dry_run: bool) -> tuple[bool, bool, bool]:
    resource = _source_anchor_payload(source)
    existing = connection.execute(
        "SELECT id FROM resource_library WHERE resource_uuid = ? OR content_unit = ?",
        (resource["resource_uuid"], resource["content_unit"]),
    ).fetchone()
    if dry_run:
        return (not bool(existing), bool(existing), False)
    if existing:
        _update_resource_anchor(connection, int(existing["id"]), resource)
        return False, True, False
    _insert_resource_anchor(connection, resource)
    return True, False, False


def _source_anchor_payload(source: dict[str, Any]) -> dict[str, Any]:
    blueprint = {
        "version": PIPELINE_VERSION,
        "source_mapping": {
            "source_name": source["name"],
            "source_url": source["url"],
            "source_group": source["group"],
            "source_policy": SOURCE_POLICY,
            "copyright_boundary": "no_third_party_full_text",
        },
        "content_role": "浏览冲浪来源锚点",
        "why_collect": f"为 {', '.join(source['themes'][:3])} 提供高质量外部入口，并转化为本地原创训练卡。",
        "what_to_store": ALLOWED_USE,
        "what_not_to_store": DISALLOWED_USE,
        "fit_scenes": list(source["scenes"]),
        "fit_themes": list(source["themes"]),
        "conversion_template": [
            "登记来源可信度和使用边界。",
            "只保存标题、链接、摘要、短摘录和结构化分析。",
            "按场景生成本地原创案例、对话对比、练习任务。",
            "用错题反馈和质量报告决定下一轮扩展。",
        ],
        "trajectory_principle": TRAJECTORY_PHRASE,
    }
    content = "\n".join(
        [
            f"来源定位：{source['name']}｜{source['group']}",
            f"来源摘要：{source['summary']}",
            f"内容结构：{source['structure']}",
            f"质量说明：{source['quality_notes']}",
            f"适用主题：{'、'.join(source['themes'])}",
            f"适用场景：{'、'.join(source['scenes'])}",
            f"采集边界：{SOURCE_POLICY}",
            f"轨迹指南：{TRAJECTORY_PHRASE}。",
            "转化路径：来源登记 -> 原始锚点 -> 结构化分析 -> 本地原创训练卡 -> 练习反馈 -> 审计报告 -> 下一轮扩展。",
        ]
    )
    signature = "|".join([PIPELINE_VERSION, source["url"], source["name"]])
    return {
        "resource_uuid": f"source-surf:{uuid.uuid5(uuid.NAMESPACE_URL, signature)}",
        "type": "media",
        "category": "浏览冲浪来源锚点",
        "title": f"{source['name']}｜来源锚点",
        "content": content,
        "emotional_tone_json": _json({"primary": "来源治理", "group": source["group"], "trajectory": TRAJECTORY_PHRASE}),
        "emotional_intensity": 3,
        "applicable_scene": str(source["scenes"][0]),
        "difficulty_level": 1,
        "gender_target": "通用",
        "attachment_suitability": "通用",
        "usage_tip": "先打开来源理解主题边界，再回到资源海洋练本地原创案例；不要把外部原文当训练卡全文。",
        "effectiveness_rating": 8,
        "source": PIPELINE_SOURCE,
        "source_url": source["url"],
        "tags": ",".join(["浏览冲浪", "高质量信息源", "来源锚点", source["group"], *source["themes"], *source["scenes"]]),
        "review_status": "published",
        "reviewer_id": "source_surf_expansion_seed",
        "source_title": source["name"],
        "source_excerpt": _short_excerpt(source),
        "source_summary": source["summary"],
        "source_license": SOURCE_POLICY,
        "quality_score": 93,
        "expression_tool_ids_json": _json([]),
        "expression_goal": "来源理解与训练转化",
        "expression_level": "D1",
        "speech_act": "来源研读 / 结构化分析 / 本地原创转化",
        "mistake_pattern": "把外部来源当全文素材搬运，或只登记链接不生成可训练结构。",
        "recommended_drills_json": _json([
            {"type": "source_scan", "prompt": f"打开 {source['name']}，只记录标题、链接和一个结构化观察。"},
            {"type": "template_mapping", "prompt": "把一个主题映射为场景故事、完整对话、低质回应、更好回应和边界出口。"},
            {"type": "audit", "prompt": "检查是否保存了第三方全文；如有，改为摘要和本地原创改写。"},
        ]),
        "case_blueprint_json": _json(blueprint),
        "variant_signature": "sha256:" + _hash(signature),
        "content_unit": "|".join(["source_surf_anchor", source["group"], source["name"]]),
        "coverage_axis": _coverage_axis(source),
        "variant_family": f"source_surf|{source['group']}",
        "case_completeness_score": 92,
        "content_fingerprint": "sha256:" + _hash(content),
    }


def _insert_resource_anchor(connection: sqlite3.Connection, resource: dict[str, Any]) -> None:
    now = _now()
    connection.execute(_RESOURCE_INSERT_SQL, _resource_values(resource, now))


def _update_resource_anchor(connection: sqlite3.Connection, resource_id: int, resource: dict[str, Any]) -> None:
    now = _now()
    connection.execute(
        """
        UPDATE resource_library
        SET type=?, category=?, title=?, content=?, emotional_tone_json=?,
            emotional_intensity=?, applicable_scene=?, difficulty_level=?,
            gender_target=?, attachment_suitability=?, usage_tip=?,
            effectiveness_rating=?, source=?, source_url=?, tags=?,
            review_status=?, reviewer_id=?, reviewed_at=?, published_at=?,
            source_title=?, source_excerpt=?, source_summary=?, source_license=?,
            content_fingerprint=?, quality_score=?, expression_tool_ids_json=?,
            expression_goal=?, expression_level=?, speech_act=?, mistake_pattern=?,
            recommended_drills_json=?, case_blueprint_json=?, variant_signature=?,
            content_unit=?, coverage_axis=?, variant_family=?, case_completeness_score=?
        WHERE id=?
        """,
        _resource_values(resource, now, include_uuid=False) + (resource_id,),
    )


_RESOURCE_INSERT_SQL = """
    INSERT INTO resource_library (
      resource_uuid, type, category, title, content, emotional_tone_json,
      emotional_intensity, applicable_scene, difficulty_level, gender_target,
      attachment_suitability, usage_tip, effectiveness_rating, source, source_url,
      tags, created_at, review_status, reviewer_id, reviewed_at, published_at,
      source_title, source_excerpt, source_summary, source_license, content_fingerprint,
      quality_score, expression_tool_ids_json, expression_goal, expression_level,
      speech_act, mistake_pattern, recommended_drills_json, case_blueprint_json,
      variant_signature, content_unit, coverage_axis, variant_family,
      case_completeness_score
    )
    VALUES (
      ?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?
    )
"""


def _resource_values(resource: dict[str, Any], now: str, *, include_uuid: bool = True) -> tuple[Any, ...]:
    values: tuple[Any, ...] = (
        resource["type"],
        resource["category"],
        resource["title"],
        resource["content"],
        resource["emotional_tone_json"],
        resource["emotional_intensity"],
        resource["applicable_scene"],
        resource["difficulty_level"],
        resource["gender_target"],
        resource["attachment_suitability"],
        resource["usage_tip"],
        resource["effectiveness_rating"],
        resource["source"],
        resource["source_url"],
        resource["tags"],
        resource["review_status"],
        resource["reviewer_id"],
        now,
        now,
        resource["source_title"],
        resource["source_excerpt"],
        resource["source_summary"],
        resource["source_license"],
        resource["content_fingerprint"],
        resource["quality_score"],
        resource["expression_tool_ids_json"],
        resource["expression_goal"],
        resource["expression_level"],
        resource["speech_act"],
        resource["mistake_pattern"],
        resource["recommended_drills_json"],
        resource["case_blueprint_json"],
        resource["variant_signature"],
        resource["content_unit"],
        resource["coverage_axis"],
        resource["variant_family"],
        resource["case_completeness_score"],
    )
    if include_uuid:
        return (resource["resource_uuid"], *values[:15], now, *values[15:])
    return values


def _upsert_trajectory_section(connection: sqlite3.Connection, *, dry_run: bool) -> tuple[int, bool]:
    existing = connection.execute("SELECT id FROM knowledge_sections WHERE section_uuid = ?", (TRAJECTORY_SECTION_UUID,)).fetchone()
    if existing:
        return int(existing["id"]), False
    if dry_run:
        return -1, True
    cursor = connection.execute(
        """
        INSERT INTO knowledge_sections (
          section_uuid, name, description, icon, sort_order, source, source_id, created_at, updated_at
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            TRAJECTORY_SECTION_UUID,
            "项目发展轨迹指南",
            "把每次扩展都落成可追踪、可复盘、可验证的数据轨迹。",
            "🧭",
            12,
            PIPELINE_SOURCE,
            "local_anchor:project_trajectory_guide",
            _now(),
            _now(),
        ),
    )
    return int(cursor.lastrowid), True


def _upsert_trajectory_entry(connection: sqlite3.Connection, section_id: int, *, dry_run: bool) -> tuple[bool, bool]:
    existing = connection.execute("SELECT id FROM knowledge_entries WHERE entry_uuid = ?", (TRAJECTORY_ENTRY_UUID,)).fetchone()
    content = _trajectory_content()
    if dry_run:
        return (not bool(existing), bool(existing))
    if existing:
        connection.execute(
            """
            UPDATE knowledge_entries
            SET section_id=?, title=?, subtitle=?, content=?, summary=?, category=?,
                tags_json=?, quality_score=?, review_status=?, reviewer_id=?,
                reviewed_at=?, published_at=?, source=?, source_id=?,
                source_metadata_json=?, updated_at=?
            WHERE entry_uuid=?
            """,
            (
                section_id,
                TRAJECTORY_PHRASE,
                "项目进化不是靠一次性奇迹，而是靠每条数据和每次验证留下轨迹。",
                content,
                "把来源登记、原始锚点、结构化分析、本地原创训练卡、练习反馈、错题改写和审计报告连成闭环。",
                "项目原则 / 数据治理 / 进化路线",
                _json(["发展轨迹", "数据治理", "来源登记", "审计闭环", "世界级原则", "无奇迹只有轨迹"]),
                99,
                "published",
                "source_surf_expansion_seed",
                _now(),
                _now(),
                PIPELINE_SOURCE,
                "local_anchor:project_trajectory_guide",
                _json({"template_version": PIPELINE_VERSION, "principle": TRAJECTORY_PHRASE}),
                _now(),
                TRAJECTORY_ENTRY_UUID,
            ),
        )
        return False, True
    connection.execute(
        """
        INSERT INTO knowledge_entries (
          entry_uuid, section_id, title, subtitle, content, summary, category, tags_json,
          quality_score, review_status, reviewer_id, reviewed_at, published_at,
          source, source_id, source_metadata_json, created_at, updated_at
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            TRAJECTORY_ENTRY_UUID,
            section_id,
            TRAJECTORY_PHRASE,
            "项目进化不是靠一次性奇迹，而是靠每条数据和每次验证留下轨迹。",
            content,
            "把来源登记、原始锚点、结构化分析、本地原创训练卡、练习反馈、错题改写和审计报告连成闭环。",
            "项目原则 / 数据治理 / 进化路线",
            _json(["发展轨迹", "数据治理", "来源登记", "审计闭环", "世界级原则", "无奇迹只有轨迹"]),
            99,
            "published",
            "source_surf_expansion_seed",
            _now(),
            _now(),
            PIPELINE_SOURCE,
            "local_anchor:project_trajectory_guide",
            _json({"template_version": PIPELINE_VERSION, "principle": TRAJECTORY_PHRASE}),
            _now(),
            _now(),
        ),
    )
    return True, False


def _trajectory_content() -> str:
    return "\n".join(
        [
            f"# {TRAJECTORY_PHRASE}",
            "",
            "这句话是项目的数据进化原则：不要期待突然变好，要让每次变好都有证据、有路径、有复盘。",
            "",
            "## 项目轨迹闭环",
            "1. 来源登记：记录名称、链接、可信度、使用边界和风险。",
            "2. 原始锚点：只保存标题、URL、摘要、短摘录、结构化观察和 hash。",
            "3. 结构化分析：拆出主题、场景、情绪流、边界、表达工具和 5W2H。",
            "4. 本地原创训练卡：生成场景故事、完整对话、低质量回应、更好回应、多角度变体和练习任务。",
            "5. 练习反馈：用用户表现更新掌握模型、错题归因和推荐资源。",
            "6. 审计报告：检查重复、低质、来源健康、字段完整度和版权边界。",
            "7. 下一轮扩展：只根据缺口补数据，避免盲目堆量。",
            "",
            "## 5W2H 执行准则",
            "- Why：提升关系感知、表达选择和可迁移练习，而不是堆素材。",
            "- What：每条最小记录都要有来源、结构、场景、对话、边界和练习。",
            "- Who：资源海洋、表达工具箱、知识中枢、训练中心、AI 伴侣和错题本共同使用。",
            "- When：当某类场景、标签、表达目的或工具低于阈值时补齐。",
            "- Where：SQLite 是主真源，文档是设计索引，页面是学习入口。",
            "- How：先登记来源，再原创转化，再审核发布，再用反馈迭代。",
            "- How much：不追求一次性完美，追求每轮可验证新增、可回滚、可复盘。",
            "",
            "## 反面清单",
            "- 不把不同标签套在同一段话上伪装成变体。",
            "- 不默认搬运第三方全文。",
            "- 不让卡片只有概念，没有场景故事、对话和可练任务。",
            "- 不让页面只有数据堆，没有检索、分组、目录和详情。",
        ]
    )


def _insert_batch(connection: sqlite3.Connection, report: dict[str, Any]) -> None:
    connection.execute(
        """
        INSERT INTO content_import_batches (
          source_name, source_type, imported_sections, imported_entries,
          skipped_entries, issues_count, status, report_json, created_at
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            PIPELINE_SOURCE,
            "source_surf_expansion",
            int(report["created_sources"]) + int(report["created_raw_items"]) + int(report["created_sections"]),
            int(report["created_resource_anchors"]) + int(report["created_entries"]),
            int(report["skipped_resource_anchors"]),
            0,
            "completed",
            _json(report),
            _now(),
        ),
    )


def _surf_metadata(source: dict[str, Any]) -> dict[str, Any]:
    return {
        "group": source["group"],
        "summary": source["summary"],
        "structure": source["structure"],
        "quality_notes": source["quality_notes"],
        "themes": list(source["themes"]),
        "scenes": list(source["scenes"]),
    }


def _source_uuid(source: dict[str, Any]) -> str:
    return f"source-surf:{uuid.uuid5(uuid.NAMESPACE_URL, source['url'])}"


def _source_type(source: dict[str, Any]) -> str:
    group = str(source["group"])
    if "数据" in group:
        return "open_data"
    if "课程" in group or "教材" in group:
        return "course"
    if "播客" in group or "视频" in group:
        return "media"
    if "中文" in group:
        return "chinese_source"
    if "安全" in group:
        return "safety_education"
    return "expert_reference"


def _trust_score(source: dict[str, Any]) -> float:
    group = str(source["group"])
    if "开放教材" in group or "开放数据" in group or "健康关系教育" in group or "安全关系教育" in group:
        return 0.9
    if "中文" in group or "科普" in group:
        return 0.78
    if "播客" in group or "视频" in group:
        return 0.76
    return 0.84


def _privacy_risk(source: dict[str, Any]) -> float:
    haystack = f"{source['group']} {source['summary']} {source['quality_notes']}"
    if "用户内容" in haystack or "真实" in haystack:
        return 0.18
    return 0.03


def _copyright_risk(source: dict[str, Any]) -> float:
    haystack = f"{source['group']} {source['structure']}"
    if "播客" in haystack or "课程" in haystack or "视频" in haystack:
        return 0.42
    return 0.24


def _coverage_axis(source: dict[str, Any]) -> str:
    haystack = " ".join([*source["themes"], *source["scenes"], source["summary"]])
    if "边界" in haystack or "同意" in haystack or "安全" in haystack:
        return "boundary_consent"
    if "冲突" in haystack or "修复" in haystack:
        return "conflict_repair"
    if "情绪" in haystack or "同理" in haystack or "共情" in haystack:
        return "emotion_flow"
    if "长期" in haystack or "承诺" in haystack:
        return "long_connection"
    return "micro_signal"


def _short_excerpt(source: dict[str, Any]) -> str:
    text = f"结构导读：{source['structure']}"
    return text if len(text) <= 120 else text[:117] + "..."


def _json(data: Any) -> str:
    return json.dumps(data, ensure_ascii=False, sort_keys=True)


def _hash(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _now() -> str:
    return datetime.now().isoformat(timespec="seconds")


def main() -> None:
    parser = argparse.ArgumentParser(description="Seed source-surf expansion anchors and project trajectory guide.")
    parser.add_argument("--db", type=Path, default=DB_PATH)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    print(json.dumps(seed(args.db, dry_run=args.dry_run), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
