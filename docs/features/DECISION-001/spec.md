# DECISION-001：需求与方案研究起草及证据评审

**DEV-STAGES-20261104-01：负责人确认六阶段26切片并明确要求PLEASE IMPLEMENT THIS PLAN，当前仅实施准备切片P0。** 旧TEAM/R2等批准保原字节/范围。[唯一记录](tasks.md)保原18项及本轮实施/检查/独审/人工验收状态；[SPEC](../../../SPEC.md)、[PLANS](../../../PLANS.md)、[契约](../../contracts/CURRENT_CONTRACTS.md)、[唯一协议](../../evaluation/CURRENT_EVAL_PROTOCOL.json)各守原权威。r12/P-02 No-Go保留。

## 用户问题与交付

面向团队研发，首版限定本机最多两个身份、共享项目与人工交接，无管理后台／实时共编／远程接入，真实团队和具体任务仍待找。支持review_only、requirements_only、solution_only、requirements_to_solution。想法无仓库可用；材料限一个主GitHub固定版本、许可公开证据和本人选定本地text／源码／diff。源码只读不执行，diff不应用；原始私人Draft与不可变生成文档分开。发起者编辑／对话修订需求，项目指定当前确认人明确确认准确版本，再由发起者显式接续方案；两角色可同一身份。仅需求可独立结束，仅方案须当前准确确认。UI及各Markdown准确绑定同一版本。

需求稿说明问题／用户／目标／范围／流程／AC／依据／假设／待决；工程方案说明架构数据流／模块接口数据／正常失败／权限费用恢复／取舍验证。评审无权威基准只观察／假设；起草可提建议但不能自升已接受条件。案例B已选固定GPT Researcher3582a6841fe7dc801e2a34e34ee408641aea9bce已有研究／报告编辑／持久聊天到需求编辑／准确确认／绑定方案，作为开发材料／后续另授pilot；实际用途价值待证，不自动成为正式题／gold，不自动批准／改仓库／运行系统。

采集／保留／模型／分享／完整Search query与Fetch URL用途分别许可，派生继承私有输入祖先。退出读会话不取消独立执行Task；来源／成员撤销收紧新调用、新提交和当前读取。详细竞争、schema与数值以契约为准。

## DEC-AC-08–20：当前验收契约

以下均为待实现/待验行为。六阶段工程验收需要08–15、18及19的工程Trace部分；16、20及19的formal/质量/计时部分由负责人按需显式启动，未执行记未评测，不阻工程验收。17延期，禁用机制仍须工程验证。发现的真实缺陷仍处理；假数据不冒真实成功，掌握由本人确认。

