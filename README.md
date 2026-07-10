# Intel-agent · 情报智能体生成器

用自然语言描述需求，自动生成并运行针对特定领域的情报收集与分析智能体。LangGraph 跑「搜集 → 分析 → 结论」三节点工作流，SSE 实时推送运行过程，结果存为 Markdown 报告并可下载。

> 自用项目，本地运行。LLM 走自定义 OpenAI 兼容网关，数据源走免 Key 免费源（可选 Tavily 升级）。

## 功能

- **自然语言生成智能体**：描述需求 → LLM 解析意图（领域/主题/时间/关键实体）→ 自动匹配工具集与提示词 → 入库
- **三节点工作流 + SSE 实时流**：搜集（领域数据源）→ 分析（LLM 提炼）→ 结论（生成 Markdown 报告），每步实时推送真实思考内容（资料标题/提炼要点/报告标题），运行中刷新页面过程不丢
- **5 预设领域 + 自定义领域**：军事 / 金融 / 科技 / 教育 / 公司，支持添加自定义领域（持久化，每个领域不同色）
- **模板库**：常用情报需求存成模板，一键复用（预置 5 领域通用模板）
- **定时运行**：单次 / 每天 / 每周，可视化选择时间，到点自动跑，报告自动存档
- **报告管理**：Markdown 渲染 + 下载 .md；**搜索 + 筛选**（按智能体/领域/状态/关键词）；历史运行可查
- **报告对比**：选同智能体两份报告 → AI 变化摘要（新增/删除/变化）+ 行级 diff 高亮
- **智能体记忆**：每次运行自动提取关键结论存入记忆，下次运行参考"相比上次的变与不变"，报告有连续性
- **追问报告**：看完报告直接对话追问，LLM 基于报告内容回答（有依据不编造，多轮对话）
- **综合研判**：选多个智能体，AI 跨领域交叉印证各报告，产出综合情报报告（非简单拼接，找关联/印证/矛盾/合力）
- **智能体删除**：详情页删除（级联清理运行记录+定时配置，二次确认）
- **明暗双主题**

## 技术栈

| 层 | 技术 |
|----|------|
| 前端 | Next.js 16 (App Router) + React 19 + Tailwind v4 + TypeScript |
| 后端 | FastAPI + SQLAlchemy + LangGraph |
| LLM | OpenAI 兼容网关（自定义/DeepSeek/GLM 可切换） |
| 实时推送 | Server-Sent Events (SSE) |
| 数据库 | SQLite |
| 调度 | APScheduler |

## 目录结构

```
Intel-agent/
├── backend/                 # FastAPI 后端
│   ├── app/
│   │   ├── api/             # 路由（agents/reports/templates/schedules/domains/health）
│   │   ├── tools/           # 数据源工具（arxiv/github/finance/rss/tavily/web_search 等）
│   │   ├── config.py        # 配置（LLM provider 自动识别）
│   │   ├── engine.py        # LangGraph 三节点工作流 + SSE + 记忆
│   │   ├── intent.py        # LLM 意图解析
│   │   ├── llm.py           # LLM 抽象层
│   │   ├── diff.py          # 报告对比（段落级 diff + LLM 变化摘要）
│   │   ├── aggregate.py     # 多智能体综合研判引擎
│   │   ├── models.py        # SQLAlchemy 模型
│   │   ├── crud.py          # 数据访问层
│   │   ├── scheduler.py     # APScheduler 定时调度
│   │   └── main.py          # FastAPI 入口
│   ├── requirements.txt
│   └── .env.example         # 配置模板（复制为 .env 填 Key）
├── frontend/                # Next.js 前端
│   └── src/
│       ├── app/             # 仪表台/生成/详情/编辑/报告/对比/模板/综合研判/设置 + 动态路由
│       ├── components/      # Sidebar/ThemeProvider/ScheduleSection/Markdown/ReportsList/ReportAsk/AgentMemorySection/DeleteAgentButton
│       └── lib/api.ts       # API 客户端 + 类型
├── prototype/               # 早期 HTML 原型（验证设计用）
└── design-system/           # 设计系统 token
```

