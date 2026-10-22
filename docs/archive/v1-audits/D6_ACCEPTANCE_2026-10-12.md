# D6 验收复核 — 2026-10-14 至 2026-10-15

本记录复核 2026-10-12 的未提交 D6 实现。旧记录中的通过数字和结论不沿用；以下只列本次代码、命令与操作证据。`docs/specs/V1_SPEC.md` 是产品依据，另核对 `docs/contracts/V1_CONTRACTS.md`、任务表、测试矩阵和基准协议。受控伪造提供方结果不是 DeepSeek 实跑，也不是性能提升证据。

## 执行基线

- 分支 `main`，HEAD `c8d97acdd10075036c4bde8d7331b2e568b63f25`，跟踪 `origin/main`；暂存区为空。执行前主仓库已有 D6 的前端、基准、CI、文档及 Agent 工具路由改动，均未提交；没有切分支、重置或改动现有数据库。
- `git ls-files --stage browser-use` 和获准环境下的 `git -C browser-use rev-parse HEAD` 都返回 `7be96ed8bafa8dfe1eef228b59cf5c884b8b2431`；子模块 `git status --short` 无输出。checked-out 源码存在 `Agent.run(max_steps, on_step_end)`、`stop`、`close`、`ChatDeepSeek` 和 token 用量接口。
- 本次隔离 UI 数据库为 `.pytest_cache/d6-recheck-live/demo.db`。最新完整受控基准记录在 `.pytest_cache/d6-recheck-benchmark/d6-controlled-b1f1536c/`；此前中断仅生成 16 条、无汇总，未计入验收。`data/benchmark/` 不存在，没有可核对的真实运行记录。

## 本次验收矩阵

| 需求 | 用户可观察的通过条件 | 代码位置 | 验证方法 | 本次证据 | 结论 |
| --- | --- | --- | --- | --- | --- |
| T14 创建与错误 | 空目标不可提交；创建、加载、422、503 和断网反馈准确 | `frontend/src/App.vue`, `api.ts`; `backend/api/research.py` | 交互测试；浏览器请求/页面记录 | 前端 20/20；空目标按钮禁用；键盘提交任务 `72fbb741` 返回 202；无密钥 POST 503、空白目标 POST 422、未知任务 404、停 API 后刷新显示代理 HTTP 500 的中文说明 | 通过 |
| T14 任务与时间线 | 六条 API 完整；SSE 重连、ID 去重、并发轨迹不丢，终态关闭 | `frontend/src/App.vue`, `api.ts` | 前端竞态测试；SSE 断线/重启浏览器路径 | 20 个交互测试含 ID 去重、轨迹并发、排队到运行轮询同步、初始列表竞态、初始轨迹失败仍开启 SSE、仅动作编号、终态详情失败后恢复及刷新重连；任务 `b7f373de` 有 200 SSE，断线后同库重启显示 `server_restart` 及第三条 `task_finished` | 通过 |
| T14 结果与恢复 | 来源报告、取消、刷新和最近任务与服务端一致；键盘可用，浏览器无密钥 | `frontend/src/App.vue`, `api.ts` | 浏览器路径；存储和构建检查 | `72fbb741` 五条事件及 GitHub 来源；`25021957` UI 取消后 `user_cancelled` 和四条事件；部分完成报告显示“待核实或未完成”的测试先 failed 后 20 passed；刷新恢复历史；浏览器 local/sessionStorage 均为空，网络只见六条既定路由 | 通过 |
| T15 三组运行 | B01–B03 原文轮换 18 次；baseline 接口正确；browser-only 禁 GitHub | `benchmark/runner.py`, `baseline.py`, `adaptive.py`; Planner/Router | 计划输出、源码核对、受控执行和定向测试 | `python -m benchmark.runner` 输出 18 个唯一轮换尝试且 `live_runs=0`；受控执行三组各 6 条；baseline 超时步骤 URL 顺序和 adaptive 时限前已完成动作均有失败先行回归，基准 85 passed，browser-only 拒绝 GitHub 调用 | 通过 |
| T15 计分与公平 | 值有对应官方来源且不重复计分；预算越界与 mismatch 明确 | `benchmark/metrics.py`, `runner.py` | 失败先行的正反例、预算测试、记录核查 | B02 官方文档首页及 B03 `Unknown or unfinished` 段均不得提供字段来源，后者先 1 failed；修复后基准 85 passed；GitLab、B03 版本和来源正反例均通过；baseline token parity 为 `mismatched` | 通过 |
| T15 原始记录 | 成败均保存脱敏 JSON；缺用量为 null；三组分别汇总 | `benchmark/runner.py`, `metrics.py` | 受控 18 次执行逐条断言并抽查原始文件 | 大写 HTTPS URL 泄露路径的定向测试先 1 failed；修复后基准 85 passed；最新受控 18 个 JSON 中 2 次失败保留且带项目及上游工作区 SHA-256，baseline token 为 null；完成率缺人工备注时为 null，两类比较分开 | 通过 |
| T16 门禁与文档 | 锁定安装、类型检查、测试、构建列入 CI；README 命令可执行 | `.github/workflows/ci.yml`, `frontend/package-lock.json`, `README.md`, `tests/d6_demo_server.py` | 本地 CI 等价命令、工作流核对、文档启动 | Node 22 CI job 含四门禁；获准本机环境 `npm ci`、类型检查、20/20、构建退出 0；Python 3.12/3.13 最后修复后各 383 passed/1 deselected；Ruff、格式、编译、锁文件退出 0；文档命令启动 GET 200 | 通过 |
| D6 集成与审查 | 完整隔离浏览器路径；最终 diff 的独立只读审查阻断项关闭 | D6 全部 diff；`backend/main.py` | 浏览器操作记录；独立审查及复验 | UI 路径完成；25 次完成的原生完整审查均显示 `sandbox: read-only`，累计 61 项发现均已复现并修复；最后两项的限定范围只读复审也显示有效只读且无阻断发现；修复后双版本全量门禁通过 | 通过 |

