# V3 工程配置迁移映射

日期：2026-10-23。范围为本轮工程文档和 Codex 入口；采用 Inventory → Classification → Mapping → Approval → Migration → Reference Validation → Regression → Cleanup。用户已要求实施配置方案；此映射不授权业务代码、付费运行或 GitHub 写操作。

| 现有位置 | 分类与目标位置 | 理由、引用影响与恢复 |
| --- | --- | --- |
| `SPEC.md`、`PLANS.md`、`docs/contracts/CURRENT_CONTRACTS.md`、`docs/evaluation/CURRENT_EVAL_PROTOCOL.json` | **保留**，继续作为四个现行入口 | 新产品方向先记录在决策和 ADR；正式规格／契约变更另审。本轮不改原要求。 |
| `docs/design/adr/0005-windows-worker-wsl-postgres.md` | **保留**；新增 `0006-python-open-source-decision-agent.md` | 0005 约束运行架构；0006 只记录产品决策与不变的运行边界。0005 页首“未实施”与 P-01 部分实现不一致，留作后续获批修订候选。 |
| 根 `AGENTS.md`、`docs/README.md` | **修订原位**，指向新决策与工程流程 | 只更新导航及已验证状态；Git 可恢复本轮修改。 |
| `docs/research/AI_CODING_WORKFLOWS.md`、`HIGH_STAR_AGENT_MECHANISMS_2026-10-22.md`、`ENGINEERING_STRUCTURE_REVIEW.md` | **保留**；新增 `AGENT_JOB_PRODUCT_FIT_2026-10-23.md` | 旧文是各自日期的研究证据；新文补充岗位与产品边界，不复制旧文结论为新事实。 |
| `docs/tasks/` 既有 P-01 至 P-04 任务包 | **保留**；重要新能力使用 `docs/features/DECISION-001/` | 原任务 ID、依赖和验收继续按现行计划解释；新任务包标草案，避免出现两份已批准计划。 |
| `docs/testing/V1_TEST_MATRIX.md`、`docs/evaluation/` | **保留**；新增 `docs/testing/STRATEGY.md` | 前者是 V1 与正式评测证据，后者只说明按风险选择 L0–L6 的执行方式。 |
| `.github/workflows/ci.yml`、`.github/PULL_REQUEST_TEMPLATE.md` | CI **保留**；PR 模板**原位修订** | 模板添加 Task／AC、真实证据与未验证项；无 CI 改写。 |
| `.agents/skills/` 三项、`.codex-workflow/lifecycle/` | 三项 Skill **保留**，其中实施与失败归因的旧流程引用**原位修订**；lifecycle **历史保留** | 两个 Skill 现指向 `docs/engineering/WORKFLOW.md`，实施 Skill 另指向 `docs/testing/STRATEGY.md`；归档流程与旧记录不动。 |
| `docs/archive/`、原始 SQLite 与 r12、`browser-use/` | **原样保留** | 历史和上游 checkout 不属于配置清理对象。 |

本轮**没有删除候选**。未来若提出删除，须列出被引用处、替代入口、原因及 Git 恢复点，获得单独批准后才能清理。所选目录的职责与 Codex 加载方式见[配置说明](../engineering/CONFIGURATION.md)；引用校验及结果见[配置验收](../audits/V3_CONFIG_ACCEPTANCE_2026-10-23.md)。CI 状态以实际远端运行结果为准。
