# P-01 任务记录

- 日期：2026-10-20，Asia/Shanghai
- 实施更新：2026-10-21，Asia/Shanghai。用户已授权执行目录重组与工程闭环方案；R0 本地验收完成，P-01 已实现 PostgreSQL 账本、独立 API/Worker、调用记录与启动器。本机假任务架构关口第二轮 48/48 通过；真实浏览器及研究质量不在该模拟结论内。逐项命令、证据和剩余项见[实施验收记录](P01_ACCEPTANCE_2026-10-21.md)，产品仍 No-Go。
- 入口：[SPEC](../../SPEC.md)、[PLANS](../../PLANS.md)、[当前契约](../contracts/CURRENT_CONTRACTS.md)、[current-3 协议](../evaluation/CURRENT_EVAL_PROTOCOL.json)、[ADR-0005](../design/adr/0005-windows-worker-wsl-postgres.md)、[最终设计记录](../audits/PREDEV_FINAL_DESIGN_REVIEW_2026-10-19.md)。现有能力以 V1 源码/契约为准；r12 为历史 No-Go。

## 基线与已知阻碍

R0 迁移前的 V1 基线中，`backend/services/research.py` 在 API 进程内创建任务并使用 `adaptive_agent/runtime/task_manager.py` 的内存队列；`backend/main.py` 启动时终结未完成任务；`backend/db/` 仅有 SQLite 目标的建表方式，`backend/api/research.py` 的 SSE 使用进程内通知。R0 只整理目录，不改变这些业务边界；P-01 要改这些边界，不能把离线测试视为 Worker/PostgreSQL 已通过。原始 `data/adaptive_agent.db`、r12、旧协议和 `browser-use/` 不作迁移目标、不覆写。

首次只读环境探针：沙箱内 `wsl.exe --list --quiet` 返回 `Wsl/E_ACCESSDENIED`；获只读提权后列出 Ubuntu 24.04.1 LTS，当时 `psql`/`pg_dump`/`pg_lsclusters` 均不存在。此后用户单独授权安装，[环境配置记录](../audits/PREDEV_ENV_SETUP_2026-10-20.md)确认 PostgreSQL 16.15 已安装、本机回环连接在 WSL 存活时成功。WSL 没有前台进程时退出，独立连接被拒绝；P-01 启动器必须维护 WSL 生命周期，并在数据库失联时失败关闭。

