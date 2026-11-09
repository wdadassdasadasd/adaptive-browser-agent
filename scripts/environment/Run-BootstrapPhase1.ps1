# Stage-1 controlled bootstrap window, phase 1: preflight, enable services, import (or resume)
# the derived distro, run synthetic first-boot negatives, perform the bounded offline APT solve,
# stop the VM. ELEVATED (UAC). Requires the human to have PHYSICALLY disconnected the network.
# Fail-closed: on failure the VM is terminated and services are set back to Disabled.
[CmdletBinding()]
param()
# Actual PreWindow found protected original last-write drift against the immutable seal.
# Keep research/VM closed. This is not cleared by source/config preparation or a new run ID.
throw 'ENV_M1_01_ORIGINAL_BINDING_DRIFT_CURRENT_FIRST_VM_GATE_CLOSED'
$ErrorActionPreference = 'Stop'
Set-StrictMode -Version Latest

$logRoot = 'D:\adaptive-browser-agent\.tmp\stage-1-1-resume-20261107\bootstrap\window-01'
New-Item -ItemType Directory -Force -Path $logRoot | Out-Null
$stamp = [DateTimeOffset]::UtcNow.ToString('yyyyMMddTHHmmssZ') -replace ':', ''
Start-Transcript -Path (Join-Path $logRoot "phase1-$stamp.log") | Out-Null

$dailySid = 'S-1-5-21-2765399256-1806415232-1753294129-1001'
$identity = [Security.Principal.WindowsIdentity]::GetCurrent()
if ($identity.User.Value -cne $dailySid) { throw 'actual_daily_token_required' }
$principal = [Security.Principal.WindowsPrincipal]::new($identity)
if (-not $principal.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)) { throw 'elevation_required' }

$tar = 'D:\adaptive-browser-agent\.tmp\stage-1-1-resume-20261107\bootstrap\stage1-bootstrap-derived.tar'
$installDir = 'D:\WSL-Stage1\stage1-bootstrap'
$wslExe = "$env:SystemRoot\System32\wsl.exe"
Add-Type -Path (Join-Path $PSScriptRoot 'BoundedNative.cs')

function Invoke-Wsl {
    # Direct executable invocation, never cmd /c. Capture raw pipes before decoding so native
    # stderr cannot become a PS5 terminating ErrorRecord. Guest payloads remain base64 ASCII.
    $deadline = if ($args[0] -eq '--terminate') { 30000 } else { 120000 }
    # 4MiB decoded -> 5,592,408 base64 characters -> at most ~11.2MiB UTF-16 transport.
    # This envelope includes host warnings; Read-GuestText enforces the original 4MiB cap.
    $r = [AraBoundedNative]::Run($wslExe, [string[]]$args, $deadline, 12582912)
    return [pscustomobject]@{ exit = $r.Exit; lines = @($r.Lines) }
}

function Read-GuestText([string]$Command) {
    $r = Invoke-Wsl -d stage1-bootstrap -u root -- sh -c $Command
    # Exact observed WSL2.6.3 zh-CN machine-policy warning, not arbitrary setting mentions.
    # Keep the script ASCII for Windows PowerShell 5.1's legacy source decoding.
    $policyPrefix=[Text.Encoding]::UTF8.GetString([Convert]::FromBase64String('6K6h566X5py6562W55Wl5bey56aB55SoIC53c2xjb25maWcg6K6+572u'))
    foreach($line in $r.lines) {
        foreach($setting in 'wsl2.kernelModules','wsl2.systemDistro','wsl2.kernel') {
            $pattern='^wsl:\s*'+[regex]::Escape($policyPrefix)+'['+[char]0x201c+'"]'+[regex]::Escape($setting)+'['+[char]0x201d+'"]['+[char]0x3002+'.]\s*$'
            if($line -cmatch $pattern) {
                if($script:policyOverrides -cnotcontains $setting){$script:policyOverrides+= $setting}
                Write-Output "POLICY_OVERRIDE_OBSERVED=$setting" | Out-Host
            }
        }
    }
    if ($r.exit -ne 0) { throw "guest_command_failed:exit=$($r.exit):$($r.lines -join ' | ')" }
    # Policy warnings are host stderr, never part of the base64 guest payload.
    $payloads = @($r.lines | Where-Object { $_ -cmatch '^ARA_B64=[A-Za-z0-9+/]*={0,2}$' })
    if ($payloads.Count -ne 1) { throw "guest_payload_count:$($payloads.Count)" }
    $encoded = $payloads[0].Substring(8)
    if ($encoded.Length -gt 5592408) { throw 'guest_encoded_output_over_cap' }
    $bytes = [Convert]::FromBase64String($encoded)
    if ($bytes.Length -gt 4194304) { throw 'guest_decoded_output_over_cap' }
    return (New-Object Text.UTF8Encoding($false, $true)).GetString($bytes)
}
$script:policyOverrides=@()
$configSession=$null

