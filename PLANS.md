# Adaptive Research Agent — 需求到方案闭环交付计划

**TEAM-BASELINE-20261103-01：负责人确认完整团队研发计划后，以“PLEASE IMPLEMENT THIS PLAN”授权阶段0配置对齐。** 依据[规格](SPEC.md)、[契约](docs/contracts/CURRENT_CONTRACTS.md)、[AC](docs/features/DECISION-001/spec.md)、[唯一协议](docs/evaluation/CURRENT_EVAL_PROTOCOL.json)、[唯一任务／原18项](docs/features/DECISION-001/tasks.md)。本轮实现范围为配置与限定离线检查；后继业务、环境和真实执行仍走准确任务关口，实际落地／检查／独审状态只由唯一记录裁定。

## 配置与历史

本批对齐本机双身份共享项目、指定确认角色与撤销预留，以及真实单链先试用、动态分工和私源后续补齐的顺序。先保存进入快照／保护指纹，再修改、限定离线回归、冻结完整正文／diff、独立实施审查、核实修复／重测／必要复审。原RESEARCH-BASELINE-20261103-R2及更早交付按原字节、授权和范围保留；唯一draft-m1-3与公开材料索引原字节不变，能力引用升为draft-m1-capabilities-5。材料仍pending，不制题／gold；新审计仅追加.tmp/team-plan-20261103-01，不覆盖旧证据，不改业务／依赖／环境／Git。

FOCUS-BASELINE-20261102原28文件与批准继续绑定其原字节；DRAFT-BASELINE-20261102按final-01、REVIEW-BASELINE-20261101按final-02继续有效，不以新研究重绑定旧交付。PREP-BASELINE-20261029原40路径与2026-10-30五文件原字节／JSON修复按原被审字节有效。旧候选池／短名单、20%及强制DR仅属旧产品规则。r12／P-02 No-Go、原SQLite／授权／费用／失败／来源许可受保护。

## 任务依赖与可观察交付

