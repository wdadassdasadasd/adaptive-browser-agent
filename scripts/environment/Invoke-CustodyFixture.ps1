# Executes only the fixed small synthetic fixtures. No original/archive VHDX is opened.
[CmdletBinding()]
param([Parameter(Mandatory)][ValidateSet('Admin','Standard','WorkspaceProbe')][string]$Mode)
$ErrorActionPreference = 'Stop'
Set-StrictMode -Version Latest
$id = [Security.Principal.WindowsIdentity]::GetCurrent()
$elevated = [Security.Principal.WindowsPrincipal]::new($id).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
if ($Mode -eq 'WorkspaceProbe') {
    if ($elevated) { throw 'workspace_probe_must_not_elevate' }
} elseif ($id.User.Value -cne 'S-1-5-21-2765399256-1806415232-1753294129-1001' -or $elevated -ne ($Mode -eq 'Admin')) { throw 'wrong_operator_token' }
$base = 'D:\adaptive-browser-agent'
$scripts = Join-Path $base 'scripts\environment'
$logRoot = Join-Path $base '.tmp\stage-1-implementation-20261106-01'
$expectedScript = '694801E5713BC66CB0F775E87DDE5A74280611B4DF475CFFF7A49E2980F67EE5'
$expectedNative = 'AC534ED09A4725ECAEEC8517A2C6837B1A678F354D3587E1C68E3DC665CBA2D9'
$phases = if ($Mode -eq 'Admin') { @('Prepare','InspectSealed','InjectAfterMove','InspectPartial') }
    elseif ($Mode -eq 'WorkspaceProbe') { @('DelayProbe','Verify') } else { @('Verify') }

