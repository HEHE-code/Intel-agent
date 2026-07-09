"use client";

import { useState } from "react";
import { api } from "@/lib/api";

interface Msg {
  role: "user" | "assistant";
  content: string;
}

export default function ReportAsk({ runId, open: controlledOpen, onOpenChange }: { runId: string; open?: boolean; onOpenChange?: (v: boolean) => void }) {
  const [internalOpen, setInternalOpen] = useState(false);
  const open = controlledOpen ?? internalOpen;
  const setOpen = (v: boolean) => {
    if (onOpenChange) onOpenChange(v);
    else setInternalOpen(v);
  };
  const [msgs, setMsgs] = useState<Msg[]>([]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);

  const ask = async () => {
    const q = input.trim();
    if (!q || loading) return;
    setInput("");
    const newMsgs = [...msgs, { role: "user" as const, content: q }];
    setMsgs(newMsgs);
    setLoading(true);
    try {
      const r = await api<{ answer: string }>(`/api/reports/${runId}/ask`, {
        method: "POST",
        body: JSON.stringify({ question: q, history: msgs }),
      });
      setMsgs([...newMsgs, { role: "assistant", content: r.answer }]);
    } catch (e) {
      setMsgs([...newMsgs, { role: "assistant", content: "回答失败：" + (e instanceof Error ? e.message : String(e)) }]);
    } finally {
      setLoading(false);
    }
  };

  if (!open) {
    return (
      <button
        onClick={() => setOpen(true)}
        className="bg-surface-2 border border-borderc px-3 py-2 rounded-lg text-sm hover:border-primary cursor-pointer"
      >
        💬 追问
      </button>
    );
  }

  return (
    <div className="fixed bottom-4 right-4 w-96 max-w-[90vw] bg-surface border border-borderc rounded-xl shadow-2xl flex flex-col z-50" style={{ height: 480 }}>
      <div className="flex items-center justify-between px-4 py-2.5 border-b border-borderc">
        <span className="text-sm font-semibold">💬 追问报告</span>
        <button onClick={() => { setOpen(false); setMsgs([]); }} className="text-muted hover:text-text cursor-pointer text-lg leading-none">×</button>
      </div>
      <div className="flex-1 overflow-y-auto p-3 space-y-3">
        {msgs.length === 0 && (
          <div className="text-xs text-muted text-center mt-8">
            基于本报告内容追问，如"这个结论的依据""展开讲讲风险"
          </div>
        )}
        {msgs.map((m, i) => (
          <div key={i} className={`flex ${m.role === "user" ? "justify-end" : "justify-start"}`}>
            <div
              className={`max-w-[85%] px-3 py-2 rounded-lg text-xs whitespace-pre-wrap leading-relaxed ${
                m.role === "user" ? "bg-primary text-on-primary" : "bg-surface-2"
              }`}
            >
              {m.content}
            </div>
          </div>
        ))}
        {loading && (
          <div className="flex justify-start">
            <div className="bg-surface-2 px-3 py-2 rounded-lg text-xs text-muted">
              <span className="inline-block animate-pulse">思考中…</span>
            </div>
          </div>
        )}
      </div>
      <div className="p-3 border-t border-borderc flex gap-2">
        <input
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={(e) => { if (e.key === "Enter" && !e.shiftKey) { e.preventDefault(); ask(); } }}
          placeholder="输入追问…"
          className="flex-1 bg-surface-2 border border-borderc rounded-lg px-3 py-1.5 text-xs focus:outline-none focus:ring-2 focus:ring-ring"
        />
        <button
          onClick={ask}
          disabled={loading || !input.trim()}
          className="bg-primary text-on-primary px-3 py-1.5 rounded-lg text-xs cursor-pointer hover:opacity-90 disabled:opacity-50"
        >
          发送
        </button>
      </div>
    </div>
  );
}
