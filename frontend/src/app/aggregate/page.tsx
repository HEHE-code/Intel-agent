"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { DOMAIN_META, api, type AggregateSummary, type Agent } from "@/lib/api";
import Markdown from "@/components/Markdown";

export default function AggregatePage() {
  const [agents, setAgents] = useState<Agent[]>([]);
  const [selected, setSelected] = useState<string[]>([]);
  const [theme, setTheme] = useState("");
  const [name, setName] = useState("");
  const [list, setList] = useState<AggregateSummary[]>([]);
  const [creating, setCreating] = useState(false);
  const [error, setError] = useState("");

  const load = async () => {
    try {
      const [a, l] = await Promise.all([
        api<Agent[]>("/api/agents"),
        api<AggregateSummary[]>("/api/aggregate"),
      ]);
      setAgents(a);
      setList(l);
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
    }
  };
  useEffect(() => { load(); }, []);

  const toggle = (id: string) => {
    setSelected((prev) => (prev.includes(id) ? prev.filter((x) => x !== id) : [...prev, id]));
  };

  const create = async () => {
    if (selected.length < 2 || !name.trim()) return;
    setCreating(true);
    setError("");
    try {
      await api("/api/aggregate", {
        method: "POST",
        body: JSON.stringify({ name: name.trim(), agent_ids: selected, theme: theme.trim() }),
      });
      setName(""); setTheme(""); setSelected([]);
      await load();
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
    } finally {
      setCreating(false);
    }
  };

  const agentName = (id: string) => agents.find((a) => a.id === id)?.name || id.slice(0, 8);

  return (
    <div>
      <header className="px-8 py-6 border-b border-borderc">
        <h1 className="text-xl font-semibold">综合研判</h1>
        <p className="text-sm text-muted mt-0.5">
          选多个智能体，AI 跨领域交叉印证，产出综合情报报告
        </p>
      </header>

      <div className="px-8 py-6 space-y-6">
        {/* 新建综合研判 */}
        <div className="bg-surface border border-borderc rounded-xl p-5">
          <div className="text-sm font-semibold mb-3">新建综合研判</div>
          <div className="flex gap-2 mb-3">
            <input value={name} onChange={(e) => setName(e.target.value)} placeholder="综合主题名（如：XX公司投资价值评估）"
              className="flex-1 bg-surface-2 border border-borderc rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-ring" />
            <input value={theme} onChange={(e) => setTheme(e.target.value)} placeholder="分析重点（可选）"
              className="w-64 bg-surface-2 border border-borderc rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-ring" />
          </div>
          <div className="text-xs text-muted mb-2">选择智能体（至少 2 个，取各自最新报告综合）：</div>
          <div className="grid grid-cols-2 md:grid-cols-3 gap-2 mb-3 max-h-48 overflow-y-auto">
            {agents.map((a) => {
              const checked = selected.includes(a.id);
              const d = DOMAIN_META[a.domain] || { label: a.domain, color: "#64748B" };
              return (
                <label key={a.id} className={`flex items-center gap-2 p-2 rounded-lg border cursor-pointer text-xs ${checked ? "border-primary bg-primary/5" : "border-borderc"}`}>
                  <input type="checkbox" checked={checked} onChange={() => toggle(a.id)} className="accent-primary" />
                  <span className="px-1.5 py-0.5 rounded font-mono text-[10px]" style={{ background: `${d.color}22`, color: d.color }}>{d.label}</span>
                  <span className="truncate">{a.name}</span>
                </label>
              );
            })}
          </div>
          <div className="flex items-center gap-3">
            <button onClick={create} disabled={creating || selected.length < 2 || !name.trim()}
              className="bg-primary text-on-primary px-4 py-2 rounded-lg text-sm font-medium hover:opacity-90 disabled:opacity-50 disabled:cursor-not-allowed">
              {creating ? "创建中…" : `✦ 开始综合（${selected.length}）`}
            </button>
            <span className="text-xs text-muted">{selected.length < 2 ? "至少选 2 个智能体" : ""}</span>
          </div>
          {error && <div className="mt-3 text-xs text-failed">{error}</div>}
        </div>

        {/* 历史综合研判 */}
        <div>
          <h2 className="text-sm font-semibold text-muted mb-3">历史综合研判</h2>
          {list.length === 0 ? (
            <div className="bg-surface border border-borderc rounded-xl p-8 text-center text-sm text-muted">
              还没有综合研判任务
            </div>
          ) : (
            <div className="bg-surface border border-borderc rounded-xl overflow-hidden divide-y divide-borderc">
              {list.map((a) => (
                <AggregateRow key={a.id} agg={a} agentName={agentName} />
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

function AggregateRow({ agg, agentName }: { agg: AggregateSummary; agentName: (id: string) => string }) {
  const [open, setOpen] = useState(false);
  const [report, setReport] = useState("");
  const time = agg.created_at.slice(0, 16).replace("T", " ");
  const names = agg.agent_ids.map(agentName).join(" + ");

  const view = async () => {
    if (open) { setOpen(false); return; }
    setOpen(true);
    if (!report && agg.status === "completed") {
      try {
        const d = await api<{ report_md: string }>(`/api/aggregate/${agg.id}`);
        setReport(d.report_md);
      } catch {}
    }
  };

  return (
    <div>
      <button onClick={view} className="w-full p-4 flex items-center gap-3 hover:bg-surface-2 text-left">
        <span className={`w-2 h-2 rounded-full shrink-0 ${agg.status === "completed" ? "bg-done" : agg.status === "running" ? "bg-running animate-pulse" : "bg-failed"}`} />
        <div className="flex-1 min-w-0">
          <div className="text-sm font-medium">{agg.name}</div>
          <div className="text-xs text-muted mt-0.5 truncate">{names}</div>
        </div>
        <span className="text-[11px] text-muted font-mono shrink-0">{time}</span>
        <span className="text-xs text-muted shrink-0">{agg.status === "completed" ? `${agg.report_length}字` : agg.status === "running" ? "综合中…" : "失败"}</span>
      </button>
      {open && report && (
        <div className="px-8 pb-6">
          <article className="bg-surface border border-borderc rounded-xl p-6">
            <Markdown content={report} />
          </article>
        </div>
      )}
    </div>
  );
}
