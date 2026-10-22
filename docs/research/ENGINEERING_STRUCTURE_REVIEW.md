# 工程结构研究与目录整理方案

日期：2026-10-20（Asia/Shanghai）。范围：本仓库的目录、文档入口、配置、需求拆分、开发验收及研究评测闭环；外部证据只用官方仓库文件。本文是研究和整理建议，不替代现行规格、计划、契约及协议，也不批准业务实现或改变历史验收。

后续状态（2026-10-22）：下文“本次修改前”“尚未迁移”等叙述保留 2026-10-20 盘点时点；R0 物理迁移和 P-01 假任务关口已分别记录在 [R0 验收](../tasks/R0_ACCEPTANCE_2026-10-20.md)与 [P-01 验收](../tasks/P01_ACCEPTANCE_2026-10-21.md)。真实研究仍按 [P02 停线记录](../tasks/P02_PILOT_PREP_2026-10-21.md)为 No-Go。以下证据链接指向迁移后的文件位置。

## 结论

目前主要是**文档的版本、职责和状态难以辨认**，尚无充分证据认定源码必须整体换目录或重写架构。已有准备材料很丰富；下一步的收益在于让任务能从现行要求直接找到实现范围和验收证据，并按已确认的 P-01 关口检验目标架构。

本次先完成低风险整理：新增[统一导航](../README.md)，从根 README 接入；保留源码路径、冻结文件、历史审计、SQLite、r12 和上游 checkout。本报告给出其余整理的范围及验收条件，尚未执行物理迁移。

## 本地盘点与问题证据

本次修改前，`docs/` 共 **60 个文件**：`audits` 24、`design` 18、`evaluation` 7、`contracts` 3、`archive` 3，其余五个分类各 1 个。`.codex-workflow/lifecycle/` 另有 16 个历史过程文件。统计不含缓存、上游 checkout 和运行数据。

| 发现 | 可复查证据 | 影响及判断 |
| --- | --- | --- |
| 同一根目录呈现多代规格/计划 | 现行 [SPEC](../../SPEC.md)、[PLANS](../../PLANS.md)，以及根目录 `SPEC_0.4.md`、`PLANS_0.4.md` | 旧快照正文仍记录当时的 APPROVED 和旧相对链接；读者若绕过现行入口，容易误用旧目标。旧快照不能直接改写。 |
| `design` 不能整体理解为现行设计 | [设计索引](../archive/design-0.3/00_DESIGN_INDEX.md)明确主要正文是 0.3 历史；[ADR-0005](../design/adr/0005-windows-worker-wsl-postgres.md)却是当前决定 | 目录按主题分了类，但没有直接表达哪些仍有效。导航应明确区分，不能让读者自己比较五个 ADR 后猜架构。 |
| 任务设计放在审计分类中 | [P-01 开工包](../tasks/PREDEV_P01_START_PACKAGE_2026-10-20.md)、[后续任务包](../tasks/PREDEV_P02_P04_TASK_PACKAGE_2026-10-20.md)当时在 `audits`；`tasks` 内只有 V1 任务记录 | 找下一步开发的人自然会先进入 `tasks`，却找不到当前任务包。未来任务按用途归档，现有文件先由导航消歧。 |
| 文件名容易被当作当前状态 | [CURRENT_CHANGESET_ACCEPTANCE](../archive/v1-audits/CURRENT_CHANGESET_ACCEPTANCE.md)标题实际是 2026-10-10；另有多份 PREDEV/FINAL/VERIFICATION | 每个记录可以对当时范围成立，但文件数量和 FINAL 字样不能证明现在“全部最终确认”。日期、基线、范围和证据应共同解释结论。 |
| 旧执行器与新评测协议并存 | 根目录 `benchmark/` 与[历史协议](../benchmark/BENCHMARK_PROTOCOL.md)属于 V1；[现行协议说明](../evaluation/README.md)定义 `current-3` | 协议可被校验不等于新的实际执行、核源和项目总账链路已经完成。不能把运行旧 runner 视为完成现行 15 次验收。 |
| 已有过程记录分布在两处 | `.codex-workflow/lifecycle/` 与 `docs/audits/` | 历史证据可保留，但新任务不应为同一状态维护两份独立结论。一个任务记录链接命令输出和 AC 结果即可。 |
| 工作区包含大量既有未提交资料 | 主仓库 `main`，HEAD `dbacdc02fb119f70bc65a14608ab1bede75c0622`；修改前主仓库状态有既有修改和未跟踪材料 | 本次编辑前建立内容哈希基线，不能把整个工作区当成本轮成果。未跟踪不等于可以删除。 |