## 缺陷证明与修复

- `tests/unit/test_benchmark.py` 的 B02 同一段双官方链接负例和 B03 错配 release tag/空变更负例，在原实现均失败（2 failed，退出 1）。`benchmark/metrics.py` 改为只采纳单一项目可归属的证据段，并要求显式 tag 版本匹配、变更标题有描述；修复后基准定向 25 passed（退出 0）。
- 原受控 UI 服务脚本只在忽略目录，README 的“按记录复现”无法在新 checkout 执行。现提供 `tests/d6_demo_server.py`，要求显式隔离数据库路径；README 给出启动及重启步骤。实际 `uv run ... uvicorn tests.d6_demo_server:app --port 8001` 启动完成，`GET /api/research` 返回 HTTP 200 `[]`。
- 原生只读审查指出 `benchmark/runner.py:92-95` 的 Cookie 多键值泄露、`benchmark/metrics.py:180-185` 的 B03 正文式/同行引用变更漏计，以及 `benchmark/runner.py:221-225` 的真实运行浏览器版本缺失。前两项用负例复现（2 failed；第三项由 `browser=unverified` 默认代码路径证明），随后按当前上游 `BrowserSession`/CDP 接口加入版本预检并在失败时显式标注。新增探针关闭和失败保留测试；基准套件 30 passed。负例首次执行另有一项 pytest `tmp_path` 环境访问拒绝，改用仓库内 `--basetemp` 后完成验证。
- 第二次只读复审指出 `benchmark/runner.py:118-120` 的 `Authorization: Basic` 和 `access_token` 残留，以及 `frontend/src/App.vue:226-233` 初次列表请求与新建任务竞态。凭据负例 1 failed；增强后的前端竞态测试 1 failed，旧响应确实把最近任务改成旧任务。现在整行遮盖授权头、扩展 token 键名遮盖，并用列表请求版本及初次选择版本阻止旧响应覆盖；基准 31 passed、前端 12 passed。以上为定向复验，全量门禁待最后执行。
- 第三次只读复审指出 `benchmark/runner.py:192-196` 在脱敏后计算重复 URL，令不同搜索查询误计，以及 `benchmark/metrics.py:65-71` 把相邻独立引用的表格/比较行误判为混合段。两项回归先 2 failed，改为保留原始 URL 仅在内存计数、按可归属引用行分段；随后基准 33 passed。另核对上游 `Agent` 默认 `use_judge=True` 与协议“未改动的上游 Agent”，发现 baseline 显式设 `False`，新增负例先 failed，移除覆盖后基准 34 passed。受控记录只保存脱敏 URL，未保存原始查询或密钥。
- 第四次只读复审指出 `benchmark/runner.py:92-98` 引号 JSON 字段内凭据残留、`frontend/src/App.vue:113-115` 终态详情失败后丢失恢复路径、`benchmark/baseline.py:98-99` 恰好 40,000 token 的成功误判失败。三个回归先 2 failed（Python）和 1 failed（前端）；修复后基准 36 passed、前端 13 passed，终态自动恢复后计时器数量为 0。
- 第五次只读复审指出 `benchmark/runner.py:207-212` 的非官方 URL 路径可能包含未知页面凭据、`benchmark/metrics.py:40-42` 的 URL 计数错误折叠路径/查询大小写和尾斜杠，以及 `benchmark/metrics.py:79-87` 的多行候选声明与下一行来源拆散。三项回归先 3 failed，现非官方 URL 持久化仅保留 origin、官方来源保留路径；原始 URL 只在内存计数，规范化仅折叠 scheme/host 并去 fragment；按相邻来源保留声明。基准 40 passed，其中有完整 JSON 记录中秘密路径不落盘的回归。
- 第六次只读复审指出 `benchmark/metrics.py:125-126` B01 前置背景仓库挤掉第二个完整候选，及 `benchmark/metrics.py:67-70` B03 仅有 releases 列表页也可得满覆盖。两个负例先 2 failed，改为按每个仓库证据字段完整度选两个候选，且 B03 仅接受可匹配所述版本的具体 tag URL；基准 42 passed。
- 第七次只读复审指出 `benchmark/metrics.py:175-180` B01 同一仓库的许可和安装分段引用未合并，及 `benchmark/metrics.py:73` issue 链接误作仓库根 URL。两个负例先 2 failed，改为按仓库聚合每段有来源的字段，并单独要求 `owner/repo` 根链接；基准 44 passed。
- 对同一 B03 变更用 `Added`/`Adds` 改写的重复计分再补负例，先 1 failed；改以变更描述而非动词时态去重，基准 45 passed。
- 第八次只读复审指出 `benchmark/metrics.py:232-233` B03 唯一具体发布页放末尾来源节导致字段漏计、`frontend/src/App.vue:202-203` 初次详情失败后手动刷新不重开 SSE，以及 `benchmark/metrics.py:73` 排斥 GitLab 等公开仓库。基准 2 failed、前端 1 failed 先行；修复后基准 47 passed、前端 14 passed，类型检查退出 0。仓库宿主采用明确白名单，B03 仍要求具体 tag 与版本匹配。
- 第九次只读复审指出官方 URL 路径内的 `api_key` 可落盘、终态详情持续失败会无限重试，以及创建成功后等待列表响应会推迟进入任务时间线。三项分别以失败先行回归证明；现在官方来源路径中的秘密标记整段遮盖、终态详情最多自动重试三次后提示手动刷新、创建成功即选中并订阅任务。修复后基准 48 passed、前端 16 passed、类型检查退出 0。
- 第十次只读复审指出上游 `agent_steps()` 可把页面提取文本中的 `sessionid`/`private_key` 落盘、GitLab 子组仓库会被合并、以及 baseline 自评失败错误影响协议完成率。三个定向回归先 3 failed；现在持久化轨迹只含步骤/动作/结果元数据，GitLab 使用完整子组路径识别仓库，baseline 自评单列 `upstream_success`；基准 51 passed。
- 第十一次只读复审指出答案正文中的独立 `sk-`/`ghp_` 密钥样式未遮盖，及脏工作区的不同源码会被记录为同一 HEAD。两个负例先 2 failed；现在独立凭据遮盖，记录增加 `project_dirty` 和工作区内容 SHA-256，指纹不可得时拒绝真实运行。基准 54 passed；受控 18 次记录三组各 6，2 次失败保留。
- 第十二次只读复审指出 B02 比较标题会污染单项目证据、上游 Agent 在 40,000 token 回调后仍可能调用 judge，以及上游子模块未提交源码不进指纹。三个回归先 3 failed；现在剔除无来源的双项目比较标题，在预算阈值抛出专用终止异常跳过 judge，同时散列主仓库和 browser-use 工作区。基准 57 passed；受控 18 次记录再次通过。
- 第十三次只读复审指出排队任务转运行后轮询仍显示旧状态，及 upstream 30 步耗尽哨兵被扣除后错误记为完成。前端新增回归先 1 failed/17、基准已有用例调整后先 1 failed；现在轮询同步所选和最近任务状态，哨兵计入 `step_budget_reached` 失败而执行步数仍为 30。前端 17 passed、基准 57 passed；受控 18 次记录再次通过。
- 第十四次只读复审指出上游因连续失败退出而未执行 `done`，可能被记录为完成。新回归先 1 failed；现在以 `history.is_done()` 单独判定执行是否完成，不使用自评真假替代协议计分。基准 58 passed；受控 18 次记录再次通过。
- 第十五次只读复审指出 B01 仅有 `pip install -U` 却计安装字段、B03 `Fixed issue`/`Updated docs` 计具体变更、B02 `async views` 漏计、终态详情成功但轨迹失败时页面继续显示运行。三个基准负例先 3 failed，前端更新既有恢复断言先 1 failed；分开加载详情/轨迹后又使有界重试测试先 1 failed，修正计时器后全部通过：基准 61 passed、前端 17 passed。
- 第十六次只读复审指出 B01 官方 GitHub API 来源被排除、B03 研究日期误计发布日期、B02 `pip install "fastapi[standard]"` 漏计。三个新增回归先 3 failed/61 deselected、退出 1；局部修复后 3 passed/61 deselected，完整基准 64 passed。API 来源可支持名称/许可证等声明，但仓库 URL 字段仍须单独给出仓库根链接。
- 第十七次完整只读复审指出初次轨迹请求失败会阻止运行任务建立 SSE，以及 Markdown 反引号包住的发布页 URL 被解析为无效。新前端回归先 1 failed/17 passed，基准回归先 1 failed/64 deselected；现在详情成功即启动 SSE，轨迹请求可与实时事件合并，URL 解析排除反引号。修复后前端 18 passed、基准 65 passed。此前一次第十七轮启动后被外部中断，无结论，不计入已完成轮次。
- 第十八次完整只读复审指出 `Changes in this release` 被计为发布变更、单独 `Source:` 计官方来源字段、生命周期事件错误显示动作步号。基准 2 failed/65 deselected、前端 1 failed/18 passed 的负例先行；现在跳过通用变更章节标题，官方来源字段须伴随具体发布声明，仅 `step_evaluated` 显示动作步号。修复后基准 67 passed、前端 19 passed。
- 第十九次完整只读复审指出同页点击/滚动/提取及无来源失败动作被误计为 URL 重访，以及 B01 为 Playwright/Selenium 给出 `pip install flask`/`django` 仍可满分。四个定向回归先 4 failed；初次修复揭示命令尾部句号导致既有 8 个正例失败，修正后完整基准 69 passed。现在 baseline 的逐步 URL 与 adaptive 的浏览器事件均折叠连续同页观测，后续返回才计重访；候选安装包名按该项目名称或仓库别名匹配。
- 对新安装别名规则继续核对，`browser-use` 的通用仓库前缀 `browser` 曾可误计。新增负例先 1 failed/69 deselected；排除通用前缀后基准 70 passed。候选按完整度排序，测试断言有效安装字段数量而非假设项目序号固定。
- 第二十次完整只读复审指出 B02 同一段提及两套框架时漏计带官方来源的有效字段、B03 版本旁日期漏计、部分报告的未完成事项未在前端展示。新增基准正例先 2 failed，反向归属负例另先 1 failed；前端部分报告回归先 1 failed/19 passed。现按唯一官方来源及首先提及的框架归属字段、接受与版本相邻的发布日期，并在报告中展示“待核实或未完成”；修复后基准 73 passed、前端 20 passed。
- 第二十一次完整只读复审指出 B03 报告复述任务标题会把“two changes from its release notes”误计为变更，以及大写 `HTTPS://` URL 绕过脱敏。新增定向回归先 2 failed/73 deselected；现在移除任务提示语后计发布变更，URL 脱敏忽略 scheme 大小写，并补完整 JSON 记录中的大写 URL 回归。修复后基准 76 passed。
- 第二十二次完整只读复审指出 GitLab issue 链接可被当成第二个项目、B03 旧 tag 可支撑声称的最新版，以及 baseline 只用上游步骤前 URL 会漏掉动作后的导航。三个定向回归先 3 failed/76 deselected；修复后 GitLab 非根链接归并到原项目、声称版本按报告首个版本与唯一 tag 对齐、baseline 交错步骤前与回调后 URL，基准 79 passed。新增测试的格式检查曾退出 1，按 Ruff 指示修正后全量格式检查退出 0。
- 第二十三次完整只读复审指出 B03 先描述并引用旧版、后声称无来源新版为最新版仍可满覆盖。新负例先 1 failed/79 deselected；修复后又以同句旧版与有来源新版的正例先 1 failed/80 deselected，明确最新版声明优先使用其后的版本，且须与唯一官方 tag 一致；基准 81 passed。
- 第二十四次完整只读复审指出 B02 仅引用两套文档首页也可满覆盖，以及上游超时步骤未写入 history 时 baseline 回调 URL 与下一条历史记录错位。两个新增负例先 2 failed/81 deselected；现在 B02 要求具体文档页，baseline 按回调时已保存的 history 条数插入访问观察；修复后基准 83 passed。
- 第二十五次完整只读复审指出 B03 `Unknown or unfinished` 段仍可提供版本、日期和变更，以及 adaptive 动作已完成但紧接着达到时间上限时漏记步骤、访问和轨迹。三个新增负例先 3 failed/117 deselected；现在计分先剔除未完成段，AgentLoop 将已完成但尚未评估的工具结果交给基准适配器计入安全元数据；聚焦复验 120 passed、基准 85 passed。随后仅对这两处修复运行一次限定范围的实际只读复审，结论无阻断发现。

