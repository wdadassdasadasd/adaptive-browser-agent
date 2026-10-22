# Adaptive Research Agent — 0.5 目标规格

**状态：用户确认的开发前目标，业务尚未实施。** 2026-10-18。本文件取代 [0.4 历史快照](SPEC_0.4.md)作为后续明确授权任务的目标；当前实现仍以 [V1 规格](docs/specs/V1_SPEC.md)、[V1 契约](docs/contracts/V1_CONTRACTS.md)和源码为准。任务顺序见 [PLANS.md](PLANS.md)，目标边界见 [0.5 契约](docs/contracts/0.5_TARGET_CONTRACTS.md)与 [ADR-0003](docs/design/adr/0003-langgraph-postgres-lan.md)，评测见 [G3 协议](docs/evaluation/G3_EVAL_PROTOCOL.json)。0.3、0.4、r12 原件及评分保留，r12 仍为 No-Go。本规格不授权业务代码、付费运行或部署。

## 产品定位

最多 5 名可信同事在局域网自主研究公开、非敏感的技术问题。首版覆盖开源项目选型、技术文档对比和发布记录研究。每次交付可核源事实、标明适用条件与取舍的建议，以及可观察的执行和失败过程。关键事实必须以官方仓库、文档或发布页核实；其他公开网页可提供线索和注明来源的补充，不得单独支撑关键结论。证据不足须披露缺口，不虚构官方推荐、版本兼容性或成功。输入不含敏感内容，不访问登录后资料，不执行外部写入。约 20 人目标留待个人和小团队版本成功后重评。

## 当前与目标架构

**CURRENT（V1）**：Vue 3 → FastAPI/ResearchService/进程内 TaskManager → AgentLoop → Planner/ContextManager/Evaluator/StateReducer/Reporter → ToolRouter → GitHubTool/BrowserUseAdapter；SQLite 保存任务、事实、事件。六路 `/api/research` 已有代码，但真实 r12 业务成功未获证实，尚无团队账户和归属隔离。

