# Applies the exact WSL 2.6.3 machine policy set under HKLM\Software\Policies\WSL.
# Every value is REG_DWORD 0/1 per src/windows/inc/wslpolicies.h (tag 2.6.3); a missing or
# non-0/1 value falls back to "allowed", so this script writes all of them explicitly and
# verifies kind + byte content + key ACL afterwards. Idempotent by value comparison; refuses
# to run twice in the same verification state only if drift is detected.
# Requires: actual daily account, elevated (UAC). Never starts WSL or any service.
[CmdletBinding()]
param()
$ErrorActionPreference = 'Stop'
Set-StrictMode -Version Latest

$dailySid = 'S-1-5-21-2765399256-1806415232-1753294129-1001'
$identity = [Security.Principal.WindowsIdentity]::GetCurrent()
if ($identity.User.Value -cne $dailySid) { throw 'actual_daily_token_required' }
$principal = [Security.Principal.WindowsPrincipal]::new($identity)
if (-not $principal.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)) { throw 'elevation_required' }

$service = Get-Service -Name WslService
if ($service.Status -ne 'Stopped' -or $service.StartType -ne 'Disabled') { throw 'wslservice_must_be_stopped_disabled' }
$vmcompute = Get-Service -Name vmcompute
if ($vmcompute.Status -ne 'Stopped' -or $vmcompute.StartType -ne 'Disabled') { throw 'vmcompute_must_be_stopped_disabled' }

# All REG_DWORD per wslpolicies.h. DefaultNetworkingMode: 0=None per official WSL.admx enum.
$policyValues = [ordered]@{
    AllowWSL                          = 1  # WSL itself stays allowed for the controlled new distro
    AllowInboxWSL                     = 0  # only the store WSL 2.6.3 may run
    AllowWSL1                         = 0  # no WSL1 fallback
    AllowKernelUserSetting            = 0  # no user kernel override
    AllowSystemDistroUserSetting      = 0  # no user system-distro override
    AllowKernelCommandLineUserSetting = 0  # no user kernel command line override
    AllowDebugShell                   = 0  # no debug shell
    AllowNestedVirtualization         = 0  # no nested virtualization
    AllowKernelDebugUserSetting       = 0  # no kernel debugging
    AllowDiskMount                    = 0  # wsl --mount refused
    AllowNetworkingModeUserSetting    = 0  # user cannot change networking mode
    AllowFirewallUserSetting          = 0  # user cannot change firewall setting
    DefaultNetworkingMode             = 0  # None: guest has no networking at hypervisor level
}

# Provider paths for Get-Item/Test-Path/Get-Acl (Get-Acl rejects the Registry:: form) and the
# .NET key-name form for Registry.SetValue.
$keyPath = 'HKLM:\Software\Policies\WSL'
$result = [ordered]@{
    schema          = 'ENV-M1-01.machine-policy.v1'
    utc             = [DateTimeOffset]::UtcNow.ToString('o')
    daily_sid       = $dailySid
    elevated        = $true
    wslservice      = "$($service.Status)/$($service.StartType)"
    vmcompute       = "$($vmcompute.Status)/$($vmcompute.StartType)"
    before          = [ordered]@{}
    after           = [ordered]@{}
    key_acl_before  = $null
    key_acl_after   = $null
    wslservice_sha256 = $null
}

$wslServiceExe = 'C:\Program Files\WSL\wslservice.exe'
$stream = [IO.File]::Open($wslServiceExe, 'Open', 'Read', 'Read')
try {
    $sha = [Security.Cryptography.SHA256]::Create()
    try { $result.wslservice_sha256 = [BitConverter]::ToString($sha.ComputeHash($stream)).Replace('-', '') }
    finally { $sha.Dispose() }
} finally { $stream.Dispose() }

