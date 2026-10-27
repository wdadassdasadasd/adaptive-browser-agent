# 现行评测协议

## 当前 M1 补充验收与正式协议

PREP-BASELINE-v4.3 已批准并于2026-10-27同步。[DECISION_M1_PROTOCOL.json](DECISION_M1_PROTOCOL.json)是**独立补充协议**，当前未执行；3条任务各3次（全9、每题≥2/3）、来源线索8条件运行（各≤3轮）、C0/1/2的12次真实决策阶段调用、至少1真实症状纠正的诊断/最小修改/回归/授权复测。题面、候选固定版本、条件脚本、官方材料、逐轮评分和全部槽位已落入[准备材料](../../data/evaluation/decision-m1-1/preparation.json)；实际代码、模型/地域、资金、种子等执行绑定仍须运行前完成及取得具体授权，不凭本JSON直接开跑。来源/用途/已知与未知费用、失败/取消/中断均保留。

[CURRENT_EVAL_PROTOCOL.json](CURRENT_EVAL_PROTOCOL.json)仍是唯一正式研究放行协议，九道题15次和原阈值不变；跨平台绑定使用 CRLF→LF 后 SHA256 `bc75a1a6d14f7633462538c7c83b79ed5f5bcf0d670997b2000c92caa0002948`（与当前 Git blob 一致）；原 CRLF 工作树观察哈希 `1c18d53624c21b1e25f5cea5640b4c8b4a5e0cfc001f430c8d603a01d51a8507` 仅为当时字节快照，不作为跨检出原字节门槛。正式协议原件不改。新增准备包和来源摘录以 `.gitattributes -text` 保留原字节，协议中的 preparation SHA256 继续按原字节核验。M1通过不能替代五账户/完整管理、容量、真实安全恢复、加密备份恢复或解除r12/P02 No-Go。旧结果绑定原版本，不重标为新AC通过。

M1资金按诊断30元分配内规划，69等价轮/22.08元是模型费用假设示例，不是现金或grant。10.57元余额快照/历史全账及在途未齐硬阻塞首pilot；所有真实运行逐次匹配代码/模型/用途/次数/轮数/金额授权。不得挪正式200元、自动加调用或用未知0凑通过。开发回放/假供应商/诊断pilot/独立补充/冻结正式是五类不同证据，模型评分仅诊断、人工逐结论核源为准。详见[任务记录](../features/DECISION-001/tasks.md)。

[CURRENT_EVAL_PROTOCOL.json](CURRENT_EVAL_PROTOCOL.json) (`current-3`) 是正式开发与后续验收的唯一现行机读评测入口，受 [现行规格](../../SPEC.md)与[现行计划](../../PLANS.md)约束。[`current-2` 原字节归档](archive/CURRENT_EVAL_PROTOCOL_current-2.json)的 SHA-256 为 `6fa06e0ff2cb73b6fcf246130da23aa559b9b5256a9ef46d8065496850e7a53f`；更早的 [`current-1` 原字节归档](archive/CURRENT_EVAL_PROTOCOL_current-1.json)仍保留。`current-3` 只修正费用对账、pilot 未验证权限与人工复核绑定；九题题面、字段与 15 次门槛不变。协议描述**尚未执行的验收**，不能作为成功率、成本或岗位竞争力成果。任何付费真实运行均需单独授权。

已实现的离线计划入口 `python -m adaptive_research.evaluation.current --phase pilot --output data/evaluation/<new-file>.json` 只校验冻结题面、生成 B01–B03 三条预览和源码/锁文件哈希；`--phase formal` 预览 15 次，`--execute` 会拒绝。输出标记尝试和 provider 调用均为 0。[当前 pilot 计划](../../data/evaluation/p02-pilot-dry-run-r6-20261022.json)与[空项目总账基线](../../data/evaluation/p02-project-ledger-initial-20261022.json)均为离线工件。价格依据为[2026-10-22 DeepSeek CNY 快照](DEEPSEEK_CNY_PRICING_2026-10-22.json)，旧快照保留；逐调用计算仅覆盖快照列出的 token 价格，Search/Fetch 等非模型计费仍须单独核对。快照到期、缓存拆分/模型/时段不明则费用为 null，真实执行前须重新核对官方单价并冻结新批次。

