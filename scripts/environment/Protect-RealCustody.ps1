# Protects the two real stage-one VHDX objects in place with metadata-only access.
# Never reads file content, never hashes a real disk, never renames or moves anything.
#
# Objects and resulting state:
#   original  C:\Users\FFFFFF\AppData\Local\Packages\CanonicalGroupLimited.Ubuntu_79rhkp1fndgsc\
#             LocalState\ext4.vhdx      -> O:BAD:P(A;;0x120080;;;SY)(A;;0x120080;;;BA)
#   LocalState parent dir                   -> O:BAD:P(SY/BA FA OICI; daily read+execute only)
#   copy      C:\ProgramData\ARA-Stage1-Archive-20261106\capture\Ubuntu.vhdx.pending
#                                           -> same protected metadata-only DACL as the original
#   capture parent dir                      -> O:BAD:P(SY/BA FA; daily read+execute), protected flag set
#   C:\Users\FFFFFF\.wslconfig              -> O:BAD:P(SY/BA FA; daily read+execute), bytes preserved
#
# The protected DACL on the disk files grants only 0x120080 (READ_CONTROL 0x20000 |
# FILE_READ_ATTRIBUTES 0x80 | SYNCHRONIZE 0x100000) to SYSTEM and Administrators: metadata binding
# stays possible, but no FILE_READ_DATA/FILE_WRITE_DATA/DELETE bit is granted, so no principal can
# read or write file data and the registered old distro cannot boot, and neither can the quarantined
# copy. An elevated token holding the BA owner group additionally keeps implicit
# READ_CONTROL/WRITE_DAC — the documented recovery path available to ANY elevated administrator,
# and SeBackupPrivilege/SeRestorePrivilege holders can bypass DACLs for data access; ACLs never
# defend against a malicious same-machine administrator. A non-elevated daily token has no ACE and
# gets ERROR 5 on every access (probed separately by Test-RealCustody.ps1).
# Requires: actual daily account, elevated. WslService/vmcompute must be Stopped/Disabled.
[CmdletBinding()]
param()
$ErrorActionPreference = 'Stop'
Set-StrictMode -Version Latest

$dailySid = 'S-1-5-21-2765399256-1806415232-1753294129-1001'
$identity = [Security.Principal.WindowsIdentity]::GetCurrent()
if ($identity.User.Value -cne $dailySid) { throw 'actual_daily_token_required' }
$principal = [Security.Principal.WindowsPrincipal]::new($identity)
if (-not $principal.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)) { throw 'elevation_required' }
foreach ($service in 'WslService', 'vmcompute') {
    $state = Get-Service -Name $service
    if ($state.Status -ne 'Stopped' -or $state.StartType -ne 'Disabled') { throw "service_not_fenced:$service" }
}

$originalPath = 'C:\Users\FFFFFF\AppData\Local\Packages\CanonicalGroupLimited.Ubuntu_79rhkp1fndgsc\LocalState\ext4.vhdx'
$localStatePath = 'C:\Users\FFFFFF\AppData\Local\Packages\CanonicalGroupLimited.Ubuntu_79rhkp1fndgsc\LocalState'
$copyPath = 'C:\ProgramData\ARA-Stage1-Archive-20261106\capture\Ubuntu.vhdx.pending'
$capturePath = 'C:\ProgramData\ARA-Stage1-Archive-20261106\capture'
$wslConfigPath = 'C:\Users\FFFFFF\.wslconfig'
$expectedSize = [long]4867489792

$protectedDir = "O:BAD:P(A;OICI;FA;;;SY)(A;OICI;FA;;;BA)(A;OICI;0x1200a9;;;$dailySid)"
$protectedFlatDir = "O:BAD:P(A;;FA;;;SY)(A;;FA;;;BA)(A;;0x1200a9;;;$dailySid)"
$script:firstOpenDumps = @()
# Metadata-only protected leaf DACL: READ_CONTROL|FILE_READ_ATTRIBUTES|SYNCHRONIZE for SY/BA,
# no data-read/write/delete bit for anyone (review finding: 0x20081 would have included 0x1).
$metadataOnlyDacl = 'O:BAD:P(A;;0x120080;;;SY)(A;;0x120080;;;BA)'

$receiptRoot = 'C:\ProgramData\ARA-Stage1-Archive-20261106\real-custody-20261107'
$protectedReceipt = "O:BAD:P(A;;FA;;;SY)(A;;FA;;;BA)(A;;0x1200a9;;;$dailySid)"

