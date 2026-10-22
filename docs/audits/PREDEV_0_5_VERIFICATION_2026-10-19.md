# 0.5 开发前准备验证记录

日期：2026-10-19（Asia/Shanghai）。范围仅为规格、计划、目标契约、ADR、研究记录、仓库指令/Skill、评测协议、离线校验器/单测及 CI 名称。该记录不取代 [0.4 历史验证](PREDEV_VERIFICATION_2026-10-18.md)，不构成业务、容量、安全或部署验收。

## 实际结果

| 命令或检查 | 结果 |
| --- | --- |
| `python scripts/validate_project.py` | 退出 0；输出 `offline validation passed; live model performance and source truth remain unverified`。覆盖本地 Markdown 链接、0.5/0.4 版本指针、需求—任务—AC 映射、历史快照哈希、Skill frontmatter、B/G 冻结题面/字段及 G3 结构。 |
| `python -m pytest -q tests/unit/test_validate_project.py --basetemp <workspace-unique-path>` | 退出 0；`9 passed in 0.09s`。默认 Windows 临时目录受沙箱限制，因此使用先核对不存在的仓库内唯一目录。 |
| `python -m ruff check scripts/validate_project.py tests/unit/test_validate_project.py` | 退出 0；`All checks passed!`。 |
| `python -m ruff format --check scripts/validate_project.py tests/unit/test_validate_project.py` | 退出 0；`2 files already formatted`。 |
| `python -m compileall -q scripts/validate_project.py tests/unit/test_validate_project.py` | 退出 0，无错误输出。 |
| Skill Creator `quick_validate.py` | `research-implementation`、`agent-failure-triage`、`research-eval` 均退出 0，`Skill is valid!`；Windows 运行第三项时设置 `PYTHONUTF8=1`，因为脚本默认 GBK 读取 UTF-8 的 ≥ 字符失败。 |
| `git -c submodule.recurse=false diff --check --ignore-submodules=all` | 退出 0，仅有 Git 换行格式提示；Git 不覆盖未跟踪文件，另用脚本检查当前核心文档尾随空白，0 条。 |
| [LangGraph](https://docs.langchain.com/oss/python/langgraph/checkpointers)、[PostgreSQL](https://www.postgresql.org/docs/current/sql-select.html)、[Docker Windows](https://docs.docker.com/desktop/setup/install/windows-install/)、[Caddy](https://caddyserver.com/docs/automatic-https) 官方入口 | 2026-10-19 网页只读打开成功；研究记录中的部分旧固定提交链接未逐个重新访问，不能称全部外链已核实。 |

`SPEC_0.4.md` 与 `PLANS_0.4.md` 是 2026-10-18 原件逐字节副本，SHA-256 分别为 `31b8e45383ce0b39d665ccfe4e6bd813bd6439248c17b446d6b0f4baedf12847` 与 `3741de432b9396d0bc08bcc5a6c685332111dc459af06a3f10efde4a93a60701`。G2 旧协议、B/G 题面和字段仍作冻结比较；r12 原件与评分未修改。项目或个人 `.codex/config.toml` 未新增。

## 未执行及余项

没有安装依赖、修改业务代码、运行模型/浏览器真实任务、部署、提交、推送或建立 PR。Docker 命令本机未识别，WSL 状态因权限未核实；Chromium 双任务、PostgreSQL、HTTPS、外联私网阻断、跨账户授权、备份恢复和 15 次正式任务均留待 G3 阶段。现有业务仍 No-Go。

最后一次 pytest 创建的唯一临时目录 `.pytest-g3-d00401ed94884ea4b8409ef08f0f261f` 曾因自动审批服务容量不足暂留；2026-10-19 在确认其绝对路径位于本仓库、名称和内容符合预期后，经审批成功删除。原有 dirty 工作树、子模块和无关文件未被重置或提交。
