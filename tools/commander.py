"""本地指挥官：读取模块 DAG，选择下一项并运行质量门禁。"""
from __future__ import annotations

import argparse
import json
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_DAG = PROJECT_ROOT / "docs" / "tasks" / "module_dag.json"
DEFAULT_STATE = PROJECT_ROOT / "docs" / "tasks" / "commander_state.json"
DEFAULT_VALIDATION_COMMANDS = [
    ".venv/bin/python -m pytest -q",
    "cd frontend && npm run type-check && npm run build",
]


@dataclass(frozen=True)
class ModuleTask:
    """模块级任务节点。"""

    id: str
    name: str
    priority: int
    status: str
    dependencies: list[str]
    acceptance: list[str]
    verification: list[str]


def load_module_dag(path: Path = DEFAULT_DAG) -> list[ModuleTask]:
    """读取模块 DAG。"""
    data = json.loads(path.read_text(encoding="utf-8"))
    modules = data.get("modules", [])
    return [_task_from_dict(item) for item in modules if isinstance(item, dict)]


def select_next_task(tasks: list[ModuleTask]) -> ModuleTask | None:
    """选择依赖满足的最高优先级未完成任务。"""
    completed = {task.id for task in tasks if task.status == "completed"}
    candidates = [
        task
        for task in tasks
        if task.status != "completed" and all(dependency in completed for dependency in task.dependencies)
    ]
    if not candidates:
        return None
    return sorted(candidates, key=lambda task: (task.priority, task.id))[0]


def validate_project(commands: list[str] | None = None, *, dry_run: bool = False) -> list[dict[str, Any]]:
    """运行项目质量门禁。"""
    selected = commands or DEFAULT_VALIDATION_COMMANDS
    results: list[dict[str, Any]] = []
    for command in selected:
        if dry_run:
            results.append({"command": command, "returncode": None, "status": "dry_run"})
            continue
        completed = subprocess.run(command, cwd=PROJECT_ROOT, shell=True, text=True, capture_output=True, check=False)
        results.append({
            "command": command,
            "returncode": completed.returncode,
            "status": "passed" if completed.returncode == 0 else "failed",
            "stdout_tail": _tail(completed.stdout),
            "stderr_tail": _tail(completed.stderr),
        })
        if completed.returncode != 0:
            break
    return results


def run_next(*, dag_path: Path = DEFAULT_DAG, dry_run: bool = False, validate: bool = False) -> dict[str, Any]:
    """返回下一项任务；可选运行该任务的验证命令。"""
    tasks = load_module_dag(dag_path)
    next_task = select_next_task(tasks)
    if next_task is None:
        return {
            "status": "all_completed",
            "message": "所有模块任务已完成；下一步应补充新目标或升级验收标准。",
            "task": None,
            "validation": [],
        }
    validation = validate_project(next_task.verification, dry_run=dry_run) if validate or dry_run else []
    return {
        "status": "next_task",
        "task": _task_to_dict(next_task),
        "validation": validation,
    }


def sync_state(
    *,
    dag_path: Path = DEFAULT_DAG,
    state_path: Path = DEFAULT_STATE,
    dry_run: bool = False,
) -> dict[str, Any]:
    """Record an audit-friendly commander state snapshot."""
    tasks = load_module_dag(dag_path)
    next_task = select_next_task(tasks)
    snapshot = {
        "status": "dry_run" if dry_run else "recorded",
        "generated_at": _now_iso(),
        "summary": _dag_summary(tasks),
        "next_task": _task_to_dict(next_task) if next_task else None,
        "state_path": str(state_path),
        "principle": "每轮自动执行后都要同步 DAG、进度、验证和下一动作，避免状态漂移。",
    }
    if not dry_run:
        state_path.parent.mkdir(parents=True, exist_ok=True)
        state_path.write_text(json.dumps(snapshot, ensure_ascii=False, indent=2), encoding="utf-8")
    return snapshot


def run_weekly_evolution(*, dry_run: bool = True, batch_limit: int = 5) -> dict[str, Any]:
    """Invoke the local weekly evolution scheduler through the same code path as the API."""
    from sqlmodel import Session

    from backend.api.evolution import ScheduledEvolutionRunRequest, run_weekly_scheduler
    from backend.database.connection import create_db_and_tables, engine

    create_db_and_tables()
    with Session(engine) as session:
        return run_weekly_scheduler(
            ScheduledEvolutionRunRequest(dry_run=dry_run, batch_limit=batch_limit),
            session,
        )


