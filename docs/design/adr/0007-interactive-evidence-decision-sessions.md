# ADR-0007：需求与方案研究起草会话与数据流

## 2026-11-04 DEV-STAGES现行覆盖

当前配置DEV-STAGES-20261104-01、能力引用draft-m1-capabilities-6。本次Default明确实施六阶段26切片计划的P0，状态与实际检查/实施独审见唯一任务记录；原TEAM/R2及以下日期化决定保原字节/范围，只解释当时设计。路线唯一正文为PLANS，不由下文旧阶段顺序重建。

六阶段工程验收与显式按需效果包分离；效果未运行不记pass。原full/reqonly两个pilot分别承担4.5公开及5.4私源最小真实工程链，原配额/安全资格不减；dynamic/private仍工程必需。stage5影响请求/Token/权限/恢复时先补验，5.4前最低恢复须覆盖当时基线，不重领诊断。逐片人验收及准确Git授权→必要CI→同stage下一片；merge另批，下stage合并后明确启动。工程M1、原稿质量、掌握、团队价值、Go/发布分别取证。


## 2026-11-03 TEAM历史基线（以下原正文按当时范围解释）

- 原日期2026-10-26；当前**TEAM-BASELINE-20261103-01**。完整团队研发计划已确认，本轮“PLEASE IMPLEMENT THIS PLAN”实施阶段0配置；RESEARCH-BASELINE-20261103-R2及更早批准保原字节／范围，不恢复业务或真实执行资格，状态见[唯一记录](../../features/DECISION-001/tasks.md)。
- 权威：[规格](../../../SPEC.md)、[计划](../../../PLANS.md)、[契约](../../contracts/CURRENT_CONTRACTS.md)、[部署ADR5](0005-windows-worker-wsl-postgres.md)、[决定ADR8](0008-m1-engineering-baseline.md)。具体数值只在契约／唯一协议维护。

## TEAM本机共享项目与确认职责

首版限定本机最多两个身份，共享项目与人工交接，无实时共同编辑或管理后台。独立产品入口保留Vue／API／Worker／新Pg／supervisor与真实LangGraph阶段，应用表拥有业务事实，checkpoint仅有界已提交引用，不接旧AgentLoop。

本机有权操作者以受控CLI管理项目、成员和唯一确认人；发起者负责接受目标、编辑、取消和显式linkedTurn，确认人只确认／撤销准确需求版本，可与发起者同一身份。项目策略及账户／成员资格revision随确认记录绑定；换人、离队、禁用后旧确认失效，重新加入不复活，普通logout／凭据轮换不自行撤销内容确认。方案start/send/commit重核有效确认；权限变更先提交则阻新send／commit，先前合法claim可在途，迟到只原Call审计／费用。无确认人可需求／评审，不能方案。

每个当前确认及适用资格独立拥有下一次必要撤销预留；新增前原子取得，满额不能挤占已有撤销能力。确认撤销不借账户／成员／项目策略预留；永久失效才可在根事务有界释放，临时来源不可用不作永久失效。精确字节、桶、幂等和锁序由契约唯一维护。所有新CLI写者同样受sup／根锁／ShutdownReceipt及pending RearmOperation作废规则约束，角色设置不授研究许可。

当前顺序为02-A/B→02-C单链安全核心→03a离线四模式→原最低恢复及03b全部真实资格→公开源完整单链pilot→动态重集成→私源，再按原两pilot／真实纠错／正式六槽／完整恢复验收。动态和私源仍为完整M1必需，早期单链不关闭其父任务；fake／real共用准入及提交内核。formal仍同一真实参与者，可同一账户兼任两角色；跨身份集成测试不证明真实团队价值。以下日期化原决定保持历史身份，涉及“本人确认”的当前角色按本节及契约解释。

## 2026-11-02 FOCUS增量及保留理由

