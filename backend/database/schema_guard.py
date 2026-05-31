"""SQLite schema guard and lightweight migration helpers.

This project intentionally avoids a heavyweight migration stack for now, but
`SQLModel.metadata.create_all()` cannot add new columns to existing SQLite
tables. These helpers close that gap for local-first development.
"""
from __future__ import annotations

import json
from datetime import date, datetime
from typing import Any

from sqlalchemy import Boolean, Date, DateTime, Engine, Float, Integer, inspect, text
from sqlalchemy.exc import OperationalError
from sqlalchemy.schema import Column
from sqlmodel import SQLModel

from backend.database.content_sources import audit_content_sources

SCHEMA_REVISION = "2026_05_21_schema_guard_v1"
MIGRATION_TABLE = "schema_migrations"
SCHEMA_REVISION_PLAN = [
    {
        "revision": SCHEMA_REVISION,
        "status": "active",
        "capabilities": ["create_missing_tables", "add_missing_columns", "json_quality_audit"],
    },
    {
        "revision": "2026_05_21_content_sources_v1",
        "status": "active",
        "capabilities": ["content_sources_preferred_root", "legacy_root_fallback", "import_batch_visibility"],
    },
    {
        "revision": "future_formal_migrations_v2",
        "status": "planned",
        "capabilities": ["column_rebuild", "index_rebuild", "data_backfill_jobs", "rollback_metadata"],
    },
]


def ensure_schema_compatibility(bind: Engine) -> dict[str, Any]:
    """Create migration metadata and add missing columns for existing tables."""
    _load_model_metadata()
    _ensure_migration_table(bind)
    added_columns: list[dict[str, str]] = []
    skipped_columns: list[dict[str, str]] = []

    inspector = inspect(bind)
    existing_tables = set(inspector.get_table_names())
    for table in SQLModel.metadata.sorted_tables:
        if table.name not in existing_tables:
            continue
        existing_columns = {column["name"] for column in inspector.get_columns(table.name)}
        for column in table.columns:
            if column.name in existing_columns:
                continue
            if column.primary_key:
                skipped_columns.append({"table": table.name, "column": column.name, "reason": "primary_key"})
                continue
            ddl = _add_column_sql(bind, table.name, column)
            with bind.begin() as connection:
                connection.execute(text(ddl))
                backfill = _backfill_value(column)
                if backfill is not None:
                    connection.execute(
                        text(
                            f"UPDATE {_quote(bind, table.name)} "
                            f"SET {_quote(bind, column.name)} = :value "
                            f"WHERE {_quote(bind, column.name)} IS NULL"
                        ),
                        {"value": backfill},
                    )
            added_columns.append({"table": table.name, "column": column.name, "type": column.type.compile(dialect=bind.dialect)})

    details = {"added_columns": added_columns, "skipped_columns": skipped_columns}
    _record_schema_revision(bind, details)
    audit = audit_schema(bind)
    audit["migration"] = details
    return audit