| Task | 独立结果与职责 | 前置依赖 | Requirement／AC | 核心验收和停线 |
| --- | --- | --- | --- | --- |
| ENV-M1-01 | 安全启动、冷切、独立新Pg与角色／路径资格 | 准确环境操作另授，boot前旧自动服务／出站保护 | NFR-003/006/008/009；DEC-AC-15 | 不能证明安全不先启WSL；新旧库／凭据／连接及误写阻断 |
| DEC-M1-01 | 真登录→私人原始Draft保存／重开→第二测试身份404＋最小supervisor | ENV-M1-01、精确依赖与业务授权 | FR-009；NFR-008；DEC-AC-15 | 不建InputRevision／Task；无旧Settings／模型旁路；失连续旧身份失效 |
| DEC-M1-02-A／02-B | 最小team／project／用途权限与真实阶段图假供应商；不可变文档、指定确认人／准确确认CAS与linkedTurn | 01、精确框架锁与兼容资格；团队不塞首工 | FR-001/004/006/014；DEC-AC-08、09、12、14、15 | 幂等先CAS、原子对象、读会话与执行许可分开；发起者编辑／确认人确认；角色／head失效与方案三端双序 |
| DEC-M1-02-C单链核心 | 同一Work／Call内核的预留、取消、lease/fence、unknown、seal、唯一终态及物理收拢 | 02-A/B；spawn关闭 | FR-006/014；DEC-AC-09、13、14、15 | 不因单链省略安全义务；checkpoint切点不重发；动态父任务保持未完成 |
| DEC-M1-03a | 想法／固定公开资料／选定本地text-code-diff→问题／来源／Claim→保护Context→四模式及同快照UI／Markdown | 02-C单链核心、受限schema及public profile | FR-002/003/004/008/010/015；DEC-AC-10、DEC-AC-11、DEC-AC-12、DEC-AC-18 | 核权／封定、精确引用、反证、未读非不存在；先离线单链验收，动态合入再复验受影响链 |
| ENV-M1-02（08a） | 最低独立介质／纸钥／来源纸卡与真实隔离恢复资格 | 环境、工具、介质、恢复分别准确授权 | NFR-009；DEC-AC-14、DEC-AC-15 | 首次公开源真实pilot也前置；旧库零写、失败目标隔离；不依赖07 |
| DEC-M1-03b资格／首public full pilot | Gateway／完整本地Token、hosted-fit、usage／费用及受控rearm资格后，先真实公开源单链完整流程 | 03a单链、08a、全账／unknown／余额／grant及精确真实授权 | FR-007/012；NFR-002/010/011；DEC-AC-13、14、15 | 首pilot前离线、restrictedPg及paid-disabled进程资格齐备；最终claim／commit双核、overflow撤资格、费用unknown全停；仅提前反馈非完整M1 |
| DEC-M1-02-C动态／重集成 | 专题assignment、替换、共享消费者、归并、取消与恢复 | 首public单链pilot反馈之后；沿同一内核 | DEC-AC-09、12、14、15、18 | 复验四模式、Context、Gateway及安全边界后关闭动态父任务；不预填质量收益 |
| DEC-M1-03b私源 | GitHub App准确仓库／权限资格、续签、撤权、private ancestry及派生读取 | public pilot及动态重集成；App精确操作另授 | DEC-AC-10、11、13、14、15 | 公共200不代私源授权，unknown停刷新；完整M1必须补齐，不宣称public已覆盖 |
| DEC-M1-04（延期，非当前M1必需） | 未来跨Case Memory候选；未实施、未验，不算pass | 真实复用需求→独立设计审查→准确范围另批；非03a／03b当前前置 | FR-011未来；DEC-AC-17延期 | 当前所有入口关闭，不建空Store／seed；候选TTL／更正／撤销／隔离规则仅未来参考 |
| DEC-M1-05 | Browser连接层／bridge研究与真实资格 | 当前暂缓真实接入，未来另授及资源重评 | FR-012；NFR-003；DEC-AC-10、DEC-AC-13、DEC-AC-14、DEC-AC-15 | 保持Browser0；当前HTTP／存储无Browser额度，不从Search失败自动回退 |
| DEC-M1-06 | 真实症状→本人最小修复→回归／独审→另授同条件真实复测 | 03b迹证；05仅按症状影响，04当前禁用且非前置 | NFR-004/005；DEC-AC-20 | 最多两复测Case，漂移／改条件非收益；无真缺陷待证不植bug |
| DEC-M1-07 | REQ完整链／CON评审／EXP仅方案三对六次，原稿核源与final／时间分列 | 必要模块、独立材料／评分隔离／版本／资格／资金冻结 | DEC-AC-16、DEC-AC-19 | 三Agent原稿均过关键项；六final全共质才描述median，无20%硬门槛，全失败保留 |
| DEC-M1-08b | 完整恢复故障覆盖、最新备份、本人解释与成功／失败演示 | 相应模块证据及最新capture | NFR-005/009；DEC-AC-15、DEC-AC-19、DEC-AC-20 | 最低pilot恢复不延至此；旧身份／Memory不复活；Go发布另判 |

准确业务文件／命令／回滚仍由唯一记录逐包冻结。旧DEC-T07–13只保历史，不建并行任务线。五个Agent方向映射Runtime02／03b、Tools与证据03／延期05、Context03a／Token03b、Memory04延期、Evaluation／Tracing／优化06／07／08。MCP研究不产生安装接入资格。

## 窗口优先级、本人实践与投入

