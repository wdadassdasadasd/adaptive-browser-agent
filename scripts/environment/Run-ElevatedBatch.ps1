# One-shot elevated batch for stage-one 1.1: machine policy, then real custody protection.
# Each script runs in its OWN fresh powershell child process: the 2026-11-07 diag proved the
# CustodyNative Binding succeeds elevated in a fresh process but failed when Protect ran in the
# same process after Apply (residual in-process state, see shape-diag-20261107T052133Z.log).
# Logs everything to .tmp\stage-1-1-resume-20261107\, never rolls back, stops at first failure.
throw 'completed_apply_protect_batch_retired_do_not_reapply_real_custody'
$ErrorActionPreference = 'Stop'
$logRoot = 'D:\adaptive-browser-agent\.tmp\stage-1-1-resume-20261107'
$stamp = [DateTimeOffset]::UtcNow.ToString('yyyyMMddTHHmmssZ') -replace ':', ''
$batchLog = Join-Path $logRoot ("elevated-batch-$stamp.log")
Start-Transcript -Path $batchLog | Out-Null
$exitCode = 1
try {
    if ($PSVersionTable.PSVersion.Major -ne 5) { throw 'host_must_be_powershell_5_1' }
    $psExe = "$env:SystemRoot\System32\WindowsPowerShell\v1.0\powershell.exe"
    foreach ($step in @(@('APPLY', "$PSScriptRoot\Apply-WslMachinePolicy.ps1"),
            @('PROTECT', "$PSScriptRoot\Protect-RealCustody.ps1"))) {
        $name = $step[0]
        $scriptPath = $step[1]
        $outLog = Join-Path $logRoot ("elevated-child-$name-$stamp.log")
        $errLog = Join-Path $logRoot ("elevated-child-$name-$stamp.err.log")
        Write-Output "BATCH_STEP=$name starting_fresh_child_process out=$outLog"
        $child = Start-Process -FilePath $psExe -ArgumentList @('-NoProfile', '-NonInteractive',
            '-ExecutionPolicy', 'Bypass', '-File', $scriptPath) -Wait -PassThru -NoNewWindow `
            -RedirectStandardOutput $outLog -RedirectStandardError $errLog
        Write-Output "BATCH_STEP=$name child_exit=$($child.ExitCode)"
        if ($child.ExitCode -ne 0) { throw "child_step_failed:$name:exit=$($child.ExitCode)" }
        Write-Output "BATCH_STEP=${name}=completed_no_terminating_error"
    }
    $exitCode = 0
    'BATCH_RESULT=OK'
} catch {
    "BATCH_FAILURE=$($_.Exception.Message)"
    "BATCH_RESULT=FAILED"
    $exitCode = 1
} finally {
    Stop-Transcript | Out-Null
}
exit $exitCode