## 命令原始结果摘要

| 命令 | 退出码 | 输出或异常 |
| --- | ---: | --- |
| `npm ci --prefix frontend` | 0 | added 142 packages；本机 Node v23.11.1 对 `abbrev`/`nopt` 有 EBADENGINE 警告，CI 指定 Node 22 |
| `npm run type-check --prefix frontend` | 0 | `vue-tsc --noEmit` |
| `npm run test --prefix frontend` | 0 | 1 file，20 passed；第二十轮部分报告回归修复前 1 failed/19 passed |
| `npm run build --prefix frontend` | 0 | 12 modules transformed，Vite build 完成 |
| `uv run --isolated --python 3.12 --offline --locked pytest -q -p no:cacheprovider --basetemp .pytest_cache/d6-final-after-25-312` | 0 | 383 passed，1 deselected，15.49 秒 |
| 同命令改为 `--python 3.13`、`--basetemp .pytest_cache/d6-final-after-25-313` | 0 | 383 passed，1 deselected，17.66 秒 |
| D5/D4 定向 `pytest`：API/SSE/数据库/持久化/AgentLoop/TaskManager | 0 | 67 passed |
| `uv run --offline --locked pytest -q -p no:cacheprovider --basetemp .pytest_cache/d6-review25-benchmark-final tests/unit/test_benchmark.py` | 0 | 85 passed；第二十五轮三个定向回归修复前 3 failed/117 deselected |
| `uv run --offline --locked ruff check adaptive_agent backend benchmark tests` | 0 | All checks passed |
| `uv run --offline --locked ruff format --check adaptive_agent backend benchmark tests` | 0 | 76 files already formatted |
| `uv run --offline --locked python -m compileall -q adaptive_agent backend benchmark tests` | 0 | 无错误输出 |
| `uv lock --check --offline` | 0 | Resolved 282 packages in 4ms |
| `uv run --offline --locked python -m benchmark.runner` | 0 | B01–B03 × 三组 × 两次，18 项，`live_runs=0` |
| `uv run --offline --locked python .pytest_cache/d6-recheck-live/controlled_benchmark.py` | 0 | `CONTROLLED_FAKE_ONLY`；`d6-controlled-b1f1536c` 的 18 个 JSON，2 次失败保留，三组各 6，完成率均 null，baseline parity mismatched；中断的 16 条另存，未计入 |
| `git -c submodule.recurse=false diff --check --ignore-submodules=all` | 0 | 无空白错误；仅 LF→CRLF 工作区提示 |
| `rg -n 'DEEPSEEK_API_KEY|GITHUB_TOKEN|D6_FAKE_PROVIDER_ONLY|sk-[A-Za-z0-9]{8}' frontend/dist frontend/src frontend/public` | 1 | 无匹配；1 是 `rg` 对空结果的正常退出码 |

