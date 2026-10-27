# 已实现代码审查与人工验收记录

日期：2026-10-27（Asia/Shanghai）。状态：已完成限界代码审查与离线修复；人工业务验收及数据库集成验证待完成。

## Requirement、范围与授权

- Requirement：DECISION-001 已批准的 DEC-T01–T05 已实现切片；DEC-AC-01–07 及调用链实际涉及的旧 AC-001–007、AC-009/010、AC-N01/02/04/06/08/10。
- 验收重点：旧请求兼容与边界；已准入事实的 ID／主体／来源／片段绑定；矩阵未知与冲突；硬条件、偏好和提示注入；取消、失败、超时、预算停线时的事实／事件／状态／费用；API、PostgreSQL、Worker、SSE、历史与 Vue 一致性；仅在当前实现边界检查现有所有权与隔离。
- 实现路径：FastAPI DTO 与研究入口 → SQLite V1 或 PostgreSQL store／Worker 持久快照 → Planner、ContextManager、StateReducer、DecisionService、Reporter → API detail/trace/SSE 与 Vue 表单、矩阵、报告、历史和取消。
- 任务状态依据：DEC-T01 为限定离线切片 DONE；DEC-T02–T05 已提交但整体仍有验收缺口；DEC-T06 模板为 PENDING；PREP-BASELINE-v4.3 为准备材料，不表示业务实现。详见 DEC-T01、T02-01、T03-01、T04-01 记录及 DECISION-001 任务表。
- 本轮授权：现有实现边界内核实并修复缺陷、补回归检查、运行无需新增依赖／数据库／真实浏览器或模型的本机检查、执行独立审查并准备人工验收材料。禁止启动／迁移／清理数据库、安装依赖、真实调用、付费评测、暂存、提交、推送、PR、合并、发布。若需扩大业务范围或变更架构／权限／数据库／依赖，受影响部分停线。

## 基线与保留清单

- 基线 revision：`7c50c131fe06b708fbeaebb4dad5fd4e1e2439b2`，分支 `main`，`origin/main`；ahead 1 / behind 0。
- 开始状态：暂存差异为空；未暂存差异为空；未跟踪文件为空。当前提交相对 `origin/main` 含既有 60 文件准备／契约差异，属于基线，不纳入本任务改动。
- 忽略内容含 `.env`、`data/adaptive_agent.db`、历史 benchmark／P-01 工件、`.tmp`、虚拟环境和前端依赖。均为保留内容，不读取秘密、不清理或覆盖。`browser-use/` 保持上游所有权，不触碰。
- 现行权威文件：根 AGENTS.md、SPEC.md、PLANS.md、CURRENT_CONTRACTS.md、CURRENT_EVAL_PROTOCOL.json、DECISION-001 spec/tasks、STRATEGY.md；DEC-AC-01–07 保持已批准旧行为目标，AC-08–20 为目标而非已通过实现。

## 基线检查

| 检查 | 结果 |
| --- | --- |
| 后端定点离线测试（T01、决策、传输、Planner、Context、Evaluator、Reducer、Reporter） | `python -m pytest -q --basetemp ..\.tmp\review-baseline-be ...`；exit 0，133 passed in 3.07s。运行目录 `backend/`，使用已有 `.venv`。 |
| 前端基线 | `npm test -- --run` 在 Vitest 启动后无输出；中断 exit 1，未完成，不能记为通过。 |
| 适用层 | L1 已运行；L2/L3/L4/L5/L6 尚未运行。本轮禁止数据库、浏览器和模型环境操作；按后续发现评估无基础设施的 API／UI 检查。 |

## 本轮发现与 AC 结论

审查与修复中，逐项记录触发条件、Requirement／AC、源码／测试／证据、影响、修复及复验。未验证、环境未运行、Mock 与真实评测边界分别列明，不从历史结果推断本轮通过。

