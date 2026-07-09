# Task Plan: 情报智能体生成器 (Intelligence Agent Generator)

## Goal
按已批准设计文档（`2026-07-02-intelligence-agent-generator-design.md`）从零实现一个 Web 应用：用户用自然语言描述需求，系统生成并运行领域情报智能体（军事/金融/科技/教育/公司），LangGraph 跑搜集→分析→结论三节点工作流，SSE 实时推送步骤，结果存为 Markdown 报告并可下载。

## Current Phase
Phase 1-8 + 10 + 11 全部完成 ✅｜剩 Phase 9（多智能体协同）进行中

## Phases

### Phase 1: 项目骨架与基础设施
- [x] 建立仓库目录结构（backend/ 已建，frontend/ 待 Phase 5）
- [x] 后端 FastAPI 骨架（main.py、路由占位、CORS、健康检查）
- [x] 前端 Next.js (App Router) + Tailwind 骨架（Phase 5 已做）
- [x] SQLite 数据库初始化（SQLAlchemy 三表，启动自动 create_all）
- [x] `.env` 配置体系 + LLM provider 自动识别（DeepSeek/GLM）
- [x] 前后端联调跑通（Phase 5 已做）
- **Status:** complete

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

### Phase 6: 错误处理、降级与收尾
- [x] LLM 解析失败的用户友好提示（parse_intent 降级 + 前端错误态）
- [x] 未配置 API Key 领域自动降级为纯搜索模式 + 页面提示（@safe 容错 + health 显示数据源状态）
- [x] 端到端跑通多个完整示例（军事/教育/金融/科技等真实运行）
- [x] README 与运行说明（已写完整 README + 上传 GitHub）
- [x] 清理孤儿 run_record + 超时回收（@safe 节点级容错，失败不中断）
- **Status:** complete

### Phase 7: 高价值增强（定时运行 / 模板库 / 报告对比）
- 实现顺序（用户确认）：**7C 定时 → 7B 模板 → 7A 对比**
- [x] 7C 定时自动运行：APScheduler + Schedule 表持久化（单次/每天/每周）✅
- [x] 7B 模板库：独立 AgentTemplate 表 + /templates 页
- [x] 7A 报告对比：段落级 diff，左右并排
- **Status:** complete（7C 定时 ✅ / 7B 模板 ✅ / 7A 对比含 LLM 摘要+行级diff ✅）

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
- [x] 7C-1 装 APScheduler，写最小调度器模块 `app/scheduler.py`（BackgroundScheduler + add/remove/list job），单元测试一个每 30 秒打印的任务能触发
- [x] 7C-2 建 Schedule 表（agent_id/cron_expr/enabled/last_run_at/created_at），crud.py 加 schedule CRUD
- [x] 7C-3 lifespan 集成：启动时从 DB 重建所有 enabled 任务；关闭时优雅 shutdown
- [x] 7C-4 定时触发逻辑：job 执行时调 run_agent(agent_id, cb=None) 静默跑，更新 last_run_at；失败记日志不中断调度器
- [x] 7C-5 端点：POST /api/agents/{id}/schedule（建）、GET /api/agents/{id}/schedule、PUT（开关/cron）、DELETE
- [x] 7C-6 前端详情页加"定时运行"区：开关 + cron 输入 + 最近定时运行时间 + 下次预计运行
- [x] 7C-7 前端仪表台卡片加定时徽标 ⏰（有 enabled schedule 时显示）
- [x] 7C-8 验证：建一个每分钟跑的测试 schedule，等 1 分钟确认自动生成报告入库；清理测试
- 难点：cron 时区（用本地时区）、APScheduler 与 SQLAlchemy session 线程安全（每次 job 新建 session）

#### Phase 7B: 模板库
**目标：常用情报需求存成模板，一键复用，不用每次从零描述。**

子任务：
- [x] 7B-1 建 AgentTemplate 表（name/domain/intent_template/tools/prompt_template/created_at），crud.py 加 template CRUD
- [x] 7B-2 端点：GET /api/templates（列表）、POST /api/templates（新建）、GET/PUT/DELETE /api/templates/{id}
- [x] 7B-3 "从智能体存为模板"：POST /api/agents/{id}/as-template（用现有 agent 配置生成模板）
- [x] 7B-4 前端 /templates 页：列表（卡片）+ 新建/编辑/删除
- [x] 7B-5 前端生成页加"从模板新建"入口：选模板 → 预填 intent/tools/prompt（intent 可改）→ 正常生成流程
- [x] 7B-6 侧栏导航加"模板库"项
- [x] 7B-7 验证：建 2 个模板 → 从模板新建智能体 → 运行；删除模板不影响已生成智能体
- 预填语义：模板是蓝图，应用后生成独立 AgentConfig，两者无关联

#### Phase 7A: 报告对比
**目标：同智能体两次运行报告并排，看动态增减。**

