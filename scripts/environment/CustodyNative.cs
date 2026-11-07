using System;
using System.ComponentModel;
using System.Linq;
using System.Runtime.InteropServices;
using System.Security.AccessControl;
using System.Text;
using Microsoft.Win32.SafeHandles;

public static class AraCustodyHandle {
    [DllImport("kernel32.dll", CharSet = CharSet.Unicode, SetLastError = true)]
    private static extern SafeFileHandle CreateFileW(string path, uint access, uint share,
        IntPtr security, uint disposition, uint flags, IntPtr template);
    [DllImport("kernel32.dll", CharSet = CharSet.Unicode, SetLastError = true)]
    private static extern uint GetFinalPathNameByHandleW(SafeFileHandle handle,
        StringBuilder path, uint capacity, uint flags);
    [DllImport("kernel32.dll", SetLastError = true)]
    private static extern bool GetFileInformationByHandleEx(SafeFileHandle handle,
        int informationClass, byte[] result, uint length);
    [DllImport("kernel32.dll", SetLastError = true)]
    private static extern bool DeviceIoControl(SafeFileHandle handle, uint code,
        byte[] input, uint inputLength, byte[] output, uint outputLength,
        out uint returned, IntPtr overlapped);
    [DllImport("kernel32.dll", SetLastError = true)]
    private static extern bool ReadFile(SafeFileHandle handle, byte[] output, uint length,
        out uint returned, IntPtr overlapped);
    [DllImport("advapi32.dll")]
    private static extern uint GetSecurityInfo(SafeFileHandle handle, uint type, uint flags,
        IntPtr owner, IntPtr group, IntPtr dacl, IntPtr sacl, out IntPtr descriptor);
    [DllImport("advapi32.dll")]
    private static extern uint SetSecurityInfo(SafeFileHandle handle, uint type, uint flags,
        byte[] owner, IntPtr group, byte[] dacl, IntPtr sacl);
    [DllImport("advapi32.dll")]
    private static extern uint GetSecurityDescriptorLength(IntPtr descriptor);
    [DllImport("kernel32.dll")]
    private static extern IntPtr LocalFree(IntPtr pointer);

    public static SafeFileHandle Open(string path, uint access, uint share) {
        SafeFileHandle handle = CreateFileW(path, access, share, IntPtr.Zero, 3, 0x02200000, IntPtr.Zero);
        if (handle.IsInvalid) {
            int error = Marshal.GetLastWin32Error();
            handle.Dispose();
            throw new Win32Exception(error);
        }
        return handle;
    }

    private static byte[] Info(SafeFileHandle handle, int kind, int size) {
        byte[] result = new byte[size];
        if (!GetFileInformationByHandleEx(handle, kind, result, (uint)size))
            throw new Win32Exception(Marshal.GetLastWin32Error());
        return result;
    }

    public static string Binding(SafeFileHandle handle, string path, bool directory) {
        StringBuilder final = new StringBuilder(32768);
        uint length = GetFinalPathNameByHandleW(handle, final, (uint)final.Capacity, 0);
        if (length == 0 || length >= final.Capacity || final.ToString() != "\\\\?\\" + path)
            throw new InvalidOperationException("final_path_changed");
        byte[] id = Info(handle, 18, 24);
        byte[] basic = Info(handle, 0, 40);
        byte[] standard = Info(handle, 1, 24);
        if ((BitConverter.ToUInt32(basic, 32) & 0x400) != 0 || standard[20] != 0 || (standard[21] != 0) != directory)
            throw new InvalidOperationException("object_shape_changed");
        byte[] usn = new byte[1024];
        uint used;
        if (!DeviceIoControl(handle, 0x000900EB, new byte[] {3, 0, 3, 0}, 4,
            usn, (uint)usn.Length, out used, IntPtr.Zero))
            throw new Win32Exception(Marshal.GetLastWin32Error());
        string fileId = BitConverter.ToString(id, 8, 16).Replace("-", "").ToLowerInvariant();
        if (used < 76 || used > usn.Length || BitConverter.ToUInt32(usn, 0) != used ||
            BitConverter.ToUInt32(usn, 4) != 3 ||
            BitConverter.ToString(usn, 8, 16).Replace("-", "").ToLowerInvariant() != fileId)
            throw new InvalidOperationException("usn_shape_changed");
        return String.Join("|", new string[] {
            BitConverter.ToUInt64(id, 0).ToString(), fileId,
            BitConverter.ToInt64(standard, 8).ToString(), BitConverter.ToUInt32(standard, 16).ToString(),
            BitConverter.ToInt64(basic, 0).ToString(), BitConverter.ToInt64(basic, 16).ToString(),
            BitConverter.ToInt64(usn, 40).ToString()
        });
    }

    public static string ReadAcl(SafeFileHandle handle) {
        IntPtr descriptor;
        uint result = GetSecurityInfo(handle, 1, 5, IntPtr.Zero, IntPtr.Zero, IntPtr.Zero, IntPtr.Zero, out descriptor);
        if (result != 0) throw new Win32Exception((int)result);
        try {
            uint length = GetSecurityDescriptorLength(descriptor);
            if (length == 0 || length > 65536) throw new InvalidOperationException("descriptor_size");
            byte[] bytes = new byte[length];
            Marshal.Copy(descriptor, bytes, 0, bytes.Length);
            return new RawSecurityDescriptor(bytes, 0).GetSddlForm(AccessControlSections.Owner | AccessControlSections.Access);
        } finally { LocalFree(descriptor); }
    }