## 快速开始

### 1. 后端

```bash
cd backend

# 建虚拟环境装依赖（用 uv 免 root，或用 venv）
uv venv .venv && source .venv/bin/activate
uv pip install -r requirements.txt
# 或：python -m venv .venv && source .venv/bin/activate && pip install -r requirements.txt

# 配置：复制模板并填入 LLM Key
cp .env.example .env
# 编辑 .env，至少填一个 LLM 配置（见下方"配置"）

# 启动
uvicorn app.main:app --host 0.0.0.0 --port 8001
```

### 2. 前端

```bash
cd frontend
npm install

# 配置后端地址（用 IP 便于其他设备访问）
cat > .env.local << 'EOF'
NEXT_PUBLIC_API_BASE=http://<后端IP>:8001
EOF

# 生产模式（推荐，IP 访问无 HMR 问题）
npm run build
npm run start -- -H 0.0.0.0 -p 3000

# 或开发模式（仅 localhost，热更新）
npm run dev
```

打开 `http://<前端IP>:3000`。

## 配置（backend/.env）

```ini
# LLM —— 三选一，系统自动识别
# 方式A：自定义 OpenAI 兼容网关（优先级最高）
LLM_BASE_URL=http://your-gateway/v1
LLM_API_KEY=your-key
LLM_MODEL=glm-5.1

# 方式B：DeepSeek 官方
DEEPSEEK_API_KEY=sk-xxx

# 方式C：GLM（智谱）官方
ZHIPU_API_KEY=xxx

# 数据源升级（可选，有 Tavily Key 大幅提升搜索质量）
TAVILY_API_KEY=tvly-xxx

# 运行配置
DATABASE_PATH=data/intelligence.db
CORS_ORIGINS=http://localhost:3000,http://127.0.0.1:3000,http://<前端IP>:3000
```

> 不填 LLM Key 后端能启动但无法生成/运行智能体；不填 Tavily Key 走免 Key 搜索源（召回质量略低）。

## 数据源

按领域配置，**默认免 Key 免费源**，有 Tavily Key 时自动启用深度搜索：

| 领域 | 数据源 |
|------|--------|
| 军事 | RSS（人民网/军网/新华）+ Bing 搜索 |
| 金融 | akshare（东方财富/新浪聚合）+ Bing |
| 科技 | GitHub Search API + arXiv + Bing |
| 教育 | arXiv + Bing（+ Tavily 搜分数线等） |
| 公司 | Bing + akshare 个股新闻 + 网页爬取 |
| 自定义 | Bing + Tavily（若有 Key） |

## 使用流程

1. **新建智能体**：仪表台点「新建」→ 描述需求（可选手领域，留空自动识别）→ 生成
2. **运行**：进详情页点「运行」→ 实时看搜集/分析/结论步骤 → 完成后看报告
3. **定时**：详情页设单次/每天/每周 → 到点自动跑
4. **模板**：`/templates` 页从模板新建，或把常用智能体存为模板
5. **对比**：详情页历史运行勾选 2 份 → AI 变化摘要 + 行级 diff
6. **追问**：报告页点「追问」→ 基于报告内容多轮对话
7. **综合研判**：`/aggregate` 选多个智能体 → AI 跨领域交叉印证 → 综合报告

## 已知限制

- LLM 长文本生成较慢（单次运行约 2-3 分钟），SSE 流式让等待不枯燥
- 国内网络下百度/部分搜索源被反爬，已用 Bing + 权威源限定 + Tavily 规避
- 报告数据准确性取决于搜索结果；LLM 被约束**严禁编造数据**，资料未提供处会明说

## License

自用项目，未设开源协议。
