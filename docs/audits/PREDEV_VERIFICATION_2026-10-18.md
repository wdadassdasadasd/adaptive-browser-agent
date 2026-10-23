# 0.4 工作台验证与批准记录（2026-10-18）

**历史记录范围（0.4 当时）**：仅研究、规格、仓库指令/Skill、评测协议、标准库校验器、测试与 CI 配置。用户当时批准 [0.4 规格快照](../archive/target-0.4/SPEC_0.4.md) 并切换设计权威；后来已由 0.5 目标取代，当前验证结果须另查本轮实际命令。[0.3 设计索引](../archive/design-0.3/00_DESIGN_INDEX.md)保留历史。真实业务仍沿用历史 r12 **No-Go**。[现状审计](PREDEV_BASELINE_2026-10-18.md)给出源码和数据流证据。

## 实际检查

| 检查 | 结果 |
| --- | --- |
| `python scripts/validate_project.py` | 退出 0；项目根与 `docs/` 的本地 Markdown 目标、权威版本指针、需求/任务/验收 ID、三个 Skill、B/G 固定原文和协议结构通过；不等于网页内容核源 |
| `uv lock --check --offline`、`uv run --offline --locked python -c "from backend.config import Settings; Settings(_env_file=None)"` | 均退出 0 |
| `uv run --offline --locked ruff check adaptive_agent backend benchmark scripts tests` | 退出 0，All checks passed |
| `uv run --offline --locked ruff format --check adaptive_agent backend benchmark scripts tests` | 退出 0，78 files already formatted |
| `uv run --offline --locked python -m compileall -q adaptive_agent backend benchmark scripts tests` | 退出 0 |
| `uv run --offline --locked pytest -q` | 首版工作台时退出 0，**419 passed, 1 deselected in 18.04s**；在可创建本地 socketpair 的执行环境运行，`UV_CACHE_DIR`、`TEMP`、`TMP` 指向仓库已忽略的 `.venv` 目录；下述团队需求修改后只重跑受影响校验器测试 |
| `npm run type-check --prefix frontend`、`npm run build --prefix frontend`、`npm run test --prefix frontend` | 均退出 0；构建成功，前端 **20 tests passed** |
| Skill Creator `quick_validate.py` 对 `gate2-task`、`agent-failure-triage`、`research-eval` | 三个均退出 0，`Skill is valid!` |
| `git -c submodule.recurse=false diff --check --ignore-submodules=all`、新增文件尾随空白 `rg` | Diff 检查退出 0；新增文件未发现尾随空白；Git 提示 LF/CRLF 转换，不是检查失败 |
| 新 Codex 会话只读演练（批准前） | 发现三个 Skill 及各自触发边界，当时 AGENTS 将 0.3 视为现行、0.4 视为候选；发现旧 07 工作流时点文字过期，已加日期说明；未改文件。批准后的新指针经离线校验，未再次开启新会话 |

首次在默认受限环境运行全量 pytest 时，Windows asyncio 的本地 socketpair 阻断导致首个异步测试停住；首次放宽环境运行又因 Windows 默认 Temp 不可写产生 39 个 setup 错误。将缓存/临时目录置于 `.venv` 后，最后一次全量测试如上通过。此为运行环境问题，未修改业务代码或测试来规避失败。

## 团队需求重评后的增量检查

用户明确新增：三类成功报告均须可核源建议（B01–B03 原文不变）；约 20 人在同一 Windows 11/i7-12700H/16 GB RAM 主机的内网使用，自建管理员开通账户、个人任务隔离、统一 Provider 凭据按人记用量、至少 8 个任务可提交/排队（运行槽由容量测试决定），并由管理员统一安装内部 CA 信任。约 170 GB 可用磁盘来自用户提供的系统截图，不作为已实测资源曲线。服务只要求工作时段在线；管理员提供内网共享存储，需每日异机加密备份、保留 30 天、每月验证恢复。由此新增[ADR-0002](../archive/design-0.3/adr/0002-team-runtime.md)、[术语](../../GLOSSARY.md)、FR-009/010、NFR-007/008/009 和 G2-10/11/12；后续候选计划由 57 小时重估为 120 小时。此段记录批准前的候选阶段；用户随后明确批准 0.4 并授权切换权威指针。

