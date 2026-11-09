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

// Additive 2026-11-08 for the window B-3 bounded offline package transfer (restricted stdin
// stream). Same transport discipline as Run: no shell, no retries, bounded raw pipes, deadline;
// plus a bounded stdin pump whose input cap kills the child and whose early child exit is
// reported as a broken stream instead of being mistaken for success.
public sealed class AraNativeStdinResult {
    public int Exit;
    public string[] Lines;
    public long BytesWritten;
    public bool InputComplete;
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

    // Conditional quoting (2026-11-08). MEASURED fact that forced this addition: wsl.exe in this
    // environment FAILS to parse an option that arrives quoted. The same meta command gave a
    // garbled failure with Arguments = "\"--version\"" (exit -1) and a clean 354-byte version
    // table with Arguments = "--version" (exit 0). Because Quote() wrapped EVERY argument, every
    // `-d`/`-u`/`--exec` call had its options quoted, wsl.exe did not recognise them, and it fell
    // back to executing the remainder as a command line -- which is exactly the recorded
    // `/bin/bash: line 1: -d: command not found` of window-02/07/09.
    // So: quote only when the argument actually needs it; otherwise pass it bare.
    public static string QuoteArg(string arg) {
        if (arg == null) return "\"\"";
        if (arg.Length == 0) return "\"\"";
        foreach (char c in arg) {
            if (c == ' ' || c == '\t' || c == '\n' || c == '\r' || c == '"' ||
                c == '&' || c == '|' || c == '<' || c == '>' || c == '^') {
                return Quote(arg);
            }
        }
        return arg;
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

    // Additive 2026-11-08 for the window B-3 bounded offline package transfer (restricted stdin
    // stream). Same transport discipline as Run: no shell, no retries, bounded raw pipes, and a
    // deadline that now covers the WHOLE call including the stdin write phase (the pump runs on
    // a task; a wedged child is killed by the deadline instead of blocking it forever). Input
    // cap kills the child; early child exit is reported as a broken stream, not success.
    public static AraNativeStdinResult RunWithStdin(string file, string[] args, Stream stdinSource,
        long inputCap, int timeoutMs, int cap) {
        var quoted = new string[args.Length];
        for (int i = 0; i < args.Length; i++) quoted[i] = QuoteArg(args[i]);
        using (var process = new Process()) {
            process.StartInfo = new ProcessStartInfo {
                FileName = file, Arguments = String.Join(" ", quoted), UseShellExecute = false,
                CreateNoWindow = true, RedirectStandardInput = true,
                RedirectStandardOutput = true, RedirectStandardError = true
            };
            // Windows PowerShell/.NET Framework can flush a UTF-8 preamble into stdin.
            // Reflection keeps the other PS5 callers compilable; binary transfer requires
            // the explicitly selected modern runtime and never silently falls back.
            var inputEncoding = typeof(ProcessStartInfo).GetProperty("StandardInputEncoding");
            if (inputEncoding == null || !inputEncoding.CanWrite)
                throw new PlatformNotSupportedException("binary_stdin_requires_powershell7");
            inputEncoding.SetValue(process.StartInfo, new UTF8Encoding(false), null);
            if (!process.Start()) throw new InvalidOperationException("native_start_failed");
            var capture = new Capture { Process = process, Cap = cap };
            var stdout = Task.Factory.StartNew(() => capture.Read(process.StandardOutput.BaseStream));
            var stderr = Task.Factory.StartNew(() => capture.Read(process.StandardError.BaseStream));
            long written = 0;
            bool inputComplete = false;
            Exception pumpError = null;
            var pump = Task.Factory.StartNew(() => {
                try {
                    byte[] buffer = new byte[8192];
                    while (true) {
                        int count = stdinSource.Read(buffer, 0, buffer.Length);
                        if (count == 0) { inputComplete = true; break; }
                        written += count;
                        if (written > inputCap) {
                            try { process.Kill(); } catch (InvalidOperationException) { }
                            pumpError = new IOException("native_input_over_cap");
                            return;
                        }
                        try {
                            process.StandardInput.BaseStream.Write(buffer, 0, count);
                            process.StandardInput.BaseStream.Flush();
                        } catch (IOException) {
                            if (process.HasExited)
                                pumpError = new IOException("native_input_broken_stream_child_exited");
                            else
                                pumpError = new IOException("native_input_write_failed");
                            return;
                        }
                    }
                } catch (Exception error) {
                    if (pumpError == null) pumpError = error;
                } finally {
                    try { process.StandardInput.Close(); } catch (InvalidOperationException) { }
                }
            });
            bool exited = process.WaitForExit(timeoutMs);
            if (!exited) {
                try { process.Kill(); } catch (InvalidOperationException) { }
                if (!process.WaitForExit(5000)) throw new TimeoutException("native_kill_unconfirmed");
            }
            // The kill above (deadline or cap) unblocks a wedged pump; wait briefly. Outcome
            // order (review N4): a deadline kill is reported as native_deadline_exceeded even
            // though killing the child also breaks the pump's pending write; the over-cap kill
            // keeps its own error because the child exit makes `exited` true.
            try { pump.Wait(5000); } catch (AggregateException) { }
            if (!exited) {
                throw new TimeoutException(pumpError == null
                    ? "native_deadline_exceeded"
                    : "native_deadline_exceeded:" + pumpError.Message);
            }
            if (pumpError != null) throw pumpError;
            if (!Task.WaitAll(new Task[] { stdout, stderr }, 5000))
                throw new TimeoutException("native_pipe_close_unconfirmed");
            if (capture.Overflow != 0) throw new IOException("native_output_over_cap");
            return new AraNativeStdinResult {
                Exit = process.ExitCode,
                Lines = (Decode(stderr.Result) + "\n" + Decode(stdout.Result)).Split(
                    new string[] { "\r\n", "\n" }, StringSplitOptions.RemoveEmptyEntries),
                BytesWritten = written,
                InputComplete = inputComplete
            };
        }
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
        for (int i = 0; i < args.Length; i++) quoted[i] = QuoteArg(args[i]);
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
