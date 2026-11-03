# DECISION-001：需求与方案研究起草及证据评审

**RESEARCH-BASELINE-20261103：CONTENT-20261103-01完整确认，CONFIG-PLAN-20261103-01配置实施获批。** [唯一任务／原18项](tasks.md)分别记录批准、实施、检查、独审和交付。依据[根规格](../../../SPEC.md)、[计划](../../../PLANS.md)、[契约](../../contracts/CURRENT_CONTRACTS.md)、[唯一协议](../../evaluation/CURRENT_EVAL_PROTOCOL.json)。旧FOCUS／DRAFT／REVIEW及更早交付继续绑定原字节，业务、环境、真实运行及本人验收另取证，r12／P-02 No-Go不变。

## 用户问题与交付

面向开发者／团队，支持review_only、requirements_only、solution_only、requirements_to_solution。想法无仓库可用；材料限一个主GitHub固定版本、许可公开证据和本人选定本地text／源码／diff。源码只读不执行，diff不应用；原始私人Draft与不可变生成文档分开。需求首稿经本人编辑／对话修订并确认准确版本后，才可生成方案；仅需求可独立结束，仅方案须明确确认既有需求。UI及各Markdown准确绑定同一版本。

需求稿说明问题／用户／目标／范围／流程／AC／依据／假设／待决；工程方案说明架构数据流／模块接口数据／正常失败／权限费用恢复／取舍验证。评审无权威基准只观察／假设；起草可提建议但不能自升已接受条件。暂无真实任务，价值待证，不自动批准／改仓库／运行系统。

采集／保留／模型／分享／完整Search query与Fetch URL用途分别许可，派生继承私有输入祖先。退出读会话不取消独立执行Task；来源／成员撤销收紧新调用、新提交和当前读取。详细竞争、schema与数值以契约为准。

## DEC-AC-08–20：当前验收契约

以下均为待实现／待验行为。结构检查、离线fixture、受限Pg、真实任务、人核源与本人掌握分别取证。

| ID | 可观察通过条件 | 必须保留的失败／竞争证据；任务 |
| --- | --- | --- |
| DEC-AC-08 | 四模式和目标有原消息出处，基准／未知／范围可澄清；接受才有InputRevision；仅方案绑定本人确认需求；依据三分 | 私Draft不自动入team，网页／模型／Memory不改硬条件；无基准仍探索；02 |
| DEC-AC-09 | 同发起者／Session／key／正文先重放后CAS，接受revision／Task／active／event／version原子提交 | 异body409；需求保存、确认与方案start/send/commit双序CAS，改head原子失效确认；满额／DB失败无孤立对象；控制Task无研究许可；02 |
| DEC-AC-10 | 无仓库想法或单主仓库固定版本，有界关键文档及选定本地text／code／diff，public按需补证 | 本地逐stream实际计数／严格解码／30s／核权reserve和commit；未seal不入模型，未知diff基点非commit；截断／未读／失败非覆盖；Browser0；03a/03b |
| DEC-AC-11 | 实质主张有主体／适用版本／范围、capture表示hash及UTF-8引用；摘要非原文 | 子串不证语义，反证／限定／未知版本保留；新capture不覆盖，改条件默认同commit；03a/03b，当前不依赖04 |
| DEC-AC-12 | 需求／方案／评审不可变版本含依据／假设／验证；编辑显式保存与对话修订，UI／各Markdown同hash，完整包保双稿及确认refs | 未读非不存在，文档声明非已运行；关键不足partial，探索可有事实unknown；16版本及首工件compile/slot/bytes多维预留，已知无容量零发；repair／summary0；02/03 |
| DEC-AC-13 | 所有Call含签发／probe／retry逐次准入预留，精确请求与资格绑定，Token／usage／费用分账 | prepared／admitted非发送；unknown停全项目外调；schema／unknown不技术重试；未知不填0；03b |
| DEC-AC-14 | send与commit核实时租约／fence／执行代次／权限／资格；终态／active／event原子；checkpoint只refs | cancel／success、lease／commit双序，late只原Callaudit／费用；completed不重发，资源确认才释放；02/03b，Memory禁用／空refs |
| DEC-AC-15 | 真认证、私人Draft／项目共享分开；member／source／Taskgrant及读取claim可验；新cluster／sup | logout／expiry后SSE不续读；每response／page／frame重核，最后有界在途可送达；源撤权派生禁用，恢复保守；01/ENV/08 |
| DEC-AC-16 | draft-m1-3的REQ双首稿／CON原评审／EXP原方案各过关键项；六final交付包共质且计时完整后才描述已登记三pair省时 | 无20%硬门槛，非关键逐条不合总分；缺／0baseline不挑pair；未启动／取消／缺失均保分母；07 |
| DEC-AC-17（延期，非当前M1必需） | 未来跨Case自动Memory候选，未实施／未验，不算pass | 当前所有Memory入口关闭且实际请求无注入；不建空Store／seed；真实复用需求、独立设计审查及准确范围另批才重开04；原容量不挪用 |
| DEC-AC-18 | 完整条件／未知、必要证据／反证先保护；Manifest解释选排；完整公开格式本地计数／hosted-fit／实际usage三层证据 | 缺许可／超限拒发partial；合法计数差异只记录，溢出／供应商协议错root撤affected资格，业务输出错不混同；不推测内部使用；03a/03b；当前不依赖04 |
| DEC-AC-19 | 原程序、原report核源、本人finalhash三轴；canonical／usage／费用／active／wait可重算 | 六slot同版全保，gold受限；许可非实际显示，不明时点不算saving；audit不偷偷供研究；06/07/08 |
| DEC-AC-20 | 至少一真实症状→trace→预设假设→本人亲改→回归／独审→另授同条件真实复测纠正 | 无真bug待证不植bug，最多两复测Case，改条件／source-model漂移为混杂；失败不替纠正；06 |