| AC | 当前结论 | 证据／缺口 |
| --- | --- | --- |
| DEC-AC-01 | 部分验证 | PG DTO／幂等离线路由路径有测试；新增 provider 缺失重放回归通过 mock 路由测试，真实 PostgreSQL 集成回归未运行。默认 SQLite V1 路径接收但丢弃 `decision_context`，影响新上下文能力；其修复需扩展 V1 状态/Agent 边界，暂缓决定。 |
| DEC-AC-02 | 部分验证（离线） | `test_decision.py` 和 T03 记录覆盖机器事实准入、主体／URL／片段／时间及 fact ID；本轮 decision 单测通过。人工官方身份核查及真实报告引用未验证。 |
| DEC-AC-03 | 部分验证（离线） | 固定判断逻辑覆盖 unknown、conflicting 与双向 fact ID；Vue 组件测试覆盖矩阵／事实展示。PostgreSQL 恢复到 UI 的端到端一致性本轮未运行。 |
| DEC-AC-04 | 部分验证（离线） | `test_decision.py` 与 `test_decision_condition_changes.py` 覆盖硬条件不足／均不满足、偏好取舍及无证据不推荐；替身结果不代表真实模型行为。 |
| DEC-AC-05 | 部分验证（离线） | DEC-T04-01 的固定事实硬条件变化对照及提示注入单测通过；真实研究价值和官方来源未验证。 |
| DEC-AC-06 | 部分验证 | DEC-T01 预算重试离线测试和 Vue 取消状态组件测试通过；本轮未运行 API/Worker/DB 取消、失租、超时或费用持久化路径，真实 usage/cost 未知。 |
| DEC-AC-07 | 未验证 | DEC-T06 逐条件独立复核模板尚未执行；正式评测协议与分母不变。 |

旧 AC 交叉结论：AC-001／009 为 P-01 owner-scoped 单一合成 owner 的局部离线验证，真实账户和跨 owner 权限待验；AC-002 为模拟观察及离线 Agent 链路部分验证，真实浏览器研究未验；AC-003／004 为机器事实及报告引用部分验证，人工核源未验；AC-005／006 为 SSE／取消 UI 与历史代码局部测试，本轮没有端到端／故障恢复证据；AC-007／N02 为旧账本实现及离线单测部分验证，未取得当前真实 provider usage/cost；AC-010 为离线建议逻辑部分验证，不证明真实推荐质量。AC-N01/04/06/08/10 的完整运行时／安全／费用门槛未在本轮执行，不能因路径存在而判通过。

### 已核实缺陷及待决定范围

1. **DEC-T02 幂等重放被 provider 配置前置检查阻断（已修复，P2）**：基线 `7c50c131` 的 `api/pg_research.py` 在缺少 `deepseek_api_key` 时先返回 503，随后才调用 `PgStore.create_task` 的 owner-scoped 幂等查询。触发：已有 key K 的任务已提交，provider key 后续撤除，客户端按相同 key／规范化 body 重试；原路径返回 503，不能返回现有任务。影响是提交结果不确定时无法安全恢复；违反 DEC-T02 same-key replay 语义。当前修复在既有 PG store 增加只读、owner-scoped 的同键重放解析；body 相同返回原任务、冲突返回 409；只有首次创建仍要求 provider 配置。schema／状态／调用语义不变。新路由单测及已加入的 PostgreSQL 集成回归覆盖该分支；后者因本轮禁止数据库运行而未执行。修复代码见 `pg_research.py`、`pg_store.py`，离线回归见 `test_pg_transport.py`。
2. **默认 V1 API 接受但丢弃 decision_context（边界待决定）**：`ResearchCreateRequest` 含可选上下文；`frontend/src/api.ts` 会发送；默认 V1 `api/research.py` 仅调用 `ResearchService.create(request.goal)`，而持久任务、service 和 AgentLoop 均无该字段。按 V1 README 入口提交决策上下文会成功创建普通任务，条件不进入报告。此修复需把 V1 任务状态、持久化和 Agent 链路扩展至 DECISION-001 功能；当前权威文件同时将 V1 定为保留旧入口、将 P-01 PG 路径用于 DEC-T02 新上下文，范围是否承诺 V1 同样执行该新功能存在歧义。由于修复会扩大业务实现范围，本轮不改 V1 链路；等待产品／契约决定。现有代码与测试仍作为本轮已发现风险披露。

### 评测与既有证据边界

