"""Tavily 搜索（高质量，需 Key，1000 credits/月）。

实测能搜到 cn.bing 拿不到的数据（如高考分数线）。
省 credit 策略：search_depth='basic'（1 credit/次），由 engine 控制调用次数。
"""
from __future__ import annotations

from tavily import TavilyClient

from app.config import get_settings
from app.tools.base import Doc, safe


@safe("tavily")
def search(query: str, max_results: int = 5) -> list[Doc]:
    """Tavily 网页搜索。每次调用消耗 1 credit（basic）。"""
    s = get_settings()
    if not s.tavily_api_key:
        return []
    client = TavilyClient(api_key=s.tavily_api_key)
    r = client.search(
        query,
        search_depth="basic",  # 省 credit
        max_results=max_results,
        include_answer=False,
    )
    docs: list[Doc] = []
    for d in r.get("results", []):
        docs.append(
            Doc(
                source="tavily",
                title=d.get("title", ""),
                url=d.get("url", ""),
                content=d.get("content", ""),
            )
        )
    return docs