FR-001–015、NFR-001–011及原AC完整映射见SPEC；模块依赖见PLANS。权限、费用、恢复、测试映射七专项，不以框架、配置或模块存在代效果。

## 材料、本人实践与放行

当前M1关闭全部Memory功能入口，包括手动／自动、API／CLI、默认profile／框架Store预加载、旧checkpoint refs、导入／恢复／重建与后台路径；不提取候选、不读写、不检索、不注入，active Memory refs必须为空并与各模型阶段实际请求一致。Trace记disabled/not_applicable，hits／writes为null并附feature_disabled，不以测试零次冒充禁用证据，不要求空Store／seed／Memory快照。Case内条件、证据、文档和审计照常持久化；本人明确选定历史报告走SourceSet准确获许可版本，不解引用Memory refs，继续核当前权限和已知私有祖先。DEC-AC-17／DEC-M1-04保留延期、未实施／未验；完整Context属03a、Token资格属03b，当前M1不依赖04。真实复用需求、独立设计审查及准确范围另批后才可重开，原Memory预留容量保持闲置上界，不挪给其他功能。

REQ两变体完整链、CON两变体评审（均含无权威基准子问）、EXP两变体基于已确认需求仅方案，材料组合／规模及共同goal须可比。REQ保首次需求、实际本人改动（可空）／确认、首次方案及最终双稿包；人工修好不洗raw失败。仅需求独立终结、直接编辑／对话修订以聚焦回归和既有pilot观察，不声称各自独立正式质量／省时。澄清不缩共同goal，实质改scope保原slot partial／不可比，合理备选设计不强制唯一gold。三个类型、各两个可比变体的正式材料须独立制备并另审；当前公开索引待制备，本批不生成新题面／gold。inputs／controller／scorer分包，Worker不可读评分包；公开rubric非隐藏答案。先冻稿件和计时再揭依据；曝光／错误金标／评分修订保原slot及审查链，不换题洗分母。

Agent侧产品＋本人读源改稿，无外部AI代修／复制Control。Control登记日常人工／普通AI／搜索，DR按需计时计费；同登记手工引擎。全部实质断言核支持，机器quote／AI评分不代人语义；本人修好不改原始质量失败。真实用户价值、读码／预测／操作／亲改／解释由本人确认，不由AI代填。

## 本轮新增验收细化（仍待业务实现／验证）

以下细化既有DEC-AC，不另建权威AC系统；完整状态／参数见契约。

| 对应AC | 正常行为 | 必须覆盖的反例 |
| --- | --- | --- |
| 08／09／14 | 主链按需委派同Task Work，准确assignment head／依赖，原子创建替换与幂等回放；主链按当前frontier归并 | 旧目标／权限继续调用、相同规划重复创建、取消后迟到、无关子任务推进误拒有效结果；全部资源无重置 |
| 10／11／15 | Task拥有共享取材，各消费者当前核权，保每源身份和private ancestry | 同URL不同权限误共享、取消首child误删其他消费者、零消费者仍推进、一次capture冒多证实 |
| 12／13 | 六purpose按程序映射共享正常池，compile最多四次物理含retry，尚未首次尝试首工件多维预留 | 第五次compile、retry免计、失败自动补满、可选版本挤占首方案、无容量仍发送 |
| 12／14／18 | 正式compile前seal研究输入；保护证据实际文本及反证／未知进入请求 | seal后结果偷偷归并、新requirements head沿旧确认编译、Manifest有ref但实际请求缺保护内容 |
| 13／18／19 | 完整本地计数、工程hosted-fit、合法actualusage／缓存／费用分开 | 合法非零差异被误拒、溢出资格仍可用、业务输出坏误撤协议资格、缺usage／费unknown填零或自动开闸 |
| 16／19／20 | 两案例静态走查、正式六槽位、真实用途和本人实践分别取证 | 配置测试通过冒充并发／真实质量、旧失败改判、未来安排写成本人已掌握 |

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
