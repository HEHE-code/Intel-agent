"""多智能体协同 —— 取各智能体最新报告，LLM 综合研判。

不同于单智能体工作流（搜集→分析→结论），聚合是：
取 N 个智能体的最新报告 → LLM 交叉印证综合分析 → 综合报告。
"""
from __future__ import annotations

import logging

from langchain_core.messages import HumanMessage, SystemMessage

from app.crud import (
    create_aggregate, get_aggregate, latest_report_md_for_agent, update_aggregate,
)
from app.db import SessionLocal
from app.llm import build_chat_model

log = logging.getLogger(__name__)


def run_aggregate(agg_id: str) -> dict:
    """执行综合研判：取各智能体最新报告 → LLM 综合 → 存综合报告。"""
    with SessionLocal() as s:
        agg = get_aggregate(s, agg_id)
        if not agg:
            raise ValueError("聚合任务不存在")
        agent_ids = list(agg.agent_ids or [])
        theme = agg.theme or ""

    # 取各智能体最新报告
    reports: list[tuple[str, str]] = []  # (agent_name, md)
    missing: list[str] = []
    with SessionLocal() as s:
        for aid in agent_ids:
            md, name = latest_report_md_for_agent(s, aid)
            if md:
                reports.append((name, md[:2000]))  # 各取摘要控 token
            else:
                missing.append(name)

    if not reports:
        with SessionLocal() as s:
            update_aggregate(s, agg_id, status="failed", report_md="（无可用报告：所选智能体均无已完成报告）")
            s.commit()
        return {"status": "failed", "report_md": "无可用报告"}

    # 拼 LLM 输入
    parts = []
    for i, (name, md) in enumerate(reports, 1):
        parts.append(f"=== 报告{i}：{name} ===\n{md}")
    reports_text = "\n\n".join(parts)
    missing_hint = f"\n\n（注：{', '.join(missing)} 暂无已完成报告，未纳入综合）" if missing else ""

    sys = (
        "你是高级情报综合分析师。基于多份单领域情报报告，做跨领域交叉印证与综合研判。"
        "要求：\n"
        "1. 不要简单拼接各报告，要找它们之间的关联、印证、矛盾、合力\n"
        "2. 围绕综合主题，提炼整体态势判断（如多角度如何指向同一结论）\n"
        "3. 标注交叉印证点（如'财务报告的XX与舆情报告的YY相互印证'）\n"
        "4. 指出各角度的盲区与互补\n"
        "5. 给出综合结论与建议\n"
        "6. 输出结构化 Markdown 报告（含综合摘要/交叉印证/整体态势/综合结论/数据来源）\n"
        "7. 严禁编造，只基于提供的报告内容\n"
        "8. 控制在 1200 字内"
    )
    user = f"综合主题：{theme or '（未指定，请根据报告自行提炼）'}\n\n{reports_text}{missing_hint}"

    try:
        llm = build_chat_model(temperature=0.3)
        resp = llm.invoke([SystemMessage(content=sys), HumanMessage(content=user)])
        report = resp.content if isinstance(resp.content, str) else str(resp.content)
        if not report.strip().startswith("#"):
            report = f"# 综合研判报告：{theme or '多领域情报综合'}\n\n{report}"
        with SessionLocal() as s:
            update_aggregate(s, agg_id, status="completed", report_md=report)
            s.commit()
        return {"status": "completed", "report_md": report}
    except Exception as e:
        log.exception("综合研判失败")
        with SessionLocal() as s:
            update_aggregate(s, agg_id, status="failed", report_md=f"（综合研判失败：{e}）")
            s.commit()
        return {"status": "failed", "report_md": str(e)}