def run_regression_audit(*, dry_run: bool = True, batch_limit: int = 5) -> dict[str, Any]:
    """Run a production-style regression audit across core local quality gates."""
    if dry_run:
        checks = [
            "database_health",
            "weekly_evolution",
            "import_quality",
            "reviewed_publish_candidates",
            "vector_recall",
            "gold_interrater",
            "gold_conflict_queue",
            "ai_quality",
            "ai_failure_analysis",
            "ai_provider_diagnostics",
        ]
        return {
            "dry_run": True,
            "checks": [{"id": item, "status": "planned"} for item in checks],
            "next_actions": ["run without --dry-run to execute local regression audit gates"],
        }

    from sqlmodel import Session

    from backend.api.analytics import get_ai_failure_analysis, get_ai_provider_diagnostics, get_ai_quality_report
    from backend.api.evolution import (
        ScheduledEvolutionRunRequest,
        VectorRecallEvaluationRequest,
        evaluate_vector_index,
        import_quality_report,
        reviewed_asset_publish_candidates,
        run_weekly_scheduler,
    )
    from backend.api.samples import get_gold_conflict_queue, get_gold_interrater_consistency
    from backend.core.vector_index import rebuild_metadata_vector_index
    from backend.database.connection import create_db_and_tables, engine
    from backend.database.resource_case_quality_automation import audit_case_quality
    from backend.database.schema_guard import audit_schema

    create_db_and_tables()
    with Session(engine) as session:
        database = audit_schema(engine)
        weekly = run_weekly_scheduler(ScheduledEvolutionRunRequest(dry_run=True, batch_limit=batch_limit), session)
        import_quality = import_quality_report(session=session)
        publish_candidates = reviewed_asset_publish_candidates(limit=10, session=session)
        vector_rebuild = rebuild_metadata_vector_index(session, limit_per_type=500)
        vector = evaluate_vector_index(VectorRecallEvaluationRequest(limit_per_type=2, thresholds=[0.2, 0.35]), session)
        gold = get_gold_interrater_consistency(session=session)
        gold_conflicts = get_gold_conflict_queue(limit=10, session=session)
        ai_quality = get_ai_quality_report(limit=120, session=session)
        ai_failures = get_ai_failure_analysis(limit=120, session=session)
        provider_diagnostics = get_ai_provider_diagnostics(limit=120, session=session)
    case_quality = audit_case_quality(limit=5000)

    checks = [
        _audit_check(
            "database_health",
            database.get("status") == "ok" and database.get("integrity_check") == "ok",
            {
                "status": database.get("status"),
                "integrity_check": database.get("integrity_check"),
                "missing_tables": database.get("missing_tables", []),
                "missing_columns": database.get("missing_columns", {}),
            },
        ),
        _audit_check(
            "weekly_evolution",
            weekly.get("dry_run") is True and bool(weekly.get("next_actions")),
            {"dry_run": weekly.get("dry_run"), "next_actions": weekly.get("next_actions", [])[:3]},
        ),
        _audit_check(
            "import_quality",
            "quality_score" in import_quality and "repair_plan" in import_quality,
            _import_quality_audit_detail(import_quality),
        ),
        _audit_check(
            "reviewed_publish_candidates",
            "items" in publish_candidates and "quality_gates" in publish_candidates,
            {
                "total": publish_candidates.get("total"),
                "publish_ready": publish_candidates.get("publish_ready"),
                "quality_gates": publish_candidates.get("quality_gates"),
                "top_candidates": publish_candidates.get("items", [])[:3],
                "next_actions": publish_candidates.get("next_actions", [])[:3],
            },
        ),
        _audit_check(
            "vector_recall",
            float(vector.get("summary", {}).get("top10_recall", 0)) >= 0.5,
            {
                "backend": vector.get("summary", {}).get("backend"),
                "probes": vector.get("summary", {}).get("probes"),
                "top10_recall": vector.get("summary", {}).get("top10_recall"),
                "index_rebuild": {
                    "rebuilt": vector_rebuild.get("rebuilt", {}),
                    "total_vectors": vector_rebuild.get("total_vectors"),
                    "backend": vector_rebuild.get("backend"),
                },
            },
        ),
        _audit_check(
            "gold_interrater",
            "summary" in gold and "quality_gates" in gold,
            {
                "summary": gold.get("summary"),
                "quality_gates": gold.get("quality_gates"),
                "resolved_conflict_samples": gold.get("summary", {}).get("resolved_conflict_samples"),
                "open_conflict_samples": gold.get("summary", {}).get("conflict_samples"),
                "next_actions": gold.get("next_actions", [])[:3],
            },
        ),
        _audit_check(
            "gold_conflict_queue",
            "items" in gold_conflicts and "quality_gates" in gold_conflicts,
            {
                "total": gold_conflicts.get("total"),
                "quality_gates": gold_conflicts.get("quality_gates"),
                "top_conflicts": gold_conflicts.get("items", [])[:3],
                "next_actions": gold_conflicts.get("next_actions", [])[:3],
            },
        ),
        _audit_check(
            "ai_quality",
            "summary" in ai_quality and "next_actions" in ai_quality,
            {"summary": ai_quality.get("summary"), "next_actions": ai_quality.get("next_actions", [])[:3]},
        ),
        _audit_check(
            "ai_failure_analysis",
            "summary" in ai_failures and "clusters" in ai_failures,
            {"summary": ai_failures.get("summary"), "clusters": ai_failures.get("clusters", [])[:3]},
        ),
        _audit_check(
            "ai_provider_diagnostics",
            "provider" in provider_diagnostics and "recent" in provider_diagnostics,
            {
                "provider": provider_diagnostics.get("provider"),
                "request_shape": provider_diagnostics.get("request_shape"),
                "recent": provider_diagnostics.get("recent"),
                "risk_level": provider_diagnostics.get("risk_level"),
                "diagnostics": provider_diagnostics.get("diagnostics", [])[:3],
                "failure_playbook": {
                    "risk_level": provider_diagnostics.get("failure_playbook", {}).get("risk_level"),
                    "root_cause_matrix": provider_diagnostics.get("failure_playbook", {}).get("root_cause_matrix", [])[:2],
                    "quality_gate": provider_diagnostics.get("failure_playbook", {}).get("quality_gate"),
                },
                "next_actions": provider_diagnostics.get("next_actions", [])[:3],
            },
        ),
        _audit_check(
            "resource_case_quality",
            case_quality.get("summary", {}).get("incomplete", 0) == 0
            and case_quality.get("summary", {}).get("context_mismatch", 0) == 0
            and case_quality.get("summary", {}).get("stereotype_or_manipulation_risk", 0) == 0,
            {
                "summary": case_quality.get("summary", {}),
                "quality_gate": case_quality.get("quality_gate", {}),
                "samples": case_quality.get("samples", {}),
                "next_actions": case_quality.get("next_actions", [])[:3],
            },
        ),
    ]
    failed = [item for item in checks if item["status"] != "passed"]
    return {
        "dry_run": False,
        "status": "passed" if not failed else "needs_attention",
        "checks": checks,
        "next_actions": _regression_next_actions(failed),
    }


