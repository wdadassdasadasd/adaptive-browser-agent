# V1 D7 真实验收与放行记录（2026-10-17）

## 结论

**No-Go。** r12 benchmark 的固定 B01–B03 × baseline、adaptive full、adaptive browser-only × 两次共 18 条真实尝试已完成，独立脱敏原始记录、逐条人工核源和有效的两类描述性比较均齐备。三次独立真实 UI 业务验收均未完成研究任务，也没有合格的带引用报告，因此 V1 的业务放行条件失败。协议没有 Adaptive 超过 baseline 的数值阈值；本结论未增设阈值，也未把指标低于 baseline 当作单独代码缺陷。

## 固定基线与运行条件

D6 最终复审通过；其 18 条受控伪造记录未进入 D7。正式 r12 批次 `20261016T152251931497Z-3de75ed5`，协议 `V1-D7-r12`，UTC `2026-10-16T15:22:54.728816+00:00–2026-10-16T15:38:52.664054+00:00`。批次期间代码和协议固定。主仓库起始 HEAD `7385fcf5e8cbb194c04b18f5aaba9f070a6c243f`，受控工作区 SHA-256 `1f98ac965d2a5f4e44332f514334418e91c8b58e94e97bf61954e2dd10d8f1cb`；browser-use gitlink/实际 HEAD `7be96ed8bafa8dfe1eef228b59cf5c884b8b2431`，工作区干净，HEAD tree 指纹 `0af6d30d1bd2e44bc4502cadddbf6e909b32a769`。`uv.lock` SHA-256 `76fd95fcc38ef62931e8b1073a0f70958bbdd7186e6e5601dade23a43113c2cf`；`frontend/package-lock.json` SHA-256 `f59cff9b0e7c91c54ce5e104b830a2905d6e5809739789cc3d8ec7b56df8a3b9`。Windows 11 `10.0.26200`、Python 3.12.13、Chromium `Chrome/155.0.8059.80`、`deepseek-flash`；`network=unverified` 表示网络条件未量化。真实提供方、公开站点、隔离 SQLite 和 runner 均实际运行，密钥只由本地 `.env` 注入进程。

18 条唯一 `run_id`、各案例原文哈希、三组轮换、模型、浏览器和代码指纹核对通过。最大 6 步、99.9 秒、已知 prompt+completion 29,169，低于 30 步、900 秒、40,000 token；六条 baseline token 保留 `null`，不能据此证明调用前预算同等。提交前 Git index 中的原始 JSON blob（LF 规范化）按文件名排序，将各 blob 内容的 SHA-256 十六进制串接再取 SHA-256：`1f1729638f85317d0ec3914e72aaedd4326298713ec45f5aec44b653767c0acf`。密钥原值及常见 Bearer/token 模式扫描均 0 命中。18 条人工 note 填完后执行 `python -m benchmark.runner --summarize data/benchmark/20261016T152251931497Z-3de75ed5`，退出 0；`protocol_complete=true`、`smoke_only=false`、`controlled_advantage_claim_allowed=false`。

## 三次独立业务验收

三项均使用案例原文，从真实 Chromium 中的 Vue UI 创建，经过 FastAPI、TaskManager、AgentLoop、DeepSeek/工具、隔离 SQLite 和 SSE。任务 ID 与 benchmark 完全分离。逐事件、报告正文、目标哈希和重启核验见 [V1_UI_ACCEPTANCE.json](V1_UI_ACCEPTANCE.json)。下面 token 为 SQLite 生命周期/步骤事件中的用量增量之和；终态事件为 0 并不表示整次运行使用 0 token。

| 案例 | UI 任务 ID | 终态/停止原因 | 持久动作步/SSE | prompt/completion | 报告、来源及重启 |
| --- | --- | --- | ---: | ---: | --- |
| B01 | `45985791-55cc-43e1-bd26-003056dfd915` | failed / `token_budget` | 2/6 | 8,920/25,074 | 未完成报告，0 来源；重启后 HTTP 200 |
| B02 | `a91ba448-74d8-4a7f-9ce9-b527da58e2c9` | failed / `token_budget` | 1/5 | 15,482/4,103 | 未完成报告，0 来源；重启后 HTTP 200 |
| B03 | `3cda2d59-3b03-4c17-9d21-70e38bd47ffb` | failed / `no_progress` | 5/9 | 20,676/4,286 | 未完成报告，0 来源；重启后 HTTP 200 |

