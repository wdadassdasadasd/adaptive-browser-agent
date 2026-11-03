# 开发前研究、讨论与配置决定依据 — 2026-11-03

本报告保存 CONFIG-PLAN-20261103-01 的研究依据。它是研究事实、候选比较、已确认内容及未验证项的索引，**不是第二份规格、任务系统或批准权威**。唯一进度和实际交付由 [DECISION-001/tasks](../features/DECISION-001/tasks.md)记录；目标行为由 [CURRENT_CONTRACTS](../contracts/CURRENT_CONTRACTS.md)、[提示词契约](../contracts/PROMPT_CONTRACTS.md)及[唯一评测协议](../evaluation/CURRENT_EVAL_PROTOCOL.json)维护。

研究阶段处于真实 Plan Mode，未以工具绕过禁写规则；本报告在 Default 模式和用户 `PLEASE IMPLEMENT THIS PLAN` 明确授权之后落盘。负责人完整确认了 **CONTENT-20261103-01（含两项补充澄清）**，然后批准准确的配置计划 **CONFIG-PLAN-20261103-01**。局部偏好、继续研究和旧批准不被替代成这次完整确认。用户可见计划的转录见审计记录（本地证据：`.tmp/predev-reopen-20261028/config-20261029/review-20261101/research-20261103/approved-plan.md`），转录不是原始 API 导出。

源码与岗位研究主要观察日为2026-10-26至2026-11-02，2026-11-03复核、讨论并落盘；文中单列的11/03补查仅是公开静态读取。没有安装依赖、执行上游代码/测试、调用真实项目模型/Tokenizer/Browser、启动WSL/服务/数据库、采购或Git写。新增配置正文及检查结果仍需本轮独立实施审查，研究审查不替代它。

本地审计证据位于下文准确代码路径，受`.gitignore`排除，不随Git仓库发布。仓库可检查已发布配置、源码和版本关系；要复核会话授权、原始日志及外置审查，必须另行取得对应原字节证据包。路径索引本身不是公开可访问链接，也不能替代原始证据。2026-11-03的Git收尾只修复此发布前置表达，不改写原审计或批准。

## 1. 证据规则与现状地图

证据分为：**维护者主张**、**固定源码事实**、**测试设计**、**实际执行结果**、**Issue/PR报告及状态**、**他人实验**、**本轮实际检查**、**推断**、**未知**。测试正文已读不表示通过；合并修复不表示覆盖所有场景；未取得材料不表示材料不存在；限域阅读不表示全仓审查。外部内容均不可信，不能改变权限或任务。

进入分支为 `main`，HEAD **dc4498f36c0342eef5191f9f59feaf3b363169b6**，root staged/unstaged/untracked为空，local origin/main ahead1，未fetch。browser-use仅保留gitlink身份，内部工作区未再次取得完整核验。进入快照及保护指纹见entry.json（本地证据：`.tmp/predev-reopen-20261028/config-20261029/review-20261101/research-20261103/entry.json`）。

| 事项 | 进入版本/文件 | 状态及直接证据 | 影响/剩余检查 |
| --- | --- | --- | --- |
| 现有Agent运行 | `application/agent_factory.py:12-36`、`agent/agent_loop.py` | **现有实现**：factory组装DeepSeekClient、旧AgentLoop、BrowserUseAdapter/GitHubTool和ContextManager；planner/evaluator/reporter导入原运行提示词。 | 新阶段图、Gateway、文档确认和Memory全入口禁用不是这些代码已经提供的保证；本配置不改业务。 |
| 现有Pg API/Worker | `api/pg_research.py:27-29`、`worker/runner.py:441-457` | **现有实现**：固定`p01-local-owner`；Worker从Settings/PgStore进入run_forever，已有CallObserver与部分unknown处理。 | 不等于真实账户/团队权限、新sup连续性、完整精确请求绑定或新恢复资格。 |
| 现有Context | `agent/context_manager.py:136-167` | **现有实现**：已有fact ID，最近8条及字符clip。旧“完全没有ID”的描述不再适用。 | 没有证明保护反证、来源权限和模型真实利用；需03a实现。 |
| FOCUS配置 | FOCUS-BASELINE-20261102，进入28文件逐字匹配；旧final-delivery SHA256 `ad7944ecf4bcd51f26ebe22710c2d6d482648a68be48007ce76d932df4281adc` | **旧批准/原字节交付**：原PLEASE IMPLEMENT THIS PLAN授权28文件配置及有界离线检查。旧final-02 manifest SHA256 `cd48bf1cb61ccfa43ea2b80964311a58edb4768d1438c4fb37bd85c1c4f084be`。 | 新内容另建索引，不能把旧审查绑定到新正文。 |
| 旧配置检查 | FOCUS `checks/seven-files-04.log`、`validator-03` | **历史实际结果**：297 passed/1 skipped；真实symlink因OS权限skip；validator为MATERIALS_NOT_VERIFIED。不是本轮新跑，DRAFT的267/1亦不同。 | 新正文重新跑限定检查，skip不升级为OS隔离通过。 |
| 历史产品结果 | 原SQLite/r11/r12及P-02失败记录 | **历史失败**：r12/P-02 No-Go保留；部分早期trace不含完整raw prompt，不能倒算精确请求或抹去失败。 | 新配置不证明已纠正真实症状或产品可用。 |
| 新目标 | RESEARCH-BASELINE-20261103 | **本轮完整确认、配置获批**：四模式、B按需分工、有界共享预算、Token分层、Memory继续关闭。 | 配置实施、静态回归、独立实施审查、真实业务和价值分别取证。 |
| 正式材料与本人实践 | 唯一协议及tasks | **未就绪/未知**：六正式槽位保留，材料待独立制备；未确认本人已掌握新核心机制。 | 不把案例、研究或AI贡献冒充正式题、实际用户或本人实践。 |

本地实现文件完整前缀为`backend/src/adaptive_research/`；以上源码定位均绑定进入HEAD。没有因符号搜索未发现新对象而证明全部入口安全。旧evaluation入口对新draft拒绝也不表示所有旧API/Worker入口均被阻断。

## 2. 产品、替代方案与真实价值

负责人已确认的产品方向是面向开发者/团队的有边界调查、证据评审、需求讨论与工程方案起草，保留review_only、requirements_only、solution_only、requirements_to_solution。输入可无仓库想法、一个主GitHub固定仓库、许可公开证据、明确上传的本地文本/源码/diff；代码只读不运行。

