"""数据访问层：智能体配置与领域工具配置的 CRUD。

搜集节点、生成端点、编辑页都通过这里读写数据库。
"""
from __future__ import annotations

import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import AgentConfig, DomainToolConfig, RunRecord
from app.tools.registry import DOMAIN_PROMPTS, DOMAIN_TOOLS, ensure_registered


# ---------- AgentConfig ----------

def create_agent(
    session: Session,
    *,
    name: str,
    domain: str,
    intent: str,
    tools: list[str] | None = None,
    prompt_template: str | None = None,
    agent_id: str | None = None,
) -> AgentConfig:
    """新建智能体配置。tools/prompt 未指定时用领域默认。"""
    ensure_registered()
    agent = AgentConfig(
        id=agent_id or f"agt_{uuid.uuid4().hex[:12]}",
        name=name,
        domain=domain,
        intent=intent,
        tools=tools or DOMAIN_TOOLS.get(domain, ["web_search"]),
        prompt_template=prompt_template or DOMAIN_PROMPTS.get(domain, ""),
    )
    session.add(agent)
    session.flush()
    return agent


def get_agent(session: Session, agent_id: str) -> AgentConfig | None:
    return session.get(AgentConfig, agent_id)


def list_agents(session: Session) -> list[AgentConfig]:
    return list(session.scalars(select(AgentConfig).order_by(AgentConfig.created_at.desc())))


def update_agent(
    session: Session, agent_id: str, *, name: str | None = None,
    tools: list[str] | None = None, prompt_template: str | None = None,
) -> AgentConfig | None:
    agent = session.get(AgentConfig, agent_id)
    if not agent:
        return None
    if name is not None:
        agent.name = name
    if tools is not None:
        agent.tools = tools
    if prompt_template is not None:
        agent.prompt_template = prompt_template
    session.flush()
    return agent


def delete_agent(session: Session, agent_id: str) -> bool:
    """删除智能体（级联删 runs + 删 schedule）。返回是否删除成功。"""
    agent = session.get(AgentConfig, agent_id)
    if not agent:
        return False
    # 删关联 schedule（runs 通过 cascade=all,delete-orphan 自动删）
    sch = get_schedule(session, agent_id)
    if sch:
        session.delete(sch)
    session.delete(agent)
    session.flush()
    return True


# ---------- RunRecord ----------

def create_run(session: Session, agent_id: str, run_id: str | None = None) -> RunRecord:
    run = RunRecord(id=run_id or f"run_{uuid.uuid4().hex[:12]}", agent_id=agent_id)
    session.add(run)
    session.flush()
    return run


def get_run(session: Session, run_id: str) -> RunRecord | None:
    return session.get(RunRecord, run_id)


def list_runs_for_agent(session: Session, agent_id: str) -> list[RunRecord]:
    return list(
        session.scalars(
            select(RunRecord).where(RunRecord.agent_id == agent_id).order_by(RunRecord.created_at.desc())
        )
    )


def list_runs(session: Session) -> list[RunRecord]:
    return list(
        session.scalars(select(RunRecord).order_by(RunRecord.created_at.desc()))
    )


def update_run(
    session: Session, run_id: str, *,
    status: str | None = None, steps: list | None = None, report_md: str | None = None,
) -> RunRecord | None:
    run = session.get(RunRecord, run_id)
    if not run:
        return None
    if status is not None:
        run.status = status
    if steps is not None:
        run.steps = steps
    if report_md is not None:
        run.report_md = report_md
    session.flush()
    return run


def mark_run(session: Session, run_id: str, *, starred: bool | None = None, note: str | None = None) -> RunRecord | None:
    """标星 / 写批注。"""
    run = session.get(RunRecord, run_id)
    if not run:
        return None
    if starred is not None:
        run.starred = starred
    if note is not None:
        run.note = note
    session.flush()
    return run


# ---------- AgentMemory（智能体记忆） ----------

def add_memory(session: Session, agent_id: str, run_id: str, key_points: list[str]) -> None:
    """存本次运行的关键结论到记忆。"""
    from app.models import AgentMemory
    session.add(AgentMemory(agent_id=agent_id, run_id=run_id, key_points=key_points))
    session.flush()


def recent_memories(session: Session, agent_id: str, limit: int = 3) -> list:
    """取最近 N 条记忆（每条含 key_points + 时间）。"""
    from app.models import AgentMemory
    return list(
        session.scalars(
            select(AgentMemory)
            .where(AgentMemory.agent_id == agent_id)
            .order_by(AgentMemory.created_at.desc())
            .limit(limit)
        )
    )


# ---------- AggregateTask（多智能体协同） ----------

def create_aggregate(session: Session, *, name: str, agent_ids: list[str], theme: str = "") -> "AggregateTask":
    from app.models import AggregateTask
    agg = AggregateTask(
        id=f"agg_{uuid.uuid4().hex[:12]}",
        name=name, agent_ids=agent_ids, theme=theme,
    )
    session.add(agg)
    session.flush()
    return agg


def get_aggregate(session: Session, agg_id: str):
    from app.models import AggregateTask
    return session.get(AggregateTask, agg_id)


def list_aggregates(session: Session) -> list:
    from app.models import AggregateTask
    return list(session.scalars(
        select(AggregateTask).order_by(AggregateTask.created_at.desc())
    ))


def update_aggregate(session: Session, agg_id: str, *, status: str | None = None, report_md: str | None = None):
    agg = get_aggregate(session, agg_id)
    if not agg:
        return None
    if status is not None:
        agg.status = status
    if report_md is not None:
        agg.report_md = report_md
    session.flush()
    return agg


