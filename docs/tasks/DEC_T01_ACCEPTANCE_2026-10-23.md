# DEC-T01：P-02 首个研究质量切片与离线验收

日期：2026-10-23（Asia/Shanghai）。状态：**DONE（限定为离线切片）**；真实研究质量和产品放行仍为 **No-Go**。

| 字段 | 记录 |
| --- | --- |
| Task／需求／验收 | DEC-T01；[切片定义](../features/DECISION-001/tasks.md)、FR-002／003／004、DEC-AC-02／06；关联 AC-002／003／004。 |
| 用户价值与可观察目标 | 减少到达相关页面后继续导航而没有取证的路径；本地 Token 预检拒绝时在不重发已启动请求的条件下保留关键证据、尝试一次更小的规划上下文。 |
| 依赖与授权 | P-01 假任务关口及 P-02 r11 同版三题诊断已完成；用户授权 DEC-T01 本地开发、离线验收与 Git commit。本切片不运行付费模型或浏览器。 |
| 基线与保护 | 源码基线 `aafd23cb82ae907ab8b1c90e3b6367c0c54e4cdb`；使用独立 `codex/dec-t01` 工作树，原工作区的 DEC-T02–T05 和原始 r11 工件不修改。B01 原捕获事件 SHA-256 `d40796271738cc90df0b88c3004d0d7a5015af46f90e3cc0d73061a66c12a72f`；预算补证 SHA-256 `3bd610928a0522d78d2d7f42704069f9b245abec67c9cc3e1b6850ed16b9672b`。 |
| 范围与接口 | 只改 Planner、Context 和动作指引及对应离线测试；不改六路 API、任务状态、持久结构、调用账本、事实准入规则或五次无进展阈值。预计工作量 1–2 个兼职工作日，最大未知是真实模型是否遵循新取证指引。 |
| 实施 | 对已到达的相关页面提示先提取证据；常规上下文保留近期事实 ID 和主体；仅 `budget`、`provider_request_started=false` 且没有已报告用量时构造更小的当前目标／页面／失败线索／事实视图，至多压缩重试一次。压缩后仍不足或结果不明时沿既有失败路径停线。 |
| 回滚 | 单独回退 DEC-T01 提交；配置提交和 r11 证据不回退、不改写。 |

## 同口径离线证据

`backend/tests/unit/test_dec_t01.py` 从 r11 脱敏事件核对 B01 连续三次导航及 `no_progress` 终态，从只读预算补证读取 B02 的 −43 和 B03 的 −7,048 输出余量。它把这些安全投影送入**受控假模型**，不复原原始 Prompt 或浏览器页面。首次对基线运行该文件：**5 failed、1 passed，退出码 1**；其中已发请求不重试的保护原本通过。新增“压缩回复动作无效”边界后再次先红：**1 failed、6 passed，退出码 1**，发现可能发生第二次压缩重试；限制为整次规划最多一次后转绿。新增“预检标志与已报告用量矛盾”边界后先红：**1 failed、7 passed，退出码 1**；拒绝自动重试后转绿。

| 检查 | 本切片结果 |
| --- | --- |
| `python -m pytest -q --basetemp ../.tmp/pytest-dec-t01-final2 tests/unit/test_dec_t01.py tests/unit/test_planner.py tests/unit/test_context_manager.py tests/unit/test_evaluator.py tests/integration/test_agent_loop.py`（工作树 `backend/`，使用项目已有 `.venv`） | 96 passed，退出码 0；覆盖取证指引、B02／B03 预检、一次压缩、已发请求及已报告用量不重试、fact ID／来源、错来源准入及既有无进展停线。 |
| `python -m ruff check --config pyproject.toml` 与 `python -m ruff format --check --config pyproject.toml`（仅受改 Python 文件） | 分别退出码 0；`All checks passed!`，4 个文件格式符合要求。 |
| `python scripts/validate_project.py`（隔离工作树根） | 首次退出码 1，29 项冻结归档字节哈希不匹配；新 Windows 工作树按全局 `core.autocrlf=true` 检出了不同于原始冻结字节的行尾。将 37 个**仅隔离工作树内**的已跟踪归档文件从已通过校验的原工作区逐字节复制后重跑，退出码 0；原工作区与 Git 提交中的归档内容未改。 |
| `git diff --check --ignore-submodules=all` 与 `git diff --cached --check` | 均退出码 0；行尾提示不属于空白错误。暂存仅包含本切片六个文件。 |

## 验收判定与限制

| 条件 | 判定 |
| --- | --- |
| DEC-AC-02：关键证据准入与可追溯 | fact ID／来源在正常及压缩上下文的离线用例中保留，既有错来源准入回归通过；真实官方身份与逐结论人工核源**待验证**。 |
| DEC-AC-06：预算、取消与诚实停线 | 本地预检的单次压缩、第二次拒绝、已发请求和已报告用量不可重试通过离线用例；取消、失租与真实费用未在本切片运行，继续沿用现有契约并**待真实复查**。 |
| B01–B03 真实研究质量 | r11 原失败保留；没有改动后的真实模型／浏览器尝试，不能宣称字段完整度、成功率或费用改善。P-02 继续 No-Go。 |

未运行 L3 PostgreSQL、L4 浏览器界面、L5 实际故障注入或 L6 真实模型／浏览器评测；本切片未更改这些边界。隔离工作树的归档文件因恢复冻结字节可能显示为工作区修改，**不暂存、不提交**。本文件所在提交即本切片版本；实际运行若失败，按冻结协议另行诊断和授权复测，不修改原样本。
