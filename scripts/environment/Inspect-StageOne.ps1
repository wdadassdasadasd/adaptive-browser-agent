# Metadata only: never invokes WSL, reads a VHDX, or changes machine settings.
[CmdletBinding()]
param()
$ErrorActionPreference = 'Stop'
Set-StrictMode -Version Latest
$id = [Security.Principal.WindowsIdentity]::GetCurrent()
$expectedSid = 'S-1-5-21-2765399256-1806415232-1753294129-1001'
if ($id.User.Value -cne $expectedSid) { throw 'actual_daily_token_required' }
$principal = [Security.Principal.WindowsPrincipal]::new($id)
$result = [ordered]@{
    schema = 'ENV-M1-01.host-preflight.v1'
    utc = [DateTimeOffset]::UtcNow.ToString('o')
    actual_daily_sid = $true
    elevated = $principal.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
    services = @()
    wsl_version = (Get-Item -LiteralPath 'C:\Program Files\WSL\wslservice.exe').VersionInfo.FileVersion
    physical_up = @(Get-NetAdapter -Physical | Where-Object Status -eq Up).Count
    policies = [ordered]@{}
    registered = @()
    custody = @()
    old_tcp_connections = @()
}
foreach ($name in 'WslService','vmcompute') {
    $service = Get-Service -Name $name
    $result.services += [ordered]@{name=$name;status=[string]$service.Status;start_type=[string]$service.StartType}
}
$policyKey = 'Registry::HKEY_LOCAL_MACHINE\Software\Policies\WSL'
if (Test-Path -LiteralPath $policyKey) {
    $key = Get-Item -LiteralPath $policyKey
    foreach ($name in 'AllowWSL','AllowInboxWSL','AllowWSL1','AllowKernelUserSetting','AllowSystemDistroUserSetting',
        'AllowKernelCommandLineUserSetting','AllowDiskMount','AllowDebugShell','DefaultNetworkingMode','AllowNetworkingModeUserSetting') {
        if ($name -in $key.GetValueNames()) {
            $result.policies[$name] = [ordered]@{kind=[string]$key.GetValueKind($name);value=$key.GetValue($name)}
        }
    }
}
$lxss = 'Registry::HKEY_CURRENT_USER\Software\Microsoft\Windows\CurrentVersion\Lxss'
foreach ($key in @(Get-ChildItem -LiteralPath $lxss)) {
    $name = $key.GetValue('DistributionName')
    $path = $key.GetValue('BasePath')
    if ($name -cne 'Ubuntu') { throw 'unexpected_registered_distribution' }
    $leaf = $key.GetValue('VhdFileName','ext4.vhdx')
    if ($leaf -cne [IO.Path]::GetFileName($leaf)) { throw 'registered_leaf_not_bounded' }
    $file = Get-Item -LiteralPath (Join-Path $path $leaf) -Force
    $result.registered += [ordered]@{
        guid=$key.PSChildName;name=$name;base_path=$path;leaf=$leaf;size=$file.Length
        modified_utc=$file.LastWriteTimeUtc.ToString('o');attributes=[string]$file.Attributes
    }
}
foreach ($path in 'C:\','C:\ProgramData','C:\ProgramData\ARA-Stage1-Archive-20261106',
    'C:\ProgramData\ARA-Stage1-Archive-20261106\capture') {
    $item = Get-Item -LiteralPath $path -Force
    $acl = Get-Acl -LiteralPath $path
    $result.custody += [ordered]@{
        path=$path;reparse=[bool]($item.Attributes -band [IO.FileAttributes]::ReparsePoint)
        sddl=$acl.GetSecurityDescriptorSddlForm([Security.AccessControl.AccessControlSections]'Owner,Access')
    }
}
$connections = @(Get-NetTCPConnection -ErrorAction Stop)
foreach ($port in 5433,55432) {
    $result.old_tcp_connections += [ordered]@{port=$port;count=@($connections | Where-Object LocalPort -eq $port).Count}
}
$text = $result | ConvertTo-Json -Depth 7 -Compress
if ([Text.Encoding]::UTF8.GetByteCount($text) -gt 16384) { throw 'preflight_output_cap' }
$text
