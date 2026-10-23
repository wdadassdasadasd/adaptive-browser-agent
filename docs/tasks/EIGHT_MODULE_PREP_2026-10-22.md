# 八模块深化：准备整改与后续任务门槛

**任务 ID：PREP-EIGHT-MODULE。日期：2026-10-22；最新进展：2026-10-23。状态：准备完成，同版三题 pilot 已采集诊断基线；P-02 研究质量及产品 No-Go。** 本文跟踪已授权的八模块实施方案，不把未来接口或上游机制写成当前实现。权威依次为[规格](../../SPEC.md)、[计划](../../PLANS.md)、[目标契约](../contracts/CURRENT_CONTRACTS.md)、[current-3 评测协议](../evaluation/CURRENT_EVAL_PROTOCOL.json)；当前行为以 V1 源码/测试和 [P-01 验收](P01_ACCEPTANCE_2026-10-21.md)为准。

## 当前证据与停线

- 已有本机假任务 P-01 架构关口第二轮 48/48；r12 真实研究仍无完整成功。2026-10-22 优化前 pilot 的[持久预检](../../data/evaluation/p02-pilot-preflight-stop-20261022.json)因 DeepSeek CNY 余额不足 1 元而停在建额前：任务、预算、调用、报告均为 0。它不是 B01 的一次尝试，也不是优化前基线。
- 本轮仅进行固定版本[上游机制研究](../research/HIGH_STAR_AGENT_MECHANISMS_2026-10-22.md)、需求/契约追踪、历史窗口配置贯通、Node 版本约定和运行指纹更新。默认 `RECENT_TRACE_COUNT=5` 不变；非默认值现在传入 `ContextManager`。这些不宣称改善真实研究质量。
- 真实 pilot 在任何质量行为改动前完成 B01–B03 各一次，须重新检查余额、价表、来源和数据库，冻结新代码/环境指纹，并遵守单次付费授权与 49 元上限。余额不足、费用未知或条件漂移则继续 No-Go；保存既有停线工件，不改写成失败尝试。

## 八模块需求与交付顺序

| 模块 | Task ID 与依赖 | 验收重点 | 本轮状态 |
| --- | --- | --- | --- |
| Agent Loop / Runtime | P02-LOOP-TOOLS；P02-PILOT 后 | 需求完成、无进展、取消、超时、迟到结果和唯一终态；完整真实轨迹 | 目标未实现；现有 AgentLoop 保留 |
| Context Engineering | P02-CONTEXT、P02-CTX-ABLATION；P02-PILOT 后 | Planner/Evaluator/Reporter 投影，fact ID/来源、矛盾、失败线索保留；冻结轨迹比较质量、Token、费用、时长 | 历史窗口配置修复；选择/消融未实现 |
| Memory Management | P03-MEMORY；P03-ACCOUNTS 后 | owner 隔离、核源工件与报告哈希绑定、7 天过期/撤销、最多 5 条、正式评测关闭复用 | FR-011 / AC-011 契约已定义，代码未实现 |
| Tool Calling / MCP | P02-LOOP-TOOLS 后 P03-MCP | 统一 schema；实际本地只读 stdio 子进程的协商、非法参数、错误、超时、取消与清理 | FR-012 / AC-012 契约已定义，适配未实现 |
| Evaluation / Reflection | P02-PILOT → P03-DIAGNOSE → P04-FORMAL | 原始尝试保留失败分母；逐结论官方核源；一条真实失败→修复→复验 | pilot 尚无尝试；No-Go |
| LLM Gateway | P02-GATEWAY；P02-PILOT 后 | 假供应商替换、阶段额度、429/结果不明、缺失 usage、修复调用与费用对账 | NFR-010 / AC-N10 契约已定义，代码未实现 |
| Observability / Persistence | P01-CALL → P02-GATEWAY → P03-RECOVERY-BACKUP | call→task→batch→project 账本、SSE 补读、幂等写入、脱敏与恢复 | P-01 假任务证据已有；真实链未验证 |
| Backend / Product Delivery | P03-ACCOUNTS、P03-RECOVERY-BACKUP → P04-HANDOFF | 五账户逐对象隔离、管理员创建/列表/停用/重置、冷启动、容量模拟、加密备份恢复 | 目标未实现 |

## 实验与成本契约

