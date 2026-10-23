# P02 B01 首次真实 pilot 失败诊断（2026-10-22）

**任务范围：** [P02-PILOT](../tasks/PREDEV_P02_P04_TASK_PACKAGE_2026-10-20.md)；`current-3` 的 B01 第一试，run ID `45ecbdf2-bc98-5fb3-9fa7-3b4f505c2c1c`，task ID `59a0f54a-e250-48df-b2ba-bbf4834a9256`。本记录是失败诊断，不改变原始捕获、评测题面或产品放行结论。执行源码指纹 `64bded4dde2eeb3e24fbb0d140894fde401455cb833097827d6343c4ac47eb7a`，计划与捕获指纹相同；[捕获版本记录](../../data/evaluation/p02-pilot-r9-20261022/45ecbdf2-bc98-5fb3-9fa7-3b4f505c2c1c/capture/source-version.json)仍明确标注 `execution_source_verified=false`，不能仅凭两个哈希证明进程当时装载的字节。用户本次授权上限人民币 10 元，专用 PostgreSQL 预算在任务提交前从 49 元原子降至 10 元；[r9 冻结工件](../../data/evaluation/p02-pilot-runtime-freeze-r9-20261022.json) SHA-256 为 `109695243fc7427d58eb6353908a288bad5e629ae7820387d1022b6ef8d020fb`。

## 实际结果与证据

