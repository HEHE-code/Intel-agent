# Task Plan: 情报智能体生成器 (Intelligence Agent Generator)

## Goal
按已批准设计文档（`2026-07-02-intelligence-agent-generator-design.md`）从零实现一个 Web 应用：用户用自然语言描述需求，系统生成并运行领域情报智能体（军事/金融/科技/教育/公司），LangGraph 跑搜集→分析→结论三节点工作流，SSE 实时推送步骤，结果存为 Markdown 报告并可下载。

## Current Phase
Phase 1-5 全部完成 ✅（端到端可用）

## Phases

### Phase 1: 项目骨架与基础设施
- [x] 建立仓库目录结构（backend/ 已建，frontend/ 待 Phase 5）
- [x] 后端 FastAPI 骨架（main.py、路由占位、CORS、健康检查）
- [ ] 前端 Next.js (App Router) + Tailwind 骨架（Phase 5）
- [x] SQLite 数据库初始化（SQLAlchemy 三表，启动自动 create_all）
- [x] `.env` 配置体系 + LLM provider 自动识别（DeepSeek/GLM）
- [ ] 前后端联调跑通（待 Phase 5 前端）
- **Status:** in_progress（后端骨架完成，前端部分移至 Phase 5）

### Phase 2: 数据层与领域配置
- [x] 实现 ORM/数据访问层（SQLAlchemy + crud.py，AgentConfig/RunRecord/DomainToolConfig 全CRUD）
- [x] 实现领域工具集映射（registry.py：9工具 + 5领域映射 + 提示词模板）
- [x] 实现 DomainToolConfig CRUD（运行时开关工具，启动幂等初始化）
- [x] 实现 LLM 提供方抽象层（自定义网关/DeepSeek/GLM 统一封装，真实跑通）
- **Status:** complete

### Phase 3: 智能体生成与意图解析
- [x] `POST /api/agents/generate` — 自然语言 → 结构化配置 JSON（真调 LLM）
- [x] LLM 意图解析提示词：提取领域/主题/时间范围/关键实体/搜索关键词
- [x] 按领域匹配预设工具集与提示词模板，生成 AgentConfig 入库
- [x] `GET /api/agents`、`GET /api/agents/{id}`、`PUT /api/agents/{id}`
- **Status:** complete

### Phase 4: LangGraph 引擎与 SSE 运行流
- [x] LangGraph 三节点工作流：搜集节点 → 分析节点 → 结论节点
- [x] 搜集节点：领域工具调度（RSS/arXiv/GitHub/akshare/爬取，按 agent.tools）
- [x] 分析节点：LLM 提炼关键情报
- [x] 结论节点：生成结构化 Markdown 报告
- [x] `POST /api/agents/{id}/run` 启动执行 + SSE 流式推送（StreamingResponse+后台线程）
- [x] SSE 消息格式：step_start / step_result / step_complete / report_ready / error
- [x] 节点级重试（2次），失败标 failed 不中断整体
- [x] RunRecord 入库（status、steps JSON、report_md）
- **Status:** complete（端到端真实跑通，生成真实情报报告）

### Phase 5: 前端页面
- [x] 仪表台 `/` — 智能体卡片列表 + 新建按钮（真实数据）
- [x] 生成页 `/agents/new` — 自然语言输入 + 领域快捷标签（真调 LLM）
- [x] 详情页 `/agents/[id]` — SSE 实时步骤流 + 历史运行（fetch streaming）
- [x] 编辑页 `/agents/[id]/edit` — 名称/工具开关/提示词模板（PUT 真实保存）
- [x] 报告页 `/reports/[id]` — Markdown 渲染 + 下载 .md（react-markdown）
- [x] 设置页 `/settings` — LLM/数据源状态/降级提示（health 只读，Key 在 .env）
- [x] SSE 前端消费（fetch streaming；自动重连待补，当前单次）
- [x] 前后端联调跑通（IP 访问，CORS 已配，生产模式无 HMR）
- **Status:** complete（6 页全完成，生产模式 IP 可用）
- **Status:** pending

### Phase 6: 错误处理、降级与收尾
- [ ] LLM 解析失败的用户友好提示
- [ ] 未配置 API Key 领域自动降级为纯搜索模式 + 页面提示
- [ ] 端到端跑通一个完整示例（如科技领域某主题）
- [ ] README 与运行说明
- [ ] 清理孤儿 run_record（run_243973a9ca90 卡 running）+ 超时回收机制
- **Status:** pending

### Phase 7: 高价值增强（定时运行 / 模板库 / 报告对比）
- 实现顺序（用户确认）：**7C 定时 → 7B 模板 → 7A 对比**
- [ ] 7C 定时自动运行：APScheduler + Schedule 表持久化
- [ ] 7B 模板库：独立 AgentTemplate 表 + /templates 页
- [ ] 7A 报告对比：段落级 diff，左右并排
- **Status:** pending

