# V3 决策记录

本页记录人的选择和生效边界；现行开发要求仍以根目录 `SPEC.md`、`PLANS.md`、`docs/contracts/CURRENT_CONTRACTS.md` 和 `docs/evaluation/CURRENT_EVAL_PROTOCOL.json` 为准。研究依据见 [岗位与产品研究](../research/AGENT_JOB_PRODUCT_FIT_2026-10-23.md)。

| ID | 日期 | 决定与依据 | 生效边界 |
| --- | --- | --- | --- |
| V3-PRODUCT-001 | 2026-10-23 | 用户选择面向 **Agent 应用研发校招**，以**开发团队技术负责人**为首要用户，将 **Python 开源技术选型决策 Agent** 作为产品方向；首版给出有 fact ID 支持的条件化推荐。原因是现有九题覆盖候选发现、文档比较和发布核查，但真实成功与决策能力仍未证明。 | 产品方向、[产品 ADR](../design/adr/0006-python-open-source-decision-agent.md)和工程配置已批准；本轮“执行”授权 [SPEC](../../SPEC.md)、[计划](../../PLANS.md)、[契约](../contracts/CURRENT_CONTRACTS.md)的窄范围同步及对应离线业务开发。目标行为尚未实现，仍需逐任务验证。 |
| V3-ARCH-001 | 2026-10-23 | 保留 ADR-0005 的 Windows API、独立 Worker、WSL PostgreSQL 及现有 AgentLoop；不因产品表述改变引入新编排框架。 | 已有运行架构继续有效；P-01 假任务通过不代表真实任务通过。 |
| V3-EVAL-001 | 2026-10-23 | 九题、十五次正式尝试、人工官方核源和 299 元总额保持原协议；另设计独立决策质量复核。 | 补充复核不进入正式分母；任何额外真实运行仍逐次授权。 |
| V3-CONFIG-001 | 2026-10-23 | 采用模块化但按需创建的工程目录；复用三项现有 Skill，不预建子代理、项目 `config.toml` 或 MCP 配置。 | 本地配置批次按[迁移映射](V3_CONFIG_MIGRATION_MAP.md)完成，实际范围与未验证项见[验收记录](../audits/V3_CONFIG_ACCEPTANCE_2026-10-23.md)；不删除历史或修改业务代码。 |
| V3-AUTH-001 | 2026-10-23 | 用户对“现行 P-02 的离线失败诊断和修复”及“DECISION-001 规格／契约变更提案与任务包”要求“执行”。按[逐项映射](V3_SPEC_CONTRACT_CHANGE_PROPOSAL.md)把方向和兼容边界写入现行入口，DEC-AC-01–07 与现有 FR/AC 建立追踪。 | 授权本地规格／契约同步和相应离线业务开发；冻结协议、历史记录、付费运行及 Git 写操作不在本次授权内。同步是目标定义，不是测试或真实成功证据。 |

仍待单独授权：依赖安装、每次付费真实运行、部署、Git Commit／Push／PR／合并。不得把本页当作这些动作的自动授权；DECISION-001 的完成程度以实际代码、离线测试与真实评测证据分别记录。
