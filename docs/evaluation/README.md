# 现行评测协议

[CURRENT_EVAL_PROTOCOL.json](CURRENT_EVAL_PROTOCOL.json) (`current-3`) 是正式开发与后续验收的唯一现行机读评测入口，受 [现行规格](../../SPEC.md)与[现行计划](../../PLANS.md)约束。[`current-2` 原字节归档](archive/CURRENT_EVAL_PROTOCOL_current-2.json)的 SHA-256 为 `6fa06e0ff2cb73b6fcf246130da23aa559b9b5256a9ef46d8065496850e7a53f`；更早的 [`current-1` 原字节归档](archive/CURRENT_EVAL_PROTOCOL_current-1.json)仍保留。`current-3` 只修正费用对账、pilot 未验证权限与人工复核绑定；九题题面、字段与 15 次门槛不变。协议描述**尚未执行的验收**，不能作为成功率、成本或岗位竞争力成果。任何付费真实运行均需单独授权。

已实现的离线计划入口 `python -m adaptive_research.evaluation.current --phase pilot --output data/evaluation/<new-file>.json` 只校验冻结题面、生成 B01–B03 三条预览和源码/锁文件哈希；`--phase formal` 预览 15 次，`--execute` 会拒绝。输出标记尝试和 provider 调用均为 0。[当前 pilot 计划](../../data/evaluation/p02-pilot-dry-run-r6-20261022.json)与[空项目总账基线](../../data/evaluation/p02-project-ledger-initial-20261022.json)均为离线工件。价格依据为[2026-10-22 DeepSeek CNY 快照](DEEPSEEK_CNY_PRICING_2026-10-22.json)，旧快照保留；逐调用计算仅覆盖快照列出的 token 价格，Search/Fetch 等非模型计费仍须单独核对。快照到期、缓存拆分/模型/时段不明则费用为 null，真实执行前须重新核对官方单价并冻结新批次。

`python -m adaptive_research.evaluation.pilot_budget` 默认只离线检查价表；单独授权后的 `--arm` 可在空库写入同库 pilot 预算上限，Worker 在未建额时拒绝带价表的模型调用。`adaptive_research.evaluation.pilot_capture.capture_attempt` 对已有 pilot 任务只读导出七份带 SHA-256 的脱敏诊断工件。`python -m adaptive_research.evaluation.pilot_runner` 默认无动作；经单次真实运行及费用授权后，其 `--execute` 模式才可在本机 API 上按幂等键串行提交、等待、捕获 B01–B03，并逐次追加只写一次的项目总账。它在未知费用、非完成终态、超时或证据不稳时停线；全部捕获也只标记“待人工复核”，不生成合格结果。当前预算表为空，没有真实尝试、人工核源或 provider 账单对账。详见[P02 pilot 准备证据](../tasks/P02_PILOT_PREP_2026-10-21.md)。

## 固定任务与判定

B01–B03 的原题与字段继承 [V1 benchmark 协议](../benchmark/BENCHMARK_PROTOCOL.md)，G01–G03 继承 [G2 历史协议](G2_EVAL_PROTOCOL.json)及[公开预注册](../archive/design-0.3/05_TEST_AND_EVALUATION.md)，O01–O03 继承 [G3 归档协议](G3_EVAL_PROTOCOL.json)。协议冻结后，若题面、字段或评分改变，必须新建协议版本和完整新批次；旧原始记录及评分不改写。O01/O02 的社区补充为空数组；O03 必须有标为 `community_supplement`、写明局限的社区经验，它不能代替官方发布事实。

优化前 pilot 仅 B01–B03 各一次，须在定点质量改动前使用同一代码、模型、预算、评分和环境修订。系统性故障或费用不可界定时暂停，保留已发生尝试；修复后如要重新比较，须预算内另起完整三题 pilot，否则标不可比。正式批次为 15 个独立 task/run ID：B 各三次，每题至少 2/3 完整成功；G 各一次，合计至少 2/3；O 各一次，必须 3/3。失败、超时、取消和中断均保留并计入分母。旧 68/75 聚合字段阈值不作现行放行门槛。

P-02 pilot 是研究质量诊断。若账户功能尚未接入，`access_checks` 中三个值填 `null`，意为未验证；`false` 只表示实际检查失败。pilot 的候选 `completed/full` 仍须有人工核源和其他完整证据，但**不计算正式放行成功**。正式批次三个访问检查必须是布尔值，任何一个缺失或为 false 都不能把该条算作 full 成功。

