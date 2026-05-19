"""
数据库连接管理
"""
from pathlib import Path
from typing import Any

from loguru import logger
from pydantic_settings import BaseSettings
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


def create_db_and_tables() -> None:
    """创建数据库和所有表"""
    logger.info("正在创建数据库表...")
    SQLModel.metadata.create_all(engine)
    logger.info("数据库表创建完成")


def get_session() -> Session:
    """获取数据库会话"""
    with Session(engine) as session:
        yield session


def init_database() -> None:
    """初始化数据库"""
    create_db_and_tables()
    logger.info(f"数据库初始化完成: {DB_PATH}")


def execute_raw_sql(sql: str) -> None:
    """执行原生SQL（用于初始化数据）"""
    with Session(engine) as session:
        session.exec(text(sql))
        session.commit()