| ID | 可观察通过条件 | 必须保留的失败／竞争证据；任务 |
| --- | --- | --- |
| DEC-AC-08 | 四模式和目标有原消息出处，基准／未知／范围可澄清；接受才有InputRevision；仅方案绑定项目当前确认人准确确认；依据三分 | 私Draft不自动入team，网页／模型／Memory不改硬条件；无基准可探索，无确认人可需求／评审而不可方案；02 |
| DEC-AC-09 | 同发起者／Session／key／正文先重放后CAS，接受revision／Task／active／event／version原子提交 | 异body409；需求head及确认策略／账户／成员资格与方案start/send/commit双序，失效不复活；满额／DB失败无孤立对象；控制Task无研究许可；02 |
| DEC-AC-10 | 无仓库想法或单主仓库固定版本，有界关键文档及选定本地text／code／diff，public按需补证 | 本地逐stream实际计数／严格解码／30s／核权reserve和commit；未seal不入模型，未知diff基点非commit；截断／未读／失败非覆盖；Browser0；03a/03b |
| DEC-AC-11 | 实质主张有主体／适用版本／范围、capture表示hash及UTF-8引用；摘要非原文 | 子串不证语义，反证／限定／未知版本保留；新capture不覆盖，改条件默认同commit；03a/03b，当前不依赖04 |
| DEC-AC-12 | 需求／方案／评审不可变版本含依据／假设／验证；编辑显式保存与对话修订，UI／各Markdown同hash，完整包保双稿及确认refs | 未读非不存在，文档声明非已运行；关键不足partial，探索可有事实unknown；16版本及首工件compile/slot/bytes多维预留，已知无容量零发；repair／summary0；02/03 |
| DEC-AC-13 | 所有Call含签发／probe／retry逐次准入预留，精确请求与资格绑定，Token／usage／费用分账 | prepared／admitted非发送；unknown停全项目外调；schema／unknown不技术重试；未知不填0；03b |
| DEC-AC-14 | send与commit核实时租约／fence／执行代次／权限／资格；终态／active／event原子；checkpoint只refs | cancel／success、lease／commit双序，late只原Callaudit／费用；completed不重发，资源确认才释放；02/03b，Memory禁用／空refs |
| DEC-AC-15 | 真认证、私人Draft／项目共享分开；member／source／Taskgrant及读取claim可验；CLI管理项目唯一确认人，发起者编辑／确认人确认；新cluster／sup | logout／expiry后SSE不续读；每response／page／frame重核；换人／离队／禁用及满额撤确认后仍可独立禁用／撤成员／清策略；有界在途非瞬时召回；01/02/ENV/08 |
| DEC-AC-16（按需效果） | draft-m1-3的REQ双首稿／CON原评审／EXP原方案各过关键项；六final交付包共质且计时完整后才描述已登记三pair省时 | 无20%硬门槛，非关键逐条不合总分；缺／0baseline不挑pair；未启动／取消／缺失均保分母；07 |
| DEC-AC-17（延期，非当前M1必需） | 未来跨Case自动Memory候选，未实施／未验，不算pass | 当前所有Memory入口关闭且实际请求无注入；不建空Store／seed；真实复用需求、独立设计审查及准确范围另批才重开04；原容量不挪用 |
| DEC-AC-18 | 完整条件／未知、必要证据／反证先保护；Manifest解释选排；完整公开格式本地计数／hosted-fit／实际usage三层证据 | 缺许可／超限拒发partial；合法计数差异只记录，溢出／供应商协议错root撤affected资格，业务输出错不混同；不推测内部使用；03a/03b；当前不依赖04 |
| DEC-AC-19 | 工程必需：canonical/usage/费用及既有记录可重建；按需效果：原程序/原稿核源/本人finalhash、六槽同版、gold与active/wait计时 | 工程审计不偷偷供研究；formal启动后许可非实际显示、不明时点不算saving；03b/08b工程，06/07按需效果 |
| DEC-AC-20（按需效果） | 至少一真实症状→trace→预设假设→本人亲改→回归／独审→另授同条件真实复测纠正 | 无真bug待证不植bug，最多两复测Case，改条件／source-model漂移为混杂；失败不替纠正；06 |

FR-001–015、NFR-001–011及原AC完整映射见SPEC；模块依赖见PLANS。权限、费用、恢复、测试映射七专项，不以框架、配置或模块存在代效果。

## 材料、本人实践与放行

当前M1关闭全部Memory功能入口，包括手动／自动、API／CLI、默认profile／框架Store预加载、旧checkpoint refs、导入／恢复／重建与后台路径；不提取候选、不读写、不检索、不注入，active Memory refs必须为空并与各模型阶段实际请求一致。Trace记disabled/not_applicable，hits／writes为null并附feature_disabled，不以测试零次冒充禁用证据，不要求空Store／seed／Memory快照。Case内条件、证据、文档和审计照常持久化；本人明确选定历史报告走SourceSet准确获许可版本，不解引用Memory refs，继续核当前权限和已知私有祖先。DEC-AC-17／DEC-M1-04保留延期、未实施／未验；完整Context属03a、Token资格属03b，当前M1不依赖04。真实复用需求、独立设计审查及准确范围另批后才可重开，原Memory预留容量保持闲置上界，不挪给其他功能。