**TARGET（未实施）**：保留 Python、FastAPI、Vue 3、DeepSeek、GitHubTool 和 browser-use 的可用边界，选择性复用经诊断和测试证明可靠的代码。LangGraph 是新运行核心；PostgreSQL 应用表保存任务、权限、事实、报告及用户可见事件，PostgreSQL 检查点用于执行恢复。检查点不充当业务事实，SSE 唤醒不充当事件存储。[LangGraph 官方文档](https://docs.langchain.com/oss/python/langgraph/checkpointers)提示重放可能重新执行节点，故不确定的浏览器动作必须单独处理。

```text
用户 → HTTPS → Vue/FastAPI（认证、研究 API、归属、SSE 补读）
                   ↓ 持久入队/取消/查询
          PostgreSQL 应用表 ← 已提交事实/报告/事件
                   ↑ 原子认领/租约/终态
Worker → LangGraph（观察→规划→工具→证据评估→状态→报告）
                   ↕ PostgreSQL 检查点（执行恢复）
             GitHubTool / BrowserUseAdapter → 公开网络
```

同一 Windows 11 主机运行 HTTPS 代理、前端/API、独立 Worker 和 PostgreSQL。最多 2 项同时运行、至少 8 项安全排队；持久租约、原子认领、唯一终态和取消竞争须验证。[PostgreSQL 行锁文档](https://www.postgresql.org/docs/current/sql-select.html)说明 `FOR UPDATE SKIP LOCKED`，不证明指定主机容量。已提交应用事件是 SSE 补读的唯一事实来源，重连按事件 ID 补读。

## 数据流和故障语义

1. 初始管理员开通、停用和重置本地账户；用户经 HTTPS 登录，API 验证会话、CSRF、输入和 owner，持久入队后返回任务 ID。管理员只管理账户，不默认读取成员研究内容。
2. Worker 原子认领任务，LangGraph 观察、规划、调用 GitHub/浏览器、评价来源和事实、更新状态、生成报告。临时技术错误有界重试；目标不符或证据不足应重新观察和规划。页面与工具输出视为不可信。
3. 应用事务提交准入事实、社区补充、建议、状态、报告和用户事件。三类内容在数据与 UI 中明确分层。建议引用事实 ID、官方来源、适用条件和未知项；Vue 的 loading/error/partial/success 由 API 状态推导并释放 SSE 订阅。
4. 同一任务在故障后最多自动恢复一次：保留已提交事实，重启浏览器并重新观察、规划；不原样重放结果不明的动作。第二次故障以 `partial` 或 `failed` 诚实终结。终态唯一、不可逆，取消和异常释放资源。
5. 原始 V1 SQLite 原件只读保留；可重复导入到新存储，旧任务仅**初始管理员**可在新 UI 查询，成员不默认共享，导入失败不损坏原件。

保留六路 `/api/research` 路径及核心语义；增加登录、注销、当前用户和管理员账户接口。列表、详情、trace、SSE、取消均逐对象授权，不通过响应差异泄漏他人任务。精确 DTO、索引、迁移与状态码在相应实施任务冻结，见 [目标契约](docs/contracts/0.5_TARGET_CONTRACTS.md)。

## 部署与安全放行

容器优先，先实测 Windows 11 主机的 WSL/Docker、Chromium 和双任务 CPU/内存/磁盘占用；容器不可用时评估同机原生服务回退。目前本机未识别 Docker 命令，WSL 状态因权限未核实。LAN 入口须 HTTPS、独立安全会话、登录限速、CSRF、逐对象授权及浏览器外联边界。DNS、重定向、弹窗和子资源访问私网的阻断未有实证前，局域网部署 **No-Go**。服务只需工作时段在线。每日一致性数据库备份加密存异机、留存 30 天，每月演练恢复。部署前核对容器许可、异机路径和客户端证书信任。参考 [Docker Windows 要求](https://docs.docker.com/desktop/setup/install/windows-install/)、[Caddy HTTPS](https://caddyserver.com/docs/automatic-https)、[PostgreSQL 备份](https://www.postgresql.org/docs/current/backup-dump.html)。

## 需求—任务—验收

下表描述未来验收，不能视为当前通过。P1 的 FR-008 另行排期。

| 需求 | 目标 | 任务 | 验收 |
| --- | --- | --- | --- |
| FR-001 | P0 持久提交、排队、六态与历史 | G3-02、G3-06 | AC-001 |
| FR-002 | P0 LangGraph 观察、规划、工具和有界重规划 | G3-01、G3-02 | AC-002 |
| FR-003 | P0 官方事实准入、去重、归属、社区标注 | G3-03 | AC-003 |
| FR-004 | P0 已接纳事实生成可追溯报告 | G3-03、G3-07 | AC-004 |
| FR-005 | P0 已提交事件、SSE 补读与历史 UI | G3-02、G3-05 | AC-005 |
| FR-006 | P0 取消、一次恢复、故障诚实终结与唯一终态 | G3-06 | AC-006 |
| FR-007 | P0 调用级用量、失败与耗时诊断 | G3-01、G3-03 | AC-007 |
| FR-008 | P1 可编辑模板与 Markdown 导出 | 后续另行排期 | AC-008 |
| FR-009 | P0 账户、归属与初始管理员旧数据 | G3-04 | AC-009 |
| FR-010 | P0 事实支持的条件化建议与三类信息分层 | G3-03、G3-05 | AC-010 |
| NFR-001 | P0 有界运行与资源释放 | G3-02、G3-06 | AC-N01 |
| NFR-002 | P0 成本、性能及未知用量 | G3-01、G3-07 | AC-N02 |
| NFR-003 | P0 公开输入与浏览器私网外联阻断 | G3-06 | AC-N03 |
| NFR-004 | P0 故障可按调用与事件复盘 | G3-01 | AC-N04 |
| NFR-005 | P0 小步可复核交付 | G3-01、G3-07 | AC-N05 |
| NFR-006 | P0 同机可重复启动与恢复 | G3-02、G3-06 | AC-N06 |
| NFR-007 | P0 五人、双运行、八排队、租约认领 | G3-02、G3-06 | AC-N07 |
| NFR-008 | P0 HTTPS、会话、CSRF、跨账户隔离 | G3-04、G3-06 | AC-N08 |
| NFR-009 | P0 异机加密备份、30 天保留、月度恢复 | G3-06 | AC-N09 |

## 业务放行

[G3 协议](docs/evaluation/G3_EVAL_PROTOCOL.json)保留 B01–B03、G01–G03 原题与字段，预注册 O01–O03。正式 **15 次**独立尝试全部保存：B 每题 3 次且各至少 2 次完整成功；G 三题各 1 次且至少 2 次完整成功；O 三题各 1 次且全部完整成功。逐结论人工官方核源、建议与事实对应、UI/API/PostgreSQL/SSE 一致和归属检查是每次成功条件。还需跨账户访问、唯一认领与终态、一次恢复、5 人/2 运行/8 排队、HTTPS 私网访问边界及备份恢复。任一门槛未通过保持 No-Go；离线测试不代替真实成功。0.3 的 `68/75` 聚合阈值**不再设**为放行门槛，旧评分不改。

本轮只验证准备材料，不安装依赖、不改业务代码、不运行付费模型任务或部署。业务实施、真实评测和对外变更另行授权。