def resolve_gold_conflicts_command(
    *,
    dry_run: bool = True,
    limit: int = 20,
    reviewer_id: str = "consensus-panel-v1",
) -> dict[str, Any]:
    """Close open Gold conflicts by creating auditable consensus versions."""
    from sqlmodel import Session

    from backend.api.samples import GoldConflictResolveRequest, get_gold_interrater_consistency, resolve_gold_conflicts
    from backend.database.connection import create_db_and_tables, engine

    create_db_and_tables()
    with Session(engine) as session:
        before = get_gold_interrater_consistency(session=session)
        result = resolve_gold_conflicts(
            GoldConflictResolveRequest(limit=limit, reviewer_id=reviewer_id, dry_run=dry_run),
            session=session,
        )
        after = get_gold_interrater_consistency(session=session)
    return {
        "dry_run": dry_run,
        "before": _gold_calibration_snapshot(before),
        "result": result,
        "after": _gold_calibration_snapshot(after),
        "principle": "Gold 共识解决只新增 consensus_review 版本；外部专家原始分歧保留为审计证据。",
    }


def scheduler_plan_command() -> dict[str, Any]:
    """Return production scheduler jobs without starting the daemon."""
    from backend.core.production_scheduler import scheduler_plan

    return scheduler_plan()


def scheduler_run_once_command(
    job_id: str,
    *,
    dry_run: bool | None = None,
    batch_limit: int | None = None,
) -> dict[str, Any]:
    """Run one production scheduler job immediately."""
    from backend.core.production_scheduler import run_scheduled_job

    return run_scheduled_job(job_id, dry_run=dry_run, batch_limit=batch_limit)


def scheduler_service_plan_command(*, apply: bool = False) -> dict[str, Any]:
    """Generate local service manager artifacts for the production scheduler."""
    from backend.core.production_scheduler import scheduler_service_plan

    return scheduler_service_plan(write_files=apply)


