# DECISION-001 与 P-02 本地离线实施记录

日期：2026-10-23。仅记录当前未提交工作区的离线检查；源码版本须在未来实际运行时重新绑定 Commit SHA 或快照哈希。本记录不改变 `current-3` 评测协议、P-02 No-Go 或历史 r11 结果。

| 范围 | 已实现或检查 | 仍未验证 |
| --- | --- | --- |
| P-02 | Planner 对已到达的相关页面优先提取的指引；仅在 provider 请求未开始的本地预算预检失败后，保留当前子目标、页面、失败线索与 fact ID 的一次压缩重试；常规 Context 增补 fact ID。离线测试覆盖不重试已发请求、第二次拒绝停线、既有来源错配准入。 | 无冻结 r11 轨迹的模型重放结果；不能推断 B01–B03 已可成功，真实浏览器和付费复测须逐次授权。 |
| DEC-T02 | 可选决策上下文校验、任务事务内 PostgreSQL JSONB 快照、幂等比较、Worker 执行与恢复传递，旧 `goal` 请求兼容；新增 Alembic `20261023_07`。 | 未在一次性 PostgreSQL 测试库执行新增持久集成测试或迁移升级。 |
| DEC-T03–04 | 从已准入事实构建候选 × 条件矩阵；缺证保持 unknown，错主体／缺片段不支撑判断，冲突保留；仅在唯一候选的所有硬条件有机器依据且其他候选硬条件判断明确时产生待人工核实建议。缺推荐时任务不以 full 完成。 | 模型语义判断、官方身份和推荐价值尚无人核源；不能据 Mock 判定真实准确率。 |
| DEC-T05–06 | 前端可选表单与矩阵展示；旧流程保留。独立人工决策复核模板已备，正式分母不变。 | 浏览器 E2E、人工逐事实核源和独立决策质量复核尚未执行。 |

离线结果：`python -m pytest -q --basetemp .tmp/pytest-v3-verify-7d92 backend/tests` 为 **616 passed、3 skipped、1 deselected**；新功能相关回归 80 passed；Ruff 检查与格式检查通过；`python scripts/validate_project.py` 退出 0。前端 `npm test -- --run` 为 27/27、`npm run type-check` 与 `npm run build` 退出 0。`git diff --ignore-submodules=all --check` 退出 0（仅行尾提示）。第一次直接运行全量 pytest 时 126 项因系统 Temp 路径权限被拒而无法建立 fixture；改用工作区 `--basetemp` 后通过，不将该环境错误记为业务失败。

当前结论：**离线实现可继续审查；真实研究质量与产品放行仍为 No-Go。** PostgreSQL L3、真实浏览器、人工官方核源、费用与正式十五次评测均不得写成已通过。

## 2026-10-24 工作区审查与修复

- 审查覆盖本次工作区的后端、迁移、前端、测试和文档。修复了 Agent 发现候选的大小写重复 ID、无效重复判断行遮蔽有效判断行，以及矩阵只给 fact ID 而缺少来源、最小片段和记录时间的问题。条件化建议现在列出偏好判断与其 fact ID。新增对应回归和前端核对展示。
- `browser-use` 子模块工作树经显式 Git dir 检查为空。当前沙箱中的 Git 无法 `chdir` 进入 `.git` 目录；仓库本地配置 `submodule.browser-use.ignore=dirty` 后，普通 `git status` 可用且仍检查 gitlink 提交指针。此设置只在本机 `.git/config`，不随提交分发；每次需要核对子模块内部改动时执行 `git --git-dir=.git/modules/browser-use --work-tree=browser-use status --porcelain=v1`。
- 最终离线检查：`.venv/Scripts/python.exe -m pytest -q --basetemp .tmp/pytest-final-1024 backend/tests` 为 **618 passed、3 skipped、1 deselected**；`.venv/Scripts/ruff.exe check backend` 和 `ruff format --check backend` 通过（120 files already formatted）；前端 `npm test -- --run` 为 **27 passed**，`npm run type-check`、`npm run build` 退出 0；`.venv/Scripts/python.exe scripts/validate_project.py` 退出 0；`git diff --check` 退出 0（仅 Git 行尾转换提示）；`alembic -c migrations/alembic.ini heads` 显示 `20261023_07 (head)`。
- PostgreSQL 集成测试需要新的一次性测试库，本轮未运行；Alembic 升级、浏览器端到端、真实模型研究、人工官方核源及正式评测均未验证。上述离线检查只支持本地代码验收，不解除 P-02 和产品 No-Go。
