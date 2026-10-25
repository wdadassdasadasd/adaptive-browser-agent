# Implementation Plan: P-04（迁移）

**Date**: 2026-10-25 | **Spec**: [spec.md](spec.md)

## Summary

以冻结协议为唯一执行口径：先离线核对冻结清单与校验器，再授权执行正式批次并做人工核源、对账与交付包。

## Constitution Check

符合 II（协议与历史不改写）、III（Go/No-Go 只按协议证据）；批次与机动费用逐次授权，总额严格低于 300 元。

## 顺序

T1 → T2 → T3 → T4；批次中途不得修复续跑，须另起完整批次。