def scheduler_health_command() -> dict[str, Any]:
    """Return production scheduler health, alerts, and recovery runbook."""
    from backend.core.production_scheduler import scheduler_health

    return scheduler_health()


def scheduler_daemon_command() -> dict[str, Any]:
    """Build and start the production scheduler daemon."""
    from time import sleep

    from backend.core.production_scheduler import build_background_scheduler, scheduler_plan

    scheduler = build_background_scheduler()
    scheduler.start()
    try:
        while True:
            sleep(60)
    except KeyboardInterrupt:
        scheduler.shutdown(wait=False)
    return {"status": "stopped", "plan": scheduler_plan()}


def resource_case_quality_command(*, apply: bool = False, limit: int = 500, reviewer_id: str = "case-quality-automation") -> dict[str, Any]:
    from backend.database.resource_case_quality_automation import audit_case_quality, repair_case_quality

    before = audit_case_quality(limit=limit)
    repair = repair_case_quality(dry_run=not apply, limit=limit, reviewer_id=reviewer_id)
    after = audit_case_quality(limit=limit) if apply else None
    return {
        "status": "applied" if apply else "dry_run",
        "before": before,
        "repair": repair,
        "after": after,
        "next_actions": [
            "run regression-audit after apply",
            "review quarantined stereotype/manipulation-risk resources before rewriting",
        ],
    }


def resource_similarity_rewrite_iteration_command(
    *,
    apply: bool = False,
    iterations: int = 1,
    cluster_limit: int = 5000,
    batch_size: int = 12,
    threshold: float = 0.82,
    reviewer_id: str = "resource-similarity-commander",
) -> dict[str, Any]:
    """Rewrite the largest near-duplicate resource families into concrete cases."""
    from sqlmodel import Session

    from backend.api.resources import ResourceSimilarityRewriteRequest, resource_similarity_rewrite_batch
    from backend.core.vector_index import resource_similarity_queue
    from backend.database.connection import create_db_and_tables, engine

    create_db_and_tables()
    rounds: list[dict[str, Any]] = []
    with Session(engine) as session:
        before = resource_similarity_queue(session, limit=cluster_limit, threshold=threshold, max_clusters=10)
        for index in range(1, max(1, iterations) + 1):
            queue = resource_similarity_queue(session, limit=cluster_limit, threshold=threshold, max_clusters=1)
            clusters = queue.get("clusters", [])
            if not clusters:
                rounds.append({"iteration": index, "status": "no_cluster"})
                break
            cluster = clusters[0]
            resource_ids = [int(item["id"]) for item in cluster.get("items", [])[:batch_size] if item.get("id")]
            if not resource_ids:
                rounds.append({"iteration": index, "status": "empty_cluster", "family_key": cluster.get("family_key")})
                break
            request = ResourceSimilarityRewriteRequest(
                resource_ids=resource_ids,
                reviewer_id=reviewer_id,
                reason=f"commander iteration {index}: rewrite near-duplicate family {cluster.get('family_key')}",
                dry_run=not apply,
                mark_originals_quarantine=True,
            )
            result = resource_similarity_rewrite_batch(request, session=session)
            rounds.append({
                "iteration": index,
                "status": "applied" if apply else "dry_run",
                "family_key": cluster.get("family_key"),
                "family_size": cluster.get("size"),
                "resource_ids": resource_ids,
                "created": result.get("created"),
                "drafts": len(result.get("drafts", [])) if not apply else None,
                "audit_logs": len(result.get("audit_logs", [])) if apply else None,
            })
            if not apply:
                break
        after = resource_similarity_queue(session, limit=cluster_limit, threshold=threshold, max_clusters=10)
    return {
        "status": "applied" if apply else "dry_run",
        "iterations_requested": iterations,
        "batch_size": batch_size,
        "threshold": threshold,
        "before": _similarity_snapshot(before),
        "rounds": rounds,
        "after": _similarity_snapshot(after),
        "quality_gates": {
            "content_deleted": False,
            "third_party_full_text_saved": False,
            "originals_quarantined_not_deleted": True,
        },
        "next_actions": [
            "run resource-case-quality --apply after applied rewrites",
            "run regression-audit after case-quality repair",
        ] if apply else ["rerun with --apply to rewrite and quarantine the selected family"],
    }


