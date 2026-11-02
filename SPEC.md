# Adaptive Research Agent — 需求与方案研究起草产品与技术规格

**FOCUS-BASELINE-20261102：FOCUS-20261102-01的28文件配置实施获批；实际检查、当前文件独审与最终交付以唯一任务记录及本轮外置索引匹配结果裁定。** 本规格描述已确认设计，不证明业务实现、真实质量、本人掌握或用户价值。原PREP-BASELINE-20261029及原字节／严格JSON修复仍按各自被审字节有效；r12、P-02 No-Go保留。

权威配套：[计划](PLANS.md)、[现行契约](docs/contracts/CURRENT_CONTRACTS.md)、[功能AC](docs/features/DECISION-001/spec.md)、[唯一评测协议](docs/evaluation/CURRENT_EVAL_PROTOCOL.json)、[唯一任务及18项记录](docs/features/DECISION-001/tasks.md)。M1补充只引用唯一协议，不另立资金或Go规则。具体API、参数、资源与失败规则集中在契约，本页定义产品结果。

## 用户、价值与核心路径

面向开发者／团队的需求与方案研究起草Agent，结合目标、材料和相关源码形成可核查、可编辑的需求与工程方案，保留已有文档证据评审。用户问题是假设：准备新功能或调整设计时，将想法、文档、实现约束和公开证据整理成可讨论、可解释、可实施的草稿，减少遗漏和核源负担。当前没有已确认真实任务或团队需求证据，不宣称收益；普通AI与Spec Kit已可写文档，额外机制的价值须真实任务验证。

| 入口 | 前提与交付 |
| --- | --- |
| review_only（仅评审） | 已有材料的问题、证据、冲突、未知与修改建议；无权威基准只给观察／假设，不宣布符合性 |
| requirements_only（仅需求） | 从想法或材料形成需求稿，可独立结束，不自动进入方案 |
| solution_only（仅方案） | 本人明确确认准确既有需求版本后，研究并起草工程方案 |
| requirements_to_solution（完整闭环） | 需求首稿→本人编辑／对话修订并确认准确版本→工程方案首稿→修订与导出 |

输入允许无仓库想法、一个主GitHub仓库固定commit、获许可公开证据，以及本人明确选定的本地普通文本／源码／未提交差异。源码只读不执行，diff不应用；未知基点如实unknown，用户声明与已核版本分开。选定文件不等于可遍历本机目录或原子worktree快照，不承诺全仓穷尽。未枚举、未选、未读、失败、超限、无权分别展示，“未找到”不能写成“不存在”。

需求稿至少包括问题／用户、目标、范围、主要流程、AC、依据、假设和待决定事项；方案稿至少包括架构与数据流、模块、接口与数据、正常／失败链、权限费用恢复、取舍与验证。新起草的需求和AC可作建议，只有本人明确确认才成为该方案的接受基础；来源或模型不能冒称已有硬条件。文档／代码声明非系统实测，不自动批准设计、执行、改仓库或创建PR。

私人原始Draft与生成文档分开。目标及选定材料→明确加入team/project→Case有界研究／澄清→需求DocumentVersion→本人RequirementsConfirmation→方案DocumentVersion→当前权限下UI与各份Markdown。直接编辑＋对话修订；仅显式保存／AI成功提交产生不可变版本，键入保有界UI内存草稿，不localStorage，logout／换身份清除。保存不是确认；新需求head在同根事务清除当前确认，旧确认和旧方案保留历史。方案start/send/commit均核准确需求及确认，过期状态由引用差异派生，不另立权威flag。

R1经C1确认后生成S1期间，若R2先保存，C1不再当前；S1迟到仅原Call审计／费用，不成为当前方案。确认和保存CAS，409明确冲突供人工重载，不能静默覆盖或丢弃可见未保存编辑。改条件默认复用固定commit，明确更新才新SourceVersion。重大冲突／权限／费用／必要证据缺口保存进度partial，回复linkedTurn不重置Case目的、期限和额度。需求再次改版后的新方案消耗余量，不保证无限首稿。

## 团队、权限与读取

仅明确加入项目的资料、任务和报告在团队统一分享；个人私有材料不自动加入，不继承GitHub逐成员ACL。账户、私人Draft仍属个人；未来Memory的作者边界也不改变个人归属，不把owner机械替换为team。上游GitHub私源授权主体是团队GitHub App installation与仓库；本地成员和Task执行许可独立核验。

采集处理、持久保留、外部模型处理、团队展示／导出及向Search／Fetch披露分别受用途与范围许可约束。私有输入祖先关系随派生传播，公开引用或公开URL不能洗掉私有来源。来源用途／分享撤销后阻止新使用与派生，并通过当前访问门禁限制相关历史报告；保审计不等于继续展示，不能召回已下载副本。

