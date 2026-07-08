"""通用网络搜索 —— Bing 抓取（国内可达，免 Key）。

DuckDuckGo / Yahoo Finance 在国内被墙，改用 Bing HTML 抓取。
所有领域的基础工具。

召回优化：
- query 增强：纯时事 query 补时间限定，提升时效性结果权重
- 结果过滤：剔除百科/下载站/邮箱等噪声域，保留新闻/官媒/垂直站
"""
from __future__ import annotations

import re
from datetime import datetime
from urllib.parse import quote

import httpx

from app.tools.base import Doc, safe

_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36"
    ),
    "Accept-Language": "zh-CN,zh;q=0.9",
}
_TAG = re.compile(r"<[^>]+>")

# 噪声域名：百科/下载站/邮箱/社交首页等，与情报分析无关
_NOISE_HOSTS = (
    "baike.baidu.com", "zhidao.baidu.com", "baike.so.com",
    "mail.qq.com", "qq.com", "weixin.qq.com",
    "pcsoft", "download", "microsoft.com/detail",
    "zhihu.com/question",  # 知乎问答式泛知识，非新闻
)


def _strip(html: str) -> str:
    return _TAG.sub("", html).replace("&ensp;", " ").replace("&#0183;", "·").strip()


def _is_noise(url: str) -> bool:
    return any(h in url for h in _NOISE_HOSTS)


def _enhance_query(query: str, *, news: bool) -> str:
    """给 query 补时间限定，提升时效性召回。"""
    year = datetime.now().year
    q = query.strip()
    # 已含年份就不重复加
    if re.search(r"20\d{2}", q):
        return q
    sep = " " if news else " 最新"
    return f"{q}{sep}{year}"


@safe("web_search")
def search(query: str, max_results: int = 8, site: str | None = None) -> list[Doc]:
    """Bing 网页搜索（HTML 抓取）。

    site: 限定站点（如 news.cn），cn.bing 对纯中文分词差，
    限定权威源后召回质量大幅提升。
    """
    q = _enhance_query(query, news=False)
    if site:
        q = f"{q} site:{site}"
    url = f"https://cn.bing.com/search?q={quote(q)}&setlang=zh-CN&cc=cn&count=30"
    r = httpx.get(url, timeout=15, headers=_HEADERS, follow_redirects=True)
    r.raise_for_status()
    html = r.text

    docs: list[Doc] = []
    for block in re.finditer(r'<li class="b_algo"[^>]*>(.*?)</li>', html, re.S):
        seg = block.group(1)
        href_m = re.search(r'href="(http[^"]+)"', seg)
        title_m = re.search(r"<h2[^>]*>(.*?)</h2>", seg, re.S)
        if not href_m or not title_m:
            continue
        href = href_m.group(1)
        if "r.bing.com/rs/" in href or _is_noise(href):
            continue
        p_m = re.search(r"<p[^>]*>(.*?)</p>", seg, re.S)
        docs.append(
            Doc(
                source="web_search",
                title=_strip(title_m.group(1)),
                url=href,
                content=_strip(p_m.group(1)) if p_m else "",
            )
        )
        if len(docs) >= max_results:
            break
    return docs


@safe("news_search")
def news(query: str, max_results: int = 8) -> list[Doc]:
    """Bing 新闻搜索（news vertical）。"""
    q = _enhance_query(query, news=True)
    url = f"https://cn.bing.com/news/search?q={quote(q)}&qft=sortbydate&setlang=zh-CN"
    r = httpx.get(url, timeout=15, headers=_HEADERS, follow_redirects=True)
    r.raise_for_status()
    html = r.text

    docs: list[Doc] = []
    # 新闻卡片容器：class 含 newsitem
    for block in re.finditer(r'<div class="newsitem[^"]*"[^>]*>(.*?)</div>', html, re.S):
        seg = block.group(1)
        href_m = re.search(r'href="(http[^"]+)"', seg)
        title_m = re.search(r"<a[^>]*>(.*?)</a>", seg, re.S)
        if not href_m or not title_m:
            continue
        href = href_m.group(1)
        if _is_noise(href):
            continue
        snip_m = re.search(r'class="snippet"[^>]*>(.*?)</div>', seg, re.S)
        docs.append(
            Doc(
                source="news_search",
                title=_strip(title_m.group(1)),
                url=href,
                content=_strip(snip_m.group(1)) if snip_m else "",
            )
        )
        if len(docs) >= max_results:
            break
    return docs