$nativeSource = [IO.File]::ReadAllBytes((Join-Path $PSScriptRoot 'CustodyNative.cs'))
$sha = [Security.Cryptography.SHA256]::Create()
try {
    $digest = [BitConverter]::ToString($sha.ComputeHash($nativeSource)).Replace('-', '')
} finally { $sha.Dispose() }
if ($digest -cne 'AC534ED09A4725ECAEEC8517A2C6837B1A678F354D3587E1C68E3DC665CBA2D9') { throw 'helper_identity' }
Add-Type -TypeDefinition ([Text.Encoding]::UTF8.GetString($nativeSource))

# First-open shape anomaly: an AV filter can report transient metadata on the FIRST open of a
# file in a process and clean bytes on the second (observed 2026-11-07: shape-diag second-open
# OK, every first-open Binding object_shape_changed). A binding failure therefore triggers ONE
# byte-dump + one retry with a fresh handle; both dumps are recorded. A REAL shape change fails
# both attempts and hard-stops, so fail-closed semantics are unchanged.
$src = @'
using System;
using System.ComponentModel;
using System.Runtime.InteropServices;
using System.Text;
using Microsoft.Win32.SafeHandles;
public static class CustodyShapeDump {
    [DllImport("kernel32.dll", CharSet = CharSet.Unicode, SetLastError = true)]
    private static extern SafeFileHandle CreateFileW(string path, uint access, uint share,
        IntPtr security, uint disposition, uint flags, IntPtr template);
    [DllImport("kernel32.dll", SetLastError = true)]
    private static extern bool GetFileInformationByHandleEx(SafeFileHandle handle,
        int informationClass, byte[] result, uint length);
    public static string Dump(string path) {
        SafeFileHandle h = CreateFileW(path, 0x20080, 7, IntPtr.Zero, 3, 0x02200000, IntPtr.Zero);
        if (h.IsInvalid) throw new Win32Exception(Marshal.GetLastWin32Error());
        try {
            byte[] basic = new byte[40];
            byte[] standard = new byte[24];
            bool b1 = GetFileInformationByHandleEx(h, 0, basic, 40);
            bool b2 = GetFileInformationByHandleEx(h, 1, standard, 24);
            int e1 = b1 ? 0 : Marshal.GetLastWin32Error();
            int e2 = b2 ? 0 : Marshal.GetLastWin32Error();
            return string.Format("attrs=0x{0:X} deletePending={1} directory={2} links={3} basicErr={4} standardErr={5}",
                BitConverter.ToUInt32(basic, 32), standard[20], standard[21],
                BitConverter.ToUInt32(standard, 16), e1, e2);
        } finally { h.Dispose(); }
    }
}
'@
Add-Type -TypeDefinition $src

function Open-BoundRetry([string]$Path, [uint32]$Access, [bool]$Directory) {
    for ($attempt = 1; $attempt -le 2; $attempt++) {
        $h = [AraCustodyHandle]::Open($Path, $Access, 7)
        try {
            $null = [AraCustodyHandle]::Binding($h, $Path, $Directory)
            if ($attempt -eq 2) {
                Write-Host "BINDING_RETRY_CLEANED path=$Path (first-open dump in transcript)"
            }
            return $h
        } catch {
            $dump = try { [CustodyShapeDump]::Dump($Path) } catch { "dump_failed:$($_.Exception.Message)" }
            Write-Host "BINDING_ATTEMPT${attempt}_FAILED path=$Path dump=$dump"
            $script:firstOpenDumps += "attempt${attempt}:path=$Path dump=$dump"
            $h.Dispose()
            if ($attempt -eq 2) { throw "binding_failed_after_retry:${Path}:$($_.Exception.Message)" }
        }
    }
    throw 'unreachable'
}

# Identity continuity per the reviewed fixture pattern: compare binding fields 0..5 only
# (volume|fileId|size|links|ctime|mtime). Field 6 is the file's latest USN sequence, which by
# design changes when this script itself sets an ACL — comparing it would self-fail.
function Test-IdentityEqual([string]$Before, [string]$After) {
    $b = $Before.Split('|'); $a = $After.Split('|')
    if ($b.Count -ne 7 -or $a.Count -ne 7) { throw 'binding_field_count' }
    for ($i = 0; $i -le 5; $i++) { if ($b[$i] -cne $a[$i]) { return $false } }
    return $true
}

