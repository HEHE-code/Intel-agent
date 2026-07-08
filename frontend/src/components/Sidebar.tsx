"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { useTheme } from "./ThemeProvider";

const NAV = [
  { href: "/", label: "仪表台", icon: "▦" },
  { href: "/agents/new", label: "新建智能体", icon: "＋" },
  { href: "/templates", label: "模板库", icon: "▤" },
  { href: "/reports", label: "报告", icon: "▤" },
  { href: "/settings", label: "设置", icon: "⚙" },
];

export default function Sidebar() {
  const pathname = usePathname();
  const { theme, toggle } = useTheme();

  return (
    <aside className="w-60 shrink-0 border-r border-borderc bg-surface flex flex-col">
      {/* Logo */}
      <div className="px-5 py-5 border-b border-borderc flex items-center gap-2.5">
        <div className="w-8 h-8 rounded-lg bg-primary text-on-primary flex items-center justify-center font-bold">
          情
        </div>
        <div>
          <div className="text-sm font-semibold leading-tight">情报智能体</div>
          <div className="text-[11px] text-muted font-mono leading-tight">
            Generator
          </div>
        </div>
      </div>

      {/* 导航 */}
      <nav className="flex-1 px-3 py-4 space-y-1">
        {NAV.map((n) => {
          const active =
            n.href === "/"
              ? pathname === "/"
              : pathname.startsWith(n.href);
          return (
            <Link
              key={n.href}
              href={n.href}
              className={`w-full flex items-center gap-3 px-3 py-2 rounded-lg text-sm font-medium cursor-pointer transition-colors hover:bg-primary/10 ${
                active ? "bg-primary/10 text-primary" : ""
              }`}
            >
              <span>{n.icon}</span> {n.label}
            </Link>
          );
        })}
      </nav>

      {/* 主题切换 */}
      <div className="px-3 py-4 border-t border-borderc">
        <button
          onClick={toggle}
          className="w-full flex items-center justify-center gap-2 px-3 py-2 rounded-lg text-sm bg-surface-2 border border-borderc cursor-pointer hover:border-primary"
        >
          {theme === "dark" ? "☀" : "☾"} {theme === "dark" ? "亮色" : "暗色"}
        </button>
      </div>
    </aside>
  );
}
