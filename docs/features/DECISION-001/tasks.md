# DECISION-001 纵向任务与验收状态

当前主线：PREP-BASELINE-v4.3 设计及限定16份文档同步已批准，2026-10-27 落地检查/独立审查见文末 DEC-PREP-BASELINE-20261026。业务实施未授权。下列2026-10-24切片状态按原证据保留：

历史状态（2026-10-24）：**现行规格／契约已同步；DEC-T01 完成其离线切片验收，DEC-T02–T05 的代码已提交但仍有验收缺口，DEC-T06 仅备好复核模板。P-02 真实研究与产品仍为 No-Go。** 阶段顺序以 [现行计划](../../../PLANS.md)为准；每个切片通常按 1–2 个兼职工作日计划，估计须含读码、测试、Review 和修复。以下是实现范围与验收依据；实际状态逐项列在下表。付费运行仍需单独授权。

| Task ID／依赖 | 独立结果与预计调用链 | 必须验证与完成证据 |
| --- | --- | --- |
| DEC-T01／P-02 失败分析 | 冻结 B01–B03 轨迹，分别验证页面事实提取、无进展和 Token 预检的可证伪修复假设；范围限 Planner、Context、Evaluator、调用预算相邻链路。 | 离线回归覆盖事实准入、来源错配、关键证据裁剪和预算不足；记录基线与改动后的相同口径结果，真实复测另获授权。对应 DEC-AC-02、06。 |
| DEC-T02／T01、目标契约同步 | 为既有提交 DTO 增加可选决策上下文并保持旧请求兼容；API → 持久任务 → Worker → Agent 状态传递。 | API／Schema、空值、非法候选、长度、幂等冲突与权限测试；检查输入和事件不泄露秘密。对应 DEC-AC-01。 |
| DEC-T03／T02 | 从已准入事实构建候选 × 条件矩阵，保留冲突、未知及每项 fact ID；优先复用事实和报告模型。 | 纯逻辑及集成测试覆盖错主体、缺片段、矛盾来源和无证据条件；恢复后引用稳定。对应 DEC-AC-02、03。 |
| DEC-T04／T03 | 报告器依据矩阵生成条件化建议、改变建议的条件与无法推荐原因；无新的独立 Agent 或数值打分服务。 | 用硬条件变化、偏好取舍、候选均不满足及提示注入样本做回归；每项建议可追至事实。对应 DEC-AC-04、05。 |
| DEC-T05／T04 | API／UI 展示目标、比较矩阵、未知项与机器／人工核源差别，保留取消和历史路径。 | 前端交互、API、SSE、权限及部分报告检查；记录可复查截图／输出与风险。对应 DEC-AC-03、06。 |
| DEC-T06／T05 | 对现有正式运行工件及冻结离线材料附加独立的决策质量复核，不修改正式协议。 | 逐条件记录人工判定、报告 SHA-256、fact ID、未知项、复核者与时间；额外真实运行另获授权。对应 DEC-AC-07。 |

## 实施与验收状态

`IMPLEMENTED` 表示代码已提交，不表示 AC 完成；`PARTIAL` 表示仅部分检查有证据。`DONE（离线）` 仅适用于明确限定为离线的切片。[离线实施记录](OFFLINE_IMPLEMENTATION_2026-10-23.md)保存既有命令与结果；本表不把其中的模拟结果提升为真实验收。

