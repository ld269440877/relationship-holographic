"""
FastAPI 主应用入口
"""
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from loguru import logger

from backend.api import emotions, samples, resources, training, reviews, profile, strategies
from backend.database.connection import create_db_and_tables, settings
import sys
from pathlib import Path
# Ensure the project root is in the Python path
_project_root = Path(__file__).resolve().parent.parent
if str(_project_root) not in sys.path:
    sys.path.insert(0, str(_project_root))


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期"""
    # 启动时
    logger.info("正在初始化数据库...")
    create_db_and_tables()
    logger.info("数据库初始化完成")
    
    yield
    
    # 关闭时
    logger.info("应用关闭")


# 创建应用
app = FastAPI(
    title="关系动力学全息",
    description="世界最顶级的两性关系感知训练系统",
    version="1.0.0",
    lifespan=lifespan
)

# CORS 配置
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 注册路由
app.include_router(emotions.router)
app.include_router(samples.router)
app.include_router(resources.router)
app.include_router(training.router)
app.include_router(reviews.router)
app.include_router(profile.router)
app.include_router(strategies.router)


@app.get("/")
def root() -> dict:
    """根路径"""
    return {
        "name": "关系动力学全息",
        "version": "1.0.0",
        "description": "两性关系感知训练系统 API"
    }


@app.get("/health")
def health_check() -> dict:
    """健康检查"""
    return {"status": "healthy"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "backend.main:app",
        host=settings.api_host,
        port=settings.api_port,
        reload=True
    )