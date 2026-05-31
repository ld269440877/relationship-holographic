"""Formal migration runner with backup and audit records.

The schema guard keeps local SQLite compatible by creating missing tables and
adding missing columns. This runner adds a more professional governance layer:
planned revisions, dry-run visibility, pre-run backups, and durable run
records. It intentionally avoids destructive migrations until an explicit
revision implements them.
"""
from __future__ import annotations

import json
import shutil
from datetime import datetime
from typing import Any

from sqlalchemy import Engine, inspect, text
from sqlmodel import Session

from backend.core.vector_index import rebuild_metadata_vector_index
from backend.database.connection import DB_PATH
from backend.database.schema_guard import audit_schema, ensure_schema_compatibility

RUNNER_TABLE = "formal_migration_runs"
BACKUP_DIR = DB_PATH.parent / "backups"

MIGRATION_REVISIONS: list[dict[str, Any]] = [
    {
        "revision": "2026_05_21_formal_runner_v1",
        "title": "正式迁移运行器与备份审计",
        "status": "active",
        "destructive": False,
        "capabilities": ["dry_run_plan", "pre_run_backup", "schema_guard_execution", "run_audit"],
    },
    {
        "revision": "2026_05_21_metadata_vector_index_rebuild_v1",
        "title": "元数据向量索引重建与 sqlite-vec 镜像校验",
        "status": "active",
        "destructive": False,
        "capabilities": ["vector_index_build", "metadata_signature_backfill", "sqlite_vec_sync", "index_row_audit"],
    },
    {
        "revision": "2026_05_22_import_issue_status_normalization_v1",
        "title": "导入 issue 状态归一化与治理字段回填",
        "status": "active",
        "destructive": False,
        "capabilities": ["import_issue_status_normalization", "updated_at_backfill", "issue_status_audit"],
    },
    {
        "revision": "future_rebuild_migrations_v1",
        "title": "SQLite 表重建类迁移",
        "status": "planned",
        "destructive": True,
        "capabilities": ["rename_column", "drop_column", "change_column_type", "rollback_metadata"],
    },
]


def migration_plan(bind: Engine) -> dict[str, Any]:
    """Return migration runner status and planned revisions."""
    _ensure_runner_table(bind)
    applied = _applied_revisions(bind)
    active = [item for item in MIGRATION_REVISIONS if item["status"] == "active"]
    pending = [item for item in active if item["revision"] not in applied]
    latest = _latest_run(bind)
    return {
        "runner": {
            "table": RUNNER_TABLE,
            "backup_dir": str(BACKUP_DIR),
            "supports_backup": _supports_file_backup(),
            "applied_revisions": sorted(applied),
            "latest_run": latest,
        },
        "revisions": MIGRATION_REVISIONS,
        "pending": pending,
        "next_action": _next_action(pending, latest),
        "principle": "正式迁移必须先可计划、可 dry-run、可备份、可审计；破坏性变更必须单独显式实现。",
    }


def run_formal_migrations(
    bind: Engine,
    *,
    dry_run: bool = True,
    create_backup: bool = True,
) -> dict[str, Any]:
    """Run active non-destructive migration revisions with audit records."""
    plan = migration_plan(bind)
    pending = list(plan["pending"])
    before = audit_schema(bind)
    if dry_run:
        return {
            "status": "dry_run",
            "plan": plan,
            "would_run": [item["revision"] for item in pending],
            "backup": {"created": False, "reason": "dry_run"},
            "schema_before": _schema_snapshot(before),
            "principle": "dry-run 只报告将执行内容，不写入迁移记录或备份。",
        }

    backup = create_database_backup() if create_backup else {"created": False, "reason": "disabled"}
    applied: list[str] = []
    errors: list[dict[str, str]] = []
    for revision in pending:
        try:
            _execute_revision(bind, revision)
            _record_run(bind, revision["revision"], "applied", {"backup": backup, "title": revision["title"]})
            applied.append(str(revision["revision"]))
        except Exception as exc:  # pragma: no cover - defensive audit path
            error = {"revision": str(revision["revision"]), "error": str(exc)}
            errors.append(error)
            _record_run(bind, revision["revision"], "failed", {"backup": backup, "error": str(exc)})
            break
    after = audit_schema(bind)
    return {
        "status": "failed" if errors else "applied",
        "applied": applied,
        "errors": errors,
        "backup": backup,
        "schema_before": _schema_snapshot(before),
        "schema_after": _schema_snapshot(after),
        "plan": migration_plan(bind),
    }


