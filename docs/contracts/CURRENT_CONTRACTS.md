# 现行目标契约 — RESEARCH-BASELINE-20261103

CONTENT-20261103-01（含两项补充澄清）已完整确认，负责人以“PLEASE IMPLEMENT THIS PLAN”批准CONFIG-PLAN-20261103-01。当前Default模式仅实施30份既有配置、两份新增文档及必要审计／离线检查。实际检查、完整diff独立审查和交付状态见[唯一任务](../features/DECISION-001/tasks.md)，保留原18项历史含义。本页定义运行目标，不证明旧业务程序已经实现。[SPEC](../../SPEC.md)定义产品，[PLANS](../../PLANS.md)定义依赖；[draft-m1-3](../evaluation/CURRENT_EVAL_PROTOCOL.json)独占正式质量／计时／六槽位／整批资金，M1能力补充只引用它。

FOCUS-BASELINE-20261102按进入HEAD dc4498f36c0342eef5191f9f59feaf3b363169b6及原path/raw hash读取；DRAFT final-01、REVIEW final-02、PREP及RAWJSON仍绑定各自原字节，不重写索引。current-3原1ffade6de07ebe3d1e72afb4c44b8677466eca67及显式换行规则不变。[V1](V1_CONTRACTS.md)和[P-01](../tasks/P01_ACCEPTANCE_2026-10-21.md)仅解释原行为。配置不授业务、依赖、环境／DB／ACL、真实模型／Tokenizer／Browser、采购、外部或Git写；原SQLite、费用与来源证据及r12／P-02 No-Go保留。研究／独立设计审查证据及限制见[本轮研究](../research/PREDEV_CONFIGURATION_REVIEW_2026-11-03.md)。

## 1. 目标、对象与应用权限

面向开发者／团队的需求与方案研究起草Agent，保留评审；模式review_only/requirements_only/solution_only/requirements_to_solution。输入可为无仓库想法、单主GitHub固定commit、许可public证据或本人选定本地text／源码／diff，public按需补证。需求稿含问题／用户／目标／范围／流程／AC／依据／假设／待决；方案稿含架构数据流／模块接口数据／正常失败／权限费用恢复／取舍验证。成员提出目标，澄清并接受项目／范围／标准；评审无权威基准先探索，不以自拟检查点宣布符合性通过；起草可提出新需求／AC，但本人确认前不作已接受硬条件。不运行源码或系统，不自动批准设计／改仓库。关键缺口、范围／权限／费用与决定性权威冲突保存进度partial结束；回复建linkedTurn，同Case原目的、累计预算与截止不变。

| 对象 | 权威、关系及最小约束 |
| --- | --- |
| Account/AuthSession | 当前enabled、credential_rev、session rev/state/expiry；登录会话不等业务Session／Task执行许可 |
| Team/Membership/Project | 服务端成员与项目归属，明确加入项目的来源／任务／报告统一分享；测试身份不证明团队需求 |
| Draft/RawMessage | 私人草稿可修，原始消息及位置不可变；个人材料不自动加入团队，不等于接受条件 |
| SourceConnection/SourceGrant | connection/App installation/repo ID、key generation、use/share/model/public-disclosure各自范围与revision；本地grant不代上游能力 |
| Session | creator/requester及team/project/version/active_task；同Session一个非终态业务Task |
| ResearchCase | 首次澄清模型前建立，原purpose/objective hash、team/project/allocation、累计上限与原截止；新Case不自动分配 |
| InputRevision/ReviewQuestion | 不可变接受版本及原消息位置；question basis为user_accepted/source_stated/agent_suggested，后两者不自升硬条件 |
| Task/Turn | 研究／起草Task承载一Turn，唯一status；独立qualification Task为控制类型，不新建review Turn或研究Case／许可 |
| TaskExecutionGrant | 独立于登录会话，绑定责任发起者／成员／Case目的／revision策略／阶段／期限与allocation；logout本身不取消 |
| ExecutionAttempt | 持久UUID、fence、lease、actor generation及恢复次数，不是新Turn |
| PlanRevision/Work | Task内主链／专题／共享取材的稳定逻辑义务，保前驱／替代及输入绑定；换plan／query／ID不绕失败或completed／unknown |
| Assignment/Task frontier/consumers | 应用权威的准确委派head、义务／依赖、当前归并frontier及共享消费者；位于Work协调锁层，不要求另建持久化权威 |
| ResearchInputSeal | 正式编译使用的准确研究输入集合及hash；不替代需求head／确认和当前权限 |
| StageOutput/Call | stage保存已提交输出refs；每物理Call有请求version/安全bytes/hash、profile／凭据handle／许可／slot／usage／费用 |
| SourceCapture/Claim/ReportSnapshot | 不可变采集表示、主体／版本／范围／精确片段与关系、不可变报告；当前可见性独立门禁 |
| ContextManifest/ModelQualification | 实际请求选排／输入祖先、禁用Memory及空active refs；精确官方编码及模型字段资格revision；Memory对象仅未来候选、当前不建不读 |
| SourceSet/LocalCapture | 选定来源集合版本及封定；本地实际上传bytes/hash与解码表示独立身份，未知diff基点不伪commit |
| DocumentVersion/DocumentHead | Case内不可变requirements/solution/review正文、author/parent/hash/known lineage；当前head仅应用表权威，非私人raw Draft |
| RequirementsConfirmation | 当前确认精确绑定requirements version/hash/actor；历史确认不可变；非Task执行grant或资金许可 |
| Checkpoint | 有界serializable已提交ID／refs，仅引用；不决定事实、授权、资金或终态 |

Pg应用表是唯一业务权威。checkpoint独立schema／角色／连接／事务，采用durability=sync目标，不能假定与SQLAlchemy／asyncpg应用事务原子。启动只验环境／schema／代码／部署身份，setup及迁移另授，无DDL运行角色。

首工仍按§7私人Draft和真实认证；后继02才加入team/project/member/use权限。服务器取得actor及归属，不接受模型或body伪造。发起者控制接受／修订／cancel，管理员可cancel／revoke；其他成员查看或另建关联评审。发起者离队／disable／撤执行许可阻新claim并partial，保进度；管理员接管须新接受／linkedTurn，不改旧creator/requester/accepted_by/actor，不重置Case目的／期限／额度／Work。

## 2. API、读取claim与Runtime

| API | 最小输入／结果与边界 |
| --- | --- |
| POST/GET /api/sessions | 取得当前team/project资格后创建／分页50；GET不推进业务、不touch认证 |
| POST /api/sessions/{id}/messages | 明确加入当前项目的原文和出处，返回ID，不自动接受 |
| POST /api/sessions/{id}/cases | raw_message_id、expected_session_version、allocation_id；缺grant可存，不外调 |
| POST /api/cases/{id}/discussions | 受限Case澄清，返回proposal/hash/问题，未接受revision为空 |
| POST /api/sessions/{id}/accept-runs | case_id、parent Turn或null、proposal id/hash、expected version、Idempotency-Key；服务器固定principal |
| GET Task/report/event/source/claim/artifact；POST cancel | 项目成员／用途／lineage及当前读授权；不可见与不存在统一404，cancel有在途边界 |
| POST受限source qualification | 显式控制Task，仅source/operation/allocation及当前控制权限；GET／打开报告无隐藏刷新 |

