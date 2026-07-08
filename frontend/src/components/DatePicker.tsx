"use client";

import { useState } from "react";

const WEEK_HEADERS = ["一", "二", "三", "四", "五", "六", "日"];

interface Props {
  value: string; // YYYY-MM-DD
  onChange: (v: string) => void;
  disabled?: boolean;
}

export default function DatePicker({ value, onChange, disabled }: Props) {
  const [open, setOpen] = useState(false);
  // 视图所在月（默认值所在月或当月）
  const init = value ? parseYM(value) : parseYM(today());
  const [viewY, setViewY] = useState(init.y);
  const [viewM, setViewM] = useState(init.m); // 0-11

  const todayStr = today();
  const cells = buildCells(viewY, viewM);

  const prevMonth = () => {
    if (viewM === 0) { setViewY(viewY - 1); setViewM(11); }
    else setViewM(viewM - 1);
  };
  const nextMonth = () => {
    if (viewM === 11) { setViewY(viewY + 1); setViewM(0); }
    else setViewM(viewM + 1);
  };

  const pick = (d: string | null) => {
    if (d) {
      onChange(d);
      setOpen(false);
    }
  };

  const display = value ? formatCN(value) : "选择日期";

  return (
    <div className="relative">
      <button
        type="button"
        onClick={() => !disabled && setOpen(!open)}
        disabled={disabled}
        className="bg-surface-2 border border-borderc rounded px-2 py-1 text-xs hover:border-primary"
      >
        📅 {display}
      </button>
      {open && (
        <div className="absolute z-50 mt-1 bg-surface border border-borderc rounded-lg p-3 shadow-lg w-56">
          {/* 月份导航 */}
          <div className="flex items-center justify-between mb-2">
            <button type="button" onClick={prevMonth} className="px-2 text-sm hover:text-primary">‹</button>
            <span className="text-xs font-semibold">{viewY}年{viewM + 1}月</span>
            <button type="button" onClick={nextMonth} className="px-2 text-sm hover:text-primary">›</button>
          </div>
          {/* 星期表头 */}
          <div className="grid grid-cols-7 gap-0.5 mb-1">
            {WEEK_HEADERS.map((w) => (
              <div key={w} className="text-center text-[10px] text-muted">{w}</div>
            ))}
          </div>
          {/* 日期网格 */}
          <div className="grid grid-cols-7 gap-0.5">
            {cells.map((c, i) => (
              <button
                key={i}
                type="button"
                disabled={!c}
                onClick={() => pick(c)}
                className={`text-center text-[11px] py-1 rounded ${
                  !c
                    ? "invisible"
                    : c === value
                    ? "bg-primary text-on-primary"
                    : c === todayStr
                    ? "bg-accent/20 text-accent"
                    : "hover:bg-surface-2"
                }`}
              >
                {c ? Number(c.slice(8)) : ""}
              </button>
            ))}
          </div>
          {/* 快捷：今天 */}
          <button
            type="button"
            onClick={() => pick(todayStr)}
            className="mt-2 w-full text-[11px] text-primary hover:underline"
          >
            选今天
          </button>
        </div>
      )}
    </div>
  );
}

// —— 工具函数 ——
function parseYM(ymd: string) {
  const [y, m] = ymd.split("-").map(Number);
  return { y, m: m - 1 };
}
function today(): string {
  const d = new Date();
  return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())}`;
}
function pad(n: number) {
  return String(n).padStart(2, "0");
}
function formatCN(ymd: string) {
  const [y, m, d] = ymd.split("-");
  return `${y}年${m}月${d}日`;
}
/** 构建某月日历单元格（周一起始），返回 42 个 'YYYY-MM-DD' 或 null */
function buildCells(year: number, month: number): (string | null)[] {
  const first = new Date(year, month, 1);
  // 周一=0...周日=6
  let startWeekday = first.getDay() - 1;
  if (startWeekday < 0) startWeekday = 6; // 周日
  const daysInMonth = new Date(year, month + 1, 0).getDate();
  const cells: (string | null)[] = [];
  for (let i = 0; i < startWeekday; i++) cells.push(null);
  for (let d = 1; d <= daysInMonth; d++) {
    cells.push(`${year}-${pad(month + 1)}-${pad(d)}`);
  }
  while (cells.length % 7 !== 0) cells.push(null);
  return cells;
}
