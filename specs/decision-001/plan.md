# Implementation Plan: DECISION-001（迁移）

**Date**: 2026-10-25 | **Spec**: [spec.md](spec.md) | **Origin**: [docs/features/DECISION-001/tasks.md](../../docs/features/DECISION-001/tasks.md)

## Summary

在既有 AgentLoop/事实链路上补齐决策输入、矩阵、条件化建议与展示；无新增独立 Agent 或数值打分服务。

## Technical Context

复用现有 FastAPI/Worker/PostgreSQL/AgentLoop 链路（ADR-0005）；调用链与边界见 [现行契约](../../docs/contracts/CURRENT_CONTRACTS.md) DECISION-001 各节。

## Constitution Check

符合 constitution I/III/IV：四入口权威、实现/验收分离、原 ID 保留；R2 范围（API/持久化）改动须技术方案与独立审查。

## 任务顺序（依赖不变）

DEC-T01 → T02 → T03 → T04 → T05 → T06；证据与已提交切片见 tasks.md。