同发起者/session/key＋规范body先幂等重放再CAS，异body409；接受时核Case/parent/proposal，InputRevision＋Task＋active＋event＋Session version同事务，满队列／DB失败无孤立对象。一般研究条件需活动Turn先结束再改；文档显式编辑及确认按下述根事务CAS可与方案在途竞争，不能改写原Task输入；新revision不扩grant，ID相同不证明语义未扩，重要范围冲突问本人。

所有读取含TraceView／Markdown导出在**每个response、每页、每SSE帧**取得current delivery claim：根事务核账户enabled/credential_rev、auth_session rev/state/expiry/撤销、sup连续资格/actor generation，再核当前membership/team/project/use/share及报告实际输入祖先；GitHub私有来源或其私有祖先才核适用GitHub private proof，纯公开无凭据profile只核当前本地use/share许可与固定source身份，不要求App安装或签发。cursor仅定位不授权。response正文绑定固定snapshot/hash，网络写在锁外；撤销先提交拒未claim交付并关订阅，claim先最多最后一个有界响应／帧可在途，不承诺瞬时召回。ReportSnapshot body≤64KiB、artifact含必要封装body≤1MiB、SSE frame≤1KiB且仅白名单metadata，不正文／prompt／私URL。不长时下载流、后台预取或无鉴权预签URL；来源HTML／远程图片／iframe／链接预览不自动执行／加载。手动外链不携秘密，不替应用权限。logout／session expiry关闭旧读会话后续交付，但独立Task grant有效时任务可继续。未认证401、CAS／幂等409、容量429、资格／DB不可用503；安全错误只固定code和白名单field，不回显body／Pydantic input/ctx／exception。

澄清图load_unaccepted→clarify→validate_proposal→publish_proposal；研究图load_accepted→research_plan→discover_documents/selected_sources→collect→extract→identity_and_gaps→coverage_stop→gap_plan或evidence_review→document_compile/model→validate_publish。节点strict StageOutput仅已提交refs，真实阶段节点不包旧AgentLoop；仅并行独立只读工作，稳定ID归并，checkpoint失败不能伪造业务提交。

| 资源／时间 | 上限 |
| --- | --- |
| 调度 | 活动2／排队4，含业务讨论与独立控制Task；业务Session非终态1、Case最多8研究／起草Turns |
| 分支／调用槽 | Turn取证2／全局4，model物理在途2；Browser0，不保证供应商远端并发 |
| lease／恢复 | 30秒／heartbeat5秒；同Task最多恢复1，原期限与累计量不变 |
| 截止 | 队列5min、讨论10min、研究45min；Case Worker累计60min、普通墙钟7天／formal24h |
| model Call | 绝对墙钟60s且不超过Task剩余；与库的分项timeout不同，未实测不称保证 |
| 控制Task | 单独allocation／source purpose／deadline，最多8 HTTP／60s，额外已知技术retry每Work1／Task1，mint不自动retry |
| DB | READ COMMITTED，clock_timestamp实时；锁wait1s／statement2s，最多2次纯DB重试不包网络 |

running研究／起草Task资格刷新在其自身有界Work／Call内，不能在满2／4队列中等待另一控制Task；独立资格Task无模型／研究授权。关闭UI、断线、logout或自然auth expiry不自动取消已接受Task；账户／成员／Taskgrant明确失效才阻新claim。Task queued→running→recovering→running或completed/partial/failed/cancelled；等用户就是terminal partial释放调度槽，recovering留活动槽。Attempt active→fenced→resources_quiesced→closed，先seal旧代出口／连接并确认实际资源收拢，再新Attempt；不能确认保物理槽并停能力。

全部应用写者含CLI／heartbeat／reaper／终结／迟到结算先锁deployment级ProjectControl，再account→auth_session（仅相关读／认证操作）→team→membership→project→source connection/grant→Session→Case→Task→Work／assignment协调元数据（同一固定全序）→Call→DocumentHead/DocumentVersion/RequirementsConfirmation（同类ID排序）→ModelQualification→budget/capacity→slot，同类ID排序，最后append artifact/claim/event。Task执行不因锁序出现auth_session而依赖当前登录续存。FK RESTRICT、归属不变；checkpoint不回调该锁序；网络／Argon／Tokenizer／关系遍历锁外。提交不明按原operation核对，不猜成功。

Call prepared→admitted（仅预留）→send_claimed→completed/known_failed/unknown。最终claim根事务重核gate OPEN/epoch、独立Task执行principal/member/grants、原目的／期限、DB实时lease/fence/Attempt generation、适用GitHub源proof（GitHub私有来源或其私有祖先）／精确版本、Memory功能禁用／active refs为空且实际请求无Memory注入、模型资格当前及绑定rev、request version/实际safe bytes/hash、credential handle、未撤未耗reservation及物理slot。unknown停线和claim同根串行化；source新rev或Memory禁用状态／请求空refs不符令旧未发送许可失效，须重编新request version，不能覆盖已发送请求。

Stage／Claim／Report／proof提交同样核根gate、DB实时lease、Task状态／cancel／member／principal／输入及源版本／Memory禁用与空refs／model资格，不能等reaper才fence。qualification允许不用旧proof的窄bootstrap，仍核当前connection/repo/grant/key generation/operation/control allocation；新proof精确回执绑定，不延长原deadline。

| 切点／竞争 | 行为 |
| --- | --- |
| cancel／revoke先提交 | 新send／新内容commit拒绝 |
| claim先提交 | 请求在途，不能保证撤回、供应商停工或零费 |
| send_claim后崩溃且不能证未发 | unknown，不凭内存／新ID重发 |
| completed响应已存、stage未提交 | 合格hash／当前权限及profile才本地重处理；缺坏工件partial保费用，不重发 |
| Stage已提交、checkpoint落后 | 复用输出不外调；缺失／版本不符拒伪恢复 |
| bad schema／overlimit | 受影响路径停止／partial，0repair，不Planner换名 |
| lease／cancel／qualification失效后late | 不新stage／事实／proof／报告；仅原Call有许可audit quarantine及幂等usage/cost |
| 无audit正文保留许可 | 仅允许digest／安全metadata，诚实说明不可重处理 |
| 失效Task终结协调 | reaper窄权只终结／event／active及已有进度refs，不伪旧Attempt或新私源派生正文 |

终态根锁事务：已终态返回原结论；cancel先提交为cancelled；权限／源／期限／额度／unknown／fence等阻断为partial；合格有效Attempt报告才completed，无可用结果failed。成功先提交后cancel返回completed。报告指针／唯一终态event／active释放／version同事务，DB失联不称已持久。Task调度槽不等物理在途槽。unknown部署全项目停新外调，含proof刷新；只读安全进度／cancel／revoke及安全确定性终结仍可，私源资格过期仍阻正文访问。迟到结算不开闸，本人对账后另授恢复。

### 按需专题委派、共享取材与封存

主研究者保持目标、全局判断、人类讨论及交付责任；阶段图内单链随时可用，只在问题确实独立且收益足够时委派专题，不设固定角色配额或递归委派。子研究仅同Task下Work分支，不新增Task、Case、Turn、Taskgrant或顶层排队槽；继承原截止、累计额度和执行代次。主链等子结果不占model在途槽或持DB锁。

