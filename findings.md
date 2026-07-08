# Findings & Decisions

## Requirements
<!-- 来自设计文档 2026-07-02-intelligence-agent-generator-design.md -->
- Web 应用：自然语言描述需求 → 自动生成并运行领域情报智能体
- 五大领域：军事、金融、科技、教育、公司
- 三节点工作流：搜集 → 分析 → 结论（LangGraph）
- SSE 实时推送运行步骤到前端
- 结果存为 Markdown 报告，可下载
- 仪表台管理智能体与历史
- LLM 可配置切换：DeepSeek / GLM
- 未配置 API Key 的领域自动降级为纯网络搜索模式 + 页面提示
- 后期扩展（模板库/多用户/PDF/定时）不在当前范围

## Research Findings
- **数据源成本调研（2026-07-02，官方页面核实）**：
  - Tavily：免费 1000 credits/月（无需信用卡），超额 $0.008/次；学生免费。https://tavily.com/pricing
  - Alpha Vantage：免费仅 25次/天、5次/分钟 —— 金融领域最紧。https://www.alphavantage.co/documentation/
  - NewsAPI：免费 100次/天，**但条款明确"仅限开发环境，不能用于生产/staging"**，商业版约 $449/月（部署上线的合规坑）。https://newsapi.org/pricing
  - arXiv API：完全免费，无 key，礼貌限速 1次/3秒
  - GitHub Trending：官方无 API，需爬取；GitHub REST API 免费（60次/小时无认证 / 5000次/小时有认证）
  - RSS / 网页爬取：完全免费
  - LLM：DeepSeek ≈¥1/百万token、GLM 有免费额度，成本可忽略
## Issues Encountered
| Issue | Resolution |
|-------|------------|
| 公网部分被墙（国内网络）：duckduckgo.com ❌、Yahoo Finance(hq.sinajs/yahoo) ❌、rsshub.app ❌；baidu/Bing/arxiv/github/东方财富 ✅ | 数据源换国内可达方案：搜索用 Bing/百度，金融用 akshare（聚合东财/新浪） |
| DuckDuckGo web_search 实测超时返回空 | 同上，需替换搜索源 |
| 8000 端口被其他进程占用 | 后端固定用 8001 |
| 系统无 pip/venv/sudo | 装 uv（~/.local，免 root）建虚拟环境 |

## 网络可达性实测（2026-07-02）
- ✅ 可达：baidu.com、cn.bing.com、sogou.com、arxiv.org、api.github.com、eastmoney.com、内网 LLM 网关 172.16.3.6:8589
- ❌ 被墙：duckduckgo.com、query1.finance.yahoo.com（→ yfinance 不可用）、rsshub.app
- 结论：免 Key 数据源需走国内可达方案
  - 通用/新闻搜索：**Bing（cn.bing.com）抓取** 或 百度，替代 DuckDuckGo
  - 金融行情：**akshare**（聚合东方财富/新浪/同花顺，免 Key），替代 yfinance
  - 论文 arXiv：✅ 直接可用
  - GitHub：✅ 直接可用
  - RSS：需直连具体媒体源（公网 rsshub 不可用），或退化为搜索


  - 金融行情：用 yfinance（免费无 key）/ 东方财富替代 Alpha Vantage
  - 新闻：本机用 NewsAPI 免费版；上线用 GDELT(免费)/RSS 聚合/爬取替代，避开商业授权
  - 设置页降级逻辑已实现（原型⑥），未配 Key 的领域自动纯搜索


- **ui-ux-pro-max 设计系统已生成**（持久化于 `design-system/intelligence-agent-generator/MASTER.md`）：
  - Pattern：Real-Time / Operations Landing（暗或中性底 + 状态色，data-dense）
  - Style：Data-Dense Dashboard
  - 主色 #1E40AF / CTA 琥珀 #D97706 / 背景 #F8FAFC（亮）→ 原型自定暗色底 #0B1220
  - 字体：Fira Sans（正文）+ Fira Code（数据/代码）
  - 反模式：忌花哨装饰、忌无筛选