- DEC-T01 的历史验收绑定其离线切片 revision；本轮 133 项后端单测不替代该历史证据，也不验证真实来源／模型。
- DEC-T02/T03/T04 记录分别包含一次性 PostgreSQL、离线事实矩阵、固定替身条件对照等历史结果；不能记作本轮数据库或真实研究结果。
- DEC-T05 的浏览器端到端、跨账户权限、崩溃恢复部分仍待验证；本地固定替身／组件测试不证明真实业务价值。
- 正式评测、人工官方来源核查、DEC-T06 复核、用户业务验收与产品 Go 均未执行或完成。费用及用量未知保持未知，P-02／产品 No-Go 不变。

## 实际检查、独立审查与人工步骤

| 本轮命令 | 退出码／结果 | 边界 |
| --- | --- | --- |
| `..\.venv\Scripts\python.exe -m pytest -q --basetemp ..\.tmp\review-final-be tests/unit/test_dec_t01.py tests/unit/test_decision.py tests/unit/test_decision_transport.py tests/unit/test_planner.py tests/unit/test_context_manager.py tests/unit/test_evaluator.py tests/unit/test_state_reducer.py tests/unit/test_reporter.py tests/unit/test_pg_transport.py`（`backend/`） | 0；139 passed in 2.89s。 | 离线单测、ASGI fake-store 传输，不触达真实 PostgreSQL。 |
| 修复后：`..\.venv\Scripts\python.exe -m pytest -q --basetemp ..\.tmp\review-condition-be tests/unit/test_decision_condition_changes.py`（`backend/`） | 0；3 passed in 0.20s。 | 固定事实与固定模型替身；验证硬条件变化、全部不满足和报告事实绑定，不证明真实推荐质量。 |
| `npm exec -- vitest run --reporter=verbose --maxWorkers=1 --minWorkers=1 --pool=threads`（`frontend/`） | 0；27 passed。 | Vue/jsdom 组件替身；不等于浏览器 E2E。先前默认并行命令无输出后中断，未记通过。 |
| `npm run type-check`（`frontend/`） | 0。 | 前端静态类型检查。 |
| `..\.venv\Scripts\python.exe -m ruff check ...` 与 `ruff format --check ...`（四个受影响后端文件） | 均 0；All checks passed，4 files already formatted。 | 不运行测试或改写文件。 |
| `python scripts/validate_project.py` | 0；offline validation passed。 | validator 明示 live model performance/source truth remain unverified。 |
| `git diff --check`／`git diff --cached --check` | 均 0；Git 有 LF→CRLF 提示，无空白错误；暂存区为空。 | 未更改行尾或历史文件。 |
| `pytest ... tests/integration/test_pg_api_worker.py` | 未运行。 | 包含数据库迁移／写入；本轮禁止启动或迁移数据库。已在该测试加入 provider 缺失重放集成断言，留待获准的一次性 DB 环境执行。 |

独立审查：三份 fresh-context 子审查只读检查 T01–04 决策逻辑、T02/T05 transport/persistence 和 T05 UI/API 路径；决策逻辑未见可复现缺陷，transport 确认本记录第 1 项，UI 确认第 2 项。其后 security_reviewer fresh-context 审查了相对基线的完整工作区 Diff、新审查记录、相关需求／契约与源码；检查 owner/key 查询约束、冲突行为、provider 停线和记录证据准确性，结论 `DONE_WITH_CONCERNS`，无可执行 P0–P3 发现。审查者没有运行测试；确认 HEAD 未变且审查期间五份文件字节与审查前 SHA-256 一致。有效权限为 workspace-write；其自述只读操作，不宣称系统权限隔离。后续仅在审查记录中回填该审查结果，不改行为代码；本轮行为代码复审证据仍对应审查时的完全相同字节。

审查快照 SHA-256：`pg_research.py` `B2E8F175801BF97C753EA46D3D25203AAE1577E2D06E97A86C1BDF7425045D04`；`pg_store.py` `69CD7AFD3E008C8E2F603226CA914D165CE9B3612BF81847457D2980B5864FEB`；`test_pg_transport.py` `6F18325519B25315E7BD51605C6B15DF2E8EADCD53CDB4CC805CD14B750D1413`；`test_pg_api_worker.py` `AA5B04A531FB712C1D608B8DD31B995CBC520E79407A2896B78AD07DC5F6FC18`；本记录审查前版本 `6F5263ED311D26A0DFC7C1D61450BD1669342869412DBBE4D0DC146541CD0C30`。

