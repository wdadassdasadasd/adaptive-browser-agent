# Read-only post-restart static verification for stage-one 1.1.
# Zero writes: reads machine policy, service state, custody objects (metadata-only), the sealed
# real-custody receipt, the preserved .wslconfig bytes, persistent mount registrations and
# autorun surfaces. Exits non-zero on any drift from the sealed state.
# Requires: actual daily account, elevated (needed to read the metadata-only DACLs and bindings).
[CmdletBinding()]
param([switch]$PreWindow)
$ErrorActionPreference = 'Stop'
Set-StrictMode -Version Latest

$dailySid = 'S-1-5-21-2765399256-1806415232-1753294129-1001'
$identity = [Security.Principal.WindowsIdentity]::GetCurrent()
if ($identity.User.Value -cne $dailySid) { throw 'actual_daily_token_required' }
$principal = [Security.Principal.WindowsPrincipal]::new($identity)
if (-not $principal.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)) { throw 'elevation_required' }

$nativeSource = [IO.File]::ReadAllBytes((Join-Path $PSScriptRoot 'CustodyNative.cs'))
$sha = [Security.Cryptography.SHA256]::Create()
try {
    $digest = [BitConverter]::ToString($sha.ComputeHash($nativeSource)).Replace('-', '')
} finally { $sha.Dispose() }
if ($digest -cne 'AC534ED09A4725ECAEEC8517A2C6837B1A678F354D3587E1C68E3DC665CBA2D9') { throw 'helper_identity' }
Add-Type -TypeDefinition ([Text.Encoding]::UTF8.GetString($nativeSource))
Add-Type -TypeDefinition @'
using System;
using System.ComponentModel;
using System.Runtime.InteropServices;
using Microsoft.Win32.SafeHandles;
public static class AraVerifyShapeDump {
    [DllImport("kernel32.dll", CharSet=CharSet.Unicode, SetLastError=true)]
    private static extern SafeFileHandle CreateFileW(string p, uint a, uint s, IntPtr sd, uint d, uint f, IntPtr t);
    [DllImport("kernel32.dll", SetLastError=true)]
    private static extern bool GetFileInformationByHandleEx(SafeFileHandle h, int c, byte[] b, uint n);
    public static string Dump(string path) {
        using (var h = CreateFileW(path, 0x20080, 7, IntPtr.Zero, 3, 0x02200000, IntPtr.Zero)) {
            if (h.IsInvalid) throw new Win32Exception(Marshal.GetLastWin32Error());
            byte[] basic = new byte[40], standard = new byte[24];
            bool b = GetFileInformationByHandleEx(h, 0, basic, 40);
            int be = b ? 0 : Marshal.GetLastWin32Error();
            bool s = GetFileInformationByHandleEx(h, 1, standard, 24);
            int se = s ? 0 : Marshal.GetLastWin32Error();
            return "basic=" + Convert.ToBase64String(basic) + ";standard=" + Convert.ToBase64String(standard) + ";errors=" + be + "," + se;
        }
    }
}
'@

$result = [ordered]@{
    schema = 'ENV-M1-01.post-restart-verify.v1'
    utc = [DateTimeOffset]::UtcNow.ToString('o')
    checks = [ordered]@{}
    binding_open_failures = @()
}
$result.verification_mode = if ($PreWindow) { 'pre_window' } else { 'post_restart' }
$bootUtc = (Get-CimInstance Win32_OperatingSystem).LastBootUpTime.ToUniversalTime()
$result.last_boot_utc = $bootUtc.ToString('o')
if (-not $PreWindow) {
    $windowRoot = 'D:\adaptive-browser-agent\.tmp\stage-1-1-resume-20261107\bootstrap\window-01'
    foreach ($phase in 'phase1', 'phase2') {
        $latest = Get-ChildItem -LiteralPath $windowRoot -Filter "$phase-*.log" | Sort-Object LastWriteTimeUtc -Descending | Select-Object -First 1
        if ($null -eq $latest -or $bootUtc -le $latest.LastWriteTimeUtc) { throw "restart_after_window_not_proven:$phase" }
        $log = [IO.File]::ReadAllText($latest.FullName)
        $marker = $phase.ToUpperInvariant() + '_RESULT=OK'
        if ($log -notmatch "(?m)^$marker\r?$") { throw "latest_phase_not_success:$phase" }
    }
}

function Assert-Check([string]$Name, [bool]$Condition, [string]$Detail) {
    if (-not $Condition) { Write-Host "VERIFY_FAILED_DETAIL=${Name}:$Detail"; throw "post_restart_drift:$Name" }
    $script:result.checks[$Name] = $Detail
}

# 1. Services still fenced.
foreach ($name in 'WslService', 'vmcompute') {
    $state = Get-Service -Name $name
    Assert-Check "service_$name" ($state.Status -eq 'Stopped' -and $state.StartType -eq 'Disabled') "$($state.Status)/$($state.StartType)"
}

