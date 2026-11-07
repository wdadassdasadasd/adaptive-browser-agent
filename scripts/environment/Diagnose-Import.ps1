# Import failure diagnosis inside the same offline window: service health, wsl.exe identity,
# and a raw-output import attempt via cmd redirect (avoids UTF-16 console garbling in PS 5.1).
[CmdletBinding()]
param()
throw 'retired_diagnostic_no_delete_no_reimport_use_existing_approved_registration'
$ErrorActionPreference = 'Continue'
$logRoot = 'D:\adaptive-browser-agent\.tmp\stage-1-1-resume-20261107\bootstrap\window-01'
$stamp = [DateTimeOffset]::UtcNow.ToString('yyyyMMddTHHmmssZ') -replace ':', ''
Start-Transcript -Path (Join-Path $logRoot "import-diag-$stamp.log") | Out-Null

try {
    '== services =='
    foreach ($name in 'WslService', 'vmcompute') {
        $svc = Get-Service -Name $name
        "$name $($svc.Status)/$($svc.StartType)"
    }
    '== enable services if needed =='
    foreach ($name in 'WslService', 'vmcompute') {
        $svc = Get-Service -Name $name
        if ($svc.StartType -eq 'Disabled') { $null = & sc.exe config $name start= demand 2>&1 }
        if ($svc.Status -ne 'Running') { $null = & sc.exe start $name 2>&1 | Out-String }
        Start-Sleep -Seconds 2
        $svc = Get-Service -Name $name
        "$name now=$($svc.Status)"
    }
    '== wsl.exe identity =='
    $wsl = "$env:SystemRoot\System32\wsl.exe"
    (Get-Item $wsl).VersionInfo.FileVersion
    (Get-Item $wsl).Length
    '== wsl --version (cmd redirect, raw) =='
    & cmd.exe /c "$wsl --version > $logRoot\wsl-version.txt 2>&1"
    "exit=$LASTEXITCODE"
    Get-Content -LiteralPath "$logRoot\wsl-version.txt" | Select-Object -First 6
    '== wsl --status =='
    & cmd.exe /c "$wsl --status > $logRoot\wsl-status.txt 2>&1"
    "exit=$LASTEXITCODE"
    Get-Content -LiteralPath "$logRoot\wsl-status.txt" | Select-Object -First 8
    '== wsl --list --verbose =='
    & cmd.exe /c "$wsl --list --verbose > $logRoot\wsl-list.txt 2>&1"
    "exit=$LASTEXITCODE"
    Get-Content -LiteralPath "$logRoot\wsl-list.txt" | Select-Object -First 10
    '== install dir state =='
    "install_dir_exists=$(Test-Path 'D:\WSL-Stage1\stage1-bootstrap')"
    if (Test-Path 'D:\WSL-Stage1\stage1-bootstrap') {
        Get-ChildItem -Force 'D:\WSL-Stage1\stage1-bootstrap' | ForEach-Object { "  $($_.Name) $($_.Length)" }
    }
    '== import attempt with raw redirect =='
    $tar = 'D:\adaptive-browser-agent\.tmp\stage-1-1-resume-20261107\bootstrap\stage1-bootstrap-derived.tar'
    & cmd.exe /c "$wsl --import stage1-bootstrap D:\WSL-Stage1\stage1-bootstrap $tar --version 2 > $logRoot\import-attempt.txt 2>&1"
    "import_exit=$LASTEXITCODE"
    Get-Content -LiteralPath "$logRoot\import-attempt.txt" | Select-Object -First 15
    "vhdx_after=$(Test-Path 'D:\WSL-Stage1\stage1-bootstrap\ext4.vhdx')"
    '== import attempt without --version flag =='
    if (-not (Test-Path 'D:\WSL-Stage1\stage1-bootstrap\ext4.vhdx')) {
        if (Test-Path 'D:\WSL-Stage1\stage1-bootstrap') { $null = Remove-Item -Recurse -Force 'D:\WSL-Stage1\stage1-bootstrap' }
        & cmd.exe /c "$wsl --import stage1-bootstrap D:\WSL-Stage1\stage1-bootstrap $tar > $logRoot\import-attempt2.txt 2>&1"
        "import2_exit=$LASTEXITCODE"
        Get-Content -LiteralPath "$logRoot\import-attempt2.txt" | Select-Object -First 15
        "vhdx_after2=$(Test-Path 'D:\WSL-Stage1\stage1-bootstrap\ext4.vhdx')"
    }
} finally {
    '== cleanup: terminate + disable services =='
    $null = & cmd.exe /c "$env:SystemRoot\System32\wsl.exe --terminate stage1-bootstrap 2>&1"
    foreach ($name in 'WslService', 'vmcompute') {
        $null = & sc.exe stop $name 2>&1 | Out-String
        $null = & sc.exe config $name start= disabled 2>&1
    }
    Start-Sleep -Seconds 2
    foreach ($name in 'WslService', 'vmcompute') {
        $svc = Get-Service -Name $name
        "$name final=$($svc.Status)/$($svc.StartType)"
    }
    Stop-Transcript | Out-Null
}
