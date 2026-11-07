// B-direction read-only integrity primitive (ENV-M1-01 binding-drift-decision.md option B).
// Temporarily enables SeBackupPrivilege ONLY around a single CreateFile with
// FILE_READ_DATA|FILE_READ_ATTRIBUTES + FileShare.Read + FILE_FLAG_BACKUP_SEMANTICS,
// then streams SHA256 through that one bound handle. Never opens write/delete access,
// never modifies ACL/times/contents, never retries. Privilege is restored (disabled)
// deterministically; the caller token must not already have it enabled.
using System;
using System.ComponentModel;
using System.Runtime.InteropServices;
using System.Security.Cryptography;
using System.Security.Principal;
using System.Diagnostics;
using Microsoft.Win32.SafeHandles;

public sealed class AraIdentity {
    public uint VolumeSerial;
    public long FileIndex;
    public long Size;
    public long CreationFileTime;
    public long LastWriteFileTime;
}

public sealed class AraBoundReadResult {
    public bool Ok;
    public string ErrorKind;
    public string Win32Error;
    public AraIdentity Before;
    public AraIdentity After;
    public string Sha256;
    public long BytesRead;
    public long ElapsedMs;
    public int ReadCalls;
    public bool PrivilegePresent;
    public bool PrivilegeEnabledBefore;
    public bool PrivilegeEnabledDuring;
    public bool PrivilegeEnabledAfter;
    public bool PrivilegeRestoreVerified;
}

public static class AraIntegrityReadNative {
    const uint FILE_READ_DATA = 0x1;
    const uint FILE_READ_ATTRIBUTES = 0x80;
    const uint FILE_SHARE_READ = 0x1;
    const uint FILE_SHARE_WRITE = 0x2;
    const uint FILE_SHARE_DELETE = 0x4;
    const uint OPEN_EXISTING = 3;
    const uint FILE_FLAG_BACKUP_SEMANTICS = 0x02000000;
    const int TOKEN_QUERY = 0x8;
    const int TokenPrivilegesClass = 3;
    const uint SE_PRIVILEGE_ENABLED = 0x2;
    const int ERROR_NOT_ALL_ASSIGNED = 1300;
    const int ERROR_INSUFFICIENT_BUFFER = 122;
    public const string BackupPrivilegeName = "SeBackupPrivilege";

    [StructLayout(LayoutKind.Sequential)]
    private struct BY_HANDLE_FILE_INFORMATION {
        public uint FileAttributes;
        public uint CreationTimeLow; public uint CreationTimeHigh;
        public uint LastAccessTimeLow; public uint LastAccessTimeHigh;
        public uint LastWriteTimeLow; public uint LastWriteTimeHigh;
        public uint VolumeSerialNumber;
        public uint FileSizeHigh; public uint FileSizeLow;
        public uint NumberOfLinks;
        public uint FileIndexHigh; public uint FileIndexLow;
    }
    [StructLayout(LayoutKind.Sequential)]
    private struct LUID { public uint LowPart; public int HighPart; }
    [StructLayout(LayoutKind.Sequential)]
    private struct TOKEN_PRIVILEGES_ONE { public uint PrivilegeCount; public LUID Luid; public uint Attributes; }

    [DllImport("kernel32.dll", SetLastError = true, CharSet = CharSet.Unicode)]
    private static extern SafeFileHandle CreateFile(string name, uint access, uint share, IntPtr security,
        uint disposition, uint flags, IntPtr template);
    [DllImport("kernel32.dll", SetLastError = true)]
    private static extern bool GetFileInformationByHandle(SafeFileHandle h, out BY_HANDLE_FILE_INFORMATION info);
    [DllImport("kernel32.dll", SetLastError = true)]
    private static extern bool ReadFile(SafeFileHandle h, byte[] data, uint size, out uint count, IntPtr overlapped);
    [DllImport("advapi32.dll", SetLastError = true, CharSet = CharSet.Unicode)]
    private static extern bool LookupPrivilegeValue(string system, string name, out LUID luid);
    [DllImport("advapi32.dll", SetLastError = true)]
    private static extern bool AdjustTokenPrivileges(IntPtr token, bool disableAll,
        ref TOKEN_PRIVILEGES_ONE newState, uint bufferLen, IntPtr previous, IntPtr returnLength);
    [DllImport("advapi32.dll", SetLastError = true)]
    private static extern bool GetTokenInformation(IntPtr token, int kind, IntPtr info, uint length, out uint returnLength);

