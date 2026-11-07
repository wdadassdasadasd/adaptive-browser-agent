# Two-file sequential one-pass integrity read (B direction, ENV-M1-01 binding-drift decision).
# Real mode is fenced; running it is NOT itself a grant. The human's one-time read authorization
# (marker receipt referencing the decision doc hash) plus machine fences are mandatory.
[CmdletBinding()]
param(
    [ValidateSet('Synthetic', 'Real')][string]$Mode = 'Synthetic',
    [Parameter(Mandatory = $true)][string]$OriginalPath,
    [Parameter(Mandatory = $true)][string]$CopyPath,
    [Parameter(Mandatory = $true)][string]$ReceiptDir,
    [long]$ExpectedSizeEach = 4867489792,
    [uint32]$OriginalVolumeSerial = 0,
    [long]$OriginalFileIndex = -1,
    [uint32]$CopyVolumeSerial = 0,
    [long]$CopyFileIndex = -1,
    [Parameter(Mandatory = $true)][ValidateRange(1, 3600000)][int]$BatchDeadlineMs,
    [string]$AuthorizationReceipt
)
$ErrorActionPreference = 'Stop'
Set-StrictMode -Version Latest
Import-Module (Join-Path $PSScriptRoot 'IntegrityRead.psm1') -Force
Initialize-IntegrityNative
if (-not (Test-Path -LiteralPath $ReceiptDir)) { throw 'integrity_receipt_dir_missing' }

if ($Mode -eq 'Real') {
    if (-not $AuthorizationReceipt) { throw 'integrity_real_authorization_receipt_required' }
    if (-not (Test-Path -LiteralPath $AuthorizationReceipt)) { throw 'integrity_real_authorization_receipt_missing' }
    $auth = Get-Content -LiteralPath $AuthorizationReceipt -Raw
    if ($auth -notmatch '0fcf7a23624c7e127aa21b7fbae00d5613fdf0d1be797d073200bcf6ec993167') {
        throw 'integrity_real_authorization_decision_hash_missing'
    }
    if ($auth -notmatch 'GRANT_REAL_INTEGRITY_READ') { throw 'integrity_real_authorization_marker_missing' }
    Assert-IntegrityFence
}

$batchStart = [DateTime]::UtcNow
$receipts = @()
foreach ($pair in @(
    @{ name = 'original'; path = $OriginalPath; vol = $OriginalVolumeSerial; idx = $OriginalFileIndex },
    @{ name = 'copy'; path = $CopyPath; vol = $CopyVolumeSerial; idx = $CopyFileIndex })) {
    $elapsed = [int]([DateTime]::UtcNow - $batchStart).TotalMilliseconds
    $remaining = $BatchDeadlineMs - $elapsed
    if ($remaining -le 0) {
        Write-Output 'INTEGRITY_BATCH_RESULT=STOP reason=batch_deadline_exhausted'
        exit 2
    }
    $receiptPath = Join-Path $ReceiptDir ($pair.name + '-integrity-receipt.json')
    $r = Invoke-BoundIntegrityRead -Path $pair.path -MaxBytes $ExpectedSizeEach -ExpectedSize $ExpectedSizeEach `
        -ExpectedVolumeSerial $pair.vol -ExpectedFileIndex $pair.idx -DeadlineMs $remaining -ReceiptPath $receiptPath
    if (-not $r.Ok) {
        Write-Output ('INTEGRITY_BATCH_RESULT=STOP file=' + $pair.name + ' error=' + $r.ErrorKind +
            ' win32=' + $r.Win32Error)
        Write-Output 'STOP_LINE_NO_SECOND_REAL_READ'
        exit 2
    }
    $receipts += $receiptPath
    Write-Output ('PASS=integrity_' + $pair.name + ' bytes=' + $r.BytesRead + ' ms=' + $r.ElapsedMs)
}
Write-Output ('RECEIPTS=' + ($receipts -join ','))
Write-Output 'INTEGRITY_BATCH_RESULT=OK'