def audit_schema(bind: Engine) -> dict[str, Any]:
    """Return an audit-friendly snapshot of database/schema health."""
    _load_model_metadata()
    inspector = inspect(bind)
    existing_tables = set(inspector.get_table_names())
    expected_tables = [table.name for table in SQLModel.metadata.sorted_tables]
    missing_tables = [table for table in expected_tables if table not in existing_tables]
    missing_columns: dict[str, list[str]] = {}

    for table in SQLModel.metadata.sorted_tables:
        if table.name not in existing_tables:
            continue
        existing_columns = {column["name"] for column in inspector.get_columns(table.name)}
        expected_columns = {column.name for column in table.columns}
        missing = sorted(expected_columns - existing_columns)
        if missing:
            missing_columns[table.name] = missing

    managed_tables = set(expected_tables) | {MIGRATION_TABLE, "sqlite_sequence"}
    managed_tables.update(table for table in existing_tables if _is_sqlite_vec_table(table))
    extra_tables = sorted(table for table in existing_tables if table not in managed_tables)
    with bind.connect() as connection:
        foreign_keys = _pragma_scalar(connection, "foreign_keys")
        integrity_check = _pragma_scalar(connection, "quick_check")
        migration_count = _migration_count(connection) if MIGRATION_TABLE in existing_tables else 0
        latest_migration = _latest_migration(connection) if MIGRATION_TABLE in existing_tables else None
        row_counts = _row_counts(connection, existing_tables)
        json_quality = _json_quality(connection, existing_tables)
        content_import_status = _content_import_status(connection, existing_tables)
        formal_migration_status = _formal_migration_status(connection, existing_tables)
        vector_backend_status = _vector_backend_status(connection, existing_tables)

    has_json_issues = any(item["invalid"] > 0 for item in json_quality.values())
    status = "ok" if not missing_tables and not missing_columns and integrity_check == "ok" and not has_json_issues else "needs_attention"
    return {
        "status": status,
        "revision": SCHEMA_REVISION,
        "schema_evolution": {
            "current_revision": SCHEMA_REVISION,
            "latest_recorded": latest_migration,
            "plan": SCHEMA_REVISION_PLAN,
            "formal_migration_needed_for": ["drop_column", "rename_column", "change_column_type", "index_rebuild", "large_backfill"],
        },
        "foreign_keys": bool(foreign_keys),
        "integrity_check": integrity_check,
        "expected_tables": len(expected_tables),
        "existing_tables": len(existing_tables),
        "missing_tables": missing_tables,
        "missing_columns": missing_columns,
        "extra_tables": extra_tables,
        "migration_count": migration_count,
        "row_counts": row_counts,
        "json_quality": json_quality,
        "content_sources": audit_content_sources(),
        "content_import_status": content_import_status,
        "formal_migration_status": formal_migration_status,
        "vector_backend_status": vector_backend_status,
    }


def _ensure_migration_table(bind: Engine) -> None:
    with bind.begin() as connection:
        connection.execute(text(
            f"""
            CREATE TABLE IF NOT EXISTS {MIGRATION_TABLE} (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                revision TEXT NOT NULL UNIQUE,
                applied_at DATETIME NOT NULL,
                details_json TEXT
            )
            """
        ))


def _load_model_metadata() -> None:
    from backend.models import (  # noqa: F401
        emotion,
        evolution,
        expression,
        knowledge,
        resource,
        runtime,
        sample,
        training,
        user,
    )


def _record_schema_revision(bind: Engine, details: dict[str, Any]) -> None:
    with bind.begin() as connection:
        connection.execute(
            text(
                f"""
                INSERT OR REPLACE INTO {MIGRATION_TABLE}
                    (revision, applied_at, details_json)
                VALUES
                    (:revision, :applied_at, :details_json)
                """
            ),
            {
                "revision": SCHEMA_REVISION,
                "applied_at": datetime.now().isoformat(sep=" ", timespec="seconds"),
                "details_json": json.dumps(details, ensure_ascii=False),
            },
        )


def _add_column_sql(bind: Engine, table_name: str, column: Column[Any]) -> str:
    column_type = column.type.compile(dialect=bind.dialect)
    return f"ALTER TABLE {_quote(bind, table_name)} ADD COLUMN {_quote(bind, column.name)} {column_type}"


def _quote(bind: Engine, identifier: str) -> str:
    return bind.dialect.identifier_preparer.quote(identifier)


def _backfill_value(column: Column[Any]) -> Any | None:
    if column.nullable:
        return None
    if isinstance(column.type, Boolean):
        return 0
    if isinstance(column.type, Integer):
        return 0
    if isinstance(column.type, Float):
        return 0.0
    if isinstance(column.type, DateTime):
        return datetime.now().isoformat(sep=" ", timespec="seconds")
    if isinstance(column.type, Date):
        return date.today().isoformat()
    if column.name.endswith("_json"):
        return "{}"
    return ""


def _pragma_scalar(connection: Any, name: str) -> Any:
    return connection.execute(text(f"PRAGMA {name}")).scalar()


def _migration_count(connection: Any) -> int:
    return int(connection.execute(text(f"SELECT count(*) FROM {MIGRATION_TABLE}")).scalar() or 0)