Assignment绑定服务端Task/Work/assignment身份、准确已接受InputRevision/hash、问题与义务／关键性、依赖／排除、来源和工具用途权限子集、ContextManifest、资源预留及原截止；solution路径另绑定requirements version/hash与confirmation。父子不得复制秘密、隐藏system、整个历史或Memory；实际请求必须含必要条件、证据文本、限定、反证、冲突、未知及其关系，不仅是ID。主链／子链所有规划、抽取、归并、讨论及提案所需模型调用均消耗§4六purpose和同Case资源。模型只提案，不能授予权限、选择更大purpose或自升关键条件。

创建幂等键是Task＋不可变原始规划model Call／Stage身份＋command kind＋proposal index，正文hash另核相等，不能把body hash放进key使变体绕重放。同计划回放不增Work／预留。创建assignment、Work、依赖、consumer、frontier、event和资源预留同根事务，失败不留孤立记录；替换CAS expected assignment head/hash，同事务supersede旧head、建立新head、解除旧消费者及失效未发送许可，不释放在途槽。无关子任务推进不使有效结果作废：child提交核自己的当前assignment head、直接相关输入／依赖和当前门禁；主链基于当前frontier合并CAS冲突只重做本地归并，不重发模型。

以上写入遵守既有ProjectControl根锁序，所有受影响Work／协调记录使用同一固定排序，在Call之前取得，禁止先child或Call后反锁共享Work。关系展开、正文构造、模型／工具网络在锁外，事务内重核有界版本和预留。每次创建／替换源于已计数的唯一规划输出；新可执行子研究至少预留一个剩余正常模型槽及实际元数据／结果空间。使用原Case64MiB、canonical metadata2MiB、stage-derived2MiB、Claim512／edge2048、Manifest64KiB等上界，不新增任意角色数／元数据池；超限保留frontier引用、未读与缺口并partial，不静默截权限／lineage／反证。

Shared acquisition只限同Task且由Task拥有，不附着首个child。共享资格绑定准确source identity/version、实际request、adapter/compiler、purpose/principal及当前权限／credential版本，不能仅凭URL或内容hash。消费者逐个当前核权，同一次capture不算独立佐证。一个child取消只detach自身；仍有有效消费者时可按shared Work自身门禁提交capture。零消费者在claim前拒新发并仅释放确定未用reserve；claim后保原Call有许可审计、费用及物理槽，不再新增研究内容。父Task取消／相关来源撤权使全部适用消费者失效。新assignment可显式复用已合法提交且当前有权的capture，不将late audit提升为研究资料，不重发unknown。

子提案必须保question/basis、Claim支持／反驳／限定／冲突、来源和Work/Call引用、未知／未读、失败及停止理由；结构准入为machine_admitted_pending_human，非语义真值。关键义务绑定原已接受目标及完成标准，失败后不能改称可选或缩scope。只有事先允许接受未知的探索标准可用有依据的未知满足该义务；否则关键缺口partial，可选失败也在交付中列明。

document_compile前在同根事务seal准确当前研究输入集合：关键义务已答或满足已接受的unknown标准；仍未完成的可选研究停止新调用并列unread/failed。seal后不新建研究assignment、不将新研究结果纳入该集合；迟到只原Call审计／费用。编译send和commit重核seal refs/hash、准确需求head／确认、当前权限和模型资格。新需求head先提交则拒旧方案，终态后不能替换旧Task，以同Case linkedTurn继续且不重置资源。恢复复用稳定Work/Call／已提交输出；unknown全项目停线、终态不替代物理资源收拢。

### 文档版本、确认及首工件义务

原始私人Draft不是生成文档。Case每版DocumentVersion绑定kind(requirements/solution/review)、author、parent、body hash及实际已知来源祖先；人工保存和AI修订只追加，不覆盖首稿／确认稿。当前requirements/solution/review head由Pg拥有。本人显式保存才建版本，键入仅有界UI内存草稿，不localStorage；logout／换身份清除。409或保存失败保编辑可见并明确重载，不静默覆盖／丢稿；重载不是自动合并。

RequirementsConfirmation由当前有权actor显式确认准确当前requirements version/hash，CAS expected_head；保存不等于确认，预选／沉默／超时／模型建议不确认。新requirements head与清除current_confirmation在同一root事务提交，旧确认保历史。确认不扩grant／model用途许可。solution_only可导入既有需求形成受追溯版本并由本人明确确认；full先需求首稿→本人编辑／确认→方案首稿；requirements_only可独立终结。

方案start、最终send_claim、Stage／文档commit均核current_req_head==bound_req_version、current_confirmation==bound_confirmation及其version/hash一致，同时核目标solution parent/head CAS，且继续核Task/lease/fence/generation/权限／profile等原门禁。R1/C1→R2后旧C1不再当前；旧方案stale由引用比较派生，非第二权威flag。R2先提交则旧S1不新发或发布；S1先提交成为历史后R2使其过期。旧在途结果只原Call有许可audit/usage/cost，不新Document/Claim/Stage；不重发completed或unknown。

跨模式仅Case原目的内显式接受条件变化，不重置Turn／Case额度／期限；接受事务先核新增尚缺首工件多维reserve，不足则拒扩或partial保已有产物。实质改目的须另行明确新Case与grant，不能新ID绕全项目unknown／总批次cap。需求改版后再次编译消耗剩余额度，不保证无限首方案。

每Case累计DocumentVersion≤16，正文UTF8≤64KiB、metadata≤16KiB含必要lineage，不截祖先。全部实际envelope计stage-derived 2MiB及Case64MiB；16×80KiB=1.25MiB不是其他stage可无界的保证。首工件在可选人工保存／AI修订／其他stage写入前，仅为尚未进行首次尝试的义务各保留1个正常模型调用、32768输入／8192输出预留、版本槽、每件80KiB envelope及canonical／terminal空间；full保护首次需求和首次方案两件，其他模式一件。首次模型发送即对应调用／Tokenreserve转used一次，失败不返还、不因未产稿自动补满；交付义务未满足不得计成功。保存空间按实际提交／安全结算处理，不把未用字节误计已存正文；未来首方案资源不被可选版本占用。后续仅在合法retry、compile和全部剩余额度均满足时尝试，否则partial。已知无法存结果则零新模型发送，安全partial不借终结预留生成新正文。

完整包ReportSnapshot≤64KiB只放文档版本/hash／需求确认及有界问题摘要，不内联2×64KiB正文；文档分别计版本桶，各Markdown与UI读取准确版本并逐响应核当前权限。不新增ZIP或无限复制大导出。

## 3. Tool Calling、Search与证据

static server registry仅GitHub auth/qualify/resolve/tree/blob、public Search/Fetch、stage model白名单。模型只提出strict工具ID／参数，不能给secret、host、team、grant或任意工具；服务端compile绑定schema/adapter/compiler/request version、Case目的、source/use/model披露rev、credential generation/短期handle、deadline、reservation及actor。Authorization只服务端注入，不进prompt／日志／artifact／checkpoint。direct API优先、SDK隐含retry0、redirect自动跟随0、无多供应商fallback／ambient proxy/cookie/preconnect；连接每次send有当前许可，owned/injected client生命周期明确，close不证明物理quiescence。

| Case累计物理尝试 | 上限 |
| --- | ---: |
| Search | 12 |
| Fetch | 24 |
| GitHub data | 32 |
| GitHub qualification/control | 64 |

