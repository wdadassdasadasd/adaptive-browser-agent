# 现行目标契约 — PREP-BASELINE-20261029

2026-10-29负责人以“PLEASE IMPLEMENT THIS PLAN”批准40文件配置及限定校验兼容批次。本页为获批设计，业务尚未实现。产品见[SPEC](../../SPEC.md)，依赖见[PLANS](../../PLANS.md)，批准、唯一18项清单和实际检查见[连续记录](../features/DECISION-001/tasks.md)。[discovery-m1-1](../evaluation/CURRENT_EVAL_PROTOCOL.json)是唯一现行评测协议，[M1材料](../evaluation/DECISION_M1_PROTOCOL.json)只引用它，不另设资金或Go规则。历史行为按[V1契约](V1_CONTRACTS.md)、[P-01验收](../tasks/P01_ACCEPTANCE_2026-10-21.md)及原版本解释。旧协议按固定Git commit/path/原字节SHA读取，不复制新归档、不扩旧账。配置批准不授权业务、依赖安装、环境/DB、真实模型/Tokenizer/Browser、购买、外部或Git写；r12/P-02/新产品No-Go保持。

## 1. 输入、对象与API

从无候选需求开始：澄清并接受条件/未知/范围→路线→候选发现→有限短名单深查→证据结论和下一步验证。首需求只预置“居家老人陪伴问答”；旧题的语言/角色/本地化/候选不是硬条件。交付止于调研核源和验证方案，不实施语音集成或效果测试。已接受范围内自主推进；重大方向/范围/费用冲突保存进度、partial结束，答复后建关联新轮。

| 对象 | 权威、关系与约束 |
| --- | --- |
| Draft/RawMessage | 草稿可修；原始消息及出处不可变；均不等于已接受条件 |
| Session | owner/version/active_task；同会话最多一个非终态Task |
| ResearchCase | 首次澄清模型调用前建立，固定owner/session、root_objective_artifact/hash、purpose_id、allocation_id和累计额度/原截止 |
| InputRevision | 本人接受目标/条件/偏好/未知/范围的不可变版本，保留原消息位置和接受出处 |
| Turn/Task | 同一执行对象，唯一status，不维护两份可独立改变的状态 |
| ExecutionAttempt | 持久UUID、fence、租约、恢复计数；不是新Turn |
| PlanRevision/Obligation | 应用稳定义务ID、前驱/替代关系；plan ordinal/query/hash不生成绕过失败的新身份 |
| StageOutput | work/input_version/output_schema唯一，保存已提交输出引用 |
| CallAttempt | 每物理尝试ID、请求version/安全bytes/hash、许可、slot/generation、结果/usage/费用 |
| SourceCapture/Claim/ReportSnapshot | 不可变表示、有主体/适用范围/证据关系的主张、绑定条件与引用的不可变报告 |
| Checkpoint | 仅可序列化ID/计划版本/已提交引用，不决定事实、授权、费用、终态 |

应用Pg唯一业务权威。checkpointer独立schema/角色/连接/事务；不能假定psycopg与应用SQLAlchemy/asyncpg原子提交。普通启动只验环境/依赖/DB/schema身份，setup属另授权迁移。

owner由服务端会话取得；列表/详情/游标/事件/工件均先授权。跨owner与不存在对象404；未认证401；CAS/幂等409；排队/容量429；资格/DB不可用503。错误仅有界code及白名单字段名，不回显请求、Pydantic input/ctx或任意exception。

| API | 最小输入/结果 |
| --- | --- |
| POST/GET /api/sessions | 创建及分页50读取；GET不推进业务/续认证 |
| POST /api/sessions/{id}/messages | 原文和出处，返回ID，不自动接受 |
| POST /api/sessions/{id}/cases | raw_message_id、expected_session_version、allocation_id；缺grant可保存Case，不出站 |
| POST /api/cases/{id}/discussions | 固定Case额度内澄清；proposal/hash/问题，input_revision_id=null、acceptance_state=unaccepted |
| POST /api/sessions/{id}/accept-runs | case_id、predecessor_turn_id或null、proposal_id/hash、expected_session_version、Idempotency-Key |
| GET Task/report/event/source/claim/artifact；POST cancel | 同owner对象链；事件分页；报告发布不覆盖，取消有在途边界 |

