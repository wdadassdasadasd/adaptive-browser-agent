# Ordinary-principal refusal probes for the two real stage-one VHDX objects.
# Runs as the actual daily account, NOT elevated. Reads no file content; every probe below
# must fail with a Windows access-denied class error. Refuses to pass if any access succeeds.
[CmdletBinding()]
param()
$ErrorActionPreference = 'Stop'
Set-StrictMode -Version Latest

$dailySid = 'S-1-5-21-2765399256-1806415232-1753294129-1001'
$identity = [Security.Principal.WindowsIdentity]::GetCurrent()
if ($identity.User.Value -cne $dailySid) { throw 'actual_daily_token_required' }
$principal = [Security.Principal.WindowsPrincipal]::new($identity)
if ($principal.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)) { throw 'must_not_elevate' }

$nativeSource = [IO.File]::ReadAllBytes((Join-Path $PSScriptRoot 'CustodyNative.cs'))
$sha = [Security.Cryptography.SHA256]::Create()
try {
    $digest = [BitConverter]::ToString($sha.ComputeHash($nativeSource)).Replace('-', '')
} finally { $sha.Dispose() }
if ($digest -cne 'AC534ED09A4725ECAEEC8517A2C6837B1A678F354D3587E1C68E3DC665CBA2D9') { throw 'helper_identity' }
Add-Type -TypeDefinition ([Text.Encoding]::UTF8.GetString($nativeSource))

$originalPath = 'C:\Users\FFFFFF\AppData\Local\Packages\CanonicalGroupLimited.Ubuntu_79rhkp1fndgsc\LocalState\ext4.vhdx'
$localStatePath = 'C:\Users\FFFFFF\AppData\Local\Packages\CanonicalGroupLimited.Ubuntu_79rhkp1fndgsc\LocalState'
$copyPath = 'C:\ProgramData\ARA-Stage1-Archive-20261106\capture\Ubuntu.vhdx.pending'
$capturePath = 'C:\ProgramData\ARA-Stage1-Archive-20261106\capture'
$wslConfigPath = 'C:\Users\FFFFFF\.wslconfig'

function Expect-Denied([string]$Case, [scriptblock]$Action) {
    try { & $Action }
    catch {
        $err = $_.Exception
        while ($null -ne $err) {
            if ($err -is [ComponentModel.Win32Exception]) {
                if ($err.NativeErrorCode -ne 5) { throw "unexpected_win32:${Case}:$($err.NativeErrorCode)" }
                "DENIED $Case win32=5"
                return
            }
            # .NET Framework maps ERROR_ACCESS_DENIED to UnauthorizedAccessException (0x80070005).
            if ($err -is [UnauthorizedAccessException] -and ($err.HResult -band 0xFFFF) -eq 5) {
                "DENIED $Case unauthorized=0x80070005"
                return
            }
            $err = $err.InnerException
        }
        throw "no_access_denied_error:$Case"
    }
    throw "unexpected_success:$Case"
}

