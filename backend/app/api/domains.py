"""领域路由：返回所有领域（预设+自定义）、新增自定义领域。"""
from __future__ import annotations

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import select

from app.db import get_session, SessionLocal
from app.models import CustomDomain

router = APIRouter(prefix="/domains", tags=["domains"])

# 预设 5 领域（与 registry.py DOMAIN_TOOLS 对齐）
PRESET_DOMAINS = [
    {"key": "military", "label": "军事", "color": "#DC2626", "preset": True},
    {"key": "finance", "label": "金融", "color": "#059669", "preset": True},
    {"key": "tech", "label": "科技", "color": "#3B82F6", "preset": True},
    {"key": "education", "label": "教育", "color": "#7C3AED", "preset": True},
    {"key": "company", "label": "公司", "color": "#D97706", "preset": True},
]

# 自定义领域调色板（避开预设 5 色，每个自定义领域按名哈希取色，保证不同名不同色）
_CUSTOM_PALETTE = [
    "#0891B2",  # 青
    "#9333EA",  # 紫
    "#DB2777",  # 粉
    "#65A30D",  # 草绿
    "#EA580C",  # 橘
    "#0D9488",  # 蓝绿
    "#7C3AED",  # 靛
    "#CA8A04",  # 金
    "#2563EB",  # 宝蓝
    "#E11D48",  # 玫红
]
_PRESET_COLORS = {d["color"] for d in PRESET_DOMAINS}


def pick_color(key: str, used_colors: set[str] | None = None) -> str:
    """为领域选色：优先哈希命中且未被占用的色，否则取首个未占用色。

    used_colors: 已被其他领域占用的颜色（预设色 + 现有自定义色），用于避让。
    """
    used = used_colors or set()
    # 哈希命中色若未被占用则用，保证同名稳定
    hashed = _CUSTOM_PALETTE[hash(key) % len(_CUSTOM_PALETTE)]
    if hashed not in used:
        return hashed
    # 否则取首个未占用色
    for c in _CUSTOM_PALETTE:
        if c not in used:
            return c
    return hashed  # 全占用完，兜底


@router.get("")
def list_() -> list[dict]:
    """返回所有领域：预设 5 个 + 用户自定义。"""
    with SessionLocal() as s:
        customs = list(s.scalars(select(CustomDomain).order_by(CustomDomain.created_at)))
    custom_list = [
        {"key": c.key, "label": c.label, "color": c.color, "preset": False}
        for c in customs
    ]
    return PRESET_DOMAINS + custom_list


class DomainCreateReq(BaseModel):
    key: str = Field(..., min_length=1, description="领域标识，如 能源")
    label: str | None = None  # 不填则同 key
    color: str | None = None  # 不填则默认灰


@router.post("")
def create(req: DomainCreateReq) -> dict:
    """新增自定义领域。已存在则返回已有。"""
    key = req.key.strip()
    if any(d["key"] == key for d in PRESET_DOMAINS):
        raise HTTPException(400, "预设领域无需重复添加")
    with SessionLocal() as s:
        existing = s.get(CustomDomain, key)
        if existing:
            return {"key": existing.key, "label": existing.label, "color": existing.color, "preset": False}
        # 已占用色 = 预设色 + 现有自定义色，避让防重复
        used = _PRESET_COLORS | {c.color for c in s.scalars(select(CustomDomain))}
        d = CustomDomain(
            key=key,
            label=(req.label or key).strip(),
            color=req.color or pick_color(key, used),
        )
        s.add(d)
        s.commit()
        return {"key": d.key, "label": d.label, "color": d.color, "preset": False}


@router.delete("/{key}")
def remove(key: str) -> dict:
    """删除自定义领域。不影响已用该领域的智能体。"""
    with SessionLocal() as s:
        d = s.get(CustomDomain, key)
        if not d:
            raise HTTPException(404, "领域不存在")
        s.delete(d)
        s.commit()
        return {"ok": True}
