namespace ClarityIMETSF.Services;

/// <summary>Append-only debug log for TSF IME (loaded inside ctfmon).</summary>
static class DebugLog
{
    static readonly string LogPath = Path.Combine(
        Environment.GetFolderPath(Environment.SpecialFolder.LocalApplicationData),
        "ClarityIME", "tsf-debug.log");

    public static void Write(string message)
    {
        try
        {
            Directory.CreateDirectory(Path.GetDirectoryName(LogPath)!);
            File.AppendAllText(LogPath, $"{DateTime.Now:yyyy-MM-dd HH:mm:ss} {message}{Environment.NewLine}");
        }
        catch
        {
            // ignore logging failures
        }
    }
}
