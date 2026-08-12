using System.Net.Http.Json;
using System.Text.Json;

namespace ClarityIMEHost;

sealed class CoreClient
{
    private const string Base = "http://127.0.0.1:17800";
    private readonly HttpClient _http = new() { Timeout = TimeSpan.FromSeconds(8) };

    public CoreClient()
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
        catch { return false; }
    }

    public string Clarify(string text, string mode, string? contact = null)
    {
        var payload = new Dictionary<string, object>
        {
            ["text"] = text,
            ["mode"] = mode,
            ["nbest"] = new[] { text },
        };
        if (!string.IsNullOrEmpty(contact)) payload["contact"] = contact!;
        return PostClarified("/v1/clarify", payload, text);
    }

    public List<CandidateOption> GetCandidates(string text, string mode, string? contact = null, string[]? nbest = null)
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
            return list.Count > 0 ? list : Fallback(text, mode);
        }
        catch
        {
            return Fallback(text, mode);
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
        catch { return null; }
    }

    public void Feedback(string raw, string preferred) => Feedback(raw, preferred, null, null, null);

    public List<ContactRow> ListContacts()
    {
        try
        {
            var resp = _http.GetStringAsync($"{Base}/v1/contacts").GetAwaiter().GetResult();
            using var doc = JsonDocument.Parse(resp);
            var list = new List<ContactRow>();
            foreach (var item in doc.RootElement.GetProperty("contacts").EnumerateArray())
            {
                var id = item.GetProperty("id").ValueKind == JsonValueKind.Number
                    ? item.GetProperty("id").GetInt32().ToString()
                    : item.GetProperty("id").GetString() ?? "";
                CeromeL2Values? cerome = null;
                var mood = "steady";
                if (item.TryGetProperty("cerome", out var ceromeEl) && ceromeEl.ValueKind == JsonValueKind.Object)
                {
                    if (ceromeEl.TryGetProperty("L2", out var l2) && l2.ValueKind == JsonValueKind.Object)
                    {
                        cerome = new CeromeL2Values(
                            l2.TryGetProperty("clarity", out var cl) ? cl.GetDouble() : 0.7,
                            l2.TryGetProperty("warmth", out var w) ? w.GetDouble() : 0.5,
                            l2.TryGetProperty("efficiency", out var ef) ? ef.GetDouble() : 0.5,
                            l2.TryGetProperty("precision", out var pr) ? pr.GetDouble() : 0.5,
                            l2.TryGetProperty("humor", out var hu) ? hu.GetDouble() : 0.3);
                    }
                    if (ceromeEl.TryGetProperty("L5", out var l5) && l5.TryGetProperty("label", out var lbl))
                        mood = lbl.GetString() ?? "steady";
                }
                list.Add(new ContactRow(
                    id,
                    item.GetProperty("name").GetString() ?? "",
                    item.TryGetProperty("relationship", out var r) ? r.GetString() ?? "" : "",
                    item.TryGetProperty("style_notes", out var s) ? s.GetString() ?? "" : "",
                    item.TryGetProperty("comprehension_notes", out var c) ? c.GetString() ?? "" : "",
                    cerome,
                    mood));
            }
            return list;
        }
        catch
        {
            return new List<ContactRow>();
        }
    }

    public bool SaveContact(
        string name,
        string relationship,
        string styleNotes,
        string comprehension,
        CeromeL2Values? cerome = null,
        string moodLabel = "steady")
    {
        try
        {
            var payload = new Dictionary<string, object>
            {
                ["name"] = name,
                ["relationship"] = relationship,
                ["style_notes"] = styleNotes,
                ["comprehension_notes"] = comprehension,
            };
            if (cerome != null)
            {
                payload["cerome"] = new Dictionary<string, object>
                {
                    ["L2"] = new
                    {
                        clarity = cerome.Clarity,
                        warmth = cerome.Warmth,
                        efficiency = cerome.Efficiency,
                        precision = cerome.Precision,
                        humor = cerome.Humor,
                    },
                    ["L5"] = new { label = moodLabel },
                };
            }
            var resp = _http.PostAsJsonAsync($"{Base}/v1/contacts", payload).GetAwaiter().GetResult();
            return resp.IsSuccessStatusCode;
        }
        catch { return false; }
    }

    public (bool Loopback, string KeyBackend, bool CeromeTags)? GetSecurityStatus()
    {
        try
        {
            using var doc = JsonDocument.Parse(_http.GetStringAsync($"{Base}/v1/security/status").GetAwaiter().GetResult());
            var root = doc.RootElement;
            return (
                root.TryGetProperty("loopback_only", out var lb) && lb.GetBoolean(),
                root.TryGetProperty("key_backend", out var kb) ? kb.GetString() ?? "" : "",
                root.TryGetProperty("cerome_tags", out var ct) && ct.GetBoolean());
        }
        catch { return null; }
    }

    public bool DeleteContact(string name)
    {
        try
        {
            var resp = _http.DeleteAsync($"{Base}/v1/contacts?name={Uri.EscapeDataString(name)}")
                .GetAwaiter().GetResult();
            return resp.IsSuccessStatusCode;
        }
        catch { return false; }
    }

    public string? ExportContactBundle(string name)
    {
        try
        {
            return _http.GetStringAsync(
                    $"{Base}/v1/contacts/export?name={Uri.EscapeDataString(name)}")
                .GetAwaiter().GetResult();
        }
        catch { return null; }
    }

    public bool ImportContactBundle(string json)
    {
        try
        {
            using var content = new StringContent(json, System.Text.Encoding.UTF8, "application/json");
            var resp = _http.PostAsync($"{Base}/v1/contacts/import", content).GetAwaiter().GetResult();
            return resp.IsSuccessStatusCode;
        }
        catch { return false; }
    }

    public JsonDocument? GetSettings()
    {
        try
        {
            var json = _http.GetStringAsync($"{Base}/v1/settings").GetAwaiter().GetResult();
            return JsonDocument.Parse(json);
        }
        catch { return null; }
    }

    public bool SaveSettings(string? language, string? model, string? audience, string? applyMode, bool? autoApplyTop = null)
    {
        var payload = new Dictionary<string, object>();
        if (language != null) payload["asr_language"] = language;
        if (model != null) payload["whisper_model"] = model;
        if (audience != null) payload["default_audience"] = audience;
        if (applyMode != null) payload["apply_mode"] = applyMode;
        if (autoApplyTop.HasValue) payload["auto_apply_top"] = autoApplyTop.Value;
        try
        {
            var resp = _http.PostAsJsonAsync($"{Base}/v1/settings", payload).GetAwaiter().GetResult();
            return resp.IsSuccessStatusCode;
        }
        catch { return false; }
    }

    public (bool CloudSync, bool AggregateResearch)? GetConsent()
    {
        try
        {
            using var doc = JsonDocument.Parse(_http.GetStringAsync($"{Base}/v1/consent").GetAwaiter().GetResult());
            return (
                doc.RootElement.GetProperty("cloud_sync").GetBoolean(),
                doc.RootElement.GetProperty("aggregate_research").GetBoolean());
        }
        catch { return null; }
    }

    public bool SaveConsent(bool cloudSync, bool aggregateResearch)
    {
        try
        {
            var resp = _http.PostAsJsonAsync($"{Base}/v1/consent", new
            {
                cloud_sync = cloudSync,
                aggregate_research = aggregateResearch,
            }).GetAwaiter().GetResult();
            return resp.IsSuccessStatusCode;
        }
        catch { return false; }
    }

    static List<CandidateOption> Fallback(string text, string mode) =>
        new() { new CandidateOption(OfflineRules.Clarify(text, mode), "offline") };

    string PostClarified(string path, object payload, string fallback)
    {
        try
        {
            var resp = _http.PostAsJsonAsync($"{Base}{path}", payload).GetAwaiter().GetResult();
            resp.EnsureSuccessStatusCode();
            using var doc = JsonDocument.Parse(resp.Content.ReadAsStringAsync().GetAwaiter().GetResult());
            return doc.RootElement.GetProperty("clarified").GetString() ?? fallback;
        }
        catch
        {
            var mode = payload is Dictionary<string, object> d && d.TryGetValue("mode", out var m)
                ? m?.ToString() ?? "default"
                : "default";
            return OfflineRules.Clarify(fallback, mode);
        }
    }
}

