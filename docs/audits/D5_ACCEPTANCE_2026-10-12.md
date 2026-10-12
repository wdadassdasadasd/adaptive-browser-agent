# D5 runtime, SQLite and public API acceptance — 2026-10-12

## 本次独立复核（D5 必需门禁通过）

本节从 `f8614fff160d216262da236bf5d894c23ca60c2d` 的当前未提交 D5 diff
重新取证；下方结论只引用本轮输出，旧记录中的通过结论不作为凭证。
当前分支为 `main`，上游 `origin/main`，暂存区为空；主仓库有 14 个已修改的
跟踪文件和 5 个未跟踪文件。普通 `git status` 因 `browser-use` 子模块元数据
权限失败，本轮使用 `git -c submodule.recurse=false status --ignore-submodules=all`
清点主仓库，不触碰现有 SQLite 数据或凭据文件。

| 需求 | 可观察的通过条件 | 代码位置 | 测试或手工步骤 | 实际结果 | 证据位置 | 结论 |
| --- | --- | --- | --- | --- | --- | --- |
| T11-1 并发排队 | 同时至多两项运行，第三项等待槽位 | `TaskManager._run` | `test_third_task_waits_and_queued_cancel_never_starts`；本地三任务路径 | 两项 running、第三项 queued | 本节“本地用户路径” | 通过 |
| T11-2 排队取消 | 排队任务不进入 Agent，终态仅一次 | `TaskManager.cancel`、`ResearchService.cancel` | 排队时取消并查询轨迹 | queued→cancelled，终态轨迹一条 | 本节“本地用户路径”；`test_queued_and_running_cancel_are_idempotent` | 通过 |
| T11-3 运行中取消 | 软取消收敛为 cancelled，重复取消无改写 | `ResearchService.cancel`、`AgentLoop.run` | 运行时取消并重复请求 | 两次取消均 200/true，终态轨迹一条 | 本节“本地用户路径”；`test_cancel_racing_with_completed_terminal_returns_false` | 通过 |
| T11-4 异常释放 | 执行异常终结任务并释放槽位 | `TaskManager._run`、`ResearchService._execute` | `test_unhandled_agent_error_persists_failure_and_frees_slot` | 连续两项故障任务均启动并以 `failed/execution_error` 终结 | 本节“自动化门禁” | 通过 |
| T11-5 资源隔离 | 每任务独立 Agent/工具资源，关闭互不影响 | `ResearchService._new_agent` | `test_parallel_agents_keep_resources_and_cancellation_isolated` | 两个 Agent 实例与 task ID 一一对应，取消一项时另一项继续运行 | 本节“自动化门禁” | 通过 |
| T11-6 关闭清理 | 关闭后无活跃任务或遗留订阅者；运行中任务按中断证据恢复 | `TaskManager.shutdown`、`ResearchService.shutdown`、应用 lifespan | 资源隔离退出检查；`test_shutdown_finalizes_running_task_as_server_restart` | Agent 均关闭，活跃任务及订阅数均为 0；重启后 failed/server_restart，终态一条 | 本节“修复与回归” | 通过 |
| T11-7 订阅者 | 多订阅者互不干扰；队列有界且慢客户端不阻塞任务 | `TaskManager.subscribe/publish` | `test_subscribers_receive_same_event_without_slow_client_blocking`、`test_slow_subscriber_catches_up_and_disconnect_is_isolated` | 队列容量 1；单端断开不影响另一端；慢端从 SQLite 追上 | 本节“自动化门禁” | 通过 |
| T12-1 持久化 | 任务、步骤、事实、轨迹均可从新会话读取 | `PersistenceService.record_event` | `test_full_agent_loop_rebuilds_sourced_report_via_api`、`test_repeated_evidence_is_stored_only_once` | 完成任务重启后保留 5 条轨迹、事实来源及报告 | 本节“本地用户路径” | 通过 |
| T12-2 终态原子性 | 终态和唯一 `task_finished` 同事务提交；内存状态只接受已成功持久化事件 | `PersistenceService.record_event`、`AgentLoop.emit` | `test_terminal_status_and_trace_are_atomic`、`test_cancel_wins_over_start_and_terminal_event_is_unique`、`test_rejected_step_does_not_put_unstored_facts_in_report` | 竞争下仅一条终态轨迹；拒收大步骤后最终报告无未落库事实 | 本节“修复与回归” | 通过 |
| T12-3 回滚 | 注入写入失败后，终态和终结轨迹均未提交 | `PersistenceService.record_event` | `test_terminal_status_and_trace_are_atomic` | 注入轨迹写入失败后仍为 queued，只有排队轨迹 | 本节“自动化门禁” | 通过 |
| T12-4 事实去重 | 相同来源及内容的事实不重复落库 | `PersistenceService.record_event/save_fact` | `test_repeated_evidence_is_stored_only_once`、`test_direct_fact_saves_deduplicate_same_evidence` | 事件路径和直接保存路径均只保留首条事实 | 本节“修复与回归” | 通过 |
| T12-5 重建 | 轨迹有序；报告的结论有已存事实和来源支撑，大报告不丢失 | `PersistenceService.report_for_task` | 完成任务重启后查询；`test_restart_report_names_unfinished_subgoal`；`test_large_sourced_terminal_report_is_not_lost` | 同 5 条有序轨迹，报告来源为所存 GitHub URL；大于 64 KB 的带来源报告完整恢复 | 本节“修复与回归” | 通过 |
| T12-6 重启恢复 | 未完成任务重启后终结且不再执行，终态唯一 | `PersistenceService.finalize_unfinished` | `test_restart_finalizes_unfinished_task_once` | 首次恢复 1、再次 0；状态 failed/server_restart，终态一条 | 本节“自动化门禁” | 通过 |
| T12-7 旧库保护 | 不兼容旧表明确报错，原数据和结构不变 | `initialize_schema` | 原库只读哈希、旧库副本启动；`test_incompatible_existing_table_is_reported_without_deletion` | 明确报 4 个缺列；原件与副本哈希均不变 | 本节“旧库保护” | 通过 |
| T13-1 六路由与状态码 | 六条固定路由给出 202/200/404/422/503，终态详情自洽 | `backend/api/research.py` | 真实本地 HTTP 客户端逐路由请求；`test_response_status_matches_terminal_trace_during_completion` | 202/200/404/422/503 均按契约返回；完成竞争下 status 与终态字段一致 | 本节“本地用户路径”；“修复与回归” | 通过 |
| T13-2 缺密钥 | 503 且无新增任务或排队轨迹 | `ResearchService.create` | 无密钥本地服务 POST 后查询列表 | POST 503，列表 200 且长度 0 | 本节“本地用户路径” | 通过 |
| T13-3 取消幂等 | 排队、运行中、已取消和其他终态响应符合契约 | `ResearchService.cancel` | 本地四次取消；终态竞态回归测试 | 取消均 200；已完成竞态返回 false，未改写终态 | 本节“修复与回归” | 通过 |
| T13-4 SSE 接续 | 已持久化回放接实时通知，ID 有序且不重复 | `stream_research_events` | `test_replay_joins_live_events_and_reconnect_skips_seen_id`；本地 SSE | 完成任务 5 个 ID 匹配轨迹；运行任务实时事件无重复 | 本节“本地用户路径” | 通过 |
| T13-5 重连 | `Last-Event-ID` 只续传后续事件，未知 ID 为 422 | `stream_research_events` | HTTP/SSE 断开后重连 | 断在 started；只续传 cancel_requested、task_finished；未知 ID 为 422 | 本节“本地用户路径” | 通过 |
| T13-6 多订阅与终结 | 慢客户端不阻塞 Agent，断开不取消任务，终结后关闭 | `stream_research_events` | `test_slow_subscriber_catches_up_and_disconnect_is_isolated`、`test_http_sse_disconnect_keeps_database_usable` | 断开后数据库仍可查询；另一订阅者至终态关闭，连接池无 ERROR | 本节“修复与回归” | 通过 |
| T13-7 凭据隔离 | 凭据不出现在日志、轨迹、SSE 或报告 | `PersistenceService._safe_event` | `test_sse_and_report_redact_configured_credentials` | 两类哨兵值均未出现在四种输出 | 本节“自动化门禁” | 通过 |

