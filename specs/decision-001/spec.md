# Feature Specification: DECISION-001 Python 开源选型决策（迁移）

**Created**: 2026-10-25 | **Status**: migrated (implementation in progress, acceptance partial) | **Origin**: [docs/features/DECISION-001/spec.md](../../docs/features/DECISION-001/spec.md)

**Repository Authority**: 本文件展开已批准的 DECISION-001 变更；权威与完整验收语义见 [SPEC.md](../../SPEC.md)、[现行契约](../../docs/contracts/CURRENT_CONTRACTS.md) 的 DECISION-001 各节。离线收敛不是产品 Go。

## User Scenarios & Testing

### User Story 1 - 条件化选型建议 (P1)

用户提交用途、硬条件、偏好与可选候选；系统将已准入官方事实映射为候选 × 条件矩阵，输出有 fact ID 支持的条件化建议，明确未知与冲突；无关键证据或硬条件全违反时不输出无条件赢家。

**Acceptance Scenarios**: DEC-AC-01–05、DEC-AC-07（定义见原 spec，不改）。

### User Story 2 - 兼容旧请求 (P1)

仅含 `goal` 的旧请求语义不变；新 `decision_context` 校验、幂等比较与 409 语义按现行契约。

**Acceptance Scenarios**: DEC-AC-01。

### User Story 3 - 决策过程与人工核源差异展示 (P2)

界面展示目标、矩阵、未知项及机器准入/人工核源分层，保留取消与历史路径。**Acceptance**: DEC-AC-03、06。

## Requirements

- **FR-013**（原 ID）：可选决策上下文、候选 × 条件证据矩阵、硬条件约束与无法推荐语义；细化验收 **DEC-AC-01–05、DEC-AC-07**，复用 FR-002/003/004/010（定义见 [SPEC.md](../../SPEC.md) 需求表）。

## Success Criteria

以 [docs/features/DECISION-001/tasks.md](../../docs/features/DECISION-001/tasks.md) 的逐任务验收缺口为准（实现/验收分离记录）；正式成功仍按冻结协议人工逐结论核源。

## Assumptions

- P-02 真实研究仍 No-Go；本功能不因 UI/格式实现而宣称产品通过。
