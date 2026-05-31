"""Seed the meta-stage scene expression and deep empathy architecture.

The seed is intentionally project-original. External videos or posts are used
only as inspiration for structure; the database stores original cases,
analysis, and practice tasks.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sqlite3
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any

from backend.database.connection import DB_PATH, create_db_and_tables

SOURCE = "project_original:scene_empathy_worldclass_v1"
SOURCE_URL = "local_anchor:阶元式心理沟通与场景化表达标准流程"
DOC_PATH = Path(__file__).resolve().parents[2] / "docs" / "阶元式心理沟通与场景化表达标准流程.md"


META_STAGES: list[dict[str, Any]] = [
    {
        "key": "intent",
        "index": 0,
        "name": "元意图",
        "concept": "开口前先确认目标：我是想证明自己对，还是想让对方更容易真实表达。",
        "principle": "意图会决定语气。关系沟通的第一目标不是赢，而是让真实信息安全浮现。",
        "method": ["停一秒确认目标", "把赢输改成理解", "只处理当前最小问题", "保留对方选择权"],
        "mistake": "把对话当辩论，一开口就想压过对方。",
        "tools": ["expr_tool_041", "expr_tool_019"],
        "tags": ["元认知", "安全感", "边界"],
    },
    {
        "key": "observe",
        "index": 1,
        "name": "场景观察",
        "concept": "先抓可见事实：时间、地点、原话、停顿、语气、动作，而不是猜动机。",
        "principle": "事实越具体，后面的理解越不容易变成脑补。",
        "method": ["记录对方原话", "标出可见动作", "区分事实和解释", "只选一个最强信号回应"],
        "mistake": "听到一句话就立刻解释对方是不是不爱、不重视或故意针对。",
        "tools": ["expr_tool_011", "expr_tool_041"],
        "tags": ["微关系信号", "场景化表达", "事实观察"],
    },
    {
        "key": "picture",
        "index": 2,
        "name": "画面化表达",
        "concept": "把抽象结论改成对方能看见的具体画面，让观点自然进入体验。",
        "principle": "结论容易触发防御，画面更容易激活共鸣。",
        "method": ["用具体细节开头", "减少评价词", "说出画面中的人和影响", "最后再轻轻收束观点"],
        "mistake": "直接说你错了、你不懂、你应该改变。",
        "tools": ["expr_tool_011", "expr_tool_014", "expr_tool_020"],
        "tags": ["场景化表达", "故事赋能", "对比显效"],
    },
    {
        "key": "label_emotion",
        "index": 3,
        "name": "情绪承接",
        "concept": "识别并轻轻说出对方可能的情绪，让对方感到自己先被看见。",
        "principle": "情绪没被接住时，道理会被听成压力。",
        "method": ["复述处境", "命名一个可能情绪", "用也许降低确定性", "邀请对方纠正"],
        "mistake": "对方说累，你说大家都累；对方失望，你说别想太多。",
        "tools": ["expr_tool_041", "expr_tool_042"],
        "tags": ["情绪流动", "共情", "接住情绪"],
    },
    {
        "key": "understand_reason",
        "index": 4,
        "name": "给出理解",
        "concept": "不只说你很难过，还尝试说出为什么难过，并允许对方修正。",
        "principle": "被理解的感觉来自原因被看见，而不是情绪词被复读。",
        "method": ["说出事件影响", "说出可能原因", "加一句如果我理解错你纠正我", "停下等反馈"],
        "mistake": "只机械复述，或者把自己的解释当成定论。",
        "tools": ["expr_tool_042", "expr_tool_050"],
        "tags": ["深度共情", "情绪原因", "校准理解"],
    },
    {
        "key": "curiosity",
        "index": 5,
        "name": "好奇深挖",
        "concept": "用开放问题表达在意，让对方愿意继续说，而不是被审问。",
        "principle": "好奇的功能是给空间，不是索取隐私。",
        "method": ["只问一个问题", "问题可回答也可跳过", "从感受问到需要", "不要连续追问"],
        "mistake": "挺好、然后呢、你到底怎么想的。",
        "tools": ["expr_tool_027", "expr_tool_019"],
        "tags": ["开放问题", "深聊", "安全感"],
    },
    {
        "key": "non_judgment",
        "index": 6,
        "name": "拒绝评判",
        "concept": "在对方脆弱时暂停反驳、挑剔和优越感，先建立安全表达环境。",
        "principle": "人只有在不被审判时，才愿意把更真实的部分说出来。",
        "method": ["不说我早说过", "不急着纠正", "先承认处境不容易", "把建议放到对方允许之后"],
        "mistake": "我早说他不靠谱、是你不够努力、这有什么好难过。",
        "tools": ["expr_tool_056", "expr_tool_042"],
        "tags": ["边界与同意", "拒绝评判", "安全表达"],
    },
    {
        "key": "deep_empathy",
        "index": 7,
        "name": "深度共情",
        "concept": "听见内容、情绪和更深处的身份压力，陪对方面对情绪。",
        "principle": "深度共情不是催对方开心，而是让对方不用独自承受。",
        "method": ["听见表层事件", "听见委屈疲惫", "听见身份压力", "给出陪伴而非命令"],
        "mistake": "你别难过了、快点想开、我给你一个解决方案。",
        "tools": ["expr_tool_041", "expr_tool_042", "expr_tool_050"],
        "tags": ["深度共情", "长期连接", "冲突修复"],
    },
    {
        "key": "boundary_exit",
        "index": 8,
        "name": "边界出口",
        "concept": "任何深聊都必须允许对方不说、晚点说或只说一部分。",
        "principle": "安全感来自可退出。越能退出，越可能愿意靠近。",
        "method": ["明确可以不回答", "给晚点再说选项", "只约定下一小步", "复盘对方是否舒服"],
        "mistake": "以关心之名逼问到底，或把沉默理解为拒绝关系。",
        "tools": ["expr_tool_056", "expr_tool_019"],
        "tags": ["边界", "同意", "可退出"],
    },
]

SCENARIOS: list[dict[str, str]] = [
    {
        "key": "暧昧沉默",
        "scene": "暧昧",
        "stage": "互有好感但还没确定关系",
        "setting": "晚上聊天，对方突然回得很慢，只发来一句“今天有点不想说话”。",
        "their_words": "我也不知道怎么了，就是有点累。",
        "bad": "你是不是对我没兴趣了？",
        "need": "既希望被理解，又不想被逼着解释关系态度。",
        "transfer": "换成对方说“你刚才那句话让我不知道怎么接”。",
    },
    {
        "key": "社交小事",
        "scene": "社交",
        "stage": "朋友或同事的日常分享",
        "setting": "朋友说下班路上突然买了一块蛋糕，语气不像单纯开心。",
        "their_words": "今天突然特别想吃甜的。",
        "bad": "挺好，少吃点别胖了。",
        "need": "希望有人看见小事背后的疲惫、自我奖励或求安慰。",
        "transfer": "换成朋友说“今天突然想一个人走很远”。",
    },
    {
        "key": "伴侣旧伤",
        "scene": "冲突",
        "stage": "伴侣争吵后重新谈旧伤",
        "setting": "对方提起发烧那晚独自熬了一夜，你回来没有问候。",
        "their_words": "我发烧 39 度那晚，你回来连一句问候都没有。",
        "bad": "你怎么又翻旧账，我那天也很累。",
        "need": "希望孤单和被忽略的影响被承认，而不是被反驳记忆。",
        "transfer": "换成一次公开场合被忽略后的私下复盘。",
    },
    {
        "key": "拒绝请求",
        "scene": "边界确认",
        "stage": "熟人临时请求帮助",
        "setting": "对方今晚临时把方案丢给你，希望你帮他改完。",
        "their_words": "你就帮我这一次吧，真的很急。",
        "bad": "我不想帮，你找别人。",
        "need": "既想保留关系，又需要保护自己的项目和休息边界。",
        "transfer": "换成上次帮别人救火导致自己项目延期被批。",
    },
    {
        "key": "失恋安抚",
        "scene": "修复",
        "stage": "朋友失恋后反复怀疑自己",
        "setting": "深夜聊天，对方反复问自己是不是不够好。",
        "their_words": "为什么他可以那么快抽身？是不是我真的很差？",
        "bad": "他不值得，你早该看清了。",
        "need": "价值感受损，需要被陪伴，而不是被催着清醒。",
        "transfer": "换成复盘第一次约会迟到 40 分钟时的不舒服。",
    },
    {
        "key": "职场预算",
        "scene": "职场",
        "stage": "会议中的预算或方案说服",
        "setting": "对方质疑预算必要性，会议里开始只盯着数字表。",
        "their_words": "为什么不能再压一点预算？",
        "bad": "我们这个方案就是最优的，不能再砍。",
        "need": "需要看见预算不足会造成的真实后果和人的压力。",
        "transfer": "换成客户凌晨三点系统崩溃、办公室来回踱步的痛点故事。",
    },
]

DIFFICULTIES = {
    1: "D1：只完成一个本阶动作。",
    2: "D2：把本阶动作和开放问题组合起来。",
    3: "D3：在防御、沉默或压力升高时仍保留边界出口。",
}


def _dumps(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True)


def _hash(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _now() -> str:
    return datetime.now().isoformat()


def seed(dry_run: bool = False) -> dict[str, Any]:
    create_db_and_tables()
    with sqlite3.connect(DB_PATH) as con:
        con.row_factory = sqlite3.Row
        result = {
            "dry_run": dry_run,
            "knowledge_entries_created": 0,
            "knowledge_entries_updated": 0,
            "chains_created": 0,
            "chains_updated": 0,
            "resources_created": 0,
            "resources_skipped": 0,
        }
        section_id = _upsert_section(con, dry_run)
        for stage in META_STAGES:
            created = _upsert_knowledge_entry(con, section_id, stage, dry_run)
            result["knowledge_entries_created" if created else "knowledge_entries_updated"] += 1
        for chain in _chain_specs():
            created = _upsert_chain(con, chain, dry_run)
            result["chains_created" if created else "chains_updated"] += 1
        for stage in META_STAGES:
            for scenario in SCENARIOS:
                for difficulty in DIFFICULTIES:
                    created = _insert_resource(con, stage, scenario, difficulty, dry_run)
                    result["resources_created" if created else "resources_skipped"] += 1
        if not dry_run:
            con.commit()
    return result


def _upsert_section(con: sqlite3.Connection, dry_run: bool) -> int:
    now = _now()
    section_uuid = "knowledge_scene_empathy_worldclass_v1"
    existing = con.execute("SELECT id FROM knowledge_sections WHERE section_uuid=?", (section_uuid,)).fetchone()
    if existing:
        if not dry_run:
            con.execute(
                """
                UPDATE knowledge_sections
                SET name=?, description=?, icon=?, sort_order=?, source=?, source_id=?, updated_at=?
                WHERE section_uuid=?
                """,
                (
                    "阶元式心理沟通与场景化表达",
                    "把场景化表达、四阶心理沟通、边界出口和错题复盘组织成可学习路径。",
                    "🧭",
                    12,
                    SOURCE,
                    SOURCE_URL,
                    now,
                    section_uuid,
                ),
            )
        return int(existing["id"])
    if dry_run:
        row = con.execute("SELECT max(id) AS max_id FROM knowledge_sections").fetchone()
        return int(row["max_id"] or 0) + 1
    cur = con.execute(
        """
        INSERT INTO knowledge_sections (
          section_uuid, name, description, icon, sort_order, source, source_id, created_at, updated_at
        ) VALUES (?,?,?,?,?,?,?,?,?)
        """,
        (
            section_uuid,
            "阶元式心理沟通与场景化表达",
            "把场景化表达、四阶心理沟通、边界出口和错题复盘组织成可学习路径。",
            "🧭",
            12,
            SOURCE,
            SOURCE_URL,
            now,
            now,
        ),
    )
    return int(cur.lastrowid)


def _upsert_knowledge_entry(con: sqlite3.Connection, section_id: int, stage: dict[str, Any], dry_run: bool) -> bool:
    now = _now()
    entry_uuid = f"knowledge:scene-empathy:{stage['key']}"
    title = f"阶元 {stage['index']}：{stage['name']}"
    content = "\n".join(
        [
            f"定义：{stage['concept']}",
            f"核心原则：{stage['principle']}",
            "执行步骤：" + " -> ".join(stage["method"]),
            f"常见误区：{stage['mistake']}",
            "推荐工具：" + "、".join(stage["tools"]),
            _knowledge_case_line(stage),
            "练习：把最近一次失败回应拆成“事实、情绪、理解、好奇、边界”五行，再改写成一句更安全的话。",
        ]
    )
    metadata = {
        "doc": str(DOC_PATH),
        "learning": {
            "concept": stage["concept"],
            "principle": stage["principle"],
            "method": stage["method"],
            "scene": "适用于暧昧、社交、伴侣冲突、拒绝请求、失恋安抚和职场说服。",
            "drill": "选一个真实对话，把旧回应改写成：具体画面 + 情绪承接 + 一个可跳过的问题 + 边界出口。",
        },
        "stage_index": stage["index"],
        "tools": stage["tools"],
        "source_policy": "project_original_structured_analysis_no_third_party_fulltext",
    }
    existing = con.execute("SELECT id FROM knowledge_entries WHERE entry_uuid=?", (entry_uuid,)).fetchone()
    payload = (
        section_id,
        title,
        "场景化表达、四阶心理沟通、深度共情与边界出口的标准化学习阶元。",
        content,
        stage["concept"],
        "阶元沟通",
        _dumps([*stage["tags"], "场景化表达", "四阶心理沟通", "世界级架构"]),
        98,
        "published",
        "scene_empathy_worldclass_seed",
        now,
        now,
        SOURCE,
        SOURCE_URL,
        _dumps(metadata),
        now,
        entry_uuid,
    )
    if existing:
        if not dry_run:
            con.execute(
                """
                UPDATE knowledge_entries
                SET section_id=?, title=?, subtitle=?, content=?, summary=?, category=?,
                    tags_json=?, quality_score=?, review_status=?, reviewer_id=?,
                    reviewed_at=?, published_at=?, source=?, source_id=?,
                    source_metadata_json=?, updated_at=?
                WHERE entry_uuid=?
                """,
                payload,
            )
        return False
    if not dry_run:
        con.execute(
            """
            INSERT INTO knowledge_entries (
              section_id, title, subtitle, content, summary, category, tags_json, quality_score,
              review_status, reviewer_id, reviewed_at, published_at, source, source_id,
              source_metadata_json, updated_at, entry_uuid, created_at
            ) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
            """,
            (*payload, now),
        )
    return True


def _knowledge_case_line(stage: dict[str, Any]) -> str:
    if stage["key"] == "picture":
        return "案例：不要说“熬夜危害大”，改说“你这周眼下像挂了两个小口袋，脸色也比平时灰”。"
    if stage["key"] == "deep_empathy":
        return "案例：不要催“别难过”，改说“这件事像是不只失去了一个人，也让你怀疑自己有没有被好好选择”。"
    if stage["key"] == "boundary_exit":
        return "案例：不要追问到底，改说“你不用现在讲完整，如果继续说太重，我们可以先停在这里”。"
    return "案例：先还原一个可见细节，再说可能情绪，最后给对方纠正和退出的空间。"


def _chain_specs() -> list[dict[str, Any]]:
    return [
        {
            "chain_uuid": "expr_chain_scene_empathy_meta_v1",
            "name": "场景化共情九阶链",
            "goal": "引导深聊",
            "scene": "暧昧/社交/冲突/职场",
            "stage": "D3 阶元迁移",
            "tool_ids": ["expr_tool_011", "expr_tool_041", "expr_tool_042", "expr_tool_027", "expr_tool_056"],
            "sequence": ["场景化表达", "情绪标注", "共情反射", "请求结构", "边界声明"],
            "before": "你到底怎么了？你说清楚啊。",
            "after": "我先说我看见的画面：你刚才停了很久，只说有点累。听起来像是今天真的撑得很满。你不用现在讲完整，如果愿意，我想听听最重的是哪一小段。",
        },
        {
            "chain_uuid": "expr_chain_nonjudgment_curiosity_v1",
            "name": "不评判好奇深挖链",
            "goal": "降低防御",
            "scene": "社交/暧昧",
            "stage": "D2 深聊推进",
            "tool_ids": ["expr_tool_041", "expr_tool_027", "expr_tool_019", "expr_tool_056"],
            "sequence": ["情绪标注", "请求结构", "留白沉默", "边界声明"],
            "before": "这有什么好难过的？",
            "after": "这件事好像确实让你有点难受。我不会急着判断，你愿意说说最卡住的是哪一部分吗？不想说也没关系。",
        },
        {
            "chain_uuid": "expr_chain_workplace_scene_persuasion_v1",
            "name": "职场画面化说服链",
            "goal": "说清事实",
            "scene": "职场/分歧",
            "stage": "D2 风险画面",
            "tool_ids": ["expr_tool_011", "expr_tool_014", "expr_tool_020", "expr_tool_023"],
            "sequence": ["场景化表达", "故事叙述", "对比表达", "问题解决结构"],
            "before": "我们方案最好，预算不能砍。",
            "after": "我想先讲一个风险画面：如果预算继续压，最可能发生的是半夜系统出问题但没人兜底。现在的方案不是追求好看，而是把这个风险提前挡住。",
        },
        {
            "chain_uuid": "expr_chain_conflict_detail_repair_v1",
            "name": "冲突细节修复链",
            "goal": "修复信任",
            "scene": "伴侣冲突/修复",
            "stage": "D3 旧伤承接",
            "tool_ids": ["expr_tool_011", "expr_tool_041", "expr_tool_042", "expr_tool_050"],
            "sequence": ["场景化表达", "情绪标注", "共情反射", "承接再转向"],
            "before": "你怎么又翻旧账。",
            "after": "你提的是那晚发烧自己熬过去，而我回来没问候。这不是小事，我能理解那一刻你会觉得很孤单。我们先把这个影响说清楚，再谈我下次怎么补上。",
        },
        {
            "chain_uuid": "expr_chain_request_boundary_warm_v1",
            "name": "温和拒绝边界链",
            "goal": "确认边界",
            "scene": "拒绝请求/长期",
            "stage": "D2 关系保留",
            "tool_ids": ["expr_tool_011", "expr_tool_056", "expr_tool_027", "expr_tool_019"],
            "sequence": ["场景化表达", "边界声明", "请求结构", "留白沉默"],
            "before": "我不想帮，你找别人。",
            "after": "我知道你现在很急，也能想象方案卡住的压力。今晚我不能接完整修改，但我可以帮你看第一版结构；如果这不够，我们一起想第二个求助对象。",
        },
    ]


def _upsert_chain(con: sqlite3.Connection, chain: dict[str, Any], dry_run: bool) -> bool:
    now = _now()
    payload = (
        chain["name"],
        chain["goal"],
        chain["scene"],
        chain["stage"],
        _dumps(chain["tool_ids"]),
        _dumps([{"order": index + 1, "tool": tool} for index, tool in enumerate(chain["sequence"])]),
        _dumps(["逼问隐私", "反问施压", "否定感受", "借共情操控决定"]),
        _dumps({"before": chain["before"], "after": chain["after"]}),
        "published",
        98,
        now,
        chain["chain_uuid"],
    )
    existing = con.execute("SELECT id FROM expression_tool_chains WHERE chain_uuid=?", (chain["chain_uuid"],)).fetchone()
    if existing:
        if not dry_run:
            con.execute(
                """
                UPDATE expression_tool_chains
                SET name=?, goal=?, scene=?, stage=?, tool_ids_json=?, sequence_json=?,
                    forbidden_tools_json=?, example_dialogue_json=?, review_status=?,
                    quality_score=?, updated_at=?
                WHERE chain_uuid=?
                """,
                payload,
            )
        return False
    if not dry_run:
        con.execute(
            """
            INSERT INTO expression_tool_chains (
              name, goal, scene, stage, tool_ids_json, sequence_json, forbidden_tools_json,
              example_dialogue_json, review_status, quality_score, updated_at, chain_uuid, created_at
            ) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)
            """,
            (*payload, now),
        )
    return True


def _insert_resource(
    con: sqlite3.Connection,
    stage: dict[str, Any],
    scenario: dict[str, str],
    difficulty: int,
    dry_run: bool,
) -> bool:
    blueprint = _resource_blueprint(stage, scenario, difficulty)
    content = _resource_content(blueprint)
    signature = _hash("|".join([stage["key"], scenario["key"], str(difficulty), content]))
    resource_uuid = f"scene-empathy-meta:{uuid.uuid5(uuid.NAMESPACE_URL, signature)}"
    if con.execute("SELECT id FROM resource_library WHERE resource_uuid=?", (resource_uuid,)).fetchone():
        return False
    if dry_run:
        return True
    now = _now()
    con.execute(
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
        ) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
        """,
        (
            resource_uuid,
            "game",
            f"阶元沟通·{stage['name']}",
            f"{scenario['key']}｜阶元{stage['index']}{stage['name']}｜D{difficulty}",
            content,
            _dumps({"primary": stage["name"], "scene": scenario["scene"], "generator": SOURCE}),
            min(9, 4 + difficulty + (1 if stage["key"] in {"deep_empathy", "boundary_exit"} else 0)),
            scenario["scene"],
            difficulty,
            "通用",
            "通用",
            "按阶元练习：先画面化，再承接情绪，再好奇深挖，最后保留边界出口。",
            9,
            SOURCE,
            SOURCE_URL,
            ",".join(["具体案例", "阶元沟通", stage["name"], scenario["scene"], f"difficulty:{difficulty}"]),
            now,
            "published",
            "scene_empathy_worldclass_seed",
            now,
            now,
            "阶元式心理沟通与场景化表达",
            "项目原创训练资源；不搬运第三方全文。",
            "把场景化表达、四阶心理沟通、边界出口组织为可练案例。",
            "project_original",
            "sha256:" + _hash(content),
            97 + difficulty,
            _dumps(stage["tools"]),
            f"{stage['name']}：{stage['principle']}",
            f"D{difficulty} 阶元训练",
            stage["principle"],
            stage["mistake"],
            _dumps(
                [
                    {"type": "rewrite", "prompt": blueprint["practice_task"]},
                    {"type": "transfer", "prompt": blueprint["transfer_scene"]},
                ]
            ),
            _dumps(blueprint),
            signature,
            f"{stage['key']}::{scenario['key']}",
            stage["key"],
            "scene_empathy_meta_stage_v1",
            99,
        ),
    )
    return True


