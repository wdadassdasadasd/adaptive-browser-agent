# Synthetic qualification for the B-direction integrity read primitive.
# Small public synthetic fixtures only; never touches real originals, VMs, services or network.
[CmdletBinding()]
param([ValidatePattern('^[a-z][a-z0-9-]{0,15}$')][string]$Run = 'run01')
$ErrorActionPreference = 'Stop'
Set-StrictMode -Version Latest
Import-Module (Join-Path $PSScriptRoot 'IntegrityRead.psm1') -Force
Initialize-IntegrityNative
$sid = [Security.Principal.WindowsIdentity]::GetCurrent().User.Value
$priv = [AraIntegrityReadNative]::PrivilegeState([AraIntegrityReadNative]::BackupPrivilegeName)
$held = $priv[0]
$base = 'D:\adaptive-browser-agent\.tmp\integrity-fixtures-20261107'
$case = Join-Path $base $Run
if (Test-Path -LiteralPath $case) { throw 'integrity_fixture_case_exists_no_overwrite' }
New-Item -ItemType Directory -Path $case -Force | Out-Null
$count = 0; $skips = 0

function New-Synthetic([string]$Name, [int]$Bytes, [bool]$Protected, [ref]$ExpectedHash) {
    $p = Join-Path $case $Name
    $acl = [Security.AccessControl.FileSecurity]::new()
    $acl.SetSecurityDescriptorSddlForm("O:${sid}D:P(A;;FA;;;$sid)(A;;FA;;;SY)")
    $fs = [IO.FileStream]::new($p, [IO.FileMode]::CreateNew, [Security.AccessControl.FileSystemRights]::WriteData,
        [IO.FileShare]::Read, 4096, [IO.FileOptions]::WriteThrough, $acl)
    try {
        if ($Bytes -gt 0) {
            $buf = New-Object byte[] $Bytes
            $rng = [Random]::new(20261107)
            $rng.NextBytes($buf)
            $sha = [Security.Cryptography.SHA256]::Create()
            try { $ExpectedHash.Value = ([BitConverter]::ToString($sha.ComputeHash($buf)) -replace '-', '').ToLowerInvariant() } finally { $sha.Dispose() }
            $fs.Write($buf, 0, $buf.Length); $fs.Flush($true)
        } else {
            $ExpectedHash.Value = 'e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855'
        }
    } finally { $fs.Dispose() }
    if ($Protected) {
        # Swap DACL via icacls: user keeps read-attributes only, SYSTEM full. .NET SetAccessControl
        # would demand SeSecurityPrivilege for the SACL section it marks present.
        $out = & icacls $p /inheritance:r /grant:r "*${sid}:(RA)" /grant:r "SYSTEM:(F)" 2>&1
        if ($LASTEXITCODE -ne 0) { Write-Output ($out | Out-String); throw 'fixture_dacl_swap_failed' }
    }
    return $p
}

function Pass([string]$Name, [string]$Detail = '') {
    $script:count++; if ($Detail) { Write-Output "PASS=$Name $Detail" } else { Write-Output "PASS=$Name" } }
function Skip([string]$Name) { $script:skips++; Write-Output "SKIP=$NAME REASON=SeBackupPrivilege_not_held_elevation_required" }
function Expect-Failure([string]$Name, [scriptblock]$Action, [string]$Pattern) {
    try { & $Action | Out-Null; throw "expected_failure_missing:$Name" }
    catch { if ($_.Exception.ToString() -notmatch $Pattern) { Write-Output "UNEXPECTED_STACK=$($_.ScriptStackTrace)"; throw } }
    Pass $Name
}
function Expect-SharingRefusal([string]$Name, [scriptblock]$Action) {
    try { & $Action | Out-Null; throw "expected_sharing_failure_missing:$Name" }
    catch {
        $error = $_.Exception
        while ($null -ne $error.InnerException) { $error = $error.InnerException }
        $code = $error.HResult -band 0xffff
        if ($code -ne 32) { Write-Output "UNEXPECTED_SHARING_ERROR=$code STACK=$($_.ScriptStackTrace)"; throw }
    }
    Pass $Name 'WIN32=32'
}

$hashNormal = [ref]''
$hashBig = [ref]''
$hashProtected = [ref]''
$hashEmpty = [ref]''
$normal = New-Synthetic 'normal-3mib.bin' 3145728 $false $hashNormal
$big = New-Synthetic 'big-64mib.bin' 67108864 $false $hashBig
$protected = New-Synthetic 'protected-1mib.bin' 1048576 $true $hashProtected
$empty = New-Synthetic 'protected-empty.bin' 0 $true $hashEmpty