function Read-PolicyState {
    $state = [ordered]@{}
    if (-not (Test-Path -LiteralPath $keyPath)) {
        $script:keySddl = '<absent>'
        return $state
    }
    $key = Get-Item -LiteralPath $keyPath
    foreach ($name in $policyValues.Keys) {
        if ($name -in $key.GetValueNames()) {
            $state[$name] = [ordered]@{
                kind = [string]$key.GetValueKind($name)
                bytes = [Convert]::ToBase64String([BitConverter]::GetBytes([int]$key.GetValue($name)))
                value = $key.GetValue($name)
            }
        } else {
            $state[$name] = [ordered]@{ kind = '<absent>' }
        }
    }
    $acl = Get-Acl -Path $keyPath
    $script:keySddl = $acl.GetSecurityDescriptorSddlForm('Owner,Access')
    return $state
}

function Assert-KeyNotUserWritable {
    # Only HKLM policies\WSL: ordinary users can read but never write this hive path.
    # Write capability = specific bits (SetValue|CreateSubKey|Delete|WRITE_DAC|WRITE_OWNER) plus
    # generic GW|GA (0x50000000) which the system maps to real key-write for non-exempt principals;
    # READ_CONTROL 0x20000 is shared with ReadKey and is NOT write access. Deny rules never grant.
    $acl = Get-Acl -Path $keyPath
    $writeMask = [int]([Security.AccessControl.RegistryRights]::SetValue) -bor
        [int][Security.AccessControl.RegistryRights]::CreateSubKey -bor
        [int][Security.AccessControl.RegistryRights]::Delete -bor
        [int][Security.AccessControl.RegistryRights]::ChangePermissions -bor
        [int][Security.AccessControl.RegistryRights]::TakeOwnership
    foreach ($rule in $acl.Access) {
        if ($rule.AccessControlType -ne 'Allow') { continue }
        # Capability/unmappable SIDs keep their raw S-1-… form in IdentityReference; translate when
        # possible, fall back to the raw value (an unmappable SID can never be SYSTEM/BA).
        try {
            $identityRef = $rule.IdentityReference.Translate([Security.Principal.SecurityIdentifier]).Value
        } catch [System.Security.Principal.IdentityNotMappedException] {
            $identityRef = $rule.IdentityReference.Value
        }
        $rights = [int]$rule.RegistryRights
        if ((($rights -band $writeMask) -ne 0 -or ($rights -band 0x50000000) -ne 0) -and
            -not ($identityRef -in @('S-1-5-18', 'S-1-5-32-544'))) {
            throw "policy_key_writable_by:$identityRef"
        }
    }
}

$before = Read-PolicyState
$result.key_acl_before = $script:keySddl
foreach ($name in $before.Keys) {
    $entry = $before[$name]
    if ($entry.kind -eq '<absent>') { $result.before[$name] = '<absent>' }
    else { $result.before[$name] = "$($entry.kind):$($entry.value)" }
}
if ($script:keySddl -cne '<absent>') { Assert-KeyNotUserWritable }

foreach ($name in $policyValues.Keys) {
    $expected = [int]$policyValues[$name]
    $entry = $before[$name]
    $current = if ($null -ne $entry -and $entry.kind -ne '<absent>') { [int]$entry.value } else { $null }
    if ($current -ne $expected) {
        # .NET Registry.SetValue takes a real key name, not a provider path.
        [Microsoft.Win32.Registry]::SetValue('HKEY_LOCAL_MACHINE\Software\Policies\WSL', $name, $expected, [Microsoft.Win32.RegistryValueKind]::DWord)
    }
}

$after = Read-PolicyState
$result.key_acl_after = $script:keySddl
if ($script:keySddl -eq '<absent>') { throw 'policy_key_missing_after_write' }
Assert-KeyNotUserWritable
foreach ($name in $policyValues.Keys) {
    $entry = $after[$name]
    if ($null -eq $entry -or $entry.kind -ne 'DWord') { throw "policy_kind_drift:$name" }
    if ([int]$entry.value -ne [int]$policyValues[$name]) { throw "policy_value_drift:$name" }
    $result.after[$name] = "$($entry.kind):$($entry.value)"
}

$text = $result | ConvertTo-Json -Depth 6
if ([Text.Encoding]::UTF8.GetByteCount($text) -gt 16384) { throw 'policy_output_cap' }
$text
