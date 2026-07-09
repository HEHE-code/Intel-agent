# Progress Log

## Session: 2026-07-02

### Phase 0: 规划初始化
- **Status:** complete
- **Started:** 2026-07-02
- Actions taken:
  - 阅读设计文档 2026-07-02-intelligence-agent-generator-design.md
  - 加载 planning-with-files skill
  - 检查项目目录：仅有设计文档与 .claude 目录，无既有规划文件
  - 读取 task_plan / findings / progress 模板
  - 创建三份规划文件，将设计文档提炼为 6 阶段计划
- Files created/modified:
  - task_plan.md (created)
  - findings.md (created)
  - progress.md (created)

### Phase 1: 项目骨架与基础设施
- **Status:** in_progress（原型先行）
- Actions taken:
  - 用户要求"先做个原型出来" → 决定先做 HTML 可点击原型验证设计，再落 Next.js
  - 加载 ui-ux-pro-max skill，生成并持久化设计系统到 design-system/intelligence-agent-generator/MASTER.md
  - 与用户确认：明暗双主题 + 全部 6 页
  - 用户反馈：增量交付，分功能分点写（已存记忆 incremental-work-style）
  - **步骤①完成**：prototype/index.html — HTML shell + Tailwind CDN + 双主题切换(含 localStorage 记忆) + 侧栏导航 + JS 路由 + mock 数据层 + 仪表台页（3 统计卡 + 智能体卡片网格）
  - 浏览器验证：python3 -m http.server 8765；暗色渲染正常，主题切换到亮色正常；图像分析确认结构完整无布局问题
- Files created/modified:
  - prototype/index.html (created)
  - prototype/proto-step1-dark.png, proto-step1-light.png (验证截图)
  - findings.md, task_plan.md, progress.md (updated)
- 遗留：仅 favicon.ico 404（无害，可忽略）
- 下一步：待用户确认步骤①风格方向 → 步骤②生成页

### 原型步骤②：生成页
- **Status:** complete
- Actions taken:
  - 填充 #page-new：领域快捷标签（可单选高亮）+ 自然语言输入框（实时字数统计）+ 示例 chips + 生成按钮
  - runGenerate() 模拟意图解析动画：3 步依次推进（解析意图→匹配工具集→生成配置），每步打勾+详情
  - guessDomain() 关键词推断领域；finishGenerate() 成功态 + 「返回仪表台/前往运行」双按钮
  - 接入路由（renderNew）+ 生成按钮绑定
  - 浏览器验证：示例 chip 填入「半导体先进制程进展」→ 生成 → 领域正确推断为「科技」→ 3 步全打勾 → 成功态双按钮；图像分析确认布局无破损
- Files created/modified:
  - prototype/index.html（#page-new + renderNew/runGenerate/finishGenerate/guessDomain/domainTools）
  - prototype/proto-step2-new-idle.png, proto-step2-new-done.png
- 下一步：步骤③详情页 + SSE 实时运行流动画

### 原型步骤③：详情页（含 SSE 实时运行流）
- **Status:** complete
- Actions taken:
  - 填充 #page-agent：头部信息区 + 运行控制条 + SSE 流容器 + 空态 + 右侧元信息/工具集 + 历史运行列表
  - renderAgent()：渲染头部(名称/领域/返回/编辑)、元信息(创建/运行次数/状态)、工具集、历史运行(含 failed 记录)
  - runAgent()：核心 SSE 模拟 —— 3 节点(搜集/分析/结论)逐节点、逐步骤推送，每步带 [type] 标记(start/result/complete)，节点图标 pending○→running◌→done✓ 推进
  - finishRun()：绿色"报告已生成 · 查看报告→" + 按钮重置"再次运行"
  - 接入路由 + 运行按钮绑定
  - 浏览器验证：详情页初始态完整 → 点运行 → mid-run(搜集✓分析✓结论○待运行) → 完成态(三节点全✓+绿色报告链接)；图像分析三阶段均确认无破损
- Files created/modified:
  - prototype/index.html（#page-agent + TOOL_SET/AGENT_DETAIL/renderAgent/resetRunArea/runAgent/finishRun）
  - prototype/proto-step3-agent-idle/running/done.png
- 下一步：步骤④编辑页

### 原型步骤④⑤⑥：编辑页 / 报告页 / 设置页
- **Status:** complete
- Actions taken:
  - **④编辑页**：renderEdit() 渲染名称输入 + 工具开关(toggle,aria-pressed,蓝/灰态切换) + 提示词模板；saveEdit() 回写 mock 并显示"已保存"
  - **⑤报告页**：REPORTS mock 含完整 Markdown；mdToHtml() 极简解析器(h1/h2/h3/列表/表格/引用/粗体)；renderReport() 渲染 + 面包屑；downloadReport() Blob 下载 .md；.prose-report 排版样式
  - **⑥设置页**：renderSettings() LLM 双卡选择(DeepSeek/GLM) + 3 个 API Key 输入；updateDegrade() 按 DOMAIN_DEPS 实时计算受影响领域 → 琥珀降级/绿色全配提示；saveSettings() 保存反馈
  - 全部接入路由 + 按钮绑定
- 验证：编辑页 toggle 切换 OK；报告页 Markdown 正确渲染(H1/blockquote/H2/H3/列表/表格)；设置页降级实时计算(填 Tavily 后未配置 3→2，受影响领域收窄)；下载逻辑数据正确(文件名+内容)；全程 0 console error(仅 Tailwind CDN 生产警告，预期内)
- Files created/modified:
  - prototype/index.html（1044 行，含全部 6 页）
  - prototype/proto-step4-edit.png, proto-step5-report.png, proto-step6-settings-degraded/partial.png
