"""工具注册表与领域映射。

统一管理所有数据源工具的入口，供搜集节点调度。
每个工具函数签名约定：(query 或 keyword 参数, max_results) -> list[Doc]。
"""
from __future__ import annotations

from typing import Callable

from app.tools.base import Doc

# 工具注册表：name -> (函数, 显示名, 描述, 是否需要参数)
ToolFunc = Callable[..., list[Doc]]


class ToolSpec:
    """单个工具的元信息。"""

    def __init__(self, name: str, func: ToolFunc, label: str, desc: str, needs_arg: bool):
        self.name = name
        self.func = func
        self.label = label
        self.desc = desc
        self.needs_arg = needs_arg  # True=需 query/symbol；False=无需参数

    def run(self, arg: str | None, max_results: int = 8) -> list[Doc]:
        try:
            if self.needs_arg:
                if not arg:
                    return []
                return self.func(arg, max_results=max_results)
            return self.func(max_results=max_results)
        except TypeError:
            # 部分工具无 max_results 形参，兜底
            return self.func(arg) if self.needs_arg else self.func()


# —— 注册表 ——
_REGISTRY: dict[str, ToolSpec] = {}


def register(spec: ToolSpec) -> ToolSpec:
    _REGISTRY[spec.name] = spec
    return spec


def get_tool(name: str) -> ToolSpec | None:
    return _REGISTRY.get(name)


def all_tools() -> list[ToolSpec]:
    return list(_REGISTRY.values())


# 延迟注册（避免导入时触发数据源库初始化）
def _register_all() -> None:
    if _REGISTRY:
        return
    from app.tools import arxiv, fetch_url, finance, gaokao, github, rss, tavily, web_search

    register(ToolSpec("web_search", web_search.search, "全网搜索", "Bing 网页搜索（通用）", True))
    register(ToolSpec("news_search", web_search.news, "新闻搜索", "Bing 新闻搜索", True))
    register(ToolSpec("arxiv", arxiv.search, "论文检索", "arXiv 学术论文", True))
    register(ToolSpec("github", github.search, "开源动态", "GitHub 热门仓库", True))
    register(ToolSpec("finance_news", finance.finance_news, "财经快讯", "东方财富全球快讯", False))
    register(ToolSpec("stock_news", finance.stock_news, "个股新闻", "按股票代码查新闻", True))
    register(ToolSpec("stock_quote", finance.stock_quote, "实时行情", "A股实时行情", True))
    register(ToolSpec("rss_military", rss.military_feed, "军事RSS", "人民网/军网/新华防务", False))
    register(ToolSpec("fetch_url", fetch_url.fetch, "网页爬取", "抓取指定URL正文", True))
    register(ToolSpec("gaokao_schools", gaokao.search, "院校查询", "高考择校/院校信息(eol.cn)", True))
    register(ToolSpec("tavily", tavily.search, "深度搜索", "Tavily 高质量搜索(需Key)", True))


# —— 领域 → 默认工具集映射（对齐设计文档） ——
DOMAIN_TOOLS: dict[str, list[str]] = {
    "military": ["rss_military", "web_search", "fetch_url"],
    "finance": ["finance_news", "stock_news", "web_search"],
    "tech": ["web_search", "github", "arxiv"],
    "education": ["gaokao_schools", "web_search"],
    "company": ["web_search", "stock_news", "fetch_url"],
}

# 各领域默认提示词模板
DOMAIN_PROMPTS: dict[str, str] = {
    "military": "你是军事情报分析师，关注部署动态、防务合作、装备发展、地缘风险，输出客观中立研判。",
    "finance": "你是金融分析师，结合行情数据与财经快讯，关注政策、资金流向与市场情绪。",
    "tech": "你是科技行业分析师，聚焦技术趋势、开源动态、产学研进展与竞争格局。",
    "education": "你是教育领域分析师，关注高考择校、分数线、录取政策、院校动态及学术研究进展，基于公开资讯与数据给出客观研判与建议。",
    "company": "你是企业情报分析师，关注公司动态、财务、产品与竞争态势。",
}

# 各领域权威源（用于 Bing site: 限定，提升中文召回质量）
# 实测：cn.bing 不限站点时中文分词差（"美日韩"→"美"），限定权威新闻站后召回精准
DOMAIN_SITES: dict[str, list[str]] = {
    "military": ["news.cn", "81.cn", "people.com.cn"],
    "finance": ["finance.eastmoney.com", "cls.cn", "yicai.com"],
    "tech": ["36kr.com", "news.cn", "ithome.com"],
    "education": ["news.cn", "eol.cn", "gaokao.com"],
    "company": ["finance.eastmoney.com", "news.cn"],
}


def sites_for_domain(domain: str) -> list[str]:
    return DOMAIN_SITES.get(domain, ["news.cn"])


# 各领域锚词：简单高频词，cn.bing 对复合短语分词差、对简单词友好
# 用锚词 site:权威源 能稳定召回领域相关新闻
DOMAIN_ANCHOR: dict[str, str] = {
    "military": "军事演习",
    "finance": "财经",
    "tech": "科技",
    "education": "高考 录取 分数线",
    "company": "企业",
}


def anchor_for_domain(domain: str) -> str:
    return DOMAIN_ANCHOR.get(domain, "")


# 噪声标题特征（百科/翻译/学校/词霸/早报错配等），搜集后过滤
NOISE_TITLE_HINTS = (
    "百科", "是什么意思", "翻译", "音标", "词霸", "实验学校", "小学",
    "联合早报", "百度百科", "搜狗", "包含哪里", "到底是什么", "知乎",
)


def is_noise_title(title: str) -> bool:
    return any(h in title for h in NOISE_TITLE_HINTS)


def tools_for_domain(domain: str) -> list[str]:
    """返回某领域的默认工具集。

    已知领域用专属工具；自定义领域用 web_search（有 Tavily Key 时 engine 会自动启用）。
    """
    return DOMAIN_TOOLS.get(domain, ["web_search"])


def ensure_registered() -> None:
    """显式触发注册（搜集节点调用前确保工具就绪）。"""
    _register_all()
