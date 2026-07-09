"use client";

import { useRouter } from "next/navigation";
import { useState } from "react";
import { api } from "@/lib/api";

export default function DeleteAgentButton({ agentId, agentName }: { agentId: string; agentName: string }) {
  const router = useRouter();
  const [confirming, setConfirming] = useState(false);
  const [deleting, setDeleting] = useState(false);

  const del = async () => {
    setDeleting(true);
    try {
      await api(`/api/agents/${agentId}`, { method: "DELETE" });
      router.push("/");
    } catch (e) {
      alert("删除失败：" + (e instanceof Error ? e.message : String(e)));
      setDeleting(false);
      setConfirming(false);
    }
  };

  if (!confirming) {
    return (
      <button
        onClick={() => setConfirming(true)}
        className="border border-failed/40 text-failed px-3 py-2 rounded-lg text-sm hover:bg-failed/10 cursor-pointer"
      >
        🗑 删除
      </button>
    );
  }

  return (
    <div className="flex items-center gap-2">
      <span className="text-xs text-failed">删除「{agentName}」及其所有运行记录？</span>
      <button
        onClick={del}
        disabled={deleting}
        className="bg-failed text-white px-3 py-1.5 rounded-lg text-xs cursor-pointer hover:opacity-90 disabled:opacity-50"
      >
        {deleting ? "删除中…" : "确认删除"}
      </button>
      <button
        onClick={() => setConfirming(false)}
        className="text-xs text-muted px-2 py-1.5 cursor-pointer hover:text-text"
      >
        取消
      </button>
    </div>
  );
}
