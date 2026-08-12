namespace ClarityIMEHost;

static class AppPaths
{
    public static string RepoRoot
    {
        get
        {
            var dir = AppContext.BaseDirectory.TrimEnd('\\', '/');
            // dist/ or ClarityIMEHost/bin/ → climb to repo root (contains clarityime/main.py)
            for (var i = 0; i < 6; i++)
            {
                var candidate = Path.Combine(dir, "clarityime", "main.py");
                if (File.Exists(Path.Combine(dir, "clarityime", "main.py")))
                    return dir;
                dir = Path.GetDirectoryName(dir) ?? dir;
            }
            // installed: use env or walk up from install dir
            var env = Environment.GetEnvironmentVariable("CLARITYIME_ROOT");
            if (!string.IsNullOrEmpty(env) && Directory.Exists(env)) return env;
            return Path.Combine(
                Environment.GetFolderPath(Environment.SpecialFolder.LocalApplicationData),
                "Programs", "ClarityIME");
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

    /// <summary>clarityime CLI on PATH, bundled core, or venv Scripts.</summary>
    public static string ClarityimeExe
    {
        get
        {
            var envCoreExe = Environment.GetEnvironmentVariable("CLARITYIME_CORE_EXE");
            if (!string.IsNullOrEmpty(envCoreExe) && File.Exists(envCoreExe)) return envCoreExe;
            var envCore = Environment.GetEnvironmentVariable("CLARITYIME_CORE");
            if (!string.IsNullOrEmpty(envCore) && File.Exists(envCore)) return envCore;
            var installCore = Path.Combine(InstallDir, "clarityime-core.exe");
            if (File.Exists(installCore)) return installCore;
            var bundledDev = Path.Combine(RepoRoot, "platforms", "windows", "dist", "clarityime-core.exe");
            if (File.Exists(bundledDev)) return bundledDev;
            var venvCli = Path.Combine(RepoRoot, ".venv", "Scripts", "clarityime.exe");
            if (File.Exists(venvCli)) return venvCli;
            var installCli = Path.Combine(InstallDir, "clarityime.cmd");
            if (File.Exists(installCli)) return installCli;
            return "clarityime";
        }
    }

    /// <summary>Executable used for ``capture`` (bundled core or Python).</summary>
    public static string CaptureExe => ClarityimeExe;

    public static string CaptureArguments(int seconds = 10)
    {
        var exe = CaptureExe;
        if (exe.EndsWith("clarityime-core.exe", StringComparison.OrdinalIgnoreCase)
            || exe.EndsWith("clarityime.exe", StringComparison.OrdinalIgnoreCase))
            return "capture --seconds " + seconds;
        return "-m clarityime.main capture --seconds " + seconds;
    }

    public static string InstallDir => Path.Combine(
        Environment.GetFolderPath(Environment.SpecialFolder.LocalApplicationData),
        "Programs", "ClarityIME");

    public static string OnboardingFlagPath => Path.Combine(InstallDir, ".onboarded");
}