当前M1关闭全部Memory功能入口，包括手动／自动、API／CLI、默认profile／框架Store预加载、旧checkpoint refs、导入／恢复／重建与后台路径；不提取候选、不读写、不检索、不注入，active Memory refs必须为空并与各模型阶段实际请求一致。Trace记disabled/not_applicable，hits／writes为null并附feature_disabled，不以测试零次冒充禁用证据，不要求空Store／seed／Memory快照。Case内条件、证据、文档和审计照常持久化；本人明确选定历史报告走SourceSet准确获许可版本，不解引用Memory refs，继续核当前权限和已知私有祖先。DEC-AC-17／DEC-M1-04保留延期、未实施／未验；完整Context属03a、Token资格属03b，当前M1不依赖04。真实复用需求、独立设计审查及准确范围另批后才可重开，原Memory预留容量保持闲置上界，不挪给其他功能。

原DRAFT起草配置按final-01字节有效，以下会话／版本设计保留，不把历史设计审查当作FOCUS新字节审查。

原显式会话方案B将原消息、提议、本人接受、业务轮和证据分开，比父子Task重建更便于核对归属、历史和活动轮；代价是对象权限与事务恢复。保留真实LangGraph阶段节点与Pg应用权威，不将旧AgentLoop整体包节点。单用户吞吐并非Pg唯一理由，还包括可靠性与本人学习目标。

2026-11-01文档证据评审交付已核实有效，本轮由用户明确增加需求／方案起草。四模式为仅评审、仅需求、基于本人确认需求仅方案、需求到方案完整闭环；无仓库想法可用，固定主GitHub／许可公开资料／选定本地text-code-diff可组合，源码只读不运行。不新增协作体系。新价值仍未获真实任务证据；闭环窗口优先不是完整首阶段或M1完成。

## 组件与对象流转

私人raw Draft→发起者明确加入team/project的目标及选定材料→Case／有界澄清／接受模式InputRevision→Worker阶段研究→SourceSet/SourceCapture/Claim/ContextManifest→需求DocumentVersion→项目确认人精确RequirementsConfirmation→发起者显式接续→方案DocumentVersion→有界ReportSnapshot引用双稿及确认→当前权限下UI／各Markdown→核源修订／linkedTurn。仅需求独立结束，仅方案先导入追溯需求并由当前确认人明确确认；review保留原证据路径。

API负责真实身份、确认、对象访问及交付claim；Worker负责规划／取源／抽取／缺口／停止／报告，Gateway统一物理调用及许可；Pg拥有事实、SourceSet、本地capture、不可变DocumentVersion及current heads、RequirementsConfirmation、Task执行许可、Work／Call、source用途／分享、费用与证据。TraceView只是只读canonical关系视图。checkpoint采用sync目标，仅有界已提交refs，不与应用事务假定原子、不决定授权；缓存／Context／framework Store都不是业务权威。

业务Session与登录session分开。creator/requester/accepted_by/actor保原身份，Task有独立执行许可；logout／断UI／auth自然expiry不自动取消已接受Task。本地成员离队／disable／撤Task许可阻新claim并partial；同Case仅原发起者可接受／编辑／取消／显式linkedTurn，有权本机操作者的撤权等收紧权限不授予接管权。其他成员只能读取获许可材料或另建关联Case，不替换原owner，不转移原Case或重置其目的、期限、累计预算和Work；关联Case不自动取得grant或新配额。资格控制Task不是review Turn，不带研究许可；运行中资格刷新在当前Task内有界执行，不等待同一满队列另一Task。

## 接受、状态与故障

同发起者/session/key同正文先幂等重放后CAS；接受条件／Task／active／event／version同事务，无孤立对象。模型提议、来源或Memory不写accepted。ReviewQuestion依据分别user_accepted/source_stated/agent_suggested；无权威标准时有界探索，不自动宣布符合性。

DocumentVersion只由显式人工保存／AI成功提交追加，当前head CAS；键入不是逐键版本，未保存仅有界UI内存，不localStorage，logout／换身份清除。保存不等确认；任一新requirements head在同root事务清current_confirmation，旧确认不删。确认绑定version/hash/actor并CAS当前head；方案start/send/commit同时核绑定需求和当前确认及solution目标parent/head。R1/C1→R2后旧S1不能发布；迟到仅原Call audit/usage/cost，旧方案过期由引用比较，不新权威flag。冲突409明确人工重载，不静默覆稿。

