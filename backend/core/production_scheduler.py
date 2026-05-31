"""Production-style scheduler definitions for commander quality gates."""
from __future__ import annotations

import json
from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime
from importlib import import_module
from pathlib import Path
from typing import Any

from apscheduler.schedulers.background import BackgroundScheduler  # type: ignore[import-untyped]
from apscheduler.triggers.cron import CronTrigger  # type: ignore[import-untyped]
from apscheduler.triggers.interval import IntervalTrigger  # type: ignore[import-untyped]


@dataclass(frozen=True)
class SchedulerJobSpec:
    id: str
    name: str
    command: str
    trigger: str
    dry_run_default: bool
    batch_limit: int
    risk_gate: str


PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_SCHEDULER_STATE = PROJECT_ROOT / "docs" / "tasks" / "production_scheduler_state.json"
DEFAULT_SERVICE_DIR = PROJECT_ROOT / "docs" / "tasks" / "scheduler_service"

PRODUCTION_JOBS = [
    SchedulerJobSpec(
        id="commander_sync_state_hourly",
        name="Commander 状态同步",
        command="sync_state",
        trigger="interval:hours=1",
        dry_run_default=False,
        batch_limit=0,
        risk_gate="writes only docs/tasks/commander_state.json",
    ),
    SchedulerJobSpec(
        id="regression_audit_daily",
        name="每日生产回归审计",
        command="regression_audit",
        trigger="cron:hour=7,minute=30",
        dry_run_default=False,
        batch_limit=2,
        risk_gate="read-only local quality gates",
    ),
    SchedulerJobSpec(
        id="weekly_evolution_dry_run",
        name="每周进化调度预演",
        command="weekly_evolution",
        trigger="cron:day_of_week=mon,hour=8,minute=0",
        dry_run_default=True,
        batch_limit=5,
        risk_gate="dry-run by default; does not publish assets",
    ),
]


def scheduler_plan() -> dict[str, Any]:
    """Return auditable scheduler jobs without starting a daemon."""
    return {
        "jobs": [_job_to_dict(job) for job in PRODUCTION_JOBS],
        "state_path": str(DEFAULT_SCHEDULER_STATE),
        "health": scheduler_health(),
        "quality_gates": {
            "uses_apscheduler": True,
            "has_regression_audit": True,
            "weekly_evolution_is_dry_run_by_default": True,
            "writes_audit_snapshot": True,
            "has_failure_alerts": True,
            "has_recovery_runbook": True,
        },
        "principle": "生产调度默认可审计、可 dry-run、可单次执行；守护进程只调度既有 commander 安全入口。",
    }


def scheduler_service_plan(
    *,
    service_dir: Path = DEFAULT_SERVICE_DIR,
    python_path: Path | None = None,
    write_files: bool = False,
) -> dict[str, Any]:
    """Build auditable launchd/systemd service artifacts without installing them globally."""
    resolved_python = python_path or PROJECT_ROOT / ".venv" / "bin" / "python"
    artifacts = _service_artifacts(resolved_python)
    result = {
        "status": "generated" if write_files else "planned",
        "service_dir": str(service_dir),
        "python_path": str(resolved_python),
        "artifacts": artifacts,
        "install_guidance": {
            "macos_launchd": {
                "copy_to": "~/Library/LaunchAgents/com.relationship-dynamics.commander-scheduler.plist",
                "load_command": "launchctl load ~/Library/LaunchAgents/com.relationship-dynamics.commander-scheduler.plist",
                "unload_command": "launchctl unload ~/Library/LaunchAgents/com.relationship-dynamics.commander-scheduler.plist",
            },
            "linux_systemd_user": {
                "copy_to": "~/.config/systemd/user/relationship-dynamics-scheduler.service",
                "enable_command": "systemctl --user enable --now relationship-dynamics-scheduler.service",
                "status_command": "systemctl --user status relationship-dynamics-scheduler.service",
            },
        },
        "quality_gates": {
            "project_local_generation_only": True,
            "global_install_performed": False,
            "daemon_command": "tools.commander scheduler-daemon",
            "state_snapshot": str(DEFAULT_SCHEDULER_STATE),
        },
        "principle": "服务化配置先生成到项目审计目录；不自动写入 launchd/systemd 全局位置，避免无审计地改变本机守护进程。",
    }
    if write_files:
        service_dir.mkdir(parents=True, exist_ok=True)
        written: dict[str, str] = {}
        for artifact in artifacts:
            path = service_dir / artifact["filename"]
            path.write_text(str(artifact["content"]), encoding="utf-8")
            written[artifact["kind"]] = str(path)
        manifest = service_dir / "manifest.json"
        manifest_payload = dict(result)
        manifest_payload["written"] = written
        manifest.write_text(json.dumps(manifest_payload, ensure_ascii=False, indent=2), encoding="utf-8")
        written_with_manifest = dict(written)
        written_with_manifest["manifest"] = str(manifest)
        result["written"] = written_with_manifest
    return result


