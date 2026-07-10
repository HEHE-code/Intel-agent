"""FastAPI 应用入口。

启动：uvicorn app.main:app --reload --port 8000
"""
from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import agents, aggregate, domains, health, reports, schedules, templates
from app.config import get_settings
from app.crud import sync_domain_tool_configs
from app.db import SessionLocal, engine
from app.models import Base
from app.scheduler import shutdown_scheduler, start_scheduler


@asynccontextmanager
async def lifespan(_app: FastAPI):
    # 启动时建表（SQLite，开发期用 create_all 足够；正式可迁移 Alembic）
    Base.metadata.create_all(engine)
    # 初始化领域工具默认配置（幂等）
    with SessionLocal() as session:
        sync_domain_tool_configs(session)
        session.commit()
    # 启动定时调度器（从 DB 重建所有 enabled 任务）
    start_scheduler()
    yield
    # 关闭调度器
    shutdown_scheduler()


settings = get_settings()

app = FastAPI(
    title="情报智能体生成器 API",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 路由统一挂在 /api 下
app.include_router(health.router, prefix="/api")
app.include_router(agents.router, prefix="/api")
app.include_router(reports.router, prefix="/api")
app.include_router(schedules.router, prefix="/api")
app.include_router(templates.router, prefix="/api")
app.include_router(domains.router, prefix="/api")
app.include_router(aggregate.router, prefix="/api")


@app.get("/")
def root() -> dict:
    return {"name": "情报智能体生成器 API", "docs": "/docs", "health": "/api/health"}