同owner/session/key+规范化body先幂等重放后CAS，异body409；接受时核case/parent/proposal绑定，InputRevision+Task+active+event+Session version同事务，拒绝不留孤立对象。运行中改条件先结束活动Turn。grant绑定owner/Case/原目的/阶段/工具/代码模型价格/金额/时间及input_binding_policy：clarify_original_messages或owner_accepted_case_revisions。接受新revision不扩权；ID无法证明语义未扩范围，重大冲突问本人；新Case不自动新allocation。

## 2. 图、状态、锁与发送

澄清子图load_unaccepted→clarify→validate_proposal→publish_proposal。研究图load_accepted→route_plan→discover→collect→extract→identity_and_gaps→coverage_stop→bounded_gap_plan或report_compile/model→validate_publish。每节点输入当前Case/owner/revision及已提交引用、输出strict StageOutput；网页/模型不能写owner/grant/accepted。必须真实阶段节点，不包装整个旧AgentLoop。只并行独立只读取证，稳定ID归并。

| 资源/时间 | 上限 |
| --- | --- |
| 调度 | 全局活动2、排队4，包含澄清/讨论/研究；Session非终态1；Case累计Task8 |
| 分支/调用槽 | Turn取证2/全局4；model物理在途2；Browser资格后1否则0，不保证供应商远端并发 |
| 租约/恢复 | 30秒/心跳5秒；同Task最多恢复1次，原截止与累计额度不变 |
| 截止 | 排队5分钟/讨论10分钟/研究45分钟，受Case剩余额度约束；Case Worker累计60分钟，普通墙钟7天/正式24小时 |
| 时间累计 | 首claim至终态含失租/恢复，同Task一次不叠加分支；终态后等本人不计Worker时间 |
| DB事务 | READ COMMITTED、clock_timestamp实时时间；锁等待1秒/statement timeout2秒，最多两次纯DB重试不包网络 |

Task queued→running→recovering→running或completed/partial/failed/cancelled；await_user为terminal partial并释放调度槽。recovering留活动槽不回普通队列。Attempt active→fenced→resources_quiesced→closed；旧代出口阻断/实际资源终止确认后新Attempt，不能确认保物理槽并停能力，可只释放终态Task调度槽。

所有应用写者含CLI/心跳/reaper/终态/迟到结算先锁ProjectControl，再owner→auth_session→Session→Case→Task→Work→Call→Memory→budget/capacity→slot，同类ID排序，最后追加artifact/claim/event。FK RESTRICT、归属键不可变，避免cascade/循环延迟约束隐含逆序。checkpoint不回调该锁序；迁移另授停写。网络/Argon/Tokenizer/关系遍历不在锁内。提交不明按operation核对，不猜成功。

Call prepared→admitted（仅预留）→send_claimed（最终发送线性点）→completed/known_failed/unknown。claim根锁事务重核项目gate OPEN/authority epoch、owner/Task/原截止、实时租约/fence、request version/精确安全bytes/hash、逐项Memory rev/state/expiry、grant rev/state/owner/Case/phase/input策略/expiry、reservation原身份未耗/未撤销、slot及实际actor generation。unknown关闸与claim同根串行化。网络在事务外。

