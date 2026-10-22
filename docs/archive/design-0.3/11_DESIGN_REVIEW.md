# Gate 1 第二遍设计复审

状态：**APPROVED（设计审查记录）** · 复审日期：2026-10-17 至 2026-10-18 · 审查者：主代理多轮源码/契约复核，另有两个限定范围的子代理只读核对；**未验证隔离只读权限，也未声称第三方 Reviewer 已批准**

审查范围是本目录的 PRD、架构、六类 DFD、数据/API、测试、验收、工作流、路线图、追踪矩阵、官方项目研究和 ADR，基线为 `dbacdc02`。项目规则指出可写父权限会覆盖子角色的只读设置；本轮未验证有效只读隔离，因此不把代理角色名当成独立安全边界。审查方式是逐项回看源码证据、图和跨文档约束，记录并修正设计矛盾。下列 §1–3 的 DR-01..13 是 0.2 版历史复审，§4 是 0.3 冻结前增量复核；旧版工时和九次指标由 §4 与现行 05/06/08 替代。审查结果不等于 Gate 1 最终批准。

## 1. 发现、严重级别与修正

| ID / 严重级别 | 发现及证据 | 修改建议与本轮处理 | 复查 |
|---|---|---|---|
| DR-01 / **P0** 架构边界 | 初稿组件图把新增用量事件画为 `AgentLoop→Persistence` 直连，违反 [ResearchService 事件回调](../../backend/services/research.py#L79)的现有写入所有权 | [02 组件图](02_SYSTEM_ARCHITECTURE.md#4-图-3component-architecture)已改为 Loop→ResearchService 的可选事件元数据，由 Service 经 Persistence 提交 | **已修正**；无新的 domain→backend 导入 |
| DR-02 / **P0** 事件契约 | 初稿若称“在 JSON 中直接添加”会与 [Reducer 严格键校验](../../adaptive_agent/state_reducer.py#L267)及 `_StepEvaluatedPayload.extra=forbid` 矛盾 | [04](04_DATA_AND_API_CONTRACTS.md#4-事件-payload事务与重启)明确只有获批后扩展三个既有事件的可选 `usage_by_stage` 并测试旧 trace；不双计总用量 | **已修正**；当前能力仍标 PROPOSED |
| DR-03 / **P0** 证据链 | PRD 的“每项事实可见证据片段”与当前 `ResearchFact.evidence` 可空字段有落差 | [04](04_DATA_AND_API_CONTRACTS.md#1-三层模型边界)规定新准入实质事实必须保存可对照片段；历史无片段显示未知，不倒填；[03](03_DATA_FLOW_AND_STATE.md#dfd-05事实与报告数据链)、[05](05_TEST_AND_EVALUATION.md#2-可追踪测试矩阵)和 G2-04 已同步 | **已修正**；需回放真实误拒以验证可行性 |
| DR-04 / **P1** 门槛解释 | 每题 ≥2/3 成功和九次整体覆盖 ≥90% 并非等价，失败样本覆盖不足时后者更严格 | [05](05_TEST_AND_EVALUATION.md#3-新版评测协议建议与历史-r12-分离)写明两项须同时满足、失败仍入分母；[06](06_ACCEPTANCE_AND_RELEASE.md#3-指标与目标)保留逐项与总体指标 | **已说明**；属于待用户批准的质量取舍 |
| DR-05 / **P1** 部署安全 | 前置 DNS 和导航后 URL 检查不能证明重定向的内部请求在发出前被阻断，[Adapter](../../adaptive_agent/adapters/browser_use_adapter.py#L309)无法单靠源码证明网络隔离 | [02](02_SYSTEM_ARCHITECTURE.md#3-图-2container--deployment-architecture)、[05](05_TEST_AND_EVALUATION.md)和[06](06_ACCEPTANCE_AND_RELEASE.md)均限制可信本机，受控安全烟测为后续任务 | **风险保留**；公网发布 No-Go |
| DR-06 / **P1** 历史数据 | `create_all` 不迁移旧 SQLite，新增列会给本机用户数据带来兼容风险 | [04](04_DATA_AND_API_CONTRACTS.md#4-事件-payload事务与重启)优先既有 JSON 可选字段；若须 schema 变化先备份隔离副本并另行审批 | **已约束**；无数据库改动 |
| DR-07 / **P0** 混合事实拒绝 | FR-003 曾要求拒绝项可见，而[Evaluator](../../adaptive_agent/evaluator.py#L127)会过滤候选，混合结果没有逐项持久原因；04 仅映射准入事实卡 | [01](01_PRODUCT_REQUIREMENTS.md)收敛为**步骤级**拒绝数量/原因码；[04](04_DATA_AND_API_CONTRACTS.md)定义可选安全摘要，03/05/08/09 同步，不保存被拒绝正文 | **设计契约已修正**；实现及真实误拒仍待 Gate 2 |
| DR-08 / **P0** 修复用量与缺失值 | DeepSeek 把首次/修复 usage 合并，[DeepSeekClient](../../adaptive_agent/llm/deepseek.py#L56)无法由现有返回值拆分；先前阶段 schema 只许整数，却要求缺失为 `null` | [04](04_DATA_AND_API_CONTRACTS.md)定义 attempt 计量、互斥阶段、known Token 下界与 unknown 调用，完整总量未知；[05/08](05_TEST_AND_EVALUATION.md)要求单计、旧 trace 与缺失测试 | **设计契约已修正**；Provider seam 可实现性待 Gate 2 失败先行测试 |
| DR-09 / **P0** 安全验收措辞 | NFR 要限制私有目标，但原 TEST-N03 把阻断和风险声明并列为通过；导航后 URL 检查不能证明重定向事前阻断 | [01/05/06](01_PRODUCT_REQUIREMENTS.md)分开直接私有目标事前拒绝与受控重定向观测；只按已知残余风险批准可信本机，不宣称 SSRF 完整防护 | **设计门槛已修正**；网络行为仍未实测，公网 No-Go |
| DR-10 / **P1** 测试可执行性 | NFR-001..006 原 A/B 合行，无法分别留下正常/异常用例证据 | [05](05_TEST_AND_EVALUATION.md)拆为十二个独立 ID、输入、预期和证据 | **已修正** |
| DR-11 / **P1** 排期可信度 | r12 真实完成率 0，而 G2-09 给九次运行/核源 5 h | [08](08_IMPLEMENTATION_ROADMAP.md)明确 5 h 是链路稳定的条件估算；超时仍 No-Go 并重排，不压缩样本 | **已约束**；实际工时不可预先保证 |
| DR-12 / **P0** 模型输出与诊断信任边界 | 若把拒绝摘要直接加进 LLM 使用的 `EvaluationResult` schema，模型可自行生成“验证通过/拒绝数量”，使 UI 诊断失真 | [04](04_DATA_AND_API_CONTRACTS.md)改为 Evaluator 解析后确定性计算摘要，内部 `EvaluationOutcome` 传给 AgentLoop，摘要仅在事件顶层保存；[05](05_TEST_AND_EVALUATION.md)增加伪造诊断输入用例 | **设计契约已修正**；实现待 Gate 2 |
| DR-13 / **P0** 页面数据留存边界 | FR-007 原“不得记录原始敏感页面内容”与[当前事件](../../adaptive_agent/agent_loop.py#L312)持久 `tool_result.content`、[Persistence](../../backend/services/persistence.py#L40)仅替换已配置秘密矛盾 | [01/04/05/06](01_PRODUCT_REQUIREMENTS.md)明确仅**新增诊断元数据**不复制正文，现有 trace 仍有有界页面内容；演示限公开资料与可信本机，测试已配置密钥和元数据脱敏 | **设计陈述已修正**；任意敏感文本自动清除不在当前范围 |

## 2. 七个视角的复核

| 视角 | 复核问题与结果 |
|---|---|
| Architecture | 方案 A 是唯一推荐；未把 TaskManager 描述成独立 Worker；DB 写入在 Persistence、浏览器资源在 Adapter/Loop；Python import 图只表示实际 import。**通过设计层复核** |
| Agent Runtime | Observe→Context→Plan→Validate→Tool→Evaluate→Reduce→Persist→Stop 闭合；技术重试与语义重规划有界；Planner 重复上下文与证据误拒仍需调用级实测。**P0 实现风险保留** |
| Data | `ToolResult→候选证据→ResearchFact→ResearchReport` 的来源、ID、生命周期与存储已列；新增步骤级拒绝摘要不保存候选正文，已知用量和未知调用分开；旧 trace 缺字段按未知呈现。**设计契约已修正，实施待验证** |
| QA | FR/NFR 对应 AC、TEST、模块与 API/事件；P0 正常/异常用例拆分，真实九次与 Mock 层级分开。**设计层通过，尚无新测试运行结果** |
| Security | 已配置密钥需经脱敏，不能承诺任意页面敏感信息不进 trace；网页文本为非可信数据；直接私有目标事前拒绝与重定向事后检测有不同验收；本机公开资料边界明确。**公网能力不批准，受控网络行为未验证** |
| Scope | 不引入 RAG、MCP、LangGraph、Redis、独立 Worker、Alembic 或视觉模型；可选模板/导出不进入 P0。**通过** |
| Documentation | Mermaid 图数量为架构 4、数据流 6+状态机 1、ER 1；六路 API、六种状态、九次验收、53h 路线图与 ADR 一致。静态链接/围栏检查见下；**渲染器运行未验证** |

## 3. 检查证据与剩余限制

- 已执行文档静态检查：逐文件围栏配对与本地相对链接存在性；Mermaid 代码块数量 12（架构 4、DFD 6、状态机 1、ER 1）。本环境没有现成 Mermaid CLI，**没有**声称已做真实渲染；语法已按 GitHub Mermaid 支持的 `flowchart`、`sequenceDiagram`、`stateDiagram-v2`、`erDiagram` 人工复核。
- 已对照 [V1 Spec](../specs/V1_SPEC.md)、[Contracts](../contracts/V1_CONTRACTS.md)、[当前源码审计](10_CURRENT_STATE_AUDIT.md)及 [r12 原件](../../data/benchmark/20261016T152251931497Z-3de75ed5/summary.json)。旧文档时效差异不以修改历史文件消除。
- 本轮未运行 Python/前端测试、真实浏览器或付费模型；设计结论不能替代未来 Gate 2 的代码、CI 与九次真实任务证据。远端 CI、GitHub 分支保护、子模块清洁状态与实际公网网络隔离仍 **UNVERIFIED**。

**0.2 版第四轮复查结论（历史记录）**：DR-07..09、DR-12/13 的 P0 文档契约矛盾已同步修正；其“九次、53 h”表述已由下面的 0.3 版复核替代。

## 4. Gate 1 Final Design Verification（0.3 冻结候选）

| ID / 严重级别 | 源码或契约证据与冲突 | 本轮修正 | 复查结果 |
|---|---|---|---|
| FV-01 / P0 权威 | [`AGENTS.md`](../../AGENTS.md) 将 V1 Spec 定为现行来源，0.2 索引只写“获批后同步”，未给过渡期间优先级 | [00](00_DESIGN_INDEX.md)明确 V1 当前/设计目标两条权威线；[08](08_IMPLEMENTATION_ROADMAP.md)增加 G2-00 文档迁移，先审查版本指针再做行为 PR | **设计冲突已消除**；实际迁移须另获文件范围批准 |
| FV-02 / P0 用量 | [DeepSeek](../../adaptive_agent/llm/deepseek.py#L56)合并首次/修复 usage；无 attempt 能力的替换 Provider 无法满足 `calls=HTTP attempts` | [04](04_DATA_AND_API_CONTRACTS.md#4-事件-payload事务与重启)规定仅支持逐请求记录者写 `usage_by_stage`；旧事件或不支持者省略，不推算 calls；事件对账、未知值与突发死亡限制同步到 03/05/06/08 | **契约自洽**；实现与计量损失仍待回归 |
| FV-03 / P1 数据流 | [SSE 路由](../../backend/api/research.py#L108)先验游标再订阅；[AgentLoop](../../adaptive_agent/agent_loop.py#L347) 的 Provider 异常不进 Evaluator；Reducer 不直接调用 Service/Reporter | [03](03_DATA_FLOW_AND_STATE.md)三图改为实际顺序与所有权，[05](05_TEST_AND_EVALUATION.md)补游标竞态及 Provider/工具分流测试 | **图与当前调用一致** |
| FV-04 / P1 调度 | [`ResearchService.create`](../../backend/services/research.py#L65)在 queued 提交后调用 submit，异常缺本地补偿 | [03](03_DATA_FLOW_AND_STATE.md)标当前缺口为 PROPOSED；[05/08](05_TEST_AND_EVALUATION.md)增加失败注入与 G2-05 所有权 | **目标行为可测，当前未实现** |
| FV-05 / P0 评分 | [旧协议](../benchmark/BENCHMARK_PROTOCOL.md)与[`score_answer`](../../benchmark/metrics.py#L173)定义的字段未在新版验收锁定分母；仅称“≥90%”不可复算 | [05/06](05_TEST_AND_EVALUATION.md)锁定 B01/B02/B03 为 10/10/5，九次 75、至少 68 字段；逐结论人工核源表；另设三项独立留出任务并分表报告 | **门槛可复算**；十二次真实任务尚未运行 |
| FV-06 / P1 安全 | [Adapter](../../adaptive_agent/adapters/browser_use_adapter.py#L197)显式导航前校验，但 DNS 到 Chromium 请求有 TOCTOU；浏览器内部请求事前拦截未证实 | [01/05/06](01_PRODUCT_REQUIREMENTS.md)写明 DNS 变化、重定向/点击/弹窗/子资源、三个恶意页 canary、请求日志与可信本机残余风险 | **安全声明与证据层级一致**；不批准公网 |

本轮只修改 `docs/design/`，未改业务、历史 benchmark、V1 文件或工程配置。对 14 个 Markdown 文件执行了围栏配对、相对链接存在性、行尾空白检查；12 个 Mermaid 块（架构 4、DFD 6、状态机 1、ER 1）的声明类型和围栏均通过静态检查；13 个 P0 FR/NFR 均能找到 PRD、追踪矩阵、A/B 测试及 AC。Mermaid CLI/GitHub 渲染器未运行，**不声称实际渲染通过**。`git diff --check` 因 `browser-use` 子模块元数据权限不足无法完成，已由文档行尾检查替代，子模块清洁状态仍 UNVERIFIED。`VERIFIED` 仅说明源码与历史记录可支持当前事实，新增字段、G2-00、留出集与安全改进是已批准但未实施的目标。残余风险是 Provider attempt 计量可行性、突发死亡诊断缺口、浏览器内部请求与 DNS TOCTOU、十二次真实样本的成本/站点漂移；当前真实业务仍是 D7 **No-Go**。用户已明确批准 0.3 **设计冻结**，未授权 Gate 2；本次优先级与完整成功定义澄清不放宽门槛，后续实质变更需新版本。
