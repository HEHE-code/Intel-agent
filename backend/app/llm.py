"""LLM provider 抽象层。

把自定义网关 / DeepSeek / GLM 统一封装成一个 ChatModel，
上层只需 `get_llm()` 拿到实例后 `.invoke(messages)`，无需关心具体 provider。
三者都是 OpenAI 兼容接口，因此统一用 langchain_openai.ChatOpenAI。
"""
from __future__ import annotations

from functools import lru_cache

from langchain_core.language_models.chat_models import BaseChatModel

from app.config import Settings, get_settings


class LLMNotConfiguredError(RuntimeError):
    """未配置任何可用 LLM Key 时抛出。"""


def build_chat_model(settings: Settings | None = None, **overrides) -> BaseChatModel:
    """根据配置构建一个 OpenAI 兼容的 ChatModel。

    Args:
        settings: 配置；默认从 .env 读。
        **overrides: 覆盖参数，如 temperature=0、model=...。
    """
    s = settings or get_settings()
    if not s.llm_available:
        raise LLMNotConfiguredError(
            "未配置 LLM。请在 .env 设置 LLM_BASE_URL+LLM_API_KEY，"
            "或 DEEPSEEK_API_KEY / ZHIPU_API_KEY。"
        )

    # 延迟导入，避免无 LLM 时也能启动后端骨架
    from langchain_openai import ChatOpenAI

    params = {
        "model": s.llm_model_resolved,
        "api_key": s.llm_api_key_resolved,
        "base_url": s.llm_base_url_resolved,
        "timeout": 60,
        "max_retries": 2,
    }
    params.update(overrides)
    return ChatOpenAI(**params)


@lru_cache
def get_llm() -> BaseChatModel:
    """全局单例 LLM。settings 变化时调用 get_llm.cache_clear()。"""
    return build_chat_model()