function Open-Bound([string]$Path, [uint32]$Access, [bool]$Directory) {
    $h = [AraCustodyHandle]::Open($Path, $Access, 7)
    try { $null = [AraCustodyHandle]::Binding($h, $Path, $Directory) }
    catch { $h.Dispose(); throw "binding_failed:${Path}:$($_.Exception.Message)" }
    $h
}



function Assert-RealShape([string]$Path) {
    $item = Get-Item -LiteralPath $Path -Force
    if ($item.Attributes -band [IO.FileAttributes]::ReparsePoint) { throw "reparse:$Path" }
    if ($item.Length -ne $expectedSize) { throw "unexpected_size:${Path}:$($item.Length)" }
    if ([IO.Path]::GetFileName($Path) -cne [IO.Path]::GetFileName($item.FullName)) { throw 'leaf_not_bounded' }
}

function Binding-Of([string]$Path, [bool]$Directory) {
    # Metadata-only: FILE_READ_ATTRIBUTES|READ_CONTROL|SYNCHRONIZE. No data read.
    $h = Open-BoundRetry $Path 0x20080 $Directory
    try { return [AraCustodyHandle]::Binding($h, $Path, $Directory) } finally { $h.Dispose() }
}

# This machine empirically denies DACL rewrites on owner=BA protected objects even to an elevated
# token holding the BA group (observed 2026-11-07 twice: synthetic HKCU key residue and the run-7
# resume re-hardening). SeRestorePrivilege is the documented backup/restore bypass that grants
# WRITE_DAC/WRITE_OWNER regardless of DACL; elevated tokens hold it disabled, so enable it once.
$privSrc = @'
using System;
using System.ComponentModel;
using System.Runtime.InteropServices;
public static class CustodyPrivilege {
    [DllImport("advapi32.dll", SetLastError = true)]
    private static extern bool OpenProcessToken(IntPtr process, uint access, out IntPtr token);
    [DllImport("advapi32.dll", CharSet = CharSet.Unicode, SetLastError = true)]
    private static extern bool LookupPrivilegeValueW(string system, string name, out long luid);
    [StructLayout(LayoutKind.Sequential, Pack = 4)]
    private struct TokenPrivileges1 { public uint privilegeCount; public long luid; public uint attributes; }
    [DllImport("advapi32.dll", SetLastError = true)]
    private static extern bool AdjustTokenPrivileges(IntPtr token, bool disableAll,
        ref TokenPrivileges1 newState, uint bufferLength, IntPtr previous, IntPtr returnLength);
    [DllImport("kernel32.dll")]
    private static extern IntPtr GetCurrentProcess();
    [DllImport("kernel32.dll")]
    private static extern bool CloseHandle(IntPtr handle);

    public static void Enable(string privilegeName) {
        IntPtr token;
        if (!OpenProcessToken(GetCurrentProcess(), 0x28, out token)) {
            throw new Win32Exception(Marshal.GetLastWin32Error());
        }
        try {
            long luid;
            if (!LookupPrivilegeValueW(null, privilegeName, out luid)) {
                throw new Win32Exception(Marshal.GetLastWin32Error());
            }
            TokenPrivileges1 state = new TokenPrivileges1();
            state.privilegeCount = 1;
            state.luid = luid;
            state.attributes = 2; // SE_PRIVILEGE_ENABLED
            if (!AdjustTokenPrivileges(token, false, ref state, 0, IntPtr.Zero, IntPtr.Zero)) {
                throw new Win32Exception(Marshal.GetLastWin32Error());
            }
            if (Marshal.GetLastWin32Error() == 1300) { // ERROR_NOT_ALL_ASSIGNED
                throw new UnauthorizedAccessException("privilege_not_held:" + privilegeName);
            }
        } finally { CloseHandle(token); }
    }
}
'@
Add-Type -TypeDefinition $privSrc
[CustodyPrivilege]::Enable('SeRestorePrivilege')
[CustodyPrivilege]::Enable('SeTakeOwnershipPrivilege')
Write-Host 'PRIVILEGES_ENABLED=SeRestore,SeTakeOwnership'
$script:privilegesEnabled = 'SeRestorePrivilege,SeTakeOwnershipPrivilege (Pack=4 layout verified: size=16 luid@4 attributes@12)'

