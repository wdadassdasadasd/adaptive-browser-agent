# AI Coding 工程流程：官方来源研究与本项目取舍

> 查阅日期：2026-10-18（Asia/Shanghai），Star/API 复核约 08:30 UTC；0.5 相关来源同日复核。本文件是研究记录，不是 Adaptive Research Agent 已实现能力或 0.5 设计的独立批准记录。只使用项目官方仓库、官方文档和工程团队署名文章。五个仓库的文件链接固定到当次 `main` 提交；Star 数是当次 GitHub REST 快照，随时变化，只解释样本选择，不是技术优劣证据。实施具体外部 API 前仍须重新核对版本。

## 高 Star 项目：可核验做法与适用性

| 项目与 2026-10-18 Star 快照 | 直接核验的官方文件及做法 | 对本项目的判断 |
|---|---|---|
| [Codex，129,690](https://github.com/openai/codex) | 官方 [`docs/agents_md.md`](https://github.com/openai/codex/blob/8c076942cb70fba8e5c4732c23f1faabc4aed484/docs/agents_md.md) 指向 AGENTS 指南；[`agents_md.rs`](https://github.com/openai/codex/blob/8c076942cb70fba8e5c4732c23f1faabc4aed484/codex-rs/core/src/agents_md.rs) 明确从项目根到当前目录收集指令并定义合并边界。该提交**没有根目录 `AGENTS.md`**，不能以不存在的文件作证据。 | **采用原则**：短入口指令路由到有版本的规格与实际检查。**不照搬** Rust 实现或臆造该仓库的项目规则。 |
| [Gemini CLI，107,434](https://github.com/google-gemini/gemini-cli) | [仓库 `GEMINI.md`](https://github.com/google-gemini/gemini-cli/blob/c7b920717fad72229c788aa8efc646afac7a2965/GEMINI.md) 直接列出模块、按范围运行的测试和提交前的完整检查，且说明纯文档修改可跳过本地完整检查；另有 [`commands.md`](https://github.com/google-gemini/gemini-cli/blob/ed96faedfd5571f055c44f2c9509d62321d1138d/docs/reference/commands.md) 的 `/memory` 分层指令、[`tools.md`](https://github.com/google-gemini/gemini-cli/blob/ed96faedfd5571f055c44f2c9509d62321d1138d/docs/reference/tools.md) 的工具确认与沙箱、[`checkpointing.md`](https://github.com/google-gemini/gemini-cli/blob/ed96faedfd5571f055c44f2c9509d62321d1138d/docs/cli/checkpointing.md) 的修改前快照。 | **采用原则**：按修改范围选择检查，新会话确认实际加载的指令；权限和恢复以运行时证据确认。**不照搬** `.gemini` 配置或自动恢复：本仓库须保护已有 Git 工作区。 |
| [Cline，70,490](https://github.com/cline/cline) | [`plan-and-act.mdx`](https://github.com/cline/cline/blob/a42df8c8d5fd9d9f9a9073589baffe32ea9bb2f0/docs/core-workflows/plan-and-act.mdx) 区分计划与执行；[README](https://github.com/cline/cline/blob/a42df8c8d5fd9d9f9a9073589baffe32ea9bb2f0/README.md) 说明项目规则和 Skill；[`checkpoints.mdx`](https://github.com/cline/cline/blob/a42df8c8d5fd9d9f9a9073589baffe32ea9bb2f0/docs/core-workflows/checkpoints.mdx) 描述文件/任务恢复与差异检查。 | **采用原则**：高影响任务先明确设计与验收，再执行和审查差异；小修无需强制大计划。**不照搬** Cline 专有规则文件和自动批准策略。 |
| [OpenHands，91,170](https://github.com/OpenHands/OpenHands) | [README 的架构与仓库边界](https://github.com/OpenHands/OpenHands/blob/852132d38dbc15e03d6825bbacbeb971c72575be/README.md) 将 Agent Canvas、SDK/Agent Server、TypeScript 客户端和自动化拆为各自责任；[SDK 架构概述](https://github.com/OpenHands/docs/blob/bc442c6bc18826f2fe70cb357690ff89b02edea3/sdk/arch/overview.mdx) 区分本地单进程与生产沙箱模式；[沙箱说明](https://github.com/OpenHands/docs/blob/bc442c6bc18826f2fe70cb357690ff89b02edea3/openhands/usage/advanced/custom-sandbox-guide.mdx) 指出容器内执行。 | **采用原则**：明确 API、Worker、浏览器执行与客户端责任，按局域网部署威胁验证隔离。0.5 的同机容器首选、原生回退和浏览器外联阻断是本项目约束与待验证方案，**不是** OpenHands 经验对其可行性或安全性的证明。 |
| [Aider，49,606](https://github.com/Aider-AI/aider) | [`repomap.md`](https://github.com/Aider-AI/aider/blob/5dc9490bb35f9729ef2c95d00a19ccd30c26339c/aider/website/docs/repomap.md) 只向模型发送相关仓库地图；[`languages.md`](https://github.com/Aider-AI/aider/blob/5dc9490bb35f9729ef2c95d00a19ccd30c26339c/aider/website/docs/languages.md) 说明编辑后 lint；[`git.md`](https://github.com/Aider-AI/aider/blob/5dc9490bb35f9729ef2c95d00a19ccd30c26339c/aider/website/docs/git.md) 描述自动提交、dirty-file 提交及可关闭选项。 | **采用原则**：按任务缩小上下文、编辑后反馈真实检查结果。**不照搬** 自动 Git 提交：与本仓库的提交授权规则冲突。 |

这些项目的共同点是让代理读到**足够且相关**的上下文，并用工具结果和测试反馈修正工作；具体产品的权限、恢复、提交策略差异很大。以上为项目公开文档所述功能，不代表本地已经运行验证，也不代表各维护组织内部统一采用同一开发流程。

## 公司工程文章：公开案例的范围

| 第一方案例 | 文章报告的实际发现 | 适用于 Adaptive Research Agent 的决定与限制 |
|---|---|---|
| [OpenAI Engineering，2026-02-11](https://openai.com/index/harness-engineering/) | 文章记录**一个内部产品团队**的 agent-first 实验：短 `AGENTS.md` 作地图，版本化文档和计划放仓库，机械检查架构边界与文档链接，工作树中让代理看到 UI、日志和指标。 | 本轮用简短 `AGENTS.md` 指向规格、计划和历史证据；用离线校验器查确定性的链接/ID/协议结构。文章的代理自主建 PR、宽松合并门禁和“无人手写代码”是该团队实验做法，**不能**推断为 OpenAI 全公司政策，也不适合本项目 No-Go 阶段直接复制。 |
| [Anthropic Engineering，2025-11-26](https://www.anthropic.com/engineering/effective-harnesses-for-long-running-agents) | 文章的长任务实验以初始化环境、机器可读 feature list、每轮只做一项、进度记录和端到端浏览器验收避免跨上下文遗失、过早宣称完成；作者也指出浏览器工具有盲区。 | 用 `SPEC.md` 的验收 ID、`PLANS.md` 的任务/证据状态和真实任务尝试记录恢复上下文；离线测试不等于业务成功。文章中的自动 commit 和大型应用 feature JSON 是实验设置，不能替代本仓库提交授权、既有测试与 r12 原件。 |
| [GitHub Copilot Code Review 工程案例，2026-07-10](https://github.blog/ai-and-ml/github-copilot/better-tools-made-copilot-code-review-worse-heres-how-we-actually-improved-it/) | 把代码探索工具换成共享 `grep/glob/view` 后，内部基准发现成本升高、有效问题变少；从轨迹看是宽泛搜索循环。把指令改为从 PR diff 提问、批量轻搜索、再定向读代码后，文章报告平均审查成本约降 20%，质量维持。 | scoped Diff Review 从明确差异及需求出发，再查调用点和最小必要上下文；记录证据行号。该百分比只属于文中评测，不能外推到本项目，也不证明“工具越少越好”。 |
| [GitHub 工程师的 WRAP 流程，2025-12-26](https://github.blog/ai-and-ml/github-copilot/wrap-up-your-backlog-with-github-copilot-coding-agent/) | 两名作者介绍他们在 GitHub 使用 Copilot coding agent 的经验：写清上下文与示例、精炼仓库指令、把大问题拆成可测试和审查的原子任务，并让人判断任务缘由、歧义及跨系统影响。这是署名工程师报告的实践与建议，不能推断 GitHub 所有团队均照此执行。 | 将 0.5 的诊断、最小运行链路、证据、账户、恢复与验收分成依赖明确的任务；人负责确认产品门槛和真实核源。文章不证明本项目 2 任务并发或任何特定框架选择。 |
| [OpenAI Developers：精简 Skill 与提示，2026-09-11](https://developers.openai.com/blog/rethinking-skills-and-prompts-for-gpt-6-astra) | 官方文章指出 Skill 描述过多或过长会使选择困难，建议明确触发条件、按需展开；`AGENTS.md` 应按任务指向所需文档，避免每次编辑强制读全套文档。该建议针对文中模型与 Codex 工作流，不是所有模型的性能结论。 | 0.5 将根 `AGENTS.md` 作为版本和边界入口，Skill 只负责稳定且可重复的诊断、实施、评测流程；各任务读取相关契约。精简本身不替代验收、授权或安全检查。 |

## 本轮可迁移的最小闭环

1. **意图入口**：`AGENTS.md` 只说明权威版本、模块边界和如何找到 `SPEC.md`／`PLANS.md`；V1 当前行为、0.4 历史目标及冻结 0.3 设计各有明确状态。[Codex 官方指南](https://learn.chatgpt.com/docs/agent-configuration/agents-md)说明从仓库根到工作目录加载指令以及近处文件的覆盖顺序；这支持按范围配置，不替代本仓库事实核验。
2. **任务执行**：按 0.5 Task ID 定义输入、依赖、契约影响、验收和停止条件；先读取相关代码、测试及真实失败轨迹，保持 `VERIFIED`／`INFERRED`／`PROPOSED` 区分。调用级诊断先于 LangGraph、PostgreSQL 和容器最小链路；框架采用是产品决定，公开案例不能证明迁移会修好当前失败。
3. **反馈门禁**：离线检查可判文档、技能格式、ID 映射和代码回归；真实 LLM/浏览器任务与人工核源是另一个证据层，需独立费用授权。保留 B/G 历史原件与 O01–O03 的所有正式尝试，不通过删除失败或修改 r12 评分制造 Go。
4. **审查与保护**：从 scoped diff 启动审查，给出实际文件/行/测试结果；保护 dirty worktree、`browser-use` 固定 checkout 和历史 SQLite/benchmark。GitHub、OpenAI、Anthropic 的案例没有验证本项目的账户授权、持久认领、故障恢复、浏览器私网阻断、备份或 5 人容量，这些仍须独立验收。自动提交和远端写入不因参考项目采用而自动授权。

## 方法与未验证项

- Star 数来自 2026-10-18 官方 GitHub REST 仓库快照：[Codex](https://api.github.com/repos/openai/codex)、[Gemini CLI](https://api.github.com/repos/google-gemini/gemini-cli)、[Cline](https://api.github.com/repos/cline/cline)、[OpenHands](https://api.github.com/repos/OpenHands/OpenHands)、[Aider](https://api.github.com/repos/Aider-AI/aider)。当次默认分支提交分别为 `8c076942cb70fba8e5c4732c23f1faabc4aed484`、`ed96faedfd5571f055c44f2c9509d62321d1138d`、`a42df8c8d5fd9d9f9a9073589baffe32ea9bb2f0`、`852132d38dbc15e03d6825bbacbeb971c72575be`、`5dc9490bb35f9729ef2c95d00a19ccd30c26339c`；另查阅 Gemini CLI `GEMINI.md` 的 `c7b920717fad72229c788aa8efc646afac7a2965` 和 OpenHands/docs 的 `bc442c6bc18826f2fe70cb357690ff89b02edea3`。Star 快照和提交版本是不同概念。
- 只读官方仓库文件与网页，没有 clone 或运行五个参考项目，也未审查其全部代码、真实性能、内部权限或生产安全。OpenHands 项目结构正在演进，若比较运行时 API，应重新核验 [`software-agent-sdk`](https://github.com/OpenHands/software-agent-sdk)。
- 上述“采用原则”和“本轮可迁移”是**本项目依据来源作的推论**。真正架构与验收仍以本仓库现行代码、测试、历史 [r12 记录](../archive/design-0.3/10_CURRENT_STATE_AUDIT.md) 和经批准的规格版本为准；Star、文章 throughput、内部基准数字都不能替代本项目实测。0.5 的 LangGraph/PostgreSQL、同机 LAN 部署与放行门槛依据本项目规格；此研究只帮助设定 Codex 工作方式。
