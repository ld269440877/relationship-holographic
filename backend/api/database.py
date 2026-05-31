"""数据库健康检查 API。"""
from typing import Any

from fastapi import APIRouter

from backend.database.connection import create_db_and_tables, engine
from backend.database.migration_runner import migration_plan, run_formal_migrations
from backend.database.schema_guard import audit_schema

router = APIRouter(prefix="/api/database", tags=["数据库"])


@router.get("/health")
def database_health() -> dict[str, Any]:
    """返回 SQLite schema、完整性和关键表行数。"""
    return audit_schema(engine)


@router.post("/migrate")
def database_migrate() -> dict[str, Any]:
    """执行幂等轻量迁移：建缺表、补缺列、记录 revision。"""
    return create_db_and_tables()


@router.get("/migration-plan")
def database_migration_plan() -> dict[str, Any]:
    """返回正式迁移运行器计划、待执行 revision 和最近运行记录。"""
    return migration_plan(engine)


@router.post("/migration-run")
def database_migration_run(dry_run: bool = True, create_backup: bool = True) -> dict[str, Any]:
    """执行正式迁移运行器；默认 dry-run，真实执行前会创建 SQLite 备份。"""
    return run_formal_migrations(engine, dry_run=dry_run, create_backup=create_backup)
