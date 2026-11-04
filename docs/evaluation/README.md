# 需求／方案研究起草的评测入口

当前配置为**DEV-STAGES-20261104-01**，当前只实施P0。工程路线与逐片验收见[PLANS](../../PLANS.md)；[CURRENT_EVAL_PROTOCOL](CURRENT_EVAL_PROTOCOL.json)仍为原字节draft-m1-3，独占整批资金及已启动效果包内部规则；[M1引用](DECISION_M1_PROTOCOL.json)升级capabilities-6，分离六阶段工程验收与显式按需效果，不另立资金或Go。[唯一记录](../features/DECISION-001/tasks.md)保实际结果及原18项。配置通过不授权运行。

## 配置、材料与运行分开

[DISCOVERY_M1_CASES](DISCOVERY_M1_CASES.json)沿用原路径，但现在只是公开材料索引 `draft-m1-material-index-1`。本批不制备新正式题面或金标；状态为 `pending_independent_material_preparation`，三个包身份为 null。没有真实任务、正式结果或本人验收证据。

索引只保留三个公开类型（requirements／consistency／exploration）、六个 slot ID、公开 rubric、准备状态及包／审查身份。精确题面、对照卡和关键答案分别放在受限本地 `inputs.json`、`controller.json`、`scorer.json`，不发布至产品来源或注入 Context／Memory。Worker／评分器的真实隔离属于后续业务包，不是本批文档已实现的 ACL。

核对顺序为：非实现作者制备 → 非作者实际材料独审 → 固定三包原字节及原始审查 → 公开索引 → 唯一协议 → M1引用。引用方向不得自循环；正文改变后旧审查不再覆盖。公开资料和熟悉度须披露，不能声称真正盲测。

## 当前Memory禁用与新流程覆盖

Memory全部功能入口继续禁用并延期：手动／自动、API／CLI、默认profile／框架、旧checkpoint、导入／恢复／重建和后台均不得产生候选、读写、检索或注入。active refs为空并与实际请求核对，Trace记disabled/not_applicable、null hits/writes及feature_disabled。Case资料正常持久化；显式选入历史报告走SourceSet权限及私有祖先核验，不解引用Memory。04／17未实施、未验且非当前M1前置，预留闲置；重开需真实需求、独立审查与另行批准。 权威范围见[契约](../contracts/CURRENT_CONTRACTS.md)，本页只定义核验方法。

### 新流程覆盖与结论边界

三对六slot沿用原ID，不新增调用或资金：REQ-A/B为无仓库想法也可开始的需求→本人确认准确版本→工程方案闭环；CON-A/B为固定仓库＋选定本地文本／源码／未提交差异的纯评审，两变体都含无权威基准的有界子问；EXP-A/B为基于已确认既有需求、补充必要事实和实现假设研究的方案起草。各对目标、材料格式组合、规模和难度须独立制备并另审；澄清不得缩小共同目标刷比较，实质范围变化保原slot为partial／不可比，不换题。允许有充分依据的不同工程设计，不设唯一隐藏方案。

REQ同时保首次需求原稿、本人实际编辑（允许无改）及准确确认、首次方案原稿和最终双稿交付包。两份首稿均须过冻结关键项，人工改好不能清除raw失败。六final指六份完整交付包，full链包绑定需求／方案各版本hash及确认；有界ReportSnapshot只存refs和摘要，不内联两份64KiB正文。对照侧采用同样目标和计时，人工确认／改稿计入主动时间。

两个既有pilot槽固定承担4.5公开requirements_to_solution与5.4私源requirements_only最小真实工程验收；原调用/Case/费用/deadline不增，无新pilot自动补赠。先冻结目标/预期行为/许可并保原稿和实际费，工程实测不设对照效果通过门槛。效果试用/同条件纠错收益复测/正式六槽由人显式按需启动，不阻工程验收；比较时事前按原协议登记基线/关键项/计时，不追溯补造。仅需求/编辑不另获独立formal效果口径，正式三pair结论不外推真实团队。

## 限定校验

在仓库根目录运行已有 Python：

```text
.venv\Scripts\python.exe -B scripts\validate_project.py
```

