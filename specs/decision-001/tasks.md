# Tasks: DECISION-001（迁移自 docs/features/DECISION-001/tasks.md，原 ID/依赖/状态/证据保留）

**Authority**: 需求与验收以 [SPEC.md](../../SPEC.md) FR-013、[现行契约](../../docs/contracts/CURRENT_CONTRACTS.md) DECISION-001 各节为准；正式放行仍按[冻结协议](../../docs/evaluation/CURRENT_EVAL_PROTOCOL.json)；阶段顺序见 [PLANS.md](../../PLANS.md)。本文件不改门槛。

**状态口径**: `IMPLEMENTED`=代码已提交；`PARTIAL`=部分检查有证据；`DONE(offline)`=离线切片验收。实现完成与验收完成分开记录。

- [x] DEC-T01（依赖：P-02 失败分析）**IMPLEMENTED / DONE(offline)** — 冻结轨迹驱动的离线修复。证据：[DEC_T01_ACCEPTANCE_2026-10-23.md](../../docs/tasks/DEC_T01_ACCEPTANCE_2026-10-23.md)（绑定 `ec4a1496`）。剩余：真实取证/人工核源/费用按 P-02 与正式协议另行授权验证；不解除 No-Go。对应 DEC-AC-02、06。
- [ ] DEC-T02（依赖 T01、目标契约同步）**IMPLEMENTED / PARTIAL** — 可选决策上下文 + 旧请求兼容。证据：`266a49cc`、[DEC_T02_01_ACCEPTANCE_2026-10-24.md](../../docs/tasks/DEC_T02_01_ACCEPTANCE_2026-10-24.md)、[GitHub CI PostgreSQL job](https://github.com/wdadassdasadasd/adaptive-browser-agent/actions/runs/39984876768) 4 项集成测试（整体工作流失败）。剩余：Windows/WSL 冷启动、真实失租恢复、跨账户权限检查。对应 DEC-AC-01。
- [ ] DEC-T03（依赖 T02）**IMPLEMENTED / PARTIAL（DEC-T03-01 离线切片 DONE）** — 候选 × 条件矩阵。证据：`266a49cc`、[DEC_T03_01_ACCEPTANCE_2026-10-25.md](../../docs/tasks/DEC_T03_01_ACCEPTANCE_2026-10-25.md)、一次性 PostgreSQL 集成 4 passed、只读独立 Review。剩余：真实官方来源/冲突人工核查、Windows/WSL 进程崩溃恢复、正式门槛。对应 DEC-AC-02、03。
- [ ] DEC-T04（依赖 T03）**IMPLEMENTED / PARTIAL** — 条件化建议。证据：`266a49cc`、[backend/tests/unit/test_decision.py](../../backend/tests/unit/test_decision.py)（无证据、冲突、页面诱导不新增硬条件）。剩余：硬条件变化对照、授权真实研究后人工复核推荐价值。对应 DEC-AC-04、05。
- [ ] DEC-T05（依赖 T04）**IMPLEMENTED / PARTIAL** — API/UI 展示。证据：`266a49cc`、前端测试、[离线实施记录](../../docs/features/DECISION-001/OFFLINE_IMPLEMENTATION_2026-10-23.md)。剩余：Vue→API→历史/SSE 端到端、跨账户权限、部分报告检查。对应 DEC-AC-03、06。
- [ ] DEC-T06（依赖 T05）**PENDING** — 独立决策质量复核。已有：[离线复核模板](../../docs/features/DECISION-001/OFFLINE_DECISION_REVIEW_TEMPLATE.md)。剩余：同一冻结报告快照上逐条件复核（报告哈希、fact ID、复核者、时间），正式分母不变。对应 DEC-AC-07。

## Dependencies & Execution Order

T01→T02→T03→T04→T05→T06；若 T01 无真实事实质量进展，后继切片不得标产品完成。付费运行、提交/推送/PR/合并各自授权。
