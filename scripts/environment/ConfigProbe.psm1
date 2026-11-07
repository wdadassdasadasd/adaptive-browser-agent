# Approved R2 direction: retain the original config object, never its copy, then restore it.
# Importing this module never changes a file, service, registry value or ACL.
Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'
$script:DailySid = 'S-1-5-21-2765399256-1806415232-1753294129-1001'
$script:ConfigHash = '5BA5428E1CFC55BF92D9E19FC2DBF04B02FB164AD55C378CAE292278BDCC5CAF'

function Initialize-ProbeNative {
    if (-not ('AraCustodyHandle' -as [type])) {
        $bytes = [IO.File]::ReadAllBytes((Join-Path $PSScriptRoot 'CustodyNative.cs'))
        if ((Get-ProbeHash $bytes) -cne 'AC534ED09A4725ECAEEC8517A2C6837B1A678F354D3587E1C68E3DC665CBA2D9') { throw 'native_identity' }
        Add-Type -TypeDefinition ([Text.Encoding]::UTF8.GetString($bytes))
    }
    if (-not ('AraConfigProbeNative' -as [type])) {
        $bytes=[IO.File]::ReadAllBytes((Join-Path $PSScriptRoot 'ConfigProbeNative.cs'))
        if ((Get-ProbeHash $bytes) -cne '3A74FE6B763F3C06E275239C9474BE18183ECB85460B55645E2B0788606F5F41') { throw 'config_native_identity' }
        Add-Type -TypeDefinition ([Text.Encoding]::UTF8.GetString($bytes))
    }
}

function Get-ProbeHash([byte[]]$Bytes) {
    $sha = [Security.Cryptography.SHA256]::Create()
    try { return [BitConverter]::ToString($sha.ComputeHash($Bytes)).Replace('-', '') }
    finally { $sha.Dispose() }
}

function Get-ProbeConfigBytes {
    $lines = @('[wsl2]', 'memory=1GB', 'processors=1', 'swap=0', 'networkingMode=none',
        'guiApplications=false', 'localhostForwarding=false', 'nestedVirtualization=false',
        'kernel=D:\\adaptive-browser-agent\\.tmp\\stage-1-1-resume-20261107\\config-canary-01\\kernel.img',
        'kernelModules=D:\\adaptive-browser-agent\\.tmp\\stage-1-1-resume-20261107\\config-canary-01\\modules.vhdx',
        'systemDistro=D:\\adaptive-browser-agent\\.tmp\\stage-1-1-resume-20261107\\config-canary-01\\system.vhdx')
    $bytes = [Text.Encoding]::UTF8.GetBytes(($lines -join "`n") + "`n")
    if ((Get-ProbeHash $bytes) -cne $script:ConfigHash) { throw 'canary_template_identity' }
    return ,$bytes
}

function Get-ProbePaths([string]$Mode, [string]$Case) {
    if ($Mode -notin 'Workspace','ProfileFixture','Real' -or $Case -cnotmatch '^[a-z][a-z0-9-]{0,31}$') { throw 'probe_scope' }
    if ($Mode -eq 'Real') {
        if ($Case -cne 'policy-01') { throw 'real_probe_identity_fixed' }
        $live = 'C:\Users\FFFFFF'
        $root = 'C:\Users\FFFFFF\.ara-stage1-policy-probe-20261107'
    } else {
        $base = if ($Mode -eq 'Workspace') { 'D:\adaptive-browser-agent\.tmp\config-probe-fixtures-20261107' }
            else { 'C:\Users\FFFFFF\.ara-stage1-policy-fixtures-20261107' }
        $live = Join-Path (Join-Path $base $Case) 'live'
        $root = Join-Path (Join-Path $base $Case) 'retained'
    }
    return @{ mode=$Mode; case=$Case; live=$live; root=$root; source=(Join-Path $live '.wslconfig');
        saved=(Join-Path $root 'original.wslconfig'); canary=(Join-Path $root 'observed-canary.wslconfig');
        intent=(Join-Path $root 'intent.json') }
}

