# V3 工程配置：已选择的模块化方案 B

状态：工程配置已落地，产品功能仍受[现行四入口](../README.md)约束。此页说明目录的用途与加载方式，不新增业务要求、Codex 权限或自动执行能力。旧文件去向见[迁移映射](../decisions/V3_CONFIG_MIGRATION_MAP.md)；原配置批次见[2026-10-23 验收](../audits/V3_CONFIG_ACCEPTANCE_2026-10-23.md)，当前修复见[2026-10-24 复审](../audits/CONFIG_REVIEW_2026-10-24.md)。

```text
AGENTS.md                              # Codex 仓库规则与权威入口
SPEC.md / PLANS.md                     # 现行目标与阶段计划
.specify/                              # Spec Kit v1.2.3：constitution、管理模板、overrides/、脚本、workflow
specs/                                 # Spec Kit 功能包（spec/plan/tasks）；迁移包保留原 Requirement/AC/Task ID
.agents/skills/                        # 三项任务型 Skill + speckit-*（Spec Kit Codex 集成，事件关闭）
.github/PULL_REQUEST_TEMPLATE.md       # 人工填写的交付证据
.github/workflows/ci.yml               # 现有离线与 PostgreSQL CI
docs/
  README.md                            # 文档导航，不另立规格
  decisions/                           # V3 决策、权威变更提案、迁移映射
  design/adr/                           # 0005 运行架构；0006 产品方向
  engineering/                          # G0–G7 关口、配置说明、任务模板
  features/DECISION-001/               # 已批准需求与切片；实际进度见 tasks.md
  testing/STRATEGY.md                  # 风险驱动 L0–L6 检查选择
  evaluation/CURRENT_EVAL_PROTOCOL.json # 唯一正式评测协议
  audits/                              # 按版本和范围保存实际验收
  archive/                             # 不改写的历史版本与证据
scripts/validate_project.py            # 离线引用、协议、Skill 与归档索引字节校验
```

## 使用与维护

| 入口 | 为什么存在；输入 → 输出；触发与维护 | 权威、发现及验证 |
| --- | --- | --- |
| 根 `AGENTS.md` | 维护者在产品／架构／权限边界变化时更新；从现行四入口与 ADR 提炼简短导航 → Codex 工作约束。无需按每个模块再建规则文件。 | Codex 从项目根到当前目录读取；本仓库仅有根文件。以实际会话所收到规则、文件大小和引用校验核对，不能把文档链接当成强制执行。 |
| `.agents/skills/` | 维护者仅在实施、失败归因或真实评测流程发生可重复变化时修订；任务类型 → 专项步骤与证据。三项现存 Skill 足够；一般文档或单测不触发专项 Skill。 | Codex 在仓库路径扫描 `SKILL.md` 的名称与描述，正文按需加载。离线校验检查元数据和本地链接；实际自动选择要在对应任务中观察。 |
| `.specify/` 与 `specs/` | Spec Kit v1.2.3（Codex 集成，原生事件关闭）于 2026-10-25 经授权初始化；constitution 与 `.specify/templates/overrides/` 的 spec/plan/tasks 模板含本仓库权威覆盖，功能包迁移自 DECISION-001/P-02/P-03/P-04 并保留原 ID。维护者不手改管理模板或 speckit Skill 生成文件。 | `$speckit-*` 逐条在任务内执行、逐结果人工复核；四入口权威与 G 关口不因 Spec Kit 豁免；离线 converge 不等于产品 Go。`scripts/validate_project.py` 的 `check_speckit` 校验 constitution 版本/原则/四入口引用、三份 override 的权威段、四个功能包的原 Task ID、P-02 的 No-Go 标记、权威引用，以及 10 个 speckit Skill 的 name/description；`specify integration status` 与模板解析另行核对。 |
| `.github/` | PR 作者填真实 Task／AC、测试、CI、风险和授权；现有 Actions 运行离线与数据库检查。模板在交付时触发，CI 在 GitHub 事件触发。 | GitHub 模板是提示，不替代人工 Review；Actions 是否执行及分支门禁须查看远端实际结果。当前仅校验本地 YAML 内容与模板链接。 |
| `docs/decisions/`、`docs/design/adr/` | 用户作产品或架构决定时记录依据、范围和待决项；变更提案 → 获批后才更新正式规格／契约。维护者避免复制原验收门槛。 | 决策记录解释选择，`SPEC.md`、`PLANS.md`、目标契约和评测协议仍为现行要求；链接及状态可离线检查。 |
| `docs/features/`、`docs/engineering/` | 重要需求从 AC → 可验收切片；获批任务用模板记录范围、测试与证据。小变更可合并到任务或 PR，不强制新文档。 | `AGENTS.md` 指向流程；任务执行者按需读取。需求草案不能越过现行四入口；验收检查 Task／AC 与实际证据。 |
| `docs/testing/`、`docs/evaluation/`、`docs/audits/` | 按变更风险选 L0–L6；正式评测按冻结协议执行；审计记录指定版本的实际结果。配置变动、真实运行和阶段验收分别触发。 | 策略只决定检查方式，协议独占正式题面／门槛，审计不改历史。校验脚本锁定协议和归档哈希；真实成功仍需授权运行与人工核源。 |
| `docs/README.md`、`scripts/validate_project.py` | 文档增删或链接变更时维护导航及离线检查列表；路径 → 可读入口与错误报告。 | README 不另立权威；CI 调用校验器，本地运行同一脚本核验引用、冻结协议及历史归档的工作区／Git 索引字节。 |

## Codex 实际加载边界

[OpenAI 官方 AGENTS.md 文档](https://learn.chatgpt.com/docs/agent-configuration/agents-md)说明 Codex 在一次运行开始时按项目根到工作目录发现规则；[官方 Skill 文档](https://learn.chatgpt.com/docs/build-skills)说明仓库 `.agents/skills/` 以 `name`／`description` 参与发现，正文按需读取。当前会话的可用 Skill 列表确实包含三项仓库 Skill，且根规则已进入任务上下文。新文件或 Skill 修订在新会话中重新核对；本轮静态检查不宣称已模拟一次未来任务的自动 Skill 选择。

本仓库没有项目 `.codex/config.toml`、`.codex/agents/` 或新增 MCP 配置。当前方案不需要项目级模型、权限或工具覆盖；[OpenAI 官方配置说明](https://learn.chatgpt.com/docs/config-file/config-basic)指出项目配置只在受信任项目加载。今后若出现具体、可验证的缺口，另提案说明字段、权限、维护者和生效检查。没有声明不存在的 Hook、自动命令或只读子代理隔离。