# T01: manual bound-stream hash equals Get-FileHash on a normal synthetic file.
$expected1 = (Get-FileHash -LiteralPath $normal -Algorithm SHA256).Hash.ToLowerInvariant()
$h = [AraIntegrityReadNative]::OpenBound($normal)
try {
    $calls = 0; $read = [long]0
    $got = [AraIntegrityReadNative]::StreamHash($h, 4867489792, 60000, [ref]$calls, [ref]$read)
} finally { $h.Dispose() }
if ($got -ne $expected1 -or $got -ne $hashNormal.Value) { throw 'T01_hash_mismatch' }
Pass 'T01_bound_stream_hash_matches' ("calls=$calls bytes=$read")

# T02: binding refusal at the PS pre-check layer (no privilege, no data access).
Expect-Failure 'T02_binding_refuse_wrong_fileindex' {
    $other = [AraIntegrityReadNative]::OpenMetadata($big)
    try { $otherId = [AraIntegrityReadNative]::ReadIdentity($other) } finally { $other.Dispose() }
    Invoke-BoundIntegrityRead -Path $normal -ExpectedFileIndex $otherId.FileIndex -DeadlineMs 60000 | Out-Null
} 'integrity_binding_refuse'

# T03: FileShare.Read on the bound handle excludes write/delete/attributes writers.
$h = [AraIntegrityReadNative]::OpenBound($normal)
try {
    Expect-SharingRefusal 'T03a_write_refusal' { [IO.File]::Open($normal, 'Open', 'Write', 'Read').Dispose() }
    Expect-SharingRefusal 'T03b_delete_refusal' { [IO.File]::Delete($normal) }
    Expect-SharingRefusal 'T03c_settime_refusal' { (Get-Item -LiteralPath $normal -Force).LastWriteTimeUtc = [DateTime]::UtcNow }
    $calls = 0; $read = [long]0
    $mid = [AraIntegrityReadNative]::StreamHash($h, 4867489792, 60000, [ref]$calls, [ref]$read)
    $after = [AraIntegrityReadNative]::ReadIdentity($h)
} finally { $h.Dispose() }
if ($mid -ne $expected1) { throw 'T03_midstream_hash_mismatch' }
Pass 'T03d_hash_on_shared_handle_ok'

# T04: absolute deadline stops the stream; no partial success is reported.
Expect-Failure 'T04_deadline_stops_stream' {
    $h = [AraIntegrityReadNative]::OpenBound($big)
    try {
        $calls = 0; $read = [long]0
        [AraIntegrityReadNative]::StreamHash($h, 4867489792, 1, [ref]$calls, [ref]$read) | Out-Null
    } finally { $h.Dispose() }
} 'integrity_deadline_exceeded'

# T05: privilege lifecycle + protected-ACL bypass + same-handle identity recheck (orchestrated ReadBound).
if ($held) {
    $r = [AraIntegrityReadNative]::ReadBound($protected, 4867489792, 1048576, 0, -1, 60000)
    if (-not $r.Ok) { Write-Output ("READBOUND_ERROR={0} WIN32={1}" -f $r.ErrorKind, $r.Win32Error); throw 'T05_readbound_failed' }
    if ($r.Sha256 -ne $hashProtected.Value) { throw 'T05_hash_mismatch' }
    if ($r.PrivilegeEnabledBefore) { throw 'T05_before_not_disabled' }
    if (-not $r.PrivilegeEnabledDuring) { throw 'T05_during_not_enabled' }
    if ($r.PrivilegeEnabledAfter) { throw 'T05_after_still_enabled' }
    if (-not $r.PrivilegeRestoreVerified) { throw 'T05_restore_unverified' }
    if ($r.Before.FileIndex -ne $r.After.FileIndex -or $r.Before.Size -ne $r.After.Size -or
        $r.Before.VolumeSerial -ne $r.After.VolumeSerial -or
        $r.Before.CreationFileTime -ne $r.After.CreationFileTime -or
        $r.Before.LastWriteFileTime -ne $r.After.LastWriteFileTime) { throw 'T05_binding_drift_after_read' }
    Pass 'T05_privilege_lifecycle_and_bypass' ("calls=$($r.ReadCalls) ms=$($r.ElapsedMs)")
    $re = [AraIntegrityReadNative]::ReadBound($empty, 4867489792, 0, 0, -1, 60000)
    if (-not $re.Ok -or $re.Sha256 -ne $hashEmpty.Value) { throw 'T06_empty_protected_failed' }
    Pass 'T06_metadata_only_zero_byte_hash'
} else {
    Skip 'T05_privilege_lifecycle_and_bypass'
    Skip 'T06_metadata_only_zero_byte_hash'
}

