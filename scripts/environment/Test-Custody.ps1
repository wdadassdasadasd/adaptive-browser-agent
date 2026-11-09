# Pure NTFS fixture. Never takes an original, archive, or arbitrary target path.
[CmdletBinding()]
param(
    [Parameter(Mandatory)][ValidateSet('Workspace','CustodyRoot')][string]$Volume,
    [Parameter(Mandatory)][ValidateSet('Prepare','Verify','InspectSealed','InjectAfterMove','InspectPartial')][string]$Phase,
    [byte[]]$NativeSource
)
$ErrorActionPreference = 'Stop'
Set-StrictMode -Version Latest
$sid = 'S-1-5-21-2765399256-1806415232-1753294129-1001'
$identity = [Security.Principal.WindowsIdentity]::GetCurrent()
$admin = [Security.Principal.WindowsPrincipal]::new($identity).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
$workspace = 'D:\adaptive-browser-agent\.tmp'
$vault = 'C:\ProgramData\ARA-Stage1-Archive-20261106'
$base = if ($Volume -eq 'CustodyRoot') { $vault } else { $workspace }
$name = if ($Phase -in @('InjectAfterMove','InspectPartial')) { 'synthetic-ntfs-partial-20261106-07' } else { 'synthetic-ntfs-qualification-20261106-07' }
$root = Join-Path $base $name
$from = Join-Path $root 'from'
$to = Join-Path $root 'to'
$collision = Join-Path $root 'collision'
$old = Join-Path $from 'original.decoy'
$new = Join-Path $to 'isolated.decoy'
$alias = Join-Path $from 'linked.decoy'
$receipt = Join-Path $root 'fixture-receipt.json'
$control = Join-Path $to 'read-control.decoy'
$open = [Collections.Generic.List[IDisposable]]::new()
$protectedDirectory = "O:BAD:P(A;OICI;FA;;;SY)(A;OICI;FA;;;BA)(A;OICI;0x1200a9;;;$sid)"
$protectedReceipt = "O:BAD:P(A;;FA;;;SY)(A;;FA;;;BA)(A;;0x1200a9;;;$sid)"

