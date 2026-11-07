# B-direction read-only integrity qualification module (ENV-M1-01 binding-drift decision option B).
# Synthetic-safe by default; real objects are only touched through Invoke-IntegrityRead.ps1 Real mode.
Set-StrictMode -Version Latest

$script:IntegrityNativeLoaded = $false

function Initialize-IntegrityNative {
    if ($script:IntegrityNativeLoaded) { return }
    $src = Join-Path $PSScriptRoot 'IntegrityReadNative.cs'
    if (-not (Test-Path -LiteralPath $src)) { throw 'integrity_native_source_missing' }
    Add-Type -TypeDefinition ([IO.File]::ReadAllText($src)) -ErrorAction Stop
    $script:IntegrityNativeLoaded = $true
}

# Machine constraints before any real-object read: services fenced, no guest VM processes.
# Last-access updates must be disabled so a read cannot modify the original's metadata.
function Assert-IntegrityFence {
    [CmdletBinding()]
    param()
    foreach ($name in @('WslService', 'vmcompute')) {
        $svc = Get-Service -Name $name -ErrorAction Stop
        if ($svc.Status -ne 'Stopped') { throw "integrity_fence_service_not_stopped:$name" }
        if ($svc.StartType -ne 'Disabled') { throw "integrity_fence_service_not_disabled:$name" }
    }
    foreach ($proc in @('vmmemWSL', 'wslhost')) {
        if (Get-Process -Name $proc -ErrorAction SilentlyContinue) { throw "integrity_fence_guest_process:$proc" }
    }
    $out = (& fsutil behavior query disablelastaccess 2>&1) -join ' '
    if ($out -notmatch 'updates disabled') { throw "integrity_fence_lastaccess_not_disabled:$out" }
}

# No-privilege metadata-only binding pre-check on the exact path (attributes access only).
function Get-IntegrityIdentity {
    [CmdletBinding()]
    param([Parameter(Mandatory)][string]$Path)
    Initialize-IntegrityNative
    $resolved = (Resolve-Path -LiteralPath $Path -ErrorAction Stop).Path
    $h = [AraIntegrityReadNative]::OpenMetadata($resolved)
    try { return [AraIntegrityReadNative]::ReadIdentity($h) } finally { $h.Dispose() }
}

function Invoke-BoundIntegrityRead {
    [CmdletBinding()]
    param(
        [Parameter(Mandatory)][string]$Path,
        [long]$MaxBytes = 4867489792,
        [long]$ExpectedSize = -1,
        [uint32]$ExpectedVolumeSerial = 0,
        [long]$ExpectedFileIndex = -1,
        [Parameter(Mandatory)][ValidateRange(1, 3600000)][int]$DeadlineMs,
        [string]$ReceiptPath
    )
    Initialize-IntegrityNative
    $resolved = (Resolve-Path -LiteralPath $Path -ErrorAction Stop).Path
    $pre = Get-IntegrityIdentity -Path $resolved
    if ($ExpectedSize -ge 0 -and $pre.Size -ne $ExpectedSize) { throw 'integrity_binding_refuse:pre_size' }
    if ($ExpectedVolumeSerial -ne 0 -and $pre.VolumeSerial -ne $ExpectedVolumeSerial) { throw 'integrity_binding_refuse:pre_volume' }
    if ($ExpectedFileIndex -ge 0 -and $pre.FileIndex -ne $ExpectedFileIndex) { throw 'integrity_binding_refuse:pre_fileindex' }
    $result = [AraIntegrityReadNative]::ReadBound($resolved, $MaxBytes, $ExpectedSize,
        $ExpectedVolumeSerial, $ExpectedFileIndex, $DeadlineMs)
    if ($ReceiptPath) { Write-IntegrityReceipt -ReceiptPath $ReceiptPath -Result $result }
    return $result
}

# Exclusive, length-capped, durable receipt. Schema-fixed, no file body, no overwrite ever.
function Write-IntegrityReceipt {
    [CmdletBinding()]
    param([Parameter(Mandatory)][string]$ReceiptPath, [Parameter(Mandatory)]$Result)
    if (Test-Path -LiteralPath $ReceiptPath) { throw 'integrity_receipt_exists_no_overwrite' }
    $parent = Split-Path -Parent $ReceiptPath
    if (-not $parent -or -not (Test-Path -LiteralPath $parent)) { throw 'integrity_receipt_parent_missing' }
    function Convert-Identity([object]$id) {
        if ($null -eq $id) { return $null }
        [ordered]@{
            volume_serial = [long]$id.VolumeSerial
            file_index = [long]$id.FileIndex
            size = [long]$id.Size
            creation_filetime = [long]$id.CreationFileTime
            last_write_filetime = [long]$id.LastWriteFileTime
        }
    }
    $receipt = [ordered]@{
        schema = 'ara.stage1.integrity-read/1'
        created_utc = [DateTime]::UtcNow.ToString('o')
        ok = [bool]$Result.Ok
        error_kind = $Result.ErrorKind
        win32_error = $Result.Win32Error
        identity_before = Convert-Identity $Result.Before
        identity_after = Convert-Identity $Result.After
        sha256 = $Result.Sha256
        bytes_read = [long]$Result.BytesRead
        elapsed_ms = [long]$Result.ElapsedMs
        read_calls = [int]$Result.ReadCalls
        privilege = [ordered]@{
            present = [bool]$Result.PrivilegePresent
            enabled_before = [bool]$Result.PrivilegeEnabledBefore
            enabled_during = [bool]$Result.PrivilegeEnabledDuring
            enabled_after = [bool]$Result.PrivilegeEnabledAfter
            restore_verified = [bool]$Result.PrivilegeRestoreVerified
        }
        body_stored = $false
    }
    $json = ConvertTo-Json -InputObject $receipt -Depth 6
    $bytes = [Text.Encoding]::UTF8.GetBytes($json)
    if ($bytes.Length -gt 16384) { throw 'integrity_receipt_over_cap' }
    $fs = [IO.FileStream]::new($ReceiptPath, [IO.FileMode]::CreateNew,
        [Security.AccessControl.FileSystemRights]::WriteData, [IO.FileShare]::Read, 4096,
        [IO.FileOptions]::WriteThrough)
    try { $fs.Write($bytes, 0, $bytes.Length); $fs.Flush($true) } finally { $fs.Dispose() }
}

Export-ModuleMember -Function Initialize-IntegrityNative, Assert-IntegrityFence, Get-IntegrityIdentity,
    Invoke-BoundIntegrityRead, Write-IntegrityReceipt