上下文消融固定同一来源和任务轨迹，比较最近窗口、相关性选择、相关性加关键证据保护；记录证据保留、需求覆盖、provider 实际 Token、总费用、耗时和失败。跨任务记忆单独测过期、撤销与越权；正式尝试使用隔离记忆空间且关闭复用。任务上限 40,000 Token、报告预留 4,096；规划/评估/报告输出上限 1,024/2,048/4,096。输入估算、实际输入/输出、缓存、未知 usage 与 CNY 不互相冒充；修复和重试计入调用账本。

正式放行仍采用原九题 15 次：B 每题至少 2/3，G 合计至少 2/3，O 必须 3/3，并逐结论人工官方核源、冲突与 full 二次复核。准备、模块、产品分别判定；未达到真实证据或费用界限时均不得称产品 Go。新增真实运行上限为 pilot 49 + 诊断 30 + 正式 200 + 机动 20 = 299 元；每段单独授权。

## 准备验收清单

| ID | 可审查产物 | 判定条件 |
| --- | --- | --- |
| PREP-CONFIG-TRACE | `agent_factory.py` 与配置单测 | 非默认历史窗口传入运行实例；默认行为不变，聚焦测试通过 |
| PREP-LINKS | 现行审查文档链接、`validate_project.py` 与回归用例 | 当前文档的本地链接必须直达；归档原件的旧路径按映射兼容 |
| PREP-ENV | `.nvmrc`、CI、README、环境与依赖清单 | Node 版本入口一致；Node 22 本机、PostgreSQL/WSL、子模块状态各自标注实测范围 |
| PREP-TRACEABILITY | `SPEC.md`、`PLANS.md`、契约、校验器和回归 | FR-011/012、NFR-010 及 AC 在指定阶段闭合，链接与冻结协议检查通过 |
| PREP-UPSTREAM-8 | 固定提交源码研究 | 来源、版本、本项目取舍及验证边界可逐项追溯 |
| PREP-FREEZE | `.nvmrc`、本记录、全套离线检查及新 pilot dry-run | CI 与文档指向 Node 22；本机版本单列；生成新源指纹，不覆盖旧 r6 或余额停线证据 |
| PREP-TASK-READY | [P-02 至 P-04 任务包](PREDEV_P02_P04_TASK_PACKAGE_2026-10-20.md) | 每个任务均可追溯需求/AC、接口边界、依赖、测试、证据与停线 |

依赖安装、付费真实调用、外部写入、Git 提交/推送/PR、部署均需按仓库规则分别授权。

## 2026-10-22 实际检查