每次有界响应、分页和SSE帧重核当前账户、会话、supervisor、成员和适用来源许可；仅GitHub私有来源或其私有祖先核适用GitHub proof，纯公开无凭据profile核当前本地use/share许可及固定来源身份，不要求App签发。撤权先提交拒绝未claim交付；已claim最后一个有界响应可能在途，不保证瞬时召回。退出登录停止旧会话后续读取，不自动取消仍有独立执行许可的后台Task。UI及Markdown惰性显示来源文字，不执行HTML、不自动加载图片或链接预览。

## 运行、证据与模型边界

保留本机Windows UI、WSL独立API／Worker／新独立Pg。Worker采用真实LangGraph阶段节点，Pg应用表拥有业务事实、权限、Work／Call、证据、报告、usage和费用；checkpoint只持有界已提交引用，不是恢复授权。API处理身份／接受／访问，Worker推进阶段，Gateway统一出站，TraceView只是canonical记录的只读视图。

GitHub direct API与DeepSeek单一Search／Fetch适配器优先。私源五分钟资格每次重新限权签发并核安全回执、仓库身份及读取能力；公开200不能续私源资格。Search按需补证，许可绑定最终完整query与目的；Fetch完整URL同样核披露依据。Browser真实接入暂缓、保持0，MCP研究，无自动回退。

使用路径、标题、关键词和原文段落选择，不默认向量库、Embedding或Reranker。采集表示、原始blob身份、摘要与结论分开；引文绑定主体、版本、表示hash与UTF-8范围。结构准入不证明语义支持，人工核源独立；来源漂移新capture不覆盖旧证据，不声称固定快照就是当前最新。

Context保护完整条件／未知、阶段任务及必要证据／限定／反证，再选可选证据；保护内容缺许可或装不下即拒发partial。

当前M1关闭全部Memory功能入口，包括手动／自动、API／CLI、默认profile／框架Store预加载、旧checkpoint refs、导入／恢复／重建与后台路径；不提取候选、不读写、不检索、不注入，active Memory refs必须为空并与各模型阶段实际请求一致。Trace记disabled/not_applicable，hits／writes为null并附feature_disabled，不以测试零次冒充禁用证据，不要求空Store／seed／Memory快照。Case内条件、证据、文档和审计照常持久化；本人明确选定历史报告走SourceSet准确获许可版本，不解引用Memory refs，继续核当前权限和已知私有祖先。DEC-AC-17／DEC-M1-04保留延期、未实施／未验；完整Context属03a、Token资格属03b，当前M1不依赖04。真实复用需求、独立设计审查及准确范围另批后才可重开，原Memory预留容量保持闲置上界，不挪给其他功能。

模型repair和额外摘要调用为0。唯一编译器生成安全业务请求bytes/hash，Gateway使用同body；thinking显式disabled、输出上限显式。完整本地官方converter／模板／Tokenizer资格未成立则paid off；有限诊断另有总allocation，不以换profile／Turn／重启重领。本地Token、provider usage、缓存、费用和余额分账；漂移在根事务撤资格revision，阻旧未发许可，在途按原Call结算不重发。

Work稳定，Call物理；completed／unknown不凭新ID重发。unknown全项目停新外调，含来源资格刷新，因此GitHub私源proof过期可使相关历史报告暂不可读。send与commit双端核当前权限、Task、租约、fence及执行代次；迟到仅原Call许可审计／费用。终态不提前释放物理在途槽，sup须封旧代并确认资源收拢。

## 需求与验收追溯

历史AC-001–012、AC-N01–10及P阶段保留原范围。现行DEC-AC-08–20见功能规格，任务与本人操作见唯一记录。

