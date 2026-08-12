using System.Diagnostics;
using System.Net.Http.Json;
using System.Text.Json;

namespace ClarityIMETSF.Core;

/// <summary>HTTP client for clarityime serve at 127.0.0.1:17800 (shared logic with tray host).</summary>
sealed class CoreApiClient
{
    private const string Base = "http://127.0.0.1:17800";
    private readonly HttpClient _http = new() { Timeout = TimeSpan.FromSeconds(30) };

    public CoreApiClient()
    {
        var token = ReadLocalApiToken();
        if (!string.IsNullOrEmpty(token))
            _http.DefaultRequestHeaders.Add("X-ClarityIME-Token", token);
    }

    static string? ReadLocalApiToken()
    {
        try
        {
            var root = Environment.GetEnvironmentVariable("CLARITYIME_ROOT");
            if (string.IsNullOrWhiteSpace(root)) return null;
            var path = Path.Combine(root, "data", ".local_api_token");
            if (!File.Exists(path)) return null;
            return File.ReadAllText(path).Trim();
        }
        catch { return null; }
    }

    public bool IsHealthy()
    {
        try
        {
            var s = _http.GetStringAsync($"{Base}/v1/health").GetAwaiter().GetResult();
            return s.Contains("\"ok\": true") || s.Contains("\"ok\":true");
        }
        catch
        {
            return false;
        }
    }

    public List<CandidateOption> GetCandidates(string text, string mode = "default", string? contact = null, string[]? nbest = null)
    {
        var payload = new Dictionary<string, object>
        {
            ["text"] = text,
            ["mode"] = mode,
        };
        if (!string.IsNullOrEmpty(contact)) payload["contact"] = contact!;
        if (nbest is { Length: > 0 }) payload["nbest"] = nbest;
        try
        {
            var resp = _http.PostAsJsonAsync($"{Base}/v1/candidates", payload).GetAwaiter().GetResult();
            resp.EnsureSuccessStatusCode();
            using var doc = JsonDocument.Parse(resp.Content.ReadAsStringAsync().GetAwaiter().GetResult());
            var list = new List<CandidateOption>();
            foreach (var item in doc.RootElement.GetProperty("candidates").EnumerateArray())
            {
                list.Add(new CandidateOption(
                    item.GetProperty("text").GetString() ?? text,
                    item.GetProperty("label").GetString() ?? "option"));
            }
            return list.Count > 0 ? list : new List<CandidateOption> { new(text, "raw") };
        }
        catch
        {
            return new List<CandidateOption> { new(text, "offline") };
        }
    }

    public string? Feedback(
        string raw,
        string preferred,
        string[]? nbest = null,
        IReadOnlyList<CandidateOption>? candidates = null,
        string? mode = null)
    {
        try
        {
            var payload = new Dictionary<string, object>
            {
                ["raw"] = raw,
                ["preferred"] = preferred,
            };
            if (nbest is { Length: > 0 }) payload["nbest"] = nbest;
            if (candidates is { Count: > 0 })
            {
                payload["candidates"] = candidates.Select(c => new { text = c.Text, label = c.Label }).ToArray();
            }
            if (!string.IsNullOrEmpty(mode)) payload["mode"] = mode!;
            var resp = _http.PostAsJsonAsync($"{Base}/v1/feedback", payload).GetAwaiter().GetResult();
            if (!resp.IsSuccessStatusCode) return null;
            using var doc = JsonDocument.Parse(resp.Content.ReadAsStringAsync().GetAwaiter().GetResult());
            if (doc.RootElement.TryGetProperty("bundle_url", out var url))
                return url.GetString();
            return null;
        }
        catch
        {
            return null;
        }
    }

    public void Feedback(string raw, string preferred) => Feedback(raw, preferred, null, null, null);

    public bool IsAutoApplyTopEnabled()
    {
        try
        {
            using var doc = JsonDocument.Parse(_http.GetStringAsync($"{Base}/v1/settings").GetAwaiter().GetResult());
            return doc.RootElement.TryGetProperty("auto_apply_top", out var v)
                && v.ValueKind == JsonValueKind.True;
        }
        catch
        {
            return false;
        }
    }
}

/// <summary>Voice capture via Python subprocess (same as ClarityIMEHost).</summary>
static class VoicePipeline
{
    public static VoiceResult? Capture(string repoRoot, string pythonExe, int seconds = 10)
    {
        var psi = new ProcessStartInfo
        {
            FileName = pythonExe,
            Arguments = "-m clarityime.main capture --seconds " + seconds,
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
        p.WaitForExit(120_000);
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

static class AppPaths
{
    public static string RepoRoot
    {
        get
        {
            var dir = AppContext.BaseDirectory.TrimEnd('\\', '/');
            for (var i = 0; i < 8; i++)
            {
                if (File.Exists(Path.Combine(dir, "clarityime", "main.py")))
                    return dir;
                dir = Path.GetDirectoryName(dir) ?? dir;
            }
            var env = Environment.GetEnvironmentVariable("CLARITYIME_ROOT");
            if (!string.IsNullOrEmpty(env) && Directory.Exists(env)) return env;
            return Path.GetFullPath(Path.Combine(
                Environment.GetFolderPath(Environment.SpecialFolder.LocalApplicationData),
                "ClarityIME", "core"));
        }
    }

    public static string PythonExe
    {
        get
        {
            var envPy = Environment.GetEnvironmentVariable("CLARITYIME_PYTHON");
            if (!string.IsNullOrEmpty(envPy) && File.Exists(envPy)) return envPy;
            var venv = Path.Combine(RepoRoot, ".venv", "Scripts", "python.exe");
            if (File.Exists(venv)) return venv;
            return "python";
        }
    }
}

record CandidateOption(string Text, string Label);
record VoiceResult(string Raw, string Language, string[] Nbest)
{
    public VoiceResult(string raw, string language) : this(raw, language, Array.Empty<string>()) { }
}
