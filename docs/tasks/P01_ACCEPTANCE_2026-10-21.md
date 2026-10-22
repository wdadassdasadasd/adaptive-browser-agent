# P-01 实施与验收证据（2026-10-21）

本文记录 [P-01 Task ID](PREDEV_P01_START_PACKAGE_2026-10-20.md) 的实际实现与验证，不增加另一套规格或任务状态。用户已授权执行结构迁移与工程闭环方案；本轮未安装依赖、运行付费模型/真实研究、提交 Git、推送或部署。工作树原有改动保持在原位。

## 实现范围

- `infrastructure/pg_models.py`、`pg_store.py` 和 `backend/migrations/`：独立 PostgreSQL 应用账本、原子容量、FIFO、租约/fencing、取消、唯一终态、调用/事实/报告/费用、已提交事件。
- `api/pg_main.py`、`pg_research.py`：独立 API 开发入口，六路研究接口，429、持久取消、503 和数据库事件补读。任务/报告同快照查询；终态提交和 SSE 补读间的竞态有回归。
- `worker/runner.py`：独立执行、心跳、取消、最多一次重认领、旧 token 拒绝。已提交步骤可重建事实和用量；重建浏览器后重新观察。账本不可用后停止外部调用和失去租约的写入。
- `agent/call_observer.py`、AgentLoop 与 DeepSeek provider：调用前持久确认，实际 HTTP 重试与 JSON 修复逐请求留账；网络结果未知时留 `started` 供对账，不自动重试。无 observer 的 V1 路径保留原行为。
- `scripts/start-p01.ps1`：WSL 保活、就绪与迁移、独立进程、Worker 重启、数据库故障暂停、端口归属检查、所属进程树清理。`scripts/measure_p01.py` 和 `backend/tests/p01_fake_worker.py` 仅用于明确守卫的本机假任务测量。
- 前端持久显示“取消中”，分别提示容量满额、数据库不可用和 provider 配置缺失。CI 增加 PostgreSQL 16 集成作业；尚未推送执行。

Python 包名与布局已统一。默认 `api.main` 仍是保留的 V1 路径；P-01 明确使用 `api.pg_main` 与 `worker.runner`，阶段放行前不静默切换默认行为。P-01 为单个合成 owner；账户、会话、人工核源、核定价格和正式费用对账仍属于后续任务。未核定调用费用保留 null，不将未知写成零。

## 已执行的检查

| 命令与范围 | 实际结果 |
| --- | --- |
| `.venv/Scripts/python.exe -m pytest -q --basetemp=.../p01-full-20261021`，设置隔离 PG 测试库 | 451 passed、1 deselected，40.77 秒；后续变更由下列回归覆盖 |
| 全部离线 Python 测试，`p01-final-offline-20261021`，不设置 PG 测试库 | 456 passed、2 skipped、1 deselected，44.05 秒。两项跳过均为显式 PostgreSQL 用例；真实浏览器为 deselected |
| PG 两文件纵切：`tests/integration/test_pg_store.py`、`test_pg_api_worker.py` | 隔离库首次组合为 3 passed；迁移、FIFO/容量/fencing/恢复、真实 AgentLoop 离线事实入库与 SSE 均实测。之后 PG + 项目校验器定点为 32 passed、14.66 秒。费用字段迁移后再跑 3 passed、4.31 秒；中间一次 WSL 退出造成 2 项连接失败，保留失败并以同一命令在 WSL 保活期间复查通过 |
| provider/调用账本/AgentLoop/配置定点回归 | 75 passed，7.59 秒；MockTransport 验证实际重试/JSON 修复逐请求、未知网络结果禁止后续请求、恢复后先观察及用量保留 |
| `npm.cmd run test --prefix frontend` | 23 passed；包含持久取消、429/503 区分 |
| 前端 type-check、build | 均退出 0 |
| Ruff 显式使用 `backend/pyproject.toml` | check 通过；format 为 96 files already formatted（包括测量脚本完成版本） |
| `uv --directory backend lock --check --offline`，仓库内 UV 缓存 | 退出 0；286 packages，未安装/升级依赖 |
| PowerShell Parser 检查 `start-p01.ps1` | 退出 0 |
| `git diff --check --ignore-submodules=all` | 退出 0；仅已有 CRLF 提示 |

测试使用现有 `.venv` 与仓库内隔离 basetemp。受限 Windows 沙箱不能完成本机套接字/asyncio 检查；上述实际套接字测试在获准的本机执行环境运行。首次尝试把 URL 打印到 shell 变量被自动审批拒绝，后改为测试代码内部读取现有秘密、外部仅传测试库名；最终命令不打印密码。原始失败和后续通过分别保留，不把环境错误算作代码通过。

## 本机进程与负载记录

空开发库迁移后，`scripts/start-p01.ps1 -ApiPort 8013`：`GET /api/research` 为 200/`[]`，OpenAPI 包含六路研究方法。确认 WSL 无运行发行版后冷启，到 API 就绪 **9.934 秒**。只终止已核实的空 Worker，自动重启 **1.242 秒**；停止启动器后已确认 API/Worker 子进程清空。这些是空进程探针，不代替带任务故障验收。