function Assert-ProbeFence([string]$Mode, [bool]$Beginning) {
    if ($Mode -eq 'Workspace') { return }
    $id = [Security.Principal.WindowsIdentity]::GetCurrent()
    if ($id.User.Value -cne $script:DailySid -or -not ([Security.Principal.WindowsPrincipal]::new($id)).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)) { throw 'actual_elevated_daily_token_required' }
    foreach ($name in 'WslService','vmcompute') {
        $svc = Get-Service -Name $name
        if ($svc.Status -ne 'Stopped' -or $svc.StartType -ne 'Disabled') { throw "probe_service_not_fenced:$name" }
    }
    if (@(Get-Process -Name 'vmmemWSL','wslhost' -ErrorAction SilentlyContinue).Count) { throw 'probe_guest_present' }
    if ($Mode -eq 'Real' -and $Beginning -and @(Get-NetAdapter -Physical | Where-Object Status -eq 'Up').Count) { throw 'probe_requires_physical_offline' }
    if ($Mode -eq 'Real') {
        $key=Get-Item -LiteralPath 'HKLM:\Software\Policies\WSL'
        foreach($name in 'AllowWSL','AllowInboxWSL','AllowWSL1','AllowKernelUserSetting','AllowSystemDistroUserSetting',
            'AllowKernelCommandLineUserSetting','AllowDebugShell','AllowNestedVirtualization','AllowKernelDebugUserSetting',
            'AllowDiskMount','AllowNetworkingModeUserSetting','AllowFirewallUserSetting','DefaultNetworkingMode') {
            $expected=if($name -ceq 'AllowWSL'){1}else{0}
            if($name -cnotin $key.GetValueNames() -or $key.GetValueKind($name) -ne 'DWord' -or [int]$key.GetValue($name) -ne $expected){throw "config_probe_policy_drift:$name"}
        }
    }
}

function Get-ProbeAcl([bool]$Directory, [string]$Mode='Workspace') {
    $sid = [Security.Principal.WindowsIdentity]::GetCurrent().User.Value
    $inherit = if ($Directory) { 'OICI' } else { '' }
    # Applies only at creation of NEW probe objects. Original config ACL is never changed.
    if ($Mode -eq 'Workspace') { return "O:${sid}D:P(A;$inherit;FA;;;$sid)(A;$inherit;FA;;;SY)(A;$inherit;FA;;;BA)" }
    return "O:BAD:P(A;$inherit;FA;;;SY)(A;$inherit;FA;;;BA)(A;$inherit;0x1200a9;;;$script:DailySid)"
}

function Write-ProbeReceipt([string]$Path, $Object, [string]$Mode) {
    $bytes = [Text.Encoding]::UTF8.GetBytes(($Object | ConvertTo-Json -Depth 5 -Compress))
    if ($bytes.Length -gt 16384) { throw 'probe_receipt_cap' }
    $acl = [Security.AccessControl.FileSecurity]::new()
    $acl.SetSecurityDescriptorSddlForm((Get-ProbeAcl $false $Mode))
    $f = [IO.FileStream]::new($Path, [IO.FileMode]::CreateNew, [Security.AccessControl.FileSystemRights]::WriteData,
        [IO.FileShare]::Read, 4096, [IO.FileOptions]::WriteThrough, $acl)
    try { $f.Write($bytes,0,$bytes.Length); $f.Flush($true) } finally { $f.Dispose() }
}

function Get-ProbeBinding($Handle, [string]$Path, [bool]$Directory) {
    return [AraCustodyHandle]::Binding($Handle,$Path,$Directory)
}

function Test-ProbeIdentity([string]$Now, [string]$Expected) {
    $a=$Now.Split('|'); $b=$Expected.Split('|')
    if ($a.Count -ne 7 -or $b.Count -ne 7) { return $false }
    return (($a[0..5] -join '|') -ceq ($b[0..5] -join '|'))
}