### 修复与回归

- `test_cancel_racing_with_completed_terminal_returns_false` 先以 `True is False`
  失败：取消请求读到旧 running 快照后，任务已提交 completed 但协程尚未退出。
  服务在发出取消信号后复查持久化终态；该测试及既有取消测试随后通过。
- `test_direct_fact_saves_deduplicate_same_evidence` 先因第二次直接保存产生
  `fact-duplicate` 失败。直接保存入口现按规范化来源与内容返回已有事实；
  `test_persistence.py` 与 API 测试合计 16 通过。
- 真实 HTTP 的 `test_http_sse_disconnect_keeps_database_usable` 先以 500 失败，
  日志显示断线取消了 SQLite 查询并使连接池复用失效。SSE 短数据库读取使用
  AnyIO 屏蔽取消，原有连接池配置下该测试通过且无连接池 ERROR。AnyIO 已
  声明为直接依赖，离线锁文件已更新。
- 新增独立 Agent 资源隔离、意外异常终结及凭据哨兵测试；其第一次执行即
  通过，作为原先缺口的覆盖，不冒称“先红后绿”。
- 独立只读审查指出三项触发条件：超过 64 KB 的终态报告、服务关闭中的取消、
  终态落在状态与轨迹两次读取之间。对应三个回归测试首次合跑为 **3 failed**：
  分别抛出 `Agent trace exceeds the storage limit`、错误的 `cancelled` 状态、
  `running` 与 `full` 同时出现。终态事件保留完整报告；服务关闭时不再把
  关闭触发的取消写成用户取消，随后按已存证据恢复；API 响应从同一终态轨迹
  派生状态和报告。三项修复后同一测试 **3 passed**。审查的最终复核见下节。
