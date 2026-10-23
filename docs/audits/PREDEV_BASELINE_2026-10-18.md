# 开发前现状核验（2026-10-18）

**方法**：只读检查当前主仓库源码、测试入口、0.3 设计和历史 r12 记录；本文件的 `VERIFIED` 指“源码/记录存在”，不等于真实业务验收通过。审计起点 HEAD `dbacdc02fb119f70bc65a14608ab1bede75c0622`，当前工作区有用户未提交改动；`browser-use` 子模块的实际清洁状态未验证。本轮不改历史 V1、r12 原件或 SQLite。

## 已实现链路

| 核对项 | 证据与当前行为 | 状态/限制 |
| --- | --- | --- |
| 应用启动 | `backend/main.py:15-35` 建表、创建服务、重启恢复与关闭 | VERIFIED 源码；干净环境启动待实测 |
| 主链路 | `backend/services/research.py:48-113` 连接 DeepSeekClient、BrowserUseAdapter、GitHubTool、ToolRouter、AgentLoop；创建时先持久 queued 再提交 TaskManager；AgentLoop 的观察、计划、工具、评估、Reducer、报告见 `adaptive_agent/agent_loop.py:133-177,240-329,338-475` | VERIFIED 源码；真实任务仍失败 |
| 路由 | `backend/api/research.py:55-171`：`POST /api/research`、`GET /api/research`、`GET /api/research/{task_id}`、`GET /api/research/{task_id}/events`、`GET /api/research/{task_id}/traces`、`POST /api/research/{task_id}/cancel` | VERIFIED 六路；不把 SSE 当另一持久源 |
| 状态与事件 | `adaptive_agent/state.py:85-91`：queued/running/completed/partial/failed/cancelled；`adaptive_agent/events.py:10-17`：task_queued/task_started/subgoals_initialized/step_evaluated/cancel_requested/task_finished | VERIFIED 六状态、六事件 |
| 数据表 | `backend/db/models.py:17,37,55,78`：research_task/research_step/research_fact/agent_trace | VERIFIED 四表；无独立报告表 |
| 写入与报告 | `backend/services/persistence.py:177-249` 事务写状态、step、准入 fact、trace；终态报告在 task_finished payload，由 `backend/api/research.py:27-52` 重建 | VERIFIED 源码；大规模异常一致性待测 |
| SSE/UI | `backend/api/research.py:114-153` 从 SQLite 补读、TaskManager 队列唤醒；`frontend/src/api.ts:51-80` 封装接口；`frontend/src/App.vue:89-110,146-216,295` 刷新详情/trace、订阅/轮询和释放流 | VERIFIED 路径；真实断线/慢订阅竞态待测 |
| 取消/重启 | `backend/services/research.py:137-167` 分 queued/running 取消；`backend/services/persistence.py:350-428` 将重启时未完成任务有事实转 partial、无事实转 failed，原因 server_restart，不续跑 | VERIFIED 路径；取消与自然完成竞态、资源释放待测 |

`ResearchState` 是可序列化领域状态，见 `adaptive_agent/state.py:123-145`；其用量当前只汇总已报告值。AgentLoop 使用 DeepSeek 并有单次工具技术重试及预算/停止分支；不能从这些代码路径推定目标完成率。分层依赖和目标责任由[候选 SPEC](../../SPEC.md)定义，0.3 冻结架构仍见[设计索引](../archive/design-0.3/00_DESIGN_INDEX.md)。

## 已设计与未验证的缺口

| 主题 | 证据 | 判定与下一步 |
| --- | --- | --- |
| 调度失败补偿 | `backend/services/research.py:69-77` 在已提交 queued 后调用 `submit`，没有本地补偿 | **VERIFIED 缺口**；G2-05 先复现，再使任务可终结 |
| 事实拒绝原因 | `adaptive_agent/evaluator.py:126-159` 做 URL、片段和主体核验；0.3 目标需要步骤级拒绝数量/原因码 | **TARGET 未实现**；G2-04 不应放松无源事实门槛 |
| 请求级用量 | `adaptive_agent/state.py:136-137` 只有累计已报告 Token；阶段/独立修复/未知 attempt 诊断未记录 | **TARGET 未实现**；G2-01/02 先核调用轨迹再计量 |
| 证据/诊断 UI | `frontend/src/App.vue:323-334` 有报告及来源展示，缺独立事实证据卡、阶段用量和拒绝摘要 | **TARGET 未实现**；G2-07 从真实 API 投影 |
| 浏览器访问边界 | 直接显式导航公有地址校验有代码；DNS 变化、重定向/点击/弹窗/子资源是否事前拦截缺实测 | **UNVERIFIED**；本机单用户公开资料限制继续有效 |
| 实际业务/生命周期 | 当前已有 Fake/集成测试与路由，未完成新版真实批次、正式来源核验、干净环境复现 | **UNVERIFIED / No-Go**；须另获费用授权 |

## 历史结果与版本冲突

[D7 交付报告](../archive/v1-audits/V1_DELIVERY_REPORT.md)记载 r12 共 18 次真实 benchmark 尝试，三组完整成功率均 0；full-system 平均字段覆盖约 13.3%。三次独立 UI 任务分别在 B01/B02 因 `token_budget`、B03 因 `no_progress` 失败。baseline 六次 Token 记录缺失，预算不对等；不能据此做成本改善因果结论。原始数据和旧 scorer 均保留。

现行获批 0.3 的 `docs/design/01_PRODUCT_REQUIREMENTS.md:62`、`05_TEST_AND_EVALUATION.md:63-65`、`06_ACCEPTANCE_AND_RELEASE.md:17,24,60` 设 B 九次聚合 68/75 字段阈值；[0.4 候选](../../SPEC.md)拟以**每次完整成功须全字段**和每次独立报告覆盖取代聚合阈值。此为显式设计冲突，0.4 获用户确认前仍依 0.3 权威，不静默改动上述历史文件。
