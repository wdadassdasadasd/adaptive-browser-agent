# 需求／方案研究起草：核源、计时与独立复核

规则仅来自[唯一协议](CURRENT_EVAL_PROTOCOL.json)，[M1材料](DECISION_M1_PROTOCOL.json)只引用它。复用[唯一任务记录](../features/DECISION-001/tasks.md)，不另立资金、质量或发布规则。本批只有配置，没有新运行器、正式题面、金标、ACL或真实尝试。

1. **准备和隔离。** 开发集与正式材料分开。非实现作者独立准备三对六个可比任务，另审目标难度、材料规模、语言、可得性及关键项。产品只得到当前任务范围、可见基准、允许资料和公开rubric；预期发现、冲突答案、隐藏定位只在scorer包。输入／对照／评分包按[公开索引](DISCOVERY_M1_CASES.json)分离，默认配置校验不等材料已核。见过gold的实现作者不能把材料继续称独立holdout；曝光slot及污染保留，不悄悄换题。
2. **运行前资格。** 固定代码／锁／模板／selector／本地完整格式与托管fit资格／工具／配额／Memory政策／来源版本／价格及材料身份，核全部历史unknown、在途、币种、余额、grant及全批覆盖。公开源仍须安全冷切、认证supervisor、Gateway和最低独立介质纸钥真实恢复资格。Browser0、MCP研究；缺资格不运行。当前slot和pilot的Memory全入口禁用，active refs为空并与实际请求一致，Trace为disabled/not_applicable与null hits/writes＋feature_disabled；Case内资料持久化，显式历史按SourceSet权限和私有祖先核验。完整禁用规则以[契约](../contracts/CURRENT_CONTRACTS.md)为准，不能用零次命中宣称通过。
3. **注册和揭题。** 冻结后一次CSPRNG seed，沿协议算法分配六slot，不重抽。先持久 `reveal_authorized/disclosure_committed`，绑定seed／slot／method／actor／题面hash，这只是披露许可。实际显示另保客户端时点及clock依据、服务器ACK收到时间、本人计时记录；不把许可或ACK收到时刻冒充显示，不把网络等待静默算主动。重连／重取／重复ACK不重置首次显示；ACK不成为业务授权。无法核实时保留最早可能暴露及 `timing_uncertain`，不进入有效saving，Control同口径。
4. **运行和全部尝试。** 六次串行、每次主动≤120分钟／墙钟24小时、整批14天；已揭题不延期。每条人工读写、提示、搜索、核源、读审计缺陷及改稿均计主动，纯等待与审计劳动另列，实际研究不能挪入行政。保原程序稿、每次人工revision／parent／hash／区间及最终提交；所有未启、失败、partial、取消、缺失、unknown和不可评分保留在已分配分母，不补120分钟为完成时间。
5. **核源与反馈。** 对已冻结原稿逐条核关键结论及额外实质断言，查原始版本／主体／表示hash／UTF-8位置／限定／反证；机器子串、URL和AI评分不证明语义。区分观察、推断和建议，未读不能写不存在，文档声明不能冒充已实现。最多两轮缺陷反馈，仅缺陷类型和原报告定位，不供隐藏来源或答案；新增研究需披露贡献时间、费用和污染。本人实际补查及改稿计主动。最终稿与计时先冻结，再揭评分依据，不能倒流补该次产品输入。
6. **分别判定。** 三个Agent原始交付各自关键项全部通过（REQ同时检查首次需求和首次方案）才过原始产品质量；人工修稿不能清除原错误。指定故障的诚实partial可过安全预期，但不算正常任务fullcompleted。最终六个人工交付包的所有必要文档共质、完整非零计时才描述三配对省时中位数，缺失则inconclusive，不降分母、截负数或设20%硬门槛。普通发现及遗漏逐项描述，不假造穷尽recall或合成总分。真实用户／团队价值、本人掌握、M1、Go、发布分开。
7. **追溯与访问。** Pg canonical串联accepted revision／question basis／Work／Call／capture／Claim／ContextManifest／精确安全请求／response／usage／费用／报告；UI事件封顶不裁canonical。TraceView、每页、每SSE帧及有界导出核当前登录、sup、成员、用途分享、来源proof和派生lineage；cursor不授权。撤权先提交拒未claim数据，最后一个有界在途响应可能送达。日志不收秘密／原私有prompt／任意异常全文／隐藏思维链。
8. **重建与优化。** 离线只读核hash、关系、selector、计时、slot及usage算术，不graph replay、网络或重跑Tokenizer。缺失或因许可不保原文标not_reconstructible。优化保真实症状／原trace→预定义可证伪目标→本人最小修复→固定源离线回归→独立实现审查及复审→另授权同条件真实复测，最多两个Case。保全部失败和来源／模型漂移混杂，不造bug凑至少一项真实纠正。

