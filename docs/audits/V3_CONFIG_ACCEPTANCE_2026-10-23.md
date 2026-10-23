# V3 工程配置本地验收

日期：2026-10-23（Asia/Shanghai）。范围：本轮[已选方案 B](../engineering/CONFIGURATION.md)的入口、流程、迁移映射、Skill 引用、PR 模板和离线校验。此记录只判断工程配置是否可用于下一次**获批准的任务**，不判断 DECISION-001 功能、真实研究质量、正式评测、远端 CI 或 GitHub 门禁。

## 变更与权威核对

| 检查 | 实际结果 |
| --- | --- |
| Inventory → Mapping | [迁移映射](../decisions/V3_CONFIG_MIGRATION_MAP.md)逐组列出保留、修订和新入口；没有迁移、归档或删除现有文件。两个 Skill 的旧流程指针已改到现行 [G0–G7 流程](../engineering/WORKFLOW.md)。 |
| 产品与历史边界 | [ADR-0006](../design/adr/0006-python-open-source-decision-agent.md)和[DECISION-001 草案](../features/DECISION-001/spec.md)标明未替代四个现行入口；`SPEC.md`、`PLANS.md`、`docs/contracts/CURRENT_CONTRACTS.md`、`docs/evaluation/CURRENT_EVAL_PROTOCOL.json`、历史验收和原始失败记录未修改。 |
| Codex 规则发现 | 根 `AGENTS.md` 存在、非空，大小 3553 字节；仓库内无嵌套 `AGENTS.md`／override。当前会话收到该项目规则。[OpenAI 官方说明](https://learn.chatgpt.com/docs/agent-configuration/agents-md)支持根到当前目录的加载机制；新会话是否读取更新后字节尚未单独做启动探针。 |
| Skill 发现 | `.agents/skills/` 下恰有 `research-implementation`、`agent-failure-triage`、`research-eval` 三项，均在当前会话可用 Skill 列表中；名称／描述与目录对应。[官方 Skill 文档](https://learn.chatgpt.com/docs/build-skills)说明此路径与按需加载。实际未来任务是否正确自动选择，须在首个对应任务观察，不以文件存在代替行为验证。 |
| 项目配置与代理 | 本仓库不存在 `.codex/config.toml`、`.codex/agents/`；未新增 MCP、Hook 或项目权限配置。现有根规则与三项 Skill 满足本轮用途，无额外运行设置需要验证。 |
| GitHub 交付 | PR 模板包含 Task／AC、契约、实际测试／CI、Agent 证据、Review、授权和回滚；现有 CI YAML 未修改。未创建 PR，未检查远端 Actions 或 Ruleset 实际权限。 |

## 本地执行证据

| 命令或检查 | 结果 |
| --- | --- |
| `python skill-creator/scripts/quick_validate.py .agents/skills/<name>`，`PYTHONUTF8=1`，逐个检查三项 | 三项均返回 `Skill is valid!`，退出码 0；验证格式，不证明自动触发。 |
| `.venv/Scripts/python.exe scripts/validate_project.py` | 退出码 0：`offline validation passed; live model performance and source truth remain unverified`；覆盖本轮新文档、Skill 链接与冻结协议校验。 |
| `.venv/Scripts/python.exe -m pytest -q --basetemp <工作区内新目录> backend/tests/unit/test_validate_project.py` | 退出码 0：`31 passed in 4.95s`。使用新建工作区临时目录，避开系统 Temp 的访问拒绝。 |
| `.venv/Scripts/python.exe -m ruff check --config backend/pyproject.toml scripts/validate_project.py` | 退出码 0：`All checks passed!`。 |
| `.venv/Scripts/python.exe -m ruff format --check --config backend/pyproject.toml scripts/validate_project.py` | 退出码 0：`1 file already formatted`。 |
| `git diff --check --ignore-submodules=all` | 退出码 0；Git 仅提示工作副本未来可能进行 LF→CRLF 转换，没有空白错误。未跟踪新文档由链接校验覆盖内容引用。 |

## 判定边界

**本地配置批次通过**：上述离线检查均通过，链接无失效，四个现行入口及历史原件保持原状。新会话加载、未来任务的 Skill 自动选择、远端 CI 与实际工程收益属于后续使用证据；若失败，修正相应配置并追加同口径记录。P-02 真实 Pilot 与正式评测仍为 **No-Go**，不能据此解锁业务实现或付费运行。
