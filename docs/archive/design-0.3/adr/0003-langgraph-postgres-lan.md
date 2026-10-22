# ADR-0003：0.5 研究运行时与同机局域网边界

- 日期：2026-10-18
- 状态：**ACCEPTED TARGET — 未实施**
- 权威：[SPEC.md 0.5](../../../SPEC.md)；[目标契约](../../contracts/0.5_TARGET_CONTRACTS.md)。[ADR-0002](0002-team-runtime.md)与 [0.4 快照](../../../SPEC_0.4.md)保留为历史目标；当前代码仍是 V1。

## 背景

r12 的真实研究结果仍为 No-Go。0.4 曾计划同机 API/Worker 与 SQLite 持久队列，但新产品限定 5 名可信局域网成员，要求可恢复的研究执行、两项并行、至少八项排队、独立账户与逐对象授权。当前 SQLite/进程内 AgentLoop 不能凭设计推断满足这些要求；现有模块需在调用级诊断后选择性复用。

## 决定

1. 同机模块化代码库保留 FastAPI/Vue/DeepSeek/GitHubTool/browser-use 边界，API 与研究 Worker 独立进程。LangGraph 仅编排研究执行和检查点恢复；任务、owner、准入事实、报告与用户事件由 PostgreSQL 应用表持有。检查点不授予对象访问、不替代终态事实。[LangGraph 检查点文档](https://docs.langchain.com/oss/python/langgraph/checkpointers)说明节点重放边界。
2. Worker 通过 PostgreSQL 行锁与租约认领任务，初始 2 个运行槽、至少 8 项排队；唯一有效认领、取消请求、状态和终态通过持久事务裁决。`SKIP LOCKED` 适用于队列式行认领，但能力与性能须在本机证明。[PostgreSQL SELECT](https://www.postgresql.org/docs/current/sql-select.html)。已提交应用事件供 SSE 按 ID 补读。
3. 故障后同一任务最多自动恢复一次：保留已提交事实，重建浏览器并重新观察、规划，不原样重放未知结果的动作。再次故障转为 partial/failed。恢复次数与不确定动作须有独立记录。
4. 容器优先，同机原生服务可作为验证后的回退。LAN 入口只经 HTTPS；认证、CSRF、逐对象授权、浏览器重定向与子资源私网阻断必须实测。每日一致性 PostgreSQL 备份加密存异机，留存 30 天，每月恢复演练。任何安全或恢复证据缺失均 No-Go。

## 后果与待验证项

PostgreSQL 与 LangGraph 引入新的迁移、连接和检查点运维成本，不能用更换框架代替失败根因诊断。G3-02 先建立最小闭环并实测 Windows 11 16 GB 主机的 WSL/Docker、Chromium 双任务占用与 API/SSE 延迟；G3-06 验证竞态、私网外联、TLS 客户端信任及备份恢复。容器许可和异机路径部署前核对。未经 G3-07 十五次真实任务验收，不宣称研究业务成功。
