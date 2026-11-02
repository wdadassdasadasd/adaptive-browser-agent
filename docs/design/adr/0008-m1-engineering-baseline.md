# ADR-0008：需求与方案起草工程基线与历史决定

当前状态：**FOCUS-BASELINE-20261102，28文件配置同步已批准，当前实际检查／独审／交付待证**。[唯一任务／18项](../../features/DECISION-001/tasks.md)记录结果；[SPEC](../../../SPEC.md)、[PLANS](../../../PLANS.md)、[契约](../../contracts/CURRENT_CONTRACTS.md)、[唯一协议](../../evaluation/CURRENT_EVAL_PROTOCOL.json)定义当前行为。本ADR记录决定理由与替代范围，不另列参数权威。

## 2026-11-02 FOCUS决定（当前）

本人选择保留四模式、团队目标及真实阶段图，将Memory移出当前M1必需范围；这不是确认旧配置缺陷，也不否定旧交付。PLEASE IMPLEMENT THIS PLAN准确批准FOCUS-20261102-01的28路径、限定离线检查及新focus审计，业务／环境／真实运行仍未授权。

当前M1关闭全部Memory功能入口，包括手动／自动、API／CLI、默认profile／框架Store预加载、旧checkpoint refs、导入／恢复／重建与后台路径；不提取候选、不读写、不检索、不注入，active Memory refs必须为空并与各模型阶段实际请求一致。Trace记disabled/not_applicable，hits／writes为null并附feature_disabled，不以测试零次冒充禁用证据，不要求空Store／seed／Memory快照。Case内条件、证据、文档和审计照常持久化；本人明确选定历史报告走SourceSet准确获许可版本，不解引用Memory refs，继续核当前权限和已知私有祖先。DEC-AC-17／DEC-M1-04保留延期、未实施／未验；完整Context属03a、Token资格属03b，当前M1不依赖04。真实复用需求、独立设计审查及准确范围另批后才可重开，原Memory预留容量保持闲置上界，不挪给其他功能。

代价是首阶段不展示跨Case自动复用；收益是从真实任务验证复用需求后才承担存储、更正、撤销、恢复及隔离机制。普通AI＋人工与更窄技术调查仍为实质候选，当前没有效果或需求实证。若重复真实任务显示显式SourceSet复用不足，才重开受影响设计。DRAFT按final-01、REVIEW按final-02原字节继续有效。

## 2026-11-02起草范围（保留决定及原理由）

用户明确要求既有需求／方案评审之外，产出新需求／方案草稿，讨论交互进行；依次选择两种起点、先确认需求再方案、工程实施细度、按需只读源码、选定本地文件／差异、窗口完整闭环优先、直接编辑＋对话修订，并接受模型重分配和三对不同流程覆盖；本次PLEASE IMPLEMENT THIS PLAN授权28现有文件配置同步，不授业务／环境／真实运行。

| 保留／调整 | 依据、收益与代价 | 适用边界／可推翻证据 |
| --- | --- | --- |
| 保留API/Worker/Pg/Gateway/sup与证据、费用、恢复 | 原review交付经核实有效；新增目标不要求新框架或协作体系 | 目标未实现；实际并发/恢复资格失败须按证据重开，首工不扩 |
| 四模式，需求先确认再方案 | 用户要求从想法及已有材料均能产出，保review；比纯报告增加版本／确认事务与学习负担 | 无真实任务，不宣称价值；若真实任务普通AI更合适或确认成本超过收益则重评 |
| SourceSet及选定本地text/code/diff | 可呈现未提交内容，读取范围由显式上传界定 | 无FS bridge/代码执行，不伪工作树原子与未知diff基点；真实transport尚待验 |
| 不可变DocumentVersion与精确确认 | 保作者／首稿／修订及来源；新需求head原子失效当前确认，方案start/send/commit核准确绑定 | R1/C1→R2旧S1迟到不得发布；双序和容量并发未实测，失败即可推翻实现正确性 |
| 14normal/最多16physical，四compile独占 | extract及evidence工作重分配到双首稿／有限语义修订；无额外repair/summary/隐藏judge | 首工件模型/版本/bytes多维预留；改版后非无限方案，效果待pilot；精确数值唯一契约／协议 |
| REQ full／CON review／EXP solution-only | 三对覆盖不同流程，不加formal/Case/资金；REQ双首稿与双终稿包分别记录 | 仅需求独立结束、编辑／对话修订只回归/pilot，不各自formal效果；材料仍pending |
| 窗口闭环优先，不沿用旧工时 | 用户7–8周≤20h周不扩；旧92–136/130–194非实测且未覆盖新增 | 新范围本人实耗未知，不承诺完成工期；私源App/Memory/正式材料/完整恢复后置，最低live恢复仍前置 |

