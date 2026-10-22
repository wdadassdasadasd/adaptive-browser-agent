# P-01 开工前环境配置与探针（2026-10-20）

**授权范围**：用户单独授权在 Ubuntu WSL 安装 PostgreSQL 16 服务端/客户端，在 Windows 项目锁文件加入 `asyncpg`、Alembic，创建本机隔离开发库并做连接探针。本记录仅证明环境探针，不证明独立 Worker、容量、安全恢复或真实研究成功。未修改业务代码、旧 SQLite、r12、`browser-use/`，未部署或运行付费任务。

## 安装与保留原件

- Ubuntu WSL 为 24.04.1 LTS。首次 `apt-get install` 因 `127.0.0.1:7897` 代理 502/旧索引 404 失败，且未安装 PostgreSQL；随后只对命令临时禁用故障代理，从 Ubuntu 官方源 `apt-get update`。再次模拟显示 **12 个新包、0 个升级、0 个移除**，再安装 `postgresql-16` 与 `postgresql-client-16` 成功（退出码 0），解析版本均为 **16.15-0ubuntu0.24.04.1**。未增加第三方 apt 源。
- `pg_lsclusters` 显示 `16/main` 在线、端口 **5433**；`psql` 与 `pg_dump` 均为 16.15。WSL 内 `ss -ltn` 显示 PostgreSQL 只监听 `127.0.0.1:5433`。
- 项目运行依赖新增 `alembic>=1.16,<2` 与 `asyncpg>=0.30,<1`；`uv.lock` 新锁定 Alembic **1.20.0**、asyncpg **0.32.0**，另新增 Mako/MarkupSafe 传递依赖。`uv add ... --no-sync` 和 `uv sync --locked --dev` 均退出 0；`pyproject.toml` 仅新增两行、`uv.lock` 仅新增 99 行，无既有包版本替换。
- 新建 `adaptive_agent_dev` 空数据库和 `adaptive_agent_app` 登录角色；角色查询显示 `rolsuper=false`、`rolcreatedb=false`、`rolcreaterole=false`，`public` 表数为 0。随机密码仅保存在 Git 忽略的 `.env` 中新增的 `P01_DATABASE_URL` 键；未打印、写入文档/trace 或改动既有 `DATABASE_URL`。第一次建库命令因 WSL 直接 `exec runuser` 找不到 PATH 在执行 SQL 前失败；验证新键仍不存在后，使用 `/usr/sbin/runuser` 重试成功。
- 安装前后只读核对的原始 `data/adaptive_agent.db` 文件 SHA-256 为 `1cf908a6f9e83985548ba7bd0753a204e6d8ccbaf70ac34daa9d3152ecbd0064`；r12 `summary.json` 为 `4d1bd15ddb80c8f6fc4148d6ce4b95b4e6c13afe78f534d29158fb3b7839d88d`。原始记录未作为新数据库的迁移输入。

## 本机连接结果与启动约束

Windows `Test-NetConnection 127.0.0.1:5433` 在 WSL 运行时为 true；Windows `.venv` 的 SQLAlchemy `create_async_engine` + `asyncpg` 执行只读 `SELECT` 得到 `adaptive_agent_dev / adaptive_agent_app / 127.0.0.1 / 5433`，无密码输出。单独、未先唤醒 WSL 的 Python 探针两次遭 `ConnectionRefusedError`；此时 `wsl --list --running` 无 Ubuntu。临时隐藏进程 `wsl.exe --distribution Ubuntu --exec /usr/bin/sleep 45` 存活时再次 `SELECT 1` 成功，随后该临时进程已按 PID 停止。

**结论**：Windows↔WSL 本机连接在 WSL 持续运行时可用；当前没有常驻启动器，不能宣称冷启动后的独立连接持续可用。P-01 启动器须拥有 WSL 前台保活进程的生命周期、检测 PostgreSQL 是否在线，再启动 API/Worker；WSL/数据库故障仍按失败关闭和人工恢复后对账，不暗示数据库自动重启。P-01 两周关口必须重新测启动、故障与资源负载。新 `.env` 键供 P-01 使用，V1 `Settings` 当前忽略它，因而现有 SQLite 默认运行路径未被切换。

## 待验证

PostgreSQL 版本化迁移、任务认领/fencing、调用账本、API/Worker 集成、十任务容量模拟、数据库失联恢复、加密备份及 16 GB 资源记录均未实施或未验证。

依赖变更后实际检查：`uv lock --check --offline` 退出 0；Python `pytest -q --basetemp=.pytest_cache\predev-env-full-20261020` 为 **432 passed，1 deselected**；`scripts/validate_project.py` 通过；Ruff check 通过、format check 为 78 files already formatted；前端 `npm run type-check` 退出 0、`npm run test` 为 **20 passed**、`npm run build` 退出 0。首次在受限沙箱运行 `uv lock --check --offline` 因 uv 缓存目录拒绝访问失败，随后以获准的环境权限原命令重跑通过；该失败不是锁文件不一致。以上均为离线/本机检查，不证明真实研究成功。