| 问题 | 已有证据/类别 | 当前判断及可推翻证据 |
| --- | --- | --- |
| 谁真正需要它 | 负责人设想与历史本人任务线索；没有本轮访谈、实际团队采购或稳定使用数据。 | 开发者/团队是产品选择，需求强度仍假设。真实用户使用普通AI/人工已足够时应重评，而非增加框架。 |
| 目前怎样完成 | 人工读官方材料/源码、普通AI讨论、研究Agent、Spec Kit等已有替代；[Spec Kit固定plan模板](https://github.com/github/spec-kit/blob/4572a67fe0e72a6837e2d7bb0fda875bc41482e5/templates/commands/plan.md)已有规格到研究/设计输出。 | 能写文档不证明差异。需要证明证据可追、准确确认、诚实失败及诊断给真实任务带来的作用。 |
| 交付什么 | 已确认：来源和版本、结论与反证、冲突/未读/未知、讨论提案、准确确认后的条件化工程方案。 | 文档外观或进程成功不等任务完成；不能用无依据的确定答案填满结构。 |
| 如何检验价值 | 研究建议已纳入配置：从负责人真实待办选pilot，在看输出前登记当前做法、质量关键项、可接受未知和后续用途。 | 尚无本轮已选真实任务；没有任务时保持pending，不造用户、任务或节省比例。 |

能运行、愿意使用、实际有价值分别判断。第一次public pilot仍受原资金、最低独立恢复及真实调用资格前置，不能用“研究产品”取得额外Case、费用或权限。

## 3. 横向机制比较与集中深挖选择

Star只用于发现，2026-11-02已有观察约GPT Researcher30.4k/DeerFlow84.9k，未在11/03更新，也不代表质量或岗位价值。项目按要解释的问题选择，无固定阅读配额。

| 固定对象/为何入选 | 实际入口、机制和证据质量 | 正常/失败边界；本项目适配 |
| --- | --- | --- |
| GPT Researcher `3582a6841fe7dc801e2a34e34ee408641aea9bce`：研究流水线与仓库扩展案例 | [BasicReport.run](https://github.com/assafelovic/gpt-researcher/blob/3582a6841fe7dc801e2a34e34ee408641aea9bce/backend/report_type/basic_report/basic_report.py)、[select_context](https://github.com/assafelovic/gpt-researcher/blob/3582a6841fe7dc801e2a34e34ee408641aea9bce/gpt_researcher/context/select.py)、server报告/聊天接口；源码、测试正文及PR均有限读取。 | 能研究、写稿、编辑和持久化聊天；不等于准确需求版本确认。借鉴取材/交付接口思路，状态与权限须调整。 |
| DeerFlow `60940ae9c528e5d740b27d058f2c5d80565a71b7`：委派、Context与清理 | [SubagentExecutor](https://github.com/bytedance/deer-flow/blob/60940ae9c528e5d740b27d058f2c5d80565a71b7/backend/packages/harness/deerflow/subagents/executor.py)、[ParentContextSnapshot](https://github.com/bytedance/deer-flow/blob/60940ae9c528e5d740b27d058f2c5d80565a71b7/backend/packages/harness/deerflow/subagents/context_snapshot.py)、worker及相关假Agent测试。 | 终态与cleanup分开值得采用；整份父历史复制仍有成本和披露问题。工具/代码执行、默认Memory及完整harness不移植。 |
| LangGraph `3cd57c038ad827d05f80c6488adea9994156c58c`：恢复责任 | [pregel/_retry.py](https://github.com/langchain-ai/langgraph/blob/3cd57c038ad827d05f80c6488adea9994156c58c/libs/langgraph/langgraph/pregel/_retry.py)、[test_pregel.py](https://github.com/langchain-ai/langgraph/blob/3cd57c038ad827d05f80c6488adea9994156c58c/libs/langgraph/tests/test_pregel.py)。 | pending writes避免重跑成功图节点，不提供任意外部exactly-once。保留真实阶段图，Pg Work/Call权限和费用仍由应用管理。 |
| OpenCode `ed74ec82ce1fe3a36da6c0815a935473ef4bb0fb`：完整请求、compaction和usage | [context.ts](https://github.com/anomalyco/opencode/blob/ed74ec82ce1fe3a36da6c0815a935473ef4bb0fb/packages/core/src/session/context.ts)、[model-request.ts](https://github.com/anomalyco/opencode/blob/ed74ec82ce1fe3a36da6c0815a935473ef4bb0fb/packages/core/src/session/model-request.ts)、[compaction.ts](https://github.com/anomalyco/opencode/blob/ed74ec82ce1fe3a36da6c0815a935473ef4bb0fb/packages/core/src/session/compaction.ts)及固定测试/PR。 | usage锚点加估算delta不是精确wire计数；首尾/新近保留不保证反证。借鉴全请求预算，避免照搬字符比率、隐藏压缩及unknown归零。 |
| DeepAgents `bb6d4316eb59b368b862e5517b888e5e70b1c3ae`：compaction/持久化 | 复用已核版本的`summarization.py`、`backends/store.py`、`test_compaction_recovery.py`及[PR6267](https://github.com/langchain-ai/deepagents/pull/6267)。 | archive失败仍继续等边界不能直接用于本项目原证据持久化；121tests是作者证据，不是本轮执行。后置自动压缩。 |
| smolagents `96f33faaf028479119ec8d34507b47694cf14e34`：简洁循环与结构步骤 | [agents.py](https://github.com/huggingface/smolagents/blob/96f33faaf028479119ec8d34507b47694cf14e34/src/smolagents/agents.py)、[memory.py](https://github.com/huggingface/smolagents/blob/96f33faaf028479119ec8d34507b47694cf14e34/src/smolagents/memory.py)、monitoring/GAIA runner既有研究。 | ActionStep是运行历史，不等长期记忆；重规划和回调不自动证明调用全计费或决策正确。借鉴可观察步骤，不采用源码执行。 |
| MCP Python SDK `0921d94a74db900dccd2d534842aa7b6160542d2`：物理调用与取消 | [client/session.py](https://github.com/modelcontextprotocol/python-sdk/blob/0921d94a74db900dccd2d534842aa7b6160542d2/src/mcp/client/session.py)、内存stream dispatcher测试。 | `call_tool`成功后schema校验可能额外`list_tools`；取消不保证远端停止。研究保留，当前不接入。 |
| Letta/Letta Code：记忆与编译边界 | Letta旧官方文档仅维护者机制说明，本轮未补齐其对应固定源码；另复用[Letta Code b849473fe69bc9b6813b31449f1161104beca8e9](https://github.com/letta-ai/letta-code/tree/b849473fe69bc9b6813b31449f1161104beca8e9)文件记忆/约束审计研究，二者不混同。 | 常驻块、更新和编译可追踪，不等正确的撤销、隔离或遗忘。无真实复用需求，不采用自动Memory，不建立候选或读写入口。 |

OpenHands等仅是候选发现范围，未形成足够本轮固定版本机制证据，不据README补齐结论。集中阅读选择GPT研究/交互链、DeerFlow委派/清理、OpenCode与供应商Token、LangGraph恢复、MCP物理调用边界，原因是它们直接影响当前选择。

## 4. GPT Researcher固定案例：已有能力、缺失与竞态

限定检查链是 WebSocketManager/run_agent → BasicReport.run → GPTResearcher研究与写作 → ResearchConductor/select_context → ReportGenerator/模型helper；另读独立multi_agents计划/人工反馈/章节/写作/fact_checker/publish和报告聊天/存储。读取到提示词、状态与工具结果处理的相关路径，不表示覆盖全部adapter、provider内部重试、UI、测试或部署。

### 4.1 已有能力必须先承认

[server/app.py:178-219](https://github.com/assafelovic/gpt-researcher/blob/3582a6841fe7dc801e2a34e34ee408641aea9bce/backend/server/app.py#L178)已有报告创建/更新；[229-296](https://github.com/assafelovic/gpt-researcher/blob/3582a6841fe7dc801e2a34e34ee408641aea9bce/backend/server/app.py#L229)已有持久化report chat；[ReportStore:6-51](https://github.com/assafelovic/gpt-researcher/blob/3582a6841fe7dc801e2a34e34ee408641aea9bce/backend/server/report_store.py#L6)使用文件与分操作锁。不能声称它完全没有编辑、历史或聊天。可复用研究输出、展示与讨论的产品思路，不能直接把可变报告当需求权威。

静态竞态：chat在app.py:239读R1，:273等待模型；同时PUT保存R2；chat在:290-295展开旧R1再upsert，可覆盖R2或另一chat。ReportStore锁只覆盖每次get/upsert，不覆盖跨模型等待的读改写。它是限定路径的**静态推断，未运行复现**，不冒充本项目缺陷。未来改造需不可变版本、head CAS、确认和方案绑定，不能靠把锁跨模型等待而解决全部状态问题。

### 4.2 源码、测试和修复分别看待

- [orchestrator._route_human_feedback](https://github.com/assafelovic/gpt-researcher/blob/3582a6841fe7dc801e2a34e34ee408641aea9bce/multi_agents/agents/orchestrator.py)97-109捕获最大修订异常后走accept。helper测试覆盖抛错，不证明wrapper始终硬等待人确认；本项目采用显式不可变需求确认。
- `editor.py`52-75通过gather并行章节，兄弟标题不等兄弟全部证据共享；fact_checker读assembled draft不等独立核源。分工可增加覆盖，也增加重复取材、Context复制和归并风险。
- [PR2145](https://github.com/assafelovic/gpt-researcher/pull/2145)已合并，merge `816e893e34c6f63d782a60e858c309b4218404af`；原规划来源没进入抓取，后续空搜会丢。固定案例版已有修复，[planning_sources测试](https://github.com/assafelovic/gpt-researcher/blob/3582a6841fe7dc801e2a34e34ee408641aea9bce/tests/test_planning_sources.py)用mock验证后续空搜仍保留来源。不是本轮真实研究质量结果。
- [lexical_context_filter测试](https://github.com/assafelovic/gpt-researcher/blob/3582a6841fe7dc801e2a34e34ee408641aea9bce/tests/test_lexical_context_filter.py)与select_context显示关键词选择边界；无TypeSafe时auto可用keyword，小材料可全入，无词重合取开头不能解释为语义命中。
- 既有普通模型helper存在多尝试/回退，流式路径不同；未完全证明SDK物理请求数。报告费用字段不能替代本项目每物理Call的准入和账目。

### 4.3 扩展接口及验证路径

“发现与证据展示→需求讨论编辑→准确确认→工程方案”可复用基本研究产物与交互入口，但需新建应用层文档版本、确认、输入封存、权限和调用治理。旧报告正文/聊天不自动迁移为已接受需求；导入只能作为带来源的历史材料，已知私有ancestry保留，未知外部来源不自证安全。

正向验证应追输入版本→源捕获→Claim→实际Context→讨论提案→人确认的准确hash→方案请求/提交；反向包括chat/编辑竞争、head变化、旧确认、取消/迟到、未知调用、资源不足和恢复。程序部分、UI迁移、完整测试和真实质量均未执行，必要材料缺口保留，不修改或执行GPT仓库替代研究。

## 5. 五专项及关键取舍

### 5.1 Runtime/Harness：单链A与按需分工B

| 候选 | 收益 | 代价/失败 | 完整确认结果及验证 |
| --- | --- | --- | --- |
| A 阶段图内单研究决策链 | 全局条件连续，少复制和合并，适合依赖密集或预算紧任务。 | 深专题容易挤占主Context，跨平台/源码可并行证据覆盖受限。 | 保留自然退化路径；用同任务覆盖/成本/反证保持检验，不预设较浅。 |
| B 主研究者＋有限专题子研究者 | 独立平台/源码问题可集中深入，主链继续全局讨论。 | 过期目标、私源披露、重复取材、迟到结果、无效封存和额外调用。 | **已确认按需B，无固定角色配额、无递归；并发与预算不增加。** 无独立子题时采用A。 |

DeerFlow task tool经ParentContextSnapshot→SubagentExecutor/create_agent→astream传递受限背景；[context_snapshot.py:88-95](https://github.com/bytedance/deer-flow/blob/60940ae9c528e5d740b27d058f2c5d80565a71b7/backend/packages/harness/deerflow/subagents/context_snapshot.py#L88)排除父system、runtime与隐藏材料，历史动作不成为子执行证明；复制仍消耗Context。[executor.py:149-151](https://github.com/bytedance/deer-flow/blob/60940ae9c528e5d740b27d058f2c5d80565a71b7/backend/packages/harness/deerflow/subagents/executor.py#L149)区分终态与cleanup完成。相关固定测试使用假模型/stream，未证明远端取消；不把本机超时当费用结清。

本项目采用同Task Work分支、准确assignment输入与直接依赖、Task拥有共享取材和消费者、stable幂等创建/替换、根锁序、原配额与deadline。子提交核本地head及直接依赖，父按当前metadata归并，不能因无关sibling推进丢弃有效结果。当前核权决定能否读取或发出，共享exact capture不构成多份证据。

编译前seal研究输入；关键义务不可因失败被降级，允许的未知需满足事先标准。取消一个消费者不误取消其他合法消费者；零消费者、父取消、来源撤权和发送前后分别处理。late result只审计/结算，terminal不释放仍在途物理槽。LangGraph成功节点恢复证据不替任意外调幂等，unknown全项目停发仍为应用规则。

需本人掌握：从accepted InputRevision追Work/Call；画出创建/替换/取消/提交双序；说明何时不能复用结果，何时只需重做归并而不重发模型。程序事务、真实Pg竞态和恢复仍待后续业务验证。

### 5.2 Context Engineering与Token分层

资料链是发现→取得/表示→切分→按问题选入→必要展开→排序→可解释裁剪/压缩→实际请求编译→模型利用→交付。保存来源与问题关系、条件、反证、限定、冲突和未知；原始数据与Context投影分开。明确“未取得/未识别/未选入/裁剪丢失/摘要失真/模型未利用/输出未体现”，才能从trace定位原因。

OpenCode使用完整请求与provider usage锚点，再估计新增消息；hook/编译后body仍可能变化。其字符近似、buffer和首尾裁剪不能证明准确Token或反证保留；缺usage/价格归零的路径不适合本项目。当前不增加模型摘要、向量/embedding/reranker服务；装不下必要证据时有界分批或partial。

**纠正先前过宽判断**：官方[1017发布README Prompt Encoding](https://huggingface.co/deepseek-ai/DeepSeek-V4.1-Flash-1017/blob/1bae0e1088993b9b82de08f59de5be5a34e42170/README.md#prompt-encoding)明确recipe提供相同prompt格式，不能继续笼统写“完全没有官方映射”。这不证明本机已匹配或托管服务内部计数必相等。固定recipe `935817c66f5d6e64838f419692545f06787e485f` 的V4.1资料还指向Vision-Exp比较revision `6821d6ad3681a4b137b066b76094fa82ebd0a380`、tokenizer hash `81f64d1248a68ce3663e07ab3ee48b851e5df0e32d27cb98e4c9a268151e8d99`；原导入revision未完整取得，不能把比较声明升级成托管1017字节等价。

`dsv41.rs`239-299涉及json_object、system/BOS/角色及非thinking封装；只数正文漏计。`tokenizer.rs:43-109`克隆tokenizer并清added vocabulary，special ranges另编码；padding/truncation仍需显式检查关闭。[PR47](https://github.com/deepseek-ai/deepseek-recipe/pull/47)在读取时open，不能当合并修复或本机资产确有故障。Issue5对应`93b0fd229cc9ffa6b1a8c63d42b0bf741bbec170`的维护者修复说法与测试不等本轮执行。

| 分层 | 能证明什么 | 失败与剩余风险 |
| --- | --- | --- |
| local-format qualification | 固定公开模型映射、转换器/模板/tokenizer/options/字段，完整本地请求计数控制本地用途及累计配额。 | 本机资产、实现与匹配未运行；字段/模板/资产变化撤旧资格，不自动下载或沿用默认padding/truncation。 |
| hosted-fit qualification | 固定text-only、nonthinking、非stream、json_object等范围，显式输出预留、窗口和版本适配；现有有限诊断仅采样。 | estimated-fit不是数学零overflow；首调用可能失败并消耗槽与费用，不自动重发，overflow等撤受影响资格。 |
| actual usage/cache/fee | 保存provider prompt/completion/cache值、原响应和币种价表；prompt=hit+miss、total=prompt+completion，reasoning不双计。 | 合法非零本地差异记录后可继续，不学习offset/加额度。缺usage或费用不明保留预留、全项目停止新外发。 |

供应商响应协议schema异常与模型生成的业务JSON不合格分开；后者是不可用交付、repair0，不能误撤供应商资格。`prompt+显式O>C`、completion超过O、context_overflow、unsupported映射等按资格规则处理，原Call结算不抹去。价格或资金失效拒新准入；恢复、迟到usage和新ID不自动重开资格。

[官方计价](https://api-docs.deepseek.com/zh-cn/quick_start/pricing/)与[Search计费说明](https://api-docs.deepseek.com/guides/search/#billing)属于日期化公开规则：Search/Fetch非200或空结果不计费不能推出本地丢响应也免费，模型错误码未普遍声明免费。2.20/Call与296.46整批是基于公开上下文/价表的保守条件预算，不承诺供应商任意违约下绝对封顶；当前余额、旧账、币种、grants和unknown仍待资格。实际Token、模型、费用测试本轮均未执行。

需本人掌握：完整请求的两种工件（API安全bytes与公开模板编码）、本地/实报/缓存/费用分账、合法差异与资格失效、Context损失位置。不能用重编码输出证明provider计费。

### 5.3 Memory Management：理解机制但不启用

工作历史/ActionStep、当前Context、业务状态/证据、checkpoint与跨任务记忆是不同对象。Letta资料中的常驻块、工具更新、整块替换及detach不等删除，提示更正、撤销、过期和私源污染的风险；LangGraph namespace/TTL不是授权；smolagents结构步骤不等长期学习。

比较结果：无Memory最容易解释当前任务来源；显式选入历史报告可解决已知复用且逐次核源/核权；自动Memory潜在减少重复，但新增提取误差、陈旧继承、私有来源撤销、跨用户污染、费用及评价复杂度。本轮没有充分真实复用需求支持承担它。

**正式决定仍是全入口禁用/延期**，不产生Memory候选、读写、检索、注入或后台入口。默认profile、框架Store预载、旧checkpoint refs、import/restore/rebuild均在关闭范围；active refs为空且对应实际请求，trace为disabled/not_applicable、hits/writes=null+feature_disabled。Case证据、条件、文档与审计持久化照常；明确选入历史材料仅走SourceSet权限及已知私有ancestry，不解引用Memory。

保留未来重新评估所需的真实需求、独立审查和另行范围批准，不在当前配置建立启用候选。Memory预留闲置不挪用。本人当前需能解释差别和验证没有注入，未来自动提取、更正、遗忘实践不冒充已完成。

### 5.4 Tool Calling/MCP：每层成功语义不同

直接API便于固定身份和可观察请求；应用工具路由提供严格schema、授权、限额和结果处理；模型原生调用只是请求表达；MCP还包含发现、transport、生命周期和服务器行为。MCP SDK `session.py:1013-1047`在tools/call后可为结果校验补list_tools，证明一次SDK动作不等一个物理请求。内存stream取消测试不证明远端已停；协议取消可被忽略或晚于完成。

当前采用GitHub直接adapter和受约束Search/Fetch，模型原生工具0、Browser0、MCP仅研究。工具发现/描述/选择/参数/执行/消费、技术错误/业务错误、幂等/取消/清理都必须绑定当前身份、准确请求与物理Call。SDK隐式重试和隐藏证明刷新不能绕开Gateway；公开页面内容不能授新权限。

工具200/执行成功、内容有用、形成研究进展、义务满足与任务完成分别记录。无效证据不自动重试；已完成/unknown不重发；有副作用的消息发送不因“工具能做”自动授权。本人需追一次参数→外发→结果→Claim→Context，解释业务失败与技术不明。

### 5.5 Evaluation/Reflection：用症状和证据改进

运行中自检帮助发现缺口，但模型反思可能强化错误并消耗调用；角色fact_checker不是独立事实证明。离线回归、独立审查、真实运行、人工验收和实际价值各有不同对象。DeerFlow delivery固定测试允许多个产物只呈一件就成功，说明harness完成不保证本产品full flow双首稿和准确确认。

采用真实症状→原trace→可证伪假设→最小修改→正反回归→独立审查→准确获授权匹配复测→解释结果。没有真实症状不编造纠正；保留失败、unknown、费用、混杂因素，全部正式槽位原分母不替换。程序原稿、人工修订、最终交付和实际用途分开；owner亲改/核源/读码不由AI代填。

唯一协议保留6正式槽位、3Agent原稿与6人工终稿；REQ完整需求到方案含两首稿，CON两变体含无权威基准问题，EXP已确认需求的方案。requirements_only与编辑无独立正式效果声明；材料pending，本轮不制题/gold。人类最终质量、描述省时、本人掌握、真实团队价值、Go和发布分开，无20%硬门槛或强制DR。

## 6. 贯穿案例与需决定的真实问题

### 案例A：从“养老语音助手”想法出发

这是负责人设想，不是已证实需求。应先拆成“哪类人、哪个任务、现用替代、什么困难、设备/平台/应用/语言、预期交付、成功如何观察”。老年、肢体、视听或认知障碍不能合并成同一用户；识别、导航、读消息和发送各有不同错误代价。用户访谈、现场观察、真实手机与原型均未执行。

2026-11-03静态复核：[Voice Access官方命令](https://support.google.com/accessibility/android/answer/6151854)已提供语音开应用/导航，但语言列表无中文；[Apple iOS/iPadOS27可用性](https://www.apple.com/ios/feature-availability/#accessibility-voice-control)列普通话/粤语。系统内建能力不是第三方应用任意控制权限，也不能证明具体用户能成功操作。

[Google Play AccessibilityService政策](https://support.google.com/googleplay/android-developer/answer/10964491)限制自主发起/规划/执行自动化，verified核心残障辅助工具有明确例外；这是Play适用政策，不推广成所有Android渠道绝对技术禁令。[Android messaging intents](https://developer.android.com/guide/components/intents-common#Messaging)可发起compose界面，不证明消息已发送或已送达。

应比较系统功能/教程、具体任务辅助、受约束自动化等简单替代；对读消息的隐私/旁听、联系人歧义、口述识别错误、发送与结果不明提出候选控制和验证，但未讨论的候选不能成为已接受需求。A/B分工可把平台证据与用户困难研究独立进行，主研究者必须保留它们冲突和未知；权威法规/政策与真实需求不是同一类证据。

交互样例是“用户想发什么→当前平台能支持什么/不能证明什么→冲突与代价→需要用户决定哪些范围→准确需求版本→条件化方案”。若没有具体设备与真实用户，结论停在假设/原型验证建议，不宣布可商用、可上架或已解决用户困难。

### 案例B：从GPT Researcher固定仓库出发

首先承认研究、文档和持久报告聊天/编辑已有，再分别判断准确需求版本、确认、并发安全、来源权限和方案绑定是否在已读链路成立。不能用README宣称缺功能，也不能用有限未读证明全仓不存在。

预期新增机制是围绕原产物的版本与权限契约，而非重新造全部研究器。兼容性包括旧报告导入、chat与需求稿分离、旧链接/引用、私源ancestry、取消与恢复；未读取或未验证的迁移/完整UI/provider路径列出，不直接移植旧whole-object upsert和默认环境行为。

正常与失败走查分别覆盖：查证→展示发现→提案编辑→人确认hash→方案；缺证据、取消、首稿失败、并发编辑、方案在途需求变更、旧资格、unknown和预算不足。两案例共同测试自主调查与有内容的提问，不代替正式材料或产品价值实验。

## 7. 调用池和首次交付：收益、代价、精确边界

负责人先表达B/共享池/Token分开证明的方向，随后确认Token风险、仅保护首稿，最终确认完整CONTENT版本。下表是讨论追踪，不单独产生授权。

| 议题 | 事实/冲突与候选 | 已确认决定与代价 | 验证/配置落点 |
| --- | --- | --- | --- |
| 分工 | A简单连续；B专题深入但多状态/合并成本。 | 按需B，A自然退化，不预设角色数量或递归。 | Assignment/Work、shared consumers、seal、独立竞态/恢复测试；契约/ADR。 |
| 正常调用 | 旧按用途2/2/3/2/1/4固定配额，不适配专题深度。 | 14normal共享，保六用途单次上限与总量；不提高费用上界。 | purpose程序选择，所有父子/归并调用计数；唯一协议及validator。 |
| 首次文档 | 保护全部四次编译压缩研究空间；不预留会生成但无法保存。 | 仅尚未尝试首件预留，full2/others1，失败已用不补；不保证成功，后修仅剩余额度。 | 调用/Token/版本/终态多维原子预留及负例；契约与测试规格。 |
| compile次数 | 旧4normal可另有retry，容易被误解为4total。 | **最多4次物理compile，技术重试也计入。** 更严格、失败后修订机会减少。 | Case2/Work1 retry、16physical与Token同时限；四次上限负例。 |
| Token | 本地模板、托管fit和实报不同；严格相等会误拒，纯估算冒实报会误导。 | 采用分层；合法差异记录，overflow撤资格，费用unknown全停；接受首调用可能溢出/付费风险。 | 固定资产/请求双工件/原usage，诊断仍独立有限授权。 |
| Memory/工具 | 框架功能不等真实复用与权限保证。 | Memory全禁延期；Browser0/MCP研究，直接API优先。 | active refs/实际请求/隐藏调用/私源撤权；不借用Memory资源。 |
| 质量/春招 | 技术可行、真实用途、本人掌握并非同一结论。 | 真任务检验，岗位能力绑定亲手操作与证据，不以框架数或未来要求包装履历。 | pilot/trace/亲改/回归/展示，人验分别记录。 |

正常池上限14、输入360448、输出预留61440；物理最多16、累计输入458752、输出预留81920；已知瞬时错误重试Case≤2/Work≤1，各用途单次限保持。旧加两最大重试的派生总量425984/77824也不能被理解为额外配额。工具/并发/时间/存储、Memory闲置和全批116model/Search84/Fetch168/GitHub704/HTTP1072上界保留，实际参数以协议为准。

一份讨论用可行算术例子为：clarify1、主plan1＋子plan2、子extract2＋主extract1、review2、gap1、compile4，共14；主extract用24576，其余按相应单次上限可得到360448/61440。它只证明一个分配能放进上界，不是默认角色/次数模板、质量证明或Context资格。取消/replan/linkedTurn不重领总量，compile至多4物理包括retry。

## 8. 五专项连接与验证规格

目标→研究/工具→证据/Context→判断/补研→需求讨论/确认→工程方案→交付/Trace/评测/改进，需要逐连接取证。

| 失败连接 | 可观察证据及可证伪检查 | 本轮/后续边界 |
| --- | --- | --- |
| 工具success但证据无效 | 原响应→SourceCapture→Claim；固定无关/过期/空内容不推进义务。 | 配置要求/离线fixture可查；真实源质量未验。 |
| 取得但未选入，或摘要丢反证 | 获取/选择/裁剪理由、保护集合、Manifest和实际请求；加入关键反证检查是否仍在。 | 静态契约及后续03a行为，不以字数缩短证明质量。 |
| 子任务沿过期目标或撤权继续 | assignmenthead/依赖/grant与send/commit双序，检查旧请求拒绝及仍在途审计。 | 真实Pg/并发/撤权测试待业务授权。 |
| reqhead改变仍用旧确认或方案 | DocumentHead/Confirmation/send/commit竞争，双方顺序均不得提交错绑定。 | 配置能规定，不能当事务已通过。 |
| 取消/恢复/replan重发或unknown换ID | stableWork/Call、原请求hash、sup与Pg连续性、原预算deadline。 | 后续故障注入/真实外发匹配验证。 |
| shared取材消费者失效 | exact capture与current consumers，取消一支不伤合法支，零消费者不晋升迟到研究内容。 | 真实权限与资源回收未验。 |
| seal后迟到内容改变交付 | compile封存refs/hash与lateaudit；关键未满足不能被optional化。 | 离线状态规格与后续竞争验证。 |
| Memory默认路径仍注入 | 禁用feature状态、空active refs与实际请求一致；旧checkpoint/default/import负例。 | 无任何Memory启用/访问资格。 |
| Token合法差异误拒或费unknown当0 | 本地/实报字段、profile revision、price/currency/reservation和原Call结算。 | 本轮不运行Tokenizer/模型/账户余额。 |
| Trace有数据却定位不了 | 能否追到目标/问题/Work/Call/source/Claim/Context/文档版本/费用，以及首次偏差。 | 静态字段要求不是实际诊断能力。 |

## 9. 岗位适配与本人实践

用户对集中资格询问回复“**不用管，agent应用中大厂**”。本轮只以此确定方向，不继续推定届别、学历、校招/实习资格、地区、年份、可投入小时或投递日；历史“JS/TS/Vue基础、尚未读懂AI核心代码”是旧记录，不当现已更新事实。

2026-11-02限定官方样本：[百度Harness J100779](https://talent.baidu.com/jobs/detail/GRADUATE/74d83772-1bd0-42b9-8cc5-69eb45696b62)为上海校招技术，页头2026-07-21未证明该字段是发布日期，职责覆盖执行约束、状态、隔离、上下文交接和反馈；[百度AIDU J99974](https://talent.baidu.com/jobs/detail/GRADUATE/6f9c3a86-6557-409d-8fa7-e6f4c68d6765)为北京2027AIDU类别，涉及规划/工具/状态及稳定性、成本、延迟。特殊项目类别不等普通校招统一门槛；官方存在页面不证明当前仍招或本人合格。小米/小红书/腾讯部分动态正文未取得，本轮不以索引或旧观察补成最新职位。少量样本不能代表整个市场。

| 岗位能力归纳（不是雇主统一要求） | 项目机制/实现证据入口 | 本人实践、演示与追问 |
| --- | --- | --- |
| Agent端到端应用 | 原始Draft→条件→研究→版本确认→方案；API/Worker/Pg/实际请求。 | 亲追一次请求，解释哪个事实由谁拥有；演示正常、取消、需求换版；不能把目标图当已实现。 |
| 状态、并发、恢复 | stableWork/Call、权限/封存双序、sup连续性、unknown及cleanup。 | 先预测竞争结果，再读trace解释为何不能重发；Mock和真实Pg分别说明。 |
| 工具、证据与Context | source→Claim支持/反证→实际请求→文档，固定源和范围。 | 亲核一个“片段存在但不支持”反例，区分未取得/未选入/未利用；展示如何定位。 |
| 调用治理/费用 | purpose、公开模板计数、usage/cache、price、funds与unknown。 | 解释一次合法计数差异与一次拒绝；无实际账证不报节省。 |
| 调试/评价闭环 | 原症状→假设→亲改→回归→独审→获授权匹配复测。 | 亲做有界修改、解释取舍和被推翻假设，展示正反行为；未发生保持pending。 |
| 交付与产品判断 | 真实待办、原稿/人工终稿、用途、失败和限界、恢复演练。 | 区分技术通过、本人掌握、真实价值和发布；不保证录用或把AI工作写成独立贡献。 |

这些是后续实践安排，尚未证明本人完成。旧92–136h/130–194h仅原范围估计，当前投入未知不填0，也不据日期外推春招期限。

## 10. 独立审查、证据缺口与配置落点

研究阶段取得独立技术/安全候选审查，最后结果转录摘要见design-review-summary（本地证据：`.tmp/predev-reopen-20261028/config-20261029/review-20261101/research-20261103/design-review-summary.md`）。审查者有效权限为workspace-write，要求只读不是实际隔离。旧消息摘要不是raw报告导出，不捏造消息id或原文hash。

- **B-v3：DONE_WITH_CONCERNS**。原四项设计前置静态补齐，未确认新P级概念缺陷；终态/清理、共享权限、事务竞争/恢复/计数和真实质量未运行。首稿失败/重试/四次compile交叉负例尚待验证。
- **TOKEN-v2：DONE_WITH_CONCERNS**。漂移P2静态关闭，未确认新缺陷；estimated-fit、供应商计费履约仍风险假设，不能声称远端精确计数、零overflow或任意故障绝对封顶。
- **CONFIG-CONTENT-20261103-v1增量：DONE**。覆盖运行/评测权威、同bytes hash/解析/语义、六purpose及compile物理计数；未确认新增P0–P3。B/Token内部不重复审；用户随后完整确认明确收紧与newprompt范围。
- 现有配置审计并非全业务全仓审查：新一轮23/28全文，较大tasks/validator/tests定点及部分同字节旧审查复用；原技术报告覆盖28全文/完整patch，原安全报告23全文+5有界。没有把各自范围混说成独立全包安全复审。

缺口不阻止表达有边界的配置决定，但会阻止未来真实研究资格或效果声明：restrictedPg双序/恢复、完整新程序、官方Tokenizer本机匹配、API模型字段/usage/币种价/余额/旧账、最低独立介质纸钥恢复、正式材料独立制备、真实用户/设备和本人实践均待实际证据。部分DeerFlow provider factory、GPT SDK物理重试、Letta对应固定源码、report-store专门测试未完整取得；未读到不是不存在。

配置保留安全边界和历史，简化重复Memory长段/参数镜像，合并同职责引用，重构共享预算、委派、Token及校验器原始bytes链；删除仅经核实的重复表达，不删除旧研究和checklist。新增提示词契约只描述目标，不改运行prompt。validator减少大段描述重复，仍保留独立批准rev/rawhash与关键不变量，防hash与语义检查不同输入；不增加prod跳过或自动重绑定。

后续路线按[PLANS](../../PLANS.md)：ENV隔离→DEC-M1-01真实认证/私有Draft/最小sup→02权限/Task/Work/阶段图/文档确认→03a来源/证据/Context→首public前最低独立恢复→03bGateway/Token资格与获授权真实pilot→06真实症状纠正→07正式六槽→08b完整恢复/本人演示。Memory04与Browser05延期。各切片的正常/失败验收和所需操作授权独立；本轮只完成配置与限定验证。

## 11. 本报告的实际检查与交付解释

本文件形成时只进行了公开静态读取、进入材料读取和文档编写；没有本报告作者执行的新业务/上游测试结果。实际配置回归、完整diff审查、保护指纹与发现修复结果由唯一任务记录和新审计索引提供，不在本报告预填通过或测试数量。

最终分别报告静态配置、离线测试、独立实施审查、真实执行、人工业务验收、本人掌握、实际价值和发布准备。配置通过不能替代后七类证据，独立设计审查不能替代新正文实施审查。发生重要新设计/范围变化时返回相应确认，而非藏入配置修复。


## 12. 2026-11-03 R2受控重启与首闭环补研

本节为RESEARCH-BASELINE-20261103-R2日期化追加，原报告全部原字节前缀保持。CONTENT-20261103-02完整确认后，负责人以“执行计划”授权CONFIG-PLAN-20261103-02的17文件配置、限定离线检查及新审计，不授业务／环境／付费／Git。本节不是第二任务或批准系统；实际配置检查和实施独审由[唯一任务](../features/DECISION-001/tasks.md)裁定。

### 当前实现与静态风险

本轮进入main@81ecfa2756ca3ebe02824c857572270f3150cdb0，根工作区干净、本地origin/main同HEAD，未查远端；browser-use内部查询Permission denied。已追Vue→旧SQLite或P-01 Pg API→Worker→agent_factory→旧AgentLoop。固定p01-local-owner仍是旧实现，新认证、文档确认、SourceSet、新sup及Gateway不是现有能力。以下静态路径不是本轮业务回归，也未运行故障复现：

| 固定HEAD源码位置（前缀backend/src/adaptive_research/） | 触发／机制与影响 | 后续验证 |
| --- | --- | --- |
| worker/runner.py:441–453；infrastructure/pg_store.py:738–791 | 有有效密钥／旧Pg、无price-book及PgBudget时require_budget=False，可能先发缺价格／预算资格的模型调用；响应后停线不代发前拒绝 | ENV启WSL前隔离旧自动服务／旧出口；假供应商／restrictedPg验证零发送，本轮不启动旧服务 |
| infrastructure/pg_store.py:456–472及:224–230；agent/agent_loop.py:548–553 | 最后本地cancel检查后API先提交取消，finish_task仅核live/fence/lease不核cancel flag，仍可能completed及新报告 | 两连接barrier固定取消／成功双序，不冒新程序保证已过 |
| agent/tools/github_tool.py:48–53；agent/agent_loop.py:390–402；agent/call_observer.py:100–108 | 可能已到远端的ReadTimeout等RequestError被包technical ToolResult、落failed再重试，unknown分类丢失 | MockTransport不明结果保unknown／一次物理尝试，不推广GET为未来付费Search安全重试 |

### 固定上游与供应商补核

[LangGraph 3cd57c038ad827d05f80c6488adea9994156c58c的成功writes恢复](https://github.com/langchain-ai/langgraph/blob/3cd57c038ad827d05f80c6488adea9994156c58c/libs/langgraph/langgraph/pregel/_loop.py#L789)和[测试827–917](https://github.com/langchain-ai/langgraph/blob/3cd57c038ad827d05f80c6488adea9994156c58c/libs/langgraph/tests/test_pregel.py#L827)只复用成功节点，失败节点可重执行，不保证外调exactly-once。DeerFlow60940ae9c528e5d740b27d058f2c5d80565a71b7的[executor终态／清理](https://github.com/bytedance/deer-flow/blob/60940ae9c528e5d740b27d058f2c5d80565a71b7/backend/packages/harness/deerflow/subagents/executor.py#L2029)及[假stream测试](https://github.com/bytedance/deer-flow/blob/60940ae9c528e5d740b27d058f2c5d80565a71b7/backend/tests/test_subagent_executor.py#L5667)区分超时终态与物理槽。测试正文已核，未运行。

OpenCode固定ed74ec82ce1fe3a36da6c0815a935473ef4bb0fb的[estimatePrompt:1005／hasMeasuredPrompt:1050](https://github.com/anomalyco/opencode/blob/ed74ec82ce1fe3a36da6c0815a935473ef4bb0fb/packages/core/src/session/compaction.ts#L1005)按provider ID筛usage锚点，precompute另核model ID／variant；旧“同provider/model历史”过强，勘误另见[原研究追加](HIGH_STAR_AGENT_MECHANISMS_2026-10-22.md#2026-11-03-r2补核与历史表述勘误)。生产context.load及完整provider序列化未全取得，不宣布生产跨模型bug；prepare后hook可改请求，预算对象不是wire bytes证明。

[MCP2025-11-25 Task Cancellation](https://modelcontextprotocol.io/specification/2025-11-25/basic/utilities/tasks#task-cancellation)的取消终态不证明远端已停止，停止执行仅SHOULD attempt；[重投递](https://modelcontextprotocol.io/specification/2025-11-25/basic/transports#resumability-and-redelivery)也不授权重执行工具。保持MCP研究、Browser0。

2026-11-03官方[DeepSeek中文价表](https://api-docs.deepseek.com/zh-cn/quick_start/pricing/)Flash峰价输入2／输出8元每百万Token、Search／Fetch5元每千成功请求，与原CNY条件预算相符；USD不能混算为冲突。[Token说明](https://api-docs.deepseek.com/quick_start/token_usage/)与[Chat API](https://api-docs.deepseek.com/api/create-chat-completion/)支持本地计数／实际usage分层；当前“1M”页面未单独展开1048576，精确托管C／格式／账单待资格，不从本地模型推定。

### 受控重启候选、选择与审查

PostgreSQL16.15固定7d3e000c5961a544302072058a1184e9a588837b：[pg_control.h:98](https://github.com/postgres/postgres/blob/7d3e000c5961a544302072058a1184e9a588837b/src/include/catalog/pg_control.h#L98)的system_identifier用于匹配cluster WAL；[xlog.c:5171](https://github.com/postgres/postgres/blob/7d3e000c5961a544302072058a1184e9a588837b/src/backend/access/transam/xlog.c#L5171)区分普通crash延续timeline与archive恢复新timeline，结束后统一production。[同步commit](https://www.postgresql.org/docs/16/wal-async-commit.html)的正常崩溃持久性依赖实际存储，不证明未恢复旧数据；[PITR](https://www.postgresql.org/docs/16/continuous-archiving.html)可有意停旧一致状态。cluster ID／启动时间／timeline／UUID／hash链均不能单独证历史费用／撤权最新。

| 候选 | 收益、代价及适用前提 | 本人选择 |
| --- | --- | --- |
| A人工核对后重新授权 | 同一未替换目录、未restore／copy／PITR的受控停机；可信操作者真实陈述，无外置持久组件，但程序不能检测漏报旧库还原，弱于原B5.2独立最新性 | 已选并完整确认，不放宽所有恢复 |
| B独立停机锚点 | Pg恢复单元外READY／ACTIVE否决见证，启动从实际权威状态重算；增加双写、锁和独立回滚域／持久性资格，共同回滚仍不保证 | 未采用，不新增外置组件／第二业务账 |

A先全非终态Task及未发许可收尾、物理出口收拢、费核清且无未解决unknown停线才clean回执；新boot研究closed，核证／本人未还原陈述→新CLI→精确CONTROL_ONLY→当前资格→新research许可。旧grant／Attempt／proof不复活，原Casecap／deadline及历史unknown不洗零／不重发，文档确认保准确版本但当前head／actor／来源重核。异常断电、WSL崩溃、PG意外重启、证据不齐／疑还原仍隔离，运行细则只在[契约B5.2](../contracts/CURRENT_CONTRACTS.md#b52-supervisor)。

新上下文design_coherence_review与controlled_rearm_security审现行架构及A/B；v0排队／未发预留遗漏、CONTROL_ONLY前置循环和B权威root／窄写者歧义经v1补足。采用A的受影响技术／安全复审无新确认P0–P3，原相关P2静态关闭。实际权限仍workspace-write，只读要求不是隔离；未跑Pg、进程、持久性、控制请求、模型或费用。它是设计审查，不替本轮17文件完整正文／diff／实际检查的实施独审。

### 首闭环、岗位与未验

本人选择GPT Researcher3582a6841fe7dc801e2a34e34ee408641aea9bce的需求到方案改造为案例B，优先完整业务闭环；先承认已有研究／报告编辑／持久聊天，不凭有限未读宣称全仓无功能。它是开发材料／后续另授pilot目标，登记预读与已知发现，非formal gold，实际用途价值待证；案例A继续模糊输入、系统替代和反证。目标为2027春招Agent应用开发／AI全栈正式岗位，后端可靠性结合Vue3／TypeScript，先依赖规划、不承诺工期，首实践后实耗校准，不推定地区／资格／掌握。

2026-11-03重读[百度Harness样本](https://talent.baidu.com/jobs/detail/GRADUATE/74d83772-1bd0-42b9-8cc5-69eb45696b62)及[2027AIDU全栈样本](https://talent.baidu.com/jobs/detail/GRADUATE/6f9c3a86-6557-409d-8fa7-e6f4c68d6765)，分别涉及状态／约束／Context／反馈及规划／工具／评测成本延迟。类别／日期有限，不证明当前名额、本人资格、整个市场或未来统一门槛；岗位Memory／多Agent词不代机制收益。本人请求追踪、解释竞争、亲改回归及异常演示仍需实际确认。

跨Turn首需求partial→编辑确认→linkedTurn→新Task seal／方案加入贯穿验收；03b首次真实pilot前增加A的离线、restrictedPg和paid-disabled进程证据，不反扩首工认证／Draft／最小sup，不豁免最低独立备份、费用／Token资格。唯一draft-m1-3及公开材料原字节、六槽位不变，能力引用draft-m1-capabilities-4。本节未运行新业务、上游测试、模型、Tokenizer、Browser、WSL或数据库。


## 13. 2026-11-03 TEAM：完整路线重评与阶段0配置依据

本段追加，进入全文raw字节不改。当前负责人重新评估完整方案并确认本机双身份团队共享／人工交接、独立产品链、CLI指定项目确认人，随后Default模式`PLEASE IMPLEMENT THIS PLAN`授权阶段0配置。可见会话转录见`.tmp/team-plan-20261103-01/authorization.md`及approved-plan.md；不是原始API导出，不将agent记录当人授权。当前产品、运行参数和实施顺序仍分别由SPEC、CURRENT_CONTRACTS及PLANS负责，本报告不立第二规则。

原始一手研究本轮补核：[LangGraph固定1.0.0 durable execution](https://github.com/langchain-ai/langgraph/blob/1.0.0/docs/docs/concepts/durable_execution.md)要求确定性回放及side-effect幂等；未完成task可能重入，故checkpoint不是外调exactly-once或业务权限。当前durable-execution文档URL已重定向至Persistence，版本证据不能与未来选定依赖混用。[Anthropic 2024-12-19 effective agents](https://www.anthropic.com/research/building-effective-agents)及[2025-06-13 multi-agent research](https://www.anthropic.com/research/multi-agent-research-system)提供按任务独立性增加复杂度的经验；其内部多Agent质量与token数字不作为本项目收益或预算证据，也不直接指定本项目架构。

另核固定GPT Researcher3582a6841fe7dc801e2a34e34ee408641aea9bce的[report routes](https://github.com/assafelovic/gpt-researcher/blob/3582a6841fe7dc801e2a34e34ee408641aea9bce/backend/server/app.py)及[ReportStore](https://github.com/assafelovic/gpt-researcher/blob/3582a6841fe7dc801e2a34e34ee408641aea9bce/backend/server/report_store.py)：报告编辑／持久聊天确实存在；读取与whole-object写入分别锁文件，不能直接充当本产品的不可变需求、精确确认与事务权威。此为限定源码路径观察，未跑上游，不证明全仓没有其他能力。独立产品链、增量改旧链、以上游为底座三候选经过讨论，负责人选择独立产品链；保Vue，合格纯helper可复用，不接旧AgentLoop。

已确认顺序允许完整单链安全内核、四模式离线集成、最低独立恢复和Gateway/Token/资金/来源/rearm资格后先做真实public full pilot；再动态委派重集成和私源。动态与私源保完整M1要求，单链不是完整父任务验收。首次pilot检查现状／需求边界／改造设计／首批任务／开工阻碍，另记人工核查补救负担；真实团队和任务未发现，不写价值已成立，不新增Case/调用/资金。

新增确认职责是本轮真实产品决定：发起者接受／编辑／取消／显式接续，项目指定负责人确认／撤销，同身份允许。精确policy／member／account eligibility版本永久失效，角色换回／重入／reenable不复活旧确认；logout和换凭据不等内容撤销。独立设计审查发现每资格reserve不足以保障多current confirmation的显式撤销，补每确认独立3072B预留后受影响复核关闭该P2。仅收紧revoke不读来源正文、不刷新proof、不需研究grant/time，仍核当前身份／指定人／Case权限；有限桶与程序保证待真实Pg验证。

设计审查为本聊天新上下文plan_design_review及两次受影响复核，结论DONE_WITH_CONCERNS、无剩余确认P0–P3；其正文是可见消息，不伪造API导出／消息ID／原始hash。该结论不是本轮实际16文件实施独审，也不是调用、Token、恢复、本人实践或团队价值证据。当前实际修改／命令／独审／限制只由唯一任务记录及新审计索引裁定；当前不执行业务、环境、安装、真实模型/Tokenizer/Browser或费用。
