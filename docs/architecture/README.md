# 架构边界

## 当前与目标的区别（2026-10-27）

- **已实现/部分验收**：V1 Vue/FastAPI/SQLite；Pg API/Worker/租约/事件/调用账本及P01假任务48/48；T02–05离线切片，真实研究/跨账户/恢复仍有缺口，见[任务状态](../features/DECISION-001/tasks.md)。
- **批准的M1目标，未实现**：[ADR8](../design/adr/0008-m1-engineering-baseline.md)在[ADR5](../design/adr/0005-windows-worker-wsl-postgres.md)/[ADR7](../design/adr/0007-interactive-evidence-decision-sessions.md)上细化通用角色、两成员身份、Session/Revision/Turn/报告、显式来源线索、C0/1/2、一次决策请求、F1/admission/恢复高水位、审计A。应用表拥有事实/事件/费用，checkpoint和临时投影不拥有真相。
- **未验证**：新目标调用链、真实产品价值、tokenizer资格、真实浏览器恢复、资金全账、备份恢复/五账户与正式评测；文档检查不证明实现/安全/效果，r12/P02 No-Go保持。

精确接口和数据归属见[现行契约](../contracts/CURRENT_CONTRACTS.md)，模块依赖/非职责见[PLANS](../../PLANS.md)，风险验证见[策略](../testing/STRATEGY.md)。保留现有AgentLoop，不因上游框架增加而替换；新增LangGraph需独立故障证据/设计决定。下方历史设计导航保留原版本。

默认 V1 入口是 `Vue → FastAPI → ResearchService → TaskManager → AgentLoop → Planner/ContextManager/Evaluator/StateReducer/Reporter → ToolRouter → GitHubTool/BrowserUseAdapter`。SQLite 保存已提交事实和事件。其行为以 [V1 规格](../specs/V1_SPEC.md)、[V1 契约](../contracts/V1_CONTRACTS.md)、源码和测试判定。

P-01 独立开发入口为 `Vue → api.pg_main → PostgreSQL ← worker.runner → AgentLoop`。API 只持久提交和查询；Worker 用短事务认领、续租、检查取消，并用 fencing token 写调用、事实和终态。SSE 每 250 毫秒从已提交事件补读，事件编号按提交顺序推进。任务和报告查询使用同一条 SQL 快照；状态和对应事件在一个事务提交。过期执行只允许一次重认领，第二次过期诚实终结。恢复从已提交规划和步骤事件重建事实及用量，重建浏览器并重新观察；结果未知的调用保留 `unknown_outcome`。

`scripts/start-p01.ps1` 维护 WSL 前台生命周期、迁移新 PostgreSQL 应用库、启动 Windows API/Worker 并监测 Worker。`P01_DATABASE_URL` 单独配置，禁止回退到 V1 SQLite。数据库失联后停止新认领和失去租约的写入；恢复连接后的对账按账本执行。已实现与实测范围见 [P-01 任务记录](../tasks/PREDEV_P01_START_PACKAGE_2026-10-20.md)。目前仍是单个合成 owner，五账户、人工官方核源和正式费用核算按后续阶段实施。

[ADR-0005](../design/adr/0005-windows-worker-wsl-postgres.md)记录决定及故障、取消、恢复边界，[现行契约](../contracts/CURRENT_CONTRACTS.md)定义目标语义。独立进程的假任务关口、真实浏览器恢复和产品放行分别留证。

职责边界：前端通过 HTTP/SSE 访问 API；API 负责提交、持久确认和查询；Worker 从数据库认领并执行长任务；Agent 核心仅接收可选调用观察接口和可序列化恢复状态，不依赖 API 路由、Worker 启动器或持久化实现；数据库中的已提交记录才是对用户可见的事实。新 `backend/src/adaptive_research/` 结构已完成行为等价迁移。`evaluation.current` 生成离线 dry-run；`evaluation.pilot_runner` 已实现显式授权后可用的串行三题任务提交与证据链，已有真实运行，三题均未完整成功，见[同版 pilot 失败分析](../audits/P02_PILOT_R11_FAILURE_TRIAGE_2026-10-23.md)；此处不将“已运行”等同“已验收”。评测可访问产品 API 和读取证据，生产执行链不导入评测模块；实际状态见[P02-PILOT 证据](../tasks/P02_PILOT_PREP_2026-10-21.md)。

新增已批准目标为[ADR-0007](../design/adr/0007-interactive-evidence-decision-sessions.md)方案 B：`Vue → decision-sessions API → PostgreSQL → Worker → TurnExecutionContext → 澄清／解释／AgentLoop研究 → 不可变报告`。会话、条件版本、轮次、引用和报告归应用表；每轮是有限 PgTask，等待用户不持租约。统一上下文拥有调用／额度／截止时间与 provider 生命周期；旧单任务事实不混入跨轮引用。所有新路径仍未实现，付费模式关闭；文档批准不执行迁移或解锁资金。旧 Worker 的无 kind 认领必须由兼容数据库协议护栏与受控停机迁移解决，不能只靠启动器。详情以现行契约为准。

本页是阅读入口，不添加新产品要求。阶段 Go/No-Go 依据[现行计划](../../PLANS.md)与实际记录；真实研究结果仍为 No-Go。
