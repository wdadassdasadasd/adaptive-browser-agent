# 文档导航

本页只指路。后续开发的四个权威入口是[现行规格](../SPEC.md)、[现行计划](../PLANS.md)、[现行契约](contracts/CURRENT_CONTRACTS.md)与[评测协议](evaluation/CURRENT_EVAL_PROTOCOL.json)。目标架构仍待 P-01 实证；产品当前为 **No-Go**。已经实现的行为须核对 [V1 规格](specs/V1_SPEC.md)、[V1 契约](contracts/V1_CONTRACTS.md)、源码与测试。

| 要查什么 | 入口 | 使用方式 |
| --- | --- | --- |
| 当前架构与目标边界 | [架构说明](architecture/README.md)、[ADR-0005](design/adr/0005-windows-worker-wsl-postgres.md) | 区分默认 V1 与 P-01 独立开发入口，并核对实际验收范围。 |
| 下一项开发与验收 | [任务索引](tasks/README.md)、[P-01 任务包](tasks/PREDEV_P01_START_PACKAGE_2026-10-20.md) | Task ID 链接需求、依赖、改动边界和预定 AC；实际结果须另附证据。 |
| 后续研究质量、账户与正式验收 | [P-02 至 P-04 任务包](tasks/PREDEV_P02_P04_TASK_PACKAGE_2026-10-20.md) | 按现行计划的阶段关口推进。 |
| 真实研究如何判定 | [评测说明](evaluation/README.md)、[核源流程](evaluation/REVIEW_WORKFLOW.md) | 机器协议固定题面和门槛；离线核源仍需实际报告与记录。 |
| 开发前已检查什么 | [环境探针](audits/PREDEV_ENV_SETUP_2026-10-20.md)、[准备记录](audits/PREDEV_SEVEN_CORE_FINALIZATION_2026-10-20.md) | 只代表记录所写日期、命令和范围。 |
| 为什么这样整理 | [工程结构研究](research/ENGINEERING_STRUCTURE_REVIEW.md) | 包含高星项目参考、原问题和本轮迁移结果。 |
| 旧版本和旧验收 | [归档索引](archive/README.md) | 历史资料留原字节并标明旧路径。 |

`docs/audits/` 收指定基线的实际检查；`docs/tasks/` 收待实施的任务及后续单任务验收；`docs/research/` 收来源研究；`docs/architecture/` 说明当前/目标边界。根目录的 `browser-use/` 是上游 checkout，`data/` 保存本机运行证据。

开发与验收沿同一链路：**需求和 AC → Task ID → 契约与实现 → 适用检查 → 实际证据 → 阶段判定**。研究质量改动须从失败轨迹提出可证伪假说，做定点修改并以同口径复查。P-01 架构关口、P-02 质量 pilot、P-03 安全与恢复、P-04 正式验收各自判断，不以目录整理或离线检查替代。
