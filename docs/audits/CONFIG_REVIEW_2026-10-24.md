# 2026-10-24 Codex 工程配置复审

基线：`ec4a149664a8d084584f03c94942dd72400349e4`；范围为仓库 Codex 导航、需求切片状态、测试／评测关口、PR 模板、归档字节校验与现行 GitHub CI。此记录不修改产品契约、正式评测协议或历史事实；未运行付费模型／浏览器任务，P-02 与产品仍为 No-Go。

## 修复与判定

| 问题 | 处理与证据 | 本轮判定 |
| --- | --- | --- |
| DECISION-001 批准及实施状态在多个入口漂移 | 根 `AGENTS.md`、`SPEC.md`、`PLANS.md`、现行契约、文档导航和配置说明统一指向[任务状态](../features/DECISION-001/tasks.md)；历史实施记录补实际提交 ID。 | 本地导航一致；T02–T05 仍为 `PARTIAL`，T06 为 `PENDING`。 |
| 代码提交与产品放行混用 | [G0–G7 流程](../engineering/WORKFLOW.md)、[任务模板](../engineering/TASK_TEMPLATE.md)和 PR 模板分别记录实施、范围内验收与正式 Go。 | 本地规则明确；离线提交及 CI 不能解除 No-Go。 |
| Linux CI 的历史归档哈希失败 | [原工作流](https://github.com/wdadassdasadasd/adaptive-browser-agent/actions/runs/39984876768)的 Python 3.12／3.13 job 各在归档校验处报 10 项失败；本地对照发现 36 个冻结路径中，10 个 Git blob 的换行被规范化，而 Windows 工作区字节符合冻结 SHA-256。`.gitattributes` 对这 10 个路径设置 `-text`，并在 Git 索引恢复其原始字节；校验器新增索引字节检查和跨平台回归测试。 | 36 个暂存 Git blob 与冻结哈希相符；10 个恢复的 blob 与旧 blob 仅换行不同。远端须在获授权提交／推送后复测。 |
| PostgreSQL 验收记录缺少远端结果 | 同一工作流的 PostgreSQL job 在 Linux 一次性库完成迁移及 4 项集成测试，前端 job 通过；已补进[任务状态](../features/DECISION-001/tasks.md)和[实施记录](../features/DECISION-001/OFFLINE_IMPLEMENTATION_2026-10-23.md)。 | 只补相应远端 L3 证据；Windows／WSL、浏览器和真实研究仍待验证。 |

## 本地执行证据

| 命令／检查 | 实际结果 |
| --- | --- |
| `.venv/Scripts/python.exe scripts/validate_project.py` | 退出码 0；离线校验通过，新增 Git 索引归档检查覆盖 36 个冻结路径。 |
| `.venv/Scripts/python.exe -m pytest -q --basetemp .tmp/pytest-gitarchive-red backend/tests/unit/test_validate_project.py::test_archive_git_index_detects_normalized_history_before_publish`（修复校验函数前） | 退出码 1；测试捕获“工作区 SHA 正确但 Git 索引换行被规范化”的问题。 |
| 同一测试使用 `--basetemp .tmp/pytest-gitarchive-green`（修复后） | 退出码 0；`1 passed`。 |
| `.venv/Scripts/python.exe -m pytest -q --basetemp .tmp/pytest-config-final-20261024 backend/tests/unit/test_validate_project.py` | 退出码 0；`32 passed`，包括新增的 Git 索引换行回归。 |
| `.venv/Scripts/python.exe -m pytest -q --basetemp .tmp/pytest-decision-status-20261024 backend/tests/unit/test_decision.py backend/tests/unit/test_decision_transport.py backend/tests/integration/test_agent_loop.py` | 退出码 0；`48 passed`。这是离线测试，不代替真实研究。 |
| `npm test -- --run`（`frontend/`） | 退出码 0；`27 passed`。 |
| `.venv/Scripts/ruff.exe check --config backend/pyproject.toml scripts/validate_project.py backend/tests/unit/test_validate_project.py`；对应 `ruff format --check` | 均退出码 0；检查通过，2 个文件格式符合要求。 |
| `git diff --check` 与 `git diff --cached --check` | 均退出码 0；暂存 27 个明确文件，其中 10 个归档 blob 仅恢复原始换行；`git diff --exit-code` 为 0，无剩余未暂存修改。 |

## 尚待完成的门禁

- 当前修复尚未提交或推送；[GitHub CI](https://github.com/wdadassdasadasd/adaptive-browser-agent/actions/runs/39984876768)仍显示旧提交失败，不能宣称远端已通过。
- 远端 `rulesets` 查询返回空列表；当前 GitHub 集成读取 `main` branch protection 返回 403，故不能断言该分支有或没有保护。PR 模板和 CI 文件本身不等于强制门禁。
- T02–T06 的未验证 AC、Windows／WSL、本机浏览器、人工核源与正式评测继续按[任务表](../features/DECISION-001/tasks.md)和现行协议推进。