function Close-ConfigProbe($Session) {
    foreach ($name in 'canaryHandle','originalHandle','rootHandle','liveHandle') {
        if ($Session.Contains($name) -and $null -ne $Session[$name]) { $Session[$name].Dispose(); $Session[$name]=$null }
    }
}

function Start-ConfigProbe {
    param([ValidateSet('Workspace','ProfileFixture','Real')][string]$Mode,
        [ValidatePattern('^[a-z][a-z0-9-]{0,31}$')][string]$Case,
        [ValidateSet('None','AfterIntent','AfterMove','AfterCanaryWrite','AfterCanary')][string]$Inject='None')
    Initialize-ProbeNative
    Assert-ProbeFence $Mode $true
    $p = Get-ProbePaths $Mode $Case
    if (Test-Path -LiteralPath $p.root) { throw 'probe_root_exists_preserve_no_retry' }
    $s = @{ paths=$p }
    try {
        $s.liveHandle=[AraCustodyHandle]::Open($p.live,0x20081,3)
        $s.originalHandle=[AraCustodyHandle]::Open($p.source,0x30081,1)
        $binding=Get-ProbeBinding $s.originalHandle $p.source $false
        $size=[int]$binding.Split('|')[2]
        $data=[AraConfigProbeNative]::ReadConfig($s.originalHandle,$size)
        $sourceHash=Get-ProbeHash $data
        if ($Mode -eq 'Real') {
            $sealed=Get-Content -LiteralPath 'C:\ProgramData\ARA-Stage1-Archive-20261106\real-custody-20261107\sealed.json' -Raw | ConvertFrom-Json
            if (-not (Test-ProbeIdentity $binding $sealed.wslconfig_binding) -or $sourceHash -cne $sealed.wslconfig_sha256 -or
                [AraCustodyHandle]::ReadAcl($s.originalHandle) -cne $sealed.sddl_after.($p.source)) { throw 'real_config_sealed_identity_or_acl_drift' }
        }
        [StageOneNative]::CreateDirectoryExclusive($p.root,(Get-ProbeAcl $true $Mode))
        $s.rootHandle=[AraCustodyHandle]::Open($p.root,0x20081,3)
        $s.intent=@{schema='ENV-M1-01.config-probe.v1';utc=[DateTimeOffset]::UtcNow.ToString('o');mode=$Mode;case=$Case;
            original_binding=$binding;original_sha256=$sourceHash;original_sddl=[AraCustodyHandle]::ReadAcl($s.originalHandle);
            root_binding=(Get-ProbeBinding $s.rootHandle $p.root $true);live_binding=(Get-ProbeBinding $s.liveHandle $p.live $true);
            canary_sha256=$script:ConfigHash}
        Write-ProbeReceipt $p.intent $s.intent $Mode
        if ($Inject -eq 'AfterIntent') { throw 'injected_after_intent' }
        [AraConfigProbeNative]::RenameNoReplace($s.originalHandle,$s.rootHandle,'original.wslconfig')
        if (-not (Test-ProbeIdentity (Get-ProbeBinding $s.originalHandle $p.saved $false) $binding)) { throw 'original_changed_on_retain' }
        Write-ProbeReceipt (Join-Path $p.root 'original-moved.json') @{state='original_retained';binding=$binding} $Mode
        if ($Inject -eq 'AfterMove') { throw 'injected_after_move' }
        $bytes=Get-ProbeConfigBytes
        $acl=[Security.AccessControl.FileSecurity]::new(); $acl.SetSecurityDescriptorSddlForm((Get-ProbeAcl $false $Mode))
        $f=[IO.FileStream]::new($p.source,[IO.FileMode]::CreateNew,[Security.AccessControl.FileSystemRights]::WriteData,
            [IO.FileShare]::None,4096,[IO.FileOptions]::WriteThrough,$acl)
        try { $f.Write($bytes,0,$bytes.Length); $f.Flush($true) } finally { $f.Dispose() }
        if ($Inject -eq 'AfterCanaryWrite') { throw 'injected_after_canary_write_unbound_partial' }
        # Only the synthetic canary gets the original creation time. Original timestamps untouched.
        [IO.File]::SetCreationTimeUtc($p.source,[DateTime]::FromFileTimeUtc([long]$binding.Split('|')[4]))
        $s.canaryHandle=[AraCustodyHandle]::Open($p.source,0x20081,1)
        $cb=Get-ProbeBinding $s.canaryHandle $p.source $false
        if ((Get-ProbeHash ([AraConfigProbeNative]::ReadConfig($s.canaryHandle,[int]$cb.Split('|')[2]))) -cne $script:ConfigHash) { throw 'created_canary_bytes_changed' }
        Write-ProbeReceipt (Join-Path $p.root 'canary-active.json') @{state='canary_active';binding=$cb;sha256=$script:ConfigHash} $Mode
        if ($Inject -eq 'AfterCanary') { throw 'injected_after_canary' }
        return $s
    } catch { Close-ConfigProbe $s; throw }
}

