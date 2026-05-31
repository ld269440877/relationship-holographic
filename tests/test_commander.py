import json

from tools.commander import (
    ModuleTask,
    load_module_dag,
    resolve_gold_conflicts_command,
    resource_similarity_rewrite_iteration_command,
    run_next,
    run_regression_audit,
    run_weekly_evolution,
    scheduler_health_command,
    scheduler_plan_command,
    scheduler_run_once_command,
    scheduler_service_plan_command,
    select_next_task,
    sync_state,
)


def test_commander_selects_first_unfinished_ready_task_from_dag_nodes():
    tasks = [
        ModuleTask(
            id="data_life_cycle",
            name="数据生命体闭环",
            priority=10,
            status="completed",
            dependencies=[],
            acceptance=[],
            verification=[],
        ),
        ModuleTask(
            id="blocked_quality",
            name="被依赖阻塞的质量任务",
            priority=20,
            status="pending",
            dependencies=["missing_dependency"],
            acceptance=[],
            verification=[],
        ),
        ModuleTask(
            id="ready_quality",
            name="已就绪质量任务",
            priority=30,
            status="pending",
            dependencies=["data_life_cycle"],
            acceptance=[],
            verification=["pytest -q"],
        ),
    ]
    selected = select_next_task(tasks)

    assert selected is not None
    assert selected.id == "ready_quality"
    assert selected.status == "pending"


