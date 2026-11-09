[CmdletBinding()]
param([Parameter(Mandatory)][string]$FixtureDir,[Parameter(Mandatory)][string]$Python,[switch]$LegacyRefusal)
$ErrorActionPreference='Stop'
Set-StrictMode -Version Latest
Add-Type -Path (Join-Path $PSScriptRoot 'BoundedNative.cs')
if($LegacyRefusal) {
    $stream=[IO.MemoryStream]::new([byte[]]@(1))
    try { $null=[AraBoundedNative]::RunWithStdin($Python,@('-c','pass'),$stream,1,1000,1024);throw 'legacy_transfer_not_rejected' }
    catch {if($_.Exception.ToString() -notmatch 'binary_stdin_requires_powershell7'){throw}}
    finally {$stream.Dispose()}
    'LEGACY_BINARY_STDIN_REFUSED';exit 0
}
if($PSVersionTable.PSVersion.Major -lt 7){throw 'powershell7_required'}
if(Test-Path -LiteralPath $FixtureDir){throw 'fixture_already_exists'}
$null=New-Item -ItemType Directory -Path $FixtureDir
$child='import sys,hashlib; d=sys.stdin.buffer.read(); print(len(d)); print(hashlib.sha256(d).hexdigest())'
foreach($length in 0,1,4,256,67108864) {
    $bytes=[byte[]]::new($length)
    for($i=0;$i -lt [Math]::Min($length,256);$i++){$bytes[$i]=[byte]$i}
    if($length -gt 256){for($offset=256;$offset -lt $length;$offset*=2){[Buffer]::BlockCopy($bytes,0,$bytes,$offset,[Math]::Min($offset,$length-$offset))}}
    $hash=[Convert]::ToHexString([Security.Cryptography.SHA256]::HashData($bytes)).ToLowerInvariant()
    $stream=[IO.MemoryStream]::new($bytes,$false)
    try {$r=[AraBoundedNative]::RunWithStdin($Python,@('-c',$child),$stream,$length,30000,4096)}finally{$stream.Dispose()}
    if($r.Exit -ne 0 -or -not $r.InputComplete -or $r.BytesWritten -ne $length -or $r.Lines.Count -ne 2 -or $r.Lines[0] -cne [string]$length -or $r.Lines[1] -cne $hash){throw "binary_roundtrip_mismatch:$length"}
    "BINARY_EXACT=$length"
}
function Expect-Failure([string]$Name,[string]$Code,[int]$Bytes,[long]$InputCap,[int]$Timeout,[int]$OutputCap,[string]$Expected) {
    $stream=[IO.MemoryStream]::new([byte[]]::new($Bytes),$false)
    try {$null=[AraBoundedNative]::RunWithStdin($Python,@('-c',$Code),$stream,$InputCap,$Timeout,$OutputCap);throw "missing_failure:$Name"}
    catch {if($_.Exception.ToString() -notmatch $Expected){throw};"EXPECTED_FAILURE=$Name"}
    finally {$stream.Dispose()}
}
Expect-Failure 'over_cap' $child 8192 4096 5000 4096 'native_input_over_cap'
Expect-Failure 'early_exit' 'import sys; sys.exit(0)' 8388608 8388608 5000 4096 'native_input_(broken_stream_child_exited|write_failed)'
Expect-Failure 'timeout' 'import time; time.sleep(30)' 8388608 8388608 200 4096 'native_deadline_exceeded'
Expect-Failure 'output_cap' 'import sys; sys.stdin.buffer.read(); print("x"*8192)' 4 4 5000 128 'native_output_over_cap'
'STDIN_PRIMITIVE_RESULT=OK'
