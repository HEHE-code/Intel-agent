"""定时运行路由。支持 once/daily/weekly 三种类型。"""
from __future__ import annotations

from datetime import datetime

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.crud import get_agent, get_schedule, upsert_schedule, delete_schedule
from app.db import get_session
from app.scheduler import add_job, remove_job

router = APIRouter(tags=["schedules"])

# 周几 → cron 数字（cron 周字段 0=周日..6=周六）
WEEKDAY_TO_CRON = {"sun": 0, "mon": 1, "tue": 2, "wed": 3, "thu": 4, "fri": 5, "sat": 6}


class ScheduleReq(BaseModel):
    run_type: str  # once/daily/weekly
    hour: int  # 0-23
    minute: int  # 0-59
    once_date: str | None = None  # once 时用，YYYY-MM-DD
    weekday: str | None = None  # weekly 时用，mon/tue/.../sun


class ScheduleOut(BaseModel):
    agent_id: str
    run_type: str
    hour: int
    minute: int
    weekday: str | None = None
    once_date: str | None = None
    enabled: bool
    last_run_at: str = ""
    created_at: str = ""

    @classmethod
    def from_orm(cls, s) -> "ScheduleOut":
        # 从 cron_expr 反解 hour/minute/weekday
        hour, minute, weekday = 0, 0, None
        if s.cron_expr:
            parts = s.cron_expr.split()
            if len(parts) == 5:
                minute = int(parts[0])
                hour = int(parts[1])
                w = parts[4]
                if w != "*":
                    cron_to_weekday = {v: k for k, v in WEEKDAY_TO_CRON.items()}
                    weekday = cron_to_weekday.get(int(w))
        once_date = s.once_at.strftime("%Y-%m-%d") if s.once_at else None
        if s.run_type == "once" and s.once_at:
            hour = s.once_at.hour
            minute = s.once_at.minute
        return cls(
            agent_id=s.agent_id,
            run_type=s.run_type,
            hour=hour,
            minute=minute,
            weekday=weekday,
            once_date=once_date,
            enabled=s.enabled,
            last_run_at=s.last_run_at.isoformat() if s.last_run_at else "",
            created_at=s.created_at.isoformat() if s.created_at else "",
        )


def _build_schedule_params(req: ScheduleReq):
    """把前端请求转成 (run_type, cron_expr, once_at)。"""
    if req.run_type not in ("once", "daily", "weekly"):
        raise HTTPException(400, "run_type 需为 once/daily/weekly")
    if not (0 <= req.hour <= 23) or not (0 <= req.minute <= 59):
        raise HTTPException(400, "时间非法")

    if req.run_type == "once":
        if not req.once_date:
            raise HTTPException(400, "单次运行需提供 once_date")
        try:
            dt = datetime.strptime(f"{req.once_date} {req.hour:02d}:{req.minute:02d}", "%Y-%m-%d %H:%M")
        except ValueError:
            raise HTTPException(400, "日期格式非法")
        if dt < datetime.now():
            raise HTTPException(400, "单次运行时间已过")
        return "once", "", dt
    elif req.run_type == "daily":
        return "daily", f"{req.minute} {req.hour} * * *", None
    else:  # weekly
        if req.weekday not in WEEKDAY_TO_CRON:
            raise HTTPException(400, "weekday 非法")
        return "weekly", f"{req.minute} {req.hour} * * {WEEKDAY_TO_CRON[req.weekday]}", None


@router.post("/agents/{agent_id}/schedule", response_model=ScheduleOut)
def create_schedule(agent_id: str, req: ScheduleReq) -> ScheduleOut:
    with get_session() as s:
        if not get_agent(s, agent_id):
            raise HTTPException(404, "智能体不存在")
        run_type, cron_expr, once_at = _build_schedule_params(req)
        sch = upsert_schedule(
            s, agent_id, run_type=run_type, cron_expr=cron_expr, once_at=once_at, enabled=True
        )
        out = ScheduleOut.from_orm(sch)
        # 在 session 内拷贝调度所需字段，避免 detached
        sched_snapshot = type("S", (), {
            "run_type": sch.run_type,
            "cron_expr": sch.cron_expr,
            "once_at": sch.once_at,
        })()
    add_job(agent_id, sched_snapshot)
    return out


@router.get("/agents/{agent_id}/schedule", response_model=ScheduleOut | None)
def get_agent_schedule(agent_id: str):
    with get_session() as s:
        sch = get_schedule(s, agent_id)
        return ScheduleOut.from_orm(sch) if sch else None


class ScheduleUpdate(BaseModel):
    enabled: bool | None = None


@router.put("/agents/{agent_id}/schedule", response_model=ScheduleOut)
def update_schedule(agent_id: str, req: ScheduleUpdate) -> ScheduleOut:
    with get_session() as s:
        sch = get_schedule(s, agent_id)
        if sch is None:
            raise HTTPException(404, "无定时配置，请先 POST 创建")
        if req.enabled is not None:
            sch.enabled = req.enabled
        out = ScheduleOut.from_orm(sch)
        sched_snapshot = type("S", (), {
            "run_type": sch.run_type,
            "cron_expr": sch.cron_expr,
            "once_at": sch.once_at,
        })()
    if out.enabled:
        add_job(agent_id, sched_snapshot)
    else:
        remove_job(agent_id)
    return out


@router.delete("/agents/{agent_id}/schedule")
def delete(agent_id: str) -> dict:
    with get_session() as s:
        if not delete_schedule(s, agent_id):
            raise HTTPException(404, "无定时配置")
    remove_job(agent_id)
    return {"ok": True}