    public static void SetAcl(SafeFileHandle handle, string sddl) {
        RawSecurityDescriptor wanted = new RawSecurityDescriptor(sddl);
        if (wanted.Owner == null || wanted.DiscretionaryAcl == null || wanted.DiscretionaryAcl.Count == 0 ||
            (wanted.ControlFlags & ControlFlags.DiscretionaryAclProtected) == 0)
            throw new InvalidOperationException("acl_shape");
        byte[] owner = new byte[wanted.Owner.BinaryLength];
        byte[] acl = new byte[wanted.DiscretionaryAcl.BinaryLength];
        wanted.Owner.GetBinaryForm(owner, 0);
        wanted.DiscretionaryAcl.GetBinaryForm(acl, 0);
        bool setOwner = !new RawSecurityDescriptor(ReadAcl(handle)).Owner.Equals(wanted.Owner);
        uint result = SetSecurityInfo(handle, 1, setOwner ? 0x80000005 : 0x80000004,
            setOwner ? owner : null, IntPtr.Zero, acl, IntPtr.Zero);
        if (result != 0) throw new Win32Exception((int)result);
        RawSecurityDescriptor actual = new RawSecurityDescriptor(ReadAcl(handle));
        if (!actual.Owner.Equals(wanted.Owner) || actual.DiscretionaryAcl == null ||
            (actual.ControlFlags & ControlFlags.DiscretionaryAclProtected) == 0)
            throw new InvalidOperationException("acl_readback_changed");
        byte[] currentAcl = new byte[actual.DiscretionaryAcl.BinaryLength];
        actual.DiscretionaryAcl.GetBinaryForm(currentAcl, 0);
        if (!currentAcl.SequenceEqual(acl))
            throw new InvalidOperationException("acl_readback_changed");
    }

    public static string ReadSmall(SafeFileHandle handle, int length) {
        if (length < 1 || length > 4096) throw new InvalidOperationException("small_read_size");
        byte[] output = new byte[length];
        uint read;
        if (!ReadFile(handle, output, (uint)length, out read, IntPtr.Zero) || read != length)
            throw new InvalidOperationException("small_read_incomplete");
        return new UTF8Encoding(false, true).GetString(output);
    }
}

// Native creation applies the protected descriptor at birth and refuses existing names.
public static class StageOneNative {
    [StructLayout(LayoutKind.Sequential)]
    private struct SecurityAttributes { public int length; public IntPtr descriptor; public int inherit; }
    [StructLayout(LayoutKind.Sequential)]
    private struct IoStatus { public IntPtr status; public UIntPtr information; }
    [DllImport("advapi32.dll", CharSet = CharSet.Unicode, SetLastError = true)]
    private static extern bool ConvertStringSecurityDescriptorToSecurityDescriptorW(
        string text, uint revision, out IntPtr descriptor, out uint length);
    [DllImport("kernel32.dll", CharSet = CharSet.Unicode, SetLastError = true)]
    private static extern bool CreateDirectoryW(string path, ref SecurityAttributes attributes);
    [DllImport("kernel32.dll")]
    private static extern IntPtr LocalFree(IntPtr pointer);
    [DllImport("ntdll.dll")]
    private static extern int NtSetInformationFile(SafeFileHandle file, out IoStatus status, byte[] data, uint size, int kind);
    [DllImport("ntdll.dll")]
    private static extern uint RtlNtStatusToDosError(int status);

    public static void CreateDirectoryExclusive(string path, string sddl) {
        IntPtr descriptor;
        uint length;
        if (!ConvertStringSecurityDescriptorToSecurityDescriptorW(sddl, 1, out descriptor, out length))
            throw new Win32Exception(Marshal.GetLastWin32Error());
        try {
            SecurityAttributes attributes = new SecurityAttributes();
            attributes.length = Marshal.SizeOf(typeof(SecurityAttributes));
            attributes.descriptor = descriptor;
            if (!CreateDirectoryW(path, ref attributes)) throw new Win32Exception(Marshal.GetLastWin32Error());
        } finally { LocalFree(descriptor); }
    }

    public static void RenameNoReplace(SafeFileHandle file, SafeFileHandle directory, string leaf) {
        // Both production and synthetic names are fixed. No path, stream, or arbitrary leaf is accepted.
        if (IntPtr.Size != 8 || (leaf != "isolated.decoy" && leaf != "Ubuntu.original.vhdx"))
            throw new InvalidOperationException("rename_leaf_not_permitted");
        byte[] name = Encoding.Unicode.GetBytes(leaf);
        byte[] data = new byte[22 + name.Length];
        bool held = false;
        try {
            directory.DangerousAddRef(ref held);
            BitConverter.GetBytes(directory.DangerousGetHandle().ToInt64()).CopyTo(data, 8);
            BitConverter.GetBytes(name.Length).CopyTo(data, 16);
            name.CopyTo(data, 20);
            IoStatus io;
            int status = NtSetInformationFile(file, out io, data, (uint)data.Length, 10);
            if (status != 0) throw new Win32Exception((int)RtlNtStatusToDosError(status));
        } finally { if (held) directory.DangerousRelease(); }
    }
}