- **原型配色定稿**（经用户确认：明暗双主题）：
  - 暗色：底 #0B1220 / 卡 #131C2E / 文字 #E2E8F0；亮色：底 #F8FAFC / 卡 #FFFFFF / 文字 #1E3A8A
  - 状态色：running #3B82F6 / completed #22C55E / failed #EF4444 / idle #64748B
  - 领域色：军事红 / 金融绿 / 科技蓝 / 教育紫 / 公司琥珀
- **原型技术选择**：单文件 HTML + Tailwind CDN + 内嵌 JS（无构建步骤，浏览器直开）
  - 路由用 JS 切换 .page.active（非真实 URL），mock 数据内嵌
  - Playwright 验证：file:// 被拦，需 `python3 -m http.server 8765` 起本地服务器访问
- **用户工作方式反馈（重要）**：必须增量交付，分功能分点写，不可一次性堆完。原型按 6 步逐页交付，每步停下确认

<!-- 设计文档已确定的技术选型 -->
- 技术栈：Next.js (App Router) + Tailwind / FastAPI (Python) / LangGraph / SSE / SQLite（可迁 PostgreSQL）
- 领域工具集映射：
  - 军事：Web Search + RSS（防务媒体）
  - 金融：Web Search + Alpha Vantage + NewsAPI
  - 科技：Web Search + NewsAPI + GitHub Trending
  - 教育：Web Search + arXiv API
  - 公司：Web Search + NewsAPI + 网页爬取
- 后端 API 端点（设计文档已定）：
  - POST /api/agents/generate, POST /api/agents/{id}/run
  - GET/PUT /api/agents, /api/agents/{id}
  - GET /api/reports, /api/reports/{id}
- 数据模型三表：AgentConfig / RunRecord / DomainToolConfig（字段已在设计文档定义）
- SSE 消息类型：step_start / step_result / step_complete / report_ready / error
- 错误处理：SSE 断开重连最多 3 次；节点级重试最多 2 次；LLM 解析失败给友好提示

## Technical Decisions
| Decision | Rationale |
|----------|-----------|
| Monorepo 同仓库（backend/ + frontend/） | 个人研究者单人项目，共用 .env/README，联调方便 |
| Web Search 用 Tavily | LLM agent 友好，结构化摘要，有免费额度 |
| 运行用 FastAPI BackgroundTasks | 单进程异步跑工作流，SSE 同进程推送，简单够用，初期无需 Redis |
| 数据访问层用 SQLAlchemy | 设计文档明确"可迁移 PostgreSQL"，ORM 迁移顺滑 |
| **部署模式 = 自用（本机/单用户）** | 用户确认 2026-07-02 自用 → 免费版数据源均合规（NewsAPI 生产限制不适用），照设计文档原工具集实现，不换源 |
| **数据源 = 免 Key 免费优先** | 用户只有 LLM Key，数据源不想再申请 → 全部用免 Key 免费源，保留可选 Key 升级位 |
| **LLM = 自定义 OpenAI 兼容网关** | 用户提供的 172.16.3.6:8589 精灵云网关，glm-5.1；config 支持 LLM_BASE_URL+KEY+MODEL，custom 优先级最高 |
| **搜集架构 = 领域专项源直爬（非通用搜索）** | 实测：cn.bing 中文分词差召回不可用、DDG/Yahoo/rsshub 被墙、LLM 网关无联网能力。改走每个领域的权威专项源直爬，国内可达+结构化+质量高。这才是设计文档"领域工具集"本意 |
| LLM 调用方式 | langchain_openai.ChatOpenAI（三者都走 OpenAI 兼容接口），上层 get_llm().invoke() |
| LLM 调用方式 | 待定：直接 HTTP vs LangChain 封装（Phase 2 决） |

## Issues Encountered
| Issue | Resolution |
|-------|------------|
|       |            |

## Resources
- 设计文档：/home/han/Desktop/Agent/2026-07-02-intelligence-agent-generator-design.md
- 规划文件：./task_plan.md, ./progress.md（本目录）

## Visual/Browser Findings
- 暂无

---
*Update this file after every 2 view/browser/search operations*
