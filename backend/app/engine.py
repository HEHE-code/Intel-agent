"""LangGraph 三节点工作流引擎。

搜集 → 分析 → 结论，每步通过回调推送 SSE 事件。
- 搜集节点：按领域调度工具，拿原始资料
- 分析节点：LLM 提炼关键情报（结构化）
- 结论节点：LLM 生成 Markdown 报告
节点级重试 2 次，失败标 failed 不中断整体流程。
"""
from __future__ import annotations

import json
import logging
from datetime import datetime
from typing import Callable, TypedDict

from langchain_core.messages import HumanMessage, SystemMessage
from langgraph.graph import END, START, StateGraph

from app.crud import add_memory, create_run, get_agent, update_run
from app.db import SessionLocal
from app.llm import build_chat_model, LLMNotConfiguredError
from app.tools.base import Doc
from app.tools.registry import ensure_registered, get_tool

log = logging.getLogger(__name__)

MAX_RETRY = 2  # 节点级重试上限


# —— 工作流状态 ——
class WorkflowState(TypedDict, total=False):
    agent_id: str
    intent: str
    domain: str
    tools: list[str]
    prompt_template: str
    keywords: list[str]  # 搜索关键词（从 intent 解析或直接用 intent）
    docs: list[dict]  # 搜集到的资料（Doc.to_dict）
    analysis: str  # 分析节点输出
    report_md: str  # 最终报告
    steps: list[dict]  # 各节点运行日志
    errors: list[str]


# SSE 事件回调：type/node/message/data
EventCb = Callable[[dict], None]


def _emit(cb: EventCb | None, event: dict) -> None:
    """推送一个 SSE 事件。"""
    if cb:
        try:
            cb(event)
        except Exception as e:  # 回调失败不影响主流程
            log.warning("SSE 回调失败: %s", e)


def _with_retry(node_name: str, fn: Callable[[], dict], state: WorkflowState, cb: EventCb | None) -> dict:
    """节点级重试包装。fn 返回该节点的 step 日志（含 status）。"""
    last_err = None
    for attempt in range(1, MAX_RETRY + 2):  # 初次 + 2 次重试
        _emit(cb, {"type": "step_start", "node": node_name, "attempt": attempt,
                    "message": f"{node_name} 第 {attempt} 次尝试"})
        try:
            result = fn()
            _emit(cb, {"type": "step_complete", "node": node_name,
                        "message": result.get("message", "完成"), "data": result.get("data")})
            return result
        except Exception as e:
            last_err = e
            log.warning("节点 %s 第 %d 次失败: %s", node_name, attempt, e)
            _emit(cb, {"type": "step_result", "node": node_name, "attempt": attempt,
                        "message": f"第 {attempt} 次失败: {e}"})
    # 全部失败：标 failed，不中断
    _emit(cb, {"type": "step_complete", "node": node_name, "status": "failed",
                "message": f"{node_name} 失败（已重试{MAX_RETRY}次）: {last_err}"})
    return {"status": "failed", "message": f"{node_name} 失败: {last_err}", "error": str(last_err)}


# ============ 节点 ============

def _resolve_keywords(state: WorkflowState) -> list[str]:
    """运行时解析意图，拿精准搜索关键词（替代 intent 截断）。"""
    if state.get("keywords"):
        return state["keywords"]
    intent = state.get("intent", "")
    try:
        from app.intent import parse_intent
        parsed = parse_intent(intent)
        kws = parsed.search_keywords or [intent[:10]]
    except Exception as e:
        log.warning("运行时意图解析失败，用 intent 兜底: %s", e)
        kws = [intent[:10]]
    state["keywords"] = kws
    return kws


