"""智能体路由：生成、列表、详情、编辑、运行(SSE)。"""
from __future__ import annotations

import json
import queue
import threading

from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

from app.crud import create_agent, delete_agent, get_agent, get_schedule, list_agents, list_runs_for_agent, update_agent
from app.db import get_session
from app.engine import run_agent
from app.intent import parse_intent
from app.tools.registry import DOMAIN_PROMPTS, ensure_registered, tools_for_domain

router = APIRouter(prefix="/agents", tags=["agents"])


class GenerateRequest(BaseModel):
    intent: str = Field(..., min_length=2, description="自然语言情报需求")
    domain: str | None = Field(None, description="可选，强制指定领域")


class AgentOut(BaseModel):
    id: str
    name: str
    domain: str
    intent: str
    tools: list[str]
    prompt_template: str
    created_at: str
    last_run_at: str = ""
    last_status: str = ""
    run_count: int = 0
    has_schedule: bool = False

    @classmethod
    def from_orm(cls, a, runs=None, has_schedule: bool = False) -> "AgentOut":
        runs = runs if runs is not None else []
        last = runs[0] if runs else None
        return cls(
            id=a.id,
            name=a.name,
            domain=a.domain,
            intent=a.intent,
            tools=a.tools,
            prompt_template=a.prompt_template,
            created_at=a.created_at.isoformat() if a.created_at else "",
            last_run_at=last.created_at.isoformat() if last and last.created_at else "",
            last_status=last.status if last else "idle",
            run_count=len(runs),
            has_schedule=has_schedule,
        )


@router.post("/generate", response_model=AgentOut)
def generate(req: GenerateRequest) -> AgentOut:
    """自然语言 → 智能体配置并入库。"""
    ensure_registered()
    parsed = parse_intent(req.intent)
    # 领域：用户指定优先（支持自定义领域，不限于预设5个），否则用 LLM 解析结果
    domain = req.domain.strip() if req.domain and req.domain.strip() else parsed.domain
    # 自定义领域（非预设）自动持久化，下次生成页能看到该领域标签
    _persist_custom_domain(domain)
    with get_session() as s:
        agent = create_agent(
            s,
            name=parsed.agent_name,
            domain=domain,
            intent=req.intent,
            tools=tools_for_domain(domain),
            prompt_template=DOMAIN_PROMPTS.get(domain, ""),
        )
        return AgentOut.from_orm(agent)


def _persist_custom_domain(domain: str) -> None:
    """非预设领域自动存 CustomDomain（已存在则跳过）。"""
    from app.api.domains import PRESET_DOMAINS, pick_color
    from app.api.domains import _PRESET_COLORS
    from app.db import SessionLocal
    from app.models import CustomDomain
    if not domain or any(d["key"] == domain for d in PRESET_DOMAINS):
        return
    with SessionLocal() as s:
        if not s.get(CustomDomain, domain):
            from sqlalchemy import select as _select
            used = _PRESET_COLORS | {c.color for c in s.scalars(_select(CustomDomain))}
            s.add(CustomDomain(key=domain, label=domain, color=pick_color(domain, used)))
            s.commit()


@router.get("", response_model=list[AgentOut])
def list_() -> list[AgentOut]:
    with get_session() as s:
        agents = list_agents(s)
        return [
            AgentOut.from_orm(a, list_runs_for_agent(s, a.id), get_schedule(s, a.id) is not None)
            for a in agents
        ]


@router.get("/{agent_id}", response_model=AgentOut)
def detail(agent_id: str) -> AgentOut:
    with get_session() as s:
        agent = get_agent(s, agent_id)
        if not agent:
            raise HTTPException(404, "智能体不存在")
        return AgentOut.from_orm(
            agent, list_runs_for_agent(s, agent_id), get_schedule(s, agent_id) is not None
        )


class UpdateRequest(BaseModel):
    name: str | None = None
    tools: list[str] | None = None
    prompt_template: str | None = None


@router.put("/{agent_id}", response_model=AgentOut)
def update(agent_id: str, req: UpdateRequest) -> AgentOut:
    with get_session() as s:
        agent = update_agent(
            s, agent_id,
            name=req.name, tools=req.tools, prompt_template=req.prompt_template,
        )
        if not agent:
            raise HTTPException(404, "智能体不存在")
        return AgentOut.from_orm(agent)


@router.delete("/{agent_id}")
def remove(agent_id: str) -> dict:
    """删除智能体（级联删 runs + schedule）。"""
    with get_session() as s:
        if not delete_agent(s, agent_id):
            raise HTTPException(404, "智能体不存在")
        return {"ok": True}


# ============ 运行（SSE 流式） ============

def _sse(event: dict) -> str:
    """格式化为 SSE 数据帧。"""
    return f"data: {json.dumps(event, ensure_ascii=False)}\n\n"


@router.post("/{agent_id}/run")
def run(agent_id: str) -> StreamingResponse:
    """启动执行并 SSE 流式推送运行步骤。"""
    # 校验智能体存在
    with get_session() as s:
        if not get_agent(s, agent_id):
            raise HTTPException(404, "智能体不存在")

    # 用 queue 在引擎线程与 SSE 流之间传事件
    ev_q: "queue.Queue[dict | None]" = queue.Queue()

    def cb(event: dict) -> None:
        ev_q.put(event)

    def worker() -> None:
        try:
            run_agent(agent_id, cb=cb)
        except Exception as e:
            ev_q.put({"type": "error", "message": f"运行失败: {e}"})
        finally:
            ev_q.put(None)  # 结束信号

    def stream():
        t = threading.Thread(target=worker, daemon=True)
        t.start()
        try:
            while True:
                event = ev_q.get(timeout=300)  # 单事件最长等 5 分钟
                if event is None:
                    break
                yield _sse(event)
        except queue.Empty:
            yield _sse({"type": "error", "message": "运行超时"})

    return StreamingResponse(
        stream(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


@router.get("/{agent_id}/active-run")
def active_run(agent_id: str) -> dict:
    """返回某智能体正在运行的 run（含已发生的实时事件），供前端中途查看。

    无活跃运行返回 {active: false}。
    """
    from app.crud import list_runs_for_agent
    with get_session() as s:
        runs = list_runs_for_agent(s, agent_id)
        for r in runs:
            if r.status == "running":
                return {
                    "active": True,
                    "run_id": r.id,
                    "events": r.steps or [],
                    "created_at": r.created_at.isoformat() if r.created_at else "",
                }
    return {"active": False}


@router.get("/{agent_id}/memory")
def memory(agent_id: str) -> list[dict]:
    """查看智能体记忆（历次关键结论，旧→新）。"""
    from app.crud import recent_memories
    with get_session() as s:
        mems = list(reversed(recent_memories(s, agent_id, limit=10)))
        return [
            {
                "run_id": m.run_id,
                "key_points": m.key_points or [],
                "created_at": m.created_at.isoformat() if m.created_at else "",
            }
            for m in mems
        ]


@router.delete("/{agent_id}/memory")
def clear_memory(agent_id: str) -> dict:
    """清空智能体记忆。"""
    from app.models import AgentMemory
    with get_session() as s:
        s.query(AgentMemory).filter(AgentMemory.agent_id == agent_id).delete()
        s.commit()
    return {"ok": True}
