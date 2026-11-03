# 按风险选择的配置检查与Agent验收策略

TEAM-BASELINE-20261103-01对应已确认完整团队研发计划及当前“PLEASE IMPLEMENT THIS PLAN”阶段0配置对齐：限定现有配置、有界离线检查／新审计。R2及更早交付保持原字节和范围，旧344passed／1skipped不冒本轮结果。[契约](../contracts/CURRENT_CONTRACTS.md)定义运行约束，[唯一协议](../evaluation/CURRENT_EVAL_PROTOCOL.json)定义正式质量／计时／槽位与整批资金，[唯一任务](../features/DECISION-001/tasks.md)记录命令、失败、审查和原18项历史。配置、业务实现、真实运行、本人验收／掌握、实际价值、Go和发布分别取证。

| 层 | 对象 | 不可替代的证据 |
| --- | --- | --- |
| L0 | 严格JSON/类型/hash/链接/范围/算术/版本 | 不证明语义核源、实际许可或运行 |
| L1 | 固定fixture的解析、准入、状态和失败 | 不冒充真实任务 |
| L2 | API/DTO/事件/归属/持久确认 | 未来业务授权，不由配置创造 |
| L3 | restrictedPg独立连接并发 | 缺库skip或Mock不替代真实事务 |
| L4 | UI→API及Windows本人操作 | 本人确认，不代填已掌握 |
| L5 | 进程/失租/unknown/取消/资源/恢复 | 真实进程和双序，非假异常即可 |
| L6 | 另授权真实任务/源核查/费用/改进 | 原始与人工终稿、对照、省时独立 |

## 本配置批次检查

只用已安装D盘根.venv。在backend目录的聚焦套件为：

```text
..\.venv\Scripts\python.exe -B -m pytest -q -rs -p no:cacheprovider -p pytest_asyncio.plugin tests/unit/test_validate_project.py tests/unit/test_current_evaluation.py tests/unit/test_pilot_runner.py tests/unit/test_pilot_capture.py tests/unit/test_project_ledger.py tests/unit/test_pilot_cost_reconciliation.py tests/unit/test_legacy_entry_guards.py
```

每次basetemp和日志选本轮audit下未存在的新目录，记录准确argv/cwd/env/exit/timeout及hash；缓存和遥测不写用户全局配置。测试中本地socketpair不算外部模型服务；权限阻止时保存失败，不修改测试掩盖、自动提权或安装。当前validator、显式材料未就绪拒绝、diff检查及两修改Python的Ruff/format-check并行口径一致。

需要回归：新draft-m1协议拒旧DR/20%和配额策略；六slot及原始/终稿gate分开；公开index拒gold及未知字段；默认配置有效仍materials未核；显式三包缺失/角色错/hash错/旧reviewreceipt/路径越界或链接/reparse/文件身份变化拒绝，错误不回显题文。先检查原路径组件再resolve，不跟随manifest任意ref。实际路径fixture不能运行时诚实skip，不能声称通过OS隔离。

严格JSON拒重复键(含转义等价)/NaN/Infinity/指数溢出非有限值，保有限int/float且bool不等int。保原字节微改拒绝、输入variant/output_requirements等严格语义；新材料入口等价覆盖而非删除旧修复。所有copy/hash/protocol/M1单向引用不自循环。旧current-3入口对新/坏/缺失协议必须先于Settings/client/engine/output/ledger写拒绝；历史固定Git/path/rawSHA/显式换行继续回归，不能借历史读取扩账。

旧621、原49/七文件200及FOCUS 297 passed／1 skipped检查属于各旧字节，不证明本次文件。新测试数量与失败/修复/复审按本次实际记录。本批不需前端构建、数据库或全后端重跑，除非新失败提供相关理由；不运行模型/Tokenizer/Browser、远端CI。

## 当前配置回归与后续行为分开

本批限定回归核原字节draft-m1-3／新能力引用draft-m1-capabilities-5与pending材料、本机双身份／指定确认角色／必要撤销预留／单链先pilot且动态私源仍必需的映射、四模式、六用途固定单次上限及共享有界池；固定用途次数残留、总量越界、purpose错配、隐藏调用、跨Turn或换ID重置必须拒绝。首工件只预留尚未尝试的首次尝试，失败不补满；optional不得侵占，compile第五次或retry绕四次物理上限必须拒绝。既有显式材料参数保留，不扩历史runner／ledger。

本批保留严格Memory keyset／类型／值、误开拒绝、required／deferred冲突、Context错误依赖04、原容量挪用、旧材料／回执／索引及新旧入口拒绝回归。新材料预期根research-20261103/materials，仅更新pending引用、不制角色包。draft-m1-1、draft-m1-2和当前draft-m1-3都不得驱动旧运行器。

