# P-02 r11 三题调用级失败诊断与首个定点修复

任务：P02-PILOT 后的 P02-DIAGNOSE / P02-FACT-REPORT。基线为同一[运行冻结](../../data/evaluation/p02-pilot-runtime-freeze-r11-20261023.json)下的三次真实尝试；原始捕获、人工复核包与费用总账不改写。本记录的代码修复只经过离线验证，尚无优化后的真实复查。

| 题目 | 首个可见偏差及后续停因 | 证据与限制 |
| --- | --- | --- |
| B01 `39d4a2d0-8729-5b97-be65-a87d0678a0f2` | 第 0 步 GitHub 搜索没有足够字段，第 1 步直接仓库读取 HTTP 403。第 2–4 步连续浏览器导航，始终没有提取或准入事实；第五次无事实重规划后按 V1 既定阈值 `no_progress` 停止。 | [原始事件](../../data/evaluation/p02-pilot-r11-20261023/39d4a2d0-8729-5b97-be65-a87d0678a0f2/capture/events.json)、[报告](../../data/evaluation/p02-pilot-r11-20261023/39d4a2d0-8729-5b97-be65-a87d0678a0f2/capture/report.json)；[V1 契约](../contracts/V1_CONTRACTS.md)规定至多五次无新事实/子目标的重规划。403 增加了回退路径，但不是已证明的唯一根因。 |
| B02 `347bd8b2-0e09-5975-8dff-e8ed4f2c1a52` | 官方 FastAPI 页面抽取后没有准入事实；随后结构化模型请求的本地预检发现剩余 15,533、请求保守上界 15,576、输出余量 −43，未发 provider 请求。 | [原始事件](../../data/evaluation/p02-pilot-r11-20261023/347bd8b2-0e09-5975-8dff-e8ed4f2c1a52/capture/events.json)、[持久事件只读补证](../../data/evaluation/p02-pilot-r11-20261023/budget-preflight-supplement-20261023.json)。缺少原始 Prompt，不能复算其具体组成或证明裁剪 43 字节就能完成任务。 |
| B03 `e4e3e822-f5f0-582d-9412-e7cb91daefe4` | GitHub 发布 API 403 后转浏览器；第一次提取事实无观察证据，第二次准入两条候选。后续结构化请求的本地预检剩余 8,123、上界 15,171、余量 −7,048，未发 provider 请求。候选事实的 `retrieved_at` 早于运行。 | [原始事件](../../data/evaluation/p02-pilot-r11-20261023/e4e3e822-f5f0-582d-9412-e7cb91daefe4/capture/events.json)、[事实](../../data/evaluation/p02-pilot-r11-20261023/e4e3e822-f5f0-582d-9412-e7cb91daefe4/capture/facts.json)、[补证](../../data/evaluation/p02-pilot-r11-20261023/budget-preflight-supplement-20261023.json)。人工只核实版本、Latest 和 URL，发布日期与两项变化仍缺失。 |

补证 SHA-256：`3bd610928a0522d78d2d7f42704069f9b245abec67c9cc3e1b6850ed16b9672b`。它来自隔离 PostgreSQL 的 `app_event.task_finished` 行，只读查询事件 ID、时间和 `budget_preflight`；绑定三份原始捕获的 `events.json` 与 `manifest.json` 哈希。B01 持久事件没有预算预检。原脱敏捕获投影遗漏了安全的 `budget_preflight` 字段，因此只在后继工件补证，并修复未来捕获；不重写原件。

## 根因与修复范围

1. **已证实的本地终止机制：** B01 触及现行五次无事实重规划门槛；B02/B03 是模型 HTTP 请求前的保守 Token 上界拒绝，不代表实际已用满 40,000 Token。改变 B01 门槛会触及 V1 契约；本次没有改变停止规则。下一步应以冻结轨迹设计“先提取可用页面证据”的规划回归，以及针对 B02/B03 的上下文选择实验，保留字段覆盖与 Token/费用对照；不能凭本次轨迹承诺成功率提升。
2. **已证实的事实时间错误：** [Worker](../../backend/src/adaptive_research/worker/runner.py)先前把模型可提供的 `ResearchFact.created_at` 作为持久化 `retrieved_at`。B03 的旧日期与该路径相符，但不能反向证明模型为何输出了该日期。后续版本改为使用本次 `step_evaluated` 事件时间；原 B03 事实不改写，也不据此补足来源定位或官方身份依据。
3. **诊断捕获缺口：** [pilot_capture](../../backend/src/adaptive_research/evaluation/pilot_capture.py)现在仅在结构、数值关系与 `provider_request_started=false` 有效时导出预算预检的五个安全字段，并丢弃任何额外键。这样未来失败可从脱敏捕获直接区分本地拒绝与已发请求；没有保存 Prompt 或工具正文。

离线回归先红后绿：新增 Worker 旧时间戳用例先失败，修改后通过；新增预检字段用例先因字段缺失失败，修改后通过。`backend` 中 `python -m pytest -q tests/unit/test_worker_fact_timestamp.py tests/unit/test_pilot_capture.py` 为 **20 passed**；`python -m pytest -q tests/unit/test_evaluator.py tests/integration/test_agent_loop.py` 为 **57 passed**；`python -m pytest -q tests` 为 **605 passed、3 skipped、1 deselected**。受改文件的 `ruff check`、`ruff format --check` 退出 0。仓库根目录 `python scripts/validate_project.py --ledger data/evaluation/ledger-after-e4e3e822-f5f0-582d-9412-e7cb91daefe4.json` 与 `git diff --ignore-submodules=all --check` 均退出 0。PostgreSQL 持久事件已只读核对，本次修改后的新运行未执行；前端未改且本轮未重跑。真实研究效果尚未复查；P-02 质量和产品仍 No-Go。
