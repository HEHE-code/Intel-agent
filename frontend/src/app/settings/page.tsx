import Link from "next/link";
import { api } from "@/lib/api";

export const dynamic = "force-dynamic";

interface Health {
  status: string;
  llm: {
    provider: string | null;
    available: boolean;
    base_url: string | null;
    model: string | null;
    key_hint: string;
  };
  data_sources: Record<string, boolean>;
}

const PROVIDER_LABEL: Record<string, string> = {
  custom: "自定义网关 (OpenAI 兼容)",
  deepseek: "DeepSeek",
  glm: "GLM (智谱)",
};

export default async function SettingsPage() {
  let health: Health | null = null;
  let error = "";
  try {
    health = await api<Health>("/api/health");
  } catch (e) {
    error = e instanceof Error ? e.message : String(e);
  }

  const llm = health?.llm;
  const ds = health?.data_sources || {};
  const optionalCount = Object.keys(ds).length;
  const configured = Object.values(ds).filter(Boolean).length;

  return (
    <div>
      <header className="px-8 py-6 border-b border-borderc">
        <h1 className="text-xl font-semibold">设置</h1>
        <p className="text-sm text-muted mt-0.5">
          查看当前 LLM 与数据源配置。所有 Key 在后端{" "}
          <code className="font-mono text-xs">backend/.env</code> 管理，修改后重启后端生效。
        </p>
      </header>

      <div className="px-8 py-6 max-w-2xl space-y-6">
        {error && (
          <div className="bg-failed/10 text-failed border border-failed/30 rounded-xl p-4 text-sm">
            无法读取配置：{error}
          </div>
        )}

        {/* LLM 配置 */}
        <div className="bg-surface border border-borderc rounded-xl p-5">
          <div className="text-sm font-semibold mb-3">LLM 引擎</div>
          {llm?.available ? (
            <dl className="space-y-2.5 text-sm">
              <Row label="Provider" value={PROVIDER_LABEL[llm.provider || ""] || llm.provider || "—"} />
              <Row label="Base URL" value={llm.base_url || "—"} mono />
              <Row label="Model" value={llm.model || "—"} mono />
              <Row label="API Key" value={`••••${llm.key_hint || ""}`} mono />
            </dl>
          ) : (
            <div className="text-sm text-failed">
              ⚠ 未配置 LLM。请在 backend/.env 设置 LLM_BASE_URL + LLM_API_KEY，或 DEEPSEEK_API_KEY / ZHIPU_API_KEY。
            </div>
          )}
        </div>

        {/* 数据源 */}
        <div className="bg-surface border border-borderc rounded-xl p-5">
          <div className="text-sm font-semibold mb-1">数据源状态</div>
          <p className="text-xs text-muted mb-3">
            默认全部使用免 Key 免费源（DuckDuckGo/arXiv/GitHub/akshare/RSS）。以下为可选升级项，配置后启用更高质量数据。
          </p>
          <div className="space-y-2">
            <SourceRow name="Tavily（搜索升级）" on={ds.tavily} />
            <SourceRow name="Alpha Vantage（金融行情）" on={ds.alpha_vantage} />
            <SourceRow name="NewsAPI（新闻，仅本机自用）" on={ds.newsapi} />
          </div>
          <div className={`mt-4 rounded-lg p-3 border text-xs ${
            configured === optionalCount
              ? "border-done/40 bg-done/10 text-done"
              : "border-accent/40 bg-accent/10 text-accent"
          }`}>
            {configured === optionalCount
              ? `✓ 全部 ${optionalCount} 项可选数据源已配置`
              : `⚠ ${optionalCount - configured} 项未配置 — 未配置领域自动降级为纯免费源，不影响运行`}
          </div>
        </div>

        {/* 配置指引 */}
        <div className="bg-surface-2 border border-borderc rounded-xl p-5">
          <div className="text-sm font-semibold mb-2">如何修改配置</div>
          <ol className="text-xs text-muted space-y-1.5 list-decimal list-inside">
            <li>编辑 <code className="font-mono">backend/.env</code> 文件</li>
            <li>填入/修改对应的 Key（参考 <code className="font-mono">.env.example</code>）</li>
            <li>重启后端：<code className="font-mono">uvicorn app.main:app --host 0.0.0.0 --port 8001</code></li>
            <li>刷新本页确认配置生效</li>
          </ol>
        </div>

        <div className="text-xs text-muted">
          <Link href="/" className="hover:text-primary">← 返回仪表台</Link>
        </div>
      </div>
    </div>
  );
}

function Row({ label, value, mono }: { label: string; value: string; mono?: boolean }) {
  return (
    <div className="flex justify-between gap-4">
      <dt className="text-muted shrink-0">{label}</dt>
      <dd className={`text-right break-all ${mono ? "font-mono" : ""}`}>{value}</dd>
    </div>
  );
}

function SourceRow({ name, on }: { name: string; on: boolean }) {
  return (
    <div className="flex items-center justify-between text-sm">
      <span>{name}</span>
      <span className={`text-xs ${on ? "text-done" : "text-muted"}`}>
        {on ? "✓ 已配置" : "未配置"}
      </span>
    </div>
  );
}
