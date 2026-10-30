# DECISION-001 纵向任务与验收状态

当前主线（2026-10-30）：PREP-BASELINE-20261029原40路径的封存、原批准和独审证据已重新核实，原限定本机准备结论在其被审版本有效。本轮另获CONFIG-RAWJSON-20261030五文件修复批准，当前为IMPLEMENTED_PENDING_FINAL_ATTESTATION；只有本节末指定的新外置索引匹配本轮实际正文、检查及非作者独审时才算专项完成。原封存不覆盖新增量，也不因新专项而被改写。业务实施、真实评测、本人掌握、M1/Go/发布仍未通过；首业务拟授权包为DEC-M1-01，尚无开工授权。旧切片与日期记录只解释当时范围。

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


## 历史 M1 后续任务（PREP-BASELINE-v4.3，当时全部待具体实施授权）

T01–T06历史表及验收工件保留。本节是2026-10-26的目标记录，不是2026-10-29现行任务；新的DEC-M1系列见文末和[计划](../../../PLANS.md)。旧账户/真实MCP/9/8/12/四周等要求不进入新准入链；PENDING不是已开工或通过。

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

已确认：语音初始未知、经用户澄清接受；第3轮“全部本地处理、不上传音频”仅为评测演练；来源线索与上下文对照用 ORM/PDF；新增持久材料目录；历史供应商账单可取得程度未知。主材料入口为 历史preparation（固定Git commit1ffade6de07ebe3d1e72afb4c44b8677466eca67，path=data/evaluation/decision-m1-1/preparation.json，原字节SHA256=481da876ce5794020be05403eb7a75a75f0ce79194a1e40d2f468ca4535bde60），与历史补充协议配套（固定Git commit1ffade6de07ebe3d1e72afb4c44b8677466eca67，path=docs/evaluation/DECISION_M1_PROTOCOL.json，原字节SHA256=961dbf8d1dc94ed4ecad9b03cc8b1cf2aab78d7d8ff71cf773df905eaec1f8c8）；当前同路径文件已替换为新协议的能力引用，不是该历史配套版本。非业务runner、非运行授权。

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

## DEC-PREP-BASELINE-20261026：2026-10-28 重评续记

### 本轮要求、授权与进入基线

负责人要求持续完成开发前配置的调查、讨论、独立审查、本人决定及获批配置落地，达到18项准备标准后停在首个业务任务的单独实施授权之前。旧配置、旧批准及准备完成结论可重新评估；确认淘汰的配置原位替换/删除并清理引用，不新增旧方案归档。原始业务数据、真实运行/费用/授权证据、秘密和无关工作受保护。本记录承接此前任务，不另建协作体系。

本轮入口 HEAD `1ffade6de07ebe3d1e72afb4c44b8677466eca67`，`main`，根暂存/未暂存/未跟踪状态为空。最新代码提交另有[实际代码审查记录](../../audits/IMPLEMENTED_CODE_REVIEW_2026-10-27.md)，不能用上一节配置审查替代；其分阶段记录和最终结论需一起阅读。`browser-use` gitlink 为 `7be96ed8bafa8dfe1eef228b59cf5c884b8b2431`，未核实其内部工作树。初始正文及指纹仅存本机 `.tmp/predev-reopen-20261028/`，不作为新增旧配置归档。

本轮最初处于 Plan Mode，只调查和讨论；随后会话明确切至 Default。负责人“我的回答到达后：记录决定→更新主计划及受影响设计”的指令先授权本页连续记录维护，随后D19明确批准11份现有配置同步（精确路径见下）。不把未选候选写成正式要求；评测JSON、源码及其余配置不在本批修改范围。模式切换不授予业务实现、安装、环境写入、数据库、真实模型/浏览器、付费、充值、外部写入或Git写权限。

### 本人已确认的产品与约束

以下为本聊天2026-10-28逐题回复；D15明确区分本人委托与AI选择，其余为本人明确选择。本批已进入正式规格同步，最终检查与独立审查结果见本续记末段。

| 决定 | 本人选择与精确边界 | 对旧配置的影响 |
| --- | --- | --- |
| D01 用户与定位 | “扩大为从零发现候选的技术调研助手”；首个真实用户以本人需求起步 | 调整旧“已有少量候选、发现仅辅助”的主流程；不据此选框架 |
| D02 主要价值 | “主要减少人工搜索、整理和核源时间” | 新价值验收需计本人时间及共同质量；完整报告/短名单不自动证明省时 |
| D03 场景 | “沿用养老语音需求”；仅明确“居家老人陪伴问答”，其余由助手澄清，允许未知 | 旧评测指定的六候选、普通话接受及全本地演练不能变成真实硬条件或通用枚举 |
| D04 研究流程 | “先拆解技术路线，再发现候选并深查短名单” | 从零发现须独立验证；不是从既定候选名单开始 |
| D05 交互自主性 | 确认关键条件与研究范围后自动推进；重要方向/范围/费用冲突才问本人 | 普通搜索失败、换来源由Agent有界处理；未知不自动升为本人条件 |
| D06 真实替代与计时 | 对照“搜索引擎＋通用AI＋自己打开原文核验”；“没有可靠记录，先设计计时基线，不填写节省比例” | 尚无省时事实或百分比；计时/质量/样本/门槛待设计批准 |
| D07 时间 | 核心范围优先，约五周、每周最多20小时，首周校准 | 100小时是最大投入窗口，不是新估时；旧66–96小时未覆盖新范围，需重估读码/实现/测试/审查/核源/本人实践/交付 |
| D08 资金 | 新增真实运行总支出严格低于300元作为设计上限 | 旧49/30/200/20分配需重评；上限不等于余额、到账、grant或运行授权 |
| D09 产品交付边界 | 止于调研、核验及下一步验证方案；不执行语音集成或效果测试 | 保留不交付养老应用的边界；官方支持声明不等于老年人语音效果实测 |
| D10 价值验收强度 | “采用本人三对任务，先验证我的实际省时价值” | 预注册不同但尽量等价的三对任务；双方共同质量、顺序/熟悉度/全时间/失败记录；任务与旧批次关系及费用工时本轮再具体冻结，不直接叠加 |
| D11 省时目标 | “中位省时率至少20%，否则不算价值通过” | 以三对双方都达到共同质量且全部失败保留为前提；逐对省时率再取中位数，零/缺基线不通过；20%是批准目标，非已证实收益 |
| D12 搜索停止原则 | “按覆盖与证据增量收敛，并设硬上限，缺口诚实标明” | 工具故障不能算充分/饱和；决定性缺口仍在则partial/unknown；具体次数/额度和充分性规则在本轮准备阶段另定 |
| D13 等待用户 | “保存进度并结束本轮，答复后关联新一轮继续” | 保存证据和部分结果、释放执行资源；不是恢复Python指令位置，不重新从零取证；有效性重核及关联规则待契约固定 |
| D14 旧入口使用者 | “无必须持续服务的旧入口使用者，允许新主线单入口” | 保留旧数据和真实证据及明确查看/取证方式；没有授权现在删代码、停服务或迁移数据，也未自动选择数据库/框架 |
| D15 执行引擎委托与选择 | 本人答“为我选择一个技术深度深的，效果好的，不用考虑变更成本”；AI据此选择LangGraph内部执行编排 | 不再以迁移成本小推荐自建；真正拆阶段节点而非包整个旧loop。选择不是效果已优的实证；五周/20h与<300未被自动撤销。尚不授权安装/实现或捆绑最终部署拓扑 |
| D16 资料获取策略 | “Search／GitHub／Fetch优先，受限Browser补充” | Browser回退须安全资格/剩余额度/适用授权均满足，搜索失败不自动增加权限；供应商、具体动作/出站约束及重试额度仍待本轮固定 |
| D17 部署 | “T2：WSL独立API／Worker＋PostgreSQL” | 单一新主线，Windows访问UI；替换Windows进程＋WSL库目标，旧真实证据保留。尚未验当前Linux环境，不授权环境写入 |
| D18 工件存储 | “S1：有界工件同入数据库及上述上限” | 安全来源表示/可重处理响应同入Pg；单份1MiB、每轮64MiB、项目新增1GiB未压缩工件上限。超过诚实partial；磁盘/WAL/备份另计，容量/真实质量未验 |
| D19 本批配置批准 | “批准上述11份配置范围” | 仅AGENTS.md、SPEC.md、PLANS.md、CURRENT_CONTRACTS、feature spec/tasks、ADR5/7/8、docs/README、CONFIGURATION；同步本轮已决产品/运行设计及引用，替换冲突旧规则，未决标明；不含源码、安装、DB/环境、真实运行、Git写/发布 |

### 主清单：18项完成标准与阻塞层

状态只对本轮成立。`准备`表示阻塞开发前准备完成；`首工`表示首个无模型工程任务；`pilot`表示真实研究诊断；`M1`表示首阶段验收；`Go/发布`分别保留正式放行与发布决定。当前没有新业务开工授权。下表是唯一主清单，旧17项表只保留原日期证据。18项的准备裁决均以文末外置最终索引及独立增量复核匹配为生效条件；未匹配前仍不计全部完成。

2026-10-30专项承接：原40路径条件已由原r2快照/原final-delivery实际核验满足，原审查仅绑定其原字节。下表09/13/15/16/17增加本次五文件增量；其余项沿用原证据和原有后续资格。新专项状态由CONFIG-RAWJSON节的新索引承接，不要求旧索引反向匹配后来的获批修改，也不将当前正文自身当完成证据。

