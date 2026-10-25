# Codex 全局配置与 Spec Kit 迁移任务包（2026-10-25）

状态：**A/B/E/F 已实施；依赖安装与初始化已获用户授权（2026-10-25 “继续”）并完成；C（constitution/模板覆盖）与 D（四包迁移、流程/配置说明更新）已实施，待新会话加载与后续 converge 复核。** 本包按 [任务模板](../engineering/TASK_TEMPLATE.md) 记录范围、基线、决定、映射与待授权命令。离线收敛不改变 r12 与 P-02 的 No-Go。

## 初始化与 C/D 实施记录（2026-10-25）

- 授权命令与结果：`uv tool install specify-cli --from git+https://github.com/github/spec-kit.git@v1.2.3` 成功（43 包，`specify-cli==1.2.3`，提交 `5ea8b1cf`）；`specify --version` → `specify 1.2.3`。
- 初始化：`specify init --here --integration codex --integration-options="--skills" --script ps --non-interactive --force` → 成功。生成：`.specify/`（constitution 模板、templates、scripts(ps)、workflows、init-options.json、integration.json）与 10 个 `.agents/skills/speckit-*`；未创建项目 `.codex/config.toml`（无原生事件）；`AGENTS.md` 未被 init 改动（init 后的 diff 仅含 B/D 步人工编辑，无 init 写入）；三项既有 Skill SHA-256 与基线一致。`specify integration status` → `Integration status: OK`、`Modified managed files: 0`、`Missing managed files: 0`。
- C：写 `.specify/memory/constitution.md`（权威顺序、冻结证据不可改、实现≠验收、ID 保留、验证诚实、授权边界、安全）。初版将“Repository Authority (override)”段直接加在三份管理模板头部；独立验收时发现这会使集成状态报 3 个 managed files modified，现已移至 `.specify/templates/overrides/`，恢复管理模板原字节。未手改任何 `speckit-*` Skill 生成文件。
- D：创建 `specs/decision-001/`、`specs/p02-research-evidence/`、`specs/p03-isolation-resilience/`、`specs/p04-formal-release/` 各含 `spec.md/plan.md/tasks.md`，按上表映射保留原 ID、依赖、IMPLEMENTED/PARTIAL/DONE(offline) 状态、验收缺口与证据链接；完成项（P-00/R0/P-01、DEC-T01 离线切片）原位保留为历史。`AGENTS.md`、`docs/engineering/WORKFLOW.md`、`docs/engineering/CONFIGURATION.md` 已更新为“Spec Kit 为功能开发主编排、G 关口叠加适用”（措辞与 WORKFLOW 一致，未声称唯一/已实际运行）；三项项目 Skill 经检索无 G0 流程引用，未改。



## 已确认决定（用户 2026-10-25）

1. 人工负责目标、重大架构/权限/费用决定和业务验收；AI 负责调研、方案、实现、测试及审查。R0/R1 按风险自主推进；R2 先有技术方案并做独立审查；提权请求由人工审批。
2. GitHub Spec Kit 稳定版 **v1.2.3** 为主开发流程；Codex 使用项目 `.agents/skills/speckit-*/SKILL.md`；AI 在任务中调度 Skills，不启用后台 workflow 或原生事件。
3. 一次迁移 DECISION-001、P-02、P-03、P-04 的未完成需求与任务，保留原 Requirement/AC/Task ID、依赖、实现状态、验收缺口和证据链接；完成项作历史保存。
4. 本地独立 Code Review 为主；Spec Kit converge 查功能完整性，之后另审固定 Git diff、失败路径、安全边界和实际测试。
5. 根规格、阶段计划、现行契约和冻结评测协议各管原有权威；Spec Kit 功能文件引用并展开所属变更，不复制或降低现行门槛。

## 基线（A 步记录）

- HEAD `f2b758e3b19638b7df62290248c0e0d0a525564c`，工作区起始 clean（`git status --porcelain` 为空）。
- Spec Kit 初始化（Codex 集成）预期写入：`.specify/`（constitution/模板/脚本）、`.agents/skills/speckit-<command>/SKILL.md`、根 `AGENTS.md` 追加说明；原生事件才写 `.codex/config.toml`，本迁移以 `--events false` 关闭，故不应生成项目 config.toml。现有三项 Skill（`agent-failure-triage`、`research-eval`、`research-implementation`）与 `speckit-*` 无命名冲突；`docs/`、原始 SQLite、r12 记录、`browser-use/` 不在写入范围。`scripts/validate_project.py` 对 `.agents/skills/` 做元数据/链接校验，新增 speckit Skills 后须复核该脚本是否需要纳入。
- 关键文件基线 SHA-256（改动前）：

