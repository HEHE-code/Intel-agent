"use client";

import Link from "next/link";
import { useMemo, useState } from "react";
import { DOMAIN_META, STATUS_META, type ReportSummary } from "@/lib/api";

export default function ReportsList({ reports }: { reports: ReportSummary[] }) {
  const [query, setQuery] = useState("");
  const [agentFilter, setAgentFilter] = useState("");
  const [domainFilter, setDomainFilter] = useState("");
  const [statusFilter, setStatusFilter] = useState("");

  // 智能体选项（去重）
  const agents = useMemo(() => {
    const m = new Map<string, string>();
    reports.forEach((r) => { if (r.agent_name) m.set(r.agent_id, r.agent_name); });
    return [...m.entries()];
  }, [reports]);

  // 筛选
  const shown = reports.filter((r) => {
    if (agentFilter && r.agent_id !== agentFilter) return false;
    if (domainFilter && r.domain !== domainFilter) return false;
    if (statusFilter && r.status !== statusFilter) return false;
    if (query) {
      const q = query.toLowerCase();
      const hay = `${r.agent_name || ""} ${r.preview || ""}`.toLowerCase();
      if (!hay.includes(q)) return false;
    }
    return true;
  });

  const hasFilter = query || agentFilter || domainFilter || statusFilter;

  return (
    <>
      {/* 搜索 + 筛选条 */}
      <div className="flex flex-wrap items-center gap-2 mb-4">
        <input
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          placeholder="搜索报告内容/智能体名…"
          className="bg-surface-2 border border-borderc rounded-lg px-3 py-1.5 text-sm w-56 focus:outline-none focus:ring-2 focus:ring-ring"
        />
        <select
          value={agentFilter}
          onChange={(e) => setAgentFilter(e.target.value)}
          className="bg-surface-2 border border-borderc rounded-lg px-2 py-1.5 text-xs"
        >
          <option value="">全部智能体</option>
          {agents.map(([id, name]) => <option key={id} value={id}>{name}</option>)}
        </select>
        <select
          value={domainFilter}
          onChange={(e) => setDomainFilter(e.target.value)}
          className="bg-surface-2 border border-borderc rounded-lg px-2 py-1.5 text-xs"
        >
          <option value="">全部领域</option>
          {Object.entries(DOMAIN_META).map(([k, d]) => <option key={k} value={k}>{d.label}</option>)}
        </select>
        <select
          value={statusFilter}
          onChange={(e) => setStatusFilter(e.target.value)}
          className="bg-surface-2 border border-borderc rounded-lg px-2 py-1.5 text-xs"
        >
          <option value="">全部状态</option>
          <option value="completed">已完成</option>
          <option value="failed">失败</option>
          <option value="running">运行中</option>
        </select>
        <span className="text-xs text-muted ml-auto">
          {hasFilter ? `命中 ${shown.length} / ${reports.length}` : `共 ${reports.length} 份`}
        </span>
        {hasFilter && (
          <button
            onClick={() => { setQuery(""); setAgentFilter(""); setDomainFilter(""); setStatusFilter(""); }}
            className="text-xs text-muted hover:text-primary cursor-pointer"
          >
            清除
          </button>
        )}
      </div>

      {shown.length === 0 ? (
        <div className="bg-surface border border-borderc rounded-xl p-10 text-center text-sm text-muted">
          {hasFilter ? "没有匹配的报告，试试清除筛选" : "还没有报告"}
        </div>
      ) : (
        <div className="bg-surface border border-borderc rounded-xl overflow-hidden divide-y divide-borderc">
          {shown.map((r) => {
            const s = STATUS_META[r.status] || STATUS_META.idle;
            const d = r.domain ? DOMAIN_META[r.domain] : null;
            const time = r.created_at.slice(0, 16).replace("T", " ");
            return (
              <Link
                key={r.id}
                href={`/reports/${r.id}`}
                className="p-4 flex items-center gap-3 hover:bg-surface-2 transition-colors"
              >
                <span className="w-2 h-2 rounded-full shrink-0" style={{ background: s.dot }} />
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2">
                    {d && (
                      <span
                        className="px-1.5 py-0.5 rounded text-[10px] font-medium font-mono shrink-0"
                        style={{ background: `${d.color}22`, color: d.color }}
                      >
                        {d.label}
                      </span>
                    )}
                    <span className="text-sm font-medium truncate">{r.agent_name || "智能体"}</span>
                    <span className="text-[11px] text-muted font-mono shrink-0">{time}</span>
                  </div>
                  <div className="text-xs text-muted mt-1 truncate">{r.preview || "(无预览)"}</div>
                </div>
                <span className="text-[11px] text-muted font-mono shrink-0">{r.report_length}字</span>
                <span className="text-xs text-muted shrink-0">{s.text}</span>
                <span className="text-muted">›</span>
              </Link>
            );
          })}
        </div>
      )}
    </>
  );
}
