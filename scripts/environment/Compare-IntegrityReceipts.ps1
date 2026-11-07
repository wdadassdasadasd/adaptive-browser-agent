# Local-only three-boolean comparison of integrity receipts. Prints booleans only; never prints digests.
[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)][string]$OriginalReceipt,
    [Parameter(Mandatory = $true)][string]$CopyReceipt,
    [string]$HistoricalOriginalReceipt
)
$ErrorActionPreference = 'Stop'
Set-StrictMode -Version Latest

function Load-Receipt([string]$Path) {
    if (-not (Test-Path -LiteralPath $Path)) { throw "integrity_receipt_missing:$Path" }
    $r = Get-Content -LiteralPath $Path -Raw | ConvertFrom-Json
    if ($r.schema -ne 'ara.stage1.integrity-read/1') { throw 'integrity_receipt_schema_unknown' }
    if (-not $r.ok) { throw ('integrity_receipt_not_ok:' + $r.error_kind) }
    if (-not $r.privilege.restore_verified) { throw 'integrity_receipt_privilege_restore_unverified' }
    return $r
}

$orig = Load-Receipt $OriginalReceipt
$copy = Load-Receipt $CopyReceipt
if (-not $orig.sha256 -or $orig.sha256.Length -ne 64) { throw 'integrity_receipt_digest_missing' }
$originalMatchesCopy = ($orig.sha256 -eq $copy.sha256) -and ([long]$orig.bytes_read -eq [long]$copy.bytes_read)
Write-Output ('ORIGINAL_MATCHES_COPY=' + $originalMatchesCopy)

if ($HistoricalOriginalReceipt) {
    if (-not (Test-Path -LiteralPath $HistoricalOriginalReceipt)) { throw 'integrity_historical_receipt_missing' }
    $hist = Get-Content -LiteralPath $HistoricalOriginalReceipt -Raw | ConvertFrom-Json
    # Historical receipts are not from this schema; require comparable digest+size fields, never guess.
    $histDigest = $null; $histSize = $null
    foreach ($prop in @('sha256', 'hash', 'digest')) {
        if ($hist.PSObject.Properties[$prop]) { $histDigest = [string]$hist.$prop; break }
    }
    foreach ($prop in @('size', 'bytes', 'length')) {
        if ($hist.PSObject.Properties[$prop]) { $histSize = [long]$hist.$prop; break }
    }
    if (-not $histDigest -or $histDigest.Length -ne 64) { throw 'integrity_historical_receipt_digest_unverifiable' }
    if ($null -eq $histSize) { throw 'integrity_historical_receipt_size_unverifiable' }
    $d = $histDigest.ToLowerInvariant()
    Write-Output ('ORIGINAL_MATCHES_HISTORICAL_RECEIPT=' + (($orig.sha256 -eq $d) -and ([long]$orig.bytes_read -eq $histSize)))
    Write-Output ('COPY_MATCHES_HISTORICAL_RECEIPT=' + (($copy.sha256 -eq $d) -and ([long]$copy.bytes_read -eq $histSize)))
} else {
    Write-Output 'ORIGINAL_MATCHES_HISTORICAL_RECEIPT=NOT_EVALUATED_NO_HISTORICAL_RECEIPT'
    Write-Output 'COPY_MATCHES_HISTORICAL_RECEIPT=NOT_EVALUATED_NO_HISTORICAL_RECEIPT'
}
Write-Output 'COMPARE_RESULT=BOUNDED_BOOLEANS_ONLY'