# T07: bound open with privilege DISABLED is denied on the protected synthetic (proves privilege is required).
# Win32 code 5 check only - never match localized error text.
try { [AraIntegrityReadNative]::OpenBound($protected).Dispose(); throw 'T07_denial_missing' }
catch {
    $winErr = $_.Exception
    while ($null -ne $winErr.InnerException -and $winErr -isnot [ComponentModel.Win32Exception]) {
        $winErr = $winErr.InnerException
    }
    if ($winErr -is [ComponentModel.Win32Exception]) { $code = $winErr.NativeErrorCode }
    else { $code = $winErr.HResult -band 0xffff }
    if ($code -ne 5) { Write-Output "UNEXPECTED_DENIAL_CODE=$code STACK=$($_.ScriptStackTrace)"; throw }
    Pass 'T07_protected_denied_without_enabled_privilege' 'WIN32=5'
}

# T08: receipt is exclusive (no overwrite), capped, no body.
$receipt = Join-Path $case 'receipts\synthetic.receipt.json'
New-Item -ItemType Directory -Path (Join-Path $case 'receipts') -Force | Out-Null
$res = New-Object AraBoundReadResult
$res.Ok = $true; $res.Sha256 = $hashNormal.Value; $res.BytesRead = 3145728; $res.ElapsedMs = 12; $res.ReadCalls = 3
$res.PrivilegePresent = $held; $res.PrivilegeRestoreVerified = $true
$idb = New-Object AraIdentity; $idb.VolumeSerial = 7; $idb.FileIndex = 42; $idb.Size = 3145728
$idb.CreationFileTime = 134000000000000000; $idb.LastWriteFileTime = 134000000000000001
$res.Before = $idb; $res.After = $idb
Write-IntegrityReceipt -ReceiptPath $receipt -Result $res
Expect-Failure 'T08_receipt_no_overwrite' {
    Write-IntegrityReceipt -ReceiptPath $receipt -Result $res
} 'integrity_receipt_exists_no_overwrite'
$raw = Get-Content -LiteralPath $receipt -Raw
$json = $raw | ConvertFrom-Json
if ($json.body_stored -ne $false) { throw 'T09_body_stored_true' }
if ($json.identity_before.size -ne 3145728) { throw 'T09_identity_missing' }
if (-not $json.privilege.restore_verified) { throw 'T09_privilege_block_missing' }
if ([Text.Encoding]::UTF8.GetByteCount($raw) -gt 16384) { throw 'T09_receipt_over_cap' }
Pass 'T09_receipt_shape_no_body'

# T10: read does not modify ctime/mtime/size/SDDL of the synthetic (LastAccess excluded by design).
$item = Get-Item -LiteralPath $normal -Force
$beforeC = $item.CreationTimeUtc.Ticks; $beforeW = $item.LastWriteTimeUtc.Ticks
$beforeS = (Get-Acl -LiteralPath $normal).Sddl; $beforeZ = $item.Length
$h = [AraIntegrityReadNative]::OpenBound($normal)
try { $calls = 0; $read = [long]0; [AraIntegrityReadNative]::StreamHash($h, 4867489792, 60000, [ref]$calls, [ref]$read) | Out-Null } finally { $h.Dispose() }
$item2 = Get-Item -LiteralPath $normal -Force
if ($item2.CreationTimeUtc.Ticks -ne $beforeC -or $item2.LastWriteTimeUtc.Ticks -ne $beforeW -or
    $item2.Length -ne $beforeZ -or (Get-Acl -LiteralPath $normal).Sddl -ne $beforeS) { throw 'T10_metadata_modified' }
Pass 'T10_read_preserves_metadata'

# T11: locale-robust last-access fence - must accept only provably-disabled policy, fail closed otherwise.
$fsOut = (& fsutil behavior query disablelastaccess 2>&1) -join ' '
$fsDisabled = $false
foreach ($tok in @('已禁用', '已停用', 'disabled')) { if ($fsOut -match [regex]::Escape($tok)) { $fsDisabled = $true; break } }
$fsEnabled = $false
foreach ($tok in @('已启用', 'enabled')) { if ($fsOut -match [regex]::Escape($tok)) { $fsEnabled = $true; break } }
if ($fsDisabled -and -not $fsEnabled) {
    Assert-IntegrityLastAccessDisabled
    Pass 'T11_lastaccess_fence_accepts_disabled_policy'
} else {
    try { Assert-IntegrityLastAccessDisabled; throw 'T11_expected_refusal_missing' }
    catch { if ($_.Exception.Message -notmatch 'integrity_fence_lastaccess') { throw } }
    Pass 'T11_lastaccess_fence_fails_closed_current_policy'
}

Write-Output "FIXTURE_ROOT=$case"
if ($skips -gt 0) {
    Write-Output "INTEGRITY_SYNTHETIC_RESULT=PARTIAL passed=$count skipped=$skips elevation_required=1"
    exit 2
}
Write-Output "INTEGRITY_SYNTHETIC_RESULT=OK count=$count"