失败／retry／签发／probe都计原allocation；Case已知瞬态技术额外retry最多2，每Work最多1，schema／超限／权限／语义／unknown不技术retry。独立控制Task如§2不借研究槽。候选timeout GH data15s/auth10s/Search20s/Fetch30s，受Task剩余和绝对截止约束；Retry-After超过剩余即停。账号本地QPS GH2/Search2/Fetch1，换key不增额度。HTTP结果、内容可用性与billing独立；200空Search可成功，空Fetch／坏schema不usable，可能已发送的timeout／cancel是unknown而非免费。费用不明保预留并沿全项目停外调，不用供应商一般重试建议覆盖本项目规则。

### 选定本地材料及SourceSet

浏览器File API仅本人显式选定普通文本／源码／未提交diff，不提供Windows FS bridge、任意服务端path、目录监听、ZIP或PDF/Word解析；不执行源码／apply diff／自动读diff提到的路径。元数据不是打开路径的权限。File API只证明实际上传bytes，不证明原symlink资格或整worktree原子快照；base commit未知记unknown，user_declared与verified分开。raw bytes/hash与严格UTF8解码表示/hash分别保，不借转换后的hash定位原文。

每Case累计≤32本地items，不随SourceSet／Turn重置；先提交≤16KiB固定item IDs等有界JSON元数据，再逐item raw application/octet-stream。正文以应用stream逐chunk先计实际raw≤1MiB、严格UTF8解码后≤512KiB，拒非identity Content-Encoding；非multipart，不走默认UploadFile/spooling或在有界检查前read全body／JSON/form parser。接收绝对30s。头／请求行／服务端缓冲要有固定配置及未来真实transport资格，不凭应用计数宣称部署已保证。只检查Content-Length不足以资格。

读body前核当前session/rev／sup／Case/project／retain/use并reserve有界空间，网络读取不持DB锁；提交再核当前门禁、SourceSet expected version和实际字节，正文/hash/capture同事务，无许可或失败不留假capture。错误不回显正文；确定未用reserve才释放。SourceSet seal列准确成功captures与失败／未读项，接受输入及ContextManifest绑定准确sealed set revision/hash和capture IDs/hash，新set不覆盖旧set或原Task输入，未seal不入模型，partial集合不冒完整采集。所有实际捕获、解码与安全副本共用GH/Fetch/local的34.5MiB桶／Case64MiB／project1GiB，不保证32项max同时保存，满拒新，不删lineage凑容量。

本地想法／文件无不存在的GitHub App proof要求，但仍核author/project/retain/use/model/share/public-disclosure当前rev及准确bytes；已知GitHub私源及其派生继续原App proof。已知私有祖先不因local profile／新ID／编辑／导出重导入洗白；外部未知出处只能user_provided/provenance_unverified，不声称识别一切手工复制来源。项目合法共享文档不套Memory同作者限制；私人raw Draft仍owner隔离。

### GitHub App与私源资格

上游主体为team App installation＋稳定repo ID，个人GitHub权限变化不自动撤团队App源；本地成员离队即时约束自身Task／读取。App registration/install/key与POST token签发是未来准确操作包另授，配置不执行。只一个主repo、contents read＋metadata；每创建／续最长5min proof，当前App/key向精确installation重新签发限定repo ID／scope的token，安全receipt须证明仓库选择、权限及expiry。缺字段／不符拒proof，不能拿公开metadata／内容200补证；mint unknown／schema不明不自动再签。

proof绑定team/connection/installation/repo ID/key generation/local grant rev/operation/scope/当前签发receipt及独立短期token handle version。正常短期token刷新不冒作配置授权变更；每Call仍绑定实际handle。expiry=min(本周期最早qualification claim＋300s, token expiry)，late commit不延寿。每周期mint＋identity＋contents probe最多3基本请求；64 control硬cap不保证完整60min／8Turn覆盖，耗尽partial。token只受保护服务端内存生命周期，持久化只白名单receipt，不完整签发响应或secret。失proof／清楚deny停私用及派生report读取；不能换credential回退或借公开profile续私有lineage。

GitHub固定api.github.com，固定repo identity/commit/tree/blob/path，不clone／archive／代码执行；tree有界非recursive子树遍历，truncated或响应超限保frontier，不能称全枚举。先mode拒symlink/submodule，防Contents隐式解引用；rename／名称复用／同SHA不同repo不混，connection变更重核。public参考独立无Authorization／cookie／私凭据resolver profile，同GH data cap，不能洗私源来源关系。

### 发现、公开披露与证据链

优先显式路径→明确基准来源→已读文档内部链接→仓库入口／文档名／关键词，平局固定path序；名字／日期不证权威。普通Markdown／文本以外的binary／LFS pointer／坏编码／超限／外仓链接各给未读原因，不越授权主repo。旧路线3／候选池20／短名单3只属旧选型产品，不迁成文档评审规则。QueryPlan／Work保question/purpose/input revision/顺序/披露依据；改写只既有模型槽，无逐工具隐藏模型。

Search count5、need_content=false、ori_question省略；query1–128 Unicode且非空白，分数／snippet／日期仅线索。许可覆盖**最终完整query bytes/hash、词语组合／限定、目的和私有输入祖先**：whole query有可追公开出处且无私有派生，或权利人明确许可该完整query和目的外发；词表／单词分别公开／模型称匿名化不是降密依据。无许可保gap求决策。Fetch仅普通公开HTTPS完整URL，无userinfo或secret／capability参数；私文档里的公开链接也需完整URL披露依据，不静默删query冒充同源，不用页面回显洗private taint。供应商Fetch只title/content，不掌握其内部DNS／redirect或源HTML。

采集、持久保留、模型输入及team展示／导出分别核许可，不能先取／存全文再以导出摘录补救。只有摘录用途时须证明适配器在获准处理范围生成合格片段，不能证明则不可用／许可gap。保留可观察license／来源说明，不将软件LICENSE自动推至外链全文；摘要不扩许可。

SourceCapture不可变：GH repo ID/commit/path/blob；web requested_url及仅可观察provider URL、received_at、representation_kind、完整／部分标识、实际保留safe业务响应／表示hash／转换版本。缺final_url/redirect_chain/origin_fetched_at保持null，接收时间非源站时间。GH严格decode不换行／Unicode归一化；UTF8起止offset和quote绑定该表示hash，行号是派生；blob身份与本地表示hash分别记。Fetch只定位存储Markdown，不写源HTML行号；剔除secret后的safe-derived明确缺失，不能称原HTTP或借旧hash定位已删文字。raw stream／解码／安全序列化各先限后处理，chunk／压缩膨胀／JSON副本均限；单响应／artifact≤1MiB、decoded text≤512KiB，更严阶段cap优先。

ClaimDraft strict包含question/basis refs、subject/assertion、适用版本／时间／范围、capture refs/UTF8locator/quote及support/refute/qualify/conflict。Pg赋归属及ID，核权限／hash／片段／版本／引用闭合后仅machine_admitted_pending_human，非语义已验。Case≤512claim／2048edge，正文≤1KiB/excerpt≤4KiB/edge reason≤512B，实际封装计关系桶，保护遍历到限保frontier。未知版本反证先保待核，不能排名删掉或按README／日期定权威。

