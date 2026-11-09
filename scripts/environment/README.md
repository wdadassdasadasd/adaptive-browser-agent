# ENV-M1-01 环境工具

阶段一采用已批准的旧 Ubuntu 退役与独立环境重建。[重建操作卡](../../docs/tasks/STAGE_1_REBUILD_2026-11-08.md)记录准确对象、实际执行与证据。当前资格和原始授权见[唯一任务记录](../../docs/features/DECISION-001/tasks.md)末尾索引。

`Invoke-StageOneRebuild.ps1` 和 `Invoke-RebuildOfflineWindow.ps1` 是该次实际资格的入口，绑定指定宿主、候选和一次性回执。环境操作需按具体现场授权。日常开发应先查计划与现行门禁。

## 历史入口

`Run-BootstrapPhase1.ps1`、`Run-BootstrapPhase2.ps1`、`Verify-PostRestart.ps1` 以及旧保管、探针和固定窗口命令属于已退役的原路线。仅供证据复核，禁止在现有环境执行。旧隔离验证失败及磁盘增长事实见唯一任务记录。

## 离线合成检查

```powershell
.\.venv\Scripts\python.exe -m pytest -q backend/tests/unit/test_stage1_fixed_debs.py backend/tests/unit/test_rebuild_download.py backend/tests/unit/test_rebuild_transport.py backend/tests/unit/test_rebuild_mount_boundary.py --basetemp .tmp/environment-tests-new
```

使用尚不存在的工作区内临时目录。Windows 输运测试使用相应 PowerShell 版本，挂载解析夹具使用 Bash。合成检查与实际环境资格分别记录。