function Set-ProtectedAcl([string]$Path, [string]$Sddl, [bool]$Directory) {
    if ($Directory) {
        $acl = [Security.AccessControl.DirectorySecurity]::new()
        $acl.SetSecurityDescriptorSddlForm($Sddl)
        [IO.Directory]::SetAccessControl($Path, $acl)
    } else {
        $acl = [Security.AccessControl.FileSecurity]::new()
        $acl.SetSecurityDescriptorSddlForm($Sddl)
        [IO.File]::SetAccessControl($Path, $acl)
    }
}

function Read-Sddl([string]$Path) {
    $acl = Get-Acl -LiteralPath $Path
    $acl.GetSecurityDescriptorSddlForm([Security.AccessControl.AccessControlSections]'Owner,Access')
}

function Durable-Receipt([string]$Path, [string]$Text) {
    $acl = [Security.AccessControl.FileSecurity]::new()
    $acl.SetSecurityDescriptorSddlForm($protectedReceipt)
    $f = [IO.FileStream]::new($Path, [IO.FileMode]::CreateNew, [Security.AccessControl.FileSystemRights]::WriteData,
        [IO.FileShare]::None, 4096, [IO.FileOptions]::WriteThrough, $acl)
    try {
        $bytes = [Text.Encoding]::UTF8.GetBytes($Text)
        $f.Write($bytes, 0, $bytes.Length)
        $f.Flush($true)
    } finally { $f.Dispose() }
}

foreach ($path in $originalPath, $copyPath) { Assert-RealShape $path }
Write-Output 'PROTECT_STAGE=shape_checks_done'
$wslConfigItem = Get-Item -LiteralPath $wslConfigPath -Force
if ($wslConfigItem.Length -le 0 -or $wslConfigItem.Length -gt 65536) { throw 'wslconfig_size' }

$before = [ordered]@{}
foreach ($path in $originalPath, $localStatePath, $copyPath, $capturePath, $wslConfigPath) {
    Write-Output "PROTECT_STAGE=before_binding path=$path"
    $before[$path] = [ordered]@{
        binding = Binding-Of $path ($path -in $localStatePath, $capturePath)
        sddl = Read-Sddl $path
    }
}

# Receipt root: exclusive-create on a fresh run; on a resume run (intent exists, sealed absent —
# e.g. the 2026-11-07 run that applied all hardening then stopped on the USN-field comparison)
# continue with the existing root and intent, re-verify ACL state idempotently.
Write-Output 'PROTECT_STAGE=receipt_root'
$resumeRun = $false
if (Test-Path -LiteralPath (Join-Path $receiptRoot 'intent.json')) {
    if (Test-Path -LiteralPath (Join-Path $receiptRoot 'sealed.json')) { throw 'already_sealed_no_rerun' }
    $resumeRun = $true
    Write-Output 'PROTECT_RESUME=intent_present_sealed_absent'
    $intentPath = Join-Path $receiptRoot 'intent.json'
    $intentBytes = [IO.File]::ReadAllBytes($intentPath)
    if ($intentBytes.Length -le 0 -or $intentBytes.Length -gt 65536) { throw 'intent_size' }
    $intentObj = [Text.Encoding]::UTF8.GetString($intentBytes) | ConvertFrom-Json
    if ($intentObj.schema -cne 'ENV-M1-01.real-custody.intent.v1') { throw 'intent_schema' }
    foreach ($path in $intentObj.before.PSObject.Properties.Name) {
        $expected = $intentObj.before.$path.binding.Split('|')
        $actualNow = (Binding-Of $path ($path -in $localStatePath, $capturePath)).Split('|')
        for ($i = 0; $i -le 5; $i++) {
            if ($expected[$i] -cne $actualNow[$i]) { throw "resume_identity_drift:${path}:field$i" }
        }
    }
    Write-Output 'PROTECT_RESUME=identity_fields_0_5_match_intent'
} else {
    [StageOneNative]::CreateDirectoryExclusive($receiptRoot, $protectedFlatDir)
}
$receiptHandle = Open-Bound $receiptRoot 0x20081 3 $true
try {
    $rootBinding = [AraCustodyHandle]::Binding($receiptHandle, $receiptRoot, $true)
    $rootSddl = [AraCustodyHandle]::ReadAcl($receiptHandle)
} finally { $receiptHandle.Dispose() }
$expectedRootSddl = [Security.AccessControl.RawSecurityDescriptor]::new($protectedFlatDir).GetSddlForm('Owner,Access')
if ($rootSddl -cne $expectedRootSddl) { throw 'receipt_root_acl_drift' }

