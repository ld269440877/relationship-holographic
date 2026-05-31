"""Seed developmental emotion transition materials.

This pack turns the user-provided emotion-social development framework into
auditable project-original knowledge, an expression tool, one tool chain, and
practice resources. It keeps the material educational and non-manipulative:
the goal is emotional literacy, boundary-aware support, and developmental
scaffolding rather than persuasion or control.
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

SOURCE = "user_provided:developmental_emotion_transition_v1"
SOURCE_URL = "local_anchor:情绪社交发展_情绪流动跃迁体系"
SECTION_UUID = "knowledge_developmental_emotion_transition_v1"
TOOL_UUID = "expr_tool_064"
CHAIN_UUID = "expr_chain_developmental_emotion_transition_v1"
PIPELINE_VERSION = "developmental_emotion_transition_v1"

CORE_DIMENSIONS = [
    ("强度", "情绪的生理唤醒与主观体验强烈程度，从轻微波动到超出承载。"),
    ("效价", "愉悦、不愉悦、中性与混合效价，例如悲喜交加或又期待又害怕。"),
    ("指向", "情绪指向自我、他人、环境还是关系。"),
    ("时序", "情绪位于预期、触发、上升、高峰、下降或残余阶段。"),
]

TRANSITIONS = [
    ("同层强度跃迁", "同一情绪维度内升降级，例如担心变焦虑，或绝望降到还能呼吸。", "先承接，再调节强度。"),
    ("跨维质变跃迁", "情绪性质转化，例如愤怒下面浮出悲伤，羞耻转成可负责的内疚。", "先保证安全，再用试探式翻译。"),
    ("跨层元认知跃迁", "从情绪反应上升到模式、价值和自我调节策略。", "帮助对方把外部支架内化成自己的工具。"),
]

AGE_STAGES = [
    ("0-6岁", "安全基地与命名", ["饿", "困", "疼", "开心", "生气", "难过", "害怕", "孤单"], "用简单词命名，不做抽象反思。"),
    ("7-11岁", "规则与观点采择", ["尴尬", "内疚", "自豪", "嫉妒", "失望", "担心", "紧张", "憋屈"], "用我信息和规则帮助表达。"),
    ("12-18岁", "元情绪与身份整合", ["空虚", "迷茫", "焦虑", "被背叛", "疏离", "存在焦虑"], "允许矛盾情绪，连接身份和价值。"),
    ("18岁+", "成熟的人际情绪智慧", ["悲欣交集", "反思性接纳", "矛盾情绪", "边界中的亲密"], "用元沟通、留白、幽默和边界支持自我调节。"),
]

CONCEPTS = [
    {
        "entry_uuid": "knowledge:developmental-emotion-transition:three-layer-model",
        "title": "情绪-社交发展的三层嵌套模型",
        "category": "发展性情绪跃迁",
        "tags": ["情绪发展", "社交发展", "三层模型", "最近发展区", "关系动力学"],
        "summary": "把基本情绪、社会情绪能力和元调节信念组织成可学习、可训练、可迁移的关系能力地图。",
        "content": [
            "第一层：基本情绪与交互模式层，关注情绪表达、轮流反应、身体线索和基本安抚。",
            "第二层：社会情绪能力层，关注共情、情绪命名、观点采择、规则理解和调节策略。",
            "第三层：元层次，关注自我调节、关系信念、价值系统和人格整合。",
            "教育目标：每次共情都不是技巧表演，而是在对方最近发展区内提供支架，让情绪调节能力逐步内化。",
        ],
    },
    {
        "entry_uuid": "knowledge:developmental-emotion-transition:dimensions",
        "title": "情绪事件四维定位：强度、效价、指向、时序",
        "category": "情绪定位",
        "tags": ["情绪粒度", "强度", "效价", "指向", "时序", "情绪流动"],
        "summary": "任何情绪事件都要先定位四个维度，避免只贴一个情绪词就进入回应。",
        "content": [
            "四维定位：" + "；".join(f"{name}：{definition}" for name, definition in CORE_DIMENSIONS),
            "典型错误：只说“你生气了”却不判断强度、对象、发生阶段和背后的混合感受。",
            "训练方法：先圈事实线索，再给情绪词，再估强度，再判断当前处于触发、上升、高峰、下降还是残余。",
        ],
    },
    {
        "entry_uuid": "knowledge:developmental-emotion-transition:three-transitions",
        "title": "情绪流动的三种跃迁机制",
        "category": "情绪流动",
        "tags": ["情绪跃迁", "同化", "顺应", "内化", "情绪调节"],
        "summary": "同层强度、跨维质变和跨层元认知三类跃迁，让抽象情绪流动变成可观察路径。",
        "content": [
            "三类跃迁：" + "；".join(f"{name}：{definition}。回应原则：{rule}" for name, definition, rule in TRANSITIONS),
            "理论对应：同层强度跃迁接近同化和量变；跨维质变跃迁接近顺应；跨层元认知跃迁接近支架内化。",
            "质量边界：强唤醒时先降级，不急着做价值反思；对方沉默、防御或超出承载时必须暂停推进。",
        ],
    },
    {
        "entry_uuid": "knowledge:developmental-emotion-transition:age-scaffold",
        "title": "0-25岁情绪词汇与支架节奏",
        "category": "情绪词库",
        "tags": ["年龄阶段", "情绪词库", "适龄回应", "支架", "情绪命名"],
        "summary": "按发展阶段选择情绪词、提问深度和调节目标，避免对儿童或高压状态使用过度抽象回应。",
        "content": [
            f"{age}：{goal}。可处理词汇：{'、'.join(words)}。支架原则：{rule}"
            for age, goal, words, rule in AGE_STAGES
        ],
    },
]

SCENARIOS = [
    {
        "key": "初识不敢深聊",
        "scene": "初识",
        "setting": "刚认识的朋友说自己不太会聊很深，语气轻，但说完观察你的反应。",
        "their_words": "我其实不太会和刚认识的人聊很深。",
        "bad": "这有什么，放松点就好了，跟我不用想那么多。",
        "dimension": "强度=轻度不安；效价=负性混合中性；指向=关系；时序=预期性防御。",
        "transition": "同层强度跃迁",
        "better": "没关系，我们不用一下子聊很深。先停在轻一点的层次就好，你愿意说兴趣或最近的小事也完全够。",
        "follow": "嗯，这样我会舒服一点，至少不用马上证明自己很会聊天。",
        "support": "那我们就按舒服的节奏来；你提醒边界这件事本身就很清楚。",
    },
    {
        "key": "暧昧又期待又害怕",
        "scene": "暧昧",
        "setting": "暧昧对象说跟你聊天开心，但担心太快，表情有点害羞又紧张。",
        "their_words": "跟你聊天会有点开心，但我也怕太快。",
        "bad": "那你就是喜欢我了，别怕，我们顺其自然就行。",
        "dimension": "强度=中度；效价=正负混合；指向=关系；时序=上升期。",
        "transition": "跨维质变跃迁",
        "better": "我听见两个感觉同时在：开心，也有点怕节奏太快。我们可以先承认这份舒服，不急着把关系定义完。",
        "follow": "对，我不是不想靠近，就是怕一下子变得太确定。",
        "support": "那就先让它慢一点。你不用给结论，我也会注意不把开心变成压力。",
    },
    {
        "key": "冲突后愤怒下面的委屈",
        "scene": "修复",
        "setting": "争执后对方说话很硬，但反复提到自己没被当回事。",
        "their_words": "你每次都说知道了，但我感觉根本没被当回事。",
        "bad": "我都已经解释了，你能不能别总翻旧账？",
        "dimension": "强度=强烈；效价=负性；指向=他人与关系；时序=高峰转折。",
        "transition": "跨维质变跃迁",
        "better": "我先不急着解释。你现在听起来很生气，但更底下像是委屈：你说过很多次，却没有看到我真的改变。这个理解接近吗？",
        "follow": "对，我气的是你每次都让我觉得自己在白说。",
        "support": "这次我先承认影响。我们只定一个你能检查的小改变，不要求你马上原谅。",
    },
    {
        "key": "长期关系里的自我模式",
        "scene": "长期",
        "setting": "长期伴侣发现自己一有不确定就想反复确认，自己也觉得累。",
        "their_words": "我知道我一直问你还爱不爱我很烦，但我停不下来。",
        "bad": "你知道烦就别问了，我又没做什么。",
        "dimension": "强度=中高；效价=负性混合羞耻；指向=自我与关系；时序=循环残余。",
        "transition": "跨层元认知跃迁",
        "better": "我听见你不只是想确认我爱不爱你，也在看见自己的一个模式：不确定一来，你就会很想抓住答案。我们可以一起找一个比反复确认更稳的办法。",
        "follow": "嗯，我也不想一直这样，但我一害怕就会想问。",
        "support": "下次这种感觉上来时，你可以先说“我现在有点悬着”。我先回应感受，再一起看事实。",
    },
    {
        "key": "亲子作业崩溃",
        "scene": "亲子",
        "setting": "孩子写作业时突然把笔摔在桌上，说自己就是不会，已经接近情绪高峰。",
        "their_words": "我就是不会！你别再说了！",
        "bad": "这有什么不会的？你就是不认真。",
        "dimension": "强度=高峰；效价=负性；指向=自我与任务；时序=高峰期。",
        "transition": "同层强度跃迁",
        "better": "好，我们先停一下。你现在不是坏，也不是笨，是太急太挫败了。先喝口水，等这股劲降一点再看第一小步。",
        "follow": "我就是觉得自己怎么都做不好。",
        "support": "我听见你是在挫败，不是在故意闹。我们只看第一题的第一步，不一次解决全部。",
    },
    {
        "key": "友谊被忽略",
        "scene": "友谊",
        "setting": "朋友在聚会后说自己没事，但反复提到大家好像都在聊别人的事。",
        "their_words": "没事啦，可能我今天本来就不太会插话。",
        "bad": "你别这么敏感，大家没有针对你。",
        "dimension": "强度=中度；效价=负性；指向=关系；时序=下降后的残余。",
        "transition": "跨维质变跃迁",
        "better": "我不急着说你敏不敏感。你说“不太会插话”，听起来表面是尴尬，底下可能有点被落下的失落，对吗？",
        "follow": "嗯，就是感觉自己在不在都差不多。",
        "support": "那这个感觉挺重的。下次如果我注意到你沉默，我会主动把话题递给你一点。",
    },
    {
        "key": "职场硬撑",
        "scene": "职场",
        "setting": "同事说项目还能做，但一直强调自己在硬撑，语速变慢。",
        "their_words": "项目还能做，就是最近一直在硬撑。",
        "bad": "那你列个计划，把优先级排好就行。",
        "dimension": "强度=中高；效价=负性；指向=环境与自我；时序=上升期。",
        "transition": "跨维质变跃迁",
        "better": "我听见你说“硬撑”。事实是项目还在推进，但感受上可能已经很孤立、很累了。我们先不只谈计划，你最需要被分担的是哪一块？",
        "follow": "其实是我觉得所有东西都压到我这里。",
        "support": "那重点不是你不会安排，而是承载过多。我们先把必须你做和可以移交的部分分开。",
    },
    {
        "key": "伴侣冲突旧账",
        "scene": "伴侣冲突",
        "setting": "伴侣争执时提到旧事，说每次都是同样模式，语气又气又累。",
        "their_words": "你看，又是这样，每次最后都变成我一个人在意。",
        "bad": "你能不能别每次都上纲上线？",
        "dimension": "强度=强烈；效价=负性；指向=关系；时序=高峰转折。",
        "transition": "跨层元认知跃迁",
        "better": "这不只是这一件事了，更像一个重复模式：你一在意，就感觉自己孤立无援。我先承认这次又让你落到那个位置了。",
        "follow": "对，我累的是每次都这样。",
        "support": "我们先不争输赢，只记录这个循环：你提醒，我防御，你更孤单。下一步我先做一个可检查的小改变。",
    },
    {
        "key": "长期复盘疏远",
        "scene": "长期复盘",
        "setting": "长期关系里双方没有爆发冲突，但一方说最近好像越来越像室友。",
        "their_words": "我们最近好像也没吵架，但就是越来越像室友。",
        "bad": "老夫老妻都这样，你别想太多。",
        "dimension": "强度=中度；效价=低落；指向=关系；时序=残余与模式期。",
        "transition": "跨层元认知跃迁",
        "better": "我不想用“老夫老妻”把它盖过去。你说的更像一种长期情绪残余：没有大冲突，但连接感在慢慢变少。我们可以一起复盘最近少了哪些小连接。",
        "follow": "对，我不是要浪漫，就是感觉彼此不太看见了。",
        "support": "那我们先找一个很小的恢复动作，比如每天十分钟不处理事务，只聊今天真正有感觉的一件事。",
    },
]


def backup_database(db_path: Path = DB_PATH) -> Path:
    backup_dir = db_path.parent / "backups"
    backup_dir.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    backup_path = backup_dir / f"{db_path.stem}-before-developmental-emotion-transition-{timestamp}{db_path.suffix}"
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
            "source": SOURCE,
            "created_sections": 0,
            "created_entries": 0,
            "updated_entries": 0,
            "created_tools": 0,
            "updated_tools": 0,
            "created_chains": 0,
            "updated_chains": 0,
            "created_resources": 0,
            "skipped_resources": 0,
            "backup_path": str(backup_path) if backup_path else None,
        }
        section_id, section_created = _upsert_section(connection, dry_run=dry_run)
        report["created_sections"] += int(section_created)
        created_entries, updated_entries = _upsert_entries(connection, section_id, dry_run=dry_run)
        report["created_entries"] += created_entries
        report["updated_entries"] += updated_entries
        tool_created, tool_updated = _upsert_tool(connection, dry_run=dry_run)
        report["created_tools"] += int(tool_created)
        report["updated_tools"] += int(tool_updated)
        chain_created, chain_updated = _upsert_chain(connection, dry_run=dry_run)
        report["created_chains"] += int(chain_created)
        report["updated_chains"] += int(chain_updated)
        created_resources, skipped_resources = _seed_resources(connection, dry_run=dry_run)
        report["created_resources"] += created_resources
        report["skipped_resources"] += skipped_resources
        if not dry_run:
            _insert_batch(connection, report)
            connection.commit()
        else:
            connection.rollback()
    return report


def _upsert_section(connection: sqlite3.Connection, *, dry_run: bool) -> tuple[int, bool]:
    existing = connection.execute("SELECT id FROM knowledge_sections WHERE section_uuid=?", (SECTION_UUID,)).fetchone()
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
            SECTION_UUID,
            "发展性情绪跃迁体系",
            "以教育发展理论组织情绪词库、情绪流动、支架回应和跨层整合训练。",
            "🌱",
            18,
            SOURCE,
            SOURCE_URL,
            _now(),
            _now(),
        ),
    )
    return int(cursor.lastrowid), True


def _upsert_entries(connection: sqlite3.Connection, section_id: int, *, dry_run: bool) -> tuple[int, int]:
    created = 0
    updated = 0
    for item in CONCEPTS:
        existing = connection.execute("SELECT id FROM knowledge_entries WHERE entry_uuid=?", (item["entry_uuid"],)).fetchone()
        payload = _entry_payload(section_id, item)
        if existing:
            updated += 1
            if not dry_run:
                connection.execute(
                    """
                    UPDATE knowledge_entries
                    SET section_id=?, title=?, subtitle=?, content=?, summary=?, category=?,
                        tags_json=?, quality_score=?, review_status=?, reviewer_id=?,
                        reviewed_at=?, published_at=?, source=?, source_id=?, source_metadata_json=?, updated_at=?
                    WHERE entry_uuid=?
                    """,
                    payload + (item["entry_uuid"],),
                )
            continue
        created += 1
        if not dry_run:
            connection.execute(
                """
                INSERT INTO knowledge_entries (
                  section_id, title, subtitle, content, summary, category, tags_json,
                  quality_score, review_status, reviewer_id, reviewed_at, published_at,
                  source, source_id, source_metadata_json, updated_at, entry_uuid, created_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                payload + (item["entry_uuid"], _now()),
            )
    return created, updated


