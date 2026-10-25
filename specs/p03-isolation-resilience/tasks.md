# Tasks: P-03（迁移，沿用原 Task ID；真值源：[PREDEV_P02_P04_TASK_PACKAGE](../../docs/tasks/PREDEV_P02_P04_TASK_PACKAGE_2026-10-20.md)、[EIGHT_MODULE_PREP](../../docs/tasks/EIGHT_MODULE_PREP_2026-10-22.md)）

- [ ] P03-ACCOUNTS **未实施** — 身份/会话/owner 隔离、登录、完整管理员界面（FR-009/AC-009、NFR-008/AC-N08）；依赖 P-02。
- [ ] P03-RECOVERY-BACKUP **未实施** — 启动器/Worker 恢复、加密离线备份与独立目录恢复（FR-006/AC-006、NFR-006/AC-N06、NFR-009/AC-N09）；依赖 P-01 架构与 P03-ACCOUNTS。剩余：双故障、迟到 fencing、数据库失联对账与独立目录恢复哈希，原件保护。
- [ ] P03-DIAGNOSE **PARTIAL** — 依赖 P02-PILOT 与 P03-ACCOUNTS。已有 [B01 真实失败逐调用诊断](../../docs/audits/P02_B01_LIVE_FAILURE_TRIAGE_2026-10-22.md)与预算拒绝离线复现；精确根因、最小修复、完整离线回归与真实复查（≤30 元诊断额度，另行授权）尚无，不算完成。
- [ ] P03-MEMORY **未实施** — 可选 `memory_mode` 与 owner-scoped 来源线索接口（FR-011/AC-011）；依赖 P03-ACCOUNTS 与已核源事实。剩余：报告哈希/核源工件校验、过期/撤销/越权、最多五条及正式评测禁用复用。
- [ ] P03-MCP **未实施** — 本地只读 stdio MCP（FR-012/AC-012）；依赖 P02-LOOP-TOOLS 统一 schema。

**原阶段需求补充映射**：PLANS.md P-03 行及需求表另列 FR-001/AC-001、FR-005/AC-005、FR-010/AC-010、NFR-001/AC-N01、NFR-003/AC-N03、NFR-007/AC-N07 的真实链路/容量证据；原任务包无独立 Task ID。本迁移新增 P03-CAPACITY 追踪缺口，不将其标成已完成。

- [ ] P03-CAPACITY **新增映射任务 / 未实施** — 依赖 P03-ACCOUNTS 与 P03-RECOVERY-BACKUP；按现行契约对上述六组需求/AC 做容量模拟、失败/取消/历史可见性及资源记录，逐项链接实测工件。本机结果不代表 LAN 放行。

**顺序**: ACCOUNTS → RECOVERY-BACKUP / MEMORY / CAPACITY；MCP 依赖 P02-LOOP-TOOLS 统一 schema；DIAGNOSE 依赖 PILOT 与 ACCOUNTS。任一隔离/恢复/诊断闭环失败即 No-Go。
