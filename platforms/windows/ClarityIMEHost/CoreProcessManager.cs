namespace ClarityIMEHost;

using System.Diagnostics;

static class CoreProcessManager
{
    public static void EnsureRunning()
    {
        if (new CoreClient().IsHealthy()) return;
        try
        {
            Process.Start(new ProcessStartInfo
            {
                FileName = AppPaths.ClarityimeExe,
                Arguments = "serve",
                WorkingDirectory = AppPaths.RepoRoot,
                WindowStyle = ProcessWindowStyle.Hidden,
                CreateNoWindow = true,
                UseShellExecute = false,
            });
            Thread.Sleep(1500);
        }
        catch
        {
            // Settings UI will show error
        }
    }

    public static bool WaitForHealthy(int attempts = 8)
    {
        var client = new CoreClient();
        for (var i = 0; i < attempts; i++)
        {
            if (client.IsHealthy()) return true;
            Thread.Sleep(400);
        }
        return false;
    }
}
