import Link from "next/link";
import { api, type CompareResult } from "@/lib/api";

export const dynamic = "force-dynamic";

const STATUS_META: Record<string, { label: string; color: string; bg: string }> = {
  added: { label: "新增", color: "#22C55E", bg: "rgba(34,197,94,0.10)" },
  removed: { label: "删除", color: "#EF4444", bg: "rgba(239,68,68,0.10)" },
  changed: { label: "改动", color: "#D97706", bg: "rgba(217,119,6,0.10)" },
  unchanged: { label: "未变", color: "#64748B", bg: "transparent" },
};

export default async function ComparePage({
  params,
}: {
  params: Promise<{ a: string; b: string }>;
}) {
  const { a, b } = await params;
  let result: CompareResult | null = null;
  let error = "";
  try {
    result = await api<CompareResult>(`/api/reports/compare/${a}/vs/${b}`);
  } catch (e) {
    error = e instanceof Error ? e.message : String(e);
  }

  if (error || !result) {
    return (
      <div className="p-8">
        <Link href="/reports" className="text-sm text-muted hover:text-primary">
          ← 返回报告
        </Link>
        <div className="mt-4 bg-failed/10 text-failed border border-failed/30 rounded-xl p-4 text-sm">
          对比失败：{error || "未知错误"}
        </div>
      </div>
    );
  }

  const leftTime = result.left.created_at.slice(0, 16).replace("T", " ");
  const rightTime = result.right.created_at.slice(0, 16).replace("T", " ");
  const sections = result.diff.sections;
  const stats = {
    added: sections.filter((s) => s.status === "added").length,
    removed: sections.filter((s) => s.status === "removed").length,
    changed: sections.filter((s) => s.status === "changed").length,
    unchanged: sections.filter((s) => s.status === "unchanged").length,
  };

  return (
    <div>
      <header className="px-8 py-6 border-b border-borderc">
        <div className="flex items-center gap-2 mb-1 text-xs text-muted">
          <Link href="/reports" className="hover:text-primary">← 报告列表</Link>
        </div>
        <h1 className="text-xl font-semibold">报告对比</h1>
        <div className="flex items-center gap-6 mt-2 text-sm">
          <span className="text-muted">
            左：<span className="text-text font-mono">{leftTime}</span>
          </span>
          <span className="text-muted">
            右：<span className="text-text font-mono">{rightTime}</span>
          </span>
        </div>
        <div className="flex gap-3 mt-3 text-xs">
          <Stat n={stats.added} label="新增" color="#22C55E" />
          <Stat n={stats.removed} label="删除" color="#EF4444" />
          <Stat n={stats.changed} label="改动" color="#D97706" />
          <Stat n={stats.unchanged} label="未变" color="#64748B" />
        </div>
      </header>

      <div className="px-8 py-6 space-y-6">
        {/* LLM 变化摘要 */}
        {result.summary && (
          <div className="bg-surface border border-borderc rounded-xl p-5">
            <div className="flex items-center gap-2 mb-3">
              <span className="text-sm font-semibold">✦ 变化摘要</span>
              <span className="text-[11px] text-muted">AI 对比两份报告的实质变化</span>
            </div>
            <div className="text-sm whitespace-pre-wrap leading-relaxed">{result.summary}</div>
          </div>
        )}

        {/* 段落级 diff */}
        {sections.length === 0 ? (
          <div className="text-sm text-muted">无可对比段落</div>
        ) : (
          <div className="space-y-4">
            {sections.map((sec, i) => {
              const m = STATUS_META[sec.status];
              return (
                <div key={i} className="border border-borderc rounded-xl overflow-hidden">
                  <div className="flex items-center gap-2 px-4 py-2 border-b border-borderc bg-surface-2">
                    <span
                      className="px-2 py-0.5 rounded text-[11px] font-medium font-mono"
                      style={{ background: `${m.color}22`, color: m.color }}
                    >
                      {m.label}
                    </span>
                    <span className="text-sm font-medium">{sec.title || "(前言)"}</span>
                    {sec.similarity !== undefined && (
                      <span className="text-[11px] text-muted ml-auto font-mono">
                        相似度 {(sec.similarity * 100).toFixed(0)}%
                      </span>
                    )}
                  </div>
                  {/* changed 段：行级 diff 高亮；其他：直接显示内容 */}
                  {sec.status === "changed" && sec.line_diff ? (
                    <div className="p-3 font-mono text-xs leading-relaxed">
                      {sec.line_diff.map((ln, j) => (
                        <div
                          key={j}
                          className="px-2 py-0.5"
                          style={
                            ln.type === "added"
                              ? { background: "rgba(34,197,94,0.15)", color: "#22C55E" }
                              : ln.type === "removed"
                              ? { background: "rgba(239,68,68,0.15)", color: "#EF4444" }
                              : { color: "var(--text-muted)" }
                          }
                        >
                          <span className="select-none mr-2">
                            {ln.type === "added" ? "+" : ln.type === "removed" ? "-" : " "}
                          </span>
                          {ln.content || " "}
                        </div>
                      ))}
                    </div>
                  ) : (
                    <div className="p-4 text-xs whitespace-pre-wrap leading-relaxed">
                      {sec.right || sec.left || <span className="text-muted">（无）</span>}
                    </div>
                  )}
                </div>
              );
            })}
          </div>
        )}
      </div>
    </div>
  );
}

function Stat({ n, label, color }: { n: number; label: string; color: string }) {
  return (
    <span className="flex items-center gap-1.5 px-2 py-1 rounded" style={{ background: `${color}15` }}>
      <span className="w-1.5 h-1.5 rounded-full" style={{ background: color }} />
      <span style={{ color }}>{n}</span>
      <span className="text-muted">{label}</span>
    </span>
  );
}
