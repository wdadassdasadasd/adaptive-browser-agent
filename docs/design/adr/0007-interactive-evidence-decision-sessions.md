# ADR-0007：需求与方案研究起草会话与数据流

- 原日期2026-10-26；当前**FOCUS-BASELINE-20261102**。P2/A1/R2及后继专项已确认，28文件配置同步获批，当前文件审查／业务／真实验收见[唯一记录](../../features/DECISION-001/tasks.md)。
- 权威：[规格](../../../SPEC.md)、[计划](../../../PLANS.md)、[契约](../../contracts/CURRENT_CONTRACTS.md)、[部署ADR5](0005-windows-worker-wsl-postgres.md)、[决定ADR8](0008-m1-engineering-baseline.md)。具体数值只在契约／唯一协议维护。

## 2026-11-02 FOCUS增量及保留理由

当前M1关闭全部Memory功能入口，包括手动／自动、API／CLI、默认profile／框架Store预加载、旧checkpoint refs、导入／恢复／重建与后台路径；不提取候选、不读写、不检索、不注入，active Memory refs必须为空并与各模型阶段实际请求一致。Trace记disabled/not_applicable，hits／writes为null并附feature_disabled，不以测试零次冒充禁用证据，不要求空Store／seed／Memory快照。Case内条件、证据、文档和审计照常持久化；本人明确选定历史报告走SourceSet准确获许可版本，不解引用Memory refs，继续核当前权限和已知私有祖先。DEC-AC-17／DEC-M1-04保留延期、未实施／未验；完整Context属03a、Token资格属03b，当前M1不依赖04。真实复用需求、独立设计审查及准确范围另批后才可重开，原Memory预留容量保持闲置上界，不挪给其他功能。

原DRAFT起草配置按final-01字节有效，以下会话／版本设计保留，不把历史设计审查当作FOCUS新字节审查。

原显式会话方案B将原消息、提议、本人接受、业务轮和证据分开，比父子Task重建更便于核对归属、历史和活动轮；代价是对象权限与事务恢复。保留真实LangGraph阶段节点与Pg应用权威，不将旧AgentLoop整体包节点。单用户吞吐并非Pg唯一理由，还包括可靠性与本人学习目标。

2026-11-01文档证据评审交付已核实有效，本轮由用户明确增加需求／方案起草。四模式为仅评审、仅需求、基于本人确认需求仅方案、需求到方案完整闭环；无仓库想法可用，固定主GitHub／许可公开资料／选定本地text-code-diff可组合，源码只读不运行。不新增协作体系。新价值仍未获真实任务证据；闭环窗口优先不是完整首阶段或M1完成。

## 组件与对象流转

私人raw Draft→本人明确加入team/project的目标及选定材料→Case／有界澄清／接受模式InputRevision→Worker阶段研究→SourceSet/SourceCapture/Claim/ContextManifest→需求DocumentVersion→本人精确RequirementsConfirmation→方案DocumentVersion→有界ReportSnapshot引用双稿及确认→当前权限下UI／各Markdown→核源修订／linkedTurn。仅需求独立结束，仅方案先导入追溯需求并明确确认；review保留原证据路径。

API负责真实身份、确认、对象访问及交付claim；Worker负责规划／取源／抽取／缺口／停止／报告，Gateway统一物理调用及许可；Pg拥有事实、SourceSet、本地capture、不可变DocumentVersion及current heads、RequirementsConfirmation、Task执行许可、Work／Call、source用途／分享、费用与证据。TraceView只是只读canonical关系视图。checkpoint采用sync目标，仅有界已提交refs，不与应用事务假定原子、不决定授权；缓存／Context／framework Store都不是业务权威。

业务Session与登录session分开。creator/requester/accepted_by/actor保原身份，Task有独立执行许可；logout／断UI／auth自然expiry不自动取消已接受Task。本地成员离队／disable／撤Task许可阻新claim并partial；管理员接管必须新接受／linkedTurn，不能替换原owner或重置Case原目的、期限、累计预算和Work。资格控制Task不是review Turn，不带研究许可；运行中资格刷新在当前Task内有界执行，不等待同一满队列另一Task。

## 接受、状态与故障

同发起者/session/key同正文先幂等重放后CAS；接受条件／Task／active／event／version同事务，无孤立对象。模型提议、来源或Memory不写accepted。ReviewQuestion依据分别user_accepted/source_stated/agent_suggested；无权威标准时有界探索，不自动宣布符合性。

DocumentVersion只由显式人工保存／AI成功提交追加，当前head CAS；键入不是逐键版本，未保存仅有界UI内存，不localStorage，logout／换身份清除。保存不等确认；任一新requirements head在同root事务清current_confirmation，旧确认不删。确认绑定version/hash/actor并CAS当前head；方案start/send/commit同时核绑定需求和当前确认及solution目标parent/head。R1/C1→R2后旧S1不能发布；迟到仅原Call audit/usage/cost，旧方案过期由引用比较，不新权威flag。冲突409明确人工重载，不静默覆稿。

各模式先保首工件：full需求＋方案，其余一件；4compile之外无隐含调用，版本／Token／正文envelope／canonical终结同事务预留。人工保存仍计版本容量；条件改版不无限首稿，模式切换仅原Case目的显式接受且可原子预留新增义务，否则拒扩／partial，不自动新Case洗额度。精确数值只见契约。

等用户终结partial释放调度槽，回复linkedTurn同Case累计。稳定Work不是plan序号，物理Call每次独立；发送前claim精确bytes、当前权限／proof／模型资格、DB实时lease/fence和generation；输出提交再核，不能等reaper才判断失租。cancel先提交拒，claim先在途；unknown停部署全项目新外调，completed／unknown不凭新ID重发。

已完成响应在当前hash／权限／profile合格时可本地重处理；checkpoint落后复用stage，引用坏拒伪恢复。迟到不新增Document／Claim／Stage／proof／报告，只原Call受限审计及幂等费用。终态唯一event／report指针／active同事务；reaper仅安全已有refs，不能伪旧Attempt重编失效私源正文。物理槽由sup seal旧代出口／连接并确认资源收拢后释放，不等Task调度槽。

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