| 需求 | 当前行为 | 主要验收追溯 |
| --- | --- | --- |
| FR-001 | Session／Case／revision／Task原子提交、幂等与历史 | AC-001；DEC-AC-08、DEC-AC-09、DEC-AC-14 |
| FR-002 | 阶段图、目标驱动文档发现、取证与停止 | AC-002；DEC-AC-10、DEC-AC-18 |
| FR-003 | 来源与被评审主体身份、版本、去重保出处 | AC-003；DEC-AC-10、DEC-AC-11 |
| FR-004 | 需求／方案／评审版本、精确需求确认及证据绑定的不可变交付包 | AC-004；DEC-AC-11、DEC-AC-12 |
| FR-005 | 已提交事件、受限分页／SSE及历史UI | AC-005；DEC-AC-09、DEC-AC-14、DEC-AC-15 |
| FR-006 | 取消、唯一终态、重处理及unknown诚实失败 | AC-006；DEC-AC-14 |
| FR-007 | 调用／Context／费用Tracing与人工核源 | AC-007；DEC-AC-13、DEC-AC-18、DEC-AC-19 |
| FR-008 | 直接编辑／对话修订与各文档有界Markdown，同快照引用，不自动审批 | AC-008历史；DEC-AC-12、DEC-AC-15 |
| FR-009 | 真认证、私人Draft、项目共享与测试身份隔离 | AC-009；DEC-AC-15 |
| FR-010 | 有源观察、冲突／限定／未知和验证步骤 | AC-010；DEC-AC-12 |
| FR-011 | 条件修订与Case内跨轮证据；跨Case Memory延期 | AC-011；DEC-AC-11；DEC-AC-17延期未验 |
| FR-012 | direct API参数／错误／关闭，Browser0／MCP研究 | AC-012；DEC-AC-10、DEC-AC-13、DEC-AC-15 |
| FR-013 | 逐评审问题证据关系，不要求旧选型矩阵 | DEC-AC-01–07历史；DEC-AC-08、DEC-AC-10、DEC-AC-12 |
| FR-014 | 接受范围内自主，重要冲突终结并关联新Turn | DEC-AC-08、DEC-AC-09、DEC-AC-12、DEC-AC-14 |
| FR-015 | 有界关键文档与选定本地材料、源码／diff，处理／未覆盖清单 | DEC-AC-10、DEC-AC-11 |
| NFR-001 | 时间、调用、恢复和资源有界 | AC-N01；DEC-AC-13、DEC-AC-14 |
| NFR-002 | 单资金权威，预留／结算及已知／未知分账 | AC-N02；DEC-AC-13 |
| NFR-003 | 本机信任、不可信来源和受控出站 | AC-N03；DEC-AC-15 |
| NFR-004 | 真实症状、可证伪假设、本人最小修复与复测 | AC-N04；DEC-AC-19、DEC-AC-20 |
| NFR-005 | 原件保护、可复现交付与本人实践 | AC-N05；DEC-AC-16、DEC-AC-20 |
| NFR-006 | 故障恢复不重置权限、截止或预算 | AC-N06；DEC-AC-14、DEC-AC-15 |
| NFR-007 | 并发／容量原子拒绝，无孤立对象 | AC-N07；DEC-AC-09、DEC-AC-13 |
| NFR-008 | Host／Origin／CSRF及当前逐对象授权 | AC-N08；DEC-AC-15 |
| NFR-009 | 独立介质、纸钥、可信hash与隔离恢复 | AC-N09；DEC-AC-14、DEC-AC-15 |
| NFR-010 | 完整本地Token、输出预留、绝对截止／有限重试 | AC-N10；DEC-AC-13、DEC-AC-18 |
| NFR-011 | 稳定义务、物理调用、最终claim与canonical审计 | DEC-AC-13、DEC-AC-14、DEC-AC-15 |

## 质量、窗口与放行

draft-m1-2三个正式Agent原始交付分别通过预冻结关键项（REQ同时检查需求和方案首稿），才算产品原始质量通过；本人修订不洗原始失败。六次最终人工交付包共同质量通过且首次实际显示／主动时间完整、基线非零后，才描述三个配对省时中位数，允许负值、不设20%硬门槛。Control预注册日常人工阅读／普通AI／搜索，DR按需；Agent侧不用外部AI代修或复制Control。独立正式材料、失败分母及口径只由唯一协议定义，公开索引不含金标。

2026-10-29起七至八周、本人每周≤20h，窗口优先需求到方案闭环与本人讲解。原92–136h纵切／130–194h完整范围估计仅解释旧评审范围，非实测，不能承诺新起草范围工期；已发生投入未知不填0，后续真实本人实耗校准，超窗交具体取舍，不扩每周时间或费用。私源、正式评测和完整恢复未完成不称首阶段／M1；Memory已移出当前M1必需范围，不把延期计为完成；公开源真实pilot仍须最低独立介质纸钥恢复及全部资格，离线替身不冒充真实模型。

费用epoch保持2026-10-28、增量严格低于300元；条件预算296.46元不是到账、grant或剩余可花，历史unknown不填0。P-01假48/48、旧切片及r11/r12失败仅解释原版本。配置检查、当前文件独审、实现、本人核源／掌握、真实价值、M1、Go、发布分别判定；本批不授业务、依赖、环境、真实运行、付费、购买、外部或Git写。

DRAFT-BASELINE-20261102原28文件交付经只读核实有效；FOCUS仅将Memory后置并同步依赖、协议和完成口径，不倒填旧审查。DRAFT按final-01、REVIEW-BASELINE-20261101按final-02的manifest/path/raw hash追溯，不冒称HEAD对象。
