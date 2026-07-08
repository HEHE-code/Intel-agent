"""网页正文爬取（公司/军事等领域通用，免 Key）。

给定 URL，用 readability-lxml 提取正文，过滤导航/广告等噪声。
用于爬取公司官网文章、官媒报道、爬到的搜索结果原文等。
"""
from __future__ import annotations

import re

import httpx
from readability import Document

from app.tools.base import Doc, safe

_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36"
    ),
    "Accept-Language": "zh-CN,zh;q=0.9",
}
_TAG = re.compile(r"<[^>]+>")
_WS = re.compile(r"\s+")


def _clean(html: str) -> str:
    return _WS.sub(" ", _TAG.sub("", html)).strip()


@safe("fetch_url")
def fetch(url: str, max_chars: int = 2000) -> list[Doc]:
    """抓取单个 URL 的正文。返回单元素列表（与工具接口统一）。"""
    r = httpx.get(url, timeout=15, headers=_HEADERS, follow_redirects=True)
    r.raise_for_status()
    doc = Document(r.text)
    body = _clean(doc.summary())
    return [
        Doc(
            source="fetch_url",
            title=_clean(doc.title()),
            url=str(r.url),
            content=body[:max_chars],
        )
    ]
