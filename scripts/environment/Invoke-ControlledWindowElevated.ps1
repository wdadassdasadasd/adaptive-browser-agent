# Exact reviewed window launcher: retain read-only leases on every implementation input.
[CmdletBinding()]
param([switch]$DisableWlan)
throw 'ENV_M1_01_ORIGINAL_BINDING_DRIFT_DO_NOT_DISABLE_NETWORK_OR_START_WINDOW'
$ErrorActionPreference='Stop'
Set-StrictMode -Version Latest
$identity=[Security.Principal.WindowsIdentity]::GetCurrent()
if($identity.User.Value -cne 'S-1-5-21-2765399256-1806415232-1753294129-1001' -or
    -not ([Security.Principal.WindowsPrincipal]::new($identity)).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)){throw 'window_launcher_actual_elevated_daily_token_required'}
$repo='D:\adaptive-browser-agent'
$log=Join-Path $repo '.tmp\stage-1-1-resume-20261107\bootstrap\window-01\controlled-window-wrapper-01.log'
if(Test-Path -LiteralPath $log){throw 'wrapper_log_exists_no_retry'}
$locks=[Collections.Generic.List[IDisposable]]::new()
$networkDisabled=$false
$exitCode=1
Start-Transcript -LiteralPath $log|Out-Null
try {
    $manifestPath=Join-Path $repo '.tmp\stage-1-1-resume-20261107\review-11\manifest.json'
    $manifest=Get-Content -LiteralPath $manifestPath -Raw|ConvertFrom-Json
    foreach($entry in @($manifest|Where-Object path -like 'scripts/environment/*')) {
        $path=Join-Path $repo $entry.path
        if((Get-Item -LiteralPath $path -Force).Attributes -band [IO.FileAttributes]::ReparsePoint){throw 'window_source_reparse'}
        $f=[IO.File]::Open($path,'Open','Read','Read');$locks.Add($f)
        if($f.Length -ne $entry.bytes){throw "window_source_length:$($entry.path)"}
        $sha=[Security.Cryptography.SHA256]::Create()
        try{$hash=[BitConverter]::ToString($sha.ComputeHash($f)).Replace('-','').ToLowerInvariant()}finally{$sha.Dispose()}
        if($hash -cne $entry.sha256){throw "window_source_hash:$($entry.path)"}
    }
    Set-Location -LiteralPath $repo
    if($DisableWlan) {
        # Exact human authorization in this chat: temporarily disable WLAN and run the window.
        Disable-NetAdapter -Name 'WLAN' -Confirm:$false -ErrorAction Stop
        $networkDisabled=$true
        'CONTROLLED_WINDOW_WLAN_TEMPORARILY_DISABLED'
    }
    'CONTROLLED_WINDOW_WAITING_FOR_HUMAN_PHYSICAL_OFFLINE'
    $offlineDeadline=[DateTimeOffset]::UtcNow.AddMinutes(3)
    while(@(Get-NetAdapter -Physical|Where-Object Status -eq 'Up').Count) {
        if([DateTimeOffset]::UtcNow -ge $offlineDeadline){throw 'physical_offline_wait_expired_no_window_started'}
        Start-Sleep -Seconds 1
    }
    & 'D:\adaptive-browser-agent\scripts\environment\Run-BootstrapPhase1.ps1'
    $phaseCode=$LASTEXITCODE
    Write-Output "CONTROLLED_WINDOW_SCRIPT_EXIT=$phaseCode"
    $exitCode=$phaseCode
} catch {
    "CONTROLLED_WINDOW_LAUNCH_FAILURE=$($_.Exception.ToString())"
    "CONTROLLED_WINDOW_FAILURE_STACK=$($_.ScriptStackTrace)"
    $exitCode=1
} finally {
    if($networkDisabled) {
        try {
            foreach($name in 'WslService','vmcompute') {
                $svc=Get-Service -Name $name
                if($svc.Status -ne 'Stopped' -or $svc.StartType -ne 'Disabled'){throw 'network_restore_service_not_fenced'}
            }
            if(@(Get-Process -Name 'vmmemWSL','wslhost' -ErrorAction SilentlyContinue).Count){throw 'network_restore_guest_present'}
            $source='C:\Users\FFFFFF\.wslconfig'
            if(Test-Path -LiteralPath 'C:\Users\FFFFFF\.ara-stage1-policy-probe-20261107\original.wslconfig'){throw 'network_restore_original_still_retained'}
            $sealed=Get-Content -LiteralPath 'C:\ProgramData\ARA-Stage1-Archive-20261106\real-custody-20261107\sealed.json' -Raw|ConvertFrom-Json
            if((Get-FileHash -LiteralPath $source -Algorithm SHA256).Hash -cne $sealed.wslconfig_sha256){throw 'network_restore_config_bytes_drift'}
            if((Get-Acl -LiteralPath $source).GetSecurityDescriptorSddlForm('Owner,Access') -cne $sealed.sddl_after.($source)){throw 'network_restore_config_acl_drift'}
            if(-not('AraCustodyHandle' -as [type])){Add-Type -Path (Join-Path $repo 'scripts\environment\CustodyNative.cs')}
            $h=[AraCustodyHandle]::Open($source,0x20080,7)
            try{$binding=[AraCustodyHandle]::Binding($h,$source,$false)}finally{$h.Dispose()}
            if(($binding.Split('|')[0..5]-join '|') -cne ($sealed.wslconfig_binding.Split('|')[0..5]-join '|')){throw 'network_restore_config_object_drift'}
            Enable-NetAdapter -Name 'WLAN' -Confirm:$false -ErrorAction Stop
            'CONTROLLED_WINDOW_WLAN_RESTORED_AFTER_VERIFIED_FENCE'
        } catch { "NETWORK_RESTORE_WITHHELD=$($_.Exception.Message)"; $exitCode=2 }
    }
    foreach($f in $locks){$f.Dispose()}
    Stop-Transcript|Out-Null
}
exit $exitCode
