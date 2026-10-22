# Gate 1 双向需求追踪矩阵

状态：**APPROVED（设计）**｜版本：Gate 1 冻结版 0.3｜日期：2026-10-18｜实施：未授权

本矩阵将 [01 PRD](01_PRODUCT_REQUIREMENTS.md) 的需求连接到设计、**实际源码位置**、传输/事件、测试方案和验收。`VERIFIED` 仅表示所列源码或历史记录确实存在，**不**表示需求已通过真实业务验收；`PROPOSED` 表示目标设计或尚未执行的测试。测试 ID 是 [05 测试与评测](05_TEST_AND_EVALUATION.md) 应采用的追踪主 ID；`-A` 为正常路径，`-B` 为异常/边界路径。验收结果只以新的原始记录和运行输出更新，不以 Mock 通过替代真实成功。

## 1. 设计锚点与证据规则

| 设计锚点 | 设计责任与对应文档 |
| --- | --- |
| ARC-001 | 任务创建/排队、API→Service→TaskManager 与数据提交：[02 架构](02_SYSTEM_ARCHITECTURE.md)、[03 主链路](03_DATA_FLOW_AND_STATE.md)、[04 契约](04_DATA_AND_API_CONTRACTS.md) |
| ARC-002 | 单轮 Observe→Plan→Tool→Evaluate→Reduce、去重和有界停止：[02](02_SYSTEM_ARCHITECTURE.md)、[03](03_DATA_FLOW_AND_STATE.md) |
| ARC-003 | 工具结果→证据→事实、主体归属和来源链：[03](03_DATA_FLOW_AND_STATE.md)、[04](04_DATA_AND_API_CONTRACTS.md) |
| ARC-004 | 事实 ID→报告与持久化终态：[03](03_DATA_FLOW_AND_STATE.md)、[04](04_DATA_AND_API_CONTRACTS.md) |
| ARC-005 | 持久事件、SSE 补读、历史与前端时间线：[02](02_SYSTEM_ARCHITECTURE.md)、[03](03_DATA_FLOW_AND_STATE.md)、[04](04_DATA_AND_API_CONTRACTS.md) |
| ARC-006 | 取消、异常、重启终结和事务状态机：[03](03_DATA_FLOW_AND_STATE.md)、[04](04_DATA_AND_API_CONTRACTS.md) |
| ARC-007 | LLM 分阶段用量、耗时和诊断展示：[03](03_DATA_FLOW_AND_STATE.md)、[04](04_DATA_AND_API_CONTRACTS.md) |
| ARC-008 | 可选模板/Markdown 导出：[01 PRD](01_PRODUCT_REQUIREMENTS.md)、[08 路线图](08_IMPLEMENTATION_ROADMAP.md) |
| ARC-N01…N06 | 可靠性、成本、安全、可观测性、可维护性、本机部署的横切设计：[02](02_SYSTEM_ARCHITECTURE.md)、[05](05_TEST_AND_EVALUATION.md)、[06](06_ACCEPTANCE_AND_RELEASE.md)、[07](07_AI_CODING_WORKFLOW.md) |

**历史证据标尺**：[D7 真实验收](../audits/V1_DELIVERY_REPORT.md) 和 [r12 summary](../../data/benchmark/20261016T152251931497Z-3de75ed5/summary.json)为 `VERIFIED` 的失败基线：18 次真实尝试完整完成率均为 0，三次独立 UI 验收均失败。下列源码存在性与测试文件名来自当前 checkout HEAD `dbacdc02fb119f70bc65a14608ab1bede75c0622`；本轮未运行测试。缺少实际输出时状态只能是待验证。

## 2. 正向矩阵：需求 → 设计 → 代码/传输 → 测试 → 验收

