# ENV-M1-01 / 1.1 B方向只读完整性资格重建·准确操作卡（2026-11-07）

权威链：`entry/binding-drift-decision.md`（0fcf7a23624c7e127aa21b7fbae00d5613fdf0d1be797d073200bcf6ec993167，独立设计审查原文 `binding-drift-design-review-original.md`）→ 本人于2026-11-07会话中明确选择"B：批准B方向，立即开始本地实现"。本卡只落实B的限定实现；**真实读取仍未发生、仍未获批**。

## 资格现状（截至本卡）

- 已实现：`scripts/environment/IntegrityReadNative.cs`（原语）、`IntegrityRead.psm1`（围栏/回执）、`Test-IntegrityRead.ps1`（合成套件）、`Invoke-IntegrityRead.ps1`（双文件一次批量入口）、`Compare-IntegrityReceipts.ps1`（三布尔比较）。
- 合成资格 run06（2026-11-07，普通token）：T01–T04、T07–T10 共11项PASS；T05/T06（SeBackupPrivilege生命周期+受保护文件旁路+零字节）SKIP——当前会话非提升token，**未运行=未评估**。
- 本实现未经真实对象执行；未取得任何真实资格；不解除1.1 partial，不进1.2/1.3。

## 真实读前置门禁（全部满足才可执行，缺一即停）

| # | 门禁 | 状态 |
| --- | --- | --- |
| G1 | `Test-IntegrityRead.ps1` 在实际提升日常token下全项PASS（含T05/T06），新run id | 待运行 |
| G2 | 本实现独立审查完成，无未闭合P0–P2 | 待审 |
| G3 | 本人新的一次性真实读授权：marker文件含`GRANT_REAL_INTEGRITY_READ`及决策稿sha256 `0fcf7a23…`；一次有效，失败不补 | 待本人授予 |
| G4 | 机器围栏`Assert-IntegrityFence`通过：WslService/vmcompute Stopped+Disabled、无vmmemWSL/wslhost、卷last-access更新Disabled | 每次执行时核 |
| G5 | 绑定钉定：对两对象先跑`Get-IntegrityIdentity`（仅metadata、无特权、无数据读，属已核可范围），与保管回执/sealed记录核对后钉定`-Expected*FileIndex/-Expected*VolumeSerial/-ExpectedSizeEach 4867489792` | 执行时核 |
| G6 | 历史私有回执路径/权威/保管核实（不得伪造占位命令）；仅本地程序读取，摘要不进日志/模型/远端 | 执行时核 |

## 执行步骤（真实路径一律取自保管记录，本卡不写入任何真实路径占位）

0. 提升token下先以两个合成文件走一遍 `-Mode Synthetic` 批量入口（新run、新回执根、-ExpectedSizeEach 取合成实际大小），`INTEGRITY_BATCH_RESULT=OK` 后才允许Real模式。普通token下该入口已演练：正确停在 `integrity_privilege_not_held` 并输出 `STOP_LINE_NO_SECOND_REAL_READ`（exit 2），无任何读取。

1. 提升daily token下运行合成套件（G1）。
2. 核围栏与绑定（G4/G5）：`Get-IntegrityIdentity -Path <原件路径>`、`-Path <副本路径>`，输出与保管记录逐字段核对。
3. 批量读（一次，顺序，共两文件，共享绝对5分钟期限，1MiB缓冲）：
   `powershell.exe -NoProfile -ExecutionPolicy Bypass -File scripts\environment\Invoke-IntegrityRead.ps1 -Mode Real -OriginalPath <原件> -CopyPath <副本> -ReceiptDir <新独占回执根> -OriginalFileIndex <…> -OriginalVolumeSerial <…> -CopyFileIndex <…> -CopyVolumeSerial <…> -BatchDeadlineMs 300000 -AuthorizationReceipt <授权marker>`
4. 比较（仅输出布尔，不输出摘要）：
   `powershell.exe -NoProfile -ExecutionPolicy Bypass -File scripts\environment\Compare-IntegrityReceipts.ps1 -OriginalReceipt <原件回执> -CopyReceipt <副本回执> -HistoricalOriginalReceipt <历史私有回执>`

## 结果语义（沿用决策稿§5，不放宽）

- 三布尔：原件对历史回执、副本对历史回执、原件对副本。全等仅证明**新读取时刻**的内容完整性及读取前后同对象绑定；不证明谁写mtime；不追认旧seal覆盖重启区间；来源/费用/UNKNOWN不变。
- 任一不等/证据缺/共享冲突/超时/特权无法恢复 → 停线，保留部分证据，**无第二次真实读**；立即向本人报告。
- 新资格只产生追加回执；旧sealed、旧失败、mtime漂移事实与`binding-drift-readonly-01.json`永不覆盖或"修复"。原件SDDL/文件名/时间完全不动（卷last-access更新Disabled为围栏项，防止读行为改metadata）。

## 后续（真实读之后，另批）

完整实施独审→（如布尔全真）按另已审配置方案继续有限新Base材料引导→后置重启核验→完整AC→准确Git/CI。研究准入、旧运行、1.2/1.3、合并/发布门禁均不变。原十分钟目标不构成任何授权依据。