- [任务终态](../../data/evaluation/p02-pilot-r9-20261022/45ecbdf2-bc98-5fb3-9fa7-3b4f505c2c1c/capture/task.json)：`partial`、`stop_reason=token_budget`、`recovery_count=0`。执行器保留该尝试并写入 [`paused_no_go`](../../data/evaluation/p02-pilot-r9-20261022/paused.json)；B02、B03 没有提交。这不是三题基线完成，也不是 B01 成功。
- [事件](../../data/evaluation/p02-pilot-r9-20261022/45ecbdf2-bc98-5fb3-9fa7-3b4f505c2c1c/capture/events.json)显示 10:49:56 UTC 入队，10:50:03 初始化子目标，10:50:12–10:50:48 完成五个 `step_evaluated`，10:50:52 终结。第 1 步的 `github.get_repository` 返回 HTTP 403，并发生一次技术重试；两次失败的调用均见[调用记录](../../data/evaluation/p02-pilot-r9-20261022/45ecbdf2-bc98-5fb3-9fa7-3b4f505c2c1c/capture/calls.json)。第 4 步浏览器提取成功，但评估结果为 `insufficient_info`；随后还有一次规划模型调用和一次浏览器提取，未形成新的 `step_evaluated`。
- 共记录 9 次完成的模型 HTTP 调用，provider 回报输入 23,860、输出 4,572 Token，合计 **28,432 / 40,000**；11 次工具调用中两次 `github.get_repository` 失败。模型已知费用 **0.04139536 元**。工具调用的 11 个金额均为未知，故[捕获清单](../../data/evaluation/p02-pilot-r9-20261022/45ecbdf2-bc98-5fb3-9fa7-3b4f505c2c1c/capture/manifest.json)和[项目账本](../../data/evaluation/ledger-after-45ecbdf2-bc98-5fb3-9fa7-3b4f505c2c1c.json)将总费用设为 `null`、结论设为 No-Go；不把工具费用推断为零。尚未与 provider 账单对账。
- [事实](../../data/evaluation/p02-pilot-r9-20261022/45ecbdf2-bc98-5fb3-9fa7-3b4f505c2c1c/capture/facts.json)只有同一项目名称与仓库 URL 两条，均为 `candidate_unverified_official`，没有人工核源状态；题目要求的两项目、各自许可证和安装命令没有齐备。[报告](../../data/evaluation/p02-pilot-r9-20261022/45ecbdf2-bc98-5fb3-9fa7-3b4f505c2c1c/capture/report.json)明确称证据不足。两条事实的 `retrieved_at` 均为 **2024-01-01**，与 2026-10-22 的调用时间不符；仅能认定该元数据有异常，不能据此断定页面在 2024 年被访问。
- 本次助手只读打开 [Microsoft 官方 Playwright Python 仓库](https://github.com/microsoft/playwright-python)及[官方安装页](https://playwright.dev/python/docs/intro)，确认当前仓库身份与 URL 与两条候选事实吻合；这是**事后助手交叉检查**，并不修复运行时来源链或代替独立人工核源。两条事实引用的是无查询定位的 GitHub 搜索端点，没有仓库页定位、官方身份依据或可信检索时间。
- 捕获清单列出的 6 个文件 SHA-256 全部复算匹配；项目账本对清单、上一版空账本的哈希绑定均匹配。[项目校验器](../../scripts/validate_project.py)对本账本退出 1，报告 `No-Go: ledger entry[0] cost unknown; stop new paid calls`，属于预期停线。停止运行链后，专用库任务 1、状态 `partial`，预算被持久设为 `halted`、理由 `pilot_partial_no_go`，本机 8000 端口无监听。

## 根因排序与证伪

1. **最可能：提取后的下一次模型请求被本地保守 Token 输入上界拒绝。** 9 次真实调用只消耗 28,432 Token，尚余 11,568；最后一次已记录模型调用后仍有浏览器提取，随后无新的模型 HTTP 调用而终态为 `token_budget`。[AgentLoop](../../backend/src/adaptive_research/agent/agent_loop.py)将预算类 `LLMError` 映射到该停因；[DeepSeekClient](../../backend/src/adaptive_research/agent/llm/deepseek.py)在发 HTTP 前以请求体 UTF-8 字节数加 128 估计输入，估计值若不小于剩余额度就抛出预算错误。这一解释与调用/事件顺序一致，但捕获故意不保存原始 Prompt 或未提交的工具正文，所以尚不能复算当时的 `prompt_bound`。**证伪：** 在冻结轨迹的离线重放中只记录安全的 `phase、remaining_tokens、prompt_bound、输出额度`，核对最后一次调用前拒绝点；若上界未超过 11,568，则检查 meter 累加和异常来源。
2. **伴随问题：匿名 GitHub API 403 使直接仓库读取失败，代理转入浏览器，增加了路径与上下文负担。** 运行环境未配置 `GITHUB_TOKEN`；事件的两次 `GitHub HTTP 403` 与当前同一仓库端点只读复查的 HTTP 403、`x-ratelimit-remaining: 0` 相符。另一次 `/rate_limit` 读取却报告 `core_remaining=9`，不能据此唯一归因为基础配额；缓存、出口差异或次级限流仍需区分。**证伪：** 保存同一请求的非敏感响应状态、限流头和时间；用本地 fake 工具重放 403→浏览器回退，并与无 403 的冻结轨迹比较 Token 与字段覆盖。不要把 403 单独宣称为最终停因。
3. **独立证据质量缺口：事实来源时间和官方归属未经可靠准入。** 两条候选事实仍可进入部分报告，但检索时间异常、来源是泛搜索 URL 且没有人工核源；它们不能支撑许可证、安装命令或第二项目。**证伪：** 用离线伪造旧时间、错误主体/版本和无定位搜索结果，验证事实准入拒绝或标未知；后续真实复查再由人工逐项打开官方来源。

[现行 V1 契约](../contracts/V1_CONTRACTS.md)以 provider 回报的输入加输出 Token 作为任务 40,000 上限的权威计数，并限制当前视图/摘要长度。这里 28,432 是实际回报用量，`token_budget` 很可能来自**下一次请求的本地预检**，并不等于已消费 40,000。需在离线重放中核查预检输入上界是否可通过裁剪上下文降低；不能直接调大任务上限来掩盖证据选择问题。目标规格的报告预留与阶段额度尚是后续设计，不能倒写为此次 V1 已实现的行为。

**离线机制复现：** 在 `backend` 工作目录用 `httpx.MockTransport` 和长度 12,000 的合成输入调用 `DeepSeekClient.complete_budgeted(..., remaining_tokens=11568)`，得到 `LLMError.kind=budget`、模拟 HTTP 请求 0 次，退出码 0。它证明该源码路径可在实际使用量不足 40,000 时本地停线；因为未保存 B01 当时的完整 Prompt，**不证明**这就是 B01 的精确触发字节数。第一次在受限沙箱运行 asyncio 诊断停滞并被中断；获准的本机运行环境复跑得到以上结果。

## 后续边界

先以现有原始记录做离线重放和价目/账单核对，保留 11 条费用未知及 B01 失败分母。若要补齐 B01–B03 同版基线，需要新的完整 cohort、当前价表与预算/授权核查；本次暂停的 cohort 不重写或续跑。完成真实基线后才按任务包修改上下文选择、事实准入或阶段预算；每次只变动一个主要因素，报告质量、Token、已知/未知费用与时延。当前 P-02 基线未通过，产品继续 No-Go。