人工步骤：在获准的本地 P-01 PostgreSQL API 环境，用测试／合成执行器提交带幂等键任务，撤除 provider 配置后用相同规范化 body 重试，预期返回原 task ID；同键不同 body 预期 409；不存在的键且无 provider 预期 503 且不创建任务。此步骤需要数据库环境，本轮未执行。另在 V1 默认入口提交 `decision_context` 会发现字段未进入任务／报告；需先决定 V1 是继续仅兼容旧请求，还是把新决策功能扩展到 V1，再验收该路径。

结论分栏：实现边界内的幂等重放修复已完成；所运行的离线技术检查通过；完整独立审查完成且无可操作发现；正式评测未执行；人工官方来源核查未完成；用户业务验收待用户执行；产品状态仍 No-Go。费用／真实 usage 本轮没有运行，保持未知。

可复核入口：运行上述后端定点命令复验离线路由／决策；运行 `npm exec -- vitest run --reporter=verbose --maxWorkers=1 --minWorkers=1 --pool=threads` 与 `npm run type-check` 复验前端组件和类型。数据库回归按 DEC-T02 一次性 PostgreSQL 任务记录执行，须另有数据库运行授权；V1 条件丢失问题须先决定产品／契约边界。人工官方核源及真实推荐价值不得用本地替身复验代替。

回滚边界：仅逆转本轮 `pg_research.py`、`pg_store.py`、`test_pg_api_worker.py`、`test_pg_transport.py` 的具体 hunks，并移除本审查记录；不恢复整个工作树，不触碰 HEAD、暂存区、忽略数据、评测工件或 `browser-use/`。当前未暂存，未提交。

用户人工验收与产品 Go／No-Go 均由用户决定。本记录不把实现、技术检查或独立 Review 结论替代业务验收或正式评测。

## 全面审查与离线验收补记（2026-10-27）

本节续记本审查任务，不改写上文绑定原始工作区快照的记录。审查范围为当前工作区四条既有改动、V1 与 DEC-T01–T05 已实现调用链；DEC-T07–T13 仅按现行任务表记为待实施。HEAD 仍为 `7c50c131fe06b708fbeaebb4dad5fd4e1e2439b2`，暂存区为空；所有修复均未提交。

### 修复与行为边界

| 发现 | 处理与当前状态 |
| --- | --- |
| DEC-T02 幂等重放先被 provider 配置检查拦截（P2） | 先做 owner-scoped 同键/规范化 body 查询；匹配时返回原任务，同键异 body 为 409；仅未命中时要求 provider。ASGI 离线回归已覆盖，新增 PostgreSQL 回归未运行。 |
| 决策模型可漏列候选的反向事实并仍给出唯一推荐（P1） | 新 schema 要求逐候选事实分类完整且不重复。用户于 2026-10-27 选择保守 unknown：硬条件的 satisfied/not_satisfied 行若含 irrelevant/unresolved 分类则不采纳，缺口转 unknown 并阻止推荐；conflicting 行仍保留双方引用。新增遗漏和误标 irrelevant 回归。该边界会使原 DEC-T04 合成多条件样例不再产生赢家；历史验收证据仍只适用于其原 revision，当前行为待用户业务亲验。 |
| 无价格簿时模型调用未知费用不阻止后续请求（P2） | `PgCallObserver` 对任何 model call 的 null cost 或 pricing error 均在持久化结果后抛错；`CallRecorder` 锁定后续调用。离线回归验证首个调用后第二个 provider 请求未执行。隔离 PostgreSQL 的“费用账本持久化＋记录器停线”组合仍待单独授权验证。 |
| 默认 V1 路径丢弃 `decision_context`（已发现的产品/契约边界） | 按本次批准计划不扩展 V1 状态/Agent 链路，也不把它记为已修复。需先决定 V1 是否提供新决策上下文功能；相关验收仍未通过。 |

独立审查：核心决策逻辑修复经另一 fresh-context reviewer 复审为 DONE；费用停线修复经 security_reviewer 复审，无 P0–P2 发现，另指出上述 L3 组合证据缺口；PG API/store 和 Worker 初审未发现额外高优先级问题。UI/API 审查确认 V1 上下文丢失问题，按计划保留为待决定项。审查者只读，未宣称其有效权限受到沙箱限制。

