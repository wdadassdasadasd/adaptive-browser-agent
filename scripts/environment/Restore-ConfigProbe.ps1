# Recovery only: no VM/service changes and no overwrites; exact retained original or fail.
[CmdletBinding()]
param()
$ErrorActionPreference='Stop'
Import-Module (Join-Path $PSScriptRoot 'ConfigProbe.psm1') -Force
Restore-ConfigProbe -Mode Real -Case policy-01
