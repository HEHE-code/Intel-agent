"""报告路由：列表、详情、下载。"""
from __future__ import annotations

from fastapi import APIRouter, HTTPException
from fastapi.responses import PlainTextResponse

from app.crud import get_run, list_runs
from app.db import get_session

router = APIRouter(prefix="/reports", tags=["reports"])


class ReportOut:
    pass


@router.get("")
def list_() -> list[dict]:
    """历史报告列表（不含正文，只含摘要）。"""
    with get_session() as s:
        return [
            {
                "id": r.id,
                "agent_id": r.agent_id,
                "status": r.status,
                "created_at": r.created_at.isoformat() if r.created_at else "",
                "report_length": len(r.report_md or ""),
                "preview": (r.report_md or "")[:80],
                "steps_count": len(r.steps or []),
            }
            for r in list_runs(s)
        ]


@router.get("/{run_id}")
def detail(run_id: str) -> dict:
    """报告详情（含完整 Markdown 与步骤日志）。"""
    with get_session() as s:
        r = get_run(s, run_id)
        if not r:
            raise HTTPException(404, "报告不存在")
        return {
            "id": r.id,
            "agent_id": r.agent_id,
            "status": r.status,
            "created_at": r.created_at.isoformat() if r.created_at else "",
            "report_md": r.report_md,
            "steps": r.steps,
        }


@router.get("/{run_id}/download", response_class=PlainTextResponse)
def download(run_id: str) -> str:
    """下载报告 .md 原文。"""
    with get_session() as s:
        r = get_run(s, run_id)
        if not r:
            raise HTTPException(404, "报告不存在")
        return r.report_md or "(无报告内容)"