| 切点/竞争 | 行为 |
| --- | --- |
| cancel/revoke先提交 | claim拒绝 |
| claim先提交 | 已在途，不能保证物理撤回 |
| claim后网络前崩溃且不能证明未发 | unknown，不凭内存重发 |
| completed响应已持久、stage未提交 | 只从hash合格安全响应本地重处理；缺失/坏工件partial保费用 |
| stage已提交、checkpoint落后 | 复用输出不外调 |
| checkpoint引用缺失/版本不符 | 拒绝伪恢复 |
| invalid schema | 结束受影响路径/确定性partial，不回Planner改名绕repair=0 |
| 失租迟到 | 不写新事实/stage，仅原Call幂等费用结算一次，不改报告/不开闸 |

终态根锁协调：已终态返回；取消先提交则cancelled；截止/额度耗尽partial；unknown/fenced partial；否则有效Attempt及合格报告才completed，无可用结果failed。成功先提交后取消返回completed。报告/唯一终态event/active释放/version同事务；DB失联不称已持久终态。

unknown全项目停新外调，换plan/query/Work/Turn不能解锁。保两轮进度、预留及Call身份，读取/cancel/revoke/确定性partial仍可；本人对账后另授恢复，迟到结算不开gate。supervisor先seal旧generation所有出口/既有连接，再终止实际transport资源组（含Browser/代理/后台请求）并确认空，最后slot_id+不复用UUID generation幂等释放。Task终态不释放在途物理槽；本地断连不证明供应商停止/不计费。

## 3. Search/RAG/工具/证据

直接API优先、DeepSeek单一Search/Fetch可替换适配器，无自动双供应商回退。MCP保留研究非M1真实集成交付。strict请求白名单、SDK隐式重试0；技术重试仅已知瞬态，每Work≤1/Case≤2且计原物理槽，unknown/schema不技术重试。每DNS/dial/HTTP发送需当前sup单次许可，无隐藏内部模型或免费重试。

| 阶段 | Search | Fetch | GitHub |
| --- | ---: | ---: | ---: |
| discovery | 6 | 6 | 2 |
| shortlist deep | 3 | 12 | 4 |
| gap | 3 | 6 | 2 |
| Case合计含失败/重试 | 12 | 24 | 8 |

路线3/候选池20/短名单3，同候选跨route只占1深查槽。Search count=5、need_content=false；摘要/日期/authority/rerank_score仅供应商线索。Query含Case/input revision/route/work/目标条件/目的/顺序；route/gap既有模型槽生成计划，不逐工具加调用。未用预留仅向后转；初始候选4 Fetch按身份→硬条件→限制反证→版本费用等目标，不假设四页够。

应用UUID主体；精确仓库稳定ID或有源官网↔仓库关系且范围一致才能归并。同名/fork/迁移/同正文仅建议，content hash去重不合并主体，保各capture出处。每pool项筛查为hard_excluded/identity_duplicate_verified/retained_shortlist/not_deeply_investigated，带source/claim依据。

路线轮转后按身份已核、已支持硬条件数降序、未解决定性条件数升序（无claim也计未解）、独立官方来源数降序封顶3、发现序/UUID排序；有源硬失败后置。排序只分资源不证明可信或事实排除。gap顺序为硬条件缺口→已识别反证适用性→冲突→决定性偏好，条件序/source ID稳定打破平局。

SourceCapture为requested_url、可观察provider URL、representation_kind/received_at、主体版本依据/完整部分标识/artifact hash/转换版本。Fetch title/content无final_url/redirect_chain/origin_fetched_at时保持null，received_at不冒充源站时间；DOM不冒充原HTML。保存可重处理白名单业务响应，剔除/转换标safe-derived，不能称完整原HTTP。raw stream/解码/安全序列化分别先限后处理，覆盖chunk/压缩膨胀/JSON表示，不能先全读再截字符。

ClaimDraft strict：candidate/capture refs、主张、版本/地域/时间、条件refs、表示UTF8字节locator、support/refute/qualify/conflict。owner/Case/ID应用赋值；核归属/hash/片段/版本，machine_admitted_pending_human，子串不证明语义。Case claim≤512/edge≤2048；claim正文≤1KiB、excerpt≤4KiB、edge reason≤512B，实际封装也计关系4MiB桶，不截短冒充完整。

