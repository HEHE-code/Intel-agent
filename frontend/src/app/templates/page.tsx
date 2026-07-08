"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { DOMAIN_META, api, type Template } from "@/lib/api";

export default function TemplatesPage() {
  const [templates, setTemplates] = useState<Template[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [editing, setEditing] = useState<Template | null>(null);
  const [showForm, setShowForm] = useState(false);

  const load = async () => {
    setLoading(true);
    try {
      setTemplates(await api<Template[]>("/api/templates"));
      setError("");
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    load();
  }, []);

  const del = async (id: string) => {
    if (!confirm("确认删除此模板？已生成的智能体不受影响。")) return;
    await api(`/api/templates/${id}`, { method: "DELETE" });
    load();
  };

  return (
    <div>
      <header className="px-8 py-6 flex items-center justify-between border-b border-borderc">
        <div>
          <h1 className="text-xl font-semibold">模板库</h1>
          <p className="text-sm text-muted mt-0.5">
            常用情报需求存成模板，一键复用，免每次从零描述
          </p>
        </div>
        <button
          onClick={() => {
            setEditing(null);
            setShowForm(true);
          }}
          className="bg-primary text-on-primary px-4 py-2 rounded-lg text-sm font-medium hover:opacity-90"
        >
          ＋ 新建模板
        </button>
      </header>

      <div className="px-8 py-6">
        {loading ? (
          <div className="text-sm text-muted">加载中…</div>
        ) : error ? (
          <div className="bg-failed/10 text-failed border border-failed/30 rounded-xl p-4 text-sm">
            加载失败：{error}
          </div>
        ) : templates.length === 0 ? (
          <div className="bg-surface border border-borderc rounded-xl p-10 text-center text-sm text-muted">
            还没有模板，点击右上角「新建模板」，或在生成页直接从需求创建
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-4">
            {templates.map((t) => {
              const d = DOMAIN_META[t.domain] || { label: t.domain, color: "#64748B" };
              return (
                <div
                  key={t.id}
                  className="bg-surface border border-borderc rounded-xl p-4"
                >
                  <div className="flex items-start justify-between gap-2">
                    <span
                      className="px-2 py-0.5 rounded text-[11px] font-medium font-mono"
                      style={{ background: `${d.color}22`, color: d.color }}
                    >
                      {d.label}
                    </span>
                    <div className="flex gap-2 text-xs">
                      <button
                        onClick={() => {
                          setEditing(t);
                          setShowForm(true);
                        }}
                        className="text-muted hover:text-primary"
                      >
                        ✎
                      </button>
                      <button
                        onClick={() => del(t.id)}
                        className="text-muted hover:text-failed"
                      >
                        ✕
                      </button>
                    </div>
                  </div>
                  <h3 className="font-semibold mt-2.5">{t.name}</h3>
                  <p className="text-xs text-muted mt-1 line-clamp-3">
                    {t.intent_template}
                  </p>
                  <div className="mt-3 pt-3 border-t border-borderc">
                    <Link
                      href={`/agents/new?from_template=${t.id}`}
                      className="text-sm text-primary hover:underline"
                    >
                      从此模板新建智能体 →
                    </Link>
                  </div>
                </div>
              );
            })}
          </div>
        )}
      </div>

      {showForm && (
        <TemplateForm
          template={editing}
          onDone={() => {
            setShowForm(false);
            load();
          }}
          onCancel={() => setShowForm(false)}
        />
      )}
    </div>
  );
}

function TemplateForm({
  template,
  onDone,
  onCancel,
}: {
  template: Template | null;
  onDone: () => void;
  onCancel: () => void;
}) {
  const [name, setName] = useState(template?.name || "");
  const [domain, setDomain] = useState(template?.domain || "military");
  const [intent, setIntent] = useState(template?.intent_template || "");
  const [prompt, setPrompt] = useState(template?.prompt_template || "");
  const [saving, setSaving] = useState(false);
  const [err, setErr] = useState("");

  const save = async () => {
    if (name.trim().length < 1 || intent.trim().length < 2) return;
    setSaving(true);
    setErr("");
    try {
      if (template) {
        await api(`/api/templates/${template.id}`, {
          method: "PUT",
          body: JSON.stringify({
            name, domain, intent_template: intent, prompt_template: prompt,
          }),
        });
      } else {
        await api("/api/templates", {
          method: "POST",
          body: JSON.stringify({
            name, domain, intent_template: intent, prompt_template: prompt,
          }),
        });
      }
      onDone();
    } catch (e) {
      setErr(e instanceof Error ? e.message : String(e));
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
      <div className="bg-surface border border-borderc rounded-xl p-6 w-full max-w-lg">
        <h2 className="text-lg font-semibold mb-4">
          {template ? "编辑模板" : "新建模板"}
        </h2>
        <div className="space-y-3">
          <div>
            <label className="block text-xs text-muted mb-1">模板名称</label>
            <input
              value={name}
              onChange={(e) => setName(e.target.value)}
              className="bg-surface-2 border border-borderc rounded-lg w-full px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-ring"
            />
          </div>
          <div>
            <label className="block text-xs text-muted mb-1">领域</label>
            <select
              value={domain}
              onChange={(e) => setDomain(e.target.value)}
              className="bg-surface-2 border border-borderc rounded-lg w-full px-3 py-2 text-sm"
            >
              {Object.entries(DOMAIN_META).map(([k, d]) => (
                <option key={k} value={k}>
                  {d.label}
                </option>
              ))}
            </select>
          </div>
          <div>
            <label className="block text-xs text-muted mb-1">
              需求模板（可作占位描述）
            </label>
            <textarea
              value={intent}
              onChange={(e) => setIntent(e.target.value)}
              className="bg-surface-2 border border-borderc rounded-lg w-full p-3 text-sm min-h-[100px] resize-none focus:outline-none focus:ring-2 focus:ring-ring"
            />
          </div>
          <div>
            <label className="block text-xs text-muted mb-1">
              提示词模板（可选）
            </label>
            <textarea
              value={prompt}
              onChange={(e) => setPrompt(e.target.value)}
              className="bg-surface-2 border border-borderc rounded-lg w-full p-3 text-sm min-h-[80px] resize-none font-mono focus:outline-none focus:ring-2 focus:ring-ring"
            />
          </div>
          {err && <div className="text-xs text-failed">{err}</div>}
        </div>
        <div className="flex justify-end gap-2 mt-5">
          <button
            onClick={onCancel}
            className="bg-surface-2 border border-borderc px-4 py-2 rounded-lg text-sm hover:border-primary"
          >
            取消
          </button>
          <button
            onClick={save}
            disabled={saving}
            className="bg-primary text-on-primary px-4 py-2 rounded-lg text-sm hover:opacity-90 disabled:opacity-50"
          >
            {saving ? "保存中…" : "保存"}
          </button>
        </div>
      </div>
    </div>
  );
}
