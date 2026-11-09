# Elevated wrapper for the shape diagnostic (same proven launch pattern as Run-ElevatedBatch).
$ErrorActionPreference = 'Stop'
$logRoot = 'D:\adaptive-browser-agent\.tmp\stage-1-1-resume-20261107'
$stamp = [DateTimeOffset]::UtcNow.ToString('yyyyMMddTHHmmssZ') -replace ':', ''
Start-Transcript -Path (Join-Path $logRoot "shape-diag-$stamp.log") | Out-Null
try {
    & "$PSScriptRoot\Diagnose-ShapeElevated.ps1"
    'DIAG_RESULT=OK'
} catch {
    "DIAG_FAILURE=$($_.Exception.Message)"
} finally {
    Stop-Transcript | Out-Null
}
exit 0
