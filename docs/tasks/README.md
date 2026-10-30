# 当前任务与历史证据索引

当前主线的唯一18项、40路径配置、批准/检查/审查与首工拟授权包由[DECISION-001连续记录](../features/DECISION-001/tasks.md)维护。[PLANS](../../PLANS.md)定义ENV-M1-01/02及DEC-M1-01–08依赖。首工为真实认证/原始草稿＋最小supervisor，实施另批；旧DEC-T07-01不自动开工。

## 历史任务索引

下表只保留原阶段/任务/证据归属，不是并行现行计划或新放行门槛。Task状态仍在各唯一原记录，未执行不倒填。

| 阶段 | Task ID | 记录 |
| --- | --- | --- |
| R0 | R0 结构迁移 | [本地验收记录](R0_ACCEPTANCE_2026-10-20.md) |
| P-01 | P01-ENV、P01-TRACE、P01-DB、P01-RUNTIME、P01-CALL、P01-API-CI | [P-01 任务记录](PREDEV_P01_START_PACKAGE_2026-10-20.md)，[假任务验收证据](P01_ACCEPTANCE_2026-10-21.md) |
| 准备整改 | PREP-CONFIG-TRACE、PREP-TRACEABILITY、PREP-UPSTREAM-8、PREP-FREEZE | [八模块准备记录](EIGHT_MODULE_PREP_2026-10-22.md) |
| P-02 | P02-PILOT、P02-LOOP-TOOLS、P02-CONTEXT、P02-FACT-REPORT | [P-02 至 P-04 任务记录](PREDEV_P02_P04_TASK_PACKAGE_2026-10-20.md)，[pilot 离线准备证据](P02_PILOT_PREP_2026-10-21.md) |
| P-02 深化 | P02-GATEWAY、P02-CTX-ABLATION | [八模块准备记录](EIGHT_MODULE_PREP_2026-10-22.md)；依赖同版 pilot |
| DECISION-001 | DEC-T01–DEC-T06 | [切片与逐项状态](../features/DECISION-001/tasks.md)；[T01 离线验收](DEC_T01_ACCEPTANCE_2026-10-23.md) |
| P-03 | P03-ACCOUNTS、P03-RECOVERY-BACKUP、P03-DIAGNOSE | [P-02 至 P-04 任务包](PREDEV_P02_P04_TASK_PACKAGE_2026-10-20.md) |
| P-03 深化 | P03-MEMORY、P03-MCP | [八模块准备记录](EIGHT_MODULE_PREP_2026-10-22.md)；记忆依赖账户隔离 |
| P-04 | P04-FORMAL、P04-HANDOFF | [P-02 至 P-04 任务包](PREDEV_P02_P04_TASK_PACKAGE_2026-10-20.md) |

迁移前任务包位于 `docs/audits/`；[路径映射](../archive/README.md)记录旧路径。V1 的七日任务记录仍见 [V1_TASKS.md](V1_TASKS.md)，不能作为 P-01 至 P-04 已完成证据。