上游新增证据：GPT Researcher的人工反馈路由修订超限会accept，不能借其角色或测试代替本项目强制确认；DeerFlow工件交付可在多个产物只展示一个时成功，不能证明本项目双稿齐全；Spec Kit已有起草工作流，额外产品价值要实证而非“能写文档”。固定源码/测试与条件见研究文档，本项目未运行它们。

原review28正文完整文件/差异、进入与最终指纹、原始授权及检查/独审已核，未确认新原基线缺陷；新候选技术兼安全复审DONE，不是新增配置字节实现独审。候选发现的旧确认竞争、多维预留、模式义务和无权威基准评测缺口已静态关闭，后续新正文仍须实际检查和独审。原review字节按现有final-02 manifest/path/raw hash追溯，不冒称HEAD；旧索引不改写为审过新字节。

## 2026-11-01决定与变化前提（历史，仅解释原review字节）

本轮只读核验确认原40路径封存及五文件raw JSON修复有效，未把它们重复列为缺陷。产品定位来源需重新检验，暂无真实任务；固定版本研究显示成熟实现的检索／工具／持久运行机制不能证明本项目用户效果。用户先选择资料到交付物，再确认开发团队文档评审包，随后逐项决定P2/A1/R2/T2/C1/D1/E2与整体G1/G2/G3。原批准不是本轮新决定；设计审查不是实现审查。

| 本轮决定 | 新依据、收益与代价 | 受影响范围／未验证 |
| --- | --- | --- |
| P2：单主GitHub文档需求／方案证据评审包，team已入项目资料共享 | 比旧单一技术选型扩大交付物；user选择而非已证真实需求 | 目标、AC、报告与来源；私源／分享／模型许可负担增加，真实价值待证 |
| A1：保API／Worker／Pg及sup，team/member/source与creator分别归属 | 应用权威和运行闭环保留；checkpoint只是refs | 首工仍私人auth/Draft，后继team；成员离队、管理员接管不洗身份／Case |
| R2：独立Task执行许可、控制Task、sync checkpoint、发送与提交双核 | UI关闭不误取消，late与恢复有明确权威；增加竞争与资源收拢验证 | completed/unknown不重发；控制Task无研究权；reaper只安全已有refs |
| T2：App installation／repo权限及五分钟fresh签发proof，direct adapters | 公开200不代表App仍被授权，freshreceipt保守；控制调用／秘密管理有代价 | 上游ACL与本地成员分开；私源proof过期可使旧报告不可读；真实资格待验 |
| C1：问题basis三分、版本化capture精确引用、先词法检索 | 原材料小、路径与标题可解释；无向量并非无检索增强 | 不照搬英语BM25或无命中首页回退；未读非不存在，语义靠人核 |
| D1：受限自动Memory同author/team/project、官方完整本地编码 | 保本人选择自动偏好与cue，收紧跨项目污染；误存与撤销仍有成本 | 私有祖先不洗白；Tokenizer与托管模型匹配未证paid off；extra摘要／repair0 |
| E2/G2：质量工程先行，三原始Agent稿关键项全部过；六final仅描述省时，DR按需 | 人工修稿不能洗原始失败；旧20%与强制DR不匹配新场景 | 新六材料待独立制备，真实任务和本人价值仍pending，旧实验不改判 |
| G1：逐response/page/frame当前读claim；完整query披露 | 长SSE旧会话不能沿旧权限续读；单词公开不证明组合query公开 | 最后一个有界已claim响应可在途，用户已接受；无瞬时召回保证 |
| G3：公开manifest／受限三包，许可与实际显示分离 | gold不能混产品输入；DB提交不是人已见题；更多角色／路径／审查绑定 | 本批只pending公开索引；路径reparse和显示不明均拒／不计saving |
| 窗口公开纵切优先，Browser真实接入延期0 | 新team/App/privateproof/Memory等不能沿用旧工时；减少窗口承诺 | 92–136h估计非实测，完整130–194h后续，不豁免public pilot最低恢复／资金资格 |

收益不是已验证性能、节省或招聘结果；源版本、协议、价格、资源实测或真实任务若推翻前提，只重开受影响决定并由本人确认，不自行扩scope。

## 仍保留的原设计理由（2026-10-29历史记录）

原PREP-BASELINE-20261029批准40路径配置及限定validator／legacy guard，原产品是从零发现候选的技术调研助手，首起点“居家老人陪伴问答”；三对旧领域、20%门槛、每题独立DR、完整范围优先与100–144h等仅解释当时范围，已由上述新决定替代。原40路径与后续五文件修复并未因产品重评而失效，亦不能覆盖本轮新字节。

下表保留原候选采用理由／代价；其中具体运行行为以本轮契约收紧或替代，不作为第二套当前规则。

