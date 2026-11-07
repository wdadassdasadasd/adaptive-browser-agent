# ENV-M1-01 / 1.1 B方向只读完整性资格重建·准确操作卡（2026-11-07）

权威链：`entry/binding-drift-decision.md`（0fcf7a23624c7e127aa21b7fbae00d5613fdf0d1be797d073200bcf6ec993167，独立设计审查原文 `binding-drift-design-review-original.md`）→ 本人于2026-11-07会话中明确选择"B：批准B方向，立即开始本地实现"。本卡只落实B的限定实现；**真实读取仍未发生、仍未获批**。

## 资格现状（截至本卡）

- 已实现：`scripts/environment/IntegrityReadNative.cs`（原语）、`IntegrityRead.psm1`（围栏/回执）、`Test-IntegrityRead.ps1`（合成套件）、`Invoke-IntegrityRead.ps1`（双文件一次批量入口）、`Compare-IntegrityReceipts.ps1`（三布尔比较）。
- 合成资格 run06（2026-11-07，普通token）：T01–T04、T07–T10 共11项PASS；T05/T06（SeBackupPrivilege生命周期+受保护文件旁路+零字节）SKIP——当前会话非提升token，**未运行=未评估**。
- 本实现未经真实对象执行；未取得任何真实资格；不解除1.1 partial，不进1.2/1.3。

## 真实读前置门禁（全部满足才可执行，缺一即停）

| # | 门禁 | 状态 |
| --- | --- | --- |
| G1 | `Test-IntegrityRead.ps1` 在实际提升日常token下全项PASS（含T05/T06），新run id | **已完成** elev02（2026-11-07，review-17修复后代码）：14/14 PASS含T11，`INTEGRITY_SYNTHETIC_RESULT=OK`；合成批量`INTEGRITY_BATCH_RESULT=OK`；回执特权生命周期全真（`.tmp\integrity-elevated-20261107\g1-elev02.log`、回执、g1-done.marker） |
| G2 | 本实现独立审查完成，无未闭合P0–P2 | **已完成** review-17（`.tmp\stage-1-1-resume-20261107\review-17\review-original.md`，DONE_WITH_CONCERNS，0×P0/P1、4×P2）：N-1/M-1/I-1/I-2全部代码修复并复验（处置见review-17/disposition.md），P3同步修N-3/I-4/T-1/T-3/C-1；复验run10（非提升12PASS/2SKIP）+elev02（14/14） |
| G3 | 本人新的一次性真实读授权：marker文件含`GRANT_REAL_INTEGRITY_READ`及决策稿sha256 `0fcf7a23…`；一次有效，失败不补 | **已消耗（2026-11-07 real-read-01）**。本人会话内四项授权（执行/临时禁用last-access/批准G6验收替代/300000ms期限）录于`entry\real-read-authorization-20261107.txt`；窗口执行完成：双文件各4,867,489,792字节完整读入（3993/4183ms），回执结构全真（ok/绑定前后一致/特权生命周期/无正文），last-access设3读后恢复2。**比较结果`ORIGINAL_MATCHES_COPY=False`→§B.5停线触发；授权已用尽，无第二真实读** |
| G4 | 机器围栏`Assert-IntegrityFence`通过：WslService/vmcompute Stopped+Disabled、无vmmemWSL/wslhost、卷last-access更新Disabled | 每次执行时核。**本机现状（2026-11-07实测）：fsutil `DisableLastAccess = 2`（托管的系统，上次访问时间更新已启用）→ 围栏将正确拒绝真实读（run10/elev02 T11实证闭锁）。真实读前须本人在受控窗口明确处理：改为可证禁用，或书面接受LastAccessTime变化及其USN风险（BASic_INFO_CHANGE可致field6再次漂移）** |
| G5 | 绑定钉定：对两对象先跑`Get-IntegrityIdentity`（仅metadata、无特权、无数据读，属已核可范围），与保管回执/sealed记录核对后钉定`-Expected*FileIndex/-Expected*VolumeSerial/-ExpectedSizeEach 4867489792` | 执行时核 |
| G6 | 历史私有回执路径/权威/保管核实（不得伪造占位命令）；仅本地程序读取，摘要不进日志/模型/远端 | **已预核（2026-11-07，形状级扫描，未输出任何值）**：保管回执根`C:\ProgramData\ARA-Stage1-Archive-20261106\real-custody-20261107`仅含intent.json/sealed.json；original_binding/copy_binding仅metadata绑定（0个64hex）；`content_reads`=none、`first_open_dumps`=[]；全库唯一内容哈希属`wslconfig_sha256`。**结论：原/副本的历史内容基线不存在——三布尔仅"原件对副本"可计算，另两项结构性NOT_EVALUATED；决策稿B§4"原已获准私有回执"前提与实际保管证据不符** |