function Read-BoundedSource([string]$Path,[int]$Cap) {
    if ((Get-Item -LiteralPath $Path -Force).Attributes -band [IO.FileAttributes]::ReparsePoint) { throw 'source_reparse' }
    $stream = [IO.File]::Open($Path,'Open','Read','Read')
    try {
        if ($stream.Length -le 0 -or $stream.Length -gt $Cap) { throw 'source_size_before_read' }
        $reader = [IO.BinaryReader]::new($stream)
        $bytes = $reader.ReadBytes([int]$stream.Length)
        if ($bytes.Length -ne $stream.Length) { throw 'source_short_read' }
        return ,$bytes
    } finally { $stream.Dispose() }
}
$native = Read-BoundedSource (Join-Path $scripts 'CustodyNative.cs') 32768
$hash = [Security.Cryptography.SHA256]::Create()
try {
    if ([BitConverter]::ToString($hash.ComputeHash($native)).Replace('-','') -cne $expectedNative) { throw 'native_digest' }
} finally { $hash.Dispose() }
Add-Type -TypeDefinition ([Text.Encoding]::UTF8.GetString($native))
# Claim every existing output ancestor before privileged file creation. Share=Read excludes
# both directory write-data/reparse handles and delete/rename handles until output is closed.
$leases = [Collections.Generic.List[IDisposable]]::new()
try {
foreach ($path in @('D:\',$base,(Join-Path $base '.tmp'),$logRoot)) {
    $handle = [AraCustodyHandle]::Open($path,0x20081,1)
    $leases.Add($handle)
    $null = [AraCustodyHandle]::Binding($handle,$path,$true)
}
foreach ($phase in $phases) {
    $prefix = if ($Mode -eq 'WorkspaceProbe') { 'workspace-probe-' } else { 'c-fixture-07-' }
    $outputPath = Join-Path $logRoot ($prefix + $phase + '.json')
    if (Test-Path -LiteralPath $outputPath) { throw 'fixture_result_exists_no_retry' }
    # Child reads each source once, hashes the captured bytes, then executes those same bytes.
    $volume = if ($Mode -eq 'WorkspaceProbe') { 'Workspace' } else { 'CustodyRoot' }
    $runLine = if ($phase -eq 'DelayProbe') { 'Start-Sleep -Seconds 30' }
        else { "& ([ScriptBlock]::Create([Text.Encoding]::UTF8.GetString(`$s))) -Volume $volume -Phase $phase -NativeSource `$n" }
    $guard = @"
`$ErrorActionPreference='Stop'
`$ProgressPreference='SilentlyContinue'
function Read-Captured([string]`$p) {
if ((Get-Item -LiteralPath `$p -Force).Attributes -band [IO.FileAttributes]::ReparsePoint) { throw 'source_reparse' }
`$f=[IO.File]::Open(`$p,'Open','Read','Read')
try {
if (`$f.Length -le 0 -or `$f.Length -gt 32768) { throw 'source_size_before_read' }
`$r=[IO.BinaryReader]::new(`$f); `$b=`$r.ReadBytes([int]`$f.Length)
if (`$b.Length -ne `$f.Length) { throw 'source_short_read' }; return ,`$b
} finally { `$f.Dispose() }
}
`$s=Read-Captured '$scripts\Test-Custody.ps1'
`$n=Read-Captured '$scripts\CustodyNative.cs'
`$h=[Security.Cryptography.SHA256]::Create()
try {
if ([BitConverter]::ToString(`$h.ComputeHash(`$s)).Replace('-','') -cne '$expectedScript') { throw 'script_digest' }
if ([BitConverter]::ToString(`$h.ComputeHash(`$n)).Replace('-','') -cne '$expectedNative') { throw 'native_digest' }
} finally { `$h.Dispose() }
$runLine
"@
    $encoded = [Convert]::ToBase64String([Text.Encoding]::Unicode.GetBytes($guard))
    $start = [Diagnostics.ProcessStartInfo]::new('C:\Windows\System32\WindowsPowerShell\v1.0\powershell.exe',
        ('-NoProfile -NonInteractive -EncodedCommand ' + $encoded))
    $start.UseShellExecute = $false
    $start.CreateNoWindow = $true
    $start.RedirectStandardOutput = $true
    $start.RedirectStandardError = $true
    $process = [Diagnostics.Process]::new()
    $process.StartInfo = $start
    try {
        if (-not $process.Start()) { throw 'fixture_child_start' }
        $stdout = $process.StandardOutput.ReadToEndAsync()
        $stderr = $process.StandardError.ReadToEndAsync()
        $timeout = if ($phase -eq 'DelayProbe') { 1000 } else { 60000 }
        $timedOut = -not $process.WaitForExit($timeout)
        $termination = 'not_needed'
        $killExit = $null
        if ($timedOut) {
            $priorPreference = $ErrorActionPreference
            try {
                $ErrorActionPreference = 'Continue'
                $null = & 'C:\Windows\System32\taskkill.exe' /PID $process.Id /T /F 2>&1
                $killExit = $LASTEXITCODE
            } finally { $ErrorActionPreference = $priorPreference }
            $exited = $process.WaitForExit(5000)
            $termination = if ($killExit -eq 0 -and $exited) { 'confirmed' } else { 'unknown' }
        }
        $drained = [Threading.Tasks.Task]::WaitAll(@($stdout,$stderr),5000)
        $out = if ($stdout.IsCompleted) { $stdout.Result } else { '[output_incomplete]' }
        $err = if ($stderr.IsCompleted) { $stderr.Result } else { '[output_incomplete]' }
        $outputOverflow = $out.Length -gt 16384 -or $err.Length -gt 16384
        if ($out.Length -gt 16384) { $out = $out.Substring(0,16384) }
        if ($err.Length -gt 16384) { $err = $err.Substring(0,16384) }
        $exitCode = if ($process.HasExited) { $process.ExitCode } else { $null }
        $record = [ordered]@{phase=$phase;utc=[DateTimeOffset]::UtcNow.ToString('o');elevated=$elevated;exit_code=$exitCode;timed_out=$timedOut;termination=$termination;taskkill_exit=$killExit;output_complete=$drained;output_overflow=$outputOverflow;stdout=$out;stderr=$err}
        $file = [IO.FileStream]::new($outputPath,[IO.FileMode]::CreateNew,[IO.FileAccess]::Write,
            [IO.FileShare]::None,4096,[IO.FileOptions]::WriteThrough)
        try {
            $bytes = [Text.Encoding]::UTF8.GetBytes(($record | ConvertTo-Json -Compress))
            $file.Write($bytes,0,$bytes.Length)
            $file.Flush($true)
        } finally { $file.Dispose() }
        if ($phase -eq 'DelayProbe') {
            if (-not $timedOut -or $termination -ne 'confirmed' -or -not $drained) { throw 'timeout_probe_cleanup_unknown' }
        } elseif ($timedOut -or -not $drained -or $outputOverflow) { throw 'fixture_timeout_or_output_keep_partial' }
        elseif ($phase -eq 'InjectAfterMove') {
            if ($process.ExitCode -ne 1 -or $err -notmatch 'injected_fixture_failure_after_move') { throw 'fixture_unexpected_injection_result' }
        } elseif ($process.ExitCode -ne 0 -or $err) { throw 'fixture_phase_failed' }
        "C_FIXTURE_PHASE=$phase; EXPECTED_RESULT=true"
    } finally { $process.Dispose() }
}
} finally { foreach ($lease in $leases) { $lease.Dispose() } }
