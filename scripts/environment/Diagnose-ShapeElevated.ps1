# Elevated diagnostic for the object_shape_changed anomaly on the original ext4.vhdx.
# Opens the file exactly like AraCustodyHandle.Open (same flags/share) and dumps the raw
# FILE_BASIC_INFO / FILE_STANDARD_INFO bytes plus the final path, without changing anything.
[CmdletBinding()]
param()
$ErrorActionPreference = 'Stop'
Set-StrictMode -Version Latest

$src = @'
using System;
using System.ComponentModel;
using System.Runtime.InteropServices;
using System.Text;
using Microsoft.Win32.SafeHandles;
public static class ShapeDiag {
    [DllImport("kernel32.dll", CharSet = CharSet.Unicode, SetLastError = true)]
    private static extern SafeFileHandle CreateFileW(string path, uint access, uint share,
        IntPtr security, uint disposition, uint flags, IntPtr template);
    [DllImport("kernel32.dll", SetLastError = true)]
    private static extern bool GetFileInformationByHandleEx(SafeFileHandle handle,
        int informationClass, byte[] result, uint length);
    [DllImport("kernel32.dll", CharSet = CharSet.Unicode, SetLastError = true)]
    private static extern uint GetFinalPathNameByHandleW(SafeFileHandle handle,
        StringBuilder path, uint capacity, uint flags);

    public static string Probe(string path) {
        SafeFileHandle h = CreateFileW(path, 0x20080, 7, IntPtr.Zero, 3, 0x02200000, IntPtr.Zero);
        if (h.IsInvalid) throw new Win32Exception(Marshal.GetLastWin32Error());
        try {
            StringBuilder final = new StringBuilder(32768);
            uint len = GetFinalPathNameByHandleW(h, final, (uint)final.Capacity, 0);
            byte[] basic = new byte[40];
            byte[] standard = new byte[24];
            byte[] id = new byte[24];
            bool b1 = GetFileInformationByHandleEx(h, 0, basic, 40);
            bool b2 = GetFileInformationByHandleEx(h, 1, standard, 24);
            bool b3 = GetFileInformationByHandleEx(h, 18, id, 24);
            int e1 = b1 ? 0 : Marshal.GetLastWin32Error();
            int e2 = b2 ? 0 : Marshal.GetLastWin32Error();
            int e3 = b3 ? 0 : Marshal.GetLastWin32Error();
            return string.Format(
                "final={0}|basicOK={1} basicErr={2} attrs=0x{3:X} reparse={4}|standardOK={5} standardErr={6} links={7} deletePending={8} directory={9}|idOK={10} idErr={11} vol=0x{12:X}",
                final.ToString(), b1, e1, BitConverter.ToUInt32(basic, 32),
                (BitConverter.ToUInt32(basic, 32) & 0x400) != 0,
                b2, e2, BitConverter.ToUInt32(standard, 16), standard[20], standard[21],
                b3, e3, BitConverter.ToUInt64(id, 0));
        } finally { h.Dispose(); }
    }
}
'@
Add-Type -TypeDefinition $src

$path = 'C:\Users\FFFFFF\AppData\Local\Packages\CanonicalGroupLimited.Ubuntu_79rhkp1fndgsc\LocalState\ext4.vhdx'
$item = Get-Item -LiteralPath $path -Force
"item_attrs=$($item.Attributes) len=$($item.Length)"
[ShapeDiag]::Probe($path)

# Then the exact production path: the real CustodyNative open + Binding on the same object.
$nativePath = Join-Path $PSScriptRoot 'CustodyNative.cs'
$nativeSource = [IO.File]::ReadAllBytes($nativePath)
$sha = [Security.Cryptography.SHA256]::Create()
try {
    $digest = [BitConverter]::ToString($sha.ComputeHash($nativeSource)).Replace('-', '')
} finally { $sha.Dispose() }
"custody_native_sha256=$digest"
Add-Type -TypeDefinition ([Text.Encoding]::UTF8.GetString($nativeSource))
try {
    $h = [AraCustodyHandle]::Open($path, 0x20080, 7)
    try {
        $binding = [AraCustodyHandle]::Binding($h, $path, $false)
        "CUSTODY_BINDING_OK binding=$binding"
    } finally { $h.Dispose() }
} catch {
    $inner = $_.Exception
    while ($inner.InnerException) { $inner = $inner.InnerException }
    "CUSTODY_BINDING_FAILED inner=$($inner.GetType().Name):$($inner.Message)"
}

# H5 controls: the quarantined copy and a plain control file through the same probe.
foreach ($p in @('C:\ProgramData\ARA-Stage1-Archive-20261106\capture\Ubuntu.vhdx.pending',
        'C:\Users\FFFFFF\.wslconfig')) {
    try { "$([IO.Path]::GetFileName($p)) probe: " + [ShapeDiag]::Probe($p) }
    catch { "$([IO.Path]::GetFileName($p)) probe FAILED: $($_.Exception.Message)" }
}

# H2: exclusive open (share=0) detects any other open handle via ERROR_SHARING_VIOLATION.
try {
    $h0 = [AraCustodyHandle]::Open($path, 0x20080, 0)
    $h0.Dispose()
    'exclusive_open=OK_no_other_openers_detected_by_this_probe'
} catch {
    $inner = $_.Exception
    while ($inner.InnerException) { $inner = $inner.InnerException }
    $code = if ($inner -is [ComponentModel.Win32Exception]) { $inner.NativeErrorCode } else { -1 }
    "exclusive_open=CONFLICT win32=$code (32 means another handle exists)"
}

# H3: token privilege state (SeBackup/SeRestore enabled in THIS process would alter opens).
$priv = & whoami /priv 2>&1
"privileges:"
$priv | ForEach-Object { "  $_" }
