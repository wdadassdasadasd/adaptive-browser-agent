# 架构边界

默认 V1 入口是 `Vue → FastAPI → ResearchService → TaskManager → AgentLoop → Planner/ContextManager/Evaluator/StateReducer/Reporter → ToolRouter → GitHubTool/BrowserUseAdapter`。SQLite 保存已提交事实和事件。其行为以 [V1 规格](../specs/V1_SPEC.md)、[V1 契约](../contracts/V1_CONTRACTS.md)、源码和测试判定。

P-01 独立开发入口为 `Vue → api.pg_main → PostgreSQL ← worker.runner → AgentLoop`。API 只持久提交和查询；Worker 用短事务认领、续租、检查取消，并用 fencing token 写调用、事实和终态。SSE 每 250 毫秒从已提交事件补读，事件编号按提交顺序推进。任务和报告查询使用同一条 SQL 快照；状态和对应事件在一个事务提交。过期执行只允许一次重认领，第二次过期诚实终结。恢复从已提交规划和步骤事件重建事实及用量，重建浏览器并重新观察；结果未知的调用保留 `unknown_outcome`。

`scripts/start-p01.ps1` 维护 WSL 前台生命周期、迁移新 PostgreSQL 应用库、启动 Windows API/Worker 并监测 Worker。`P01_DATABASE_URL` 单独配置，禁止回退到 V1 SQLite。数据库失联后停止新认领和失去租约的写入；恢复连接后的对账按账本执行。已实现与实测范围见 [P-01 任务记录](../tasks/PREDEV_P01_START_PACKAGE_2026-10-20.md)。目前仍是单个合成 owner，五账户、人工官方核源和正式费用核算按后续阶段实施。

[ADR-0005](../design/adr/0005-windows-worker-wsl-postgres.md)记录决定及故障、取消、恢复边界，[现行契约](../contracts/CURRENT_CONTRACTS.md)定义目标语义。独立进程的假任务关口、真实浏览器恢复和产品放行分别留证。

职责边界：前端通过 HTTP/SSE 访问 API；API 负责提交、持久确认和查询；Worker 从数据库认领并执行长任务；Agent 核心仅接收可选调用观察接口和可序列化恢复状态，不依赖 API 路由、Worker 启动器或持久化实现；数据库中的已提交记录才是对用户可见的事实。新 `backend/src/adaptive_research/` 结构已完成行为等价迁移。`evaluation.current` 生成离线 dry-run；`evaluation.pilot_runner` 已实现显式授权后可用的串行三题任务提交与证据链，但尚未真实运行。评测可访问产品 API 和读取证据，生产执行链不导入评测模块；实际状态见[P02-PILOT 证据](../tasks/P02_PILOT_PREP_2026-10-21.md)。

本页是阅读入口，不添加新产品要求。阶段 Go/No-Go 依据[现行计划](../../PLANS.md)与实际记录；真实研究结果仍为 No-Go。
