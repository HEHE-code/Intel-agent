# 情报智能体生成器 — 设计文档

**日期:** 2026-07-02  
**状态:** 已批准

---

## 概述

一个 Web 应用，允许个人研究者/独立分析师通过自然语言描述需求，自动生成并运行针对特定领域（军事、金融、科技、教育、公司）的情报收集与分析智能体。智能体运行过程实时可见，结果可下载为报告，历史记录通过仪表台管理。

---

## 技术栈

| 层 | 技术 |
|----|------|
| 前端 | Next.js (App Router) + Tailwind CSS |
| 后端 | FastAPI (Python) |
| 智能体引擎 | LangGraph |
| 实时推送 | Server-Sent Events (SSE) |
| 数据库 | SQLite（初期，可迁移至 PostgreSQL） |
| LLM | DeepSeek API 或 GLM API（可配置切换） |

---

## 整体架构

```
用户浏览器
    │
    ├─ Next.js 前端
    │     ├─ 仪表台（首页）
    │     ├─ 生成页
    │     ├─ 智能体详情页（含实时运行流）
    │     ├─ 智能体编辑页
    │     ├─ 报告详情页
    │     └─ 设置页
    │
    └─ FastAPI 后端
          ├─ POST /api/agents/generate   — 自然语言 → 智能体配置
          ├─ POST /api/agents/{id}/run   — 启动执行，SSE 流式推送
          ├─ GET  /api/agents            — 列表
          ├─ GET  /api/agents/{id}       — 详情
          ├─ PUT  /api/agents/{id}       — 编辑配置
          ├─ GET  /api/reports           — 历史报告列表
          ├─ GET  /api/reports/{id}      — 报告详情
          └─ LangGraph Engine
                ├─ 搜集节点（Web Search + 专项 API）
                ├─ 分析节点（LLM 提炼关键情报）
                └─ 结论节点（生成结构化 Markdown 报告）
```

---

## 核心工作流

用户输入自然语言 → 系统执行三步：

1. **解析意图**：LLM 提取领域、主题、时间范围、关键实体，输出结构化的智能体配置 JSON
2. **生成智能体**：根据领域匹配预设工具集和提示词模板，无需用户手动配置
3. **执行工作流**：LangGraph 按节点顺序运行，每步通过 SSE 实时推送前端

### 领域工具集映射

| 领域 | 工具集 |
|------|--------|
| 军事 | Web Search + RSS（防务媒体） |
| 金融 | Web Search + Alpha Vantage + NewsAPI |
| 科技 | Web Search + NewsAPI + GitHub Trending |
| 教育 | Web Search + arXiv API |
| 公司 | Web Search + NewsAPI + 网页爬取 |

---

## 数据模型

```sql
-- 智能体配置
AgentConfig
  id           TEXT PRIMARY KEY
  name         TEXT
  domain       TEXT  -- military/finance/tech/education/company
  intent       TEXT  -- 原始自然语言输入
  tools        JSON  -- 工具集列表
  prompt_template TEXT
  created_at   DATETIME

-- 每次执行记录
RunRecord
  id           TEXT PRIMARY KEY
  agent_id     TEXT REFERENCES AgentConfig(id)
  status       TEXT  -- running/completed/failed
  steps        JSON  -- 各节点运行日志
  report_md    TEXT  -- 最终 Markdown 报告
  created_at   DATETIME

-- 领域工具配置（可运行时调整）
DomainToolConfig
  domain       TEXT
  tool_name    TEXT
  api_key_env  TEXT  -- 对应的环境变量名
  enabled      BOOLEAN
```

---

## 页面结构

### 仪表台 `/`
- 顶部"新建智能体"按钮
- 智能体卡片列表：领域标签、名称、最近运行时间、状态（idle/running/completed）
- 点击卡片进入智能体详情页

### 生成页 `/agents/new`
- 自然语言输入框（占主体）
- 领域快捷标签辅助选择（可选）
- 提交后调用 `/api/agents/generate`，生成配置后跳回仪表台

### 智能体详情页 `/agents/[id]`
- 上方：智能体名称、领域、创建时间 + "运行"按钮 + "编辑"入口
- 中部（运行时）：SSE 实时步骤流
  ```
  [✓] 搜索: 找到 12 条相关结果
  [✓] 爬取: 提取 8 篇全文
  [→] 分析: 正在提炼关键情报...
  [ ] 生成报告
  ```
- 下方：历次运行记录列表，点击跳转报告详情页

### 智能体编辑页 `/agents/[id]/edit`
- 可修改：名称、工具集开关、提示词模板
- 保存后更新 AgentConfig，不影响已有运行记录

### 报告详情页 `/reports/[id]`
- Markdown 全文渲染
- 下载按钮（.md 格式，后期支持 PDF）
- 面包屑导航回智能体详情页

### 设置页 `/settings`
- LLM 选择：DeepSeek / GLM，对应 API Key 输入
- 各领域数据 API Key 输入（NewsAPI、Alpha Vantage 等）
- 保存至本地 `.env` 文件
- 未配置 API Key 的领域自动降级为纯网络搜索模式，页面显示降级提示

---

## SSE 消息格式

```json
{ "type": "step_start",    "node": "search",   "message": "开始搜索..." }
{ "type": "step_result",   "node": "search",   "message": "找到 12 条结果", "data": [...] }
{ "type": "step_start",    "node": "analyze",  "message": "正在分析..." }
{ "type": "step_complete", "node": "analyze",  "message": "分析完成" }
{ "type": "report_ready",  "report_id": "...", "message": "报告已生成" }
{ "type": "error",         "message": "..." }
```

---

## 错误处理

- SSE 连接断开：前端自动重连（最多 3 次），超时后显示"运行中断，可刷新页面查看最新状态"
- API 调用失败：节点级别重试（最多 2 次），失败后标记该步骤为 failed，不中断整体流程
- LLM 解析失败：返回用户友好提示，建议重新描述需求

---

## 后期扩展点（不在当前范围）

- 模板库（预设常用情报模板）
- 多用户/团队协作
- PDF 导出
- 定时自动运行智能体