## Decisions Made（Phase 7）
| Decision | Rationale |
|----------|-----------|
| 顺序：定时→模板→对比 | 定时是质变(手动→自动)，模板让定时易用，对比最后加 |
| 定时用 APScheduler | 成熟 cron 库，随 FastAPI 启动，加一个依赖可接受 |
| 对比用段落级 diff | 报告结构化强(##块)，段落比对直观，行级噪点多 |
| 模板用独立 AgentTemplate 表 | 与 AgentConfig 分离，模板=蓝图，应用后生独立智能体 |

#### Phase 7C: 定时自动运行（先做）
**目标：智能体按 cron 定时自动跑，报告自动存档，无需手动点。**

子任务（每步独立验证）：
- [ ] 7C-1 装 APScheduler，写最小调度器模块 `app/scheduler.py`（BackgroundScheduler + add/remove/list job），单元测试一个每 30 秒打印的任务能触发
- [ ] 7C-2 建 Schedule 表（agent_id/cron_expr/enabled/last_run_at/created_at），crud.py 加 schedule CRUD
- [ ] 7C-3 lifespan 集成：启动时从 DB 重建所有 enabled 任务；关闭时优雅 shutdown
- [ ] 7C-4 定时触发逻辑：job 执行时调 run_agent(agent_id, cb=None) 静默跑，更新 last_run_at；失败记日志不中断调度器
- [ ] 7C-5 端点：POST /api/agents/{id}/schedule（建）、GET /api/agents/{id}/schedule、PUT（开关/cron）、DELETE
- [ ] 7C-6 前端详情页加"定时运行"区：开关 + cron 输入 + 最近定时运行时间 + 下次预计运行
- [ ] 7C-7 前端仪表台卡片加定时徽标 ⏰（有 enabled schedule 时显示）
- [ ] 7C-8 验证：建一个每分钟跑的测试 schedule，等 1 分钟确认自动生成报告入库；清理测试
- 难点：cron 时区（用本地时区）、APScheduler 与 SQLAlchemy session 线程安全（每次 job 新建 session）

#### Phase 7B: 模板库
**目标：常用情报需求存成模板，一键复用，不用每次从零描述。**

子任务：
- [ ] 7B-1 建 AgentTemplate 表（name/domain/intent_template/tools/prompt_template/created_at），crud.py 加 template CRUD
- [ ] 7B-2 端点：GET /api/templates（列表）、POST /api/templates（新建）、GET/PUT/DELETE /api/templates/{id}
- [ ] 7B-3 "从智能体存为模板"：POST /api/agents/{id}/as-template（用现有 agent 配置生成模板）
- [ ] 7B-4 前端 /templates 页：列表（卡片）+ 新建/编辑/删除
- [ ] 7B-5 前端生成页加"从模板新建"入口：选模板 → 预填 intent/tools/prompt（intent 可改）→ 正常生成流程
- [ ] 7B-6 侧栏导航加"模板库"项
- [ ] 7B-7 验证：建 2 个模板 → 从模板新建智能体 → 运行；删除模板不影响已生成智能体
- 预填语义：模板是蓝图，应用后生成独立 AgentConfig，两者无关联

#### Phase 7A: 报告对比
**目标：同智能体两次运行报告并排，看动态增减。**

子任务：
- [ ] 7A-1 后端 GET /api/reports/compare?ids=a,b：校验同 agent_id，返回两份 {meta, md}
- [ ] 7A-2 写 `app/diff.py`：按 `## ` 切段，段落级 diff（新增/删除/未变/改动）；返回结构化 diff 结果
- [ ] 7A-3 前端 /reports/compare 页：左右并排，渲染 diff（新增绿底、删除红底、未变灰、改动高亮）
- [ ] 7A-4 前端 Markdown diff 渲染：复用 react-markdown，给段落块加背景色 class
- [ ] 7A-5 入口：详情页历史运行列表加多选 + "对比"按钮 → 跳 /reports/compare?ids=a,b
- [ ] 7A-6 边界处理：不同智能体报告不可比（提示）；报告为空/失败的不可比
- [ ] 7A-7 验证：同智能体跑两次（改点关键词让内容有差异）→ 对比看新增/删除段正确
- 难点：段落匹配（按标题对齐，无标题段按顺序）；diff 算法用 difflib.SequenceMatcher 够用

## Key Questions
1. ~~用 SQLAlchemy 还是原生 sqlite3？~~ → **已定：SQLAlchemy**（可迁移 PG）
2. ~~前端 Next.js 用哪种 SSE 客户端消费方式？~~ → 待定 EventSource vs fetch streaming（Phase 5 决）
3. ~~Web Search 用哪个具体服务？~~ → **已定：Tavily**
4. LLM 调用是否用 LangChain 的 DeepSeek/GLM 封装，还是直接 HTTP？→ 待 Phase 2 决
5. ~~前后端是否在同一仓库 monorepo？~~ → **已定：Monorepo 同仓库**
6. ~~运行是同步阻塞还是后台任务？~~ → **已定：FastAPI BackgroundTasks**

## Decisions Made
| Decision | Rationale |
|----------|-----------|
| Monorepo（backend/ + frontend/） | 单人项目，共用配置，联调方便 |
| Web Search = Tavily | LLM agent 友好，结构化摘要，有免费额度 |
| 执行 = FastAPI BackgroundTasks | 单进程异步，SSE 同进程推送，初期无需额外依赖 |
| 数据层 = SQLAlchemy | 设计文档要求可迁移 PostgreSQL |

## Errors Encountered
| Error | Attempt | Resolution |
|-------|---------|------------|
|       | 1       |            |

## Notes
- 设计文档状态为"已批准"，日期 2026-07-02（今天），可直接进入实现
- 设计文档末尾"后期扩展点"（模板库/多用户/PDF/定时）不在当前范围
- 6 个 Key Questions 中 #3、#5、#6 设计文档未指定，需在 Phase 1 前与用户确认
- 规划文件位于项目根目录：task_plan.md / findings.md / progress.md
- 每完成一个 Phase 更新状态：pending → in_progress → complete
- 决策前重读本计划；所有错误记入 Errors Encountered