def _entry_payload(section_id: int, item: dict[str, Any]) -> tuple[Any, ...]:
    metadata = {
        "template_version": PIPELINE_VERSION,
        "source_policy": "user_provided_structured_material",
        "education_theory": ["Piaget", "Vygotsky", "emotion_development", "innate_acquired_interaction"],
    }
    return (
        section_id,
        item["title"],
        item["summary"],
        "\n".join(item["content"]),
        item["summary"],
        item["category"],
        _json(item["tags"]),
        99,
        "published",
        "developmental_emotion_transition_seed",
        _now(),
        _now(),
        SOURCE,
        SOURCE_URL,
        _json(metadata),
        _now(),
    )


def _upsert_tool(connection: sqlite3.Connection, *, dry_run: bool) -> tuple[bool, bool]:
    existing = connection.execute("SELECT id FROM expression_tools WHERE tool_uuid=?", (TOOL_UUID,)).fetchone()
    payload = _tool_payload()
    if dry_run:
        return (not bool(existing), bool(existing))
    if existing:
        connection.execute(
            """
            UPDATE expression_tools
            SET name=?, layer=?, category=?, formula=?, description=?, best_scenes_json=?,
                relationship_fit_json=?, emotion_fit_json=?, risk_flags_json=?,
                micro_steps_json=?, learning_blueprint_json=?, example_before=?,
                example_after=?, mastery_stage=?, source=?, source_url=?,
                review_status=?, quality_score=?, updated_at=?
            WHERE tool_uuid=?
            """,
            (*payload, TOOL_UUID),
        )
        return False, True
    connection.execute(
        """
        INSERT INTO expression_tools (
          tool_uuid, name, layer, category, formula, description, best_scenes_json,
          relationship_fit_json, emotion_fit_json, risk_flags_json, micro_steps_json,
          learning_blueprint_json, example_before, example_after, mastery_stage,
          source, source_url, review_status, quality_score, created_at, updated_at
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (TOOL_UUID, *payload, _now()),
    )
    return True, False


def _tool_payload() -> tuple[Any, ...]:
    return (
        "发展性情绪跃迁支架",
        "emotion",
        "情绪流动",
        "四维定位 -> 发展阶段 -> 跃迁类型 -> 支架回应 -> 内化复盘",
        "根据情绪事件的强度、效价、指向、时序和发展阶段，选择同层降级、跨维翻译或跨层整合回应。",
        _json(["初识", "暧昧", "冲突修复", "长期关系", "亲子/教育", "心理支持"]),
        _json(["情绪流动", "深度情感连接", "长期连接", "冲突修复", "边界同意"]),
        _json(["担心", "委屈", "害怕", "羞耻", "期待", "悲欣交集", "悬着"]),
        _json(["强唤醒时过早反思", "把猜测当诊断", "逼迫深聊", "忽略年龄阶段", "没有暂停出口"]),
        _json(["圈事实线索", "四维定位", "判断发展支架", "选择跃迁路径", "给可纠正回应", "复盘内化句"]),
        _json(_tool_blueprint()),
        "你就是太敏感了，别想那么复杂。",
        "我先不急着判断。事实是你刚才说到这里停了一下，感受上可能有点悬着；我们可以先把强度降下来，不急着下结论。",
        "integration",
        SOURCE,
        SOURCE_URL,
        "published",
        99,
        _now(),
    )


def _tool_blueprint() -> dict[str, Any]:
    return {
        "concept": "发展性情绪跃迁支架把情绪识别从贴标签升级为可学习路径：定位、承接、转化、内化。",
        "dimensions": [{"name": name, "definition": definition} for name, definition in CORE_DIMENSIONS],
        "transitions": [{"name": name, "definition": definition, "response_rule": rule} for name, definition, rule in TRANSITIONS],
        "age_stages": [
            {"age": age, "goal": goal, "feeling_words": words, "scaffold_rule": rule}
            for age, goal, words, rule in AGE_STAGES
        ],
        "quality_rules": [
            "强唤醒先降级，再做跨维或跨层解释。",
            "任何情绪假设都必须可纠正。",
            "年龄阶段和当前承载力比话术漂亮更重要。",
            "情绪支架的终点是对方获得自主调节能力，不是依赖你的解释。",
        ],
    }


def _upsert_chain(connection: sqlite3.Connection, *, dry_run: bool) -> tuple[bool, bool]:
    existing = connection.execute("SELECT id FROM expression_tool_chains WHERE chain_uuid=?", (CHAIN_UUID,)).fetchone()
    payload = (
        "发展性情绪跃迁训练链",
        "把情绪流动训练成可迁移的自我调节能力",
        "初识/暧昧/修复/长期/教育支持",
        "D1-D3 情绪跃迁",
        _json([TOOL_UUID, "expr_tool_056", "expr_tool_062"]),
        _json([
            {"order": 1, "tool": "四维定位", "action": "标注强度、效价、指向和时序。"},
            {"order": 2, "tool": "发展支架", "action": "判断当前适合命名、观点采择、元反思还是暂停。"},
            {"order": 3, "tool": "跃迁选择", "action": "在同层降级、跨维翻译和跨层整合中只选一个主动作。"},
            {"order": 4, "tool": "边界出口", "action": "允许对方纠正、停下或降低深度。"},
        ]),
        _json(["情绪诊断", "强迫深聊", "跳过承接直接讲道理", "用年龄标签否定对方", "没有退路"]),
        _json({
            "before": "你又焦虑了，你应该学会成熟一点。",
            "after": "我听见你现在有点悬着。我们先不评价成熟不成熟，只看这份不确定从哪一刻开始变强。",
        }),
        "published",
        99,
        _now(),
    )
    if dry_run:
        return (not bool(existing), bool(existing))
    if existing:
        connection.execute(
            """
            UPDATE expression_tool_chains
            SET name=?, goal=?, scene=?, stage=?, tool_ids_json=?, sequence_json=?,
                forbidden_tools_json=?, example_dialogue_json=?, review_status=?,
                quality_score=?, updated_at=?
            WHERE chain_uuid=?
            """,
            (*payload, CHAIN_UUID),
        )
        return False, True
    connection.execute(
        """
        INSERT INTO expression_tool_chains (
          chain_uuid, name, goal, scene, stage, tool_ids_json, sequence_json,
          forbidden_tools_json, example_dialogue_json, review_status, quality_score,
          created_at, updated_at
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (CHAIN_UUID, *payload, _now()),
    )
    return True, False


def _seed_resources(connection: sqlite3.Connection, *, dry_run: bool) -> tuple[int, int]:
    created = 0
    skipped = 0
    for scenario in SCENARIOS:
        for difficulty in (1, 2, 3):
            resource = _resource_payload(scenario, difficulty)
            existing = connection.execute(
                "SELECT id FROM resource_library WHERE resource_uuid=? OR content_unit=?",
                (resource["resource_uuid"], resource["content_unit"]),
            ).fetchone()
            if existing:
                skipped += 1
                continue
            created += 1
            if not dry_run:
                _insert_resource(connection, resource)
    return created, skipped


def _resource_payload(scenario: dict[str, str], difficulty: int) -> dict[str, Any]:
    blueprint = _blueprint(scenario, difficulty)
    content = _content(blueprint)
    content_unit = f"developmental_emotion_transition::{scenario['key']}::D{difficulty}"
    signature = "|".join([SOURCE, content_unit, blueprint["better_response"]])
    return {
        "resource_uuid": f"developmental-emotion-transition:{uuid.uuid5(uuid.NAMESPACE_URL, signature)}",
        "type": "game",
        "category": "发展性情绪跃迁",
        "title": f"{scenario['key']}｜发展性情绪跃迁｜D{difficulty}",
        "content": content,
        "emotional_tone_json": _json({"primary": "情绪流动", "scene": scenario["scene"], "transition": scenario["transition"]}),
        "emotional_intensity": min(10, 4 + difficulty * 2),
        "applicable_scene": scenario["scene"],
        "difficulty_level": difficulty,
        "gender_target": "通用",
        "attachment_suitability": "通用",
        "usage_tip": "先定位情绪四维和跃迁类型，再回应；强烈情绪先降级，不急着做元反思。",
        "effectiveness_rating": 9,
        "source": SOURCE,
        "source_url": SOURCE_URL,
        "tags": ",".join(["发展性情绪跃迁", "情绪流动", "情绪词库", "支架", scenario["transition"], scenario["scene"], f"difficulty:{difficulty}"]),
        "review_status": "published",
        "reviewer_id": "developmental_emotion_transition_seed",
        "source_title": "情绪-社交发展与情绪跃迁体系",
        "source_excerpt": "用户提供结构化框架转化为项目原创训练卡，不保存第三方全文。",
        "source_summary": "以三层模型、四维定位、三种跃迁和年龄支架构建情绪社交训练资源。",
        "source_license": "user_provided_structured_material",
        "quality_score": 99,
        "expression_tool_ids_json": _json([TOOL_UUID, "expr_tool_056", "expr_tool_062"]),
        "expression_goal": "情绪跃迁与自我调节",
        "expression_level": f"D{difficulty}",
        "speech_act": "情绪定位 / 发展支架 / 跃迁回应 / 边界出口",
        "mistake_pattern": blueprint["common_mistake"],
        "recommended_drills_json": _json([
            {"type": "four_dimensions", "prompt": "标出强度、效价、指向、时序。"},
            {"type": "transition_choice", "prompt": "判断应使用同层、跨维还是跨层跃迁。"},
            {"type": "rewrite", "prompt": "写出一句可纠正、有退路的支架回应。"},
        ]),
        "case_blueprint_json": _json(blueprint),
        "variant_signature": "sha256:" + _hash(signature),
        "content_unit": content_unit,
        "coverage_axis": "developmental_emotion_transition",
        "variant_family": "developmental_emotion_transition_scaffold",
        "case_completeness_score": 100,
        "content_fingerprint": "sha256:" + _hash(content),
    }


def _blueprint(scenario: dict[str, str], difficulty: int) -> dict[str, Any]:
    dialogue = [
        {"speaker": "TA", "line": scenario["their_words"], "purpose": "原始情绪信号"},
        {"speaker": "低质量回应", "line": scenario["bad"], "purpose": "跳过定位或否定情绪"},
        {"speaker": "更好回应", "line": scenario["better"], "purpose": "四维定位后的支架回应"},
        {"speaker": "TA", "line": scenario["follow"], "purpose": "被承接后补充真实感受"},
        {"speaker": "继续回应", "line": scenario["support"], "purpose": "边界收束与内化方向"},
    ]
    return {
        "version": PIPELINE_VERSION,
        "axis": "developmental_emotion_transition",
        "axis_label": "发展性情绪跃迁",
        "scene": scenario["scene"],
        "setting": scenario["setting"],
        "their_words": scenario["their_words"],
        "emotion_dimensions": scenario["dimension"],
        "transition_type": scenario["transition"],
        "common_mistake": f"没有根据情绪强度、时序和发展支架回应；旧回应通常会说：{scenario['bad']}",
        "why_wrong": "它把情绪当成需要立刻纠正的问题，忽略了对方此刻的承载力和可退出边界。",
        "better_response": _difficulty_response(scenario, difficulty),
        "dialogue_script": dialogue[: 3 + difficulty],
        "response_steps": [
            "圈事实：只看原话、停顿、语气和动作。",
            "四维定位：标注强度、效价、指向、时序。",
            "选跃迁：同层降级、跨维翻译、跨层整合只选一个主路径。",
            "给支架：用可纠正语言帮助命名或调节。",
            "留出口：允许暂停、纠正、降低深度或换到现实行动。",
        ],
        "practice_task": "把低质量回应改成：事实线索 + 四维定位 + 跃迁路径 + 边界出口。",
        "transfer_scene": "迁移到初识、暧昧、冲突修复、长期关系和教育支持场景。",
        "difficulty_contract": {
            1: "D1：能完成四维定位并写一句不评判回应。",
            2: "D2：能判断跃迁类型并承接对方补充。",
            3: "D3：能把支架转成对方可内化的下一步语言。",
        }[difficulty],
    }


def _difficulty_response(scenario: dict[str, str], difficulty: int) -> str:
    if difficulty == 1:
        return scenario["better"]
    if difficulty == 2:
        return f"{scenario['better']} 我先按“{scenario['transition']}”来理解，如果听偏了你可以纠正我。"
    return f"{scenario['better']} 之后如果类似感觉再出现，你可以先说出一个词，我们再一起看它是变强了、变了性质，还是碰到旧模式。"


def _content(blueprint: dict[str, Any]) -> str:
    dialogue = "；".join(f"{turn['speaker']}：{turn['line']}" for turn in blueprint["dialogue_script"])
    return "\n".join(
        [
            f"案例定位：{blueprint['axis_label']} / {blueprint['transition_type']} / {blueprint['difficulty_contract']}",
            f"场景故事：{blueprint['setting']}",
            f"TA说：{blueprint['their_words']}",
            f"情绪四维：{blueprint['emotion_dimensions']}",
            f"完整对话：{dialogue}",
            f"常见失误：{blueprint['common_mistake']}",
            f"为什么错：{blueprint['why_wrong']}",
            f"更好回应：{blueprint['better_response']}",
            "五步拆解：" + "；".join(blueprint["response_steps"]),
            f"练习任务：{blueprint['practice_task']}",
            f"迁移场景：{blueprint['transfer_scene']}",
        ]
    )


def _insert_resource(connection: sqlite3.Connection, resource: dict[str, Any]) -> None:
    now = _now()
    connection.execute(
        """
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
        """,
        (
            resource["resource_uuid"],
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
            now,
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
        ),
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
            SOURCE,
            "user_provided_seed",
            int(report["created_sections"]),
            int(report["created_entries"]) + int(report["created_tools"]) + int(report["created_chains"]) + int(report["created_resources"]),
            int(report["skipped_resources"]),
            0,
            "completed",
            _json(report),
            _now(),
        ),
    )


def _json(data: Any) -> str:
    return json.dumps(data, ensure_ascii=False, sort_keys=True)


def _hash(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _now() -> str:
    return datetime.now().isoformat(timespec="seconds")


def main() -> None:
    parser = argparse.ArgumentParser(description="Seed developmental emotion transition materials.")
    parser.add_argument("--db", type=Path, default=DB_PATH)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    print(_json(seed(args.db, dry_run=args.dry_run)))


if __name__ == "__main__":
    main()