- **🎉 原型 6 页全部完成，可点击流程跑通**

### 原型总结
- 单文件 HTML(1044行) + Tailwind CDN + 内嵌 JS，浏览器直开无需构建
- 6 页：仪表台/生成/详情(含 SSE 流)/编辑/报告(含下载)/设置(含降级)
- 明暗双主题切换 + localStorage 记忆
- mock 数据驱动，纯前端动画模拟后端行为
- 访问：http://192.168.184.128:8765/index.html（python3 -m http.server 8765，已在后台运行）

### 正式实现：数据源与 Key 策略确认
- 用户确认：自用 + 只有 LLM Key，数据源用免 Key 免费方案
- LLM：DeepSeek/GLM 自动识别（按 .env 哪个 Key 存在自动选）
- 数据源映射（免Key默认 + 可选升级）：见 findings.md
  - 通用搜索 DuckDuckGo(可升 Tavily) / 金融 yfinance(可升 AlphaVantage) / 新闻 GDELT+RSS(可升 NewsAPI) / 论文 arXiv / GitHub 爬取 / RSS+爬取
- 后端优先实现（用户选择）

### Phase 1 后端骨架（正式栈）
- **Status:** complete
- Actions taken:
  - 系统无 pip/venv/sudo → 装 uv（~/.local，免 root）建 .venv 装依赖
  - 建 backend/ 结构：app/{main,config,db,models}.py + app/api/{health,agents,reports}.py
  - config.py：pydantic-settings 读 .env；active_llm_provider 自动识别 DeepSeek/GLM
  - models.py：SQLAlchemy 三表 AgentConfig/RunRecord/DomainToolConfig（字段对齐设计文档）
  - main.py：FastAPI + CORS + lifespan 建表 + 路由挂 /api；health 端点返回 provider/数据源状态
  - requirements.txt：FastAPI/uvicorn/sqlalchemy/langchain/langgraph + 免Key数据源库(duckduckgo-search/yfinance/arxiv/feedparser/readability-lxml)
  - .env.example + .env（Key 暂空）+ 根 .gitignore
- 验证：8001 端口启动 OK；/api/health 返回 status:ok + 正确降级识别(llm_provider:null)；三表建表成功字段齐全；agents/reports 占位路由 OK；openapi/root 200；provider 自动识别三种场景(DeepSeek/GLM/空)逻辑全对
- 注意：8000 端口被其他进程占用，后端固定用 8001
- Files created/modified:
  - backend/{requirements.txt,.env.example,.env} + backend/app/{__init__,main,config,db,models}.py + backend/app/api/{__init__,health,agents,reports}.py
  - .gitignore (根)
- 下一步：Phase 2 数据层工具映射 + LLM provider 抽象层，或直接做"后端最小闭环"（一个领域真调 LLM+搜索跑通）

### Phase 2（块1）：LLM provider 抽象层
- **Status:** complete
- Actions taken:
  - 探测用户提供的 LLM 端点 http://172.16.3.6:8589 → 是"精灵云-AI-API"OpenAI 兼容网关，提供 glm-5.1/GLM-5.2/xopdeepseekv4pro 等
  - raw curl 验证 /v1/chat/completions 可用，glm-5.1 正常返回
  - config.py 升级：支持自定义 LLM_BASE_URL+LLM_API_KEY+LLM_MODEL（custom 优先级最高），保留 DeepSeek/GLM 自动识别兜底；新增 llm_base_url_resolved/llm_api_key_resolved/llm_model_resolved
  - 新建 app/llm.py：build_chat_model() 统一封装（三者都走 langchain_openai.ChatOpenAI），LLMNotConfiguredError，get_llm() 单例
  - health 端点升级：暴露 provider/base_url/model + key末4位
  - .env 写入用户内网网关配置（LLM_BASE_URL/KEY/MODEL=glm-5.1）
- 验证：真实代码路径 build_chat_model(temperature=0).invoke() 返回 '2' ✅；/api/health 显示 provider=custom available=true model=glm-5.1 key_hint=0b43
- Files created/modified:
  - backend/app/config.py（升级）, backend/app/llm.py（新建）, backend/app/api/health.py（升级）, backend/.env
- 后端运行：uvicorn app.main:app --port 8001（pid 79410 在跑）
- 下一步：Phase 2 块2 领域工具集映射 + 免Key数据源工具实现（duckduckgo/yfinance/arxiv/feedparser）+ DomainToolConfig CRUD

### Phase 2 块2：领域工具集（领域专项源直爬架构）
- **Status:** complete
- 架构决策变更：放弃通用搜索（cn.bing 中文分词差召回不可用、DDG/Yahoo/rsshub 被墙、LLM 网关无联网），改走**领域专项源直爬**——这才是设计文档"领域工具集"本意，国内可达+结构化+质量高
- 5 个核心工具全部真实验证通过：
  - ① arXiv（教育/科技）：Atom XML，follow_redirects，按 entry 切分解析，4篇全取 ✅
  - ② GitHub Search API（科技）：替代 trending，按 stars+时间过滤，langchain/autogen ✅
  - ③ 金融 akshare（财经）：finance_news 东财快讯200条 + stock_news 个股新闻 + stock_quote 行情(偶发反爬,@safe容错) ✅
  - ④ fetch_url（公司/军事通用）：readability-lxml 提正文，东财文章正文干净 ✅
  - ⑤ RSS（军事）：人民网军事/中国军网/新华国际，多源聚合6条 ✅