| Task／对应 AC | 实施／验收状态 | 已有证据 | 完成前仍需的证据 |
| --- | --- | --- | --- |
| DEC-T01／DEC-AC-02、06 | `IMPLEMENTED`／`DONE（离线切片）` | [单独验收](../../tasks/DEC_T01_ACCEPTANCE_2026-10-23.md)绑定 `ec4a1496` 的离线回归与限制。 | 真实取证、人工官方核源及费用另按 P-02／正式协议验证；本切片不解除 No-Go。 |
| DEC-T02／DEC-AC-01 | `IMPLEMENTED`／`PARTIAL` | `266a49cc` 包含可选输入、PostgreSQL 快照、Worker 传递及离线传输测试；[GitHub CI 的 PostgreSQL job](https://github.com/wdadassdasadasd/adaptive-browser-agent/actions/runs/39984876768)在 Linux 一次性库完成迁移和 4 项集成测试（整体工作流仍失败）。[DEC-T02-01](../../tasks/DEC_T02_01_ACCEPTANCE_2026-10-24.md)补 API／Schema、幂等及快照回归；本机一次性 PostgreSQL 测试 `4 passed`。 | Windows／WSL 冷启动、真实失租恢复与跨账户权限检查仍待证据。 |
| DEC-T03／DEC-AC-02、03 | `IMPLEMENTED`／`PARTIAL`（DEC-T03-01 离线切片 `DONE`） | `266a49cc` 包含矩阵构建与离线逻辑回归；[DEC-T03-01 记录](../../tasks/DEC_T03_01_ACCEPTANCE_2026-10-25.md)包含事实去重、时间及恢复对账定点验证、一次性 PostgreSQL 库集成 `4 passed`、只读独立 Review 与项目校验通过证据。 | 真实官方来源及冲突仍须人工逐条核查；Windows／WSL 实际进程崩溃恢复和正式门槛另行验证。 |
| DEC-T04／DEC-AC-04、05 | `IMPLEMENTED`／`PARTIAL` | `266a49cc` 包含条件化建议；[离线测试](../../../backend/tests/unit/test_decision.py)覆盖无证据、冲突与页面诱导文字不能新增硬条件。[DEC-T04-01](../../tasks/DEC_T04_01_ACCEPTANCE_2026-10-26.md)补固定事实的硬条件变化／全部不满足对照、报告引用及人工核实标识，聚焦测试 16 passed；fresh-context 独立审查 DONE、无 P0–P3 发现，审查者 pytest 未完成复跑的限制已保留。 | DEC-T04-01 用户亲验输出待完成；经授权真实研究后的推荐价值和事实支持仍待人工复核。 |
| DEC-T05／DEC-AC-03、06 | `IMPLEMENTED`／`PARTIAL` | `266a49cc` 包含前端表单、矩阵展示及前端测试；见[实施记录](OFFLINE_IMPLEMENTATION_2026-10-23.md)。 | Vue → API → 历史／SSE 的端到端交互、跨账户权限及部分报告检查。 |
| DEC-T06／DEC-AC-07 | `PENDING`／`PENDING` | [离线复核模板](OFFLINE_DECISION_REVIEW_TEMPLATE.md)已备。 | 在同一冻结报告快照上执行独立逐条件复核，记录报告哈希、fact ID、复核者和时间；正式分母保持不变。 |

后续任务开工前使用[单任务模板](../../engineering/TASK_TEMPLATE.md)记录具体文件、基线命令、估计与回滚；已提交的 T02–T05 以本表追踪剩余验收，不补写不存在的开工前证据。若 T01 无真实事实质量进展，后继切片不应被标为产品完成。Git Commit、Push、创建 PR 和合并各自授权；2026-10-24 用户另行授权核对本地与 GitHub、合并未合并分支并同步，不改变真实研究及正式放行的 No-Go。


## 现行 M1 后续任务（PREP-BASELINE-v4.3，全部待具体实施授权）

T01–T06 历史表及验收工件保留；本节替代2026-10-26早期语音专属的T07–T13目标表，Task ID 不变。新要求、旧新映射见[规格](spec.md)，模块职责/工时/本人参与见[计划](../../../PLANS.md)。PENDING 不是已开工或通过。

| Task ID/依赖 | 现行责任/非责任 | AC/验收与证据 | 实施/技术/业务 |
| --- | --- | --- | --- |
| DEC-T07/具体授权 | 兼容基础、统一上下文、终态与恢复；首个T07-01仅kind/旧Worker护栏 | 13–15；旧API/事件、NULL setting、池清理、隔离Pg混合队列与兼容回滚 | PENDING/PENDING/PENDING |
| DEC-T12/具体授权，与T07并行 | F1单资金权威、旧账/预留/grant/admission/撤销与恢复代次；不以客户端授权 | 13；资金/锁序/unknown/最新高水位、安全审查；未过禁止pilot | PENDING/PENDING/PENDING |
| P-03最小账户/T08前置 | 两真实成员/CLI与所有对象隔离；正式五账户/管理UI仍保留 | AC009/N08、15；认证、停用/注销、CSRF/SSE/ref/cancel | PENDING/PENDING/PENDING |
| DEC-T08/T07与账户 | 澄清/条件接受/revision/报告/取消的假供应商纵切 | 08/09/15；端到端、幂等先CAS、竞争无孤立记录 | PENDING/PENDING/PENDING |
| DEC-T09/T08，复用T01/T03 | 通用身份、引用/时效、C0/1/2、Gateway/审计A/Token影子 | 10/11/18；固定资料及授权早期pilot、反证和实际费用 | PENDING/PENDING/PENDING |
| DEC-T10/T07–09 | 解释/恢复、同会话与跨任务显式来源线索、历史 | 12/14/17；条件覆盖、7天/5条/撤销隔离/新核验 | PENDING/PENDING/PENDING |
| DEC-T11/T09/10 | 通用角色/组合/分批/完整交互、只读真实stdio MCP | 10/12、AC012；4或3×2/显示3，错误/断连/取消清理 | PENDING/PENDING/PENDING |
| DEC-T13/贯穿，最终依赖T07–12 | 早期真实失败诊断→亲改→回归→授权复测，最终独立补充评测/演示 | 16/19/20；全9E2E/8线索条件运行/12决策调用与核源；≥1真实目标症状纠正 | PENDING/PENDING/PENDING |

四周、每周15–20h目标与本人66–96h估算有差距，负责人决定保留目标、首周实际校准，预计超窗提交期限/投入取舍，不削核心闭环。原T02–06与P02–04缺口不自动通过。等待某模块亲验时只推进已授权且不依赖该结论的工作。

## DEC-DOC-SYNC-20261026：文档同步任务

### 需求、授权与边界

- 唯一任务记录复用本页；阶段为既有 G0–G7 中批准设计后的项目文档／契约同步，风险 R2（目标事务、状态和安全契约），不是业务实现。
- 用户需求已回复“认可”；架构最终批准原文：“批准方案 B 及上述默认上界，仅同步所列项目文档与契约”。方案为 ARCH-20261026-v3.1，默认上界见 ADR-0007。
- 基线 HEAD `e70b5f983532868b765e988f9162ddf989cf153d`，原工作区 10 modified＋3 untracked、暂存为空。AGENTS、本页、STRATEGY 与已有修改重叠，只增量保留；其余旧工作、SQLite／r12、browser-use 不变。
- 13 份范围：根 `AGENTS.md`、`SPEC.md`、`PLANS.md`；`docs/contracts/CURRENT_CONTRACTS.md`；本 feature 的 `spec.md`／`tasks.md`；新增 `docs/design/adr/0007-interactive-evidence-decision-sessions.md`；`docs/decisions/DECISION_LOG.md`；两份原研究文件 `AGENT_JOB_PRODUCT_FIT_2026-10-23.md`／`HIGH_STAR_AGENT_MECHANISMS_2026-10-22.md`；`docs/README.md`、`docs/architecture/README.md`、`docs/testing/STRATEGY.md`。
- 不改业务代码、依赖、数据库、冻结协议、历史评测／No-Go、共享规则／Skills／角色／模型／MCP／权限，不执行真实调用或 Git 写操作。旧 ADR5／6 不改，新 ADR7 追加并说明替代范围；旧 API、同任务引用和历史授权按日期保留。

### AC、验证与交付

| 文档同步 AC | 必须证据 | 当前状态 |
| --- | --- | --- |
| DOC-AC-01 | 相对进入本轮基线只修改上述 13 份 Markdown；完整 task diff 和新文件快照 | DONE（文档范围） |
| DOC-AC-02 | 需求／上界／B 方案及契约、模块／依赖／AC 一致；标目标未实现 | DONE（独立文档审查） |
| DOC-AC-03 | 冻结九题十五次、五账户／恢复／备份、原费用上界、No-Go 与旧任务状态不变 | DONE（原字节／正文核对） |
| DOC-AC-04 | 非范围基线哈希、原未跟踪内容、暂存区、HEAD 和 browser-use gitlink 均保持 | DONE（基线清单范围） |
| DOC-AC-05 | 项目校验、diff 空白检查、fresh-context 独立审查及必要修复复审 | DONE（文档技术验证） |

临时基线／完整 patch／哈希清单保存在忽略目录 `.tmp/decision-doc-sync-20261026/`，含 406 个原文件哈希、13 份范围的旧文件副本、原 staged／unstaged patch；临时证据不作为业务事实或另一个任务体系。后续在此补记实际命令与退出码。未运行全套业务／数据库／前端测试、迁移或付费评测；文档检查不证明新行为通过。

回滚只逆转本轮 task-owned 差异，三份重叠文件用进入本轮副本核对，不 git reset／clean／覆盖整个工作区。交付后由人阅读规格、契约和新 ADR；不把“文档完成”或已有设计批准提升为新业务实施授权。

### 实际结果（2026-10-26）

本任务完成的是 **13 份项目文档／契约同步与技术验证**；新 DEC-T07–T13 均 PENDING，真实研究／产品 No-Go、个人理解验收与正式放行未完成。供人复核的入口为根规格／计划、现行契约 V2 和 ADR-0007；没有业务运行结果可供验收。

| 实际命令／检查 | 结果与边界 |
| --- | --- |
| `.venv\Scripts\python.exe scripts\validate_project.py` | exit 0：offline validation passed；链接、结构、现有映射和历史冻结校验通过，不证明来源真实或产品效果。 |
| `git diff --check` | exit 0，无空白错误；仅 LF／CRLF 提示，未据此改写其他文件。 |
| `.venv\Scripts\python.exe .tmp\decision-doc-sync-20261026\verify.py` | exit 0：恰 13 个范围文件变化，406 个基线文件清单中的范围外内容无变化，无范围外新增；HEAD／空暂存／browser-use gitlink 不变；tasks／策略／log／契约／两研究旧字节前缀保留。 |
| fresh-context `decision_docs_review_final`（security_reviewer） | 完整 13 份当前正文、task-owned diff 与新 ADR 初审发现 1 项 P2：旧事件四名称缺 task_ 前缀。核对 events.py 与 App.vue 后仅修正文档，受影响复审 DONE，无未关闭 P0–P3。审查者独立做哈希及 diff 检查，未复跑 validator 或业务套件。 |

审查基线 HEAD／current commit 均为 e70b5f983532868b765e988f9162ddf989cf153d。初审 task patch SHA-256 `8f7cadf80a8f22a50470607f2ce7ef1ceb87fb07649f53485519c2ef108c152e`，修复复审 patch SHA-256 `d9cdbaa6c7e2519c2d8641fcfba29adc2d8e4a2cd813286dd7c9f765b1ef18a9`；contracts SHA-256 `6f81e3ebf77f8df5f21809b695b6fb8d6641ed3cc09862752ed803e493165625`。本段实际证据补记会改变本页及整体 patch 身份，最终内容清单／复核结果保留在临时目录，不把上述旧 patch 哈希冒充最终 bytes。

冻结协议 SHA-256 始终为 `1c18d53624c21b1e25f5cea5640b4c8b4a5e0cfc001f430c8d603a01d51a8507`。临时证据含 baseline.json、review1-task-owned.patch、review2/ 的完整 13 份复审快照／patch、checks.json／checks-final.json、最终 task-owned.patch／verification.json 与 review-final.txt。审查有效权限是共享 workspace-write，审查者本次仅执行只读操作，不宣称系统沙箱隔离。

未运行数据库迁移、全套后端／前端／浏览器故障测试或付费评测，也没有安装、Git stage／commit／push／PR 或外部写入；未来实现按具体任务授权后触发相应检查。当前文档交付不授权新实现，不将历史或未知项改写为通过。


## DEC-PREP-BASELINE-20261026：开发准备基线落地

### 原始要求、已决事项与授权

负责人要求面向开发者的有证据交互式技术决策助手，在M1包括记忆、上下文、真实评测/纠错优化、执行/费用/隔离、个人实践和交付完整闭环；语音只是任务，不可决定通用结构。按既有G0–G7/五文件任务记录研究、讨论、独立审查、明确确认后同步项目文件，业务实现另授权。

最新明确授权原文：“PLEASE IMPLEMENT THIS PLAN: # 已批准的 M1 开发准备基线落地计划”；其中“你已明确批准 PREP-BASELINE-v4.3 整体设计及以下16份文档同步范围”，并要求“同步上述文件…运行现有项目校验…固定完整task-owned内容及指纹，取得独立文件审查，核实发现、修复并复核”。这取代此前计划模式内不可写项目文件的执行限制；当前实际为Default模式。退出计划模式本身不构成业务授权。

| 已决事项 | 结论/状态 |
| --- | --- |
| 产品及任务边界 | 通用有限候选技术决策；语音实际需求，ORM/PDF公开需求衍生；价值未验证 |
| 核心方案 | ADR8/v4.3已批准：通用role、条件/报告不可变、显式7天/5条来源线索、C0/1/2、单决策物理请求、F1/admission/恢复高水位、审计A、tokenizer影子 |
| AC及任务 | DEC-AC17–20新增；全部M1核心不后移；T07+T12前置、T08假纵切、T09早pilot、T10/11完整、T13贯穿 |
| 本人参与/时间 | 工具失败重规划、反证保护、线索撤销、漏样本、真实故障最小修复；66–96h对四周60–80h有风险，首周校准 |
| 设计审查 | 讨论阶段独立技术/安全审查完成；不得代替实际16文件审查、实现审查或运行验收 |
| 本轮授权 | 仅下列16份文档、审计副本/增量/指纹、适用检查与独立文件审查修复；无业务/安装/真实调用/Git写 |
| 资金 | 2026-10-26 21:39:41北京时间官方GET只读余额CNY10.57，非grant；历史账/在途/批次覆盖未就绪硬阻塞真实pilot，不阻塞文档及另授权无模型工程 |

### 范围、基线与审计

HEAD `e70b5f983532868b765e988f9162ddf989cf153d`，暂存为空，进入本轮19 modified＋4 untracked。原字节/407个原文件指纹/旧working-tree diff、16份范围清单保存在 `.tmp/prep-baseline-20261026-141454149872/manifest.json` 与 `preimages/`。另有早期空目录 `.tmp/prep-baseline-20261026/`，保留不覆盖。审计工件不拥有业务事实或另立协作体系。

| 文件 | 原问题→批准落地/需求映射 | 历史/兼容/验证 |
| --- | --- | --- |
| SPEC.md | 语音及核心后移→通用用户问题、FR/NFR逐项、M1完整/正式分离 | 原AC/正式阈值；映射校验 |
| PLANS.md | 旧排期→职责/依赖/66–96h/停线/本人实践/提交包 | P阶段编号和门槛保留 |
| docs/contracts/CURRENT_CONTRACTS.md | V2任务特化/资金未决→通用role、真实owner、记忆/投影/admission/F1/审计A | 旧六路/六态/七事件、同task事实保持 |
| docs/features/DECISION-001/spec.md | 旧AC不足→修订08–16/新增17–20、例反例、旧新逐项/复用/补测/成本 | 01–07及历史验收绑定原版 |
| docs/features/DECISION-001/tasks.md | 旧任务→本连续主计划/批准/实际检查审查/下一任务 | 旧T01–06与DOC-SYNC原证据保留 |
| docs/design/adr/0008-m1-engineering-baseline.md | 新增候选比较、数据归属/锁序/安全/受影响替代 | ADR5/7原件不改 |
| docs/decisions/DECISION_LOG.md | 追加方案/批准/实际同步独立状态 | 历史决定不重写 |
| docs/research/AGENT_JOB_PRODUCT_FIT_2026-10-23.md | 官方实习/职责/加分/日期/能力证据与用户问题 | 旧校招/社招样本有范围，不伪造资格 |
| docs/research/HIGH_STAR_AGENT_MECHANISMS_2026-10-22.md | 固定版本OpenCode/DeepSeek、记忆/上下文、PR/Issue与迁移限制 | 未运行上游，旧研究保留日期 |
| docs/testing/STRATEGY.md | 对应风险/核源/独立审查/优化测试 | 不把本轮文档校验当业务测试 |
| docs/engineering/CONFIGURATION.md | 环境事实/缺口/tokenizer资格/启动恢复前置 | 不改全局规则、依赖或权限 |
| docs/evaluation/DECISION_M1_PROTOCOL.json | 新增补充协议、题面冻结前置/9+8+12/停止/证据 | 冻结正式协议哈希不变 |
| docs/evaluation/README.md | 补充/正式/历史导航及资金边界 | 不挪分母/历史结果 |
| docs/README.md | 当前基线与历史入口 | 导航非新权威 |
| docs/architecture/README.md | 已实现/批准目标/未验证分层 | 不宣称新设计已运行 |
| README.md | 产品/准备状态/M1与交付边界 | 原运行命令按V1范围保留 |

不改业务源码/测试、依赖/.env、AGENTS/共享规则/Skills/模型/MCP/权限、SQLite/r12/上游browser-use、冻结协议及历史工件。不执行Git add/commit/push/PR。回滚只恢复本轮task-owned增量，不能reset/clean或覆盖进入本轮重叠修改。

### 准备完成关口与未决事项

| 关口 | 必需证据 | 当前状态 |
| --- | --- | --- |
| PREP-AC01 | 恰16份批准文档实际写入；范围外原字节/HEAD/暂存/gitlink不变 | DONE：范围检查exit0，14原文件+2新增 |
| PREP-AC02 | FR/NFR/旧新/AC/Task/数字/链接/JSON一致、正式协议哈希不变 | DONE：项目/补充一致性校验exit0 |
| PREP-AC03 | 固定完整task内容/增量指纹，fresh-context独立文件审查及修复复核 | DONE：16文件独立正文审查无可确证P0–P3；最终补记核对见审计工件 |
| PREP-AC04 | 当前设计/授权/同步/实现/测试/本人验收/正式Go分开 | DONE（文档状态区分）；业务/个人/正式仍待各自证据 |
| PREP-AC05 | 第一项具体开工包明确、未来资金/环境/个人/验收风险可执行 | DONE（开工范围/前置已定义）；DEC-T07-01业务未授权 |

尚未解决的**实施期前置**：历史完整费用总账/在途与实际批次资金覆盖、逐次grant、tokenizer隔离安装资格、加密备份工具资格及真实源核查；首周时间校准。它们被明确记录为真实pilot/后续模块门槛，不虚构已经解决；本轮仅文档开发准备，不能解除No-Go。

### 第一项可单独授权实施包：DEC-T07-01

目标：operation_kind 与旧 Worker 防护。限定 PgTask/model、PgStore、additive migration、claim/写入边界及隔离PostgreSQL假任务测试；不得顺带实现会话、付费、真实模型/浏览器或新权限。开工读取原始store/model/迁移及Worker能力；核对具体文件后固定小范围。需要隔离库/环境满足，迁移执行范围另在该任务授权中明确。

通过条件：旧legacy六路/六态/七事件不变；旧claim/无setting/NULL不能认领或改写decision_turn；新事务SET LOCAL仅当事务有效且池不泄漏；不能通过改kind绕过；新旧混合队列容量/认领和终态一致；兼容回滚关闭新入口、保留新增数据、不回退到不识别kind二进制。交付迁移/测试实际命令、失败路径、完整diff/指纹、独立安全实现审查、运行步骤/预期及回滚，由本人聚焦CR/亲验后再另授权Git。**此包已具备范围定义，当前实施未获授权。**


### 实际同步、检查及独立审查结果（2026-10-27）

16份文档已实际写入，区别于此前“仅批准/未同步”。适用离线技术检查及fresh-context独立全文审查已完成；本轮没有新业务实现、业务验收、个人掌握或正式Go结论。以下结果补记会改变本页及整体patch；初审hash只绑定初审内容，最终字节/结果补记复核另存在审计目录，不用自引用hash冒充最终身份。

| 实际检查/审查 | 结果/边界 |
| --- | --- |
| `.venv\Scripts\python.exe -B scripts/validate_project.py --ledger data/evaluation/ledger-after-e4e3e822-f5f0-582d-9412-e7cb91daefe4.json` | exit0，现有链接/映射/归档/冻结和该声明ledger校验通过；不是全账户历史费用对齐或来源真实证明。 |
| `git diff --check` | exit0，仅换行转换提示，无空白错误；没有因此改写范围外文件。 |
| `.venv\Scripts\python.exe -B .tmp/prep-baseline-20261026-141454149872/verify.py` | 初次exit0：16范围、14原文件/2新文件、全部相对链接、FR001–015/NFR001–011旧新行、DEC-AC01–20、T07–13、JSON 9/8/12分母/69等价轮/22.08模型示例/299 ceiling；原407文件中的范围外字节、HEAD、空暂存、browser-use gitlink和正式冻结hash保持。最终同命令重验结果见verification.json。 |
| `m1_synced_file_review`（fresh-context security_reviewer） | DONE，独立读取全部16份257843 bytes、task-owned patch和HEAD全部任务路径差异及新增全文；起止hash均匹配。无可确证P0–P3；独立复跑validator/ledger、diff检查及只读链接/数字/原407文件/patch重建。未复核所有远端网页，不称源码运行或真实安全验证。 |

初审patch SHA256 `e48b6f7ea4d10b85a54d03bc7e075cbf383695b34fa733f54148697161ec00dd`，对应`review1/snapshot/`、`review1/verification.json`、`review1/report.md`；最终完整快照/增量与各文件hash见审计目录`review-snapshot/`、`task-owned.patch`、`head-task-paths.patch`、`verification.json`。结果补记增量的独立复核另记`review2-report.md`，本段不预填尚未返回的具体复核结论。根README/契约/ADR/协议及研究正文保持初审字节，不在审查时改动。

审查实际权限为共享workspace-write，本次仅只读，不宣称沙箱隔离。未运行全套后端/前端/数据库/浏览器/迁移/恢复/tokenizer或付费测试，未触发远端CI、安装、Git stage/commit/push/PR或发布。文档准备的完成与业务、真实运行/核源、本人CR/实践、正式Go分别记录；历史No-Go未解除。

### DEC-T07-01 开工文件与环境清单（只读定位结果）

当前路径定位：`backend/src/adaptive_research/infrastructure/pg_models.py`的PgTask；`backend/src/adaptive_research/infrastructure/pg_store.py`的create_task/claim_next及必要写入护栏；新additive迁移拟`backend/migrations/versions/20261027_08_operation_kind.py`，接现有`20261023_07`（实施前再确认head无并发变更）；`backend/tests/integration/test_pg_store.py`及必要的`test_pg_api_worker.py`隔离假任务检查。`backend/src/adaptive_research/worker/runner.py`只涉及认领能力参数边界时才改，禁止延伸到新session或真实执行。已有单元/接口兼容测试按受影响范围选择，具体小diff和审查内容绑定实际实施基线。

现有Pg集成测试要求P01_TEST_DATABASE_NAME或P01_TEST_DATABASE_URL指向与应用库不同的空一次性数据库，并拒绝非Alembic表/已应用迁移；测试会迁移并清理其创建表，不能连接原库。实施授权须覆盖该隔离库范围；本次只读核对源码，未启动WSL/创建库/执行迁移或测试。先核实数据库地址/身份/空库和后备原件保护，无法满足就保持该L3检查待执行。第一任务不依赖真实模型资金到账，但不能据此绕过隔离数据库或实施授权。依赖满足后具备具体开工条件；当前仍未获得业务实施授权。


## DEC-PREP-BASELINE-20261026 续记：2026-10-27 完整准备补齐

### 本轮授权、证据身份与完成口径

负责人明确授权原文为“PLEASE IMPLEMENT THIS PLAN: v4.3 开发准备补齐与首任务开工基线”。当前已退出计划模式；只批准六份现有准备文件及 `data/evaluation/decision-m1-1/` 的材料实际落地、适用检查和独立文件审查，不授权业务实施。原16文件同步/审查结论按原字节与范围保留；本节补齐新增准备标准，不把旧范围的 DONE 扩张成全部开发准备完成。

本轮基线 HEAD 为 `e70b5f983532868b765e988f9162ddf989cf153d`、暂存为空。进入副本、410个原文件指纹及完整旧工作树差异见 continuation manifest（本机历史证据：`.tmp/prep-baseline-20261026-141454149872/continuation-20261027T093049764107Z/manifest.json`）。原审计目录仅追加证据；不覆盖旧清单、快照、patch和审查报告。现有 SQLite/r12、browser-use、原暂存/未暂存/未跟踪工作均保留。

已确认：语音初始未知、经用户澄清接受；第3轮“全部本地处理、不上传音频”仅为评测演练；来源线索与上下文对照用 ORM/PDF；新增持久材料目录；历史供应商账单可取得程度未知。主材料入口为 [preparation.json](../../../data/evaluation/decision-m1-1/preparation.json)，与[补充协议](../../evaluation/DECISION_M1_PROTOCOL.json)配套，非业务runner、非运行授权。

**本节成品内容已编写，技术检查与实际内容独立审查由本轮最终结果补记给出；此处不预填通过。** 六个业务包均为 `PENDING / PENDING / PENDING`（实施/技术/本人业务），新文件及函数名均为受限拟定范围，当前没有相应实现可供亲验。

### 17项完成标准逐项审计与证据索引

分类：①已完成且证据充分；②已批准尚未落实；③已落实但验证/审查不足；④仍需本人决定；⑤实施期或真实运行前置；⑥历史/已替代。阻塞层分别记准备、首无模型任务、pilot、M1、正式Go/发布；同一行允许不同事实分别分类。

| #/完成标准 | 事实与证据 → 判断/分类 | 缺口 → 阻塞 → 下一步/负责人 |
| --- | --- | --- |
| 1 产品/任务边界 | [SPEC](../../../SPEC.md)、[ADR8](../../design/adr/0008-m1-engineering-baseline.md)把有限技术决策与语音/ORM/PDF任务输入分开 → ① | 无新增产品决定；AI维持通用role/身份，不把评测角色写成产品枚举。 |
| 2 岗位能力与M1证据 | [岗位研究](../../research/AGENT_JOB_PRODUCT_FIT_2026-10-23.md)官方样本、日期局限、职责/必需/加分、能力→行为→AC→缺口 → ① | 真正能力证明属⑤，阻塞M1个人证据而非准备；AI提供轨迹和代码，本人解释/实践，不推定资格或录用。 |
| 3 用户问题/替代/价值 | SPEC及岗位研究记录本人/同学问题、人工文档/通用LLM/研究报告替代和待验证收益 → ① | 真人使用正负反馈属⑤M1；本人评价候选排除、可信度及下一步行动，不能现在代填价值成立。 |
| 4 旧需求/设计/任务/历史 | [feature spec](spec.md)旧新映射及本页T01–06状态逐项保留；ADR5/7历史适用范围清楚 → ①⑥ | ③T02–05仍有端到端/隔离/恢复或本人亲验缺口，T06待独立复核；按原任务继续，阻塞相应M1/正式验收，不反推旧切片全通过。 |
| 5 新需求/AC本人确认 | v4.3整体批准原文及本次具体题面/材料范围回答均已记录 → ① | 本轮将回答落到材料；发生题面/核心范围/费用变化再由本人决定，不重索相同批准。 |
| 6 全M1核心可观察验收 | feature DEC-AC08–20、[测试策略](../../testing/STRATEGY.md)、9/8/12及真实纠错链 → ① | 实际实现/核源/个人证据为⑤M1；不以Mock或M2承诺替代。 |
| 7 记忆/上下文/评测/优化进调用链 | [契约V2](../../contracts/CURRENT_CONTRACTS.md)和PLANS规定Loop→证据→投影→admission→单次决策→持久报告 → ①设计、②业务待实施 | ⑤T09/10/12/13逐包实施和真实验证，阻塞pilot/M1；现在只固定准备输入与验收。 |
| 8 核心比较/审查/批准 | ADR8保留候选和改变决定证据；旧16文件审查有效；本次候选技术复核关闭逐轮评分、种子配对和T12依赖问题 → ① | 本次实际文件审查仍待最终证据，阻塞准备；AI固定完整内容并委派独立技术/安全审查。 |
| 9 模块/接口/状态/归属 | 契约拥有Session/InputRevision/Turn/ReportSnapshot/SessionEvidenceRef及资金/事实/检查点职责 → ① | 本节六包把②近期文件、接口与异常边界具体化；本轮检查/独立审查前阻塞准备。 |
| 10 依赖/优先级/里程碑 | [PLANS](../../../PLANS.md)主线、首窗口六包和T12对象依赖已确认 → ①目标、②本轮成品待验证 | AI核对每包依赖与AC，业务实施授权另由本人给出；不把纯逻辑可先行当对象集成已验收。 |
| 11 本人CR/调试/亲改 | PLANS区分重点CR/聚焦CR/结果验收、五类实践；本节给近期源码入口、命令及预期 → ①安排 | 实际读码/预测/解释/亲改记录属⑤M1；代码尚不存在时不造“已掌握”，AI在对应包实施后提供可运行材料。 |
| 12 测试/核源/benchmark/优化 | 原协议有分母与原则；本轮preparation固定逐轮题面、候选/资料、金标隔离、评分/slots/核源模板 → ②成品待检查 | 阻塞准备：实际材料完整性及独立文件审查；运行绑定与真人核源为⑤pilot/M1。AI补齐后闭环，不把全部冻结推第4周。 |
| 13 环境/依赖/资金/权限 | [CONFIGURATION](../../engineering/CONFIGURATION.md)及本轮只读调查区分版本元数据/可导入/可运行；余额和账覆盖诚实分开 → ① | ⑤专用空库和权限核实阻塞首无模型运行；F1/账/在途/资金覆盖阻塞pilot；本人账单范围事实未知，AI准备字段而不再次查余额。 |
| 14 Git/交付/备份/恢复/发布 | 契约、CONFIGURATION及[交付清单](../../audits/PREDEV_DELIVERY_CHECKLIST_2026-10-20.md)规定范围/原件/回滚/单独授权 → ① | ④⑤高水位位置/保管人、介质、密钥恢复人、工具安装及实际恢复归相应前置；阻塞恢复提升/正式Go，非T07开工。 |
| 15 获批文件落地/检查/审查 | 旧16文件及指纹/审查为①；本轮六份补充和新材料是②，不能复用旧审查覆盖新增内容 | 阻塞准备：AI固定最终diff/新文件hash、检查、独立审查和修复复核；结果另补记。 |
| 16 时间/未知/取舍 | 四周15–20h、本人66–96h，范围含读码/本人修改/测试/审查修复/运行/核源，首周校准已批准 → ① | ⑤首周实际投入和剩余预测；超窗由本人选择延长期限或增加投入，不自动删核心，阻塞超窗后的里程碑承诺。 |
| 17 第一最小业务包 | 原T07-01范围已有；本节补父/附属护栏、11入口、检查/本人验收/精确授权包 → ②成品待验证 | 本轮实际检查/审查阻塞准备；准确DB运行范围及实施授权阻塞首任务。仅完成准备后停在授权之前。 |

### 首窗口共用执行与验收规则（业务均未授权）

以下卡片承接[任务模板](../../engineering/TASK_TEMPLATE.md)，而不是新协作系统。每包获具体实施授权后先固定实际HEAD、旧工作树/新文件与scope指纹、相关失败和隔离环境，再实施。默认业务、真实运行、安装、外部写入、Git写操作均未授权；拟定路径变更只允许必要的小范围调整并记录理由，重要行为/权限/费用变化须重新审查并由本人决定。

每包交付原始Requirement/AC、可运行入口、完整task-owned diff（含已提交/暂存/未暂存/新文件）、命令/退出码、失败与跳过项、内容指纹、独立审查及复审、本人参与原文、限制和回滚；本人验收与技术检查分列。独立审查保持内容稳定，R2采用安全及正确性视角。未发现问题、离线测试或假供应商输出不能证明真实质量、个人理解、资金覆盖或正式Go。

下面命令是**未来验收入口，当前未在本轮执行**。新增测试文件是拟实施范围，创建并收集到这些测试后方可执行；测试选择为0、skipped、超时或无结果均不能记通过。所有命令从仓库根目录运行，不安装依赖，不读出秘密。

### DEC-T07-01：operation_kind与旧Worker兼容护栏

| 字段 | 可执行准备定义 |
| --- | --- |
| Requirement/AC/状态 | FR-001/005/006，NFR-006/007，DEC-AC-15及13/14兼容子集；`PENDING/PENDING/PENDING`。不宣称完成统一context、资金或新session。 |
| 输入→输出/用户可见价值 | 输入为现有PgTask/store、迁移head20261023_07、legacy六路/六态/七事件及冻结旧执行器；输出为兼容kind/能力边界、additive迁移、隔离Pg混合队列/旧写拒绝证据和兼容回滚包。可见结果为旧假任务照常、错误旧路径对decision假任务原子拒绝。 |
| 依赖/范围/复用 | 只复用现有PgStore租约/fencing/事件/容量和Worker轮询；限定 `backend/src/adaptive_research/infrastructure/pg_models.py`、`pg_store.py`、必要的 `worker/runner.py`、`backend/migrations/versions/20261027_08_operation_kind.py`、`backend/tests/integration/test_pg_store.py`、必要的 `test_pg_api_worker.py` 及最小旧代码测试夹具。迁移文件名/父head在开工重核。 |
| 职责/非职责 | 创建后kind不可转换，默认legacy；新版Store显式能力才可写decision，不能所有legacy方法自动SET LOCAL。父任务和app_event/app_fact/app_call_attempt/app_cost/app_report写入校验关联task及旧新task_id；兼容SQL使用常规迁移权限、无新角色/RLS/扩权。全局budget通过同事务call/cost拒绝回滚，不新增kind。禁止产品会话、真实模型/浏览器、F1、上线或绕过隔离库。 |
| 接口/状态/锁 | 旧DTO不暴露新kind，旧列表/详情不泄露decision；能力参数同时约束claim与先于claim的reconcile。decision写事务校验 `current_setting('app.execution_protocol',true) IS DISTINCT FROM 'decision-v2'`，missing/NULL/错值拒绝；仅事务内SET LOCAL，不设池/role/database默认。父/附属guard复用scheduler→task→附属顺序，不新增反向锁；此协议不是持凭据恶意进程认证。 |
| 正常/边界/失败 | legacy旧请求/假任务不变；正确新事务可建/写decision假任务，未知kind、kind降级/换task_id、无能力与无setting/NULL拒绝。触发器/SQL失败无孤立事件/fact/call/cost/report，不因数据排版完整算完成。 |
| 并发/取消/恢复 | 混合队列共同两运行八排队，第11个429不落库；启用decision入口前兼容Worker支持全部已启用kind，验证共同FIFO、唯一认领/终态。排队/运行取消、续租、失租一次重认领/二次终结均守guard；旧扫描失败关闭不得误改decision。池复用/回滚/异常后setting均清除。 |
| 最小实施/实际证据 | 先锁旧Store/model/DTO和最小依赖完整内容/hash，兼容夹具直接执行真实旧方法（不发送模型）；再迁移/模型、Store/Worker能力、父及附属guard、下表测试。实际SQL/锁方案实施前固定并独立核对。交付每入口前后表快照、token/事件线、命令/退出码/hash；不得用新版替身声称旧二进制测试。 |
| 检查/预期 | T07-C01 heads唯一；C02无DB旧传输及metadata基线；C03受影响Ruff；C04精确隔离Pg两文件，新增下表用例全部实际运行且通过，无DB项被skip。六路/六态/七事件闭集合保持。 |
| 风险/停线/回滚 | 库身份/空库/原件保护不符、常规权限不能建guard、迁移head漂移、锁序冲突、旧路径旁路、Pg测试未执行即停该验收。先停不兼容API/Worker再迁移；业务回滚关闭新入口、保留新增数据，仅退到懂kind/guard的兼容基础版；绝不以downgrade base或删除原库回滚。 |
| 独立审查/本人参与 | R2独立安全实现审查覆盖完整diff/旧夹具/迁移/并发与实际结果。本人聚焦CR：读PgTask→create/claim→_live→附属guard及runner.tick；先预测旧append_event是否可写，再运行C04目标用例看拒绝且全表无副作用，解释SET LOCAL和测试清理/业务回滚差别。记录本人解释/命令/结果，不代填通过。 |
| 估时/开工/授权 | 估算AI工作1–2个兼职工作日；本人聚焦CR/运行验收约2–3h，计入首周16–22h而非另加；未知为旧夹具依赖和DB锁/权限。须另获代码范围和准确host/port/database/role、WSL保活、建库/迁移/测试清理授权；历史127.0.0.1:5433不是本轮就绪事实。资金到账非此包前置，Git/安装/付费均不含。 |

| 写入口（pg_store.py） | 必须观察的正常及拒绝结果 |
| --- | --- |
| create_task | legacy默认/显式成功；decision仅正确能力事务成功；unknown/missing/NULL/错setting与kind转换拒绝，创建原子。 |
| claim_next | 旧真实方法不能认领decision；新版显式能力认领支持kind；容量共算、FIFO、双认领竞争无重复。 |
| renew_lease | 正确token/owner/协议续租；错协议/过期/迟到token拒绝或按原返回值失败，租约不变。 |
| request_cancel | queued/running/terminal与重复取消、取消竞争；拒绝事务不能遗留cancel事件或状态。 |
| append_event | 旧方法即使有有效running/token/lease也不能新增decision event/fact；同事务facts与event一同回滚。 |
| finish_task | report/event/cost/终态原子；错协议及迟到结果不能写任何附属表；唯一终态。 |
| reconcile_expired | 在claim之前扫描混合running集；一次恢复/二次终结/取消竞争合规，旧扫描不能改变decision及其账。 |
| mark_unknown_calls | 旧方法不能改decision call/cost/budget；错误协议全事务回滚，合法unknown保持费用未知。 |
| start_call | 正确新假调用可记started；旧方法有合法token也拒绝，调用不得实际发送。 |
| _end_call/complete/fail | completed/failed/unknown费用写入同guard；错误协议call/cost/budget均不改，UPDATE不能迁移到别的task。 |
| store_fact | 仅锁父task不算通过；旧真实方法向decision附属表INSERT须被DBguard阻断，合法新写保持事实/事件规则。 |

```powershell
# T07-C01：只读迁移图；预期唯一20261023_07（实施后为新唯一head）。
.\.venv\Scripts\python.exe -B -m alembic -c backend/migrations/alembic.ini heads
# T07-C02：无数据库基线；上轮4项曾无返回中断，必须实际重核，不能复用为通过。
.\.venv\Scripts\python.exe -B -m pytest -c backend/pyproject.toml -p no:cacheprovider -q backend/tests/unit/test_pg_transport.py backend/tests/integration/test_pg_store.py::test_postgres_metadata_is_separate_from_v1_sqlite
# T07-C03：预期exit0；只检查，不自动格式化。
.\.venv\Scripts\python.exe -B -m ruff check --config backend/pyproject.toml backend/src/adaptive_research/infrastructure/pg_models.py backend/src/adaptive_research/infrastructure/pg_store.py backend/src/adaptive_research/worker/runner.py backend/migrations backend/tests/integration/test_pg_store.py backend/tests/integration/test_pg_api_worker.py
# T07-C04：先另授权并核实准确隔离空库；预期全部适用Pg用例实际通过。
.\.venv\Scripts\python.exe -B -m pytest -c backend/pyproject.toml -p no:cacheprovider -q -rs backend/tests/integration/test_pg_store.py backend/tests/integration/test_pg_api_worker.py
```

隔离测试的 `P01_TEST_DATABASE_NAME/URL` 必须指向不同于应用库的独占空一次性库；核对实际host/port/database/role、无原业务表/无已应用迁移、原库/原件hash。当前测试结尾会 `downgrade base` 清理测试所建表，故运行授权必须明确覆盖该库迁移及清理；结束核对剩余表和精确库身份，删除数据库若需要也须具体授权。不得把“应用库同名比较通过”当全部身份保护，也不得把测试清理混作兼容回滚。

### DEC-T07-02：假执行上下文与phase边界

| 字段 | 可执行准备定义 |
| --- | --- |
| Requirement/AC/状态 | FR-002/006/007，NFR-001/010，DEC-AC-13/14执行子集；`PENDING/PENDING/PENDING`，不单独完成AC14会话终态。 |
| 输入→输出 | 输入T07-01兼容任务、原queued/截止、阶段/调用覆盖和假provider；输出可注入的TurnExecutionContext、phase结构输出/coverage、外层终结接口与资源关闭证据。假任务可观察累计而不重置、内层phase完成不发task_finished。 |
| 范围/复用/非职责 | 拟增 `backend/src/adaptive_research/agent/runtime/turn_execution.py`、`backend/tests/unit/test_turn_execution.py`，限改 `agent/agent_loop.py`、`agent/llm/base.py`、`agent/call_observer.py`、`worker/runner.py` 及必要Pg阶段持久接口/迁移/集成测试。复用现有meter/recorder/provider契约、Loop工具清理和fencing；不重新造第二账本，不实现session/API/UI、实际provider发送或F1。 |
| 接口/状态/依赖 | 依赖T07-01。context唯一拥有provider/recorder/meter、原queued/截止、阶段输出、call IDs和usage覆盖；Loop仅研究phase，返回确定性事实/阶段结果，不重置或关闭共享provider；外层关闭一次。应用阶段状态是恢复依据，临时投影不是权威。session active/revision/report/event/task原子发布由T08拥有。 |
| 正常/边界/失败/并发 | 假澄清/规划/评估/决策共享≤900秒/40000Token/4096预留及1024/2048/4096输出；缺usage/unknown停新增。两个阶段串行/重复completion去重；取消/超时/异常均清理Loop资源、外层provider恰一次，不能产生重复call或终态。 |
| 恢复 | 完整阶段输出+coverage可至多一次按原截止/累计用量恢复；started无结果unknown停线；completed丢阶段输出保known费用并以phase_output_not_committed终结，不重发、不改unknown。故障注入覆盖调用前/返回后/阶段提交前后，迟到fencing拒绝。 |
| 基线/检查/预期 | 先固定现有Loop/provider/worker调用链。未来 `.venv\Scripts\python.exe -B -m pytest -c backend/pyproject.toml -p no:cacheprovider -q backend/tests/unit/test_turn_execution.py backend/tests/unit/test_loop_usage.py backend/tests/unit/test_call_observer.py backend/tests/unit/test_deepseek.py`；新增阶段落库用例并入T07-C04。预期call数精确、资源close=1、恢复不重置/重发；Ruff检查所有受影响源码/测试。 |
| 可见验收/风险/回滚 | 提供假执行时间线、阶段输出/coverage/hash及错误样本。context重复计费/内层终态污染/资源归属或恢复缺coverage即停线；回滚停decision执行、保旧legacy与新工件，仅退兼容基础版，不删除已提交账/阶段。 |
| 独立审查/本人 | R2独立正确性/恢复审查，付费/秘密边界受影响时安全覆盖。本人聚焦CR：读context→Loop phase→外层close，预测cancel与completed丢输出结果，运行上述用例并解释为何不能重调。保留本人原文，不填掌握。 |
| 估时/前置/授权 | AI约1–2个兼职工作日，本人约1.5–2.5h计入首周；未知为Loop资源所有权改动面。准确源码/测试/迁移范围另授权，Pg运行另核隔离库；无真实请求/安装/Git授权。 |

### P03-MIN-01：两真实成员与本地账户操作

| 字段 | 可执行准备定义 |
| --- | --- |
| Requirement/AC/状态 | FR-009，NFR-008，AC-009/N08，DEC-AC-15；`PENDING/PENDING/PENDING`，正式五账户/完整管理员界面不取消。 |
| 输入→输出 | 输入既有Pg owner基础和已批准认证/对象契约；输出两实际成员、可调用的认证依赖、登录/注销/me及本地CLI开通/停用/重置。本人能以两个账户验证同一研究对象只归其owner。 |
| 范围/复用/非职责 | 拟增 `backend/src/adaptive_research/application/auth.py`、`api/auth.py`、`api/schemas/auth.py`、`scripts/manage_accounts.py`、`backend/tests/unit/test_auth.py`、`backend/tests/integration/test_pg_auth.py`；限改pg_models/store、版本化additive迁移、api/pg_main.py及pg_research.py身份依赖。现有仅合成owner边界和Pg事务可复用，不能声称已有完整认证系统。无自助注册/完整管理UI/LAN发布/管理员默认内容读取。 |
| 接口/状态/依赖 | T07-01兼容基础和准确空测试库；依现行契约POST login/logout、GET me，服务端随机会话只存hash、密码自适应哈希、Cookie HttpOnly/适合SameSite/过期、注销停用重置撤销会话、登录限速、写请求CSRF。owner来自认证而非DTO；逐对象授权先于SSE/cursor读。算法/参数在该包具体实现设计冻结并安全审查；若需新依赖或改变既有行为另获批准，不凭已安装库自动采用。 |
| 正常/边界/失败/并发 | 两成员登录、会话到期、错误凭据/未知账户不泄露额外信息；他人/不存在对象同不可见结果；Host精确loopback、Origin/JSON/CSRF缺失null跨站拒绝。双登录/注销-读/SSE/停用-cancel竞争均重检授权，无凭据进prompt/log/event。CLI从隐藏输入取得密码，不放命令行。 |
| 取消/恢复 | 账户停用/注销撤销现有会话，不能用旧cookie继续读/取消；已提交任务诚实按其取消/终态规则处理，不伪造自动成功。恢复代次使旧会话失效接口供T12/T08整体验证；新会话和旧数据不跨owner。 |
| 基线/检查/预期 | 先列现有六路用LOCAL_OWNER_ID的位置；未来 `.venv\Scripts\python.exe -B -m pytest -c backend/pyproject.toml -p no:cacheprovider -q -rs backend/tests/unit/test_auth.py backend/tests/integration/test_pg_auth.py backend/tests/unit/test_pg_transport.py`，准确隔离库授权后覆盖A/B列表/详情/traces/SSE/cancel和CLI。预期跨owner泄露为0、撤销立即拒绝后续授权；受影响Ruff与T07-C04兼容检查通过。 |
| 验收/风险/回滚 | 提供两账户实际API请求/拒绝及退出会话步骤；不能用合成owner充数。密码/会话/CSRF泄露、身份绕过或旧接口兼容破坏即停线。回滚关闭受影响新入口，保账户/审计/owner数据，不把已有真owner任务交回合成身份开放读取。 |
| 独立审查/本人 | R2安全独立审查覆盖认证/会话/CSRF/owner链及完整检查。本人聚焦CR：读auth依赖→pg路由owner→SSE前授权；用A创建、B访问/取消应拒绝，再注销A旧cookie应拒绝，解释管理员为何不默认读内容。 |
| 估时/前置/授权 | AI约1–2个兼职工作日，本人约2–3h计首周；未知为尚无真auth及具体安全参数资格。任务代码/隔离库另授权；实际成员标识及创建/重置操作在授权包列明，不要求本轮提供秘密；安装/外部/Git另批。 |

### DEC-T12-01：只读历史账覆盖与核对包

| 字段 | 可执行准备定义 |
| --- | --- |
| Requirement/AC/状态 | NFR-002/006，FR-007，AC-N02，DEC-AC-13资金准备子集；`PENDING/PENDING/PENDING`。 |
| 输入→输出 | 输入声明ledger、r11/r12原始工件、可取得的Pg/旧库只读记录、本人可提供账单范围；输出账户/时段/模型覆盖表、稳定run/task/physical call映射、重复/冲突、known/unknown/in-flight、证据hash及导入契约。未知账单不造总额或grant。 |
| 范围/复用/非职责 | 拟增 `backend/src/adaptive_research/evaluation/ledger_inventory.py`、`backend/tests/unit/test_ledger_inventory.py`；必要复用 `evaluation/project_ledger.py`、`pilot_cost_reconciliation.py` 纯校验，输出到新授权审计子目录。旧SQLite/r12/ledger全只读，不导入旧UI、不改旧费用，不执行供应商查询/余额/充值或创建grant。 |
| 接口/状态/依赖 | 可与T07读码并行；清单每项含provider/account安全标识、时段、代码/模型、用途分配、数据库/run/call ID、来源hash、状态、去重键/冲突映射、费用精度及覆盖缺口。历史4次声明0.16536812元仅其范围，0.12舍入核对不等于逐调用发票；空SQLite不能恢复全账。无稳定身份/证据不猜合并。 |
| 正常/边界/失败/并发 | 同一调用跨工件只计一次，身份相同内容不同拒绝合并；已知零/unknown/null分开，缺价表/费用/账单保留原因。只读扫描期间文件漂移以起止hash识别，不能混版本；中断保部分结果及未覆盖时段，不将其提升完整账。 |
| 取消/恢复 | 中断不改原件，重新盘点按hash/稳定ID比对而非从0重算覆盖历史；恢复副本不能作为第二资金权威，记录备份截止及后备份差额/在途，独立最新高水位来源待本人事实。 |
| 检查/预期 | 未来 `.venv\Scripts\python.exe -B -m pytest -c backend/pyproject.toml -p no:cacheprovider -q backend/tests/unit/test_ledger_inventory.py backend/tests/unit/test_project_ledger.py backend/tests/unit/test_pilot_cost_reconciliation.py`；预期重复/冲突/缺失/舍入/未知/文件漂移/中断均有明确结果，原件hash前后相等。拟工具默认只读/dry inventory，必须先显示拟读文件/时段而不输出秘密。 |
| 验收/风险/停线/回滚 | 可见产物为完整覆盖矩阵及不能核对项；任一未解释费用/在途冲突硬阻塞pilot，不能用准备完成解除。盘点错误只弃用本轮派生工件并保原件/旧工件，不覆写历史；不把删除报告当修复账。 |
| 独立审查/本人 | 独立安全/账正确性审查验证去重身份、覆盖分母和未知。本人聚焦CR：读清单输入→去重/冲突→结果；核对一笔重复、一笔unknown和舍入，说明为何余额/299上限不是grant。本人补账户/时段/仓库外调用/账单可取得程度，不提供凭据进记录。 |
| 估时/前置/授权 | AI约0.5–1个兼职工作日，本人约1–2h计首周；未知主要为供应商历史证据取得程度。准确只读数据源/新输出及代码另授权；访问供应商账单若需要另授权，不能重复已用完余额GET。 |

### DEC-T08-01：API与假Worker会话纵切

| 字段 | 可执行准备定义 |
| --- | --- |
| Requirement/AC/状态 | FR-001/005/013/014，DEC-AC-08/09/14/15会话子集；`PENDING/PENDING/PENDING`。本切片是API→假Worker，不等于Vue完整E2E或真实研究。 |
| 输入→输出 | 输入T07兼容context、真账户、契约V2会话/条件/轮次；输出草稿→提议接受→提交有限turn→持久SSE/不可变报告→取消/历史的可运行API请求包。无需资金到账，但paid保持关闭。 |
| 范围/复用/非职责 | 拟增 `backend/src/adaptive_research/application/decision_sessions.py`、`api/decision_sessions.py`、`api/schemas/decision_sessions.py`、`backend/tests/integration/test_pg_decision_sessions.py`；限改pg_models/store、additive迁移、pg_main和worker受限分发。复用PgTask/事件/SSE/事实矩阵、真实auth及T07context，不复制旧fact归属规则。无真实provider/候选专属枚举/完整Vue或MCP；Vue路径 `frontend/src/App.vue`、`api.ts` 的后继T08切片仍保留L4/本人交互验收。 |
| 接口/状态/依赖 | 依赖T07-01/02和P03-MIN-01。Session owner/version/active，InputRevision不可变，Turn绑定有限task，ReportSnapshot不可变，SessionEvidenceRef单独归属；新session命名空间与旧六路闭集分离。幂等先于CAS；同键同规范化body返回原turn，不同body409；新键才核版本与revision。同session一个未终结轮次。 |
| 正常/边界/失败/并发 | 草稿不调模型；只有用户接受/编辑条件进入revision，页面或模型提议不自动生效，允许unknown。双提交/429/409/存储失败无孤立revision/turn/task；锁scheduler→session→task→附属，同轮输出/事件/version/active原子提交。owner/Host/Origin/JSON/SSE/cursor逐对象先授权。 |
| 取消/恢复/资源 | running时改条件先取消等终态再提交；queued取消立即释放槽，运行返回持久取消中。正常、失败、超时、排队截止、取消、失租、二次故障全部唯一终态并释放active。T08拥有task/report/event/session版本原子发布；T07phase结束不能提前终结。旧报告不覆盖；恢复核hash/fencing/coverage，unknown与completed丢输出按契约诚实结束。 |
| 基线/检查/预期 | 未来 `.venv\Scripts\python.exe -B -m pytest -c backend/pyproject.toml -p no:cacheprovider -q -rs backend/tests/integration/test_pg_decision_sessions.py backend/tests/integration/test_pg_auth.py backend/tests/integration/test_pg_api_worker.py backend/tests/unit/test_pg_transport.py`；预期真Pg幂等/CAS/双提交/满额/全终态/对象链均实际通过，旧接口兼容；Ruff覆盖新增/调整文件。请求演示使用测试客户端按真实路由/假Worker运行，输出期望session/turn/revision/report/event ID，无模型调用。 |
| 验收/风险/回滚 | 交付精确API请求、A/B账户授权步骤、正常及cancel/409/429/数据库失联结果/工件。孤立记录、active残留、同键误判、跨owner读取或新事件污染旧闭集即停线。回滚关新路由/分发、保应用新表和历史；不downgrade删除，不恢复旧二进制读取decision。 |
| 独立审查/本人 | R2独立事务/恢复与安全审查。本人结果验收（CAS/原子终态聚焦CR）：按请求包创建/接受/研究，重发同键应同ID，改body409，运行取消后active清空，B读/取消A应拒绝；说明该API切片尚未证明Vue或真实建议。 |
| 估时/前置/授权 | AI约1–2个兼职工作日，本人约2–3h计首周；未知为旧事件/phase与新终态适配。代码、假Worker、精确隔离库/迁移及账户操作另授权，paid关闭；不含UI后继、真实运行或Git。 |

### DEC-T12-02：假供应商F1与admission基础

| 字段 | 可执行准备定义 |
| --- | --- |
| Requirement/AC/状态 | NFR-002/006，DEC-AC-13/14/17资金/准入子集；`PENDING/PENDING/PENDING`，不把假测试记为资金已到账/真实保护通过。 |
| 输入→输出 | 输入T12-01覆盖/冲突、真实owner/session/turn/revision和准确代次接口、授权/计价资料形状；输出单一活动Pg资金权威、逐调用预留/结算、单次精确admission、恢复paid_disabled和对账包。假provider发送计数可与账本逐一对应。 |
| 范围/复用/非职责 | 拟增 `backend/src/adaptive_research/infrastructure/funding.py`、`backend/tests/unit/test_funding.py`、`backend/tests/integration/test_pg_funding.py`，限改pg_models/store、必要additive迁移和唯一付费Gateway/observer边界。复用现有Decimal/pricebook/physical call账和事务；旧PgBudget需按F1受控接续，旧SQLite及恢复副本不成为第二权威。无自动生成授权/充值/真实模型/旧账重写/高水位同备份自证。 |
| 依赖/接口/状态 | 纯资金算法可在T12-01后离线先行；**对象绑定及恢复集成验收必须依赖T07-01、P03-MIN-01、T08-01的真实owner/session/turn/revision schema**，占位ID不可记通过。grant录入绑定人的授权原文引用、代码/模型/阶段用途/任务轮次尝试/金额/价格/owner/generation；admission绑定精确请求/版本/引用hash，一次不可转用。hint真实生命周期/撤销竞争整合依T10，不能在本包代记AC17全完成。 |
| 正常/边界/异常/并发 | 单资金权威/项目控制→scheduler→session→task→grant→按ID排序hint及附属；缺项跳过不反向锁。并发预留不能超可用额；已知零/unknown保留，未知call占用预留并停止新增。admission必须提交后才发送；commit结果不明不发送，物理结果不明不重发；同admission换body/重复send/跨owner/旧generation均拒绝，确定性DB重试仅发送前。 |
| 取消/恢复 | 取消只按已知未发送/已发生事实结算，不释放未知在途作余额。新generation、旧登录/grant失效、paid关闭；停止旧authority并核独立最新ledger/grant/revocation高水位、后备份供应商/在途/撤销差额后才可另授权提升。无最新证据维持资金和线索注入关闭，不重发completed/unknown。 |
| 未来检查/预期 | `.venv\Scripts\python.exe -B -m pytest -c backend/pyproject.toml -p no:cacheprovider -q -rs backend/tests/unit/test_funding.py backend/tests/integration/test_pg_funding.py backend/tests/unit/test_pricing.py backend/tests/unit/test_project_ledger.py`；准确隔离Pg授权后验证双计/漏计/并发预留/commitunknown/send次数/恢复高水位/旧sessiongrant失效。T10接入后在同文件补admit/revoke两种提交顺序集成，先revoke拒绝，先admit只保其精确在途body。预期ledger/reservation/call逐笔相等、假send不超授权、未知不归0；受影响Ruff通过。 |
| 验收/风险/回滚 | 可见工件为账户与分配/grant/每call预留结算对账、覆盖缺口和恢复关闭截图/输出；缺真实对象约束、高水位、账覆盖或存在双权威即停线。回滚先paid_disabled停止新authority发送，保全部账/预留/撤销、拒旧代次；不恢复旧可消费资金副本。此切片完成不自动允许pilot。 |
| 独立审查/本人 | R2独立安全/并发资金审查与实际故障证据。本人聚焦CR：读reserve→admission commit→send→settle，运行两并发预留/unknown/旧备份恢复案例，解释为什么预算、余额、授权和在途不同；高水位保管/授权录入/恢复责任由本人在运行前确认。 |
| 估时/前置/授权 | AI约1–2个兼职工作日，本人约2–3h分摊首/次周，非额外加到66–96h；未知为历史账完整性/恢复代次联动。具体代码/隔离库/迁移/假调用另授权；实际grant金额/完整批次资金、计价≤24h快照、每次真实运行及供应商账单访问另确认。 |

### 近期包后的前置、本人参与与交付安排

T09–T13仍按主计划逐包开工前细化，不把现在可冻结的材料后置。准备阶段材料已用 `preparation.json` 具体定义；T13执行前只补实际code/worktree、model/provider/environment/renderer指纹、计价/账户/资金/grant、实际E2E核源种子及来源漂移，缺项不运行。T09 tokenizer为离线影子资格，未安装/未运行状态不改；只复用后续已获授权调用的可取得usage，不增加线上请求，不替换硬准入。测试金标与调试材料不混入请求，受控重排与自然任务分开。

| 前置/负责人 | 具体产物与本人确认时点 | 阻塞对象 |
| --- | --- | --- |
| T07-01环境/AI＋本人 | 准确host/port/database/role、库独占/空库/原件hash/常规迁移权限、WSL保活和清理范围；**创建/迁移/运行前**本人明确授权 | 首无模型工程的L3/运行，不因准备文件完成而已获准 |
| T12历史全账/AI盘点＋本人事实 | 账户/时段/仓库外调用/可得账单精度、稳定call映射、重复冲突/unknown/in-flight；本人当前回答“可取得程度未知”，对应只读访问前确认范围 | 真实pilot；不阻塞另授权T07代码准备 |
| T12权威/高水位/本人＋AI | authority/generation、旧authority停止、ledger/grant/revocation各最后序号/hash/截止、独立保存位置与保管人、备份后差额；**首付费和恢复提升前**确认 | 真实pilot与恢复提升；缺证据paid/hints保持关闭 |
| T13执行冻结/AI＋本人 | 运行code/model/env/renderer/资料漂移、实际种子report hash/facts核源、9/8/12 slots和评分既定值、全批资金覆盖/停止/逐次授权；**每个真实批次前**确认匹配性 | M1真实运行；不能将“材料已冻”当执行资格 |
| 加密备份/本人＋AI | 发行来源/校验/资格、介质、密钥保管/恢复人、独立目录/原件hash和实际恢复；**安装/备份操作前**分别授权 | 正式Go/相关恢复；不阻塞T07 |
| D0/首周校准/本人＋AI | D0仅在准备实际审查完成且首任务具体授权后起算；日常记录本人读码/亲改/测试/CR修复/运行/核源耗时；首周给剩余预测 | 超窗后的里程碑承诺；若96h对4周20h/周仍差16h，提出约5周20h/周或4周约24h/周选项，不删核心 |
| Git与交付/AI准备＋本人决定 | 每模块完整diff/指纹、适用CI真实状态、失败/未知、本人参与、复现/成功失败演示、兼容回滚及中文提交摘要；看过包后另授权Commit/Push/PR | Git交付；Merge/发布独立，CI或AI审查不自动授权 |

本人五类重点实践继续覆盖工具失败重规划、反证保护、线索撤销、漏样本和真实故障最小修复；T09/10/13实施后AI先提供关键源码/可复现命令/失败与预期，再记录本人阅读、预测、解释、实际修改/调试和回归。个人实践、技术测试、独立审查、本人业务验收、正式Go分列，不能代填。

回滚本轮准备文件只逆转本轮task-owned增量并按进入副本核对；新材料保留其审计身份，不清理历史或原工作区。最终检查、完整diff/指纹与实际独立文件审查由本轮交付补记追加；这些证据尚未返回前，不宣称全部开发前准备完成。完成后停在DEC-T07-01的具体实施授权之前；r12、P-02及正式产品仍No-Go。

### 2026-10-27 实际结果与完成标准裁决

本节是上述进入审计的结果补记，前表中的“本轮待检查/审查”保留为进入时状态，以本节实际结果为准。实际变更仅六份获批文件（本页、PLANS、CONFIGURATION、M1协议、evaluation README、STRATEGY）及30份新材料（preparation、23份来源JSON、6份许可）；没有业务源码/测试实现/依赖/数据库或正式协议变更。

检查证据：review-v2 verification（本机历史证据：`.tmp/prep-baseline-20261026-141454149872/continuation-20261027T093049764107Z/review-v2/verification.json`）记录35项检查、零error及完整正文/patch/指纹。项目校验加声明ledger、完整git diff --check、25份任务内JSON解析/重键、链接、来源定位/hash/范围、9/8/12槽位/顺序/逐轮报告、金标白名单、原费用/阈值与正式协议均通过。作者早期83项材料自检仅作辅助，不能替代最终35项及独立审查；先前缺preparation导致的链接失败已随最终复跑解决，过程见审计check-history.json。前轮4项无数据库pytest仍为中断无结果，本轮未重跑，不计通过。

HEAD仍e70b5f983532868b765e988f9162ddf989cf153d、暂存与新增提交为空；进入410份原文件的范围外字节保持，原SQLite哈希保持且无sidecar。旧16文件在进入时逐字节匹配已审查快照，旧结论继续适用；本轮增量另审。browser-use gitlink未变，内部Git状态仍因权限限制未核实，不能声称子模块工作树干净。

实际内容独立审查：技术报告（本机历史证据：`.tmp/prep-baseline-20261026-141454149872/continuation-20261027T093049764107Z/technical-review.md`）来自fresh-context reviewer `/root/actual_technical_review`；安全初审（本机历史证据：`.tmp/prep-baseline-20261026-141454149872/continuation-20261027T093049764107Z/security-review-v1.md`）及受影响补审（本机历史证据：`.tmp/prep-baseline-20261026-141454149872/continuation-20261027T093049764107Z/security-review-v2.md`）来自fresh-context security_reviewer `/root/actual_security_review`。审查者均非作者，有效权限共享workspace-write、实际只读，不虚称沙箱隔离；核对36文件完整正文/增量/HEAD差异/实际命令及指纹，独立重建patch吻合。未重新逐页打开所有远端材料，不代表未来人工核源已完成。

两项已核实P2已最小修复并独立复核关闭：①完整评测脚本只由控制端持有，每轮仅当前消息/已提交历史/已接受条件，禁止未来脚本与评分金标提前进入输入；②运行绑定按本次适用性/before时点/blocks_real_execution核对，E2E后种子在线索批次前、本人证据在M1验收前，避免循环前置，首跑资金/代码/真账户/授权门槛不变。最终无未关闭可确证P0–P3；这不宣称无缺陷或门禁已运行实现。v2完整任务patch为e9f6c22f34aaa188c030808ded7a65afef17e9a160a43798e67ac4686eaa53f9；本节补记后的最终指纹和独立补记复核由同审计目录final-delivery.json索引，不能用v2旧指纹代替本节审查。

| 标准 | 最终准备裁决与证据／后续阻塞 |
| --- | --- |
| C01 产品/任务 | 已满足；SPEC/ADR8及材料product_boundary保持通用产品与任务条件分离。 |
| C02 岗位映射 | 已满足；现有官方研究映射保持。真实能力/岗位适配为M1本人证据，不推定资格。 |
| C03 问题/价值 | 已满足准备定义；SPEC/研究有问题/替代/假设，真实价值仍须本人业务验收。 |
| C04 历史评估 | 已满足；前表链接和T01–06原状态保留，未将旧未验收项目升级。 |
| C05 本人确认 | 已满足；v4.3及本次具体落地计划已有明确授权，无新增产品/费用决定待补批。 |
| C06 核心验收 | 已满足设计与可观察验收准备；DEC-AC08–20、协议及评分全保留，实现/真实结果仍待M1。 |
| C07 实际调用链安排 | 已满足准备；契约/T09–13进入真实调用链的职责明确，当前未实施，不能记业务已达成。 |
| C08 设计/审查 | 已满足；复用原批准设计，新增实际内容经技术/安全审查及两项修复复核。 |
| C09 模块归属 | 已满足；契约和六卡明确模块/状态/数据/终态职责，后继切片开工前再固定实际基线。 |
| C10 任务里程碑 | 已满足；PLANS及六卡固定依赖/优先级，纯逻辑先行不替代真实对象集成。 |
| C11 本人实践 | 已满足可执行安排；卡片有代码入口/命令/预测步骤。实际解释/亲改/调试仍阻塞M1本人证据。 |
| C12 评测材料 | 已满足；preparation固定题面/条件/候选/来源/评分/9/8/12；运行版本、真实核源与种子按时点绑定。 |
| C13 环境资金 | 已满足事实核查与处置安排；准确隔离库阻塞首任务L3，账覆盖/F1/资金/grant阻塞pilot。 |
| C14 交付恢复 | 已满足准备边界；高水位保管在首付费/恢复前、工具/介质/密钥在备份前确认；正式Go/发布仍待证。 |
| C15 文件检查审查 | 已满足实际落地及上述检查/独立审查；本补记须有最终独立复核和指纹才生效。 |
| C16 时间未知 | 已满足；66–96h对60–80h供给冲突保留，首周实耗校准，超窗由本人选投入/期限，不降核心。 |
| C17 首包 | 已满足准备；T07-01明确受限文件、11入口、隔离Pg/旧夹具/回滚/聚焦CR/授权，业务仍PENDING。 |

**全部开发前准备的完成边界**：上列17项均已有实际准备证据或合理且有责任/时点的实施运行前置；以本补记的独立复核及最终指纹吻合作为完成生效条件。没有仍需本人决定而阻塞准备的事项。运行前须本人补充的账单范围/账户时段/仓库外使用/在途入口、高水位位置与责任人、备份介质/密钥恢复人，以及准确测试库操作授权，均挂到前述具体任务，未假装已回答。

第一业务任务仅待另行明确授权：T07-01受限源码/迁移/测试/旧夹具范围，准确host/port/database/role、WSL保活、建库/迁移/测试及清理范围。验收包按T07-C01–04和11入口矩阵、混合队列/唯一认领/无副作用/兼容回滚、独立安全实现审查及本人聚焦CR执行；Pg关键项未完成或skip不能记L3通过。资金到账不是此无模型包前置，Git写不包含其中。

本轮没有执行业务套件、数据库/迁移/WSL服务、真实模型/浏览器、tokenizer、远端CI、安装、余额查询或Git写。本人理解/业务验收、M1真实质量、正式Go和发布分别待证；r12、P-02及正式产品继续No-Go。完成后停在DEC-T07-01具体实施授权之前。

## 2026-10-27 当前 Git 改动审查与提交

用户本轮明确要求“审查当前git 更改，修复，然后提交”，授权当前改动与范围内审查修复的本地提交；不包含 push、PR、合并或发布。历史各轮未获 Git 授权的文字保留为当时事实。基线 HEAD `e70b5f983532868b765e988f9162ddf989cf153d`，初始暂存为空，审查含全部57份修改及新增文件；完整审查、检查、修复和交付证据见[本轮记录](../../audits/GIT_REVIEW_2026-10-27.md)。

本轮修复跨检出换行造成的冻结哈希失效，并纳入可重跑的离线报告生成器。用户随后要求缓存与无关文件不提交，因此报告输出、原始审计副本、完整patch及原件快照仅保留在本机 `.tmp`，上文已标其为本机历史证据；Git内仅保留必要脚本和精简审查记录。当前最终内容由本轮独立复审另行绑定。未来业务任务、真实模型/浏览器/数据库运行及本人验收仍未由本轮授权，No-Go保持。