| 检查（工作目录除注明外为仓库根） | 实际结果与范围 |
| --- | --- |
| `.venv/Scripts/python.exe scripts/validate_project.py` | 退出 0；现行映射、冻结协议和本地链接的离线校验通过，不核验公开来源真伪 |
| `backend: ../.venv/Scripts/python.exe -m pytest -q tests/unit/test_config.py --basetemp=../.pytest_tmp/config-fixed` | 7 passed，退出 0；覆盖默认 5 与非默认 3 的构造传递 |
| `backend: ../.venv/Scripts/python.exe -m pytest -q tests/unit/test_validate_project.py --basetemp=../.pytest_tmp/traceability-fixed` | 30 passed，退出 0；包含 FR-011/012、NFR-010 缺失/错阶段的拒绝用例 |
| `backend: ../.venv/Scripts/python.exe -m pytest -q --basetemp=../.pytest_tmp/full-prep-20261022` | 588 passed、3 skipped、1 deselected，退出 0；真实 PostgreSQL 集成与真实浏览器未在本轮重新运行 |
| `.venv/Scripts/ruff.exe check`、`ruff format --check` | 退出 0；105 files already formatted |
| `uv --directory backend lock --check --offline` | 退出 0；锁定 286 packages，未安装依赖 |
| `frontend: npm run test`、`npm run type-check`、`npm run build` | 均退出 0；23 项测试通过、类型检查及构建完成；本机 Node v23.11.1，CI 与新增 `.nvmrc` 指向 22，Node 22 本机运行尚未验证 |
| PowerShell Parser 检查 `scripts/start-p01.ps1` | 0 parser errors；未重新做冷启动或 Worker 故障演练 |
| `git diff --ignore-submodules=all --check` | 退出 0；仅有 Windows 换行提醒。`browser-use` 子模块 Git 元数据访问受限，未核实其工作区状态 |
| `evaluation.current --phase pilot --output data/evaluation/p02-pilot-dry-run-r7-20261022.json` | 退出 0，`not_live_execution`，计划三题、0 次尝试；文件 SHA-256 `8b929bed59e1815e231ebd39929f4b279c9ac7433160bc90175a9506a7aeea35`；新源码指纹 `7241401264fc31532142f09461791556912382c555ad1dd9e5f587d052cd10ef`，旧 r6 为 `90a4b9963dbedaab8ffcc35d7a8bf6e055b61c1f871ec4760859f36685b74e52`；协议和锁哈希相同。此工件仅为预览，正式运行须重新冻结实际环境 |
| DeepSeek 官方 `GET /user/balance` 只读复核 | HTTP 200，`is_available=true`，CNY 余额区间仍为 `0 <= balance < 1`；不保存精确余额，未调用模型、未建额。官方[余额接口](https://api-docs.deepseek.com/api/get-user-balance/)说明字段；[模型与价格](https://api-docs.deepseek.com/quick_start/pricing/)需在真实运行前重新确认。原 pilot 授权引用为 `chat:2026-10-22-p02-pilot-cny49`，余额门槛未过，继续 No-Go |

首次 pytest 试跑指定了尚不存在的 basetemp 父目录，出现 `FileNotFoundError`；创建仓库内 `../.pytest_tmp` 后重跑，以上列出通过结果。没有把环境错误当作代码回归通过。上次[预检停线记录](../../data/evaluation/p02-pilot-preflight-stop-20261022.json)仍为原始证据；本次只读余额结果没有改写它，也没有产生新尝试。

## 校招准备整改：配置与证据边界复核

本节记录在既有准备工作上的补充整改；上述旧检查表仍是当时的实际结果，不用它替代本次复跑结果。

| 配置/入口 | 已核实的读取与消费路径 | 当前验证边界 |
| --- | --- | --- |
| `RECENT_TRACE_COUNT` | `.env.example` → `Settings`（默认 5、允许 3–5）→ `new_agent` → `AgentLoop.context_manager` → `ContextManager.build` 对最近事件的实际投影 | 新单测同时检查环境读取、对象构造及 3/5 条输出；P-02 相关性选择仍未实现 |
| `MAX_STEPS`、`DEEPSEEK_MODEL` | `.env.example` → `Settings` → `new_agent` 的 Loop 上限与 `DeepSeekClient` 型号 | 已有配置/循环/provider 离线测试；本轮不代表实时模型可用 |
| `DATABASE_URL`、`P01_DATABASE_URL` | V1 SQLite 入口与独立 PostgreSQL API/Worker 分开；后者缺失或非 `postgresql+asyncpg` 即拒绝 | SQLite 路径与 PostgreSQL 类型有单测；本轮真实 PostgreSQL 集成未重跑 |
| `DEEPSEEK_API_KEY`、`GITHUB_TOKEN` | `Settings` 的 `SecretStr` 与服务端工具/模型构造；空白视为缺失 | `.env` 不输出到本文；秘密不得进入 Prompt、事件、轨迹或 Diff；真实端到端脱敏仍待 P-02/P-03 证据 |
| 价表与冻结指纹 | P-02 启动器将独立价表传给 Worker，pilot 执行器要求同一价表、代码/模型/环境及既有总账 | 2026-10-22 价表只在自身有效窗口内使用，过期重核官方价格并生成新指纹；余额停线仍有效 |
| 上游与运行环境 | `browser-use` 为可编辑子模块依赖；`uv.lock` 锁版本；`.nvmrc` 为 Node 22，CI 从中读取 | 子模块 Git 元数据受限未核实工作树；本机 Node 23 已验证，Node 22 本机尚未验证；WSL 冷启/恢复需另跑 |

状态口径为：**已实现**看源码和接口，**已离线验证**看本轮命令，**假任务实测**看 P-01 原始记录，**真实研究实测**看核源尝试，**目标设计**看现行规格/契约。真实 pilot 未开始，产品继续 No-Go。校招展示重点为上下文证据选择、事实到结论链，以及一次可证伪的调用级优化；所有模块仍按[现行任务包](PREDEV_P02_P04_TASK_PACKAGE_2026-10-20.md)交付。

## 2026-10-22 校招整改复核

下表是本次整改后的新结果，不覆盖上节原始检查记录。后端全套测试在获准的本机执行环境运行，因受限沙箱的 asyncio 测试曾停滞；聚焦测试与静态检查在仓库环境完成。所有真实模型/浏览器调用数为 0。

| 命令与范围 | 实际结果 |
| --- | --- |
| `.venv/Scripts/python.exe scripts/validate_project.py` | 退出 0；现行文档链接直达、权威映射、冻结题面与协议离线校验通过；不证明网页来源真实 |
| `backend: ../.venv/Scripts/python.exe -m pytest -q tests/unit/test_config.py tests/unit/test_validate_project.py --basetemp=.tmp/pytest-prep-focused-20261022` | 38 passed、退出 0；包括环境变量→运行上下文 3/5 条投影与迁移后链接回归 |
| `backend: ../.venv/Scripts/python.exe -m pytest -q --basetemp=.tmp/pytest-prep-full-20261022` | 589 passed、3 skipped、1 deselected、退出 0；PostgreSQL opt-in 与真实浏览器未验证 |
| `.venv/Scripts/ruff.exe check`、`ruff format --check`、`python -m compileall -q` | 退出 0；111 个 Python 文件格式通过，编译通过 |
| `uv --cache-dir .tmp/uv-plan-cache --directory backend lock --check --offline --python ../.venv/Scripts/python.exe` | 退出 0；离线锁定 286 packages，无依赖安装 |
| `git diff --ignore-submodules=all --check` | 退出 0；仅 Windows 换行提醒；未验证子模块 Git 工作区状态 |
| `backend: PYTHONPATH=src ../.venv/Scripts/python.exe -m adaptive_research.evaluation.current --phase pilot --output ../data/evaluation/p02-pilot-dry-run-r8-20261022.json` | 退出 0，`not_live_execution`，三题计划、0 次尝试、0 次模型/浏览器调用；[新预览](../../data/evaluation/p02-pilot-dry-run-r8-20261022.json) SHA-256 `6e73885902c99e1ba44c1d2bf97cce76bfa2e5abb6f53dc262f7ccc4b91e8a11`，源码指纹 `64bded4dde2eeb3e24fbb0d140894fde401455cb833097827d6343c4ac47eb7a`，正式运行须再冻结环境 |

前端本轮未改源码，上一轮 Node v23.11.1 的 23 项测试、类型检查和构建结果仍有效；本机 nvm 目录仅查到 v16.20.2 和 v23.11.1，Node 22 本机运行与远端 CI 结果仍未验证。`actions/setup-node@v4` 的[官方用法](https://github.com/actions/setup-node/blob/v4/README.md#usage)支持 `node-version-file` 读取 `.nvmrc`，但代码审查不代替一次 CI 执行。随后 WSL 的 PostgreSQL 只读检查成功；启动器仍未通过，本机真实浏览器恢复、备份恢复和五账户隔离本轮均未重跑。

只读复核显示，原始 V1 SQLite SHA-256 仍为 `1cf908a6f9e83985548ba7bd0753a204e6d8ccbaf70ac34daa9d3152ecbd0064`，r12 `summary.json` 仍为 `4d1bd15ddb80c8f6fc4148d6ce4b95b4e6c13afe78f534d29158fb3b7839d88d`。新预览只用于准备验收；原余额不足 1 元的停线工件保留为历史证据，后续只读余额检查显示 CNY 余额已达到 1 元最低门槛。pilot 仍未开跑。准备整改可判离线通过，P-02/P-03/P-04 与产品均继续 No-Go。

## 2026-10-22 真实 pilot 启动前停线补记

此前针对 B01–B03 各一次、合计最多 49 元的明确授权引用仍为 `chat:2026-10-22-p02-pilot-cny49`。只读余额复核得到 `CNY >= 1`，不记录精确余额。WSL PostgreSQL 专用库 `adaptive_agent_pilot_20261022` 的迁移版本为 `20261021_05`；建额前应用任务、调用、预算、事实和报告等八张表均为 0。`browser-use` 提交核对为 `7be96ed8bafa8dfe1eef228b59cf5c884b8b2431`。现行价表仍在本地 24 小时有效窗口内，r8 计划的源码指纹与工作区复算一致。新[运行冻结工件](../../data/evaluation/p02-pilot-runtime-freeze-r8-20261022.json) SHA-256 为 `93cf884d20d9315e31f97ce6d1ece3aa9ed643f5078959915355158aa3f01e14`；旧冻结与旧余额停线记录保留。

在专用库执行 `pilot_budget --arm` 后，返回 `armed`、pilot 上限 49 元、项目上限 299 元、任务/模型调用均为 0。随后本机 API/Worker 启动命令遭自动审批拒绝：审批认为命令中 `hide_password=False` 的数据库 URL 处理可能暴露凭据，并认为长期服务启动缺少对具体操作的授权；审批明确要求不得换路径绕过。本轮遵守停线，未启动 API/Worker，也未执行 `pilot_runner --execute`。拒绝后只读复核：任务 0、调用 0、报告 0、预算 1 且状态 `armed`；本轮创建的 WSL 保活进程已停止，8000 端口无监听。**没有真实研究尝试、模型调用或本轮可归因的付费费用。**

后续须先解决上述自动审批的凭据处理与服务启动授权；再复核余额、价表时效、运行指纹、专用库预算状态和无任务/调用，才能继续同一 pilot。当前 `armed` 只是持久预算额度，不是研究已开始或已经花费 49 元。到期须生成新价表/计划并复核可比性；未取得真实基线前不得开展 P-02 质量行为修改。

## 2026-10-22 用户降额授权后的真实结果

用户随后明确批准启动本机 API/Worker 并执行 B01–B03，**本次总上限人民币 10 元**。在没有任务与调用的专用库中，先把持久预算从 49 元原子降为 10 元，并将授权引用改为 `chat:2026-10-22-p02-pilot-cny10`；[r9 冻结工件](../../data/evaluation/p02-pilot-runtime-freeze-r9-20261022.json) SHA-256 `109695243fc7427d58eb6353908a288bad5e629ae7820387d1022b6ef8d020fb`。本机 API/Worker 使用进程内环境传递数据库连接串，没有在命令输出打印凭据。启动后再次确认 API HTTP 200、Worker 存活、专用库预算 10 元及任务/调用均为 0。

执行器串行提交 B01 后，任务 `59a0f54a-e250-48df-b2ba-bbf4834a9256` 以 `partial`、`token_budget` 终结。执行器写入[暂停记录](../../data/evaluation/p02-pilot-r9-20261022/paused.json)，**未提交 B02、B03**；B01 失败计入本次尝试，不把三题计划当作三题实测。B01 捕获中的 9 次模型调用已知费用为 `0.04139536` 元，11 次工具调用费用未知，故实际总费用为 `null`、[项目账本](../../data/evaluation/ledger-after-45ecbdf2-bc98-5fb3-9fa7-3b4f505c2c1c.json)为 No-Go。6 个捕获文件、清单与上一版总账的 SHA-256 绑定已复算匹配；项目校验器对该账本退出 1，明确报告费用未知须停新付费调用。运行链已关闭，8000 端口无监听，持久预算已设为 `halted`、理由 `pilot_partial_no_go`。[调用级诊断](../audits/P02_B01_LIVE_FAILURE_TRIAGE_2026-10-22.md)记录了证据、待证伪假说与人工核源缺口。

**层级判定：** 准备层的离线检查通过；P-02 三题基线没有完成，B01 未通过，费用总额仍未知；P-03/P-04 尚无新验收，产品保持 No-Go。下一步先对账并做离线失败重放，任何新真实 cohort、诊断付费运行及正式评测仍遵守各自授权与预算停线规则。

## 2026-10-23 费用核销与新批次准备进度

原始 B01 捕获、失败分母和旧 No-Go 账本均未改写。复算捕获清单中 6 个文件及清单自身的 SHA-256 全部相符；20 条调用为 9 次模型和 11 次工具，模型费用合计 `0.04139536` 元。用户报告 DeepSeek 页面显示 `0.04` 元，只有两位小数，无截图或逐请求明细；[脱敏说明](../../data/evaluation/b01-deepseek-console-attestation-20261022.json)不将该显示值伪装成精确费用。[逐调用核销工件](../../data/evaluation/b01-cost-reconciliation-20261022.json)绑定旧账本、原捕获和说明的 SHA-256，并将 11 次已核实走本地 browser-use 或公开 GitHub REST 的工具调用列为有依据的零费用。[后继账本](../../data/evaluation/ledger-after-b01-reconciliation-20261022.json)记录 B01 总额 `0.04139536` 元、未知调用数 0，项目校验器退出 0；其 `billing_reconciliation` 仍明确为用户报告的四舍五入控制台金额，**未取得逐请求 provider 发票**。旧 B01 仍为 `partial/token_budget` 失败。

准备工具增加了确证零费用与未知费用的分列、拒绝前的安全 Token 上界诊断、执行进程源码指纹与捕获时源码核对。新执行器允许稳定任务级失败继续下一题，系统故障、未知费用、证据不一致及预算超额仍停线。未更改规划、上下文选择、事实准入或研究质量策略。旧 B01 未保存原始 Prompt，离线合成重放只证实预算预检机制，不能精确重算当时的拒绝字节数；GitHub 403 与异常检索时间仍按[调用级诊断](../audits/P02_B01_LIVE_FAILURE_TRIAGE_2026-10-22.md)保留为伴随问题。

验证：`python scripts/validate_project.py --ledger data/evaluation/ledger-after-b01-reconciliation-20261022.json` 退出 0；`uv lock --check --offline` 退出 0；后端 `python -m pytest -q backend/tests` 为 603 passed、3 skipped、1 deselected，另对一次性空 PostgreSQL 测试库运行 `test_pg_store.py` 为 3 passed；前端 `npm run test -- --runInBand` 为 23 passed，`npm run type-check` 和 `npm run build` 退出 0。异步测试在受限 Windows 沙箱中连最小事件循环都无法启动，以上后端结果来自获批的本机执行。`ruff check` 通过；格式修正后仍需最终复核。当前 Node 为 v23.11.1，`.nvmrc` 要求 22，本机现有 nvm 目录未见 Node 22；WSL Ubuntu 的 PostgreSQL 5433 接受连接，`browser-use` 提交仍为 `7be96ed8bafa8dfe1eef228b59cf5c884b8b2431`，锁文件离线校验通过。

**当前 No-Go：** 新三题批次尚无独立付费授权、Node 22 尚未安装/核验，也未形成 B01–B03 三次独立同版尝试或人工核源记录。下一入口为补齐这两项运行门槛后重新冻结计划、余额、官方价表、GitHub 限流与新隔离 pilot 库，按人民币 10 元新批次上限串行运行并交由用户逐字段核源；在此之前不得宣称准备完成或开始质量行为改动。

进一步核对发现旧执行器可接受 49 元 pilot 预算，因此已将新批次执行前门槛收紧到 **最多 10 元**，新增 11 元预算拒绝回归；`test_pilot_runner.py` 15 passed。新建隔离的 WSL 库 `adaptive_agent_pilot_20261023`，迁移到 `20261022_06`；只读确认任务、调用、预算、报告均为 0。未建额、未提交任务。最终[离线三题计划](../../data/evaluation/p02-pilot-dry-run-r11-20261023.json)包含 B01–B03 各一次，SHA-256 为 `4ba96406e4494e95de75d70f9435d884ce38c474f36ccb822decd25be72b3cd1`，状态 `not_live_execution`；前一个 r10 预览因执行器源码后续收紧而仅保留为历史。Node 22、余额/价表临运行时复核及新批次授权仍待完成。

## 2026-10-23 新批次真实三题诊断基线

用户分别授权本机安装 Node 22 和本批次 B01–B03 各一次、合计最多人民币 10 元的真实付费运行。官方 Node 22.23.4 发布包经 SHA-256 核对后置于 Git 忽略的 `.tmp/node22`，该进程环境下前端 23 项测试、类型检查和构建通过。临运行时再次打开 [DeepSeek 人民币价表](https://api-docs.deepseek.com/zh-cn/quick_start/pricing/)并刷新[价格快照](../evaluation/DEEPSEEK_CNY_PRICING_2026-10-23.json)；只读余额接口返回可用、CNY 总额至少 10 元（未保存精确额），GitHub 仓库 GET 为 HTTP 200、限流余量 59。新库在建额前为零任务零调用；随后持久预算设为 10 元。[运行冻结](../../data/evaluation/p02-pilot-runtime-freeze-r11-20261023.json)绑定 r11 计划、当前价格快照、前序项目账本、协议及锁文件哈希，SHA-256 `602cfe51c3fd1e0d0523f9ceed92962ec53bd4180d27ceccba7356e2ebb68082`。

串行执行器完成三次独立尝试，状态均保留为诊断材料，**无完整成功**：

| 题目 | run ID / task ID | 真实终态 | 本次已知费用（元） | 事实数 |
| --- | --- | --- | ---: | ---: |
| B01 | `39d4a2d0-8729-5b97-be65-a87d0678a0f2` / `89d08313-5851-47e7-a4a4-6918bd596c4a` | `failed/no_progress` | 0.03792848 | 0 |
| B02 | `347bd8b2-0e09-5975-8dff-e8ed4f2c1a52` / `136c307b-a562-4ea4-8e8c-da325ceeb01a` | `failed/token_budget` | 0.03836468 | 0 |
| B03 | `e4e3e822-f5f0-582d-9412-e7cb91daefe4` / `ecad1481-a489-4c0f-b01a-04076ac01e9b` | `partial/token_budget` | 0.04767960 | 2 个待核源候选 |

新批次费用合计 **0.12397276 元**，未知费用调用 0，低于 10 元上限；旧 B01 及新三题合计四次尝试、项目已知总额 `0.16536812` 元。每次脱敏捕获的 6 个文件共 18 个 SHA-256 均复算匹配，运行源码核对为 true。最终[项目账本](../../data/evaluation/ledger-after-e4e3e822-f5f0-582d-9412-e7cb91daefe4.json)通过 `validate_project.py --ledger`，后继链保留旧 B01 失败；[诊断基线摘要](../../data/evaluation/p02-pilot-r11-20261023/diagnostic-baseline-summary.json)绑定三题报告、捕获和[逐字段待人工复核包](../../data/evaluation/p02-pilot-r11-20261023/)。API 已停止、8000 端口无监听；新库预算被持久改为 `halted/authorized_pilot_batch_complete`，防止复用授权。

**准备完成判定仍待人工项：** B01/B02 没有候选事实，B03 的两条候选均指向 browser-use 官方发布页，但其 `retrieved_at` 为 2026-10-16，早于本次运行，且缺少来源定位与人工身份确认。核源人须逐字段打开官方页面并在复核包记录结论；另需人工核对 DeepSeek 控制台/账单有无本批次漏记用量。当前包的所有人工结论均为 `null`，不能把助手事后打开页面视为用户人工核源。研究质量与产品放行继续按 P-02 至 P-04 的后续门槛判定；下一开发入口是在人工结论完成后对 `no_progress`、Token 预检及事实时间/定位缺口分别提出可证伪的最小改动。

## 2026-10-23 人工核源与批次交接

以上待复核包保留原样。[人工核源后继结论](../../data/evaluation/p02-pilot-r11-20261023/human-review-conclusion-20261023.json)（SHA-256 `78a7b67c193f9ae1ee53f6dbb07cfd1295a72455c27bf7ec33038c1d540bf6cd`）绑定三题复核包及报告。用户打开 [browser-use 官方 0.13.13 发布页](https://github.com/browser-use/browser-use/releases/tag/0.13.13)后答复“核实”；结论仅覆盖 B03 候选事实 `f1`/`f4` 的版本 `0.13.13`、页面 `Latest` 标记和该 URL。B01/B02 无候选事实，全部必需字段未核实；B03 发布日期与两项变化缺失，仍未核实。B03 原事实时间早于运行及缺少定位的问题继续保留，B03 仍为部分结果。

用户另报告 DeepSeek 控制台本批次显示 `0.12` 元。[脱敏显示额说明](../../data/evaluation/p02-pilot-r11-20261023/provider-console-attestation-20261023.json)（SHA-256 `aa4ca0b693c3981f999fcffdfd4b7f19cfe7e9c6497fd3488d8068f2487f6a21`）将该两位小数显示值与逐调用用量及价表计算的 `0.12397276` 元核对，四舍五入一致。未取得逐请求账单或截图，不把显示值当成精确费用。新批次 0 个费用未知调用、总额低于 10 元；旧 B01 与新三题均留在[最终项目总账](../../data/evaluation/ledger-after-e4e3e822-f5f0-582d-9412-e7cb91daefe4.json)。

[最终交接工件](../../data/evaluation/p02-pilot-r11-20261023/predev-handoff-20261023.json)（SHA-256 `079ace1b91a8c5b2f5b1e9241a3ba1fc27b318c154532ead6c15fc492d313a26`）绑定冻结、三题基线、旧账核销、最终账本、人工核源及控制台说明。**开发前准备完成，P-02 研究质量和产品放行仍为 No-Go。** 后续从调用轨迹分别定位 B01 无进展、B02 Token 预检和 B03 事实时间/来源定位缺口；先提出可证伪的定点改动，再执行 P-02 至 P-04 的独立验收。