| 文件 | SHA-256 |
| --- | --- |
| `.agents/skills/agent-failure-triage/SKILL.md` | 5f477f1bd0a3f9a541796b57a4f07cb0ba3b770dc8d3a35952d4d1b53c14006c |
| `.agents/skills/research-eval/SKILL.md` | 2ac91f6959a6230fbe2a11e95c803090b894d6ee0d03602231b7906b24086c5e |
| `.agents/skills/research-implementation/SKILL.md` | cb5dfa3a0abb60a7f29e4d5dc9feb408a813a580a5250be952fa1c914de33345 |
| `AGENTS.md`（改动前） | 84424ab09d9cb1773d562b152f6a1063aa004f5794d49a9548819fabd2da5716 |
| `SPEC.md` | 3a7ce99e90a012936451e957311ee5256b2fe75dbbe01ac71d7abad7f0f00024 |
| `PLANS.md` | 13f84de5968562baa6fbadc5696f236629cdff934fa49c36df2683548c7818de |
| `docs/contracts/CURRENT_CONTRACTS.md` | 40b30284ee3a65c8a7a80502a3167a08d49cbb78d04be37a83ff3f26a9e89e82 |
| `docs/evaluation/CURRENT_EVAL_PROTOCOL.json` | 1c18d53624c21b1e25f5cea5640b4c8b4a5e0cfc001f430c8d603a01d51a8507 |

（哈希取自 2026-10-25 本机 `Get-FileHash`；`AGENTS.md` 哈希为本次 B 步改动前值。）

## 已实施改动（B）

- 用户级 `C:\Users\FFFFFF\.codex\AGENTS.md`：新增 Roles（人工/AI 分工、R2 方案+独立审查、R3 人工审批）；Skills 节明确 Spec Kit 为主流程、AI 任务内调度、不启用后台 workflow/原生事件。原有风险分级、委托、审查、Git、交付规则保留。
- 用户级 `C:\Users\FFFFFF\.codex\config.toml`：顶层补 `approval_policy = "on-request"`、`sandbox_mode = "workspace-write"`（原文件无此二键）；模型、`[windows] sandbox = "elevated"`、marketplaces、plugins、MCP、projects trust 等无关设置原样保留。
- 项目根 `AGENTS.md`：Task workflow 节改为引用全局通用规则并声明 Spec Kit v1.2.3 迁移状态（授权初始化前 G0–G7 仍为现行程序，四入口权威不变）；Verification 节删除与全局重复的通用 diff/命令汇报语句，保留产品数据保护、Skill、授权边界。
- 不创建项目 `.codex/config.toml`：当前无必要运行时差异（Codex 集成的事件配置以 `--events false` 关闭）。

## 旧 ID → 新产物映射（C/D 授权后执行）

Spec Kit 目录根以初始化实际结果为准（`.specify/` 与 `specs/` 布局在 init 后核对）；下表为目标映射，旧 ID 一律保留：

| 旧产物 | 新位置（计划） | 保留内容 |
| --- | --- | --- |
| `docs/features/DECISION-001/spec.md` + `tasks.md` | `specs/decision-001/{spec,plan,tasks}.md` | Requirement DECISION-001、DEC-AC-01–07、DEC-T01–T06、依赖、IMPLEMENTED/PARTIAL 状态、验收缺口、证据链接（含 `ec4a1496`、`266a49cc`、DEC_T0* 验收记录） |
| P-02 未完成项（研究质量、FR-003/004/007/010、NFR-002/004/010、pilot 复测） | `specs/p02-research-evidence/` | 原 FR/AC ID、No-Go 状态、冻结轨迹与 pilot 证据链接 |
| P-03 未完成项（隔离/记忆/MCP/恢复/备份） | `specs/p03-isolation-resilience/` | 原 FR/AC ID、依赖、未验证边界 |
| P-04 正式验收（15 次尝试、人工核源、总账） | `specs/p04-formal-release/` | 冻结协议引用、门槛、费用上限；不复制协议 |
| 已完成项（P-00、R0、P-01、DEC-T01 离线切片等） | 原位置保留为历史，Spec Kit 文件以链接引用 | 证据与验收记录不改写 |

实施完成与验收完成分开记录（沿用 IMPLEMENTED/PARTIAL/DONE(离线) 语义）。`docs/engineering/WORKFLOW.md`、`CONFIGURATION.md` 在 D 步更新为以 Spec Kit 为主编排的说明；三项既有项目 Skill 原字节保留。生成文件不手改，项目模板差异经 `.specify/templates/overrides/` 落地。

## 待授权操作（依赖安装，R3；已于 2026-10-25 经用户“继续”授权并按下列实际命令执行成功）