def _resource_blueprint(stage: dict[str, Any], scenario: dict[str, str], difficulty: int) -> dict[str, Any]:
    response_steps = [
        f"本阶目标：{stage['name']}。",
        "先引用一个具体场景细节，不直接塞结论。",
    ]
    if difficulty >= 2:
        response_steps.append("加入一个开放问题，邀请对方继续说。")
    if difficulty >= 3:
        response_steps.append("明确可以不说、晚点说或只说一部分。")
    return {
        "axis": stage["key"],
        "axis_label": stage["name"],
        "resource_type": "game",
        "resource_type_label": "阶元沟通训练卡",
        "scene": scenario["scene"],
        "relation_stage": scenario["stage"],
        "trigger": f"{scenario['key']}场景中，需要用{stage['name']}避免抽象说教或逼问。",
        "setting": scenario["setting"],
        "their_words": scenario["their_words"],
        "surface_signal": f"对方的原话里有可观察信号：{scenario['their_words']}",
        "deeper_need": scenario["need"],
        "common_mistake": f"{stage['mistake']}；旧回应通常会说：{scenario['bad']}",
        "why_wrong": stage["principle"],
        "better_response": _better_response(stage, scenario, difficulty),
        "response_steps": response_steps,
        "boundary_note": "让对方敞开心扉不等于要求对方交代隐私；任何练习都要允许跳过。",
        "practice_task": f"把“{scenario['bad']}”改写成符合“{stage['name']}”的一句话。",
        "transfer_scene": scenario["transfer"],
        "variant_deltas": [
            f"阶元不同：{stage['index']} / {stage['name']}。",
            f"场景不同：{scenario['key']} / {scenario['stage']}。",
            f"难度不同：{DIFFICULTIES[difficulty]}",
            "输出不同：必须有具体画面、情绪承接或边界出口中的至少两个要素。",
        ],
        "difficulty_contract": DIFFICULTIES[difficulty],
    }