REQ两变体完整链、CON两变体评审（均含无权威基准子问）、EXP两变体基于已确认需求仅方案，材料组合／规模及共同goal须可比。REQ保首次需求、实际本人改动（可空）／确认、首次方案及最终双稿包；人工修好不洗raw失败。仅需求独立终结、直接编辑／对话修订以聚焦回归和既有pilot观察，不声称各自独立正式质量／省时。澄清不缩共同goal，实质改scope保原slot partial／不可比，合理备选设计不强制唯一gold。三个类型、各两个可比变体的正式材料须独立制备并另审；当前公开索引待制备，本批不生成新题面／gold。inputs／controller／scorer分包，Worker不可读评分包；公开rubric非隐藏答案。先冻稿件和计时再揭依据；曝光／错误金标／评分修订保原slot及审查链，不换题洗分母。

Agent侧产品＋本人读源改稿，无外部AI代修／复制Control。Control登记日常人工／普通AI／搜索，DR按需计时计费；同登记手工引擎。全部实质断言核支持，机器quote／AI评分不代人语义；本人修好不改原始质量失败。真实用户价值、读码／预测／操作／亲改／解释由本人确认，不由AI代填。

## 本轮新增验收细化（仍待业务实现／验证）

以下细化既有DEC-AC，不另建权威AC系统；完整状态／参数见契约。

DEV-STAGES的P0只同步配置与校验，不运行以下业务检查。准确六阶段26切片见PLANS；4.5公开完整链与5.4私源仅需求工程实测分别消耗原两pilot槽，dynamic/private仍工程必需。效果试用/纠错收益/正式六槽按需，不再作为六阶段工程完成前置；正式启动后冻结规则保持。首次共享读取当片核权，阶段五变更后的最低恢复/Token/权限等资格先补验再真实调用，不重领额度。

| 对应AC／任务 | TEAM新增可观察通过条件 | 必须覆盖的反例 |
| --- | --- | --- |
| 08／09／15；02-A/B | CLI操作者指定唯一确认人；发起者编辑／接受／取消／接续，确认人确认／撤销，其他成员读或另建Case；角色可同一身份 | 确认人接管Task、模型指定角色、私人Draft自动入项目、无确认人仍生成方案 |
| 09／12／14／15；02-B/03 | 确认绑定准确version/hash/actor及策略／账户／成员资格revision；角色失效与方案三端双序 | 换人A→B→A、离队重入、disable→enable复活旧确认；logout／凭据轮换误撤内容；失效先提交仍发布旧方案 |
| 09／14／15；02-B | 资格及每个当前确认各自先保必要撤销空间；同operation幂等回放；仅永久失效后根事务有界释放 | 普通容量满先撤多个确认再独立禁用／撤成员／清策略；跨对象借预留、重复计费、临时proof不可用即释放、无余量先确认后补预留 |
| 16／19；07 | 同一真实参与者可同账户兼任两角色，保原formal计时／六槽 | 第二测试身份当真实团队采用证据、不同真实确认人混入原formal口径、增加正式槽位 |

| 对应AC | 正常行为 | 必须覆盖的反例 |
| --- | --- | --- |
| 08／09／14 | 主链按需委派同Task Work，准确assignment head／依赖，原子创建替换与幂等回放；主链按当前frontier归并 | 旧目标／权限继续调用、相同规划重复创建、取消后迟到、无关子任务推进误拒有效结果；全部资源无重置 |
| 10／11／15 | Task拥有共享取材，各消费者当前核权，保每源身份和private ancestry | 同URL不同权限误共享、取消首child误删其他消费者、零消费者仍推进、一次capture冒多证实 |
| 12／13 | 六purpose按程序映射共享正常池，compile最多四次物理含retry，尚未首次尝试首工件多维预留 | 第五次compile、retry免计、失败自动补满、可选版本挤占首方案、无容量仍发送 |
| 12／14／18 | 正式compile前seal研究输入；保护证据实际文本及反证／未知进入请求 | seal后结果偷偷归并、新requirements head沿旧确认编译、Manifest有ref但实际请求缺保护内容 |
| 13／18／19 | 完整本地计数、工程hosted-fit、合法actualusage／缓存／费用分开 | 合法非零差异被误拒、溢出资格仍可用、业务输出坏误撤协议资格、缺usage／费unknown填零或自动开闸 |
| 16／19／20 | 两案例静态走查、正式六槽位、真实用途和本人实践分别取证 | 配置测试通过冒充并发／真实质量、旧失败改判、未来安排写成本人已掌握 |

