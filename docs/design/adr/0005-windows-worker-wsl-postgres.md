# ADR-0005：WSL独立API／Worker／Pg与连续运行资格

- 原决定：2026-10-19；当前配置：**FOCUS-BASELINE-20261102**，28文件同步获批；原PREP基线按原字节保留，当前文件独审、业务实现和运行资格分别待证。
- 权威：[SPEC](../../../SPEC.md)、[PLANS](../../../PLANS.md)、[契约](../../contracts/CURRENT_CONTRACTS.md)、[唯一任务记录](../../features/DECISION-001/tasks.md)。本ADR记录取舍，不复制契约参数表。

## 采用T2与独立新cluster

本人选择WSL内独立FastAPI、Worker/LangGraph和PostgreSQL，Windows访问本机UI。Worker故障与API分离，后端、工具隔离和持久数据同Linux环境，便于故障诊断；宿主/WSL仍是共同故障域，非高可用保证。比较过Windows API/Worker＋WSL库及单进程SQLite；它们各有组件/迁移代价，现有假任务可用不构成回退理由。

新目标复用**资格通过的已安装Pg16.15 binary**，独立data/config/凭据/端口55432，业务库ara_m1与隔离ara_m1_test。旧5433 cluster及SQLite只读取证，不因新库选择自动关闭旧数据库服务、重置旧费用/unknown或删除原件。实际Linux绝对路径、二进制/权限/端口和构建同步身份由ENV-M1-01核实后提交准确操作包，当前不伪造可执行命令。新实例与旧服务不能混入同一资源组。

## 应用权威与启动

Pg应用表拥有team/project/member/source用途、条件与ReviewQuestion、SourceSet及LocalCapture、DocumentVersion/head和RequirementsConfirmation、Task执行许可、Attempt/fence、稳定Work、物理Call、grant/费用、工件、证据、报告与事件。checkpoint采用sync目标但仅保存有界已提交引用，应用与checkpoint分schema/角色/连接，不假定跨写入原子。普通启动只验证代码、依赖、schema和部署身份；建库、迁移和checkpointer setup分别授权，运行角色无DDL。

首次启动WSL前核旧systemd/bootcommand/launcher自动服务及出站/原件保护。不能证明安全时停止，先提出离线取证或启动前隔离的具体权限/路径/影响方案；不能先启动再补关旧Worker。冷切按旧准入关闭→队列/在途/unknown核对→停止旧API/Worker→失效旧写凭据和存活连接→确认不能误写→另授权新迁移/版本核对。新程序握手不能替代旧进程隔离；无法证明时保留必要数据库护栏。

## supervisor连续许可与保守恢复

本人比较后选择连续运行许可，并在首个无模型任务建立最小supervisor。它持独立本机IPC和持续Pg监测连接，绑定本次boot、实际Pg进程启动时间及库/schema/部署身份。所有池新连接/重连同步核对；监测断线、Pg重启/还原、supervisor失联使本generation封闭，恢复出的数据库OPEN不能自激活。

同一持续supervisor和同Pg进程下，API/Worker可用新actor UUID重新核对加入；旧generation先阻断实际出口/连接、确认资源组终止，才幂等释放匹配slot。不能确认则保留物理占用、停用能力；Task终态不自动释放仍在途槽。网络关闭不证明远端停止执行或计费。

身份资格同样来自本生命周期明确的CLI新凭据操作；丢失连续性后恢复账号隔离、旧cookie/密码不能换新session复活。新CLI凭据只开放限定草稿读写/历史读取，研究和自动记忆仍关闭。精确单次claim先于seal的操作已经在途，可能随后提交；seal不能保证瞬时撤回。数据库当前enabled/revision/epoch/owner仍是另一收紧边界，不能被supervisor缓存覆盖。2秒是本地执行截止，非COMMIT物理完成保证；不明提交保留unknown，不换操作重做。

没有独立最新性证明时，不恢复付费研究或从恢复消息/报告重生记忆。UUID、hash chain或两个序号相等不证明最新；本期不另造第二业务权威/持久分布式见证。管理员同Pg进程在线回灌/改表必须先seal停写并另授权，连续连接不承诺检测任意superuser篡改。

## 网络、资源与备份

