[CmdletBinding()]
param([Parameter(Mandatory)][string]$FixtureDir)
$ErrorActionPreference='Stop'
Set-StrictMode -Version Latest
if(Test-Path -LiteralPath $FixtureDir){throw 'fixture_exists'}
$null=New-Item -ItemType Directory -Path $FixtureDir
$module=Import-Module (Join-Path $PSScriptRoot 'StageOneRebuild.psm1') -Force -PassThru
& $module {
    param($fixture)
    $script:Repo=$fixture
    $script:Root=Join-Path $fixture 'evidence'
    $null=New-Item -ItemType Directory -Path $script:Root
    $files=@()
    foreach($path in Get-RebuildCandidatePaths){$p=Join-Path $fixture $path;$null=New-Item -ItemType Directory -Path (Split-Path $p) -Force;[IO.File]::WriteAllText($p,'fixture');$files+=@{path=$path;sha256=(Get-FileHash -LiteralPath $p).Hash.ToLowerInvariant()}}
    $candidate=@{files=$files;runtime_sha256=(Get-FileHash -LiteralPath ([Environment]::ProcessPath)).Hash.ToLowerInvariant()}
    Write-RebuildJson (Join-Path $script:Root 'candidate.json') $candidate
    $null=Assert-RebuildCandidate
    [IO.File]::AppendAllText((Join-Path $fixture $files[0].path),'changed')
    try{$null=Assert-RebuildCandidate;throw 'source_drift_not_denied'}catch{if($_.Exception.Message -notmatch '^candidate_source_drift:'){throw}}
    $a=[pscustomobject]@{guid='{new-one}';base='D:\fixture';file_identity='volume|file|birth'}
    $b=[pscustomobject]@{guid='{new-one}';base='D:\fixture';file_identity='volume|file|birth'}
    Assert-RebuildIdentity $a $b
    $b.guid='{replacement}'
    try{Assert-RebuildIdentity $a $b;throw 'guid_drift_not_denied'}catch{if($_.Exception.Message -cne 'new_instance_identity_changed'){throw}}
    $b.guid=$a.guid;$b.file_identity='volume|replacement|birth'
    try{Assert-RebuildIdentity $a $b;throw 'file_drift_not_denied'}catch{if($_.Exception.Message -cne 'new_instance_identity_changed'){throw}}
    # The complete production wrapper must refuse a missing retirement receipt
    # before touching any real registry, VHD or guest operation.
    function Assert-LegacyRetired {throw 'must_not_read_host_without_retirement_receipt'}
    try{$null=Assert-NewRegistration;throw 'missing_receipt_not_denied'}catch{if($_.Exception.Message -cne 'retirement_receipt_required'){throw}}
    function Assert-LegacyRetired {}
    function Assert-NoReparse {}
    $script:Install='D:\fixture';$script:Distro='fixtureDistro';$script:Lxss='fixtureRegistry'
    function Get-RebuildRegistrations {[pscustomobject]@{guid='{new-one}';name='fixtureDistro';base='D:\fixture';version=2;leaf='ext4.vhdx'}}
    function Get-RebuildFileIdentity {'volume|file|birth'}
    function Get-Item {param($Path);$obj=[pscustomobject]@{};$obj|Add-Member -MemberType ScriptMethod -Name GetValue -Value {param($name);'{new-one}'};$obj}
    $null=New-Item -ItemType Directory -Path (Join-Path $script:Root 'retire')
    Write-RebuildJson (Join-Path $script:Root 'retire\receipt.json') @{success=$true;new_registration=$a}
    $positive=Assert-NewRegistration
    if($positive.guid -cne '{new-one}'){throw 'valid_retirement_receipt_not_accepted'}
    'CANDIDATE_AND_INSTANCE_DRIFT_REFUSED'
} $FixtureDir
