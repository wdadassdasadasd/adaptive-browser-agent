# 文档导航

**PREP-BASELINE-20261029：40路径配置方案获批。** [连续任务记录](features/DECISION-001/tasks.md)是唯一决定、18项主清单、完整范围、实际检查和独立审查入口。准备完成、业务开工、真实质量、本人价值和Go分别判定。

| 需要了解 | 当前入口及适用范围 |
| --- | --- |
| 产品、价值、需求和AC | [SPEC](../SPEC.md)、[DECISION-001规格](features/DECISION-001/spec.md) |
| 纵向任务、依赖、投入与实践 | [PLANS](../PLANS.md)；首任务是登录/原始草稿＋最小supervisor，需单独实施授权 |
| 对象/API/状态/锁序/调用与证据 | [当前契约](contracts/CURRENT_CONTRACTS.md)，详细工程参数的权威正文 |
| 架构取舍 | [ADR5部署恢复](design/adr/0005-windows-worker-wsl-postgres.md)、[ADR7会话](design/adr/0007-interactive-evidence-decision-sessions.md)、[ADR8基线决定](design/adr/0008-m1-engineering-baseline.md) |
| 环境与工程流程 | [配置](engineering/CONFIGURATION.md)、[G0–G7](engineering/WORKFLOW.md)、[任务模板](engineering/TASK_TEMPLATE.md)、[测试策略](testing/STRATEGY.md) |
| 唯一现行评测 | [CURRENT_EVAL_PROTOCOL](evaluation/CURRENT_EVAL_PROTOCOL.json)、[M1能力材料](evaluation/DECISION_M1_PROTOCOL.json)、[评测说明](evaluation/README.md)、[核源流程](evaluation/REVIEW_WORKFLOW.md)；材料与执行资格分别审查，不自动开跑 |
| 固定版本研究与岗位映射 | [机制研究](research/HIGH_STAR_AGENT_MECHANISMS_2026-10-22.md)、[岗位研究](research/AGENT_JOB_PRODUCT_FIT_2026-10-23.md)；源码/观察/推论/本项目真实效果分开 |
| 已实现范围与历史 | [V1规格](specs/V1_SPEC.md)、[V1契约](contracts/V1_CONTRACTS.md)、[P-01验收](tasks/P01_ACCEPTANCE_2026-10-21.md)、[代码审查](audits/IMPLEMENTED_CODE_REVIEW_2026-10-27.md)、[任务索引](tasks/README.md) |
| 原件及历史配置 | [既有归档](archive/README.md)和带日期的audits/tasks/data；旧协议/未执行preparation从固定Git身份读取，不新增旧方案归档 |

本期采用WSL独立API/Worker/Pg、LangGraph阶段图、Search/GitHub/Fetch优先和受限Browser；Pg应用表拥有业务权威。详细数据流与限额只在契约及协议维护，本页不另立规则。原r12/P-02 No-Go保留。安装、环境/数据库、真实调用、购买和Git写操作均须对应授权，配置批准不包含首业务实施。