function Assert-Fence {
    if ($Volume -ne 'CustodyRoot') { return }
    if ($identity.User.Value -cne $sid -or $admin -ne ($Phase -ne 'Verify')) { throw 'wrong_fixture_token' }
    foreach ($service in 'WslService','vmcompute') {
        $state = Get-Service -Name $service
        if ($state.Status -ne 'Stopped' -or $state.StartType -ne 'Disabled') { throw 'fixture_service_not_fenced' }
    }
    if ([IO.DriveInfo]::new('C:\').DriveFormat -ne 'NTFS') { throw 'fixture_non_ntfs' }
}

function Open-Bound([string]$Path,[uint32]$Access,[uint32]$Share,[bool]$Directory) {
    $h = [AraCustodyHandle]::Open($Path,$Access,$Share)
    try { $null = [AraCustodyHandle]::Binding($h,$Path,$Directory) }
    catch { $h.Dispose(); throw }
    $h
}

function Expect-Error([string]$Case,[int[]]$Allowed,[scriptblock]$Action) {
    try { & $Action }
    catch {
        $err = $_.Exception
        while ($null -ne $err -and $err -isnot [ComponentModel.Win32Exception]) { $err = $err.InnerException }
        if ($null -eq $err -or $err.NativeErrorCode -notin $Allowed) { throw }
        "PASS $Case win32=$($err.NativeErrorCode)"
        return
    }
    throw "unexpected_success:$Case"
}

function Durable([string]$Path, [string]$Text) {
    if ($Volume -eq 'CustodyRoot') {
        $acl = [Security.AccessControl.FileSecurity]::new()
        $acl.SetSecurityDescriptorSddlForm($protectedReceipt)
        $f = [IO.FileStream]::new($Path,[IO.FileMode]::CreateNew,[Security.AccessControl.FileSystemRights]::WriteData,
            [IO.FileShare]::None,4096,[IO.FileOptions]::WriteThrough,$acl)
    } else {
        $f = [IO.FileStream]::new($Path,[IO.FileMode]::CreateNew,[IO.FileAccess]::Write,[IO.FileShare]::None,4096,[IO.FileOptions]::WriteThrough)
    }
    try {
        $bytes = [Text.Encoding]::UTF8.GetBytes($Text)
        $f.Write($bytes,0,$bytes.Length)
        $f.Flush($true)
    } finally { $f.Dispose() }
}

function Assert-VaultAcl($Handle) {
    $read = [Security.AccessControl.RawSecurityDescriptor]::new([AraCustodyHandle]::ReadAcl($Handle))
    $expected = [Security.AccessControl.RawSecurityDescriptor]::new($protectedDirectory)
    if ($read.GetSddlForm('Owner,Access') -cne $expected.GetSddlForm('Owner,Access')) { throw 'fixture_vault_acl_drift' }
}

function Read-LocalDependency([string]$Name) {
    if ($null -ne $NativeSource -and $NativeSource.Length -gt 0) {
        if ($Name -cne 'CustodyNative.cs' -or $NativeSource.Length -gt 32768) { throw 'fixture_dependency_shape' }
        return ,$NativeSource
    }
    $f = [IO.File]::Open((Join-Path $PSScriptRoot $Name),'Open','Read','Read')
    try {
        if ($f.Length -le 0 -or $f.Length -gt 32768) { throw 'fixture_dependency_length' }
        $reader = [IO.BinaryReader]::new($f)
        try { return ,$reader.ReadBytes([int]$f.Length) }
        finally { $reader.Dispose() }
    } finally { $f.Dispose() }
}

function Open-FixtureDir([string]$Path) {
    $h = Open-Bound $Path 0x20081 3 $true
    try { if ($Volume -eq 'CustodyRoot') { Assert-VaultAcl $h } }
    catch { $h.Dispose(); throw }
    $h
}

function Assert-LeafDescriptor([string]$Sddl) {
    $read = [Security.AccessControl.RawSecurityDescriptor]::new($Sddl)
    $expected = [Security.AccessControl.RawSecurityDescriptor]::new('O:BAD:P(A;;FA;;;SY)(A;;FA;;;BA)')
    if ($null -eq $read.Owner -or -not $read.Owner.Equals($expected.Owner) -or
        $null -eq $read.DiscretionaryAcl -or
        -not ($read.ControlFlags -band [Security.AccessControl.ControlFlags]::DiscretionaryAclProtected)) {
        throw 'fixture_leaf_acl_drift'
    }
    $actualBytes = [byte[]]::new($read.DiscretionaryAcl.BinaryLength)
    $expectedBytes = [byte[]]::new($expected.DiscretionaryAcl.BinaryLength)
    $read.DiscretionaryAcl.GetBinaryForm($actualBytes,0)
    $expected.DiscretionaryAcl.GetBinaryForm($expectedBytes,0)
    if ([Convert]::ToBase64String($actualBytes) -cne [Convert]::ToBase64String($expectedBytes)) {
        throw 'fixture_leaf_acl_drift'
    }
}

function Assert-LeafAcl($Handle) {
    Assert-LeafDescriptor ([AraCustodyHandle]::ReadAcl($Handle))
}

function Fixture-State([string]$Path,[string]$State) {
    if ((Get-Item -Force -LiteralPath $Path).Length -gt 1024) { throw 'fixture_receipt_size' }
    $result = Get-Content -LiteralPath $Path -Raw | ConvertFrom-Json
    if ($result.state -cne $State -or $result.identity.Split('|').Count -ne 7) { throw 'fixture_receipt_shape' }
    $result.identity
}

function New-FixtureDir([string]$Path) {
    if (Test-Path -LiteralPath $Path) { throw 'fixture_directory_exists' }
    if ($Volume -eq 'CustodyRoot') {
        [StageOneNative]::CreateDirectoryExclusive($Path,$protectedDirectory)
    } else {
        $null = [IO.Directory]::CreateDirectory($Path)
    }
    $open.Add((Open-FixtureDir $Path))
}

function Invoke-Fixture {
    Assert-Fence
    $bytes = Read-LocalDependency 'CustodyNative.cs'
    $sha = [Security.Cryptography.SHA256]::Create()
    try { $digest = [BitConverter]::ToString($sha.ComputeHash($bytes)).Replace('-','') }
    finally { $sha.Dispose() }
    if ($digest -cne 'AC534ED09A4725ECAEEC8517A2C6837B1A678F354D3587E1C68E3DC665CBA2D9') { throw 'fixture_helper_identity' }
    Add-Type -TypeDefinition ([Text.Encoding]::UTF8.GetString($bytes))

    if ($Volume -eq 'CustodyRoot') {
        $parents = [ordered]@{
            'C:\' = '05000000000005000000000000000000'
            'C:\ProgramData' = 'ceba0700000009000000000000000000'
            $vault = '04630400000050000000000000000000'
        }
        foreach ($path in $parents.Keys) {
            $h = Open-Bound $path 0x20081 3 $true
            $open.Add($h)
            $parts = [AraCustodyHandle]::Binding($h,$path,$true).Split('|')
            if ($parts[0] -cne '8130948118040412392' -or $parts[1] -cne $parents[$path]) { throw 'fixture_vault_chain_drift' }
            if ($path -eq $vault) { Assert-VaultAcl $h }
        }
    }
    if ($Phase -in @('Verify','InspectSealed','InspectPartial')) {
        foreach ($path in @($root,$from,$to)) { $open.Add((Open-FixtureDir $path)) }
        if ($Phase -eq 'InspectPartial') {
            if (Test-Path -LiteralPath $receipt) { throw 'fixture_partial_claimed_success' }
            $intent = Fixture-State (Join-Path $root 'intent.json') 'intent'
            $hasSource = Test-Path -LiteralPath $old
            $hasDestination = Test-Path -LiteralPath $new
            $movedPath = Join-Path $root 'moved.json'
            $hasMovedReceipt = Test-Path -LiteralPath $movedPath
            if ($hasSource -eq $hasDestination -or ($hasSource -and $hasMovedReceipt)) { throw 'fixture_partial_namespace' }
            $states = @($intent)
            if ($hasMovedReceipt) { $states += (Fixture-State $movedPath 'moved') }
            $location = if ($hasSource) { $old } else { $new }
            $h = Open-Bound $location 0x20080 7 $false
            try {
                $actual = [AraCustodyHandle]::Binding($h,$location,$false).Split('|')
                foreach ($state in $states) {
                    if (($actual[0..5] -join '|') -cne ($state.Split('|')[0..5] -join '|')) { throw 'fixture_partial_identity' }
                }
            } finally { $h.Dispose() }
            Assert-Fence
            "PASS partial retained; source=$hasSource moved_receipt=$hasMovedReceipt same_object=true sealed_claim=false; volume=$Volume"
            return
        }
        if (Test-Path -LiteralPath $old) { throw 'unexpected_fixture_source' }
        if ($Volume -eq 'CustodyRoot' -and $Phase -eq 'Verify') {
            $h = Open-Bound $control ([uint32]2147483648) 7 $false
            try { if ([AraCustodyHandle]::ReadSmall($h,1) -cne '+') { throw 'fixture_read_control' } }
            finally { $h.Dispose() }
            foreach ($mask in 1,2,4,0x10,0x100,0x10000,0x40000,0x80000) {
                Expect-Error "ordinary_access_$mask" @(5) { $probe=[AraCustodyHandle]::Open($new,$mask,7); $probe.Dispose() }
            }
            foreach ($path in @('C:\','C:\ProgramData',$vault,$root,$to)) {
                Expect-Error 'ordinary_delete_child' @(5) { $probe=[AraCustodyHandle]::Open($path,0x40,7); $probe.Dispose() }
            }
        }
        $finalState = if ($Volume -eq 'CustodyRoot') { 'sealed' } else { 'moved_only' }
        $recorded = Fixture-State $receipt $finalState
        if ($Volume -eq 'Workspace' -or $Phase -eq 'InspectSealed') {
            $h = Open-Bound $new 0x20080 7 $false
            try {
                if ([AraCustodyHandle]::Binding($h,$new,$false) -cne $recorded) { throw 'fixture_receipt_drift' }
                if ($Volume -eq 'CustodyRoot') { Assert-LeafAcl $h }
            }
            finally { $h.Dispose() }
        }
        Assert-Fence
        "FIXTURE_VERIFY=$Volume; recorded_state=$finalState"
        return
    }
    if (Test-Path -LiteralPath $root) { throw 'fixture_already_exists_no_retry' }
    New-FixtureDir $root
    New-FixtureDir $from
    # Test the opposite share-check order before taking the actual target lease.
    if ($Volume -eq 'CustodyRoot') { [StageOneNative]::CreateDirectoryExclusive($to,$protectedDirectory) }
    else { $null = [IO.Directory]::CreateDirectory($to) }
    $priorDelete = [AraCustodyHandle]::Open($to,0x10000,7)
    try { Expect-Error 'preexisting_parent_delete_blocks_claim' @(32) { $probe=Open-FixtureDir $to; $probe.Dispose() } }
    finally { $priorDelete.Dispose() }
    $open.Add((Open-FixtureDir $to))
    # Keep the occupied target intact in a separate directory. Deleting a same-name
    # target before rename can apply NTFS name tunneling to the creation timestamp.
    New-FixtureDir $collision
    $collisionParent = $open[$open.Count-1]
    Durable $old 'fixture'
    $occupied = Join-Path $collision 'isolated.decoy'
    Durable $occupied 'occupied'
    Durable $control '+'
    $holding = [AraCustodyHandle]::Open($old,2,7)
    try {
        Expect-Error 'preexisting_write_blocks_claim' @(32) {
            $probe=[AraCustodyHandle]::Open($old,0x10080,0); $probe.Dispose()
        }
    } finally { $holding.Dispose() }
    $null = New-Item -ItemType HardLink -Path $alias -Target $old
    $h = Open-Bound $old 0x80 7 $false
    try {
        if ([AraCustodyHandle]::Binding($h,$old,$false).Split('|')[3] -ne '2') { throw 'hard_link_not_detected' }
        'PASS hard_link_detected_prior_to_move'
    } finally { $h.Dispose() }
    [IO.File]::Delete($alias)
    $d = $open[$open.Count-2]
    Expect-Error 'parent_delete_handle_conflict' @(32) { $probe=[AraCustodyHandle]::Open($to,0x10000,7); $probe.Dispose() }
    $rights = if ($Volume -eq 'CustodyRoot') { 0xF0080 } else { 0x10080 }
    $s = Open-Bound $old $rights 0 $false
    try {
        $before = [AraCustodyHandle]::Binding($s,$old,$false).Split('|')
        $parent = [AraCustodyHandle]::Binding($d,$to,$true).Split('|')
        if ($before[0] -ne $parent[0] -or $before[3] -ne '1') { throw 'fixture_not_same_volume_single_link' }
        Expect-Error 'no_overwrite' @(80,183) { [StageOneNative]::RenameNoReplace($s,$collisionParent,'isolated.decoy') }
        if ([IO.File]::ReadAllText($occupied) -cne 'occupied') { throw 'occupied_target_changed' }
        Durable (Join-Path $root 'intent.json') ('{"state":"intent","identity":"' + ($before -join '|') + '"}')
        [StageOneNative]::RenameNoReplace($s,$d,'isolated.decoy')
        $after = [AraCustodyHandle]::Binding($s,$new,$false).Split('|')
        if (($after[0..5] -join '|') -cne ($before[0..5] -join '|') -or (Test-Path -LiteralPath $old)) {
            throw 'same_handle_binding_changed'
        }
        Durable (Join-Path $root 'moved.json') ('{"state":"moved","identity":"' + ($after -join '|') + '"}')
        'PASS no_replace_same_object_no_content_read'
        if ($Phase -eq 'InjectAfterMove') { throw 'injected_fixture_failure_after_move' }
        if ($Volume -eq 'CustodyRoot') { [AraCustodyHandle]::SetAcl($s,'O:BAD:P(A;;FA;;;SY)(A;;FA;;;BA)') }
    } finally { $s.Dispose() }
    $verify = Open-Bound $new 0x20080 7 $false
    try {
        $last = [AraCustodyHandle]::Binding($verify,$new,$false)
        if (($last.Split('|')[0..5] -join '|') -cne ($after[0..5] -join '|')) { throw 'fixture_post_close_identity' }
        if ($Volume -eq 'CustodyRoot') { Assert-LeafAcl $verify }
    }
    finally { $verify.Dispose() }
    Assert-Fence
    $finalState = if ($Volume -eq 'CustodyRoot') { 'sealed' } else { 'moved_only' }
    Durable $receipt ('{"state":"' + $finalState + '","identity":"' + $last + '"}')
    "FIXTURE_PREPARE=$Volume; retained=$root"
}

try { Invoke-Fixture }
finally { foreach ($h in $open) { $h.Dispose() } }
