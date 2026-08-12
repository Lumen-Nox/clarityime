namespace ClarityIMEHost;

/// <summary>Shared visual tokens — professional, minimal, not "AI product" chrome.</summary>
static class UiTheme
{
    public static readonly Color Accent = Color.FromArgb(45, 106, 158);
    public static readonly Color AccentMuted = Color.FromArgb(232, 240, 248);
    public static readonly Color SuccessBg = Color.FromArgb(237, 246, 239);
    public static readonly Color SuccessBorder = Color.FromArgb(129, 178, 154);
    public static readonly Color TextMuted = Color.FromArgb(102, 102, 102);
    public static readonly Color TextSecondary = Color.FromArgb(68, 68, 68);
    public static readonly Color Surface = Color.FromArgb(250, 250, 252);
    public static readonly Font TitleFont = new("Microsoft YaHei UI", 10f, FontStyle.Bold);
    public static readonly Font BodyFont = new("Microsoft YaHei UI", 9f);
}

/// <summary>Audience mode with user-facing label.</summary>
sealed record ModeOption(string Value, string Label)
{
    public override string ToString() => Label;
}

static class AudienceModes
{
    public static readonly ModeOption[] All =
    [
        new("default", "通用清晰化"),
        new("structured", "结构化"),
        new("contact", "联系人"),
    ];

    public static string Normalize(string? raw)
    {
        if (string.IsNullOrWhiteSpace(raw)) return "default";
        return raw.Trim().ToLowerInvariant() switch
        {
            "ai" => "structured",
            _ => raw.Trim().ToLowerInvariant(),
        };
    }

    public static string LabelFor(string value) =>
        All.FirstOrDefault(m => m.Value == Normalize(value))?.Label ?? value;
}