    // [0]=present, [1]=enabled on the current process token.
    public static bool[] PrivilegeState(string name) {
        LUID luid;
        if (!LookupPrivilegeValue(null, name, out luid)) throw new Win32Exception(Marshal.GetLastWin32Error());
        uint len;
        if (!GetTokenInformation(WindowsIdentity.GetCurrent().Token, TokenPrivilegesClass, IntPtr.Zero, 0, out len)) {
            int err = Marshal.GetLastWin32Error();
            if (err != ERROR_INSUFFICIENT_BUFFER) throw new Win32Exception(err);
        }
        IntPtr buf = Marshal.AllocHGlobal((int)len);
        try {
            if (!GetTokenInformation(WindowsIdentity.GetCurrent().Token, TokenPrivilegesClass, buf, len, out len))
                throw new Win32Exception(Marshal.GetLastWin32Error());
            int count = Marshal.ReadInt32(buf, 0);
            for (int i = 0; i < count; i++) {
                long raw = Marshal.ReadInt64(buf, 4 + i * 12);
                int attr = Marshal.ReadInt32(buf, 4 + i * 12 + 8);
                uint low = (uint)(raw & 0xffffffffL);
                int high = (int)(raw >> 32);
                if (low == luid.LowPart && high == luid.HighPart)
                    return new bool[] { true, (attr & (int)SE_PRIVILEGE_ENABLED) != 0 };
            }
            return new bool[] { false, false };
        } finally { Marshal.FreeHGlobal(buf); }
    }

    public static void SetPrivilege(string name, bool enable) {
        LUID luid;
        if (!LookupPrivilegeValue(null, name, out luid)) throw new Win32Exception(Marshal.GetLastWin32Error());
        TOKEN_PRIVILEGES_ONE tp;
        tp.PrivilegeCount = 1; tp.Luid = luid; tp.Attributes = enable ? SE_PRIVILEGE_ENABLED : 0;
        if (!AdjustTokenPrivileges(WindowsIdentity.GetCurrent().Token, false, ref tp, 0, IntPtr.Zero, IntPtr.Zero))
            throw new Win32Exception(Marshal.GetLastWin32Error());
        int err = Marshal.GetLastWin32Error();
        if (err == ERROR_NOT_ALL_ASSIGNED) throw new InvalidOperationException("integrity_privilege_not_held");
        if (err != 0) throw new Win32Exception(err);
    }

    // One bound handle: data-read + attributes only, share=read only, backup semantics.
    public static SafeFileHandle OpenBound(string path) {
        SafeFileHandle h = CreateFile(path, FILE_READ_DATA | FILE_READ_ATTRIBUTES, FILE_SHARE_READ,
            IntPtr.Zero, OPEN_EXISTING, FILE_FLAG_BACKUP_SEMANTICS, IntPtr.Zero);
        if (h.IsInvalid) throw new Win32Exception(Marshal.GetLastWin32Error());
        return h;
    }

    // Attributes-only metadata open with NO privilege and NO data access.
    public static SafeFileHandle OpenMetadata(string path) {
        SafeFileHandle h = CreateFile(path, FILE_READ_ATTRIBUTES, FILE_SHARE_READ | FILE_SHARE_WRITE | FILE_SHARE_DELETE,
            IntPtr.Zero, OPEN_EXISTING, FILE_FLAG_BACKUP_SEMANTICS, IntPtr.Zero);
        if (h.IsInvalid) throw new Win32Exception(Marshal.GetLastWin32Error());
        return h;
    }

    public static AraIdentity ReadIdentity(SafeFileHandle h) {
        BY_HANDLE_FILE_INFORMATION i;
        if (!GetFileInformationByHandle(h, out i)) throw new Win32Exception(Marshal.GetLastWin32Error());
        AraIdentity id = new AraIdentity();
        id.VolumeSerial = i.VolumeSerialNumber;
        id.FileIndex = ((long)i.FileIndexHigh << 32) | (long)i.FileIndexLow;
        id.Size = ((long)i.FileSizeHigh << 32) | (long)i.FileSizeLow;
        id.CreationFileTime = ((long)i.CreationTimeHigh << 32) | (long)i.CreationTimeLow;
        id.LastWriteFileTime = ((long)i.LastWriteTimeHigh << 32) | (long)i.LastWriteTimeLow;
        return id;
    }

