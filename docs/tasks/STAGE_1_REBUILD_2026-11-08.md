# ENV-M1-01：阶段一退役重建准确操作包

2026-11-08。唯一动态记录仍为 `docs/features/DECISION-001/tasks.md`。
原始授权为本聊天用户完整重贴并要求实施《第一阶段收尾：退役旧 Ubuntu，重建干净环境》；同时保留先前“直接销毁旧环境”问题、选项与回答。此次明确覆盖1.1–1.3，替代先前1.1交付后停止；不授权合并、阶段二、研究/模型调用或采购。

## 对象与不可逆差额

- 仅销毁当前SID `S-1-5-21-2765399256-1806415232-1753294129-1001` 下 `Ubuntu`，GUID `{5bd0012b-1a62-445a-ad9e-da37f21ba704}`，BasePath `C:\Users\FFFFFF\AppData\Local\Packages\CanonicalGroupLimited.Ubuntu_79rhkp1fndgsc\LocalState`。执行前再次核名称/GUID/版本/真实路径及无reparse祖先；不新增旧盘内容读取/备份。`wsl --unregister Ubuntu`永久销毁其关联文件系统；无回滚。
- 保留stage1-bootstrap及其GUID/路径、C:\ProgramData既有保管对象、历史回执/失败、仓库和Windows PostgreSQL。不能递归删除父目录、重装WSL引擎、停止归属不明的进程或恢复旧授权。
- 新实例 `ara-m1-stage1` / `D:\WSL-Stage1\ara-m1-stage1`，只从已签验派生tar SHA256 `6513c1e9004a25263cf8b8a9f94a81ebc7b780627050a21681c953fd844f52e4`导入。新实例目录必须原不存在。
- 旧“从未启动/原盘未改变”保持FAIL；替换验收为授权退役销毁、新环境独立来源/身份/无旧授权。旧队列/在途/费用UNKNOWN不清零，研究closed。

## 准确操作与写集

固定入口 `scripts/environment/Invoke-StageOneRebuild.ps1`，显式Phase；仅1.3/新入口使用已装PS7.6.9。证据新增于 `.tmp/stage1-rebuild-20261108`，每phase一次性回执，不覆盖失败。

1. Audit：只读注册/服务/机器策略/相关计划任务、服务命令、Run/Startup/WMI和已加载其他用户注册；命令正文不输出秘密，只留匹配主体、范围/缺口。核签验tar、来源回执、磁盘/内存及脚本身份。
2. Retire：本人断网及UAC；核旧注册精确、服务Stopped/Disabled、无guest；临时启用WslService/vmcompute，只执行unregister旧Ubuntu，不启动旧guest；核旧GUID/路径无注册且ext4.vhdx不存在。若删除被原保护ACL拒绝，只在明确失败证据后另形成该单一旧对象的修复差额，不递归放权。导入新实例、设置新默认，不恢复旧GUID。失败保留半态，关闭服务。
3. Bootstrap/Solve：临时将 `C:\Users\FFFFFF\.wslconfig`替换为明确offline配置（1GB/1CPU/swap0/无GUI/无localhost转发），原bytes/mtime存phase私有证据并在收拢恢复；机器13项策略不改。新guest禁systemd/interop/automount，核来源/无旧秘密任务、无网卡路由、无用户磁盘/可写hostshare（仅允许固定引擎只读drivers挂载）；规范化已签验APT索引名称，冻结六pin解算/URI及前后dpkg/索引绑定，停止新guest并禁用服务。
4. Fetch：宿主联网且WSL服务禁用；沿用已签验snapshot及现有fetch机制、整单校验、单物理请求无retry/400项/64MiB每项/1.5GB总量；只写本包debs和回执。再断网。
5. Install/Qualify：临时同一offline配置/服务；完整逐deb size/hash与guest hash；有界二进制stdin直接交接收命令，不使用占stdin的脚本管道。guest写 `/tmp/ara-rebuild`、dpkg安装状态/已签验包路径、policy-rc.d/createcluster守卫、Pg独立data/config/log、`/var/lib/ara-m1/credentials`(0700/0600)、限定Linux资格用户、ara-stage1 cgroup及其中pg子组。所有Pg启动与恢复在目标cgroup内；不访问旧数据库。Pg16.15/55432/ara_m1+ara_m1_test，admin peer、运行角色SCRAM、migration NOLOGIN；无TCP。密码在guest生成，绝不进入prompt/argv/宿主回执。资格后停新cluster，保留数据和私有凭据；清理临时安装守卫，关闭guest/服务并恢复宿主配置。
6. Verify/PostRestart：核本包回执完整哈希、旧对象缺席、新身份/默认正确、无guest/服务禁用、配置恢复；本人重启后用不同boot时间确认同样结果。外部副本保留原隔离；不声称全机器/恶意管理员防护。