| Requirement / 为什么存在 | Design | 实际责任模块；输入 → 输出 | API / Event | 测试设计及已有可核对测试 | Acceptance / 当前证据状态 |
| --- | --- | --- | --- | --- | --- |
| **FR-001 P0** 创建、队列与历史，避免长任务阻塞请求 | ARC-001 | `backend/api/research.py`、`backend/services/research.py::create`、`adaptive_agent/runtime/task_manager.py`、`backend/services/persistence.py::create_task`；目标文本 → 持久 `queued` 任务 ID | `POST /api/research`、`GET /api/research`、`GET /api/research/{id}`；`task_queued`/`task_started` | **TEST-001-A/B**：202+历史、422/503 不落库、并发上限；现有 `tests/integration/test_research_api.py`、`tests/unit/test_task_manager.py` 可复用 | **AC-001**；源码与 Fake 测试存在为 VERIFIED，真实排队业务放行仍 PROPOSED |
| **FR-002 P0** 动态工具决策，避免无效动作和无限重复 | ARC-002 | `adaptive_agent/agent_loop.py::run`、`planner.py::PlannerService`、`context_manager.py::ContextManager`、`tools/router.py::ToolRouter`、`evaluator.py::EvaluatorService`、`state_reducer.py::StateReducer`；状态+观察 → 有效单步决策/评估/新状态 | `step_evaluated`，内部 `PlanDecision`/`ToolResult`/`EvaluationResult` | **TEST-002-A/B**：观察改变决策、非法动作拒绝、技术/语义失败和 no-progress；现有 `test_planner.py`、`test_evaluator.py`、`test_agent_loop.py` | **AC-002**；代码链 VERIFIED，r12 完整完成失败 VERIFIED，调用级根因 INFERRED |
| **FR-003 P0** 证据可信且可追溯，防止错归属和虚构事实 | ARC-003 | `adaptive_agent/state.py::ResearchFact`、`evaluator.py`、`state_reducer.py`、`backend/services/persistence.py::record_event`；工具可观察内容+来源 → 已接纳事实 ID、拟议步骤级拒绝数量/原因码 | `step_evaluated` 的准入事实及 PROPOSED `fact_rejection_summary`、`GET /api/research/{id}/traces`；无独立事实路由 | **TEST-003-A/B**：有效/未观察/错主体/重复/混合准入与脱敏；现有 `test_evaluator.py`、`test_state_reducer.py`、`test_persistence.py` 可复用 | **AC-003**；Evaluator 片段匹配 VERIFIED；拒绝摘要、证据卡片与逐项真实核源 PROPOSED |
| **FR-004 P0** 给用户可用而不虚构的研究结论 | ARC-004 | `adaptive_agent/reporter.py::ReporterService`、`state.py::ResearchReport`、`backend/services/persistence.py`、`frontend/src/App.vue`；接纳事实+终止原因 → 可溯源报告 | `task_finished` 载荷、`GET /api/research/{id}` | **TEST-004-A/B**：事实到 finding 引用、partial/failed、重启读取；B01–B03 各 3 次真实验收；现有 `test_reporter.py`、`test_research_api.py` | **AC-004**；报告代码 VERIFIED；r12/UI 业务 No-Go VERIFIED；2/3 目标 PROPOSED |
| **FR-005 P0** 长任务过程可观察且断线不丢历史 | ARC-005 | `backend/api/research.py::stream_research_events`、`backend/services/persistence.py`、`adaptive_agent/runtime/task_manager.py`、`frontend/src/App.vue`；已提交事件 → SSE/历史时间线 | `GET /api/research/{id}/events`、`/traces`、`Last-Event-ID`；六类 `AgentEvent` | **TEST-005-A/B**：实时、重连补读、慢订阅/断开、终态关闭；现有 `tests/integration/test_sse.py`、`frontend/src/App.test.ts` | **AC-005**；持久补读路径 VERIFIED，跨真实任务稳定性待新验收 |
| **FR-006 P0** 取消、失败和重启必须有唯一且诚实的终态 | ARC-006 | `adaptive_agent/runtime/task_manager.py`、`adaptive_agent/agent_loop.py`、`backend/services/research.py::cancel/recover/shutdown`、`backend/services/persistence.py::finalize_unfinished`；取消/异常/重启 → 唯一终态+释放资源 | `POST /api/research/{id}/cancel`、`cancel_requested`、`task_finished` | **TEST-006-A/B**：排队/运行取消、竞态、重复事件、重启、有/无事实、浏览器清理；现有 `test_task_manager.py`、`test_persistence.py`、`test_research_api.py` | **AC-006**；终态实现和 Fake 测试存在 VERIFIED；真实资源完整回收另需验证 |
| **FR-007 P0** 成本和失败可解释，支持复盘真实 0% 完成率 | ARC-007 | `adaptive_agent/llm/deepseek.py`、`agent_loop.py`、`state_reducer.py`、`state.py::ResearchState`、`backend/services/persistence.py`、`frontend/src/App.vue`；请求级已报告 usage/未知调用/阶段耗时 → 已知下界与完整总量是否可验证 | 现有 `step_evaluated`/`task_finished` 与详情；PROPOSED 可选 `usage_by_stage` 增量，不新增路由 | **TEST-007-A/B**：首次/修复/重试单计、未知不计零、旧 trace、脱敏与刷新复现；现有 `test_loop_usage.py` 仅覆盖部分用量 | **AC-007**；当前总量是已报告值 VERIFIED；请求级分阶段用量/可视化 PROPOSED |
| **FR-008 P1** 降低输入和分享成本 | ARC-008 | `frontend/src/App.vue`、`frontend/src/api.ts`、现有 `ResearchReport.markdown`；可编辑模板/持久报告 → 目标文本/Markdown 文件 | 沿用 `POST /api/research`、`GET /api/research/{id}`，无新增 API | **TEST-008-A/B**：模板可修改、固定任务原文不变、导出一致与脱敏；尚无专用测试 | **AC-008**；仅报告 `markdown` 字段 VERIFIED，功能本身 PROPOSED |
| **NFR-001 P0** 有界可靠运行 | ARC-N01 | AgentLoop、TaskManager、Persistence；限制/错误/取消 → 一致终态 | `task_finished`、任务状态 | **TEST-N01-A/B**：预算、并发、异常、取消、事务；现有 `test_persistence.py` 等 | **AC-N01**；局部路径 VERIFIED；真实失败仍 No-Go |
| **NFR-002 P0** 可比较的成本与性能证据 | ARC-N02 | `ResearchState`、LLM Provider、benchmark runner；调用/步骤 → Token、耗时、重复 URL 与缺失标记 | trace/benchmark raw record | **TEST-N02-A/B**：预算上限、九次逐次记录和 P95 口径；现有 `test_loop_usage.py`、`tests/unit/test_benchmark.py` | **AC-N02**；r12 用量与预算不对等事实 VERIFIED；新目标 PROPOSED |
| **NFR-003 P0** 保护本机密钥和浏览边界 | ARC-N03 | `adaptive_agent/adapters/browser_use_adapter.py`、`state.py::require_http_url`、Persistence 已配置秘密替换；直接导航 URL/不可信网页内容 → 事前公有目标校验与有界 trace | 所有 URL、trace、SSE、报告输出 | **TEST-N03-A/B**：直接私网事前拒绝，DNS 变化与重定向/点击/弹窗/子资源请求日志、三个恶意页 canary、已配置密钥脱敏及新增诊断元数据不复制正文；现有 `test_browser_use_adapter.py`、`test_sse.py`、`test_persistence.py` 可复用 | **AC-N03**；直接目标校验和现有 trace 保存工具内容 VERIFIED；浏览器内部请求事前阻断 UNVERIFIED，仅可信本机公开资料 |
| **NFR-004 P0** 故障可复现 | ARC-N04 | AgentEvent、Persistence、任务详情、benchmark manifest；task/event ID → 顺序、错误、用量 | `/traces`、`/events`、run JSON | **TEST-N04-A/B**：给定 task ID 重建失败，检查脱敏与缺失字段；现有 SSE/持久化测试 | **AC-N04**；r12 原始记录 VERIFIED；阶段诊断 PROPOSED |
| **NFR-005 P0** 小步可维护交付 | ARC-N05 | 仓库模块边界、`.github/workflows/ci.yml`、`pyproject.toml`、`frontend/package.json`；变更 → 静态/测试结果 | API/事件兼容性门禁 | **TEST-N05-A/B**：按影响运行 Python/前端门禁、契约回归；历史 D7 检查见审计，不充当前轮结果 | **AC-N05**；配置存在 VERIFIED；本轮无新执行结果 |
| **NFR-006 P0** 本机可演示且能解释重启 | ARC-N06 | `README.md`、`backend/main.py`、`backend/services/research.py::recover/shutdown`、SQLite 配置；环境+启动 → 可提交任务/可读历史 | 六路 API、`server_restart` 终态 | **TEST-N06-A/B**：干净环境启动、缺密钥、停机重启、历史读取；现有集成测试仅是局部证据 | **AC-N06**；本机路径 VERIFIED，干净环境复现需新验收 |