- 注册表 registry.py：9个工具 ToolSpec(name/func/label/needs_arg) + DOMAIN_TOOLS 5领域映射 + DOMAIN_PROMPTS
- crud.py：AgentConfig/RunRecord/DomainToolConfig 全 CRUD + sync_domain_tool_configs 幂等初始化
- main.py lifespan：建表后调用 sync_domain_tool_configs
- 验证：数据层全链路(建表/初始化14条/建agent/查启用/关工具/建run/查历史)通过；后端重启 health 正常(启动慢~8s 因 akshare/feedparser 导入)
- Files: backend/app/tools/{base,web_search,arxiv,github,finance,fetch_url,rss,registry}.py + backend/app/crud.py + main.py升级
- 后端运行：uvicorn app.main:app --port 8001（pid在跑）
- 下一步：Phase 3 智能体生成与意图解析（POST /api/agents/generate + LLM 解析意图 + agents CRUD 路由）

### Phase 3：智能体生成与意图解析
- **Status:** complete
- Actions taken:
  - 新建 app/intent.py：parse_intent() 用 LLM 提取领域/主题/时间范围/关键实体/搜索关键词/智能体名，输出 ParsedIntent；_extract_json 容错(去代码块/找{到})；_fallback_domain 关键词兜底；LLM不可用或失败降级
  - 重写 app/api/agents.py：POST /generate(真调LLM解析→入库) + GET 列表 + GET /{id} 详情 + PUT /{id} 编辑 + 404；AgentOut 响应模型
- 验证：4领域意图解析全对(自动生成中英混合关键词如"Asia-Pacific military deployment")；curl 端到端：generate返回 agt_id+正确domain+工具集+提示词模板，list/detail/update(改名+关工具)/404 全通过
- Files: backend/app/intent.py(新建), backend/app/api/agents.py(重写)
- 后端运行：8001 端口(pid在跑)
- 下一步：Phase 4 LangGraph 三节点工作流 + SSE 实时运行流（搜集→分析→结论 + POST /{id}/run）

### Phase 5（前端骨架）
- **Status:** 进行中
- 环境确认：Node v22 + npm 10 已就绪（无需装环境）
- 创建 Next.js 16 + React 19 + Tailwind v4 + TS 骨架（create-next-app，src-dir）
- ⚠️ frontend/AGENTS.md 警告此 Next 版本有 breaking changes → 按原则①读 node_modules/next/dist/docs 确认用法：params 是 Promise(await)、交互组件需'use client'、Tailwind v4 用 @theme
- 设计系统迁移：globals.css 用 @theme inline 映射双主题语义 token(照原型)、Fira Sans/Code 字体
- 组件：ThemeProvider(use client, localStorage记忆)、Sidebar(client, 导航+主题切换)
- lib/api.ts：API_BASE 常量 + Agent/Report 类型 + api() fetch 封装
- 根 layout：字体+ThemeProvider+Sidebar 壳
- 待验证：dev server 启动 + 浏览器渲染骨架

**前端骨架验证结果（2026-07-02）：**
- dev server 就绪 http://localhost:3000（1.3s启动）
- 浏览器渲染：暗色骨架正常（侧栏logo+导航+主题按钮、主区仪表台标题+新建按钮），0 console error
- 主题切换：暗↔亮切换正常，localStorage 记忆
- 前后端联调打通：浏览器从 3000 跨域 fetch 8001/api/agents 成功(CORS ok)，拿到真实智能体"亚太防务动态监测(自定义)"
- 前端运行：npm run dev（后台跑）
- 下一步：逐页填充——仪表台(真实列表)→生成→详情+SSE→编辑→报告→设置

### Phase 5 页①：仪表台
- **Status:** complete
- 后端小增强：AgentOut 补 last_run_at/last_status/run_count（从 RunRecord join），list/detail 带出；清理残留死代码
- 前端：page.tsx 改 Server Component，force-dynamic，fetch /api/agents，渲染统计卡(总数/运行中/累计报告)+卡片网格(领域标签+状态徽章+最近运行+运行次数)；Agent类型补字段；空态/错误态
- 验证：0 console error；图像分析确认统计卡1/0/2、卡片(军事标签+已完成+2次运行)、暗色主题、布局完整；点卡片跳 /agents/[id]（预期404，详情页待做）
- Files: backend/app/api/agents.py(增强), frontend/src/lib/api.ts(Agent类型), frontend/src/app/page.tsx(重写)
- 下一步：页②生成页（接 POST /api/agents/generate）

### Phase 5 页②：生成页
- **Status:** complete
- 前端：/agents/new client 组件，领域快捷标签(单选高亮) + 自然语言输入(字数统计) + 示例 chips + 生成按钮 + 解析过程动画 + 错误态；submit 调 POST /api/agents/generate 后 router.push('/') 跳回仪表台
- 验证：0 console error；点示例「特斯拉Q2财报与舆情」→ 生成 → 真调 LLM → 跳回仪表台，智能体总数 1→2，新卡片「企业财报舆情分析员」公司领域(LLM 自动识别特斯拉→company) + 空闲状态
- Files: frontend/src/app/agents/new/page.tsx
- 下一步：页③详情页 + SSE 实时运行流（核心交互，接 POST /{id}/run）