- 第二轮只读审查又指出：`step_evaluated` 超限拒收时，AgentLoop 已提前把事实
  归入内存状态。按单步工具内容上限构造六条同源长证据后，回归测试首次以
  “报告存在未落库来源”失败。`emit` 现先校验并等待事件持久化成功，再接纳
  下一状态与事件；该测试加 D4 AgentLoop 测试合计 **34 passed**。最后一次
  全量门禁和最终只读复核仍以下方新输出为准。

### 自动化门禁

以下为本轮实际命令与退出码；离线全量测试显式排除浏览器标记用例，浏览器
烟测另行选中执行。最初受限沙箱中的 `uv` 查询解释器失败（退出 2），改用
获准执行环境后从头运行；不能把该失败记作测试通过。

| 命令 | 退出码 | 本轮输出 |
| --- | ---: | --- |
| `uv run --offline --locked pytest -q -p no:cacheprovider --basetemp .pytest_cache/tmp tests/unit/test_task_manager.py tests/integration/test_database.py tests/integration/test_persistence.py tests/integration/test_research_api.py tests/integration/test_sse.py` | 0 | 33 passed |
| `uv run --offline --locked pytest -q -p no:cacheprovider --basetemp .pytest_cache/tmp tests/integration/test_agent_loop.py tests/integration/test_d2_component_flow.py tests/integration/test_d3_component_flow.py tests/unit` | 0 | 264 passed |
| `uv run --isolated --python 3.12 --offline --locked pytest -q -p no:cacheprovider --basetemp .pytest_cache/tmp` | 0 | 294 passed, 1 deselected |
| `uv run --isolated --python 3.13 --offline --locked pytest -q -p no:cacheprovider --basetemp .pytest_cache/tmp` | 0 | 294 passed, 1 deselected |
| `uv run --offline --locked pytest -q -m browser -p no:cacheprovider --basetemp .pytest_cache/tmp tests/smoke/test_browser_use_adapter.py` | 0 | 1 passed |
| `uv run --offline --locked ruff check adaptive_agent backend benchmark tests` | 0 | All checks passed |
| `uv run --offline --locked ruff format --check adaptive_agent backend benchmark tests` | 0 | 73 files already formatted；之前三次退出 1 均为测试文件局部换行，修正后重验通过 |
| `uv run --offline --locked python -m compileall -q adaptive_agent backend benchmark tests` | 0 | 无错误输出 |
| `uv lock --check --offline` | 0 | Resolved 282 packages |
| `uv build --offline --wheel` | 0 | 生成 `dist/adaptive_browser_agent-0.1.0-py3-none-any.whl` |

### 本地用户路径（受控提供方；手工用户路径验收）