普通 `git status` 因 `.git/modules/browser-use` 访问受限失败；使用 `git -c status.submoduleSummary=false status --short --ignore-submodules=all` 得到主仓库状态。这不能证明子模块清洁，本次也未修改上游。

## 源码结构应怎样理解

当前主链是 `Vue → FastAPI → ResearchService → TaskManager/AgentLoop → 工具`，SQLite 保存事实和事件，SSE 读取已提交事件。独立 Worker 与 WSL PostgreSQL 是目标方案，不能画成现状。

| 路径 | 当前责任 | 整理判断 |
| --- | --- | --- |
| `frontend/src/` | Vue 展示、API 客户端、SSE 与交互 | 先保留。`App.vue` 337 行，后续账户/历史功能增加时再按界面职责和状态所有权拆分；行数本身不是缺陷。 |
| `backend/` | HTTP/SSE、配置、应用编排、持久化 | 与 Agent 算法分开有意义；不应仅为匹配外部仓库改名 `api/` 或 `apps/api/`。 |
| `adaptive_agent/` | Loop、规划、上下文、事实评估、报告、状态与工具适配 | 本次搜索没有发现导入 `backend`；这支持保持其可被 API、Worker 和评测复用的方向，不是完整依赖审计结论。 |
| `adaptive_agent/runtime/` | 当前进程内 TaskManager | Worker 分离时的真实改动点；目录存在不代表持久认领、fencing token 或恢复已实现。 |
| `benchmark/` | V1 runner、基线及评分 | 先保持旧行为可复查。新正式评测执行链要依照现行协议逐项实施，不靠目录改名完成迁移。 |
| `tests/unit/`、`integration/`、`smoke/` | 分层代码验证 | 已有层次；新增 PostgreSQL/恢复/账户测试时复用，不必为每个开发阶段再建一套测试树。 |
| `browser-use/` | 上游子模块 | 保持上游所有权及固定版本，不纳入目录重构。 |
| `data/`、`dist/`、缓存目录 | 运行数据、构建产物、本地缓存 | 不与源码混同。先查跟踪状态和用途，再考虑编辑器排除显示；本次不删除。 |

目标架构继续遵守 ADR-0005：API 接收和持久化请求；Worker 执行长任务；PostgreSQL 应用表拥有任务、租约、事实、费用和事件；通知只唤醒；浏览器交给工具适配层管理。P-01 用假任务验证认领、取消、故障与对账，P-02 再验证研究质量。架构拆进程不能自动修复 r12 的研究失败。

设计拆分时，Module 应让调用方通过小而稳定的 Interface 使用足够完整的行为；API/Worker 的实际运行差异才是需要明确的 Seam。避免为“目录看起来专业”新增只有转发作用的层、通用 `utils` 或尚无需求的平台包。

## GitHub 高星项目：核实到了什么

### R0 补充：按固定提交核对分层与评测（2026-10-20）