### Phase 5 页③：详情页 + SSE 实时运行流
- **Status:** 代码完成，验证中
- 前端：/agents/[id] client 组件，use(params) 读动态路由；load() 并发 fetch agent+reports；run() 调 runAgentStream(fetch streaming 消费 SSE，逐帧解析 data:)；events 状态聚合三节点(search/analyze/report)状态 pending/running/done；头部+运行控制+SSE流+元信息+工具集+历史运行
- api.ts 加 runAgentStream(SSE streaming 消费) + SSEEvent 类型
- 问题：IP 访问时 dev HMR WebSocket 握手失败→client 组件反复重渲染卡"加载中"；localhost 访问正常
- 解法：生产 build(next build+start, 绑0.0.0.0)无HMR，IP可用；dev 留改代码用
- 下一步：build 完成后用 IP 验证详情页 + 真实运行 SSE 流

**详情页验证结果（2026-07-02）：**
- IP 访问卡加载问题 → 根因 dev HMR WebSocket 在 IP 握手失败致 client 组件反复重渲染；解法：生产 build(next build+next start -H 0.0.0.0)，无 HMR，IP 可用
- localhost 与 IP 访问均正常加载详情页
- SSE 实时运行流端到端完美：点运行→搜集✓(RSS5+搜索5=10条)→分析✓→结论✓→绿色"运行完成"→"查看最新报告"链接→历史运行刷新→按钮变"再次运行"
- 生产前端运行：next start -H 0.0.0.0 -p 3000（无HMR，IP可用）
- 注意：改代码需重新 build；dev 模式仅 localhost 可用

### Phase 5 页④：报告页
- **Status:** complete
- 前端：/reports/[id] Server Component，await params，fetch /api/reports/{id}；Markdown client 子组件(react-markdown)；.prose-report 排版样式(h1/h2/h3/列表/引用/表格/代码)；下载按钮 a[href=API_BASE/reports/{id}/download] download
- 安装 react-markdown（复用成熟库，原则④）
- 验证：IP 访问报告页 Markdown 完整渲染(H1/blockquote/H2分节/H3/列表)，下载端点返回真实 .md(2509字节)；0 关键 console error
- 启动注意：本地 next 二进制路径 frontend/node_modules/.bin/next（npx 会装远程，需用本地）
- Files: frontend/src/app/reports/[id]/page.tsx, frontend/src/components/Markdown.tsx, globals.css(.prose-report)
- 下一步：页⑤编辑页

### Phase 5 页⑤：编辑页
- **Status:** complete
- 前端：/agents/[id]/edit client 组件，use(params)；加载 agent 填充名称/工具(toggle 开关)/提示词；save 调 PUT /api/agents/{id}
- 踩坑：首次 build 后运行时 404（.next 缓存残留）→ clean build(rm -rf .next) 后正常；启动注意用本地 next 二进制(./node_modules/.bin/next)，npx 会装远程
- 验证：改名+关 web_search 工具→保存→后端数据真实更新(name 变、tools 变)；已恢复原数据

### Phase 5 页⑥：设置页
- **Status:** complete
- 前端：/settings Server Component，fetch /api/health 展示 LLM 配置(provider/base_url/model/key脱敏••••0b43)+数据源状态(3项未配置)+降级提示(琥珀)+配置指引(Key 在 backend/.env 管理，安全)
- 设计决策：Key 只读展示不前端编辑（安全：Key 属后端 .env，遵循架构原则⑥）
- 验证：IP 访问设置页 LLM 配置完整正确显示，降级提示，配置指引 4 步

### Phase 5 完成 🎉
- 6 页全部完成并验证：仪表台/生成/详情(SSE流)/编辑/报告(Markdown+下载)/设置
- 生产模式运行：next start -H 0.0.0.0 -p 3000（无 HMR，IP 可用）
- 后端：uvicorn --host 0.0.0.0 --port 8001（IP 可用，CORS 含 IP）
- 访问：http://192.168.184.128:3000
- 完整闭环：生成智能体→运行(SSE实时)→看真实报告→下载.md；编辑/设置可调

### 搜集质量优化（修"资料完全缺失"问题）
- **Status:** complete
- 问题：报告常说"资料中完全缺失与XXX相关的直接信息"——根因 engine.py 用 intent 前15字截断当搜索词 + RSS 不过滤 + Bing 中文分词差
- 实测诊断：百度程序化抓取被验证码拦(httpx+Playwright 都弹"百度安全验证")，不可用；cn.bing 对复合短语分词差("美日韩"→"美")但对**简单高频词+site:权威源**召回好
- 修复三件套：
  1. web_search.search 加 site 参数(限定权威源)
  2. registry 加 DOMAIN_SITES(军事news.cn/81.cn/people.com.cn 等) + DOMAIN_ANCHOR(军事"军事演习"等简单高频锚词) + is_noise_title 噪声过滤(百科/翻译/学校/早报错配)
  3. engine 搜索节点重写：_resolve_keywords 运行时调 parse_intent 拿精准词；用 锚词+关键词(多) site:首选权威源 搜；RSS 按关键词过滤；去重+噪声过滤
- 验证：军事agent(亚太军演)搜索从"百度百科/QQ邮箱"噪声 → "环球网军事/国防部/西陆/中国军网/新华军事"真实军源；完整运行报告从"资料完全缺失"→ 实质内容(海军访塞舌尔/巴阿反恐/上合联演)+趋势研判+诚实识别缺口(缺美日韩当期联演)
- Files: web_search.py, registry.py, rss.py, engine.py
- 局限：百度验证码无解(需付费API)；宽泛intent仍可能缺特定事件，但不再全是缺口

