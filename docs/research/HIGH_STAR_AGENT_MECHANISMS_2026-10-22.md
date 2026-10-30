# Agent工程机制：固定来源与现行采用裁决

**PREP-UPSTREAM-8，承接PREP-BASELINE-20261029。** 当前产品和工程采用由[契约](../contracts/CURRENT_CONTRACTS.md)、[计划](../../PLANS.md)和[唯一协议](../evaluation/CURRENT_EVAL_PROTOCOL.json)定义。后续带日期源码/测试/PR观察保留其原身份，不是第二套现行要求。未运行上游测试或模型，不据Star和作者成绩证明本项目效果。

## 2026-10-29：研究问题、采用、失败与验收

| 问题/本项目缺口 | 固定证据及实际行为 | 采用/不采用和失败边界 | Task/AC/改变选择的新证据 |
| --- | --- | --- | --- |
| 重入/事务/检查点 | LangGraph 3cd57c038ad827d05f80c6488adea9994156c58c的AsyncPostgresSaver setup建表迁移、独立psycopg；声明1.2.16/checkpoint-postgres3.2.0非本机安装/兼容证明 | 真实阶段图、Pg业务权威、稳定Obligation/最终claim，checkpoint仅引用；不整体包旧AgentLoop/不把replay当只读审计 | DEC-M1-02/03b，DEC-AC-09/13/14；提交切点/并发/依赖资格失败才针对重评 |
| Context裁剪反证 | 当前ContextManager已有fact ID，仍最近8条/字符clip；旧“无ID”观察纠正。smolagents结构步骤/GPT Researcher多策略分离历史与投影 | 关系＋关键词，保护条件/反证/限定，展开后筛适用性；装不下partial；额外模型summary0，无vector/reranker默认 | 03a/04，DEC-AC-18；未采集/识别/绑定/选入/裁剪分别取证 |
| 从零候选/停止 | GPT Researcher3582a6841fe7dc801e2a34e34ee408641aea9bce分初搜/计划/抓取/curation；curator额外模型/JSON恢复失败回原源 | routes3/pool20/deep3，成功batch/no_delta/故障分开，低rank不作排除；不照搬额外curator调用/无限递归或visited=核源 | 03a/b，DEC-AC-10/11/12；配额不足如实partial，再议具体预算/范围 |
| 引用/主体真值 | 本地Evaluator片段子串/DecisionService labelhash不证明语义/身份；官方Search忽略未知参数，Fetch主要title/content | strict请求、不可变安全表示hash/UTF8 locator/支持反证限定冲突；无finalURL/源站时间不伪造；机器准入与人工核源分开 | 03，DEC-AC-11/19；同名fork/版本/反证/漂移测试 |
| Memory/撤销 | LangGraph namespace/TTL不等owner/撤销，Letta编译边界不授策略自治 | 自动线索＋本人明确长期技术偏好，typed lineage/revision/expiry，读不续，满更正先停旧项；不只显式导入/不积累流程或敏感画像 | 04，DEC-AC-17/18；否定/引用/冲突/knownalias新ID复活负例 |
| Token/费用 | DeepSeek recipe935817c66f5d6e64838f419692545f06787e485f完整模板/特殊token；OpenCode字符估算/usage锚点非精确tokenizer | 官方Tokenizer正式准入，匹配完整请求/模型/字段，漂移停发，首次有限诊断另授；repair0/summary0/thinkingdisabled；usage/cache/价/余额分账 | 03b，DEC-AC-13/18；本机资格未验，旧缺rawprompt不补算 |
| Evaluation/Tracing/优化 | promptfoo缺值不通过、GPT Researcher固定源replay、Open Deep Research质量维度只提供方法 | canonical Pg链＋只读TraceView；原症状/预目标/最小改动/固定源回归/独立审查/另授匹配真复测，至少纠正1真症状 | 06/07/08，DEC-AC-19/20；条件/来源/模型漂移和人工改稿不冒充程序收益 |
| 工具与Browser | 研究browser-use aa093...与本地gitlink7be96...不同；mitmproxy12.3.1 commit51c1d6b2d8d3367a773411eb7a3eeccec82b3ea7须再验serializer/pipe | direct API/DeepSeek单SearchFetch、MCP研究非交付；Browser仅nav/wait/scroll/DOM、唯一出口/ns/bridge/sup，无连接资格0 | 05，DEC-AC-13/14/15；DNS/v4/v6/redirect/subresource/UDP/旧连接对抗实证；供应商内部不可观察 |

