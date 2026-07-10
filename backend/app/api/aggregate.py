"""多智能体协同（综合研判）路由。"""
from __future__ import annotations

import threading

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from app.crud import create_aggregate, get_aggregate, list_agents, list_aggregates
from app.db import SessionLocal, get_session

router = APIRouter(prefix="/aggregate", tags=["aggregate"])


class AggregateReq(BaseModel):
    name: str = Field(..., min_length=1)
    agent_ids: list[str] = Field(..., min_items=2)
    theme: str = ""


@router.post("")
def create(req: AggregateReq) -> dict:
    """创建综合研判任务并后台执行。"""
    # 校验 agent_ids 有效
    with get_session() as s:
        existing = {a.id for a in list_agents(s)}
        for aid in req.agent_ids:
            if aid not in existing:
                raise HTTPException(400, f"智能体不存在: {aid}")
        agg = create_aggregate(s, name=req.name, agent_ids=req.agent_ids, theme=req.theme)
        agg_id = agg.id

    # 后台执行（不阻塞，综合研判调 LLM 较慢）
    def worker():
        from app.aggregate import run_aggregate
        try:
            run_aggregate(agg_id)
        except Exception as e:
            with SessionLocal() as s:
                from app.crud import update_aggregate
                update_aggregate(s, agg_id, status="failed", report_md=f"（失败：{e}）")
                s.commit()

    threading.Thread(target=worker, daemon=True).start()
    return {"id": agg_id, "status": "running"}


@router.get("")
def list_() -> list[dict]:
    """综合研判任务列表。"""
    with get_session() as s:
        return [
            {
                "id": a.id, "name": a.name, "agent_ids": a.agent_ids,
                "theme": a.theme, "status": a.status,
                "created_at": a.created_at.isoformat() if a.created_at else "",
                "report_length": len(a.report_md or ""),
            }
            for a in list_aggregates(s)
        ]


@router.get("/{agg_id}")
def detail(agg_id: str) -> dict:
    """综合研判详情（含报告）。"""
    with get_session() as s:
        a = get_aggregate(s, agg_id)
        if not a:
            raise HTTPException(404, "任务不存在")
        return {
            "id": a.id, "name": a.name, "agent_ids": a.agent_ids,
            "theme": a.theme, "status": a.status,
            "created_at": a.created_at.isoformat() if a.created_at else "",
            "report_md": a.report_md,
        }