# 2. Machine policy still exact.
$policyValues = [ordered]@{
    AllowWSL = 1; AllowInboxWSL = 0; AllowWSL1 = 0; AllowKernelUserSetting = 0
    AllowSystemDistroUserSetting = 0; AllowKernelCommandLineUserSetting = 0; AllowDebugShell = 0
    AllowNestedVirtualization = 0; AllowKernelDebugUserSetting = 0; AllowDiskMount = 0
    AllowNetworkingModeUserSetting = 0; AllowFirewallUserSetting = 0; DefaultNetworkingMode = 0
}
$keyPath = 'Registry::HKEY_LOCAL_MACHINE\Software\Policies\WSL'
$key = Get-Item -LiteralPath $keyPath
foreach ($name in $policyValues.Keys) {
    if ($name -cnotin $key.GetValueNames()) { throw "policy_absent:$name" }
    if ($key.GetValueKind($name) -ne 'DWord') { throw "policy_kind:$name" }
    if ([int]$key.GetValue($name) -ne [int]$policyValues[$name]) { throw "policy_value:$name" }
}
Assert-Check 'policy_all_exact' $true '13 values DWord exact'
$policyAcl = Get-Acl -Path 'HKLM:\Software\Policies\WSL'
foreach ($rule in $policyAcl.Access) {
    if ($rule.AccessControlType -ne 'Allow') { continue }
    try { $sid = $rule.IdentityReference.Translate([Security.Principal.SecurityIdentifier]).Value }
    catch [System.Security.Principal.IdentityNotMappedException] { $sid = $rule.IdentityReference.Value }
    if (([long]$rule.RegistryRights -band 0x500D0006) -ne 0 -and $sid -notin 'S-1-5-18', 'S-1-5-32-544') { throw "policy_writable_by:$sid" }
}
Assert-Check 'policy_acl' $true $policyAcl.GetSecurityDescriptorSddlForm('Owner,Access')

# 3. Custody objects: bindings must equal the sealed receipt; sizes unchanged.
$sealedPath = 'C:\ProgramData\ARA-Stage1-Archive-20261106\real-custody-20261107\sealed.json'
$sealed = Get-Content -LiteralPath $sealedPath -Raw | ConvertFrom-Json
Assert-Check 'boot_after_custody_seal' ($bootUtc -gt [DateTimeOffset]::Parse([string]$sealed.utc).UtcDateTime) 'Current boot follows the protected seal receipt; pre-seal user-mode handles cannot survive it. Does not attest the pre-reboot interval.'

function Binding-Of([string]$Path, [bool]$Directory) {
    for ($attempt = 1; $attempt -le 2; $attempt++) {
        $h = [AraCustodyHandle]::Open($Path, 0x20080, 7)
        try { return [AraCustodyHandle]::Binding($h, $Path, $Directory) }
        catch {
            if ($_.Exception.ToString() -notmatch 'object_shape_changed') { throw }
            $dump = try { [AraVerifyShapeDump]::Dump($Path) } catch { "dump_failed:$($_.Exception.Message)" }
            $script:result.binding_open_failures += "attempt=${attempt}:path=${Path}:$dump"
            Write-Host "BINDING_ATTEMPT_${attempt}_FAILED $Path $dump"
            if ($attempt -eq 2) { throw }
        } finally { $h.Dispose() }
    }
    throw 'binding_retry_exhausted'
}

foreach ($pair in @(
    @{ name = 'original'; path = 'C:\Users\FFFFFF\AppData\Local\Packages\CanonicalGroupLimited.Ubuntu_79rhkp1fndgsc\LocalState\ext4.vhdx'; dir = $false; key = 'original_binding' },
    @{ name = 'copy'; path = 'C:\ProgramData\ARA-Stage1-Archive-20261106\capture\Ubuntu.vhdx.pending'; dir = $false; key = 'copy_binding' },
    @{ name = 'local_state'; path = 'C:\Users\FFFFFF\AppData\Local\Packages\CanonicalGroupLimited.Ubuntu_79rhkp1fndgsc\LocalState'; dir = $true; key = 'local_state_binding' },
    @{ name = 'capture'; path = 'C:\ProgramData\ARA-Stage1-Archive-20261106\capture'; dir = $true; key = 'capture_binding' },
    @{ name = 'wslconfig'; path = 'C:\Users\FFFFFF\.wslconfig'; dir = $false; key = 'wslconfig_binding' }
)) {
    # Identity continuity = binding fields 0..5 (volume|fileId|size|links|ctime|mtime); field 6
    # (latest USN sequence) legitimately changes with any metadata operation such as an ACL set.
    $binding = Binding-Of $pair.path $pair.dir
    $bNow = $binding.Split('|')
    $sealedValue = $sealed.$($pair.key)
    if ($null -eq $sealedValue) { throw "sealed_binding_missing:$($pair.key)" }
    $bSealed = $sealedValue.Split('|')
    $identityMatch = $bNow.Count -eq 7 -and $bSealed.Count -eq 7
    $mismatchField = -1
    if ($identityMatch) {
        for ($i = 0; $i -le 5; $i++) {
            if ($bNow[$i] -cne $bSealed[$i]) { $identityMatch = $false; $mismatchField = $i; break }
        }
    }
    $detail = "now=$($bNow[0..5] -join '|'); sealed=$($bSealed[0..5] -join '|'); mismatch_field=$mismatchField"
    Assert-Check "binding_$($pair.name)" $identityMatch $detail
    $sddlNow = (Get-Acl -LiteralPath $pair.path).GetSecurityDescriptorSddlForm('Owner,Access')
    Assert-Check "sddl_$($pair.name)" ($sddlNow -ceq $sealed.sddl_after.($pair.path)) $sddlNow
}

