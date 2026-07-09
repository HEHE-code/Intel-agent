"use client";

import { useState } from "react";
import { api } from "@/lib/api";

export default function ReportMark({ runId, starred, note }: { runId: string; starred: boolean; note: string }) {
  const [star, setStar] = useState(starred);
  const [noteText, setNoteText] = useState(note);
  const [editing, setEditing] = useState(false);
  const [saved, setSaved] = useState(false);

  const toggleStar = async () => {
    const next = !star;
    setStar(next);
    try {
      await api(`/api/reports/${runId}/mark`, { method: "PUT", body: JSON.stringify({ starred: next }) });
    } catch {
      setStar(!next);
    }
  };

  const saveNote = async () => {
    try {
      await api(`/api/reports/${runId}/mark`, { method: "PUT", body: JSON.stringify({ note: noteText }) });
      setEditing(false);
      setSaved(true);
      setTimeout(() => setSaved(false), 2000);
    } catch {
      // 失败保留编辑态
    }
  };

  return (
    <div className="flex items-center gap-2 shrink-0">
      {/* 批注 */}
      {editing ? (
        <div className="flex items-center gap-1">
          <input
            value={noteText}
            onChange={(e) => setNoteText(e.target.value)}
            placeholder="加批注..."
            className="bg-surface-2 border border-borderc rounded px-2 py-1 text-xs w-40 focus:outline-none focus:ring-2 focus:ring-ring"
            autoFocus
          />
          <button onClick={saveNote} className="text-xs bg-primary text-on-primary px-2 py-1 rounded cursor-pointer">保存</button>
          <button onClick={() => { setNoteText(note); setEditing(false); }} className="text-xs text-muted px-1 cursor-pointer">取消</button>
        </div>
      ) : (
        <button
          onClick={() => setEditing(true)}
          className="text-xs px-2 py-1 rounded border border-borderc text-muted hover:border-primary cursor-pointer"
          title={note || "加批注"}
        >
          {note ? `📝 ${note.slice(12)}${note.length > 14 ? "…" : ""}` : "📝 批注"}
        </button>
      )}
      {saved && <span className="text-[11px] text-done">✓</span>}
      {/* 标星 */}
      <button
        onClick={toggleStar}
        className="text-lg cursor-pointer hover:scale-110 transition-transform"
        title={star ? "取消收藏" : "收藏"}
      >
        {star ? "★" : "☆"}
      </button>
    </div>
  );
}
