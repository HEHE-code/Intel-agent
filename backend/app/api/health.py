"""健康检查与系统状态。"""
from __future__ import annotations

from fastapi import APIRouter

from app.config import get_settings

router = APIRouter(tags=["system"])


@router.get("/health")
def health() -> dict:
    """前后端联调探针，暴露解析后的 LLM/数据源真实配置。"""
    s = get_settings()
    return {
        "status": "ok",
        "llm": {
            "provider": s.active_llm_provider,
            "available": s.llm_available,
            "base_url": s.llm_base_url_resolved,
            "model": s.llm_model_resolved,
            # 仅返回 key 末 4 位，避免泄漏
            "key_hint": (s.llm_api_key_resolved or "")[-4:],
        },
        "data_sources": {
            "tavily": bool(s.tavily_api_key),
            "alpha_vantage": bool(s.alpha_vantage_api_key),
            "newsapi": bool(s.newsapi_key),
        },
    }
