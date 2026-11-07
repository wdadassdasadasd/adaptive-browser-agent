// Only small config reads and three fixed no-replace leaf renames. No ACL or VHDX writes.
using System;
using System.ComponentModel;
using System.Runtime.InteropServices;
using System.Text;
using Microsoft.Win32.SafeHandles;

public static class AraConfigProbeNative {
    [StructLayout(LayoutKind.Sequential)]
    private struct IoStatus { public IntPtr Status; public UIntPtr Information; }
    [DllImport("ntdll.dll")]
    private static extern int NtSetInformationFile(SafeFileHandle h, out IoStatus io, byte[] data, uint size, int kind);
    [DllImport("ntdll.dll")]
    private static extern uint RtlNtStatusToDosError(int status);
    [DllImport("kernel32.dll", SetLastError=true)]
    private static extern bool SetFilePointerEx(SafeFileHandle h, long offset, out long position, uint method);
    [DllImport("kernel32.dll", SetLastError=true)]
    private static extern bool ReadFile(SafeFileHandle h, byte[] data, uint size, out uint count, IntPtr overlapped);

    public static byte[] ReadConfig(SafeFileHandle h, int size) {
        if (size < 1 || size > 16384) throw new InvalidOperationException("config_read_cap");
        long position;
        if (!SetFilePointerEx(h, 0, out position, 0)) throw new Win32Exception(Marshal.GetLastWin32Error());
        byte[] data = new byte[size];
        uint read;
        if (!ReadFile(h, data, (uint)size, out read, IntPtr.Zero)) throw new Win32Exception(Marshal.GetLastWin32Error());
        if (read != size) throw new InvalidOperationException("config_short_read");
        return data;
    }

    public static void RenameNoReplace(SafeFileHandle source, SafeFileHandle destination, string leaf) {
        if (IntPtr.Size != 8 || (leaf != ".wslconfig" && leaf != "original.wslconfig" && leaf != "observed-canary.wslconfig"))
            throw new InvalidOperationException("config_rename_leaf_not_permitted");
        byte[] name = Encoding.Unicode.GetBytes(leaf);
        byte[] data = new byte[22 + name.Length];
        bool held = false;
        try {
            destination.DangerousAddRef(ref held);
            BitConverter.GetBytes(destination.DangerousGetHandle().ToInt64()).CopyTo(data, 8);
            BitConverter.GetBytes(name.Length).CopyTo(data, 16);
            name.CopyTo(data, 20);
            IoStatus io;
            int status = NtSetInformationFile(source, out io, data, (uint)data.Length, 10);
            if (status != 0) throw new Win32Exception((int)RtlNtStatusToDosError(status));
        } finally { if (held) destination.DangerousRelease(); }
    }
}