最终源码/测试快照 SHA-256（以下代码在独立行为复审后仅做格式化改写，没有语义变化）：

| 文件 | SHA-256 |
| --- | --- |
| `backend/src/adaptive_research/agent/decision.py` | `38E93717F56F631CE15C838FB29059E6D24DFD38A5708B1DC40BF8AB737222B1` |
| `backend/src/adaptive_research/api/pg_research.py` | `B2E8F175801BF97C753EA46D3D25203AAE1577E2D06E97A86C1BDF7425045D04` |
| `backend/src/adaptive_research/infrastructure/pg_store.py` | `69CD7AFD3E008C8E2F603226CA914D165CE9B3612BF81847457D2980B5864FEB` |
| `backend/src/adaptive_research/worker/runner.py` | `B80A9E69D814DB8A2277DC80BBC75198D8FDDC7362B6B461F3EEA6F3393D30FA` |
| `backend/tests/integration/test_pg_api_worker.py` | `AA5B04A531FB712C1D608B8DD31B995CBC520E79407A2896B78AD07DC5F6FC18` |
| `backend/tests/unit/test_decision.py` | `DD3BDF271FFCF04DFE3AD4EAF14128D1A94DB0ACF584CE50B04FF11777356F0E` |
| `backend/tests/unit/test_decision_condition_changes.py` | `FB329963316E9C36C5B138992EFFEF530A5CE7AF351EACCFAE673975293AAEC7` |
| `backend/tests/unit/test_pg_transport.py` | `E6FB256B42060497C253669CDE9A17E3D884863772E991E6593D73552FCD0C15` |

### 最终离线检查

| 检查 | 结果 | 边界 |
| --- | --- | --- |
| 后端全部 unit tests（`backend/`；`BROWSER_USE_CONFIG_DIR` 指向 `.tmp` 临时目录） | **567 passed** | 全离线；不触发真实浏览器或 provider。 |
| SQLite 临时库集成：Agent loop、D2/D3、SQLite schema/persistence、V1 API、SSE | **69 passed** | 仅 pytest 临时目录数据库；不含 PostgreSQL migration/集成。 |
| 决策、报告、幂等传输、费用停线定点回归 | **25 passed** | ASGI/fake store 与固定合成事实；不证明真实来源质量。 |
| 前端 Vitest | **27 passed** | Vue/jsdom 测试，不是浏览器 E2E。 |
| 前端 `npm run type-check`、`npm run build` | 均 exit 0 | 静态类型检查与本地构建。 |
| 后端 Ruff check 与 format check | 最终格式化后通过；113 个 Python 文件格式合规 | 仅静态检查。 |
| `scripts/validate_project.py`、`git diff --check`、`git diff --cached --check` | 均 exit 0 | 项目离线校验通过；暂存检查为空。 |

PostgreSQL L3、PostgreSQL API 幂等回归、P-01 冷启动/失租恢复、跨账户权限、真实浏览器 E2E、人工官方来源核验、DEC-T06 逐条件复核及 current-3 正式 L6 批次均未运行。数据库操作需先提供隔离库的准确地址/名称及创建、迁移、清理范围并获得具体授权；正式评测仍需冻结协议规定的逐次授权。费用和真实 usage 保持未知，DEC-T02–T05整体验收仍按任务表保持 PARTIAL；P-02 与产品仍为 No-Go。

### 人工验收入口

1. 用固定合成报告复核 DEC-T04 保守规则：候选事实完整支持且无 irrelevant/unresolved 时可给 machine-candidate-only 建议；遗漏事实或将未决事实标 irrelevant 时应 unknown 且无赢家；冲突必须保留支持/反证 ID。
2. 在获准的一次性 PostgreSQL 环境提交 idempotency key 任务，移除 provider 配置后同 body 重放应返回原 task ID；同 key 不同 body 应 409；新 key 且 provider 缺失应 503 且不创建任务。
3. 在仅用于测试的 Worker 账本环境，触发已知费用/未知费用结果；未知模型费用应保留为 null，当前物理请求之后不再触发 provider 请求。
4. V1 默认入口提交 `decision_context` 的行为仍需产品/契约决策；在该决定前不将此路径纳入通过项。