当前优先案例B完整需求到方案闭环、证据评审和本人能够解释／修改核心机制。固定GPT Researcher 3582a6841fe7dc801e2a34e34ee408641aea9bce已有研究／报告编辑／持久聊天→需求编辑／准确确认／绑定方案，作为开发材料及后续另授pilot目标；预读资料和已知发现须登记，不成为正式题或gold，实际价值待证。案例A继续检验模糊想法适应性。顺序为ENV→01→02-A/B→02-C单链核心→03a四模式离线链→最低恢复、Gateway／Token／全账资金／来源及受控rearm资格→另授首个public full pilot→02-C动态重集成→私源→原第二reqonly pilot／真实纠错→正式六槽及完整恢复／实践。单链fake与real走同一应用准入／提交路径；前置不成立时交明确标注替身的离线链，不称真实Agent已运行。动态和私源仍属完整M1必需，单链反馈不关闭父任务或完整M1。以下七至八周、≤20h及小时估计保留为旧安排，不推定当前可投入条件或新期限。

首版只验证本机最多两个身份的共享项目与人工交接；项目／成员／唯一确认人由本机有权操作者CLI设置，无管理后台。发起者编辑、接受／取消及显式接续，指定确认人确认／撤销准确版本，可为同一身份。角色资格失效及撤销预留按契约执行，不扩Task／费用／来源许可。formal继续同一真实参与者／可同一账户，跨身份测试独立，不冒真实团队价值。首public pilot按现状核实、需求边界、改造设计、首批任务、开工阻碍五项检查能否据此实际开发，并记录原稿缺陷与本人核查／补救负担。

Memory全部功能入口继续禁用并延期：手动／自动、API／CLI、默认profile／框架、旧checkpoint、导入／恢复／重建和后台均不得产生候选、读写、检索或注入。active refs为空并与实际请求核对，Trace记disabled/not_applicable、null hits/writes及feature_disabled。Case资料正常持久化；显式选入历史报告走SourceSet权限及私有祖先核验，不解引用Memory。04／17未实施、未验且非当前M1前置，预留闲置；重开需真实需求、独立审查与另行批准。 详细范围见[契约](docs/contracts/CURRENT_CONTRACTS.md)，Context归03a、Token归03b。

从2026-10-29起每周≤20h，原140–160h窗口须扣除已发生本人投入；实际已耗未知不填0。下表仅保留2026-11-01旧评审范围的估计，不是新增起草范围的工期或容量承诺。新文档版本、上传与交互尚无本人实耗，不能沿用总数；后续记录实际投入校准，超窗提交具体取舍。

| 旧评审纵切本人工作（历史估计） | 估计小时 |
| --- | ---: |
| 配置阅读、核对与验收准备 | 6–10 |
| ENV、认证与最小supervisor | 18–26 |
| Runtime、最小团队／项目与公开授权 | 18–26 |
| 公开文档证据与Context | 20–28 |
| Token／Gateway／canonical费用 | 12–18 |
| 首pilot最低独立备份恢复 | 6–10 |
| 公开pilot与症状诊断 | 8–12 |
| 本人解释与演示 | 4–6 |
| 合计 | **92–136** |

旧评审完整范围估计130–194h，Browser另8–14h亦为旧估计且真实接入延期；原100–144h及AI260–420 agent-hours仅解释旧范围，不能证明新工期。本轮目标为2027春招Agent应用开发／AI全栈正式岗位，Agent后端可靠性结合Vue3／TypeScript；地区、个人资格和掌握程度不推定。先依赖规划、不承诺工期，首个本人实践切片后按实际投入校准。AI辅助不代本人掌握：01追认证／store与404；02预测CAS／取消／失租；03沿quote核源并否决语义不支持；03a对照实际请求解释选排／裁剪与保护超限；04待另批后再做更正／撤销／满额；06亲改真bug回归；07解释原稿终稿／失败分母／计时；08解释恢复为何不复活权限。实际操作和业务接受由本人确认。

### 受控重启的实现位置

