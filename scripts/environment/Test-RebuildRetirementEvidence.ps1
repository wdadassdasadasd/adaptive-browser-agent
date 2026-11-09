param([Parameter(Mandatory)][string]$FixtureDir)
$ErrorActionPreference='Stop'
Set-StrictMode -Version Latest
if(Test-Path $FixtureDir){throw 'fixture_exists'}
$null=New-Item -ItemType Directory $FixtureDir
$source='D:\adaptive-browser-agent\.tmp\stage1-rebuild-20261108'
foreach($name in 'audit-05','retire','candidate-originals-r8','retired-candidate-r8.json'){Copy-Item -LiteralPath (Join-Path $source $name) -Destination $FixtureDir -Recurse}
$module=Import-Module (Join-Path $PSScriptRoot 'StageOneRebuild.psm1') -Force -PassThru
& $module {
 param($fixture)
 $script:Root=$fixture
 Assert-RebuildRetirementEvidence
 $path=Join-Path $fixture 'retire\receipt.json';$bytes=[IO.File]::ReadAllBytes($path)
 [IO.File]::AppendAllText($path,' ')
 try{Assert-RebuildRetirementEvidence;throw 'changed_receipt_accepted'}catch{if($_.Exception.Message -cne 'retirement_receipt_bytes_changed'){throw}}
 [IO.File]::WriteAllBytes($path,$bytes)
 $p=Join-Path $fixture 'candidate-originals-r8\scripts\environment\Invoke-StageOneRebuild.ps1'
 [IO.File]::AppendAllText($p,'changed')
 try{Assert-RebuildRetirementEvidence;throw 'changed_original_accepted'}catch{if($_.Exception.Message -cne 'retired_candidate_original_drift'){throw}}
 'EXACT_RETIRED_CANDIDATE_RECEIPT_AND_ORIGINALS_BOUND'
} $FixtureDir
