# Production publisher + a real concurrent reader; no WSL, C profile, services or network.
[CmdletBinding()]
param()
$ErrorActionPreference='Stop'
$t=$null;$e=$null
$ast=[System.Management.Automation.Language.Parser]::ParseFile((Join-Path $PSScriptRoot 'Test-StandardPolicyNegative.ps1'),[ref]$t,[ref]$e)
if($e.Count){throw 'producer_parse'}
$node=$ast.Find({param($n)$n -is [System.Management.Automation.Language.FunctionDefinitionAst] -and $n.Name -ceq 'Publish-StandardPolicyResult'},$true)
. ([ScriptBlock]::Create($node.Extent.Text))
Add-Type -TypeDefinition @'
using System;
using System.IO;
using System.Diagnostics;
using System.Threading;
using System.Threading.Tasks;
public static class AraPublicationObserver {
    public static Task<int> Observe(string path) {
        return Task.Factory.StartNew(() => {
            var clock=Stopwatch.StartNew();
            while(clock.ElapsedMilliseconds<5000) {
                if(File.Exists(path)) {
                    byte[] data=File.ReadAllBytes(path);
                    if(data.Length!=16384) throw new InvalidOperationException("observed_partial_publication");
                    for(int i=0;i<data.Length;i++) if(data[i]!=120) throw new InvalidOperationException("observed_corrupt_publication");
                    return data.Length;
                }
                Thread.Sleep(1);
            }
            throw new TimeoutException("publication_not_observed");
        });
    }
}
'@
$root='D:\adaptive-browser-agent\.tmp\stage-1-1-resume-20261107\checks-preparation-01\publication-01'
if(Test-Path -LiteralPath $root){throw 'publication_fixture_exists_preserve'}
New-Item -ItemType Directory -Path $root|Out-Null
$data=[Text.Encoding]::ASCII.GetBytes(('x'*16384))
foreach($n in 1..10) {
    $destination=Join-Path $root "$n.json"
    $observer=[AraPublicationObserver]::Observe($destination)
    Publish-StandardPolicyResult $destination $data
    if(-not $observer.Wait(5000) -or $observer.Result -ne 16384){throw 'reader_failed'}
}
'PASS=ten_concurrent_maximum_producer_consumer_publications'
$destination=Join-Path $root 'oversize.json'
try{Publish-StandardPolicyResult $destination (New-Object byte[] 16385);throw 'expected_cap_rejection_missing'}
catch{if($_.Exception.ToString() -notmatch 'ordinary_result_producer_cap'){throw}}
if(Test-Path -LiteralPath $destination){throw 'oversize_wrote_final'}
'PASS=over_limit_fails_before_writing'
$destination=Join-Path $root '1.json'
try{Publish-StandardPolicyResult $destination ([Text.Encoding]::ASCII.GetBytes('new'));throw 'expected_no_overwrite_missing'}
catch{if($_.Exception.ToString() -match 'expected_no_overwrite_missing'){throw}}
if([IO.File]::ReadAllText($destination).Length -ne 16384){throw 'existing_final_overwritten'}
'PASS=existing_final_preserved_pending_evidence_retained'
'POLICY_PUBLICATION_TESTS=12_PASSED'