Memory全部功能入口继续禁用并延期：手动／自动、API／CLI、默认profile／框架、旧checkpoint、导入／恢复／重建和后台均不得产生候选、读写、检索或注入。active refs为空并与实际请求核对，Trace记disabled/not_applicable、null hits/writes及feature_disabled。Case资料正常持久化；显式选入历史报告走SourceSet权限及私有祖先核验，不解引用Memory。04／17未实施、未验且非当前M1前置，预留闲置；重开需真实需求、独立审查与另行批准。 具体入口及参数以[契约](../contracts/CURRENT_CONTRACTS.md)为准；以下是未来程序验收规格，不是本轮实验结果。

本轮校验器必须对批准修订及预期原始hash建立独立锚点；同一次有界raw读取同时用于hash、严格JSON解析、引用链及不变量，不能hash根文件却检查外传dict。纯结构helper fixture不等于当前bundle通过。原字节微改、未批准策略改动、错引用链及读取后替换的负例分别保留，禁止生产skip-hash或自动重绑定。

Token负例区分本地公开格式／托管fit／实际usage：合法非零差异保留，越界或供应商协议异常撤资格、业务JSON不合格不误撤，unknown费用全停，重资格不自动重领诊断。静态字段和fixture只检查配置／算法，真实Tokenizer、API和费用资格未验。

未来业务测试另授后必须覆盖：全部模型阶段放置canary旧Memory对象／refs／profile preload／checkpoint／import／restore／rebuild／后台路径，均不可读取、生成候选、写入或注入；active refs为空且对照实际请求验证，Trace为禁用/null而非实测零。仅文档和协议关闭不冒称运行实验通过。

未来业务测试另授后必须覆盖：首尝试失败转used不补预留、retry／四compile／总物理上限交叉、子任务和可选修订不侵首尝试资源；R1/C1生成S1期间R2保存、confirm与edit双序、start/send/commit三端检查及旧Call迟到仅audit/usage/cost；重复保存／同发起者双窗口保存CAS／其他成员写入拒绝／409重载；原发起者离队或禁用后，管理员／指定确认人不能借新接受或linkedTurn接管同Case，管理撤权不授编辑／取消／接续权，关联Case不自动获新grant或配额；显式保存才增版本，键入不耗16槽，logout换身份清内存。16版本、2MiB派生桶、首工件slot＋80KiB envelope＋Token＋canonical/terminal原子预留；无保存容量0send，模式变化同Case原目的显式接受并预留新增义务，否则拒扩／partial，不自动新Case洗额度；跨Turn不重置，改需求不无限保首方案。

TEAM角色的未来L2/L3/L4验收必须覆盖：同一账户兼任与双身份分工；发起者能编辑／接受／取消／显式接续，确认人只能准确确认／撤销，其他成员只读或另建Case；模型／body／CLI数据库凭据不能自授角色或研究许可。无确认人仍可需求／评审、拒方案；确认时核当前来源读取和确切head／策略／账户／成员资格，拒过期expected revision及异body operation。

restrictedPg独立连接barrier覆盖角色A→B→A、离队重入、disable→enable、新requirements head与方案start/send/commit双序；旧确认不可复活，失效先提交拒新send／commit，合法先claim仅承认有界在途／迟到audit，不能宣称物理召回。logout／自然expiry／凭据轮换不自行撤销内容确认，源权限丢失仍独立阻当前使用。新CLI写入与shutdown receipt／pending rearm竞争必须作废对应旧资格，不以角色配置开研究。

容量检查按契约实际封装计数：每种资格及每个当前确认的撤销预留独立；普通空间耗尽后撤多个确认，再分别disable、撤成员、清项目确认人，全部安全操作仍能记录，不借其他预留／Memory。确认创建无足够普通bytes及撤销预留时原子拒绝；同operation重放不重占、异body409，不变策略不增revision且新回执不能挤撤销空间。真撤销后重确认须新预留；只有根事务证明旧确认永久非当前才有界释放一次，临时sourceproof不可用不能释放。

首次真实public full pilot只在单链核心／03a离线链及原最低恢复／Gateway／Token／全账资金／来源／rearm关口全满足后另授；动态关闭但安全内核不删。后续动态assignment／共享消费者合入后，重跑受影响四模式、保护Context、Gateway和撤权／取消／seal／恢复竞争，再验私源。动态和私源仍必需于完整M1，提前pilot不能关闭父AC。五项任务包检查和原稿／人工补救负担记录不另立formal评分或槽位。