def run_scheduled_job(
    job_id: str,
    *,
    dry_run: bool | None = None,
    batch_limit: int | None = None,
    state_path: Path | None = None,
) -> dict[str, Any]:
    """Run one scheduled job immediately and persist a compact audit snapshot."""
    job = _job_by_id(job_id)
    resolved_state_path = state_path or DEFAULT_SCHEDULER_STATE
    effective_dry_run = job.dry_run_default if dry_run is None else dry_run
    effective_batch_limit = job.batch_limit if batch_limit is None else batch_limit
    result = _execute_job(job, dry_run=effective_dry_run, batch_limit=effective_batch_limit)
    snapshot = {
        "job": _job_to_dict(job),
        "ran_at": datetime.now().isoformat(timespec="seconds"),
        "dry_run": effective_dry_run,
        "batch_limit": effective_batch_limit,
        "result_status": _result_status(result),
        "result_summary": _result_summary(result),
    }
    _record_scheduler_state(snapshot, resolved_state_path)
    return {
        "ok": True,
        "snapshot": snapshot,
        "health": scheduler_health(resolved_state_path),
        "state_path": str(resolved_state_path),
        "principle": "run-once 用于部署前验证；所有结果写入本地调度审计快照。",
    }


def scheduler_health(state_path: Path | None = None) -> dict[str, Any]:
    """Summarize long-running scheduler health from the local audit snapshot."""
    resolved_state_path = state_path or DEFAULT_SCHEDULER_STATE
    state = _load_scheduler_state(resolved_state_path)
    history = [item for item in state.get("history", []) if isinstance(item, dict)]
    latest_by_job = _latest_scheduler_snapshots(history)
    now = datetime.now()
    job_health = [_scheduler_job_health(job, latest_by_job.get(job.id), now) for job in PRODUCTION_JOBS]
    alerts = _scheduler_alerts(job_health)
    return {
        "status": "healthy" if not alerts else "needs_attention",
        "checked_at": now.isoformat(timespec="seconds"),
        "state_path": str(resolved_state_path),
        "jobs": job_health,
        "alerts": alerts,
        "recovery_runbook": _scheduler_recovery_runbook(alerts),
        "quality_gate": {
            "state_file_exists": resolved_state_path.exists(),
            "all_jobs_observed": all(item["observed"] for item in job_health),
            "no_failed_latest_runs": not any(item["latest_status"] in {"failed", "needs_attention"} for item in job_health),
            "no_stale_required_jobs": not any(item["stale"] for item in job_health if item["required"]),
        },
        "principle": "调度健康只基于本地审计快照、任务摘要和时间戳，不保存敏感原文。",
    }


def build_background_scheduler(
    *,
    state_path: Path = DEFAULT_SCHEDULER_STATE,
    job_runner: Callable[[str], dict[str, Any]] | None = None,
) -> Any:
    """Build but do not start an APScheduler daemon."""
    scheduler = BackgroundScheduler(timezone="Asia/Shanghai")
    runner = job_runner or (lambda job_id: run_scheduled_job(job_id, state_path=state_path))
    for job in PRODUCTION_JOBS:
        scheduler.add_job(
            runner,
            _trigger_for(job.trigger),
            id=job.id,
            name=job.name,
            args=[job.id],
            replace_existing=True,
            max_instances=1,
            coalesce=True,
        )
    return scheduler


def _execute_job(job: SchedulerJobSpec, *, dry_run: bool, batch_limit: int) -> dict[str, Any]:
    commander: Any = import_module("tools.commander")

    if job.command == "sync_state":
        result: Any = commander.sync_state(dry_run=dry_run)
        return _ensure_dict(result)
    if job.command == "regression_audit":
        result = commander.run_regression_audit(dry_run=dry_run, batch_limit=batch_limit)
        return _ensure_dict(result)
    if job.command == "weekly_evolution":
        result = commander.run_weekly_evolution(dry_run=dry_run, batch_limit=batch_limit)
        return _ensure_dict(result)
    raise ValueError(f"unknown scheduler command: {job.command}")


def _record_scheduler_state(snapshot: dict[str, Any], state_path: Path) -> None:
    state_path.parent.mkdir(parents=True, exist_ok=True)
    history: list[dict[str, Any]] = []
    if state_path.exists():
        try:
            current = json.loads(state_path.read_text(encoding="utf-8"))
            if isinstance(current.get("history"), list):
                history = [item for item in current["history"] if isinstance(item, dict)]
        except json.JSONDecodeError:
            history = []
    history.append(snapshot)
    state = {
        "updated_at": datetime.now().isoformat(timespec="seconds"),
        "latest": snapshot,
        "history": history[-20:],
        "health": scheduler_health_from_history(history[-20:], state_path),
        "principle": "长期调度审计只保存任务状态、摘要和门禁结果，不保存敏感原文。",
    }
    state_path.write_text(json.dumps(state, ensure_ascii=False, indent=2), encoding="utf-8")