真实 Uvicorn 监听 `127.0.0.1`，HTTPX 通过网络套接字调用六路由，使用
`.pytest_cache/d5-recheck/` 下独立 SQLite 文件。可复跑的忽略脚本与原始输出
分别为 `system_probe.py`、`system_probe_final.log`；本次命令
`uv run --offline --locked python .pytest_cache/d5-recheck/system_probe.py`
退出 0。这里的提供方、GitHub 工具和浏览器均为受控模拟，不能称作真实研究成功。

| 用户动作 | 实际响应及可核对结果 |
| --- | --- |
| 创建→状态→来源报告 | POST 202，列表/详情/轨迹 200；任务 `d7f43fdc-dc82-4e5c-9612-70201c078761` completed；报告来源 `https://api.github.com/repos/fastapi/fastapi`，与模拟工具观察的事实相符 |
| SSE 回放 | 200；`task_queued`→`task_started`→`subgoals_initialized`→`step_evaluated`→`task_finished`；ID 依次为 `024c1fa3-5fe0-4ca8-83ff-14e4a8560717`、`d8f0038a-03d9-4715-bfc3-b9c5012b7ecf`、`c027da2c-7697-4ae6-9424-1b2bd17a2f82`、`e6131008-e259-43e1-9635-367aa75f8c58`、`781909be-b61a-4856-bcf8-4ef24f8cdcd7`，与轨迹一一对应 |
| 排队与取消 | 三任务依次观察到 running/running/queued，最终均 cancelled；四次取消及重复取消均为 200，各仅一条 `task_finished` |
| 实时事件、断线与重连 | 实时流从排队/启动接到取消/终结；客户端在 `7e1e21d3-06b2-48df-8e93-320733512252` 断开，`Last-Event-ID` 只续传 `faaf5155-3734-4774-b67c-e715705f29b7`、`fd7ca2ef-15c4-4e69-a435-bff9b256a5f1`，无重复；未知游标为 422 |
| 重启查询 | 服务关闭并重启后，详情和轨迹均 200；仍 completed，5 条同 ID 轨迹，报告保留相同来源 |
| 错误路径 | 无密钥 POST 503 且列表为空；空目标 422；未知任务的详情、轨迹、SSE、取消均 404 |

以普通使用者视角，状态、停止原因、事件顺序和报告来源能够对应理解；此处
是本轮手工用户路径验收，不是业务方签字。断线后原有任务继续执行；服务和
客户端均已停止。慢客户端及多订阅者由上述定向测试覆盖。

### 旧库保护与真实提供方边界

只读原件 `data/adaptive_agent.db` 的 SHA-256 为
`1cf908a6f9e83985548ba7bd0753a204e6d8ccbaf70ac34daa9d3152ecbd0064`。
`legacy_probe.py` 只在忽略的副本上尝试初始化，退出 0，明确报
`research_fact` 缺少 `evidence, source_title, subject, subject_kind`；原件和
副本的哈希在检查前后均不变。没有迁移或清空旧库。

现有非空 DeepSeek 凭据通过忽略的 `auth_probe.py` 发起一次有界真实请求，
命令退出 0，`deepseek-flash` 返回非空内容，提示/完成用量为 38/14 token，
HTTP 客户端已关闭；脚本不打印密钥和响应内容。这只验证认证提供方链路。
本轮未运行完整的真实提供方研究任务；历史记录中的失败任务不替代本轮
业务通过凭证。D6 前端、D7 公开任务与基准测试、远端 CI 均不属于 D5
放行条件，仍为未验证。

### 独立只读审查与放行

三轮原生 Codex CLI 审查均使用
`codex -s read-only -a never --strict-config review --uncommitted`，启动日志
实际显示 `sandbox: read-only`、`approval: never`；审查范围为当前 16 个已跟踪
修改路径和 5 个未跟踪 D5 路径。审查日志在忽略的
`.pytest_cache/d5-recheck/review.log`、`review_final.log`、
`review_final3.log`；未使用子代理的可写权限配置冒充只读隔离。