本轮另核对了三个仓库的固定提交，避免把变化中的 `main` 当作同一版本。GitHub 当时显示 [DeerFlow](https://api.github.com/repos/bytedance/deer-flow) 约 84.2k、[Dify](https://api.github.com/repos/langgenius/dify) 约 159k、[Open Deep Research](https://api.github.com/repos/langchain-ai/open_deep_research) 约 12.7k stars。热度只用于选择样本。Open Deep Research 已归档，作为研究流程的历史参考。

- DeerFlow 的 [Gateway](https://github.com/bytedance/deer-flow/blob/d288935865a7a0f2f33d8138aedaaa29997e0e7c/backend/app/gateway/app.py) 与后端 Agent 包分层；其 [SSE 离线回放测试](https://github.com/bytedance/deer-flow/blob/d288935865a7a0f2f33d8138aedaaa29997e0e7c/backend/tests/test_replay_golden.py)还检查 replay miss。可借鉴接口级回放与失败显式化；它的默认运行拓扑并非本项目已确认的独立 Worker。
- Dify 的 [部署配置](https://github.com/langgenius/dify/blob/1.17.1/docker/docker-compose.yaml)让 API、Worker 以不同模式运行同一个后端镜像；[查询实现](https://github.com/langgenius/dify/blob/638ed4eb5565b8771a6b016358a129062bbfed83/api/repositories/sqlalchemy_api_workflow_run_repository.py#L248)在 SQL 中限定 tenant 与 app。对本项目的推论是共用后端代码并让 owner 过滤进入数据库读写条件；无需照搬 Celery、Redis 或 Dify 的平台规模。
- Open Deep Research 的[研究流程](https://github.com/langchain-ai/open_deep_research/blob/1b7d2e80db9faa586165c60e09096dbbfd483a64/src/open_deep_research/deep_researcher.py)将 brief、研究和报告分步；[评测入口](https://github.com/langchain-ai/open_deep_research/blob/1b7d2e80db9faa586165c60e09096dbbfd483a64/tests/run_evaluate.py)固定模型与实验配置。可借鉴实验条件记录，其 LLM 评分不代替本项目逐事实的人工官方核源。

由这些源码推导的本项目选择已体现在[架构入口](../architecture/README.md)：`frontend/` 与 `backend/` 集中布局、API/Worker 共用应用与持久化接口、离线回放和逐次证据；真实研究放行仍依现行协议。以上是源码和配置调研，没有运行这三个外部项目，也没有验证其最新 CI 或实际研究成功率。

2026-10-20 查阅的官方主页显示近似热度：[browser-use](https://github.com/browser-use/browser-use) 118.5k、[Dify](https://github.com/langgenius/dify) 159.0k、[LangGraph](https://github.com/langchain-ai/langgraph) 43.5k。星数和页面抓取可能不同步，只用于解释样本选择。本次没有运行这三个项目；下列链接多为可变 `main`，证明的是所查文件中的公开机制，不是同一提交的完整审计或实际执行率保证。

### browser-use：模块清楚，不等于真实任务门槛适合照抄

其 [模块说明](https://github.com/browser-use/browser-use/blob/main/browser_use/README.md)及[实际目录](https://github.com/browser-use/browser-use/tree/main/browser_use)按 agent/browser/dom/llm/tools 等职责组织，同一功能内放相关服务、模型和提示。[pyproject.toml](https://github.com/browser-use/browser-use/blob/main/pyproject.toml)集中定义开发依赖、打包及 pytest 配置；[AGENTS](https://github.com/browser-use/browser-use/blob/main/AGENTS.md)指向环境示例和检查，并要求结构化输入输出。这支持本项目保持 Agent 核心、工具与 HTTP 层的明确责任。

[test.yaml](https://github.com/browser-use/browser-use/blob/main/.github/workflows/test.yaml)区分代码测试与 agent evaluation，并保存结果；但其中存在真实密钥依赖，不能称整个流程都是离线 CI。[evaluate_tasks.py](https://github.com/browser-use/browser-use/blob/main/tests/ci/evaluate_tasks.py)读取 task/judge_context/max_steps、用子进程隔离任务；缺少所需 Browser Use/Google 密钥时，却会返回带 skipped 说明的 `success: True`，正常汇总逻辑也只在有任务且零通过时判失败。因此其绿灯不能直接证明任务研究质量达到本项目门槛。

另外，[eval-on-pr.yml](https://github.com/browser-use/browser-use/blob/main/.github/workflows/eval-on-pr.yml)将 commitSha/testCase 发给外部评测，触发步骤允许 continue-on-error；[publish.yml](https://github.com/browser-use/browser-use/blob/main/.github/workflows/publish.yml)具有 release environment 审核检查，但部分发布前测试仍为注释。可学习任务输入和逐次结果的绑定；本项目仍须区分 skipped/failed/passed，不能照抄这些放行条件。

### Dify：按运行职责组织，并把失败证据接到测试

[根 AGENTS](https://github.com/langgenius/dify/blob/main/AGENTS.md)解释 api/web/docker/agent/cli/e2e 等职责及作用域规则；[API AGENTS](https://github.com/langgenius/dify/blob/main/api/AGENTS.md)明确 controllers 处理传输，services 编排，core/领域 owner 承担业务规则，libs 保持业务无关。这为本项目保留 Vue/API/Agent 核心的责任划分提供参考，不能推出本项目也需要它的全部目录和中间件。

[贡献指南](https://github.com/langgenius/dify/blob/main/CONTRIBUTING.md)要求说明使用场景、复现、预期、错误和日志，并为有可观察行为或回归风险的变更补测试；[前端测试指南](https://github.com/langgenius/dify/blob/main/web/docs/test.md)以稳定的用户可见行为为目标，按问题选择单元/组件/集成/真实浏览器验证，浏览器失败留截图与 traces。可迁移的是“一个变化对应可核实行为和失败证据”，不是用覆盖率数字代替验收。

[api-tests.yml](https://github.com/langgenius/dify/blob/main/.github/workflows/api-tests.yml)分 unit/controllers/integration 并保存 JUnit；[db-migration-test.yml](https://github.com/langgenius/dify/blob/main/.github/workflows/db-migration-test.yml)检查迁移 SQL，并实际执行数据库迁移与就绪检查。对本项目的推论是：P-01 需要 PostgreSQL 的真实事务/迁移测试，SQLite fake 不能替代；Windows/WSL 实机证据仍另验，不照搬 Dify 的数据库种类和平台规模。

### LangGraph：契约测试与候选产物验证，不自动证明业务成功

[libs](https://github.com/langchain-ai/langgraph/tree/main/libs)按 core、checkpoint、存储实现、SDK/CLI、conformance 等独立责任组织；[checkpoint-conformance 说明](https://github.com/langchain-ai/langgraph/blob/main/libs/checkpoint-conformance/README.md)检查 blob 往返、metadata、namespace isolation、incremental updates 等存储契约。这证明相应存储 Adapter 的行为，不证明 Agent 的研究结果正确。

[PR 模板](https://github.com/langchain-ai/langgraph/blob/main/.github/PULL_REQUEST_TEMPLATE.md)要求验证方式、破坏性变化和依赖 PR；[CI](https://github.com/langchain-ai/langgraph/blob/main/.github/workflows/ci.yml)按变更路径选择包级检查，同时覆盖 core 对 SDK 集成的影响。[release.yml](https://github.com/langchain-ai/langgraph/blob/main/.github/workflows/release.yml)将 build/publish 权限分开，包含预发布检查和候选 wheel 安装后的单元测试。可迁移的是检查依赖影响和实际候选产物；不意味着本项目应立即拆包或引入 LangGraph。

[LangSmith 评测说明](https://docs.langchain.com/langsmith/evaluation)区分预先准备数据集的离线实验和线上流量监测，并将失败 trace 用于后续测试数据。对本项目而言，可学习失败样本回流与版本比较；没有必要因此新增 SaaS 或改写已经冻结的正式题面。新增诊断样本和正式评分集需要分清。

三者共同支持的取舍是：**代码按业务和运行责任组织，文档按权威与用途组织，结果按版本和尝试留证；工程阶段由任务和索引串联。** 这是本报告结合来源作出的推论，不能推断三项目执行相同的内部流程，也不应另建“讨论/设计/开发/验收/最终确认”五套平行代码树。

## 从开发前准备到交付的闭环

以下整理**现有要求的使用方法**，不重写现行门槛。权威分别在规格、计划、契约和评测协议中；表格用于检查是否能找到对应实物。

| 环节 | 要回答的问题与最小产物 | 本项目入口及完成判据 |
| --- | --- | --- |
| 产品与功能设计 | 用户是谁、首个场景是什么、成功/失败表现是什么、哪些延期？ | [SPEC](../../SPEC.md)：B01 首个纵切，FR/NFR、AC 和非目标明确。冻结设计不等于实现完成。 |
| 架构与契约 | 谁拥有状态、事务和资源？超时、取消、重启、数据库失联怎么表现？ | [现行契约](../contracts/CURRENT_CONTRACTS.md)、ADR-0005；用 P-01 实机假任务验证关键假设。 |
| 开发前配置 | 版本可复现吗？配置示例属于哪个运行时？环境探针覆盖了什么？ | Python/uv 与 npm 锁文件、CI、[环境记录](../audits/PREDEV_ENV_SETUP_2026-10-20.md)。WSL 保活连接成功不等于完整冷启动/恢复通过。 |
| 需求拆分 | 一个任务是否有依赖、范围、兼容影响、正常/失败验收和停止条件？ | [P-01 包](../tasks/PREDEV_P01_START_PACKAGE_2026-10-20.md)已有 DB/RUNTIME/CALL/API-CI 边界；每项绑定 FR/NFR 和 AC。 |
| 开发与代码验收 | 改动能否演示，失败路径能否复现，证据能否对应当前版本？ | 按相关源码和测试实施；记录命令、退出码、基线/差异、跳过原因及风险。独立审查按仓库规定的明确范围和有效权限进行。 |
| Agent 真实评测 | 结果正确还是只返回 completed？来源、条件和费用是否可复查？ | [current-3](../evaluation/CURRENT_EVAL_PROTOCOL.json)与[人工核源](../evaluation/REVIEW_WORKFLOW.md)；保留全部尝试，实际结果与用量对账。 |
| 诊断与优化 | 哪次调用出了什么问题，如何反证根因，修复是否带来新风险？ | [r12 症状清单](../audits/PREDEV_R12_SYMPTOM_INVENTORY_2026-10-20.md)是起点；调用证据→假说→定点改动→回归→真实复查，不能把症状直接写成根因。 |
| 最终验收与交付 | 哪些 AC 有当前证据，哪些失败，能否从干净环境复现和恢复？ | [后续任务包](../tasks/PREDEV_P02_P04_TASK_PACKAGE_2026-10-20.md)、[交付清单](../audits/PREDEV_DELIVERY_CHECKLIST_2026-10-20.md)；真实 15 次和隔离/恢复等关口通过后才能正式 Go。 |

具体任务宜采用一个可验收行为，例如“排队取消后释放容量且不执行”，包含 API、存储、Worker 和必要 UI 的验证；避免只写“做数据库”“写前端”。数据库等共享基础任务确有前置依赖时单独实施，但必须对应可验证的不变量。

一个任务只需一条可追溯记录：`Task ID / FR-NFR / AC / 依赖 / 状态 / 代码基线及差异 / 检查结果 / 证据链接 / 未解决项`。已有任务包作设计，实施后追加或链接实际结果；无需每轮新增一份泛称 FINAL 的总报告。全项目阶段状态继续以 PLANS 为入口。

## 配置盘点：已有基础和真正缺口

| 项目 | 本次看到的配置 | 还不能声称什么 |
| --- | --- | --- |
| Python | `pyproject.toml` 声明 Python 3.12/3.13、uv 锁、pytest/Ruff；asyncpg/Alembic 已列依赖 | 安装依赖不代表迁移和 PostgreSQL 事务行为完成；本次未安装。 |
| 前端 | `package-lock.json`，type-check/test/build 脚本，Vite 本机入口 | 有脚本不代表目标账户、管理员和新历史功能已实现。 |
| 应用配置 | `.env.example` 仍以 V1 SQLite 为示例，凭据留空 | 不能直接把 DATABASE_URL 换成 PostgreSQL 就称完成 P-01；须同步迁移、运行时和集成验证。未读取真实 `.env`。 |
| 工程流程 | 仓库规则、三个专用 Skill、Bug/PR 模板、现行协议及离线校验器 | 文件存在不代表自动执行或全部验收通过；不需要再叠加一套代理配置。 |
| CI | Python 3.12/3.13 离线测试/静态检查、前端类型/测试/构建 | 本次只读取 YAML，未证明远端 Actions 成功；Windows/WSL 容量和恢复不由 Ubuntu 离线任务证明。 |
| 运行证据 | SQLite、r12、V1 审计及环境探针已保留 | r12 仍 No-Go；新的真实评测、账户隔离、恢复、备份及完整交付尚未验收。 |

`adaptive_agent/evaluator.py` 判断单步研究证据，`tests/` 检查代码行为，`docs/evaluation/` 约束整项研究验收。这三个层级需要在任务说明中写明，不能统一简称“评测通过”。

## 分阶段整理，不重做一套工程体系

### 本次已做：先消除入口歧义

- 根 README 增加统一导航链接；新增 `docs/README.md`，解释现行目标、V1、历史、任务、评测与数据的用途。
- 本报告集中记录原因、外部来源、方案及边界；没有修改产品范围、协议门槛、业务代码或历史结果。
- 校验全部项目文档本地链接与现行版本约束，核对本轮之外文件的内容哈希；实际命令与结果在文末记录。

### 后续新任务：按职责放文件，减少新的混放

保留现有代码目录和四个权威入口，不创建 `apps/packages/infra` 骨架。后续确有新文件时采用：

```text
README.md / AGENTS.md / SPEC.md / PLANS.md
adaptive_agent/    Agent 核心、工具与执行
backend/           HTTP、应用编排、应用持久化
frontend/          用户界面
benchmark/         历史 V1 runner；新执行链实施时明确版本
tests/             单元、集成、受控 smoke
scripts/           确有需要的维护与验证脚本
docs/
  README.md        导航
  contracts/       当前与明确版本的契约
  tasks/           后续新增任务的范围、依赖与实际交付链接
  audits/          指定日期/基线的检查和验收结果
  evaluation/      协议、核源流程和评测证据说明
  research/        第一方来源调研及取舍
  design/          历史设计及现有 ADR；当前决定由导航定位
  specs/testing/   保留现有 V1 说明
  archive/         归档原件
```

此树说明职责，不表示本次移动了既有文件。当前任务包仍由导航指向其原路径；不复制一份正文到 tasks 形成两个现行来源。未来新增任务记录再使用 tasks。

### 物理迁移：作为独立的小任务处理

如果仍需把根目录 0.4 快照、历史设计或旧协议统一放进 archive，先登记“旧路径→新路径→内容哈希→引用方→校验规则”，确认保留原件的方式，再串行迁移。冻结文档内部的相对链接不能随意改字节；可保持旧路径只读，或在明确归档方案下增加解释性索引。不要用批量移动后全局替换掩盖这个冲突。

例如 `scripts/validate_project.py` 的 `DOCS`、`HISTORICAL_HASHES`、`ARCHIVED_TARGET_HASHES`、冻结题面来源，以及相应测试，都依赖既有路径或内容。因此“文件已搬过去”不足以验收，必须同时检查链接、哈希、校验器及现行入口。是否值得迁移，应以实际导航收益决定。

目录整理的完成标准：从 README 能找到四个权威入口、下一项 Task 和对应 AC；历史不再被解释为现行目标；任何阶段“通过”均能落到指定版本的证据；链接和冻结校验通过；原始数据及无关改动不变。隐藏缓存或减少顶层文件数不是充分标准。

## 当前确认与下一步

可以确认：现行方向和 P-00 准备材料已具备导航，主源码职责分工值得保留。尚不能确认：P-01 架构可行性、真实研究质量、五账户隔离、安全恢复、备份及产品整体放行。

建议下一步使用已确认的 P-01 细分任务推进假任务纵切，严格保留 P-02 的优化前 pilot 顺序。先取到实现和失败证据，再决定优化点；不再以新增框架、目录层级或“最终版”材料代替工程进展。业务实施依然按当前任务范围和仓库授权规则执行。

## 本次实际验证及限制

| 检查 | 实际结果 |
| --- | --- |
| `.venv/Scripts/python.exe scripts/validate_project.py` | 整理前、整理后均退出码 0；本地链接、版本/冻结约束及相关离线结构检查通过。没有提供 `--results` 或 `--ledger`，不代表实际结果批次或付费总账通过。 |
| `git -c core.safecrlf=false diff --check -- README.md` | 退出码 0。此 diff 包含 README 原有未提交改动；本轮仅新增开头的导航段落。 |
| 新增两个 Markdown 文件的逐行尾部空白检查 | 均无尾部空白；实际链接纳入上述全项目文档校验。 |
| 编辑前记录的 244 个既有文件 SHA-256 与编辑后比较 | 仅 README 内容变化，缺失文件 0；既有文档、项目配置、脚本、测试及已纳入基线的历史数据保持内容不变。基线临时记录在忽略的 `.pytest_cache/directory-audit-before.json`。 |
| SQLite 与 r12 汇总哈希 | 只读计算分别为 `1cf908a6f9e83985548ba7bd0753a204e6d8ccbaf70ac34daa9d3152ecbd0064`、`4d1bd15ddb80c8f6fc4148d6ce4b95b4e6c13afe78f534d29158fb3b7839d88d`，与既有准备记录一致。 |

本轮没有运行 Python/前端完整测试：仅修改导航和研究文档，未改变运行行为，验证采用文档链接、冻结约束和内容保护检查。未安装依赖、执行真实模型/浏览器任务、修改数据库或远端系统，也未提交或推送。上游子模块状态仍受权限限制未验证。外部研究没有取得统一提交快照，后续实施具体外部接口前需固定相关版本重新核验。

## R0 实施补记（2026-10-20）

上文记录的是本报告首次完成时的整理建议与当时验证结果；本节记录随后获授权的 R0 目录迁移。当前导航见[文档首页](../README.md)，目标运行边界见[架构入口](../architecture/README.md)。目录变化不将目标业务标记为已实现，产品仍 No-Go。

- 两份当前任务包从 `docs/audits/` 移至 [`docs/tasks/`](../tasks/README.md)。移动后调整了包内指向审计记录的相对链接；Task ID、依赖与 AC 沿用原包，任务索引只指向这些记录，不维护第二套状态。
- 0.3 设计正文与 ADR-0001 至 ADR-0004、V1 旧验收和根目录 0.4 快照按原字节归入[历史归档](../archive/README.md)。ADR-0005 留在现行路径。旧文档正文不重写；校验器按[逐文件路径与 SHA-256 映射](../archive/R0_PATH_MAP.json)解析迁移前的引用。
- 四个权威入口仍位于 `SPEC.md`、`PLANS.md`、`docs/contracts/CURRENT_CONTRACTS.md`、`docs/evaluation/CURRENT_EVAL_PROTOCOL.json`。开发与实际验收仍按现行计划的 R0、P-01 至 P-04 阶段和独立证据判定。

本节只说明本轮文档动作；代码迁移、完整测试和配置的 R0 结果见[本地验收记录](../tasks/R0_ACCEPTANCE_2026-10-20.md)。前述“未物理迁移”的陈述保留为报告初版的历史状态，不再代表现状。