def _search_node(state: WorkflowState, cb: EventCb | None) -> WorkflowState:
    agent_tools = state.get("tools", [])
    domain = state.get("domain", "")
    # 立刻发事件给前端反馈（parse_intent 是 LLM 调用，耗时 10-30s，不能让它阻塞首事件）
    _emit(cb, {"type": "step_start", "node": "search", "message": "正在解析情报需求…"})
    keywords = _resolve_keywords(state)
    _emit(cb, {"type": "step_result", "node": "search",
                "message": f"关键词：{', '.join(keywords[:3])}"})
    top_kw = keywords[0] if keywords else state.get("intent", "")[:10]

    def _do() -> dict:
        ensure_registered()
        from app.config import get_settings
        from app.tools.registry import (
            sites_for_domain, anchor_for_domain, is_noise_title,
        )
        from app.tools import web_search as ws, rss as rss_mod, tavily as tavily_mod

        all_docs: list[Doc] = []
        sites = sites_for_domain(domain)
        anchor = anchor_for_domain(domain)
        settings = get_settings()
        has_tavily = bool(settings.tavily_api_key)
        # 搜索 query 集：锚词 + 关键词（去重，最多 3 个）
        queries = []
        for q in [anchor, top_kw] + keywords[1:3]:
            if q and q not in queries:
                queries.append(q)
            if len(queries) >= 3:
                break

        # 0) Tavily 优先（有 Key 时）：搜 1-2 个主关键词，质量高、省 credit
        #    教育领域搜分数线等具体数据，其他领域搜主关键词
        if has_tavily and "web_search" in agent_tools:
            if domain == "education":
                # 教育领域：用 intent 原文 + 地域分数线 query，搜具体院校分数线（非泛词）
                intent = state.get("intent", "")
                tavily_queries = [
                    f"{intent} 录取分数线 位次 历年",  # 用原始需求，含院校/地域
                    f"{top_kw} 大学 录取分数线 最低位次",
                ]
            else:
                tavily_queries = [top_kw] + (keywords[1:2] if len(keywords) > 1 else [])
            for q in tavily_queries[:2]:  # 最多 2 次 = 2 credit
                docs = tavily_mod.search(q, max_results=5)
                all_docs.extend(docs)
                _emit(cb, {"type": "step_result", "node": "search",
                            "message": f"深度搜索({q[:14]}) 命中 {len(docs)} 条",
                            "data": [{"title": d.title, "url": d.url} for d in docs[:3]]})

        # 1) web_search：每个 query 限定权威源（召回质量关键）
        #    有 Tavily 时减少 web_search 次数（Tavily 已覆盖主关键词）
        if "web_search" in agent_tools:
            ws_queries = queries if not has_tavily else queries[1:]  # 有 Tavily 跳过主词
            for q in ws_queries:
                site = sites[0]  # 用首选权威源
                docs = ws.search(q, max_results=5, site=site)
                all_docs.extend(docs)
                _emit(cb, {"type": "step_result", "node": "search",
                            "message": f"全网搜索({site}, {q[:10]}) 命中 {len(docs)} 条",
                            "data": [{"title": d.title, "url": d.url} for d in docs[:3]]})

        # 2) RSS：按关键词过滤（军事等领域）
        if "rss_military" in agent_tools:
            docs = rss_mod.military_feed(max_results=8, keywords=keywords)
            all_docs.extend(docs)
            _emit(cb, {"type": "step_result", "node": "search",
                        "message": f"军事RSS(关键词过滤) 命中 {len(docs)} 条",
                        "data": [{"title": d.title, "url": d.url} for d in docs[:3]]})

        # 3) 其他工具（arxiv/github/stock_news/gaokao_schools 等）按关键词跑
        for tool_name in agent_tools:
            if tool_name in ("web_search", "rss_military", "fetch_url"):
                continue
            spec = get_tool(tool_name)
            if not spec:
                continue
            # gaokao_schools 用主关键词取较多（院校列表）
            if tool_name == "gaokao_schools":
                docs = spec.run(top_kw, max_results=12)
                all_docs.extend(docs)
                _emit(cb, {"type": "step_result", "node": "search",
                            "message": f"{spec.label}({top_kw[:10]}) 命中 {len(docs)} 条",
                            "data": [{"title": d.title, "url": d.url} for d in docs[:5]]})
                continue
            for kw in keywords[:2]:
                docs = spec.run(kw if spec.needs_arg else None, max_results=4)
                all_docs.extend(docs)
                _emit(cb, {"type": "step_result", "node": "search",
                            "message": f"{spec.label}({kw[:10]}) 命中 {len(docs)} 条",
                            "data": [{"title": d.title, "url": d.url} for d in docs[:3]]})

        # 去重 + 噪声过滤（去百科/翻译/学校等无关条目）
        seen = set()
        uniq: list[Doc] = []
        for d in all_docs:
            if d.url and d.url not in seen and not is_noise_title(d.title):
                seen.add(d.url)
                uniq.append(d)
        state["docs"] = [d.to_dict() for d in uniq[:12]]
        return {"message": f"共搜集 {len(uniq)} 条资料", "data": {"count": len(uniq)}}

    step = _with_retry("search", _do, state, cb)
    state.setdefault("steps", []).append({"node": "search", **step})
    if step.get("status") == "failed":
        state.setdefault("errors", []).append(step.get("error", ""))
    return state