function Invoke-Step([string]$Name, [scriptblock]$Action) {
    Write-Output "STEP_BEGIN=$Name"
    # Stream diagnostics: buffering the action loses its output when the action throws.
    & $Action | Out-Host
    Write-Output "STEP_END=$Name"
}

function Assert-PolicyExact {
    $key = Get-Item -LiteralPath 'HKLM:\Software\Policies\WSL'
    foreach ($n in 'AllowWSL', 'AllowInboxWSL', 'AllowWSL1', 'AllowKernelUserSetting',
        'AllowSystemDistroUserSetting', 'AllowKernelCommandLineUserSetting', 'AllowDebugShell',
        'AllowNestedVirtualization', 'AllowKernelDebugUserSetting', 'AllowDiskMount',
        'AllowNetworkingModeUserSetting', 'AllowFirewallUserSetting', 'DefaultNetworkingMode') {
        if ($n -cnotin $key.GetValueNames()) { throw "policy_absent:$n" }
        if ($key.GetValueKind($n) -ne 'DWord') { throw "policy_kind:$n" }
        $expected = if ($n -ceq 'AllowWSL') { 1 } else { 0 }
        if ([int]$key.GetValue($n) -ne $expected) { throw "policy_value:$n" }
    }
    if ([int]$key.GetValue('DefaultNetworkingMode') -ne 0) { throw 'policy_networking_not_none' }
    if ([int]$key.GetValue('AllowDiskMount') -ne 0) { throw 'policy_diskmount_open' }
    if ([int]$key.GetValue('AllowWSL') -ne 1) { throw 'policy_wsl_closed' }
    'policy_verified_exact_13'
}

function Assert-Services([string]$Status, [string]$StartType) {
    foreach ($name in 'WslService', 'vmcompute') {
        $svc = Get-Service -Name $name
        if ("$($svc.Status)" -ne $Status -or "$($svc.StartType)" -ne $StartType) {
            throw "service_state:${name}:$($svc.Status)/$($svc.StartType) expected:$Status/$StartType"
        }
    }
    "$Status/$StartType verified"
}

function Assert-Offline {
    $up = @(Get-NetAdapter -Physical | Where-Object Status -eq 'Up')
    if ($up.Count -gt 0) { throw "physical_network_up:$($up.Count)_adapters" }
    'physical_offline_verified'
}

function Assert-GuestRegistered {
    $lxss = Get-ChildItem 'HKCU:\Software\Microsoft\Windows\CurrentVersion\Lxss' -ErrorAction SilentlyContinue
    foreach ($k in $lxss) {
        if ($k.GetValue('DistributionName') -ceq 'stage1-bootstrap') {
            return $k.PSChildName
        }
    }
    return $null
}

