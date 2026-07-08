"""应用配置：从 .env 读取，自动识别可用的 LLM provider 与数据源。"""
from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", extra="ignore"
    )

    # —— LLM 配置 ——
    # 自定义 OpenAI 兼容端点（如内网网关），优先级最高
    llm_base_url: str = ""
    llm_api_key: str = ""
    llm_model: str = ""
    # 官方 provider（无自定义端点时用）
    deepseek_api_key: str = ""
    zhipu_api_key: str = ""
    glm_api_key: str = ""  # 智谱别名，等价于 zhipu_api_key
    llm_provider: str = ""  # 显式指定 deepseek | glm；空则自动识别

    # —— 数据源升级 Key（可选） ——
    tavily_api_key: str = ""
    alpha_vantage_api_key: str = ""
    newsapi_key: str = ""

    # —— 运行配置 ——
    database_path: str = "data/intelligence.db"
    cors_origins: str = "http://localhost:3000,http://127.0.0.1:3000"

    @property
    def cors_origin_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]

    @property
    def sqlite_url(self) -> str:
        return f"sqlite:///{self.database_path}"

    @property
    def db_dir(self) -> Path:
        return Path(self.database_path).parent

    # —— 核心：解析实际使用的 LLM 配置 ——
    # 优先级：自定义 OpenAI 兼容端点 > 官方 provider 自动识别
    @property
    def active_llm_provider(self) -> str | None:
        """返回 custom | deepseek | glm | None。"""
        if self.llm_base_url and self.llm_api_key:
            return "custom"
        if self.llm_provider in ("deepseek", "glm"):
            return self.llm_provider
        if self.deepseek_api_key:
            return "deepseek"
        if self.zhipu_api_key or self.glm_api_key:
            return "glm"
        return None

    @property
    def llm_base_url_resolved(self) -> str | None:
        """实际请求的 base_url（OpenAI 兼容，含 /v1）。"""
        if self.active_llm_provider == "custom":
            return self.llm_base_url.rstrip("/")
        if self.active_llm_provider == "deepseek":
            return "https://api.deepseek.com/v1"
        if self.active_llm_provider == "glm":
            return "https://open.bigmodel.cn/api/paas/v4"
        return None

    @property
    def llm_api_key_resolved(self) -> str | None:
        if self.active_llm_provider == "custom":
            return self.llm_api_key
        if self.active_llm_provider == "deepseek":
            return self.deepseek_api_key
        if self.active_llm_provider == "glm":
            return self.zhipu_api_key or self.glm_api_key
        return None

    @property
    def llm_model_resolved(self) -> str | None:
        """模型名：显式指定 > provider 默认。"""
        if self.llm_model:
            return self.llm_model
        if self.active_llm_provider == "deepseek":
            return "deepseek-chat"
        if self.active_llm_provider == "glm":
            return "glm-4-plus"
        if self.active_llm_provider == "custom":
            return "glm-5.1"  # 自定义端点默认；可经 LLM_MODEL 覆盖
        return None

    @property
    def llm_available(self) -> bool:
        return self.active_llm_provider is not None


@lru_cache
def get_settings() -> Settings:
    return Settings()
