# ADR-0005：WSL独立API／Worker／Pg与连续运行资格

- 原决定：2026-10-19；当前配置：**PREP-BASELINE-20261029**，方案获批、实现和运行资格分别待证。
- 权威：[SPEC](../../../SPEC.md)、[PLANS](../../../PLANS.md)、[契约](../../contracts/CURRENT_CONTRACTS.md)、[唯一任务记录](../../features/DECISION-001/tasks.md)。本ADR记录取舍，不复制契约参数表。

## 采用T2与独立新cluster

本人选择WSL内独立FastAPI、Worker/LangGraph和PostgreSQL，Windows访问本机UI。Worker故障与API分离，后端、工具隔离和持久数据同Linux环境，便于故障诊断；宿主/WSL仍是共同故障域，非高可用保证。比较过Windows API/Worker＋WSL库及单进程SQLite；它们各有组件/迁移代价，现有假任务可用不构成回退理由。

新目标复用**资格通过的已安装Pg16.15 binary**，独立data/config/凭据/端口55432，业务库ara_m1与隔离ara_m1_test。旧5433 cluster及SQLite只读取证，不因新库选择自动关闭旧数据库服务、重置旧费用/unknown或删除原件。实际Linux绝对路径、二进制/权限/端口和构建同步身份由ENV-M1-01核实后提交准确操作包，当前不伪造可执行命令。新实例与旧服务不能混入同一资源组。

## 应用权威与启动

Pg应用表拥有条件、Task、Attempt/fence、稳定Obligation、物理Call、grant/费用、工件、证据、报告与事件。checkpoint仅保存有界已提交引用，应用与checkpoint分schema/角色/连接，不假定跨写入原子。普通启动只验证代码、依赖、schema和部署身份；建库、迁移和checkpointer setup分别授权，运行角色无DDL。

首次启动WSL前核旧systemd/bootcommand/launcher自动服务及出站/原件保护。不能证明安全时停止，先提出离线取证或启动前隔离的具体权限/路径/影响方案；不能先启动再补关旧Worker。冷切按旧准入关闭→队列/在途/unknown核对→停止旧API/Worker→失效旧写凭据和存活连接→确认不能误写→另授权新迁移/版本核对。新程序握手不能替代旧进程隔离；无法证明时保留必要数据库护栏。

## supervisor连续许可与保守恢复

本人比较后选择连续运行许可，并在首个无模型任务建立最小supervisor。它持独立本机IPC和持续Pg监测连接，绑定本次boot、实际Pg进程启动时间及库/schema/部署身份。所有池新连接/重连同步核对；监测断线、Pg重启/还原、supervisor失联使本generation封闭，恢复出的数据库OPEN不能自激活。

同一持续supervisor和同Pg进程下，API/Worker可用新actor UUID重新核对加入；旧generation先阻断实际出口/连接、确认资源组终止，才幂等释放匹配slot。不能确认则保留物理占用、停用能力；Task终态不自动释放仍在途槽。网络关闭不证明远端停止执行或计费。

身份资格同样来自本生命周期明确的CLI新凭据操作；丢失连续性后恢复账号隔离、旧cookie/密码不能换新session复活。新CLI凭据只开放限定草稿读写/历史读取，研究和自动记忆仍关闭。精确单次claim先于seal的操作已经在途，可能随后提交；seal不能保证瞬时撤回。数据库当前enabled/revision/epoch/owner仍是另一收紧边界，不能被supervisor缓存覆盖。2秒是本地执行截止，非COMMIT物理完成保证；不明提交保留unknown，不换操作重做。

没有独立最新性证明时，不恢复付费研究或从恢复消息/报告重生记忆。UUID、hash chain或两个序号相等不证明最新；本期不另造第二业务权威/持久分布式见证。管理员同Pg进程在线回灌/改表必须先seal停写并另授权，连续连接不承诺检测任意superuser篡改。

## 网络、资源与备份

API只绑定可信本机HTTP origin，仍有真实认证、Host/Origin/CSRF和逐对象授权；Cookie不隔离同host不同端口，恶意本机进程不在隔离保证内。Browser临时无个人登录环境、唯一受控出口与pipe/bridge资格不成立则关闭；Search失败不扩权。接口与对抗测试见当前契约。

父cgroup4GiB/CPU4候选包含Browser、proxy、bridge、Worker、Pg、API、supervisor和备份管线共4032MiB子预算，64MiB余量。实际资格、峰值及磁盘停线须测，不能脱组重试。逻辑业务工件1GiB不包括WAL/索引/checkpoint/备份物理空间。

备份资格目标为age1.3.2标准X25519，公钥在线、纸钥本人离线单独保管；短时在可信本机恢复不承诺OS无残留。独立纸卡绑定密文与manifest hash，单库dump和manifest同snapshot；先验来源/完整解密，再隔离restore，失败目标不开放、旧库零写。开发先做本机有限恢复，真实pilot前必须有独立物理介质及从纸录钥真实恢复。借用优先；购买、工具安装、密钥生成和恢复操作分别授权，详细容量/截止以契约为准。

## 历史证据与验收边界

2026-10-20[环境探针](../../audits/PREDEV_ENV_SETUP_2026-10-20.md)及2026-10-21[P-01假任务48/48](../../tasks/P01_ACCEPTANCE_2026-10-21.md)证明原Windows/Pg部分实现，不证明新cluster、LangGraph、Browser或资金恢复。旧启动器会保活WSL、启Pg并自动迁移，仅作为历史实现阅读。旧2运行8排队和60/120秒指标不作新默认。r12/P-02 No-Go保留。

新环境、身份、资源、秘密、冷切和恢复的实际检查均须对应任务取证。本批仅配置/guard落地与检查，不执行安装、环境/数据库或真实调用；完整实际文件审查和未来实现审查分别完成。