# Metadata-only property both directions, even for this elevated token: a raw data-read mask
# (0x1, no SYNCHRONIZE) must be denied while the metadata mask succeeds.
foreach ($protectedFile in @(
    @{ name = 'original'; path = 'C:\Users\FFFFFF\AppData\Local\Packages\CanonicalGroupLimited.Ubuntu_79rhkp1fndgsc\LocalState\ext4.vhdx' },
    @{ name = 'copy'; path = 'C:\ProgramData\ARA-Stage1-Archive-20261106\capture\Ubuntu.vhdx.pending' }
)) {
    try {
        $h = [AraCustodyHandle]::Open($protectedFile.path, 1, 7)
        $h.Dispose()
        throw "elevated_raw_data_read_allowed:$($protectedFile.name)"
    } catch [ComponentModel.Win32Exception] {
        if ($_.Exception.NativeErrorCode -ne 5) { throw }
    }
    $h = [AraCustodyHandle]::Open($protectedFile.path, 0x120080, 7)
    $h.Dispose()
    Assert-Check "metadata_only_$($protectedFile.name)" $true 'raw 0x1 denied elevated; 0x120080 allowed'
}

# 4. Preserved .wslconfig bytes.
$stream = [IO.File]::Open('C:\Users\FFFFFF\.wslconfig', 'Open', 'Read', 'Read')
try {
    $sha2 = [Security.Cryptography.SHA256]::Create()
    try {
        $hash = [BitConverter]::ToString($sha2.ComputeHash($stream)).Replace('-', '')
    } finally { $sha2.Dispose() }
} finally { $stream.Dispose() }
Assert-Check 'wslconfig_bytes' ($hash -ceq $sealed.wslconfig_sha256) $hash

# 5. No persistent disk mount registrations for the daily SID.
$dm = 'HKLM:\SOFTWARE\Microsoft\Windows\CurrentVersion\Lxss\DiskMounts'
$dmUser = Get-Item -LiteralPath "$dm\$dailySid" -ErrorAction SilentlyContinue
$mountCount = 0
if ($null -ne $dmUser) { $mountCount = @($dmUser.Property).Count + @(Get-ChildItem -LiteralPath $dmUser.PSPath -ErrorAction SilentlyContinue).Count }
Assert-Check 'diskmounts_empty' ($mountCount -eq 0) "entries=$mountCount"

# 6. No Ubuntu/WSL autorun surfaces appeared.
$autorunHits = 0
foreach ($runPath in 'HKCU:\Software\Microsoft\Windows\CurrentVersion\Run', 'HKLM:\SOFTWARE\Microsoft\Windows\CurrentVersion\Run',
    'HKLM:\SOFTWARE\WOW6432Node\Microsoft\Windows\CurrentVersion\Run') {
    $runKey = Get-Item -LiteralPath $runPath -ErrorAction SilentlyContinue
    if ($null -eq $runKey) { continue }
    foreach ($name in $runKey.Property) {
        $command = [string]$runKey.GetValue($name)
        if ($name -imatch 'ubuntu|wsl|linux|bash' -or $command -imatch 'ubuntu|wsl(?:\.exe|\s)|bash\.exe|linux') { $autorunHits++ }
    }
}
foreach ($dir in @("$env:APPDATA\Microsoft\Windows\Start Menu\Programs\Startup", "$env:ProgramData\Microsoft\Windows\Start Menu\Programs\StartUp")) {
    foreach ($item in @(Get-ChildItem -LiteralPath $dir -ErrorAction SilentlyContinue)) {
        if ($item.Name -imatch 'ubuntu|wsl|linux|bash') { $autorunHits++ }
    }
}
Assert-Check 'autoruns_clean' ($autorunHits -eq 0) "hits=$autorunHits"

# 7. Old service ports still silent.
$connections = @(Get-NetTCPConnection -ErrorAction Stop)
foreach ($port in 5433, 55432) {
    Assert-Check "port_${port}_silent" (@($connections | Where-Object LocalPort -eq $port).Count -eq 0) 'count=0'
}

$text = $result | ConvertTo-Json -Depth 6
if ([Text.Encoding]::UTF8.GetByteCount($text) -gt 16384) { throw 'verify_output_cap' }
if ($PreWindow) { 'PRE_WINDOW_VERIFY_OK' } else { 'POST_RESTART_VERIFY_OK' }
$text