def test_commander_run_next_dry_run_outputs_validation_commands(tmp_path):
    dag_path = tmp_path / "module_dag.json"
    dag_path.write_text(
        json.dumps(
            {
                "modules": [
                    {
                        "id": "base",
                        "name": "基础",
                        "priority": 10,
                        "status": "completed",
                        "dependencies": [],
                        "acceptance": [],
                        "verification": [],
                    },
                    {
                        "id": "next",
                        "name": "下一项",
                        "priority": 20,
                        "status": "pending",
                        "dependencies": ["base"],
                        "acceptance": ["can be validated"],
                        "verification": ["pytest -q"],
                    },
                ]
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )
    result = run_next(dag_path=dag_path, dry_run=True)

    assert result["status"] == "next_task"
    assert result["task"]["id"] == "next"
    assert result["validation"]
    assert result["validation"][0]["status"] == "dry_run"


def test_module_dag_json_is_parseable():
    tasks = load_module_dag()
    encoded = json.dumps([task.id for task in tasks], ensure_ascii=False)

    assert "data_life_cycle" in encoded
    assert "dynamic_evolution_scheduler" in encoded


def test_commander_sync_state_records_next_task_snapshot(tmp_path):
    dag_path = tmp_path / "module_dag.json"
    state_path = tmp_path / "commander_state.json"
    dag_path.write_text(
        json.dumps(
            {
                "modules": [
                    {"id": "done", "name": "完成", "priority": 1, "status": "completed", "dependencies": [], "acceptance": [], "verification": []},
                    {"id": "next", "name": "下一项", "priority": 2, "status": "pending", "dependencies": ["done"], "acceptance": [], "verification": []},
                ]
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )

    snapshot = sync_state(dag_path=dag_path, state_path=state_path)

    assert snapshot["status"] == "recorded"
    assert snapshot["next_task"]["id"] == "next"
    assert snapshot["summary"]["completed"] == 1
    assert json.loads(state_path.read_text(encoding="utf-8"))["next_task"]["id"] == "next"


def test_commander_weekly_evolution_dry_run_entry():
    result = run_weekly_evolution(dry_run=True, batch_limit=2)

    assert result["dry_run"] is True
    assert "next_actions" in result


def test_commander_regression_audit_dry_run_plans_core_gates():
    result = run_regression_audit(dry_run=True, batch_limit=2)

    check_ids = {item["id"] for item in result["checks"]}
    assert result["dry_run"] is True
    assert {"database_health", "weekly_evolution", "import_quality", "reviewed_publish_candidates", "vector_recall", "gold_interrater", "gold_conflict_queue", "ai_quality", "ai_failure_analysis", "ai_provider_diagnostics"} <= check_ids


def test_commander_regression_audit_runs_local_gates():
    result = run_regression_audit(dry_run=False, batch_limit=2)

    check_ids = {item["id"] for item in result["checks"]}
    assert result["dry_run"] is False
    assert "database_health" in check_ids
    assert "import_quality" in check_ids
    assert "gold_interrater" in check_ids
    assert "gold_conflict_queue" in check_ids
    assert "ai_failure_analysis" in check_ids
    assert "ai_provider_diagnostics" in check_ids
    import_quality = next(item for item in result["checks"] if item["id"] == "import_quality")
    assert "quality_score" in import_quality["detail"]
    assert "quality_debt" in import_quality["detail"]
    assert "repair_plan_counts" in import_quality["detail"]
    publish_candidates = next(item for item in result["checks"] if item["id"] == "reviewed_publish_candidates")
    assert "publish_ready" in publish_candidates["detail"]
    assert "quality_gates" in publish_candidates["detail"]
    provider = next(item for item in result["checks"] if item["id"] == "ai_provider_diagnostics")
    assert "provider" in provider["detail"]
    assert "request_shape" in provider["detail"]
    assert "schema_hash" in provider["detail"]["request_shape"]
    assert "risk_level" in provider["detail"]
    gold_conflicts = next(item for item in result["checks"] if item["id"] == "gold_conflict_queue")
    assert "total" in gold_conflicts["detail"]
    assert "quality_gates" in gold_conflicts["detail"]
    gold = next(item for item in result["checks"] if item["id"] == "gold_interrater")
    assert "resolved_conflict_samples" in gold["detail"]
    assert "open_conflict_samples" in gold["detail"]
    assert all(item["status"] in {"passed", "needs_attention"} for item in result["checks"])
    assert result["next_actions"]


def test_commander_gold_conflict_resolution_command_dry_run_and_apply():
    preview = resolve_gold_conflicts_command(dry_run=True, limit=1, reviewer_id="consensus-test")

    assert preview["dry_run"] is True
    assert "before" in preview
    assert "after" in preview
    assert preview["result"]["dry_run"] is True
    if preview["result"]["would_create_versions"] == 0:
        return

    applied = resolve_gold_conflicts_command(dry_run=False, limit=1, reviewer_id="consensus-test")

    assert applied["dry_run"] is False
    assert applied["result"]["dry_run"] is False
    assert applied["result"]["resolved_count"] >= 1
    assert applied["after"]["resolved_conflict_samples"] >= applied["before"]["resolved_conflict_samples"]


def test_resource_similarity_rewrite_iteration_command_dry_run_selects_largest_cluster():
    from sqlmodel import Session

    from backend.database.connection import create_db_and_tables, engine
    from backend.models.resource import ResourceLibrary

    create_db_and_tables()
    unique = "commander-similarity-" + json.dumps({"k": "v"}).replace('"', "")
    with Session(engine) as session:
        for index in range(1, 5):
            session.add(
                ResourceLibrary(
                    resource_uuid=f"{unique}-{index}",
                    type="story",
                    category=f"近重复治理{unique}",
                    title=f"修复｜重复簇｜案例{index}",
                    content="场景：重复簇测试。TA说：我有点累。常见失误：你又不回。更好回应：我不催你，晚点说也可以。边界：允许暂停。练习任务：改写一句。",
                    applicable_scene="修复",
                    tags=f"具体案例,{unique}",
                    quality_score=95,
                    review_status="reviewed",
                    source="pytest",
                )
            )
        session.commit()

    result = resource_similarity_rewrite_iteration_command(
        apply=False,
        iterations=3,
        cluster_limit=1000,
        batch_size=3,
        reviewer_id="commander-rewrite-test",
    )

    assert result["status"] == "dry_run"
    assert result["rounds"]
    assert result["rounds"][0]["drafts"] == 3
    assert result["quality_gates"]["originals_quarantined_not_deleted"] is True


def test_commander_scheduler_plan_and_run_once_are_auditable(tmp_path, monkeypatch):
    state_path = tmp_path / "scheduler_state.json"
    plan = scheduler_plan_command()

    job_ids = {item["id"] for item in plan["jobs"]}
    assert {"commander_sync_state_hourly", "regression_audit_daily", "weekly_evolution_dry_run"} <= job_ids
    assert plan["quality_gates"]["uses_apscheduler"] is True

    import backend.core.production_scheduler as production_scheduler

    monkeypatch.setattr(production_scheduler, "DEFAULT_SCHEDULER_STATE", state_path)
    result = scheduler_run_once_command("weekly_evolution_dry_run", dry_run=True, batch_limit=1)

    assert result["ok"] is True
    assert result["snapshot"]["dry_run"] is True
    assert result["snapshot"]["job"]["id"] == "weekly_evolution_dry_run"
    assert "health" in result
    assert state_path.exists()
    state = json.loads(state_path.read_text(encoding="utf-8"))
    assert "health" in state
    assert "recovery_runbook" in state["health"]


def test_scheduler_health_reports_missing_required_jobs(tmp_path, monkeypatch):
    import backend.core.production_scheduler as production_scheduler

    state_path = tmp_path / "scheduler_state.json"
    state_path.write_text(json.dumps({"history": []}), encoding="utf-8")
    monkeypatch.setattr(production_scheduler, "DEFAULT_SCHEDULER_STATE", state_path)

    health = scheduler_health_command()

    assert health["status"] == "needs_attention"
    assert any(item["job_id"] == "commander_sync_state_hourly" for item in health["alerts"])
    assert any(step["command"].startswith(".venv/bin/python -m tools.commander") for step in health["recovery_runbook"])


def test_scheduler_health_marks_run_once_history_as_observed(tmp_path, monkeypatch):
    import backend.core.production_scheduler as production_scheduler

    state_path = tmp_path / "scheduler_state.json"
    monkeypatch.setattr(production_scheduler, "DEFAULT_SCHEDULER_STATE", state_path)

    scheduler_run_once_command("commander_sync_state_hourly", dry_run=True)
    health = scheduler_health_command()
    sync_job = next(item for item in health["jobs"] if item["id"] == "commander_sync_state_hourly")

    assert sync_job["observed"] is True
    assert sync_job["latest_status"] == "dry_run"
    assert sync_job["stale"] is False


def test_production_scheduler_daemon_registers_expected_jobs():
    from backend.core.production_scheduler import build_background_scheduler

    scheduler = build_background_scheduler(job_runner=lambda job_id: {"job_id": job_id})

    try:
        job_ids = {job.id for job in scheduler.get_jobs()}
    finally:
        if scheduler.running:
            scheduler.shutdown(wait=False)
    assert {"commander_sync_state_hourly", "regression_audit_daily", "weekly_evolution_dry_run"} <= job_ids


def test_scheduler_service_plan_generates_project_local_artifacts(tmp_path):
    from backend.core.production_scheduler import scheduler_service_plan

    preview = scheduler_service_plan(service_dir=tmp_path, write_files=False)

    assert preview["status"] == "planned"
    assert preview["quality_gates"]["global_install_performed"] is False
    assert any(item["kind"] == "launchd" for item in preview["artifacts"])
    assert any(item["kind"] == "systemd_user" for item in preview["artifacts"])
    assert not list(tmp_path.iterdir())

    applied = scheduler_service_plan(service_dir=tmp_path, write_files=True)

    assert applied["status"] == "generated"
    assert (tmp_path / "com.relationship-dynamics.commander-scheduler.plist").exists()
    assert (tmp_path / "relationship-dynamics-scheduler.service").exists()
    assert (tmp_path / "manifest.json").exists()
    manifest = json.loads((tmp_path / "manifest.json").read_text(encoding="utf-8"))
    assert manifest["quality_gates"]["project_local_generation_only"] is True


def test_commander_scheduler_service_plan_command_preview():
    result = scheduler_service_plan_command(apply=False)

    assert result["status"] == "planned"
    assert result["quality_gates"]["daemon_command"] == "tools.commander scheduler-daemon"
