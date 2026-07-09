// 后端 API 地址。开发期后端跑在 8001，前端 3000。
export const API_BASE =
  process.env.NEXT_PUBLIC_API_BASE || "http://localhost:8001";

// 领域元信息（与后端 DOMAIN_META 对齐）
export const DOMAIN_META: Record<
  string,
  { label: string; color: string }
> = {
  military: { label: "军事", color: "#DC2626" },
  finance: { label: "金融", color: "#059669" },
  tech: { label: "科技", color: "#3B82F6" },
  education: { label: "教育", color: "#7C3AED" },
  company: { label: "公司", color: "#D97706" },
};

export const STATUS_META: Record<
  string,
  { dot: string; text: string }
> = {
  completed: { dot: "#22C55E", text: "已完成" },
  running: { dot: "#3B82F6", text: "运行中" },
  failed: { dot: "#EF4444", text: "失败" },
  idle: { dot: "#64748B", text: "空闲" },
};

// —— API 类型（与后端响应模型对齐） ——
export interface Agent {
  id: string;
  name: string;
  domain: string;
  intent: string;
  tools: string[];
  prompt_template: string;
  created_at: string;
  last_run_at: string;
  last_status: string;
  run_count: number;
  has_schedule: boolean;
}

export interface Template {
  id: string;
  name: string;
  domain: string;
  intent_template: string;
  tools: string[];
  prompt_template: string;
  created_at: string;
}

export interface ReportSummary {
  id: string;
  agent_id: string;
  agent_name?: string;
  domain?: string;
  status: string;
  created_at: string;
  report_length: number;
  preview: string;
  steps_count: number;
  starred?: boolean;
  note?: string;
}

export interface ReportDetail extends ReportSummary {
  report_md: string;
  steps: any[];
  starred: boolean;
  note: string;
}

export interface DiffSection {
  title: string;
  status: "added" | "removed" | "unchanged" | "changed";
  left: string;
  right: string;
  similarity?: number;
  line_diff?: { type: "added" | "removed" | "unchanged"; content: string }[];
}

export interface CompareResult {
  left: { id: string; created_at: string; status: string };
  right: { id: string; created_at: string; status: string };
  diff: { sections: DiffSection[] };
  summary: string;
}

export interface Schedule {
  agent_id: string;
  run_type: string; // once/daily/weekly
  hour: number;
  minute: number;
  weekday: string | null; // mon..sun
  once_date: string | null; // YYYY-MM-DD
  enabled: boolean;
  last_run_at: string;
  created_at: string;
}

export interface ScheduleReq {
  run_type: string;
  hour: number;
  minute: number;
  once_date?: string | null;
  weekday?: string | null;
}

// —— API 调用 ——
export async function api<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`, {
    ...init,
    headers: { "Content-Type": "application/json", ...(init?.headers || {}) },
  });
  if (!res.ok) {
    throw new Error(`API ${res.status}: ${await res.text()}`);
  }
  return res.json() as Promise<T>;
}

// —— SSE 事件（与后端 engine.py 对齐） ——
export interface SSEEvent {
  type: "step_start" | "step_result" | "step_complete" | "report_ready" | "error";
  node?: string;
  attempt?: number;
  message?: string;
  status?: string;
  data?: any;
  run_id?: string;
}

/**
 * 触发智能体运行并以 SSE 流式消费事件。
 * onEvent 在每个事件到达时调用；完成后 resolve 最终的 report_ready 事件。
 */
export async function runAgentStream(
  agentId: string,
  onEvent: (e: SSEEvent) => void,
  signal?: AbortSignal
): Promise<SSEEvent | null> {
  const res = await fetch(`${API_BASE}/api/agents/${agentId}/run`, {
    method: "POST",
    signal,
  });
  if (!res.ok || !res.body) {
    throw new Error(`运行失败: ${res.status}`);
  }

  const reader = res.body.getReader();
  const decoder = new TextDecoder();
  let buffer = "";
  let final: SSEEvent | null = null;

  while (true) {
    const { done, value } = await reader.read();
    if (done) break;
    buffer += decoder.decode(value, { stream: true });
    // SSE 帧以 \n\n 分隔
    const frames = buffer.split("\n\n");
    buffer = frames.pop() || "";
    for (const frame of frames) {
      const line = frame.split("\n").find((l) => l.startsWith("data:"));
      if (!line) continue;
      try {
        const evt = JSON.parse(line.slice(5).trim()) as SSEEvent;
        onEvent(evt);
        if (evt.type === "report_ready") final = evt;
      } catch {
        /* 忽略非 JSON 帧 */
      }
    }
  }
  return final;
}
