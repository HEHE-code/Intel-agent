"""数据源工具公共结构。

所有工具返回统一的 Doc 列表，搜集/分析节点可泛化处理。
单个工具失败不应中断整体流程 —— 用 @safe 包装，失败返回空列表。
"""
from __future__ import annotations

import functools
import logging
from dataclasses import dataclass, field, asdict
from typing import Callable, ParamSpec, TypeVar

log = logging.getLogger(__name__)


@dataclass
class Doc:
    """一条搜集到的资料。"""

    source: str  # 工具名，如 web_search / yfinance
    title: str = ""
    url: str = ""
    content: str = ""  # 摘要或正文片段
    published: str = ""  # 发布时间（若有）
    meta: dict = field(default_factory=dict)

    def to_dict(self) -> dict:
        return asdict(self)


P = ParamSpec("P")
R = TypeVar("R", bound=list)


def safe(tool_name: str) -> Callable[[Callable[P, R]], Callable[P, R]]:
    """装饰器：工具抛异常时记录并返回空列表，不中断工作流。"""

    def deco(fn: Callable[P, R]) -> Callable[P, R]:
        @functools.wraps(fn)
        def wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
            try:
                return fn(*args, **kwargs)
            except Exception as e:  # 节点级容错：失败标 failed，不中断
                log.warning("工具 %s 失败: %s", tool_name, e)
                return []  # type: ignore[return-value]

        return wrapper

    return deco