def worldclass_data_audit_command() -> dict[str, Any]:
    """Audit the world-class data matrix against current terminal learning goals."""
    import sqlite3

    from backend.database.connection import DB_PATH, create_db_and_tables

    create_db_and_tables()
    with sqlite3.connect(DB_PATH) as connection:
        connection.row_factory = sqlite3.Row
        samples_total = _count(connection, "interaction_samples")
        resources_total = _count(connection, "resource_library")
        knowledge_total = _count(connection, "knowledge_entries")
        emotion_total = _count(connection, "emotion_spectrum")
        mixed_total = _count(connection, "mixed_emotions")
        chains_total = _count(connection, "expression_tool_chains")
        sample_coverage = {
            field: _coverage(connection, "interaction_samples", field, samples_total)
            for field in (
                "their_behavior",
                "bad_response_reason",
                "good_response_tension",
                "good_response_humor",
                "principle_ref",
                "five_w_two_h_json",
                "signal_highlights_json",
                "emotion_flow_json",
                "feeling_tags_json",
                "need_radar_json",
                "boundary_state_json",
                "tension_dimensions_json",
            )
        }
        gold_count = int(
            connection.execute(
                "SELECT count(*) FROM interaction_samples WHERE gold_label_json IS NOT NULL AND trim(gold_label_json) <> ''"
            ).fetchone()[0]
        )
        placeholder_knowledge = int(
            connection.execute(
                """
                SELECT count(*)
                FROM knowledge_entries
                WHERE title LIKE '低分知识%' OR content='只有简短说明。' OR summary='简短说明。'
                """
            ).fetchone()[0]
        )
        long_resource_fields = {
            "speech_act_long": int(
                connection.execute("SELECT count(*) FROM resource_library WHERE length(coalesce(speech_act,'')) > 24").fetchone()[0]
            ),
            "expression_goal_long": int(
                connection.execute("SELECT count(*) FROM resource_library WHERE length(coalesce(expression_goal,'')) > 36").fetchone()[0]
            ),
        }
        chain_stages = {
            str(row["stage"] or "unknown"): int(row["count"])
            for row in connection.execute("SELECT stage, count(*) AS count FROM expression_tool_chains GROUP BY stage").fetchall()
        }
    targets = {
        "knowledge_entries": {"current": knowledge_total, "target": 180, "priority": "P1"},
        "emotion_spectrum": {"current": emotion_total, "target": 240, "priority": "P1"},
        "mixed_emotions": {"current": mixed_total, "target": 80, "priority": "P2"},
        "expression_tool_chains": {"current": chains_total, "target": 60, "priority": "P2"},
        "gold_labels": {"current": gold_count, "target": max(300, int(samples_total * 0.35)), "priority": "P2"},
    }
    gaps = [_target_gap(name, detail) for name, detail in targets.items()]
    gaps.extend(_coverage_gaps(sample_coverage))
    if placeholder_knowledge:
        gaps.append({"id": "placeholder_knowledge", "priority": "P0", "gap": placeholder_knowledge, "action": "rewrite placeholder knowledge entries"})
    if long_resource_fields["speech_act_long"] or long_resource_fields["expression_goal_long"]:
        gaps.append({
            "id": "resource_taxonomy_long_fields",
            "priority": "P2",
            "gap": long_resource_fields,
            "action": "continue canonical taxonomy normalization",
        })
    active_gaps = [gap for gap in gaps if gap.get("gap")]
    return {
        "status": "needs_expansion" if active_gaps else "worldclass_data_gate_passed",
        "totals": {
            "resources": resources_total,
            "samples": samples_total,
            "knowledge_entries": knowledge_total,
            "emotion_spectrum": emotion_total,
            "mixed_emotions": mixed_total,
            "expression_tool_chains": chains_total,
            "gold_labels": gold_count,
        },
        "sample_coverage": sample_coverage,
        "chain_stages": chain_stages,
        "quality_debt": {
            "placeholder_knowledge": placeholder_knowledge,
            **long_resource_fields,
        },
        "targets": targets,
        "gaps": sorted(gaps, key=lambda item: (str(item["priority"]), str(item["id"]))),
        "next_actions": _worldclass_next_actions(gaps),
    }