### UX 修复：点运行后空白期
- **Status:** complete
- 问题：点运行后过一会才显示工作流——根因 _search_node 第一步 _resolve_keywords 是 LLM 调用(10-30s)，发生在首个 SSE 事件前，前端这段时间是空占位
- 修复后端：_search_node 进节点先发 step_start"正在解析情报需求…"事件，再跑 parse_intent；解析完发 step_result 显示关键词
- 修复前端：running && events.length===0 时显示"正在启动工作流…"脉动加载态(而非"点击运行"空占位)
- 验证：点运行后立即收到"正在解析情报需求"→"关键词：亚太军事部署,美日韩演习,…"→ 搜集命中，全程无空白期
- Files: engine.py(_search_node 前置事件), agents/[id]/page.tsx(加载态分支)

### Phase 7 计划确认（2026-07-03）
- 三个高价值功能：定时运行(7C) / 模板库(7B) / 报告对比(7A)
- 实现顺序：7C → 7B → 7A（用户确认，定时是质变优先）
- 决策：APScheduler 调度 / 段落级 diff / 独立 AgentTemplate 表
- 计划详情见 task_plan.md Phase 7
- 下一步：先做 7C 定时自动运行

### Phase 7C：定时自动运行
- **Status:** 后端+前端完成，端到端验证中
- 7C-1: 装 APScheduler 3.11.3 + scheduler.py(单例 BackgroundScheduler, add/remove/rebuild job, 时区 Asia/Shanghai, job 新建 session 线程安全) + Schedule 表
- 7C-2: crud.py 加 schedule CRUD(get/upsert/delete/list)
- 7C-3: main.py lifespan 集成 start_scheduler(重建任务)/shutdown_scheduler
- 7C-4: _run_agent_job 调 run_agent(cb=None) 静默跑 + 更新 last_run_at
- 7C-5: schedules 端点 POST/GET/PUT/DELETE + cron 校验(段数+CronTrigger)
- 7C-6: 前端 ScheduleSection 组件(开关+cron输入+保存/删除+最近运行) 接入详情页右侧栏
- 7C-7: 后端 AgentOut 加 has_schedule + 仪表台卡片 ⏰ 徽标
- 验证：端点 POST/GET/PUT/校验(400) 全通过；前端定时区+徽标渲染正确(图像分析确认)
- 下一步：7C-8 等定时触发自动生成报告确认

**7C-8 端到端验证通过（2026-07-07）：**
- 设测试 cron(41分) → 10:41 自动触发 → 10:42:20 完成，last_run_at 更新
- 生成新报告：1011字/3步/completed，无人手动点击
- 已恢复 cron 为 0 9 * * *(每天9点)
- **7C 定时运行完整闭环：cron配置→调度器→自动跑→报告存档→前端徽标/定时区**

### Phase 7C 完成
- 定时运行全功能：APScheduler 单例 + Schedule 表持久化 + lifespan 重建 + 端点 + 前端定时区 + 仪表台徽标
- 验证：单元(调度器触发)+端点(CRUD+校验)+前端(定时区+徽标渲染)+端到端(cron自动生成报告)
- Files: scheduler.py, models.py(Schedule), crud.py(schedule CRUD), api/schedules.py, main.py(lifespan), api/agents.py(has_schedule), ScheduleSection.tsx, agents/[id]/page.tsx, page.tsx(徽标), api.ts
- 下一步：7B 模板库

### 7C 增强：可视化定时 UI（替代 cron 输入）
- **Status:** complete
- 用户反馈：cron 对用户不友好 → 改可视化选择
- 后端：Schedule 表加 run_type(once/daily/weekly)+once_at；scheduler.py 支持 DateTrigger(once)+CronTrigger(daily/weekly)；once 触发后自动 enabled=False；schedules 端点改收 run_type/hour/minute/weekday/once_date，转换 cron
- 前端：ScheduleSection 重写——频率单选(单次/每天/每周)+时间(时:分下拉)+单次日期选择+每周周几选择+可读描述"将于X自动运行"，完全隐藏 cron
- 验证：后端 once/daily/weekly + 校验(过去时间/非法类型 400) 全通过；前端三种模式 UI 正确切换(单次出日期、每周出周几)
- 数据库迁移：旧 schedule 表删表重建(SQLAlchemy drop+create)
- 启动坑：next start 端口被旧进程占(EADDRINUSE)需先 kill 旧 pid
- 下一步：7B 模板库

### Phase 4：LangGraph 引擎与 SSE 运行流
- **Status:** complete
- Actions taken:
  - 新建 app/engine.py：WorkflowState(TypedDict) + 三节点(_search_node/_analyze_node/_report_node) + _with_retry 节点级重试(2次) + _emit SSE回调 + build_graph(LangGraph编排) + run_agent(建RunRecord→顺序执行带回调→落库)
  - 搜集节点：按 agent.tools 调度注册表工具，多关键词，去重，上限12条(控token)
  - 分析节点：LLM(temperature=0) 提炼关键情报
  - 报告节点：LLM(temperature=0.3) 生成 Markdown 报告(限800字加速)
  - agents.py 加 POST /{id}/run：StreamingResponse + 后台线程 + queue 传事件，media_type=text/event-stream
  - reports.py 实现：GET 列表/GET {id}详情/GET {id}/download(.md原文)
- 性能发现：glm-5.1 长文本生成慢(单次分析LLM 28s/945字)，三次LLM+搜集35s 总耗时2-3分钟。已优化：资料上限20→12、报告限800字。根本解法是SSE流式(已实现)，前端不卡
- 启动方式：nohup .venv/bin/python -m uvicorn ... & disown（source/exec/setsid 在此环境不稳）
- 后端运行：8001 端口
- 下一步：等 Monitor 确认端到端 SSE 流跑通 + 真实报告生成

