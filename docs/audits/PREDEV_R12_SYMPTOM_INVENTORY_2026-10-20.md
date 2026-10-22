# r12 只读症状清单（P-01 准备）

- 日期：2026-10-20；范围：历史批次 `20261016T152251931497Z-3de75ed5` 的 18 条 `V1-D7-r12` 真实尝试，以及单独三次 UI 验收。
- 原始入口：[18 条逐条链接及人工核源](V1_DELIVERY_REPORT.md#r1218-次真实尝试及逐条核源)、[批次汇总](../../data/benchmark/20261016T152251931497Z-3de75ed5/summary.json)、[UI 原始记录](V1_UI_ACCEPTANCE.json)。本文件不改写任何原始 JSON、人工评分或历史结论。
- 当前工作树文件字节 SHA-256：`summary.json` 为 `4d1bd15ddb80c8f6fc4148d6ce4b95b4e6c13afe78f534d29158fb3b7839d88d`；`V1_UI_ACCEPTANCE.json` 为 `3f5e8ecfb08ab24b58a1a047a99c30429db2841d057473d1c0417e7b7a8cd0a6`。r12 交付报告另有 **Git index blob 内容**的 18 条聚合哈希口径；不能将本工作树文件哈希误称为该聚合哈希。

| 历史组别 | 尝试 | 观察到的终态与症状 | 可支持的判断 |
| --- | ---: | --- | --- |
| adaptive-full | 6 | `token_budget` 5（其中 B01-r1 4/10、B03-r2 2/5 为 partial），`no_progress` 1；full 0 | 有零散官方字段，但未完成固定题；预算症状不能单独证明根因。 |
| adaptive-browser-only | 6 | `token_budget` 2、`no_progress` 3、`execution_error` 1；full 0 | B02-r1 异常的底层归因仍未知，安全轨迹未暴露底层异常。 |
| baseline | 6 | `upstream_unfinished` 6；full 0，token 用量为 `null` | [交付报告](V1_DELIVERY_REPORT.md)记录默认 DeepSeek `tool_choice` HTTP 400；预算不对等，不能用于因果效果主张。 |
| 独立 UI 验收 | 3 | B01/B02 `token_budget`、B03 `no_progress`；均 failed，来源链接 0 | UI/API/SSE 可显示失败与历史，不证明真实研究成功。 |

特别保留的样本：[B01 adaptive-full r1](../../data/benchmark/20261016T152251931497Z-3de75ed5/B01_adaptive-full_r1.json) 有 4/10 字段但缺第二项目与安装命令；[B03 adaptive-full r2](../../data/benchmark/20261016T152251931497Z-3de75ed5/B03_adaptive-full_r2.json) 有 2/5 字段但缺官方发布页的两项变更；[B02 browser-only r1](../../data/benchmark/20261016T152251931497Z-3de75ed5/B02_adaptive-browser-only_r1.json) 为唯一 `execution_error`。所有 18 条文件路径、步骤、用量和字段评分以交付报告的逐行表及原始 JSON 为准；未将失败记录删去或选取重跑。

下一步诊断须在新持久调用尝试账本中分别检验：调用前后是否有未知结果、每阶段用量、工具失败类型、重规划重复、事实拒绝原因，以及报告字段缺口。每一假说要指出可能推翻它的调用级观察。旧 r12 没有足够细的请求级用量/底层异常/事实拒绝记录，故本清单只分类症状，**不声称已经定位根因或观察到优化效果**。新 pilot 必须在任何针对性质量改动前同版完成 B01–B03；原 r12 不能冒充新 pilot。