每步失败收拢只针对新实例；不能unregister新实例或删其数据作为回滚。本人本轮追加原话“帮我断网，执行，然后恢复网络，不然我断网你就无法正常回答了”，因此允许准确控制原本Up的物理网卡：按名称+InterfaceGuid冻结，先启独立600秒恢复watchdog并核ready，再禁这些网卡；正常/失败finally按原身份启用并核link Up。watchdog只在无正恢复回执且期限到达时先围栏WSL服务，再恢复同批网卡；不改IP/DNS/防火墙/VPN/其他网卡。两次同链失败先整体分析，不同质重试。

网络收拢r9：600秒为整个离线窗口的硬截止，合法慢安装也可被取消，保留partial而非无限等待。看门狗超时先落cancel，按PID+创建时间绑定并停止主协调器及其已绑定直系wsl子进程、确认退出，再通过与正常finally共享的本地mutex取得唯一收尾权；确认双服务Stopped/Disabled且无guest后才可启原网卡。正常finally同样先围栏，不能把围栏失败当安全恢复；围栏不能确认时保留明确失败，恢复不能冒充成功。r8首次实际网络恢复超时且备用守护未落终态，保留失败。r9改用当前提升用户的WMI隐藏进程脱离tool作业，已在同准确UAC/launcher下证明父正常退出/被杀后同SID/admin存活并落终态；记录PID/创建时刻、transcript及错误/正常/超时结果。服务/网络时序mock通过，下一实际窗口仍需实际回执。

## 验收

1.1：退役、新来源/注册绑定、无旧启动目标及重启持续性。1.2：相关旧入口不可写，保留失败/UNKNOWN/旧账。1.3：传输0/1/4/全字节/最大/超限/早退/阻塞/超时；实际deb一致；三角色15条原探针、真实DDL/TEMP/跨库/schema失败与同socket认证正负；独立连接；Pg cgroup所有PID、memory.current/peak/events/cpu.max，真实正常写/崩溃恢复/停机及数据保留。WSL1GB是VM总帽，不声称Pg可独占1GB或整套业务容量通过。

设计审查/root/environment_design_review DONE_WITH_CONCERNS，原报告保留于本包entry；发现必须在实现/实测闭合。完整可读候选与检查冻结后新上下文实施独审。技术检查/独审/准确Git与必要CI/人验分别登记；不以时间目标代PASS。

已退役对象禁止再次执行Retire。r11采用r8 Audit05/Retire的准确候选SHA、两成功回执SHA及全部冻结可读源码/证据文件SHA，核新GUID/VHD身份；原bootstrap失败不覆盖。新ResumeBootstrap03入口只运行bootstrap-03，随后debs/安装均绑定当前候选；原失败和首次网络恢复失败永久保留。