第一轮退出 0，给出三个有文件、行号和触发条件的发现：
`backend/services/persistence.py:59-60` 的大终态报告丢失、
`backend/services/research.py:164-166` 的关闭误记用户取消、
`backend/api/research.py:26-31` 的状态与终态详情矛盾。
第二轮退出 0，指出 `adaptive_agent/agent_loop.py:165-168` 中拒收步骤仍进入
内存事实的问题。四项均由主执行者以上述失败测试独立复现，再做局部修复，
受影响及全量门禁随后重跑。第三轮在最终代码 diff 上退出 0，报告
`I found no actionable bugs in the staged, unstaged, or untracked changes`，
并明确它没有重跑测试。审查自身的只读模式和范围均已核实，阻断发现已关闭。

**D5 总结论：通过。** T11–T13 必需条件、两版 Python 全量离线回归、本地
HTTP/SSE 用户路径、独立只读审查均有本轮可复核证据；未发现尚存的数据丢失、
凭据泄露、重复终态或无法收敛的并发问题。模拟提供方的本地用户路径与真实
DeepSeek 单次认证检查分别记录；本轮未验证真实提供方完整研究，D6、D7 和
远端 CI 不属于本次放行条件。

## 历史记录（以下内容不作为本轮通过凭证）

## Decision and scope

**T11 Pass; T12 Pass; T13 Pass** for the V1 D5 offline and controlled local
HTTP scope. These decisions use the tests and observations below, not the D5
calendar or 17-hour estimate. A later authenticated DeepSeek check is recorded
below: authentication passed, while its first full research task failed at the
token budget. D6 Vue UI, D7 public-task acceptance and benchmark work are
outside this decision.

The starting checkout was `main` at
`f8614fff160d216262da236bf5d894c23ca60c2d` with a clean project working
tree. No unrelated project changes were found. No commit, push, PR, external
write or deployment was performed. The existing `data/adaptive_agent.db` was
not modified: its `research_fact` table lacks required columns, including
`source_title` and `evidence`. Startup now reports incompatible columns before
`create_all`; it does not attempt a migration or erase that database. Local
HTTP verification used a separate `.pytest_cache/d5-live.db` SQLite file.

| Requirement | Implementation | Test and observed evidence |
| --- | --- | --- |
| T11: two active tasks; third queued; queued/running cancel; isolated cleanup and subscribers | `adaptive_agent/runtime/task_manager.py`, per-task `AgentLoop` and tools in `backend/services/research.py` | Async event tests cover waiting, both cancellation points, failure releasing a slot, shutdown and capacity-one subscriber queues. Local HTTP showed two running and one queued, then one terminal event per cancelled task. |
| T12: durable task/step/fact/trace; atomic terminal status and event; restart reconstruction | `backend/services/persistence.py`, `backend/db/models.py`, `backend/db/session.py` | SQLite tests inject a terminal write failure and find neither half-write, race two terminal attempts, reject a standalone terminal trace, deduplicate repeated evidence, rebuild sourced reports and finalize unfinished rows after restart. The local service reload returned its report and exactly one terminal trace. |
| T13: six routes, status codes and replay/live SSE | `backend/main.py`, `backend/api/research.py`, `backend/schemas/research.py`, `backend/services/research.py`; minimal `AgentLoop` event callback | API/SSE tests cover 202/200/404/422/503, absent key with no row, idempotent cancellation, persisted replay joined to live events, `Last-Event-ID`, multiple and slow subscribers, disconnect and terminal close. Local HTTP exercised all six routes. |

The event callback awaits persistence before publishing. SSE subscribes before
reading the stored rows, advances by trace row ID, and rechecks storage before
closing on a terminal status. Each frame uses the stored `event_id`. Subscriber
notification queues have capacity one; a slow client catches up from SQLite.
Trace payloads are size bounded and configured credential values are redacted
from stored messages, SSE payloads and reconstructed reports. A supplied goal
is user content and remains part of the task record.

## Test sequence and final checks

Failure-first tests were observed for missing API wiring, terminal atomicity,
restart report fields, repeated facts, unfinished subgoals, secret-bearing
messages, standalone terminal traces and the replay/live terminal race. The
corresponding assertions passed after the fixes. The penultimate full Python
3.12 run had 1 SSE race failure and 283 passes; a targeted SSE rerun passed,
then both full suites passed. No failed test was skipped or weakened.

The restricted sandbox could not execute `uv` due `os error 5`; the following
final commands ran in the approved executable environment. `--basetemp` keeps
temporary SQLite files under this workspace. Exit codes are from the final
run after code fixes.