try {
    Invoke-Step 'preflight_policy' { Assert-PolicyExact | Write-Output }
    Invoke-Step 'preflight_engine_and_resources' {
        $version=(Get-Item -LiteralPath 'C:\Program Files\WSL\wslservice.exe').VersionInfo.FileVersion
        if($version -cne '2.6.3.0'){throw "wsl_binary_version_drift:$version"}
        $system=Get-CimInstance Win32_OperatingSystem
        if([long]$system.FreePhysicalMemory -lt 1572864){throw 'host_free_memory_below_1_5gib_for_1gib_probe'}
        $available=([IO.DriveInfo]::new('D:\')).AvailableFreeSpace
        if($available -lt 2147483648){throw 'host_work_volume_free_below_2gib'}
        "wsl_version=$version host_free_kib=$($system.FreePhysicalMemory) work_free_bytes=$available"
    }
    Invoke-Step 'preflight_offline' { Assert-Offline | Write-Output }
    Invoke-Step 'preflight_services_disabled' { Assert-Services 'Stopped' 'Disabled' | Write-Output }

    Invoke-Step 'bind_old_and_default_registration' {
        $lxss = 'HKCU:\Software\Microsoft\Windows\CurrentVersion\Lxss'
        $oldGuid = '{5bd0012b-1a62-445a-ad9e-da37f21ba704}'
        $all=@(Get-ChildItem -LiteralPath $lxss | ForEach-Object {$_.PSChildName} | Sort-Object)
        $expected=@('{12952bda-9f18-434b-886c-090b3d7f5b5f}',$oldGuid)|Sort-Object
        if(($all -join '|') -ine ($expected -join '|')){throw 'registered_distribution_set_drift'}
        if ((Get-Item -LiteralPath $lxss).GetValue('DefaultDistribution') -ine $oldGuid) { throw 'default_distribution_drift' }
        $old = Get-Item -LiteralPath "$lxss\$oldGuid"
        if ($old.GetValue('DistributionName') -cne 'Ubuntu' -or $old.GetValue('Version') -ne 2) { throw 'old_registration_drift' }
        $expectedOldPath = 'C:\Users\FFFFFF\AppData\Local\Packages\CanonicalGroupLimited.Ubuntu_79rhkp1fndgsc\LocalState'
        $oldPath = $old.GetValue('BasePath') -replace '^\\\\\?\\', ''
        if ($oldPath.TrimEnd('\') -ine $expectedOldPath -or $old.GetValue('VhdFileName', 'ext4.vhdx') -cne 'ext4.vhdx') { throw 'old_disk_pointer_drift' }
        'old_and_default_registered_disk_bound'
    }

    Invoke-Step 'custody_intact' {
        # Run the metadata-only checks in a fresh process before enabling either service.
        $ps = "$env:SystemRoot\System32\WindowsPowerShell\v1.0\powershell.exe"
        $r = [AraBoundedNative]::Run($ps, @('-NoProfile', '-NonInteractive', '-ExecutionPolicy', 'Bypass', '-File',
            (Join-Path $PSScriptRoot 'Verify-PostRestart.ps1'), '-PreWindow'), 60000, 65536)
        $r.Lines | Write-Output
        if ($r.Exit -ne 0 -or 'PRE_WINDOW_VERIFY_OK' -cnotin $r.Lines) { throw 'custody_preflight_failed' }
        if ((Get-FileHash -LiteralPath $tar -Algorithm SHA256).Hash -cne '6513C1E9004A25263CF8B8A9F94A81EBC7B780627050A21681C953FD844F52E4') { throw 'derived_tar_identity' }
        'custody_and_input_preflight_verified'
    }

    Invoke-Step 'bind_approved_existing_bootstrap_object' {
        # The human confirmed the existing import is legitimate. Bind the observed stopped
        # object for this next window; this observation does not re-attest its whole history.
        Add-Type -Path (Join-Path $PSScriptRoot 'CustodyNative.cs')
        $path = Join-Path $installDir 'ext4.vhdx'
        $h = [AraCustodyHandle]::Open($path, 0x20080, 7)
        try { $binding = [AraCustodyHandle]::Binding($h, $path, $false) }
        finally { $h.Dispose() }
        $expected = '13308238606664222418|8c101600000001000000000000000000|180355072|1|134385067867992073|134385093816688500'
        if (($binding.Split('|')[0..5] -join '|') -cne $expected) { throw 'bootstrap_object_changed_since_review_no_automatic_retry' }
        Write-Output "bootstrap_object_binding=$binding"
    }

    Invoke-Step 'prepare_public_policy_canaries' {
        Import-Module (Join-Path $PSScriptRoot 'ConfigProbe.psm1') -Force
        $canaryRoot='D:\adaptive-browser-agent\.tmp\stage-1-1-resume-20261107\config-canary-01'
        if(Test-Path -LiteralPath $canaryRoot){throw 'policy_canary_root_exists_no_retry'}
        New-Item -ItemType Directory -Path $canaryRoot | Out-Null
        foreach($leaf in 'kernel.img','modules.vhdx','system.vhdx') {
            $f=[IO.File]::Open((Join-Path $canaryRoot $leaf),'CreateNew','Write','Read')
            try{$bytes=[Text.Encoding]::ASCII.GetBytes("ARA_STAGE1_POLICY_CANARY_NOT_A_BOOT_ASSET`n");$f.Write($bytes,0,$bytes.Length);$f.Flush($true)}finally{$f.Dispose()}
        }
        $script:protectedCanary=Join-Path $canaryRoot 'protected-synthetic.vhdx'
        $f=[IO.File]::Open($script:protectedCanary,'CreateNew','Write','Read')
        try{$bytes=[Text.Encoding]::ASCII.GetBytes('SYNTHETIC_NOT_A_VHDX');$f.Write($bytes,0,$bytes.Length);$f.Flush($true)}finally{$f.Dispose()}
        $h=[AraCustodyHandle]::Open($script:protectedCanary,0x60080,7)
        try{[AraCustodyHandle]::SetAcl($h,'O:BAD:P(A;;0x120080;;;SY)(A;;0x120080;;;BA)')}finally{$h.Dispose()}
        try {
            $h=[AraCustodyHandle]::Open($script:protectedCanary,1,7);$h.Dispose();throw 'synthetic_canary_data_read_allowed'
        } catch {
            $err=$_.Exception;while($null -ne $err.InnerException){$err=$err.InnerException}
            if($err -isnot [ComponentModel.Win32Exception] -or $err.NativeErrorCode -ne 5){throw}
        }
        $h=[AraCustodyHandle]::Open($script:protectedCanary,0x120080,7)
        try{$binding=[AraCustodyHandle]::Binding($h,$script:protectedCanary,$false);Write-Output "SYNTHETIC_CANARY_BINDING=$binding"}finally{$h.Dispose()}
        $script:configSession=Start-ConfigProbe -Mode Real -Case policy-01
        'original_config_retained_canary_configuration_active'
    }

    Invoke-Step 'enable_services' {
        foreach ($name in 'WslService', 'vmcompute') {
            $null = & sc.exe config $name start= demand 2>&1
            if ($LASTEXITCODE -ne 0) { throw "sc_config_failed:$name" }
        }
        foreach ($name in 'WslService', 'vmcompute') {
            $null = & sc.exe start $name 2>&1 | Out-String
        }
        Start-Sleep -Seconds 3
        foreach ($name in 'WslService', 'vmcompute') {
            $svc = Get-Service -Name $name
            if ($svc.Status -ne 'Running') { throw "service_not_running:${name}:$($svc.Status)" }
        }
        'services_enabled_running'
    }

    Invoke-Step 'import_distro' {
        $registered = Assert-GuestRegistered
        $vhdx = Join-Path $installDir 'ext4.vhdx'
        if ($null -ne $registered -and (Test-Path -LiteralPath $vhdx)) {
            if ($registered -cne '{12952bda-9f18-434b-886c-090b3d7f5b5f}') { throw 'resumed_guid_drift' }
            $registration = Get-Item -LiteralPath "HKCU:\Software\Microsoft\Windows\CurrentVersion\Lxss\$registered"
            $basePath = $registration.GetValue('BasePath') -replace '^\\\\\?\\', ''
            if ($basePath.TrimEnd('\') -ine $installDir -or $registration.GetValue('Version') -ne 2) { throw 'resumed_registration_drift' }
            if ($registration.GetValue('VhdFileName', 'ext4.vhdx') -cne 'ext4.vhdx') { throw 'resumed_leaf_drift' }
            foreach ($path in 'D:\WSL-Stage1', $installDir, $vhdx) {
                if ((Get-Item -LiteralPath $path -Force).Attributes -band [IO.FileAttributes]::ReparsePoint) { throw 'resumed_reparse' }
            }
            # Resume: a prior attempt imported successfully but its stderr warning was
            # misreported as failure. Verify shape, continue without re-import.
            $vhdxSize = (Get-Item -LiteralPath $vhdx).Length
            Write-Output "RESUME_IMPORT registered=$registered vhdx_size=$vhdxSize"
            if ($vhdxSize -le 0 -or $vhdxSize -gt 1073741824) { throw 'resumed_vhdx_shape' }
            return 'import_resumed'
        }
        throw 'approved_existing_import_missing_no_reimport'
    }

    Invoke-Step 'guest_sanity' {
        $conf = Read-GuestText 'printf ARA_B64=; base64 -w0 /etc/wsl.conf && printf "\n"'
        Write-Output "wsl_conf: $conf"
        $sha = [Security.Cryptography.SHA256]::Create()
        try { $confHash = [BitConverter]::ToString($sha.ComputeHash([Text.Encoding]::UTF8.GetBytes($conf))).Replace('-', '').ToLowerInvariant() }
        finally { $sha.Dispose() }
        if ($confHash -cne '6012a35d99fd93d673badbc9b6a2e3a073ab6e15ba7ea4f71ff291bb8dca7b2c') { throw 'guest_config_drift' }
        $joined = Read-GuestText 'printf ARA_B64=; base64 -w0 /etc/os-release && printf "\n"'
        Write-Output "os_release: $joined"
        if ($joined -notmatch '(?m)^VERSION_ID="?24\.04"?\r?$') { throw 'unexpected_os_release' }
        Write-Output 'os_release_24_04_confirmed'
        'guest_sanity_ok'
    }

    Invoke-Step 'negative_readonly_config_override' {
        foreach($setting in 'wsl2.kernel','wsl2.kernelModules','wsl2.systemDistro') {
            if($script:policyOverrides -cnotcontains $setting){throw "machine_policy_override_not_observed:$setting"}
        }
        'all_three_untrusted_config_paths_ignored_with_live_guest_positive_control'
    }

    Invoke-Step 'negative_synthetic_attach_and_import' {
        # Fixed WSL2.6.3 AttachDisk checks AllowDiskMount BEFORE opening the disk. Invalid
        # format is irrelevant only if the exact policy-denial code is observed.
        $r=Invoke-Wsl --mount --vhd $script:protectedCanary --bare
        $output=$r.lines -join ' | '
        Write-Output "SYNTHETIC_ATTACH_EXIT=$($r.exit) OUTPUT=$output"
        if($r.exit -eq 0 -or $output -notmatch 'WSL_E_DISK_MOUNT_DISABLED'){throw 'synthetic_attach_not_policy_denial'}
        $lxss='HKCU:\Software\Microsoft\Windows\CurrentVersion\Lxss'
        $before=@(Get-ChildItem -LiteralPath $lxss | ForEach-Object {$_.PSChildName} | Sort-Object)
        if(@(Get-ChildItem -LiteralPath $lxss | Where-Object {$_.GetValue('DistributionName') -ceq 'stage1-protected-negative'}).Count){throw 'synthetic_import_name_already_exists'}
        $r=Invoke-Wsl --import-in-place stage1-protected-negative $script:protectedCanary
        $output=$r.lines -join ' | '
        Write-Output "SYNTHETIC_IMPORT_EXIT=$($r.exit) OUTPUT=$output"
        if($r.exit -eq 0 -or $output -notmatch 'E_ACCESSDENIED|ERROR_ACCESS_DENIED|0x80070005'){throw 'synthetic_import_not_access_denied'}
        $after=@(Get-ChildItem -LiteralPath $lxss | ForEach-Object {$_.PSChildName} | Sort-Object)
        if(($before -join '|') -cne ($after -join '|')){throw 'synthetic_import_changed_registration_preserve_partial_no_cleanup'}
        'synthetic_attach_and_import_denied_no_real_disk_used'
    }

    Invoke-Step 'ordinary_token_policy_negatives' {
        $ready=Join-Path $logRoot 'ordinary-negative-ready.json'
        $result=Join-Path $logRoot 'ordinary-negative-result.json'
        if((Test-Path -LiteralPath $ready) -or (Test-Path -LiteralPath $result)){throw 'ordinary_window_marker_exists_no_retry'}
        $f=[IO.File]::Open($ready,'CreateNew','Write','Read')
        try{$bytes=[Text.Encoding]::ASCII.GetBytes('{"state":"ready"}');$f.Write($bytes,0,$bytes.Length);$f.Flush($true)}finally{$f.Dispose()}
        Write-Output 'WINDOW_PHASE=awaiting_ordinary_token_negatives'
        $deadline=[DateTimeOffset]::UtcNow.AddSeconds(90)
        while(-not(Test-Path -LiteralPath $result)) {
            if([DateTimeOffset]::UtcNow -ge $deadline){throw 'ordinary_token_negatives_timeout_no_retries'}
            Start-Sleep -Milliseconds 500
        }
        $f=[IO.File]::Open($result,'Open','Read','Read')
        try {
            if($f.Length -le 0 -or $f.Length -gt 16384){throw 'ordinary_result_cap'}
            $reader=[IO.StreamReader]::new($f,[Text.Encoding]::UTF8)
            try{$ordinary=$reader.ReadToEnd()|ConvertFrom-Json}finally{$reader.Dispose()}
        }finally{$f.Dispose()}
        if($ordinary.state -cne 'ordinary_negatives_passed'){throw 'ordinary_result_not_passed'}
        'ordinary_token_policy_negatives_complete'
    }

    Invoke-Step 'negative_old_distro_boot' {
        $r = Invoke-Wsl -d Ubuntu -- /bin/true
        if ($r.exit -eq 0) { throw 'OLD_DISTRO_BOOTED_UNEXPECTEDLY' }
        $out = ($r.lines -join ' | ')
        if ($out -notmatch 'E_ACCESSDENIED|ERROR_ACCESS_DENIED|0x80070005') { throw "old_refusal_not_access_denied:$out" }
        "old_distro_boot_refused exit=$($r.exit) out=$($out.Substring(0, [Math]::Min(300, $out.Length)))"
    }

    Invoke-Step 'negative_default_distro' {
        $r = Invoke-Wsl -- /bin/true
        if ($r.exit -eq 0) { throw 'DEFAULT_DISTRO_BOOTED_UNEXPECTEDLY' }
        $out = ($r.lines -join ' | ')
        if ($out -notmatch 'E_ACCESSDENIED|ERROR_ACCESS_DENIED|0x80070005') { throw "default_refusal_not_access_denied:$out" }
        "default_distro_refused exit=$($r.exit) out=$($out.Substring(0, [Math]::Min(300, $out.Length)))"
    }

    Invoke-Step 'negative_guest_network_none' {
        $routes = Read-GuestText 'printf ARA_B64=; base64 -w0 /proc/net/route && printf "\n"'
        $lines = @($routes -split "`n" | Where-Object { $_.Trim() -and $_ -notmatch '^\s*Iface' })
        if ($lines.Count -ne 0) { throw "guest_routes_present:$($lines.Count)" }
        $devices = Read-GuestText 'printf ARA_B64=; base64 -w0 /proc/net/dev && printf "\n"'
        $interfaces = @($devices -split "`n" | Where-Object { $_ -match ':' } | ForEach-Object { ($_ -split ':', 2)[0].Trim() })
        if ($interfaces.Count -ne 1 -or $interfaces[0] -cne 'lo') { throw 'guest_non_loopback_interface' }
        Write-Output "net_route: $routes"
        Write-Output "net_dev: $devices"
        'guest_no_routes_network_none'
    }

    Invoke-Step 'negative_host_share_and_interop' {
        $mounts = Read-GuestText 'printf ARA_B64=; base64 -w0 /proc/mounts && printf "\n"'
        if ($mounts -match '(?m)^\S+\s+\S+\s+(drvfs|9p)\s' -or $mounts -match '/mnt/wslg') { throw 'guest_host_or_gui_share_present' }
        Read-GuestText 'set -eu; test ! -e /mnt/c; test ! -e /proc/sys/fs/binfmt_misc/WSLInterop; test -z "${WSL_INTEROP-}"; if command -v cmd.exe >/dev/null 2>&1; then exit 21; fi; printf ARA_B64=; printf no_host_drive_or_interop | base64 -w0; printf "\n"' | Write-Output
        'guest_host_share_and_interop_absent'
    }

    Invoke-Step 'normalize_authenticated_index_names' {
        # Repair only the three already-imported, authenticated payload names. No reimport,
        # no network, no package installation. Refuse unexpected duplicates or bytes.
        foreach ($entry in @(
            @('noble', '8f6f71ae839c8cba390a7643fcbbdacddb0bc7d12c1583a2dd80a1f8443a30e5'),
            @('noble-updates', 'caafce0abc3621247a817fc29dc0ccf2a58d9734119fe01b54e6c20a5ddce67f'),
            @('noble-security', 'e45480701a5ebc5163d91faa71e71d836c79cb084870639e4fdc8c67ac4afae0')
        )) {
            $stem = '/var/lib/apt/lists/snapshot.ubuntu.com_ubuntu_20261021T000000Z_dists_' + $entry[0]
            $old = $stem + '_Packages'
            $target = $stem + '_main_binary-amd64_Packages'
            $command = 'set -eu; old=' + $old + '; target=' + $target + '; hash=' + $entry[1] + '; ' +
                'if test -e "$target"; then test ! -e "$old"; file=$target; else file=$old; fi; ' +
                'printf "%s  %s\n" "$hash" "$file" | sha256sum -c - > /tmp/index-check.txt; ' +
                'if test "$file" = "$old"; then mv -n "$old" "$target"; test ! -e "$old"; fi; ' +
                'printf "%s  %s\n" "$hash" "$target" | sha256sum -c - >> /tmp/index-check.txt; ' +
                'printf ARA_B64=; base64 -w0 /tmp/index-check.txt; printf "\n"'
            Read-GuestText $command | Write-Output
        }
        'index_names_authenticated_and_normalized_before_simulation_binding'
    }

    Invoke-Step 'apt_solve_pre_binding' {
        $script:preStatus = Read-GuestText 'sha256sum /var/lib/dpkg/status > /tmp/status-pre.txt && printf ARA_B64= && base64 -w0 /tmp/status-pre.txt && printf "\n"'
        $script:preLists = Read-GuestText 'cd /var/lib/apt/lists && find . -type f -exec sha256sum {} \; > /tmp/lists-pre.txt && printf ARA_B64= && base64 -w0 /tmp/lists-pre.txt && printf "\n"'
        $preStatus | Set-Content -LiteralPath (Join-Path $logRoot 'apt-solve-pre-dpkg-status.sha256')
        $preLists | Set-Content -LiteralPath (Join-Path $logRoot 'apt-solve-pre-lists.sha256')
        'pre_binding_recorded'
    }

    Invoke-Step 'apt_solve' {
        $solveOut = Join-Path $logRoot 'apt-solve-output.txt'
        $pins = 'postgresql-16=16.15-0ubuntu0.24.04.1', 'postgresql-client-16=16.15-0ubuntu0.24.04.1',
            'postgresql-common=257build1', 'postgresql-client-common=257build1',
            'systemd=255.4-1ubuntu8', 'systemd-sysv=255.4-1ubuntu8'
        # Keep the requested simulation; Print-URIs must be a separate no-install pass because
        # the simulator returns before URI emission in APT's InstallPackages control flow.
        # Print-URIs exits before acquisition; Download-Only is a second installation fence.
        $noWriteOptions = '-o Debug::NoLocking=1 -o Dir::Cache::pkgcache= -o Dir::Cache::srcpkgcache= '
        $command = 'ulimit -f 8192 && apt-get ' + $noWriteOptions + '--print-uris -s -y install ' + ($pins -join ' ') +
            ' > /tmp/simulation.txt 2>&1 && apt-get ' + $noWriteOptions + '--print-uris --download-only -y install ' + ($pins -join ' ') +
            ' > /tmp/uris.txt 2>&1 && test $(wc -c < /tmp/uris.txt) -le 4194304 && printf ARA_B64= && base64 -w0 /tmp/uris.txt && printf "\n"'
        $text = Read-GuestText $command
        [IO.File]::WriteAllText($solveOut, $text, (New-Object System.Text.UTF8Encoding($false)))
        $size = (Get-Item -LiteralPath $solveOut).Length
        if ($size -gt 4194304) { throw "solve_output_over_cap:$size" }
        Write-Output "solve_output_bytes=$size encoding=utf8_via_guest_base64"
        $simulation = Read-GuestText 'printf ARA_B64=; base64 -w0 /tmp/simulation.txt && printf "\n"'
        [IO.File]::WriteAllText((Join-Path $logRoot 'apt-simulation-output.txt'), $simulation, (New-Object Text.UTF8Encoding($false)))
        'solve_completed_simulated_no_write'
    }

    Invoke-Step 'apt_solve_post_binding' {
        $postStatus = Read-GuestText 'sha256sum /var/lib/dpkg/status > /tmp/status-post.txt && printf ARA_B64= && base64 -w0 /tmp/status-post.txt && printf "\n"'
        $postLists = Read-GuestText 'cd /var/lib/apt/lists && find . -type f -exec sha256sum {} \; > /tmp/lists-post.txt && printf ARA_B64= && base64 -w0 /tmp/lists-post.txt && printf "\n"'
        $postStatus | Set-Content -LiteralPath (Join-Path $logRoot 'apt-solve-post-dpkg-status.sha256')
        $postLists | Set-Content -LiteralPath (Join-Path $logRoot 'apt-solve-post-lists.sha256')
        if ($postStatus -cne $preStatus) { throw 'dpkg_status_changed_during_simulation' }
        if ($postLists -cne $preLists) { throw 'lists_changed_during_simulation' }
        'post_binding_identical_simulation_wrote_nothing'
    }

    Invoke-Step 'uri_list_nonempty' {
        $solveText = [IO.File]::ReadAllText((Join-Path $logRoot 'apt-solve-output.txt'))
        if ($solveText -notmatch "(?m)^'https://snapshot\.ubuntu\.com/ubuntu/20261021T000000Z/pool/") { throw 'simulation_did_not_produce_uri_list_no_fetch' }
        'uri_list_present_pending_authenticated_whole_plan_validation'
    }

    Invoke-Step 'terminate_vm' {
        $terminated = Invoke-Wsl --terminate stage1-bootstrap
        if ($terminated.exit -ne 0) { throw 'terminate_failed' }
        Start-Sleep -Seconds 3
        'terminate_command_succeeded_pending_service_and_process_fence'
    }

    Invoke-Step 'disable_services' {
        foreach ($name in 'WslService', 'vmcompute') {
            $null = & sc.exe stop $name 2>&1 | Out-String
            $null = & sc.exe config $name start= disabled 2>&1
            if ($LASTEXITCODE -ne 0) { throw "sc_disable_failed:$name" }
        }
        Start-Sleep -Seconds 2
        Assert-Services 'Stopped' 'Disabled' | Write-Output
        $guests = @(Get-Process -Name 'vmmemWSL', 'wslhost' -ErrorAction SilentlyContinue)
        if ($guests.Count) { throw 'wsl_processes_remain_after_service_fence' }
        'services_disabled_again'
    }

    Invoke-Step 'restore_original_configuration' {
        Close-ConfigProbe $configSession
        $script:configSession=$null
        Restore-ConfigProbe -Mode Real -Case policy-01 | Write-Output
        'same_original_config_object_restored_before_network_restore'
    }

    Write-Output 'WINDOW_PHASE=vm_stopped_awaiting_network_restore'
    'PHASE1_RESULT=OK'
    exit 0
} catch {
    Write-Output "PHASE1_FAILURE=$($_.Exception.Message)"
    $cleanupFailures = @()
    try {
        $terminated = Invoke-Wsl --terminate stage1-bootstrap
        if ($terminated.exit -ne 0) { $cleanupFailures += "terminate_exit:$($terminated.exit)" }
    } catch { $cleanupFailures += "terminate_exception:$($_.Exception.Message)" }
    foreach ($name in 'WslService', 'vmcompute') {
        try {
            $null = & sc.exe stop $name 2>&1 | Out-String
            $null = & sc.exe config $name start= disabled 2>&1
            if ($LASTEXITCODE -ne 0) { $cleanupFailures += "disable_failed:$name" }
        } catch { $cleanupFailures += "service_exception:${name}:$($_.Exception.Message)" }
    }
    foreach ($name in 'WslService', 'vmcompute') {
        try {
            $state = Get-Service -Name $name
            $state.WaitForStatus('Stopped', [TimeSpan]::FromSeconds(15))
            $state.Refresh()
            Write-Output "CLEANUP_SERVICE=${name}:$($state.Status)/$($state.StartType)"
            if ($state.Status -ne 'Stopped' -or $state.StartType -ne 'Disabled') { $cleanupFailures += "service_not_fenced:$name" }
        } catch { $cleanupFailures += "service_verify:${name}:$($_.Exception.Message)" }
    }
    if($null -ne $configSession) {
        Close-ConfigProbe $configSession
        $script:configSession=$null
    }
    $savedConfig='C:\Users\FFFFFF\.ara-stage1-policy-probe-20261107\original.wslconfig'
    if(-not $cleanupFailures.Count -and (Test-Path -LiteralPath $savedConfig)) {
        try { Restore-ConfigProbe -Mode Real -Case policy-01 | Write-Output }
        catch { $cleanupFailures+="config_restore_unknown:$($_.Exception.Message)" }
    }
    Write-Output "CLEANUP_FAILURES=$($cleanupFailures -join ' | ')"
    if ($cleanupFailures.Count) { Write-Output 'WINDOW_PHASE=failed_cleanup_unconfirmed' }
    'PHASE1_RESULT=FAILED'
    exit 1
} finally {
    Stop-Transcript | Out-Null
}
