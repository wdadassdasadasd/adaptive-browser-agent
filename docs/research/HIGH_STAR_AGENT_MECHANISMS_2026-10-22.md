# 八模块 Agent 工程机制研究（2026-10-22）

**任务 ID：PREP-UPSTREAM-8。** 面向 Agent 应用研发校招，核对公开高关注度项目的固定版本源码与测试，选择适合本仓库 Windows 16 GB、8–12 周兼职、真实运行总预算低于 300 元的机制。以下“源码事实”只说明被引用版本如何实现；“本项目判断”是迁移建议。未运行上游项目，也未据其 Star 数或测试推断本项目研究成功率。

## 固定来源与本地基线

| 官方仓库 | 阅读的提交 | 选择用途 |
| --- | --- | --- |
| [DeerFlow](https://github.com/bytedance/deer-flow) | `60940ae9c528e5d740b27d058f2c5d80565a71b7` | 循环检测、上下文压缩、预算与记忆检索 |
| [GPT Researcher](https://github.com/assafelovic/gpt-researcher) | `3582a6841fe7dc801e2a34e34ee408641aea9bce` | 冻结证据的策略对照与指标检查 |
| [smolagents](https://github.com/huggingface/smolagents) | `96f33faaf028479119ec8d34507b47694cf14e34` | 小型 Agent Loop、结构化步骤记忆与用量监测 |
| [LangGraph](https://github.com/langchain-ai/langgraph) | `3cd57c038ad827d05f80c6488adea9994156c58c` | 超时、重试、未提交写入与恢复 |
| [MCP Python SDK](https://github.com/modelcontextprotocol/python-sdk) | `v2.1.1`，`0921d94a74db900dccd2d534842aa7b6160542d2` | 本地 stdio 工具协议验证 |
| [browser-use](https://github.com/browser-use/browser-use) | `aa093a843da5edbf323c0b4145c9b6a0db3ecde8` | 浏览器循环、超时、预算提示与收尾 |
| [promptfoo](https://github.com/promptfoo/promptfoo) | `03844fb957487102bd21f7434a229915cee90e02` | 质量、成本和延迟断言的缺失值处理 |
| [Open Deep Research](https://github.com/langchain-ai/open_deep_research) | `1b7d2e80db9faa586165c60e09096dbbfd483a64`；2026-08-21 已归档 | 研究简报与分项评测设计参考 |

本仓库的目标以[规格](../../SPEC.md)、[计划](../../PLANS.md)、[契约](../contracts/CURRENT_CONTRACTS.md)和[现行评测协议](../evaluation/CURRENT_EVAL_PROTOCOL.json)为准。[P-01 验收](../tasks/P01_ACCEPTANCE_2026-10-21.md)已有本机假任务 48/48 证据；[P-02 准备记录](../tasks/P02_PILOT_PREP_2026-10-21.md)记载优化前真实 pilot 因余额不足停在预检。V1 r12 与产品均为 No-Go。后端离线通过、假任务容量和真实公开网页研究须分别陈述。

## 新增对标机制的可执行取舍

以下“源码事实”限定在表中固定提交；“本项目取舍”仍是待验证方案。未运行上游测试，也没有复现上游公开成绩。

| 来源、源码事实 | 适用问题与本项目取舍 | 本项目验证方法与现状 |
| --- | --- | --- |
| [LangGraph 恢复测试](https://github.com/langchain-ai/langgraph/blob/3cd57c038ad827d05f80c6488adea9994156c58c/libs/langgraph/tests/test_pregel.py#L891)让一个并行节点失败、另一个成功，再断言恢复时成功节点不重跑。 | P-03 恢复需要明确已提交业务写入和结果不明的外部调用；应用表继续拥有事实与终态，框架引入仍按 ADR-0005 裁决。 | 在模型调用前、返回后提交前、提交后分别注入崩溃，核对调用账本、fencing token、事实和唯一终态；当前仅 P-01 假任务有部分故障证据。 |
| [browser-use Agent](https://github.com/browser-use/browser-use/blob/aa093a843da5edbf323c0b4145c9b6a0db3ecde8/browser_use/agent/service.py#L1543)有步数接近上限的提示、最后一步收尾、超时及失败处理。 | 研究步骤、浏览器内部步骤、模型调用、墙钟时间和 CNY 分层计量；报告预留由本项目预算边界执行。 | 用假工具分别触发各上限及取消，确认不会把提示当预算硬约束；真实浏览器和模型成本仍待实测。 |
| [GPT Researcher 上下文 replay](https://github.com/assafelovic/gpt-researcher/blob/3582a6841fe7dc801e2a34e34ee408641aea9bce/evals/context_filter/replay.py#L68)在冻结资料上比较过滤策略及成本、耗时、上下文 tokens。 | P-02 比较最近窗口、相关性选择、相关性加关键证据保护；来源和 fact ID 不因裁剪丢失。 | 同来源/轨迹离线消融记录字段覆盖、证据保留、provider 实报用量、费用和耗时；真实研究质量须另验。 |
| [promptfoo 成本断言](https://github.com/promptfoo/promptfoo/blob/03844fb957487102bd21f7434a229915cee90e02/src/assertions/cost.ts)在缺少成本值时不让断言通过；[延迟断言](https://github.com/promptfoo/promptfoo/blob/03844fb957487102bd21f7434a229915cee90e02/src/assertions/latency.ts)同样要求测量值。 | 结果评分、成本记录和运行时预算停线各有边界；未知 usage/费用保持 `null`。 | 离线测试缺失/超限值，真实批次逐调用与供应商账单对账；当前尚无完整真实批次。 |
| [Open Deep Research 评测](https://github.com/langchain-ai/open_deep_research/blob/1b7d2e80db9faa586165c60e09096dbbfd483a64/tests/evaluators.py#L103)分开相关性、结构、正确性、来源支持和完整度。 | 将任务字段完整、事实正确、来源支持、报告结构分别评分；仓库已归档，仅借鉴评测结构。 | current-3 固定题逐字段与逐结论人工官方核源，保留冲突与失败；模型评委分数不替代人工核源。 |

## 八模块机制与本项目取舍

| 模块 | 固定版本的源码事实 | 本项目判断与验证边界 |
| --- | --- | --- |
| **1. Agent Loop / Runtime** | [smolagents 主循环](https://github.com/huggingface/smolagents/blob/96f33faaf028479119ec8d34507b47694cf14e34/src/smolagents/agents.py#L540)记录步骤、工具结果和达到 `max_steps` 的错误；[DeerFlow 循环检测](https://github.com/bytedance/deer-flow/blob/60940ae9c528e5d740b27d058f2c5d80565a71b7/backend/packages/harness/deerflow/agents/middlewares/loop_detection_middleware.py#L113)将影响操作结果的参数纳入重复键，并在测试中区分相同页面与不同分页。 | 保留现有 [AgentLoop](../../backend/src/adaptive_research/agent/agent_loop.py)；用需求完成条件和失败原因裁决终态，按参数判断无进展。验证分页、重试、取消、恢复与达到上限时仍不误称成功。多层 middleware 不能替代本仓库的状态契约。 |
| **2. Context Engineering** | [smolagents 的 `summary_mode`](https://github.com/huggingface/smolagents/blob/96f33faaf028479119ec8d34507b47694cf14e34/src/smolagents/memory.py#L92)是从结构化历史确定性选择消息；[DeerFlow 压缩](https://github.com/bytedance/deer-flow/blob/60940ae9c528e5d740b27d058f2c5d80565a71b7/backend/packages/harness/deerflow/agents/middlewares/summarization_middleware.py#L853)在摘要成功后才替换旧上下文，其[测试](https://github.com/bytedance/deer-flow/blob/60940ae9c528e5d740b27d058f2c5d80565a71b7/backend/tests/test_summarization_source_coverage.py#L135)检查来源覆盖和失败后不删除历史。 | [当前 ContextManager](../../backend/src/adaptive_research/agent/context_manager.py)只取最近八条事实，且模型投影未保留 fact ID。首版先做确定性选择：当前需求、相关事实 ID/来源、最新观察和失败线索；截断不删除持久事实。模型摘要须另计费用和证据损失，不能仅凭字数减少宣称更省 Token。 |
| **3. Memory Management** | [smolagents ActionStep](https://github.com/huggingface/smolagents/blob/96f33faaf028479119ec8d34507b47694cf14e34/src/smolagents/memory.py#L51)分开工具调用、观察、错误和用量；[LangGraph Store](https://github.com/langchain-ai/langgraph/blob/3cd57c038ad827d05f80c6488adea9994156c58c/libs/checkpoint/langgraph/store/base/__init__.py#L578)按 namespace/key 存 JSON，可选向量索引；[DeerFlow 检索](https://github.com/bytedance/deer-flow/blob/60940ae9c528e5d740b27d058f2c5d80565a71b7/backend/packages/harness/deerflow/agents/memory/backends/deermem/deermem/core/relevance.py#L159)有词项相关性、去重和预算约束。 | 区分运行内上下文、PostgreSQL 任务状态、同 owner 跨任务来源线索及版本化操作规则。跨任务只复用与人工核源记录绑定的**来源线索**，新任务重新核验；过期、撤销、跨账户和冲突均入测试。现有 PostgreSQL 足以承载首版检索，不引入向量库。 |
| **4. Tool Calling / MCP** | [MCP 官方工具规范](https://github.com/modelcontextprotocol/modelcontextprotocol/blob/80041ab0a139a8f4fb3adbc99f7ae9113ea59671/docs/specification/2025-11-25/server/tools.mdx#L322)定义结构化工具结果与错误；[SDK 2.1.1 stdio 示例](https://github.com/modelcontextprotocol/python-sdk/blob/0921d94a74db900dccd2d534842aa7b6160542d2/examples/snippets/clients/stdio_client.py#L37)完成初始化、列工具和调用；[SDK 关闭逻辑](https://github.com/modelcontextprotocol/python-sdk/blob/0921d94a74db900dccd2d534842aa7b6160542d2/src/mcp/client/stdio.py#L248)管理子进程。 | 现有 [ToolRouter](../../backend/src/adaptive_research/agent/tools/router.py)是结构化 JSON 决策后的应用工具路由。先统一工具参数和错误语义，再用本地只读 stdio 服务验证仓库元数据与发布记录；测试协议错误、`is_error`、超时、取消和子进程清理。MCP 接入不等于模型原生 `tool_calls`。 |
| **5. Evaluation / Reflection** | [GPT Researcher replay](https://github.com/assafelovic/gpt-researcher/blob/3582a6841fe7dc801e2a34e34ee408641aea9bce/evals/context_filter/replay.py#L68)在冻结来源上比较不同过滤策略并记录成本、耗时、上下文 tokens；其[扰动实验](https://github.com/assafelovic/gpt-researcher/blob/3582a6841fe7dc801e2a34e34ee408641aea9bce/evals/quality_eval/perturbation.py#L1)检查指标对错误的敏感性。 | 用固定来源/轨迹比较“最近窗口、相关性选择、关键证据保护”，同时做人工逐结论核源。该项目的[域名集合式 citation_faithfulness](https://github.com/assafelovic/gpt-researcher/blob/3582a6841fe7dc801e2a34e34ee408641aea9bce/evals/quality_eval/metrics.py#L205)不能证明每条主张被来源支持；离线 replay 不计入当前协议的真实成功率。 |
| **6. LLM Gateway** | [DeerFlow token 预算](https://github.com/bytedance/deer-flow/blob/60940ae9c528e5d740b27d058f2c5d80565a71b7/backend/packages/harness/deerflow/agents/middlewares/token_budget_middleware.py#L115)跟踪运行和停止原因；[smolagents Monitor](https://github.com/huggingface/smolagents/blob/96f33faaf028479119ec8d34507b47694cf14e34/src/smolagents/monitoring.py#L36)按步累计 provider 返回的用量与时长。 | 在现有 [DeepSeekClient](../../backend/src/adaptive_research/agent/llm/deepseek.py)和调用账本上统一阶段、截止时间、并发与有限重试。输入预算估算、provider 已报 Token、缓存命中和 CNY 费用分别存，缺失值保持未知；传输结果不明时不盲目重发。上游响应后预算检测不能被引用为调用前严格金额上限。 |
| **7. Observability / Persistence** | [LangGraph 重试与超时实现](https://github.com/langchain-ai/langgraph/blob/3cd57c038ad827d05f80c6488adea9994156c58c/libs/langgraph/langgraph/pregel/_retry.py#L600)清理未提交写入并停止迟到任务；[PostgresSaver](https://github.com/langchain-ai/langgraph/blob/3cd57c038ad827d05f80c6488adea9994156c58c/libs/checkpoint-postgres/langgraph/checkpoint/postgres/__init__.py#L326)存 checkpoint 与 pending writes。 | [现有 PgStore](../../backend/src/adaptive_research/infrastructure/pg_store.py)继续拥有账户、任务、事实、调用和用户事件。用 call ID、fencing token、费用总账和事件 ID 证明恢复/补读；图检查点或重复写入去重无法保证外部模型/浏览器调用 exactly-once。 |
| **8. Backend / Product Delivery** | [smolagents GAIA runner](https://github.com/huggingface/smolagents/blob/96f33faaf028479119ec8d34507b47694cf14e34/examples/open_deep_research/run_gaia.py#L223)逐题保存预测、步骤、异常、时间和 tokens；[LangGraph 恢复测试](https://github.com/langchain-ai/langgraph/blob/3cd57c038ad827d05f80c6488adea9994156c58c/libs/langgraph/tests/test_retry.py#L2689)区分重跑失败处理与重做原节点。 | 交付以真实 task/run ID 连到界面、API、数据库、SSE、报告及脱敏 trace；保留五账户隔离、冷启动、一次故障恢复和加密备份。上游示例任务或测试通过，不替代本项目九题正式评测和人工官方核源。 |

## 记忆和预算的四个层次

| 层次 | 保存与读取 | 验收重点 |
| --- | --- | --- |
| 工作上下文 | 当前任务、未完成需求、相关事实 ID/来源、最新观察和错误的有界投影 | 老关键事实相关时仍可取回；页面文字不得变成系统指令 |
| 持久任务记忆 | 已提交事件、事实、调用和执行代次由应用表管理 | 崩溃恢复时不丢已接受事实，不将未知调用费用记为零 |
| 跨任务来源线索 | 同 owner 的人工核源引用、来源地址、时间和过期状态 | 过期/撤销不注入；新任务重新核验；正式批次隔离运行 |
| 程序性记忆 | 版本化且经确认的操作规则/Skill | 规则可追溯；公开页面不能自动生成高权限规则 |

Token 有三种不同数字：**调用前估算**用于压缩和保守预留，**provider 实际用量**用于运行统计，**按价表计出的 CNY**用于费用停线。摘要、JSON 修复和重试各是独立模型调用；节省上下文 Token 还须扣除压缩成本和额外重试。上游 [DeerFlow 记忆注入](https://github.com/bytedance/deer-flow/blob/60940ae9c528e5d740b27d058f2c5d80565a71b7/backend/packages/harness/deerflow/agents/memory/backends/deermem/deermem/core/prompt.py#L469)允许特定纠正事实超出普通注入额度，本项目不能据此承诺统一硬上限。

## 实施优先顺序与证据要求

1. 先保留当前 B01–B03 的优化前真实 pilot；[最新预检记录](../../data/evaluation/p02-pilot-preflight-stop-20261022.json)是零次任务、零次付费调用的停线，不充作一条失败尝试。运行时重新冻结代码、锁、模型、价表、题面和环境。
2. 按真实失败轨迹修研究链，再用冻结来源的离线消融检查机制，之后单列少量在线复验。每个变更记“症状、假说、反证、改动、回归、结果”；指标变化只描述实际可比条件。
3. 对 Gateway、MCP、跨任务记忆和账户层分别保留离线合同测试和实际系统验证；冻结正式批次中关闭跨任务记忆。正式九题的 15 次、人工核源、费用和 Go/No-Go 仍由[现行协议](../evaluation/CURRENT_EVAL_PROTOCOL.json)裁决。

参考源码表明机制可供借鉴；是否在本仓库正确运行，须看本仓库实际测试、真实任务、人工核源和资源记录。
