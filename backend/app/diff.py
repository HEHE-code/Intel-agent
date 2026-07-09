"""报告对比：段落级 diff。

按 ## 切段，用 difflib.SequenceMatcher 对齐段落，
标记新增/删除/未变/改动。
"""
from __future__ import annotations

import difflib
import re


def split_sections(md: str) -> list[dict]:
    """把 Markdown 按 ## 或 ### 切段，返回 [{title, content}]。

    第一个标题之前的内容作为"前言"段。
    """
    if not md:
        return []
    lines = md.split("\n")
    sections: list[dict] = []
    current_title = ""
    current_lines: list[str] = []

    for ln in lines:
        m = re.match(r"^(#{2,3})\s+(.+)$", ln)
        if m:
            if current_title or current_lines:
                sections.append({
                    "title": current_title,
                    "content": "\n".join(current_lines).strip(),
                })
            current_title = m.group(2).strip()
            current_lines = []
        else:
            current_lines.append(ln)
    if current_title or current_lines:
        sections.append({
            "title": current_title,
            "content": "\n".join(current_lines).strip(),
        })
    return sections


def diff_reports(left_md: str, right_md: str) -> dict:
    """对比两份报告，返回结构化 diff。

    返回：{left_meta_hint, right_meta_hint, sections: [...]}
    每个 section: {title, status: added/removed/unchanged/changed, left, right}
    """
    left = split_sections(left_md)
    right = split_sections(right_md)

    # 用标题对齐段落（标题相同的视为同一段做内容 diff）
    left_map = {s["title"]: s["content"] for s in left}
    right_titles = [s["title"] for s in right]

    result: list[dict] = []
    # 顺序：按 left 顺序 + right 中新增的
    seen = set()
    for s in left:
        title = s["title"]
        if title in right_titles:
            r_content = left_map  # 占位
            r_content = next((rs["content"] for rs in right if rs["title"] == title), "")
            ratio = difflib.SequenceMatcher(None, s["content"], r_content).ratio()
            status = "unchanged" if ratio > 0.95 else "changed"
            result.append({
                "title": title, "status": status,
                "left": s["content"], "right": r_content,
                "similarity": round(ratio, 2),
                "line_diff": line_diff(s["content"], r_content) if status == "changed" else None,
            })
            seen.add(title)
        else:
            result.append({
                "title": title, "status": "removed",
                "left": s["content"], "right": "",
            })
    # right 中有但 left 没有的（新增段）
    for s in right:
        if s["title"] not in seen:
            result.append({
                "title": s["title"], "status": "added",
                "left": "", "right": s["content"],
            })

    return {"sections": result}


def line_diff(left_text: str, right_text: str) -> list[dict]:
    """两段文本的行级 diff，返回 [{type, content}]。

    type: 'added'(右有左无)/'removed'(左有右无)/'unchanged'
    用 difflib.ndiff 逐行比对。
    """
    left_lines = left_text.split("\n") if left_text else []
    right_lines = right_text.split("\n") if right_text else []
    result: list[dict] = []
    for d in difflib.ndiff(left_lines, right_lines):
        if d.startswith("+ "):
            result.append({"type": "added", "content": d[2:]})
        elif d.startswith("- "):
            result.append({"type": "removed", "content": d[2:]})
        elif d.startswith("  "):
            result.append({"type": "unchanged", "content": d[2:]})
        # '? ' 行（差异标记）跳过
    return result


def summarize_diff(left_md: str, right_md: str) -> str:
    """用 LLM 生成两份报告的变化摘要：新增/删除/结论变化。

    严禁编造——只基于两份报告实际内容总结差异。
    """
    from app.llm import build_chat_model, LLMNotConfiguredError
    from langchain_core.messages import HumanMessage, SystemMessage

    sys = (
        "你是情报报告对比分析师。对比两份报告（左=旧，右=新），"
        "输出本次运行相比上次的**实质变化摘要**。\n\n"
        "要求：\n"
        "1. 新增了什么动态/数据（右报告有、左报告没有）\n"
        "2. 删除了什么（左报告有、右报告没有）\n"
        "3. 结论/研判有何变化（立场变了吗？风险判断变了吗？）\n"
        "4. 只总结真实差异，不要复述报告内容，不要编造\n"
        "5. 用要点输出，每条标注[新增]/[删除]/[变化]\n"
        "6. 若无实质变化则直说'两份报告内容基本一致'"
    )
    user = f"【左报告（旧）】\n{left_md[:3000]}\n\n【右报告（新）】\n{right_md[:3000]}"
    try:
        llm = build_chat_model(temperature=0)
        resp = llm.invoke([SystemMessage(content=sys), HumanMessage(content=user)])
        return resp.content if isinstance(resp.content, str) else str(resp.content)
    except (LLMNotConfiguredError, Exception) as e:
        return f"（LLM 摘要生成失败：{e}）"
