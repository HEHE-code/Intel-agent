import Link from "next/link";
import { API_BASE, DOMAIN_META, STATUS_META, api, type Agent } from "@/lib/api";

export const dynamic = "force-dynamic"; // 每次请求都取最新数据

export default async function Home() {
  let agents: Agent[] = [];
  let error = "";
  try {
    agents = await api<Agent[]>("/api/agents");
  } catch (e) {
    error = e instanceof Error ? e.message : String(e);
  }

  const running = agents.filter((a) => a.last_status === "running").length;
  const totalRuns = agents.reduce((s, a) => s + a.run_count, 0);

  return (
    <div>
      <header className="px-8 py-6 flex items-center justify-between border-b border-borderc">
        <div>
          <h1 className="text-xl font-semibold">仪表台</h1>
          <p className="text-sm text-muted mt-0.5">
            管理你的情报智能体，一键运行并查看实时进展
          </p>
        </div>
        <Link
          href="/agents/new"
          className="bg-primary text-on-primary px-4 py-2 rounded-lg text-sm font-medium hover:opacity-90 flex items-center gap-1.5"
        >
          ＋ 新建智能体
        </Link>
      </header>

      {/* 统计卡 */}
      <div className="px-8 py-5 grid grid-cols-3 gap-4">
        <StatCard label="智能体总数" value={agents.length} />
        <StatCard label="运行中" value={running} color="text-running" />
        <StatCard label="累计报告" value={totalRuns} />
      </div>

      {/* 卡片网格 */}
      <div className="px-8 pb-10">
        <h2 className="text-sm font-semibold text-muted mb-3">我的智能体</h2>
        {error ? (
          <div className="bg-failed/10 text-failed border border-failed/30 rounded-xl p-4 text-sm">
            加载失败：{error}
            <div className="text-xs mt-1 text-muted">
              请确认后端运行在 {API_BASE}
            </div>
          </div>
        ) : agents.length === 0 ? (
          <div className="bg-surface border border-borderc rounded-xl p-10 text-center text-sm text-muted">
            还没有智能体，点击右上角「新建智能体」开始
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-4">
            {agents.map((a) => (
              <AgentCard key={a.id} agent={a} />
            ))}
          </div>
        )}
      </div>
    </div>
  );
}

function StatCard({
  label,
  value,
  color = "",
}: {
  label: string;
  value: number;
  color?: string;
}) {
  return (
    <div className="bg-surface border border-borderc rounded-xl px-4 py-3">
      <div className="text-xs text-muted">{label}</div>
      <div className={`text-2xl font-semibold font-mono mt-1 ${color}`}>
        {value}
      </div>
    </div>
  );
}

function AgentCard({ agent }: { agent: Agent }) {
  const d = DOMAIN_META[agent.domain] || { label: agent.domain, color: "#64748B" };
  const s = STATUS_META[agent.last_status] || STATUS_META.idle;
  const lastRun = agent.last_run_at
    ? agent.last_run_at.slice(0, 16).replace("T", " ")
    : "—";

  return (
    <Link
      href={`/agents/${agent.id}`}
      className="block bg-surface border border-borderc rounded-xl p-4 hover:border-primary transition-colors"
    >
      <div className="flex items-start justify-between gap-2">
        <span
          className="px-2 py-0.5 rounded text-[11px] font-medium font-mono"
          style={{ background: `${d.color}22`, color: d.color }}
        >
          {d.label}
        </span>
        {agent.has_schedule && (
          <span className="px-1.5 py-0.5 rounded text-[11px] font-mono bg-accent/20 text-accent">
            ⏰ 定时
          </span>
        )}
        <span className="flex items-center gap-1.5 text-[11px] text-muted">
          <span
            className="w-1.5 h-1.5 rounded-full"
            style={{ background: s.dot }}
          />
          {s.text}
        </span>
      </div>
      <h3 className="font-semibold mt-2.5">{agent.name}</h3>
      <p className="text-xs text-muted mt-1 line-clamp-2">{agent.intent}</p>
      <div className="flex items-center justify-between mt-3 pt-3 border-t border-borderc text-[11px] text-muted">
        <span>最近运行 {lastRun}</span>
        <span className="font-mono">{agent.run_count} 次运行</span>
      </div>
    </Link>
  );
}
