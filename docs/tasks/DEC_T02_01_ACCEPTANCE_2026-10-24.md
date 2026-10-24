# DEC-T02-01：提交契约与幂等的首个离线验收切片

日期：2026-10-24（Asia/Shanghai）。实施状态：`IMPLEMENTED`（仅测试及证据）；本次验收：`DONE（离线切片）`。DEC-T02／DEC-AC-01 整体仍为 `PARTIAL`，P-02 与产品仍为 No-Go。

| 任务模板字段 | 本切片记录 |
| --- | --- |
| Task ID／Feature／Requirement／AC | DEC-T02-01；[DEC-T02](../features/DECISION-001/tasks.md)、FR-013、[DEC-AC-01](../features/DECISION-001/spec.md)。用户批准本次提交契约与幂等的离线验收切片。 |
| 用户价值与可观察目标 | 旧 `goal` 请求不因可选上下文而改变；合法上下文保留硬条件、偏好和候选顺序；无效输入不创建任务；同键重放只复用同一规范化请求。 |
| 依赖、优先级与批准 | 依赖已提交的 DEC-T02 实现与现行契约；先获本地离线开发和有界测试授权，2026-10-24 用户以“继续”另授权本地分支与 Commit。付费运行、依赖安装、Push、PR 和合并仍未授权。 |
| 范围与复用 | `POST /api/research` → `ResearchCreateRequest` → `PgStore` 事务快照 → `WorkerRunner` → Agent 状态。扩充既有传输、持久层、API／Worker 测试；没有修改生产代码、迁移、数据库结构、六态或冻结协议。实际工作量约一个本地工作时段；一次性 PostgreSQL 通过 WSL 临时保活运行。 |
| 接口与状态 | 无公开 API、Schema、事件、数据库、权限、事实或费用的实现变更；只验证现行行为。默认 V1 入口仍是历史路径，不在本切片切换。 |
| 基线与实施 | 基线 `b4fcc06a483b918d501684017326f4ce5878a3e2`，干净 `main`；配置校验退出 0，Python `627 passed、3 skipped、1 deselected`，前端 `27 passed`。先扩展 API 422／规范化和 Worker 初次／模拟恢复测试，再扩展一次性 PostgreSQL 的幂等、持久快照和事件断言。新增本地测试未复现生产缺陷，故未改生产代码。 |
| 验收 | 正常：旧请求和 `null`、合法上下文；边界／失败：字段长度、类型、重复、未知字段及 422 不落任务；幂等：同键重放、冲突、并发重放；持久：任务快照、Worker 初次传递及恢复快照；事件：测试标记不进入事件 payload。权限与 Windows/WSL 真实恢复不在本次完成范围。 |
| 风险与回滚 | 本次一次性库测试不能证明 Windows/WSL 冷启动、真实失租恢复或跨账户权限。默认 V1 路由接收但不传递新上下文；`memory_mode` 和账户认证仍属后续目标。若需撤销本切片，仅还原本次三个测试文件和本记录／任务索引，保留历史证据。 |
| PR 与交付 | 本地分支与 Commit 已获授权；Push、PR 和 Merge 为 `PENDING`。本记录随本地提交保存。 |

## 实际检查与 Review

| 命令或动作 | 退出码与结果 |
| --- | --- |
| `.venv/Scripts/python.exe -m pytest -q --basetemp .tmp/pytest-dec-t02-unit-red-20261024 backend/tests/unit/test_decision_transport.py` | 0；`3 passed`。新增断言通过，未产生需要修复的红例。 |
| `.venv/Scripts/python.exe -m pytest -q --basetemp .tmp/pytest-dec-t02-focused-final-20261024 backend/tests/unit/test_decision_transport.py backend/tests/integration/test_pg_store.py backend/tests/integration/test_pg_api_worker.py` | 0；`4 passed、3 skipped`。跳过项需要一次性 PostgreSQL 测试库。 |
| `.venv/Scripts/python.exe -m pytest -q --basetemp .tmp/pytest-dec-t02-all-20261024 backend/tests` | 0；`628 passed、3 skipped、1 deselected`。`deselected` 为项目默认不运行的浏览器标记。 |
| 首次 PostgreSQL 准备脚本 | 退出码 1；漏设 `PYTHONPATH`，在读取配置时停止，**尚未创建测试库**。修正后继续。 |
| 设置 `P01_TEST_DATABASE_NAME=dec_t02_01_20261024` 后运行 `.venv/Scripts/python.exe -m pytest -q --basetemp .tmp/pytest-dec-t02-pg-20261024 backend/tests/integration/test_pg_store.py backend/tests/integration/test_pg_api_worker.py` | 0；`4 passed in 4.91s`。先确认库名不存在且不同于应用库，由本机 PostgreSQL 管理账户创建应用账户所有的一次性空库；测试完成后删除该库，并以 `pg_database` 查询确认不存在。 |
| `.venv/Scripts/ruff.exe check --config backend/pyproject.toml` 与 `ruff format --check --config backend/pyproject.toml`（本次三个测试文件） | 均为 0；lint 通过，三个文件格式符合要求。 |
| `.venv/Scripts/python.exe scripts/validate_project.py`；`git diff --check` | 均为 0；配置离线校验通过，Diff 无空白错误。Git 给出两个文件的工作区 LF→CRLF 提示。 |
| 原生 `codex review --uncommitted -c sandbox_mode="read-only"` | 0；进程报告 `sandbox: read-only`，只审查当时的三个测试文件，**未发现可执行缺陷**。其系统 Python 因只读临时目录和缺少项目 `browser_use` 依赖不能完成测试收集；以上 `.venv` 结果是本任务测试证据。此前审查子代理继承可写权限，按仓库规则停止、未审查也未修改文件。 |

常规沙箱内未设置 `P01_TEST_DATABASE_URL`／`P01_TEST_DATABASE_NAME`，WSL 访问被拒；在获准的本机离线测试权限下临时保活 WSL，现有 PostgreSQL 端口 5433 可用。应用账户无建库权限，因此由本机管理账户只创建上述一次性测试库；未在应用库或历史库运行迁移／清理。测试后停止保活进程。GitHub 当前基线 `b4fcc06a` 的 CI 四个 job 成功，但本次工作区新增断言尚未进入远端 CI。前端无修改，前端 `27 passed` 是改动前基线，未在本切片重复运行。

## 逐项验收状态

| DEC-AC-01 子项 | 本切片判定 |
| --- | --- |
| 旧 `goal` 与显式 `null`、输入合法性和硬条件／偏好分离 | `DONE（本地离线 API／Schema）`：FastAPI 传输测试与既有旧请求回归通过。 |
| PostgreSQL 同 owner 规范化幂等、不同用途／条件／偏好／候选顺序冲突及并发重放 | `DONE（一次性 PostgreSQL 离线测试）`；同键返回同一任务，冲突不新增任务。 |
| API → PostgreSQL 快照 → Worker 初次执行与恢复快照、事件不含测试标记 | `DONE（一次性 PostgreSQL 离线测试）`：持久快照、初次传递及从持久事件重建快照已检查；完整失租重认领仍待验证。测试标记的事件检查不能证明任意用户凭据都被识别或阻止。 |
| 六路 API 全链路兼容、跨账户权限、Windows/WSL 本机恢复 | `PENDING`：已有旧请求与假任务历史证据，本切片未完成这些环境及 P-03 权限验收。 |

下一建议任务依赖：以本次通过的一次性库结果为基础，另立 Windows/WSL 真实失租恢复与 P-03 账户权限验收切片。真实 Agent 与 `current-3` 正式评测仍需新的明确授权。
