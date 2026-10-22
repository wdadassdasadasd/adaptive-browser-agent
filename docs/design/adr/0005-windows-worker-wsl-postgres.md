# ADR-0005：Windows 独立 Worker 与 WSL PostgreSQL 首版边界

- 日期：2026-10-19
- 状态：**ACCEPTED TARGET — 未实施**
- 覆盖：[ADR-0004](0004-portfolio-local-runtime.md)的首版组件试用与自动回退决定；不改写此前的审计、r12 或评测结果。
- 权威：[现行规格](../../../SPEC.md)、[计划](../../../PLANS.md)、[契约](../../contracts/CURRENT_CONTRACTS.md)、[评测协议](../../evaluation/CURRENT_EVAL_PROTOCOL.json)。

## 决定与理由

首版在 Windows 11、16 GB 单主机运行 Vue、FastAPI、独立 Worker、现有 AgentLoop 和浏览器，在 WSL 运行 PostgreSQL。Windows 本机启动器维护 WSL 前台保活、确认数据库可用，再启动 API/Worker，并监测与自动重启 Worker。用户选择完整管理员账户界面；B01 开源工具选型是首个面试纵切。五账户隔离、两运行八排队、一次安全恢复及可断开介质的加密备份恢复都是正式放行硬门槛，但研究质量先于管理与韧性阶段实施。

应用 PostgreSQL 表是账户、owner-scoped 任务、租约、调用尝试、事实、报告、费用及用户事件的权威。Worker 用短事务和行认领取得递增 fencing token；事实、事件、报告、费用及终态写入均须验证该 token。通知只唤醒，SSE 从已提交事件补读。每次模型/工具调用前写 `started`，返回后写 `completed` 或 `failed`；崩溃空档保留 `unknown_outcome`，不将结果或费用猜作成功、零。检查点若未来引入，只辅助执行恢复。

Worker 故障后同一任务最多重新认领一次：保留已提交事实，重建浏览器、重新观察并规划，未知结果的外部动作不盲重放。第二次故障以 `partial` 或 `failed` 终结并保留原因。API 持久确认取消请求，Worker 异步清理和终结；排队取消释放槽位。数据库失联时 API 不确认未持久化的提交/取消，Worker 暂停新认领，恢复后对账；首版不承诺 WSL/PostgreSQL 自动重启。

## 备选与退出

单进程＋SQLite 迁移较少，但用户已明确选择首版独立 Worker＋PostgreSQL，不能在 P-01 失败后静默回退。LangGraph 在检查点边界重放的机制不能证明未知浏览器动作的结果；只有现有 AgentLoop 出现可复现、局部修复不足的状态/恢复故障，且限时探针能解决时，再单独决策。首版不引入 Redis、消息代理、完整 HAR/录屏留存或 LAN 发布。

P-01 两周只用假任务验证 10 任务、两运行八排队和第 11 个请求 429 不落库、唯一认领/终态、取消、SSE 补读、数据库失联与资源占用。要求无丢失/双认领/OOM，常规 API p95 ≤1 秒、已提交事件补读 ≤2 秒；故障注入后 Worker ≤60 秒重启、任务 ≤120 秒重新认领或诚实终结，记录 Windows 11 16 GB 的 CPU/内存峰值。未过关立即暂停付费 pilot，仅按故障证据限时修复一个必要组件；若会挤占 P-02 研究质量或 P-04 正式批次，保持 No-Go 并向用户重定范围。

2026-10-20 的[环境探针](../../audits/PREDEV_ENV_SETUP_2026-10-20.md)已确认 Ubuntu 24.04.1、PostgreSQL 16.15、Windows `asyncpg` 经本机回环连接新隔离库。WSL 无前台进程时发行版退出，独立连接随即被拒绝；临时 WSL 保活进程存活时连接成功。因此 P-01 本机启动器还须在应用运行期间维护 WSL 生命周期，先检测 PostgreSQL，再启动 API/Worker；这不是数据库故障后的自动重启承诺。加密备份工具、主机负载、真实费用仍待探针。离线假任务不证明公开研究成功、真实五人并发或局域网安全。本决定不授权业务代码、付费运行、部署或 Git 提交。
