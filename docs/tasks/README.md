# 当前任务索引

阶段顺序与放行条件以[现行计划](../../PLANS.md)为准。本索引从两份任务包中的 Task ID 汇总，只列入口，不维护另一套任务状态。每个 Task ID 的依赖、拟改范围和 AC 在对应表格的唯一记录中；实施后应在该条记录链接实际命令、结果、证据和未解决项。

| 阶段 | Task ID | 记录 |
| --- | --- | --- |
| R0 | R0 结构迁移 | [本地验收记录](R0_ACCEPTANCE_2026-10-20.md) |
| P-01 | P01-ENV、P01-TRACE、P01-DB、P01-RUNTIME、P01-CALL、P01-API-CI | [P-01 任务记录](PREDEV_P01_START_PACKAGE_2026-10-20.md)，[假任务验收证据](P01_ACCEPTANCE_2026-10-21.md) |
| P-02 | P02-PILOT、P02-LOOP-TOOLS、P02-CONTEXT、P02-FACT-REPORT | [P-02 至 P-04 任务记录](PREDEV_P02_P04_TASK_PACKAGE_2026-10-20.md)，[pilot 离线准备证据](P02_PILOT_PREP_2026-10-21.md) |
| P-03 | P03-ACCOUNTS、P03-RECOVERY-BACKUP、P03-DIAGNOSE | [P-02 至 P-04 任务包](PREDEV_P02_P04_TASK_PACKAGE_2026-10-20.md) |
| P-04 | P04-FORMAL、P04-HANDOFF | [P-02 至 P-04 任务包](PREDEV_P02_P04_TASK_PACKAGE_2026-10-20.md) |

迁移前任务包位于 `docs/audits/`；[路径映射](../archive/README.md)记录旧路径。V1 的七日任务记录仍见 [V1_TASKS.md](V1_TASKS.md)，不能作为 P-01 至 P-04 已完成证据。
