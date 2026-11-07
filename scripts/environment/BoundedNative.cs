// Fixed-window native process transport. No shell, no retries, bounded raw pipes and deadline.
using System;
using System.Diagnostics;
using System.IO;
using System.Text;
using System.Threading;
using System.Threading.Tasks;

public sealed class AraNativeResult {
    public int Exit;
    public string[] Lines;
}

public static class AraBoundedNative {
    private sealed class Capture {
        public int Total;
        public int Overflow;
        public int Cap;
        public Process Process;
        public byte[] Read(Stream input) {
            using (var output = new MemoryStream()) {
                byte[] chunk = new byte[8192];
                int count;
                while ((count = input.Read(chunk, 0, chunk.Length)) != 0) {
                    if (Interlocked.Add(ref Total, count) > Cap) {
                        Interlocked.Exchange(ref Overflow, 1);
                        try { Process.Kill(); } catch (InvalidOperationException) { }
                        break;
                    }
                    output.Write(chunk, 0, count);
                }
                return output.ToArray();
            }
        }
    }

    // CommandLineToArgvW / CRT quoting: backslashes before quotes and the final quote double.
    public static string Quote(string arg) {
        var result = new StringBuilder("\"");
        int slashes = 0;
        foreach (char c in arg) {
            if (c == '\\') { slashes++; continue; }
            if (c == '"') {
                result.Append('\\', slashes * 2 + 1);
                result.Append('"');
            } else {
                result.Append('\\', slashes);
                result.Append(c);
            }
            slashes = 0;
        }
        result.Append('\\', slashes * 2);
        return result.Append('"').ToString();
    }

    private static string Decode(byte[] bytes) {
        bool utf16 = bytes.Length >= 2 && bytes[0] == 0xff && bytes[1] == 0xfe;
        if (!utf16 && bytes.Length >= 4 && bytes.Length % 2 == 0) {
            int oddZeros = 0, evenZeros = 0;
            for (int i = 0; i < bytes.Length; i += 2) {
                if (bytes[i] == 0) evenZeros++;
                if (bytes[i + 1] == 0) oddZeros++;
            }
            utf16 = oddZeros >= 2 && oddZeros > evenZeros * 3;
        }
        if (utf16) return Encoding.Unicode.GetString(bytes).TrimStart('\ufeff');
        try { return new UTF8Encoding(false, true).GetString(bytes).TrimStart('\ufeff'); }
        catch (DecoderFallbackException) {
            // WSL host diagnostics can use the actual Windows ANSI code page (936 here).
            // Guest content uses ASCII base64 and is never decoded through this fallback.
            return Encoding.GetEncoding(System.Globalization.CultureInfo.CurrentCulture.TextInfo.ANSICodePage).GetString(bytes);
        }
    }

    public static AraNativeResult Run(string file, string[] args, int timeoutMs, int cap) {
        var quoted = new string[args.Length];
        for (int i = 0; i < args.Length; i++) quoted[i] = Quote(args[i]);
        using (var process = new Process()) {
            process.StartInfo = new ProcessStartInfo {
                FileName = file, Arguments = String.Join(" ", quoted), UseShellExecute = false,
                CreateNoWindow = true, RedirectStandardInput = true,
                RedirectStandardOutput = true, RedirectStandardError = true
            };
            if (!process.Start()) throw new InvalidOperationException("native_start_failed");
            process.StandardInput.Close();
            var capture = new Capture { Process = process, Cap = cap };
            var stdout = Task.Factory.StartNew(() => capture.Read(process.StandardOutput.BaseStream));
            var stderr = Task.Factory.StartNew(() => capture.Read(process.StandardError.BaseStream));
            bool exited = process.WaitForExit(timeoutMs);
            if (!exited) {
                try { process.Kill(); } catch (InvalidOperationException) { }
                if (!process.WaitForExit(5000)) throw new TimeoutException("native_kill_unconfirmed");
            }
            if (!Task.WaitAll(new Task[] { stdout, stderr }, 5000))
                throw new TimeoutException("native_pipe_close_unconfirmed");
            if (!exited) throw new TimeoutException("native_deadline_exceeded");
            if (capture.Overflow != 0) throw new IOException("native_output_over_cap");
            return new AraNativeResult {
                Exit = process.ExitCode,
                Lines = (Decode(stderr.Result) + "\n" + Decode(stdout.Result)).Split(
                    new string[] { "\r\n", "\n" }, StringSplitOptions.RemoveEmptyEntries)
            };
        }
    }
}