本地上传测试须含：累计32项、metadata16KiB、raw1MiB/UTF8正文512KiB、实际chunk计数而非信任Content-Length、非identity编码拒绝、坏UTF8、30s绝对截止、body parser前拒绝、不使用multipart spool；先核权/预留与提交重核的撤权双序、断流不假capture、未seal不送模型、部分成功/未读清单。路径仅元数据，diff不执行、未知基点不伪commit，File API不自证原系统无symlink或整个worktree原子。known private lineage不能用local profile/新ID/编辑洗白，外部未知不声称全检测。真实头/请求行/缓冲/超时与restrictedPg事务资格不能由fixture代替。

正式REQ保首需求、实际人工改动及确认、首方案、最终双文档包；raw失败不因人工修好改pass。CON两变体均含无权威基准子问，不将Agent建议当既有硬条件。EXP只在本人准确确认既有需求后起草。reqonly独立终止安排既有pilot之一，另一个pilot完整链；编辑／修订做聚焦回归，均不声称独立formal比较。六slot实际制备仍pending，本批不造题gold/seed。

formal继续同一真实参与者，可同一账户作为发起者及项目确认人；所有本人实际操作计入原主动时间。跨账户角色竞争与交接仅作独立集成资格，不增加formal槽位、不冒真实团队效果；不同真实确认人不混入原formal计时口径。

## 历史限定修复(只解释原被审版本)

### CONFIG-RAWJSON-20261030 限定修复

本专项另获五文件批准，承接原40路径，不改变协议正文、原字节hash、业务权限或历史解析。CURRENT协议、DISCOVERY材料、M1引用三份原始输入都须严格JSON解码：任意层重复键（含转义后相同键）、NaN/正负Infinity及指数溢出非有限数值均拒绝；有限int/float保持原类型。只报固定错误类别及文件角色，不输出键、值、题面或JSON异常原文。材料output_requirements为非空字符串列表且每项非空白；variant与有效case ID后缀一致。字符串语义和评分答案隔离仍需独立实际材料审查。

三份原字节绑定JSON使用精确`-text whitespace=cr-at-eol`属性。测试通过只读`git cat-file --filters`，将同一固定Git LF blob按三个目标路径及autocrlf=true/input/false过滤，比较原字节；不写项目Git、不执行checkout，不把过滤器验证称完整clone/CI资格。主动编辑改字节仍由现有raw hash拒绝，不能自动规范化或重绑定掩盖漂移。

专项回归并入上列七文件命令，覆盖三个原始读取入口、错误输出无canary、有效有限数值、六题映射和非法输出要求元素；保留原字节微改拒绝、历史显式换行读取及旧入口guard回归。审查须读取五文件完整正文、本次进入字节增量、累计HEAD完整差异与两份既有新增文件；旧审查只复用于未变化内容。检查失败/修复重测/复审及最终封存仅追加到原审计目录，唯一任务记录和原18项承接结论。该校验器不执行研究或授予调用权限。

## 后续业务验证矩阵(全部待另授实施)

| Task/AC | 正常与必须失败边界 |
| --- | --- |
| DEC-M1-01 / DEC-AC-15 | 两真实login/cookie、个人Draft保存重开与另一owner404；CAS/容量/CSRF/Host/Origin；最小sup及Pg失连续；不创建研究Task或调用。 |
| 02 / 08/09/14 | 当前team/project/member/use grants；同Task Assignment版本／幂等／替换、共享消费者独立核权及取消、研究输入封存／迟到audit／关键义务未满足；接受/幂等先CAS、双提交、队满无孤立；独立Taskgrant、取消/成功双序、真实LangGraph阶段/StageOutput/同步checkpoint切点。 |
| 03a / 10/11/12/18 | 完整Context保护集合、反证／限定超限0send；固定repoID/commit/path/blob，截断frontier、同名/同blob不合主体；原文/采集/摘要/结论分离；CRLF/中文Emoji UTF8locator；有关键词但不支持、未知版本反证、未读非不存在。 |
| 03b / 13/14/15 | send+commit/current lease/fence/gen/source/Memory禁用及空refs/model资格；App fresh proof/控制预算、public200不能续权限、完整query/URL披露；known retry vsunknown；Token/usage/cache/钱分账，60秒绝对截止。 |
| 04 / 17（延期，非当前M1必需） | 当前所有入口关闭，未实施／未验；未来另批后才检作者teamproject隔离、长期原文归属／否定／引用、TTL、更正／撤销／满额及tombstone／alias恢复；不作当前pass。 |
| 05 / 工具资格 | Browser=0真实接入延期；后续若另授必须独立连接层/bridge/sup资格，不使用当前无Browser预算冒充够。 |
| ENV-M1-02 / 14/15 | 首public pilot前最低独立介质纸钥真实恢复、同snapshot卡/密文身份、坏钥/末块/磁盘满/单侧失败目标隔离；旧库零写。 |
| 06 / 20 | 原真实症状→预目标→本人亲改→固定源回归/独审→另授≤2Case同条件真复测；漂移/改条件非修复收益，无真实症状则pending。 |
| 07 / 16/19 | Worker拒scorer/controller；实际显示和披露许可不同、ack丢失/时钟不明不洗计时；六slot全保，3rawAgent关键项gate与6final质量/描述省时分开，无20%或强制DR。 |
| 08b / 15/19/20 | 当前read session/account/sup/sourceproof每response/page/frame重核；撤权双序/有界inflight，Trace跨team拒/私源撤权、离线不replay、完整恢复及本人成功/失败演示。 |