def _latest_migration(connection: Any) -> dict[str, Any] | None:
    row = connection.execute(
        text(
            f"SELECT revision, applied_at, details_json FROM {MIGRATION_TABLE} "
            "ORDER BY applied_at DESC, id DESC LIMIT 1"
        )
    ).fetchone()
    if row is None:
        return None
    return {
        "revision": row[0],
        "applied_at": row[1],
        "details": _loads_dict(row[2]),
    }


def _row_counts(connection: Any, existing_tables: set[str]) -> dict[str, int]:
    important_tables = [
        "emotion_spectrum",
        "mixed_emotions",
        "expression_tools",
        "expression_tool_chains",
        "interaction_samples",
        "sample_annotation_versions",
        "resource_library",
        "knowledge_entries",
        "mistake_log",
        "training_attempts",
        "practice_sessions",
        "practice_events",
        "safety_events",
        "ai_prompt_versions",
        "ai_run_logs",
        "ai_provider_probe_logs",
        "runtime_events",
        "source_registry",
        "raw_content_items",
        "annotation_jobs",
        "training_asset_versions",
        "content_import_issues",
        "metadata_vector_index",
    ]
    counts: dict[str, int] = {}
    for table in important_tables:
        if table not in existing_tables:
            continue
        counts[table] = int(connection.execute(text(f"SELECT count(*) FROM {_safe_table_name(table)}")).scalar() or 0)
    return counts


def _json_quality(connection: Any, existing_tables: set[str]) -> dict[str, dict[str, Any]]:
    json_columns = {
        "interaction_samples": [
            "emotion_tags_json",
            "five_w_two_h_json",
            "signal_highlights_json",
            "emotion_flow_json",
            "feeling_tags_json",
            "need_radar_json",
            "boundary_state_json",
            "source_trace_json",
            "quality_json",
            "tension_dimensions_json",
            "gold_label_json",
        ],
        "sample_annotation_versions": [
            "tension_dimensions_json",
            "source_trace_json",
            "quality_json",
            "safety_json",
            "gold_label_json",
        ],
        "resource_library": [
            "emotional_tone_json",
            "expression_tool_ids_json",
            "recommended_drills_json",
            "case_blueprint_json",
        ],
        "response_strategies": ["example_json"],
        "user_profile": ["progress_json"],
        "knowledge_entries": ["tags_json", "source_metadata_json"],
        "content_import_batches": ["report_json"],
        "evolution_items": ["tags_json"],
        "source_registry": ["allowed_use_json", "disallowed_use_json"],
        "annotation_jobs": ["result_json"],
        "training_asset_versions": ["source_trace_json", "quality_json"],
        "training_attempts": ["feedback_json"],
        "practice_sessions": ["topics_json", "current_state_json", "safety_summary_json"],
        "practice_events": ["suggestions_json", "relationship_state_json", "safety_json", "safe_alternatives_json"],
        "safety_events": ["flags_json", "alternatives_json"],
        "ai_prompt_versions": ["response_contract_json"],
        "ai_run_logs": ["safety_flags_json", "payload_summary_json", "response_summary_json"],
        "ai_provider_probe_logs": ["request_shape_json"],
        "mistake_log": ["error_attribution_json", "mastery_snapshot_json"],
        "metadata_vector_index": ["vector_json", "metadata_json"],
        "runtime_events": ["context_json"],
    }
    quality: dict[str, dict[str, Any]] = {}
    existing_columns_by_table = _existing_columns_by_table(connection, existing_tables)
    for table, columns in json_columns.items():
        if table not in existing_tables:
            continue
        for column in columns:
            key = f"{table}.{column}"
            if column not in existing_columns_by_table.get(table, set()):
                quality[key] = {
                    "checked": 0,
                    "invalid": 0,
                    "examples": [],
                    "skipped": "missing_column",
                }
                continue
            rows = connection.execute(
                text(
                    f"SELECT id, {_safe_table_name(column)} "
                    f"FROM {_safe_table_name(table)} "
                    f"WHERE {_safe_table_name(column)} IS NOT NULL "
                    f"AND TRIM({_safe_table_name(column)}) != '' "
                    "LIMIT :limit"
                ),
                {"limit": 5000},
            ).fetchall()
            invalid_count = 0
            invalid_examples: list[dict[str, Any]] = []
            for row in rows:
                try:
                    json.loads(str(row[1]))
                except json.JSONDecodeError:
                    invalid_count += 1
                    if len(invalid_examples) < 3:
                        invalid_examples.append({"id": row[0], "value_preview": str(row[1])[:120]})
            quality[key] = {
                "checked": len(rows),
                "invalid": invalid_count,
                "examples": invalid_examples,
            }
    return quality