## 执行步骤（真实路径一律取自保管记录，本卡不写入任何真实路径占位）

0. 提升token下先以两个合成文件走一遍 `-Mode Synthetic` 批量入口（新run、新回执根、-ExpectedSizeEach 取合成实际大小），`INTEGRITY_BATCH_RESULT=OK` 后才允许Real模式。普通token下该入口已演练：正确停在 `integrity_privilege_not_held` 并输出 `STOP_LINE_NO_SECOND_REAL_READ`（exit 2），无任何读取。

1. 提升daily token下运行合成套件（G1）。
2. 核围栏与绑定（G4/G5）：`Get-IntegrityIdentity -Path <原件路径>`、`-Path <副本路径>`，输出与保管记录逐字段核对。
3. 批量读（一次，顺序，共两文件，共享绝对5分钟期限，1MiB缓冲）：
   `powershell.exe -NoProfile -ExecutionPolicy Bypass -File scripts\environment\Invoke-IntegrityRead.ps1 -Mode Real -OriginalPath <原件> -CopyPath <副本> -ReceiptDir <新独占回执根> -OriginalFileIndex <…> -OriginalVolumeSerial <…> -CopyFileIndex <…> -CopyVolumeSerial <…> -BatchDeadlineMs 300000 -AuthorizationReceipt <授权marker>`
4. 比较（仅输出布尔，不输出摘要）：
   `powershell.exe -NoProfile -ExecutionPolicy Bypass -File scripts\environment\Compare-IntegrityReceipts.ps1 -OriginalReceipt <原件回执> -CopyReceipt <副本回执> -HistoricalOriginalReceipt <历史私有回执>`

## 结果语义（沿用决策稿§5，不放宽；含G6修订）

- **（G6修订，本人授予G3前必读）**历史内容基线不存在：即使双文件一次读全部成功且哈希互等，也只能证明**读取时刻原件≡副本**及读取前后同对象绑定；**不能**证明内容自seal以来未变（"谁写mtime/内容是否曾变"仍无答案）。决策稿"缺证保持A"与"任一证据缺→停线"均适用。是否仍值得消耗唯一一次真实读以取得"原件≡副本"互证，由本人明确决定。
- 三布尔：原件对历史回执、副本对历史回执（两项NOT_EVALUATED，无基线）、原件对副本（可计算）。全等仅证明新读取时刻的内容完整性及读取前后同对象绑定；不证明谁写mtime；不追认旧seal覆盖重启区间；来源/费用/UNKNOWN不变。
- 任一不等/证据缺/共享冲突/超时/特权无法恢复 → 停线，保留部分证据，**无第二次真实读**；立即向本人报告。
- 新资格只产生追加回执；旧sealed、旧失败、mtime漂移事实与`binding-drift-readonly-01.json`永不覆盖或"修复"。原件SDDL/文件名/时间完全不动（last-access更新须可证禁用为围栏项，防止读行为改metadata/USN）。

## 真实读结果（2026-11-07 real-integrity-read-01，负性）

- 双文件一次读全部完成：原件/副本各4,867,489,792字节，3993/4183ms，同卷不同FileId（确为两个对象），读取前后同句柄身份一致，特权生命周期present/disabled→enabled→disabled/restore_verified全真，无正文存储（回执`.tmp\stage-1-1-resume-20261107\real-integrity-read-01\receipts\`，日志`.tmp\integrity-elevated-20261107\real-read-01.log`）。
- **`ORIGINAL_MATCHES_COPY=False`：原件与副本当前内容不相等。**按已批准的G6验收替代语义（唯一可计算的互证）判定为不成立→决策稿§B.5"任一不等→停线"触发。
- 停线已遵守：无第二真实读；本授权用尽；原对象未被本读改动（原件field5读后仍为134385080318390256=今晨漂移值；副本field5=134384372834681851；读期间last-access禁用无USN新增；策略已恢复=2）。
- 含义：保管对（原件,副本）在内容层面不一致；结合无历史基线，无法归因哪侧变化、何时变化。B方向资格重建**负性关闭**；现行隔离partial（A）为存续状态；1.1连续性硬停继续有效。
- 任何进一步内容调查（副本出处核查、新基线建立、或对原件的任何新读）均为**新决定稿/R2审查/本人新授权**事项，不在本卡范围内。

## 后续

完整实施独审/真实链/准确Git/CI等门禁均维持不变；B负性关闭后，1.1在其现有权威下以隔离partial存续，进入1.2/1.3、恢复研究准入、解除硬停均需新的决定稿与本人授权。原十分钟目标不构成任何授权依据。
