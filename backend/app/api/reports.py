"""报告路由：列表、详情、下载。"""
from __future__ import annotations

from fastapi import APIRouter, HTTPException
from fastapi.responses import PlainTextResponse
from pydantic import BaseModel

from app.crud import get_run, list_runs
from app.db import get_session

router = APIRouter(prefix="/reports", tags=["reports"])


class ReportOut:
    pass


@router.get("")
def list_(search: str = "", agent_id: str = "", domain: str = "", status: str = "") -> list[dict]:
    """历史报告列表，支持搜索/筛选。

    search: 关键词，搜 agent_name + report_md 全文
    agent_id/domain/status: 筛选
    """
    from app.crud import get_agent
    with get_session() as s:
        result = []
        for r in list_runs(s):
            a = get_agent(s, r.agent_id)
            agent_name = a.name if a else "(已删除)"
            domain_val = a.domain if a else ""
            # 筛选
            if agent_id and r.agent_id != agent_id:
                continue
            if domain and domain_val != domain:
                continue
            if status and r.status != status:
                continue
            if search:
                q = search.lower()
                hay = f"{agent_name} {r.report_md or ''}".lower()
                if q not in hay:
                    continue
            result.append({
                "id": r.id,
                "agent_id": r.agent_id,
                "agent_name": agent_name,
                "domain": domain_val,
                "status": r.status,
                "created_at": r.created_at.isoformat() if r.created_at else "",
                "report_length": len(r.report_md or ""),
                "preview": (r.report_md or "")[:80],
                "steps_count": len(r.steps or []),
                "starred": bool(r.starred),
                "note": r.note or "",
            })
        return result


@router.get("/{run_id}")
def detail(run_id: str) -> dict:
    """报告详情（含完整 Markdown 与步骤日志 + 标星/批注）。"""
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
            "starred": bool(r.starred),
            "note": r.note or "",
        }


class MarkReq(BaseModel):
    starred: bool | None = None
    note: str | None = None


@router.put("/{run_id}/mark")
def mark(run_id: str, req: MarkReq) -> dict:
    """标星 / 写批注。"""
    from app.crud import mark_run
    with get_session() as s:
        r = mark_run(s, run_id, starred=req.starred, note=req.note)
        if not r:
            raise HTTPException(404, "报告不存在")
        return {"id": r.id, "starred": bool(r.starred), "note": r.note or ""}


@router.get("/{run_id}/download", response_class=PlainTextResponse)
def download(run_id: str) -> str:
    """下载报告 .md 原文。"""
    with get_session() as s:
        r = get_run(s, run_id)
        if not r:
            raise HTTPException(404, "报告不存在")
        return r.report_md or "(无报告内容)"


@router.get("/compare/{a}/vs/{b}")
def compare(a: str, b: str) -> dict:
    """对比两份报告：返回段落级 diff（新增/删除/未变/改动）。

    要求两份报告属于同一智能体（否则不可比）。
    """
    from app.diff import diff_reports, summarize_diff
    with get_session() as s:
        ra, rb = get_run(s, a), get_run(s, b)
        if not ra or not rb:
            raise HTTPException(404, "报告不存在")
        if ra.agent_id != rb.agent_id:
            raise HTTPException(400, "不同智能体的报告不可对比")
        left_md, right_md = ra.report_md or "", rb.report_md or ""
        return {
            "left": {"id": ra.id, "created_at": ra.created_at.isoformat() if ra.created_at else "", "status": ra.status},
            "right": {"id": rb.id, "created_at": rb.created_at.isoformat() if rb.created_at else "", "status": rb.status},
            "diff": diff_reports(left_md, right_md),
            "summary": summarize_diff(left_md, right_md),
        }


class AskReq(BaseModel):
    question: str
    history: list[dict] = []  # 多轮对话历史 [{role,content}]


@router.post("/{run_id}/ask")
def ask(run_id: str, req: AskReq) -> dict:
    """基于报告内容回答追问。多轮对话（保留 history）。"""
    from app.llm import build_chat_model, LLMNotConfiguredError
    from langchain_core.messages import HumanMessage, SystemMessage
    with get_session() as s:
        r = get_run(s, run_id)
        if not r:
            raise HTTPException(404, "报告不存在")
        report_md = r.report_md or ""
    sys = (
        "你是情报分析助手。基于以下报告内容回答用户追问。"
        "要求：1.答案必须有报告依据，引用报告具体内容；"
        "2.报告未涉及的问题，明确说'本报告未覆盖该内容'，不要编造；"
        "3.简洁直接，不要复述整篇报告。\n\n"
        f"【报告内容】\n{report_md[:4000]}"
    )
    msgs = [SystemMessage(content=sys)]
    for h in req.history[-6:]:  # 最近3轮（6条）控制 token
        role = h.get("role", "user")
        content = h.get("content", "")
        if role == "assistant":
            msgs.append(SystemMessage(content=f"[上次助手回答] {content}"))
        else:
            msgs.append(HumanMessage(content=content))
    msgs.append(HumanMessage(content=req.question))
    try:
        llm = build_chat_model(temperature=0)
        resp = llm.invoke(msgs)
        answer = resp.content if isinstance(resp.content, str) else str(resp.content)
        return {"answer": answer}
    except LLMNotConfiguredError:
        raise HTTPException(503, "LLM 未配置")
    except Exception as e:
        raise HTTPException(500, f"回答失败: {e}")
