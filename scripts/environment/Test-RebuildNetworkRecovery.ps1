[CmdletBinding()]
param([Parameter(Mandatory)][string]$FixtureDir)
$ErrorActionPreference='Stop'
Set-StrictMode -Version Latest
if(Test-Path -LiteralPath $FixtureDir){throw 'fixture_exists'}
$null=New-Item -ItemType Directory -Path $FixtureDir
$module=Import-Module (Join-Path $PSScriptRoot 'StageOneRebuild.psm1') -Force -PassThru
# Real process semantics, but only a newly created sleeping fixture is stopped.
$child=Start-Process -FilePath ([Environment]::ProcessPath) -WindowStyle Hidden -ArgumentList @('-NoProfile','-NonInteractive','-Command','Start-Sleep -Seconds 30') -PassThru
$intent=@{coordinator_pid=$child.Id;coordinator_started=$child.StartTime.ToUniversalTime().ToString('o')}
try {
    $wrong=@{coordinator_pid=$child.Id;coordinator_started='wrong-creation-time'}
    try{Stop-RebuildCoordinator $wrong;throw 'pid_reuse_not_denied'}catch{if($_.Exception.Message -cne 'watchdog_coordinator_pid_reused'){throw}}
    if($child.HasExited){throw 'mismatched_process_was_killed'}
    Stop-RebuildCoordinator $intent
    if(-not $child.HasExited){throw 'fixture_coordinator_not_stopped'}
} finally {if(-not $child.HasExited){$child.Kill()};$child.Dispose()}
& $module {
    param($fixture)
    # Exercise actual byte/mtime restoration against a private fixture, not the
    # host .wslconfig, as if the coordinator died after replacing the config.
    $script:Root=Join-Path $fixture 'phase-evidence';$script:Config=Join-Path $fixture 'live-config'
    $configDir=Join-Path $script:Root 'bootstrap';$null=New-Item -ItemType Directory -Path $configDir -Force
    $saved=Join-Path $configDir 'original.wslconfig';[IO.File]::WriteAllText($saved,'original-fixture')
    $script:OriginalConfigHash=(Get-FileHash $saved).Hash.ToLowerInvariant();$stamp=[datetime]::Parse('2026-01-02T03:04:05Z').ToUniversalTime()
    Write-RebuildJson (Join-Path $configDir 'config-binding.json') @{sha256=$script:OriginalConfigHash;mtime=$stamp.ToString('o')}
    [IO.File]::WriteAllText($script:Config,'temporary-offline-config')
    Restore-RebuildWindowConfig 'RetireBootstrap'
    if([IO.File]::ReadAllText($script:Config) -cne 'original-fixture' -or [IO.File]::GetLastWriteTimeUtc($script:Config) -ne $stamp){throw 'timeout_configuration_not_restored'}
    $resume=Join-Path $script:Root 'bootstrap-03';$null=New-Item -ItemType Directory $resume
    Copy-Item -LiteralPath $saved -Destination (Join-Path $resume 'original.wslconfig')
    Copy-Item -LiteralPath (Join-Path $configDir 'config-binding.json') -Destination (Join-Path $resume 'config-binding.json')
    [IO.File]::WriteAllText($script:Config,'resume-temporary-config')
    Restore-RebuildWindowConfig 'ResumeBootstrap03'
    if([IO.File]::ReadAllText($script:Config) -cne 'original-fixture' -or [IO.File]::GetLastWriteTimeUtc($script:Config) -ne $stamp){throw 'resume_configuration_not_restored'}
    $script:events=[Collections.Generic.List[string]]::new();$script:fenceFailure=$false
    function Stop-RebuildCoordinator($Intent){$script:events.Add('stop_coordinator')}
    function Stop-RebuildServiceFence {$script:events.Add('fence');if($script:fenceFailure){throw 'fixture_fence_failed'}}
    function Restore-RebuildNetwork($Adapters){$script:events.Add('restore')}
    function Restore-RebuildWindowConfig($WorkSet){$script:events.Add('restore_config')}
    $intent=@{workset=('Test-'+$PID);adapters=@()}
    Complete-RebuildNetworkRecovery $intent $fixture
    if(($script:events -join ',') -cne 'fence,restore_config,restore'){throw 'normal_cleanup_order'}
    $script:events.Clear();$script:fenceFailure=$true
    try{Complete-RebuildNetworkRecovery $intent $fixture;throw 'unfenced_network_was_restored'}catch{if($_.Exception.Message -cne 'fixture_fence_failed'){throw}}
    if(($script:events -join ',') -cne 'fence'){throw 'fence_failure_restored_network'}
    $script:events.Clear();$script:fenceFailure=$false
    Complete-RebuildNetworkRecovery $intent $fixture -Watchdog
    if(($script:events -join ',') -cne 'stop_coordinator,fence,restore_config,restore'){throw 'watchdog_cleanup_order'}
    $script:events.Clear()
    Write-RebuildJson (Join-Path $fixture 'cancelled.json') @{reason='fixture_watchdog_timed_out_after_offline_check'}
    try{Complete-RebuildNetworkRecovery $intent $fixture;throw 'cancelled_main_kept_cleanup_authority'}catch{if($_.Exception.Message -cne 'coordinator_cancelled_watchdog_owns_cleanup'){throw}}
    if($script:events.Count -ne 0){throw 'cancelled_main_touched_services_or_network'}
    'NETWORK_FAILURE_ORDER_CANCEL_AND_REAL_PROCESS_IDENTITY_OK'
} $FixtureDir