三条 SSE 均含 `task_finished`；API 重启后三条状态、轨迹和报告可读。浏览器 `kill()` 返回，API 与 Vite 已关闭；浏览器 Python 事件循环退出时另有非致命 pipe destructor 警告。报告没有事实来源可逐项核查，未把“访问过官方页”充当已引用的事实。

## r12：18 次真实尝试及逐条核源

以下 `run_id` 均以 `20261016T152251931497Z-3de75ed5-` 为前缀，链接指向独立原始 JSON。字段为核源后的 `score_fields` 真值数；B01/B02 分母 10，B03 分母 5。失败和部分运行保留原件，未挑选成功重跑。`null` 为缺失用量。

| 顺序 | run_id 后缀 / 原始 JSON | 状态 / 停止原因 | 字段 | 步骤 | prompt/completion | 秒 |
| ---: | --- | --- | ---: | ---: | ---: | ---: |
| 1 | [B01-baseline-r1](../../data/benchmark/20261016T152251931497Z-3de75ed5/B01_baseline_r1.json) | failed / `upstream_unfinished` | 0/10 | 6 | null/null | 60.5 |
| 2 | [B01-adaptive-full-r1](../../data/benchmark/20261016T152251931497Z-3de75ed5/B01_adaptive-full_r1.json) | partial / `token_budget` | 4/10 | 4 | 20117/7656 | 76.8 |
| 3 | [B01-adaptive-browser-only-r1](../../data/benchmark/20261016T152251931497Z-3de75ed5/B01_adaptive-browser-only_r1.json) | failed / `no_progress` | 0/10 | 5 | 22022/4288 | 58.7 |
| 4 | [B02-adaptive-full-r1](../../data/benchmark/20261016T152251931497Z-3de75ed5/B02_adaptive-full_r1.json) | failed / `token_budget` | 0/10 | 2 | 20282/3212 | 44.8 |
| 5 | [B02-adaptive-browser-only-r1](../../data/benchmark/20261016T152251931497Z-3de75ed5/B02_adaptive-browser-only_r1.json) | failed / `execution_error` | 0/10 | 2 | 15997/1725 | 39.2 |
| 6 | [B02-baseline-r1](../../data/benchmark/20261016T152251931497Z-3de75ed5/B02_baseline_r1.json) | failed / `upstream_unfinished` | 0/10 | 6 | null/null | 24.3 |
| 7 | [B03-adaptive-browser-only-r1](../../data/benchmark/20261016T152251931497Z-3de75ed5/B03_adaptive-browser-only_r1.json) | failed / `token_budget` | 0/5 | 4 | 19049/9204 | 79.7 |
| 8 | [B03-baseline-r1](../../data/benchmark/20261016T152251931497Z-3de75ed5/B03_baseline_r1.json) | failed / `upstream_unfinished` | 0/5 | 6 | null/null | 25.8 |
| 9 | [B03-adaptive-full-r1](../../data/benchmark/20261016T152251931497Z-3de75ed5/B03_adaptive-full_r1.json) | failed / `no_progress` | 0/5 | 5 | 20771/4950 | 64.1 |
| 10 | [B01-adaptive-full-r2](../../data/benchmark/20261016T152251931497Z-3de75ed5/B01_adaptive-full_r2.json) | failed / `token_budget` | 0/10 | 4 | 18286/10883 | 99.9 |
| 11 | [B01-adaptive-browser-only-r2](../../data/benchmark/20261016T152251931497Z-3de75ed5/B01_adaptive-browser-only_r2.json) | failed / `no_progress` | 0/10 | 5 | 23098/3976 | 72.0 |
| 12 | [B01-baseline-r2](../../data/benchmark/20261016T152251931497Z-3de75ed5/B01_baseline_r2.json) | failed / `upstream_unfinished` | 0/10 | 6 | null/null | 26.1 |
| 13 | [B02-adaptive-browser-only-r2](../../data/benchmark/20261016T152251931497Z-3de75ed5/B02_adaptive-browser-only_r2.json) | failed / `no_progress` | 0/10 | 5 | 18601/2888 | 49.5 |
| 14 | [B02-baseline-r2](../../data/benchmark/20261016T152251931497Z-3de75ed5/B02_baseline_r2.json) | failed / `upstream_unfinished` | 0/10 | 6 | null/null | 26.0 |
| 15 | [B02-adaptive-full-r2](../../data/benchmark/20261016T152251931497Z-3de75ed5/B02_adaptive-full_r2.json) | failed / `token_budget` | 0/10 | 3 | 25289/3645 | 57.4 |
| 16 | [B03-baseline-r2](../../data/benchmark/20261016T152251931497Z-3de75ed5/B03_baseline_r2.json) | failed / `upstream_unfinished` | 0/5 | 6 | null/null | 26.0 |
| 17 | [B03-adaptive-full-r2](../../data/benchmark/20261016T152251931497Z-3de75ed5/B03_adaptive-full_r2.json) | partial / `token_budget` | 2/5 | 4 | 23190/4952 | 56.7 |
| 18 | [B03-adaptive-browser-only-r2](../../data/benchmark/20261016T152251931497Z-3de75ed5/B03_adaptive-browser-only_r2.json) | failed / `token_budget` | 0/5 | 4 | 21812/5840 | 62.5 |