有效增量仅新路线/正式身份、决定性条件合格证据、适用限定/反证/实质冲突；镜像/换措辞不计。successful_batch至少一实际调用且全部尝试有界可解析schema成功；200空Search可成功，空Fetch/坏/超限/混失败/跳过/未准入不算。连续两个不同目标成功batch无增量可停，决定性缺口仍partial。

范围内推荐要求route成功调查或有源排除，推荐者全硬条件和关键主张有源且无未决决定性反证/冲突，未深查/溢出可见。qualified_no_winner/coverage_complete还须全部已发现决定性替代有源处理；不能3个失败忽略其余17。题目要求全池比较时不能改名有限范围算通过。保护遍历512节点/2048边到限保frontier+partial，未知版本反证不能先过滤。

## 4. Context/Memory/Token

编译：可信模板→完整接受条件/未知→阶段任务→关系保护证据→可选证据→可选记忆。展开关系先于适用筛选，保护条件/限定/最低证据不字符截断，装不下拒发partial。Manifest为有界候选视图/查询选择器版本/快照/实际选排理由/模板请求身份，不枚举全历史。诊断区分未采集/未识别/未绑定/未选入/被裁剪/摘要失真/输出未体现，不能断言模型内部未使用。

自动Memory仅可重核来源线索及本人明确长期技术偏好。偏好仅当前本人原始消息完整表达、长期意图、原文位置与有限类别language_ecosystem/license_preference/deployment_preference/maintenance_preference/cost_preference；网页/模型/引用/第三人/假设/敏感/归属歧义拒收。明确负向偏好可收，否定长期归属不误收；保守漏收/结构化本人录入可行。记忆仅可见建议，不成为硬条件/付费/工具/网络授权。

| Memory参数 | 上限 |
| --- | --- |
| 来源线索/偏好TTL | 7天/30天，读不续 |
| active/request | owner50；request最多5且序列化区≤2KiB |
| 正文/提取 | 单条512B，既有clarify最多3候选，专门提取call0 |
| owner历史 | ID256/总revision1024/单ID4revision，正文1MiB、元数据1MiB |

两owner正文共2MiB；Memory元数据计非Case3MiB子桶。满拒新/新revision不覆盖旧body；撤销/停用/冲突隔离更新预留固定state/epoch。明确更正因容量拒收时旧项仍先quarantine，UI“更正未保存，旧项已停用”。附带memory坏字段可丢弃，整体JSON坏则整体失败0repair。

偏好lineage=owner/raw_message/完整表达位置/category；source_hint由owner合格报告machine-admitted citation生成，只是locator不继承语义真值。cue lineage=owner+canonical_public_locator_digest，仅规范scheme/IDNAhost/defaultport/去fragment，不改path/query；≤4已验证alias、可取得主体identity、原report/capture/hash。新report/capture/memory ID仍查lineage/tombstone，同页面或known alias撤销拒自动注入；疑似alias无法证实quarantine，不承诺检测全网语义等价。本人显式重启形成同lineage新revision而非自动复活。超长完整拒收。

读取/最终claim逐项核owner/revision/state/DB实时expiry，不能仅epoch。撤销阻未最终claim、迟到写和重放；恢复数据衍生新ID也不解隔离。撤销仅停止未来自动用，保有界历史，不承诺原消息/报告/审计/备份物理删除。

| 模型阶段 | 正常义务数 | 单次input/output |
| --- | ---: | ---: |
| clarify | 2 | 8192/2048 |
| route_plan | 2 | 16384/2048 |
| discovery_extract | 2 | 32768/4096 |
| shortlist_analysis | 3 | 32768/3072 |
| gap_plan | 1 | 16384/2048 |
| gap_extract | 2 | 32768/3072 |
| report | 2 | 32768/8192 |

