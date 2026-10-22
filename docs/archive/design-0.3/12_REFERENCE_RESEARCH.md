# 高 Star 参考项目的可核验设计对照

> 状态：**APPROVED（参考记录）** · 2026-10-18。以下只引用项目官方文档或源码；GitHub Star 数量不是架构选择依据。外部 `main` 会变化，只有 browser-use 项目内锁定的 `7be96ed8bafa8dfe1eef228b59cf5c884b8b2431` 以固定 commit 引用。本记录不代表这些项目的能力已在本项目实现。

| 参考项目 → 具体官方设计/源码 | 优点 | 本项目是否适用与采用方式 | 不采用原因或验证限制 |
|---|---|---|---|
| [browser-use 固定版本 SecurityWatchdog](https://github.com/browser-use/browser-use/blob/7be96ed8bafa8dfe1eef228b59cf5c884b8b2431/browser_use/browser/watchdogs/security_watchdog.py)及[BrowserProfile](https://github.com/browser-use/browser-use/blob/7be96ed8bafa8dfe1eef228b59cf5c884b8b2431/browser_use/browser/profile.py#L628-L640) | 区分导航前的地址/域名限制、导航完成后检查与新标签页处理；BrowserProfile 暴露域名和 IP 限制配置 | **适用**：保留当前 Adapter 边界，Gate 2 用受控私有地址、重定向和弹窗实验确认锁定版本的实际网络边界；导航前拒绝与导航后检测分别验收 | 导航后拦截不能撤销已发请求；仅从配置项不能断言 SSRF 已全面阻断。不能以外部 `main` 行为替代锁定子模块事实 |
| [browser-use AgentHistoryList](https://github.com/browser-use/browser-use/blob/7be96ed8bafa8dfe1eef228b59cf5c884b8b2431/browser_use/agent/views.py#L590-L668) | 历史列表有可选用量，但序列化路径可能只导出 history | **适用**：用量必须在本项目明确的安全事件中落库并从 trace 对账，不能假设第三方 history 自动带出 usage | 不复用第三方历史对象作 ResearchState 或数据库真相源 |
| [Skyvern 故障 FAQ](https://github.com/Skyvern-AI/skyvern/blob/main/docs/developers/debugging/faq.mdx)与[Artifacts 说明](https://github.com/Skyvern-AI/skyvern/blob/main/docs/developers/debugging/using-artifacts.mdx) | 以 run status/failure reason、时间线和 run_id/step_id 关联制品定位故障 | **适用**：本项目用 task_id、event_id、step、失败类别和安全的步骤级拒绝摘要支持复盘 | 不存全量模型响应、HAR、录像或云端制品；这些会扩大隐私、存储及四周成本。Skyvern 并未提供本项目事实候选拒绝的可直接照搬契约 |
| [Stagehand v3 API 参考](https://github.com/browserbase/stagehand/blob/main/packages/docs/v3/references/stagehand.mdx#L434-L494) | `act/extract/observe/agent` 分操作用量、推理耗时和操作历史，`close()` 资源语义明确 | **适用**：把本项目 `initialize/plan/evaluate/repair/report` 设为互斥计量阶段，逐请求记录已报告用量及未知调用，按事件与任务对账 | 不引入第二套浏览器 SDK；其聚合指标不能证明本项目 DeepSeek 修复请求的用量归属 |
| [LangGraph 持久化说明](https://github.com/langchain-ai/docs/blob/main/src/oss/langgraph/persistence.mdx)和[事件类型源码](https://github.com/langchain-ai/langgraph/blob/main/libs/langgraph/langgraph/types.py) | 将任务事件、状态 checkpoint 和恢复语义分开；内存 checkpoint 不能跨重启 | **适用**：继续把当前 `server_restart` 定义为终态处理，事件补读不称断点续跑 | 当前没有暂停恢复需求；迁入 Graph 会出现第二套状态和运行时，超出业务价值与工时 |
| [Dify trace 用量汇总](https://github.com/langgenius/dify/blob/main/api/core/ops/ops_trace_manager.py#L3248-L3325)与[Workflow ORM](https://github.com/langgenius/dify/blob/main/api/models/workflow.py) | 节点执行顺序和阶段用量便于问题定位；缺失 usage 的聚合逻辑提醒区分“已知和”与“完整总额” | **适用**：保留已报告 Token 下界及未知调用数，完整总量不明时 UI/评测为 `null`，不把缺失计零 | 不复制多租户工作流平台、Redis/Celery 或复杂追踪基础设施 |
| [browser-use benchmark v2.1.1 说明](https://github.com/browser-use/benchmark/blob/main/README.md) | 固定任务及版本、逐任务事件与评分证据有利于复算 | **适用**：G2-EVAL-v1 保留九次 B01–B03 回归与三次独立留出尝试、代码/模型/环境指纹、人工核源和原始失败；r12 原件不重算 | 其任务与评分不能直接等同 B01–B03；小样本不能宣称显著性 |

## 对三项设计修订的实际影响

1. **事实拒绝**：五个参考项目均未被证实提供可直接复用的“研究事实候选→逐项拒绝原因→安全持久事件”契约。本项目只提出步骤级数量与首原因码，不保存被拒绝候选正文；这是 **PROPOSED** 的本地取舍，不冒称外部实践已验证。
2. **用量**：外部阶段指标不等于本项目每次 DeepSeek 请求的报告用量。当前 Provider 会合并首次结构化调用与修复调用；因此必须先在 Provider attempt 边界观测，再做互斥阶段汇总。未知调用与已知下界分开。
3. **浏览器安全**：导航前显式目标校验与导航后最终 URL 检查是不同保证。受控跳转实验前，重定向是否在发出私有请求前被拦截仍 **UNVERIFIED**；只批准可信本机演示，公网/多用户另需安全设计。

## 证据限制

本次只读核对了外部官方材料，没有运行这些项目、浏览器重定向实验或付费模型。Skyvern GitHub FAQ 在一次网页抓取中返回错误，以上仅使用研究过程中可定位的官方文件路径；若未来要据此实施具体 API，须重新打开对应官方源码。外部 `main` 链接按日期记录，实施前复核版本。没有以 Star 数或来源项目的架构规模推导本项目应增新组件。