def main(argv: list[str] | None = None) -> int:  # noqa: C901
    parser = argparse.ArgumentParser(description="关系动力学项目本地指挥官")
    subparsers = parser.add_subparsers(dest="command", required=True)

    run_next_parser = subparsers.add_parser("run-next", help="读取 DAG 并输出下一项任务")
    run_next_parser.add_argument("--dag", type=Path, default=DEFAULT_DAG)
    run_next_parser.add_argument("--dry-run", action="store_true")
    run_next_parser.add_argument("--validate", action="store_true")

    validate_parser = subparsers.add_parser("validate", help="运行项目默认质量门禁")
    validate_parser.add_argument("--dry-run", action="store_true")

    sync_parser = subparsers.add_parser("sync-state", help="记录当前 DAG 和下一步状态")
    sync_parser.add_argument("--dag", type=Path, default=DEFAULT_DAG)
    sync_parser.add_argument("--state", type=Path, default=DEFAULT_STATE)
    sync_parser.add_argument("--dry-run", action="store_true")

    weekly_parser = subparsers.add_parser("weekly-evolution", help="运行本地周进化调度入口")
    weekly_parser.add_argument("--dry-run", action="store_true")
    weekly_parser.add_argument("--batch-limit", type=int, default=5)

    regression_parser = subparsers.add_parser("regression-audit", help="运行生产级本地回归审计")
    regression_parser.add_argument("--dry-run", action="store_true")
    regression_parser.add_argument("--batch-limit", type=int, default=5)

    gold_resolve_parser = subparsers.add_parser("resolve-gold-conflicts", help="解决 Gold Set 开放冲突")
    gold_resolve_parser.add_argument("--apply", action="store_true", help="实际新增 consensus_review 版本")
    gold_resolve_parser.add_argument("--limit", type=int, default=20)
    gold_resolve_parser.add_argument("--reviewer-id", default="consensus-panel-v1")

    subparsers.add_parser("scheduler-plan", help="输出生产调度计划，不启动守护进程")
    subparsers.add_parser("scheduler-health", help="输出生产调度健康、告警和恢复手册")

    scheduler_service_parser = subparsers.add_parser("scheduler-service-plan", help="生成 launchd/systemd 服务化配置")
    scheduler_service_parser.add_argument("--apply", action="store_true", help="写入项目内 docs/tasks/scheduler_service 审计目录")

    scheduler_run_parser = subparsers.add_parser("scheduler-run-once", help="立即运行一个生产调度任务")
    scheduler_run_parser.add_argument("job_id")
    scheduler_run_parser.add_argument("--dry-run", action="store_true")
    scheduler_run_parser.add_argument("--apply", action="store_true")
    scheduler_run_parser.add_argument("--batch-limit", type=int, default=None)

    subparsers.add_parser("scheduler-daemon", help="启动 APScheduler 长期守护进程")

    case_quality_parser = subparsers.add_parser("resource-case-quality", help="审计并可选修复资源案例完整度和语境匹配")
    case_quality_parser.add_argument("--apply", action="store_true")
    case_quality_parser.add_argument("--limit", type=int, default=500)
    case_quality_parser.add_argument("--reviewer-id", default="case-quality-automation")

    similarity_rewrite_parser = subparsers.add_parser("resource-similarity-rewrite-iteration", help="按近重复队列自动重写大簇资源")
    similarity_rewrite_parser.add_argument("--apply", action="store_true")
    similarity_rewrite_parser.add_argument("--iterations", type=int, default=1)
    similarity_rewrite_parser.add_argument("--cluster-limit", type=int, default=5000)
    similarity_rewrite_parser.add_argument("--batch-size", type=int, default=12)
    similarity_rewrite_parser.add_argument("--threshold", type=float, default=0.82)
    similarity_rewrite_parser.add_argument("--reviewer-id", default="resource-similarity-commander")

    subparsers.add_parser("worldclass-data-audit", help="审计终极目标下的数据数量、质量、维度和粒度差距")

    args = parser.parse_args(argv)
    if args.command == "run-next":
        result = run_next(dag_path=args.dag, dry_run=args.dry_run, validate=args.validate)
    elif args.command == "validate":
        result = {"status": "validation", "validation": validate_project(dry_run=args.dry_run)}
    elif args.command == "sync-state":
        result = sync_state(dag_path=args.dag, state_path=args.state, dry_run=args.dry_run)
    elif args.command == "weekly-evolution":
        result = run_weekly_evolution(dry_run=args.dry_run, batch_limit=args.batch_limit)
    elif args.command == "regression-audit":
        result = run_regression_audit(dry_run=args.dry_run, batch_limit=args.batch_limit)
    elif args.command == "resolve-gold-conflicts":
        result = resolve_gold_conflicts_command(
            dry_run=not args.apply,
            limit=args.limit,
            reviewer_id=args.reviewer_id,
        )
    elif args.command == "scheduler-plan":
        result = scheduler_plan_command()
    elif args.command == "scheduler-health":
        result = scheduler_health_command()
    elif args.command == "scheduler-service-plan":
        result = scheduler_service_plan_command(apply=args.apply)
    elif args.command == "scheduler-run-once":
        dry_run = False if args.apply else True if args.dry_run else None
        result = scheduler_run_once_command(args.job_id, dry_run=dry_run, batch_limit=args.batch_limit)
    elif args.command == "resource-case-quality":
        result = resource_case_quality_command(apply=args.apply, limit=args.limit, reviewer_id=args.reviewer_id)
    elif args.command == "resource-similarity-rewrite-iteration":
        result = resource_similarity_rewrite_iteration_command(
            apply=args.apply,
            iterations=args.iterations,
            cluster_limit=args.cluster_limit,
            batch_size=args.batch_size,
            threshold=args.threshold,
            reviewer_id=args.reviewer_id,
        )
    elif args.command == "worldclass-data-audit":
        result = worldclass_data_audit_command()
    else:
        result = scheduler_daemon_command()
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return _exit_code(result)


