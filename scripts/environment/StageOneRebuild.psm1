Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'
$script:Repo = 'D:\adaptive-browser-agent'
$script:Root = Join-Path $script:Repo '.tmp\stage1-rebuild-20261108'
$script:LegacyRoot = Join-Path $script:Repo '.tmp\stage-1-1-resume-20261107'
$script:Distro = 'ara-m1-stage1'
$script:Install = 'D:\WSL-Stage1\ara-m1-stage1'
$script:OldGuid = '{5bd0012b-1a62-445a-ad9e-da37f21ba704}'
$script:OldPath = 'C:\Users\FFFFFF\AppData\Local\Packages\CanonicalGroupLimited.Ubuntu_79rhkp1fndgsc\LocalState'
$script:Lxss = 'HKCU:\Software\Microsoft\Windows\CurrentVersion\Lxss'
$script:Config = 'C:\Users\FFFFFF\.wslconfig'
$script:OriginalConfigHash = '43edeb6c23a0be2aebd4a63db88b464b6362308c8d32812184966ecde26f01d2'
$script:Wsl = "$env:SystemRoot\System32\wsl.exe"

function Get-RebuildSettings {
    [pscustomobject]@{Root=$script:Root;Repo=$script:Repo;LegacyRoot=$script:LegacyRoot;Distro=$script:Distro;Install=$script:Install;OldGuid=$script:OldGuid;OldPath=$script:OldPath;Lxss=$script:Lxss}
}
function Assert-RebuildRuntime {
    if ($PSVersionTable.PSVersion.ToString() -cne '7.6.9') { throw 'rebuild_requires_pinned_pwsh_7_6_9' }
    $exe = [Environment]::ProcessPath
    $expected = 'C:\Program Files\WindowsApps\OpenAI.CodexPrimaryRuntime.v26-1105-1297-0_26.1105.1297.0_x64__3k8sg7r9htsxt\dependencies\native\powershell\pwsh.exe'
    if ($exe -ine $expected) { throw 'rebuild_runtime_path_drift' }
    $identity = [Security.Principal.WindowsIdentity]::GetCurrent()
    if ($identity.User.Value -cne 'S-1-5-21-2765399256-1806415232-1753294129-1001') { throw 'daily_sid_required' }
    if (-not ([Security.Principal.WindowsPrincipal]::new($identity)).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)) { throw 'elevation_required' }
    if (-not ('AraBoundedNative' -as [type])) { Add-Type -Path (Join-Path $PSScriptRoot 'BoundedNative.cs') }
    if (-not ('AraCustodyHandle' -as [type])) { Add-Type -Path (Join-Path $PSScriptRoot 'CustodyNative.cs') }
}
function Get-RebuildCandidatePaths {
    @('scripts/environment/Invoke-StageOneRebuild.ps1','scripts/environment/StageOneRebuild.psm1','scripts/environment/BoundedNative.cs','scripts/environment/CustodyNative.cs','scripts/environment/fetch_fixed_debs.py','scripts/environment/fetch_rebuild_debs.py','scripts/environment/rebuild/bootstrap.sh','scripts/environment/rebuild/qualify_pg.sh','scripts/environment/rebuild/role_probe.sql','scripts/environment/rebuild/resume_pg.sh','scripts/environment/Invoke-RebuildOfflineWindow.ps1','scripts/environment/Watch-RebuildNetwork.ps1')
}
function Assert-RebuildCandidate {
    $path=Join-Path $script:Root 'candidate.json'
    Assert-NoReparse $path
    $candidate=Get-Content -LiteralPath $path -Raw|ConvertFrom-Json -DateKind String
    $expected=Get-RebuildCandidatePaths
    if($candidate.files.Count -ne $expected.Count -or (($candidate.files.path|Sort-Object)-join '|') -cne (($expected|Sort-Object)-join '|')){throw 'candidate_file_set_drift'}
    foreach($f in $candidate.files){$p=Join-Path $script:Repo $f.path;Assert-NoReparse $p;if((Get-FileHash -LiteralPath $p).Hash.ToLowerInvariant() -cne $f.sha256){throw "candidate_source_drift:$($f.path)"}}
    if((Get-FileHash -LiteralPath ([Environment]::ProcessPath)).Hash.ToLowerInvariant() -cne $candidate.runtime_sha256){throw 'candidate_runtime_drift'}
    (Get-FileHash -LiteralPath $path).Hash.ToLowerInvariant()
}
function Write-RebuildJson([string]$Path, $Value) {
    $stream = [IO.File]::Open($Path, [IO.FileMode]::CreateNew, [IO.FileAccess]::Write, [IO.FileShare]::Read)
    try { $bytes=[Text.UTF8Encoding]::new($false).GetBytes(($Value|ConvertTo-Json -Depth 12)); $stream.Write($bytes,0,$bytes.Length);$stream.Flush($true) } finally {$stream.Dispose()}
}
function Start-RebuildDetachedProcess([string]$Executable,[string[]]$Arguments) {
    # WMI creates under the current caller's token outside the tool's process job.
    # ShowWindow=0 is supported here; CREATE_NO_WINDOW was rejected (return 21).
    $argv=@($Executable)+$Arguments
    $command=($argv|ForEach-Object{[AraBoundedNative]::QuoteArg($_)}) -join ' '
    $startup=New-CimInstance -ClassName Win32_ProcessStartup -ClientOnly -Property @{ShowWindow=[uint16]0}
    $result=Invoke-CimMethod -ClassName Win32_Process -MethodName Create -Arguments @{CommandLine=$command;ProcessStartupInformation=$startup}
    if($result.ReturnValue -ne 0){throw "detached_process_create_failed:$($result.ReturnValue)"}
    Get-Process -Id ([int]$result.ProcessId) -ErrorAction Stop
}
function Assert-RebuildRetirementEvidence {
    $predecessor=Join-Path $script:Root 'retired-candidate-r8.json'
    Assert-NoReparse $predecessor
    $hash=(Get-FileHash -LiteralPath $predecessor).Hash.ToLowerInvariant()
    if($hash -cne '6c12c59e3d03b7a928d72bfdb03ba80f40f48199b416338d2edac4b1e1c97a31'){throw 'retired_candidate_drift'}
    $candidate=Get-Content -LiteralPath $predecessor -Raw|ConvertFrom-Json -DateKind String
    foreach($f in $candidate.files){$p=Join-Path (Join-Path $script:Root 'candidate-originals-r8') $f.path;Assert-NoReparse $p;if((Get-FileHash -LiteralPath $p).Hash.ToLowerInvariant() -cne $f.sha256){throw 'retired_candidate_original_drift'}}
    foreach($phase in 'audit-05','retire'){
        $dir=Join-Path $script:Root $phase
        $receiptPath=Join-Path $dir 'receipt.json'
        $receiptHash=if($phase -eq 'retire'){'062338c76b711175ce70143fe0d10f4e3d6c404bc9ab2e0f5252784f4aabd612'}else{'7dd5bfba77012c61dffc3220da59cabb4e07aa0bdaa6b507531673d53285ba03'}
        if((Get-FileHash -LiteralPath $receiptPath).Hash.ToLowerInvariant() -cne $receiptHash){throw 'retirement_receipt_bytes_changed'}
        $receipt=Get-Content -LiteralPath $receiptPath -Raw|ConvertFrom-Json -DateKind String
        if(-not $receipt.success -or $receipt.candidate_sha256 -cne $hash){throw 'retirement_evidence_not_passed'}
        foreach($f in $receipt.files){if([IO.Path]::GetFileName($f.name) -cne $f.name){throw 'retirement_evidence_path_escape'};$p=Join-Path $dir $f.name;Assert-NoReparse $p;if((Get-FileHash -LiteralPath $p).Hash.ToLowerInvariant() -cne $f.sha256){throw 'retirement_evidence_file_drift'}}
    }
}
function Assert-NoReparse([string]$Path) {
    $current = [IO.Path]::GetFullPath($Path)
    while ($current) {
        if (Test-Path -LiteralPath $current) {
            if ((Get-Item -LiteralPath $current -Force).Attributes -band [IO.FileAttributes]::ReparsePoint) {throw "reparse_path:$current"}
        }
        $next = [IO.Path]::GetDirectoryName($current)
        if ($next -eq $current) {break}; $current=$next
    }
}
function Get-RebuildRegistrations {
    @(Get-ChildItem -LiteralPath $script:Lxss | ForEach-Object {
        [pscustomobject]@{guid=$_.PSChildName;name=$_.GetValue('DistributionName');base=($_.GetValue('BasePath') -replace '^\\\\\?\\','').TrimEnd('\');version=$_.GetValue('Version');leaf=$_.GetValue('VhdFileName','ext4.vhdx')}
    })
}
function Assert-RebuildPolicy {
    $key=Get-Item -LiteralPath 'HKLM:\Software\Policies\WSL'
    foreach($name in 'AllowWSL','AllowInboxWSL','AllowWSL1','AllowKernelUserSetting','AllowSystemDistroUserSetting','AllowKernelCommandLineUserSetting','AllowDebugShell','AllowNestedVirtualization','AllowKernelDebugUserSetting','AllowDiskMount','AllowNetworkingModeUserSetting','AllowFirewallUserSetting','DefaultNetworkingMode') {
        $expected=if($name -ceq 'AllowWSL'){1}else{0}
        if($name -cnotin $key.GetValueNames() -or $key.GetValueKind($name) -ne 'DWord' -or [int]$key.GetValue($name) -ne $expected){throw "machine_policy_drift:$name"}
    }
    if((Get-Item 'C:\Program Files\WSL\wslservice.exe').VersionInfo.FileVersion -cne '2.6.3.0'){throw 'wsl_engine_drift'}
}
function Assert-RebuildOffline {
    if(@(Get-NetAdapter -Physical | Where-Object Status -eq 'Up').Count){throw 'physical_offline_required'}
}
function Assert-RebuildFenced {
    foreach($name in 'WslService','vmcompute') {
        $svc=Get-Service -Name $name
        if("$($svc.Status)" -cne 'Stopped' -or "$($svc.StartType)" -cne 'Disabled'){throw "service_not_fenced:$name"}
    }
    if(@(Get-Process -Name vmmemWSL,wslhost -ErrorAction SilentlyContinue).Count){throw 'guest_process_remains'}
}
function Assert-LegacyRetired {
    $r=Get-RebuildRegistrations
    if(@($r|Where-Object {$_.guid -ieq $script:OldGuid -or $_.name -ceq 'Ubuntu' -or $_.base -ieq $script:OldPath}).Count){throw 'old_registration_remains'}
    if(Test-Path -LiteralPath (Join-Path $script:OldPath 'ext4.vhdx')){throw 'old_filesystem_remains'}
    $b=@($r|Where-Object name -CEQ 'stage1-bootstrap')
    if($b.Count -ne 1 -or $b[0].guid -ine '{12952bda-9f18-434b-886c-090b3d7f5b5f}' -or $b[0].base -ine 'D:\WSL-Stage1\stage1-bootstrap'){throw 'preserved_bootstrap_drift'}
}
function Assert-NewRegistration([switch]$Initial) {
    $retire=Join-Path $script:Root 'retire\receipt.json'
    if(-not $Initial -and -not (Test-Path -LiteralPath $retire)){throw 'retirement_receipt_required'}
    Assert-LegacyRetired
    $r=@(Get-RebuildRegistrations|Where-Object name -CEQ $script:Distro)
    if($r.Count -ne 1 -or $r[0].base -ine $script:Install -or $r[0].version -ne 2 -or $r[0].leaf -cne 'ext4.vhdx'){throw 'new_registration_drift'}
    if((Get-Item $script:Lxss).GetValue('DefaultDistribution') -ine $r[0].guid){throw 'new_default_drift'}
    Assert-NoReparse $script:Install
    $identity=Get-RebuildFileIdentity
    $r[0]|Add-Member -NotePropertyName file_identity -NotePropertyValue $identity
    if(Test-Path -LiteralPath $retire){$retirementReceipt=Get-Content -LiteralPath $retire -Raw|ConvertFrom-Json -DateKind String;if(-not $retirementReceipt.success){throw 'retirement_not_passed'};Assert-RebuildIdentity $r[0] $retirementReceipt.new_registration}
    $r[0]
}
function Get-RebuildFileIdentity {
    $vhd=Join-Path $script:Install 'ext4.vhdx'
    $h=[AraCustodyHandle]::Open($vhd,0x20080,7)
    try{$parts=[AraCustodyHandle]::Binding($h,$vhd,$false).Split('|')}finally{$h.Dispose()}
    $parts[0]+'|'+$parts[1]+'|'+$parts[4]
}
function Assert-RebuildIdentity($Current,$Initial) {
    if($Current.guid -ine $Initial.guid -or $Current.base -ine $Initial.base -or $Current.file_identity -cne $Initial.file_identity){throw 'new_instance_identity_changed'}
}
function Invoke-RebuildWsl([string[]]$Arguments,[int]$Timeout=120000,[int]$Cap=12582912) {
    $result=[AraBoundedNative]::Run($script:Wsl,$Arguments,$Timeout,$Cap)
    if($result.Exit -ne 0){throw "wsl_failed:exit=$($result.Exit):$($result.Lines -join ' | ')"}
    $result
}
function Invoke-RebuildGuest([string]$Command,[int]$Timeout=120000) {
    # This channel carries scripts only. Binary receivers use direct argv and retain stdin.
    $Command=$Command.Replace("`r`n","`n")
    if($Command.Contains("`r")){throw 'guest_script_bare_cr_refused'}
    $b64=[Convert]::ToBase64String([Text.Encoding]::UTF8.GetBytes($Command))
    if($b64.Length -gt 1048576){throw 'guest_command_over_cap'}
    $wrapper='{ '+(Get-RebuildGuestFence)+'printf %s '+$b64+' | base64 -d | /bin/bash; } 2>&1'
    $r=Invoke-RebuildWsl @('-d',$script:Distro,'-u','root','--exec','/bin/sh','-c',$wrapper) $Timeout
    @($r.Lines) -join "`n"
}
function Get-RebuildGuestFence {
    # WSL2 registers this interpreter at VM level even when distro interop=false.
    # This VM contains only the new authorized guest during an offline window.
    # Disable only this entry and read procfs content (stat size is always zero).
    'set -eu; if test -e /proc/sys/fs/binfmt_misc/WSLInterop; then printf 0 > /proc/sys/fs/binfmt_misc/WSLInterop; test "$(head -n1 /proc/sys/fs/binfmt_misc/WSLInterop)" = disabled; fi; '
}
function Send-RebuildFile([string]$Source,[string]$Target,[long]$Cap=67108864) {
    if($Target -cnotmatch '^/(tmp/ara-rebuild|var/lib/ara-m1)/[A-Za-z0-9_./+~:-]+$' -or $Target.Split('/') -contains '..'){throw 'unsafe_guest_target'}
    $f=Get-Item -LiteralPath $Source
    if($f.Length -gt $Cap -or $f.Attributes -band [IO.FileAttributes]::ReparsePoint){throw 'input_shape_or_cap'}
    $expected=(Get-FileHash -LiteralPath $Source -Algorithm SHA256).Hash.ToLowerInvariant()
    $s=[IO.File]::OpenRead($Source)
    try {$r=[AraBoundedNative]::RunWithStdin($script:Wsl,@('-d',$script:Distro,'-u','root','--exec','/bin/sh','-c',('{ '+(Get-RebuildGuestFence)+'exec cat > '+$Target+'; } 2>&1')),$s,$f.Length,300000,1048576)} finally {$s.Dispose()}
    if(-not $r.InputComplete -or $r.Exit -ne 0 -or $r.BytesWritten -ne $f.Length){throw 'binary_transfer_incomplete'}
    $out=Invoke-RebuildGuest ('set -eu; test "$(wc -c < '+$Target+')" -eq '+$f.Length+'; printf "%s  %s\n" '+$expected+' '+$Target+' | sha256sum -c -')
    if($out -cnotmatch ([regex]::Escape($Target)+': OK')){throw 'guest_hash_mismatch'}
    [pscustomobject]@{target=$Target;bytes=$f.Length;sha256=$expected;verified=$true}
}
function Open-RebuildWindow([string]$PhaseDir) {
    Assert-RebuildPolicy; Assert-RebuildOffline; Assert-RebuildFenced
    Assert-NoReparse $script:Config
    $item=Get-Item -LiteralPath $script:Config -Force
    if((Get-FileHash -LiteralPath $script:Config).Hash.ToLowerInvariant() -cne $script:OriginalConfigHash){throw 'host_config_drift'}
    [IO.File]::Copy($script:Config,(Join-Path $PhaseDir 'original.wslconfig'),$false)
    Write-RebuildJson (Join-Path $PhaseDir 'config-binding.json') @{sha256=$script:OriginalConfigHash;mtime=$item.LastWriteTimeUtc.ToString('o');ctime=$item.CreationTimeUtc.ToString('o')}
    $config="[wsl2]`nmemory=1GB`nprocessors=1`nswap=0`nnetworkingMode=none`nguiApplications=false`nlocalhostForwarding=false`nnestedVirtualization=false`n"
    [IO.File]::WriteAllText($script:Config,$config,[Text.UTF8Encoding]::new($false))
    foreach($name in 'vmcompute','WslService') {Set-Service -Name $name -StartupType Manual; Start-Service -Name $name}
}
function Close-RebuildWindow([string]$PhaseDir) {
    if(-not (Test-Path -LiteralPath (Join-Path $PhaseDir 'config-binding.json'))){return}
    $failures=[Collections.Generic.List[string]]::new()
    try {
        $reg=@(Get-RebuildRegistrations|Where-Object name -CEQ $script:Distro)
        if($reg.Count){$null=[AraBoundedNative]::Run($script:Wsl,@('--terminate',$script:Distro),30000,65536)}
    }catch{$failures.Add('terminate:'+ $_.Exception.Message)}
    foreach($name in 'WslService','vmcompute') {
        try {Stop-Service -Name $name -Force -NoWait; Set-Service -Name $name -StartupType Disabled;(Get-Service $name).WaitForStatus('Stopped',[TimeSpan]::FromSeconds(30))}catch{$failures.Add('fence:'+ $name+':'+$_.Exception.Message)}
    }
    try {Assert-RebuildFenced}catch{$failures.Add($_.Exception.Message)}
    $saved=Join-Path $PhaseDir 'original.wslconfig'
    if(Test-Path -LiteralPath $saved) {
        try {
            if((Get-FileHash -LiteralPath $saved).Hash.ToLowerInvariant() -cne $script:OriginalConfigHash){throw 'saved_config_drift'}
            [IO.File]::WriteAllBytes($script:Config,[IO.File]::ReadAllBytes($saved))
            $binding=Get-Content -LiteralPath (Join-Path $PhaseDir 'config-binding.json') -Raw|ConvertFrom-Json -DateKind String
            [IO.File]::SetLastWriteTimeUtc($script:Config,[datetime]::Parse($binding.mtime).ToUniversalTime())
            if((Get-FileHash -LiteralPath $script:Config).Hash.ToLowerInvariant() -cne $script:OriginalConfigHash){throw 'config_restore_mismatch'}
        }catch{$failures.Add('config:'+ $_.Exception.Message)}
    }
    if($failures.Count){throw ('cleanup_unconfirmed:'+($failures -join '|'))}
}
function Get-RebuildBoot { (Get-CimInstance Win32_OperatingSystem).LastBootUpTime.ToUniversalTime().ToString('o') }
function Stop-RebuildServiceFence {
    foreach($name in 'WslService','vmcompute') {Stop-Service -Name $name -Force -NoWait;Set-Service -Name $name -StartupType Disabled;(Get-Service $name).WaitForStatus('Stopped',[TimeSpan]::FromSeconds(45))}
    Assert-RebuildFenced
}
function Stop-RebuildCoordinator($Intent) {
    $proc=Get-Process -Id ([int]$Intent.coordinator_pid) -ErrorAction SilentlyContinue
    if($null -eq $proc){return}
    if($proc.StartTime.ToUniversalTime().ToString('o') -cne $Intent.coordinator_started){throw 'watchdog_coordinator_pid_reused'}
    # Stop only this exact coordinator, not its tree (the watchdog is its child).
    # Its only native operation children are wsl.exe; snapshot them before stopping.
    $children=@(Get-CimInstance Win32_Process -Filter "ParentProcessId=$($proc.Id)"|Where-Object Name -CEQ 'wsl.exe'|Select-Object ProcessId,CreationDate)
    $proc.Kill();if(-not $proc.WaitForExit(10000)){throw 'coordinator_exit_unconfirmed'}
    foreach($child in $children){$p=Get-Process -Id ([int]$child.ProcessId) -ErrorAction SilentlyContinue;if($null -ne $p){if($p.StartTime.ToUniversalTime().ToString('yyyyMMddHHmmssffffff') -cne $child.CreationDate.ToUniversalTime().ToString('yyyyMMddHHmmssffffff')){throw 'native_child_pid_reused'};$p.Kill();if(-not $p.WaitForExit(10000)){throw 'native_child_exit_unconfirmed'}}}
}
function Restore-RebuildNetwork($Adapters) {
    foreach($adapter in $Adapters){$actual=@(Get-NetAdapter -Physical|Where-Object {([string]$_.InterfaceGuid) -ieq $adapter.guid});if($actual.Count -ne 1 -or $actual[0].Name -cne $adapter.name){throw 'adapter_identity_changed_during_restore'};$actual[0]|Enable-NetAdapter -Confirm:$false}
    $until=[datetime]::UtcNow.AddSeconds(30)
    do{$up=@(Get-NetAdapter -Physical|Where-Object {([string]$_.InterfaceGuid) -iin @($Adapters.guid) -and $_.Status -eq 'Up'});if($up.Count -eq $Adapters.Count){return};Start-Sleep -Seconds 1}while([datetime]::UtcNow -lt $until)
    throw 'original_network_links_not_up_after_restore'
}
function Restore-RebuildWindowConfig([string]$WorkSet) {
    $phases=switch($WorkSet){'RetireBootstrap'{@('bootstrap','retire')};'ResumeBootstrap03'{@('bootstrap-03')};'Install'{@('install')};'ResumePg06'{@('resumeinstall-06')};default{throw 'invalid_configuration_recovery_workset'}}
    foreach($phase in $phases){
        $dir=Join-Path $script:Root $phase
        $bindingPath=Join-Path $dir 'config-binding.json'
        if(-not (Test-Path -LiteralPath $bindingPath)){continue}
        $saved=Join-Path $dir 'original.wslconfig'
        Assert-NoReparse $saved;Assert-NoReparse $script:Config
        $binding=Get-Content -LiteralPath $bindingPath -Raw|ConvertFrom-Json -DateKind String
        if($binding.sha256 -cne $script:OriginalConfigHash -or (Get-FileHash -LiteralPath $saved).Hash.ToLowerInvariant() -cne $script:OriginalConfigHash){throw 'watchdog_saved_configuration_drift'}
        [IO.File]::WriteAllBytes($script:Config,[IO.File]::ReadAllBytes($saved))
        [IO.File]::SetLastWriteTimeUtc($script:Config,[datetime]::Parse($binding.mtime).ToUniversalTime())
        if((Get-FileHash -LiteralPath $script:Config).Hash.ToLowerInvariant() -cne $script:OriginalConfigHash){throw 'watchdog_configuration_restore_mismatch'}
        return
    }
    # No phase reached the configuration write; verify rather than invent a backup.
    if((Get-FileHash -LiteralPath $script:Config).Hash.ToLowerInvariant() -cne $script:OriginalConfigHash){throw 'configuration_changed_without_window_binding'}
}
function Complete-RebuildNetworkRecovery($Intent,[string]$Directory,[switch]$Watchdog) {
    # The watchdog revokes execution by terminating the bound coordinator before
    # acquiring cleanup ownership. A dead owner's abandoned mutex is recoverable.
    if($Watchdog){Stop-RebuildCoordinator $Intent}
    $mutex=[Threading.Mutex]::new($false,('Local\ARA-Stage1-Network-'+$Intent.workset))
    $held=$false
    try {
        try{$held=$mutex.WaitOne(10000)}catch [Threading.AbandonedMutexException]{$held=$true}
        if(-not $held){throw 'network_cleanup_owner_unavailable'}
        if(-not $Watchdog -and (Test-Path -LiteralPath (Join-Path $Directory 'cancelled.json'))){throw 'coordinator_cancelled_watchdog_owns_cleanup'}
        Stop-RebuildServiceFence
        Restore-RebuildWindowConfig $Intent.workset
        Restore-RebuildNetwork $Intent.adapters
    } finally {if($held){$mutex.ReleaseMutex()};$mutex.Dispose()}
}
Export-ModuleMember -Function *-Rebuild*,Assert-NoReparse,Assert-LegacyRetired,Assert-NewRegistration,Send-RebuildFile
