"use client";

import { useEffect, useState } from "react";
import { api, type Schedule, type ScheduleReq } from "@/lib/api";
import DatePicker from "./DatePicker";

const WEEKDAYS = [
  { key: "mon", label: "周一" },
  { key: "tue", label: "周二" },
  { key: "wed", label: "周三" },
  { key: "thu", label: "周四" },
  { key: "fri", label: "周五" },
  { key: "sat", label: "周六" },
  { key: "sun", label: "周日" },
];

const TYPES = [
  { key: "once", label: "单次" },
  { key: "daily", label: "每天" },
  { key: "weekly", label: "每周" },
];

export default function ScheduleSection({ agentId }: { agentId: string }) {
  const [sch, setSch] = useState<Schedule | null>(null);
  const [runType, setRunType] = useState("daily");
  const [hour, setHour] = useState(9);
  const [minute, setMinute] = useState(0);
  const [weekday, setWeekday] = useState("mon");
  const [onceDate, setOnceDate] = useState("");
  const [loading, setLoading] = useState(false);
  const [msg, setMsg] = useState("");

  const load = async () => {
    try {
      const s = await api<Schedule | null>(`/api/agents/${agentId}/schedule`);
      setSch(s);
      if (s) {
        setRunType(s.run_type);
        setHour(s.hour);
        setMinute(s.minute);
        if (s.weekday) setWeekday(s.weekday);
        if (s.once_date) setOnceDate(s.once_date);
      }
    } catch {
      /* 无配置正常 */
    }
  };
  useEffect(() => {
    load();
  }, [agentId]);

  const save = async () => {
    setLoading(true);
    setMsg("");
    try {
      const req: ScheduleReq = { run_type: runType, hour, minute };
      if (runType === "once") req.once_date = onceDate;
      if (runType === "weekly") req.weekday = weekday;
      const s = await api<Schedule>(`/api/agents/${agentId}/schedule`, {
        method: "POST",
        body: JSON.stringify(req),
      });
      setSch(s);
      setMsg("✓ 已保存");
    } catch (e) {
      setMsg(`✗ ${e instanceof Error ? e.message : String(e)}`);
    } finally {
      setLoading(false);
      setTimeout(() => setMsg(""), 2500);
    }
  };

  const toggle = async () => {
    if (!sch) return;
    setLoading(true);
    try {
      const s = await api<Schedule>(`/api/agents/${agentId}/schedule`, {
        method: "PUT",
        body: JSON.stringify({ enabled: !sch.enabled }),
      });
      setSch(s);
    } finally {
      setLoading(false);
    }
  };

  const del = async () => {
    if (!confirm("确定删除定时配置？")) return;
    setLoading(true);
    try {
      await api(`/api/agents/${agentId}/schedule`, { method: "DELETE" });
      setSch(null);
      setMsg("✓ 已删除");
      setTimeout(() => setMsg(""), 2000);
    } finally {
      setLoading(false);
    }
  };

  const lastRun = sch?.last_run_at
    ? sch.last_run_at.slice(0, 16).replace("T", " ")
    : "从未运行";

  // 人类可读的下次运行描述
  const desc = (() => {
    const t = `${String(hour).padStart(2, "0")}:${String(minute).padStart(2, "0")}`;
    if (runType === "once") {
      // onceDate 是 YYYY-MM-DD，转成中文年月日
      let d = "未选日期";
      if (onceDate) {
        const [y, m, day] = onceDate.split("-");
        d = `${y}年${m}月${day}日`;
      }
      return `${d} ${t}`;
    }
    if (runType === "daily") return `每天 ${t}`;
    const wd = WEEKDAYS.find((w) => w.key === weekday)?.label || "";
    return `每${wd} ${t}`;
  })();

  return (
    <div className="bg-surface border border-borderc rounded-xl p-4">
      <div className="flex items-center justify-between mb-3">
        <div className="text-xs font-semibold text-muted">⏰ 定时运行</div>
        {sch && (
          <button
            onClick={toggle}
            disabled={loading}
            className={`text-xs px-2 py-1 rounded ${
              sch.enabled ? "bg-done/20 text-done" : "bg-surface-2 text-muted"
            }`}
          >
            {sch.enabled ? "● 已启用" : "○ 已停用"}
          </button>
        )}
      </div>

      {/* 频率选择 */}
      <div className="flex gap-1 mb-3">
        {TYPES.map((t) => (
          <button
            key={t.key}
            onClick={() => setRunType(t.key)}
            className={`flex-1 px-2 py-1.5 rounded-lg text-xs ${
              runType === t.key
                ? "bg-primary text-on-primary"
                : "bg-surface-2 text-muted border border-borderc"
            }`}
          >
            {t.label}
          </button>
        ))}
      </div>

      {/* 时间选择 */}
      <div className="flex items-center gap-2 mb-3">
        <span className="text-xs text-muted">时间</span>
        <select
          value={hour}
          onChange={(e) => setHour(Number(e.target.value))}
          disabled={loading}
          className="bg-surface-2 border border-borderc rounded px-2 py-1 text-xs"
        >
          {Array.from({ length: 24 }, (_, i) => (
            <option key={i} value={i}>{String(i).padStart(2, "0")}</option>
          ))}
        </select>
        <span className="text-xs">:</span>
        <select
          value={minute}
          onChange={(e) => setMinute(Number(e.target.value))}
          disabled={loading}
          className="bg-surface-2 border border-borderc rounded px-2 py-1 text-xs"
        >
          {Array.from({ length: 60 }, (_, i) => i).map((m) => (
            <option key={m} value={m}>{String(m).padStart(2, "0")}</option>
          ))}
        </select>
      </div>

      {/* 单次：选日期（日历弹层，全中文） */}
      {runType === "once" && (
        <div className="mb-3 flex items-center gap-2">
          <span className="text-xs text-muted">日期</span>
          <DatePicker value={onceDate} onChange={setOnceDate} disabled={loading} />
        </div>
      )}

      {/* 每周：选周几 */}
      {runType === "weekly" && (
        <div className="mb-3 flex gap-1">
          {WEEKDAYS.map((w) => (
            <button
              key={w.key}
              onClick={() => setWeekday(w.key)}
              className={`flex-1 px-1 py-1 rounded text-[11px] ${
                weekday === w.key
                  ? "bg-primary text-on-primary"
                  : "bg-surface-2 text-muted border border-borderc"
              }`}
            >
              {w.label}
            </button>
          ))}
        </div>
      )}

      {/* 可读描述 */}
      <div className="text-xs text-muted mb-3 bg-surface-2 rounded px-2 py-1.5">
        {sch?.enabled ? "将" : "已停用 · 原"}于 <b>{desc}</b> 自动运行
      </div>

      <div className="flex gap-2">
        <button
          onClick={save}
          disabled={loading}
          className="bg-primary text-on-primary px-3 py-1.5 rounded-lg text-xs hover:opacity-90 disabled:opacity-50"
        >
          保存
        </button>
        {sch && (
          <button
            onClick={del}
            disabled={loading}
            className="bg-surface-2 border border-borderc px-3 py-1.5 rounded-lg text-xs hover:border-failed"
          >
            删除
          </button>
        )}
      </div>
      {sch && (
        <p className="text-[11px] text-muted mt-2">最近定时运行：{lastRun}</p>
      )}
      {msg && <p className="text-[11px] mt-2">{msg}</p>}
    </div>
  );
}