各模式先保首工件：full需求＋方案，其余一件；4compile之外无隐含调用，版本／Token／正文envelope／canonical终结同事务预留。人工保存仍计版本容量；条件改版不无限首稿，模式切换仅原Case目的显式接受且可原子预留新增义务，否则拒扩／partial，不自动新Case洗额度。精确数值只见契约。

等用户终结partial释放调度槽，回复linkedTurn同Case累计。稳定Work不是plan序号，物理Call每次独立；发送前claim精确bytes、当前权限／proof／模型资格、DB实时lease/fence和generation；输出提交再核，不能等reaper才判断失租。cancel先提交拒，claim先在途；unknown停部署全项目新外调，completed／unknown不凭新ID重发。

已完成响应在当前hash／权限／profile合格时可本地重处理；checkpoint落后复用stage，引用坏拒伪恢复。迟到不新增Document／Claim／Stage／proof／报告，只原Call受限审计及幂等费用。终态唯一event／report指针／active同事务；reaper仅安全已有refs，不能伪旧Attempt重编失效私源正文。物理槽由sup seal旧代出口／连接并确认资源收拢后释放，不等Task调度槽。

## 2026-11-03 R2：跨Turn双稿与受控重启

需求首稿后terminal partial等人，不保持占槽“等待中”Task；本人编辑／准确确认后原Case接受linkedTurn。前后Task分别seal研究输入，后轮显式引用前轮仍有权已提交需求／证据及当前准确确认；前轮late audit不晋升研究输入。方案start／send／commit再核head／confirmation／actor／来源，最终包绑定准确双文档及确认。Case资源、Turn数和绝对deadline不因等待／重启暂停或重领。