最终用户业务验收未由 AI 代填；本补记不改变正式评测分母/阈值、资金状态或 No-Go。

## V1 decision_context 扩展与最终离线验收（2026-10-27）

用户随后明确决定将 `decision_context` 支持扩展到默认 V1：贯通 SQLite 持久化、执行任务、Agent 和报告；同时保留旧 goal-only 请求语义。该决定覆盖上文“边界待决定”项，但不扩展 DEC-T07–T13，也不意味着 DECISION-001 全部 AC 已通过。默认 SQLite 路径是进程内 `TaskManager`，本记录所称执行任务/Worker 指这一任务执行链，不代表 PostgreSQL `WorkerRunner` 已接入 SQLite。

### 实施与验证

- API 将已验证的 `DecisionContext` 交给服务。SQLite `research_task` 新增 nullable JSON 快照；任务与 queued 事件仍在同一事务提交。执行器按 task ID 重读已提交行，再把快照交给 AgentLoop，避免只依赖请求闭包中的内存值。仅 goal 的旧任务仍不向注入式 Agent 传入新的可选参数。
- Reporter 已能消费 `ResearchState.decision_context` 并生成 DECISION-001 的 decision 对象；SQLite 重启归档从任务行恢复该快照，报告保留原用例、硬条件、偏好与候选列表。任务 API 可返回可选上下文，前端 API 类型已同步。
- 为现有 SQLite 增加受限升级：启动时用 `BEGIN IMMEDIATE` 序列化 schema 检查；只有现存模型表没有其他缺列、且唯一缺项是 `research_task.decision_context` 时，才执行 nullable JSON `ALTER TABLE`。旧任务值保持 NULL；遇到其他不兼容列先拒绝，不先改表。没有访问项目的正式 SQLite 数据库；迁移只在临时测试库验证。
- 回归覆盖规范化输入进入执行器与报告、无效上下文 422 且不建任务、旧 goal-only 路径、重启报告、已有 SQLite 行保持、其他表不兼容时不改表，以及并发 schema 初始化。

### 最终离线检查

| 检查 | 结果 | 边界 |
| --- | --- | --- |
| 后端全部 unit + 全部非 PostgreSQL integration（明确排除 `test_pg_store.py` 与 `test_pg_api_worker.py`） | **641 passed in 38.25s** | 临时测试库与合成调用；不触达 PostgreSQL、真实模型或浏览器。使用 `.venv`、`BROWSER_USE_CONFIG_DIR` 临时目录及 pytest 临时目录。 |
| V1 SQLite / DB schema / persistence / API / SSE / AgentLoop 定向集合 | **72 passed in 11.92s** | 是 641 项中的子集，不重复累加。 |
| DB schema 与 persistence 定向复验 | **17 passed in 1.96s** | 覆盖迁移、失败前无改表、并发初始化和重启报告；是上述 72 项子集。 |
| V1 上下文 API 链及两项旧 API 路径 | **3 passed in 3.07s** | API 使用固定 Agent / Reporter；不证明真实研究质量。 |
| 前端 Vitest / type-check / production build | **27 passed**；type-check exit 0；build exit 0 | 组件测试和本地构建，不是浏览器 E2E。 |
| 后端 Ruff check / format check | 均 exit 0；113 个文件格式合规 | 最后一次完整静态检查通过。 |
| `scripts/validate_project.py` | exit 0，offline validation passed | 工具说明 live model performance 与 source truth 未验证。 |
| `git diff --check` / `git diff --cached --check` | 均 exit 0 | 暂存区保持为空；Git 仅报告既有 Windows LF→CRLF 提示。 |

PostgreSQL L3 及 PostgreSQL API 幂等、费用账本集成测试仍未执行。用户回复选择授权隔离库操作，但未提供 host、port、database 和 role；未连接或迁移任何库，也未清理任何数据库。待收到准确隔离库坐标后，需再次核验目标为空且范围隔离，再按已授权范围运行迁移/测试/清理。真实浏览器、真实模型、官方来源核验和正式 current-3 L6 评测仍未执行；冻结协议、分母、阈值、费用未知和产品 No-Go 不变。DEC-T01–T05 仍按各自任务记录区分局部离线修复、技术验证与尚缺的 PostgreSQL／真实质量证据，不能整体改记为通过。