```powershell
uv tool install specify-cli --from git+https://github.com/github/spec-kit.git@v1.2.3
specify --version   # 应为 1.2.3
# 在仓库根初始化（先以 --help 核对确切旗标名）：
specify init . --integration codex --events false
# 若 init 不支持既有仓库，备选：
specify integration install codex --events false
```

原因：安装 `specify-cli` 属依赖安装，仓库 `AGENTS.md` 要求单独授权；锁定 v1.2.3（2026-10-22 发布，最新稳定版）避免漂移。授权执行后核对生成文件清单（`git status` + `.specify/` 与 `.agents/skills/speckit-*` 内容），再依上表执行 C/D。

## 限制与未验证项

- 未运行付费真实评测；冻结协议、历史记录、原始失败样本未改写。
- 无 Git 提交/推送/PR/合并/部署。
- `specs/` 迁移包为一次性人工迁移产物，未经 `$speckit-analyze`/`$speckit-converge` 实际运行复核（属后续任务内 Skill 调用）。
- 新会话加载检查未做（需实际新会话核对 speckit Skills 出现在可用列表）；`scripts/validate_project.py` 对新增 speckit Skills/`specs/` 的覆盖见下方校验记录。

## 离线校验与独立审查（F，2026-10-25 实际执行）

- `python scripts\validate_project.py` → `offline validation passed; live model performance and source truth remain unverified`，退出码 0。
- `git status --porcelain=v1`：仅 ` M AGENTS.md` 与两个新增未跟踪文档，无无关改动。
- 独立只读审查（code-explorer 子代理）结论：无 Critical/Major；Minor M1（初始化后 G0–G7 关口地位含糊，已在项目 `AGENTS.md` 补句修复）、M2（本节原缺 F 步证据，本节即修复）、M3（用户级 config.toml 第 8 行既有约 600 个尾随空格，属历史内容、TOML 无害，按“保留无关内容”原则不动）。config.toml 新增两行位置经审查确认在顶层；项目 `AGENTS.md` 全部链接经审查确认存在。
- 新会话加载检查：未做（需要新会话实际启动 Codex 核对根规则与 Skill 列表，属运行时行为，本轮无法自证）。

### 风险项修复（2026-10-25，验收后追加）

| 原风险 | 处理 |
| --- | --- |
| `scripts/validate_project.py` 不覆盖 `specs/`、`.specify/` | 新增 `check_speckit()`：constitution 语义版本/Ratified/三项核心原则/四入口引用；三份 `overrides/*` 的 Repository Authority 段与存在性；四包 `spec/plan/tasks` 存在性、原 Task ID 完整、P-02 No-Go 标记、权威引用；10 个 speckit Skill 的 name/description。接入 `main()`。首次运行即捕获决策包与 P-04 包缺权威引用的真实缺陷。 |
| `constitution.md` 版本治理未纳入校验 | 同上，`**Version**: x.y.z` 与 `**Ratified**: YYYY-MM-DD` 纳入强制检查。 |
| config.toml 第 8 行尾随空格 | 已清除（仅 1 行受影响）；`tomllib` 复核 `on-request / workspace-write / gpt-6-sol / elevated`、14 个顶层节完整。 |
| speckit Skill 新会话加载未验证 | 10/10 frontmatter `name` 与目录一致且均有 `description`（Codex 发现的必要条件），该条件已纳入校验器；`codex exec` 实机会话验证因耗时长未完成，仍列未验证。 |
| converge/analyze 未实际运行 | 未运行，保持未验证；不声称已收敛。 |
| 付费真实研究与产品 Go | 未涉及；r12 与 P-02 仍 No-Go。 |

新增单测：`test_speckit_artifacts_preserve_authority_and_original_ids`、`test_speckit_rejects_lost_task_id_and_missing_no_go`、`test_speckit_rejects_missing_constitution_and_override`（负向用例验证可捕获回归）。

验收命令实测（修复后）：`python scripts\validate_project.py` → `offline validation passed...`，退出码 0；`pytest tests/unit/test_validate_project.py -q --basetemp=<repo>` → **35 passed**；`specify integration status` → OK / Modified 0；10 个 speckit Skill frontmatter `name` 与目录 10/10 一致且有 description。

遗留：仓库根残留 `.skillcheck.txt`（本次 `codex exec` 校验的输出临时文件，内容仅为 codex 启动报错，无敏感信息），因后台 codex 进程仍持有句柄暂无法删除；用户可在此后手动删除。未修改 `.gitignore`。

### 第三方独立验收（2026-10-25，CodeBuddy 复核）

