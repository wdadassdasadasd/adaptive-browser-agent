# R0 结构迁移验收（2026-10-20）

- 状态：**本地通过**。本记录只验收结构迁移和现有 V1 行为回归；产品仍为 No-Go。
- 需求与 AC：NFR-005 / AC-N05；执行基线为 `dbacdc02fb119f70bc65a14608ab1bede75c0622` 上的既有工作区。未提交的原有改动按文件保留。
- 交付：Python 源码、测试、锁文件归入 `backend/`，现行文档从[导航](../README.md)进入，[34 项迁移与哈希映射](../archive/R0_PATH_MAP.json)保留历史原字节和旧路径；六路研究 HTTP 契约保持现有 V1 行为。

## 实际验证

| 检查 | 结果 |
| --- | --- |
| `.venv/Scripts/python.exe -m pytest -c backend/pyproject.toml backend/tests -q --tb=short --basetemp=D:/adaptive-browser-agent/.pytest_cache/r0-escalated-suite-20261020-b` | 退出码 0；442 passed、1 deselected。Windows 受限沙箱的 `asyncio` 本地 socket 创建会卡住，此次在获准的测试环境运行。 |
| `.venv/Scripts/ruff.exe check backend/src backend/tests scripts`、`ruff format --check`、`python -m compileall -q backend/src backend/tests scripts` | 均退出码 0；80 个 Python 文件已格式化。 |
| `uv --directory backend lock --check --offline` | 使用工作区 `.uv-cache`，退出码 0；286 个包的锁定解析检查通过，未安装依赖。 |
| `.venv/Scripts/python.exe scripts/validate_project.py` | 退出码 0；文档链接、协议约束和归档映射校验通过。归档映射 34 个目标哈希相符，其中 32 个历史文件保留移动前字节。 |
| `npm.cmd run type-check --prefix frontend`、`npm.cmd run test --prefix frontend`、`npm.cmd run build --prefix frontend` | 均退出码 0；20 个前端交互测试通过，构建成功。 |
| 从根目录和 `backend/` 实例化 `Settings` 并解析相同的相对 SQLite URL | 两处都指向仓库根目录的同一 `data/r0-test.db` 路径；只检查配置，没有连接该数据库。 |
| `git -c diff.ignoreSubmodules=all diff --check --ignore-submodules=all` | 退出码 0；子模块的 Git 元数据仍无法读取，所以不能据此断言子模块工作树清洁。 |

原始 `data/adaptive_agent.db` SHA-256 仍为 `1cf908a6f9e83985548ba7bd0753a204e6d8ccbaf70ac34daa9d3152ecbd0064`；r12 `data/benchmark/20261016T152251931497Z-3de75ed5/summary.json` 仍为 `4d1bd15ddb80c8f6fc4148d6ce4b95b4e6c13afe78f534d29158fb3b7839d88d`。映射文件 SHA-256 为 `51e80550124c305e8efcb3f4fac00ce15b61c0b4b8cf37bf6a2ea9912963cf25`。

## 剩余边界

R0 不证明独立 Worker、PostgreSQL 业务表、五账户隔离、真实研究质量或正式评测通过。历史文件的原始相对链接由映射校验；直接在 GitHub 打开旧正文时部分链接仍需参照[归档索引](../archive/README.md)。远端 CI、真实浏览器和付费研究均未在本次执行。