14次正常360448/50176；两最大技术重试后425984/66560。Case物理≤16、本地完整请求累计input≤458752/output预留≤73728；两报告独占合计65536/16384，不挪用。所有linked Turns累计，改条件验证同Case A→R1→接受B关联新Turn→R2，不重置。Providerusage不返还调用/本地Token槽。

Provider/Planner等额外格式修复0、额外模型摘要0；thinking显式disabled/max output显式。官方Tokenizer匹配完整协议请求/模型模板才正式准入，缺失/失败/不支持字段/漂移停发；首次资格有限单独另授诊断，不循环前置。请求先存安全业务bytes/hash，Gateway同body发送，变更撤销旧未发送许可并新version；Authorization另加不入artifact。响应白名单content/usage/finish_reason/身份，安全派生不称原HTTP；不采隐藏思维链，reasoning已含completion不重复加，usage缺则未知。计数/usage/cache/计价/余额分账。

## 5. 工件、费用和Tracing

单artifact1MiB/Turn64MiB/跨Turn共享Case64MiB/项目新增1GiB，均未压缩实际持久字节。请求/响应/派生/JSON副本/quote全部计数，同artifact引用不双存。接收/创建前原子reserve→used一次，确定未用才释放，不自动删除历史证据。

| 每Case预留 | MiB |
| --- | ---: |
| 16×(req256KiB+resp512KiB+manifest64KiB) | 13 |
| Search12×128KiB+Fetch24×1MiB+GH8×256KiB | 27.5 |
| DOM2×1MiB | 2 |
| 原文条件3/tool请求1/关系4/stage-derived2/transport meta2 | 12 |
| terminal/Memory建议/控制 | 1 |
| meta总4，transport2已计，只另加2 | 2 |
| 合计 | 57.5 |

7执行allocation预留402.5MiB，另草稿8/Memory正文2/诊断4×0.8125/非Case安全meta4=419.75MiB。Case记录≤16不等16执行allocation。项目meta32MiB=7×4+非Case3+安全1；Memory meta2+backup manifest/catalog0.390625后余0.609375MiB供auth/control，实际计满拒新。完整副本不能免费。

HTTP≤300=16model+44API+240Browser，DNS≤600（A/AAAA分算）、dial≤300，transport≤1200×1536B，DNSresponse≤4KiB/16地址；无隐藏自动DNS/多IP/HappyEyeballs retry。长URL放artifact/ref。UI普通event255×1KiB，达cap记trace_events_capped，canonical Call/费用仍完整分页；8Task×(report64KiB+terminal16KiB)=640KiB已在终态1MiB内。确定性partial≤48KiB，直接取已提交条件引用/证据冲突/缺口/停止/费用，不新推荐；完整条件ID/hash保留，不截短伪完整。

成本epoch为10月28日本次重评开始；本人称仓库外无新增，旧账/仓库未知不填0。条件最坏：qual2+health2=8.80元；early4 Case=141.52；formal3=106.14；介质/纸耗/新增DR等30；不可自动分配buffer10，总296.46<300。model116/Search84/Fetch168/GH56，工具最坏1.26；每model2.20按公开CNY峰2/8每百万与1048576input+8192output得2.162688保守预留，不是资金到账/线上硬账单保证。实际币种/价格/公开model/余额/grant/历史unknown及整批覆盖不成立则paid off。价格观察≤24h不是锁价，新增收费不藏桶外。

Tracing为Pg canonical记录+只读TraceView，不加外部平台或上传。RunManifest≤64KiB计stage-derived桶，绑定codecommit/dirty身份、lock/deps/schema、模板/selector/query策略、Tokenizer、公开model/价格/协议/材料hash，cloudweights/fingerprint不明记unknown。work有界metadata存parent/link/Attempt/revision/input-outputrefs/DB时间状态；异步Turn关联case/parent，不假单进程stack。canonical审计refs与业务同tx，checkpoint非审计权威，无审计容量不新外调。