同hash可省重复处理但保每源身份／权限／版本及物理Call费用；镜像非独立证实。同名组件、fork／迁移不自动合主体。来源声明“已实现”仅文档事实；观察／推断／建议分开。SourceManifest区分已枚举／frontier、选中／未选、抓取成功／失败／超限／无权及实际进入Context范围，未读不等不存在。不凭有capture声称模型逐字读或内部使用。

交付绑定其准确材料集；有主repo时绑定固定commit，有web时绑定采集时点，无仓库想法不伪造repo身份，未知web版本诚实未知。改条件默认复用commit；明确更新才新source version/实际新义务，不以Turn／ID让completed／unknown重发。无后台监控或发布前隐式收费刷新。两不同目标成功batch无新证据可作为停止理由，不是覆盖完成证明；关键缺口／冲突／预算不足partial。探索交付标准满足时可completed且含事实unknown，不混Call unknown；题目要求完整范围不能暗缩。权限失效走安全已有refs／metadata终结，不用失效私文重新编partial正文。

## 4. Context、Memory与Token

编译顺序：可信模板→完整接受条件／未知→阶段任务→必要证据关系／限定／反证→可选证据。当前没有Memory输入或候选提取阶段。先在有权元数据中展开关系再筛适用，未知版本反证保留；无权正文不进compiler，必要许可或保护内容不足则partial。原文段落保完整范围，不以clip假装完整条件／quote；小材料只有许可和预算允许才直接原文。结构关系＋path/title/keyword不默认vector；中英文同义漏检待开发集验证，零命中不拿开头冒支持。旧summary仅有源派生线索，不成为事实，额外summary0。

Manifest≤64KiB保存Case/Task/Work/input/阶段、template/compiler/selector/schema版本、有界候选快照／查询、选排IDs/hash/范围/理由、实际输入与全部private祖先lineage、Memory disabled/not_applicable与空active refs、source/model用途许可。它不是授权；超manifest cap不静默丢祖先／反证，拒发。诊断区分未取得／未识别／未绑定／未选入／裁剪丢失／摘要失真／请求已含但输出未体现；模型未利用只能作为待证假设，不断言模型内部行为。

当前M1关闭全部Memory功能入口，包括手动／自动、API／CLI、默认profile／框架Store预加载、旧checkpoint refs、导入／恢复／重建与后台路径；不提取候选、不读写、不检索、不注入，active Memory refs必须为空并与各模型阶段实际请求一致。Trace记disabled/not_applicable，hits／writes为null并附feature_disabled，不以测试零次冒充禁用证据，不要求空Store／seed／Memory快照。Case内条件、证据、文档和审计照常持久化；本人明确选定历史报告走SourceSet准确获许可版本，不解引用Memory refs，继续核当前权限和已知私有祖先。DEC-AC-17／DEC-M1-04保留延期、未实施／未验；完整Context属03a、Token资格属03b，当前M1不依赖04。真实复用需求、独立设计审查及准确范围另批后才可重开，原Memory预留容量保持闲置上界，不挪给其他功能。

### 后续Memory候选（当前不生效、未实施／未验）

以下保留旧DRAFT生命周期设计及上界供另批比较，不是当前API、存储、读取或验收义务；当前运行不得预建Store／表、seed／快照或解析旧refs。未来参数不得无复审沿用为已验结论。

Memory仅明确本人长期偏好language_ecosystem/license_preference/deployment_preference/maintenance_preference/cost_preference及合格公开source cue；不扩团队知识／私正文／全文报告。偏好来自本人明确加入当前team/project的原始消息完整长期表达，负偏好可收；否定归属／引用／第三人／网页／模型／敏感或歧义拒收。source cue仅合格report citation的公开locator，无语义真值；含private输入或目标祖先候选首阶段拒自动记，URL公开不能洗白。

Memory scope=author＋team＋project，自动跨Case只同人同teamproject且当前成员/use/model许可有效；私人未加入Draft不入团队，个人偏好不升级team规则，owner全局容量不随项目倍增。当前接受条件优先，单次例外不更改长期偏好，明确更正先停旧。用Pg不新Store／vector，checkpoint和任务事实非长期Memory。

| Memory参数 | 上限 |
| --- | --- |
| cue／preference TTL | 7天／30天，读不续 |
| active／request | owner50；request最多5，封装区≤2KiB |
| 正文／候选提取 | 单条512B；既有clarify最多3；专用提取call0 |
| owner历史 | ID256／revision1024／单ID4rev；正文1MiB／meta1MiB |

两owner正文2MiB，元数据入非Case桶。满拒新改、不覆旧body；更正满先quarantine旧并显示新未保存。偏好lineage=author/team/project/raw_message/完整位置/category；cue lineage=author/team/project/canonical_public_locator_digest，仅规范scheme/IDNAhost/defaultport并去fragment，不改path/query，最多4已核alias保identity及report/capture/hash。新ID仍查tombstone，疑alias隔离，非全网等价检测；本人显式重启才同lineage新rev。逐次读/sendclaim/commit核DB实时时间expiry/state/rev及归属权限，不靠epoch／Store namespace／清扫。停Memory只阻未来自动用，不承诺删除原消息／报告／审计／备份；来源撤权仍阻相关历史访问。restore失连续全隔离，新ID不复活。

### 六用途、共享调用池与首尝试保护

六purpose及提示词职责见[PROMPT_CONTRACTS](PROMPT_CONTRACTS.md)。程序以节点／Work绑定的已接受问题和输出schema决定purpose，模型不能自行选高额度。evidence_review仅有证据依据的问题回答、冲突比较／父子归并，不容纳无问题依据的免费历史压缩或隐藏judge；子提案另需模型时计extract／evidence_review。

| 用途 | 单次完整本地input／显式output上限 |
| --- | ---: |
| clarify | 8192/2048 |
| research_plan | 16384/2048 |
| extract | 32768/4096 |
| evidence_review | 32768/3072 |
| gap_plan | 16384/2048 |
| document_compile | 32768/8192 |

不设各用途固定正常次数；共享正常调用最多14，正常input累计≤360448／output预留≤61440。额外技术retry仅已知瞬时、同Work≤1／Case≤2；unknown、业务schema不合格、权限、语义、超限不技术retry。两最大retry算术上界425984/77824；所有物理调用≤16、累计本地input≤458752／output预留≤81920同时约束，不能把未用宽松cap转成新normal额度。

document_compile最多4次**物理尝试，包含技术retry**；14 normal／16 physical不额外赠送compile次数。尚未首次尝试的首工件按§2保护，full两件、其余模式一件，不再独占四次编译Token。已发送失败仍消耗调用／Token且不补满first reserve；后续语义修订／重出过期方案使用共享剩余额度，不承诺三次／两次修订或成功首稿。人工保存0模型但计版本／存储；linkedTurns／模式／子Work累计，0repair／额外summary／hidden judge，actual usage不返本地槽。

### Token三层资格与供应商结果

受资格请求仅text system/user＋prompt内strict JSON schema，stream=false、thinking.type=disabled、max_tokens显式、response_format=json_object、temperature=0；无native tools／图片／file／prefix续写／自动工具／框架隐藏调用。用户假special-token拼写按普通文本编码。provider user_id为无真实身份含义的服务端team/project隔离值，非授权／零留存证明；cache非业务Memory，准入按miss峰价。

唯一compiler产生安全持久业务JSON bytes/hash及完整公开格式编码输入，Gateway使用同body；凭据仅服务端注入exact handle。三个层次分别保存证据与revision：

