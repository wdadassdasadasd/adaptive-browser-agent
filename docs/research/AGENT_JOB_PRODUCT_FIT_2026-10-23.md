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

## 2026-10-26 复核：岗位证据、真实任务与产品边界

本节观察日期为 **2026-10-26**，追加记录本次会话中已完成的官方网页、固定版本源码和本地证据核查；上文保留为 2026-10-23 的原始研究，不将旧观察改成现状。当前产品决定见 [ADR-0007](../design/adr/0007-interactive-evidence-decision-sessions.md)，需求与实际完成状态分别见 [DECISION-001 规格](../features/DECISION-001/spec.md)和[任务表](../features/DECISION-001/tasks.md)。

### 用户已确认的目标与待验证判断

用户主投 Agent／大模型应用研发，求职展示优先；有 JavaScript／TypeScript／Vue 等前端基础，现有项目由 AI 生成且尚未阅读。目标是一个月形成实习简历和面试初版，再用 1.5 个月完善春招版本。周工时及新增预算尚未确认，时间是交付目标，不是已证明的工期。用户计划在 2027 年 3—4 月求职；准确毕业年月、实习经历及具体岗位资格未知，本次不再追问或据此假定应届资格。

首批使用者为用户和同学这样的 AI 应用开发者。真实任务是为居家老人陪伴和日常问答系统比较语音识别、语音合成、对话组件及其组合，允许开源项目、模型与云服务。初版以文字对话澄清条件、研究、解释、修改条件和按需补查，采用本机或屏幕共享试用；养老系统是研究对象，不是本项目要实施的系统。