record CandidateOption(string Text, string Label);

record CeromeL2Values(double Clarity, double Warmth, double Efficiency, double Precision, double Humor);

record ContactRow(
    string Id,
    string Name,
    string Relationship,
    string StyleNotes = "",
    string ComprehensionNotes = "",
    CeromeL2Values? Cerome = null,
    string MoodLabel = "steady");

static class OfflineRules
{
    static readonly string[] Fillers = ["嗯", "啊", "呃", "那个", "就是", "然后"];

    public static string Clarify(string text, string mode)
    {
        var outText = text.Trim();
        foreach (var f in Fillers)
            if (outText.StartsWith(f)) outText = outText[f.Length..];
        outText = outText.TrimStart('你', '好', '，', ' ');
        foreach (var w in new[] { "因为", "但是", "所以", "而且" })
        {
            var idx = outText.IndexOf(w, StringComparison.Ordinal);
            if (idx > 0 && idx < outText.Length && outText[idx - 1] is not '，' and not ',')
                outText = outText.Insert(idx, "，");
        }
        if (mode is "structured" or "ai")
        {
            var parts = outText.Split('。', StringSplitOptions.RemoveEmptyEntries | StringSplitOptions.TrimEntries);
            if (parts.Length >= 2)
                return string.Join("\n\n", parts.Select(p => p.TrimEnd('。', '！', '？') + "。"));
        }
        if (outText.Length > 0 && !"。！？".Contains(outText[^1]))
            outText += outText.Contains('吗') ? "？" : "。";
        return outText;
    }
}