报告→Claim→UTF8locator→表示hash→capture→Call→ContextManifest选排→安全request→response/usage/cost可追。owner404/分页50，导出默认关另授，日志仅code/ID/计数，不原prompt/body/cookie/key/URLnonce/exceptionstr。hash证明安全对象不证明原网页/完整HTTP/语义真值，不宣称识别所有敏感自然语言。offline reconstruct只读完整性/关系/selector/citation，缺坏not_reconstructible，network/provider禁用；框架replay会再执行外调，不能直接作为审计重放。

## 6. 出站、环境与连续资格

新独立PG16 cluster目标16.15，实际binary须另验，独立data/凭据/55432/ara_m1+ara_m1_test；旧5433/SQLite只读取证。应用/checkpoint角色无DDL，schema setup另授migration；准确Linux路径/role/同步/服务/凭据属ENV-M1-01操作包。Ubuntu当前Stopped；启动可能运行旧systemd/bootcommand/Worker，无安全隔离证据不能先boot再补防护。冷切关旧准入→核队列/在途/unknown→停止旧API/Worker→旧写凭据失效/处理存活连接→验证不能误写；不默认停旧DB/删原件。回滚停写保留新数据费用权限，回理解当前schema版本，不destructive downgrade。

单真实本人+第二测试身份；可信本机HTTP origin=http://127.0.0.1:8766；cookie不隔离同host端口，本机恶意服务/OS不在保证，不自动TLS/LAN。Browser仅navigate/wait/scroll/DOM extract，URL受控，无任意click/input/download/login/个人profile。

Browser namespace全IPv4/6默认DROP仅固定proxy TCP，UDP禁；proxy独立UID/namespace、受控DNS+public80/443。验证全部A/AAAA并numeric IP pin，Host/SNI/上游cert/实际peer核对，无重新DNS旁路。研究mitmproxy12.3.1固定commit51c1d6b2d8d3367a773411eb7a3eeccec82b3ea7，源码/测试/serializer实证未有则Browser0。临时CA仅临时Browser信任，私钥proxy私有，不装系统；lazy/upstream_cert=false，上游验证，HTTP1.1，HTTP2/3/QUIC/WebRTC/UDP/WebSocket/rawtcp/透传及额外addon关。CONNECT不先探上游，GETbody0，拒非0CL/TE/Upgrade/嵌套CONNECT，req头16KiB；剥Cookie/Auth/ProxyAuth/SetCookie。安全URL/Host/header固定hash后claim，不可证明实际序列化一致则关能力。

response identity编码，不支持拒；capture传输4MiB/Case8MiB、头32KiB、连接4、action90s，nav/wait/scroll/extract各≤2，总redirect6/单nav3，后台请求仍归Case，结束seal。GET不保证源站无业务副作用。DOM固定脚本≤10000节点/1MiB、chunk128KiB。Chrome CDP pipe→control namespace bridge，仅可信一WS client nonce256bit+actor UUID；Browser无control路由。frame/buffer2MiB、双向queue4MiB/16消息、pending32、handshake5s/背压1s失败关闭，旧代重连不建新Browser；无pipe兼容实证不TCP回退/改上游。供应商内部Fetch网络不可观察。

父cgroup4GiB/CPU4：Browser1024MiB/proxy256/bridge64/Worker含通用transport1024/Pg1024/API256/sup128/backup256（CPU1），合4032余64。主机RAM15.63GiB/free2.43是快照非可用保证，失败不脱组。heap/index/WAL/checkpoint/backup另测；max_wal_size不是硬磁盘界。

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

真实pilot还须历史账/unknown/余额/grant/价格/Tokenizer/Gateway/独立介质纸钥恢复资格，Browser未资格0。M1需真实纠正症状、六正式全保留、共同质量/本人价值/实践；Go/发布各自授权。配置自检、实际文件独立审查、业务实现、本人验收分别记录。
