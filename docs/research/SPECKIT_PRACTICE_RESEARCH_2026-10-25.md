# Spec Kit 企业实践与高星仓库研究记录（2026-10-25）

目的：为 Codex 全局/项目配置重构与 Spec Kit 主流程迁移提供外部依据。仅作取舍参考，不改变本仓库四入口权威；结论以实际安装版本（锁定 v1.2.3）生成物为准。

## 来源与版本

| 来源 | 版本/日期 | 获取方式 |
| --- | --- | --- |
| github/spec-kit 仓库主页（142.8k stars，MIT） | main 分支，抓取于 2026-10-25 | web 抓取 README |
| github/spec-kit Releases | v1.2.3 = 最新稳定版，2026-10-22 由 github-actions 发布（提交 5ea8b1c）；近期：1.2.2（10-19）、1.2.1（10-16）、1.2.0（10-13）、1.1.3（10-09） | Releases 页 |
| Spec Kit 官方文档 Codex CLI 集成页 | 无页面级时间戳（持续更新文档） | github.github.io/spec-kit/integrations/codex.html |

## 关键事实

1. **Codex 集成**：集成键 `codex`；技能写入 `.agents/skills/speckit-<command>/SKILL.md`（直接写文件、非符号链接）；原生事件配置写 `.codex/config.toml`，可用 `--events false` 关闭；`--integration-options="--skills"` 为当前唯一布局。调用语法为聊天内 `$speckit-*`（非斜杠）。声明多安装安全，但与其他共享 `.agents/skills/` 的集成共存前需核对共享规则。
2. **v1.2.3 变更要点**（与本次相关）：Presetignore 支持、`none` 集成选项（仅共享脚手架）、事件清理保留 dispatcher 所有权、PowerShell 括号路径字面处理（对 Windows 仓库有利）、集成指引对齐。
3. **定制机制**：Constitution（项目级一次）、Preset（组织级模板/命令/术语）、项目本地覆盖（单模板）、Workflow overlay、Extension/Bundle/Catalog。与本仓库“constitution 守权威顺序、命令 override、不手改生成文件”的方案对应。
4. **安装**：`uv tool install specify-cli --from git+https://github.com/github/spec-kit.git@v1.2.3` 可锁版本；要求 Python 3.11+、uv。
5. **主流程**：`constitution → specify → plan → tasks → implement → converge`，一次一个命令、逐结果人工复核；扩展（bug/assess）另装。企业实践要点：Spec Kit 官方明确“在 agent 聊天内逐条执行并复核”，与本仓库决定 2（AI 任务内调度、不开后台 workflow）一致。

## 局限

- 未实测安装与初始化（依赖安装待单独授权）；以上为文档/页面陈述，未经本机验证。
- Releases 与文档页无作者/页面修订时间，Spec Kit 迭代快（近三周连发 1.2.0–1.2.3），锁定 v1.2.3 后不追新。
- 142.8k stars 为抓取时点数字；星标不替代实测。
- 未做其他企业案例（Linear 等）一手核验，仅通过 Spec Kit README/Release 描述获知；如需扩充另做研究。