def _existing_columns_by_table(connection: Any, existing_tables: set[str]) -> dict[str, set[str]]:
    columns: dict[str, set[str]] = {}
    for table in existing_tables:
        if _is_sqlite_vec_table(table):
            columns[table] = set()
            continue
        try:
            rows = connection.execute(text(f"PRAGMA table_info({_safe_table_name(table)})")).fetchall()
        except OperationalError:
            columns[table] = set()
            continue
        columns[table] = {str(row[1]) for row in rows}
    return columns


def _content_import_status(connection: Any, existing_tables: set[str]) -> dict[str, Any]:
    if "content_import_batches" not in existing_tables:
        return {
            "available": False,
            "batches": 0,
            "issues": 0,
            "latest_batches": [],
        }
    batch_rows = connection.execute(
        text(
            "SELECT source_name, source_type, imported_sections, imported_entries, skipped_entries, issues_count, created_at "
            "FROM content_import_batches ORDER BY created_at DESC LIMIT 8"
        )
    ).fetchall()
    issue_count = 0
    if "content_import_issues" in existing_tables:
        issue_count = int(connection.execute(text("SELECT count(*) FROM content_import_issues")).scalar() or 0)
    return {
        "available": True,
        "batches": int(connection.execute(text("SELECT count(*) FROM content_import_batches")).scalar() or 0),
        "issues": issue_count,
        "latest_batches": [
            {
                "source_name": row[0],
                "source_type": row[1],
                "imported_sections": row[2],
                "imported_entries": row[3],
                "skipped_entries": row[4],
                "issues_count": row[5],
                "created_at": row[6],
            }
            for row in batch_rows
        ],
    }


def _formal_migration_status(connection: Any, existing_tables: set[str]) -> dict[str, Any]:
    table = "formal_migration_runs"
    if table not in existing_tables:
        return {"available": False, "runs": 0, "latest_run": None}
    latest = connection.execute(
        text(
            f"SELECT revision, status, applied_at, details_json FROM {_safe_table_name(table)} "
            "ORDER BY applied_at DESC, id DESC LIMIT 1"
        )
    ).fetchone()
    return {
        "available": True,
        "runs": int(connection.execute(text(f"SELECT count(*) FROM {_safe_table_name(table)}")).scalar() or 0),
        "latest_run": {
            "revision": latest[0],
            "status": latest[1],
            "applied_at": latest[2],
            "details": _loads_dict(latest[3]),
        } if latest else None,
    }


def _vector_backend_status(connection: Any, existing_tables: set[str]) -> dict[str, Any]:
    table = "metadata_vector_index_vec"
    has_audit_table = "metadata_vector_index" in existing_tables
    has_vec_table = table in existing_tables
    audit_rows = 0
    if has_audit_table:
        audit_rows = int(connection.execute(text("SELECT count(*) FROM metadata_vector_index")).scalar() or 0)
    return {
        "audit_table": "metadata_vector_index",
        "audit_rows": audit_rows,
        "sqlite_vec_table": table,
        "sqlite_vec_table_present": has_vec_table,
        "active_backend": "sqlite_vec" if has_vec_table else "local_metadata_signature",
        "note": "sqlite-vec 虚拟表按连接加载扩展后可用；审计主真源始终是 metadata_vector_index。",
    }


def _loads_dict(text_value: Any) -> dict[str, Any]:
    if not text_value:
        return {}
    try:
        data = json.loads(str(text_value))
    except json.JSONDecodeError:
        return {}
    return data if isinstance(data, dict) else {}


def _safe_table_name(table: str) -> str:
    return '"' + table.replace('"', '""') + '"'


def _is_sqlite_vec_table(table: str) -> bool:
    return table == "metadata_vector_index_vec" or table.startswith("metadata_vector_index_vec_")
