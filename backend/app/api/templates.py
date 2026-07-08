"""模板库路由：列表、新建、详情、编辑、删除、从智能体存为模板。"""
from __future__ import annotations

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from app.crud import (
    create_template, delete_template, get_template, list_templates,
    template_from_agent, update_template,
)
from app.db import get_session
from app.tools.registry import DOMAIN_TOOLS, ensure_registered

router = APIRouter(prefix="/templates", tags=["templates"])


class TemplateOut(BaseModel):
    id: str
    name: str
    domain: str
    intent_template: str
    tools: list[str]
    prompt_template: str
    created_at: str

    @classmethod
    def from_orm(cls, t) -> "TemplateOut":
        return cls(
            id=t.id,
            name=t.name,
            domain=t.domain,
            intent_template=t.intent_template,
            tools=t.tools,
            prompt_template=t.prompt_template,
            created_at=t.created_at.isoformat() if t.created_at else "",
        )


class TemplateCreateReq(BaseModel):
    name: str = Field(..., min_length=1)
    domain: str = Field(..., description="military/finance/tech/education/company")
    intent_template: str = Field(..., min_length=2)
    tools: list[str] | None = None
    prompt_template: str | None = None


class TemplateUpdateReq(BaseModel):
    name: str | None = None
    domain: str | None = None
    intent_template: str | None = None
    tools: list[str] | None = None
    prompt_template: str | None = None


@router.get("", response_model=list[TemplateOut])
def list_() -> list[TemplateOut]:
    with get_session() as s:
        return [TemplateOut.from_orm(t) for t in list_templates(s)]


@router.post("", response_model=TemplateOut)
def create(req: TemplateCreateReq) -> TemplateOut:
    ensure_registered()
    with get_session() as s:
        # tools 未指定时按领域默认补全
        tools = req.tools if req.tools is not None else DOMAIN_TOOLS.get(req.domain, ["web_search"])
        tpl = create_template(
            s,
            name=req.name,
            domain=req.domain,
            intent_template=req.intent_template,
            tools=tools,
            prompt_template=req.prompt_template or "",
        )
        return TemplateOut.from_orm(tpl)


@router.get("/{template_id}", response_model=TemplateOut)
def detail(template_id: str) -> TemplateOut:
    with get_session() as s:
        tpl = get_template(s, template_id)
        if not tpl:
            raise HTTPException(404, "模板不存在")
        return TemplateOut.from_orm(tpl)


@router.put("/{template_id}", response_model=TemplateOut)
def update(template_id: str, req: TemplateUpdateReq) -> TemplateOut:
    with get_session() as s:
        tpl = update_template(
            s, template_id,
            name=req.name, domain=req.domain, intent_template=req.intent_template,
            tools=req.tools, prompt_template=req.prompt_template,
        )
        if not tpl:
            raise HTTPException(404, "模板不存在")
        return TemplateOut.from_orm(tpl)


@router.delete("/{template_id}")
def remove(template_id: str) -> dict:
    with get_session() as s:
        if not delete_template(s, template_id):
            raise HTTPException(404, "模板不存在")
        return {"ok": True}


# 从智能体存为模板（挂在 /api/agents/{id}/as-template，但这里用 /templates/from-agent/{agent_id}）
@router.post("/from-agent/{agent_id}", response_model=TemplateOut)
def from_agent(agent_id: str, body: dict | None = None) -> TemplateOut:
    """从现有智能体生成模板。body 可选 name。"""
    name = (body or {}).get("name") if body else None
    with get_session() as s:
        tpl = template_from_agent(s, agent_id, name=name)
        if not tpl:
            raise HTTPException(404, "智能体不存在")
        return TemplateOut.from_orm(tpl)