本轮扩展后的关键人工验收步骤：

1. 用默认 V1 API 提交旧 `{goal}` 请求，确认原有执行与响应语义；再提交带 `decision_context` 请求，检查 POST、详情和列表的任务快照一致，终态报告包含相同用途、硬条件、偏好与候选原顺序。
2. 提交不符合 `DecisionContext` 契约的请求，确认 422 且不创建任务；在测试副本中重启时，检查已入队/运行任务归档报告保留提交时上下文。
3. 使用只含旧列的 SQLite 副本运行初始化，确认旧任务保留且上下文为 NULL；再对其他列缺失的 schema 初始化，确认启动失败且没有新增上下文列。
4. 用户决定的保守判定边界仍需人工复核：硬条件候选有任何被漏掉、标为 irrelevant 或 unresolved 的已准入事实时，该判断应为 unknown 且不推荐；完整且一致的支持/反证证据才允许相应的机器建议。
5. PostgreSQL L3 步骤需在取得准确坐标并核实为隔离库后进行；在此之前仍为未验证。

## 最终独立审查状态

实现者自查不代替独立审查。V1 schema/data-flow 设计审查、完整最终差异审查、PostgreSQL 账户/账本安全复核及硬条件修复复核均已完成，详见下方结果。技术审查通过不等于正式 L6、人工核源、用户关键业务验收或产品 Go；这些状态分别保持如上。

### 独立审查发现的修复与复核

完整差异 reviewer 在复审保守硬条件规则时发现一个 P2：当同一硬条件已有支持与反证，同时另一个候选事实被分类为 `irrelevant` 或 `unresolved`，旧门控只拒绝 `satisfied`／`not_satisfied`，仍会公开 `conflicting`。这与用户指定的“任何未纳入支持／反证的事实都令硬条件为 unknown”不符。实现者按审查发现补充测试；先运行时回归失败，实际得到 `conflicting`（期望 `unknown`）。修复后硬条件门控覆盖所有 verdict，提示词同步改为任何 irrelevant/unresolved 均须 unknown。新回归分别覆盖两种分类，现有完整冲突和遗漏反证路径保持通过。fresh-context reviewer 已复核修复后的实现与测试，结论 `DONE`，无剩余发现；受影响决策逻辑因此已再次独立复审。

本轮设计审查结论为 `DONE_WITH_CONCERNS`，未发现阻止实现的迁移或 V1 数据流设计缺陷；提醒现行目标契约还包含规范化 goal/context 的 `Idempotency-Key` 语义。本次 V1 扩展授权没有包含 SQLite 幂等新增，故不能因此宣称 DECISION-001 输入契约／DEC-AC-01 全面通过；这是契约覆盖缺口，不是本次纵切中的实现回归。PG API/store/Worker 的 fresh-context security review 为 `DONE`，未发现 P0–P3 新安全缺陷，并明确 P-01 固定合成 owner 仍不等于多账户隔离。完整差异 reviewer 的初次 `DONE_WITH_CONCERNS` 发现已由上述受影响行为复审闭环。

追加新回归后重新运行后端全部 unit 与所有非 PostgreSQL integration（排除 `test_pg_store.py`、`test_pg_api_worker.py`）：**643 passed in 43.83s**。此结果取代本节先前同一命令的 641 计数；差异是新增的 irrelevant/unresolved 参数化回归。Ruff 全量 check 及 format check 随后均 exit 0，项目 validator 及 diff whitespace 检查均 exit 0。SQLite/API/SSE/AgentLoop 72 项及前端 27 项为同轮已运行的子集和独立验证，不叠加成总数。

最终技术结论：本次授权且可离线验证的实现与修复已通过测试和独立行为复核；PostgreSQL L3 因缺少精确隔离库坐标继续未验证。人工关键业务验收、官方来源真实性和正式评测均仍需分别完成。`CURRENT_CONTRACTS.md` 中 V1 SQLite 幂等语义、PostgreSQL 行为、DEC-T06、真实研究及 DECISION-001 全体 AC 不属于已通过项；产品仍为 No-Go。
