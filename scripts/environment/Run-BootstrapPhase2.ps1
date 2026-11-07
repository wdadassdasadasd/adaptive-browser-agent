# Stage-1 controlled bootstrap window, phase 2: after the deb fetch, the human re-disconnects
# the network; this elevated script verifies fences and closes the window (services disabled).
[CmdletBinding()]
param()
$ErrorActionPreference = 'Stop'
Set-StrictMode -Version Latest

$logRoot = 'D:\adaptive-browser-agent\.tmp\stage-1-1-resume-20261107\bootstrap\window-01'
$stamp = [DateTimeOffset]::UtcNow.ToString('yyyyMMddTHHmmssZ') -replace ':', ''
Start-Transcript -Path (Join-Path $logRoot "phase2-$stamp.log") | Out-Null

$dailySid = 'S-1-5-21-2765399256-1806415232-1753294129-1001'
$identity = [Security.Principal.WindowsIdentity]::GetCurrent()
if ($identity.User.Value -cne $dailySid) { throw 'actual_daily_token_required' }
$principal = [Security.Principal.WindowsPrincipal]::new($identity)
if (-not $principal.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)) { throw 'elevation_required' }

try {
    $up = @(Get-NetAdapter -Physical | Where-Object Status -eq 'Up')
    if ($up.Count -gt 0) { throw "physical_network_up:$($up.Count)" }
    Write-Output 'PHASE2_offline_verified'

    foreach ($name in 'WslService', 'vmcompute') {
        $null = & sc.exe stop $name 2>&1 | Out-String
        $null = & sc.exe config $name start= disabled 2>&1
        if ($LASTEXITCODE -ne 0) { throw "sc_disable_failed:$name" }
    }
    Start-Sleep -Seconds 2
    foreach ($name in 'WslService', 'vmcompute') {
        $svc = Get-Service -Name $name
        if ($svc.Status -ne 'Stopped' -or $svc.StartType -ne 'Disabled') {
            throw "service_state:${name}:$($svc.Status)/$($svc.StartType)"
        }
    }
    Write-Output 'PHASE2_services_disabled'

    $guests = @(Get-Process -Name 'vmmemWSL', 'wslhost' -ErrorAction SilentlyContinue)
    if ($guests.Count) { throw 'wsl_processes_remain_after_fence' }
    Write-Output 'PHASE2_no_guest_processes_services_stopped'
    Write-Output 'WINDOW_PHASE=window_closed'
    'PHASE2_RESULT=OK'
    exit 0
} catch {
    Write-Output "PHASE2_FAILURE=$($_.Exception.Message)"
    foreach ($name in 'WslService', 'vmcompute') {
        try {
            $null = & sc.exe stop $name 2>&1 | Out-String
            $null = & sc.exe config $name start= disabled 2>&1
            $svc = Get-Service -Name $name
            $svc.WaitForStatus('Stopped', [TimeSpan]::FromSeconds(15))
            $svc.Refresh()
            if ($svc.StartType -ne 'Disabled') { throw 'disable_not_confirmed' }
            Write-Output "PHASE2_CLEANUP=${name}:$($svc.Status)/$($svc.StartType)"
        } catch { Write-Output "PHASE2_CLEANUP_UNKNOWN=${name}:$($_.Exception.Message)" }
    }
    'PHASE2_RESULT=FAILED'
    exit 1
} finally {
    Stop-Transcript | Out-Null
}
