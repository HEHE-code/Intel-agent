"use client";

import { use, useEffect, useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { api, type Agent } from "@/lib/api";

export default function EditAgentPage({
  params,
}: {
  params: Promise<{ id: string }>;
}) {
  const { id } = use(params);
  const router = useRouter();
  const [agent, setAgent] = useState<Agent | null>(null);
  const [name, setName] = useState("");
  const [tools, setTools] = useState<string[]>([]);
  const [prompt, setPrompt] = useState("");
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [saved, setSaved] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    (async () => {
      try {
        const a = await api<Agent>(`/api/agents/${id}`);
        setAgent(a);
        setName(a.name);
        setTools(a.tools);
        setPrompt(a.prompt_template);
      } catch (e) {
        setError(e instanceof Error ? e.message : String(e));
      } finally {
        setLoading(false);
      }
    })();
  }, [id]);

  const toggleTool = (t: string) =>
    setTools((prev) =>
      prev.includes(t) ? prev.filter((x) => x !== t) : [...prev, t]
    );

  const save = async () => {
    setSaving(true);
    setError("");
    try {
      await api(`/api/agents/${id}`, {
        method: "PUT",
        body: JSON.stringify({ name, tools, prompt_template: prompt }),
      });
      setSaved(true);
      setTimeout(() => setSaved(false), 2000);
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
    } finally {
      setSaving(false);
    }
  };

  if (loading) return <div className="p-8 text-muted">加载中…</div>;
  if (error && !agent)
    return (
      <div className="p-8">
        <div className="bg-failed/10 text-failed border border-failed/30 rounded-xl p-4 text-sm">
          加载失败：{error}
        </div>
        <Link href={`/agents/${id}`} className="text-sm text-muted hover:text-primary mt-4 inline-block">
          ← 返回详情
        </Link>
      </div>
    );
  if (!agent) return null;

  return (
    <div>
      <header className="px-8 py-6 border-b border-borderc">
        <Link
          href={`/agents/${id}`}
          className="text-xs text-muted hover:text-primary"
        >
          ← 详情
        </Link>
        <h1 className="text-xl font-semibold mt-1">编辑智能体</h1>
        <p className="text-sm text-muted mt-0.5">
          修改配置后保存，不影响已有的历史运行记录
        </p>
      </header>

      <div className="px-8 py-6 max-w-2xl space-y-6">
        {/* 名称 */}
        <div>
          <label className="block text-xs font-semibold text-muted mb-2">
            智能体名称
          </label>
          <input
            value={name}
            onChange={(e) => setName(e.target.value)}
            className="bg-surface border border-borderc rounded-lg w-full px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-ring"
          />
        </div>

        {/* 工具开关 */}
        <div>
          <label className="block text-xs font-semibold text-muted mb-2">
            工具集
          </label>
          <div className="bg-surface border border-borderc rounded-xl overflow-hidden divide-y divide-borderc">
            {agent.tools.map((t) => {
              const on = tools.includes(t);
              return (
                <div
                  key={t}
                  className="flex items-center justify-between p-3.5"
                >
                  <div>
                    <div className="text-sm font-medium font-mono">{t}</div>
                  </div>
                  <button
                    onClick={() => toggleTool(t)}
                    aria-pressed={on}
                    className="relative w-10 h-6 rounded-full transition-colors shrink-0 cursor-pointer"
                    style={{ background: on ? "var(--ring)" : "var(--text-muted)" }}
                  >
                    <span
                      className="absolute top-0.5 left-0.5 w-5 h-5 rounded-full bg-white transition-transform"
                      style={{ transform: on ? "translateX(16px)" : "translateX(0)" }}
                    />
                  </button>
                </div>
              );
            })}
          </div>
          <p className="text-[11px] text-muted mt-2">
            关闭的工具在运行时将跳过
          </p>
        </div>

        {/* 提示词模板 */}
        <div>
          <label className="block text-xs font-semibold text-muted mb-2">
            提示词模板
          </label>
          <textarea
            value={prompt}
            onChange={(e) => setPrompt(e.target.value)}
            className="bg-surface border border-borderc rounded-lg w-full p-3 text-sm leading-relaxed resize-none min-h-[120px] font-mono focus:outline-none focus:ring-2 focus:ring-ring"
          />
          <p className="text-[11px] text-muted mt-2">
            定义智能体在分析节点的人设与关注重点
          </p>
        </div>

        {/* 操作 */}
        <div className="flex items-center gap-3 pt-2">
          <button
            onClick={save}
            disabled={saving}
            className="bg-primary text-on-primary px-4 py-2 rounded-lg text-sm font-medium hover:opacity-90 disabled:opacity-50"
          >
            {saving ? "保存中…" : "保存"}
          </button>
          <Link
            href={`/agents/${id}`}
            className="bg-surface-2 border border-borderc px-4 py-2 rounded-lg text-sm hover:border-primary"
          >
            取消
          </Link>
          {saved && <span className="text-xs text-done">✓ 已保存</span>}
          {error && <span className="text-xs text-failed">{error}</span>}
        </div>
      </div>
    </div>
  );
}
