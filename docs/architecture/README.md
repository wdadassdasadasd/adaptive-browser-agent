# 架构入口 — PREP-BASELINE-20261029

本页导航当前目标和已实现历史，不另立契约。[SPEC](../../SPEC.md)定义产品/AC，[PLANS](../../PLANS.md)定义依赖，[当前契约](../contracts/CURRENT_CONTRACTS.md)定义对象/API/状态/锁序/限额，[唯一任务](../features/DECISION-001/tasks.md)维护实际状态。

## 获批目标

Windows UI→WSL独立API→应用Pg←独立Worker/LangGraph阶段图→CallGateway→Search/GitHub/Fetch及资格后受限Browser。Draft/RawMessage/Case/InputRevision/唯一Task/Attempt/fence/稳定Obligation/物理Call/Source/Claim/Report/费用由应用表拥有；checkpoint只是有界已提交引用，独立schema/role/connection，不是业务或资金权威。

从零需求先澄清接受，再路线/发现/短名单/取证/上下文/报告，不整体包装旧AgentLoop。稳定工作、最终send_claimed、unknown全项目停新出站及generation物理槽防止重规划/恢复重发。关系＋关键词上下文、来源线索与明确长期技术偏好Memory均按契约，记忆不作条件或权限。

[ADR5](../design/adr/0005-windows-worker-wsl-postgres.md)解释新独立cluster/连续sup/保守恢复，[ADR7](../design/adr/0007-interactive-evidence-decision-sessions.md)解释Session/Case/Turn，[ADR8](../design/adr/0008-m1-engineering-baseline.md)记录采用理由。首工是认证/原始Draft/第二身份隔离＋最小sup，不建InputRevision/Task/模型调用。环境、依赖、schema和安全实际证据仍待对应授权验证。

## 已实现历史

V1为Vue→FastAPI→ResearchService/TaskManager→AgentLoop→Planner/ContextManager/Evaluator/Reducer/Reporter→ToolRouter；SQLite保存事实/事件，以[V1规格](../specs/V1_SPEC.md)、[V1契约](../contracts/V1_CONTRACTS.md)、源码和测试解释，不是新业务入口。

旧P-01为Vue→api.pg_main→Pg←worker.runner→AgentLoop，租约/fence/调用/事实/事件已有[假任务48/48](../tasks/P01_ACCEPTANCE_2026-10-21.md)。旧launcher保活WSL、启Pg/自动迁移、监督Windows Worker，仅历史行为，不能当新环境只读探针。单合成owner不证明新真实认证，旧重认领/时限不作新默认。

T02–05离线决策切片及r11/r12失败见原任务及[代码审查](../audits/IMPLEMENTED_CODE_REVIEW_2026-10-27.md)。旧current-3执行器不能跑新协议，本配置只加拒绝/历史显式校验，没有新runner。P-02/r12 No-Go保持，假任务/CI不证明来源质量、本人价值和恢复。

前端只经API，路由不依赖browser internals，状态可序列化，上游browser-use保持。冷切保旧库/费用/授权/真实证据；回滚保数据停写，不让不兼容旧binary写新库。独立审查、本人验收、Go与发布分开。
