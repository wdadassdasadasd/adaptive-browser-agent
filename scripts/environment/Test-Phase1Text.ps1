# Exercise the exact production base64/text consumer without invoking WSL or service code.
[CmdletBinding()]
param()
$ErrorActionPreference='Stop'
Set-StrictMode -Version Latest
$tokens=$null;$errors=$null
$ast=[System.Management.Automation.Language.Parser]::ParseFile((Join-Path $PSScriptRoot 'Run-BootstrapPhase1.ps1'),[ref]$tokens,[ref]$errors)
if($errors.Count){throw 'phase1_parse_failed'}
$node=$ast.Find({param($n) $n -is [System.Management.Automation.Language.FunctionDefinitionAst] -and $n.Name -ceq 'Read-GuestText'},$true)
if($null -eq $node){throw 'production_consumer_missing'}
. ([ScriptBlock]::Create($node.Extent.Text))
$script:response=$null
function Invoke-Wsl { return $script:response }
$script:policyOverrides=@()
$prefix=[Text.Encoding]::UTF8.GetString([Convert]::FromBase64String('6K6h566X5py6562W55Wl5bey56aB55SoIC53c2xjb25maWcg6K6+572u'))
$warnings=@('wsl2.kernelModules','wsl2.kernel','wsl2.systemDistro') | ForEach-Object {'wsl: '+$prefix+[char]0x201c+$_+[char]0x201d+[char]0x3002}
$script:response=@{exit=0;lines=@($warnings)+@('ARA_B64=5Lit5paH')}
if((Read-GuestText 'fixture') -cne ([Text.Encoding]::UTF8.GetString([Convert]::FromBase64String('5Lit5paH')))){throw 'unicode_consumer_changed'}
if(@($script:policyOverrides).Count -ne 3){throw 'exact_override_field_recognition'}
'PASS=unicode_payload_and_three_exact_fields'
$script:policyOverrides=@()
$script:response=@{exit=0;lines=@('wsl: unknown setting wsl2.kernelModules', 'wsl: cannot open wsl2.kernel', 'wsl: invalid wsl2.systemDistro', 'ARA_B64=eA==')}
Read-GuestText 'fixture' | Out-Null
if($script:policyOverrides.Count -ne 0){throw 'non_policy_setting_mentions_counted_as_effective_policy'}
'PASS=non_policy_setting_mentions_not_policy_evidence'
$count=2
foreach($fixture in @(
    @{name='nonzero';response=@{exit=7;lines=@('ARA_B64=eA==')};error='guest_command_failed'},
    @{name='missing';response=@{exit=0;lines=@('policy warning')};error='guest_payload_count'},
    @{name='duplicate';response=@{exit=0;lines=@('ARA_B64=eA==','ARA_B64=eA==')};error='guest_payload_count'},
    @{name='invalid_utf8';response=@{exit=0;lines=@('ARA_B64=/w==')};error='Unable to translate|无法将|DecoderFallbackException'}
)) {
    $script:response=$fixture.response
    try{Read-GuestText 'fixture'|Out-Null;throw 'fixture_expected_rejection_missing'}
    catch{if($_.Exception.ToString() -notmatch $fixture.error){throw}}
    $count++;Write-Output "PASS=$($fixture.name)"
}
$payload=New-Object byte[] 4194304
$script:response=@{exit=0;lines=@('ARA_B64='+[Convert]::ToBase64String($payload))}
if((Read-GuestText 'fixture').Length -ne 4194304){throw 'maximum_legal_decoded_content_lost'}
$count++;'PASS=maximum_legal_decoded_payload'
$payload=New-Object byte[] 4194305
$script:response=@{exit=0;lines=@('ARA_B64='+[Convert]::ToBase64String($payload))}
try{Read-GuestText 'fixture'|Out-Null;throw 'oversize_expected_rejection_missing'}
catch{if($_.Exception.ToString() -notmatch 'guest_decoded_output_over_cap'){throw}}
$count++;'PASS=over_maximum_decoded_payload_rejected'
Write-Output "PHASE1_TEXT_CONSUMER_PASSED=$count"