完整成功须同时具备持久化 `completed/full`、本次报告中的全部固定字段、每条实质结论经人工打开官方来源核实、由事实 ID 支持且写明适用条件与未知项的建议、owner 可见而其他成员不可见及不能取消、UI/API/应用持久层/SSE 一致。初始演示在本机进行，五个账户包含管理员；隔离、容量和恢复另依现行规格验收。用 `completed` 状态、自动评分或离线测试单独证明不了完整成功。当前 r12 的 18 次正式尝试全部未完整成功，另有三次独立 UI 诊断未产出合格报告；这些是历史失败证据，不并入新协议分母。

## 每次尝试的证据

每次记录满足协议的 `result_record_contract`，包括 fact ID、官方身份依据、最小证据片段/定位/抓取时间、机器准入与人工官方核实的分离状态，及字段/结论到 fact ID 的引用；完整成功与冲突尝试还需隔时二次核源，注明同人或独立复核。调用尝试账本明确 `started`、返回结果或 `unknown_outcome`；调用轨迹、报告快照、原始尝试 JSON 与本地只读复查清单分别保存**相对路径和 SHA-256**；没有报告的失败条目将 `report_artifact` 填 `null`。人工复核记录的 `report_sha256` 必须与报告快照一致，复查清单也保留该哈希，确保核源结论绑定到具体报告版本。四类工件路径均相对于批次结果 JSON 所在目录，文件必须真实存在且哈希吻合。已知费用为零只用于确知免费；未知用量或费用填 `null`，不能写零。轨迹脱敏，不保存密钥、Cookie、授权头或任意页面正文。

每次模型或工具调用的已知计费金额求和，必须等于该尝试的 `known_cost_cny`；无未知计费调用时，`total_cost_cny` 必须与已知金额一致。另保留跨 pilot、诊断、中断、重跑、正式批次和机动费用的项目总账。总账 `batches` 引用已完成的 pilot/正式批次结果 JSON 及哈希，`entries` 逐次记录 run/task ID、预算分配、授权引用、已知/未知费用和原始证据工件；批次内条目必须与总账逐项一致。中断或未形成完整批次的尝试也单列条目。校验器检查重复 run ID、缺失批次条目、阶段和 299 元总上限；它不能证明账本没有漏记其他实际付费调用，最终须人工与 provider 用量或账单对账。机动费用单独授权，不自动抬高 pilot、诊断或正式批次的上限。

`comparison` 逐次记录 cohort、环境指纹、模型、预算指纹、评分修订、来源时间窗与漂移、预算可比性。同一 pilot 或正式批次内代码、模型、预算、评分与环境保持冻结；正式批次中修复问题需另起完整批次，失败不替换。B03/G03/O03 的“最新发布”按每次开始时官方页面核验，记录漂移且不更换题面。优化前 B pilot 与优化后正式批次的各题首轮只做**描述性配对**；模型、预算或来源变化要明示，不宣称因果改善。冻结正式批次前记录代码及上游浏览器指纹、依赖锁、OS/浏览器、网络、模型、预算、Prompt 哈希与评分规则。原始来源变化导致无法核验时记未验证，不以更换题目或删减字段补救。

每次运行的状态、失败原因、调用轨迹、人工来源核验、费用缺口及可比条件均随失败样本保留。费用无法界定或余额不足以完成批次时停止并记 **No-Go**。新增真实运行总费用严格低于 300 元，其中 pilot 上限 49 元、诊断上限 30 元、正式批次上限 200 元、机动上限 20 元；这些是支出上限，不是已花费用。

## 离线检查与历史边界

```text
python scripts/validate_project.py
python scripts/validate_project.py --results path/to/complete-batch.json
python scripts/validate_project.py --ledger path/to/project-ledger.json
```

结果校验器只能检查题面冻结、记录结构、数量、文件哈希和成功声明的一致性。官方页面内容、真实权限、浏览器外联、资源容量与业务成功仍需人工和独立实证。缺少真实完整批次和安全、容量、恢复证据时维持 **No-Go**。

[G3_EVAL_PROTOCOL.json](G3_EVAL_PROTOCOL.json) 是之前的 0.5 目标设计，[G2_EVAL_PROTOCOL.json](G2_EVAL_PROTOCOL.json) 是 0.4 目标设计，[V1 benchmark 协议](../benchmark/BENCHMARK_PROTOCOL.md)及 r12 原始记录均属历史。归档只供追溯，不是当前开发入口。