| 决策及来源 | 采用理由与代价 | 未验证及重评证据 |
| --- | --- | --- |
| 本人委托AI选择、AI明确宣布LangGraph | 实际阶段节点、有限分支和可检查重入；比单自建loop有框架依赖/锁版本代价 | 不能整体包旧loop；依赖兼容和本项目质量须验，框架不是效果证据 |
| 本人选择WSL独立API/Worker/Pg与独立新cluster | 同Linux运行和独立故障诊断；旧Windows/Pg可用不等于新路径；新库/凭据避免混写 | Linux路径/资源/连接和冷切未验；旧5433及SQLite只读取证，不能重置旧费用/unknown |
| 本人选择Search/GitHub/Fetch优先、direct API及DeepSeek单Search/Fetch | 限制供应商与连接复杂度，可替换适配；无自动双供应商fallback | Provider内部Fetch连接不可观察；未知字段由应用strict校验，Browser需连接层资格 |
| 本人选择S1工件同Pg | 响应与Call完成同事务、单库快照可含证据 | 存储/WAL/恢复代价；业务1GiB与物理资源另算；大二进制必要时才重评 |
| 本人选择结构关系＋关键词、受限自动记忆 | 小规模可解释取回，避免向量/embedding/reranker依赖；来源线索及长期技术偏好自动可见建议 | 偏好语义保守漏收、sourcehint未知别名、反证未识别风险；不积累程序策略或敏感画像 |
| 本人决定repair=0、Tokenizer正式准入、thinking disabled；整包批准summary=0 | 防隐含调用/价格与重试绕行，完整请求可审计 | Tokenizer模板/模型/版本资格与线上usage不等同；首次诊断有限另授 |
| unknown策略由本人委托AI、AI明确宣布全项目停新出站 | 不用plan/query/Work/Turn绕过；在途保留身份/预留，人工对账后另批恢复 | 无法撤回已claim请求；迟到结算不自动开闸 |
| 本人选择supervisor连续许可及首工即最小监督 | 同连续Sup/Pg下API可重启；失连续账号/研究/记忆隔离 | 增加IPC/进程和故障路径；DB的OPEN或UUID不自证最新；无证明不恢复paid |
| 本人选择开发本机恢复、pilot前独立介质；借优先、纸钥 | 小规模开发先练恢复，真实运行前补抗单盘故障介质 | 介质/纸卡/私钥及真实恢复未建立；临时可信主机解密不承诺无OS残留 |


## 当前调用链与七专项

私人raw Draft→明确加入team/project的目标与选定材料→Case受限澄清／接受模式→Worker/LangGraph研究与取源→question/Claim/反证→保护Context→需求版本→本人准确确认→方案版本→ReportSnapshot引用交付包→当前权限下UI／各Markdown→编辑／对话修订／核源／linkedTurn。review_only沿原评审链，requirements_only可独立结束，solution_only先确认需求。所有物理调用经Gateway最终claim；提交再次核租约、principal、source、Memory禁用状态／空refs及模型资格，不读取Memory对象。原事实／事件／费用由Pg拥有，checkpoint／缓存没有授权权。

产品、架构、Runtime、Tools、证据、Context/Memory/Token、Evaluation/Tracing七项在契约和AC相互映射；Runtime02/03b，Tools／证据03/延期05，Context03a/Token03b，Memory04延期且非当前M1前置，Eval／优化06/07/08。版本/确认在02，选定本地有界上传/封定及双稿在03a，首次无模型auth/Draft/sup为01，08a最低备份恢复前置public pilot，08b完整恢复后继，不构成循环。

## 固定证据与适用边界

研究固定版本：GPT Researcher3582a6841fe7dc801e2a34e34ee408641aea9bce、DeerFlow60940ae9c528e5d740b27d058f2c5d80565a71b7、LangGraph3cd57c038ad827d05f80c6488adea9994156c58c、MCP SDK0921d94a74db900dccd2d534842aa7b6160542d2、DeepSeek recipe935817c66f5d6e64838f419692545f06787e485f；文件／符号、合并修复／测试、观察日期与未运行见[机制研究](../../research/HIGH_STAR_AGENT_MECHANISMS_2026-10-22.md)和任务审计。上游行为与离线替身不冒本项目运行，Star不是采用证明，官方Tokenizer存在也非本地匹配已资格。

本轮重要专项、整体技术／安全及受影响设计复审已获得；FOCUS当前28文件完整正文／diff／检查仍需新上下文实际文件独审与必要复审，不能用设计或旧实现报告代替。没有运行测试、模型或环境的研究结论不填为运行通过。

首工缺实际ENV／新库与身份资格；public pilot另缺账／unknown／余额／grant、Token／Gateway与最低独立介质纸钥恢复；Browser0。新正式题／gold、原稿质量、真实纠错、本人理解／操作与真实价值各自待证。配置交付、开发准备、首工、pilot、完整首阶段、M1、Go与发布分别裁决；P-01假48/48和r11/r12失败不被新规格抹掉。