| 增量检查 | 实际结果 |
| --- | --- |
| `python scripts/validate_project.py` | 退出 0；含新需求映射、建议/归属评测协议结构和文档链接 |
| `uv run --offline --locked pytest -q tests/unit/test_validate_project.py` | 退出 0，**7 passed in 0.21s**；使用仓库 `.venv` 中的 UV 缓存与临时目录 |
| `uv run --offline --locked ruff check scripts/validate_project.py tests/unit/test_validate_project.py` | 退出 0，All checks passed |
| `uv run --offline --locked ruff format --check scripts/validate_project.py tests/unit/test_validate_project.py` | 退出 0，2 files already formatted |
| Skill Creator `quick_validate.py` 对三个仓库 Skill | 三个均退出 0，`Skill is valid!`；其中 `gate2-task` 和 `research-eval` 已补团队边界/建议审核指引 |
| `git -c submodule.recurse=false diff --check --ignore-submodules=all` | 退出 0；有既存 LF/CRLF 提示，无空白错误 |

默认受限环境的两次 `uv run` 因其缓存位置无写权限退出 1；设置 `UV_CACHE_DIR=D:\adaptive-browser-agent\.venv\.uv-cache` 和仓库 `.venv` 临时目录后，受影响测试与 Ruff 如上通过。未因本次文档/校验器修改重新运行全量 Python、前端测试或真实任务；之前的全量结果只对应之前的文件状态。

## 0.4 批准与权威切换

用户在审阅团队版修订后明确回复“批准 0.4 并切换权威指针”。已将 SPEC.md、PLANS.md、ADR-0002、评测协议状态、仓库 AGENTS.md、0.3 历史索引、V1 三份前瞻指针、两个相关 Skill 与校验器路由同步到 0.4。0.3 正文和 r12 原件保留历史，业务实现与付费运行未因此获得授权。切换后 python scripts/validate_project.py 退出 0；受影响校验器测试 7 passed in 0.18s，Ruff check 和 Ruff format --check 均退出 0；三个 Skill 校验均通过。

## Scoped Diff 核对与未验证项

本轮有意编辑的已跟踪文件为 `AGENTS.md`、`.github/workflows/ci.yml`，并仅调整 V1 Spec/Contracts/Test Matrix 顶部已有的前瞻指针以指向 0.4；在此前已未跟踪的 `docs/design/` 中，为 `00_DESIGN_INDEX.md`、`07_AI_CODING_WORKFLOW.md` 添加版本指针/时点说明，并新增 `adr/0002-team-runtime.md`。新增 `SPEC.md`、`PLANS.md`、`GLOSSARY.md`、现状/验证审计、公开实践研究、评测 JSON/说明、三个 Skill、标准库校验器及其测试。核对了上述文件的本地链接、版本冲突和门禁；未修改 `adaptive_agent/`、`backend/`、`frontend/src/`、`benchmark/`、`browser-use/`、旧 scorer、r12 原件、SQLite、锁文件或个人 Codex 配置。

工作区起始已有 `AGENTS.md`、V1 Spec/Contracts/Test Matrix 修改，以及未跟踪的 `docs/design/`、PR/Bug 模板；这些既有材料未清理或回滚；V1 三份文件的历史正文未改。常规 Git status 因 `.git/modules/browser-use` 权限问题不可用；采用 `--ignore-submodules=all` 只核对主仓库，**子模块清洁状态未验证**。远端 CI/Required Checks 未运行或修改；真实 DeepSeek/浏览器诊断、正式十二次评测、官方页面逐结论核源、站点漂移与真实资源生命周期未运行。离线校验绿灯不构成 Go，当前业务状态仍为 **No-Go**。