def _better_response(stage: dict[str, Any], scenario: dict[str, str], difficulty: int) -> str:
    name = stage["name"]
    if name == "画面化表达":
        base = f"我先不急着下结论，我看到的画面是：{scenario['setting']}你说“{scenario['their_words']}”，那一刻压力其实已经露出来了。"
    elif name == "情绪承接":
        base = f"听起来这不只是事情本身，而是让你有点委屈或撑不住。"
    elif name == "好奇深挖":
        base = f"我想更懂一点：你说“{scenario['their_words']}”的时候，最重的是事情本身，还是那一刻没人懂你？"
    elif name == "拒绝评判":
        base = "我不会急着评价你这样对不对。换成我在这个处境里，也可能会很乱。"
    elif name == "深度共情":
        base = f"我听见的不只是“{scenario['their_words']}”，还有背后的难：{scenario['need']}这部分确实不轻。"
    elif name == "边界出口":
        base = f"你不用现在讲完整；如果继续说太累，我们可以先停在这里。"
    elif name == "给出理解":
        base = f"我猜这件事难受的点可能是：{scenario['need']}如果我理解错了，你可以直接纠正我。"
    elif name == "场景观察":
        base = f"我先只说事实：你刚才说“{scenario['their_words']}”，而且是在这个场景里发生的：{scenario['setting']}"
    else:
        base = "我先把目标放在理解你，而不是证明谁对。"
    if difficulty == 1:
        return base
    if difficulty == 2:
        return f"{base} 如果你愿意，我想听听最卡住的是哪一小段。"
    return f"{base} 如果现在不想继续，也完全可以，我们晚点再说。"


def _resource_content(blueprint: dict[str, Any]) -> str:
    return "\n".join(
        [
            f"案例定位：{blueprint['axis_label']} / {blueprint['resource_type_label']} / {blueprint['difficulty_contract']}",
            f"场景：{blueprint['setting']}",
            f"关系阶段：{blueprint['relation_stage']}",
            f"TA说：{blueprint['their_words']}",
            f"表层信号：{blueprint['surface_signal']}",
            f"深层可能：{blueprint['deeper_need']}",
            f"常见失误：{blueprint['common_mistake']}",
            f"为什么错：{blueprint['why_wrong']}",
            f"更好回应：{blueprint['better_response']}",
            "回应拆解：" + "；".join(str(item) for item in blueprint["response_steps"]),
            f"边界提醒：{blueprint['boundary_note']}",
            f"练习任务：{blueprint['practice_task']}",
            f"迁移场景：{blueprint['transfer_scene']}",
            "变体差异：" + "；".join(str(item) for item in blueprint["variant_deltas"]),
        ]
    )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    print(json.dumps(seed(dry_run=args.dry_run), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
