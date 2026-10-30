# ADR-0008：从零技术调研的工程基线决定

状态：**PREP-BASELINE-20261029配置方案已批准**。本页原位替换旧现行目标；配置实际审查及18项完成状态只见[连续任务](../../features/DECISION-001/tasks.md)。本批40路径含限定校验/旧入口guard，不含业务、安装、环境/数据库、真实调用或Git写操作。

## 产品与价值决定

产品为从零发现候选的技术调研助手；真实起点仅“居家老人陪伴问答”，其余允许未知。先澄清接受，再路线/发现/有限深查/证据与下一步验证。主要价值减少本人搜索、整理、核源主动时间；止于调研，不实施语音或测效果。M1真实用户本人一位，第二真实测试身份用于隔离验证。

三对领域为后台调度、数据存取迁移、文档生成解析。Control含独立Deep Research，优先核Gemini免费资格；Agent侧本产品＋手工补查，不调用或复制外部AI代修。双方同预注册日常搜索引擎清单可切换，计全部主动时间；六稿共同质量全合格后中位省时率≥20%。原始技术失败不因本人修稿消失。研究方法、限时、失败/延期、版本及材料由[唯一协议](../../evaluation/CURRENT_EVAL_PROTOCOL.json)定义。

本人选择完整范围优先，2026-10-29起约七至八周、每周≤20h；本人100–144h和AI260–420 agent-hours是首周待校准估算。新增支出从10月28日本次重评开始，严格低于300元；条件分配296.46元不等于资金或调用授权。

## 候选比较与采用

| 决策及来源 | 采用理由与代价 | 未验证及重评证据 |
| --- | --- | --- |
| 本人委托AI选择、AI明确宣布LangGraph | 实际阶段节点、有限分支和可检查重入；比单自建loop有框架依赖/锁版本代价 | 不能整体包旧loop；依赖兼容和本项目质量须验，框架不是效果证据 |
| 本人选择WSL独立API/Worker/Pg与独立新cluster | 同Linux运行和独立故障诊断；旧Windows/Pg可用不等于新路径；新库/凭据避免混写 | Linux路径/资源/连接和冷切未验；旧5433及SQLite只读取证，不能重置旧费用/unknown |
| 本人选择Search/GitHub/Fetch优先、direct API及DeepSeek单Search/Fetch | 限制供应商与连接复杂度，可替换适配；无自动双供应商fallback | Provider内部Fetch连接不可观察；未知字段由应用strict校验，Browser需连接层资格 |
| 本人选择S1工件同Pg | 响应与Call完成同事务、单库快照可含证据 | 存储/WAL/恢复代价；业务1GiB与物理资源另算；大二进制必要时才重评 |
| 本人选择结构关系＋关键词、受限自动记忆 | 小规模可解释取回，避免向量/embedding/reranker依赖；来源线索及长期技术偏好自动可见建议 | 偏好语义保守漏收、sourcehint未知别名、反证未识别风险；不积累程序策略或敏感画像 |
| 本人决定repair=0、Tokenizer正式准入、thinking disabled；整包批准summary=0 | 防隐含调用/价格与重试绕行，完整请求可审计 | Tokenizer模板/模型/版本资格与线上usage不等同；首次诊断有限另授 |
| unknown策略由本人委托AI、AI明确宣布全项目停新出站 | 不用plan/query/Work/Turn绕过；在途保留身份/预留，人工对账后另批恢复 | 无法撤回已claim请求；迟到结算不自动开闸 |
| 本人选择supervisor连续许可及首工即最小监督 | 同连续Sup/Pg下API可重启；失连续账号/研究/记忆隔离 | 增加IPC/进程和故障路径；DB的OPEN或UUID不自证最新；无证明不恢复paid |
| 本人选择开发本机恢复、pilot前独立介质；借优先、纸钥 | 小规模开发先练恢复，真实运行前补抗单盘故障介质 | 介质/纸卡/私钥及真实恢复未建立；临时可信主机解密不承诺无OS残留 |

本次批准的是具体设计和配置参数，不倒称初始候选数字曾获逐项本人决定。详细RT/MEM/RETR/TRACE/B5/BK/FIRST约束以[当前契约](../../contracts/CURRENT_CONTRACTS.md)为单一正文，任务/AC/资源/费用推导以计划、功能规格和协议承接。

## 调用链与五个方向

原始Draft→认证API/Session/Case→澄清提议→用户接受revision/Task原子提交→Worker/LangGraph路线/发现/取证→主张/关系/保护上下文→结构化报告→人工核源。所有物理调用通过Gateway和最终发送claim，应用Pg持久业务权威，checkpoint仅引用。Memory不能成为条件或grant；Tracing关联请求、来源、选择与报告，不采集隐藏思维链或自动上传外部平台。

Runtime任务02/03b，Tools任务03/05，Context任务03a/04，Memory任务04，Evaluation/Tracing/优化任务06/07/08。MCP保持研究，不要求本期真实集成。首业务01是认证草稿＋最小supervisor；备份资格08a前置首pilot，08b只是最终恢复/交付，不形成环。

## 研究、审查与待取实际证据

固定研究版本：LangGraph `3cd57c038ad827d05f80c6488adea9994156c58c`（声明LangGraph1.2.16/checkpoint-postgres3.2.0，不证明本地已安装/兼容）；GPT Researcher `3582a6841fe7dc801e2a34e34ee408641aea9bce`；smolagents `96f33faaf028479119ec8d34507b47694cf14e34`；DeepSeek recipe `935817c66f5d6e64838f419692545f06787e485f`。来源/源码/测试、失败边界、采用理由和未运行项见[机制研究](../../research/HIGH_STAR_AGENT_MECHANISMS_2026-10-22.md)及连续记录。

既有11文件实际审查DONE_WITH_CONCERNS；Runtime三竞争发现及其聚焦修订、检索/Tracing/评测/优化、首工接口、B5.2恢复P1、备份P1/P2和Memory资源联动分别完成限定设计复审。DONE仅限其对象，不扩大为完整系统通过。先前Context/Memory原始审查材料未重新取得，本次补审不能冒充原材料恢复；新配置全文和六题实际材料仍须非作者审查并绑定指纹。

环境/资金/工具资格待真实证据：安全WSL启动与新库权限阻首工；账/unknown/余额/grant、Tokenizer/Gateway、独立介质/纸钥恢复阻pilot；Browser未资格为0。M1仍要求真实症状纠正、正式全尝试、本人价值与实践；Go/发布各自另批。P-01假48/48和r11/r12失败按原版本保存，不能因重写配置清除No-Go。
