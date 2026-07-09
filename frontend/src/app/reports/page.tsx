import { api, type ReportSummary } from "@/lib/api";
import ReportsList from "@/components/ReportsList";

export const dynamic = "force-dynamic";

export default async function ReportsPage() {
  let reports: ReportSummary[] = [];
  let error = "";
  try {
    reports = await api<ReportSummary[]>("/api/reports");
  } catch (e) {
    error = e instanceof Error ? e.message : String(e);
  }

  return (
    <div>
      <header className="px-8 py-6 border-b border-borderc">
        <h1 className="text-xl font-semibold">报告</h1>
        <p className="text-sm text-muted mt-0.5">
          所有智能体的历史报告，点 ☆ 收藏
        </p>
      </header>

      <div className="px-8 py-6">
        {error ? (
          <div className="bg-failed/10 text-failed border border-failed/30 rounded-xl p-4 text-sm">
            加载失败：{error}
          </div>
        ) : (
          <ReportsList reports={reports} />
        )}
      </div>
    </div>
  );
}
