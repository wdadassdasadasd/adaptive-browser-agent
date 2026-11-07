# Pure transport regression. Never invokes WSL, services, ACLs or the network.
[CmdletBinding()]
param()
$ErrorActionPreference = 'Stop'
Set-StrictMode -Version Latest
Add-Type -Path (Join-Path $PSScriptRoot 'BoundedNative.cs')
$python = [IO.Path]::GetFullPath((Join-Path $PSScriptRoot '..\..\.venv\Scripts\python.exe'))
$sample = @('space arg', 'embedded"quote', 'trailing\', 'apt > /tmp/uris.txt 2>&1', 'printf "\n"')
$arguments = @('-c', 'import json,sys; print(json.dumps(sys.argv[1:]))') + $sample
$r = [AraBoundedNative]::Run($python, $arguments, 5000, 8192)
if ($r.Exit -ne 0) { throw 'argv_fixture_failed' }
$actual = ConvertFrom-Json -InputObject $r.Lines[-1]
if ($actual.Count -ne $sample.Count) { throw 'argv_count' }
for ($i = 0; $i -lt $sample.Count; $i++) {
    if ($actual[$i] -cne $sample[$i]) { throw "argv_changed:$i" }
}
'ARGV_FIDELITY_OK'
try {
    $null = [AraBoundedNative]::Run($python, @('-c', 'import sys; sys.stdout.write("x" * 65536)'), 5000, 1024)
    throw 'output_overflow_not_rejected'
} catch {
    if ($_.Exception.ToString() -notmatch 'native_output_over_cap') { throw }
}
'OUTPUT_CAP_OK'
try {
    $null = [AraBoundedNative]::Run($python, @('-c', 'import time; time.sleep(10)'), 250, 1024)
    throw 'deadline_not_enforced'
} catch {
    if ($_.Exception.ToString() -notmatch 'native_deadline_exceeded') { throw }
}
'DEADLINE_KILL_AND_PIPE_CLOSE_OK'
$r = [AraBoundedNative]::Run($python, @('-c', 'import sys; sys.stderr.write("policy warning\n"); print("ARA_B64=5Lit5paH"); sys.exit(7)'), 5000, 8192)
if ($r.Exit -ne 7 -or 'ARA_B64=5Lit5paH' -cnotin $r.Lines -or 'policy warning' -cnotin $r.Lines) { throw 'stderr_exit_or_payload_corruption' }
'STDERR_EXIT_AND_BASE64_FIDELITY_OK'
$r = [AraBoundedNative]::Run($python, @('-c', 'import sys; sys.stdout.buffer.write("ARA_B64=5Lit5paH\n".encode("utf-16le"))'), 5000, 8192)
if ($r.Exit -ne 0 -or 'ARA_B64=5Lit5paH' -cnotin $r.Lines) { throw 'utf16_transport_corruption' }
'UTF16_BASE64_TRANSPORT_OK'
$r = [AraBoundedNative]::Run($python, @('-c', 'import sys; sys.stdout.buffer.write("\u4e2d\u6587\nE_ACCESSDENIED\n".encode("utf-16le"))'), 5000, 8192)
if ($r.Exit -ne 0 -or 'E_ACCESSDENIED' -cnotin $r.Lines) { throw 'utf16_non_ascii_prefix_corruption' }
'UTF16_NON_ASCII_PREFIX_REFUSAL_CODE_OK'
$r=[AraBoundedNative]::Run($python,@('-c','import sys; sys.stderr.buffer.write("\u8ba1\u7b97\u673a\u7b56\u7565\u5df2\u7981\u7528 .wslconfig \u8bbe\u7f6e\n".encode("gbk"))'),5000,8192)
$expected=[Text.Encoding]::UTF8.GetString([Convert]::FromBase64String('6K6h566X5py6562W55Wl5bey56aB55SoIC53c2xjb25maWcg6K6+572u'))
if($expected -cnotin $r.Lines){throw 'host_ansi_policy_warning_corruption'}
'HOST_ANSI_POLICY_WARNING_FIDELITY_OK'
$r = [AraBoundedNative]::Run($python, @('-c', 'import base64,sys; sys.stdout.buffer.write(("ARA_B64="+base64.b64encode(b"x"*4194304).decode()+"\n").encode("utf-16le"))'), 10000, 12582912)
if ($r.Exit -ne 0 -or $r.Lines.Count -ne 1) { throw 'maximum_legal_output_not_delivered' }
$decoded = [Convert]::FromBase64String($r.Lines[0].Substring(8))
if ($decoded.Length -ne 4194304 -or $decoded[0] -ne 120 -or $decoded[-1] -ne 120) { throw 'maximum_legal_payload_corruption' }
'MAXIMUM_4MIB_GUEST_UTF16_BASE64_CONSUMER_OK'
'BOUNDED_NATIVE_TESTS=8_PASSED'
