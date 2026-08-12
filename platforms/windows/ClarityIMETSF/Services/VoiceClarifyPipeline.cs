using ClarityIMETSF.Core;
using ClarityIMETSF.Interop;
using ClarityIMETSF.Ui;

namespace ClarityIMETSF.Services;

/// <summary>
/// Runs voice capture → clarify candidates → commit via ITfContext.
/// Called from TSF activation hotkey path (F9) or future dedicated UI button.
/// </summary>
static class VoiceClarifyPipeline
{
    private static readonly CoreApiClient Core = new();
    private static string _mode = "default";

    public static void Run(ITfContext? context)
    {
        if (context == null)
        {
            DebugLog.Write("VoiceClarifyPipeline: no active ITfContext");
            return;
        }

        if (!Core.IsHealthy())
        {
            DebugLog.Write("VoiceClarifyPipeline: core not healthy — start clarityime serve");
            // TODO: spawn clarityime serve or notify tray host
        }

        var captured = VoicePipeline.Capture(AppPaths.RepoRoot, AppPaths.PythonExe);
        if (captured == null || string.IsNullOrWhiteSpace(captured.Raw))
        {
            DebugLog.Write("VoiceClarifyPipeline: capture empty");
            return;
        }

        var raw = captured.Raw;
        var nbest = captured.Nbest.Length > 0 ? captured.Nbest : null;
        var options = Core.GetCandidates(raw, _mode, null, nbest);

        string? picked;
        if (Core.IsAutoApplyTopEnabled() && options.Count > 0)
            picked = options[0].Text;
        else if (options.Count == 1)
            picked = options[0].Text;
        else
            picked = TsfCandidatePicker.Pick(raw, options, nbest, _mode);

        if (string.IsNullOrEmpty(picked))
            return;

        if (TextCommitHelper.TryCommit(context, picked))
        {
            if (picked != raw) Core.Feedback(raw, picked);
            DebugLog.Write($"Committed: {picked}");
        }
    }
}