**端到端验证结果（2026-07-02）：**
- SSE 流完整跑通：10 个事件按序推送（search step_start→2×step_result命中→step_complete→analyze三事件→report→report_ready）
- 真实报告生成并落库：809字 Markdown，3步日志，status=completed
- 报告质量高：诚实标注情报缺口、从RSS提炼真实关键动态(无人机后勤/军地协同/A2AD)、有趋势研判与行动建议
- GET /api/reports 列表 + GET /{id} 详情 + GET /{id}/download(.md原文) 全验证通过
- 注意：第二次运行留了一条 status=running 的孤儿记录（run_243973a9ca90），是之前超时测试残留，不影响

## Test Results
| Test | Input | Expected | Actual | Status |
|------|-------|----------|--------|--------|
|      |       |          |        |        |

## Error Log
| Timestamp | Error | Attempt | Resolution |
|-----------|-------|---------|------------|
|           |       | 1       |            |

## 5-Question Reboot Check
| Question | Answer |
|----------|--------|
| Where am I? | Phase 4 完成（LangGraph+SSE 端到端真实跑通，生成真实情报报告），下一步 Phase 5 前端 |
| Where am I going? | Phase 2-4 后端(数据层→意图解析→LangGraph/SSE) → Phase 5 前端 Next.js |
| What's the goal? | 实现情报智能体生成器 Web 应用（见 task_plan.md Goal） |
| What have I learned? | 见 findings.md（设计文档已定技术栈与 API） |
| What have I done? | 初始化规划三文件，尚未开始编码 |

---
*Update after completing each phase or encountering errors*

### 教育领域工具修复（"数据真空"问题，2026-07-07）
- **Status:** complete
- 问题：教育智能体报告说"数据真空"——根因工具配错(arXiv搜不到分数线)+cn.bing site:限定对教育站点不灵
- 实测：百度程序化被验证码拦；cn.bing 的 site:eol.cn/gaokao.com 完全不生效(返回旅游/政府页)；eol.cn 院校列表 API(api.eol.cn)可用且结构化
- 修复：新建 gaokao.py 工具(调 api.eol.cn 按城市/关键词搜院校,含985/211/类型/层次)；registry 注册 gaokao_schools；教育领域工具改为 [gaokao_schools, web_search]；锚词改"高考 录取 分数线"；提示词覆盖择校场景
- engine：gaokao_schools 单独处理,取 max_results=12(原默认4太少)
- 验证：搜集从"arxiv 0条+网页噪声" → gaokao 12所真实院校(交大/西工大/西电/陕师大等)+网页；报告从"数据真空"→ 列出真实院校+判断550报985滑档+建议拓宽到西电/长安大学等
- 旧教育智能体 tools 已 DB commit 更新
- Files: tools/gaokao.py(新), registry.py, engine.py

### 分析逻辑重写（"给具体结论而非原则"，2026-07-07）
- **Status:** complete
- 问题：报告只给原则不给具体结论（如"无法判定能报哪所"），违背情报智能体本意
- 修复：engine 分析/结论节点按领域强化提示词
  - 教育分析节点：明确要求解析用户条件(分数/位次/科类/地域)+院校按录取难度分冲稳保三档+每档2-4所具体学校+适配专业+理由+诚实标注数据缺口
  - 教育结论节点：必须输出冲稳保三档表格(学校|层级|推荐专业|理由)+风险评估+填报策略
  - 其他领域：分析节点也强化"给明确判断与可执行建议，不要空泛原则"
- 验证：教育智能体(550分/位次23000/西安)报告从"无法判定"→ 冲稳保三档7所具体学校+专业+理由(西建科大/陕科大/西安理工/西安石油/西安科大/西安工程/西安文理)+风险评估+2冲3稳2保策略+诚实标注生源地缺口
- Files: engine.py(_analyze_node/_report_node 领域感知提示词)

### Tavily 接入（高质量搜索，1000 credits/月，2026-07-07）
- **Status:** complete
- 用户提供 Tavily Key（前两个无效，第三个 tvly-dev-1pLIau... 验证通过）
- 实测：Tavily 能搜到 cn.bing 拿不到的数据（高考分数线：西安理工历年录取线/掌上高考分数线等）
- 新建 tools/tavily.py（basic depth 省 credit）；registry 注册 tavily；.env 加 TAVILY_API_KEY
- engine 搜集节点：有 Tavily Key 时优先用它搜 1-2 个主关键词（每次 1 credit，省用），web_search 减少次数
- requirements 加 tavily-python==0.7.26
- 验证：health 显示 tavily=True；教育智能体运行 Tavily 真实搜到数据(2次=2credit)，报告 7 所学校+专业+位次咬合分析
- 省 credit 设计：每次运行限 2 次 Tavily，1000 credit 够跑 500+ 次
- Files: tools/tavily.py(新), registry.py, engine.py, .env, requirements.txt

### 报告格式 + 依据 + 禁编造（2026-07-07）
- **Status:** 代码完成，验证中（LLM 长输出卡顿）
- 用户反馈：表格网页乱、结论要有依据(往年位次)、要有分析不能只结论
- 实测 Tavily 搜到真实带位次分数线（西安理工最低参考位次16566等）
- 改进：结论节点教育领域去表格改分档列表(学校/往年依据/推荐专业/分析/结论)；分析节点要求逐条扫描资料提取真实数据，严禁编造(资料没有写"未提供"不得"基于历史数据约XXX"虚构)；院校层级推理算合理不算编造
- 问题：新提示词变复杂后 LLM 输出更长，完整运行卡死(status=running,0字)，需诊断是否 LLM 超时或纠结
- 下一步：单独测分析+报告节点 LLM 调用，确认卡顿根因