| 假设 | 当前证据与判断 | 仍待验证 |
| --- | --- | --- |
| 选型场景太窄，无法展示 Agent 工程深度 | 固定版本源码表明，规划、上下文、工具、状态、失败与评测可以在同一业务场景中深入验证；这一担忧尚未被证实。源码细节见[机制复核](HIGH_STAR_AGENT_MECHANISMS_2026-10-22.md#2026-10-26-固定版本复核产品框架与基础设施)。 | 本项目真实任务效果、用户本人理解与调试能力、面试评价。 |
| 仅限 Python 开源候选、一次报告，符合真实需求 | 用户的实际语音任务需要比较不同交付形态，并在条件变化时继续查证；这些边界与已确认需求不匹配，构成有依据的有限扩展理由。 | 三类组件与组合比较能否在既定时间内形成足够证据。 |
| 可复查的交互选型助手比通用问答更有价值 | 已有可提供真实任务的首批使用者；这是需求来源，不是使用效果。 | 用户能否据此缩小候选、核查关键理由并明确下一步实测；任务频率和持续使用意愿。 |

### 官方岗位样本

下表均在本轮实际打开官方正文核查。普通“任职要求”与明确的“优先／加分”分开列出；它们是具体岗位的书面要求，不是整个行业或实际录用门槛。

| 公司／岗位／来源 | 类别、批次及学历原文口径 | 任职要求摘要 | 明确优先项 | 日期与适用限制 |
| --- | --- | --- | --- | --- |
| [百度：上海 Agent Harness 研发工程师 J100779](https://talent.baidu.com/jobs/detail/GRADUATE/74d83772-1bd0-42b9-8cc5-69eb45696b62) | 校招／技术；本科及以上，相关专业 | Agent 原理、PyTorch／LangChain／AutoGen 等框架实践、算法到工程落地、长任务问题分析；职责涉及状态、执行约束和上下文交接。 | Agent 开源贡献、Harness 落地或智能体产品实践；核心开源贡献、论文、竞赛。 | 页头日期 2026-07-21，未单独说明该字段是否为发布日期；未核到 2027 年春招专门公告。 |
| [小红书：2027 校招点点 Agent 研发工程师](https://job.xiaohongshu.com/campus/position/22020) | 2027 校园招聘／研发／产品工程师；本科及以上 | 计算机基础和至少一门主流语言；理解 LLM／Agent；完整项目实践、个人贡献与取舍说明；至少一个方向深入。 | 第一作者 CCF A／B 论文、高水平 ACM 类竞赛；核心团队实习或研究课题经历。 | 未见公开发布日期。搜索摘要遗漏了独立加分段，本表依据渲染后的完整正文。 |
| [小红书：AI Agent 研发实习生—引擎架构](https://job.xiaohongshu.com/campus/position/21231) | 实习／研发／引擎架构；在校本科及以上；项目标记“其他项目”，未限定毕业届别 | 至少一门 Java／Python／Go／C++；工程基础及实际 AI 工具、Demo、脚本或工程项目；问题拆解和闭环。职责含 Runtime、Workflow、工具、记忆、评测及日志／指标／Trace 工具化。 | 总实习时长六个月以上优先。每周四天以上是要求，与优先总时长分别判断。 | 未见发布日期或截止日期；一个月是项目准备目标，不是该岗位的实习时长要求。 |
| [小米：AI Agent 开发工程师—汽车](https://xiaomi.jobs.f.mioffice.cn/campus/position/7670914994071046451/detail) | 校招／正式／2027 届计划；南京；学历原文“本科以上” | Python 或 TypeScript／Node.js、服务及前后端基础、LLM 工具和上下文；还要求深度学习及多机多卡训练框架。 | 大模型训练和项目经验优先。 | 未见公开发布日期；属于应用工程与训练能力混合岗位，不能代表纯 Agent 应用研发；投递时需确认学历原文的具体解释。 |

[百度校招职位列表](https://talent.baidu.com/jobs/list)面向 2026-09-01 至 2027-08-31 毕业的 2027 届毕业生。用户个人资格未判断。上述岗位的 2027 年春季名额、届时开放状态、实际投递和录用概率均未验证。本轮没有把实习或社招当校招条件；上文腾讯 WorkBuddy 样本仍只是社招参考。

### 岗位能力到可观察证据

| 能力 | 可观察工程证据 | 当前覆盖与缺口 |
| --- | --- | --- |
| 任务规划与工具使用 | 一个实际问题为何选工具、发生何种失败、怎样重新规划的完整轨迹 | 已有 AgentLoop 和路由；P-02 尚无完整真实研究成功，新增会话也未实现。 |
| 上下文工程 | 固定资料下的证据保留、输入选择、Token、耗时与质量对照 | DEC-T01 有离线切片证据；不能推断真实效果或成本已改善。 |
| 记忆与状态 | 用户条件快照、证据原来源与时间、跨轮引用及恢复一致性 | 单任务账本与部分恢复已有证据；方案 B 的选型会话、修订与引用仍是目标。 |
| 评测和优化 | 失败样本 → 可证伪假设 → 定点修改 → 同口径复查 | 已有失败诊断和离线回归；修复后的真实闭环与新语音任务效果待验证。 |
| 服务可靠性 | 取消、事件补读、唯一终态、失租和数据库失联的记录 | P-01 48/48 仅证明本机假任务关口；不证明真实浏览器恢复或多账户能力。 |
| 产品交付与个人贡献 | 用户试用能定位证据；本人能解释链路、取舍、失败并亲手修改与回归 | 前端基础可作为起点；项目未阅读，不能把 AI 生成代码的存在当作本人已掌握。 |

现有源码已在 [ReporterService](../../backend/src/adaptive_research/agent/reporter.py)接入 [DecisionService](../../backend/src/adaptive_research/agent/decision.py)。因此，上文“报告器固定无法推荐、没有决策链”是旧观察，不应继续当作当前事实；实现和部分离线验收也不证明推荐真实有效。具体状态以任务表及逐切片证据为准。

### 语音任务的公开资料能证明什么

本轮仅核实官方资料及示例写了什么，未执行语音模型、付费 API 或用户录音测试，未选择供应商。

| 官方来源／版本 | 公开资料支持的事实 | 不能直接推出的结论 |
| --- | --- | --- |
| [Paraformer 实时语音识别 Java SDK](https://help.aliyun.com/zh/model-studio/paraformer-real-time-speech-recognition-java-sdk)，页面中的 paraformer-realtime-v2／8k-v2 | 接入需开通服务及 API Key；有具体地域 WSS 地址、非流式和双向流式示例；语言声明按具体模型区分。 | 支持某方言不证明目标老人弱声、停顿、混合口音下可靠；流式接口不证明完整语音问答的端到端时延。 |
| [阿里云百炼模型调用价格](https://help.aliyun.com/zh/model-studio/model-pricing)，动态页 | 价格按模型与地域区分；识别可按音频秒、合成按文本字符、对话按输入输出 Token 等口径计费，历史上下文可能再次计入。 | 不同单位不能直接换成统一“每分钟系统成本”；优惠、实际时长、上下文、重试及部署成本仍需条件和记录。 |
| [FunASR v1.4.14 README](https://github.com/modelscope/FunASR/blob/v1.4.14/README.md)及[同标签 LICENSE](https://github.com/modelscope/FunASR/blob/v1.4.14/LICENSE) | 提供本地 Python、流式识别和部署示例；依赖与语言范围随实现／checkpoint 区分，工具包与模型许可分别核查。 | 可自托管不证明目标设备运行效果；工具包许可不替代模型许可核查，开源不等于算力维护成本为零。本研究不提供法律结论。 |

研究助手应分别呈现官方声明、分析假设和对应条件下的实测结果，并保留观察日期、模型／版本、地域和来源。待实测项包括目标老人识别、家庭噪声、端到端时延、音质偏好和真实总成本；本次没有这些证据。被比较语音服务的报价与 Agent 自身实际模型／工具支出分开记录。

### 当前决定与授权边界

已确认产品保持技术选型场景，扩展候选类型及多轮决策闭环；已批准方案 B“选型会话＋有限执行任务”和首版默认上界。批准内容及实现依赖由 ADR-0007、现行规格／契约与任务表承接，本研究不是另一份规格。当前授权仅同步列出的项目文档与契约，不包括业务实现、数据库迁移、依赖安装、付费运行或 Git 写操作。

研究没有证明一个月即可达到招聘要求，也没有证明产品价值。实现、真实质量、个人掌握分别验收；原[冻结评测协议](../evaluation/CURRENT_EVAL_PROTOCOL.json)、历史结果、r12／P-02 No-Go 和费用约束保持有效。新增语音／多轮复核独立记录，真实调用须另行完成资金设计和明确授权。

## PREP-BASELINE-v4.3：实习岗位、产品问题与首版证据（资料观察2026-10-26，落地2026-10-27）

本节是当前基线；上文校招/社招、Python-only与语音首批方向保留其原观察/决定日期，由[ADR8](../design/adr/0008-m1-engineering-baseline.md)局部替代。岗位只是有限官方样本，不代表行业统一标准；网页可访问不等于职位仍招，不推定本人学籍、出勤或任职资格，不保证面试/录用。招聘宣传和开源Star不能代替工程验收。

### 官方样本的类别、日期与适用限制

| 官方样本 | 分类/职责与必需条件 | 明确加分/日期与当前适用性 |
| --- | --- | --- |
| [小红书 AI Agent研发实习生—引擎架构 21231](https://job.xiaohongshu.com/campus/position/21231) | **实习/应用工程**；Agent runtime/workflow、工具、memory/eval及日志指标Trace；在校本科及以上，掌握Java/Python/Go/C++之一，工程实践；每周至少4天 | 长期约6个月为优先项，不能改为必需或本人已满足。页面正文经官方索引可读取、直接页面动态访问有限；未见明确发布日期/截止，观察日不能当发布日期或当前空缺证明。 |
| [百度 J105397](https://talent.baidu.com/jobs/detail/INTERN/83a5dbcc-48a6-4356-b6d6-b4da9f0a2528) | **实习/应用工程**；workflow/context、异常处理/状态归档、golden样本/人工评测、数据/知识库和前后端应用 | 页面头部2026-09-03，未验证其必为发布日期；分类来自INTERN，不由标题猜。当前适配在应用闭环，不把训练能力作为此项目必需。 |
| [百度 J99649](https://talent.baidu.com/jobs/detail/INTERN/e3cec5b8-b7a3-4946-99fc-b292b749cd53) | **实习/应用算法混合**；Agent/LLM应用及相关算法能力；明确至少5个月、每周4天的到岗约束 | 页面头部2026-07-21同样不冒充发布日期；训练/算法部分不由本应用项目自动覆盖，不能推断本人资格。 |
| [百度 J100779](https://talent.baidu.com/jobs/detail/GRADUATE/74d83772-1bd0-42b9-8cc5-69eb45696b62) | **校招**，不同入口/批次 | 只作后续能力参考，不作为实习门槛。 |
| [小红书2027校招22020](https://job.xiaohongshu.com/campus/position/22020) | **2027校招**，非实习 | 批次不能与实习合并；未核实本人的适用毕业时间。 |

上文小米/腾讯等混合训练或社招样本继续按原类别保存，不合成“所有Agent岗位都要求”。必需条件是雇主明确的资格/技能条目；职责是入岗工作；加分仅明确优先项。本项目重点覆盖应用工程职责，不能用有向量库/框架就判岗位能力达标。

### 能力→可观察项目证据→M1验收→当前覆盖

| 样本中的能力 | 项目必须展示的行为 | M1验收/证据 | 当前覆盖与缺口 |
| --- | --- | --- | --- |
| 应用端到端开发/问题定义 | 不完整技术需求→接受条件→短名单/排除→下一步验证 | DEC-AC08–12/16、全部9次E2E与真实使用者反馈 | 旧表单/矩阵/条件建议离线切片；新session和价值未实现/未证实 |
| Agent runtime/workflow/tools | 有意义子目标、真实工具/失败反馈、有界重规划 | AC002/012、T09/T11的轨迹/只读MCP实证 | AgentLoop/ToolRouter已有；r11无进展和真实质量No-Go |
| 上下文工程 | 当前条件不被旧轮覆盖，反证/限定语保护可解释 | DEC-AC18、C0/1/2固定资料12次决策调用/成本对照 | 当前ContextManager裁剪和Token预检有离线证据；对照/保护尚待 |
| memory/状态归档 | 目标条件、跨轮事实、跨任务线索各自归属和生命周期 | DEC-AC17、8次开关运行及到期/撤销/隔离/重核测试 | Pg任务/事实已有，checkpoint不是来源记忆；完整线索和真实对照未实现 |
| 日志/指标/Trace及可靠性 | 持久调用、unknown费用、取消恢复与诚实终态 | DEC-AC13–15；fencing/资源/唯一终态/请求审计A | P01假48/48，未证明真实浏览器恢复或资金保护 |
| 人工评测/样本/质量优化 | 全尝试保留、人工核源、真实故障最小修复与复测 | DEC-AC19/20；诊断链、独立材料/费用/失败证据 | r11/r12可诊断，T01离线切片；真实纠错复测尚缺 |
| 工程协作/测试/解释 | 独立审查、风险测试、用户读码/亲改和复现 | 模块验收包、本人五类实践、演示及取舍 | 旧审查/测试有记录；本人具体新实践尚未发生，不写已掌握 |

### 用户问题的研究结论与验证边界

一次决策不止一份综述：需要明确使用场景/候选身份，区分硬条件与偏好，先查会改变结论的证据，记录未知/冲突，展示取舍，随后根据条件变化重新判断，并留下可执行的下一步（例如小规模集成/部署/音频实测）。这来自当前本人需求与官方资料工作流的综合推论，尚无充分访谈/对照数据证明普遍痛点和时间收益。

替代方案A人工打开文档/发布页：控制强但跨页对照、时效与条件记录费力；B通用LLM：澄清容易但来源、历史和实际调用审计不一定可查；C长篇研究Agent：资料广但未必产生明确约束下可行动的选择。这些是待实测假设，不据产品宣传认定其必然失败。首版通过真人任务、保留正负反馈、问“哪些候选被排除、依据是否可信、下一步能否行动、条件变化是否可解释”验证价值，不编造节省时间阈值。

任务池依据：
- **语音组合**为负责人实际需求，角色/方言/设备/地域/预算属于任务输入；无音频实测不报告真实语音效果。
- **ORM**是公开需求衍生。[Drizzle讨论5269](https://github.com/drizzle-team/drizzle-orm/discussions/5269)只作社区动机，作者身份不升为维护者；[Drizzle schema文档](https://orm.drizzle.team/docs/sql-schema-declaration)与[TypeORM DataSource](https://typeorm.io/docs/data-source/data-source-options/)用于核对方言/驱动，不假定声明支持等于无成本切换。
- **PDF**是公开需求衍生。[Next.js issue29997](https://github.com/vercel/next.js/issues/29997)为2021历史动机，不能当2026当前故障；[Puppeteer PDF指南](https://pptr.dev/guides/pdf-generation)（观察版25.16.0）与[PDFKit入门](https://pdfkit.org/docs/getting_started.html)用于核对浏览器/绘制路径，正式材料仍需固定版本和实际部署条件。

补充材料冻结/分母与真实授权见[独立M1协议](../evaluation/DECISION_M1_PROTOCOL.json)。后两题明确不是本人另两条真实项目需要。三题覆盖组合与单选、条件变化、版本/部署/价格等差异；只能检验有限迁移，不能证明通用Agent。本人理解与软件质量/产品价值分别验收，四周目标和风险不因岗位样本而被承诺。
