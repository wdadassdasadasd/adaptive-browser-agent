param(
    [ValidateRange(1024,65535)][int]$ApiPort = 8000,
    [string]$WslDistribution = "Ubuntu",
    [switch]$ControlledTestWorker,
    [string]$PriceBookPath = ""
)

$ErrorActionPreference = "Stop"
$repositoryRoot = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
$backendRoot = Join-Path $repositoryRoot "backend"
$pythonPath = Join-Path $backendRoot ".venv\Scripts\python.exe"
if (-not (Test-Path -LiteralPath $pythonPath)) {
    # Preserve the pre-R0 environment while new clones use backend/.venv.
    $pythonPath = Join-Path $repositoryRoot ".venv\Scripts\python.exe"
}
if (-not (Test-Path -LiteralPath $pythonPath)) {
    throw "Project Python environment is missing: $pythonPath"
}
if ($ControlledTestWorker -and (-not $env:P01_FAKE_CONTROL_DIR -or $env:DEEPSEEK_API_KEY -ne 'offline-p01-fake')) {
    throw "ControlledTestWorker requires the measurement harness environment"
}
if ($ControlledTestWorker -and $PriceBookPath) {
    throw "ControlledTestWorker cannot use a paid-run price book"
}
$resolvedPriceBook = $null
if ($PriceBookPath) {
    $candidate = if ([IO.Path]::IsPathFullyQualified($PriceBookPath)) { $PriceBookPath } else { Join-Path $repositoryRoot $PriceBookPath }
    $resolvedPriceBook = (Resolve-Path -LiteralPath $candidate).Path
    $env:PYTHONPATH = Join-Path $backendRoot "src"
    & $pythonPath -m adaptive_research.evaluation.pilot_budget --price-book $resolvedPriceBook
    if ($LASTEXITCODE -ne 0) {
        throw "Pilot price book offline check failed"
    }
}
$portProbe = [Net.Sockets.TcpListener]::new([Net.IPAddress]::Loopback, $ApiPort)
try {
    $portProbe.Start()
}
finally {
    $portProbe.Stop()
}

$env:PYTHONPATH = Join-Path $backendRoot "src"
$wslKeepalive = $null
$apiProcess = $null
$workerProcess = $null
$startupWatch = [Diagnostics.Stopwatch]::StartNew()

function Test-PostgresReady {
    & wsl.exe --distribution $WslDistribution --exec /usr/bin/pg_isready -h 127.0.0.1 -p 5433 | Out-Null
    return $LASTEXITCODE -eq 0
}

function Start-Worker {
    $workerModule = if ($ControlledTestWorker) { "tests.p01_fake_worker" } else { "adaptive_research.worker.runner" }
    $workerArguments = @("-m", $workerModule)
    if ($resolvedPriceBook) {
        $workerArguments += @("--price-book", ('"{0}"' -f $resolvedPriceBook))
    }
    return Start-Process -FilePath $pythonPath `
        -ArgumentList $workerArguments `
        -WorkingDirectory $backendRoot -WindowStyle Hidden -PassThru
}

function Stop-OwnedProcessTree($process) {
    if ($null -ne $process -and -not $process.HasExited) {
        & taskkill.exe /PID $process.Id /T /F | Out-Null
    }
}

try {
    $wslKeepalive = Start-Process -FilePath "wsl.exe" `
        -ArgumentList @("--distribution", $WslDistribution, "--exec", "/usr/bin/sleep", "2147483647") `
        -WindowStyle Hidden -PassThru
    Start-Sleep -Seconds 2
    if (-not (Test-PostgresReady)) {
        & wsl.exe --distribution $WslDistribution --user root --exec /usr/bin/pg_ctlcluster 16 main start | Out-Null
        if ($LASTEXITCODE -ne 0 -or -not (Test-PostgresReady)) {
            throw "WSL PostgreSQL 16/main is unavailable on port 5433"
        }
    }

    # This command changes only the isolated P-01 database named by P01_DATABASE_URL.
    Push-Location $backendRoot
    try {
        & $pythonPath -m alembic -c migrations/alembic.ini upgrade head
        if ($LASTEXITCODE -ne 0) {
            throw "P-01 migration failed"
        }
    }
    finally {
        Pop-Location
    }

    $apiProcess = Start-Process -FilePath $pythonPath `
        -ArgumentList @("-m", "uvicorn", "adaptive_research.api.pg_main:app", "--host", "127.0.0.1", "--port", "$ApiPort") `
        -WorkingDirectory $backendRoot -WindowStyle Hidden -PassThru
    $workerProcess = Start-Worker
    $apiReady = $false
    while (-not $apiReady -and $startupWatch.Elapsed.TotalSeconds -lt 45) {
        if ($apiProcess.HasExited) {
            throw "API process exited with code $($apiProcess.ExitCode) during startup"
        }
        try {
            $probe = Invoke-WebRequest -Uri "http://127.0.0.1:$ApiPort/openapi.json" -UseBasicParsing -TimeoutSec 1
            $apiReady = $probe.StatusCode -eq 200
        }
        catch {
            Start-Sleep -Milliseconds 250
        }
    }
    if (-not $apiReady) {
        throw "API readiness deadline exceeded"
    }
    $apiChildren = @(Get-CimInstance Win32_Process -Filter "ParentProcessId=$($apiProcess.Id)" | Select-Object -ExpandProperty ProcessId)
    $listenerOwners = @(Get-NetTCPConnection -LocalPort $ApiPort -State Listen | Select-Object -ExpandProperty OwningProcess)
    if (-not ($listenerOwners | Where-Object { $_ -eq $apiProcess.Id -or $_ -in $apiChildren })) {
        throw "API port listener does not belong to this launcher"
    }
    Write-Host "P-01 API: http://127.0.0.1:$ApiPort; Worker PID $($workerProcess.Id)"
    Write-Host "startup_seconds=$([Math]::Round($startupWatch.Elapsed.TotalSeconds, 3))"

    $databasePaused = $false
    $restorationReported = $false
    while ($true) {
        Start-Sleep -Seconds 2
        if ($apiProcess.HasExited) {
            throw "API process exited with code $($apiProcess.ExitCode)"
        }
        $databaseReady = -not $wslKeepalive.HasExited -and (Test-PostgresReady)
        if (-not $databaseReady) {
            if (-not $databasePaused) {
                $databasePaused = $true
                Stop-OwnedProcessTree $workerProcess
                $workerProcess = $null
                Write-Warning "WSL or PostgreSQL disconnected. Worker stopped; API returns service unavailable. Restore manually, then restart this launcher."
            }
            continue
        }
        if ($databasePaused) {
            if (-not $restorationReported) {
                $restorationReported = $true
                Write-Warning "Database is reachable again. Worker remains paused; restart this launcher to reconcile and resume."
            }
            continue
        }
        if ($workerProcess.HasExited) {
            Write-Warning "Worker exited; restarting"
            $workerProcess = Start-Worker
        }
    }
}
finally {
    foreach ($process in @($workerProcess, $apiProcess, $wslKeepalive)) {
        Stop-OwnedProcessTree $process
    }
}