`python -m adaptive_research.evaluation.pilot_budget` 默认只离线检查价表；单独授权后的 `--arm` 可在空库写入同库 pilot 预算上限，Worker 在未建额时拒绝带价表的模型调用。`adaptive_research.evaluation.pilot_capture.capture_attempt` 对已有 pilot 任务只读导出带 SHA-256 的脱敏诊断工件。`python -m adaptive_research.evaluation.pilot_runner` 默认无动作；经新批次真实运行及费用授权后，其 `--execute` 模式才可在本机 API 上按幂等键串行提交、等待、捕获 B01–B03，并逐次追加只写一次的项目总账。稳定的任务级 `partial/failed` 且费用、证据和运行源码核对完整时继续下一题；费用未知、系统故障、超额或证据不一致立即停线。捕获仅标记“待人工复核”，不生成合格结果。旧 B01 失败和停线记录见[任务包](../tasks/EIGHT_MODULE_PREP_2026-10-22.md)；[后继费用账本](../../data/evaluation/ledger-after-b01-reconciliation-20261022.json)是基于用户报告的两位小数控制台金额与工具执行路径的离线核销，逐请求 provider 发票尚未核实。

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

## 2026-10-23 开发前 pilot 诊断基线

[r11 三题诊断摘要](../../data/evaluation/p02-pilot-r11-20261023/diagnostic-baseline-summary.json)保留 B01、B02、B03 各一次同版真实尝试，结果依次为 `failed/no_progress`、`failed/token_budget`、`partial/token_budget`。[人工核源后继结论](../../data/evaluation/p02-pilot-r11-20261023/human-review-conclusion-20261023.json)仅核实 B03 的版本、Latest 标记与官方发布 URL；其余缺失字段未核实。[批次费用说明](../../data/evaluation/p02-pilot-r11-20261023/provider-console-attestation-20261023.json)将用户报告的控制台显示额 `0.12` 元与逐调用用量计算额 `0.12397276` 元按两位小数核对一致，但没有逐请求账单。[最终交接](../../data/evaluation/p02-pilot-r11-20261023/predev-handoff-20261023.json)及[项目账本](../../data/evaluation/ledger-after-e4e3e822-f5f0-582d-9412-e7cb91daefe4.json)绑定旧 B01 和新三题。该批次完成开发前准备，不计作正式研究质量通过；P-02 至 P-04 及产品继续 No-Go。

## 2026-10-27 可执行准备材料

[preparation.json](../../data/evaluation/decision-m1-1/preparation.json)固定三题逐轮原文、允许未知、六个语音候选及ORM/PDF固定版本，附23份有界官方来源摘录与6份许可声明。代码commit、模型revision和云模型ID分别记录；云后端修订未知，模型未下载/未运行，摘录hash只覆盖本地文件字节，不冒充整网页或网络字节。开发合成故障资料与独立官方材料分离；公开预注册不称盲测，AI准备阅读不代表未来报告已人工核源。

运行输入只可取agent_input明确白名单及选定来源原片段；scorer_only中的关键事实、评分例反例和反证金标不得进入模型或C2保护集合。完整脚本只供评测控制端；每轮只发送当前用户消息、此前已提交真实历史及截至当轮已接受的条件，input_ref不代表整体注入，未来轮消息和未接受条件不得提前进入prompt。未来runner须捕获每轮实际完整编译输入验证上述隔离；本轮JSON分区不是运行时已实现隔离。

E2E顺序为VOICE/ORM/PDF、ORM/PDF/VOICE、PDF/VOICE/ORM，逐轮评分，研究轮2/3分别绑定revision和不可变报告hash，缺报告为null。任一关键轮失败则attempt失败，每题仍至少2/3。来源线索采用ORM/PDF正反条件两组，每组off/on共8次；组1off先、组2on先，每侧研究→改条件研究→解释本侧第一报告。按E2E冻结顺序选择同owner最早具备所需人工核实facts的报告，整体失败不能让未核实结论混入。两侧同seed/report hash/来源/线索版本与eligible状态、独立session；off只关闭注入；其他测试种子显式撤销留审计。读取不续期，真实时间/cache差异保留；无seed阻塞，不补setup调用。

上下文四组顺序ORM1:012、PDF1:120、ORM2:201、PDF2:021，同组固定有序资料、当前条件、历史失败、预算和渲染器，只改变策略，每slot一次最终物理请求，禁止隐藏repair/retry/润色/额外研究。自然资料不足以产生真实选择压力时记insufficient_information；不复制噪声或降低产品限额。受控重排只列离线演练，不并入12次真实调用。

材料里的所有slot均executed=false，实际run/session/revision/report/call/费用为null。prerequisites列明资金/权限/环境与人工事实前置；runtime_bindings按本次操作的适用范围和各自before时点核对，已到期且blocks_real_execution=true的项缺证据则保持关闭。E2E生成的核源种子在来源线索批次前绑定，不能反过来阻塞生成它的E2E；本人验收/实践证据在M1验收前满足，不能提前代填。证据目录按data/evaluation/decision-m1-runs/&lt;authorized-batch-id&gt;/&lt;slot-id&gt;/&lt;attempt-id&gt;/组织，保留失败、取消、中断、缺失、全部调用及已知/未知费用；诊断材料、独立M1材料和冻结正式15次分别留存。正式协议、资金上限、69/22.08示例和No-Go不变。
