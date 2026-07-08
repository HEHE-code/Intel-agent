import Link from "next/link";
import { notFound } from "next/navigation";
import { API_BASE, api, type ReportDetail } from "@/lib/api";
import Markdown from "@/components/Markdown";

export const dynamic = "force-dynamic";

export default async function ReportPage({
  params,
}: {
  params: Promise<{ id: string }>;
}) {
  const { id } = await params;
  let report: ReportDetail;
  try {
    report = await api<ReportDetail>(`/api/reports/${id}`);
  } catch {
    notFound();
  }

  return (
    <div>
      <header className="px-8 py-6 border-b border-borderc">
        <div className="flex items-center gap-2 mb-1 text-xs text-muted">
          <Link
            href={`/agents/${report.agent_id}`}
            className="hover:text-primary"
          >
            ← 智能体详情
          </Link>
          <span>/</span>
          <span className="font-mono">报告</span>
        </div>
        <div className="flex items-start justify-between gap-4">
          <div>
            <h1 className="text-xl font-semibold">情报分析报告</h1>
            <p className="text-sm text-muted mt-1">
              {report.created_at.slice(0, 16).replace("T", " ")} ·{" "}
              <span className="font-mono">{report.report_length} 字</span> ·{" "}
              {report.steps_count} 步
            </p>
          </div>
          <a
            href={`${API_BASE}/api/reports/${id}/download`}
            className="bg-accent text-on-accent px-4 py-2 rounded-lg text-sm font-medium hover:opacity-90 flex items-center gap-1.5 shrink-0"
            download
          >
            ↓ 下载 .md
          </a>
        </div>
      </header>

      <div className="px-8 py-6 max-w-3xl">
        <article className="bg-surface border border-borderc rounded-xl p-8">
          {report.report_md ? (
            <Markdown content={report.report_md} />
          ) : (
            <p className="text-sm text-muted text-center py-10">
              该运行未生成报告内容
            </p>
          )}
        </article>
      </div>
    </div>
  );
}