def latest_report_md_for_agent(session: Session, agent_id: str) -> tuple[str, str]:
    """取某智能体最新 completed 报告的 (md, agent_name)。无则 ("", name)。"""
    runs = list_runs_for_agent(session, agent_id)
    for r in runs:
        if r.status == "completed" and r.report_md:
            a = get_agent(session, agent_id)
            return r.report_md, a.name if a else "?"
    a = get_agent(session, agent_id)
    return "", a.name if a else "?"


# ---------- DomainToolConfig（运行时开关） ----------

def sync_domain_tool_configs(session: Session) -> int:
    """把注册表里的领域默认工具写入 DomainToolConfig（已存在则跳过）。

    供启动时初始化或设置页调用。返回新增条数。
    """
    ensure_registered()
    existing = {
        (r.domain, r.tool_name) for r in session.scalars(select(DomainToolConfig))
    }
    added = 0
    for domain, tool_names in DOMAIN_TOOLS.items():
        for tn in tool_names:
            if (domain, tn) in existing:
                continue
            session.add(DomainToolConfig(domain=domain, tool_name=tn, enabled=True))
            added += 1
    session.flush()
    return added


def get_domain_tools(session: Session, domain: str) -> list[DomainToolConfig]:
    return list(
        session.scalars(
            select(DomainToolConfig).where(DomainToolConfig.domain == domain)
        )
    )


def set_tool_enabled(session: Session, domain: str, tool_name: str, enabled: bool) -> bool:
    """开关某领域某工具。返回是否找到并更新。"""
    row = session.scalars(
        select(DomainToolConfig).where(
            DomainToolConfig.domain == domain, DomainToolConfig.tool_name == tool_name
        )
    ).first()
    if not row:
        return False
    row.enabled = enabled
    session.flush()
    return True


def enabled_tool_names(session: Session, domain: str) -> list[str]:
    """搜集节点用：取某领域当前已启用的工具名列表。"""
    return [
        r.tool_name
        for r in get_domain_tools(session, domain)
        if r.enabled
    ]


# ---------- Schedule（定时运行） ----------

def get_schedule(session: Session, agent_id: str) -> "Schedule | None":
    from app.models import Schedule
    return session.scalar(select(Schedule).where(Schedule.agent_id == agent_id))


def list_schedules(session: Session) -> list:
    from app.models import Schedule
    return list(session.scalars(select(Schedule).order_by(Schedule.created_at.desc())))


def upsert_schedule(
    session: Session, agent_id: str, *,
    run_type: str = "daily", cron_expr: str = "", once_at=None, enabled: bool = True,
):
    """新建或更新某智能体的定时配置。

    run_type: once/daily/weekly
    - once: 用 once_at（datetime），cron_expr 留空
    - daily/weekly: 用 cron_expr，once_at 留空
    """
    from app.models import Schedule
    from datetime import datetime
    sch = get_schedule(session, agent_id)
    if sch is None:
        sch = Schedule(
            agent_id=agent_id, run_type=run_type, cron_expr=cron_expr,
            once_at=once_at, enabled=enabled,
        )
        session.add(sch)
    else:
        sch.run_type = run_type
        sch.cron_expr = cron_expr
        sch.once_at = once_at
        sch.enabled = enabled
    session.flush()
    return sch


def delete_schedule(session: Session, agent_id: str) -> bool:
    from app.models import Schedule
    sch = get_schedule(session, agent_id)
    if sch is None:
        return False
    session.delete(sch)
    session.flush()
    return True


# ---------- AgentTemplate（模板库） ----------

def create_template(
    session: Session, *, name: str, domain: str, intent_template: str,
    tools: list[str] | None = None, prompt_template: str = "",
    template_id: str | None = None,
):
    """新建模板。tools 未指定时用领域默认。"""
    ensure_registered()
    from app.models import AgentTemplate
    tpl = AgentTemplate(
        id=template_id or f"tpl_{uuid.uuid4().hex[:12]}",
        name=name, domain=domain, intent_template=intent_template,
        tools=tools or DOMAIN_TOOLS.get(domain, ["web_search"]),
        prompt_template=prompt_template or DOMAIN_PROMPTS.get(domain, ""),
    )
    session.add(tpl)
    session.flush()
    return tpl


def get_template(session: Session, template_id: str):
    from app.models import AgentTemplate
    return session.get(AgentTemplate, template_id)


def list_templates(session: Session):
    from app.models import AgentTemplate
    return list(session.scalars(
        select(AgentTemplate).order_by(AgentTemplate.created_at.desc())
    ))


def update_template(
    session: Session, template_id: str, *,
    name: str | None = None, domain: str | None = None,
    intent_template: str | None = None, tools: list[str] | None = None,
    prompt_template: str | None = None,
):
    from app.models import AgentTemplate
    tpl = session.get(AgentTemplate, template_id)
    if not tpl:
        return None
    if name is not None: tpl.name = name
    if domain is not None: tpl.domain = domain
    if intent_template is not None: tpl.intent_template = intent_template
    if tools is not None: tpl.tools = tools
    if prompt_template is not None: tpl.prompt_template = prompt_template
    session.flush()
    return tpl


def delete_template(session: Session, template_id: str) -> bool:
    from app.models import AgentTemplate
    tpl = session.get(AgentTemplate, template_id)
    if tpl is None:
        return False
    session.delete(tpl)
    session.flush()
    return True


def template_from_agent(session: Session, agent_id: str, name: str | None = None):
    """从现有智能体生成模板（复制配置，不关联）。"""
    agent = get_agent(session, agent_id)
    if not agent:
        return None
    return create_template(
        session,
        name=name or f"{agent.name}（模板）",
        domain=agent.domain,
        intent_template=agent.intent,
        tools=agent.tools,
        prompt_template=agent.prompt_template,
    )