1. **local-format**：绑定endpoint/API与公开model映射、compiler/schema、官方converter/template/tokenizer的固定来源和hash、全部字段／options；计算system、所有消息、prompt schema、工具结果及模板控制标记的完整公开格式，非纯正文或HTTP JSON字符数。固定检查并关闭padding/truncation，literal special-token按普通文本处理；只加载获授权本地文件，不默认下载／初始化。官方HF1017固定发布1bae0e1088993b9b82de08f59de5be5a34e42170说明与recipe同prompt format，recipe935817c66f5d6e64838f419692545f06787e485f附带Vision-Exp来源tokenizer仍须按准确资产／版本核适配，不能以文件存在冒充已资格。
2. **hosted-fit**：准确公开model/API映射和固定本地格式／受限字段／请求字节上限／各purpose输入与显式输出O构成工程估计适配，不宣称远端精确计数或零overflow。有限两次既有qualification诊断仅观察样本，不证明所有输入；首次估计fit仍可能溢出并已消耗物理额度／费用，不自动重发。公开context C和计费规则作为资格前提记录，不能从本地HF模型配置推定托管精确窗口。
3. **usage／fees**：供应商usage须合法非负整数（不接受bool），prompt=cache_hit+cache_miss、total=prompt+completion、completion≤显式O，prompt+O≤资格C。reasoning仅completion明细，不重加；不以可见输出重编码证明收费。保持本地count、实际usage、缓存usage、价格／币种／账单／费用／余额分别记录，不将估计冒充实际账单。

固定范围内合法非零actual-local差异只记录原值、版本、方法及解释，其余门禁满足即可Stage提交／后续调用，不学习offset、不设自动容差或扩大上限。explicit context_overflow、prompt+O>C、completion>O、不支持model或**供应商响应协议schema异常**在原root结果事务撤affected hosted-fit revision，阻旧依赖未发送许可及Stage；已claim的原Call照常结算、不变成新Call、不重发。模型**业务输出schema不合格**、stop空白JSON、length或不支持finish_reason不产生usable Stage，但不混同响应协议异常、不因此扩调用。

本地模板／资产／options／字段变化使旧local及绑定fit资格失效；价格／币种／资金证据失效拒新付费准入。缺usage或费用不明沿billingunknown全项目停新外发并保留reserve；已知不可用结果可能收费，不能填零。迟到usage只结算，不恢复资格。重新资格需要准确证据、独立审查和相应操作授权，沿既有剩余诊断allocation，不换profile／Turn／重启领新次数。依赖、资产获取、Tokenizer和真实模型执行仍另授。

费用预留依据公开完整context／输出上界和峰价，保留原2.20元物理槽及全批296.46元条件预算；供应商遵守公开规则／限制／价目是明示假设，不承诺任意供应商故障下绝对封顶。缺乏模型错误一律免费的声明不无限阻塞配置确认；发生不明结果仍按unknown停线，不把它当免费失败。

## 5. 工件、费用、Tracing及评测接口

实际未压缩持久字节先原子reserve→used一次，确定未用才释放；单artifact≤1MiB、Turn／跨Turn Case64MiB、项目新增业务1GiB。副本、请求／响应／派生／quote都计，同artifact引用不重复存。Case总桶：

| 每Case预留 | MiB |
| --- | ---: |
| 16×(req256KiB＋resp512KiB＋manifest64KiB) | 13 |
| Search12×128KiB | 1.5 |
| GH／Fetch／选定本地采集表示、保留响应及副本共享 | 34.5 |
| Claim关系 | 4 |
| stage-derived | 2 |
| 接受原文条件 | 3 |
| tool安全请求 | 1 |
| transport meta | 2 |
| 其余canonical meta | 2 |
| terminal／control receipt及原Memory闲置预留 | 1 |
| 合计 | 64 |

不承诺32GH＋24Fetch＋32本地items各最大可同时保存；满拒新／partial，不能删lineage或audit凑桶。64控制receipt各≤2KiB占0.125MiB；8Turn×(report64KiB＋terminal16KiB)=0.625MiB，余0.25中的原Memory建议容量当前闲置，不重新分配；既有终结必要索引仍受原上界约束。control probe正文若保留入capture桶，不藏receipt；签发只安全白名单无token。canonical及终结预留不足不新claim；确定性partial≤48KiB只引用已有条件／证据／缺口／停止／费，不新推荐。

七Case448MiB＋Draft8＋Memory正文闲置上界2＋四model诊断3.25＋四独立控制Task共1＋非Case安全meta4＝466.25MiB<1GiB。独立控制Task每0.25MiB，安全req/receipt/manifest各≤2KiB，32×6KiB=0.1875MiB，余给终结，过大不借研究Case。metadata32MiB=七Case×4＋非Case3＋安全1；非Case中Memory闲置上界2、backup manifest/catalog0.390625、控制0.125，余0.484375供auth等。Pg/WAL/index/checkpoint/backup物理资格另测，业务算术不证磁盘／RAM够。

全批最高：七research Case=2pilot＋最多2优化复测＋3正式Agent，另4model诊断=qualification2＋health2，独立控制Task最多4×8。model116／Search84／Fetch168／GHdata224＋Casecontrol448＋standalone32=704，HTTP1072；Case HTTP148，无Browser／MCP。DNS最多2144（A/AAAA各计）、dial1072，不隐藏多IP／HappyEyeballs retry，DNSresponse≤4KiB/16地址；供应商内部Fetch不可观察。UI普通event255×1KiB到cap记capped，canonical Call／费用不截、分页50。

费用epoch2026-10-28，已发生归属／旧账／unknown先核，不能洗成新余额。条件预算model116×2.20=255.20，Search84＋Fetch168每次0.005共1.26，介质／纸／Control AI或DR／审计其它30硬桶，buffer10非自动分配，总296.46<300。2.20是原全context峰费保守预留（1048576×2/百万＋8192×8/百万=2.162688），非余额／账单保证。cache不降准入；合法usage及冻结有效CNY价格结算，reserve与spent不双扣，输出只计一次。价格≤24h观察非锁价，实际币种／price／完整账／余额／grant／整批覆盖或API费用依据不成立paid off，未知不填0，不暗充值／购买／桶外藏费。

Tracing用Pg canonical＋只读TraceView，无外部平台或遥测。当前Memory指标记disabled/not_applicable，hits／writes为null＋feature_disabled，不把未运行填成测得零。RunManifest≤64KiB计stage-derived，保codecommit/dirty完整snapshot refs、lock/deps/schema、公开model、模板/selector/compiler/token资格、price/protocol/material/source versions、grantrev与actor；远端weights未知不伪造。报告→question/basis→Claim→UTF8locator/表示hash→capture/Call→ContextManifest→exactsafe request→response/usage→cost/reservation可追，业务refs同tx提交。Trace／audit访问按当前member／用途／适用GitHub私源proof、本地当前用途许可与lineage，admin不自动获私body；敏感metadata也不能任意公开。普通log仅code/ID/count，无原prompt／key／cookie／privategoal／URLnonce／exceptionstr／CoT。offline reconstruct只核已有bytes/hash/关系/selector/slot/time/usage算术，禁network／graph replay／重新Token执行；缺坏／因许可不留正文记not_reconstructible，不编造可重演。

### 评测与材料接口