**诊断结果（2026-07-07）：**
- 单独测：分析节点 LLM 34s/1423字正常(严格用真实数据无编造)；报告节点 43s/1513字正常(格式对有依据)
- 根因：完整运行总耗时 150s+(搜集40+分析35+报告43+解析15)，之前卡死是 LLM 抖动撞超时，非逻辑问题
- 修通：HTTP 触发完整运行成功，报告 1745字 status=completed，分档列表无表格、禁编造生效(全标"资料未提供"+院校层级推理)
- 残留问题：Tavily 搜的是泛词"2026高考志愿 录取分"，没搜到具体院校分数线(之前测"西安理工大学分数线"能搜到位次16566)，需优化 Tavily query 为精准院校词

**优化 Tavily query + 修通验证（2026-07-07）：**
- 改教育领域 Tavily query：用 intent 原文+分数线 query（"2026年高考理科550分...西安 录取分数线 位次 历年" + "西安 大学 录取分数线 最低位次"），实测搜到真实带位次数据(西安交大595分位次563/西安理工历年分数线等)
- 完整运行验证通过(1900字)：延安大学引用真实依据"资料[1]指出550分可达延安大学"；风险评估引用"资料[4]提及8万名558分报会计学"+位次核心基准提醒；禁编造生效(全标"资料未提供"+院校层级推理)；分档列表无表格
- 残留：部分学校仍"资料未提供位次"——Tavily搜到分数线表格但LLM未完全提取，属LLM提取能力非代码bug，可后续优化分析提示词强化逐行扫描

### Phase 7B: 模板库（2026-07-08）
- **Status:** complete
- 后端：AgentTemplate 表；crud.py 加 template CRUD(create/get/list/update/delete/template_from_agent)；api/templates.py 路由(列表/新建/详情/编辑/删除 + POST /from-agent/{agent_id})；main.py 注册
- 前端：/templates 页(client，卡片列表+新建/编辑表单弹窗+删除)；生成页加 from_template 参数预填(包 Suspense 解决 useSearchParams 静态渲染)；侧栏加"模板库"项；api.ts 加 Template 类型
- 验证：后端 API 端到端通(建模板自动配领域工具/从智能体存/列表/删除)；前端 /templates 与 /agents/new?from_template 均 200
- 踩坑：client 组件用 useSearchParams 需包 Suspense 否则 build 预渲染报错(Next 16)
- Files: models.py, crud.py, api/templates.py(新), main.py; frontend: templates/page.tsx(新), agents/new/page.tsx, Sidebar.tsx, api.ts

### 运行过程改进（改进1+2，2026-07-08）
- **Status:** complete
- 用户反馈：1)运行中点进去看不到过程 2)过程是写死的，应展示真实思考
- 改进1（运行中可查看）：engine.py 加 wrapped_cb/persist_event，每发事件实时落库到 RunRecord.steps；agents.py 加 GET /{id}/active-run 返回活跃run+已发生事件；前端详情页 load 时查 active-run，有活跃则回填 events + 轮询刷新(pollActive 每2秒)
- 改进2（真实中间结论，非写死）：分析节点加2检查点——分析前推"正在分析N条资料:标题1/标题2"(真实资料)，分析后推"提炼要点:要点摘要"(LLM真实提取前3要点)；报告节点推"生成报告:真实标题"
- 验证：触发核潜艇导弹试射运行，中途 active-run 查到7事件实时进度；分析检查点推真实内容"正在分析12条资料:中国海军潜射导弹..."+"提炼要点:2026年7月6日12时01分战略核潜艇发射训练模拟弹头"；报告推真实标题
- Files: engine.py(wrapped_cb+检查点), agents.py(active-run端点), agents/[id]/page.tsx(load查active+pollActive)

### 运行中刷新保留 + 自定义领域（2026-07-08）
- **Status:** complete
- 需求1（运行中刷新保留过程）：前端详情页 load 改用 useRef(runningRef)+setInterval 轮询(替代闭包 pollActive)，刷新页面后若 active-run 返回 active 则回填 events+恢复轮询，运行结束自动标 done+刷新历史；已完成运行不回填过程(按用户要求)
- 需求2（自定义领域）：后端 generate 端点移除"必须5领域"校验，支持任意非空 domain 字符串；tools_for_domain 兜底 web_search(有Tavily自动启用)；前端生成页领域标签加"自定义领域..."输入框
- 验证：自定义领域"能源"generate 成功(domain=能源 tools=[web_search])；前端 build 通过
- Files: agents/[id]/page.tsx(轮询重构+useRef), agents.py(generate 支持自定义领域), agents/new/page.tsx(自定义领域输入)

### 自定义领域持久化（2026-07-08）
- **Status:** complete
- 后端：CustomDomain 表(key/label/color)；api/domains.py 路由(GET 返回预设5+自定义、POST 新增、DELETE)；generate 端点 _persist_custom_domain 自动把非预设领域存表；main.py 注册路由
- 前端：生成页领域标签从 /api/domains 动态读(替代写死 DOMAIN_META)，含自定义领域真实颜色；保留自定义输入框加新领域
- 验证：生成"医疗"领域智能体后 /api/domains 自动含"医疗"(preset=False)，下次生成页能看到该标签
- Files: models.py(CustomDomain), api/domains.py(新), main.py, agents.py(_persist_custom_domain), agents/new/page.tsx(动态领域)

