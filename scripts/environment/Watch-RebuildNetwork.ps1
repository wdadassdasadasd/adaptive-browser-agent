[CmdletBinding()]
param([Parameter(Mandatory)][ValidateSet('RetireBootstrap','ResumeBootstrap03','Install','ResumePg06')][string]$WorkSet)
$ErrorActionPreference='Stop'
Set-StrictMode -Version Latest
$dir=Join-Path 'D:\adaptive-browser-agent\.tmp\stage1-rebuild-20261108' ('network-'+$WorkSet.ToLowerInvariant())
Start-Transcript -LiteralPath (Join-Path $dir 'watchdog-transcript.txt')|Out-Null
try {
Import-Module (Join-Path $PSScriptRoot 'StageOneRebuild.psm1') -Force
Assert-RebuildRuntime
$null=Assert-RebuildCandidate
$intent=Get-Content -LiteralPath (Join-Path $dir 'intent.json') -Raw|ConvertFrom-Json -DateKind String
if($intent.workset -cne $WorkSet -or $intent.watchdog_seconds -ne 600 -or $intent.adapters.Count -lt 1){throw 'invalid_network_intent'}
Write-RebuildJson (Join-Path $dir 'watchdog-ready.json') @{pid=$PID;started=(Get-Process -Id $PID).StartTime.ToUniversalTime().ToString('o');intent_sha256=(Get-FileHash (Join-Path $dir 'intent.json')).Hash.ToLowerInvariant()}
$deadline=[datetime]::UtcNow.AddSeconds(600)
while([datetime]::UtcNow -lt $deadline){if(Test-Path (Join-Path $dir 'restored.json')){Write-RebuildJson (Join-Path $dir 'watchdog-result.json') @{recovery_attempted=$false;normal_restore_observed=$true;errors=@()};return};Start-Sleep -Seconds 5}
$errors=@()
Write-RebuildJson (Join-Path $dir 'cancelled.json') @{reason='offline_window_600s_deadline';coordinator_pid=$intent.coordinator_pid}
try{Complete-RebuildNetworkRecovery $intent $dir -Watchdog}catch{$errors+=$_.Exception.Message}
Write-RebuildJson (Join-Path $dir 'watchdog-result.json') @{recovery_attempted=$true;errors=$errors;finished=[DateTimeOffset]::UtcNow.ToString('o')}
} catch {$_|Out-String|Out-File -LiteralPath (Join-Path $dir 'watchdog-error.txt');throw}
finally {Stop-Transcript|Out-Null}