$denied = 0
$probeCases = [ordered]@{
    original_read_data    = { $p = [AraCustodyHandle]::Open($originalPath, 1, 7); $p.Dispose() }
    original_write_data   = { $p = [AraCustodyHandle]::Open($originalPath, 2, 0); $p.Dispose() }
    original_append       = { $p = [AraCustodyHandle]::Open($originalPath, 4, 0); $p.Dispose() }
    original_read_attrs   = { $p = [AraCustodyHandle]::Open($originalPath, 0x80, 7); $p.Dispose() }
    original_delete       = { $p = [AraCustodyHandle]::Open($originalPath, 0x10000, 7); $p.Dispose() }
    original_write_dacl   = { $p = [AraCustodyHandle]::Open($originalPath, 0x40000, 7); $p.Dispose() }
    original_write_owner  = { $p = [AraCustodyHandle]::Open($originalPath, 0x80000, 7); $p.Dispose() }
    copy_read_data        = { $p = [AraCustodyHandle]::Open($copyPath, 1, 7); $p.Dispose() }
    copy_write_data       = { $p = [AraCustodyHandle]::Open($copyPath, 2, 0); $p.Dispose() }
    copy_read_attrs       = { $p = [AraCustodyHandle]::Open($copyPath, 0x80, 7); $p.Dispose() }
    copy_delete           = { $p = [AraCustodyHandle]::Open($copyPath, 0x10000, 7); $p.Dispose() }
    copy_write_dacl       = { $p = [AraCustodyHandle]::Open($copyPath, 0x40000, 7); $p.Dispose() }
    localstate_delete_child = { $p = [AraCustodyHandle]::Open($localStatePath, 0x40, 7); $p.Dispose() }
    localstate_add_file   = { $p = [AraCustodyHandle]::Open($localStatePath, 2, 7); $p.Dispose() }
    localstate_add_subdir = { $p = [AraCustodyHandle]::Open($localStatePath, 4, 7); $p.Dispose() }
    localstate_write_dacl = { $p = [AraCustodyHandle]::Open($localStatePath, 0x40000, 7); $p.Dispose() }
    capture_delete_child  = { $p = [AraCustodyHandle]::Open($capturePath, 0x40, 7); $p.Dispose() }
    capture_add_file      = { $p = [AraCustodyHandle]::Open($capturePath, 2, 7); $p.Dispose() }
    wslconfig_write_data  = { $p = [AraCustodyHandle]::Open($wslConfigPath, 2, 0); $p.Dispose() }
}
foreach ($case in $probeCases.Keys) {
    Expect-Denied $case $probeCases[$case]
    $denied++
}

# .wslconfig delete-open is EXPECTED to succeed: the profile root still grants the daily user
# FILE_DELETE_CHILD, the documented alternative deletion path. This is a recorded residual, not a
# gap for the custody targets (both VHDX parents are hardened and deny it). The file's protection
# goal is byte integrity — write is denied above and its SHA256 is anchored in sealed.json.
try {
    $h = [AraCustodyHandle]::Open($wslConfigPath, 0x10000, 7)
    $h.Dispose()
    "ALLOWED wslconfig_delete (documented parent FILE_DELETE_CHILD alternative; bytes anchored in sealed.json)"
} catch {
    throw "wslconfig_delete_now_denied_unexpectedly"
}

# File-system level probes through normal Win32 APIs. Open-style probes only: a successful
# Copy/ReadAllText probe against a broken protection would exfiltrate ~4.9 GB before failing.
Expect-Denied 'original_delete_file_api' { [IO.File]::Delete($originalPath) }
Expect-Denied 'original_open_read_api' { $s = [IO.File]::Open($originalPath, 'Open', 'Read', 'Read'); $s.Dispose() }
Expect-Denied 'copy_open_read_api' { $s = [IO.File]::Open($copyPath, 'Open', 'Read', 'Read'); $s.Dispose() }
Expect-Denied 'original_open_write_api' { $s = [IO.File]::Open($originalPath, 'Open', 'Write', 'None'); $s.Dispose() }
$denied += 4

# Metadata continuity visible to the ordinary principal: directory index listing only
# (FindFirstFile metadata from the parent; the file itself is never opened).
$originalView = @(Get-ChildItem -LiteralPath $localStatePath -Force -Filter 'ext4.vhdx')
$copyView = @(Get-ChildItem -LiteralPath $capturePath -Force -Filter 'Ubuntu.vhdx.pending')
if ($originalView.Count -ne 1 -or $copyView.Count -ne 1) { throw 'ordinary_listing_shape' }
if ($originalView[0].Length -ne 4867489792 -or $copyView[0].Length -ne 4867489792) { throw 'ordinary_size_view_drift' }
"REAL_CUSTODY_REFUSALS_OK count=$denied; ordinary_index_view=both_4867489792"
