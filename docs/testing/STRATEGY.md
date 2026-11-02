# 按风险选择的配置检查与Agent验收策略

FOCUS-BASELINE-20261102只同步28文件及有界校验；[契约](../contracts/CURRENT_CONTRACTS.md)、[唯一协议](../evaluation/CURRENT_EVAL_PROTOCOL.json)定义参数，[唯一任务](../features/DECISION-001/tasks.md)记录命令/失败/审查/18项。配置、业务实现、真实运行、本人验收/掌握、价值、Go和发布分别取证。

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
..\.venv\Scripts\python.exe -B -m pytest -q -p no:cacheprovider tests/unit/test_validate_project.py tests/unit/test_current_evaluation.py tests/unit/test_pilot_runner.py tests/unit/test_pilot_capture.py tests/unit/test_project_ledger.py tests/unit/test_pilot_cost_reconciliation.py tests/unit/test_legacy_entry_guards.py
```

每次basetemp和日志选本轮audit下未存在的新目录，记录准确argv/cwd/env/exit/timeout及hash；缓存和遥测不写用户全局配置。测试中本地socketpair不算外部模型服务；权限阻止时保存失败，不修改测试掩盖、自动提权或安装。当前validator、显式材料未就绪拒绝、diff检查及三修改Python的Ruff/format-check并行口径一致。

需要回归：新draft-m1协议拒旧DR/20%和配额策略；六slot及原始/终稿gate分开；公开index拒gold及未知字段；默认配置有效仍materials未核；显式三包缺失/角色错/hash错/旧reviewreceipt/路径越界或链接/reparse/文件身份变化拒绝，错误不回显题文。先检查原路径组件再resolve，不跟随manifest任意ref。实际路径fixture不能运行时诚实skip，不能声称通过OS隔离。

严格JSON拒重复键(含转义等价)/NaN/Infinity/指数溢出非有限值，保有限int/float且bool不等int。保原字节微改拒绝、输入variant/output_requirements等严格语义；新材料入口等价覆盖而非删除旧修复。所有copy/hash/protocol/M1单向引用不自循环。旧current-3入口对新/坏/缺失协议必须先于Settings/client/engine/output/ledger写拒绝；历史固定Git/path/rawSHA/显式换行继续回归，不能借历史读取扩账。

旧621、原49/七文件200检查属于各旧字节，不证明本次文件。新测试数量与失败/修复/复审按本次实际记录。本批不需前端构建、数据库或全后端重跑，除非新失败提供相关理由；不运行模型/Tokenizer/Browser、远端CI。

## FOCUS-BASELINE-20261102覆盖（配置与后续业务分开）

本批限定配置回归应核draft-m1-2/材料角色版本、四模式义务、六阶段算术、4compile独占预留、三pair覆盖与pending身份；旧review协议不能混作current。既有--review-material-root与--review-material-index-sha256参数保留，不扩历史runner/ledger。历史review配置仅existing final-02 manifest/path/raw hash追溯，不冒充HEAD已有对象。

本批增加严格Memory policy keyset／类型／值与误开拒绝、M1 required／deferred冲突、Context错误依赖04、原Memory预算挪用、旧材料／回执／索引及新旧协议入口拒绝回归。新固定材料根为review-20261101/focus-20261102/materials，只更新预期引用，不制备角色包。显式旧draft-m1-1与实际draft-m1-2都应在Settings、价格、数据库、输出前拒绝。

当前M1关闭全部Memory功能入口，包括手动／自动、API／CLI、默认profile／框架Store预加载、旧checkpoint refs、导入／恢复／重建与后台路径；不提取候选、不读写、不检索、不注入，active Memory refs必须为空并与各模型阶段实际请求一致。Trace记disabled/not_applicable，hits／writes为null并附feature_disabled，不以测试零次冒充禁用证据，不要求空Store／seed／Memory快照。Case内条件、证据、文档和审计照常持久化；本人明确选定历史报告走SourceSet准确获许可版本，不解引用Memory refs，继续核当前权限和已知私有祖先。DEC-AC-17／DEC-M1-04保留延期、未实施／未验；完整Context属03a、Token资格属03b，当前M1不依赖04。真实复用需求、独立设计审查及准确范围另批后才可重开，原Memory预留容量保持闲置上界，不挪给其他功能。

未来业务测试另授后必须覆盖：全部模型阶段放置canary旧Memory对象／refs／profile preload／checkpoint／import／restore／rebuild／后台路径，均不可读取、生成候选、写入或注入；active refs为空且对照实际请求验证，Trace为禁用/null而非实测零。仅文档和协议关闭不冒称运行实验通过。

未来业务测试另授后必须覆盖：R1/C1生成S1期间R2保存、confirm与edit双序、start/send/commit三端检查及旧Call迟到仅audit/usage/cost；重复保存／双人保存CAS／409重载；显式保存才增版本，键入不耗16槽，logout换身份清内存。16版本、2MiB派生桶、首工件slot＋80KiB envelope＋Token＋canonical/terminal原子预留；无保存容量0send，模式变化同Case原目的接受并预留新增义务，跨Turn不重置，改需求不无限保首方案。

本地上传测试须含：累计32项、metadata16KiB、raw1MiB/UTF8正文512KiB、实际chunk计数而非信任Content-Length、非identity编码拒绝、坏UTF8、30s绝对截止、body parser前拒绝、不使用multipart spool；先核权/预留与提交重核的撤权双序、断流不假capture、未seal不送模型、部分成功/未读清单。路径仅元数据，diff不执行、未知基点不伪commit，File API不自证原系统无symlink或整个worktree原子。known private lineage不能用local profile/新ID/编辑洗白，外部未知不声称全检测。真实头/请求行/缓冲/超时与restrictedPg事务资格不能由fixture代替。

正式REQ保首需求、实际人工改动及确认、首方案、最终双文档包；raw失败不因人工修好改pass。CON两变体均含无权威基准子问，不将Agent建议当既有硬条件。EXP只在本人准确确认既有需求后起草。reqonly独立终止安排既有pilot之一，另一个pilot完整链；编辑／修订做聚焦回归，均不声称独立formal比较。六slot实际制备仍pending，本批不造题gold/seed。

## 历史限定修复(只解释原被审版本)

### CONFIG-RAWJSON-20261030 限定修复

本专项另获五文件批准，承接原40路径，不改变协议正文、原字节hash、业务权限或历史解析。CURRENT协议、DISCOVERY材料、M1引用三份原始输入都须严格JSON解码：任意层重复键（含转义后相同键）、NaN/正负Infinity及指数溢出非有限数值均拒绝；有限int/float保持原类型。只报固定错误类别及文件角色，不输出键、值、题面或JSON异常原文。材料output_requirements为非空字符串列表且每项非空白；variant与有效case ID后缀一致。字符串语义和评分答案隔离仍需独立实际材料审查。

三份原字节绑定JSON使用精确`-text whitespace=cr-at-eol`属性。测试通过只读`git cat-file --filters`，将同一固定Git LF blob按三个目标路径及autocrlf=true/input/false过滤，比较原字节；不写项目Git、不执行checkout，不把过滤器验证称完整clone/CI资格。主动编辑改字节仍由现有raw hash拒绝，不能自动规范化或重绑定掩盖漂移。

专项回归并入上列七文件命令，覆盖三个原始读取入口、错误输出无canary、有效有限数值、六题映射和非法输出要求元素；保留原字节微改拒绝、历史显式换行读取及旧入口guard回归。审查须读取五文件完整正文、本次进入字节增量、累计HEAD完整差异与两份既有新增文件；旧审查只复用于未变化内容。检查失败/修复重测/复审及最终封存仅追加到原审计目录，唯一任务记录和原18项承接结论。该校验器不执行研究或授予调用权限。

## 后续业务验证矩阵(全部待另授实施)

| Task/AC | 正常与必须失败边界 |
| --- | --- |
| DEC-M1-01 / DEC-AC-15 | 两真实login/cookie、个人Draft保存重开与另一owner404；CAS/容量/CSRF/Host/Origin；最小sup及Pg失连续；不创建研究Task或调用。 |
| 02 / 08/09/14 | 当前team/project/member/use grants；接受/幂等先CAS、双提交、队满无孤立；独立Taskgrant、取消/成功双序、真实LangGraph阶段/StageOutput/同步checkpoint切点。 |
| 03a / 10/11/12/18 | 完整Context保护集合、反证／限定超限0send；固定repoID/commit/path/blob，截断frontier、同名/同blob不合主体；原文/采集/摘要/结论分离；CRLF/中文Emoji UTF8locator；有关键词但不支持、未知版本反证、未读非不存在。 |
| 03b / 13/14/15 | send+commit/current lease/fence/gen/source/Memory禁用及空refs/model资格；App fresh proof/控制预算、public200不能续权限、完整query/URL披露；known retry vsunknown；Token/usage/cache/钱分账，60秒绝对截止。 |
| 04 / 17（延期，非当前M1必需） | 当前所有入口关闭，未实施／未验；未来另批后才检作者teamproject隔离、长期原文归属／否定／引用、TTL、更正／撤销／满额及tombstone／alias恢复；不作当前pass。 |
| 05 / 工具资格 | Browser=0真实接入延期；后续若另授必须独立连接层/bridge/sup资格，不使用当前无Browser预算冒充够。 |
| ENV-M1-02 / 14/15 | 首public pilot前最低独立介质纸钥真实恢复、同snapshot卡/密文身份、坏钥/末块/磁盘满/单侧失败目标隔离；旧库零写。 |
| 06 / 20 | 原真实症状→预目标→本人亲改→固定源回归/独审→另授≤2Case同条件真复测；漂移/改条件非修复收益，无真实症状则pending。 |
| 07 / 16/19 | Worker拒scorer/controller；实际显示和披露许可不同、ack丢失/时钟不明不洗计时；六slot全保，3rawAgent关键项gate与6final质量/描述省时分开，无20%或强制DR。 |
| 08b / 15/19/20 | 当前read session/account/sup/sourceproof每response/page/frame重核；撤权双序/有界inflight，Trace跨team拒/私源撤权、离线不replay、完整恢复及本人成功/失败演示。 |

canonical审计与业务同tx，UI cap不删Call/证据/费用；没有审计或terminal预留不新send。只安全元数据日志，不prompt/key/cookie/私有URLnonce/CoT。离线重建只读已有bytes/hash/关系/selector/计时/usage算术，缺坏not_reconstructible；Tokenizer执行另授。诊断区分未采集/未识别/未绑定/未选/裁剪/摘要失真/输出未体现，不推测模型内部。

实现后提供全部28正文、完整committed/staged/unstaged/new审计内容及实际checks，冻结后交非作者技术/安全实现审查；核实发现再修、重测、受影响独立复审。设计审查、旧审查或CI不替当前实现审查。人核源/读码/预测/亲改/回归及掌握由本人确认。