A的程序规则由[契约B5.2](docs/contracts/CURRENT_CONTRACTS.md#b52-supervisor)拥有：本人确认同一未替换目录且未restore／copy／PITR，程序不能发现漏报；异常／疑似还原不走A。02的假供应商阶段先完成全非终态Task收尾、未发预留及回执状态机；03b首次真实pilot前完成CONTROL_ONLY、新研究许可、费用／unknown、restrictedPg和paid-disabled进程验收。首工01仍只有认证／私人Draft／最小sup，不扩完整研究恢复；08b再扩完整故障覆盖。新Task／linkedTurn保原Case目的、累计量和绝对deadline，不重跑completed／unknown，不强制重跑仍有效资格。本人解释正常重启与异常恢复、预测竞争并亲验失败，未做不填掌握。

## 资金、资源和正式准备

费用epoch仍为2026-10-28，增量严格低于300元；旧账／unknown不得重开epoch抹零。唯一协议定义整批分配，契约定义准入及资源硬上限。七research Case是最高分配非自动grant，诊断／控制Task不获研究许可。条件预算296.46元不是余额或剩余可花，缺价格／币种／账／资金／grant／Token／最低恢复资格则paid off。Browser0无旧240调用额度。

本批仅公开材料索引待独立制备，精确题／controller／scorer未来独立准备并另审，不能入产品来源／Context／Memory。披露许可与实际显示分别记录，不明显示时点不参与有效saving，不换slot。

## 交付、回滚与历史映射

本轮完整配置自检→全部相关正文／committed、staged、unstaged和新增内容及diff／进入与当前指纹→新上下文独立技术和适用安全实施审查→核实修复／重测／必要复审→最终索引，才配置交付。原18项历史含义保持；首工、真实pilot、本人掌握、产品价值、M1、Go／发布分别报告。本轮回滚仅逆TEAM进入快照之后的自有hunk，先核后续工作并保留进入前17份修改与审计；原R2及更早进入／交付身份保持。不得reset／clean、破坏性降级数据库或自动恢复调用资格。

| 历史阶段 | 原需求／验收与证据 | 当前适用性 |
| --- | --- | --- |
| P-00/R0 | NFR-005→AC-N05；[R0](docs/tasks/R0_ACCEPTANCE_2026-10-20.md) | 原结构检查，不覆盖新配置 |
| P-01 | FR-001/002/005/006→AC-001/002/005/006；NFR-001/006/007→AC-N01/06/07；[假48/48](docs/tasks/P01_ACCEPTANCE_2026-10-21.md) | 原Windows／Pg，不证新WSL／Browser |
| P-02 | FR-002/003/004/007/010/013、NFR-002/004/010；DEC-AC-01–05/07 | r11／r12失败与离线修复按原版本，No-Go保留 |
| P-03 | FR-001/005/006/009/010/011/012；NFR-001/003/006/007/008/009 | 保原保护目的，不继承旧五账户／真实MCP规模 |
| P-04 | FR-004/007、NFR-002/005 | 旧15次只解释历史，不作新分母 |
| DEC-T01–13 | [原记录](docs/features/DECISION-001/tasks.md)、[T01](docs/tasks/DEC_T01_ACCEPTANCE_2026-10-23.md) | 已实现／未验／未实施分列，非新开工授权 |

PREP协议／旧材料按d4b906fb6a441c13583f052377283ec0c28bf5a2的原path／raw SHA解释；current-3原1ffade6de07ebe3d1e72afb4c44b8677466eca67身份及必要换行变换保持。原SQLite／r12／来源／授权／费用／上游受保护。配置交付后停在业务及准确环境授权前。

本轮首稿保护仅针对尚未首次尝试的工件：完整流程保护首需求与首方案各一次，其他模式一次；compile最多四次物理尝试，包含技术retry。首尝试失败转used不补满，修订仅用剩余额度；容量不足零发送，不能承诺成功。主子全部调用共享有界池，不借模式／Turn／新ID增额。两个既有pilot优先本人真实待办，一仅需求、另一完整链；产出前固定目标、当前普通AI／人工方式、关键正确项、可接受unknown及后续行动，之后分列原稿、人工补救和实际用途。已选案例B用于开发材料及后续另授完整链pilot，实际用途／收益仍待本人检验；案例A继续作研究适应性走查，均不替代正式材料。具体后继API／DDL及真实操作仍由另授业务包冻结。