### R2受控重启与跨Turn验收细化

复用既有AC和预算，不新增formal槽位；细则由[契约B5.2](../../contracts/CURRENT_CONTRACTS.md#b52-supervisor)维护，均待业务实现／验证。

| 对应AC／任务 | 正常行为 | 必须覆盖的反例 |
| --- | --- | --- |
| 09／12／14；02／03a | 首需求partial→编辑／准确确认→同Case linkedTurn→新Task seal引用前轮有权已提交证据→方案／最终双稿包 | confirm与终结双序、head变化、前轮late audit晋升、Casecap／deadline重置 |
| 14／15；02／03b | A停机覆盖queued／running／recovering业务与control Task，清active／唯一终态；未发许可失效，只释确定未用reserve | 排队遗留、sent／Token／首尝试used返还、物理槽未收拢先释放、未知费用仍clean |
| 14／15；03b | clean回执→新boot研究closed→只读核证／本人未还原陈述→新CLI→CONTROL_ONLY→当前资格→本人新research许可 | 回执后撤权未作废、异常／疑还原走A、旧receipt重放、提交不明换operation、旧grant／Attempt／proof复活 |
| 13／14／15；03b | control-only无研究发送，原Casecap／deadline不暂停；有效资格不强制重跑；元数据先reserve | 诊断／控制重领、mint unknown后外发、资格半成崩溃却research、容量满仍写、借Memory预留 |
| 14／15／19；03b | 本人知悉A依赖同一未替换目录且未restore／copy／PITR的可信陈述；文档确认保准确版本、当前权限重核 | 把A称独立最新性证明、声称可检测漏报还原、rearm解除未解决unknown、历史Call改completed／重发 |

03b首次真实pilot前完成以上离线、restrictedPg及paid-disabled进程证据；首工01仍仅认证／私人Draft／最小sup，不把配置写成已运行能力。2027目标及本人实践按SPEC／PLANS。

## 历史DEC-AC-01–07及实现证据

下表只解释旧DEC-T01–T06原范围，不是新入口的兼容义务。旧正式协议读取固定 `1ffade6de07ebe3d1e72afb4c44b8677466eca67:docs/evaluation/CURRENT_EVAL_PROTOCOL.json` 及明确字节身份；旧九题/15次不指向现在的协议内容。[V1契约](../../contracts/V1_CONTRACTS.md)、源码和带日期记录决定实际行为。

| ID | 原范围可观察行为 |
| --- | --- |
| DEC-AC-01 | goal兼容六路API，必须条件和偏好分开 |
| DEC-AC-02 | 比较结论指向fact ID、主体、官方URL、片段与当时获取时间 |
| DEC-AC-03 | 候选×条件矩阵显示满足/不满足/未知及支持/冲突 |
| DEC-AC-04 | 硬条件失败/关键缺失/冲突不输出无条件赢家，取舍有fact依据 |
| DEC-AC-05 | 同场景条件变化影响理由，页面诱导文字不改用户约束 |
| DEC-AC-06 | 取消/超时/失租/预算停线保存已提交事实及已知/未知费用 |
| DEC-AC-07 | 当时正式九题题面/尝试/分母不变，补充复核不冒充正式full |

旧T02–05离线切片、T01修复和本人未验项按[任务原记录](tasks.md)解释；P-01假48/48、r11/r12真实失败不被新AC倒填。原Python-only、三角色组合、五账户、真实MCP和9/8/12材料不再构成现行规则；相关真实证据和授权继续保护。