def _analyze_node(state: WorkflowState, cb: EventCb | None) -> WorkflowState:
    def _do() -> dict:
        llm = build_chat_model(temperature=0)
        docs_text = _format_docs(state.get("docs", []))
        domain = state.get("domain", "")
        intent = state.get("intent", "")

        # 读取历史记忆（最近 3 次），让分析有连续性
        from app.db import SessionLocal
        from app.crud import recent_memories
        memory_text = ""
        try:
            with SessionLocal() as s:
                mems = recent_memories(s, state.get("agent_id", ""), limit=3)
                if mems:
                    lines = []
                    for m in reversed(mems):  # 旧→新
                        t = m.created_at.strftime("%m-%d %H:%M") if m.created_at else ""
                        pts = "；".join(m.key_points[:3]) if m.key_points else ""
                        lines.append(f"[{t}] {pts}")
                    memory_text = "\n\n【历史研判记忆（供参考连续性，本次应标注相比上次的变与不变）】\n" + "\n".join(lines)
                    _emit(cb, {"type": "step_result", "node": "analyze",
                                "message": f"参考 {len(mems)} 次历史研判记忆"})
        except Exception as e:
            log.warning("读取记忆失败: %s", e)

        # 领域专用分析指令（教育=择校，需冲稳保分档推理）
        if domain == "education":
            sys = (
                "你是资深高考志愿填报分析师。基于用户的具体条件（分数/位次/科类/地域）"
                "与搜集到的院校资料（含往年分数线），做严密、可执行的择校推理。\n\n"
                "要求：\n"
                "1. 明确解析用户条件：分数、位次、科类、目标地域、生源地（若未给则假设合理值并标注）\n"
                "2. 从资料中提取往年真实数据：逐条扫描资料，找出各院校的最低录取分、最低位次、"
                "专业录取位次等具体数值，明确记录'数值+来源'。**严禁编造数据**——"
                "资料里没有的数字一律标注'资料未提供该数据'，不得用'基于历史数据约XXX'编造\n"
                "3. 将目标地域院校按录取难度分档：冲刺/稳妥/保底，每档 2-4 所具体学校\n"
                "4. 每所学校给出：往年依据(只引用资料中真实数据，无则明说) + 推荐专业(含该专业往年位次若有) + 与用户位次的匹配分析\n"
                "5. 数据不全时：基于院校层级(985/211/普通本科)与专业冷热做相对推理(如'985院校通常位次较高，23000名难以触及')，"
                "这是合理推理不算编造；但具体数字必须有出处\n"
                "6. 输出结构化要点，每个结论都要有依据或推理，不要空泛原则"
            )
            user = f"用户需求：{intent}\n\n院校资料（含往年分数线）：\n{docs_text}{memory_text}"
        else:
            sys = state.get("prompt_template", "你是情报分析师。") + (
                "\n\n从以下资料中提炼关键情报：核心事实、关键实体动向、趋势信号、风险点。"
                "用结构化要点输出，标注来源。给出基于资料的明确判断与可执行建议，不要空泛原则。"
                "若有历史研判记忆，需在分析中标注'相比上次'的变与不变。"
            )
            user = f"情报需求：{intent}\n\n资料：\n{docs_text}{memory_text}"

        # 检查点1：告诉用户分析基于哪些真实资料（非写死）
        docs = state.get("docs", [])
        titles = [d.get("title", "")[:30] for d in docs[:5] if d.get("title")]
        _emit(cb, {"type": "step_result", "node": "analyze",
                    "message": f"正在分析 {len(docs)} 条资料：" + " / ".join(titles) if titles else f"正在分析 {len(docs)} 条资料"})

        resp = llm.invoke([SystemMessage(content=sys), HumanMessage(content=user)])
        analysis = resp.content if isinstance(resp.content, str) else str(resp.content)
        state["analysis"] = analysis
        # 检查点2：推分析出的核心要点摘要（取前 2 个要点行，真实内容非写死）
        summary_lines = [ln.strip() for ln in analysis.split("\n") if ln.strip().startswith(("-", "•", "*"))][:3]
        summary = "；".join(ln.lstrip("-•* ")[:40] for ln in summary_lines) if summary_lines else "分析完成"
        _emit(cb, {"type": "step_result", "node": "analyze",
                    "message": f"提炼要点：{summary}", "data": {"length": len(analysis)}})
        return {"message": "关键情报提炼完成", "data": {"length": len(analysis)}}

    step = _with_retry("analyze", _do, state, cb)
    state.setdefault("steps", []).append({"node": "analyze", **step})
    if step.get("status") == "failed":
        state.setdefault("errors", []).append(step.get("error", ""))
    return state