def _task_from_dict(data: dict[str, Any]) -> ModuleTask:
    return ModuleTask(
        id=str(data["id"]),
        name=str(data["name"]),
        priority=int(data["priority"]),
        status=str(data["status"]),
        dependencies=[str(item) for item in data.get("dependencies", [])],
        acceptance=[str(item) for item in data.get("acceptance", [])],
        verification=[str(item) for item in data.get("verification", [])],
    )


def _task_to_dict(task: ModuleTask) -> dict[str, Any]:
    return {
        "id": task.id,
        "name": task.name,
        "priority": task.priority,
        "status": task.status,
        "dependencies": task.dependencies,
        "acceptance": task.acceptance,
        "verification": task.verification,
    }


def _tail(text: str, limit: int = 1800) -> str:
    if len(text) <= limit:
        return text
    return text[-limit:]


def _dag_summary(tasks: list[ModuleTask]) -> dict[str, Any]:
    completed = [task for task in tasks if task.status == "completed"]
    pending = [task for task in tasks if task.status != "completed"]
    return {
        "total": len(tasks),
        "completed": len(completed),
        "pending": len(pending),
        "completion_ratio": round(len(completed) / max(len(tasks), 1), 3),
        "completed_ids": [task.id for task in completed],
        "pending_ids": [task.id for task in pending],
    }


def _now_iso() -> str:
    from datetime import datetime

    return datetime.now().isoformat(timespec="seconds")


def _audit_check(check_id: str, passed: bool, detail: dict[str, Any]) -> dict[str, Any]:
    return {
        "id": check_id,
        "status": "passed" if passed else "needs_attention",
        "detail": detail,
    }


def _regression_next_actions(failed: list[dict[str, Any]]) -> list[str]:
    if not failed:
        return ["record audit snapshot and continue with the next world-class reinforcement target"]
    return [f"inspect {item['id']} regression detail" for item in failed]


def _import_quality_audit_detail(report: dict[str, Any]) -> dict[str, Any]:
    repair_plan = report.get("repair_plan", {})
    plan_counts = _import_quality_repair_plan_counts(repair_plan)
    return {
        "quality_score": report.get("quality_score"),
        "totals": report.get("totals", {}),
        "issue_count": _import_quality_issue_count(report),
        "active_issue_count": _import_quality_active_issue_count(report),
        "resolved_issue_count": _import_quality_resolved_issue_count(report),
        "quality_debt": report.get("quality_debt", {}),
        "repair_plan_counts": plan_counts,
        "next_actions": _import_quality_next_actions(report, plan_counts),
    }


def _import_quality_repair_plan_counts(repair_plan: Any) -> dict[str, int]:
    if not isinstance(repair_plan, dict):
        return {}
    counts: dict[str, int] = {}
    for section in ("samples", "resources", "knowledge_entries"):
        section_plan = repair_plan.get(section)
        if isinstance(section_plan, dict):
            counts[section] = sum(int(value) for value in section_plan.values() if isinstance(value, int))
    return counts


def _import_quality_issue_count(report: dict[str, Any]) -> int:
    totals = report.get("totals", {})
    if isinstance(totals, dict) and "issues" in totals:
        return int(totals.get("issues") or 0)
    issues = report.get("issues", [])
    return len(issues) if isinstance(issues, list) else 0


def _import_quality_active_issue_count(report: dict[str, Any]) -> int:
    totals = report.get("totals", {})
    if isinstance(totals, dict) and "active_issues" in totals:
        return int(totals.get("active_issues") or 0)
    quality_debt = report.get("quality_debt", {})
    if isinstance(quality_debt, dict):
        return int(quality_debt.get("manual_review_issues") or 0)
    return 0