两个案例仅作静态配置走查：养老助手区分用户困难、平台能力和风险候选，GPT Researcher固定版本区分既有编辑／聊天与新需求确认。它们不是正式题／gold或真实用户价值证据。

canonical审计与业务同tx，UI cap不删Call/证据/费用；没有审计或terminal预留不新send。只安全元数据日志，不prompt/key/cookie/私有URLnonce/CoT。离线重建只读已有bytes/hash/关系/selector/计时/usage算术，缺坏not_reconstructible；Tokenizer执行另授。诊断区分未采集/未识别/未绑定/未选/裁剪/摘要失真/输出未体现，不推测模型内部。

实现后提供本轮任务自有文件完整正文、完整committed/staged/unstaged/new审计内容及实际checks；进入前17份修改和历史基线保护另核，冻结后交非作者技术/安全实现审查；核实发现再修、重测、受影响独立复审。设计审查、旧审查或CI不替当前实现审查。人核源/读码/预测/亲改/回归及掌握由本人确认。

## R2受控重启A与跨Turn的分层验收规格

以下为未来程序规格，非本批业务测试。A限定可信操作者确认同一未替换目录且未restore／copy／PITR，程序不能检测漏报旧库还原；异常中断、证据不齐或疑似还原隔离。细则以[契约B5.2](../contracts/CURRENT_CONTRACTS.md#b52-supervisor)为准。

| 连接／层次 | 正常轨迹 | 反例／保留边界 |
| --- | --- | --- |
| 跨Turn；L1→L3→L4 | 首需求partial→编辑准确确认→linkedTurn→新Task seal引用前轮有权已提交证据→方案；最终双稿同确认 | 确认／终结双序、head变化、前轮late audit晋升、旧确认复活、Casecap／deadline重置 |
| 停机；L1→L3→L5 | 全queued／running／recovering业务与control Task确定终结，active清、终态唯一；未发许可作废，Attempt先fenced，资源收拢后closed | 排队遗留、admitted reserve未清、sent／Token／首attempt used返还、终态先释放在途槽 |
| clean回执；L3→L5 | 当前连续generation、物理调用／旧出口收拢、费核清且无未解决unknown停线后，窄coordinator最终回执 | 未知费／未收拢仍clean、回执后撤权／更正未先同事务作废、满metadata仍写或借Memory |
| rearm；L1→L3→L5 | 新boot研究closed→只读核证／未还原陈述→新CLI→本人精确CONTROL_ONLY→当前资格→新research许可 | 旧cookie／grant／Attempt／proof复活、旧receipt重放、提交不明换ID、资格半成崩溃仍开放研究 |
| 资格／费用；L1→L3→L6另授 | 有效资格核版本不强制新诊断，控制请求原allocation，unknown全停；历史unknown Call保留不重发 | 控制耗尽仍调用、mint unknown／价格过期／余额不明却research、rearm自动清停线、倒填已知结果 |
| 本人实践；L4／L5 | 解释A与异常恢复、原Case量／deadline不暂停、内容确认与新执行许可分离；亲验正常／失败 | 将可信陈述当机器最新性证明、模拟当Pg／进程／供应商实证、代填本人已掌握 |

旧执行器三条静态风险作为ENV隔离及未来业务回归规格：runner.py:441–453缺price-book可走无预算首调，pg_store.py:456–472取消先提交仍可能completed，github_tool.py:48–53的传输RequestError被转technical failed后由agent_loop.py:390–402重试。准确固定HEAD、机制和未运行限制见[日期化补研](../research/PREDEV_CONFIGURATION_REVIEW_2026-11-03.md#12-2026-11-03-r2受控重启与首闭环补研)。本批不修业务、不启动旧服务；相应假供应商、MockTransport及restrictedPg双序以后另授。

03b首次真实pilot前须完成A的离线、restrictedPg及paid-disabled进程验收；最低独立备份、Token／资金／来源资格不豁免。当前配置套件仅核能力映射、原协议／索引hash与越权声明负例，不证明A已实现。两个既有pilot中的完整链优先GPT Researcher案例B，登记预读／已知发现及普通AI／人工基线，不作formal gold，不增次数／费用。