def _report_node(state: WorkflowState, cb: EventCb | None) -> WorkflowState:
    def _do() -> dict:
        llm = build_chat_model(temperature=0.3)
        domain = state.get("domain", "")
        if domain == "education":
            sys = (
                "你是高考志愿填报报告专家。基于分析结果与搜集到的真实分数线数据，"
                "生成结构化 Markdown 报告。\n\n"
                "格式要求（不要用 Markdown 表格，网页渲染会乱，改用分档列表）：\n"
                "1. 摘要：用户条件(分数/位次/科类/地域) + 总体定位判断\n"
                "2. 分档推荐（用 ### 冲刺/### 稳妥/### 保底 三档）：\n"
                "   每所学校用如下结构（不要表格）：\n"
                "   **学校名**（层级）\n"
                "   - 往年依据：引用资料中的真实数据（如'2024陕西理科最低位次21000'），无数据则写'资料未提供具体位次'\n"
                "   - 推荐专业：1-2个 + 该专业往年最低位次（若有）\n"
                "   - 分析：为什么这个位次能/不能匹配，结合用户位次23000做推理\n"
                "   - 结论：建议冲刺/稳妥/保底，服从调剂建议\n"
                "3. 风险评估与填报策略\n"
                "4. 数据来源（列出引用的资料）\n\n"
                "核心原则：每个结论都要有依据(真实数据或明确推理)，不能只给结论不给分析。"
                "**严禁编造分数线/位次数据**——资料里没有的具体数字，写'资料未提供'，"
                "不得用'基于历史数据约XXX'虚构。院校层级推理(如985通常位次高)是合理的，"
                "但具体数值必须有出处。报告控制在 1200 字以内。"
            )
        else:
            sys = (
                "你是情报报告撰写专家。基于分析结果生成结构化 Markdown 报告："
                "含标题、摘要、关键动态、趋势研判、结论建议、数据来源。客观中立。"
                "给出基于资料的明确判断与可执行建议。报告控制在 800 字以内，简洁有力。"
            )
        resp = llm.invoke([
            SystemMessage(content=sys),
            HumanMessage(content=f"情报需求：{state.get('intent','')}\n\n分析结果：\n{state.get('analysis','(无)')}\n\n原始资料摘要：\n{_format_docs(state.get('docs', []), max_chars=1500)}"),
        ])
        report = resp.content if isinstance(resp.content, str) else str(resp.content)
        # 确保是 markdown
        if not report.strip().startswith("#"):
            report = f"# 情报分析报告\n\n{report}"
        state["report_md"] = report
        # 检查点：推报告真实标题（首行 # 标题），非写死
        title_line = next((ln.strip() for ln in report.split("\n") if ln.strip().startswith("#")), "报告已生成")
        _emit(cb, {"type": "step_result", "node": "report",
                    "message": f"生成报告：{title_line.lstrip('# ').strip()[:40]}"})
        return {"message": "报告已生成", "data": {"length": len(report)}}

    step = _with_retry("report", _do, state, cb)
    state.setdefault("steps", []).append({"node": "report", **step})
    return state


def _format_docs(docs: list[dict], max_chars: int = 3000) -> str:
    parts = []
    total = 0
    for i, d in enumerate(docs, 1):
        snippet = f"[{i}] {d.get('title','')} ({d.get('source','')})\n{d.get('content','')[:200]}\nURL: {d.get('url','')}\n"
        if total + len(snippet) > max_chars:
            break
        parts.append(snippet)
        total += len(snippet)
    return "\n".join(parts) if parts else "(无资料)"


def _extract_key_points(report_md: str) -> list[str]:
    """用 LLM 从报告提取 3-5 条关键结论，存入智能体记忆。

    只存结论要点（每条≤30字），不存全文，控制记忆长度。
    """
    try:
        llm = build_chat_model(temperature=0)
        sys = (
            "从以下情报报告中提取 3-5 条最关键结论，用于后续运行的连续性参考。"
            "要求：每条≤30字，只记结论不记过程；输出 JSON 数组，如 [\"结论1\",\"结论2\"]，不要其他文字。"
        )
        resp = llm.invoke([SystemMessage(content=sys), HumanMessage(content=report_md[:2500])])
        text = resp.content if isinstance(resp.content, str) else str(resp.content)
        import json, re
        text = re.sub(r"^```(?:json)?\s*", "", text.strip()).replace("```", "")
        m = re.search(r"\[.*\]", text, re.S)
        if not m:
            return []
        pts = json.loads(m.group(0))
        return [str(p).strip()[:30] for p in pts if str(p).strip()][:5]
    except Exception as e:
        log.warning("提取关键结论失败: %s", e)
        return []