def _import_quality_resolved_issue_count(report: dict[str, Any]) -> int:
    quality_debt = report.get("quality_debt", {})
    if isinstance(quality_debt, dict):
        return int(quality_debt.get("resolved_issues") or 0)
    issue_summary = report.get("issue_summary", {})
    if isinstance(issue_summary, dict):
        return int(issue_summary.get("resolved") or 0)
    return 0


def _import_quality_next_actions(report: dict[str, Any], plan_counts: dict[str, int]) -> list[str]:
    score = float(report.get("quality_score", 0) or 0)
    quality_debt = report.get("quality_debt", {})
    auto_repairable = int(quality_debt.get("auto_repairable_fields") or 0) if isinstance(quality_debt, dict) else 0
    manual_review = int(quality_debt.get("manual_review_issues") or 0) if isinstance(quality_debt, dict) else 0
    actions: list[str] = []
    if score < 85:
        actions.append(f"raise import quality score from {score:.1f} to at least 85")
    if auto_repairable > 0 or sum(plan_counts.values()) > 0:
        actions.append("run import-quality repair plan and review remaining metadata gaps")
    if manual_review > 0:
        actions.append("triage historical import issues and resolve source-level defects")
    if not actions:
        actions.append("keep import quality under scheduled regression monitoring")
    return actions


def _gold_calibration_snapshot(report: dict[str, Any]) -> dict[str, Any]:
    summary = report.get("summary", {})
    gates = report.get("quality_gates", {})
    return {
        "expert_reviews": summary.get("expert_reviews"),
        "consensus_reviews": summary.get("consensus_reviews"),
        "multi_reviewer_samples": summary.get("multi_reviewer_samples"),
        "comparable_pairs": summary.get("comparable_pairs"),
        "decision_agreement_rate": summary.get("decision_agreement_rate"),
        "average_total_score_delta": summary.get("average_total_score_delta"),
        "open_conflict_samples": summary.get("conflict_samples"),
        "resolved_conflict_samples": summary.get("resolved_conflict_samples"),
        "ready_for_multi_reviewer_calibration": gates.get("ready_for_multi_reviewer_calibration"),
    }


def _count(connection: Any, table: str) -> int:
    return int(connection.execute(f"SELECT count(*) FROM {table}").fetchone()[0])


def _coverage(connection: Any, table: str, field: str, total: int) -> dict[str, Any]:
    filled = int(connection.execute(f"SELECT count(*) FROM {table} WHERE {field} IS NOT NULL AND trim({field}) <> ''").fetchone()[0])
    return {"filled": filled, "total": total, "ratio": round(filled / max(total, 1), 4)}


def _target_gap(name: str, detail: dict[str, Any]) -> dict[str, Any]:
    current = int(detail["current"])
    target = int(detail["target"])
    return {
        "id": name,
        "priority": str(detail["priority"]),
        "current": current,
        "target": target,
        "gap": max(0, target - current),
        "action": f"expand {name} toward target {target}",
    }


def _coverage_gaps(sample_coverage: dict[str, dict[str, Any]]) -> list[dict[str, Any]]:
    gaps: list[dict[str, Any]] = []
    for field, detail in sample_coverage.items():
        if float(detail["ratio"]) >= 0.98:
            continue
        gaps.append({
            "id": f"sample_coverage:{field}",
            "priority": "P1",
            "current": detail["filled"],
            "target": detail["total"],
            "gap": int(detail["total"]) - int(detail["filled"]),
            "action": f"complete interaction sample field {field}",
        })
    return gaps


def _worldclass_next_actions(gaps: list[dict[str, Any]]) -> list[str]:
    active = [gap for gap in gaps if gap.get("gap")]
    if not active:
        return ["keep world-class data matrix under scheduled audit"]
    priorities = [gap for gap in active if gap.get("priority") in {"P0", "P1"}]
    selected = priorities or active
    return [str(item["action"]) for item in selected[:5]]


def _similarity_snapshot(report: dict[str, Any]) -> dict[str, Any]:
    clusters = report.get("clusters", [])
    return {
        "summary": report.get("summary", {}),
        "top_clusters": [
            {
                "family_key": item.get("family_key"),
                "size": item.get("size"),
                "highest_similarity": item.get("highest_similarity"),
                "average_similarity": item.get("average_similarity"),
            }
            for item in clusters[:5]
        ],
        "next_actions": report.get("next_actions", [])[:3],
    }


def _exit_code(result: dict[str, Any]) -> int:
    for item in result.get("validation", []):
        if item.get("returncode") not in (0, None):
            return int(item["returncode"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