def scheduler_health_from_history(history: list[dict[str, Any]], state_path: Path = DEFAULT_SCHEDULER_STATE) -> dict[str, Any]:
    now = datetime.now()
    latest_by_job = _latest_scheduler_snapshots(history)
    job_health = [_scheduler_job_health(job, latest_by_job.get(job.id), now) for job in PRODUCTION_JOBS]
    alerts = _scheduler_alerts(job_health)
    return {
        "status": "healthy" if not alerts else "needs_attention",
        "checked_at": now.isoformat(timespec="seconds"),
        "state_path": str(state_path),
        "jobs": job_health,
        "alerts": alerts,
        "recovery_runbook": _scheduler_recovery_runbook(alerts),
    }


def _load_scheduler_state(state_path: Path) -> dict[str, Any]:
    if not state_path.exists():
        return {}
    try:
        value = json.loads(state_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {}
    return value if isinstance(value, dict) else {}


def _latest_scheduler_snapshots(history: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    latest: dict[str, dict[str, Any]] = {}
    for item in history:
        job = item.get("job")
        if isinstance(job, dict) and job.get("id"):
            latest[str(job["id"])] = item
    return latest


def _scheduler_job_health(job: SchedulerJobSpec, snapshot: dict[str, Any] | None, now: datetime) -> dict[str, Any]:
    if snapshot is None:
        return {
            "id": job.id,
            "name": job.name,
            "required": job.id != "weekly_evolution_dry_run",
            "observed": False,
            "stale": True,
            "latest_status": "missing",
            "last_run_at": None,
            "minutes_since_last_run": None,
            "expected_interval_minutes": _expected_interval_minutes(job),
            "recovery_action": f"run scheduler-run-once {job.id} --dry-run",
        }
    ran_at = _parse_datetime(str(snapshot.get("ran_at") or ""))
    minutes_since = int((now - ran_at).total_seconds() // 60) if ran_at else None
    expected = _expected_interval_minutes(job)
    stale = minutes_since is None or minutes_since > expected
    latest_status = str(snapshot.get("result_status") or "unknown")
    return {
        "id": job.id,
        "name": job.name,
        "required": job.id != "weekly_evolution_dry_run",
        "observed": True,
        "stale": stale,
        "latest_status": latest_status,
        "last_run_at": ran_at.isoformat(timespec="seconds") if ran_at else None,
        "minutes_since_last_run": minutes_since,
        "expected_interval_minutes": expected,
        "recovery_action": _scheduler_recovery_action(job, latest_status, stale),
    }


def _scheduler_alerts(job_health: list[dict[str, Any]]) -> list[dict[str, str]]:
    alerts: list[dict[str, str]] = []
    for item in job_health:
        if not item["observed"] and item["required"]:
            alerts.append({
                "severity": "high",
                "job_id": str(item["id"]),
                "reason": "required scheduler job has no audit snapshot",
                "action": str(item["recovery_action"]),
            })
        elif item["latest_status"] in {"failed", "needs_attention"}:
            alerts.append({
                "severity": "high",
                "job_id": str(item["id"]),
                "reason": f"latest status is {item['latest_status']}",
                "action": str(item["recovery_action"]),
            })
        elif item["stale"] and item["required"]:
            alerts.append({
                "severity": "medium",
                "job_id": str(item["id"]),
                "reason": "required scheduler job is stale",
                "action": str(item["recovery_action"]),
            })
    return alerts[:8]


def _scheduler_recovery_runbook(alerts: list[dict[str, str]]) -> list[dict[str, str]]:
    steps = [
        {
            "step": "1",
            "title": "Inspect scheduler health",
            "command": ".venv/bin/python -m tools.commander scheduler-health",
        },
        {
            "step": "2",
            "title": "Run affected job once",
            "command": alerts[0]["action"] if alerts else ".venv/bin/python -m tools.commander scheduler-run-once regression_audit_daily --dry-run",
        },
        {
            "step": "3",
            "title": "Re-run production regression audit",
            "command": ".venv/bin/python -m tools.commander regression-audit --batch-limit 2",
        },
        {
            "step": "4",
            "title": "Check service manager logs",
            "command": "tail docs/tasks/scheduler_service/scheduler.err.log",
        },
    ]
    return steps


def _scheduler_recovery_action(job: SchedulerJobSpec, latest_status: str, stale: bool) -> str:
    mode = "--apply" if job.id == "regression_audit_daily" and latest_status != "failed" and not stale else "--dry-run"
    batch = f" --batch-limit {job.batch_limit}" if job.batch_limit else ""
    return f".venv/bin/python -m tools.commander scheduler-run-once {job.id} {mode}{batch}"


def _expected_interval_minutes(job: SchedulerJobSpec) -> int:
    if job.trigger.startswith("interval:hours="):
        raw = job.trigger.split("interval:hours=", 1)[1].split(",", 1)[0]
        return int(raw) * 3 * 60
    if job.id == "weekly_evolution_dry_run":
        return 10 * 24 * 60
    return 36 * 60


def _parse_datetime(value: str) -> datetime | None:
    if not value:
        return None
    try:
        return datetime.fromisoformat(value)
    except ValueError:
        return None


def _job_by_id(job_id: str) -> SchedulerJobSpec:
    for job in PRODUCTION_JOBS:
        if job.id == job_id:
            return job
    raise ValueError(f"unknown scheduler job: {job_id}")


def _job_to_dict(job: SchedulerJobSpec) -> dict[str, Any]:
    return {
        "id": job.id,
        "name": job.name,
        "command": job.command,
        "trigger": job.trigger,
        "dry_run_default": job.dry_run_default,
        "batch_limit": job.batch_limit,
        "risk_gate": job.risk_gate,
    }


def _service_artifacts(python_path: Path) -> list[dict[str, str]]:
    command = f"{python_path} -m tools.commander scheduler-daemon"
    stdout_log = PROJECT_ROOT / "docs" / "tasks" / "scheduler_service" / "scheduler.out.log"
    stderr_log = PROJECT_ROOT / "docs" / "tasks" / "scheduler_service" / "scheduler.err.log"
    launchd = f"""<?xml version=\"1.0\" encoding=\"UTF-8\"?>
<!DOCTYPE plist PUBLIC \"-//Apple//DTD PLIST 1.0//EN\" \"http://www.apple.com/DTDs/PropertyList-1.0.dtd\">
<plist version=\"1.0\">
<dict>
  <key>Label</key>
  <string>com.relationship-dynamics.commander-scheduler</string>
  <key>ProgramArguments</key>
  <array>
    <string>{python_path}</string>
    <string>-m</string>
    <string>tools.commander</string>
    <string>scheduler-daemon</string>
  </array>
  <key>WorkingDirectory</key>
  <string>{PROJECT_ROOT}</string>
  <key>RunAtLoad</key>
  <true/>
  <key>KeepAlive</key>
  <true/>
  <key>StandardOutPath</key>
  <string>{stdout_log}</string>
  <key>StandardErrorPath</key>
  <string>{stderr_log}</string>
</dict>
</plist>
"""
    systemd = f"""[Unit]
Description=Relationship Dynamics Commander Scheduler
After=network.target

[Service]
Type=simple
WorkingDirectory={PROJECT_ROOT}
ExecStart={command}
Restart=always
RestartSec=20
StandardOutput=append:{stdout_log}
StandardError=append:{stderr_log}

[Install]
WantedBy=default.target
"""
    return [
        {
            "kind": "launchd",
            "filename": "com.relationship-dynamics.commander-scheduler.plist",
            "content": launchd,
        },
        {
            "kind": "systemd_user",
            "filename": "relationship-dynamics-scheduler.service",
            "content": systemd,
        },
    ]


def _trigger_for(trigger: str) -> Any:
    kind, _, raw = trigger.partition(":")
    params = dict(item.split("=", 1) for item in raw.split(",") if item)
    if kind == "interval":
        interval_params = {key: int(value) for key, value in params.items()}
        return IntervalTrigger(**interval_params)
    if kind == "cron":
        return CronTrigger(**params)
    raise ValueError(f"unknown trigger: {trigger}")


def _ensure_dict(result: Any) -> dict[str, Any]:
    return result if isinstance(result, dict) else {"status": "unknown", "result": str(result)}


def _result_status(result: dict[str, Any]) -> str:
    status = result.get("status")
    if isinstance(status, str):
        return status
    if result.get("dry_run") is True:
        return "dry_run"
    return "recorded"


def _result_summary(result: dict[str, Any]) -> dict[str, Any]:
    if "summary" in result and isinstance(result["summary"], dict):
        return {"summary": result["summary"], "next_task": result.get("next_task")}
    if "checks" in result and isinstance(result["checks"], list):
        return {
            "checks": [
                {"id": item.get("id"), "status": item.get("status")}
                for item in result["checks"][:12]
                if isinstance(item, dict)
            ],
            "next_actions": result.get("next_actions", [])[:4],
        }
    return {
        "dry_run": result.get("dry_run"),
        "next_actions": result.get("next_actions", [])[:4] if isinstance(result.get("next_actions"), list) else [],
    }