## 3. 反向索引：外露契约与测试不应成为孤岛

| API / Event / 数据对象 | 所属需求 → 测试 → 验收 | 当前事实与待核实点 |
| --- | --- | --- |
| `POST /api/research`、`task_queued` | FR-001 → TEST-001-A/B → AC-001 | 202/422/503 路径在 `backend/api/research.py`；真实队列放行待验 |
| `GET /api/research`、`GET /api/research/{id}` | FR-001/004/005/007 → TEST-001/004/005/007 → AC-001/004/005/007 | 详情返回终态与报告；拟议诊断需核对事件字段是否足够 |
| `GET /api/research/{id}/traces` | FR-003/005/007 → TEST-003/005/007 → AC-003/005/007 | 返回已保存 AgentEvent；事实卡片投影为待设计 UI |
| `GET /api/research/{id}/events`、`Last-Event-ID` | FR-005/006 → TEST-005/006 → AC-005/006 | SQLite 补读与订阅队列唤醒分开；需要竞态验收 |
| `POST /api/research/{id}/cancel` | FR-006 → TEST-006 → AC-006 | 排队和运行语义不同，终态不可改写 |
| `task_started`、`subgoals_initialized` | FR-001/002/005 → TEST-001/002/005 → AC-001/002/005 | 只证明启动及初始化，不证明真实研究成功 |
| `step_evaluated`、`ResearchFact` | FR-002/003/005/007 → TEST-002/003/005/007 → AC-002/003/005/007 | 经 reducer 的已接纳事实与原始工具成功分开 |
| `cancel_requested`、`task_finished` | FR-004/005/006 → TEST-004/005/006 → AC-004/005/006 | 单一终态和报告一致性为事务验收重点 |
| `ResearchReport` / `markdown` | FR-004/008 → TEST-004/008 → AC-004/008 | `markdown` 字段已有，下载行为尚无 |
| 阶段 Token/耗时事件载荷 | FR-007、NFR-002/004 → TEST-007、TEST-N02/N04 → AC-007、AC-N02/N04 | **PROPOSED**；若现有 DTO 不足，04 文档规定兼容扩展 |

