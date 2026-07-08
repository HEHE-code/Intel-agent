"""RSS 订阅抓取（军事/通用领域，免 Key）。

实测国内官媒 RSS 可达且数据丰富：
- 人民网军事 100 条、新华网国际 300 条、中国军网 2537 条
"""
from __future__ import annotations

import feedparser

from app.tools.base import Doc, safe

# 军事/防务领域预设权威源
MILITARY_FEEDS = [
    ("人民网-军事", "http://www.people.com.cn/rss/military.xml"),
    ("中国军网", "http://www.81.cn/rss.xml"),
    ("新华网-国际", "https://www.xinhuanet.com/politics/news_politics.xml"),
]


@safe("rss")
def fetch_feed(name: str, url: str, max_results: int = 8) -> list[Doc]:
    """抓取单个 RSS 源。"""
    f = feedparser.parse(url)
    docs: list[Doc] = []
    for e in f.entries[:max_results]:
        docs.append(
            Doc(
                source="rss",
                title=e.get("title", ""),
                url=e.get("link", ""),
                content=e.get("summary", "") or e.get("description", ""),
                published=e.get("published", "")[:16],
                meta={"feed": name},
            )
        )
    return docs


@safe("rss")
def military_feed(max_results: int = 12, keywords: list[str] | None = None) -> list[Doc]:
    """聚合军事领域预设 RSS 源。

    keywords: 若提供，只保留标题/摘要命中关键词的条目（过滤无关通用新闻）。
    """
    docs: list[Doc] = []
    for name, url in MILITARY_FEEDS:
        docs.extend(fetch_feed(name, url, max_results=8))
    if keywords:
        kws = [k.lower() for k in keywords if k]
        docs = [
            d
            for d in docs
            if any(k in (d.title + d.content).lower() for k in kws)
        ]
    return docs[:max_results]
