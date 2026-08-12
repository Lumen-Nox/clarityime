namespace ClarityIMEHost;

/// <summary>First-run onboarding — UI only, no terminal.</summary>
sealed class OnboardingForm : Form
{
    int _step;
    readonly Panel _content = new() { Dock = DockStyle.Fill, Padding = new Padding(16) };
    readonly Button _next = new() { Text = "下一步", Width = 100, Height = 32 };
    readonly Button _skip = new() { Text = "跳过", Width = 80, Height = 32 };

    public OnboardingForm()
    {
        Text = "欢迎使用 ClarityIME";
        Width = 480;
        Height = 360;
        StartPosition = FormStartPosition.CenterScreen;
        FormBorderStyle = FormBorderStyle.FixedDialog;
        MaximizeBox = false;
        Font = new Font("Microsoft YaHei UI", 10f);

        Controls.Add(_content);

        var bottom = new Panel { Dock = DockStyle.Bottom, Height = 52 };
        _next.Location = new Point(280, 10);
        _skip.Location = new Point(388, 10);
        _next.Click += (_, _) => Advance();
        _skip.Click += (_, _) => { DialogResult = DialogResult.OK; Close(); };
        bottom.Controls.Add(_next);
        bottom.Controls.Add(_skip);
        Controls.Add(bottom);

        ShowStep();
    }

    void ShowStep()
    {
        _content.Controls.Clear();
        if (_step == 0)
        {
            AddTitle("清晰化，不是润色");
            AddBody(
                "ClarityIME 保留你的原意，去掉口语 filler，降低误解。\n\n" +
                "不是帮你装专业、换语气 — 是「意思翻译器」。");
            _next.Text = "下一步";
        }
        else if (_step == 1)
        {
            AddTitle("面向对象 + 一键发送");
            AddBody(
                "三种面向对象：\n" +
                "· 通用 — 日常清晰化\n" +
                "· 联系人 — 按对方理解习惯\n" +
                "· 结构化 — 分段易读，保留全部细节\n\n" +
                "清晰化在本地完成，同一句话结果一致。推荐候选 Enter 一键发送。");
            _next.Text = "下一步";
        }
        else if (_step == 2)
        {
            AddTitle("怎么用");
            AddBody(
                "1. Core 在后台运行 (127.0.0.1:17800)\n" +
                "2. Ctrl+Shift+Space 或托盘图标 → 说话\n" +
                "3. 选候选（或设置里开「一键发送推荐」）→ 文字自动进光标");
            _next.Text = "启动 Core";
        }
        else
        {
            AddTitle("准备就绪");
            AddBody("正在启动 Core…\n\n之后可在托盘 →「设置」里加联系人、改 mode。");
            _next.Text = "完成";
            CoreProcessManager.EnsureRunning();
        }
    }

    void AddTitle(string t)
    {
        _content.Controls.Add(new Label
        {
            Text = t,
            Font = new Font(Font.FontFamily, 14f, FontStyle.Bold),
            AutoSize = true,
            Location = new Point(0, 0),
        });
    }

    void AddBody(string t)
    {
        _content.Controls.Add(new Label
        {
            Text = t,
            AutoSize = true,
            Location = new Point(0, 40),
            MaximumSize = new Size(420, 200),
        });
    }

    void Advance()
    {
        if (_step < 3) { _step++; ShowStep(); return; }
        DialogResult = DialogResult.OK;
        Close();
    }

    public static void RunIfNeeded(IWin32Window? owner)
    {
        Directory.CreateDirectory(AppPaths.InstallDir);
        if (File.Exists(AppPaths.OnboardingFlagPath)) return;
        using var f = new OnboardingForm();
        f.ShowDialog(owner);
        File.WriteAllText(AppPaths.OnboardingFlagPath, DateTime.UtcNow.ToString("o"));
    }
}
