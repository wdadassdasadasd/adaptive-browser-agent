[CmdletBinding()]
param([Parameter(Mandatory)][ValidateSet('Audit','Retire','Bootstrap','Install','ResumeInstall','Verify','PostRestart')][string]$Phase)
$ErrorActionPreference='Stop'
Set-StrictMode -Version Latest
Import-Module (Join-Path $PSScriptRoot 'StageOneRebuild.psm1') -Force
Assert-RebuildRuntime
$s=Get-RebuildSettings
Assert-NoReparse $s.Root
$null=New-Item -ItemType Directory -Path $s.Root -Force
$phaseName=if($Phase -eq 'Audit'){'audit-05'}elseif($Phase -eq 'Bootstrap'){'bootstrap-03'}elseif($Phase -eq 'ResumeInstall'){'resumeinstall-06'}else{$Phase.ToLowerInvariant()}
$phaseDir=Join-Path $s.Root $phaseName
if(Test-Path -LiteralPath $phaseDir){throw 'phase_already_attempted_preserve_no_retry'}
$null=New-Item -ItemType Directory -Path $phaseDir
$started=[DateTimeOffset]::UtcNow.ToString('o')
$window=$false
$success=$false
$failure=$null
$cleanup=$null
$evidence=[ordered]@{schema='ENV-M1-01.rebuild-phase/1';phase=$Phase;started=$started;boot=Get-RebuildBoot;candidate_sha256=Assert-RebuildCandidate;research='closed';memory='disabled';browser=0;legacy_unknown='preserved_unresolved';checks=@()}
Start-Transcript -LiteralPath (Join-Path $phaseDir 'transcript.txt') | Out-Null
try {
    Assert-RebuildPolicy
    if($Phase -notin @('Audit','Retire')){Assert-RebuildRetirementEvidence}
    $tar=Join-Path $s.LegacyRoot 'bootstrap\stage1-bootstrap-derived.tar'
    if((Get-FileHash -LiteralPath $tar).Hash.ToLowerInvariant() -cne '6513c1e9004a25263cf8b8a9f94a81ebc7b780627050a21681c953fd844f52e4'){throw 'derived_tar_drift'}
    switch($Phase) {
        Audit {
            Assert-RebuildFenced
            $evidence.registered=Get-RebuildRegistrations
            $evidence.free_bytes=([IO.DriveInfo]::new('D:\')).AvailableFreeSpace
            $evidence.free_memory_kib=(Get-CimInstance Win32_OperatingSystem).FreePhysicalMemory
            $evidence.policy='exact_13'
            # Only matching subject identities are recorded, never arbitrary command text.
            $pattern='(?i)(wsl(\.exe)?|ubuntu|bash\.exe|WSL-Stage1|CanonicalGroupLimited|ara[-_ ]|adaptive-browser|research[-_ ]|worker)'
            $nonExecActions=0
            $tasks=@(Get-ScheduledTask|Where-Object {($_.Actions|ForEach-Object{if($_.PSObject.Properties['Execute']){"$($_.Execute) $($_.Arguments)"}else{$nonExecActions++}}) -match $pattern}|Select-Object TaskPath,TaskName,State)
            $services=@(Get-CimInstance Win32_Service|Where-Object {$_.PathName -match $pattern}|Select-Object Name,State,StartMode)
            $run=@()
            foreach($path in 'HKCU:\Software\Microsoft\Windows\CurrentVersion\Run','HKCU:\Software\Microsoft\Windows\CurrentVersion\RunOnce','HKLM:\Software\Microsoft\Windows\CurrentVersion\Run','HKLM:\Software\WOW6432Node\Microsoft\Windows\CurrentVersion\Run') {
                if(Test-Path $path){$key=Get-Item $path;foreach($name in $key.GetValueNames()){if([string]$key.GetValue($name) -match $pattern){$run+=@{key=$path;name=$name}}}}
            }
            $startup=@()
            $shell=New-Object -ComObject WScript.Shell
            foreach($folder in [Environment]::GetFolderPath('Startup'),[Environment]::GetFolderPath('CommonStartup')) {
                foreach($f in @(Get-ChildItem -LiteralPath $folder -File)) {
                    if($f.Extension -ieq '.lnk'){$lnk=$shell.CreateShortcut($f.FullName);$text="$($lnk.TargetPath) $($lnk.Arguments)"}else{$text=if($f.Length -le 65536){Get-Content -LiteralPath $f.FullName -Raw}else{'unread_over_cap'}}
                    if($text -match $pattern -or $text -eq 'unread_over_cap'){$startup+=@{path=$f.FullName;unread=($text -eq 'unread_over_cap')}}
                }
            }
            $wmi=@(Get-CimInstance -Namespace root/subscription -ClassName CommandLineEventConsumer|Where-Object {$_.ExecutablePath -match $pattern -or $_.CommandLineTemplate -match $pattern}|Select-Object Name)
            $other=@();$unreadHives=@()
            # Get-ChildItem opens every HKEY_USERS child, including protected unrelated
            # hives. Enumerate names first; record denied/non-target hives as uncovered.
            foreach($sid in [Microsoft.Win32.Registry]::Users.GetSubKeyNames()){
                $key=$null
                try{$key=[Microsoft.Win32.Registry]::Users.OpenSubKey($sid+'\Software\Microsoft\Windows\CurrentVersion\Lxss');if($null -ne $key){foreach($name in $key.GetSubKeyNames()){$sub=$key.OpenSubKey($name);try{$other+=@{sid=$sid;name=$sub.GetValue('DistributionName');base=$sub.GetValue('BasePath')}}finally{$sub.Dispose()}}}}
                catch [System.Security.SecurityException]{$unreadHives+=$sid}
                catch [System.UnauthorizedAccessException]{$unreadHives+=$sid}
                finally{if($null -ne $key){$key.Dispose()}}
            }
            $evidence.startup_surface=@{tasks=$tasks;services=$services;run=$run;startup=$startup;wmi=$wmi;loaded_user_registrations=$other;unread_user_hives=$unreadHives;non_exec_task_actions=$nonExecActions;coverage='direct_exec_tasks_services_run_startup_command_WMI_readable_loaded_hives; denied_and_unloaded_hives_and_COM_internals_unassessed; no_whole_host_claim; hostile_admin_excluded'}
            # WSL's own service is expected; other matching services require attribution.
            $blockingServices=@($services|Where-Object {$_.Name -notin @('WslService','LxssManager') -and $_.StartMode -ne 'Disabled'})
            if($tasks.Count -or $run.Count -or $startup.Count -or $wmi.Count -or $blockingServices.Count){throw 'startup_surface_requires_attribution'}
            $evidence.checks+= 'direct_startup_surfaces_enumerated_unread_hives_reported'
        }
        Retire {
            $audit=Get-Content -LiteralPath (Join-Path $s.Root 'audit-05\receipt.json') -Raw|ConvertFrom-Json -DateKind String
            if(-not $audit.success -or $audit.candidate_sha256 -cne $evidence.candidate_sha256){throw 'audit_not_passed_same_candidate'}
            Assert-RebuildOffline;Assert-RebuildFenced
            $regs=Get-RebuildRegistrations
            $old=@($regs|Where-Object guid -IEQ $s.OldGuid)
            if($regs.Count -ne 2 -or $old.Count -ne 1 -or $old[0].name -cne 'Ubuntu' -or $old[0].base -ine $s.OldPath -or $old[0].version -ne 2 -or $old[0].leaf -cne 'ext4.vhdx'){throw 'exact_retirement_target_drift'}
            Assert-NoReparse $s.OldPath
            if(Test-Path -LiteralPath $s.Install){throw 'new_install_path_exists'}
            Assert-NoReparse $s.Install
            $file=Get-Item -LiteralPath (Join-Path $s.OldPath 'ext4.vhdx') -Force
            $evidence.retired_before=@{registration=$old[0];bytes=$file.Length;mtime=$file.LastWriteTimeUtc.ToString('o');acl=(Get-Acl -LiteralPath $file.FullName).Sddl}
            # No old guest command and no old content read. Unregister is the authorized
            # destructive operation; no ACL reset or recursive filesystem deletion follows.
            $window=$true;Open-RebuildWindow $phaseDir
            $null=Invoke-RebuildWsl @('--unregister','Ubuntu') 120000 65536
            Assert-LegacyRetired
            $evidence.checks+='exact_old_registration_and_filesystem_absent'
            $null=Invoke-RebuildWsl @('--import',$s.Distro,$s.Install,$tar,'--version','2') 120000 65536
            $null=Invoke-RebuildWsl @('--set-default',$s.Distro) 30000 65536
            $evidence.new_registration=Assert-NewRegistration -Initial
        }
        Bootstrap {
            $null=Assert-NewRegistration
            $window=$true;Open-RebuildWindow $phaseDir
            $null=Invoke-RebuildGuest 'set -eu; test -d /tmp/ara-rebuild; test "$(ls -A /tmp/ara-rebuild)" = "$(printf "interop-denied.txt\ninterop-probe.exe")"'
            $probe=Send-RebuildFile (Join-Path $env:SystemRoot 'System32\whoami.exe') '/tmp/ara-rebuild/interop-probe-03.exe'
            Write-RebuildJson (Join-Path $phaseDir 'interop-probe-transfer.json') $probe
            $scriptText=Get-Content -LiteralPath (Join-Path $PSScriptRoot 'rebuild\bootstrap.sh') -Raw
            $output=Invoke-RebuildGuest $scriptText 120000
            [IO.File]::WriteAllText((Join-Path $phaseDir 'guest.txt'),$output,[Text.UTF8Encoding]::new($false))
            if($output -cnotmatch '(?m)^BOOTSTRAP_CHECKS_OK$'){throw 'bootstrap_checks_incomplete'}
            $uris=Invoke-RebuildGuest 'set -eu; printf ARA_B64=; base64 -w0 /tmp/ara-rebuild/uris.txt; printf "\n"'
            $line=@($uris -split "`n"|Where-Object {$_ -cmatch '^ARA_B64=[A-Za-z0-9+/]*={0,2}$'})
            if($line.Count -ne 1){throw 'uri_frame_missing'}
            $bytes=[Convert]::FromBase64String($line[0].Substring(8))
            if($bytes.Length -gt 4194304){throw 'solve_output_over_cap'}
            [IO.File]::WriteAllBytes((Join-Path $phaseDir 'apt-solve-output.txt'),$bytes)
            $evidence.checks+='source_residue_offline_hostshare_and_apt_solve'
        }
        Install {
            $null=Assert-NewRegistration
            $fetch=Get-Content -LiteralPath (Join-Path $s.Root 'fetch-02\debs\fetch-summary.json') -Raw|ConvertFrom-Json -DateKind String
            if($fetch.complete -ne $true -or $fetch.planned -lt 1 -or $fetch.planned -gt 400){throw 'fetch_not_complete'}
            $receipts=@(Get-ChildItem -LiteralPath (Join-Path $s.Root 'fetch-02\debs') -Filter '*.receipt.json'|ForEach-Object{Get-Content -LiteralPath $_.FullName -Raw|ConvertFrom-Json -DateKind String})
            if($receipts.Count -ne $fetch.planned){throw 'fetch_receipt_count'}
            foreach($r in $receipts){if($r.state -cne 'fetched_verified' -or $r.sha256 -cnotmatch '^[0-9a-f]{64}$' -or $r.size -le 0 -or $r.size -gt 67108864){throw 'receipt_shape'}; $leaf=$r.filename.Split('/')[-1];if($leaf -cnotmatch '^[A-Za-z0-9_+.~:-]+\.deb$'){throw 'unsafe_deb_leaf'}; $p=Join-Path $s.Root ('fetch-02\debs\'+$leaf);if((Get-Item -LiteralPath $p).Length -ne $r.size -or (Get-FileHash -LiteralPath $p).Hash.ToLowerInvariant() -cne $r.sha256){throw 'deb_receipt_drift'}}
            $window=$true;Open-RebuildWindow $phaseDir
            $null=Invoke-RebuildGuest 'set -eu; umask 077; test ! -e /tmp/ara-rebuild/install-attempt; touch /tmp/ara-rebuild/install-attempt; mkdir -m700 /tmp/ara-rebuild/debs'
            $sent=@()
            foreach($r in $receipts){$leaf=$r.filename.Split('/')[-1];$sent+=Send-RebuildFile (Join-Path $s.Root ('fetch-02\debs\'+$leaf)) ('/tmp/ara-rebuild/debs/'+$leaf)}
            $sent+=Send-RebuildFile (Join-Path $PSScriptRoot 'rebuild\qualify_pg.sh') '/tmp/ara-rebuild/qualify_pg.sh'
            $sent+=Send-RebuildFile (Join-Path $PSScriptRoot 'rebuild\role_probe.sql') '/tmp/ara-rebuild/role_probe.sql'
            Write-RebuildJson (Join-Path $phaseDir 'transfers.json') $sent
            $out=Invoke-RebuildGuest 'set -eu; /bin/bash /tmp/ara-rebuild/qualify_pg.sh' 300000
            [IO.File]::WriteAllText((Join-Path $phaseDir 'guest.txt'),$out,[Text.UTF8Encoding]::new($false))
            if($out -cnotmatch '(?m)^PG_QUALIFICATION_OK$'){throw 'pg_qualification_incomplete'}
            $evidence.checks+='signed_debs_binary_transfer_auth_roles_cgroup_concurrency_crash_stop'
        }
        ResumeInstall {
            $null=Assert-NewRegistration
            $window=$true;Open-RebuildWindow $phaseDir
            $originalTransfers=Join-Path $s.Root 'install\transfers.json'
            if((Get-FileHash $originalTransfers).Hash.ToLowerInvariant() -cne '796be3b041a3bad655f717cd10948cafab21854a59d673d99ea6989ae7ff17d0'){throw 'original_install_transfers_drift'}
            $transfers=@(Get-Content $originalTransfers -Raw|ConvertFrom-Json -DateKind String)
            if($transfers.Count -ne 99){throw 'original_transfer_count'}
            $fetchPath=Join-Path $s.Root 'fetch-02\debs\fetch-summary.json'
            if((Get-FileHash $fetchPath).Hash.ToLowerInvariant() -cne '261f601e73e3ed709db367cb668eea126d4bbfb68e6dd99aff4488637fd4fb8e'){throw 'original_fetch_summary_drift'}
            $fetch=Get-Content $fetchPath -Raw|ConvertFrom-Json -DateKind String
            if(-not $fetch.complete -or $fetch.planned -ne 97 -or $fetch.results.Count -ne 97){throw 'original_fetch_not_complete'}
            foreach($package in $fetch.results){
                $leaf=$package.filename.Split('/')[-1]
                $match=@($transfers|Where-Object target -CEQ ('/tmp/ara-rebuild/debs/'+$leaf))
                if($package.state -cne 'fetched_verified' -or $match.Count -ne 1 -or $match[0].sha256 -cne $package.sha256 -or $match[0].bytes -ne $package.size){throw 'signed_fetch_transfer_mismatch'}
            }
            $checks=@('set -eu; test "$(find /tmp/ara-rebuild/debs -maxdepth 1 -type f -name "*.deb" | wc -l)" -eq 97')
            foreach($f in $transfers){
                if(-not $f.verified -or $f.sha256 -cnotmatch '^[a-f0-9]{64}$' -or $f.target -cnotmatch '^/tmp/ara-rebuild/[A-Za-z0-9_./+~:-]+$' -or $f.target.Split('/') -contains '..'){throw 'original_transfer_shape'}
                $checks+='test "$(wc -c < '+$f.target+')" -eq '+$f.bytes+'; printf "%s  %s\n" '+$f.sha256+' '+$f.target+' | sha256sum -c -'
            }
            $verified=@()
            for($offset=0;$offset -lt $checks.Count;$offset+=8){
                $last=[Math]::Min($offset+7,$checks.Count-1)
                $verified+=Invoke-RebuildGuest ("set -eu`n"+($checks[$offset..$last] -join "`n"))
            }
            $verified=$verified -join "`n"
            [IO.File]::WriteAllText((Join-Path $phaseDir 'original-guest-reverified.txt'),$verified,[Text.UTF8Encoding]::new($false))
            $sent=Send-RebuildFile (Join-Path $PSScriptRoot 'rebuild\resume_pg.sh') '/tmp/ara-rebuild/resume-pg.sh'
            Write-RebuildJson (Join-Path $phaseDir 'resume-transfer.json') $sent
            $out=Invoke-RebuildGuest 'set -eu; /bin/bash /tmp/ara-rebuild/resume-pg.sh' 300000
            [IO.File]::WriteAllText((Join-Path $phaseDir 'guest.txt'),$out,[Text.UTF8Encoding]::new($false))
            if($out -cnotmatch '(?m)^PG_RESUMED_QUALIFICATION_OK$'){throw 'resumed_pg_qualification_incomplete'}
            $evidence.checks+='noninteractive_pending_configuration_auth_roles_cgroup_concurrency_crash_stop'
        }
        {$_ -in 'Verify','PostRestart'} {
            Assert-RebuildFenced
            $evidence.new_registration=Assert-NewRegistration
            foreach($required in 'audit-05','retire','bootstrap-03','resumeinstall-06') {
                $receipt=Get-Content -LiteralPath (Join-Path $s.Root "$required\receipt.json") -Raw|ConvertFrom-Json -DateKind String
                $expectedCandidate=if($required -in @('audit-05','retire')){'6c12c59e3d03b7a928d72bfdb03ba80f40f48199b416338d2edac4b1e1c97a31'}elseif($required -eq 'bootstrap-03'){'fd277bbf3ae0523b9ecee50255c14dc347994be3319719c899d1b795ca4263a3'}else{$evidence.candidate_sha256}
                if(-not $receipt.success -or $receipt.candidate_sha256 -cne $expectedCandidate){throw "required_phase_not_passed_bound_candidate:$required"}
                foreach($file in $receipt.files){$p=Join-Path $s.Root ($required+'\'+$file.name);if((Get-FileHash -LiteralPath $p).Hash.ToLowerInvariant() -cne $file.sha256){throw "phase_evidence_drift:$required"}}
            }
            $hash=(Get-FileHash -LiteralPath 'C:\Users\FFFFFF\.wslconfig').Hash.ToLowerInvariant()
            if($hash -cne '43edeb6c23a0be2aebd4a63db88b464b6362308c8d32812184966ecde26f01d2'){throw 'host_config_not_restored'}
            if($Phase -eq 'PostRestart'){$before=Get-Content (Join-Path $s.Root 'verify\receipt.json') -Raw|ConvertFrom-Json -DateKind String;if(-not $before.success -or $before.boot -ceq $evidence.boot){throw 'host_restart_not_proven'}}
            $evidence.checks+='closed_receipts_old_absent_new_identity_config_restored'
        }
    }
    $success=$true
} catch {
    $failure=$_.Exception.Message
    $evidence.failure_position=$_.InvocationInfo.PositionMessage
    $evidence.failure_stack=$_.ScriptStackTrace
    Write-Output "REBUILD_FAILURE=$failure"
} finally {
    if($window){try{Close-RebuildWindow $phaseDir}catch{$cleanup=$_.Exception.Message;$success=$false}}
    $evidence.success=$success;$evidence.failure=$failure;$evidence.cleanup_failure=$cleanup;$evidence.closed=[DateTimeOffset]::UtcNow.ToString('o')
    Stop-Transcript | Out-Null
    $evidence.files=@(Get-ChildItem -LiteralPath $phaseDir -File|ForEach-Object{@{name=$_.Name;sha256=(Get-FileHash -LiteralPath $_.FullName).Hash.ToLowerInvariant()}})
    Write-RebuildJson (Join-Path $phaseDir 'receipt.json') $evidence
}
if(-not $success){throw "rebuild_phase_failed:${Phase}:${failure}:${cleanup}"}
Write-Output "REBUILD_PHASE_OK=$Phase"