默认成功只表示配置结构有效，并明确 `MATERIALS_NOT_VERIFIED`；它不打开或验证受限包。必须另行显式指定一对参数才能检查材料：

```text
.venv\Scripts\python.exe -B scripts\validate_project.py --review-material-root .tmp/predev-reopen-20261028/config-20261029/review-20261101/research-20261103/materials --review-material-index-sha256 <实际公开索引原字节SHA256>
```

占位值不能执行。本批材料仍 pending，显式校验应返回 `not_ready` 非零。每个角色仅映射上述固定文件名；独审报告固定为父目录 `materials-review.json`，必要复审为 `materials-rereview.json`，不能跟随索引任意路径。先检查未解析路径所有组件的链接／Windows reparse，再核解析范围；文件身份／一致性不确定即拒。角色包和报告均限1 MiB原字节再严格 JSON，拒重复键、非有限数和错类型，错误不输出题面、键值或异常原文。

`review_receipt`绑定独立原始报告的 thread/message/context/role 和准确三包字节，不接受 `reviewed=true` 自证；身份结构校验不证明审查真实性或语义正确。报告不能引用尚未形成的索引或协议 hash。

## 调用及资格证据

所有主子研究、规划、归并和讨论调用均进入同Case有界池；不得用角色／用途／Turn变化重置额度。四次document_compile统计全部物理尝试，含技术retry；首稿预留只保护尚未尝试文档的首次尝试，失败消耗不补满。程序选择用途，额外摘要／judge／修复继续为零。

分别审查本地完整公开格式计数、托管fit资格、实际usage/cache及费用。合法差异只记录；overflow／供应商协议异常撤资格，业务生成JSON错误不混同。缺usage或费用不明保留unknown和预留，停新外发；有限诊断不证明所有输入零溢出。真实资格与费用尚未执行验证。

## 正式结果口径

三对六次全部保留，包括未启动、partial、失败、取消、缺失及不可评分。三个 Agent 原始报告均须通过各自关键项才能通过原始产品质量门槛；人工修好不抹去原失败。最终六份人工稿共同质量通过、首次显示及主动时间完整且 Control 基线非零后，才描述三个配对的省时中位数；允许负值，没有20%硬门槛，不外推真实团队价值。

Control采用预注册的日常人工仓库阅读、普通AI和搜索，DR按需且已登记，所有新增费用计入总账。Agent侧不得外部AI代修或复制Control答案。披露许可 `disclosure_committed` 与实际显示／ACK分开；时点不明保留最早可能暴露时间及 `timing_uncertain`，不得重置计时或进入有效省时比较。详细流程见[核源与计时](REVIEW_WORKFLOW.md)。

## 历史与保护

`d4b906fb6a441c13583f052377283ec0c28bf5a2` 的原路径及原字节 hash解释 `discovery-m1-1` 和旧六题；`1ffade6de07ebe3d1e72afb4c44b8677466eca67` 的显式路径／hash／必要换行转换解释历史 `current-3`。不复制另一套现行材料，不删除真实来源、许可、费用、失败或授权。

旧 `evaluation.current`、pilot runner、budget、ledger及reconciliation不是新运行器，对新／坏／缺失协议在加载Settings、客户端、目录或写账前拒绝。历史检查须明确 commit/path/raw SHA；不能借历史读取扩账、arm资金或执行新任务。r12／P-02 No-Go保留；首业务、真实pilot、M1、Go和发布分别待授权与证据。

FOCUS-BASELINE-20261102／draft-m1-2由进入HEAD dc4498f36c0342eef5191f9f59feaf3b363169b6的准确path/raw hash及focus-20261102原最终索引解释，297 passed／1 skipped仅属其原文件检查，不替代本轮结果。

DRAFT-BASELINE-20261102／draft-m1-1按draft-20261102/snapshots/final-01/manifest.json及path/raw hash保留；REVIEW-BASELINE-20261101／review-m1-1原字节由既有`review-20261101/snapshots/final-02/manifest.json`及其path/raw hash定位；该未提交配置不是HEAD中的Git对象。旧final-delivery／失败／审查不覆写，新修订的实际检查与独审另追加。
