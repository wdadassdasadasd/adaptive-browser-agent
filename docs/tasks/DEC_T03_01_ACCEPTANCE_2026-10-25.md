# DEC-T03-01：证据矩阵与持久恢复一致性离线验收

| 字段 | 记录 |
| --- | --- |
| Task／需求／AC | DEC-T03-01；DECISION-001、FR-003／004、DEC-AC-02／03 |
| 状态 | 实施 `IMPLEMENTED`（本地提交）；本次验收 `DONE（离线切片）`。真实官方人工核源与进程崩溃恢复仍属于后续验收。 |
| 用户价值 | 已准入事实从事件到 PostgreSQL、恢复状态和决策矩阵保持同一 fact ID、主体、来源、片段与时间；冲突和未知不被掩盖。 |
| 依赖与授权 | PR #2 合并提交 `7289065d`；用户批准本切片的离线开发与一次性测试库，并于 2026-10-25 明确要求继续直至 Commit。Push、PR、Merge、依赖安装及付费运行仍未授权。 |
| 范围与复用 | 复用 StateReducer、Worker、PgStore 和 DecisionService；只修改归约时间、Worker 准入事实入库／恢复对账及定点测试。无公开 API、Schema 或冻结协议改动。 |
| 工作量与不确定性 | 原计划约 1–2 个兼职工作日；主要不确定性是 Windows 到 WSL PostgreSQL 的本机连接。 |
| 风险与回滚 | 修改限于本工作区的六个代码／测试文件和任务记录；回滚可撤销 scoped diff。若已提交历史事实与事件不一致，恢复失败关闭，不据此生成新结论。 |
| Git 交付 | `codex/dec-t03-01` 隔离工作区；本记录随本地提交交付，未 Push／建 PR。 |

## 基线与审计

- 原本地 `main` 为干净的 `b4fcc06a`；获取远端后确认 `origin/main=7289065d13c44f5e7da00cd3ca7dbbb7011144fe`，本工作区从该合并提交建立。
- 改动前本地定点测试：决策及 Worker 时间戳 8 passed；状态归约 55 passed。现有决策逻辑覆盖 unknown、错主体、缺片段、冲突与 fact ID 引用；现有 PostgreSQL 测试覆盖单条事实入库与基本快照，未逐字段对账矩阵。
- 失败先行：新观察时间测试与重复事实入库测试同一命令退出 1、2 failed。原归约保留模型时间；Worker 把已被归约去重的原始载荷重复写为机器候选事实。

## 实施与验收口径

- StateReducer 在准入时以事件观察时间固定事实时间；Worker 用同一归约器计算新增事实，仅把增量与事件原子写入。恢复时逐 ID 核对 `app_fact` 与事件重放的主体、声明、来源和片段，并以持久事实的抓取时间还原矩阵时间；不一致则失败关闭。
- DEC-AC-02／FR-003：事实 ID 和上述字段逐项一致；重复或未准入材料不能新增可引用事实。DEC-AC-03／FR-004：跨候选引用拒绝，缺证据为 unknown，冲突保留双向 fact ID，矩阵引用可追到本任务事实。以上为离线口径，真实官方身份与人工核源不在本切片内。
- 现有纯逻辑测试覆盖错主体、缺片段、冲突、未知和引用；新增归约、Worker、恢复测试覆盖时间、去重与持久事实不一致时失败。PostgreSQL 集成断言补充了事实表和恢复矩阵逐项对账，并在独立一次性库通过。

## 实际检查与待办

| 层 | 命令或动作 | 结果 |
| --- | --- | --- |
| L1 基线 | `.venv/Scripts/python.exe -m pytest -q` 定点决策、时间戳、归约文件 | 8 passed 与 55 passed；均退出 0 |
| 失败先行 | 新增观察时间与重复事实用例定点运行 | 2 failed，退出 1；随后最小修复 |
| L1 修复后 | `.venv/Scripts/python.exe -m pytest -q` 定点三文件 | 65 passed，退出 0 |
| L3 初次环境调查 | 一次性库 `adaptive_agent_dec_t03_01_20261025_a1b2` 先确认不存在，再创建；两次尝试 PostgreSQL 两文件 | 默认沙箱内 Windows 到 `127.0.0.1:5433` TCP 不通；测试停在首个数据库用例，均中断，不能记为通过。WSL 无现成 pytest；临时网络监听探针被自动审批以可能暴露仓库文件为由拒绝，未运行。该库已按精确名称删除，并查询确认不存在。 |
| L3 隔离库复测 | WSL `pg_isready`；获准在沙箱外用 `Test-NetConnection 127.0.0.1 -Port 5433`；确认新库 `adaptive_agent_dec_t03_01_20261025_b2c3` 不存在后创建；从主工作区 `.env` 读取连接参数但不输出，设置 `P01_TEST_DATABASE_NAME`，运行 `pytest -q --basetemp D:/adaptive-browser-agent/.tmp/pytest-dec-t03-pg-fixed backend/tests/integration/test_pg_store.py backend/tests/integration/test_pg_api_worker.py` | WSL PostgreSQL 接受连接；沙箱外 Windows TCP 连通。两文件 **4 passed in 4.60s**，退出 0。结束后确认库内仅有 `alembic_version`，按精确库名删除并查询确认不存在；未连接已有应用库执行测试。 |
| L0 | `ruff check`、`ruff format --check`（backend/src、tests、migrations、scripts） | 分别退出 0；All checks passed／122 files already formatted。 |
| 离线回归 | `.venv/Scripts/python.exe -m pytest -q --basetemp … backend/tests` | 首轮 629 passed、1 failed（测试替身缺 `list_facts`）、3 skipped、1 deselected；补齐替身后 630 passed、3 skipped、1 deselected，退出 0。 |
| 项目校验 | `python scripts/validate_project.py`；`git diff --cached -- docs/archive`；`git hash-object --no-filters` 与 `git show HEAD:<path>` 抽检 | 初次退出 1：26 份未修改历史归档在 Windows checkout 中为 CRLF（`i/lf w/crlf`）。为 `docs/archive/**` 设置 `-text` 后，把 29 份检出时被换行转换的文件恢复为原 Git blob 字节；未修改任何归档 blob。复测校验退出 **0**，输出 `offline validation passed`；归档的 staged diff 为空。 |
| 独立 Review | 原审查代理只读隔离无法验证；随后运行原生 `codex -s read-only -a never -C D:/adaptive-browser-agent/.tmp/dec-t03-01 review --commit 7c7901c1b54511b8151ed505c5fb8c6d4374f968`，再用相同只读设置执行 `review --uncommitted` 审查本轮 `.gitattributes` 与验收记录 | CLI 明示 `sandbox: read-only`、`approval: never` 与明确范围；两次均退出 0，均结论为 **无可操作回归**。首次审查时任务记录尚未更新 L3 结果，故其“PostgreSQL 未验证”附注已由本表的独立测试证据纠正。 |

离线样本来源为合成材料；报告和矩阵的 `machine_admitted_human_unverified` 只表示机器候选。真实浏览器／LLM 取证、官方身份与冲突事实逐条人工核源、Windows／WSL 真实进程恢复及正式九题门槛仍待单独授权和证据；P-02 与产品维持 No-Go。
