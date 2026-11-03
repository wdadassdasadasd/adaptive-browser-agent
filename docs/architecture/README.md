# 架构入口 — RESEARCH-BASELINE-20261103

[SPEC](../../SPEC.md)定义产品，[PLANS](../../PLANS.md)定义依赖，[契约](../contracts/CURRENT_CONTRACTS.md)独占对象/权限/限额，[唯一任务](../features/DECISION-001/tasks.md)记录实际状态。本页描述目标，不把配置写成实现。

## 获批目标

Windows UI → WSL API → 应用Pg ← Worker/LangGraph阶段 → 精确请求Gateway → GitHub，必要时补DeepSeek Search/Fetch。Browser=0且真实接入延期；MCP仅研究。应用表拥有条件、team/project/member/source grants、Task/Attempt/Work/Call、SourceSet/LocalCapture、DocumentVersion/head/RequirementsConfirmation、证据、报告、usage及费用；checkpoint只持有已提交引用。

四模式：仅评审、仅需求、仅方案、完整需求到方案。想法可无仓库，或固定一个主GitHub版本及许可公开材料，加本人选定本地text/code/diff；源码不执行，diff不应用。接受目标/范围 → 选定SourceSet封定/固定仓库版本 → 有界研究 → Claim及问题依据 → 受保护Context → 需求DocumentVersion → 本人准确RequirementsConfirmation → 方案DocumentVersion → 有界ReportSnapshot引用双稿及确认。评审沿原报告路径，仅需求可独立结束，仅方案先确认既有需求。直接编辑和AI修订均追加版本，显式保存而非逐键；新需求head原子清当前确认，方案start/send/commit重核准确绑定及head CAS，旧稿按引用标过期。首工件compile/Token/版本槽/正文及终结预留同事务，容量不足零发送，改版和模式不重置Case额度。探索任务不伪造验收基准，未读不等不存在，机器片段准入不证明语义。UI/导出按当前权限读取不可变快照；每响应/页/SSE帧重新claim，最后一个有界已claim响应可能在途。Task独立执行许可与UI读会话分开。

最终send和提交门禁、unknown停新外调、完成或未知调用不重发、失租fence及资源收拢按契约。私有实际输入祖先随派生保留。Context03a保护条件／反证／限定，Token03b分离本地完整格式、托管fit及实际usage／费用；合法差异记录，溢出撤受影响资格，费用unknown全停。Memory全部功能入口继续禁用并延期：手动／自动、API／CLI、默认profile／框架、旧checkpoint、导入／恢复／重建和后台均不得产生候选、读写、检索或注入。active refs为空并与实际请求核对，Trace记disabled/not_applicable、null hits/writes及feature_disabled。Case资料正常持久化；显式选入历史报告走SourceSet权限及私有祖先核验，不解引用Memory。04／17未实施、未验且非当前M1前置，预留闲置；重开需真实需求、独立审查与另行批准。 具体约束只在[契约](../contracts/CURRENT_CONTRACTS.md)维护。

主研究者保全局连续性和人类讨论，独立子问题按需委派为同Task Work，不递归、不产生新grant或预算。Assignment绑定当前接受版本、问题／依赖、来源权限子集、Context和原截止；共享取材归Task、各消费者独立核权，单次capture不算独立佐证。创建／替换／回放幂等，取消与物理清理分开；无关分支进展不使有效结果失效。编译前封存研究输入，关键义务不足诚实partial，可选失败／未读披露，迟到结果仅audit。具体状态与失败规则由契约和后续程序测试落实。

六用途的模型职责见[PROMPT_CONTRACTS](../contracts/PROMPT_CONTRACTS.md)，这份目标文档未被旧运行代码加载。全部主子调用共享Case池，compile≤4含技术retry；首次尝试失败不补回首稿预留，后续只用剩余额度。

[ADR5](../design/adr/0005-windows-worker-wsl-postgres.md)保部署及恢复理由，[ADR7](../design/adr/0007-interactive-evidence-decision-sessions.md)定义状态归属，[ADR8](../design/adr/0008-m1-engineering-baseline.md)区分本轮决定与历史批准。首工仍认证/私人Draft/第二身份隔离/最小sup，无InputRevision或研究Task；业务和环境另授。

## 已实现历史

V1 Vue/FastAPI/AgentLoop/SQLite按[V1契约](../contracts/V1_CONTRACTS.md)解释。旧Pg API/Worker已有[P-01假任务48/48](../tasks/P01_ACCEPTANCE_2026-10-21.md)，不证明新认证、WSL拓扑或真实研究。旧launcher会启动服务/迁移，不作只读探针。T02–05离线片段及r11/r12失败见[原代码审查](../audits/IMPLEMENTED_CODE_REVIEW_2026-10-27.md)。旧current-3运行器拒新协议；本批不创建新业务runner。前端只经API、状态可序列化、browser-use保持上游归属；冷切不删旧库或费用，回滚先停写，不能让不兼容旧binary写新库。

选定本地上传经API有界stream、解码及许可/容量两端核验，未seal不入模型，不引入FS bridge。已知私有祖先不因local profile/编辑/导出重导入洗白，未知外部出处不冒核实。REQ full/CON review含无基准子问/EXP确认需求后仅方案，三pair只描述登记样本；正式材料和业务效果均待证。旧review交付继续绑定原字节，当前配置检查/独审由唯一记录及新外置索引裁定。
