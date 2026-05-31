"""
数据库连接管理
"""
from collections.abc import Generator
from pathlib import Path
from typing import Any

from loguru import logger
from pydantic_settings import BaseSettings
from sqlalchemy import event
from sqlmodel import Session, SQLModel, create_engine, text
from sqlmodel.pool import StaticPool

# 项目根目录
PROJECT_ROOT = Path(__file__).parent.parent.parent
DATA_DIR = PROJECT_ROOT / "data"
DATA_DIR.mkdir(exist_ok=True)

# 数据库路径
DB_PATH = DATA_DIR / "relationship_training.db"


class Settings(BaseSettings):
    """应用配置"""

    database_url: str = f"sqlite:///{DB_PATH}"
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    cors_origins: list[str] = ["http://localhost:3000", "http://localhost:5173"]
    log_level: str = "INFO"
    ai_provider: str = "deepseek"
    deepseek_api_key: str = ""
    deepseek_model: str = "deepseek-v4-pro"
    deepseek_base_url: str = "https://api.deepseek.com"
    deepseek_api_mode: str = "openai"
    deepseek_chat_path: str = "/chat/completions"
    deepseek_timeout: float = 60.0
    deepseek_live_probe_enabled: bool = False
    deepseek_reasoning_effort: str = "high"
    deepseek_thinking_enabled: bool = True

    class Config:
        env_file = ".env"
        extra = "allow"


settings = Settings()

# 创建引擎
connect_args: dict[str, Any] = {}
if "sqlite" in settings.database_url:
    connect_args["check_same_thread"] = False

engine = create_engine(
    settings.database_url,
    echo=False,
    connect_args=connect_args,
    poolclass=StaticPool,
)


@event.listens_for(engine, "connect")
def _set_sqlite_pragma(dbapi_connection: Any, _connection_record: Any) -> None:
    if "sqlite" not in settings.database_url:
        return
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.execute("PRAGMA journal_mode=WAL")
    cursor.close()


def create_db_and_tables() -> dict[str, Any]:
    """创建数据库和所有表"""
    # 确保所有 SQLModel table 类被导入，避免 create_all 漏表。
    from backend.database.schema_guard import ensure_schema_compatibility
    from backend.models import emotion, evolution, expression, knowledge, resource, sample, training, user  # noqa: F401

    logger.info("正在创建数据库表...")
    SQLModel.metadata.create_all(engine)
    audit = ensure_schema_compatibility(engine)
    logger.info("数据库表创建完成")
    if audit["status"] != "ok":
        logger.warning(f"数据库 schema 审计需要关注: {audit}")
    return audit


def get_session() -> Generator[Session, None, None]:
    """获取数据库会话"""
    with Session(engine) as session:
        yield session


def init_database() -> None:
    """初始化数据库"""
    create_db_and_tables()
    logger.info(f"数据库初始化完成: {DB_PATH}")


def execute_raw_sql(sql: str) -> None:
    """执行原生SQL（用于初始化数据）"""
    with engine.begin() as connection:
        connection.execute(text(sql))