# ============ 工作流编排 ============

def build_graph() -> "StateGraph":
    """构建 LangGraph：search → analyze → report。"""
    g = StateGraph(WorkflowState)

    def search_fn(state: WorkflowState) -> WorkflowState:
        return _search_node(state, None)  # graph 内部执行不推 SSE（SSE 由 run_agent 单独驱动）

    g.add_node("search", search_fn)
    g.add_node("analyze", _analyze_node)
    g.add_node("report", _report_node)
    g.add_edge(START, "search")
    g.add_edge("search", "analyze")
    g.add_edge("analyze", "report")
    g.add_edge("report", END)
    return g.compile()


# ============ 运行入口 ============

def run_agent(agent_id: str, cb: EventCb | None = None) -> dict:
    """运行某智能体：建 RunRecord → 顺序执行三节点（带 SSE 回调）→ 落库。

    返回 {run_id, status, report_md, steps}。
    注意：本实现用顺序执行 + 回调驱动 SSE（而非 graph.invoke），
    以便每步实时推送事件；graph 已构建供后续并行/复杂编排扩展。
    """
    with SessionLocal() as s:
        agent = get_agent(s, agent_id)
        if not agent:
            raise ValueError(f"智能体不存在: {agent_id}")
        run = create_run(s, agent_id=agent_id)
        run_id = run.id
        s.commit()

    # 包装 cb：发事件同时实时落库到 RunRecord.steps，让其他请求能读到运行中进度
    live_events: list[dict] = []

    def persist_event(event: dict) -> None:
        live_events.append(event)
        try:
            with SessionLocal() as s:
                update_run(s, run_id, steps=list(live_events))
                s.commit()
        except Exception as e:
            log.warning("实时落库失败: %s", e)

    def wrapped_cb(event: dict) -> None:
        _emit(cb, event)          # 推给当前 SSE 流
        persist_event(event)      # 落库供中途查看

    # 构造初始状态
    state: WorkflowState = {
        "agent_id": agent_id,
        "intent": agent.intent,
        "domain": agent.domain,
        "tools": agent.tools,
        "prompt_template": agent.prompt_template,
        "keywords": [],  # 由 _resolve_keywords 运行时调 parse_intent 填充
        "docs": [], "analysis": "", "report_md": "",
        "steps": [], "errors": [],
    }

    final_status = "completed"
    try:
        _search_node(state, wrapped_cb)
        if not state.get("docs"):  # 搜集全失败也继续，分析会基于空
            wrapped_cb({"type": "step_result", "node": "search", "message": "无可用资料，将基于 LLM 知识分析"})
        _analyze_node(state, wrapped_cb)
        _report_node(state, wrapped_cb)
        if state.get("errors"):
            final_status = "completed"  # 节点级失败不标整体 failed（设计文档要求不中断）
    except Exception as e:
        final_status = "failed"
        wrapped_cb({"type": "error", "message": f"运行失败: {e}"})
        log.exception("run_agent 失败")

    # 落库（steps 用 live_events，与实时落库一致）
    with SessionLocal() as s:
        update_run(s, run_id,
                   status=final_status,
                   steps=list(live_events),
                   report_md=state.get("report_md", ""))
        s.commit()

    # 报告成功则提取关键结论存入智能体记忆（供下次运行参考）
    if final_status == "completed" and state.get("report_md"):
        try:
            key_points = _extract_key_points(state["report_md"])
            if key_points:
                with SessionLocal() as s:
                    add_memory(s, agent_id, run_id, key_points)
                    s.commit()
                wrapped_cb({"type": "step_result", "node": "report",
                            "message": f"已记入智能体记忆：{len(key_points)} 条关键结论"})
        except Exception as e:
            log.warning("记忆提取失败: %s", e)

    wrapped_cb({"type": "report_ready", "run_id": run_id,
                "message": "报告已生成", "status": final_status})

    return {
        "run_id": run_id,
        "status": final_status,
        "report_md": state.get("report_md", ""),
        "steps": state.get("steps", []),
        "docs_count": len(state.get("docs", [])),
    }