具体源码：[Saver](https://github.com/langchain-ai/langgraph/blob/3cd57c038ad827d05f80c6488adea9994156c58c/libs/checkpoint-postgres/langgraph/checkpoint/postgres/aio.py)、[ResearchConductor](https://github.com/assafelovic/gpt-researcher/blob/3582a6841fe7dc801e2a34e34ee408641aea9bce/gpt_researcher/skills/researcher.py)、[SourceCurator](https://github.com/assafelovic/gpt-researcher/blob/3582a6841fe7dc801e2a34e34ee408641aea9bce/gpt_researcher/skills/curator.py)、[本地ContextManager](../../backend/src/adaptive_research/agent/context_manager.py)、[Evaluator](../../backend/src/adaptive_research/agent/evaluator.py)、[DecisionService](../../backend/src/adaptive_research/agent/decision.py)、[官方Search/Fetch](https://api-docs.deepseek.com/zh-cn/guides/search/)。源码事实、推论、采用配置和本项目实测分开；当前配额闭合不证明成功率/依赖/资金资格。

## 2026-10-22固定来源观察

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
| **2. Context Engineering** | [smolagents 的 `summary_mode`](https://github.com/huggingface/smolagents/blob/96f33faaf028479119ec8d34507b47694cf14e34/src/smolagents/memory.py#L92)是从结构化历史确定性选择消息；[DeerFlow 压缩](https://github.com/bytedance/deer-flow/blob/60940ae9c528e5d740b27d058f2c5d80565a71b7/backend/packages/harness/deerflow/agents/middlewares/summarization_middleware.py#L853)在摘要成功后才替换旧上下文，其[测试](https://github.com/bytedance/deer-flow/blob/60940ae9c528e5d740b27d058f2c5d80565a71b7/backend/tests/test_summarization_source_coverage.py#L135)检查来源覆盖和失败后不删除历史。 | [当前 ContextManager](../../backend/src/adaptive_research/agent/context_manager.py)已保留fact ID，仍取最近八条和字符clip；“无ID”是过时描述。当前采用关系保护选择/summary0，不以字数减少宣称省Token。 |
| **3. Memory Management** | [smolagents ActionStep](https://github.com/huggingface/smolagents/blob/96f33faaf028479119ec8d34507b47694cf14e34/src/smolagents/memory.py#L51)分开工具调用、观察、错误和用量；[LangGraph Store](https://github.com/langchain-ai/langgraph/blob/3cd57c038ad827d05f80c6488adea9994156c58c/libs/checkpoint/langgraph/store/base/__init__.py#L578)按 namespace/key 存 JSON，可选向量索引；[DeerFlow 检索](https://github.com/bytedance/deer-flow/blob/60940ae9c528e5d740b27d058f2c5d80565a71b7/backend/packages/harness/deerflow/agents/memory/backends/deermem/deermem/core/relevance.py#L159)有词项相关性、去重和预算约束。 | 区分运行内上下文、PostgreSQL 任务状态、同 owner 跨任务来源线索及版本化操作规则。跨任务只复用与人工核源记录绑定的**来源线索**，新任务重新核验；过期、撤销、跨账户和冲突均入测试。现有 PostgreSQL 足以承载首版检索，不引入向量库。 |
| **4. Tool Calling / MCP** | [MCP 官方工具规范](https://github.com/modelcontextprotocol/modelcontextprotocol/blob/80041ab0a139a8f4fb3adbc99f7ae9113ea59671/docs/specification/2025-11-25/server/tools.mdx#L322)定义结构化工具结果与错误；[SDK 2.1.1 stdio 示例](https://github.com/modelcontextprotocol/python-sdk/blob/0921d94a74db900dccd2d534842aa7b6160542d2/examples/snippets/clients/stdio_client.py#L37)完成初始化、列工具和调用；[SDK 关闭逻辑](https://github.com/modelcontextprotocol/python-sdk/blob/0921d94a74db900dccd2d534842aa7b6160542d2/src/mcp/client/stdio.py#L248)管理子进程。 | 现有 [ToolRouter](../../backend/src/adaptive_research/agent/tools/router.py)是结构化 JSON 决策后的应用工具路由。统一工具参数/错误/生命周期；MCP stdio仅保留机制研究，不要求M1实践，后续另授才验证真实连接。MCP 接入不等于模型原生 `tool_calls`。 |
| **5. Evaluation / Reflection** | [GPT Researcher replay](https://github.com/assafelovic/gpt-researcher/blob/3582a6841fe7dc801e2a34e34ee408641aea9bce/evals/context_filter/replay.py#L68)在冻结来源上比较不同过滤策略并记录成本、耗时、上下文 tokens；其[扰动实验](https://github.com/assafelovic/gpt-researcher/blob/3582a6841fe7dc801e2a34e34ee408641aea9bce/evals/quality_eval/perturbation.py#L1)检查指标对错误的敏感性。 | 用固定来源/轨迹比较“最近窗口、相关性选择、关键证据保护”，同时做人工逐结论核源。该项目的[域名集合式 citation_faithfulness](https://github.com/assafelovic/gpt-researcher/blob/3582a6841fe7dc801e2a34e34ee408641aea9bce/evals/quality_eval/metrics.py#L205)不能证明每条主张被来源支持；离线 replay 不计入当前协议的真实成功率。 |
| **6. LLM Gateway** | [DeerFlow token 预算](https://github.com/bytedance/deer-flow/blob/60940ae9c528e5d740b27d058f2c5d80565a71b7/backend/packages/harness/deerflow/agents/middlewares/token_budget_middleware.py#L115)跟踪运行和停止原因；[smolagents Monitor](https://github.com/huggingface/smolagents/blob/96f33faaf028479119ec8d34507b47694cf14e34/src/smolagents/monitoring.py#L36)按步累计 provider 返回的用量与时长。 | 在现有 [DeepSeekClient](../../backend/src/adaptive_research/agent/llm/deepseek.py)和调用账本上统一阶段、截止时间、并发与有限重试。输入预算估算、provider 已报 Token、缓存命中和 CNY 费用分别存，缺失值保持未知；传输结果不明时不盲目重发。上游响应后预算检测不能被引用为调用前严格金额上限。 |
| **7. Observability / Persistence** | [LangGraph 重试与超时实现](https://github.com/langchain-ai/langgraph/blob/3cd57c038ad827d05f80c6488adea9994156c58c/libs/langgraph/langgraph/pregel/_retry.py#L600)清理未提交写入并停止迟到任务；[PostgresSaver](https://github.com/langchain-ai/langgraph/blob/3cd57c038ad827d05f80c6488adea9994156c58c/libs/checkpoint-postgres/langgraph/checkpoint/postgres/__init__.py#L326)存 checkpoint 与 pending writes。 | [现有 PgStore](../../backend/src/adaptive_research/infrastructure/pg_store.py)继续拥有账户、任务、事实、调用和用户事件。用 call ID、fencing token、费用总账和事件 ID 证明恢复/补读；图检查点或重复写入去重无法保证外部模型/浏览器调用 exactly-once。 |
| **8. Backend / Product Delivery** | [smolagents GAIA runner](https://github.com/huggingface/smolagents/blob/96f33faaf028479119ec8d34507b47694cf14e34/examples/open_deep_research/run_gaia.py#L223)逐题保存预测、步骤、异常、时间和 tokens；[LangGraph 恢复测试](https://github.com/langchain-ai/langgraph/blob/3cd57c038ad827d05f80c6488adea9994156c58c/libs/langgraph/tests/test_retry.py#L2689)区分重跑失败处理与重做原节点。 | 交付以真实 task/run ID 连到界面、API、数据库、SSE、报告及脱敏 trace；当前本人＋第二测试身份、连续资格和独立备份按新契约；上游示例不替代新唯一协议及人工核源。 |

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
3. 对 Gateway、MCP、跨任务记忆和账户层分别保留离线合同测试和实际系统验证；正式批次冻结实际Memory策略，不手工清历史制造优势；旧九题15次只解释历史，新批按[唯一协议](../evaluation/CURRENT_EVAL_PROTOCOL.json)。

参考源码表明机制可供借鉴；是否在本仓库正确运行，须看本仓库实际测试、真实任务、人工核源和资源记录。

## 2026-10-26 固定版本复核：产品、框架与基础设施

本节观察日期为 **2026-10-26**。本次实际读取固定提交的核心源码、相关测试和评测脚本，未安装或运行上游项目、测试、模型、浏览器或数据集。上文保留 2026-10-22 观察；例如当时的 pilot 状态和 ContextManager 描述不能直接当作今日现状。

### 样本选择与版本

选择一个研究产品、一个小型 Agent 框架和一个浏览器基础设施项目，分别观察完整研究链、最小执行语义和真实工具环境边界。Star 是发现样本的关注度信号，以下数值为本轮官方 GitHub API 观察，不用于质量排名或效果结论。

| 官方仓库 | 固定提交／提交日期 | 2026-10-26 Star | 选择理由 |
| --- | --- | ---: | --- |
| [GPT Researcher](https://github.com/assafelovic/gpt-researcher) | [3582a6841fe7dc801e2a34e34ee408641aea9bce](https://github.com/assafelovic/gpt-researcher/commit/3582a6841fe7dc801e2a34e34ee408641aea9bce)／2026-10-10 | 30,292 | 研究产品，能核查查询规划、来源、上下文和报告评测之间的边界。 |
| [smolagents](https://github.com/huggingface/smolagents) | [96f33faaf028479119ec8d34507b47694cf14e34](https://github.com/huggingface/smolagents/commit/96f33faaf028479119ec8d34507b47694cf14e34)／2026-10-06 | 30,054 | 框架，以显式步骤、工具／代码动作和记忆观察小型运行循环的取舍。 |
| [browser-use](https://github.com/browser-use/browser-use) | [aa093a843da5edbf323c0b4145c9b6a0db3ecde8](https://github.com/browser-use/browser-use/commit/aa093a843da5edbf323c0b4145c9b6a0db3ecde8)／2026-10-17 | 119,142 | 工具基础设施，重点是浏览器状态变化、动作失效、超时和上下文压缩。 |

关注度来源：[GPT Researcher API](https://api.github.com/repos/assafelovic/gpt-researcher)、[smolagents API](https://api.github.com/repos/huggingface/smolagents)、[browser-use API](https://api.github.com/repos/browser-use/browser-use)。固定提交及上述日期用于复查，不能将默认分支后续行为混入本次结论。

### GPT Researcher：研究产品的链路与评测边界

- **源码事实——调用与数据归属：** [agent.py](https://github.com/assafelovic/gpt-researcher/blob/3582a6841fe7dc801e2a34e34ee408641aea9bce/gpt_researcher/agent.py#L141)的研究实例持有 context、visited_urls、research_sources、costs 等运行数据，并组合 conductor、context manager、scraper、curator、report generator。[ResearchConductor](https://github.com/assafelovic/gpt-researcher/blob/3582a6841fe7dc801e2a34e34ee408641aea9bce/gpt_researcher/skills/researcher.py#L97)根据来源类型规划查询、检索／抓取、选取上下文，再把资料交给报告链。已读类中这些运行字段的存在，不足以证明整个部署具备持久恢复。
- **源码事实——来源与工具：** [researcher.py](https://github.com/assafelovic/gpt-researcher/blob/3582a6841fe7dc801e2a34e34ee408641aea9bce/gpt_researcher/skills/researcher.py#L836)保留用于规划的初始搜索来源，区分待抓取预览与已抓取正文，visited_urls 去重；MCP 缓存人口由锁保护。其[规划来源测试](https://github.com/assafelovic/gpt-researcher/blob/3582a6841fe7dc801e2a34e34ee408641aea9bce/tests/test_planning_sources.py)覆盖后续搜索为空、初始页失败和其他检索器来源保留；[检索回归](https://github.com/assafelovic/gpt-researcher/blob/3582a6841fe7dc801e2a34e34ee408641aea9bce/tests/test_research_conductor_retrieval.py)区分预览与正文及已访问标记。
- **源码事实——上下文与失败：** [context/select.py](https://github.com/assafelovic/gpt-researcher/blob/3582a6841fe7dc801e2a34e34ee408641aea9bce/gpt_researcher/context/select.py)统一选择 keyword、embeddings、Jev 或不滤；Jev／embedding 路径出错时回退词项排序。[SourceCurator](https://github.com/assafelovic/gpt-researcher/blob/3582a6841fe7dc801e2a34e34ee408641aea9bce/gpt_researcher/skills/curator.py#L38)用模型整理来源并尝试恢复 JSON，非法非列表结果或异常回退原材料；[回归测试](https://github.com/assafelovic/gpt-researcher/blob/3582a6841fe7dc801e2a34e34ee408641aea9bce/tests/test_source_curator_json_parsing.py)覆盖围栏 JSON、普通 JSON 和非法结果。来源整理成功不是逐事实人工核源。
- **源码事实——评测：** [replay.py L115](https://github.com/assafelovic/gpt-researcher/blob/3582a6841fe7dc801e2a34e34ee408641aea9bce/evals/context_filter/replay.py#L115)在已保存资料上重建不同上下文策略，再生成报告，分开记录过滤／写作耗时、成本、context_chars、编码器计算的 context_tokens 与异常。这里的上下文 Token 计数不是 provider 实际输入用量，更不是运行前的金额硬上限。
- **源码事实——指标限制：** [metrics.py L68](https://github.com/assafelovic/gpt-researcher/blob/3582a6841fe7dc801e2a34e34ee408641aea9bce/evals/quality_eval/metrics.py#L68)的 citation_faithfulness 比较正文和参考列表中的域名集合；它衡量引用纪律，不证明每条主张正确。另有逐主张支持判断，但本次未执行评测或验证评分可靠性。
- **本项目推论：** 适合用冻结来源比较证据选择和上下文成本；应分别验证来源保留、引用对应与结论支持。回退保留材料有利于继续执行，也可能保留低质量资料，不能把“报告生成了”当成成功。

### smolagents：步骤记忆、执行状态与终止

- **源码事实——循环：** [agents.py L540](https://github.com/huggingface/smolagents/blob/96f33faaf028479119ec8d34507b47694cf14e34/src/smolagents/agents.py#L540)按步进行可选规划、动作、final_answer_checks、回调和记忆追加。生成错误直接抛出，其他 AgentError 放入步骤；达到步数上限仍可生成最终回答，但保留 AgentMaxStepsError。[步数耗尽测试](https://github.com/huggingface/smolagents/blob/96f33faaf028479119ec8d34507b47694cf14e34/tests/test_agents.py#L501)及[答案检查测试](https://github.com/huggingface/smolagents/blob/96f33faaf028479119ec8d34507b47694cf14e34/tests/test_agents.py#L664)体现这些语义。“有回答”和正常完成是不同状态。
- **源码事实——记忆归属：** [AgentMemory](https://github.com/huggingface/smolagents/blob/96f33faaf028479119ec8d34507b47694cf14e34/src/smolagents/memory.py#L214)保存系统提示及 task／action／planning 步骤，按顺序构造模型消息；[LocalPythonExecutor](https://github.com/huggingface/smolagents/blob/96f33faaf028479119ec8d34507b47694cf14e34/src/smolagents/local_python_executor.py#L1688)另有跨调用变量 state 和工具。源码明确其导入／内置函数限制不等于安全沙箱。
- **源码事实——评测：** [benchmark/run.py L125](https://github.com/huggingface/smolagents/blob/96f33faaf028479119ec8d34507b47694cf14e34/examples/smolagents_benchmark/run.py#L125)支持 code／tool-calling／vanilla 对照，记录问题、答案、来源、消息轨迹、时间和 Token 等；本次未运行数据集、核查评分 notebook 或证明哪种动作更优。
- **本项目推论：** 工具组合和变量复用带来表达能力，同时增加执行权限及隔离责任。选型场景已有足够机会展示循环与状态深度，无需为展示而引入代码执行器。

### browser-use：真实浏览器环境的失效与压缩

- **源码事实——核心调用链：** [agent/service.py L1036](https://github.com/browser-use/browser-use/blob/aa093a843da5edbf323c0b4145c9b6a0db3ecde8/browser_use/agent/service.py#L1036)获取浏览器状态／截图、按 URL 构造动作模型、加入上轮结果、处理压缩及预算／循环提示，然后调用模型、执行并在 finally 记录。[批量动作 L2755](https://github.com/browser-use/browser-use/blob/aa093a843da5edbf323c0b4145c9b6a0db3ecde8/browser_use/agent/service.py#L2755)结合动作终止标记与 URL／焦点 target 变化停止后续动作，保留已执行的部分结果。
- **源码事实——状态与记忆：** [AgentState](https://github.com/browser-use/browser-use/blob/aa093a843da5edbf323c0b4145c9b6a0db3ecde8/browser_use/agent/views.py#L251)保存步数、连续失败、计划、上次输出和消息状态；[消息压缩 L216](https://github.com/browser-use/browser-use/blob/aa093a843da5edbf323c0b4145c9b6a0db3ecde8/browser_use/agent/message_manager/service.py#L216)按步数／字符门槛触发，先过滤敏感值，失败保留旧状态，成功后保留摘要与近期历史。[摘要注入 L153](https://github.com/browser-use/browser-use/blob/aa093a843da5edbf323c0b4145c9b6a0db3ecde8/browser_use/agent/message_manager/service.py#L153)明确作为未验证上下文。
- **源码事实——测试与失败：** [压缩测试](https://github.com/browser-use/browser-use/blob/aa093a843da5edbf323c0b4145c9b6a0db3ecde8/tests/ci/test_message_compaction.py)、[实例状态隔离测试](https://github.com/browser-use/browser-use/blob/aa093a843da5edbf323c0b4145c9b6a0db3ecde8/tests/ci/test_message_manager_state_isolation.py)不等于摘要语义保真测试。[动作超时测试](https://github.com/browser-use/browser-use/blob/aa093a843da5edbf323c0b4145c9b6a0db3ecde8/tests/ci/test_action_timeout.py#L36)用挂起 handler 验证及时返回和错误结构；[工具超时实现](https://github.com/browser-use/browser-use/blob/aa093a843da5edbf323c0b4145c9b6a0db3ecde8/browser_use/tools/service.py#L2178)把超时转为动作错误，不证明外部动作没有发生。
- **源码事实——CI 解释边界：** [evaluate_tasks.py L61](https://github.com/browser-use/browser-use/blob/aa093a843da5edbf323c0b4145c9b6a0db3ecde8/tests/ci/evaluate_tasks.py#L61)在缺少所需密钥时跳过并返回 success:true；有密钥时[模型判定 L157](https://github.com/browser-use/browser-use/blob/aa093a843da5edbf323c0b4145c9b6a0db3ecde8/tests/ci/evaluate_tasks.py#L157)读取任务、最终输出及简要信息。本次没有核查该提交实际 CI 结果；不能把脚本成功、Agent 自报完成和外部事实验证混同。
- **本项目推论：** 浏览器状态变化、失效动作、压缩后的证据保持和失败恢复都可以在一个真实技术选型流程中验证。预算提示和事后累计不能直接借用为本项目的调用前硬额度。

### 当前本地事实与设计采用范围

[DEC-T01 验收](../tasks/DEC_T01_ACCEPTANCE_2026-10-23.md)及[任务表](../features/DECISION-001/tasks.md)已记录 fact ID／来源上下文及预算预检的一次压缩离线修复；因此，上文 ContextManager“模型投影未保留 fact ID”是 2026-10-22 的旧观察。后续 pilot 三题与人工核源状态见[交接记录](../tasks/EIGHT_MODULE_PREP_2026-10-22.md)，不再采用早期预检停线作为最新研究状态。最新代码或离线切片也没有解除 P-02／r12 No-Go。

用户已批准 [ADR-0007](../design/adr/0007-interactive-evidence-decision-sessions.md)中的方案 B，保留现有运行底座，以选型会话拥有意图／修订／报告历史，每轮有限任务承担执行和调用记录。本次仅同步文档，尚未实现会话、三类组件及组合比较。采用的是可核验机制与边界，而不是把上游测试成绩或 Star 计入本项目证据。

新选型场景中，工作上下文、持久执行记录和同会话证据引用分别处理；同会话复用不等于原有跨任务来源线索功能已完成。用户条件、事实来源、抓取时间、模型／地域适用范围、人工核源与实际调用支出均须保持可追溯。API 协议、执行上下文、预算、恢复和组合的精确定义仍由[现行契约](../contracts/CURRENT_CONTRACTS.md)管理。

本轮检查范围为只读源码／测试／官方 API 和文档核查；没有跑上游测试或复现公开指标。未知项包括本项目真实成功率、压缩质量、重复运行稳定性、语音候选在目标家庭环境中的效果以及招聘竞争力。新增对话／语音验收单列，原[正式协议](../evaluation/CURRENT_EVAL_PROTOCOL.json)保持不变；真实运行、费用及实施继续按对应授权和阶段证据推进。

## 2026-10-26 开发流程、记忆及优化证据补充

范围：本轮为优化后续推进提示词而做公开资料只读研究，只追加本节，不变更产品规格、契约、任务授权、冻结评测或业务代码。两名 researcher 分别独立调查真实 PR 流程与记忆评测适配；角色仅执行只读操作，但有效权限仍是共享 workspace-write，不宣称沙箱隔离。以下是源码／公开讨论观察与本项目方法建议，不是已实施目标或效果证据；没有运行上游测试、模型或 benchmark。

### 可核查的维护与优化流程

[smolagents 贡献指南](https://github.com/huggingface/smolagents/blob/96f33faaf028479119ec8d34507b47694cf14e34/CONTRIBUTING.md)要求非微小变更先有被维护者接受的问题，并要求 AI 辅助贡献的人读过改动、运行测试、解释正确性并回应审查。这里借鉴问题定义、范围和个人责任，不照搬外部 issue 审批到本项目。研究对象为有公开证据的维护者贡献流程，不据 GitHub 身份推定个人资历，也不概括所有公司的流程。

| 案例／固定提交 | 实际观察 | 可借鉴与限制 |
| --- | --- | --- |
| GPT Researcher [Issue #2144](https://github.com/assafelovic/gpt-researcher/issues/2144) → [PR #2145](https://github.com/assafelovic/gpt-researcher/pull/2145)，2026-09-26 合并，`816e893e34c6f63d782a60e858c309b4218404af` | 初始搜索发现来源、规划使用它，但后续 DNS／空搜索使来源未入抓取，writer 缺目标上下文。修复让规划来源继续走原抓取、内容校验、去重和压缩链，并保留后续搜索，不直接把预览当网页事实。[源码 L364–405](https://github.com/assafelovic/gpt-researcher/blob/816e893e34c6f63d782a60e858c309b4218404af/gpt_researcher/skills/researcher.py#L364)、[确定性回归](https://github.com/assafelovic/gpt-researcher/blob/816e893e34c6f63d782a60e858c309b4218404af/tests/test_planning_sources.py)。 | 从真实错误跨阶段定位，再做旧基线失败／修复通过的隔离复现与相邻回归。[维护者审查](https://github.com/assafelovic/gpt-researcher/pull/2145#pullrequestreview-5325729784)记录单独／组合测试及一次 live 对照；本轮未复跑，未取得足以计算稳定改善的完整结果；原问题还有机构歧义，不能宣称唯一根因。 |
| GPT Researcher [PR #2161](https://github.com/assafelovic/gpt-researcher/pull/2161)，2026-09-26 合并，`a5a56797465205f9a6d69b0bec2363bf59609839` | [实验说明](https://github.com/assafelovic/gpt-researcher/blob/a5a56797465205f9a6d69b0bec2363bf59609839/evals/context_filter/README.md)固定收集资料与 writer，比较过滤策略，含 none／truncate 简单对照；[replay L94–141](https://github.com/assafelovic/gpt-researcher/blob/a5a56797465205f9a6d69b0bec2363bf59609839/evals/context_filter/replay.py#L94)区分过滤／写作时间、费用、编码器上下文 Token 和异常；[judge](https://github.com/assafelovic/gpt-researcher/blob/a5a56797465205f9a6d69b0bec2363bf59609839/evals/context_filter/judge.py)交换成对报告顺序。 | 把上下文选用变成设计问题，按任务类型看质量／成本。小题量、单 writer／报告类型、裁判同模型家族、原网页报告未随结果提交，限制复现与外推；不引用为本项目收益，也不据此引入该服务。 |
| browser-use [PR #5401](https://github.com/browser-use/browser-use/pull/5401)，2026-08-06 合并，`32601887cfbc9f4f1e3cad3e2b678e56aeaeaae4` | 显式零阈值被 truthy fallback 覆盖，导致仅按步数触发压缩失效；[实现 L238–245](https://github.com/browser-use/browser-use/blob/32601887cfbc9f4f1e3cad3e2b678e56aeaeaae4/browser_use/agent/message_manager/service.py#L238)区分 None 和 0，[回归测试](https://github.com/browser-use/browser-use/blob/32601887cfbc9f4f1e3cad3e2b678e56aeaeaae4/tests/ci/test_message_compaction.py)验证按步触发、模型调用及摘要保存。 | 控制逻辑正确不证明摘要语义正确；还要分别检验硬条件、证据、冲突、时间和未完成状态保留，再看最终任务结果。未运行测试。 |

### 记忆与 benchmark 的适配和陷阱

LangGraph 固定 `3cd57c038ad827d05f80c6488adea9994156c58c`：[Checkpoint](https://github.com/langchain-ai/langgraph/blob/3cd57c038ad827d05f80c6488adea9994156c58c/libs/checkpoint/langgraph/checkpoint/base/__init__.py#L105)保存 channel values／versions／pending writes 等执行材料；[Store](https://github.com/langchain-ai/langgraph/blob/3cd57c038ad827d05f80c6488adea9994156c58c/libs/checkpoint/langgraph/store/base/__init__.py#L578)是 namespace／key 数据及可选索引。两者不是同一个记忆对象。[TTLConfig L542](https://github.com/langchain-ai/langgraph/blob/3cd57c038ad827d05f80c6488adea9994156c58c/libs/checkpoint/langgraph/store/base/__init__.py#L542)默认 refresh_on_read=true、omit_expired=false；[namespace 测试 L357](https://github.com/langchain-ai/langgraph/blob/3cd57c038ad827d05f80c6488adea9994156c58c/libs/checkpoint-postgres/tests/test_store.py#L357)及[到期／刷新测试 L1020](https://github.com/langchain-ai/langgraph/blob/3cd57c038ad827d05f80c6488adea9994156c58c/libs/checkpoint-postgres/tests/test_store.py#L1020)表明应用仍需控制检索边界和过期策略。本项目推论：存储 TTL 不等于来源证据新鲜度，namespace 不等于 owner 授权，读取旧记录不能伪装成新观测；本条API事实不构成选型理由；当前LangGraph由本人委托后明确采用，见ADR8。

[LongMemEval 固定 README](https://github.com/xiaowu0162/LongMemEval/blob/9e0b455f4ef0e2ab8f2e582289761153549043fc/README.md)，commit `9e0b455f4ef0e2ab8f2e582289761153549043fc`（2026-05-11），及[原论文 v2](https://arxiv.org/abs/2410.10813v2)面向长期对话的信息抽取、跨 session、知识更新、时间推理和弃答；原版 500 题，检索和回答分开评测，不直接测本项目官方取证、选型或实时网页研究。README 已指向 V2，本轮未审阅 V2，不声称覆盖最新研究。

[evaluate_qa.py](https://github.com/xiaowu0162/LongMemEval/blob/9e0b455f4ef0e2ab8f2e582289761153549043fc/src/evaluation/evaluate_qa.py)按提交 hypotheses 循环，未知 ID 跳过，均值来自实际评分记录；没有替使用者核对所有参考 ID 是否覆盖，也不拒绝重复。默认裁判使用 gpt-4o 别名映射的具体版本并逐题调用，仍有费用。[检索脚本](https://github.com/xiaowu0162/LongMemEval/blob/9e0b455f4ef0e2ab8f2e582289761153549043fc/src/evaluation/print_retrieval_metrics.py)排除 _abs；[eval_utils.py](https://github.com/xiaowu0162/LongMemEval/blob/9e0b455f4ef0e2ab8f2e582289761153549043fc/src/retrieval/eval_utils.py)的 recall_all@k 表示全部所需证据是否齐全，而非一般命中条数比例。本项目需独立冻结题目／尝试台账和指标公式，缺失／失败／取消／超时不能静默消失。子集只称已声明子集；金标和证据位置不能注入被测 Agent。未下载／核定实际数据修订，未运行裁判，不承诺费用或数据无噪声。

### 对后续提示词的建议（不是新产品授权）

Anthropic 的[上下文工程](https://www.anthropic.com/research/effective-context-engineering-for-ai-agents)（2025-09-29）讨论有界信息选择、按需加载与压缩损失；[评测工程](https://www.anthropic.com/research/demystifying-evals-for-ai-agents)（2026-01-09）区分任务／尝试、轨迹／最终结果、能力／回归及人工校准；[工具工程](https://www.anthropic.com/research/writing-tools-for-agents)（2025-09-11）从工具结果、错误和调用效率迭代。它们是团队公开经验，不是招聘统一要求，不能据此承诺项目效果。

本地 [ContextManager](../../backend/src/adaptive_research/agent/context_manager.py)当前有确定性裁剪、最近事实／来源及失败线索，[测试](../../backend/tests/unit/test_context_manager.py)覆盖界限和保留行为；[P-02 失败诊断](../audits/P02_PILOT_R11_FAILURE_TRIAGE_2026-10-23.md)区分无进展、取证缺口和请求前预算拒绝，修复仍只有离线证据。因此后续应做针对性实验，不把“最近窗口”自动写成最优上下文策略，也不把数据库持久化当完整记忆系统。

重点深度应围绕：条件／证据记忆生命周期、相关上下文选用及事实支持，贯通工具、执行恢复、调用成本和评测。每项优化保留用户问题／原始症状、第一处可观察偏差、替代解释、可证伪预测、简单基线、固定资料对照、原可用场景回归、经授权真实复查、独立审查及采用／放弃决定。本人先给出判断或预测，再由 AI 帮助验证，保留被推翻的假设与亲手改动，不能事后编写独立贡献。

本节原九题/框架候选等已由2026-10-29配置替换，真实历史No-Go不变；方法研究不等业务验收，实际实施/付费另授。

## PREP-BASELINE-v4.3：OpenCode / DeepSeek 与记忆上下文的定点研究

资料观察日 **2026-10-26**，2026-10-27同步。本节回应负责人深入研究OpenCode Token方案的要求；版本固定，未运行上游、未复现作者测试/成绩。上文8–12周/校招/语音固定分类保留历史；当前M1目标/实习适配以SPEC/ADR8为准。Star仅关注度信号，选择项目是因为具体问题相关；源码事实、作者观点、本项目推论与待验证假设分别标注。

### OpenCode：调用链与Token事实

固定 [anomalyco/opencode ed74ec82ce1fe3a36da6c0815a935473ef4bb0fb](https://github.com/anomalyco/opencode/tree/ed74ec82ce1fe3a36da6c0815a935473ef4bb0fb)，dev观察根版本2.1.4。V2路径为 packages/core 与 packages/ai，不能套用旧V1 session/processor源码。

| 具体源码/测试（均为固定commit） | 源码事实 | 本项目取舍/待验证 |
| --- | --- | --- |
| [session/context.ts](https://github.com/anomalyco/opencode/blob/ed74ec82ce1fe3a36da6c0815a935473ef4bb0fb/packages/core/src/session/context.ts)、[util/token.ts](https://github.com/anomalyco/opencode/blob/ed74ec82ce1fe3a36da6c0815a935473ef4bb0fb/packages/core/src/util/token.ts) | 估算round(JS string.length/4)，在模型窗口/输出额度/累计消息上计算room；给估算留ceil(×1.15)等buffer，最小输出1024，模型元数据缺失存在fallback。不是精确tokenizer。 | 中文/JSON/schema/工具描述分布不同，不能复制chars/4或15%为40000累计/人民币硬保证。参考其把完整请求与输出容量统一考虑，保留provider实报锚点。 |
| [session/model-request.ts](https://github.com/anomalyco/opencode/blob/ed74ec82ce1fe3a36da6c0815a935473ef4bb0fb/packages/core/src/session/model-request.ts)、[runner/llm.ts](https://github.com/anomalyco/opencode/blob/ed74ec82ce1fe3a36da6c0815a935473ef4bb0fb/packages/core/src/session/runner/llm.ts)、[runner/step.ts](https://github.com/anomalyco/opencode/blob/ed74ec82ce1fe3a36da6c0815a935473ef4bb0fb/packages/core/src/session/runner/step.ts) | 编译消息、system/tool schema/模型设置→provider流→持久步骤/usage→下一轮；输入预算关联完整模型请求。最近provider响应usage锚定同provider/model历史，再估算新增delta。新输入需重新prepare，不能偷插旧step。 | 我们冻结完整编译输入/模板/工件以重建哈希；不能以工具输出字符数代替最终请求。条件revision必须显式，重新编译保护集合。 |
| [session/compaction.ts](https://github.com/anomalyco/opencode/blob/ed74ec82ce1fe3a36da6c0815a935473ef4bb0fb/packages/core/src/session/compaction.ts) | 分级损失旧内容：先保留整份、再旧tool输出首尾2000、再去输出/裁输入、再只保留用户2000、最后省略最旧；尽量保留最新。摘要过大存在85/70/50/35%目标的进一步尝试，可能增加调用。 | 首尾/新近不等于语义反证保护。我们的C2先完整eligible索引保护支持/反证/限定语，最低证据不够则分批/partial，不同时引入后台摘要让效果不可归因。 |
| [runner/retry.ts](https://github.com/anomalyco/opencode/blob/ed74ec82ce1fe3a36da6c0815a935473ef4bb0fb/packages/core/src/session/runner/retry.ts)、[session-runner.test.ts](https://github.com/anomalyco/opencode/blob/ed74ec82ce1fe3a36da6c0815a935473ef4bb0fb/packages/core/test/session-runner.test.ts) | context overflow仅在尚无输出/工具副作用等允许边界走压缩恢复，次数有界；再次overflow、关闭auto或已持久输出不能任意继续。 | 不把“有重试”当安全；外部结果unknown停线，最终决策阶段禁technical retry/repair。压缩后的调用仍是新物理请求和费用。 |
| [providers/deepseek.ts](https://github.com/anomalyco/opencode/blob/ed74ec82ce1fe3a36da6c0815a935473ef4bb0fb/packages/ai/src/providers/deepseek.ts)、[openai-chat.ts](https://github.com/anomalyco/opencode/blob/ed74ec82ce1fe3a36da6c0815a935473ef4bb0fb/packages/ai/src/protocols/openai-chat.ts)、[session/usage.ts](https://github.com/anomalyco/opencode/blob/ed74ec82ce1fe3a36da6c0815a935473ef4bb0fb/packages/core/src/session/usage.ts) | 有DeepSeek原生适配：Bearer/OpenAI Chat兼容、api.deepseek.com/v1、max_tokens；usage映射缓存命中等，reasoning为输出子项需防重复累计。部分缺失/非法usage或价格路径可归0。 | “也接DeepSeek”不等于token完全相同，更不等于本项目可靠。未知价格/usage不能复制归0逻辑；我们保留null/预留/停线，实际cache hit/miss计算费用。 |
| [session-compaction.test.ts](https://github.com/anomalyco/opencode/blob/ed74ec82ce1fe3a36da6c0815a935473ef4bb0fb/packages/core/test/session-compaction.test.ts)、[session-model-request.test.ts](https://github.com/anomalyco/opencode/blob/ed74ec82ce1fe3a36da6c0815a935473ef4bb0fb/packages/core/test/session-model-request.test.ts)、[specs/v2/session.md](https://github.com/anomalyco/opencode/blob/ed74ec82ce1fe3a36da6c0815a935473ef4bb0fb/specs/v2/session.md) | 工程测试覆盖预算/编译/压缩和步骤持久边界；原历史与投影/摘要有不同归属。 | 其测试存在不是本项目对中文技术决策、反证保持或恢复资金安全的证据；本项目仍需离线＋真实跨任务对照。 |

### OpenCode维护/修复讨论，按观察日状态而非宣传采信

| PR/Issue及状态（2026-10-26） | 背景、参与证据和限制 | 迁移判断 |
| --- | --- | --- |
| [PR58015](https://github.com/anomalyco/opencode/pull/58015)，merged ac68d6a929bcc0b107b37f0d0c01b659f0160903，10-22 | 老历史分级丢失修复。机器人报告262测试是PR证据，不是本次执行；不能给机器人或作者虚构资历。 | 用真实失败理解裁剪层级，不视为语义反证问题已解决。 |
| [PR58313](https://github.com/anomalyco/opencode/pull/58313)，merged33726e8fc190a8c634a186c3f9eed530e806e1e3，10-23 | buffer≥context等非法配置可导致总压缩，修正边界行为。 | 运行配置必须失败可见/资格验证，buffer不能随意增大就声称安全。 |
| [PR57444](https://github.com/anomalyco/opencode/pull/57444)，merged6a5973d2636936317de15726ab37e3681f678be3，10-22 | experimental后台摘要默认off；作者/合并者neriousy有MEMBER关联，能说明维护参与，不能据此认定高级工程师。作者测试不是我们复测。 | 后台摘要即使未用也可能花费、内存缓存重启会丢；M1不采用，避免无收益调用/恢复歧义。 |
| [PR58492](https://github.com/anomalyco/opencode/pull/58492)，open/unmerged | 讨论阈值/输出限额反转、不同input limit和buffer覆盖；普通评论者不自动是维护者。 | 候选补丁/观点，不得写已修复或默认行为。 |
| [PR56845](https://github.com/anomalyco/opencode/pull/56845)、[PR51767](https://github.com/anomalyco/opencode/pull/51767)，open/unmerged | 前者早期后台摘要提议，后者overflow原因处理；与后来合并方案不等同。 | 不用未合并提议证明当前可用。 |
| [Issue42363](https://github.com/anomalyco/opencode/issues/42363)，closed | 用户报告V1.18.15的DeepSeek reasoning/tool-history循环；成员thdxr按V1退役关闭并要求V2复报。两个用户复现不证明我们根因。 | 关闭不是技术修复证据；不能宣称V2解决同问题或我们已复现。 |

### DeepSeek官方Tokenizer、缓存与价格的资格设计

[官方Token说明](https://api-docs.deepseek.com/zh-cn/quick_start/token_usage/)的英文/中文字符换算只是估算，实际usage才是线上结果。[KV cache](https://api-docs.deepseek.com/guides/kv_cache/)按前缀、best-effort工作，不能从字符减少推出费用降低；须记录实际hit/miss和新增调用。[官方价格](https://api-docs.deepseek.com/zh-cn/quick_start/pricing/)在观察时列deepseek-flash/V4.1 Flash1017的人民币缓存命中0.04、未命中2、输出8元/百万Token及分时价格，模型别名/时段/单价可能变化。此处是观察快照，运行前≤24h重新固定计价并核对实际模型，不能当当前到账或运行授权；额外Search/Fetch不自动等于本项目工具成本。

固定官方 [deepseek-ai/DeepSeek-recipe 935817c66f5d6e64838f419692545f06787e485f](https://github.com/deepseek-ai/DeepSeek-recipe/tree/935817c66f5d6e64838f419692545f06787e485f)，0.2.0；具体读 [docs/tokenizer.md](https://github.com/deepseek-ai/DeepSeek-recipe/blob/935817c66f5d6e64838f419692545f06787e485f/docs/tokenizer.md)、[Rust tokenizer](https://github.com/deepseek-ai/DeepSeek-recipe/blob/935817c66f5d6e64838f419692545f06787e485f/deepseek-recipe-encoding/src/tokenizer.rs)和README/Python tests/test_bindings.py。源码将模板特殊token范围与用户字面文本区分；应使用完整匹配模型的prompt template和tokenizer，不仅对拼接正文encode。

[Issue5](https://github.com/deepseek-ai/DeepSeek-recipe/issues/5)报告0.1.1特殊字面token计数差异；协作者zhu-he称0.2.0修复，对应发布commit93b0fd229cc9ffa6b1a8c63d42b0bf741bbec170；当前固定提交更后，不把旧问题当当前缺陷。[0.2.0发行文件](https://pypi.org/project/deepseek-recipe/0.2.0/#files)观察有Linux/mac wheels、无Windows wheel；Python≥3.10，Maturin/Rust源码构建还涉及OpenCV4/Clang。当前Windows Py3.12不能据Python版本便宣称可装；本轮未安装、不自动源码构建或迁移Worker。

**2026-10-29采用裁决**：官方Tokenizer正式硬准入，中文/英文/代码/JSON/schema/tools/字面及控制token和完整模型模板都纳资格。缺失/失败/不支持字段/漂移停发；首次有限诊断单独另授、不循环前置。旧影子方案退出当前默认。安装、Tokenizer执行、模型诊断未授权或未验证，公开模型/模板实际匹配仍待验。

r11 B02已用24467、剩15533、报告预检界15576（差-43）；B03已用31877、剩8123、界15171（差-7048）。这些是历史本地预检证据，**没有完整raw prompt**可精确复算，不能声称官方tokenizer必能修复。B03还缺发布日期/两项变化并有检索时间语义问题，Token不是唯一质量根因。见[P02原诊断](../audits/P02_PILOT_R11_FAILURE_TRIAGE_2026-10-23.md)。

### 其他定点参照：状态、记忆、证据保持及维护反馈

| 固定版本/关键位置 | 事实/作者观点/未运行限制 | 本项目迁移边界 |
| --- | --- | --- |
| [GPT Researcher 3582a684](https://github.com/assafelovic/gpt-researcher/tree/3582a6841fe7dc801e2a34e34ee408641aea9bce)，research conductor/source curator；[PR2145](https://github.com/assafelovic/gpt-researcher/pull/2145) merged816e893e34c6f63d782a60e858c309b4218404af | 初始规划来源在后续失败后丢失；维护者assafelovic参与评审，作者14离线测试/真实比较是作者证据；[PR2161](https://github.com/assafelovic/gpt-researcher/pull/2161)相关context改动a5a56797465205f9a6d69b0bec2363bf59609839 | 来源事实与投影/后续调用失败分开；不能用报告引用域名集合证明逐主张支持，原证据不可随失败丢弃。 |
| [DeepAgents bb6d4316](https://github.com/langchain-ai/deepagents/tree/bb6d4316eb59b368b862e5517b888e5e70b1c3ae)，libs/deepagents/deepagents/middleware/summarization.py、backends/store.py、tests/unit_tests/middleware/test_compaction_recovery.py | 完整system/tool容量、overflow一次更小恢复；archive写失败存在无archive继续路径。[PR6267](https://github.com/langchain-ai/deepagents/pull/6267)维护者MikeMerrill评审/JohnKennedy合并、121tests是作者证据 | 可借鉴严格缩小/有界恢复，不照搬无法持久原证据仍继续。本项目Pg原证据和call ledger先提交，恢复不重复物理请求。 |
| DeepAgents [PR6779](https://github.com/langchain-ai/deepagents/pull/6779) closed/unmerged，[Issue6470](https://github.com/langchain-ai/deepagents/issues/6470) open；[OpenSWE PR2678](https://github.com/langchain-ai/open-swe/pull/2678) closed/unmerged | 前者namespace精确过滤提议未合并，后者空content/超长单行摘要边界为用户报告；OpenSWE评审提问不是已接受修复 | namespace默认值不是鉴权；未合并补丁/单个边界不能写所有用户受影响或已解决。 |
| [Letta Code b849473f](https://github.com/letta-ai/letta-code/tree/b849473fe69bc9b6813b31449f1161104beca8e9)，package0.32.3；src/agent/prompts/letta.md、memory-filesystem.ts、memory-constraints.ts、system-prompt-versioning.ts、memory-git.precommit.test.ts、memory-constraints-audit.test.ts | 文件记忆、提交/重编译后影响后续prompt，检查staged而非dirty，audit HEAD；默认单文件20kchars是约束非质量证明。memory-prompt.integration.test.ts需API key可skip。旧Python Letta主分支已提示retired，不能混成当前实现。 | 学习可审计变更/版本与编译边界，不将其自治记忆Git/程序规则直接移植。条件仍本人接受，自动来源线索及明确长期技术偏好提供可见建议，应用表控lineage/rev/owner/撤销/过期，不自治改程序策略。 |
| [LangGraph 3cd57c03](https://github.com/langchain-ai/langgraph/tree/3cd57c038ad827d05f80c6488adea9994156c58c) Store TTL配置 | refresh_on_read默认true、omit_expired存在默认边界；namespace/TTL API本身不是用户隔离/撤销策略 | 来源线索7天/偏好30天，读不续，过期/撤销先于读取和最终发送；checkpoint只引用不替事实资金。 |
| [browser-use PR5401](https://github.com/browser-use/browser-use/pull/5401)，merged32601887cfbc9f4f1e3cad3e2b678e56aeaeaae4；[smolagents固定版](https://github.com/huggingface/smolagents/tree/96f33faaf028479119ec8d34507b47694cf14e34) | 0与None预算边界修复；ActionStep/计划步骤结构化记忆分别有代码，不自动拥有owner生命周期 | 空/零/未知不可混用；日志/ActionStep不等于产品来源记忆。 |

这些项目按问题分批选择：OpenCode回答完整请求/压缩/DeepSeek，DeepSeek recipe回答token资格，GPT Researcher回答来源丢失，DeepAgents回答溢出/存储边界，Letta回答记忆变更编译，LangGraph回答恢复归属。不会继续无界收集项目。当前采用LangGraph真实阶段图、Pg应用权威、确定性关系投影和单供应商；旧AgentLoop只按历史保留，不另开新功能线。首版验证/对照见[补充协议](../evaluation/DECISION_M1_PROTOCOL.json)和[测试策略](../testing/STRATEGY.md)；本研究不授权安装、真实运行、费用或Git写。
