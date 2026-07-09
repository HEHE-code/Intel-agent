export default function CompareLoading() {
  return (
    <div className="p-8">
      <div className="h-6 w-32 bg-surface-2 rounded animate-pulse mb-4" />
      <div className="h-4 w-64 bg-surface-2 rounded animate-pulse mb-6" />
      <div className="bg-surface border border-borderc rounded-xl p-5">
        <div className="flex items-center gap-2 mb-3">
          <span className="w-4 h-4 rounded-full bg-running animate-pulse" />
          <span className="text-sm font-semibold">正在生成对比分析…</span>
        </div>
        <p className="text-xs text-muted">
          AI 正在对比两份报告并生成变化摘要，约需 30 秒
        </p>
        <div className="mt-4 space-y-2">
          <div className="h-3 w-full bg-surface-2 rounded animate-pulse" />
          <div className="h-3 w-5/6 bg-surface-2 rounded animate-pulse" />
          <div className="h-3 w-4/6 bg-surface-2 rounded animate-pulse" />
        </div>
      </div>
    </div>
  );
}
