"""金融数据源（akshare，聚合东方财富/新浪，免 Key）。

实测国内可达。提供：
- finance_news：全球财经快讯
- stock_news：个股新闻（需股票代码，如 600519）
- stock_quote：个股实时行情
"""
from __future__ import annotations

import akshare as ak

from app.tools.base import Doc, safe


@safe("finance_news")
def finance_news(max_results: int = 12) -> list[Doc]:
    """东方财富全球财经快讯（无需标的，最新时事）。"""
    df = ak.stock_info_global_em()
    docs: list[Doc] = []
    for _, row in df.head(max_results).iterrows():
        docs.append(
            Doc(
                source="finance_news",
                title=str(row.get("标题", "")),
                url=str(row.get("链接", "")),
                content=str(row.get("摘要", "")),
                published=str(row.get("发布时间", ""))[:16],
            )
        )
    return docs


@safe("stock_news")
def stock_news(symbol: str, max_results: int = 10) -> list[Doc]:
    """个股新闻。symbol 为 6 位股票代码，如 600519（贵州茅台）。"""
    df = ak.stock_news_em(symbol=symbol)
    docs: list[Doc] = []
    for _, row in df.head(max_results).iterrows():
        docs.append(
            Doc(
                source="stock_news",
                title=str(row.get("新闻标题", "")),
                url=str(row.get("新闻链接", "")),
                content=str(row.get("新闻内容", "")),
                published=str(row.get("发布时间", ""))[:16],
                meta={"source": str(row.get("文章来源", ""))},
            )
        )
    return docs


@safe("stock_quote")
def stock_quote(symbol: str) -> list[Doc]:
    """个股实时行情快照。symbol 为 6 位股票代码。"""
    df = ak.stock_zh_a_spot_em()
    row = df[df["代码"] == symbol]
    if row.empty:
        return []
    r = row.iloc[0]
    content = (
        f"最新价 {r.get('最新价')}  涨跌幅 {r.get('涨跌幅')}%  "
        f"成交量 {r.get('成交量')}  成交额 {r.get('成交额')}  "
        f"名称 {r.get('名称')}"
    )
    return [
        Doc(
            source="stock_quote",
            title=f"{r.get('名称')}({symbol}) 行情",
            url=f"https://quote.eastmoney.com/sh{symbol}.html"
            if symbol.startswith("6")
            else f"https://quote.eastmoney.com/sz{symbol}.html",
            content=content,
            meta={k: r.get(k) for k in ["最新价", "涨跌幅", "成交量", "成交额"]},
        )
    ]
