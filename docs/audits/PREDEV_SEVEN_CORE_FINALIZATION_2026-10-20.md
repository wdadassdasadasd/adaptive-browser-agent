# 七项核心能力开发前定稿记录

- 日期：2026-10-20，Asia/Shanghai。
- 范围：现行设计、评测证据契约、离线校验器、P-02..P-04 任务与交付清单。业务代码、真实付费研究、部署及 Git 发布没有在本轮执行。
- 结论：**开发前材料可进入逐项授权实施；产品仍为 No-Go。** 当前 V1 的离线检查不能证明目标 Worker/PostgreSQL、真实研究成功、五账户隔离或备份恢复。

## 已固定的七项主线

| 能力 | 当前基础 | 后续关口 |
| --- | --- | --- |
| Agent Loop/规划（S+） | `AgentLoop`、Planner、Evaluator、StateReducer 有界编排 | P-02 轨迹解释子目标、预期结果、无进展和报告缺口；正式结果核源。 |
| 工具调用/执行（S+） | 结构化 JSON `PlanDecision` 经 ToolRouter 调用浏览器/GitHub；参数和重复动作测试存在 | P-02 持久调用账本与真实工具反馈；面试准确称结构化决策而非原生 `tool_calls`。 |
| 可靠性/恢复（S+） | V1 超时、取消、重试、清理回归 | P-01 Worker/PostgreSQL 假任务关口；P-03 一次安全恢复、迟到写入和失联对账。 |
| Agent Eval（S+） | 固定 B/G/O 九题、15 次门槛与离线校验器 | P-02 同版 pilot；P-04 全批次、逐结论人工官方核源、隔时复核、项目总账。 |
| Context Engineering（S） | `ContextManager` 有界选择和近期轨迹 | P-02 保留关键 fact ID/来源/失败线索并按实际 provider 用量评价质量。 |
| 后端工程化（S） | Vue、FastAPI、asyncio、SQLite、SSE 的 V1 路径 | P-01 独立 Worker/WSL PostgreSQL，P-03 身份与隔离。 |
| 业务与完整交付（S） | 三类固定研究题与 V1 界面 | B01 真实研究纵切、失败/取消/历史、启动恢复及面试演示工件。 |

## 本轮修正

`current-2` 以**原字节**归档为 [`CURRENT_EVAL_PROTOCOL_current-2.json`](../evaluation/archive/CURRENT_EVAL_PROTOCOL_current-2.json)，SHA-256 `6fa06e0ff2cb73b6fcf246130da23aa559b9b5256a9ef46d8065496850e7a53f`。现行协议升为 `current-3`，只扩证据语义；`cases`、`pilot`、`formal`、`full_success_requires` 与归档版逐项相同。

校验器现在核对已知调用费用之和与任务费用、任务已知/总费用、模型调用用量与任务用量；报告快照 SHA-256 同人工复核及复查清单绑定。pilot 的未实施权限可明确标 `null`，正式批次必须实际检查。项目总账校验跨批次 run ID、遗漏、原始工件哈希、各阶段及 299 元总额；实际 provider 账单完整性仍需人工对账。此前“调用费用 500 元、任务只报 1 元”反例现被拒绝。

[现行规格](../../SPEC.md)、[计划](../../PLANS.md)、[契约](../contracts/CURRENT_CONTRACTS.md)已映射七项能力。新增[离线核源流程](../evaluation/REVIEW_WORKFLOW.md)、[后续任务包](PREDEV_P02_P04_TASK_PACKAGE_2026-10-20.md)与[交付清单](PREDEV_DELIVERY_CHECKLIST_2026-10-20.md)，明确依赖、边界、证据、停线与面试复现条件。

## 实际验证（本轮）

| 命令或检查 | 结果 |
| --- | --- |
| `.venv\Scripts\python.exe -m pytest -q --basetemp=.pytest_cache\current3-full-final` | 退出码 0；**441 passed，1 deselected**。含费用少报、未列费用、重复调用、pilot 权限、报告哈希、项目总账中断/遗漏/超支负例。 |
| `.venv\Scripts\python.exe scripts\validate_project.py` | 退出码 0；离线结构通过，输出说明真实模型与来源真伪未验证。 |
| `.venv\Scripts\python.exe -m ruff check adaptive_agent backend benchmark scripts tests`；`ruff format --check` 同范围 | 均退出码 0；78 个文件符合格式。 |
| `npm.cmd run type-check --prefix frontend`；`npm.cmd run test --prefix frontend`；`npm.cmd run build --prefix frontend` | 均退出码 0；前端 **20 passed**，生产构建完成。 |
| `git -c diff.ignoreSubmodules=all diff --check --ignore-submodules=all` | 退出码 0；现有已跟踪文件有 LF/CRLF 提示，无空白错误。 |
| 冻结协议与原件核对 | `cases`、`pilot`、`formal`、`full_success_requires` 与 `current-2` 逐项相同。原始 SQLite SHA-256 `1cf908a6f9e83985548ba7bd0753a204e6d8ccbaf70ac34daa9d3152ecbd0064`；r12 summary SHA-256 `4d1bd15ddb80c8f6fc4148d6ce4b95b4e6c13afe78f534d29158fb3b7839d88d`，均与先前记录一致。 |

## 未验证与下一关口

P-01 业务实现与两周假任务硬关口、P-02 真实 pilot、P-03 隔离/恢复/备份、P-04 正式 15 次均未进行。项目总账无法自动发现完全未登记的 provider 调用，必须人工核账；报告官方真实性必须人工打开来源核实。子模块工作树状态因 `.git/modules/browser-use` 访问受限仍未验证；本轮没有触碰其文件。当前工作树原有多项未提交改动均保留，本轮未提交或推送。

下一步以 [P-01 开工包](PREDEV_P01_START_PACKAGE_2026-10-20.md)的 P01-DB、P01-RUNTIME、P01-CALL、P01-API-CI 逐项实施；每项按仓库规则独立记录授权与实际证据。P-01 未过关不进入付费 pilot，所有正式数字继续标为待验证。