| 项 | 当前事实/证据及实际文件 | 判断/决定/批准 | 检查与独立审查 | 未解决项 | 阻塞对象 | 下一步/负责人/满足时点 |
| --- | --- | --- | --- | --- | --- | --- |
| 01 产品与核心路径 | SPEC/契约§1/本页D01–19 | 从零需求/有限深查/诚实partial已批；准备定义满足 | r1整体实际审查及文末增量复核绑定 | 无新增准备选择；真实价值待M1 | 准备按文末条件生效；价值M1 | AI固定文件与证据；本人另验价值 |
| 02 岗位映射 | 岗位研究与本页实践卡 | 岗位→行为→任务/AC映射已备 | r1实际文件复核；原百度J100779定点核源和其他动态页局限保留，未重新核全网 | 本人实际读改解释未发生 | 准备按文末条件生效；本人证据M1 | AI交实际材料；本人对应任务实践 |
| 03 Requirement/AC | feature spec DEC-AC-08–20/唯一协议 | AC获批；材料准备满足 | 原五评测文件实际复审DONE，准确hash及后续元数据增量分开 | 实际难度/真实核源与评分未验 | 准备按文末条件生效；真实评分M1 | AI保留题面隔离；本人另授权正式运行 |
| 04 核心架构 | ADR5/7/8/契约§1–6 | LangGraph/T2/S1及精确边界整体批准 | r1整体/安全实际审查；原限定设计证据不扩大为实现 | WSL/新库/连续性/恢复未运行 | 准备按文末条件生效；运行首工/pilot | ENV准确操作包及权限另授 |
| 05 模块与数据归属 | 契约对象/API/StageOutput及本页任务包 | Pg权威/checkpoint引用/唯一Task状态已冻结 | r1整体核对接口/锁序/目标与旧实现边界 | 未来业务实现与验收 | 准备按文末条件生效；实现各Task | AI按获批任务逐包落实，不据配置开工 |
| 06 五核心方向 | 研究/PLANS/DEC-M1-02–08 | Runtime/Tools/Context/Memory/EvalTrace纵切安排满足 | r1实际文件复核；固定上游证据不代表项目效果 | 模块实际行为和失败证据 | 准备按文末条件生效；实际M1 | AI在对应任务交运行材料；本人分卡实践 |
| 07 失败/资源边界 | 契约§2–6/协议调用及容量 | unknown全项目停线/repair0/有限参数已批 | r1安全核对guard/历史读取及设计边界；没有真实故障验收 | Tokenizer/网络/资源/故障资格 | 准备按文末条件生效；故障首工/pilot/M1 | 对应Task按风险检查；无资格不运行 |
| 08 任务/依赖/里程碑 | PLANS/本页DEC-M1/ENV包 | 首工auth原始草稿+sup；03a/03b/08a依赖已明确 | r1整体核对FIRST-r2及依赖/验收包 | ENV准确路径/身份/依赖/业务授权 | 准备按文末条件生效；执行首工 | 先交具体ENV操作包，不先启动WSL |
| 09 测试/审查/验收 | STRATEGY/WORKFLOW/本页CONFIG-RAWJSON | 原结果保留；补严格JSON/材料类型与映射覆盖 | 新49回归、七文件200通过；失败/沙箱超时保留；新独审依专项索引 | 本专项实际文件独审/封存条件；真实集成/本人未验 | 专项完成；未来材料依赖该校验前关闭；非当前首工技术阻塞 | AI取得独审/封存；本人另验业务 |
| 10 评测/Tracing/优化 | 唯一协议/六题材料/契约§5 | 三对六稿共质后中位20%；真实纠正1症状 | 五文件实际复审关闭原四项；三JSON只更新审查与单向hash，另审增量 | 正式seed/尝试/调用为null或0；真实结果未验 | 准备按文末条件生效；执行pilot/M1 | 不提前展示题面/金标，不自动生成seed或调用 |
| 11 本人实践 | 本页任务实践卡/岗位研究 | 读码/预测/操作/亲改/回归/解释安排满足 | r1实际文件核对；没有本人实际实践证据 | 对应业务Task实施及亲验 | 准备按文末条件生效；本人实际M1 | AI交可跑材料，本人执行，未做不代填 |
| 12 环境/资金/权限 | CONFIGURATION/契约ENV与成本 | 新独立PG/凭据/费用上限的处置安排满足 | 原只读环境快照未作当前运行资格复验；旧账仍有未知 | 启动前autostart隔离/路径/角色；账户/价格币种/全账/资金/grant | 准备按文末条件生效；ENV首工；资金pilot | 准确环境操作另批；无资格paid关闭 |
| 13 Git/CI/复现/恢复 | CI/契约B5.2/BK/本页CONFIG-RAWJSON | 保留原本机封存；补两JSON精确-text，保持raw hash | Git只读真实过滤器三路径×三配置通过；新独审依专项索引 | 完整clone/远端CI/子模块内部未验；介质纸钥恢复仍待 | 专项及跨检出交付；恢复pilot；不单独阻首工 | AI封存增量；Git/环境/真实恢复分别另授 |
| 14 时间/费用/未知 | 本页投入/协议成本 | 10/29起7–8周≤20h周；100–144人时；296.46条件分配 | r1实际文件/算术核对，非工期或运行资金充分证明 | 首周实耗校准/真实价格账户及DR免费额度 | 准备按文末条件生效；资格pilot；实际M1 | AI首周校准；超窗取舍本人决定 |
| 15 配置落地/淘汰清理 | 原40路径及专项五文件进入副本 | 原37改2增1删保留；新五文件另批，相对HEAD累计41路径 | 三现行JSON及范围外原字节保护、完整累计diff/两新增正文由专项封存核验 | 新增量独审/最终索引匹配；不把旧授权改成41路径 | 专项完成 | AI仅逆转本专项进入增量；不reset/clean |
| 16 检查/指纹/独立复审 | 原封存＋repair-20261030-raw-json | 原审查身份保留；新五文件不得借旧审查关闭 | 新检查/完整正文/增量/累计diff须绑定新manifest；最终独审/索引另存 | 新final-delivery必须存在且匹配；不预填审查结果 | 专项完成；不否定旧被审版本 | AI冻结新正文、取非作者实际审查后封存，不回写自身hash |
| 17 准备阻塞决定清零 | 原01–16＋CONFIG-RAWJSON四P2 | 旧批无未决结论保留；新五文件修复已具体获批 | 设计技术/安全复核完成；实现关闭依新独审和索引 | 新专项未完成前不称四缺口已关闭；其他重要范围另批 | 专项/跨检出交付；非当前首工技术阻塞 | AI验证修复与独审；不扩大费用/权限/业务 |
| 18 首业务授权/验收包 | 本页FIRST-r2/PLANS/契约§7 | 可审查拟授权包已备；配置批准不等实施批准 | r1整体/安全核对目标/范围/验收/回滚；未来代码未创建 | 准确ENV/依赖/业务实施分别另授权 | 准备按文末条件生效；执行首工 | 停在DEC-M1-01业务授权前，不自动开工 |

### 2026-10-28当时的旧配置判定与保护范围

本表按D19区分已批准11文件调整与后续待批范围；后者不是删除许可。逐项检查引用和证据依赖，不将整目录按年代删除。

| 对象 | 判断候选/依据 | 影响与当前授权状态 |
| --- | --- | --- |
| SPEC/feature spec中的有限已知候选优先、四周定位 | 调整：与D01/02/04/07不符 | D19批准后已原位同步PLANS、产品ADR及导航；新AC细则仍待本轮设计批准 |
| 旧M1预置候选题、9/8/12与正式15次门槛 | 分别判定保留/调整/替换，不能机械相加或全部删除 | 已知候选回归不证明发现；批次和价值测量重设计；原运行证据/授权/费用不改 |
| 引擎/拓扑与旧实现细节 | D15/17已决定LangGraph内部阶段图及T2；待定仅精确接口/运行细节，不能把引擎/拓扑混列待选 | 2026-10-29具体细则见现行契约；方向不授权安装或环境写入 |
| G0–G7、原连续记录、独立审查与授权分离 | 拟保留并按本轮范围调整必要内容 | 不建立平行体系；实际需要修改的规则仍列入批准范围 |
| AGENTS与CONFIGURATION的当前ADR导航 | 调整：旧导航未反映重评范围 | D19批准后已同步唯一现行入口及ADR5/7/8；本批实际审查另记 |
| 本页最新审查入口 | 调整：旧配置审计不覆盖HEAD的19路径代码增量 | 本续记已链接实际代码审查；历史审查不被覆写 |
| 原始SQLite/r12/费用/授权、原审查证据及上游checkout | 保留原件与原身份 | 不属可随意删除配置，不改Git历史；没有清理操作 |

### 定点研究与设计审查状态

研究问题仅限“从零需求怎样展开搜索、发现候选及停止并保留证据”。2026-10-28通过官方仓库读取 GPT Researcher 固定提交 `3582a6841fe7dc801e2a34e34ee408641aea9bce` 的源码、测试与合并记录，未运行上游或模型。普通流程初搜后生成子查询；深研究按query/researchGoal和followUpQuestions展开，深度/零查询/全分支异常控制执行，但没有候选穷尽证明。澄清自动填答路径不能代替真实用户接受条件。

