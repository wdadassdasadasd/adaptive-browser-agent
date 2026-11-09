# Exact ordinary daily-token negatives during the ONE controlled offline window.
[CmdletBinding()]
param()
$ErrorActionPreference='Stop'
Set-StrictMode -Version Latest
function Publish-StandardPolicyResult([string]$Destination,[byte[]]$Bytes) {
    if($Bytes.Length -le 0 -or $Bytes.Length -gt 16384){throw 'ordinary_result_producer_cap'}
    $pending=$Destination+'.pending'
    $f=[IO.File]::Open($pending,'CreateNew','Write','None')
    try{$f.Write($Bytes,0,$Bytes.Length);$f.Flush($true)}finally{$f.Dispose()}
    [IO.File]::Move($pending,$Destination)
}
$id=[Security.Principal.WindowsIdentity]::GetCurrent()
if($id.User.Value -cne 'S-1-5-21-2765399256-1806415232-1753294129-1001' -or
    ([Security.Principal.WindowsPrincipal]::new($id)).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)){throw 'ordinary_daily_token_required'}
if(@(Get-NetAdapter -Physical | Where-Object Status -eq 'Up').Count){throw 'physical_offline_required'}
$root='D:\adaptive-browser-agent\.tmp\stage-1-1-resume-20261107\bootstrap\window-01'
if(-not(Test-Path -LiteralPath (Join-Path $root 'ordinary-negative-ready.json'))){throw 'controlled_window_not_ready'}
$dest=Join-Path $root 'ordinary-negative-result.json'
if(Test-Path -LiteralPath $dest){throw 'ordinary_result_exists_no_retry'}
Add-Type -Path (Join-Path $PSScriptRoot 'BoundedNative.cs')
$wsl="$env:SystemRoot\System32\wsl.exe"
$canary='D:\adaptive-browser-agent\.tmp\stage-1-1-resume-20261107\config-canary-01\protected-synthetic.vhdx'
$lxss='HKCU:\Software\Microsoft\Windows\CurrentVersion\Lxss'
$before=@(Get-ChildItem -LiteralPath $lxss | ForEach-Object {$_.PSChildName} | Sort-Object)
$checks=@()
foreach($argsAndPattern in @(
    # An ordinary caller may be refused at the CLI privilege gate before the service policy.
    # Only the separate elevated test attributes WSL_E_DISK_MOUNT_DISABLED to machine policy.
    @{name='attach';argv=@('--mount','--vhd',$canary,'--bare');pattern='WSL_E_DISK_MOUNT_DISABLED|WSL_E_ELEVATION_NEEDED|E_ACCESSDENIED|ERROR_ACCESS_DENIED|0x80070005'},
    @{name='import';argv=@('--import-in-place','stage1-protected-negative-standard',$canary);pattern='E_ACCESSDENIED|ERROR_ACCESS_DENIED|0x80070005'}
)) {
    $r=[AraBoundedNative]::Run($wsl,[string[]]$argsAndPattern.argv,30000,65536)
    $text=$r.Lines -join ' | '
    Write-Output "ORDINARY_$($argsAndPattern.name)_EXIT=$($r.Exit) OUTPUT=$text"
    if($r.Exit -eq 0 -or $text -notmatch $argsAndPattern.pattern){throw "ordinary_negative_wrong_failure:$($argsAndPattern.name)"}
    # Full native diagnostic remains in the caller's transcript; the bounded handshake carries
    # only finite categories so maximum legal native output cannot overflow the parent JSON.
    $category=if($text -match 'WSL_E_DISK_MOUNT_DISABLED'){'machine_policy_denial'}
        elseif($text -match 'WSL_E_ELEVATION_NEEDED'){'privilege_denial'}else{'data_access_denial'}
    $checks+=@{name=$argsAndPattern.name;exit=$r.Exit;category=$category}
}
$after=@(Get-ChildItem -LiteralPath $lxss | ForEach-Object {$_.PSChildName} | Sort-Object)
if(($before -join '|') -cne ($after -join '|')){throw 'ordinary_import_registration_changed_preserve_no_cleanup'}
$data=[Text.Encoding]::UTF8.GetBytes((@{state='ordinary_negatives_passed';utc=[DateTimeOffset]::UtcNow.ToString('o');checks=$checks} | ConvertTo-Json -Depth 5))
Publish-StandardPolicyResult $dest $data
'ORDINARY_POLICY_NEGATIVES=OK'
