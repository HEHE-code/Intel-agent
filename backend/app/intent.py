"""意图解析：自然语言 → 结构化智能体配置。

用 LLM 从用户描述提取领域、主题、时间范围、关键实体，
输出可直接入库的 AgentConfig 草稿。
"""
from __future__ import annotations

import json
import logging
import re
from dataclasses import dataclass

from langchain_core.messages import HumanMessage, SystemMessage

from app.llm import build_chat_model, LLMNotConfiguredError

log = logging.getLogger(__name__)

VALID_DOMAINS = ["military", "finance", "tech", "education", "company"]
DOMAIN_CN = {
    "军事": "military", "军": "military", "防务": "military",
    "金融": "finance", "财经": "finance", "股市": "finance", "股票": "finance",
    "科技": "tech", "技术": "tech", "半导体": "tech", "芯片": "tech", "AI": "tech",
    "教育": "education", "论文": "education", "学术": "education", "研究": "education",
    "公司": "company", "企业": "company", "财报": "company",
}

_SYSTEM = """你是情报需求解析器。从用户的自然语言描述中提取结构化情报需求，输出**严格的 JSON**（不要任何解释、不要 markdown 代码块）。

JSON 字段：
- domain: 必须是以下之一 military/finance/tech/education/company
- topic: 情报主题（简短，≤20字）
- time_range: 时间范围（如"近1个月""2025年Q2""无限制"）
- key_entities: 关键实体数组（人/组织/公司/事件/技术名，≤6个）
- search_keywords: 用于数据源检索的关键词数组（中英文混合，≤5个，适合搜索）
- agent_name: 智能体名称（简短专业，≤15字）

判断 domain 的依据：军事部署/防务/演习/武器→military；金融/股市/财报/行情→finance；技术/芯片/AI/开源→tech；教育/论文/学术→education；特定公司/企业动态→company。"""

_USER_TMPL = """用户需求：{intent}

输出 JSON："""


@dataclass
class ParsedIntent:
    domain: str
    topic: str
    time_range: str
    key_entities: list[str]
    search_keywords: list[str]
    agent_name: str

    def to_dict(self) -> dict:
        return {
            "domain": self.domain,
            "topic": self.topic,
            "time_range": self.time_range,
            "key_entities": self.key_entities,
            "search_keywords": self.search_keywords,
            "agent_name": self.agent_name,
        }


def _extract_json(text: str) -> dict:
    """从 LLM 输出里抠出 JSON（容错：去代码块、找首个 { 到末尾 }）。"""
    t = text.strip()
    # 去 markdown 代码块
    t = re.sub(r"^```(?:json)?\s*", "", t)
    t = re.sub(r"\s*```$", "", t)
    # 找首个 { 到最后一个 }
    start = t.find("{")
    end = t.rfind("}")
    if start == -1 or end == -1 or end <= start:
        raise ValueError(f"LLM 输出无 JSON: {text[:120]}")
    return json.loads(t[start : end + 1])


def _fallback_domain(intent: str) -> str:
    """LLM 失败时的关键词兜底领域识别。"""
    for cn, en in DOMAIN_CN.items():
        if cn in intent:
            return en
    return "company"


def parse_intent(intent: str) -> ParsedIntent:
    """用 LLM 解析自然语言意图。LLM 不可用时降级为关键词兜底。"""
    try:
        llm = build_chat_model(temperature=0)
        resp = llm.invoke(
            [
                SystemMessage(content=_SYSTEM),
                HumanMessage(content=_USER_TMPL.format(intent=intent)),
            ]
        )
        data = _extract_json(resp.content if isinstance(resp.content, str) else str(resp))
    except LLMNotConfiguredError:
        log.warning("LLM 未配置，意图解析降级为关键词兜底")
        return _fallback(intent, reason="llm_not_configured")
    except Exception as e:  # LLM 调用失败或 JSON 解析失败
        log.warning("LLM 意图解析失败，降级兜底: %s", e)
        return _fallback(intent, reason=str(e))

    # 校验 + 规范化
    domain = data.get("domain", "").strip().lower()
    if domain not in VALID_DOMAINS:
        domain = _fallback_domain(intent)
    return ParsedIntent(
        domain=domain,
        topic=data.get("topic", intent[:20]),
        time_range=data.get("time_range", "无限制"),
        key_entities=list(data.get("key_entities", []))[:6],
        search_keywords=list(data.get("search_keywords", []))[:5] or [intent[:10]],
        agent_name=data.get("agent_name", intent[:15])[:30],
    )


def _fallback(intent: str, reason: str) -> ParsedIntent:
    return ParsedIntent(
        domain=_fallback_domain(intent),
        topic=intent[:20],
        time_range="无限制",
        key_entities=[],
        search_keywords=[intent[:10]],
        agent_name=intent[:15],
    )
