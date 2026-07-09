"use client";

import { use, useEffect, useRef, useState } from "react";
import Link from "next/link";
import ScheduleSection from "@/components/ScheduleSection";
import DeleteAgentButton from "@/components/DeleteAgentButton";
import AgentMemorySection from "@/components/AgentMemorySection";
import {
  DOMAIN_META,
  STATUS_META,
  api,
  runAgentStream,
  type Agent,
  type ReportSummary,
  type SSEEvent,
} from "@/lib/api";

const NODE_LABEL: Record<string, string> = {
  search: "搜集",
  analyze: "分析",
  report: "结论",
};

export default function AgentDetailPage({
  params,
}: {
  params: Promise<{ id: string }>;
}) {
  const { id } = use(params);
  const [agent, setAgent] = useState<Agent | null>(null);
  const [runs, setRuns] = useState<ReportSummary[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [events, setEvents] = useState<SSEEvent[]>([]);
  const [running, setRunning] = useState(false);
  const [done, setDone] = useState(false);
  const [selected, setSelected] = useState<string[]>([]); // 历史运行多选（对比用）
  const runningRef = useRef(false);
  useEffect(() => { runningRef.current = running; }, [running]);

  const toggleSelect = (id: string) => {
    setSelected((prev) =>
      prev.includes(id) ? prev.filter((x) => x !== id)
      : prev.length >= 2 ? [prev[1], id]  // 最多选2个，超出替换最旧
      : [...prev, id]
    );
  };

  const load = async (poll = false) => {
    if (!poll) setLoading(true);
    try {
      const [a, rs, active] = await Promise.all([
        api<Agent>(`/api/agents/${id}`),
        api<ReportSummary[]>(`/api/reports`).then((all) =>
          all.filter((r) => r.agent_id === id)
        ),
        api<{ active: boolean; events?: any[] }>(`/api/agents/${id}/active-run`),
      ]);
      setAgent(a);
      setRuns(rs);
      // 有活跃运行：回填已发生事件，标记运行中
      if (active.active && active.events) {
        setEvents(active.events);
        setRunning(true);
        setDone(false);
      } else if (poll && runningRef.current) {
        // 轮询中发现运行已结束（之前在跑现在不跑了）
        setRunning(false);
        setDone(true);
        setRuns(rs); // rs 已是最新历史
      } else if (!poll) {
        setRunning(false);
      }
      setError("");
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
    } finally {
      if (!poll) setLoading(false);
    }
  };

  useEffect(() => {
    load();
    // 轮询：只要 running 为真就持续刷新（刷新页面后也能恢复轮询）
    const timer = setInterval(() => {
      if (runningRef.current) load(true);
    }, 2000);
    return () => clearInterval(timer);
  }, [id]);

  useEffect(() => {
    load();
  }, [id]);

  const run = async () => {
    setRunning(true);
    setDone(false);
    setEvents([]);
    try {
      await runAgentStream(id, (e) => {
        setEvents((prev) => [...prev, e]);
      });
      setDone(true);
      await load(); // 刷新历史运行
    } catch (e) {
      setEvents((prev) => [
        ...prev,
        { type: "error", message: String(e) },
      ]);
    } finally {
      setRunning(false);
    }
  };

  if (loading) return <div className="p-8 text-muted">加载中…</div>;
  if (error || !agent)
    return (
      <div className="p-8">
        <div className="bg-failed/10 text-failed border border-failed/30 rounded-xl p-4 text-sm">
          加载失败：{error || "智能体不存在"}
        </div>
        <Link href="/" className="text-sm text-muted hover:text-primary mt-4 inline-block">
          ← 返回仪表台
        </Link>
      </div>
    );

  const d = DOMAIN_META[agent.domain] || { label: agent.domain, color: "#64748B" };
  // 从事件流聚合每个节点的状态
  const nodes = ["search", "analyze", "report"];
  const nodeState = (n: string) => {
    const evs = events.filter((e) => e.node === n);
    if (evs.some((e) => e.type === "step_complete" && e.status !== "failed"))
      return "done";
    if (evs.some((e) => e.type === "step_start")) return "running";
    return "pending";
  };
  const runningNow = events.filter((e) => e.type === "step_start").length;

  return (
    <div>
      {/* 头部 */}
      <header className="px-8 py-6 border-b border-borderc">
        <div className="flex items-start justify-between gap-4">
          <div className="min-w-0">
            <div className="flex items-center gap-2 mb-1">
              <span
                className="px-2 py-0.5 rounded text-[11px] font-medium font-mono"
                style={{ background: `${d.color}22`, color: d.color }}
              >
                {d.label}
              </span>
              <Link href="/" className="text-xs text-muted hover:text-primary">
                ← 仪表台
              </Link>
            </div>
            <h1 className="text-xl font-semibold">{agent.name}</h1>
            <p className="text-sm text-muted mt-1">{agent.intent}</p>
          </div>
          <div className="flex items-center gap-2 shrink-0">
            <Link
              href={`/agents/${id}/edit`}
              className="bg-surface-2 border border-borderc px-3 py-2 rounded-lg text-sm hover:border-primary"
            >
              ✎ 编辑
            </Link>
            <DeleteAgentButton agentId={id} agentName={agent.name} />
          </div>
        </div>
      </header>

      <div className="px-8 py-6 grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* 左：运行控制 + SSE 流 */}
        <div className="lg:col-span-2 space-y-6">
          <div className="bg-surface border border-borderc rounded-xl p-4 flex items-center justify-between">
            <div>
              <div className="text-sm font-semibold">工作流执行</div>
              <div className="text-xs text-muted mt-0.5">
                搜集 → 分析 → 结论，LangGraph 实时推送
              </div>
            </div>
            <button
              onClick={run}
              disabled={running}
              className="bg-accent text-on-accent px-4 py-2 rounded-lg text-sm font-medium hover:opacity-90 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {running ? "◌ 运行中…" : done ? "▶ 再次运行" : "▶ 运行"}
            </button>
          </div>

          {/* SSE 流 */}
          {events.length > 0 ? (
            <div className="bg-surface border border-borderc rounded-xl p-5">
              <div className="flex items-center gap-2 mb-4 text-sm font-semibold">
                <span
                  className={`w-2 h-2 rounded-full ${
                    done
                      ? "bg-done"
                      : running
                      ? "bg-running animate-pulse"
                      : "bg-failed"
                  }`}
                />
                {done ? "运行完成" : running ? "运行中…" : "运行中断"}
              </div>
              <ol className="space-y-2">
                {nodes.map((n, i) => {
                  const st = nodeState(n);
                  const evs = events.filter((e) => e.node === n);
                  return (
                    <li key={n} className="bg-surface-2 rounded-lg p-3">
                      <div className="flex items-center gap-2">
                        <span
                          className={`w-5 h-5 rounded-full flex items-center justify-center text-[11px] font-mono ${
                            st === "done"
                              ? "bg-ring text-white"
                              : st === "running"
                              ? "border border-ring"
                              : "bg-surface border border-borderc"
                          }`}
                        >
                          {st === "done" ? "✓" : st === "running" ? "◌" : i + 1}
                        </span>
                        <span className="text-sm font-medium">
                          {i + 1}. {NODE_LABEL[n] || n}
                        </span>
                        <span className="ml-auto text-[11px] text-muted font-mono">
                          {n}
                        </span>
                      </div>
                      {evs.length > 0 && (
                        <div className="mt-2 ml-7 space-y-1 text-xs text-muted">
                          {evs.map((e, idx) => (
                            <div key={idx}>
                              <span className="font-mono opacity-70">
                                [{e.type.replace("step_", "")}]
                              </span>{" "}
                              {e.message}
                            </div>
                          ))}
                        </div>
                      )}
                    </li>
                  );
                })}
              </ol>
              {/* error 事件单独显示 */}
              {events
                .filter((e) => e.type === "error")
                .map((e, i) => (
                  <div
                    key={`err-${i}`}
                    className="mt-2 text-xs text-failed"
                  >
                    ⚠ {e.message}
                  </div>
                ))}
              {/* 完成后查看报告 */}
              {done && runs.length > 0 && (
                <Link
                  href={`/reports/${runs[0].id}`}
                  className="mt-4 inline-block text-sm text-primary hover:underline pt-3 border-t border-borderc w-full"
                >
                  查看最新报告 →
                </Link>
              )}
            </div>
          ) : running ? (
            <div className="bg-surface border border-borderc rounded-xl p-5">
              <div className="flex items-center gap-2 text-sm font-semibold">
                <span className="w-2 h-2 rounded-full bg-running animate-pulse" />
                正在启动工作流…
              </div>
              <p className="text-xs text-muted mt-2 ml-4">
                系统正在解析情报需求，即将开始搜集
              </p>
            </div>
          ) : (
            <div className="bg-surface border border-borderc rounded-xl p-10 text-center text-sm text-muted">
              点击「运行」开始执行，工作流步骤将在此实时显示
            </div>
          )}
        </div>

        {/* 右：元信息 */}
        <div className="space-y-6">
          <div className="bg-surface border border-borderc rounded-xl p-4">
            <div className="text-xs font-semibold text-muted mb-3">
              智能体信息
            </div>
            <dl className="space-y-2.5 text-sm">
              <div className="flex justify-between">
                <dt className="text-muted">创建时间</dt>
                <dd className="font-mono">
                  {agent.created_at.slice(0, 10)}
                </dd>
              </div>
              <div className="flex justify-between">
                <dt className="text-muted">运行次数</dt>
                <dd className="font-mono">{agent.run_count}</dd>
              </div>
              <div className="flex justify-between">
                <dt className="text-muted">最近状态</dt>
                <dd>
                  {(STATUS_META[agent.last_status] || STATUS_META.idle).text}
                </dd>
              </div>
            </dl>
          </div>
          <div className="bg-surface border border-borderc rounded-xl p-4">
            <div className="text-xs font-semibold text-muted mb-3">
              已挂载工具集
            </div>
            <div className="space-y-2">
              {agent.tools.map((t) => (
                <div key={t} className="flex items-center gap-2 text-sm">
                  <span className="w-1.5 h-1.5 rounded-full bg-done" />
                  <span className="font-mono">{t}</span>
                </div>
              ))}
            </div>
          </div>
          <ScheduleSection agentId={agent.id} />
          <AgentMemorySection agentId={agent.id} />
        </div>
      </div>

      {/* 历史运行 */}
      <div className="px-8 pb-10">
        <div className="flex items-center justify-between mb-3">
          <h2 className="text-sm font-semibold text-muted">历史运行</h2>
          {selected.length === 2 && (
            <Link
              href={`/reports/compare/${selected[0]}/vs/${selected[1]}`}
              className="text-xs bg-primary text-on-primary px-3 py-1.5 rounded-lg hover:opacity-90"
            >
              对比选中的 2 份 →
            </Link>
          )}
        </div>
        <div className="bg-surface border border-borderc rounded-xl overflow-hidden divide-y divide-borderc">
          {runs.length === 0 ? (
            <div className="p-8 text-center text-sm text-muted">
              暂无运行记录，点上方「运行」开始第一次执行
            </div>
          ) : (
            runs.map((r) => {
              const s = STATUS_META[r.status] || STATUS_META.idle;
              const checked = selected.includes(r.id);
              const comparable = r.status === "completed" && r.report_length > 0;
              return (
                <div
                  key={r.id}
                  className={`p-4 flex items-center gap-3 hover:bg-surface-2 transition-colors ${checked ? "bg-primary/5" : ""}`}
                >
                  <input
                    type="checkbox"
                    checked={checked}
                    disabled={!comparable}
                    onChange={() => toggleSelect(r.id)}
                    className="w-4 h-4 accent-primary cursor-pointer disabled:opacity-30"
                    title={comparable ? "选择对比" : "未完成的运行不可对比"}
                  />
                  <Link href={`/reports/${r.id}`} className="flex-1 min-w-0 flex items-center gap-3">
                    <span
                      className="w-2 h-2 rounded-full shrink-0"
                      style={{ background: s.dot }}
                    />
                    <div className="flex-1 min-w-0">
                      <div className="text-sm font-mono">
                        {r.created_at.slice(0, 16).replace("T", " ")}
                      </div>
                      <div className="text-xs text-muted mt-0.5">
                        {r.steps_count} 步 · {r.report_length} 字
                      </div>
                    </div>
                    <span className="text-xs text-muted">{s.text}</span>
                    <span className="text-muted">›</span>
                  </Link>
                </div>
              );
            })
          )}
        </div>
      </div>
    </div>
  );
}