受限沙箱中的 `npm ci` 报 npm `Exit handler never called`，`uv` 读取解释器/缓存报访问拒绝，均未计为测试结果；获准本机环境中的上述命令才是通过证据。本机 Node 23 的 `abbrev`/`nopt` EBADENGINE 警告不影响退出码，CI 指定 Node 22。没有跳过或削弱失败测试。

## 隔离浏览器用户路径

实际 FastAPI/Vite、隔离 SQLite，注入**受控伪造提供方、浏览器和 GitHub 工具**；不代表真实 DeepSeek 研究。

1. 使用 Tab、Enter 提交“研究 FastAPI 的公开资料”：`72fbb741-f069-408d-9559-866ed7a0893a`，POST 202；详情/轨迹 200，页面完成、时间线 5 条、报告来源 `https://api.github.com/repos/fastapi/fastapi`。刷新后报告和最近任务恢复。
2. 提交“取消路径验证任务”：`25021957-b049-4aee-a53b-04bfd46e48f6`，POST 202，SSE GET 200；取消 POST 200，页面为“已取消”、原因 `user_cancelled`、时间线 4 条。刷新后状态与服务端一致。
3. `?task=unknown-d6-recheck` 显示 404 说明；无密钥 POST 503 显示配置说明；浏览器直接提交空白 goal 返回 422；停 API 后刷新得到 Vite 代理 500，并显示“本地 API 暂时不可用”。
4. 等待任务 `b7f373de-1e40-4238-a3a7-a48beb915999` 有 200 SSE、两条初始事件。停止 API 后页面显示重连提示；同库以无密钥服务重启，无手动刷新即显示“失败”、`server_restart`、第三条 `task_finished` 及失败报告。详情/轨迹再取均为 200，事件 ID 按 `task_queued → task_started → task_finished` 唯一有序。服务与 Vite 后续均正常关闭。
5. 浏览器 localStorage、sessionStorage 为空；资源请求仅见 `/api/research` 及其五种子路径。密钥不在浏览器输入、存储或 API 请求中。

## 独立审查与放行

二十五次完成的原生 `codex review --uncommitted -c 'sandbox_mode="read-only"'` 启动日志都显示实际 `sandbox: read-only`。共 61 项具体发现经主执行者复现、修复并添加回归测试；另修复一项上游默认配置偏离。最后两项修复又以明确的五文件范围执行 `codex review -c 'sandbox_mode="read-only"'`，启动日志同样显示实际只读，结论为无具体阻断发现；该审查未代替主执行者测试。另一次完整审查启动后中断、无结论，不计入完成轮次。最后一次代码修复后的双版本全量门禁均通过，D6 本地验收通过。

真实 DeepSeek 三类公开任务、协议 18 次真实基准、逐条官方来源人工核对和远端 GitHub Actions 均属于 D7/远端未验证。受控 18 条记录不得用于性能改善或受控机制优势声称。
