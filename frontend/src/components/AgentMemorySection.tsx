"use client";

import { useEffect, useState } from "react";
import { api } from "@/lib/api";

interface Memory {
  run_id: string;
  key_points: string[];
  created_at: string;
}

export default function AgentMemorySection({ agentId }: { agentId: string }) {
  const [memories, setMemories] = useState<Memory[]>([]);
  const [loading, setLoading] = useState(true);

  const load = async () => {
    try {
      const m = await api<Memory[]>(`/api/agents/${agentId}/memory`);
      setMemories(m);
    } catch {
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { load(); }, [agentId]);

  const clear = async () => {
    if (!confirm("清空智能体记忆？下次运行将不再参考历史结论。")) return;
    await api(`/api/agents/${agentId}/memory`, { method: "DELETE" });
    setMemories([]);
  };

  return (
    <div className="bg-surface border border-borderc rounded-xl p-4">
      <div className="flex items-center justify-between mb-3">
        <span className="text-xs font-semibold text-muted">🧠 智能体记忆</span>
        {memories.length > 0 && (
          <button onClick={clear} className="text-[11px] text-muted hover:text-failed cursor-pointer">
            清空
          </button>
        )}
      </div>
      {loading ? (
        <div className="text-xs text-muted">加载中…</div>
      ) : memories.length === 0 ? (
        <div className="text-xs text-muted">
          暂无记忆。运行后自动记录关键结论，下次运行参考以保持连续性。
        </div>
      ) : (
        <div className="space-y-3 max-h-60 overflow-y-auto">
          {memories.map((m, i) => (
            <div key={m.run_id} className="text-xs">
              <div className="text-muted font-mono mb-1">
                {m.created_at.slice(0, 16).replace("T", " ")}
              </div>
              <ul className="space-y-0.5">
                {m.key_points.map((p, j) => (
                  <li key={j} className="flex gap-1.5">
                    <span className="text-accent">•</span>
                    <span>{p}</span>
                  </li>
                ))}
              </ul>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