    // Single-pass streaming SHA256 on the already-bound handle. 1MiB buffer, absolute deadline.
    public static string StreamHash(SafeFileHandle h, long maxBytes, int deadlineMs, out int readCalls, out long bytesRead) {
        readCalls = 0; bytesRead = 0;
        AraIdentity id = ReadIdentity(h);
        if (id.Size > maxBytes) throw new InvalidOperationException("integrity_size_over_cap");
        SHA256 sha = SHA256.Create();
        try {
            byte[] buf = new byte[1048576];
            Stopwatch sw = Stopwatch.StartNew();
            long total = 0;
            while (true) {
                if (deadlineMs > 0 && sw.ElapsedMilliseconds > deadlineMs)
                    throw new InvalidOperationException("integrity_deadline_exceeded");
                uint want = (uint)Math.Min((long)1048576, id.Size - total);
                if (want == 0) break;
                uint got;
                readCalls++;
                if (!ReadFile(h, buf, want, out got, IntPtr.Zero))
                    throw new Win32Exception(Marshal.GetLastWin32Error());
                if (got == 0) break;
                total += got;
                if (total > id.Size) throw new InvalidOperationException("integrity_size_grew_under_handle");
                sha.TransformBlock(buf, 0, (int)got, null, 0);
            }
            sha.TransformFinalBlock(buf, 0, 0);
            if (total != id.Size) throw new InvalidOperationException("integrity_short_read");
            bytesRead = total;
            string hex = BitConverter.ToString(sha.Hash).Replace("-", "");
            return hex.ToLowerInvariant();
        } finally { ((IDisposable)sha).Dispose(); }
    }

    // Orchestrated one-shot. Privilege lifecycle is entirely inside this call:
    // refuse-if-already-enabled -> enable -> open -> disable+verify -> read on the bound handle.
    public static AraBoundReadResult ReadBound(string path, long maxBytes, long expectedSize,
        uint expectedVolumeSerial, long expectedFileIndex, int deadlineMs) {
        AraBoundReadResult r = new AraBoundReadResult();
        SafeFileHandle h = null;
        try {
            bool[] st = PrivilegeState(BackupPrivilegeName);
            r.PrivilegePresent = st[0];
            r.PrivilegeEnabledBefore = st[1];
            if (!st[0]) { r.ErrorKind = "integrity_privilege_not_held"; return r; }
            if (st[1]) { r.ErrorKind = "integrity_privilege_already_enabled"; return r; }
            SetPrivilege(BackupPrivilegeName, true);
            r.PrivilegeEnabledDuring = true;
            try {
                h = OpenBound(path);
            } catch (Win32Exception w) {
                r.ErrorKind = "integrity_open_failed";
                r.Win32Error = w.NativeErrorCode.ToString();
                return r;
            } finally {
                SetPrivilege(BackupPrivilegeName, false);
                bool[] after = PrivilegeState(BackupPrivilegeName);
                r.PrivilegeEnabledAfter = after[1];
                r.PrivilegeRestoreVerified = after[0] && !after[1];
            }
            if (!r.PrivilegeRestoreVerified) {
                r.ErrorKind = "integrity_privilege_restore_unverified";
                return r;
            }
            r.Before = ReadIdentity(h);
            if (expectedSize >= 0 && r.Before.Size != expectedSize) {
                r.ErrorKind = "integrity_size_mismatch"; return r;
            }
            if (expectedVolumeSerial != 0 && r.Before.VolumeSerial != expectedVolumeSerial) {
                r.ErrorKind = "integrity_binding_refuse"; return r;
            }
            if (expectedFileIndex >= 0 && r.Before.FileIndex != expectedFileIndex) {
                r.ErrorKind = "integrity_binding_refuse"; return r;
            }
            Stopwatch sw = Stopwatch.StartNew();
            int calls; long read;
            r.Sha256 = StreamHash(h, maxBytes, deadlineMs, out calls, out read);
            r.ReadCalls = calls; r.BytesRead = read;
            r.ElapsedMs = sw.ElapsedMilliseconds;
            r.After = ReadIdentity(h);
            if (r.Before.VolumeSerial != r.After.VolumeSerial || r.Before.FileIndex != r.After.FileIndex ||
                r.Before.Size != r.After.Size || r.Before.CreationFileTime != r.After.CreationFileTime ||
                r.Before.LastWriteFileTime != r.After.LastWriteFileTime) {
                r.ErrorKind = "integrity_binding_drift_after_read";
                r.Sha256 = null;
                return r;
            }
            r.Ok = true;
            return r;
        } catch (Exception ex) {
            r.Ok = false;
            if (r.ErrorKind == null)
                r.ErrorKind = "integrity_failed:" + ex.GetType().Name + ":" + ex.Message;
            return r;
        } finally {
            if (h != null) h.Dispose();
        }
    }
}