21:44修复差额：WSL2 mini_init在VM层注册Windows PE解释器，proc条目stat.size=0不能代表空正文。每次新guest脚本和二进制接收前仅向具体WSLInterop条目写0，读取首行disabled；不清空其他binfmt、不改宿主机器策略/既有发行版配置。离线窗口开始无guest、只启动ara-m1-stage1；保留bootstrap不启动、不写盘。WSL服务停止后VM状态终止；每次执行均重新核禁用。实际PE须126和Exec format error且前后状态disabled；accept4超时不合格。原两个失败日志不覆盖，新probe03/log03独立保存。Pg安装前后及资格末读状态防重新启用。
依据：[Microsoft WSL interop](https://github.com/microsoft/WSL/blob/master/doc/docs/technical-documentation/interop.md)、[Linux6.6 binfmt_misc](https://docs.kernel.org/6.6/admin-guide/binfmt-misc.html)。该实现落实原已批禁interop边界；不声称WSL能防御宿主或其他恶意管理员。
脚本文本CRLF规范为LF、裸CR拒绝；整个guest围栏及payload的stderr统一到guest stdout，宿主UTF16诊断单独解码；二进制输入不做文本变换。恢复唯一写集和600秒上限不变。当前入口：Invoke-RebuildOfflineWindow.ps1 -WorkSet ResumeBootstrap03；成功后fetch_rebuild_debs.py；再-WorkSet Install。两次Bootstrap失败的容量/支持/partial/诊断/收拢分析见唯一记录21:41节，修复独审通过后才进行有新增价值的一次Bootstrap03。

22:05实际进度：Bootstrap03与正常网络恢复真实通过。首次97包Fetch首项校验失败，失败目录bootstrap03/debs保留；有界诊断首包size/hash与签验索引一致。r13独立复审DONE_WITH_CONCERNS，获取改分块循环及准确actual-size/hash失败诊断，仍原一次请求/120s父期限。首包复用诊断已验证字节，输出fetch-02/debs；准确采用r12成功Bootstrap03回执/候选及全部原件。当前fetch_rebuild_debs.py只创建fetch-02一次，Install指向该目录；不重新运行Bootstrap/Retire、不覆盖首次失败。

23:17恢复差额：原Install已传97签验包及两资格文件；原窗口缺最终回执，准确状态为partial，最终进程丢失原因UNKNOWN。诊断证明Pre-Depends导致python3/systemd-sysv未安装；非仅configure-pending可修。新入口以原固定PS7路径运行entry/launch-resume-pg.ps1，通过WMI同token创建独立顶层ResumePg协调器及独立guard，父只启动和落PID/start绑定。仅新resumeinstall/network-resumepg写回执，旧install不补成功。
先核原99传输回执SHA796be3...和fetch02完整summarySHA261f601...、全部97唯一包绑定，guest执行前重核99文件size/hash和97deb精确数量；核原install-attempt/新增一次resume-install-attempt/本次守卫。仅用本地97deb执行APT --no-download --no-remove --fix-broken安装，DEBIAN_FRONTEND=noninteractive、stdin=/dev/null，不新下载/不清锁/不force-depends/不删数据；全部版本installed/audit空后原完整Pg权限、cgroup、并发、崩溃及停止资格重跑。失败留数据/证据，第二同链失败须整体分析。恢复准入须r15准确独审通过。
23:22容量修复：r15真实恢复在包操作前99校验命令超过Windows32767chars而停止，实际Base64=33652。网络/服务/配置/guard终态完整成功；未传新resume脚本/未落恢复marker。r16不变包恢复语义，重验改每8条固定批次13批，共100检查全部覆盖，最长含2048余量4912chars，各批set-eu且全部成功才执行包操作；新ResumePg02、resumeinstall-02、network-resumepg02和entry/launch-resume-pg02.ps1，不复用失败目录。独审通过前不执行。
23:29缓存修复准备：r16原99文件重验通过、APT no-download因三个未安装包未命中archives而失败，完整失败与正常网络收拢终态保留。r17继续禁下载/移除，仅对已验签python3-minimal/python3/systemd-sysv各唯一包核Package/version/architecture与准确cache leaf后复制0644+cmp到新guest /var/cache/apt/archives；其余94不复制。新ResumePg03/resumeinstall-03/launch-resume-pg03.ps1；原attempt和前次resume marker必须存在，新03缺席，两个旧guard必须缺席、cluster空，才新建本次guard。99原文件批次hash重验保持在任何包操作前。独审通过前不执行。
23:36启动恢复差额：ResumePg03已实际完成97包版本/installed/audit空，建立16/ara_m1/55432后首次启动因ssl-cert-snakeoil.pem no start line失败；证书坏原因UNKNOWN、无角色provision。新ResumePg04/launch-resume-pg04.ps1保持已建cluster/data/cert，99旧文件先重验，核原03marker/新04缺席、guard缺席/credentials缺席、唯一精确downcluster、97installed/audit空；核HBA四行peer/SCRAM/reject完全相等及postgres实际-C listen_addresses空，然后仅append ssl=off（本环境无TCP、只Unixsocket）后重跑完整cgroup/角色/崩溃/停止。启动日志start-$stage-04独立保留旧失败，三个pgrep拒绝改显式if退出，不依赖set-e的negation。r22候选及准确launcher独审通过前不执行。


2026-11-09实际终态。r24 ResumePg06用Unix socket完成三角色权限与认证、cgroup、并发和真实崩溃恢复，成功停止并恢复网络。Verify及普通重启后的PostRestart通过。重启核验原件 `.tmp/stage1-rebuild-20261108/postrestart/receipt.json`，SHA256 `e989df5751f812866f4353f3679aeaa092eebea10634ea8bfa177b0ec8ddab1c`。证据目录保留各轮失败回执、冻结候选与签验数据；资格运行脚本固定到本机和已执行的准确状态。历史退役和安装入口按回执防止重复执行。阶段末人工验收与CI依唯一记录。