function Restore-ConfigProbe {
    param([ValidateSet('Workspace','ProfileFixture','Real')][string]$Mode,
        [ValidatePattern('^[a-z][a-z0-9-]{0,31}$')][string]$Case,
        [ValidateSet('None','AfterRetain')][string]$Inject='None')
    Initialize-ProbeNative
    Assert-ProbeFence $Mode $false
    $p=Get-ProbePaths $Mode $Case
    $s=@{paths=$p}
    try {
        $s.liveHandle=[AraCustodyHandle]::Open($p.live,0x20081,3)
        $s.rootHandle=[AraCustodyHandle]::Open($p.root,0x20081,3)
        $f=[IO.File]::Open($p.intent,'Open','Read','Read')
        try {
            if ($f.Length -gt 16384) { throw 'intent_over_cap' }
            $reader=[IO.StreamReader]::new($f,[Text.Encoding]::UTF8,$true,1024,$true)
            try { $intent=$reader.ReadToEnd() | ConvertFrom-Json } finally { $reader.Dispose() }
        } finally { $f.Dispose() }
        if ($intent.schema -cne 'ENV-M1-01.config-probe.v1' -or $intent.mode -cne $Mode -or $intent.case -cne $Case -or $intent.canary_sha256 -cne $script:ConfigHash) { throw 'intent_scope_or_version' }
        $nowRoot=Get-ProbeBinding $s.rootHandle $p.root $true
        $nowLive=Get-ProbeBinding $s.liveHandle $p.live $true
        foreach ($pair in @(@($nowRoot,$intent.root_binding),@($nowLive,$intent.live_binding))) {
            if (($pair[0].Split('|')[0..1] -join '|') -cne ($pair[1].Split('|')[0..1] -join '|')) { throw 'parent_identity_changed' }
        }
        if ($Mode -eq 'Real') {
            $sealed=Get-Content -LiteralPath 'C:\ProgramData\ARA-Stage1-Archive-20261106\real-custody-20261107\sealed.json' -Raw | ConvertFrom-Json
            if (-not (Test-ProbeIdentity $intent.original_binding $sealed.wslconfig_binding) -or $intent.original_sha256 -cne $sealed.wslconfig_sha256 -or
                $intent.original_sddl -cne $sealed.sddl_after.($p.source)) { throw 'intent_not_sealed_original' }
        }
        # Classify reality, not only the last durable journal label: rename metadata may lag.
        $savedExists=Test-Path -LiteralPath $p.saved
        if (-not $savedExists) {
            $s.originalHandle=[AraCustodyHandle]::Open($p.source,0x30081,1)
        } else {
            $s.originalHandle=[AraCustodyHandle]::Open($p.saved,0x30081,1)
        }
        $actualOriginal=if ($savedExists) { $p.saved } else { $p.source }
        $ob=Get-ProbeBinding $s.originalHandle $actualOriginal $false
        if (-not (Test-ProbeIdentity $ob $intent.original_binding) -or [AraCustodyHandle]::ReadAcl($s.originalHandle) -cne $intent.original_sddl -or
            (Get-ProbeHash ([AraConfigProbeNative]::ReadConfig($s.originalHandle,[int]$ob.Split('|')[2]))) -cne $intent.original_sha256) { throw 'original_identity_acl_or_bytes_changed_no_repair' }
        if ($savedExists) {
            if (Test-Path -LiteralPath $p.source) {
                $s.canaryHandle=[AraCustodyHandle]::Open($p.source,0x30081,1)
                $cb=Get-ProbeBinding $s.canaryHandle $p.source $false
                $activePath=Join-Path $p.root 'canary-active.json'
                if (-not(Test-Path -LiteralPath $activePath)) { throw 'unknown_canary_without_durable_binding_preserve' }
                $activeStream=[IO.File]::Open($activePath,'Open','Read','Read')
                try {
                    if($activeStream.Length -le 0 -or $activeStream.Length -gt 16384){throw 'active_receipt_cap'}
                    $activeReader=[IO.BinaryReader]::new($activeStream)
                    try{$activeBytes=$activeReader.ReadBytes([int]$activeStream.Length)}finally{$activeReader.Dispose()}
                } finally{$activeStream.Dispose()}
                $active=[Text.Encoding]::UTF8.GetString($activeBytes) | ConvertFrom-Json
                if (-not(Test-ProbeIdentity $cb $active.binding) -or $active.sha256 -cne $script:ConfigHash -or
                    (Get-ProbeHash ([AraConfigProbeNative]::ReadConfig($s.canaryHandle,[int]$cb.Split('|')[2]))) -cne $script:ConfigHash -or $cb.Split('|')[4] -cne $ob.Split('|')[4]) { throw 'unknown_canary_preserve_no_rename' }
                [AraConfigProbeNative]::RenameNoReplace($s.canaryHandle,$s.rootHandle,'observed-canary.wslconfig')
                Write-ProbeReceipt (Join-Path $p.root 'canary-retained.json') @{state='canary_retained';binding=$cb} $Mode
                $s.canaryHandle.Dispose(); $s.canaryHandle=$null
                if ($Inject -eq 'AfterRetain') { throw 'injected_after_retain' }
            }
            [AraConfigProbeNative]::RenameNoReplace($s.originalHandle,$s.liveHandle,'.wslconfig')
        }
        $final=Get-ProbeBinding $s.originalHandle $p.source $false
        if (-not (Test-ProbeIdentity $final $intent.original_binding) -or [AraCustodyHandle]::ReadAcl($s.originalHandle) -cne $intent.original_sddl -or
            (Get-ProbeHash ([AraConfigProbeNative]::ReadConfig($s.originalHandle,[int]$final.Split('|')[2]))) -cne $intent.original_sha256) { throw 'restored_original_drift_no_timestamp_or_acl_repair' }
        $receiptPath=Join-Path $p.root 'restored.json'
        if (Test-Path -LiteralPath $receiptPath) {
            $prior=Get-Content -LiteralPath $receiptPath -Raw | ConvertFrom-Json
            if ($prior.state -cne 'restored' -or $prior.sha256 -cne $intent.original_sha256 -or -not (Test-ProbeIdentity $prior.binding $final)) { throw 'existing_restore_receipt_drift' }
        } else {
            Write-ProbeReceipt $receiptPath @{state='restored';binding=$final;sha256=$intent.original_sha256;sddl=$intent.original_sddl;utc=[DateTimeOffset]::UtcNow.ToString('o')} $Mode
        }
        return 'CONFIG_ORIGINAL_RESTORED_SAME_OBJECT'
    } finally { Close-ConfigProbe $s }
}

Export-ModuleMember -Function Start-ConfigProbe,Restore-ConfigProbe,Close-ConfigProbe,Get-ProbeConfigBytes
