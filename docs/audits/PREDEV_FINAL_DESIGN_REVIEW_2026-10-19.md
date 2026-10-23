# 正式业务开发前最终设计决策记录

- 日期：2026-10-19，Asia/Shanghai
- 状态：**产品与架构方向已由用户确认；P-00 离线配置已完成，业务代码与付费验收未授权**
- 当前产品验收：**No-Go**。r12 的 18 次真实尝试及三次独立 UI 任务无合格完整报告；历史离线测试不等于真实研究成功。本轮不改写原始 SQLite、r12、旧协议或 `browser-use/`。
- 权威：[SPEC](../../SPEC.md)、[PLANS](../../PLANS.md)、[契约](../contracts/CURRENT_CONTRACTS.md)、[`current-2` 协议](../evaluation/CURRENT_EVAL_PROTOCOL.json)、[ADR-0005](../design/adr/0005-windows-worker-wsl-postgres.md)。旧 `current-1` [原字节归档](../evaluation/archive/CURRENT_EVAL_PROTOCOL_current-1.json)，SHA-256 `542320be31bd512ed39ed77fa73475d3301cbd9e1f70d9fdd1a4a6e856e2098e`。

## 已确认的需求与非目标

B01 开源工具选型是首个面试演示：提交公开研究目标、浏览器与 GitHub 工具执行、来源与事实核验、事实 ID 支持的条件化建议、失败/取消/历史、固定评测、调用轨迹诊断和同口径复测。B/G/O 九题题面和字段保持冻结；正式 15 次要求 B01–B03 每题 ≥2/3 full、G01–G03 合计 ≥2/3、O01–O03 3/3。应用中的 `completed/full` 是机器准入事实支持的候选完整报告，界面标明待人工核实；正式评测的 full 还须逐结论人工核实官方来源。每份候选完整报告均含条件化建议；证据不足写明缺口并标 `partial`。

五账户含管理员，首版须有完整管理员界面；管理员不默认阅读成员任务。逐对象 API/SSE/取消隔离、两运行八排队模拟、一次安全恢复和一次可断开介质加密备份及独立目录恢复均为硬门槛。局域网发布、真实五人并发、登录后资料、外部写入、模板编辑、Markdown 导出、完整录屏/HAR 留存均不纳入首版成果。

## 架构与备选

Windows 运行 API、独立 Worker、现有 AgentLoop、浏览器和本机启动器；WSL 运行 PostgreSQL。应用表拥有任务、授权、租约、调用账本、事实、报告、费用和已提交事件，SSE 从数据库补读。短事务认领和 fencing token 裁决迟到写入；调用前写 `started`，返回后写 `completed`/`failed`，崩溃空档标 `unknown_outcome`。Worker 自动重启，同一任务最多重新认领一次；先读已提交事实、重新观察，未知结果的外部动作不盲重放。数据库失联时不确认未落库提交/取消，恢复后对账。取消请求先持久确认，唯一终态异步可见。

