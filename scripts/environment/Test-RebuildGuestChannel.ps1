param([Parameter(Mandatory)][string]$FixtureDir,[Parameter(Mandatory)][string]$Python,[Parameter(Mandatory)][string]$Bash,[string]$ModulePath=(Join-Path $PSScriptRoot 'StageOneRebuild.psm1'),[ValidateSet('All','Newlines','Encoding','Fence')][string]$CheckMode='All')
$ErrorActionPreference='Stop'
Set-StrictMode -Version Latest
if(Test-Path $FixtureDir){throw 'fixture_exists'}
$null=New-Item -ItemType Directory $FixtureDir
Add-Type -Path (Join-Path $PSScriptRoot 'BoundedNative.cs')
$child=Join-Path (Resolve-Path $FixtureDir) 'mixed.py'
$code=@'
import subprocess,sys
sys.stderr.buffer.write(('WSL host diagnostic ' * 8 + '\n').encode('utf-16le'))
sys.stderr.buffer.flush()
r=subprocess.run([sys.argv[1],'-c',sys.argv[2]],capture_output=True,check=False)
sys.stdout.buffer.write(r.stdout)
error=r.stderr
if len(error) % 2:
    error += b' '
sys.stderr.buffer.write(error)
sys.exit(r.returncode)
'@
[IO.File]::WriteAllText($child,$code.Replace("`r`n","`n"),[Text.UTF8Encoding]::new($false))
$module=Import-Module $ModulePath -Force -PassThru
& $module {
 param($python,$bash,$child,$mode)
 $script:ChannelPython=$python;$script:ChannelBash=$bash;$script:ChannelChild=$child
 function Invoke-RebuildWsl([string[]]$Arguments,[int]$Timeout=120000,[int]$Cap=12582912){
  $match=[regex]::Match($Arguments[-1],'printf %s ([A-Za-z0-9+/]*={0,2}) \|')
  if(-not $match.Success){throw 'guest_payload_frame_missing'}
  $payload=[Text.Encoding]::UTF8.GetString([Convert]::FromBase64String($match.Groups[1].Value))
  if($payload.Contains("`r")){throw 'linux_script_payload_contains_cr'}
  $r=[AraBoundedNative]::Run($script:ChannelPython,@($script:ChannelChild,$script:ChannelBash,$Arguments[-1]),$Timeout,$Cap)
  if($r.Exit -ne 0){throw "wsl_failed:exit=$($r.Exit):$($r.Lines -join ' | ')"}
  $r
 }
 $command="set -eu`r`nprintf 'GUEST_UTF8_ERROR_123456789`n' >&2`r`nexit 7`r`n"
 if($mode -eq 'Encoding'){$command=$command.Replace("`r`n","`n")}
 if($mode -ne 'Fence'){try{Invoke-RebuildGuest $command;throw 'guest_failure_not_propagated'}catch{
  if($_.Exception.Message -notmatch 'wsl_failed:exit=7:' -or $_.Exception.Message -notmatch 'GUEST_UTF8_ERROR_123456789'){throw}
 }}
 if($mode -in @('All','Newlines')){try{Invoke-RebuildGuest "echo one`recho two";throw 'bare_cr_accepted'}catch{if($_.Exception.Message -cne 'guest_script_bare_cr_refused'){throw}}}
 if($mode -in @('All','Fence')){
  function Get-RebuildGuestFence {'set -eu; printf "FENCE_ERROR_MARKER_12345678\n" >&2; exit 23; '}
  try{Invoke-RebuildGuest 'true';throw 'fence_failure_not_propagated'}catch{if($_.Exception.Message -notmatch 'wsl_failed:exit=23:' -or $_.Exception.Message -notmatch 'FENCE_ERROR_MARKER_12345678'){throw}}
 }
 'CRLF_NORMALIZED_MIXED_ENCODING_DIAGNOSTIC_AND_EXIT_PRESERVED'
} $Python $Bash $child $CheckMode