def create_database_backup() -> dict[str, Any]:
    """Create a timestamped SQLite file backup for file-based deployments."""
    if not _supports_file_backup():
        return {"created": False, "reason": "non_file_sqlite_or_missing_db"}
    BACKUP_DIR.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    target = BACKUP_DIR / f"relationship_training-{timestamp}.db"
    shutil.copy2(DB_PATH, target)
    return {
        "created": True,
        "path": str(target),
        "bytes": target.stat().st_size,
        "created_at": datetime.now().isoformat(timespec="seconds"),
    }


def _execute_revision(bind: Engine, revision: dict[str, Any]) -> None:
    if revision["revision"] == "2026_05_21_formal_runner_v1":
        ensure_schema_compatibility(bind)
        return
    if revision["revision"] == "2026_05_21_metadata_vector_index_rebuild_v1":
        _execute_metadata_vector_index_revision(bind)
        return
    if revision["revision"] == "2026_05_22_import_issue_status_normalization_v1":
        _execute_import_issue_status_normalization_revision(bind)
        return
    raise ValueError(f"未实现的 active migration revision: {revision['revision']}")


def _execute_metadata_vector_index_revision(bind: Engine) -> None:
    ensure_schema_compatibility(bind)
    with Session(bind) as session:
        result = rebuild_metadata_vector_index(session, limit_per_type=1000)
        _record_revision_result(bind, "2026_05_21_metadata_vector_index_rebuild_v1", result)


def _execute_import_issue_status_normalization_revision(bind: Engine) -> None:
    ensure_schema_compatibility(bind)
    now = datetime.now().isoformat(sep=" ", timespec="seconds")
    with bind.begin() as connection:
        before = _import_issue_status_counts(connection)
        blank_status_rows = int(connection.execute(
            text("SELECT count(*) FROM content_import_issues WHERE status IS NULL OR trim(status) = ''")
        ).scalar() or 0)
        missing_updated_at_rows = int(connection.execute(
            text("SELECT count(*) FROM content_import_issues WHERE updated_at IS NULL OR trim(updated_at) = ''")
        ).scalar() or 0)
        connection.execute(
            text(
                "UPDATE content_import_issues "
                "SET status = 'open', updated_at = COALESCE(NULLIF(updated_at, ''), :now) "
                "WHERE status IS NULL OR trim(status) = ''"
            ),
            {"now": now},
        )
        connection.execute(
            text(
                "UPDATE content_import_issues "
                "SET updated_at = COALESCE(NULLIF(updated_at, ''), created_at, :now) "
                "WHERE updated_at IS NULL OR trim(updated_at) = ''"
            ),
            {"now": now},
        )
        after = _import_issue_status_counts(connection)
    _record_revision_result(
        bind,
        "2026_05_22_import_issue_status_normalization_v1",
        {
            "normalized_blank_status_rows": blank_status_rows,
            "backfilled_updated_at_rows": missing_updated_at_rows,
            "before_status_counts": before,
            "after_status_counts": after,
            "safety": {
                "destructive": False,
                "raw_source_text_saved": False,
                "resolution_text_returned": False,
            },
        },
    )


def _import_issue_status_counts(connection: Any) -> dict[str, int]:
    rows = connection.execute(
        text(
            "SELECT COALESCE(NULLIF(trim(status), ''), 'open') AS normalized_status, count(*) "
            "FROM content_import_issues GROUP BY normalized_status"
        )
    ).fetchall()
    return {str(row[0]): int(row[1]) for row in rows}


def _record_revision_result(bind: Engine, revision: str, result: dict[str, Any]) -> None:
    with bind.begin() as connection:
        connection.execute(
            text(
                "CREATE TABLE IF NOT EXISTS formal_migration_revision_results ("
                "id INTEGER PRIMARY KEY AUTOINCREMENT,"
                "revision TEXT NOT NULL,"
                "created_at DATETIME NOT NULL,"
                "result_json TEXT NOT NULL"
                ")"
            )
        )
        connection.execute(
            text(
                "INSERT INTO formal_migration_revision_results (revision, created_at, result_json) "
                "VALUES (:revision, :created_at, :result_json)"
            ),
            {
                "revision": revision,
                "created_at": datetime.now().isoformat(sep=" ", timespec="seconds"),
                "result_json": json.dumps(_revision_result_summary(result), ensure_ascii=False),
            },
        )


