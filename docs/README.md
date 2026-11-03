# 文档导航

**RESEARCH-BASELINE-20261103：CONTENT-20261103-01完整确认，CONFIG-PLAN-20261103-01授权配置、限定离线检查和独立实施审查。** [唯一连续记录](features/DECISION-001/tasks.md)维护实际状态并保留原18项历史含义。FOCUS、DRAFT final-01、REVIEW final-02及更早交付继续只绑定各自原字节；配置、业务、真实价值与Go分别判定。

| 内容 | 权威入口 |
| --- | --- |
| 产品、范围及AC | [SPEC](../SPEC.md)、[功能规格](features/DECISION-001/spec.md) |
| 纵切、依赖与本人实践 | [PLANS](../PLANS.md)；首工认证/原始Draft/最小supervisor仍另批 |
| 对象、数据流、权限、限额 | [CURRENT_CONTRACTS](contracts/CURRENT_CONTRACTS.md) |
| 六用途提示词目标 | [PROMPT_CONTRACTS](contracts/PROMPT_CONTRACTS.md)，未由当前运行代码加载或实现 |
| 架构决定及历史理由 | [ADR5](design/adr/0005-windows-worker-wsl-postgres.md)、[ADR7](design/adr/0007-interactive-evidence-decision-sessions.md)、[ADR8](design/adr/0008-m1-engineering-baseline.md) |
| 环境、流程和检查 | [CONFIGURATION](engineering/CONFIGURATION.md)、[G0–G7](engineering/WORKFLOW.md)、[模板](engineering/TASK_TEMPLATE.md)、[STRATEGY](testing/STRATEGY.md) |
| 唯一现行评测 | [协议](evaluation/CURRENT_EVAL_PROTOCOL.json)、[能力引用](evaluation/DECISION_M1_PROTOCOL.json)、[入口](evaluation/README.md)、[核源](evaluation/REVIEW_WORKFLOW.md)；新材料待备、无新题/金标 |
| 本轮研究、审查与决定状态 | [2026-11-03研究复核](research/PREDEV_CONFIGURATION_REVIEW_2026-11-03.md)，由唯一任务记录引用 |
| 固定上游和岗位证据 | [机制研究](research/HIGH_STAR_AGENT_MECHANISMS_2026-10-22.md)、[岗位映射](research/AGENT_JOB_PRODUCT_FIT_2026-10-23.md) |
| 已实现与历史原件 | [V1规格](specs/V1_SPEC.md)、[V1契约](contracts/V1_CONTRACTS.md)、[P-01](tasks/P01_ACCEPTANCE_2026-10-21.md)、[原代码审查](audits/IMPLEMENTED_CODE_REVIEW_2026-10-27.md)、[任务索引](tasks/README.md)、[归档](archive/README.md) |

当前面向开发者／团队研究起草需求与工程方案并评审证据。主研究者按需委派同Task专题Work，全部调用共享有界额度，研究输入封存后再编译；四次compile含技术retry、首稿只保障首次尝试资源。WSL独立API／Worker／Pg和LangGraph仍是目标。GitHub优先，Search/Fetch按许可补研；Browser=0延期，MCP研究。Memory全入口禁用和延期，Case资料正常持久化；Context03a／Token03b，04非当前M1前置，禁用范围和全部限额见契约。实际用户价值、本人掌握和真实资格待证；Agent应用中大厂是求职方向，不推定届别或资格。原r12/P-02 No-Go不改；配置不授权首工、安装、环境、真实运行、购买或Git写。