| Actual command | Exit | Result |
| --- | ---: | --- |
| `uv run --offline --locked pytest -q -p no:cacheprovider --basetemp .pytest_cache/tmp tests/unit/test_task_manager.py tests/integration/test_database.py tests/integration/test_persistence.py tests/integration/test_research_api.py tests/integration/test_sse.py` | 0 | 23 passed in 3.16s |
| `uv run --offline --locked pytest -q -p no:cacheprovider --basetemp .pytest_cache/tmp tests/integration/test_agent_loop.py tests/unit/test_reporter.py tests/unit/test_state_reducer.py tests/unit/test_deepseek.py tests/unit/test_planner.py tests/unit/test_tool_router.py tests/unit/test_github_tool.py tests/unit/test_evaluator.py tests/unit/test_context_manager.py tests/integration/test_d2_component_flow.py tests/integration/test_d3_component_flow.py tests/unit/test_goal_count.py tests/unit/test_loop_usage.py` | 0 | 197 passed in 2.06s; D4 and dependencies |
| `uv run --isolated --python 3.12 --offline --locked pytest -q -p no:cacheprovider --basetemp .pytest_cache/tmp` | 0 | 284 passed, 1 browser-marked test deselected in 8.78s |
| `uv run --isolated --python 3.13 --offline --locked pytest -q -p no:cacheprovider --basetemp .pytest_cache/tmp` | 0 | 284 passed, 1 browser-marked test deselected in 11.62s |
| `.venv\Scripts\ruff.exe check adaptive_agent backend benchmark tests` | 0 | All checks passed |
| `.venv\Scripts\ruff.exe format --check adaptive_agent backend benchmark tests` | 0 | 73 files already formatted |
| `.venv\Scripts\python.exe -m compileall -q adaptive_agent backend benchmark tests` | 0 | No errors |
| `uv lock --check --offline` | 0 | Resolved 282 packages in 3ms |
| `uv build --offline --wheel` | 0 | Built `dist/adaptive_browser_agent-0.1.0-py3-none-any.whl` |
| `git -c submodule.recurse=false diff --check --ignore-submodules=all` | 0 | No whitespace errors; Git printed LF-to-CRLF advisories |

The explicit browser smoke was not rerun in this D5 pass; the offline suites
deselected it. D4's prior Chromium and public GitHub evidence is recorded in
`docs/audits/D4_ACCEPTANCE_2026-10-11.md`. Type checking and CI are not
configured as D5 gates; no remote CI outcome is claimed.

## Local service and user-path acceptance

A local Uvicorn process used the FastAPI lifespan, an isolated SQLite database,
and a controlled fake provider/tool chain. HTTP requests were made as a normal
API client, not by calling the service object directly. The controlled source
was the public `https://api.github.com/repos/fastapi/fastapi` URL; the model
response was fake and no authenticated DeepSeek request was made. The local
server was stopped and restarted against the same database.

| User scenario and expected behavior | Actual HTTP/SQLite observation | Decision |
| --- | --- | --- |
| Create and see progress | `POST /api/research` returned 202 with a queued task ID. `GET /api/research/{id}` returned 200 and then `completed`. `GET /api/research/{id}/events` returned 200 with `task_queued`, `task_started`, `subgoals_initialized`, `step_evaluated`, `task_finished` in that order; event IDs were unique. | Pass in controlled local service |
| Trace and sourced result | `GET /api/research/{id}/traces` returned 200 and 5 events. Detail returned a report citing the same public GitHub URL; `GET /api/research` returned 200 and included the task ID. | Pass |
| Cancel queued and running work | Three creates showed `running`, `running`, `queued`. Each cancel returned 200; all ended `cancelled`, each with one terminal trace. Repeating cancel returned the same terminal response. | Pass |
| Reconnect and restart | SSE tests passed replay/live and `Last-Event-ID` continuation. After Uvicorn restart, detail and trace again returned 200; report retained one source, trace retained 5 rows and exactly one `task_finished`. | Pass |
| Disconnect and slow client | Integration tests showed one subscriber removal does not remove another; a delayed client catches up from stored rows without blocking the Agent. | Pass in controlled integration test |