def _revision_result_summary(result: dict[str, Any]) -> dict[str, Any]:
    if "normalized_blank_status_rows" in result:
        return {
            "normalized_blank_status_rows": result.get("normalized_blank_status_rows", 0),
            "backfilled_updated_at_rows": result.get("backfilled_updated_at_rows", 0),
            "before_status_counts": result.get("before_status_counts", {}),
            "after_status_counts": result.get("after_status_counts", {}),
            "safety": result.get("safety", {}),
        }
    sqlite_vec = result.get("sqlite_vec")
    return {
        "rebuilt": result.get("rebuilt", {}),
        "skipped": result.get("skipped", {}),
        "total_vectors": result.get("total_vectors", 0),
        "backend": result.get("backend"),
        "sqlite_vec": sqlite_vec if isinstance(sqlite_vec, dict) else {},
    }


def _ensure_runner_table(bind: Engine) -> None:
    with bind.begin() as connection:
        connection.execute(text(
            f"""
            CREATE TABLE IF NOT EXISTS {RUNNER_TABLE} (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                revision TEXT NOT NULL,
                status TEXT NOT NULL,
                applied_at DATETIME NOT NULL,
                details_json TEXT
            )
            """
        ))


def _record_run(bind: Engine, revision: str, status: str, details: dict[str, Any]) -> None:
    with bind.begin() as connection:
        connection.execute(
            text(
                f"INSERT INTO {RUNNER_TABLE} (revision, status, applied_at, details_json) "
                "VALUES (:revision, :status, :applied_at, :details_json)"
            ),
            {
                "revision": revision,
                "status": status,
                "applied_at": datetime.now().isoformat(sep=" ", timespec="seconds"),
                "details_json": json.dumps(details, ensure_ascii=False),
            },
        )


def _applied_revisions(bind: Engine) -> set[str]:
    _ensure_runner_table(bind)
    with bind.connect() as connection:
        rows = connection.execute(
            text(f"SELECT revision FROM {RUNNER_TABLE} WHERE status = 'applied'")
        ).fetchall()
    return {str(row[0]) for row in rows}


def _latest_run(bind: Engine) -> dict[str, Any] | None:
    inspector = inspect(bind)
    if RUNNER_TABLE not in set(inspector.get_table_names()):
        return None
    with bind.connect() as connection:
        row = connection.execute(
            text(
                f"SELECT revision, status, applied_at, details_json FROM {RUNNER_TABLE} "
                "ORDER BY applied_at DESC, id DESC LIMIT 1"
            )
        ).fetchone()
    if row is None:
        return None
    return {
        "revision": row[0],
        "status": row[1],
        "applied_at": row[2],
        "details": _loads_dict(row[3]),
    }


def _schema_snapshot(audit: dict[str, Any]) -> dict[str, Any]:
    return {
        "status": audit.get("status"),
        "integrity_check": audit.get("integrity_check"),
        "missing_tables": audit.get("missing_tables", []),
        "missing_columns": audit.get("missing_columns", {}),
        "row_counts": audit.get("row_counts", {}),
    }


def _next_action(pending: list[dict[str, Any]], latest: dict[str, Any] | None) -> dict[str, str]:
    if pending:
        return {
            "priority": "high",
            "action": "执行正式迁移 dry-run 后应用",
            "reason": f"{len(pending)} 个 active revision 尚未记录为 applied。",
        }
    if latest and latest.get("status") == "failed":
        return {"priority": "high", "action": "检查失败迁移", "reason": "最近一次正式迁移失败。"}
    return {"priority": "low", "action": "保持迁移审计", "reason": "active revisions 已全部 applied。"}


def _supports_file_backup() -> bool:
    return bool(DB_PATH.exists() and DB_PATH.is_file())


def _loads_dict(raw: Any) -> dict[str, Any]:
    if not raw:
        return {}
    try:
        value = json.loads(str(raw))
    except json.JSONDecodeError:
        return {}
    return value if isinstance(value, dict) else {}