首轮测量命令：

```powershell
.venv/Scripts/python.exe scripts/measure_p01.py --database-name adaptive_agent_p01_measure_20261021 --output data/p01/measure-20261021.json --port 8014
```

[原始 JSON](../../data/p01/measure-20261021.json) 与 [SHA-256](../../data/p01/measure-20261021.json.sha256) 原样保留，退出码 **1**。容量、429 不落库、FIFO、取消、唯一终态、旧 token、未知调用、两次进程故障与清理均通过；Worker 重启为 2.234/0.469 秒，任务恢复/终结约 30 秒。该轮客户端单调钟分辨率约 15 毫秒，且 PostgreSQL/客户端时钟偏差从 +236.6 毫秒变为 −19.8 毫秒，故脚本拒绝确认跨时钟 SSE 上界，整体未通过。不得从其单项通过推导整个关口通过。

对应的可证伪假说是：跨 WSL 时钟同步导致时延估算不稳定，而数据库/客户端事务链未丢失事件。后续测量改用同一客户端高分辨率 `perf_counter` 的“取消 POST 开始→对应 SSE 收到”保守上界：提交必在请求发起之后，因此该上界小于 2 秒即可证明提交后收到小于 2 秒；远端时钟只作诊断，不再据此推导时延。新版本须用新测试库和新证据文件执行，不能覆盖失败分母。

首轮主机资源峰值：CPU **50.0%**，物理内存使用 **97.8%**（16,412,676,096 bytes），启动器所属进程 RSS 总和峰值 **336,224,256 bytes**。主机采样包含其他桌面程序；这是内存压力证据，不能解释为研究浏览器只需该数值，也不能视为真实浏览器容量通过。

第二轮命令（新隔离库与新证据文件）：

```powershell
.venv/Scripts/python.exe scripts/measure_p01.py --database-name adaptive_agent_p01_measure_r2_20261021 --output data/p01/measure-r2-20261021.json --port 8014 --manual-database-outage
```

[第二轮原始 JSON](../../data/p01/measure-r2-20261021.json)及 [SHA-256](../../data/p01/measure-r2-20261021.json.sha256)原样保留；退出码 **0**，48 项本机假任务检查均通过，JSON SHA-256 为 `55b3ac8fec10f53e974a1899823d4ddcbaa336e2c9e8b7f6339d8e33f093d6de`。两运行八排队、第 11 个 429 不落库、FIFO、取消、旧 token 拒绝和唯一终态均通过。100 次常规列表/详情请求 p95 **0.0178 秒**；SSE 同客户端保守上界 **0.306 秒**。两次 Worker 重启 **1.922/0.266 秒**，租约到期后的重新认领/诚实终结约 30 秒。

数据库故障由本机人工停启 PG 16/main：提交和取消均返回 503，无未确认写入；Worker 暂停，恢复数据库后仍保持暂停，重启启动器后两个中断任务 **7.067 秒** 内重新认领，旧 token 写入均被拒，未完成调用记未知，终态各唯一。该结果是本机假任务故障测试，并非真实浏览器恢复或研究质量验收。[PostgreSQL 生命周期日志摘录](../../data/p01/postgresql-lifecycle-20261021.log) SHA-256 `b8a5e7d5ebf329bdbb12f76c36e0cc9f37d519140b7a2f29b2cdeb27767236a2`，OOM/PANIC 匹配 0。

第二轮主机资源峰值：CPU **54.3%**、内存使用 **97.4%**（16,346,615,808 bytes）、启动器所属进程 RSS 合计 **338,907,136 bytes**。高内存压力保留为真实浏览器容量风险，不把假任务资源外推为真实研究能力。第二轮之后启动器选择已有后端/根目录 Python 环境的细节有一次定点重启检查，11.325 秒就绪；费用字段新增后通过 PG 集成回归，但没有重新执行整套假任务负载。

## 原件与放行

原始 SQLite SHA-256 保持 `1cf908a6f9e83985548ba7bd0753a204e6d8ccbaf70ac34daa9d3152ecbd0064`；r12 summary 保持 `4d1bd15ddb80c8f6fc4148d6ce4b95b4e6c13afe78f534d29158fb3b7839d88d`。R0 历史映射保持其迁移时哈希，历史文件继续冻结；当前任务记录允许追加实施证据。未能验证 `browser-use` 子模块 Git 元数据的工作树状态，不声称其清洁。

| 判定层级 | 当前结论与依据 |
| --- | --- |
| 开发准备就绪 | 已有方向、权威入口、任务/AC、独立环境和命令；实际业务按阶段推进 |
| 结构迁移通过 | [R0 本地验收](R0_ACCEPTANCE_2026-10-20.md) 已通过 |
| 阶段业务通过 | P-01 **本机假任务架构关口通过**（第二轮 48/48）；这是本阶段的模拟验收结论。真实浏览器恢复、真实研究质量、账户隔离与费用总账属于后续阶段且仍未验证；P-02/P-03/P-04 未通过 |
| 产品放行 | **No-Go**。没有真实研究 pilot、五账户、安全/备份恢复、15 次正式尝试与人工核源证据 |
