# Ordinary local coordinator: model connectivity is not needed after the human disables Wi-Fi.
# Exact later human authorization permits the elevated child to temporarily disable WLAN.
[CmdletBinding()]
param()
throw 'ENV_M1_01_ORIGINAL_BINDING_DRIFT_DO_NOT_START_COORDINATED_WINDOW'
$ErrorActionPreference='Stop'
Set-StrictMode -Version Latest
$id=[Security.Principal.WindowsIdentity]::GetCurrent()
if($id.User.Value -cne 'S-1-5-21-2765399256-1806415232-1753294129-1001' -or
    ([Security.Principal.WindowsPrincipal]::new($id)).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)){throw 'coordinator_requires_ordinary_daily_token'}
$repo='D:\adaptive-browser-agent'
$root=Join-Path $repo '.tmp\stage-1-1-resume-20261107\bootstrap\window-01'
$log=Join-Path $root 'local-coordinator-01.log'
if(Test-Path -LiteralPath $log){throw 'coordinator_log_exists_preserve_no_retry'}
Start-Transcript -LiteralPath $log | Out-Null
$locks=[Collections.Generic.List[IDisposable]]::new()
$child=$null
try {
    $manifestPath=Join-Path $repo '.tmp\stage-1-1-resume-20261107\review-15\manifest.json'
    $manifest=Get-Content -LiteralPath $manifestPath -Raw|ConvertFrom-Json
    foreach($entry in @($manifest|Where-Object path -like 'scripts/environment/*')) {
        $path=Join-Path $repo $entry.path
        $f=[IO.File]::Open($path,'Open','Read','Read');$locks.Add($f)
        if($f.Length -ne $entry.bytes){throw 'coordinator_input_size'}
        $sha=[Security.Cryptography.SHA256]::Create()
        try{$digest=[BitConverter]::ToString($sha.ComputeHash($f)).Replace('-','').ToLowerInvariant()}finally{$sha.Dispose()}
        if($digest -cne $entry.sha256){throw "coordinator_source_drift:$($entry.path)"}
    }
    $launcher=Join-Path $PSScriptRoot 'Invoke-ControlledWindowElevated.ps1'
    $child=Start-Process -FilePath "$env:SystemRoot\System32\WindowsPowerShell\v1.0\powershell.exe" -Verb RunAs -WindowStyle Hidden -ArgumentList @('-NoProfile','-NonInteractive','-ExecutionPolicy','Bypass','-File',$launcher,'-DisableWlan') -PassThru
    Write-Output "LOCAL_COORDINATOR_ELEVATED_PID=$($child.Id)"
    $deadline=[DateTimeOffset]::UtcNow.AddMinutes(10)
    $ordinaryDone=$false
    while(-not $child.HasExited) {
        $child.Refresh()
        if(-not $ordinaryDone -and (Test-Path -LiteralPath (Join-Path $root 'ordinary-negative-ready.json'))) {
            & (Join-Path $PSScriptRoot 'Test-StandardPolicyNegative.ps1')
            $ordinaryDone=$true
        }
        if([DateTimeOffset]::UtcNow -ge $deadline){throw 'local_coordinator_deadline_child_not_force_killed_recovery_required'}
        Start-Sleep -Milliseconds 500
    }
    $child.WaitForExit()
    Write-Output "LOCAL_COORDINATOR_CHILD_EXIT=$($child.ExitCode)"
    if($child.ExitCode -ne 0){throw 'controlled_window_failed_keep_offline_until_fence_checked'}
    $saved='C:\Users\FFFFFF\.ara-stage1-policy-probe-20261107\original.wslconfig'
    if(Test-Path -LiteralPath $saved){throw 'original_configuration_not_restored'}
    foreach($name in 'WslService','vmcompute') {
        $service=Get-Service -Name $name
        if($service.Status -ne 'Stopped' -or $service.StartType -ne 'Disabled'){throw 'window_final_service_not_fenced'}
    }
    if(@(Get-Process -Name 'vmmemWSL','wslhost' -ErrorAction SilentlyContinue).Count){throw 'window_final_guest_process_present'}
    $onlineDeadline=[DateTimeOffset]::UtcNow.AddSeconds(45)
    while((Get-NetAdapter -Name WLAN).Status -ne 'Up') {
        if([DateTimeOffset]::UtcNow -ge $onlineDeadline){throw 'wlan_reconnection_not_confirmed_no_fetch'}
        Start-Sleep -Seconds 1
    }
    'LOCAL_CONTROLLED_WINDOW=OK_NETWORK_RESTORED'
    $fetchLog=Join-Path $root 'fixed-debs-fetch-01.log'
    if(Test-Path -LiteralPath $fetchLog){throw 'fetch_log_exists_preserve_no_retry'}
    & (Join-Path $repo '.venv\Scripts\python.exe') (Join-Path $PSScriptRoot 'fetch_fixed_debs.py') $root *> $fetchLog
    if($LASTEXITCODE -ne 0){throw 'fixed_deb_fetch_failed_preserve_no_retry'}
    'LOCAL_FIXED_DEB_FETCH=OK'
    Add-Type -AssemblyName System.Windows.Forms
    [Windows.Forms.MessageBox]::Show('Controlled window and fixed package fetch finished. Original configuration restored; WSL services stopped and disabled. Wi-Fi restored. Return to the chat for final closure and restart verification.', 'ARA 1.1 - Window and fetch finished', 'OK', 'Information') | Out-Null
} catch {
    "LOCAL_CONTROLLED_WINDOW_FAILURE=$($_.Exception.ToString())"
    "LOCAL_CONTROLLED_WINDOW_FAILURE_STACK=$($_.ScriptStackTrace)"
    # Do not kill the elevated owner: it owns fence/restoration. Never restore networking here.
    Add-Type -AssemblyName System.Windows.Forms
    [Windows.Forms.MessageBox]::Show('The controlled window did not complete. Keep Wi-Fi OFF until service and configuration recovery is checked. Preserve all files and return to the chat when a safe communication path is available.', 'ARA 1.1 - Window stopped', 'OK', 'Warning') | Out-Null
    throw
} finally {
    foreach($f in $locks){$f.Dispose()}
    Stop-Transcript | Out-Null
}
