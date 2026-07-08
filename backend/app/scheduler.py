"""定时调度器：APScheduler 单例封装。

随应用 lifespan 启动/关闭；启动时从 DB 重建所有 enabled 任务。
job 执行时调 run_agent 静默跑（无 SSE），报告自动入库。

线程安全：APScheduler 的 job 在独立线程跑，每次执行新建 SQLAlchemy session。
"""
from __future__ import annotations

import logging
from datetime import datetime

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger

from app.db import SessionLocal
from app.crud import get_agent, update_run, create_run
from app.engine import run_agent

log = logging.getLogger(__name__)

_scheduler: BackgroundScheduler | None = None


def get_scheduler() -> BackgroundScheduler:
    """获取全局调度器单例（懒启动）。"""
    global _scheduler
    if _scheduler is None:
        _scheduler = BackgroundScheduler(timezone="Asia/Shanghai")
    return _scheduler


def start_scheduler() -> None:
    """启动调度器并从 DB 重建任务。lifespan 调用。"""
    sched = get_scheduler()
    if not sched.running:
        sched.start()
        log.info("调度器已启动")
        rebuild_jobs()


def shutdown_scheduler() -> None:
    """优雅关闭。lifespan 调用。"""
    global _scheduler
    if _scheduler and _scheduler.running:
        _scheduler.shutdown(wait=False)
        log.info("调度器已关闭")


def _job_id(agent_id: str) -> str:
    return f"agent_run_{agent_id}"


def _run_agent_job(agent_id: str) -> None:
    """job 执行函数：静默跑 run_agent，更新 last_run_at。

    在独立线程执行，必须自建 session；失败记日志不抛（否则调度器吞异常）。
    once 类型触发后自动 enabled=False（一次性）。
    """
    log.info("定时任务触发: agent=%s", agent_id)
    try:
        result = run_agent(agent_id, cb=None)
        log.info("定时任务完成: agent=%s status=%s docs=%s",
                 agent_id, result["status"], result.get("docs_count", 0))
    except Exception as e:
        log.exception("定时任务失败: agent=%s err=%s", agent_id, e)
    finally:
        try:
            from app.models import Schedule
            with SessionLocal() as s:
                sch = s.query(Schedule).filter(Schedule.agent_id == agent_id).first()
                if sch:
                    sch.last_run_at = datetime.now()
                    # once 类型跑完即失效
                    if sch.run_type == "once":
                        sch.enabled = False
                        remove_job(agent_id)
                        log.info("单次任务已自动失效: agent=%s", agent_id)
                    s.commit()
        except Exception as e:
            log.warning("更新 last_run_at 失败: %s", e)


def add_job(agent_id: str, schedule) -> None:
    """根据 schedule 配置添加任务（支持 once/daily/weekly）。"""
    sched = get_scheduler()
    if schedule.run_type == "once" and schedule.once_at:
        from apscheduler.triggers.date import DateTrigger
        trigger = DateTrigger(run_date=schedule.once_at, timezone="Asia/Shanghai")
    elif schedule.run_type in ("daily", "weekly") and schedule.cron_expr:
        trigger = CronTrigger.from_crontab(schedule.cron_expr, timezone="Asia/Shanghai")
    else:
        log.warning("无法添加任务 agent=%s: 配置不完整", agent_id)
        return
    sched.add_job(
        _run_agent_job,
        trigger=trigger,
        args=[agent_id],
        id=_job_id(agent_id),
        replace_existing=True,
        misfire_grace_time=300,
    )
    log.info("已添加任务: agent=%s type=%s", agent_id, schedule.run_type)


def remove_job(agent_id: str) -> None:
    """移除某智能体的定时任务（存在时）。"""
    sched = get_scheduler()
    try:
        sched.remove_job(_job_id(agent_id))
        log.info("已移除定时任务: agent=%s", agent_id)
    except Exception:
        pass  # job 不存在，忽略


def rebuild_jobs() -> int:
    """从 DB 重建所有 enabled 任务。返回重建数量。"""
    from app.models import Schedule
    count = 0
    with SessionLocal() as s:
        for sch in s.query(Schedule).filter(Schedule.enabled.is_(True)).all():
            try:
                add_job(sch.agent_id, sch)
                count += 1
            except Exception as e:
                log.warning("重建任务失败 agent=%s: %s", sch.agent_id, e)
    if count:
        log.info("从 DB 重建 %d 个定时任务", count)
    return count
