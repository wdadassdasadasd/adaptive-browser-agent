# Exhaustive guest diagnosis inside the offline window. Prints EVERYTHING: boot behavior,
# raw bytes (hex prefix) of key reads, /etc listing, and the WSL meta output decoded.
[CmdletBinding()]
param()
throw 'retired_diagnostic_preserved_for_audit_do_not_start_services_use_reviewed_phase1'
$ErrorActionPreference = 'Continue'
$logRoot = 'D:\adaptive-browser-agent\.tmp\stage-1-1-resume-20261107\bootstrap\window-01'
$stamp = [DateTimeOffset]::UtcNow.ToString('yyyyMMddTHHmmssZ') -replace ':', ''
Start-Transcript -Path (Join-Path $logRoot "guest-diag-$stamp.log") | Out-Null

$wslExe = "$env:SystemRoot\System32\wsl.exe"

function Invoke-WslDiag {
    param([string]$Label)
    $tmp = [IO.Path]::GetTempFileName()
    $argString = '/d /c "' + $wslExe + ' ' + ($args | ForEach-Object { "$_" }) -join ' '
    $argString = '/d /c "' + $wslExe + ' ' + (($args | ForEach-Object { "$_" }) -join ' ') + ' > "' + $tmp + '" 2>&1"'
    $null = & cmd.exe $argString
    $exit = $LASTEXITCODE
    $bytes = [IO.File]::ReadAllBytes($tmp)
    $isUtf16 = $bytes.Length -ge 2 -and (($bytes[0] -eq 0xFF -and $bytes[1] -eq 0xFE) -or
        ($bytes.Length -ge 4 -and $bytes[1] -eq 0 -and $bytes[0] -ne 0))
    $text = if ($isUtf16) { [Text.Encoding]::Unicode.GetString($bytes) } else { [Text.Encoding]::UTF8.GetString($bytes) }
    $text = $text.TrimStart([char]0xFEFF)
    $hex = ($bytes[0..([Math]::Min(23, $bytes.Length - 1))] | ForEach-Object { $_.ToString('X2') }) -join ' '
    Write-Output ("[DIAG $Label] exit=$exit utf16=$isUtf16 bytes=$($bytes.Length) hex=$hex")
    $lines = @($text -split "`r?`n" | Where-Object { $_ -ne '' })
    foreach ($l in ($lines | Select-Object -First 12)) { Write-Output ("  | " + $l) }
    Remove-Item -LiteralPath $tmp -Force -ErrorAction SilentlyContinue
    return [pscustomobject]@{ exit = $exit; lines = $lines }
}

try {
    foreach ($name in 'WslService', 'vmcompute') {
        $svc = Get-Service -Name $name
        if ($svc.StartType -eq 'Disabled') { $null = & sc.exe config $name start= demand 2>&1 }
        if ($svc.Status -ne 'Running') { $null = & sc.exe start $name 2>&1 | Out-String }
    }
    Start-Sleep -Seconds 3

    Invoke-WslDiag 'wsl_list_verbose' --list --verbose
    Invoke-WslDiag 'echo_probe' -d stage1-bootstrap -u root -- /bin/echo hello-probe
    Invoke-WslDiag 'wsl_conf_cat' -d stage1-bootstrap -u root -- cat /etc/wsl.conf
    Invoke-WslDiag 'wsl_conf_ls' -d stage1-bootstrap -u root -- ls -la /etc/wsl.conf /etc/os-release /usr/lib/os-release
    Invoke-WslDiag 'etc_etc_head' -d stage1-bootstrap -u root -- ls /etc
    Invoke-WslDiag 'os_release_cat' -d stage1-bootstrap -u root -- cat /usr/lib/os-release
    Invoke-WslDiag 'hostname_probe' -d stage1-bootstrap -u root -- cat /etc/hostname
    Invoke-WslDiag 'dmesg_tail' -d stage1-bootstrap -u root -- dmesg
    Invoke-WslDiag 'old_distro_negative' -d Ubuntu -- /bin/true
} finally {
    $null = & cmd.exe /d /c "$wslExe --terminate stage1-bootstrap > NUL 2>&1"
    foreach ($name in 'WslService', 'vmcompute') {
        $null = & sc.exe stop $name 2>&1 | Out-String
        $null = & sc.exe config $name start= disabled 2>&1
    }
    Start-Sleep -Seconds 2
    foreach ($name in 'WslService', 'vmcompute') {
        $svc = Get-Service -Name $name
        Write-Output "$name final=$($svc.Status)/$($svc.StartType)"
    }
    Stop-Transcript | Out-Null
}
