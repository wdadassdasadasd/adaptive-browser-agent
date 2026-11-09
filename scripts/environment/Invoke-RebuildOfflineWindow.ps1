[CmdletBinding()]
param([Parameter(Mandatory)][ValidateSet('RetireBootstrap','ResumeBootstrap03','Install','ResumePg06')][string]$WorkSet)
$ErrorActionPreference='Stop'
Set-StrictMode -Version Latest
Import-Module (Join-Path $PSScriptRoot 'StageOneRebuild.psm1') -Force
Assert-RebuildRuntime
$null=Assert-RebuildCandidate
Assert-RebuildPolicy
Assert-RebuildFenced
$root=(Get-RebuildSettings).Root
$networkDir=Join-Path $root ('network-'+$WorkSet.ToLowerInvariant())
if(Test-Path -LiteralPath $networkDir){throw 'network_window_already_attempted'}
$null=New-Item -ItemType Directory -Path $networkDir
$adapters=@(Get-NetAdapter -Physical|Where-Object Status -eq 'Up'|ForEach-Object{@{name=$_.Name;guid=[string]$_.InterfaceGuid}})
if($adapters.Count -eq 0){throw 'no_initially_up_physical_adapter; reconnect_before_automatic_window'}
$intent=Join-Path $networkDir 'intent.json'
$networkIntent=@{workset=$WorkSet;created=[DateTimeOffset]::UtcNow.ToString('o');adapters=$adapters;watchdog_seconds=600;coordinator_pid=$PID;coordinator_started=(Get-Process -Id $PID).StartTime.ToUniversalTime().ToString('o')}
Write-RebuildJson $intent $networkIntent
$guard=Join-Path $PSScriptRoot 'Watch-RebuildNetwork.ps1'
$watchdog=Start-RebuildDetachedProcess ([Environment]::ProcessPath) @('-NoProfile','-NonInteractive','-ExecutionPolicy','Bypass','-File',$guard,'-WorkSet',$WorkSet)
Write-RebuildJson (Join-Path $networkDir 'watchdog-process.json') @{pid=$watchdog.Id;started=$watchdog.StartTime.ToUniversalTime().ToString('o')}
$deadline=[datetime]::UtcNow.AddSeconds(15)
while(-not (Test-Path (Join-Path $networkDir 'watchdog-ready.json'))){if($watchdog.HasExited -or [datetime]::UtcNow -gt $deadline){throw 'network_watchdog_not_ready'};Start-Sleep -Milliseconds 200}
$completed=$false
$failure=$null
try {
    foreach($adapter in $adapters){$actual=@(Get-NetAdapter -Physical|Where-Object {([string]$_.InterfaceGuid) -ieq $adapter.guid});if($actual.Count -ne 1 -or $actual[0].Name -cne $adapter.name){throw 'physical_adapter_identity_changed'};$actual[0]|Disable-NetAdapter -Confirm:$false}
    Assert-RebuildOffline
    if($WorkSet -eq 'RetireBootstrap') {
        & (Join-Path $PSScriptRoot 'Invoke-StageOneRebuild.ps1') -Phase Audit
        & (Join-Path $PSScriptRoot 'Invoke-StageOneRebuild.ps1') -Phase Retire
        & (Join-Path $PSScriptRoot 'Invoke-StageOneRebuild.ps1') -Phase Bootstrap
    } elseif($WorkSet -eq 'ResumeBootstrap03') {
        & (Join-Path $PSScriptRoot 'Invoke-StageOneRebuild.ps1') -Phase Bootstrap
    } elseif($WorkSet -eq 'ResumePg06') {
        & (Join-Path $PSScriptRoot 'Invoke-StageOneRebuild.ps1') -Phase ResumeInstall
        & (Join-Path $PSScriptRoot 'Invoke-StageOneRebuild.ps1') -Phase Verify
    } else {
        & (Join-Path $PSScriptRoot 'Invoke-StageOneRebuild.ps1') -Phase Install
        & (Join-Path $PSScriptRoot 'Invoke-StageOneRebuild.ps1') -Phase Verify
    }
    $completed=$true
} catch {$failure=$_.Exception.Message}
finally {
    $restoreErrors=@()
    try{Complete-RebuildNetworkRecovery $networkIntent $networkDir}catch{$restoreErrors+=$_.Exception.Message}
    Write-RebuildJson (Join-Path $networkDir 'result.json') @{success=$completed;failure=$failure;network_restore_errors=$restoreErrors;finished=[DateTimeOffset]::UtcNow.ToString('o')}
    # The guard exits only after a positive restore receipt; otherwise it remains
    # available to retry the same exact adapters at its bounded recovery deadline.
    if($restoreErrors.Count -eq 0){Write-RebuildJson (Join-Path $networkDir 'restored.json') @{restored=$true;adapters=$adapters}}
    # Keep the tool's process lifetime open while the independent guard owns a
    # failed restore; otherwise an enclosing Windows job may reap the child.
    if($restoreErrors.Count -gt 0){$watchdog.WaitForExit(660000)|Out-Null}
}
if($restoreErrors.Count){throw 'network_restore_incomplete_watchdog_active'}
if(-not $completed){throw "offline_work_failed:$failure"}
'OFFLINE_WINDOW_AND_NETWORK_RESTORE_OK'
