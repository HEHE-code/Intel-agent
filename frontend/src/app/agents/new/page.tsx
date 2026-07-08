"use client";

import { Suspense, useEffect, useState } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import { API_BASE, DOMAIN_META, api, type Agent, type Template } from "@/lib/api";

interface DomainInfo {
  key: string;
  label: string;
  color: string;
  preset: boolean;
}

const EXAMPLES = [
  "半导体先进制程进展",
  "特斯拉 Q2 财报与舆情",
  "大模型教育应用研究",
  "亚太地区军事演习动态",
];

export default function NewAgentPage() {
  return (
    <Suspense fallback={<div className="p-8 text-sm text-muted">加载中…</div>}>
      <NewAgentInner />
    </Suspense>
  );
}

function NewAgentInner() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const [intent, setIntent] = useState("");
  const [domain, setDomain] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [phase, setPhase] = useState(""); // 解析过程提示
  const [domains, setDomains] = useState<DomainInfo[]>([]); // 动态领域（预设+自定义）

  // 加载领域列表（预设 + 用户自定义）
  useEffect(() => {
    api<DomainInfo[]>("/api/domains").then(setDomains).catch(() => {});
  }, []);

  // 从模板新建：读 from_template 参数，预填 intent
  useEffect(() => {
    const tplId = searchParams.get("from_template");
    if (!tplId) return;
    api<Template>(`/api/templates/${tplId}`)
      .then((t) => {
        setIntent(t.intent_template);
        setDomain(t.domain);
      })
      .catch(() => {});
  }, [searchParams]);

  const submit = async () => {
    if (intent.trim().length < 2) return;
    setLoading(true);
    setError("");
    setPhase("正在解析意图并生成智能体…");
    try {
      const agent = await api<Agent>("/api/agents/generate", {
        method: "POST",
        body: JSON.stringify({ intent, domain: domain || undefined }),
      });
      setPhase("✓ 已生成，跳转仪表台…");
      // 短暂展示后跳回仪表台
      setTimeout(() => router.push("/"), 600);
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
      setPhase("");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div>
      <header className="px-8 py-6 border-b border-borderc">
        <h1 className="text-xl font-semibold">新建智能体</h1>
        <p className="text-sm text-muted mt-0.5">
          用自然语言描述你的情报需求，系统将自动解析意图并生成专属智能体
        </p>
      </header>

      <div className="px-8 py-8 max-w-3xl">
        {/* 领域快捷标签 */}
        <label className="block text-xs font-semibold text-muted mb-2">
          情报领域（可选，留空则自动识别）
        </label>
        <div className="flex flex-wrap gap-2 mb-6">
          {domains.map((d) => {
            const active = domain === d.key;
            return (
              <button
                key={d.key}
                onClick={() => setDomain(active ? null : d.key)}
                className="px-3 py-1.5 rounded-full text-xs font-medium border cursor-pointer transition-colors"
                style={{
                  borderColor: `${d.color}55`,
                  background: active ? d.color : "transparent",
                  color: active ? "#fff" : d.color,
                }}
              >
                {d.label}
              </button>
            );
          })}
          {/* 自定义领域输入（输入新领域名，生成后自动持久化） */}
          <div className="flex items-center gap-1.5">
            <input
              value={domain && !domains.some((d) => d.key === domain) ? domain : ""}
              onChange={(e) => setDomain(e.target.value.trim() || null)}
              placeholder="自定义领域..."
              className="bg-surface-2 border border-borderc rounded-full px-3 py-1.5 text-xs w-32 focus:outline-none focus:ring-2 focus:ring-ring"
            />
          </div>
        </div>

        {/* 自然语言输入 */}
        <label className="block text-xs font-semibold text-muted mb-2">
          描述你的情报需求
        </label>
        <div className="relative">
          <textarea
            value={intent}
            onChange={(e) => setIntent(e.target.value)}
            disabled={loading}
            placeholder="例如：追踪近期亚太地区军事部署与防务合作动态，重点关注美日韩三边演习与台海动向…"
            className="bg-surface border border-borderc rounded-xl w-full p-4 text-sm leading-relaxed resize-none min-h-[140px] focus:outline-none focus:ring-2 focus:ring-ring disabled:opacity-60"
          />
          <div className="absolute bottom-3 right-3 text-[11px] text-muted font-mono">
            {intent.length} 字
          </div>
        </div>

        {/* 示例 chips */}
        <div className="mt-3 flex flex-wrap items-center gap-2">
          <span className="text-xs text-muted">试试：</span>
          {EXAMPLES.map((ex) => (
            <button
              key={ex}
              onClick={() => setIntent(ex)}
              disabled={loading}
              className="text-xs bg-surface-2 border border-borderc rounded-full px-3 py-1 cursor-pointer hover:border-primary disabled:opacity-50"
            >
              {ex}
            </button>
          ))}
        </div>

        {/* 生成按钮 */}
        <div className="mt-6 flex items-center gap-3">
          <button
            onClick={submit}
            disabled={loading || intent.trim().length < 2}
            className="bg-primary text-on-primary px-5 py-2.5 rounded-lg text-sm font-medium hover:opacity-90 flex items-center gap-2 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {loading ? "◌ 生成中…" : "✦ 生成智能体"}
          </button>
          <span className="text-xs text-muted">
            解析意图 → 匹配工具集 → 生成配置
          </span>
        </div>

        {/* 解析过程 / 错误 */}
        {phase && (
          <div className="mt-6 bg-surface border border-borderc rounded-xl p-4 text-sm flex items-center gap-2">
            <span className="w-2 h-2 rounded-full bg-running animate-pulse" />
            {phase}
          </div>
        )}
        {error && (
          <div className="mt-6 bg-failed/10 text-failed border border-failed/30 rounded-xl p-4 text-sm">
            生成失败：{error}
            <div className="text-xs mt-1 text-muted">
              请确认后端运行在 {API_BASE} 且 LLM Key 已配置
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
