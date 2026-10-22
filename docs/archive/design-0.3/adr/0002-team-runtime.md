# ADR-0002：可信团队版采用同机 API 与 Worker 分进程

状态：**ACCEPTED — 0.4 Gate 2 目标设计，未实施**。日期：2026-10-18。用户明确回复“批准 0.4 并切换权威指针”。本 ADR 取代 [ADR-0001](0001-target-architecture.md)中“仅可信本机单用户、单进程执行”的未来目标边界；旧 ADR 保留历史，当前业务代码仍按 V1 工作。

## 背景与决策

新需求是在一台 Windows 11/i7-12700H/16 GB RAM 主机上供约 20 位可信内网成员同时访问；每人只见自己的任务并仅能取消自己的任务，至少 8 个任务可提交和排队，实际并行研究数由实机容量测试确定，初始仍为 2。服务只需工作时段在线，笔记本休眠/关机可中断；每日加密一致性备份须保存在管理员提供的异机内网共享存储，保留 30 天并按月验证恢复。当前 `ResearchService` 在 API 进程调用进程内 `TaskManager`；任务、取消信号和 SSE 唤醒留在内存，四张表没有用户身份或任务归属。六路研究 API 目前没有认证、对象级过滤。单纯提高 `MAX_CONCURRENT_TASKS` 或增开 Uvicorn 进程既不能形成归属隔离，也不能共享调度/取消/通知。

目标决定：保留同一模块化代码库、DeepSeek、BrowserUseAdapter、六路**研究** API 和 SQLite 事实表；将 API 与研究 Worker 拆成同机进程，Worker 从持久队列原子认领并持久化取消/租约/终态，API 从已提交 trace 补读 SSE。新增本地账户、管理员开通/停用/重置、服务端会话、对象级授权、按拥有者用量记录、可重复 schema 迁移以及内网 IP 的 HTTPS 代理。管理员统一向客户端分发内部 CA 信任。旧 V1 无 owner 的任务保留供管理员审计，普通成员默认不可见。AgentLoop、Reducer 和工具适配边界不变，不自动重放浏览器副作用。

## 权衡与验收

保留单进程并在进程内为所有用户排队是较小改动，但浏览器/Provider 长任务与登录/API/SSE 共享故障域，且难以演进到独立调度；同机 Worker 增加认领、跨进程取消、故障恢复和部署成本，却能隔离 API 响应并以持久任务为准。直接采用 Redis/Celery、PostgreSQL 或 LangGraph 会增加本版服务与迁移范围，暂不作为默认方案。SQLite 的 [WAL 模式](https://www.sqlite.org/wal.html)允许读写并行，但同一时刻只有一个 writer，只能用于同机文件；8 个任务的写入竞争不能由 WAL 名称推断为已达标。

团队版放行须在指定主机实测约 20 个在线会话、至少 8 个待处理任务、实际并行上限下的 CPU/内存/磁盘、SQLite 锁等待、API/SSE 延迟、唯一认领、取消和 Worker 重启，并验证异机备份/恢复。容量不足时保持 No-Go，调整运行槽或资源并重新验证；若跨主机或写入瓶颈成为实证需求，再另立数据库/队列 ADR。密码自适应哈希、会话秘密保护与 HTTPS 遵循 [OWASP 密码存储](https://cheatsheetseries.owasp.org/cheatsheets/Password_Storage_Cheat_Sheet.html)、[会话管理](https://cheatsheetseries.owasp.org/cheatsheets/Session_Management_Cheat_Sheet.html)；Windows 上的 HTTPS 服务可参照 [Caddy 官方服务说明](https://caddyserver.com/docs/running)和[内部 CA 行为](https://caddyserver.com/docs/automatic-https)，部署前需验证 IP 证书在客户端受信任。