API只绑定可信本机HTTP origin，真实认证、Host/Origin/CSRF与逐对象当前授权保留；Cookie不隔离同host不同端口，恶意本机进程不在保证内。每个有界response/page/SSEframe在根事务核当前账户／session／sup／member／分享／lineage；仅GitHub私有来源或其私有祖先核适用GitHub source proof，纯公开无凭据profile核本地use/share与固定source身份、不要求App签发，cursor不授权。撤权先提交拒未claim交付；已claim最后一个有界响应可能在途。logout／expiry挡旧会话新读，不取消仍有独立执行许可的Task。GET不隐式刷新五分钟私源proof，unknown停外调可使其到期后报告不可读。Browser真实接入暂缓保持0，Search失败不扩权；未来连接方案另授权及资源重评。

父cgroup4GiB/CPU4原候选包含Browser、proxy、bridge、Worker、Pg、API、supervisor和备份管线共4032MiB子预算，64MiB余量；当前Browser0不自动归还或挪用这些候选子预算。实际资格、峰值及磁盘停线须测，不能脱组重试。逻辑业务工件1GiB及当前466.25MiB业务预留峰不包括WAL/索引/checkpoint/备份物理空间；精确Case64MiB分桶见契约，不能以加和证明实际容量。

备份资格目标为age1.3.2标准X25519，公钥在线、纸钥本人离线单独保管；短时在可信本机恢复不承诺OS无残留。独立纸卡绑定密文与manifest hash，单库dump和manifest同snapshot；先验来源/完整解密，再隔离restore，失败目标不开放、旧库零写。开发先做本机有限恢复，首次公开源真实pilot前也必须有独立物理介质及从纸录钥真实恢复；窗口延期的是完整恢复故障覆盖，不豁免最低pilot安全资格。借用优先；购买、工具安装、密钥生成和恢复操作分别授权，详细容量/截止以契约为准。

## 历史证据与验收边界

2026-10-20[环境探针](../../audits/PREDEV_ENV_SETUP_2026-10-20.md)及2026-10-21[P-01假任务48/48](../../tasks/P01_ACCEPTANCE_2026-10-21.md)证明原Windows/Pg部分实现，不证明新cluster、LangGraph、Browser或资金恢复。旧启动器会保活WSL、启Pg并自动迁移，仅作为历史实现阅读。旧2运行8排队和60/120秒指标不作新默认。r12/P-02 No-Go保留。

新环境、身份、资源、秘密、冷切和恢复的实际检查均须对应任务取证。本批仅28文件配置/guard落地与检查，不执行安装、环境/数据库或真实调用；当前实际文件独审和未来业务实现独审分别取得。七至八周优先需求到方案闭环与本人讲解，私源／完整恢复未完仍保留首阶段／M1待证；Memory已另行后置，不再是当前M1前置，也不算已验能力。

## 2026-11-02 FOCUS增量决定

当前M1关闭全部Memory功能入口，包括手动／自动、API／CLI、默认profile／框架Store预加载、旧checkpoint refs、导入／恢复／重建与后台路径；不提取候选、不读写、不检索、不注入，active Memory refs必须为空并与各模型阶段实际请求一致。Trace记disabled/not_applicable，hits／writes为null并附feature_disabled，不以测试零次冒充禁用证据，不要求空Store／seed／Memory快照。Case内条件、证据、文档和审计照常持久化；本人明确选定历史报告走SourceSet准确获许可版本，不解引用Memory refs，继续核当前权限和已知私有祖先。DEC-AC-17／DEC-M1-04保留延期、未实施／未验；完整Context属03a、Token资格属03b，当前M1不依赖04。真实复用需求、独立设计审查及准确范围另批后才可重开，原Memory预留容量保持闲置上界，不挪给其他功能。

DRAFT-BASELINE-20261102按final-01原字节继续有效；以下新增起草范围的部署取舍保留，旧review仍按final-02，不重绑定旧索引。

### 同日起草增量的保留理由

本轮保留API/Worker/Pg/supervisor/checkpoint架构，新增起草及本地材料不引入文件系统桥、协同编辑框架或第二持久化权威。File API仅选定上传，API有界流式计数和用途核权，业务Pg同事务持久化，源码不执行；真实头/缓冲/截止资格仍待业务任务。文档版本及精确需求确认属于应用权威，不进入checkpoint作授权。原认证/私人raw Draft/最小sup首工不扩。窗口优先闭环不豁免真实pilot最低独立恢复；旧92–136h/130–194h非新范围承诺。原review交付按现有final-02原字节有效。