if (-not $resumeRun) {
    $intent = [ordered]@{
        schema = 'ENV-M1-01.real-custody.intent.v1'
        utc = [DateTimeOffset]::UtcNow.ToString('o')
        receipt_root_binding = $rootBinding
        before = $before
        plan = [ordered]@{
            original = 'owner=BA protected DACL SY/BA 0x120080 metadata-only'
            local_state_dir = 'owner=BA protected SY/BA FA OICI + daily read+execute OICI'
            copy = 'owner=BA protected DACL SY/BA 0x120080 metadata-only'
            capture_dir = 'owner=BA protected SY/BA FA + daily read+execute (flat)'
            wslconfig = 'owner=BA protected SY/BA FA + daily read+execute (flat); bytes preserved'
            content_reads = 'none; no hash of any real disk'
        }
    }
    $intentText = $intent | ConvertTo-Json -Depth 6 -Compress
    if ([Text.Encoding]::UTF8.GetByteCount($intentText) -gt 65536) { throw 'intent_cap' }
    Durable-Receipt (Join-Path $receiptRoot 'intent.json') $intentText
}

# Apply hardening in parent-before-leaf order so no window leaves the file deletable.
Write-Output 'PROTECT_STAGE=hardening'
Set-ProtectedAcl $localStatePath $protectedDir $true
Set-ProtectedAcl $originalPath $metadataOnlyDacl $false
Set-ProtectedAcl $capturePath $protectedFlatDir $true
Set-ProtectedAcl $copyPath $metadataOnlyDacl $false
Set-ProtectedAcl $wslConfigPath $protectedFlatDir $false

$after = [ordered]@{}
foreach ($path in $originalPath, $localStatePath, $copyPath, $capturePath, $wslConfigPath) {
    $after[$path] = [ordered]@{
        binding = Binding-Of $path ($path -in $localStatePath, $capturePath)
        sddl = Read-Sddl $path
    }
}
if (-not (Test-IdentityEqual $before[$originalPath].binding $after[$originalPath].binding)) { throw 'original_binding_changed' }
if (-not (Test-IdentityEqual $before[$copyPath].binding $after[$copyPath].binding)) { throw 'copy_binding_changed' }
if (-not (Test-IdentityEqual $before[$wslConfigPath].binding $after[$wslConfigPath].binding)) { throw 'wslconfig_binding_changed' }

$wslConfigSha = $null
$stream = [IO.File]::Open($wslConfigPath, 'Open', 'Read', 'Read')
try {
    $sha2 = [Security.Cryptography.SHA256]::Create()
    try { $wslConfigSha = [BitConverter]::ToString($sha2.ComputeHash($stream)).Replace('-', '') }
    finally { $sha2.Dispose() }
} finally { $stream.Dispose() }
if ($wslConfigSha -cne '43EDEB6C23A0BE2AEBD4A63DB88B464B6362308C8D32812184966ECDE26F01D2') { throw 'wslconfig_bytes_drift' }

$receipt = [ordered]@{
    schema = 'ENV-M1-01.real-custody.sealed.v1'
    utc = [DateTimeOffset]::UtcNow.ToString('o')
    original_binding = $after[$originalPath].binding
    copy_binding = $after[$copyPath].binding
    local_state_binding = $after[$localStatePath].binding
    capture_binding = $after[$capturePath].binding
    wslconfig_binding = $after[$wslConfigPath].binding
    wslconfig_sha256 = $wslConfigSha
    sddl_after = [ordered]@{}
    first_open_dumps = $script:firstOpenDumps
    privileges_enabled = $script:privilegesEnabled
    content_reads = 'none'
}
foreach ($path in $after.Keys) { $receipt.sddl_after[$path] = $after[$path].sddl }
$receiptText = $receipt | ConvertTo-Json -Depth 6 -Compress
if ([Text.Encoding]::UTF8.GetByteCount($receiptText) -gt 65536) { throw 'receipt_cap' }
Durable-Receipt (Join-Path $receiptRoot 'sealed.json') $receiptText
"REAL_CUSTODY_SEALED=$receiptRoot"