### 7A 报告对比（2026-07-09）
- **Status:** complete
- 后端：app/diff.py 段落级diff(按##/###切段，difflib对齐，标added/removed/changed/unchanged+相似度)；reports.py 加 GET /compare/{a}/vs/{b}（校验同agent_id，不同智能体不可比返回400）
- 前端：api.ts 加 CompareResult/DiffSection 类型；/reports/compare/[a]/vs/[b] Server Component，左右并排渲染+段落状态色(新增绿/删除红/改动橘/未变灰)+统计栏+相似度%；详情页历史运行加多选checkbox(最多2个)+对比按钮跳对比页
- 验证：compare端点真实跑通(小鹏财经2份报告6段落diff)；对比页渲染正常(左右并排+状态色+统计)
- 边界：未完成运行不可选(disabled)；不同智能体不可比(400)
- Files: app/diff.py(新), api/reports.py, frontend api.ts, reports/compare/[a]/vs/[b]/page.tsx(新), agents/[id]/page.tsx(多选)

### 7A 报告对比升级（LLM摘要+行级diff，2026-07-09）
- **Status:** complete
- 用户反馈：原对比只标段落不同，没实际用处
- 升级：①LLM变化摘要(summarize_diff，标[新增]/[删除]/[变化]，严禁编造) ②行级diff高亮(line_diff用difflib.ndiff，绿底新增/红底删除)
- 后端：diff.py 加 summarize_diff + line_diff；compare端点返回 summary + 每段 line_diff
- 前端：对比页顶部加AI摘要区，changed段渲染行级diff高亮(+绿/-红)
- 验证：小鹏财经2报告，LLM摘要精准(新增现金流区间/删除Q4数据/变化盈利预期)；行级diff高亮正常
- Files: diff.py, api/reports.py, api.ts, compare页

### Phase 10: 报告标注/收藏（2026-07-09）
- **Status:** complete
- 后端：RunRecord 加 starred/note 字段（ALTER TABLE 迁移）；crud mark_run；reports 列表+详情返回 starred/note；PUT /api/reports/{id}/mark 端点
- 前端：ReportsList client组件（☆标星乐观更新+只看收藏筛选+批注预览）；ReportMark client组件（详情页标星+批注编辑保存）；报告列表页改用组件
- 验证：标星2份→只看收藏筛选出2份；批注"测试批注"显示；详情页标星/批注编辑正常
- Files: models.py, crud.py, api/reports.py, ReportsList.tsx(新), ReportMark.tsx(新), reports/page.tsx, reports/[id]/page.tsx

### 报告列表改搜索+筛选（删收藏，2026-07-09）
- **Status:** complete
- 用户反馈：收藏意义不大（报告一直存在），改搜索+筛选解决"找"的真问题
- 后端：reports list 端点加 search/agent_id/domain/status 参数（search 搜 agent_name+report_md 全文）
- 前端：ReportsList 改搜索框(智能体名/预览)+3筛选(智能体/领域/状态)+命中数+清除；删 ReportMark 标星/批注 UI（DB 字段保留无害）
- 验证：搜"小鹏"筛出相关报告；智能体/领域/状态筛选正常；命中数显示

### 智能体删除（2026-07-09）
- **Status:** complete
- 后端：crud delete_agent（级联删 runs via cascade + 删 schedule）；DELETE /api/agents/{id} 端点
- 前端：DeleteAgentButton client组件（二次确认"删除「X」及其所有运行记录？"→确认删除→跳回仪表台）；详情页头部编辑按钮旁加删除按钮
- 验证：后端 DELETE 端点 200；前端按钮二次确认 + 跳转
- Files: crud.py(delete_agent), api/agents.py(DELETE端点), DeleteAgentButton.tsx(新), agents/[id]/page.tsx

### Phase 8: 智能体记忆/累积分析（2026-07-09）
- **Status:** complete
- 后端：AgentMemory 表(agent_id/run_id/key_points)；crud add_memory/recent_memories；engine 分析节点读最近3次记忆注入LLM(要求标注"相比上次的变与不变")；运行成功后 _extract_key_points(LLM提取5条≤30字结论)存记忆；GET/DELETE /api/agents/{id}/memory
- 前端：AgentMemorySection client组件(右侧栏显示历次关键结论+清空)；详情页引入
- 验证：军事智能体运行后自动存5条结论(海基核威慑成熟/中俄战略协同/美方敦促核军控等)；SSE推"已记入记忆"；详情页记忆区显示；下次运行分析节点会参考
- Files: models.py(AgentMemory), crud.py, engine.py(读记忆+提取记忆), agents.py(memory端点), AgentMemorySection.tsx(新)

### Phase 11: 自然语言追问报告（2026-07-09）
- **Status:** complete
- 后端：POST /api/reports/{id}/ask 端点（基于报告md作system context，多轮history保留最近3轮控token，LLM被约束"必须有报告依据+报告未覆盖明说+不编造"）
- 前端：ReportAsk client组件（报告页💬追问按钮→右下角浮窗对话框，多轮对话，思考中动画，Enter发送）
- 验证：curl ask端点基于核潜艇报告回答"最重要结论+依据"，引用报告"关键动态""趋势研判"部分，有依据不编造；前端build成功
- Files: api/reports.py(ask端点), ReportAsk.tsx(新), reports/[id]/page.tsx
