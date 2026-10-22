# 正式开发前配置定稿审查（2026-10-19）

## 结论与证据级别

**配置可提交用户最终审查；业务仍为 No-Go。** 本轮仅修改规格、计划、契约、ADR、仓库规则/Skill、评测协议、校验器、CI 与 README。没有修改业务代码，没有安装依赖、运行真实模型/外网研究、部署、提交或推送。当前六路 API、AgentLoop、SQLite/SSE、取消和历史界面属**已实现**；现有测试属**已离线测试**；r12 的 18 次真实尝试与三次独立 UI 任务属**历史真实失败记录**，完整成功均为零。LangGraph、PostgreSQL、独立 Worker、五账户隔离、一次恢复和容量模拟是**目标设计，未经验证**。离线通过不证明来源事实、真实研究成功、LAN 安全或岗位竞争力。

## 决策与配置 Diff 摘要

| 范围 | 本轮改变 | 审查边界 |
| --- | --- | --- |
| `SPEC.md`、`PLANS.md`、`docs/contracts/CURRENT_CONTRACTS.md`、ADR-0004 | 单一本机作品目标；五账户含管理员；两运行八排队模拟；一次安全恢复；两周 LangGraph/PostgreSQL/Worker 纵切及逐组件退出；P-00..P-04、8–12 周、49+30+200+20=299 元上限 | 当前代码仍按 V1；`/traces` 与实际路由一致；LAN 部署另验 |
| `docs/evaluation/CURRENT_EVAL_PROTOCOL.json` 与评测说明 | 保留 B/G/O 九题、pilot 和 15 次正式门槛；新增原始记录及调用轨迹哈希、人工核源者/定位、时间、已知与未知用量/费用、计价依据及配对可比条件 | B 每题 2/3、G 总计 2/3、O 3/3；旧 68/75 聚合阈值不作为现行放行条件 |
| `docs/archive/target-2026-10-18/` | 原 0.5 `SPEC.md`、`PLANS.md` 原字节归档，附哈希与相对链接说明 | 两份快照 SHA-256 分别为 `80c6f86f44659dd8e5a9764ea2f66e334eeff0ded65a18822077b395b80db28e`、`7238a6e76d5b14e84a8efbfb614f62d4f975a01f9a1bb00d2d7ce68564be909c` |
| `AGENTS.md`、README、设计索引/工作流、V1 前瞻指针、三个仓库 Skill | 统一指向四个现行入口，明确旧目标和历史记录只供追溯；README 分清可运行 V1 与未实施目标 | V1 正文、旧目标契约/协议、旧审计、r12 与 SQLite 原件未改 |
| `scripts/validate_project.py`、其单测、CI | 校验现行入口和归档哈希、需求映射、题面/门槛冻结、实际工件路径与 SHA-256、Prompt、人工核源声明、费用未知语义及正式批次成本；CI 改名并调用现行校验 | 文件哈希及声明只能证明记录结构，人工打开官方来源仍必需 |

Git 工作树开始时已包含多份未提交/未跟踪配置。主仓库当前 `git diff` 仅覆盖六个已跟踪文件；现行规格、计划、契约、协议、ADR、Skill、校验器和单测是未跟踪文件，必须连同本清单直接审阅，不能以 `git diff --stat` 的行数代表全部变化。未重置、暂存或提交任何既有改动。普通 `git status` 无法进入 `.git/modules/browser-use`；主仓库状态使用 `--ignore-submodules=all` 读取，子模块清洁状态仍未知。

## 实际离线校验

| 命令 | 退出码与实际结果 |
| --- | --- |
| `python scripts/validate_project.py` | 0；`offline validation passed; live model performance and source truth remain unverified`。本地文档链接、现行入口、归档哈希、映射与协议结构通过。 |
| `.\\.venv\\Scripts\\python.exe -m pytest -q --basetemp .pytest-config-20261019-verified -p no:cacheprovider` | 0；`426 passed, 1 deselected in 19.00s`；真实浏览器测试按项目 marker 排除。 |
| `.\\.venv\\Scripts\\python.exe -m ruff check adaptive_agent backend benchmark scripts tests` | 0；`All checks passed!`。 |
| `.\\.venv\\Scripts\\python.exe -m ruff format --check adaptive_agent backend benchmark scripts tests` | 0；`78 files already formatted`。 |
| `.\\.venv\\Scripts\\python.exe -m compileall -q adaptive_agent backend benchmark scripts tests` | 0；无错误输出。 |
| `npm run build --prefix frontend` | 0；Vue 类型检查和 Vite 构建成功。 |
| `npm run test --prefix frontend` | 0；Vitest `20 passed`。 |
| `uv lock --check --offline` | 沙盒内首次退出 1，因 uv 解释器缓存拒绝访问，未进入锁检查；同一只读命令获工具权限后退出 0，`Resolved 282 packages in 39ms`。未安装依赖。 |
| Skill Creator `quick_validate.py` 对三个仓库 Skill | 均退出 0，`Skill is valid!`。 |
| `git -c submodule.recurse=false diff --check --ignore-submodules=all` | 0；仅有工作副本 LF→CRLF 提示；未跟踪文件另由校验器、格式/测试和人工检查覆盖。 |

系统 Python 的全套 `pytest` 首次因缺少 `browser_use` 在收集阶段退出 1；随后使用现有项目 `.venv` 完整通过。系统 Python 的 Ruff 与项目 `.venv` 规则/版本不同，对未修改的 `benchmark/baseline.py` 报 E731；项目 `.venv` 的现行 CI 对应 Ruff 全范围退出 0。这两项环境差异没有通过安装依赖或修改业务代码掩盖。本轮测试生成的临时 `.pytest-*` 目录已逐项核对路径后清理。

## 未运行与剩余风险

没有运行真实 LLM/公开网页任务、来源人工核验、双浏览器资源探针、五账户隔离、故障恢复、备份恢复或正式 15 次评测；这些均是未来验收，费用支出为 0 元。远端 GitHub Actions 与子模块清洁状态未验证。校验器只核验本地证据文件与人工声明的结构，不判断官方网页内容是否真实。若两周架构关口失败，须记录新 ADR、切换约定替代路径并重跑相应契约测试；预算不足时保留全部失败并判 No-Go。进入业务代码、依赖安装、付费真实评测、部署、提交与推送各需明确授权。
