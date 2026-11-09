# Real NTFS synthetic transactions. Workspace mode never accesses the real profile config.
[CmdletBinding()]
param([ValidateSet('Workspace','ProfileFixture')][string]$Mode='Workspace',
    [ValidatePattern('^[a-z][a-z0-9-]{0,15}$')][string]$Run='run01')
$ErrorActionPreference='Stop'
Set-StrictMode -Version Latest
Import-Module (Join-Path $PSScriptRoot 'ConfigProbe.psm1') -Force
$module=Get-Module ConfigProbe
& $module { Initialize-ProbeNative }
$sid=[Security.Principal.WindowsIdentity]::GetCurrent().User.Value
$base=if($Mode -eq 'Workspace'){'D:\adaptive-browser-agent\.tmp\config-probe-fixtures-20261107'}else{'C:\Users\FFFFFF\.ara-stage1-policy-fixtures-20261107'}
if($Mode -eq 'ProfileFixture') { & $module { Assert-ProbeFence 'ProfileFixture' $false } }
if(Test-Path -LiteralPath $base) {
    if((Get-Item -LiteralPath $base -Force).Attributes -band [IO.FileAttributes]::ReparsePoint){throw 'fixture_base_reparse'}
} else { [StageOneNative]::CreateDirectoryExclusive($base,"O:${sid}D:P(A;OICI;FA;;;$sid)(A;OICI;FA;;;SY)(A;OICI;FA;;;BA)") }
$count=0

function New-Fixture([string]$Name) {
    $case="$Run-$Name"
    $root=Join-Path $base $case
    if(Test-Path -LiteralPath $root){throw 'fixture_case_exists_no_overwrite'}
    [StageOneNative]::CreateDirectoryExclusive($root,"O:${sid}D:P(A;OICI;FA;;;$sid)(A;OICI;FA;;;SY)(A;OICI;FA;;;BA)")
    $live=Join-Path $root 'live'
    [StageOneNative]::CreateDirectoryExclusive($live,"O:${sid}D:P(A;OICI;FA;;;$sid)(A;OICI;FA;;;SY)(A;OICI;FA;;;BA)")
    $source=Join-Path $live '.wslconfig'
    # Real original .wslconfig is already protected. Model that invariant at creation;
    # inherited ACLs legitimately change on cross-directory moves and are a different case.
    $acl=[Security.AccessControl.FileSecurity]::new()
    $acl.SetSecurityDescriptorSddlForm("O:${sid}D:P(A;;FA;;;$sid)(A;;FA;;;SY)(A;;FA;;;BA)")
    $f=[IO.FileStream]::new($source,[IO.FileMode]::CreateNew,[Security.AccessControl.FileSystemRights]::WriteData,
        [IO.FileShare]::Read,4096,[IO.FileOptions]::WriteThrough,$acl)
    try{$b=[Text.Encoding]::UTF8.GetBytes("[wsl2]`nmemory=512MB`n");$f.Write($b,0,$b.Length);$f.Flush($true)}finally{$f.Dispose()}
    return @{case=$case;root=$root;source=$source;saved=(Join-Path $root 'retained\original.wslconfig')}
}

function Expect-Failure([string]$Name,[scriptblock]$Action,[string]$Pattern) {
    try{& $Action | Out-Null;throw "expected_failure_missing:$Name"}
    catch{if($_.Exception.ToString() -notmatch $Pattern){Write-Output "FIXTURE_FAILURE_STACK=$($_.ScriptStackTrace)";throw}}
    $script:count++;Write-Output "PASS=$Name"
}

function Expect-SharingRefusal([string]$Name,[scriptblock]$Action) {
    try{& $Action | Out-Null;throw "expected_sharing_failure_missing:$Name"}
    catch {
        $error=$_.Exception
        while($null -ne $error.InnerException){$error=$error.InnerException}
        $code=$error.HResult -band 0xffff
        if($code -ne 32){Write-Output "UNEXPECTED_SHARING_ERROR=$code STACK=$($_.ScriptStackTrace)";throw}
    }
    $script:count++;Write-Output "PASS=$Name WIN32=32"
}

$fixture=New-Fixture 'roundtrip'
$session=Start-ConfigProbe -Mode $Mode -Case $fixture.case
try {
    # Match the CRT reader shape WSL uses: read access with read/write sharing, no delete.
    'STEP=before_crt_read'
    $reader=[IO.File]::Open($fixture.source,'Open','Read','ReadWrite')
    try{if($reader.Length -lt 1){throw 'reader_no_canary'}}finally{$reader.Dispose()}
    'STEP=crt_read_completed'
    Expect-SharingRefusal 'active_canary_write_refused' { $f=[IO.File]::Open($fixture.source,'Open','Write','ReadWrite,Delete');$f.Dispose() }
    Expect-SharingRefusal 'retained_original_write_refused' { $f=[IO.File]::Open($fixture.saved,'Open','Write','ReadWrite,Delete');$f.Dispose() }
} finally{Close-ConfigProbe $session}
Restore-ConfigProbe -Mode $Mode -Case $fixture.case | Write-Output
Restore-ConfigProbe -Mode $Mode -Case $fixture.case | Write-Output
$count++;'PASS=roundtrip_and_recovery_idempotence'

foreach($point in 'AfterIntent','AfterMove','AfterCanary') {
    $fixture=New-Fixture $point.ToLowerInvariant()
    Expect-Failure "inject_$point" { Start-ConfigProbe -Mode $Mode -Case $fixture.case -Inject $point } 'injected_'
    Restore-ConfigProbe -Mode $Mode -Case $fixture.case | Write-Output
    $count++;Write-Output "PASS=recover_$point"
}

$fixture=New-Fixture 'retaincrash'
$session=Start-ConfigProbe -Mode $Mode -Case $fixture.case
Close-ConfigProbe $session
Expect-Failure 'inject_after_canary_retained' { Restore-ConfigProbe -Mode $Mode -Case $fixture.case -Inject AfterRetain } 'injected_after_retain'
Restore-ConfigProbe -Mode $Mode -Case $fixture.case | Write-Output
$count++;'PASS=recover_after_canary_retained'

$fixture=New-Fixture 'tampered'
$session=Start-ConfigProbe -Mode $Mode -Case $fixture.case
Close-ConfigProbe $session
[IO.File]::WriteAllText($fixture.source,'unknown fixture bytes')
Expect-Failure 'unknown_canary_not_moved' { Restore-ConfigProbe -Mode $Mode -Case $fixture.case } 'unknown_canary'
if(-not(Test-Path -LiteralPath $fixture.saved) -or [IO.File]::ReadAllText($fixture.source) -cne 'unknown fixture bytes'){throw 'partial_not_preserved'}
$count++;'PASS=unknown_canary_and_original_preserved'

$fixture=New-Fixture 'unbound'
Expect-Failure 'inject_after_canary_write' { Start-ConfigProbe -Mode $Mode -Case $fixture.case -Inject AfterCanaryWrite } 'injected_after_canary_write'
Expect-Failure 'unbound_canary_does_not_auto_restore' { Restore-ConfigProbe -Mode $Mode -Case $fixture.case } 'unknown_canary'
if(-not(Test-Path -LiteralPath $fixture.saved)){throw 'unbound_original_missing'}
$count++;'PASS=unbound_partial_original_preserved'

Write-Output "CONFIG_PROBE_FIXTURE_PASSED=$count MODE=$Mode"
