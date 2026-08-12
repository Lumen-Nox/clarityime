using System.Diagnostics;
using System.Text.Json;

namespace ClarityIMEHost;

/// <summary>
/// Delegates voice capture + ASR to Python core (works without System.Speech / NuGet).
/// </summary>
static class VoiceCapture
{
    public static VoiceResult? Capture(string repoRoot, string pythonExe, int seconds = 10)
    {
        var captureExe = AppPaths.CaptureExe;
        var useBundled = captureExe.EndsWith("clarityime-core.exe", StringComparison.OrdinalIgnoreCase)
            || captureExe.EndsWith("clarityime.exe", StringComparison.OrdinalIgnoreCase);
        var psi = new ProcessStartInfo
        {
            FileName = useBundled ? captureExe : pythonExe,
            Arguments = AppPaths.CaptureArguments(seconds),
            WorkingDirectory = repoRoot,
            RedirectStandardOutput = true,
            RedirectStandardError = true,
            UseShellExecute = false,
            CreateNoWindow = true,
            StandardOutputEncoding = System.Text.Encoding.UTF8,
        };
        using var p = Process.Start(psi);
        if (p == null) return null;
        var stdout = p.StandardOutput.ReadToEnd();
        p.WaitForExit(120000);
        if (p.ExitCode != 0) return null;
        try
        {
            using var doc = JsonDocument.Parse(stdout.Trim());
            var root = doc.RootElement;
            var nbest = new List<string>();
            if (root.TryGetProperty("nbest", out var arr) && arr.ValueKind == JsonValueKind.Array)
            {
                foreach (var item in arr.EnumerateArray())
                {
                    var s = item.GetString();
                    if (!string.IsNullOrWhiteSpace(s)) nbest.Add(s);
                }
            }
            return new VoiceResult(
                root.GetProperty("raw").GetString() ?? "",
                root.TryGetProperty("language", out var lang) ? lang.GetString() ?? "auto" : "auto",
                nbest.ToArray());
        }
        catch
        {
            return null;
        }
    }
}

record VoiceResult(string Raw, string Language, string[] Nbest)
{
    public VoiceResult(string raw, string language) : this(raw, language, Array.Empty<string>()) { }
}
