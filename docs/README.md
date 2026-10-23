# 文档导航

本页只指路。后续开发的四个权威入口是[现行规格](../SPEC.md)、[现行计划](../PLANS.md)、[现行契约](contracts/CURRENT_CONTRACTS.md)与[评测协议](evaluation/CURRENT_EVAL_PROTOCOL.json)。[V3 决策记录](decisions/DECISION_LOG.md)已选择 Python 开源技术选型方向，目标规格与契约已同步；[迁移映射](decisions/V3_CONFIG_MIGRATION_MAP.md)说明配置改动。P-01 本机假任务架构关口已通过；真实研究质量与产品仍为 **No-Go**。既有 V1 行为核对 [V1 规格](specs/V1_SPEC.md)与 [V1 契约](contracts/V1_CONTRACTS.md)；新增切片核对现行契约、源码、测试与[逐任务证据](features/DECISION-001/tasks.md)。

| 要查什么 | 入口 | 使用方式 |
| --- | --- | --- |
| 当前架构与目标边界 | [架构说明](architecture/README.md)、[ADR-0005](design/adr/0005-windows-worker-wsl-postgres.md) | 区分默认 V1 与 P-01 独立开发入口，并核对实际验收范围。 |
| 下一项开发与验收 | [任务索引](tasks/README.md)、[P-01 任务包](tasks/PREDEV_P01_START_PACKAGE_2026-10-20.md) | Task ID 链接需求、依赖、改动边界和预定 AC；实际结果须另附证据。 |
| 后续研究质量、账户与正式验收 | [P-02 至 P-04 任务包](tasks/PREDEV_P02_P04_TASK_PACKAGE_2026-10-20.md) | 按现行计划的阶段关口推进。 |
| 真实研究如何判定 | [评测说明](evaluation/README.md)、[核源流程](evaluation/REVIEW_WORKFLOW.md) | 机器协议固定题面和门槛；离线核源仍需实际报告与记录。 |
| 开发前已检查什么 | [环境探针](audits/PREDEV_ENV_SETUP_2026-10-20.md)、[准备记录](audits/PREDEV_SEVEN_CORE_FINALIZATION_2026-10-20.md) | 只代表记录所写日期、命令和范围。 |
| 为什么这样整理 | [工程结构研究](research/ENGINEERING_STRUCTURE_REVIEW.md) | 包含高星项目参考、原问题和本轮迁移结果。 |
| 八模块为何这样设计 | [固定版本源码研究](research/HIGH_STAR_AGENT_MECHANISMS_2026-10-22.md)、[准备整改任务](tasks/EIGHT_MODULE_PREP_2026-10-22.md) | 区分上游机制、当前实现和待验证目标。 |
| V3 产品为何转向选型决策 | [岗位与竞品研究](research/AGENT_JOB_PRODUCT_FIT_2026-10-23.md)、[ADR-0006](design/adr/0006-python-open-source-decision-agent.md)、[权威变更提案](decisions/V3_SPEC_CONTRACT_CHANGE_PROPOSAL.md) | 区分批准的方向、已同步的[DECISION-001 需求](features/DECISION-001/spec.md)与尚待验收的实现。 |
| 单模块如何开发和交付 | [G0–G7 流程](engineering/WORKFLOW.md)、[已选工程配置](engineering/CONFIGURATION.md)、[任务模板](engineering/TASK_TEMPLATE.md)、[测试策略](testing/STRATEGY.md) | 按风险选择文档、检查和证据；重要新能力按[切片任务包](features/DECISION-001/tasks.md)逐项验收；[当前配置复审](audits/CONFIG_REVIEW_2026-10-24.md)列出实际检查与远端剩余门禁。 |
| 旧版本和旧验收 | [归档索引](archive/README.md) | 历史资料留原字节并标明旧路径。 |

`docs/audits/` 收指定基线的实际检查；`docs/tasks/` 收已批准阶段的任务及验收；`docs/features/` 按需收重要需求、切片与状态；`docs/research/` 收来源研究；`docs/architecture/` 说明当前/目标边界。根目录的 `browser-use/` 是上游 checkout，`data/` 保存本机运行证据。

开发与验收沿同一链路：**需求和 AC → Task ID → 契约与实现 → 适用检查 → 实际证据 → 阶段判定**。研究质量改动须从失败轨迹提出可证伪假说，做定点修改并以同口径复查。P-01 架构关口、P-02 质量 pilot、P-03 安全与恢复、P-04 正式验收各自判断，不以目录整理或离线检查替代。