来源：[researcher.py](https://github.com/assafelovic/gpt-researcher/blob/3582a6841fe7dc801e2a34e34ee408641aea9bce/gpt_researcher/skills/researcher.py)、[deep_research.py](https://github.com/assafelovic/gpt-researcher/blob/3582a6841fe7dc801e2a34e34ee408641aea9bce/gpt_researcher/skills/deep_research.py)、[初搜来源测试](https://github.com/assafelovic/gpt-researcher/blob/3582a6841fe7dc801e2a34e34ee408641aea9bce/tests/test_planning_sources.py)、[全部分支失败测试](https://github.com/assafelovic/gpt-researcher/blob/3582a6841fe7dc801e2a34e34ee408641aea9bce/tests/skills/test_deep_research_empty_results.py)、[零查询测试](https://github.com/assafelovic/gpt-researcher/blob/3582a6841fe7dc801e2a34e34ee408641aea9bce/tests/skills/test_deep_research_zero_queries.py)。[PR2145](https://github.com/assafelovic/gpt-researcher/pull/2145)已核验合并 `816e893e34c6f63d782a60e858c309b4218404af`，修复初搜来源后续丢失；作者测试报告不是本项目执行结果。URL发现/访问记账不等于正文抓取或主张核验。

待选取舍：保留“初搜校正术语、追加查询说明证据缺口、初搜证据不因后续失败丢失”的机制；不照搬假澄清、无限递归或用visited表示核源。新任务中实际遗漏路线、候选/证据增量和费用会改变停止阈值/展开策略选择；质量、候选覆盖、省时及真实成本目前均未知。本节只提出设计依据，未批准实现或固定阈值。

独立基线审计 `/root/baseline_audit`（fresh context）读取任务/工作流/规格及历史审计，确认旧17项最终证据确实存在且绑定原内容；提出导航滞后及最新代码审查入口缺失两项P3。本次不否定旧审查存在，也不把旧结论扩张到新范围。

独立产品评测设计初审 `/root/product_eval_review`（fresh context）结论 DONE_WITH_CONCERNS：已知候选测试加一次演示不足；省时比较缺共同质量/计时终点/失败规则；搜索故障不能算饱和；新批次不能直接叠加旧批次。已据此修订候选，复审及本人选择尚待返回。所有审查者实际共享workspace-write权限，按任务只读，不宣称沙箱隔离。

### 2026-10-28候选比较与当时决定（后续细则见2026-10-29续记）

1. 新产品验收比较过已知候选回归加演示／从零任务及本人计时对照／多用户对照。本人已选第二种的三对任务方案D10；第一种不足以证明新发现/省时价值，第三种不纳入本阶段。
2. 省时对照设计：养老语音用于真实诊断；预注册三对不同但尽量等价任务，双方同交付清单、质量及限时，顺序交错，熟悉度披露，失败/超时不剔除且不算胜出。双方从收到题面开始，直到完成满足共同质量的交付清单，其全部本人主动时间均计入，包括澄清、搜索、提示交互、阅读、整理、核源、结果整合/交付、纠错及独立审计触发的返工；纯等待与独立审计自身用时另计。每对省时率为(人工主动时间－辅助主动时间)/人工主动时间，零/缺失基线不可计算。三对双方均过共同质量后再比较逐对及中位数；本人已选中位数至少20%的产品目标D11，仅支持本人本批描述，不作普遍因果结论。具体题面/共同质量清单/限时及完整费用仍待本轮冻结；当前没有20%收益的实际结果。
3. 停止比较过固定次数／质量与覆盖导向且有硬上限／增加本人逐路线决定。本人已选第二种原则D12；有效新增涉及路线、身份、决定性条件、限定语或反证，镜像/重复不计。覆盖完成、无增量、故障、额度/时间上限、取消分别记录；故障不得累计饱和，关键缺口仍在时只能partial/unknown。具体次数、限额及判定必须在准备结束前定清，不推给业务实施。
4. 旧评测角色、批次替换/复用、完整费用与本人投入需先共同核算，再批准最终协议。正式当前文件未改，不借新方向静默取消历史No-Go。

### 架构与数据流比较及决定：方向已批，细则仍待完成

负责人已要求直接深入架构/数据流，不再重复产品定位确认。当前只读研究已核对本地[循环](../../../backend/src/adaptive_research/agent/agent_loop.py)、[Worker](../../../backend/src/adaptive_research/worker/runner.py)、[PgStore](../../../backend/src/adaptive_research/infrastructure/pg_store.py)、Pg模型和API。已有循环包含观察/上下文/规划/执行/评估、限额和取消；Worker包含租约/事实事件恢复对账；PgStore包含fencing和终态/报告/事件事务。新会话/阶段、从零发现链和统一资金准入并未因此实现。原技术失败一次重试不能不分工具语义照搬。

| 候选 | 实际收益与进入调用链的位置 | 代价、未验证与当前判断 |
| --- | --- | --- |
| A 自建循环＋独立Worker/Pg | 复用Planner/ContextManager/Evaluator/ToolRouter/Reducer与现有持久化；显式发现、深查、归纳和退出阶段。等待用户按D13结束本轮后新开关联轮 | 曾因迁移面小推荐；本人随后要求不考虑变更成本并委托选择，现不选A。保留它作为机制/恢复复杂度比较依据 |
| B LangGraph作为内部执行引擎 | 循环拆节点、状态与checkpoint，明确条件路由、有界并行、归并与节点恢复；应用持久库拥有业务事实 | 已按D15委托选择。新增依赖/适配/双持久化对账；interrupt会重执行节点，不能保证外部调用exactly-once。选择理由是阶段编排/可观察恢复，非等待用户需要interrupt；最终部署拓扑另选 |
| C smolagents ToolCallingAgent替代循环 | 同API/应用Pg，复用通用工具规划、步骤记忆/反馈 | 同步/异步桥接、账本/事件映射仍需做；内存interrupt不等于持久恢复，达到max_steps后的最终回答另有模型调用；不引入CodeAgent任意代码执行 |

上游固定版本与观察日：2026-10-28，LangGraph `3cd57c038ad827d05f80c6488adea9994156c58c`，smolagents `96f33faaf028479119ec8d34507b47694cf14e34`。已读取[LangGraph interrupt](https://github.com/langchain-ai/langgraph/blob/3cd57c038ad827d05f80c6488adea9994156c58c/libs/langgraph/langgraph/types.py#L903)、[pending writes恢复测试](https://github.com/langchain-ai/langgraph/blob/3cd57c038ad827d05f80c6488adea9994156c58c/libs/langgraph/tests/test_pregel.py#L891)、[timeout/retry测试](https://github.com/langchain-ai/langgraph/blob/3cd57c038ad827d05f80c6488adea9994156c58c/libs/langgraph/tests/test_retry.py#L720)、[smolagents循环](https://github.com/huggingface/smolagents/blob/96f33faaf028479119ec8d34507b47694cf14e34/src/smolagents/agents.py#L540)及[规划/记忆与中断测试](https://github.com/huggingface/smolagents/blob/96f33faaf028479119ec8d34507b47694cf14e34/tests/test_agents.py)。未安装/运行上游，未证明本项目质量改善。B的收益假设是阶段边界、有界并行和针对缺口的补查便于观察/调试，必须通过故障测试、本人代码实践及真实质量/省时对照验证；框架热度不是效果证据。

候选公共数据流：用户确认目标/条件/范围→API对象及提交校验→Pg提交条件revision和有限研究轮→Worker认领→路线/问题/证据缺口规划→统一调用入口→Search/GitHub/Fetch/必要Browser→不可信观察及来源保存→候选实体去重/证据准入→上下文编译→继续规划或核对停止→结构化结论/报告校验→Pg发布→SSE。路线假设不是用户硬条件；初搜线索不是准入事实；官方检索器的authority分数也不代替主张核验。

| 对象/边界 | 拟定责任与数据归属 | 必须检查的失败；尚待准备阶段定清 |
| --- | --- | --- |
| Session/条件revision/研究轮 | Session承载长会话与active指针；条件由本人接受后不可变修订。倾向一轮复用一个PgTask作为唯一执行记录，不另维护Turn.status双真相 | 双提交/改条件/取消竞争；1:1关系与具体schema待架构批准 |
| 路线/查询/候选 | Planner产有理由的假设/查询，候选有独立身份及发现来源；发现池与深查短名单分开 | 镜像去重、初搜有效后后续失败、漏路线、重复无增量；查询/发现/深查上限待本轮固定 |
| 来源原文/事实/结论 | 保存来源身份、版本/时间/定位和hash，区分发现/抓取失败或成功/摘要/原文/支持/反证/未知；报告引用可追溯 | 摘要不能冒充原文；错主体/版本、断链、早期反证裁剪；原文存储与大小策略待定 |
| Context/Memory | 模型输入是应用证据的投影，不改持久原件；条件、限定语、反证/冲突与失败进入选择；记忆不是checkpoint | 未识别/未绑定/被裁剪/模型未使用分开；读取/撤销/到期/隔离与是否跨轮复用待具体设计 |
| 统一CallGateway | 每个物理模型/搜索/抓取/浏览器/MCP调用都有身份、参数校验、权限/限额、调用账和适用费用；发送前持久意图/预留，之后记结果/usage/费用 | 发送/提交结果不明不能通用重试；确定性DB重试不能包住已发送网络；准确接口/错误分类待设计 |
| 发布/恢复 | Pg拥有已接受事实、授权费用、报告/用户事件及唯一终态；框架checkpoint只辅助。报告/终态/event/active释放原子 | 发送后崩溃、响应后提交前、提交后checkpoint前、失租迟到写、取消/超时/二次故障；不得把框架完成当业务完成 |
| 单入口切换 | 拟冷切换并停旧研究写入口/旧Worker；保护旧SQLite和真实证据，不继续维护两条新功能运行链 | D14不自动免除旧Worker误启动风险；需核队列/在途/unknown、启动版本门禁、旧连接/凭据或必要写护栏，再决定旧T07-01保留/替换部分；未授权实际操作 |

fresh-context security_reviewer `/root/runtime_arch_review` 已完成架构方向/技术安全审查，核到五项缺口并复审补充约束，认为可供本人选择方向。以下成为候选必须满足的设计约束，尚非保护已经实现：冷切换失效旧写凭据/处理存活连接及队列，不能只给新程序加版本检查；统一网络/动作政策覆盖Browser导航与子资源等，隔离无个人登录会话；模型/收费Search/Fetch/Browser内部模型/repair/summary/SDK重试全部覆盖调用准入；Turn持久截止、恢复不重置且新轮不自动续grant；路线/候选/查询/缺口/停止原因持久，确定性硬约束与模型充分性意见分开。若无法验证旧Worker不能再写，保留必要DB护栏；无需默认支持滚动混跑。具体工具/迁移实现和验收仍须在准备结束前定清。

### LangGraph节点、数据归属与恢复协议草案

本段是D15方向的详细设计草案，不是已批准实施契约。研究图暂按：载入已接受revision和运行边界→规划路线/问题→有界分派查询→取源→抽取候选/证据观察→归并并找缺口→确定性路由（继续/深查/需要用户/完成/达到上限）→上下文编译与结构化结论→校验/发布。每节点须有明确输入输出、幂等身份、可持久结果和重入策略，禁止只将整个旧AgentLoop包成单节点。

| 数据/职责 | 拟定归属与关系 | 设计中必须保持的不变量 |
| --- | --- | --- |
| 会话及已接受条件 | 应用表Session/InputRevision；Session持active_task_id，revision追加 | 同owner/session；用户接受才能生效；修改条件产生新revision，旧轮绑定不变 |
| 研究轮及恢复attempt | 倾向1 Turn=1 PgTask唯一执行状态；attempt记录每次认领/fence | 创建task、revision绑定及active指针同事务；所有终态含reconcile均清除匹配active；恢复不是新轮 |
| 逻辑工作及物理调用 | WorkItem与CallAttempt分开；逻辑身份为turn/phase/work_id及显式输入版本 | 工作唯一约束；工作认领、当前fence/代次、精确请求绑定和准入转换原子。新hash不能绕过旧unknown；一个逻辑工作可有已说明理由的物理attempt，不盲重发 |
| Graph state/checkpoint | 只持序列化ID、计划版本、work ID及已提交输出引用；不成为事实/费用/授权权威 | 当前owner/revision/fence/grant/截止从应用运行上下文验证，不能信任checkpoint中陈旧授权；不默认外发远端Tracing |
| 结果工件与阶段输出 | 每类节点定义足够重处理的有界、脱敏响应及hash/工件引用；来源原文与模型摘要分开 | completed与可重处理响应引用一致提交；阶段输出另提交后推进checkpoint。缺失/校验失败则partial/failed，不从摘要伪恢复；持久化前崩溃诚实unknown |
| 并行归并 | 只并行独立只读取证；每个外部调用单独账/预留，结果稳定ID归并 | 分支不任意修改共享条件/候选事实；应用有全局并发及预算约束，具体数值本轮另定 |
| 停止与迟到结果 | 应用先关闭该Turn新增准入→有界取消/收拢在途→发布终态 | 未使用许可可按提交先后撤销；已进入发送的请求按在途处理，不承诺网络撤回。unknown保预留；迟到响应不改已发布报告/事实，只走受限审计/费用对账 |

关键恢复切点：发送前准入提交结果不明→不发送并核对；发送后响应未持久→unknown不重发；调用completed但阶段输出未提交→仅从合格响应工件重处理；应用阶段输出提交但checkpoint落后→复用输出引用不重发；checkpoint领先但应用引用不存在→拒绝伪恢复。应用表与checkpoint即使同在Pg也不假定跨写入原子。

LangGraph专项独立审查已指出三项设计失败场景：仅稳定ID不足以防并发重复发送；completed调用可能缺可重处理结果；分支停止可能与其他发送/返回竞争。已据此补入上表唯一工作/原子准入、响应工件及停止收拢协议。2026-10-28受影响复审 DONE，三项在设计约束层关闭；审查者实际读取495–535行、快照和检查记录，独立核对Git状态及diff检查，绑定正文 `403c6e2750e8b62a131edd5f9a61ca3c983e3becef3fac58e69867621075cbca`、patch `6dcbc142327e9a3b43d5e86e9d0cf7d93629325387b3087fc7c706b5e6d30559`。此结论不覆盖后来新增设计或任何实现。验收必须覆盖双执行者同工作、失租后新准入拒绝、响应/阶段/checkpoint各提交边界，以及停止-发送、取消-返回、失租-阶段提交的两种顺序。旧准入已进入在途的语义单独保留，不声称fence可撤回网络。

后续D17/18已批准部署拓扑与工件存储及大小上限，D19批准本批配置同步；下列比较保留决策依据，不是并行现行配置。节点schema、并发/重试/时限、出站网络实施与迁移阻断仍须在准备阶段确定，不以方向决定开工。

补充固定版本核查：LangGraph同一commit的[AsyncPostgresSaver](https://github.com/langchain-ai/langgraph/blob/3cd57c038ad827d05f80c6488adea9994156c58c/libs/checkpoint-postgres/langgraph/checkpoint/postgres/aio.py)中，`setup()`会建表并执行迁移，不是只读资格检查；`aput`/`aput_writes`写框架专有checkpoint/blobs/writes，使用psycopg连接，不能把它与现有SQLAlchemy/asyncpg应用事务天然视作同一次提交。后续须锁定兼容发布版本和独立schema/角色/迁移流程；本次仅读源码，未调用setup、安装或测试。默认不持久化完整graph消息历史，以免把所有来源/秘密重复散入checkpoint。

### 原文、响应及证据链存储比较（S1及上限已按D18批准）

本项解决两种实际失败：已完成的调用在进程重启后无法继续处理，以及报告有URL却找不到当时支持结论的内容。现有 `PgCallAttempt` 主要保存输入/输出digest及usage，`PgFact` 保存片段/定位，`DecisionService` 以label的casefold哈希生成候选ID；这些不等于完整来源快照、稳定实体身份及重处理协议。相关入口为 `backend/src/adaptive_research/infrastructure/pg_models.py`、`agent/state.py:110`、`agent/decision.py:39`。新路径不得把预置语音角色或候选编码进公共schema。

| 存储候选 | 收益与具体代价 | 当前建议与改变选择证据 |
| --- | --- | --- |
| S1 有界正文/可重处理响应和索引同入Pg | 响应工件与调用完成可同一应用事务提交；报告、原文、引用可纳入同一数据库快照。代价是正文带来的WAL、数据库/备份体积，需容量准入且不把正文放事件或checkpoint | 当前推荐，适合首阶段有限公开文本研究；若实际存储/恢复耗时超出冻结上限或需要大量PDF/图片/音频，重新评估S2 |
| S2 内容寻址文件工件＋Pg索引 | 大工件与业务行分离、未来易替换对象存储；代价是写临时文件/校验/持久化/原子发布后才能提交DB引用，存在孤儿与双介质备份、恢复清单和丢文件诊断 | 可行但需要完整工件协议，不能仅存任意路径；本阶段未证明二次持久化机制的收益足以抵消恢复复杂度 |
| S3 只存URL、片段、摘要 | 存储最少 | 不推荐：无法恢复已完成调用的处理，页面漂移后不能核验原观察；不满足当前复现目标 |

2026-10-28读取 PostgreSQL16官方[TOAST](https://www.postgresql.org/docs/16/storage-toast.html)、[SQL dump](https://www.postgresql.org/docs/16/backup-dump.html)、[JSON类型](https://www.postgresql.org/docs/16/datatype-json.html)。Pg可透明处理较大变长字段，`pg_dump`提供数据库内部一致快照；这不等于备份含外部文件、角色配置、最新授权/资金高水位或本机已恢复成功。JSONB不会保留键顺序/空白/重复键，故需按表示分别保存安全原始字节或文本、解析JSONB及各自hash，不能把JSONB重序列化hash宣称原响应字节hash。未运行数据库或备份。

S1已批准工程边界：单个安全采集表示及单个模型响应各至多1MiB；HTTP/工具响应解码后读取也设硬上限，不能只限Content-Length或压缩传输大小。每Turn应用工件总额64MiB、项目新增应用工件总额1GiB，按未压缩字节计并在接收前预留，防并发越界；不足则记录capacity_limit并交付可核验partial，不自动删除历史工件。这些是D18批准的首阶段限制，不是数据库实际大小或质量结论。checkpoint、索引、WAL和备份另作实测容量/磁盘余量门槛，不能被这1GiB数字覆盖。模型Token/时间/费用上限另有限制，不能用字节上限替代。

证据链拟分为：Query/发现记录→SourceCapture→CandidateIdentity→Claim/EvidenceLink→ReportSnapshot。SourceCapture保存请求/最终URL、获取工具/方法、获取时间、可取得版本/发布时间、内容类型、采集表示种类、完整/部分标识、hash及提取版本。Fetch返回Markdown只能称供应商返回表示；Browser DOM提取不能称服务器原始HTML。敏感内容检查和安全元数据白名单在持久化前执行；拒绝/脱敏导致不能重处理原响应时标unusable/partial，不谎称completed且可精确重放。原始凭据、Cookie、Authorization等不进入工件。

CandidateIdentity以稳定应用ID关联官方域名/仓库等身份依据、别名及出处；字符串同名只形成待归并建议，不能自动把同名产品/版本合并。Claim必须关联精确采集版本的片段/位置、主体和适用条件；支持/反证/限定语并列，模型抽取与人工核源状态分开。结构校验检查引用存在、owner一致、片段确在所指表示中及版本/hash吻合；语义支持仍属模型判断和人工核源，不能由子串命中证明。报告绑定条件revision、事实/工件ID与内容hash，不静默替换旧原文。

正文不重复塞进SSE/Trace或LangGraph checkpoint；它们存安全摘要/ID。后续上下文编译按ID和任务相关性选片段，保留未选/裁剪原因。小规模检索可先用关系字段、关键词与ID回取；是否引入Embedding/Reranker尚须在RAG设计讨论中决定，S1不隐含向量库。重新抓取生成新SourceCapture；变化只影响新判断，旧报告保留当时证据。原始业务/费用/授权及历史运行证据不在自动清理范围。

拟定验收：超长/压缩膨胀/并发容量竞争；响应与完成记录事务切点；精确hash/引用/同名异主体；来源漂移及反证保留；离线恢复后报告→片段→原工件完整；敏感字段拒收；损坏工件不重发已完成调用。真实网页提取质量、语义支持和人工核源省时必须另授权真实集成/评测验证。负责人：AI落实契约/测试包，工程负责人批准存储取舍和本人核源路径；阻塞准备完成，不需现在运行数据库取得未来实现证据。

### 部署拓扑比较（T2已按D17批准）

只读调查明确：Windows API/Worker＋WSL Pg已部分实现，并非ADR5标题所称整体“未实施”。2026-10-21 P-01第二轮假任务48/48通过，原始 `data/p01/measure-r2-20261021.json` SHA256 `55b3ac8fec10f53e974a1899823d4ddcbaa336e2c9e8b7f6339d8e33f093d6de`已重算；不外推到新LangGraph/真实Browser。`scripts/start-p01.ps1:71`启动会保活WSL、检测/必要时启动Pg、自动迁移，然后启动API/Worker；125行起只有Worker退出自动重启，API退出触发清理，数据库故障后需人工恢复再重启。新方案需把迁移从普通启动中分出，由明确授权的迁移步骤负责，防止启动即环境写。

| 候选 | 用户可见故障行为、技术收益 | 代价/资格/当前判断 |
| --- | --- | --- |
| T1 Windows API/Worker＋WSL Pg | Worker故障时API仍可查看已提交进度/提交取消；复用既有跨系统假任务证据 | PowerShell、Windows Python/Browser、WSL生命周期与两侧网络/日志均需排障。无必须Windows个人浏览器/profile的需求，不因旧批准自动保留 |
| T2 WSL内独立API/Worker/Pg，Windows仅访问UI | Worker异常时可独立停止/重启，API继续提供已提交进度；后端、持久库与将来的隔离Linux Browser同运行环境，更贴近可复现Linux交付 | 推荐给重视Runtime故障诊断/交付练习的本项目，但非研究质量保证。需学习Linux环境/进程监督，资格与真实负载未验；宿主/WSL重启仍会一起中断，不能宣传高可用 |
| T3 单进程API＋LangGraph＋SQLite | 单人串行研究组件最少，同样可做持久调用账/证据/恢复；适合接受API重启时研究一起中断 | 框架/工具阻塞或进程退出同时影响交互与执行；SQLite单写者需限短写事务。无Pg服务但并非免除未知费用、恢复及备份设计；独立研究者认为以单人价值验证优先时应认真考虑此项 |

T2推荐依据是用户要求的独立故障诊断、取消和恢复/交付学习可进入真实运行链，而非框架/组件数量，也不是单用户吞吐必须Pg。T3是有效简化选择，不能称技术浅；采用它将S1理解为同一SQLite事务库持有有界工件，并重新审查数据库锁与checkpoint适配，不能直接沿用Pg契约。T1只有后续必要Linux Browser验证失败而Windows可满足等证据才可能优于T2；不会擅自回退。

T2拟定部署边界：一个本机WSL发行版，API与Worker独立进程，同一个Pg实例的应用schema与checkpoint schema分权；不引入Redis、消息代理、Kubernetes或云托管。Windows仓库仍为本项目开发入口；Linux虚拟环境/数据库/浏览器临时数据位于Linux文件系统，具体创建路径和同步/构建方式在环境包中固定且另获写入授权。运行时凭据不具迁移/DDL权，checkpoint `setup()`属部署迁移；API/Worker普通启动仅验证schema/version并失败关闭。API只开放本机访问，Pg不为局域网开放；本机认证、Host/Origin/CSRF及owner校验仍须设计/测试，不把loopback当身份认证。

冷启动顺序拟为：检查已授权环境和代码/依赖身份→检查持久库/应用与checkpoint版本→启动API与Worker→离线健康检查；普通启动不自动建库或迁移。进程监督需要限频重启和退出原因，Worker重启从应用账本核对fence、截止、费用与unknown，再恢复或诚实终结；停机先关新准入、收拢在途、停止Worker及API，Pg由专门环境步骤管理。WSL/Pg故障先关闭新付费准入；不得认为服务管理器重启等于资金重新获准。恢复演练在隔离库进行且paid_disabled，保留原件/hash，核对最新授权/费用/撤销高水位，再另授权启用。

研究来源：2026-10-28官方[WSL systemd](https://learn.microsoft.com/en-us/windows/wsl/systemd)、[本机网络](https://learn.microsoft.com/en-us/windows/wsl/networking)、[文件系统建议](https://learn.microsoft.com/en-us/windows/wsl/filesystems)、[SQLite WAL](https://www.sqlite.org/wal.html)/[Backup API](https://www.sqlite.org/backup.html)、[Pg16 pg_dump](https://www.postgresql.org/docs/16/app-pgdump.html)。systemd支持有版本条件，WSL生命周期仍依赖宿主；SQLite WAL同时仅一个writer，活动db文件单独复制不足；Pg单库dump不含全部全局角色且压缩不等于加密。当前机器资格未复验，旧P-01主机内存峰值97.4%含其他桌面程序，不能归因为Pg或预测新方案足够省内存。

三案均需首阶段验收：API/Worker故障影响、挂起调用取消、失租迟到写拒绝、WSL/DB不可用、重启不重复发送、快照恢复后的报告引用完整及资金默认关闭。具体冷启/恢复时间、进程数量/并发、磁盘余量和本人100小时内总投入必须在最终任务/环境/时间包冻结；当前无测量证明可达。T2选择只批准目标架构，不自动授权安装Linux依赖、创建环境、改数据库或迁移D盘项目。

### 本轮实际检查与限制

| 操作 | 实际结果与证据边界 |
| --- | --- |
| 进入及本页编辑前 `git status --short` / `git rev-parse HEAD` | 根状态为空，HEAD同上；无Git写操作 |
| `.venv\Scripts\python.exe -B scripts/validate_project.py --ledger data/evaluation/ledger-after-e4e3e822-f5f0-582d-9412-e7cb91daefe4.json` | 编辑前exit0；offline validation passed，不能代表全历史账完整或真实来源正确 |
| `git diff --check` | 编辑前exit0；编辑后需另记，不能复用空diff检查为新正文通过 |
| 本机Python及依赖元数据只读查询 | Python3.12.13；browser-use0.13.10、FastAPI0.142.2、asyncpg0.32.0、Alembic1.20.0、SQLAlchemy2.1.3、MCP2.1.1、pytest9.1.1、ruff0.16.10；未据元数据声称所有模块可导入/运行 |
| `node --version` / 既有 `.tmp/node22/node-v22.23.4-win-x64/node.exe --version` | 分别23.11.1/22.23.4；.nvmrc为22。无安装或环境修改 |
| `wsl --list --verbose` / `Get-CimInstance Win32_ComputerSystem` | WSL返回E_ACCESSDENIED；CIM资源不可访问。该事实不证明不存在WSL/内存规格，不是自动审批拒绝；本轮未启动服务 |
| 相同只读环境查询的沙箱外申请 | 自动权限审批未在截止前完成而拒绝启动，查询未执行；这是审批超时，不是判定操作危险。未因失败推断机器不存在WSL/特定内存，当前架构源码研究不依赖此结果 |
| 官网计价核查 | 发起的只读工具调用被用户切换模式时中断，无可用结果，不声明价格已核验 |
| 后续公开文档读取 | 2026-10-28重新读取[DeepSeek官方人民币计价](https://api-docs.deepseek.com/zh-cn/quick_start/pricing/)与[Search/Fetch指南](https://api-docs.deepseek.com/guides/search/)成功；Search与Fetch分别每千次成功请求5元，按次而非Token计费，模型另计。计费成功定义/空结果/失败见指南；价格是观察快照而非账户运行资格，未发起该API请求。模型、搜索、抓取及必要付费运行服务均须进入最终完整批次估算，不以只算Token遗漏工具费；尚未选定该搜索供应商 |

本页编辑后，项目validator加上述声明ledger、`git diff --check`均exit0；结构检查确认18项连续编号、9项本人决定及原历史正文（统一换行后）保持。结构探针首次误把“编号＋事项”列当成单独编号列而失败，修正探针后通过，未据此修改文件内容。实际Git差异仅本页，未暂存。完整正文/patch/指纹及可重跑检查保存在本机 `.tmp/predev-reopen-20261028/`；独立实际文件审查仍待完成，记录维护通过不代表18项准备全部满足。

独立实际文件初审 `/root/record_and_product_review` 已读取完整HEAD差异、当前/进入正文、快照和检查，并独立复跑validator加声明ledger、diff检查与18项/历史保留探针。初审绑定本页SHA256 `ff17d273269b09b26a769b0e51368dc5c1d78a6dbaccd8e0ce5bac87285dbc4c`、patch `e73b14496e6840bd3c99354eb4ba563a63140973faebb3c107408edf68b776b0`。两项发现已核实并修订：P2计时漏列整理/提示交互/结果整合，改为双方收到题面到满足共同质量的全部主动时间；P3清单16检查状态滞后，已更新。预算疑问经原聊天完整选项核实，不是正文缺陷。审查认为其余记录符合本轮记录AC、候选可供本人作方向选择，尚非最终设计或执行资格。上述旧指纹不能代表此修订后的正文；修订检查和受影响复审结果另绑定当前指纹。

受影响复审已返回 DONE，两项发现关闭：审查者重新读取完整HEAD差异、核对官方计价、独立重跑validator/ledger及diff检查，并确认原正文/快照/patch一致。复审绑定本页 `09d6834a2caa453979d12237301cacdbd1dd2e52043b7c4ef766afa529751c81`、patch `52c7a8d6e1f446fdda913a10215d3c9fed784960cc473c171a64f9106287dc33`；对应完整快照已保存在同名SHA子目录。随后仅补记本复审结果及本人D10–12决定、相应清单状态，增量须重新检查与独立核对；不把旧指纹冒充新增决定的审查。运行/业务/其他权威文件仍未由此授权。

D10–12及结果补记的独立核对任务因审查者用量限制失败，未生成通过结论；其原已完成复审只覆盖前述09d683版，不能冒充新正文已审。随后按本人回复记录D13/14并加入架构候选/数据流，当前增量检查/独立文件审查需继续完成；不以自检替代。该限制不阻止主线程继续已授权研究、讨论与记录，也不是全部准备完成。

### D19配置同步与实际审查批次（2026-10-28）

D19批准的11份现有文件已原位同步：根AGENTS/SPEC/PLANS、当前契约、feature spec/tasks、ADR5/7/8、docs/README和CONFIGURATION。替换旧定位、引擎/拓扑/双入口目标、等待与已完成调用恢复规则；没有新增旧方案归档、删除源码或原始数据。旧AC01–07及FR/NFR/P阶段映射仅保留历史证据归属，08–20改为当前方向与准备缺口，不能用历史映射恢复旧门禁。评测JSON和其余配置本批未改，后续必须按新决定继续更新；本批通过不代表全部18项满足。

存储独立设计审查 `/root/storage_design_review` 为DONE_WITH_CONCERNS、无可确证P0–P3，范围为当时517–559行，绑定正文 `f9334a10cda726ec585ae4c3b2388c79087cbbab6111592decca2442ccdef1b2`、patch `3af7f88fd5c184b8ef4bdcb24f840186896e4cd1eca65288fc504c3f3060133b`。限制是独立重取Saver固定源码失败，未将主线程读取当成自身核源；随后D18本人批准S1及上限。部署独立设计审查 `/root/topology_design_review` 为DONE、无可确证P0–P3，绑定正文 `1e56bddf90b6f58ca14bf23f8620b2bf93e9f10c3bcaaec7257c12fd65320441`、patch `451208865baeb781af3e91b4c02d9a8910262e5995283bfc07ae27c58803e702`；随后D17本人选择T2。两者不代替本批实际文件审查。

本批同步中validator曾报告62项FR/AC/P阶段映射缺失；补回明确标为历史的完整映射后，负责三文件作者复跑指定ledger的validator及diff检查exit0。结构探针一次因FR ID缩写未匹配失败，展开后通过；未修改validator来掩盖缺陷。主线程集成检查、完整11文件正文/patch/指纹与非作者审查另存本机 `.tmp/predev-reopen-20261028/batch-review/`，按其中实际内容身份解释，旧单文件快照不可替代。当前尚待本批独立实际文件审查及必要修复复审，不宣称已通过。

没有执行业务测试、安装、环境/数据库操作、真实模型/Browser、付费或Git写。Git读取对用户级ignore文件报告权限warning及换行warning，不能由命令exit0推定用户级Git配置已验；当前根差异仍限定本批11文件。

集成检查补记：首轮批量检查发现当前契约EOF多余空行，以及历史保留探针误将允许更新的顶部现行导航纳入不可变历史。已去除空行、更新滞后导航，并将探针严格限定为“历史状态（2026-10-24）”起的原正文。随后 `verify_batch.py` exit0：HEAD未变、11文件范围吻合、暂存/未跟踪为空、diff检查及指定ledger的validator均exit0；UTF-8、本地链接目标、18项/19决定编号、旧协议JSON和历史正文保护均通过。完整快照/patch/各文件指纹以 `batch-review/latest.json` 为索引；本补记纳入后重跑固定最终字节。上述是自检，不是独立审查。

下一组工具/MCP研究代理 `/root/tools_contract_research` 因用量限制失败，未交付研究结论；不能记完成。当前11文件实际独立审查仍待获得。后续先完成本批非作者审查/修复复审，再继续工具/MCP、精确Runtime数据流、检索/上下文/记忆、评测/费用与近期任务包；不重复确认D01–D19，不据本批检查启动业务。

业务套件、数据库/迁移、真实模型/浏览器、付费、安装、账户账单/余额、远端CI、备份恢复和Git写均未执行。开发前准备未完成；首业务、真实pilot、M1价值/质量、本人掌握、Go与发布分别待各自证据及授权。

## PREP-BASELINE-20261029：批准配置落地与首工拟授权包

### 授权来源、现场与保护

负责人在完整方案之后明确要求“PLEASE IMPLEMENT THIS PLAN”，随后要求“继续”；本次授权包含37修改、2新增、1删除共40路径配置、六题制备和独立审查、限定validator/历史读取/旧执行入口guard、适用离线测试及实际文件审查。它不含业务实现/DEC-M1-01开工、依赖安装、WSL/服务/数据库/迁移、模型/Tokenizer/Browser真实运行、付费/购买/外部写或Git写。后来提供的新AGENTS替换此前入口，未扩大这些权限。

入口main/HEAD为1ffade6de07ebe3d1e72afb4c44b8677466eca67；原11份未提交配置逐字节匹配旧索引，暂存与非忽略未跟踪为空。原内容身份93e2fa58992dd1ea53b48bc0aa686ae2fd6b9c2aea2c42449947d286944056ab、patch 295761 bytes/SHA256 e3b06b68c684e57b492b9f97046d8135023f0be5ef27dbf38cdceb742e33b097。已在本机 .tmp/predev-reopen-20261028/config-20261029/baseline.json 固定40路径和442个tracked普通文件原字节hash、baseline正文及entry.patch；仅本批审计材料，不新建旧方案归档。原SQLite/r12/授权/费用/真实来源、上游gitlink及范围外工作保留。用户级ignore权限warning不推定全用户配置可读，browser-use内部未证明干净。

40唯一路径如下；M=修改/N=新增/D=删除。实际差异与此核对，不以“配置”名义扩新业务源码。

```text
M AGENTS.md
M SPEC.md
M PLANS.md
M docs/README.md
M docs/contracts/CURRENT_CONTRACTS.md
M docs/features/DECISION-001/spec.md
M docs/features/DECISION-001/tasks.md
M docs/design/adr/0005-windows-worker-wsl-postgres.md
M docs/design/adr/0007-interactive-evidence-decision-sessions.md
M docs/design/adr/0008-m1-engineering-baseline.md
M docs/engineering/CONFIGURATION.md
M .agents/skills/research-eval/SKILL.md
M .agents/skills/research-implementation/SKILL.md
M docs/evaluation/CURRENT_EVAL_PROTOCOL.json
M docs/evaluation/DECISION_M1_PROTOCOL.json
M docs/evaluation/README.md
M docs/evaluation/REVIEW_WORKFLOW.md
M docs/testing/STRATEGY.md
M docs/engineering/WORKFLOW.md
M scripts/validate_project.py
M backend/tests/unit/test_validate_project.py
M .github/workflows/ci.yml
M docs/research/HIGH_STAR_AGENT_MECHANISMS_2026-10-22.md
M docs/research/AGENT_JOB_PRODUCT_FIT_2026-10-23.md
M backend/tests/unit/test_current_evaluation.py
M backend/tests/unit/test_pilot_runner.py
M backend/tests/unit/test_pilot_capture.py
M backend/tests/unit/test_project_ledger.py
M backend/tests/unit/test_pilot_cost_reconciliation.py
M backend/src/adaptive_research/evaluation/pilot_runner.py
M backend/src/adaptive_research/evaluation/pilot_cost_reconciliation.py
M backend/src/adaptive_research/evaluation/pilot_budget.py
M README.md
M backend/README.md
M docs/architecture/README.md
M docs/tasks/README.md
M .github/PULL_REQUEST_TEMPLATE.md
N docs/evaluation/DISCOVERY_M1_CASES.json
N backend/tests/unit/test_legacy_entry_guards.py
D data/evaluation/decision-m1-1/preparation.json
```

旧preparation原字节SHA256为481da876ce5794020be05403eb7a75a75f0ce79194a1e40d2f468ca4535bde60，身份为materials_prepared_not_executed，9/8/12执行flag全false；其删除只处置未执行材料表，不删引用的23份真实来源或6份许可及任何费用/授权。旧材料/协议历史入口用固定Git commit1ffade6de07ebe3d1e72afb4c44b8677466eca67:path与准确原bytes SHA解释，不复制新archive。历史LF和CRLF原hash不同，只由该证据要求的显式变换核对，不能猜全部账本同版本。

### 2026-10-29决定与设计审查承接

本段区别本人直接选择、委托选择及后来的整体配置批准，历史D01–19不倒改。

| 来源/事项 | 已确认边界及当前角色 |
| --- | --- |
| 本人：规模/并发/数据库 | 本人1真实用户＋第二测试身份；全局2执行轮；新空业务DB及独立凭据，后选独立PG16 cluster/55432，旧5433只读取证 |
| 本人：时间/费用起点 | 10/29起完整范围优先7–8周/每周≤20h；新增支出从10/28重评开始，称仓库外无新增；历史未知不填0 |
| 本人：工具/Context/Memory | direct API、DeepSeek单Search/Fetch；MCP研究非交付；关系＋关键词，无默认embedding/reranker；自动来源线索和明确长期技术偏好，仅可见建议 |
| 本人：模型 | 格式修复0、官方Tokenizer正式准入、thinking disabled/输出显式；不授权执行；额外summary0及参数由本次整体配置方案批准 |
| 本人：评测 | 三领域三对、独立DR优先核Gemini免费、每侧主动120min；24h墙钟/14天批次/有限未揭题延期；最终本人稿共质后中位20%，原技术结果保留 |
| 本人：工具对照 | Agent侧产品＋手工核查，不externalAI代修/有意复制Control笔记；双方同预注册日常搜索引擎清单可切换；Control普通AI＋一次DR |
| 本人：首工/恢复 | 连续supervisor许可，首工建最小sup；失连续隔离旧身份，CLI新凭据只草稿/history，无最新性不恢复付费研究 |
| 本人委托、AI宣布后整体批准 | unknown全项目停新出站，保预留/Call；对账本人另批，迟到结算不开闸；最终claim先则在途不保证撤回 |
| 本人：备份 | 开发本机有限演练/pilot前独立介质；借优先预算内购备用、纸钥单独长期离线，实际未建立 |
| 本次整体配置批准 | Runtime/工具/检索/Memory/Token/容量/费用/备份具体工程数字进入契约和唯一协议；不是逐项早期本人原话、不是实际实现 |

已完成限定设计审查：Runtime发送/稳定义务/物理槽三项原发现关闭；RETR-r1.2/TRACE-r1.1/EVAL-r3.1及r3.3方法边界，FIRST-r2，MEM-rfinal.1/BK-r3.2/QUOTA-r3整合均完成其范围设计复核；B5.2原两个P1、BK-r3.1原P1/P2在设计层关闭。复核发现的report输入预留文字错误已更正为两份共65536 input/16384 output，不是131072 input。所有会话候选尚未绑定当时文件正文hash，不能以本段声明替代本次实际文件审查。更早Context专题原始审查未重取；中断/限额失败尝试保留失败，不倒填完成。

### 纵向交付、AC与本人实践

以下是未来业务任务计划，不在本批执行。各行均需原始输入/输出、受限文件、基线/检查/独审/本人验收证据再按任务模板开工。实施、技术验证、业务验收当前均PENDING。

| 任务/依赖 | 输入→独立可见输出/非职责 | AC及主要失败检查 | 本人实践/后续验收工件 |
| --- | --- | --- | --- |
| ENV-M1-01/配置完成 | 安全启动与旧autostart调查→精确Linux路径/新cluster/roles操作包；不先启动再补隔离 | 15；旧Worker/凭据/存活连接/费用unknown保护，运行角色无DDL | 解释旧入口不能回退；准确授权/环境身份/停止回滚证据 |
| DEC-M1-01/ENV资格、另授依赖 | 真实登录→保存未接受原文Draft→重开→测试身份404＋min sup；无InputRevision/Task/call | 15；两身份/CSRF/CAS/容量竞态/失连续旧凭据拒绝 | 重点CR auth→application→store/sup；亲做两账号、预测越权，手改边界测试回归 |
| DEC-M1-02/01、LangGraph依赖资格 | 原消息/接受proposal→原子InputRevision+Task+真实stage图/fake provider结果 | 08/09/12/14；双提交/cancel-success/失租/原deadline/StageOutput-checkpoint切点 | 重点CR根锁、稳定义务/fence/终态；故障夹具，亲改一个CAS回归 |
| DEC-M1-03a/02 | 固定官方表示→发现/身份/claim/context/有源报告，无真实工具费 | 10/11/12/18；同名fork/错版本/子串不支持/未深查17/反证裁剪 | 聚焦CR source→claim→manifest→report；手工原文核源和预测反例 |
| ENV-M1-02/08a/01；早于03b | 独立介质/纸钥/可信纸卡→隔离真实恢复资格，不恢复付费权威 | 15；错key/尾损坏/伪manifest/错DSN/流上限/截断失败目标隔离 | 从纸重录/独立读回，解释capture不等restore/最新性；记录保管已建立与否 |
| DEC-M1-03b/03a、08a、另授资格 | Gateway/grant/reserve/Tokenizer/通用transport监督与费用→另授权养老pilot | 13/14；精确claim、unknown、技术重试、全账/资金、资源终止及迟到结算 | 重点CR逐调用费用归属与请求身份；原需求轨迹/报告/核源及失败 |
| DEC-M1-04/03a，真实种子03b/06或正式自然产出 | 保护context/自动Memory→可见建议、纠正撤销与无复活 | 17/18；expiry/revoke/lineage/满容量更正/跨owner/恢复派生 | 重点CR提取→选择→发送；亲做纠正/停用，亲改漏收或反证测试 |
| DEC-M1-05/02、03a，可与03b准备并行 | Browser唯一出口/bridge资格→有界动态取证；未资格0 | 10/13/14/15；DNS/IPv6/重定向/子资源/旧连接/背压/终止/旁路 | 聚焦CR网络/资源生命周期；看成功与fail-closed证据，不自动放权 |
| DEC-M1-06/真实症状03b | 原trace+预设假设→本人最小修复/离线回归/独审/另授最多2同条件复测 | 20；source/model漂移/条件变化非修复、关键非退化AC | 本人真实亲改代码、预测结果/解释失败，前后版本/固定源/实际复测全留 |
| DEC-M1-07/03b、04、必要05、06及资格 | 版本冻结/六题逐揭示→全尝试、共同质量/配对计时 | 16/19；失败保分母/不补槽/不代填120/knowledge transfer/费用 | 结果验收，解释各对省时率与未通过，主动时段/最终稿hash/独立缺陷审计 |
| DEC-M1-08b/07 | 最新capture隔离恢复→可复现实例/正常失败演示及交付 | 15/19；原件保护/全部证据关联/恢复不升paid | 本人跨模块口述、失败预测、恢复演示；不能代填掌握/Go |

03b的通用transport/generation监督不挪到Browser任务之后。08a前移不是依赖07的08b，避免恢复资格循环。Memory来源种子用合格报告自然生成，若无种子保持pending；正式前策略冻结，不能为了种子暗加setup调用或人工清/注入Control资料。AC08→02/03b，09→02，10/11→03/05，12→02/03，13/14→02/03b/04/05，15→01/ENV/08，16/19→07/08，17/18→03/04，20→06；AC01–07仅历史。

### DEC-M1-01：首业务拟授权与验收包（尚未开工）

用户结果为真实登录、持久原始草稿与第二测试身份隔离。采用可信本机HTTP，不承诺抵御同机恶意服务/OS；Cookie不隔离同host端口。入口product_main提供http://127.0.0.1:8766的build后Vue，端口占用报错不自动换，API404无SPA fallback；不使用旧main/SQLite/Worker回退。API/DTO/schema、Argon/CSRF/session/rate/body/error/sup规则以[契约§7](../../contracts/CURRENT_CONTRACTS.md#7-first-r2首工与验收)为准；sup的在途/unknown和恢复隔离以契约B5.2为准，不假RAM与Pg原子提交。

未来受限文件（此处路径是拟授权边界，本批不得创建业务文件）：
- 新增backend/src/adaptive_research/api/product_main.py、auth.py、drafts.py、schemas/identity_drafts.py；application/identity_drafts.py；infrastructure/product_config.py、product_models.py、product_store.py；admin/accounts.py；runtime/__init__.py、auth_supervisor.py、supervisor_ipc.py。
- 新增backend/product_migrations/alembic.ini、env.py、versions/0001_identity_drafts.py；backend/tests/unit/test_identity_drafts.py、test_auth_supervisor.py；backend/tests/integration/test_identity_drafts.py、test_auth_supervisor.py。
- 修改backend/pyproject.toml、uv.lock仅argon2-cffi25.1.0及必要传递锁（不无关升级）；frontend/src/App.vue、api.ts、App.test.ts、style.css；.github/workflows/ci.yml加入准确受限Pg job；本连续记录维护真实结果。
- 复用FastAPI/Vue/SQLAlchemy/Alembic的已核接口方法，不复用旧自动DDL入口/旧业务owner注入/旧SQLite fallback，不更改browser-use、原数据或历史运行源码行为。

ENV资格先读取准确Linux路径、Python/PG16.15实际身份、代码依赖、55432端口、cluster/data目录、ara_m1/ara_m1_test及角色/权限，再提交精确创建/迁移/凭据/监督操作包。WSL当前Stopped，无旧自动启动安全证据时不boot；必要离线取证或启动前宿主隔离的影响/权限另外明确。目标不是已可运行事实；依赖安装另授权。

实现顺序：先冷进程入口隔离和无DDL身份检查→新schema/受限角色迁移（另授权）→sup默认封闭和CLI新凭据receipt→auth→draft事务/容量/CAS→同源Vue→故障/竞争与本人验收。首工只建认证/草稿所需sup，不造完整paid/Browser系统。

未来准确检查命令（backend工作目录，使用获批已有环境，不自动安装）：
```text
uv run --offline --locked ruff check src tests product_migrations
uv run --offline --locked ruff format --check src tests product_migrations
uv run --offline --locked pytest -q tests/unit/test_identity_drafts.py tests/unit/test_auth_supervisor.py
uv run --offline --locked pytest -q tests/integration/test_identity_drafts.py tests/integration/test_auth_supervisor.py
```
frontend工作目录执行npm run type-check、npm run test、npm run build。PG集成只允许准确授权隔离库，missing/skip不得通过。当前这些业务文件和检查尚未实现/运行。

验收工件：真实两CLI账号及分离cookiejar；restrictedPg实际权限/迁移身份；独立连接barriers的reset/login、disable/write、19Draft双create、active session满额；冷进程import前旧Settings/Provider/tokenizer/network sentinel；raw chunk/CL/JSONescape/UTF8±1/NUL/surrogate安全错误；APIrestart重开草稿；sup/PGrestart旧密码/cookie不能复活，CLI新凭据只草稿；DBdown不虚报注销/撤销；DB无InputRevision/Turn/queue/call/研究event；diff/指纹/技术和安全独审/修复复审。

本人验收步骤：登录本人账号→保存多行含空白/emoji的原文→刷新/关闭页重开→原文一致→第二身份同ID404且列表无泄漏→注销旧cookie失效→两窗口版本冲突可见→观察API正常重启与sup失连续隔离差异。本人读码记录实际入口、预测越权失败、亲改边界测试和回归命令/输出，未做不写“已理解/掌握”。

风险停线：owner泄漏/绕过CSRF/旧密码复活/错误DB或DDL/旧入口意外导入/需要新增权限依赖超范围时停止相关任务。回滚关闭新入口/sup、保新草稿和所有授权/费用证据，不downgrade/删除DB、不启旧二进制写新库；只恢复任务拥有代码到准确基线。验收包可审后再获业务实施/环境/依赖及Git命名操作授权；本次没有这些执行授权。

### 时间、费用与执行分界

本人100–144小时不重叠：A准备/环境/首工20–29；B图/发现取证/Browser24–35；CContext/Memory/Gateway22–34；Dpilot/诊断亲改复测8–12；E正式18–22（主动≤12含核源返工，预注册/记录/统计6–10）；F恢复/跨模块口述演示8–12。模块CR已在A/B/C，不重复F；等待计墙钟另列。备份纸卡登记/演练在A/F，正式题后行政备份不混本人研究主动时间。10/29起7–8周约12/17–24，周≤20h；首周校准，不证明窗口足够，超窗具体范围/投入取舍由本人。

AI agent-hours260–420：研究配置24–40/认证环境36–56/Runtime36–52/取证40–64/Memory32–56/Browser32–56/评测优化恢复40–64/独立审查修复20–32，不是墙钟/收费或实测产能。两次优化槽不保证纠正，失败保留且M1如实未达。

条件费用/Token/工具/容量数值在唯一协议及契约，296.46严格<300不是运行/购买授权。Gemini实际账号地域/免费次数/普通UI模式、搜索引擎清单、模型币种/余额/grant/历史unknown均待揭题/真实调用前资格。本人需补独立介质和纸钥真实保管/恢复，不由AI代填。

### 本批检查、独立实际文件审查与完成判定

进入收尾时状态ACTIVE：三个初始执行代理中途因用量限制失败，不能以代理名或中断前消息记完成；续接只按实际文件核对。当时自检/正文冻结/完整HEAD+暂存+未暂存+新文件审查及受影响复审未齐，18项15/16/17未通过。2026-10-30收尾结果及其生效条件见以下补记，不倒改原失败。

落地检查包括JSON/链接/唯一权威/明确历史SHA/配额成本算术/40范围/受保护原字节；旧runner、budget arm、reconcile对新/缺/坏协议必须在Settings/engine/client/output/账本写前拒绝。历史回归显式读取原协议，不只改断言假称新业务实现。相关7测试及ruff通过后，再按实际失败拓宽离线回归；不自动触发真实DB/网络/安装。审查目录可写本机快照/完整patch/命令输出，Git tracked仅40范围。

最终非作者审查必须读取原始要求/AC、完整实际正文、新文件、base/current差异和命令结果，并绑定raw SHA和patch指纹；实际workspace-write不能称只读沙箱。会话设计审查/测试/自检不代替此关口。核实缺陷后修复/复测/受影响独立复审，保持被审内容固定；追加结果的记录尾也单独复核。只有18项有本轮证据或适用后续前置且无重要准备决定未决，才声明限定开发前准备完成；随后停业务授权前。远端CI/branch protection/本人业务验收/真实质量/Go/发布均未获本批证据。

回滚仅本配置拥有内容恢复到baseline准确bytes，不reset/clean，不碰范围外工作/真实数据。不新增平行历史归档，不批量删除source目录或runtime数据。

### 2026-10-30 收尾实际结果与生效条件

本次负责人再次明确“PLEASE IMPLEMENT THIS PLAN”批准配置收尾：归档已恢复的原审查、修复历史引用、三JSON审查元数据和hash联动、维护唯一18项、必要离线检查及非作者增量复核。仍不含业务实现/依赖安装/WSL或服务数据库操作/真实模型TokenizerBrowser/付费购买/外部写/项目Git写。engineering-workflow交付参考一次路由G5/G6，research-eval提供评测方法，不另建编排或任务记录。

**进入与内容身份**：main/HEAD仍为1ffade6de07ebe3d1e72afb4c44b8677466eca67，暂存与新增提交为空。40路径逐字节匹配r1，内容身份b7ea314a87ac47ae1830e043f9d097e213f2d3210586540bdf43794392abdfbb；原tracked补丁678676 bytes/SHA256=517ae0565936006fe27678c88863f1acacaddd66f36e8b8e4be9ffb40bedb0c0，实际包含38个tracked差异，两新增文件由完整快照补齐，不能声称该patch本身含新增diff。原11文件entry.patch及baseline不覆盖。442个原tracked普通文件中404个在本批范围外，原字节已核对未漂移；browser-use gitlink不变但内部未证明干净，用户级ignore警告不扩大解释。

本机证据根目录为`.tmp/predev-reopen-20261028/config-20261029/`。下列归档保存原始最终消息、source thread/turn/message ID、完成状态、被审内容身份及范围；不是由作者重写一份认可结论。

| 实际审查 | 原始身份/结果 | 本机报告与边界 |
| --- | --- | --- |
| 五评测文件复审 | /root/evaluation_actual_review；thread01a1882e-4b49-7811-a30f-1ff7f44f77cb；turn01a18839-3cfc-7fb0-9c7a-c94e0d30ec55；DONE | evaluation-actual-review-r1.json，SHA256=d686eaf7dd6ce1049a52e33ec51c37d99791b82f177aef8a97b5943d74f7dc9f。恢复的原报告中五文件hash均吻合r1；SCH决定性调查问题、卡片对齐、attempt记录契约、preparation revision四发现已在原复审关闭。不是实际难度、正式质量或省时验收。 |
| 整体实际审查 | /root/baseline_actual_review；thread01a18b14-e0c1-71c3-a226-7e97c9e16a19；turn01a18b14-e182-7033-b4b2-3089bc5322f9；DONE_WITH_CONCERNS | baseline-actual-review-r1.json，SHA256=eda703cd65cb5dd58932595f787266eb3753e6832ea62854fca56f10d706bdf0。覆盖r1文档/契约/任务/18项/首工包，发现下述P3；未来增量不在原结论内。 |
| 安全实际审查 | /root/security_actual_review；thread01a18b15-1deb-7651-ba33-8b2095c962bf；turn01a18b15-1ead-7f31-86d7-aa81bf98b6fe；DONE，无可证实P0–P3安全发现 | security-actual-review-r1.json，SHA256=46e1590b6f4d85ef5d7da361a810646d501977b8e789c797da045fda97d76468。覆盖guard/固定Git历史读取/安全设计及恢复首工边界；非运行资格或实现验收。 |

两名新审查者均为非作者新鲜上下文，实际权限共享workspace-write，实际只读，不能称只读沙箱。此前整体thread01a1883d-303d-7160-b9c3-88caa8a09adf及安全thread01a1883b-9da7-7762-a078-f6b947346b05均因用量限制failed，原error及公开进度保存在interrupted-review-attempts.json，不能记完整DONE；本轮新报告不抹除这次失败。

**发现及修复**：r1整体P3位于本页2026-10-27历史preparation段：旧材料仍链接已替换的现行M1能力文件，无法重建原配套协议。主线程用git show核实decision-m1-1原bytes后，将历史补充协议改为固定commit1ffade6de07ebe3d1e72afb4c44b8677466eca67、path=docs/evaluation/DECISION_M1_PROTOCOL.json、SHA256=961dbf8d1dc94ed4ecad9b03cc8b1cf2aab78d7d8ff71cf773df905eaec1f8c8，并明确当前同路径已替换。该修复和本尾增量的发现关闭以最终独立复核为准，不能复用r1原hash声称已关闭。

**元数据与hash链**：只修改DISCOVERY_M1_CASES、CURRENT_EVAL_PROTOCOL、DECISION_M1_PROTOCOL的审查状态/引用hash及本页。审查字段保留被审r1旧hash及不可变原报告引用/hash；新材料原bytes hash进入协议，协议原bytes hash进入M1，顺序单向。三个JSON状态描述配置准备，不增加runner、业务接口或校验器行为。正式seed仍null，正式attempt/provider calls为0，业务/真实质量/本人价值/M1/Go/release各字段仍false或待证。后续元数据增量另审，不把旧报告改写成审过最终字节。

| 检查/运行 | 实际结果、命令与证据边界 |
| --- | --- |
| 原相关测试及Ruff | guards-checks.json记录7文件150 passed、最终相关32 passed/30 deselected及Ruff check/format通过；前期113/130/139/145的过程记录保留。原输入hash和被测代码身份按原记录解释。 |
| 第一次全tests/unit | unit-full-01.json/.log：exit2，9个collection error；browser-use导入尝试访问默认用户配置目录权限失败，不是测试通过。log SHA256=01083a083d13f32ab6803e332880ddeaad07f0e0684ea1856280c5b8cb465e3c。 |
| 第二次全tests/unit | unit-full-02.json/.log：仅子进程TEMP/配置/缓存限定及遥测/云同步关闭后exit0，621 passed in53.35s（总子进程耗时54.703s）；log SHA256=1093a542900bf878420061f8ddb8cf57bcc79e6ef76069f33aed6770ca6a7264。未再次运行全单测；不是真实Browser验收。 |
| 收尾相关32项 | backend目录：已有.venv Python -B -m pytest -q -p no:cacheprovider tests/unit/test_validate_project.py -k "current_ or attempt_evidence or clarification or pair_equivalence"，独立新basetemp及限定子进程配置；32 passed/30 deselected in3.30s。准确argv/cwd/env及输出hash见finish-metadata-focused.json/.log。 |
| 元数据更新后校验 | finish-metadata-current.json及finish-metadata-historical.json均exit0。历史命令沿用guards-checks中的准确commit/path/raw SHA、显式lf-to-crlf和指定ledger；历史通过不恢复执行或资金权。 |
| 最终实际正文检查 | finish-final-current-02.json、finish-final-historical-02.json、finish-final-diff-02.json及finish-final-verification.json记录最终正文的实际命令/结果；若缺失/非零/指纹不匹配，则下述准备完成结论不生效。JSON重键/引用hash/范围/历史hash/保护字节/链接及18项结构均须核验，不能用本段预先宣告通过。 |

收尾首次diff检查exit2（finish-final-diff.json/.log）：本页EOF新增空行；已去除多余空行，修后结果以finish-final-diff-02.json/.log为准，首次失败保留。

原r1索引中unit-full-02“running”保留为当时捕获状态，实际完成结果由原unit-full-02.json/.log与本次最终索引补充，不回写旧证据。只删除原未执行preparation；固定Git原SHA481da876ce5794020be05403eb7a75a75f0ce79194a1e40d2f468ca4535bde60、29个执行flag全false、23来源/6许可原字节保留已复核。已知旧协议Git原SHA bc75a1a6d14f7633462538c7c83b79ed5f5bcf0d670997b2000c92caa0002948及其显式LF→CRLF表示1c18d53624c21b1e25f5cea5640b4c8b4a5e0cfc001f430c8d603a01d51a8507各自使用，不能推定全部历史账本同版本。

**18项准备裁决及有限闭环**：主清单逐项均有本批配置/设计/检查证据或明确责任、时点和阻塞对象的后续资格；没有已知仍需本人决定而阻塞本批准备的重要选择。此为条件待生效裁决，当前正文状态PREPARED_PENDING_FINAL_ATTESTATION。只有同目录final-delivery.json真实存在、status为limited_preparation_complete，并核对最终40路径实际原bytes/完整tracked差异/两新增diff及正文、全部适用实际检查、非作者最终增量复核报告及其hash均吻合，且没有未关闭准备发现时，本批有效状态才是限定“开发前准备完成”。任一条件不满足则仍未完成，尤其不能只因本页写出裁决而放行。

最终增量报告覆盖P3修复、三JSON状态/hash/审查旧版本绑定、本页顶部/唯一主清单/记录尾和本批授权边界。报告及final-delivery只在本机审计目录保存，最终正文固定后不反向补入自身hash或新报告hash，避免自引用及无尽补记。最终索引保存实际检查、正文和完整补丁指纹；本机ignored证据不是可移植Git交付证明。没有实际取得独立复核时，不以作者自检补足。

**未执行及停止位置**：依赖安装、WSL/服务/数据库/迁移、真实登录草稿业务、supervisor/Pg故障、真实模型/Tokenizer/Browser、远端CI、真实来源逐条核验、正式对照、资金/账单/价格币种/账号DR额度资格、独立介质/纸钥/纸卡真实恢复、本人业务验收与掌握均未由本批执行或证明。现存环境/介质/账号/资金/Tokenizer/数据库/Browser缺口分别保留给ENV/首工/pilot/M1；r12/P-02 No-Go不变。仅交付DEC-M1-01可审查拟授权/验收包，不创建业务文件、不启动该任务；业务实施、环境操作和Git命名操作仍分别另授权，Go/发布分别待证。

## CONFIG-RAWJSON-20261030：原字节稳定与限定校验修复

### 问题、原批准与进入现场

本专项承接G5/G6，不重启产品发现。目标用户、从零技术调研路径和省时价值假设均保留；仅修复工程证据身份及限定validator的真实缺口。当前配置声明不等业务实现、真实运行或本人验收。四项发现有独立技术/安全设计审查，随后负责人先选择“批准两组修复”，再以“PLEASE IMPLEMENT THIS PLAN: 已批准专项：原字节稳定与限定校验修复”授权实施。

本轮原批准直接读取自chat `01a18b3a-ddf8-7380-add9-90e13c760cdc`，turn `01a18b47-0991-79d1-9811-1153156671a3`，user message `01a18b47-0a18-7d30-9345-cbf79183ec5d`，原文归档在审计子目录`authorization.json`。范围仅`.gitattributes`、`scripts/validate_project.py`、`backend/tests/unit/test_validate_project.py`、`docs/testing/STRATEGY.md`、本页五文件。允许必要本机审计工件；不授业务、依赖、环境/DB、真实模型/Tokenizer/Browser、付费、外部或项目Git写。原40路径批准和收尾原批准也已直接读取，未用作者笔记代替。

入口main/HEAD `1ffade6de07ebe3d1e72afb4c44b8677466eca67`、暂存为空、既有40路径与原r2逐字节匹配。原内容身份`bb472e0a25d28714300fc80950676cfb31383e763714a020c416093443695d54`，原final-delivery SHA256 `da4f314c8a23738ff57a708d754994c664af282a5a29c3a176d16a1a5446dc1f`；原40快照/完整补丁/44工件hash/原审查与原会话及失败均经独立核验。旧“限定本机准备完成”在原被审字节有效；旧索引不被新任务覆盖。

本机追加证据根为`.tmp/predev-reopen-20261028/config-20261029/repair-20261030-raw-json/`（下称专项目录），`entry.json`/`entry/`/`entry-head.patch`保存五份进入原字节、443份既有普通文件hash、原HEAD差异及旧索引身份。相对进入现场仅五文件增量，相对HEAD累计41路径（原40＋属性文件）；两份既有untracked正文和原删除事实必须完整保留。范围外、三份现行JSON、原SQLite/r12/授权/费用/来源许可与上游均受保护。

### 发现、判断与专项AC

以下是本专项局部AC，复用原18项主清单及DEC-AC-16/19的配置支撑，不另立产品或准备完成标准。四P2由真实内存/CLI反例及Git过滤器支持；尚无真实执行泄漏或运行越权的证据。

| 事项/AC | 当前事实→原理由→具体缺陷 | 判断/修改及实际调用链 | 检查/观察/后续影响 |
| --- | --- | --- | --- |
| CJ1 原字节身份 | 材料→协议→M1绑定实际原bytes，M1已有-text；新两份属性未设，本机autocrlf=true会转CRLF并触发两hash错 | 保留raw身份；调整两条精确Git属性，禁止以规范化hash掩盖漂移 | 三目标路径×true/input/false真实只读Git过滤器逐字节相等；影响跨检出交付，不等完整clone资格 |
| CJ2 严格原始JSON | 三现行入口原用json.loads，重复键被最后值覆盖，NaN/Infinity/指数溢出被接受 | 替换这三处解码为内部统一函数；main→protocol→materials/supplement，任意层重复键及非有限数值拒绝，有限int/float不改型；历史路径保留 | 三入口分别顶层/嵌套/转义重复、五类非有限数值拒绝且无canary；有效输入通过；校验器无运行授权权力 |
| CJ3 输出要求类型 | 原只检查列表非空，允许object/list/null/bool/number/空白元素 | 调整材料结构检查，每项非空白字符串 | 异常项拒绝、正常材料通过；字符串语义/金标隔离仍需独立材料审查 |
| CJ4 稳定题目映射 | 原仅允许variant A/B，未核与稳定case ID一致 | 调整有效ID的A/B后缀匹配检查 | 六题逐一翻转均拒绝；未来正式分配依赖该校验前须关闭，未声称已有runner分配错误 |
| CJ5 保护与闭环 | 新增量不在旧审查范围；原证据曾因声明被误用的风险 | 保留原封存/历史guard；本次无删除/新依赖/公共API/资金或权限变化 | 五文件完整增量、累计41路径diff/两新正文/范围外hash/独立实际审查及最终索引均匹配后闭环 |

观察日期2026-10-30，Git `2.51.0.windows.1`。Git源码语义依据为[官方gitattributes](https://git-scm.com/docs/gitattributes#_text)；解码依据为[Python3.12 JSON文档](https://docs.python.org/3.12/library/json.html#standard-compliance-and-interoperability)。本项目实际过滤器/反例/检查是本地证据，文档不替代实测。候选比较保留于本轮原聊天：只约定个人autocrlf不覆盖其他检出；规范化hash改变证据语义；schema新依赖/历史重构无必要。采用精确属性＋标准库严格解码和两项结构检查；若未来确需可规范化跨编辑器身份，须以新契约另审，不自动改变当前raw语义。

### 实际检查、失败与独立审查

所有检查仅用已安装依赖。专项目录内每个`*.json`检查记录保存准确argv/cwd/限定子进程env/exit或timeout/日志hash；脚本入口`run_check.py <记录名> <相对cwd> <准确命令及参数>`只追加、不覆盖，stdout/stderr合并保存。子进程配置/缓存/TEMP限定目录，遥测/云同步/tracing关闭，无永久环境设置变更。

| 实际执行 | 结果与边界 |
| --- | --- |
| 计划阶段与进入核验 | 当前validator exit0；32 passed/30 deselected；先前七文件调用未返完整结果后中断，不计通过，见preimplementation-checks.json |
| red-regressions-02 | 新49项修复前39 failed/10 passed；其中M1三项重复键因夹具重序列化漏测，后已修正夹具保留原始非法bytes；不把初次红测当这三项的证明 |
| green-regressions / green-regressions-02 | 修后首次3 failed/46 passed定位上述夹具折叠；修正后49 passed/62 deselected in5.49s；失败原输出保留 |
| seven-file-regression / -02 | 两次沙箱内120秒超时，不通过；诊断栈停Windows asyncio自唤醒socketpair accept，未进首个异步测试正文 |
| seven-file-regression-qualified | 同七文件经该单次命令的工具级沙箱外执行，200 passed in38.45s，exit0；实际argc与日志见同名json/log。仅离线模拟客户端/本地socketpair，不是供应商调用或系统设置更改 |
| Ruff | ruff-check及最终check exit0；首次format-check发现测试排版，限定格式化该文件后format-check-02 exit0；未掩盖首次失败 |
| current-validator / historical-validator | 两者exit0；历史原commit/path/raw SHA及显式lf-to-crlf和原ledger命令完整保存在historical-validator.json，不扩旧账或资金权 |
| 辅助脚本失败 | 首次审计helper误取目录层级导致NotADirectoryError，pytest未启动；check-runner-failure-01.json和原空log保留，纠正后用新记录名运行 |
| 最终正文/范围/diff | 本页固定后再运行final-current-validator、final-diff-check及freeze；实际结果和最终身份由新final-delivery索引绑定，缺失/非零/不匹配不算完成 |

设计审查来自非作者新上下文`/root/config_boundary_design_review`，独立原封存证据核验来自`/root/baseline_evidence_audit`，原聊天消息及限定范围需原文归档，不改写为实现审查。新实际文件审查读取原要求/批准/AC、五文件完整正文和进入字节、累计41路径完整diff及两份untracked正文、真实检查/失败。有效权限仍为共享workspace-write，实际只读审查不等隔离沙箱。不得把尚未返回的实现审查预填为DONE；结果、原始审查身份、验证发现/修复/受影响复审由专项目录外置索引承接。

未重跑全单测、前端构建/远端CI，因为本次修改限静态validator和Git属性；已运行受影响七文件及旧guard兼容。不运行数据库/服务/模型/Tokenizer/Browser/付费。真实核源、业务质量、本人价值或掌握仍没有本次验收证据。

### 本人实践、完成裁决与回滚

阅读入口为本页CJ1–5→STRATEGY专项节→validate_project的`_load_current_json`、`main`和材料检查→同名回归测试。本人应能解释：hash为什么不能自动忽略换行；重复键为何必须在原始解码入口拒绝；结构隔离为什么不证明字符串没有评分答案。预测三类失败：换行/原字节改动触发hash错、重复键或非有限数值返回1且不回显正文、ID/variant矛盾被拒绝。

在backend用已安装Python运行`-B -m pytest -q -p no:cacheprovider tests/unit/test_validate_project.py -k "raw_json_cli or case_variant or output_requirements or raw_hash_paths"`，预期49 passed；沙箱若阻asyncio，先保存失败证据，不用改事件循环掩盖。本人亲改练习仅在授权的临时材料副本中构造重复键并重绑fixture后验证拒绝，再恢复副本回归；不编辑正式题面/金标、不填已掌握。本人实际解释/操作/验收当前PENDING，由本人在后续阅读实践时确认，不阻本专项工程检查完成。

| 完成检查点（对应本轮原要求16项） | 本次证据/状态；负责人/满足时点/阻塞对象 |
| --- | --- |
| 1–3 证据/原理由/AC | 原反例、CJ1–5及官方依据已备；AI/已满足/本专项 |
| 4–6 候选独审/本人批准/准确范围 | 原设计审查、authorization.json及五路径；AI归档/已批准/本专项；不扩大旧40路径 |
| 7–9 落地/引用同步/正常失败边界 | 五文件、唯一主清单09/13/15/16/17、策略/回归；AI/已实现，最终范围检查待索引匹配/本专项 |
| 10–11 检查/完整正文diff指纹 | 实际命令及保留失败；review快照/五文件增量/累计完整diff由freeze生成；AI/最终索引须实存匹配/本专项 |
| 12–13 非作者实际审查/无阻塞发现 | 新原报告及必要修复复审由外置索引确认；AI/不得由本文预填/本专项 |
| 14–15 后续前置/原18项与首工影响 | 当前本机首工不因此新增技术阻塞；跨检出交付/未来材料校验依赖前关闭；ENV/业务/运行各责任时点与原18项不变 |
| 16 最终索引匹配 | 专项目录final-delivery.json必须真实存在并符合下述条件；AI/交付时/本专项 |

本节正文状态为IMPLEMENTED_PENDING_FINAL_ATTESTATION。只有专项目录`final-delivery.json`状态为`configuration_specialty_complete`，且核对五文件最终raw hash、完整正文、进入增量、累计41路径完整diff/两新正文、全部实际检查及非作者独立实现审查/必要复审hash一致、无未关闭阻塞发现，才生效为“本轮配置专项修复与优化完成”。本文不回填自身hash或后来的报告hash；审查报告/最终检查/索引仅外置追加。旧索引不改写，新索引保存与旧被审快照的承接关系；本机ignored工件仍非可移植Git交付。

原18项在本次范围内更新，不机械全部重新打开。当前源码及未来实现/真实pilot/M1仍按原阶段边界；Browser未资格为0，费用/grant/余额/unknown/介质纸钥/恢复/本人验收缺口不因本专项消失。未关闭新发现只阻本专项和相关跨检出/材料校验依赖，不推翻原本机封存事实，不授首工。专项达标后继续已授权调查；新的重要修改范围须具体批准，不自动开业务或环境操作。

回滚先核HEAD/暂存/范围外保护，只将本五文件恢复到专项目录entry原字节；若后有新工作则仅逆转本专项hunk，不覆盖后来修改。三JSON、原数据/费用/授权/审计与旧封存不回滚、不删除；不reset/clean、无Git写，无新增平行完成标准或淘汰配置归档。