单进程/SQLite 已被用户的首版 Worker/PostgreSQL 选择取代，P-01 不自动回退。LangGraph 只有在 AgentLoop 持久状态或恢复故障可复现、局部修复不足且限时探针有益时才另行决定。Redis、消息代理和平台规模的架构在本机作品中缺少可证实收益。[PostgreSQL 行锁](https://www.postgresql.org/docs/current/sql-select.html)、[WSL 网络](https://learn.microsoft.com/windows/wsl/networking)与[LangGraph 持久化](https://github.com/langchain-ai/docs/blob/main/src/oss/langgraph/persistence.mdx)是机制依据，不是本机通过证据。

## 阶段与停线

| 阶段 | 必备产物与验收 | 真实费用上限；停线 |
| --- | --- | --- |
| P-00 配置 | 权威文档、ADR、协议归档、离线校验器及负例、CI/README/Skill 同口径；固定题和历史哈希不变 | 0 元；配置通过不等于业务通过 |
| P-01 第 1–2 周 | 先只读分类 r12；调用账本和 10 假任务两运行八排队，满额 429 不落库；无丢失/双认领/OOM，API p95 ≤1 秒、已提交 SSE 补读 ≤2 秒，Worker ≤60 秒重启、任务 ≤120 秒重认领或终结；数据库失联演练、CPU/内存峰值 | 0 元；失败先暂停 pilot，限时按证据修一个必要组件，影响研究/正式阶段则 No-Go 并重定范围 |
| P-02 第 3–6 周 | 在质量定点改动前同版 B01–B03 各一次 pilot；事实机器准入与人工官方核实分层、报告与条件化建议、逐调用诊断 | ≤49 元且另获付费授权；系统故障或费用不可界定即暂停，保留已发生尝试 |
| P-03 第 7–9 周 | 完整管理员界面和隔离、恢复与加密离线独立恢复；至少一例失败调用→可证伪根因→定点改动→离线回归→真实复查 | ≤30 元且另获付费授权；任一硬门槛失败即 No-Go |
| P-04 第 10–12 周 | 冻结代码/模型/预算/评分/环境，正式 15 次全部保留，逐结论人工官方核源、full/冲突隔时二次复核、UI/API/持久层/SSE 对账 | ≤200 元，机动 ≤20 元；总额严格低于 300 元，未知费用、预算不足或门槛失败即 No-Go |

pilot 与正式首轮只作条件可比的描述性配对；不作因果改善或总体胜率主张。发布研究题的“最新”按每次运行开始时官方页面核验，记录来源漂移，不换题或补跑替换。正式批次中修复问题须另起完整批次。

## 外部一手资料与适用范围

- [SWE-agent 轨迹查看器](https://github.com/SWE-agent/SWE-agent/blob/main/docs/usage/inspector.md)与 [v1.1.0 release](https://github.com/SWE-agent/SWE-agent/releases)：借鉴逐步诊断；项目任务领域不同，成绩不转移。
- [Skyvern 调试制品](https://github.com/Skyvern-AI/skyvern/blob/main/docs/developers/debugging/using-artifacts.mdx)与 [v1.0.56 release](https://github.com/Skyvern-AI/skyvern/releases)：借鉴状态/时间线，保留最小公开证据而不复制重型制品体系。
- [browser-use benchmark v2.1.1](https://github.com/browser-use/benchmark/releases/tag/v2.1.1)：借鉴题集/修订和轨迹锁定；其分数不属于本项目。
- [OpenHands SDK](https://github.com/OpenHands/software-agent-sdk/blob/main/README.md)：借鉴运行时/API/客户端边界，不搬入多仓库平台。
- AI coding 工作流查看固定提交：[Codex AGENTS](https://github.com/openai/codex/blob/8c076942cb70fba8e5c4732c23f1faabc4aed484/docs/agents_md.md)、[Gemini CLI 指令](https://github.com/google-gemini/gemini-cli/blob/c7b920717fad72229c788aa8efc646afac7a2965/GEMINI.md)、[Aider 仓库映射](https://github.com/Aider-AI/aider/blob/5dc9490bb35f9729ef2c95d00a19ccd30c26339c/aider/website/docs/repomap.md)。只借鉴稳定入口、按需上下文和验证路径；star 仅用于发现候选。

## 证据等级、待验证与授权

离线测试可证明代码路径；本机 UI/API/持久层/SSE 对账支持功能可用；逐结论人工官方核源和完整报告支持真实研究成功；十假任务及资源记录只支持容量模拟；故障注入和调用账本支持安全恢复；同版轨迹、针对性改动与真实复查支持观察到的优化变化。校验器只检查声明、引用和文件哈希，不能自行判断官方身份或事实真假。

WSL 发行版/PostgreSQL 实际状态、Windows 到 WSL 的连接、本机绑定、加密工具、16 GB 资源、真实费用与研究质量均未验证。下一步业务代码须按 P-01 Task ID 获授权；依赖安装、每次付费任务、部署、Git 提交/推送/PR 分别授权。未实测数字不得写入简历成果。

## P-00 离线验证记录（2026-10-20）

- `.venv\Scripts\python.exe -m pytest -q --basetemp=.pytest_cache\p00-full-20261020-final`：432 passed，1 deselected；pytest 默认系统临时目录曾因权限拒绝不可用，改用工作区内临时目录后完成。
- `.venv\Scripts\python.exe scripts\validate_project.py`：通过；输出明确提示真实模型效果和来源真实性未验证。
- `.venv\Scripts\python.exe -m ruff check adaptive_agent backend benchmark scripts tests`：通过；`ruff format --check`：78 个文件符合格式。
- `git diff --check`：退出码 0；现有已跟踪文件有 LF/CRLF 提示，无空白错误。旧 `current-1` 归档与源文件 SHA-256 一致；新旧协议的九题、pilot 和正式尝试数组逐项相同。
- 本轮未运行付费真实任务、未安装依赖、未部署，也未触碰原始 SQLite、r12 记录或 `browser-use/`。P-00 离线配置通过；P-01 和产品放行仍为 No-Go。

## 开工前补充（2026-10-20）

[P-01 开工任务包](../tasks/PREDEV_P01_START_PACKAGE_2026-10-20.md)列出逐项实施边界、假任务测量口径和环境关口；[r12 只读症状清单](PREDEV_R12_SYMPTOM_INVENTORY_2026-10-20.md)已将 18 次真实失败及三次 UI 失败归类，未推断调用级根因。只读 WSL 探针确认 Ubuntu 24.04.1 存在，PostgreSQL 16 服务端/客户端尚未安装；Windows↔WSL 连接、CPU/内存峰值和备份恢复仍未验证。安装和本机隔离数据库配置依仓库规则等待单独授权。更新文档后再次运行校验器通过、校验器单测 19 passed；原始 SQLite 与 r12 汇总文件哈希未变化。此补充不改变 P-00 离线通过、产品 No-Go 的区分。

随后用户单独授权依赖安装与本机连接探针：[环境配置记录](PREDEV_ENV_SETUP_2026-10-20.md)记载 Ubuntu 官方源 PostgreSQL 16.15、Windows `asyncpg`/Alembic 锁定、隔离库与最小权限账户。Windows 回环连接在 WSL 前台保活期间实测成功；WSL 无前台进程时自动退出导致独立连接失败，P-01 启动器须维持其生命周期。环境准备不等于 Worker/容量/恢复验收通过。

环境变更后的离线复核：锁文件一致，Python 432 passed、1 deselected，Ruff/格式/项目校验器通过；前端类型检查、20 个测试和构建通过。数据库只有空开发库与角色，没有新应用表或正式任务。开发前设计、依赖与连接探针已准备；业务仍须 P-01 的具体授权和两周关口证据。