唯一draft-m1-3定义3pair/6formal：REQ-A/B想法到需求／本人确认／方案完整链；CON-A/B固定GitHub＋本地text/code/diff评审且均含无权威基准子问；EXP-A/B已确认既有需求的solution_only及必要探索。REQ保首次需求、本人改动（可空）与准确确认、首次方案及最终双稿包，原稿两者均须过关键项；CON无基准不能自立硬条件合规pass。三pair两变体材料组合／规模、目标与覆盖可比，澄清不能缩共同goal洗分，实质scope变化保原slot partial/不可比；合理备选架构不得强制唯一gold。requirements_only独立终结及编辑／对话修订只由聚焦回归和既有pilot观察；两个pilot优先本人真实待办，先固定目标、普通AI／人工基线、关键正确项、可接受unknown与后续行动，再分列原稿、人工补救及实际用途，无任务保持待证，不增加Case／费用；仅需求及编辑／对话修订不声称独立正式效果；三个异质pair的median只描述已登记样本，不外推各模式或总体。原始程序、原report核源、本人finalhash分别记。三个正式Agent原稿均过预冻结关键项才产品原始质量通过；人工修好仍保raw失败。六final共质＋完整非零计时后才描述3pairmedian，负值不截0、不设20%硬门槛、不外推真实团队价值。Control预注册日常人工／普通AI／搜索，DR按需计时费；Agent不外部AI代修／复制Control。关键语义人核，非关键逐条不合总分；notstarted／missing／cancel／partial／failed全保分母，指定诚实partial可过安全预期但非fullcompleted。真实价值、本人掌握、M1、Go发布独立。

公开DISCOVERY_M1_CASES.json改为draft-m1-material-index-1，仅公开pair/slot/rubric/status及role包身份，当前pending_independent_material_preparation，本批不制题／gold。未来精确inputs.json／controller.json／scorer.json仅本批既有审计子目录review-20261101/research-20261103/materials，Worker无目录／表权限且无localFS工具；gold不进source／Context／Memory。独立作者制备、另审正文；实现作者见gold即exposed不能继续声称holdout，原slot保留不暗换。索引／协议／M1单向hash绑定，无自引用循环。

默认validator只核公开配置／索引，明确materials未核不formalready。显式成对--review-material-root／--review-material-index-sha256才核三精确包：先原路径各组件lstat／Windows reparse拒链接，再resolve核固定root，不跟manifest任意relative_ref；读取身份／字节一致性不明拒绝。每包raw≤1MiB先限后strict JSON，重复键／非有限／错类型拒，错误仅role＋固定code不回显题文。receipt绑定独立原始审查报告hash／上下文身份／三包bytes/hash／结论限制及受影响复审，不以reviewed=true代审查。缺坏未审identity变化not_ready；结构检查非语义正确或运行授权。

揭题先原子disclosure_committed/reveal_authorized绑定seed/slot/method/actor/promptHash和首次许可时间，不冒充first_display。实际显示ack／本人记录另留客户端时间及clock依据、服务器ack时间；ack非授权，重连重复不重置首次。实际时点不明保earliest_possible_exposure/timing_uncertain，不换slot，不入有效saving，Control同口径。active含读题／澄清／提示／搜源／核源／反馈改稿，wait／wall分列。稿件hash和计时先冻结再揭gold；≤2轮feedback只缺陷类与原report定位，额外研究记贡献／污染。错误gold追加独审amendment保原结果，不偷偷降门槛／换题。

## 6. 出站、环境与连续资格

新独立PG16 cluster目标16.15，实际binary须另验，独立data/凭据/55432/ara_m1+ara_m1_test；旧5433/SQLite只读取证。应用/checkpoint角色无DDL，schema setup另授migration；准确Linux路径/role/同步/服务/凭据属ENV-M1-01操作包。Ubuntu当前Stopped；启动可能运行旧systemd/bootcommand/Worker，无安全隔离证据不能先boot再补防护。冷切关旧准入→核队列/在途/unknown→停止旧API/Worker→旧写凭据失效/处理存活连接→验证不能误写；不默认停旧DB/删原件。回滚停写保留新数据费用权限，回理解当前schema版本，不destructive downgrade。

本机技术验证先本人＋测试身份，不证明真实团队价值；可信本机HTTP origin=http://127.0.0.1:8766；cookie不隔离同host端口，本机恶意服务/OS不在保证，不自动TLS/LAN。Browser真实接入暂缓并保持0。以下Browser连接方案仅保留后续资格研究，不属于当前调用／存储额度；未来开启须另授权和重评资源，仅navigate/wait/scroll/DOM extract，无任意click/input/download/login/个人profile。

Browser namespace全IPv4/6默认DROP仅固定proxy TCP，UDP禁；proxy独立UID/namespace、受控DNS+public80/443。验证全部A/AAAA并numeric IP pin，Host/SNI/上游cert/实际peer核对，无重新DNS旁路。研究mitmproxy12.3.1固定commit51c1d6b2d8d3367a773411eb7a3eeccec82b3ea7，源码/测试/serializer实证未有则Browser0。临时CA仅临时Browser信任，私钥proxy私有，不装系统；lazy/upstream_cert=false，上游验证，HTTP1.1，HTTP2/3/QUIC/WebRTC/UDP/WebSocket/rawtcp/透传及额外addon关。CONNECT不先探上游，GETbody0，拒非0CL/TE/Upgrade/嵌套CONNECT，req头16KiB；剥Cookie/Auth/ProxyAuth/SetCookie。安全URL/Host/header固定hash后claim，不可证明实际序列化一致则关能力。

response identity编码，不支持拒；capture传输4MiB/Case8MiB、头32KiB、连接4、action90s，nav/wait/scroll/extract各≤2，总redirect6/单nav3，后台请求仍归Case，结束seal。GET不保证源站无业务副作用。DOM固定脚本≤10000节点/1MiB、chunk128KiB。Chrome CDP pipe→control namespace bridge，仅可信一WS client nonce256bit+actor UUID；Browser无control路由。frame/buffer2MiB、双向queue4MiB/16消息、pending32、handshake5s/背压1s失败关闭，旧代重连不建新Browser；无pipe兼容实证不TCP回退/改上游。供应商内部Fetch网络不可观察。

父cgroup4GiB/CPU4原候选子预算保留资格研究：Browser1024MiB/proxy256/bridge64/Worker含通用transport1024/Pg1024/API256/sup128/backup256（CPU1），合4032余64；Browser0不代表可自动挪用其内存或开启组件。主机RAM15.63GiB/free2.43是快照非可用保证，失败不脱组。heap/index/WAL/checkpoint/backup另测；max_wal_size不是硬磁盘界。

### B5.2 supervisor

Sup启动无资格，DB OPEN只能收紧。IPC SO_PEERCRED同服务UID/dir0700/socket0600/每boot nonce256bit。持续PG监测连接固定postmaster start/dbOID/deployment/schema；所有app新连接/重连同步核对，不等/读不到先封actor。监测断、PG重启/恢复、sup失联不可逆seal该generation。API/Worker在同连续sup/PG才新actor UUID加入，不复用旧ID。

