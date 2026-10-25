# Tasks: P-02（迁移，沿用原 Task ID；真值源：[PREDEV_P02_P04_TASK_PACKAGE](../../docs/tasks/PREDEV_P02_P04_TASK_PACKAGE_2026-10-20.md)、[EIGHT_MODULE_PREP](../../docs/tasks/EIGHT_MODULE_PREP_2026-10-22.md)）

- [ ] P02-PILOT **诊断基线已交付 / 研究质量未通过（No-Go）** — 依赖 P-01 硬关口与单次付费授权。同版 B01–B03 三次真实尝试（B01 `failed/no_progress`、B02 `failed/token_budget`、B03 `partial/token_budget`），批次费用 0.12397276 元、未知调用 0；[人工核源](../../data/evaluation/p02-pilot-r11-20261023/human-review-conclusion-20261023.json)仅核实 B03 `f1/f4`；[交接工件](../../data/evaluation/p02-pilot-r11-20261023/predev-handoff-20261023.json)。剩余：调用级修复后的新 pilot 组须另获授权与预算，前后标不可比。
- [ ] P02-LOOP-TOOLS **未实施** — AgentLoop/规划/工具路由质量行为（当前 `PlanDecision` 结构保留）；依赖 P02-PILOT 修复证据。
- [ ] P02-CONTEXT **未实施** — 上下文裁剪与计量边界；依赖同上。
- [ ] P02-FACT-REPORT **未实施** — 事实准入/归属/社区补充/报告与费用对账；依赖 P02-PILOT 与调用账本。
- [ ] P02-GATEWAY **未实施** — NFR-010/AC-N10、NFR-002/AC-N02；依赖 P02-PILOT 与 P-01 调用账本。单供应商调用边界、额度/429/结果不明/缺失 usage 和费用对账；未知费用停线。
- [ ] P02-CTX-ABLATION **未实施** — FR-002/AC-002、FR-007/AC-007 离线三策略消融；依赖 P02-CONTEXT。
- [ ] P-02 后续纵切（FR-013/DECISION-001，DEC-T01–T06）→ [specs/decision-001/tasks.md](../decision-001/tasks.md)

**顺序**: PILOT 修复 → LOOP-TOOLS/CONTEXT/FACT-REPORT（可证伪症状驱动）→ GATEWAY/CTX-ABLATION；停线与判定见 [PLANS.md](../../PLANS.md) P-02 行与原任务包。