18 条答案逐一阅读，人工检查与每文件 Git blob 内容 SHA-256 见 [V1_SOURCE_CHECKS.json](V1_SOURCE_CHECKS.json)。16 条答案没有已验证的具体发现；其 `none` 仅表示无可证伪事实陈述。B01 full-r1 的 Selenium 仓库身份、浏览器自动化描述及 Apache-2.0 许可证，已打开其[确切 GitHub API 引用](https://api.github.com/repos/SeleniumHQ/selenium)与[官方仓库](https://github.com/SeleniumHQ/selenium)核对；答案明确缺安装命令，未补分。B03 full-r2 的 0.13.13 最新标签、官方 URL、旧版顺序与时间戳，已打开[确切 releases API 引用](https://api.github.com/repos/browser-use/browser-use/releases)与[官方发布页](https://github.com/browser-use/browser-use/releases/tag/0.13.13)核对；答案缺该版本发布日期及两项变更，未补分。18 条 `manual_contradiction_note` 均为 `none`，不表示未完成答案合格。

## A. Adaptive full 对 baseline：完整产品效果

每案例各组 n=2，总体各组 n=6。“有效 n”是有效真实原始记录数，不是成功数。完成率及已引用字段覆盖率差值为百分点；步骤和耗时的相对变化以同一行 baseline 均值为分母，样本数见 n 列。重复 URL 均为 0，分母为 0，未计算相对变化。token 为非缺失样本的 prompt/completion 平均值，baseline 全缺失，token 相对变化不可定义。失败类别 U=`upstream_unfinished`、T=`token_budget`、N=`no_progress`、E=`execution_error`；缺失 P/C 按 prompt/completion 各计数。

| 案例 | 有效 n B/A | 完成 B→A / Δpp | 已引用字段覆盖 B→A / Δpp | 平均步 B→A / 相对 | 重复 URL | prompt/completion B→A | 秒 B→A / 相对 | 失败 B→A | 缺失 P/C B→A | 预算 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| B01 | 2/2 | 0→0% / +0.0 | 0→20% / +20.0 | 6→4 / -33.3% | 0→0 | null/null→19201.5/9269.5 | 43.3→88.3 / +104.0% | U2→T2 | 2/2→0/0 | mismatched |
| B02 | 2/2 | 0→0% / +0.0 | 0→0% / +0.0 | 6→2.5 / -58.3% | 0→0 | null/null→22785.5/3428.5 | 25.2→51.1 / +103.3% | U2→T2 | 2/2→0/0 | mismatched |
| B03 | 2/2 | 0→0% / +0.0 | 0→20% / +20.0 | 6→4.5 / -25.0% | 0→0 | null/null→21980.5/4951 | 25.9→60.4 / +133.2% | U2→N1,T1 | 2/2→0/0 | mismatched |
| 总体 | 6/6 | 0→0% / +0.0 | 0→13.3% / +13.3 | 6→3.7 / -38.9% | 0→0 | null/null→21322.5/5883 | 31.5→66.6 / +111.8% | U6→T5,N1 | 6/6→0/0 | mismatched |

full 组可使用 GitHub 工具，可能更容易取得结构化官方来源；其覆盖率不能归因于 Planner。完成率没有提高，平均耗时更长；较少步骤主要是早停，不能称为效率提升。

## B. Adaptive browser-only 对 baseline：机制观察

口径、分母及样本数与 A 表一致。browser-only 禁用 GitHub 工具，但架构与提示词仍不同于 baseline；规划、重规划与去重差异只是观察值，不能作因果证明。

| 案例 | 有效 n B/A | 完成 B→A / Δpp | 已引用字段覆盖 B→A / Δpp | 平均步 B→A / 相对 | 重复 URL | prompt/completion B→A | 秒 B→A / 相对 | 失败 B→A | 缺失 P/C B→A | 预算 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| B01 | 2/2 | 0→0% / +0.0 | 0→0% / +0.0 | 6→5 / -16.7% | 0→0 | null/null→22560/4132 | 43.3→65.4 / +51.0% | U2→N2 | 2/2→0/0 | mismatched |
| B02 | 2/2 | 0→0% / +0.0 | 0→0% / +0.0 | 6→3.5 / -41.7% | 0→0 | null/null→17299/2306.5 | 25.2→44.4 / +76.3% | U2→E1,N1 | 2/2→0/0 | mismatched |
| B03 | 2/2 | 0→0% / +0.0 | 0→0% / +0.0 | 6→4 / -33.3% | 0→0 | null/null→20430.5/7522 | 25.9→71.1 / +174.4% | U2→T2 | 2/2→0/0 | mismatched |
| 总体 | 6/6 | 0→0% / +0.0 | 0→0% / +0.0 | 6→4.2 / -30.6% | 0→0 | null/null→20096.5/4653.5 | 31.5→60.3 / +91.6% | U6→N3,E1,T2 | 6/6→0/0 | mismatched |

两次重复仅作描述性比较，不作显著性结论。三组重复 URL 均为 0，baseline 默认运行未完成浏览；零值不能证明去重优势。所有成对比较的 `budget_parity=mismatched`：baseline 上游默认行为不能保证调用前 40,000 token 上限且六次没有用量返回，Adaptive 两组自身为 `verified`。

## 未达标项与迭代轨迹

| 轮次 / 保留批次 | 归因与原始证据 | 失败回归、修复及复验 |
| --- | --- | --- |
| UI 诊断 | Planner 请求不支持动作/畸形 GitHub target；目标计数与事实过滤不一致，项目缺陷。 | 失败回归先行，修复动作指引、有限纠正、Evaluator 与目标计数；三次真实 UI 任务仍未完成，如上。 |
| r3 `20261015T075440428037Z-dda6af17` | 18 条真实记录缺显式 `run_id`，runner 缺陷。 | 补失败回归与 ID；原件保留，r4 新指纹完整重跑。 |
| r4 `20261015T081419231556Z-add35485` | 仓库 URL 身份/数量不一致，浏览器清理超旧 5 秒等待，项目缺陷。 | 共享身份规则、20 秒有界清理；回归后 r5 重跑。 |
| r5 `20261015T141953181046Z-285c5eb4` | 复审发现非仓库 GitHub 路径及 `change` 事实误接纳；baseline HTTP 400。 | 收紧身份与事实规则，回归后 r6 重跑；baseline 默认行为未修改。 |
| r6 `20261015T144935362314Z-6a51e435` | 提供方后续 HTTP 402 余额不足；`sponsors/apps/issues/pulls` 等保留路径误判。 | 保留 402 原件；排除保留路径，余额恢复后 r7 重跑。 |
| r7 `20261015T151515073525Z-4e0853e2` | B03 full-r1 把旧版日期计给最新版，计分错误。 | 日期归属失败回归后修正，r8 完整重跑。 |
| r8 `20261016T085257506273Z-7d8fc340` | B03 browser-only-r2 把标题的 “Cloud fixes” 当 release-note 变更，计分错误。 | 剔除标题事实，回归后 r9 重跑。 |
| r9 `20261016T093445198202Z-50c4bc1e` | B01 full-r1 将 Selenium 许可证错归下一候选，计分错误。 | 新候选主体切断前项归属，回归后 r10 重跑。 |
| r10 `20261016T095412146304Z-a520c9ce` | 18 条真实/18 条人工 note；独立只读审查发现带 bullet 的候选边界与无引号 B03 标题假变更。 | 两项测试先红后绿；修复计分，r11 全三组重跑，r10 原始分数未改。 |
| r11 `20261016T112555579395Z-644bdf88` | 18 条真实/18 条人工 note；B03 full-r1 同一 GitHub 页面标题重复出现，被错算两项变更。 | r12 失败回归先行；预批次只读审查又复现 `+` bullet、分号标题、Comparison 真变更及版本标题边界；最小修复并新增回归，r12 全三组重跑。 |
| r12 `20261016T152251931497Z-3de75ed5` | 18 条真实/18 条人工 note；完成率全为 0。baseline 六次默认 DeepSeek `tool_choice` HTTP 400；browser-only 一次 `execution_error` 安全轨迹未暴露底层异常。 | 计分复算及逐条核源通过；没有可复现的新项目/runner 计分缺陷，不因指标低而看后调参。UI 0/3 是 V1 放行阻断。 |

| r12 交付审计 | 最终只读审查在 `V1_SOURCE_CHECKS.json:12` 复现 Windows CRLF 工作区字节哈希与提交时 LF Git blob 不一致；18 条及聚合哈希不可从暂存内容复现，属审计证据缺陷。 | 不改原始答案或计分；三个清单共 54 条哈希统一为 Git blob 内容口径，r12 聚合哈希重算；暂存 blob 对清单 54/54 与报告聚合核对通过。 |

历史 r3–r11 与独立诊断运行保持隔离；每轮失败记录与原始得分保留，未被后轮成功条目覆盖。r12 的单次 `execution_error` 目前不能确定是项目、网络还是提供方问题。

## 质量门禁与独立审查

受影响 benchmark 定向测试 **100 passed**；明确排除 opt-in browser 的 Python 3.12/3.13 全量离线测试各 **413 passed, 1 deselected**，退出 0。Ruff check、Ruff format（76 files）、compileall、`uv lock --check --offline` 均退出 0。前端 `npm ci`、`type-check`、20 项测试及 `build` 均退出 0；Node 23 engine 警告不阻断。真实 Chromium adapter 独立烟测限时复跑 **1 passed in 5.87s**。先前一次单独烟测进程卡住，已中断且无通过输出，不计通过；两次含 opt-in browser 的全量测试另各为 414 passed。最初并发 `uv` 写同一 `.venv` 导致环境冲突；修复受损包、隔离 3.13 环境后复验通过，属于门禁执行环境故障。

独立只读审查已有明确边界：r10 完整暂存差异审查会话 `01a14435-324f-7462-a359-ae1c433bef1f`，生效 `sandbox: read-only`、`approval: never`，两项 P2 已回归修复；r12 预批次计分范围审查会话 `01a14488-1f97-7372-82e1-7a26a2c86a63` 的四项边界已修复；最终正则范围复审会话 `01a1454b-673c-7b83-86e6-b8b238cc48a7` 生效只读，直接探针无剩余可复现阻断。最终交付数据/报告范围只读审查会话 `01a14824-8450-7a81-a826-8ec79d58521d` 生效只读，发现上述 SHA-256 口径阻断；三个清单及报告已按暂存 Git blob 修复并 54/54 核对通过；仅此变化范围复审会话 `01a1484a-8886-7253-97ed-de089598bfb2` 生效只读、`approval: never`，无剩余可复现阻断。

## V1_TEST_MATRIX.md：D7 Done-when 12 项

| # | 状态 | 证据或缺口 |
| ---: | --- | --- |
| 1 | **失败** | 三个独立真实 UI 任务 0/3 完成，见 UI 证据 JSON。 |
| 2 | **通过** | Planner 当前状态决策/有界重规划的单元与集成回归通过；真实轨迹含工具动作与早停。 |
| 3 | **通过** | r12 full 真实 GitHub、browser-only 真实 Chromium 路由；浏览器烟测通过。 |
| 4 | **通过** | Evaluator 对技术、语义及信息不足分类回归通过；r12 失败类别原样保存。 |
| 5 | **通过** | URL/查询去重回归通过，r12 重复 URL 均为 0；零值不单独证明效果。 |
| 6 | **通过** | Planner 上下文边界回归及双 Python 全量通过，真实 token 上限停止可见。 |
| 7 | **通过** | 三条 UI SSE 有序生命周期、步骤及 `task_finished`，见 UI 证据。 |
| 8 | **通过** | 隔离 SQLite 持久化，API 重启后三个 ID/轨迹/终态报告 HTTP 200。 |
| 9 | **失败** | 三次真实业务报告均无合格引用来源，未达到带引用 ResearchReport。 |
| 10 | **通过** | r12 三组各六条真实 JSON、18 条核源 note、重算 summary 及 A/B 比较可追溯；效果受 baseline 400 与预算不匹配限制。 |
| 11 | **通过** | 100 项 benchmark 定向、双 Python 各 413 项离线全量，含失败先行回归。 |
| 12 | **通过** | README 本地启动路径经真实 Vue/API/隔离数据库运行验证，前端安装/类型/测试/构建通过。 |

## 继续放行所需条件与剩余风险

先使 B01–B03 三个独立 UI 任务在协议预算内稳定完成并生成可逐页核验的官方来源报告。定位 Adaptive 的单次 `execution_error`；若可复现为项目缺陷，先写失败回归、最小修复，再以新代码指纹建立完整新批次。baseline 六次上游默认工具调用与 DeepSeek thinking mode 的 `tool_choice` 不兼容；若调整上游/提供方配置、提示词、预期字段或计分口径，先版本化协议并完整重跑可比三组，不能改写本批。每案例每组仅两次，网络未量化、公开网页随时间变化，结果不支持显著性或因果结论。