子任务：
- [x] 7A-1 后端 GET /api/reports/compare?ids=a,b：校验同 agent_id，返回两份 {meta, md}
- [x] 7A-2 写 `app/diff.py`：按 `## ` 切段，段落级 diff（新增/删除/未变/改动）；返回结构化 diff 结果
- [x] 7A-3 前端 /reports/compare 页：左右并排，渲染 diff（新增绿底、删除红底、未变灰、改动高亮）
- [x] 7A-4 前端 Markdown diff 渲染：复用 react-markdown，给段落块加背景色 class
- [x] 7A-5 入口：详情页历史运行列表加多选 + "对比"按钮 → 跳 /reports/compare?ids=a,b
- [x] 7A-6 边界处理：不同智能体报告不可比（提示）；报告为空/失败的不可比
- [x] 7A-7 验证：同智能体跑两次（改点关键词让内容有差异）→ 对比看新增/删除段正确
- 难点：段落匹配（按标题对齐，无标题段按顺序）；diff 算法用 difflib.SequenceMatcher 够用

---

### Phase 8: 智能体记忆 / 累积分析 ✅ 完成
**目标：智能体记住历次报告关键结论，下次运行参考"上次研判了什么、这次有何变化"，报告有连续性而非每次从零。**

子任务：
- [x] 8-1 AgentMemory 表（agent_id/key_points JSON/updated_at），每次运行后由 LLM 提取本次报告 3-5 条关键结论存入
- [x] 8-2 engine 分析节点注入"历史记忆"：把上次 key_points 作为上下文给 LLM，要求"对比上次，标注变化"
- [x] 8-3 详情页显示"智能体记忆"区（最近 N 次的关键结论时间线）
- [x] 8-4 端点 GET /api/agents/{id}/memory（查看/管理记忆，可手动编辑/清空）
- [x] 8-5 验证：同智能体跑两次（间隔有变化），第二次报告明确引用"相比上次…"
- 难点：记忆长度控制（只存结论不存全文）；避免 LLM 照抄旧结论
- **Status:** complete（AgentMemory表+读记忆注入+提取记忆+详情页记忆区 ✅）

### Phase 9: 多智能体协同 / 主题聚合（待做）
**目标：复杂情报需求（如"评估某公司投资价值"）组合多个智能体报告 → LLM 综合研判。**

子任务：
- [ ] 9-1 AggregateTask 表（name/agent_ids JSON/theme/created_at），选 N 个智能体 + 主题
- [ ] 9-2 聚合运行：取各智能体最新报告 → LLM 综合分析（多角度交叉印证）→ 综合报告
- [ ] 9-3 端点 POST /api/aggregate（建聚合任务 + 触发运行）+ GET /api/aggregate/{id}
- [ ] 9-4 前端 /aggregate 页：选智能体（多选）+ 输入综合主题 → 生成综合报告
- [ ] 9-5 侧栏加"综合研判"入口
- [ ] 9-6 验证：选"财务+舆情+竞品"3 智能体 → 综合报告交叉印证各角度
- 难点：多报告 token 控制（各取摘要）；避免简单拼接要真综合

### Phase 10: 报告搜索 / 筛选 ✅ 完成（原收藏改为搜索筛选）
**目标：好报告标星收藏 + 加批注，方便从历史中回找。**

子任务：
- [x] 10-1 ReportMark 字段（starred BOOLEAN/note TEXT 加到 RunRecord 或独立表）
- [x] 10-2 端点 PUT /api/reports/{id}/mark（标星/取消）+ PUT /api/reports/{id}/note（批注）
- [x] 10-3 报告列表加星标筛选（只看收藏）+ 批注预览
- [x] 10-4 报告详情页加标星按钮 + 批注编辑区
- [x] 10-5 验证：标星 3 份 + 加批注 → 列表筛选收藏 → 详情看批注
- 简单，工作量小
- **Status:** complete（改搜索+筛选替代收藏，删标星UI保留DB字段 ✅）

### Phase 11: 自然语言追问报告 ✅ 完成
**目标：看完报告想深入某点，直接对话追问，LLM 基于该报告上下文回答。**

子任务：
- [x] 11-1 端点 POST /api/reports/{id}/ask（接收问题，LLM 基于报告 md 回答）
- [x] 11-2 前端报告详情页加"追问"对话框（聊天式 UI，保留本轮对话历史）
- [x] 11-3 上下文管理：报告 md 作为 system context，追问可多轮（保留会话）
- [x] 11-4 边界：问题与报告无关时提示"建议基于本报告内容追问"
- [x] 11-5 验证：看报告后追问"这个结论依据是什么""展开风险"→ LLM 基于报告回答
- 难点：多轮对话上下文长度；防止 LLM 跑题到报告外
- **Status:** complete（/ask端点多轮+报告页+智能体详情页双入口追问 ✅）

### 暂不做（记录待定）
- **报告订阅/推送通知**（定时跑完通知）：功能明确但需接通知服务（桌面/邮件/微信），暂记不做

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
