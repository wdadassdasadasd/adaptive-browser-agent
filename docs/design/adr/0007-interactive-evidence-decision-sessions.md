# ADR-0007：交互式、有证据的技术调研会话

- 原日期：2026-10-26；当前配置：**PREP-BASELINE-20261029**。本页解释已批准设计，实际实现/验收见[唯一任务记录](../../features/DECISION-001/tasks.md)。
- 依据：[规格](../../../SPEC.md)、[计划](../../../PLANS.md)、[当前契约](../../contracts/CURRENT_CONTRACTS.md)、[ADR5部署](0005-windows-worker-wsl-postgres.md)、[ADR8决定](0008-m1-engineering-baseline.md)。

## 问题与选择

从零调研需要把原始需求、澄清提议、用户接受、技术路线、候选、证据和报告分开；旧单轮/预置候选或固定ASR/TTS/dialogue不足以表达该流程。保留显式会话方案B，相比父子Task重建更易核对归属、历史和活动轮，代价是对象授权与事务恢复。采用LangGraph实际阶段节点，不把整个AgentLoop包成节点；单用户吞吐不是使用Pg的充分理由，选择还包含可靠性与个人工程实践目标。

## 对象和数据流

Draft保存尚未接受的原文；Session属于认证owner并持version/active指针。ResearchCase在首次澄清模型调用前建立，固定原始目的、分配与累计界限。澄清响应只是提议/未知/出处，不写已接受条件。本人接受后产生不可变InputRevision与Task；Turn由同一Task承载唯一执行状态，Attempt是同Task的执行代次，不是新业务轮。

研究图为载入接受条件→路线计划→发现/取源→主张抽取→身份/缺口→覆盖停止→必要Gap→上下文与报告校验发布；澄清子图独立生成提议。StageOutput提交业务结果后才推进checkpoint；Graph state只引用应用已提交对象。稳定Obligation不随plan revision、序号或同义query变化，防止invalid schema/unknown被换名重发。

API只负责身份、验证和持久确认，模型调用经Worker/Gateway。接受接口带case、parent Turn、proposal identity/hash、expected session version和幂等键；同owner/session同键同正文先重放再CAS，不同正文409。接受条件、Task、active、事件和version同事务，队列满/冲突/DB故障不留孤立对象。所有对象/游标/报告/工件/事件先核owner再读出，服务端身份不由body或模型指定。

同Session仅一个非终态Task；澄清、讨论、研究共用全局2活动/4排队，Case最多8Task。等用户时终结partial并释放调度槽；答复关联新Turn、同Case重新核条件/证据，不自动追加grant、调用、时间或费用。条件改变能力验收必须在同Case的R1→接受新revision→关联Turn→R2，而非另Case重置后比较。

## 证据、记忆与上下文

Query→SourceCapture→CandidateIdentity→Claim/关系→ContextManifest→ReportSnapshot形成追溯链。同名、fork、正文相同不自动归并主体；未知版本反证先保留适用性待核。新capture不覆盖旧证据，获取时间和版本不因引用刷新。机器片段/引用校验不证明语义支持，最终人核源和真实效果分别记录。

当前接受条件优先；结构化关系＋关键词选择，不引入默认向量/Reranker。保护集合先展开关系，再筛适用性；放不下完整条件/最低证据则拒发并确定性partial。自动记忆只含来源线索和本人明确长期技术偏好，相关时提供可见建议、可纠正/停用/撤销；不能成为硬条件或权限。sourcehint和偏好分别有lineage，撤销不能通过已知别名/新ID复活，容量满的更正先停旧项。详细参数及反例测试由当前契约维护。

## 停止、在途与恢复

最终send_claimed而非admitted取得发送权。撤销/取消先提交则拒绝；claim先提交属于在途。unknown关闭全项目新出站，不改计划/Case/Turn绕过；completed凭已提交合格响应本地重处理。终态报告、事件、active释放同事务，迟到响应不改旧报告；物理槽独立于调度槽，由supervisor阻断旧generation后确认释放。

监督连续性与恢复身份按ADR5及契约：数据库OPEN/同UUID不证明最新，旧cookie/密码/grant不从恢复副本复活。有限认证claim与seal也保留在途语义，不保证瞬时撤回；同Pg进程任意管理员在线回灌不在自动检测承诺内。

## 首个纵切与验收

本人选首工真实登录→保存原始草稿→重开→第二测试身份404，并同时建立最小supervisor。它不创建接受InputRevision或Task，不运行模型/工具/Tokenizer/Browser；之后02再交付接受并启动研究的原子操作。可信本机HTTP、服务端会话、Argon2id、Host/Origin/CSRF和受限Pg角色由契约给精确边界。实际WSL路径、角色、建库/迁移和依赖资格是另授权前置。

软件验收、本人价值和个人实践分开。正式Agent侧手工修稿不用外部AI代修；Control侧普通AI与独立DR。首次揭题计时、共同质量、失败保留和费用规则只引用[唯一协议](../../evaluation/CURRENT_EVAL_PROTOCOL.json)，不在会话实现中另立分母。

2026-10-26旧方案B批准及当时v3.1设计审查、2026-10-28的D01–D19方向/11文档同步属于原内容证据。它们不覆盖本次实际文件或实现；原六API/双入口、五账户、单次决策和9/8/12不成为现行规则。历史记录及真实失败受保护，配置批准不授权业务开工。