qualified(owner,credential_rev)只来自本boot明确CLI新凭据operation，不能DB enabled自激活。receipt绑定operation/boot/actor/owner/action/expectedrev/同次随机化Argon verifier指纹和参数版本（禁止原密码快速hash）；sup仅本boot发起、明确commit匹配且连续性仍有效时升草稿资格。新boot不导入receipt。disable DB先提交，逐请求当前rev/epoch/enabled重核不被缓存覆盖；容量满可disable。

认证每请求精确单次claim相对seal线性化，最多4在途；seal先拒，claim先可在途随后DBcommit，不能瞬时撤回。DB根锁仍核账户/owner/revision/容量；IPC/Argon锁外。2s是本地执行截止不是物理COMMIT保证；超时cancel/disconnect，commit不明保operation unknown不成功回报/不换operation重做，同liveboot只读核原receipt不续期。sealed新session不能用于下一请求。

失连续恢复账号全隔离，旧password/cookie/grant无资格；本人另授权CLI轮换新凭据仅草稿读写/历史只读，研究Memory及恢复资料新ID衍生仍关。无独立最新性证明不恢复付费，不建第二业务权威。UUID/相同序号/hashchain/fsync非最新性证明；不自动检测任意superuser同PG在线回灌，运维先seal停写另授。

### BK-r3.2 备份

开发本机有限恢复；首pilot前独立物理介质借优先，采购另授计noncall30。age1.3.2 commit b74dce4cdbe35b5e5f66c06d9612b72f89028758；官方Linuxamd64资产SHA cbe24006683f8eb669266162894b9a522a1af52f2665fbc63a4bb032ed26ac10，仅公开身份核对，未下载/验签/安装。X25519公钥在线，纸钥本人长期离线单独保管；不入prompt/log/argv/repo/介质，地点不公开。恢复短时私钥进可信本机受限临时file/ageRAM，限制core/禁录屏云同步/用后移除，tmpfs不证明无swap/pagefile/崩溃残留，不承诺物理擦除/擅改宿主页。

capture关新研究收拢已有claim（unknown保留），安全撤销仍可；只读REPEATABLE READ export snapshot，manifest root/count同snapshot且事务保持至单库pg_dump结束。custom --compress=none，app/checkpoint同dump，不含roles/tablespaces/环境秘密，新roles/ACL来自批准模板。Linux字节pipe→age，无plaintextdump；plain/cipher各4GiB流式hardcap、O_EXCL0600临时cipher、两producer exit0/fsync/readbackSHA/同FSrename+dirfsync才capture_verified，独立copy读回才副本完成。

每independent source_bound须本人从可信capture输出独立纸卡核captureID/project/version+完整cipherSHA+manifestbytesSHA，介质旁manifest不自认证；不当撤销最新见证。manifest原bytes≤4KiB/catalog≤1KiB、最多80份，共0.390625MiB计非Casemeta，满停newcapture/research。自动capture不称restore_verified；首pilot前/交付前最新份从纸重录key（不用生成缓存）完整恢复。

restore先纸卡双hash全读匹配→parsemanifest→age全流至null认证末尾→固定同cipher二次pipe pg_restore --no-owner --no-acl --exit-on-error --single-transaction；禁--create/--clean/--no-sync/原库fallback/superuser。dump custom侧no-owner不能替代restore侧。精确quarantine新DB撤PUBLIC CONNECT，仅restorerole，API/Worker不连；两进程退出/上限/schema/root/report→claim→source全过再按隔离规则考虑草稿。第二遍失败目标仍隔离，旧库零写，不保证目标零SQL；原root先验，后隔离/凭据改动为新派生state。

保3good+1新，介质分配18GiB/新增前free6GiB/写中<2GiB停，确认new后仅另授权限定backupset精确ID/path/hash轮换，不清目录。capture30min/decrypt验证30min/restore60min/dump锁5s，到期停管线/关snapshot/目标隔离。restore初free12GiB/<4GiB停是门槛非物理硬上界，峰值不合不资格。原SQLite/r12/授权/费用/上游不在清理范围。

## 7. FIRST-r2首工与验收

DEC-M1-01：真实登录→保存未接受原文草稿→重开→第二测试身份404，加最小认证sup；无InputRevision/Task/研究event/调用，不导旧Settings/SQLite/Provider/Tokenizer/Browser。product_main在127.0.0.1:8766挂build后Vue，不用Vite代理8000，API无SPA fallback。schema project_control/account/auth_session/pre_session/auth_rate/draft/admin_receipt，独立product migration；普通启动不DDL。

POST auth/bootstrap {}精确Host/Origin/json，pre session+CSRF TTL5min/128；POST login {username,password}消费pre/旋转cookie及CSRF；GET session只读owner公开标签/expiry/CSRF no-store；POST touch/logout CSRF。username ASCII [a-z][a-z0-9_-]{2,31}/最多2身份；password15–128codepoint且UTF8≤512B；Argon2id19MiB/t2/p1/salt16/hash32，目标argon2-cffi25.1.0另授权安装且只必要锁联动。session随机256bit、仅sidhash SHA256入库，HttpOnly/SameSiteStrict/host-only/Path=/，HTTP不冒用__Host；abs8h/idle30min/每owner3active，第四429不驱逐，总16行/owner只GCexpired/revoked。GET不touch，人交互POST有限续idle；wronguser dummyhash/generic401，hash并发2/account5每15min/global10每min/ratekeys128；bootstrap source10/global30每min，满拒。

Draft POST {text}+Idempotency-Key，owner从session，同key/initialbodyhash返稳定{id}201、异body409；createkey随20draft保留。GET list id/rev/time分页50，detail原文；PUT {expected_revision,text} CAS，409人工reload不静默覆盖。login wire4KiB，draft wire128KiB/body UTF8 16KiB先raw限后JSON；拒NUL/孤立surrogate，保留CR/LF/tab/空白/emoji，HTML惰性。currentrevision不无限历史；logout/换owner清cache及未保存稿，不localStorage。安全4xx仅code/白名单field，不回显密码/verifier/CSRF/cookie/rawdraft或validation input。

真实验收：两CLI账号/cookiejar、restrictedPg、独立连接barriers reset-login/disable-write/19draft双create/会话limit；新进程import前sentinel阻旧env/模型/网络；rawchunk/CL/JSONescape/UTF8±1；APIrestart保稿；sup/PG失连续旧password/cookie均拒，CLI新凭据仅草稿；DBdown不报注销/撤销成功。missingPg/skip不通过。本人Windows UI亲验、读入口→auth→application→store、预测失败/亲改回归；不代填掌握。文件/命令/ENV前置见[首工任务包](../features/DECISION-001/tasks.md)。

真实pilot还须历史账/unknown/余额/grant/价格/Tokenizer/Gateway/独立介质纸钥恢复资格，Browser未资格0。M1仍需真实纠正症状、三个正式Agent原稿关键质量、六正式全保留、最终共同质量及本人实践；描述性省时无20%硬门槛，真实价值独立待证。公开纵切不等完整首阶段/M1；Go/发布各自授权。配置自检、实际文件独立审查、业务实现、本人验收分别记录。

DRAFT-BASELINE-20261102的28配置按draft-20261102/snapshots/final-01的manifest/path/raw hash有效，FOCUS不重绑定旧索引。REVIEW-BASELINE-20261101的28配置与原交付按既有final-02 manifest/path/raw hash保留，不冒充HEAD对象；后续合法获批改动不会反向否定旧字节。新增业务API路径／DDL／transport部署资格在另授业务包冻结，本批不实施。