环境选择：Ubuntu 官方源的 `postgresql-16`/`postgresql-client-16` 实装 **16.15**；Windows 项目锁定 asyncpg **0.32.0** 与 Alembic **1.20.0**，不加入第三方 apt 源。依据为 [Ubuntu 官方安装说明](https://documentation.ubuntu.com/server/how-to/databases/install-postgresql/)、[SQLAlchemy PostgreSQL asyncpg 方言](https://docs.sqlalchemy.org/en/20/dialects/postgresql.html#asyncpg)与 [Alembic 异步迁移说明](https://alembic.sqlalchemy.org/en/latest/cookbook.html#using-asyncio-with-alembic)。安装只证明依赖存在和连接探针，不证明迁移、认领、恢复或容量。

原始 `data/adaptive_agent.db` 当前文件字节 SHA-256 为 `1cf908a6f9e83985548ba7bd0753a204e6d8ccbaf70ac34daa9d3152ecbd0064`；r12 批次 `summary.json` 为 `4d1bd15ddb80c8f6fc4148d6ce4b95b4e6c13afe78f534d29158fb3b7839d88d`。主仓库 HEAD 的 `browser-use` gitlink 为 `7be96ed8bafa8dfe1eef228b59cf5c884b8b2431`；工作树清洁状态因子模块 Git 元数据访问受限而未验证。以上均为只读基线，不能据此声称备份/恢复已完成。

## 顺序、文件边界与交付

以下 Task ID 是本阶段唯一任务记录。用户的方案实施授权覆盖这些代码任务；依赖安装、付费真实任务、Git 与部署仍分别授权。实施保留原有脏工作树与 V1 回归，新应用数据库使用独立迁移族，不对旧 SQLite 做原地升级。回滚开发入口时停止 P-01 启动器并使用保留的 V1 入口；不靠删除新库或原始数据回滚。

| Task ID | 依赖与拟改范围 | 完成证据 | 当前状态、实证与风险 |
| --- | --- | --- | --- |
| P01-ENV | 已获单独授权并完成安装与初始连接探针；[记录](../audits/PREDEV_ENV_SETUP_2026-10-20.md)含版本、隔离空库、最小权限、回环绑定及 WSL 保活要求。 | Windows `asyncpg` 在 WSL 前台保活时成功执行只读 SQL；冷启动/持续可用由 P01-RUNTIME 启动器及故障测试再验，不能把环境探针算作架构关口通过。 | 环境与启动器已接入；冷态就绪及空进程重启实测见[证据](P01_ACCEPTANCE_2026-10-21.md)。 |
| P01-TRACE | 只读分类 r12 的 18 次尝试和三次 UI 失败；[症状清单](../audits/PREDEV_R12_SYMPTOM_INVENTORY_2026-10-20.md)已完成。后续调用级根因诊断依赖新账本，不把症状当根因，不改历史记录。 | 原始报告逐条链接与摘要哈希可复查；后续每个根因假说须列可证伪的调用证据，不写新成功率。 | r12 症状分类已记录；新调用账本离线通过，但尚无同口径真实调用轨迹，调用级根因未验。 |
| P01-DB | P01-ENV；`backend/src/adaptive_research/infrastructure/` 及版本化迁移。新 PostgreSQL 应用表含 owner 关联、任务、租约/递增 fencing token、取消请求、调用尝试、事实、费用、单调事件；使用事务约束唯一有效认领/终态。 | 新空库建表/版本核对、并发认领和迟到 token 写入拒绝的 PostgreSQL 集成测试；失败不回退到旧 SQLite 数据库。 | 已实现；隔离 PostgreSQL 迁移与 FIFO/容量/fencing/一次恢复和二次终结测试通过。步骤事件与事实同事务；报告和任务同查询快照。见[证据](P01_ACCEPTANCE_2026-10-21.md)。 |
| P01-RUNTIME | P01-DB；应用工厂、新增 `worker/` 与本机启动器。API 只持久提交；Worker 短事务认领、两运行八排队、FIFO、租约/心跳、取消和最多一次重认领。启动器维护 WSL 前台保活并先确认数据库在线，再监测 Worker；数据库失联暂停新认领。 | 从 WSL 未运行的冷态启动后 Windows 能连接；10 个可控假任务及第 11 个 429 不落库；无丢失/双认领/越权写入/双终态，排队取消释放名额。假任务只由测试夹具或本机测试入口注入，不发布成生产研究路由，也不需要真实 DeepSeek key。 | 已实现；冷启动 API 就绪 9.934 秒，空 Worker 重启 1.242 秒。第二轮 48/48 假任务检查包括数据库断开/人工恢复，详见[证据](P01_ACCEPTANCE_2026-10-21.md)；真实浏览器恢复单独留验。 |
| P01-CALL | P01-DB/RUNTIME；`agent/agent_loop.py`、provider/工具适配层、持久化。每次模型/工具调用前写 `started`，后写已知结果/用量；中断记 `unknown_outcome`、费用 null。已提交事实保留，恢复前重新观察，未知外部动作不盲重放。 | 故障注入覆盖调用前、调用中、调用后、事实/事件提交前后；旧 token 结果不得覆盖新代次；单任务第二次故障诚实 `partial/failed`，所有终态唯一。 | 已实现按实际 DeepSeek HTTP 请求记录，包含重试与 JSON 修复；未知网络结果停止后续请求。离线恢复保留事实/用量并先观察。未核定价格的调用仍为未知费用；全部故障空档和真实浏览器路径尚未穷尽，见[证据](P01_ACCEPTANCE_2026-10-21.md)。 |
| P01-API-CI | P01-DB/RUNTIME/CALL；`api/`、schemas、SSE、前端取消状态及 CI。保持六路研究 API 核心语义；429、取消请求确认、数据库失联错误可区分，SSE 从已提交事件补读。CI 加 PostgreSQL 集成作业，但 Windows/WSL 实机探针独立留档。 | API/持久层/SSE 对账、重连补读、取消响应与最终终态、数据库失联失败关闭；旧 V1 离线测试和新 PG 测试结果分开报告。 | 已实现；HTTP/SSE 纵切、终态读写竞态、非法游标和 503 回归通过；前端持久取消、429/503 提示通过。PostgreSQL CI 已配置，远端未运行。见[证据](P01_ACCEPTANCE_2026-10-21.md)。 |

P-01 测试使用固定的合成 owner；P-03 再接入五账户身份、会话和完整管理员界面。P-01 的本机纵切不可对外部署，也不能以尚未接入的身份层声明跨账户隔离通过。`browser-use/` 上游源码保持不变。PostgreSQL 异步驱动和迁移工具版本保持锁定；版本化迁移脚本和隔离库集成已有实际验证。

## 两周硬关口的测量脚本契约

同一冻结代码/环境上，先从 WSL 未运行的冷态由启动器保持 WSL 并检查 PostgreSQL，再同时保持两个可控假任务运行、八个排队；第 11 个提交返回 429 且数据库无新任务。记录每项的提交、认领、取消、事件、终态及 token 时间线，验证 FIFO、排队取消即释放名额、无丢失/双认领/OOM。负载期间对现有常规列表/详情 API 重复采样，明确样本数与各次时延，p95 ≤1 秒；对已提交事件从断线游标补读，记录提交至客户端收到的逐次时延，≤2 秒。至少一次杀 Worker：启动器 ≤60 秒重启，任务 ≤120 秒重新认领或按原因终结；测试迟到旧 token 写入、第二次故障、运行中取消、数据库断开/人工恢复后对账，并记录 Windows 主机 CPU/内存峰值、PostgreSQL 日志与所有失败样本。假任务时限不冒充真实浏览器恢复速度。

每个判断都附命令、退出码、版本、时间、机器规格和原始记录路径/哈希。任一硬项失败即暂停付费 pilot；仅可根据故障证据限时修复一个必要组件。若两周内无法过关或修复挤压 P-02 研究质量/P-04 正式批次，保持 No-Go 并请用户重定范围，不静默改用单进程、SQLite 或 LangGraph。

## 开工前与授权边界

- 已完成：方向决策、固定题面/门槛、协议原字节归档、P-00 离线验证、r12 只读症状分类、环境依赖安装、隔离库与条件化连接探针。正式研究效果、容量、安全恢复、备份恢复均未实测。
- 已授权并实施：上述 P-01 代码任务。真实模型/浏览器评测、外部写入、部署、提交/推送/PR 各自仍需独立授权。
- 立即可核对的开工条件：P-01 启动器让 WSL 持续运行后，隔离 PostgreSQL 可从 Windows 本机连接；版本与锁文件已确定；原始 SQLite/r12 哈希与路径已登记；当前脏工作树须逐项保留。环境探针通过不等于 P01-DB/RUNTIME 集成通过。