The completed local task ID was
`564b8b7d-324d-4ec3-bbf9-f2bcd7403521`. The Uvicorn processes were
stopped after verification. Lifespan shutdown and AgentLoop cleanup are covered
by tests; there was no separate operating-system handle census. The D5 human
business check was through HTTP/SSE because the frontend is a D6 task.

## Independent read-only review

A separate Codex CLI review ran against the uncommitted D5 change scope with
`codex -s read-only -a never --strict-config review --uncommitted`. Its startup
reported `sandbox: read-only`, and the review exited 0. It produced these
file-and-line findings; the root agent checked each against the accepted D5
contract before changing code.

| Finding | Resolution and regression evidence |
| --- | --- |
| `backend/db/session.py:53-60`: existing old database cannot start without migration | Accepted as an intentional compatibility boundary. The user's D5 plan explicitly requires a clear error and preservation of the old database, not an automatic migration. `test_database.py` checks the error and retained data; the old file was not rewritten. |
| `backend/services/persistence.py:201-204`: repeated facts might be inserted despite reducer deduplication, leading to duplicate or conflicting reports | Reproduced with a failing `test_repeated_evidence_is_stored_only_once`; fixed by normalized source/content deduplication before insertion. Test and full suites pass. |
| `backend/services/persistence.py:325-331`: rebuilt reports omit persisted subgoal progress | Reproduced with a failing `test_restart_report_names_unfinished_subgoal`; fixed reconstruction from initialization and evaluated-step traces. Test and full suites pass. |

Additional local failure-first checks closed the SSE terminal race, rejected
terminal event writes outside the atomic status transaction, and redacted a
secret sentinel in persisted terminal messages. No reviewer finding remains
unresolved within the agreed D5 scope.

## Remaining limits and Git handoff

Successful public browser research through the new API, frontend UX, remote
CI and D7 representative-task acceptance remain unverified. Startup with the
existing incompatible default SQLite file will
fail clearly until a separately planned migration or new database is supplied;
this is the agreed data-preservation behavior. Controlled local tests support
the D5 contracts but do not prove production network or browser behavior.

The closing Git check showed `## main...origin/main`, 14 modified tracked
files and 5 untracked D5 files (the service, three integration test files and
this audit). No file was staged, committed or pushed. `git diff --check`
returned 0; the read-only check of the old SQLite file found 0 rows in each
research table and its original fact columns unchanged.

## Follow-up: real DeepSeek authentication and API task

At the user's request, the existing `browser-use/.env` was checked by key name
and the nonempty `DEEPSEEK_API_KEY` entry was copied to the root `.env` without
printing its value. The root file also selects isolated
`data/d5-auth-check.db`. `git check-ignore -v .env` returned exit 0 with
`.gitignore:1:.env`; the credential file does not appear in Git status.

| Actual check | Exit | Observed result |
| --- | ---: | --- |
| `uv run --offline --locked python .pytest_cache/d5_auth_probe.py` | 0 | Real `DeepSeekClient.complete` authenticated successfully with `deepseek-flash`; response length 2, prompt usage 41 tokens, completion usage 17; owned HTTP client closed. The ignored probe printed no credential or response body. |
| Local Uvicorn on `127.0.0.1:8765` plus `uv run --offline --locked python .pytest_cache/d5_live_api_probe.py` | 0 | `POST /api/research` 202; task `e53be18f-1a59-4188-8001-b7923f6d01ff` reached `failed/none/token_budget` after four evaluated steps. Traces 200: eight ordered events with one `task_finished`; SSE 200 returned the same unique event IDs. Report existed with zero sourced facts. This is an authenticated provider/API execution, **not** a successful business result. |
| Restart local Uvicorn; `GET /api/research/{id}` and `/traces` | 0 | Both returned 200. Status remained `failed/token_budget`, report remained present, eight trace rows and one terminal event reloaded from SQLite. |

The real run used the V1 40,000-token task budget. Its persisted records have
four `step_evaluated` events and no facts; the terminal reason is
`token_budget`. Browser shutdown logged a reset and owned-session cleanup.
The provider credential and raw provider output were not placed in this audit.
An exact-byte scan of the isolated SQLite database and any WAL/SHM files found
no credential value. The server was stopped after the restart check. A successful sourced research
result with the real provider remains an open D7 acceptance item; this check
proves live authentication and the failure/reporting path only.