A受控重启按[契约B5.2](../../contracts/CURRENT_CONTRACTS.md#b52-supervisor)处理，不复活旧Task：全部queued／running／recovering业务与控制Task确定终结，同事务清active及唯一终态；未发许可作废，Attempt依次fenced→resources_quiesced→closed。新boot先只读核clean证据与本人未还原陈述，再新CLI→精确CONTROL_ONLY→新研究许可。原文档与准确内容确认保留但当前head／actor／来源重核；旧grant／Attempt／proof／checkpoint执行资格不复活，Call completed／unknown不重发，未解决unknown停线不能由rearm解除。

A限定同一未替换目录、未restore／copy／PITR；程序不能发现漏报旧库还原，异常／疑似还原仍隔离。Memory全入口关闭，不新增外置见证。此配置不证明真实事务竞争／恢复已通过。

## 来源、派生与读取

有repo时单主repo固定repo ID／commit／path／blob，普通网页仅采集表示版本，未知最终URL和源时间不伪造。Query→SourceCapture→question/subject→Claim关系→ContextManifest→Report形成精确追溯。新capture不覆旧，同hash不合身份，片段命中不证语义，未读非不存在。改条件默认同commit，明确更新来源才新version／义务／报告。

私源上游主体为团队App installation／仓库，非逐成员GitHub ACL；本地member／Taskgrant独立。五分钟proof需当前受限签发和身份／读取验证，公开200不续私源。采集、留存、外部模型、团队展示／导出及完整query／URL披露各自许可；私有实际输入祖先随派生传播，公开引用不洗白。源撤销挡新用／新派生并收紧旧报告访问，不能召回已下载副本。unknown也停proof刷新，来源到期可暂时使相关报告不可读，这是已确认可用性代价。

选定本地文件无GitHub App proof要求，仍核retain/use/model/share/public-disclosure当前许可及准确bytes；已知GitHub私源及派生仍需原proof，不以local profile/新ID/编辑/导入洗白。外部未知出处只标user_provided/provenance_unverified，不假称追出所有手工复制祖先。共享文档不套Memory同作者限制。SourceSet封定准确成功项和失败／未读项才入模型，不把路径元数据用于服务端open，不承诺原worktree原子或symlink资格。

每个response／page／SSEframe重新核当前账户／auth_session／sup、成员、用途分享与lineage；GitHub私有来源／其私有祖先核适用GitHub proof，纯公开无凭据profile核本地use/share及固定source身份、不要求App签发；cursor不授权，GET不隐式网络刷新。撤权先提交拒未claim，claim先最后一个有界response／frame可在途，非瞬时召回。原始私人Draft仍按owner隔离，不因项目共享而自动入team；来源文本惰性渲染，无HTML执行／图片和预览自动加载。

## Context、Memory与评测

完整接受条件／未知、阶段任务及必要证据关系／反证／限定先保护，再可选证据；保护缺许可或装不下partial。路径／标题／关键词先验证，不默认vector／Embedding／Reranker。Manifest记录实际选排和全部私有祖先，不推测模型内部使用。

原自动Memory生命周期只保为未来候选，不属于当前执行义务。当前条件和Case内证据依旧持久化；本人明确当前偏好可作为接受条件，不生成长期Memory。

原程序／原report核源／本人finalhash分列；三正式Agent原稿均过关键项才原始质量通过。REQ完整链同时保需求／方案首稿和最终双稿包，CON评审均含无基准子问，EXP仅方案基于明确确认需求；仅需求独立终态／编辑修订无独立正式效果声明。六final交付包全共质且计时完整后仅描述已登记三pair median，无20%门槛；Control DR按需，Agent无外部AI代修。公开材料索引不含gold，当前待独立制备；future三role包与Worker隔离。先落披露许可，不把DB时间当实际显示；显示不明保timing_uncertain、不算有效saving，稿件冻结后才揭评分依据。规则由[唯一协议](../../evaluation/CURRENT_EVAL_PROTOCOL.json)独占。

## 首工及历史边界

首工仍真实登录→私人原始Draft持久／重开→第二测试身份404，加最小sup，不建InputRevision／Task，不运行模型／工具／Tokenizer／Browser。团队、来源及接受研究在后继02／03包，不反向扩首工。实际WSL路径／角色／迁移／依赖分别另授；首次公开源真实pilot仍前置最低独立纸卡纸钥恢复、资金／unknown、Token与Gateway资格。

2026-10-26原方案B／v3.1、10月28日D01–19／11文档、10月29日40路径及10月30日五文件修复按各自原字节审查，旧六API／双入口／五账户／候选池及9/8/12不是并行现行规则。历史记录与真实失败受保护，配置批准不授权业务开工。

## 2026-11-03 按需专题与准确输入封存

选择主研究者连续负责＋按需独立专题，保留单链；不固定角色配额或递归。相对单链可覆盖独立来源／机制并保主目标，代价是assignment版本、父子Context、共享消费者、取消和归并事务。子研究仅同Task Work，不是新增授权／调度Task；额外模型请求都消耗共享池。

Pg拥有assignment head、依赖和Task frontier；子提交核局部相关版本，主归并CAS只本地重做，避免无关进展使有效证据作废。Task拥有共享取材而非首child拥有，各消费者逐次核权；取消只解除适用关系，全部失效后不将迟到审计提升为研究事实。

正式编译前seal准确研究输入；关键义务必须满足已接受标准，可选失败／未读显式交付。seal后不偷偷合并迟到结果，需求head／确认变化继续阻旧方案。Shared Work和协调元数据沿既有根锁固定全序，不从Call反锁Work；具体事务、失败及上界见[契约](../../contracts/CURRENT_CONTRACTS.md)。配置未实现这些程序保证。

首工件仅保护尚未首次尝试的一次资源，失败消耗不补满；四次compile统计全部物理尝试含技术retry，减少故障后的可修订余量。此收紧已随完整内容确认，不是成功产稿保证。Token本地格式、hosted-fit和actualusage分别证明；合法差异记录，费用unknown停全项目外发。Memory禁用与各输入来源许可不变。
