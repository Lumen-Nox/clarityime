using System.Text.Json;

namespace ClarityIMEHost;

sealed class TrayApplicationContext : ApplicationContext
{
    private readonly NotifyIcon _tray;
    private readonly CoreClient _core = new();
    private readonly HotkeyWindow _hotkey;
    private string _mode = "default";
    private string? _contact;

    public TrayApplicationContext()
    {
        CoreProcessManager.EnsureRunning();

        _hotkey = new HotkeyWindow(RunVoicePipeline);
        var menu = new ContextMenuStrip();
        menu.Items.Add("🎤 语音清晰化 (Ctrl+Shift+Space)", null, (_, _) => RunVoicePipeline());
        menu.Items.Add("⚙ 设置…", null, (_, _) => OpenSettings());
        menu.Items.Add("切换 mode (default/ai/contact)", null, (_, _) => CycleMode());
        menu.Items.Add("-");
        menu.Items.Add("退出", null, (_, _) => ExitThread());

        _tray = new NotifyIcon
        {
            Icon = SystemIcons.Application,
            Text = "ClarityIME",
            Visible = true,
            ContextMenuStrip = menu,
        };
        _tray.DoubleClick += (_, _) => RunVoicePipeline();

        UpdateTrayText();
        var coreOk = _core.IsHealthy();
        _tray.ShowBalloonTip(
            3000,
            "ClarityIME",
            coreOk
                ? "Core 已连接。双击托盘或 Ctrl+Shift+Space 说话。"
                : "Core 未连接 — 右键「设置」启动 Core",
            ToolTipIcon.Info);

        OnboardingForm.RunIfNeeded(null);
    }

    void OpenSettings()
    {
        var result = SettingsForm.ShowDialog(null, _mode, _contact);
        if (result == null) return;
        _mode = result.Value.Mode;
        _contact = result.Value.Contact;
        UpdateTrayText();
    }

    void CycleMode()
    {
        _mode = _mode switch
        {
            "default" => "ai",
            "ai" => "contact",
            _ => "default",
        };
        UpdateTrayText();
    }

    void UpdateTrayText()
    {
        var extra = _mode == "contact" && !string.IsNullOrEmpty(_contact) ? $" · {_contact}" : "";
        _tray.Text = $"ClarityIME [{_mode}{extra}]";
    }

    void RunVoicePipeline()
    {
        if (!_core.IsHealthy())
        {
            CoreProcessManager.EnsureRunning();
            if (!CoreProcessManager.WaitForHealthy())
            {
                _tray.ShowBalloonTip(3000, "ClarityIME", "Core 未运行 — 打开「设置」启动。", ToolTipIcon.Warning);
                OpenSettings();
                return;
            }
        }

        if (_mode == "contact" && string.IsNullOrEmpty(_contact))
        {
            _tray.ShowBalloonTip(2500, "ClarityIME", "contact 模式：请先在「设置」里选联系人。", ToolTipIcon.Warning);
            OpenSettings();
            return;
        }

        _tray.Text = "ClarityIME [listening…]";
        Application.DoEvents();

        var captured = VoiceCapture.Capture(AppPaths.RepoRoot, AppPaths.PythonExe);
        UpdateTrayText();

        if (captured == null || string.IsNullOrWhiteSpace(captured.Raw))
        {
            _tray.ShowBalloonTip(2000, "ClarityIME", "没听到声音（麦克风权限？）", ToolTipIcon.Warning);
            return;
        }

        var raw = captured.Raw;
        var nbest = captured.Nbest.Length > 0 ? captured.Nbest : null;
        var options = _core.GetCandidates(raw, _mode, _contact, nbest);

        var autoTop = IsAutoApplyTopEnabled();
        string? picked;
        if (autoTop && options.Count > 0)
            picked = options[0].Text;
        else if (options.Count == 1)
            picked = options[0].Text;
        else
            picked = CandidatePickerForm.Pick(raw, options, nbest, _mode);

        if (string.IsNullOrEmpty(picked)) return;

        TextInjector.Apply(picked);
        if (picked != raw) _core.Feedback(raw, picked);
        _tray.ShowBalloonTip(2000, "ClarityIME", "已应用到光标。", ToolTipIcon.Info);
    }

    bool IsAutoApplyTopEnabled()
    {
        using var doc = _core.GetSettings();
        if (doc == null) return false;
        return doc.RootElement.TryGetProperty("auto_apply_top", out var v)
            && v.ValueKind == JsonValueKind.True;
    }

    protected override void Dispose(bool disposing)
    {
        if (disposing)
        {
            _hotkey.Dispose();
            _tray.Visible = false;
            _tray.Dispose();
        }
        base.Dispose(disposing);
    }
}
