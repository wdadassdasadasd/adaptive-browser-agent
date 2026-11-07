# ENV-M1-01 / 1.1 本机入口

本目录是已选受控离线引导方案的本机操作实现。当前授权、资格、审查状态与未解决项只见 [唯一任务记录](../../docs/features/DECISION-001/tasks.md) 的 EOF `dev-current`；没有完整资格和实施复审时不得执行真实窗口或宣布交付。本目录不启动1.2/1.3，不安装数据库。

当前真实PreWindow已发现旧原件最后写入时间与不可变sealed不一致，Phase1、普通协调器、提权协调器均在任何副作用前硬停于 `ORIGINAL_BINDING_DRIFT`。同FileId/大小及未变副本不能替代原件内容/连续性资格；不能忽略field5、改sealed、复位原时间或换run ID。下面是历史已审候选顺序，当前不得执行真实窗口；状态和原始证据见唯一记录。现有合法新导入仍按负责人确认沿用，不因此重导或扩大主机ACL硬化。

配置探针设计已由负责人明确批准。实现新增`ConfigProbe.psm1`/`ConfigProbeNative.cs`及独立小文件夹具；实际C资格与窗口集成须按唯一记录核验。Real机制不自动执行：先保留原对象并持句柄，使用1GB/1CPU/swap0合成配置触发三个公开无效canary；只把三条准确字段覆盖warning加新客体正控制作为该负例成功，失败或未知不得把无效canary打不开判为策略成功。新创建metadata-only20字节合成文件仅用于attach/import拒绝，不使用旧盘。

当窗口日志出现`awaiting_ordinary_token_negatives`时，实施owner须在普通日常token（不是管理员）运行`Test-StandardPolicyNegative.ps1`；该入口要求物理离线，30秒/命令，必须得到确切策略/访问拒绝且注册集合不变。提升窗口最多等90秒，缺结果立即收拢。它不会在其它时点自动启服务。

如果宿主在原配置保留期间中断，保持WSL服务Stopped/Disabled，不恢复网络取包；管理员仅可用`Restore-ConfigProbe.ps1`按耐久intent及实际同对象/hash/SDDL恢复。未知或半写canary保持partial，不覆盖、不删原件、不修原时间或ACL；精确异常恢复需另核现场。

旧原盘、归档与C06/C07现场保留；禁止重新执行已完成的Protect、重导或删除现有 `stage1-bootstrap`。`Diagnose-Import.ps1`、`Diagnose-Guest.ps1`、`Run-ElevatedBatch.ps1` 已在入口处拒绝运行，原件与历史回执留本地审计。

## 不需真实窗口的检查

仓库根，Windows PowerShell 5.1：

```powershell
powershell.exe -NoProfile -NonInteractive -ExecutionPolicy Bypass -File scripts/environment/Test-BoundedNative.ps1
.\.venv\Scripts\python.exe -m pytest -q backend/tests/unit/test_stage1_fixed_debs.py --basetemp <尚不存在的仓库内测试目录>
```

前者仅测试本地Python子进程的参数、输出、超时、stderr、UTF-16及4MiB解码边界；后者不联网、不启动WSL。两者不能替代真实资格。

## 真实窗口顺序（资格与独审关闭后）

1. 本人物理断网，确认所有物理网卡不是Up；本人处理UAC。在管理员Windows PowerShell中，从仓库根执行：

   ```powershell
   powershell.exe -NoProfile -ExecutionPolicy Bypass -File scripts/environment/Run-BootstrapPhase1.ps1
   ```

   入口先核13策略、旧默认登记、服务、五对象保管与输入包；只恢复准确GUID和BasePath，绝不重新导入。客体只进行配置/网络检查、三份认证索引改为APT要求的文件名、六固定版本模拟及只打印URI。索引改名在dpkg/lists前绑定之前完成；模拟和URI阶段前后必须一致。模拟与URI打印分开，因为APT模拟分支先返回。URI阶段使用 `--print-uris --download-only`，禁锁及磁盘cache写入，不执行包安装；准确2.8.3实测仍是本片必需证据。

   预期最后出现 `PHASE1_RESULT=OK` 和 `WINDOW_PHASE=vm_stopped_awaiting_network_restore`，两服务恢复Stopped/Disabled。出现任何失败或 `failed_cleanup_unconfirmed` 时停止后续动作，保留日志；不能把非零退出直接当访问拒绝。

2. 只有成功停止VM并复核围栏后，本人恢复网络，日常非管理员执行：

   ```powershell
   .\.venv\Scripts\python.exe scripts/environment/fetch_fixed_debs.py .tmp/stage-1-1-resume-20261107/bootstrap/window-01
   ```

   替代旧 `.tmp/.../bootstrap/fetch_fixed_debs.py`。只接受非空、完整的固定snapshot池清单，先整体验证再GET；禁代理和重定向，逐项绑定已签InRelease→Packages→Size/SHA256。64MiB/项、400项、总1,500,000,000 bytes；每包独立进程120秒墙钟期限，超时/取消后terminate最多5秒、必要时kill再最多5秒，未收拢为不确定失败。首次失败立即非零停止，已有目录/下载不覆盖。成功为 `FETCH_DONE verified=N` 及 `debs/fetch-summary.json` 的 `complete=true`。重试需先核失败现场，不换目录重置机会。

3. 本人再次断网，管理员执行：

   ```powershell
   powershell.exe -NoProfile -ExecutionPolicy Bypass -File scripts/environment/Run-BootstrapPhase2.ps1
   ```

   预期 `PHASE2_RESULT=OK`、`WINDOW_PHASE=window_closed`、两服务Stopped/Disabled且无WSL客体进程。该步骤不调用可能隐式启动服务的WSL元命令。

4. 本人重启宿主，管理员执行并保留完整输出：

   ```powershell
   powershell.exe -NoProfile -ExecutionPolicy Bypass -File scripts/environment/Verify-PostRestart.ps1
   ```

   预期 `POST_RESTART_VERIFY_OK` 及JSON；最后启动时间必须晚于两阶段最新成功日志。`-PreWindow` 只是同组静态检查，不等于重启资格，输出为 `PRE_WINDOW_VERIFY_OK`。

## 保全与停止

Phase1原生调用有120秒期限，terminate为30秒，传输12MiB包络容纳4MiB解码内容经base64/UTF-16的最大合法输出；超时/超限为失败。失败后核实际服务状态并输出收拢不确定项；没有成功收拢证据时不恢复网络取包。所有操作日志保存在 `.tmp/stage-1-1-resume-20261107/bootstrap/window-01/`。

本片回退仅停止新客体并保持两服务Disabled，保留现有发行版、双盘、ACL、回执和UNKNOWN。不得自动恢复旧运行、放宽保管ACL、删除磁盘/现场或撤销机器策略。代码回退按已审准确差异操作，保留无关工作；不reset/clean。