对每个 **P0** 需求，[05](05_TEST_AND_EVALUATION.md)须定义 `-A` 正常及 `-B` 异常/边界案例，包含前提、输入、预期、层级、自动化、证据路径；[06](06_ACCEPTANCE_AND_RELEASE.md)须给出其 AC 的实际放行记录。由此可从需求找实现/测试，也可从任一对外契约返回需求和验收。未来若删改 API、事件或测试，须同步本矩阵；不允许以“无覆盖但可演示”关闭 P0。

## 4. 当前缺口与实施授权后的更新机制

1. **VERIFIED**：r12 和 UI 真实业务验收失败；`FR-004/AC-004` 不得标通过。历史 Mock/Fake、单元及 CI 结果只能支持各自层级。
2. **INFERRED**：大量 Token 与无进展可能关联重复上下文、结构化修复或证据拒绝；必须先以调用级事件及重放证明，再修改 Planner/Evaluator。`FR-007` 是可诊断性的先决项。
3. **已批准设计、尚未实现**：证据卡片、分阶段用量及可下载 Markdown 缺当前 UI 验收；另获对应 G2 执行授权后，才按 [08 路线图](08_IMPLEMENTATION_ROADMAP.md)的小 PR 更新状态和真实证据链接。
4. 历史冻结契约、D7 报告和 r12 原始记录保持原样。G2-00 另获执行授权后，在其受批范围内添加版本指针，随后才可按各任务授权开展行为 PR；每项 P0 均由本表的模块/API、`TEST-xxx-A/B`、`AC-xxx` 双向追踪。每项需求记录负责 PR、测试命令退出码、真实运行 ID、审核意见和 AC 决策，最后由用户验收。
