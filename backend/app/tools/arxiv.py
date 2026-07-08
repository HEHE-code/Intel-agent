"""arXiv 论文检索（教育/科技领域，免 Key）。

API: http://export.arxiv.org/api/query （Atom XML，http→https 重定向）
实测国内可达，返回结构化论文数据。
"""
from __future__ import annotations

import re

import httpx

from app.tools.base import Doc, safe

_TAG = re.compile(r"<[^>]+>")
_WS = re.compile(r"\s+")
_ENTRY_SPLIT = re.compile(r"<entry>(.*?)</entry>", re.S)


def _clean(s: str) -> str:
    return _WS.sub(" ", _TAG.sub("", s)).strip()


def _field(entry: str, tag: str) -> str:
    m = re.search(rf"<{tag}>(.*?)</{tag}>", entry, re.S)
    return m.group(1) if m else ""


@safe("arxiv")
def search(query: str, max_results: int = 8) -> list[Doc]:
    """arXiv 全文检索，按提交时间倒序。"""
    r = httpx.get(
        "http://export.arxiv.org/api/query",
        timeout=20,
        follow_redirects=True,  # http→https
        params={
            "search_query": f"all:{query}",
            "max_results": max_results,
            "sortBy": "submittedDate",
            "sortOrder": "descending",
        },
    )
    r.raise_for_status()
    docs: list[Doc] = []
    for entry in _ENTRY_SPLIT.findall(r.text):
        # arXiv 的 <id> 是完整 URL；title 可能含多个，取第一个
        title = _field(entry, "title")
        id_url = _field(entry, "id")
        summary = _field(entry, "summary")
        if not title:
            continue
        docs.append(
            Doc(
                source="arxiv",
                title=_clean(title),
                url=id_url.strip(),
                content=_clean(summary),
            )
        )
    return docs
