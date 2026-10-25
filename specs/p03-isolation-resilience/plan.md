# Implementation Plan: P-03（迁移）

**Date**: 2026-10-25 | **Spec**: [spec.md](spec.md)

## Summary

按 PLANS.md P-03 行：隔离与韧性优先，容量模拟与备份演练随后；改动走现有 API/Worker/PostgreSQL 链路（ADR-0005）。

## Constitution Check

符合 I/III：契约边界不动；R2 范围（认证、事务恢复、备份）须技术方案与独立审查；真实诊断付费点单列。

## 顺序

P03-ACCOUNTS → P03-RECOVERY-BACKUP / P03-MEMORY / P03-CAPACITY；P03-MCP 依赖 P02-LOOP-TOOLS，P03-DIAGNOSE 依赖 P02-PILOT 与 P03-ACCOUNTS。停线与判定见 PLANS.md P-03 行。
