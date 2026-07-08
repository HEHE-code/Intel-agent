"""GitHub 仓库检索（科技领域，免 Key）。

API: https://api.github.com/search/repositories
实测国内可达。免认证 60 次/小时（含轻量 User-Agent 即可）。
替代"GitHub Trending"——用 Search API + 时间/星标过滤实现热门项目发现。
"""
from __future__ import annotations

from datetime import datetime, timedelta

import httpx

from app.tools.base import Doc, safe

_HEADERS = {"Accept": "application/vnd.github+json", "User-Agent": "intelligence-agent"}


@safe("github")
def search(query: str, max_results: int = 8) -> list[Doc]:
    """搜索近 90 天内有更新的热门仓库，按星标倒序。"""
    since = (datetime.now() - timedelta(days=90)).strftime("%Y-%m-%d")
    r = httpx.get(
        "https://api.github.com/search/repositories",
        timeout=20,
        params={
            "q": f"{query} stars:>10 pushed:>{since}",
            "sort": "stars",
            "order": "desc",
            "per_page": max_results,
        },
        headers=_HEADERS,
    )
    r.raise_for_status()
    docs: list[Doc] = []
    for it in r.json().get("items", []):
        docs.append(
            Doc(
                source="github",
                title=it.get("full_name", ""),
                url=it.get("html_url", ""),
                content=it.get("description", "") or "",
                published=it.get("pushed_at", "")[:10],
                meta={
                    "stars": it.get("stargazers_count", 0),
                    "language": it.get("language"),
                },
            )
        )
    return docs