实际命令：`python scripts\validate_project.py` → `offline validation passed...`，退出码 0；`specify --version` → 1.2.3；`specify integration status` → OK / Modified 0 / Missing 0；`specify preset resolve {spec,plan,tasks}-template` → 三者均解析到 `.specify\templates\overrides\*.md`（top layer from: project override）；`python -c "tomllib.load(config.toml)"` → `on-request / workspace-write / gpt-6-sol / elevated`；既有三项 Skill SHA-256 与基线一致；`Test-Path .codex` → False；`Test-Path .specify\extensions.yml` → False（无 hooks）；秘密模式扫描无命中；`pytest tests\unit\test_validate_project.py` 在系统临时目录因 `WinError 5` 环境权限失败，改用 `--basetemp` 后 **32 passed**（非本次改动引入）。

结论：权限未扩大、管理模板原字节已恢复、原 ID 与状态映射完整、No-Go 未改写。本次修复：本条记录前两处描述与实际不符（init 后 diff 说明、残留"唯一主编排"措辞）。遗留：`scripts/validate_project.py` 不覆盖 `specs/`、`.specify/`（已有 32 项单测均针对四入口与协议）。

### C/D 后复跑与二次独立审查（2026-10-25）

- C/D 完成后再次执行 `python scripts\validate_project.py` → `offline validation passed; live model performance and source truth remain unverified`，退出码 0（此记录即上文“校验记录”所指的 C/D 后运行；B 步后的首次运行早于 init）。
- `git status --porcelain=v1`：` M AGENTS.md`、` M docs/engineering/CONFIGURATION.md`、` M docs/engineering/WORKFLOW.md`，未跟踪 `.specify/`、`specs/`、10 个 `.agents/skills/speckit-*`、两份新文档；`git diff --stat`：3 文件 8 插入 5 删除；无无关既有文件改动。
- 二次独立只读审查结论：无 Critical；Major M1（P-02/P-03/P-04 初版未沿用原 Task ID 且漏 P02-GATEWAY/P02-CTX-ABLATION）→ 已按原 ID 重写三个 `specs/*/tasks.md`（P02-PILOT 标注真实诊断基线已交付/No-Go，P03-DIAGNOSE 标 PARTIAL 及已有证据）；Major M2（C/D 后校验缺口）→ 本节即修复；Minor（DEC-T02 依赖与 CI 链接、待授权块标注、WORKFLOW“唯一主编排”措辞）→ 均已修复。

### 独立验收复核与修复（2026-10-25）

- 范围：仅本次未提交迁移产物；另读用户级 `AGENTS.md` 与 `config.toml` 的授权字段。独立安全审查是只读行动，但有效父沙箱为 `workspace-write`，不宣称权限隔离。全局配置原字节基线不在仓库，故不能仅据交付记录独立证明未覆盖其他用户设置。
- 修复：三份定制模板移入 `.specify/templates/overrides/`，管理模板恢复 manifest 哈希；任务 override 将默认提交提示改为仅在本任务明确授权时提交。P-02 两条 pilot 证据链接修正；P02-GATEWAY、P03-DIAGNOSE、P03-MEMORY、P03-RECOVERY-BACKUP 补原依赖/验收缺口；P-03 阶段表原有容量/真实链路 AC 增设 `P03-CAPACITY` 缺口任务（原任务包没有独立 ID，故明确标新增），P03-MCP 依赖保持原来的 P02-LOOP-TOOLS。constitution 明确 AI 改规格、勾选任务或 checklist、converge 均不构成业务验收或产品 Go。
- 实测：`specify --version` → `specify 1.2.3`；`specify integration status` → `OK`、22 个 manifest 条目哈希全匹配、modified/missing/invalid 均 0；`specify preset resolve spec-template`、`plan-template`、`tasks-template` 均解析到 `templates/overrides/`。`python scripts\\validate_project.py` → 退出 0，明确仅离线验证；新迁移文件 55 条本地链接、断链 0；`git diff --check` → 退出 0，只有现有 CRLF 提醒。
- 定点测试：`python -m pytest -q backend/tests/unit/test_validate_project.py` 两次因默认 `AppData\\Local\\Temp\\pytest-of-FFFFFF` 拒绝访问而发生 29 项 fixture 错误、3 项通过；改用可写目录 `--basetemp C:\\Users\\FFFFFF\\.codex\\visualizations\\2026\\10\\25\\01a172d3-ef71-7e00-bfe9-91b4bc1716d1\\pytest_migration_acceptance` 后 **32 passed**。前两次失败为环境访问问题，不算测试通过。
- 未做：未启动真实模型/浏览器或付费评测，未运行四包的 `$speckit-converge`/`$speckit-analyze`，未在另一新会话验证 Skill 自动发现，未提交/推送/PR。冻结协议与历史证据仍是当前唯一放行口径；r12 与 P-02 保持 No-Go。
