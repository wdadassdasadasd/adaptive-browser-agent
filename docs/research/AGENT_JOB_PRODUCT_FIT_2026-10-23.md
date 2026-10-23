# Agent 校招与产品方向研究

研究日期：2026-10-23。来源为官方招聘页、官方仓库固定提交与本仓库原始证据。岗位是样本，不是统一录用门槛；上游源码机制不证明本项目已经实现或通过真实研究。Star 仅用于发现样本，不用于架构评分。

## 本地事实与岗位对应

| 证据层 | 可核验结论 |
| --- | --- |
| [P-01 假任务验收](../tasks/P01_ACCEPTANCE_2026-10-21.md) | 第二轮 48/48；主机内存峰值使用率 97.4%。证明本机任务架构关口，不证明真实浏览器容量或研究质量。 |
| [P-02 Pilot 轨迹](../audits/P02_PILOT_R11_FAILURE_TRIAGE_2026-10-23.md) | B01 无进展停止、B02/B03 在模型请求前遭 Token 预检拒绝，三题均非 full。 |
| [现有报告器](../../backend/src/adaptive_research/agent/reporter.py) | `ReportDraft` 只按 fact ID 组织事实；`recommendation` 当前固定为证据不足，没有技术选型决策链。 |

[百度 Agent 应用全栈校招 J99974](https://talent.baidu.com/jobs/detail/GRADUATE/6f9c3a86-6557-409d-8fa7-e6f4c68d6765)要求规划、工具、长短期记忆、状态和成功率／成本／延迟评测；[百度大模型研发校招 J100679](https://talent.baidu.com/jobs/detail/GRADUATE/66a12645-f0f1-435c-8426-9fb91f1be330)强调应用落地与调用链稳定性。[百度 Agent Harness 校招 J100779](https://talent.baidu.com/jobs/detail/GRADUATE/74d83772-1bd0-42b9-8cc5-69eb45696b62)更看重长任务约束、可验证执行和上下文交接；[百度智能体算法校招 J99969](https://talent.baidu.com/jobs/detail/GRADUATE/4f1cbc80-8332-4a92-b8fa-c0132b17d47e)还涉及模型原理、微调或算法实验。项目目标选择**应用研发**，不声称满足算法训练岗位。[腾讯 WorkBuddy Harness 岗位](https://careers.tencent.com/jobdesc.html?postId=2098252452842352640)是社招参考，不用作校招最低要求。

判断：公开技术研究场景本身不必然过窄；当前真实完成率和决策实现缺口使作品仍有 Demo 风险。招聘页无法证明项目完成后即可获得面试或录用。

## 固定源码与竞品边界

| 来源与源码位置 | 观察 | 对本项目的推论 |
| --- | --- | --- |
| [GPT Researcher `ResearchConductor`](https://github.com/assafelovic/gpt-researcher/blob/3582a6841fe7dc801e2a34e34ee408641aea9bce/gpt_researcher/skills/researcher.py)、[`SourceCurator`](https://github.com/assafelovic/gpt-researcher/blob/3582a6841fe7dc801e2a34e34ee408641aea9bce/gpt_researcher/skills/curator.py) | 分开研究规划、检索及来源整理，后者使用模型评价来源。 | 通用搜索报告已有成熟实现；本产品应证明团队约束到推荐的可追溯推理。 |
| [DeerFlow TokenBudgetMiddleware](https://github.com/bytedance/deer-flow/blob/1c9e962b323c4873ba0e63dbc5ee008540b2837f/backend/packages/harness/deerflow/agents/middlewares/token_budget_middleware.py) | 按运行记录警告、硬停线和停止原因。 | 借鉴明确失败语义，不把预算提示误当事前费用上限。 |
| [Open Deep Research 评测代码](https://github.com/langchain-ai/open_deep_research/blob/1b7d2e80db9faa586165c60e09096dbbfd483a64/tests/evaluators.py) | 分开来源质量、正确性和 groundedness 等维度；仓库已归档。 | 模型评分可做诊断，正式关键事实仍须人工官方核源。 |
| [promptfoo 评测实现](https://github.com/promptfoo/promptfoo/blob/03844fb957487102bd21f7434a229915cee90e02/src/evaluator.ts) | 评测与断言用量分别计入结果。 | 决策质量复核应与正式任务成功率、调用费用分开。 |
| [Dependabot 官方说明](https://docs.github.com/en/code-security/concepts/supply-chain-security/dependabot-security-updates)、[Renovate 更新流程](https://github.com/renovatebot/renovate/blob/main/lib/workers/repository/process/write.ts)、[GitHub Dependency Review](https://docs.github.com/en/pull-requests/how-tos/review-pull-requests/reviewing-dependency-changes-in-a-pull-request) | 依赖更新、PR 与版本／漏洞差异已有成熟工具。 | 首版不做自动升级机器人；升级影响分析须独立需求及验收。 |
| [OpenSSF Scorecard 检查定义](https://github.com/ossf/scorecard/blob/main/docs/checks/internal/checks.yaml) | 维护活动等检查有明确数据口径，同时说明检测能力的限制。 | 第三方分数可作补充事实，不替代团队约束与官方证据。 |

以上代码研究只读，未运行上游项目。既有八模块的更多固定版本源码见[机制研究](HIGH_STAR_AGENT_MECHANISMS_2026-10-22.md)。

## 候选方向与选择

| 方向 | 适配与代价 |
| --- | --- |
| A 证据优先技术研究 | 复用最高，但用户决策场景不突出。 |
| **B Python 开源技术选型决策** | 用户选择；现有九题覆盖候选发现、框架比较、发布核查，需补真实决策链。 |
| C Agent 可靠性与评测工作台 | Harness 价值较强，产品转向较大。 |
| D Agent 算法实验 | 算法岗位相关，但现有主机、预算和兼职窗口不足以支撑广泛训练目标。 |

B 的首要用户为开发团队技术负责人。产品价值假设是：带 fact ID、官方来源、未知项和条件化取舍的决策记录，比通用报告更易复核；**真实用户价值尚未验证**。现行九题仍是基础关口，不能用新评测替换；额外真实运行须另定预算并逐次授权。