当前协议为draft-m1-3；DEC-AC-17／DEC-M1-04延期未验，Context归03a／Token归03b，不借延期挪用原容量。真实复用需求、独立设计审查及准确范围另批后才可开启Memory。两个既有pilot优先真实待办，先冻结目标、普通AI／人工基线、关键正确项和后续行动，再看原稿、人工补救及实际用途；暂无任务即待证。

原始审查、准确正文／diff／检查和最终指纹由唯一任务记录承接。配置校验、独立设计审查、当前实现独审、人工核源、本人业务验收和个人掌握是分别取证的结论；当前材料pending，不宣布正式就绪。

## 模式、编辑与交付专项

正式覆盖严格绑定唯一协议formal.workflow_coverage：REQ完整双稿链、CON纯评审（两变体均有无基准探索子问）、EXP基于确认需求的方案起草。评分材料必须独立检查覆盖与两变体等价；validator仅核结构，不证明语义等价。首需求／首方案必须在人工修订前分别冻结；需求确认绑定version/hash/actor，不能用人工修稿洗原始失败，也不能把需求变化后的旧方案当当前结果。

键入过程不产生历史版本，显式保存或AI成功提交才新增DocumentVersion。任一需求head变化原子清除当前确认；solution start/send/commit均核当前需求、确认与目标head CAS，冲突明示。模式变化须仍属于Case原目的并重新接受，在同一事务为尚未进行首次尝试的首工件预留一次正常调用／compile／Token、版本槽、正文meta及terminal。无容量不白跑、不自动建新Case；document_compile总计最多四次物理尝试，含技术retry；首次尝试失败已用资源不补回，需求再次变更后的重编仅用全部剩余额度，不能保证首方案成功或修订次数。

完整包引用准确需求／方案文档和确认，UI与各份Markdown核当前权限读取同一版本hash；不新增ZIP或无界复制导出。原始Draft、原稿、人工修订和最终包分别保留。仅需求终结和编辑／修订由回归及既有pilot观察，没有独立正式效果结论；三pair混合median不外推各模式质量或总体收益。

## 专题委派、Context与Token的连接核查

先固定目标、Assignment head／依赖、允许来源及实际Context，再追主子Work、共享取材消费者、调用与证据归并。取消一个消费者不自动取消其他有效消费者；同capture不得重复当独立佐证。编译输入封存后，迟到结果只留审计，不改变已封存依据；关键义务不足不能靠降低要求清零。配置走查不等于事务竞争或恢复实验。

核对“工具成功但证据无效→证据已得未入Context→摘要丢反证→旧目标／权限继续工作→需求head变更→恢复重复调用→unknown重发→Memory默认路径注入”的失败链，记录每个位置的证据和待验证项。

本地完整模板Token、托管fit与实际usage／cache／费用分别留原值和版本；合法差异不自动调额，overflow／供应商协议异常撤受影响资格，业务JSON不合格只判交付不可用。费用unknown停全项目新外发；缺usage、迟到结算、恢复和新ID不能自动补齐资格。
