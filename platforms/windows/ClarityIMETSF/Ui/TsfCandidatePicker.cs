using ClarityIMETSF.Core;

namespace ClarityIMETSF.Ui;

/// <summary>IME candidate picker: top recommendation = one-click send; alts below (matches Host UX).</summary>
sealed class TsfCandidatePickerForm : Form
{
    public string? SelectedText { get; private set; }
    readonly IReadOnlyList<CandidateOption> _options;
    readonly string[]? _nbest;
    readonly string _mode;

    public TsfCandidatePickerForm(
        string raw,
        IReadOnlyList<CandidateOption> options,
        string[]? nbest = null,
        string mode = "default")
    {
        _options = options;
        _nbest = nbest;
        _mode = mode;
        Text = "ClarityIME — 选清晰化结果";
        Width = 560;
        Height = 380;
        StartPosition = FormStartPosition.CenterScreen;
        FormBorderStyle = FormBorderStyle.FixedDialog;
        MaximizeBox = false;
        TopMost = true;
        KeyPreview = true;
        Font = new Font("Microsoft YaHei UI", 9.5f);

        var root = new TableLayoutPanel
        {
            Dock = DockStyle.Fill,
            ColumnCount = 1,
            RowCount = 3,
            Padding = new Padding(12),
        };
        root.RowStyles.Add(new RowStyle(SizeType.AutoSize));
        root.RowStyles.Add(new RowStyle(SizeType.Percent, 100));
        root.RowStyles.Add(new RowStyle(SizeType.AutoSize));
        Controls.Add(root);

        root.Controls.Add(new Label
        {
            Text = $"原文 · {raw}",
            AutoSize = true,
            MaximumSize = new Size(520, 56),
            Padding = new Padding(0, 0, 0, 8),
        }, 0, 0);

        var body = new Panel { Dock = DockStyle.Fill, AutoScroll = true };
        root.Controls.Add(body, 0, 1);

        if (_options.Count > 0)
        {
            var top = _options[0];
            var sendTop = new Button
            {
                Text = $"⏎ 发送推荐 · [{top.Label}]\r\n{top.Text}",
                Height = 76,
                Dock = DockStyle.Top,
                TextAlign = ContentAlignment.MiddleLeft,
                Padding = new Padding(12, 8, 12, 8),
                BackColor = Color.FromArgb(232, 245, 233),
                FlatStyle = FlatStyle.Flat,
            };
            sendTop.FlatAppearance.BorderColor = Color.FromArgb(129, 199, 132);
            sendTop.Click += (_, _) => AcceptOption(0);
            body.Controls.Add(sendTop);

            if (_options.Count > 1)
            {
                body.Controls.Add(new Label
                {
                    Text = "其他选项（点选 · 或按 2/3）",
                    Dock = DockStyle.Top,
                    AutoSize = true,
                    Padding = new Padding(0, 10, 0, 6),
                    ForeColor = Color.Gray,
                });

                for (var i = 1; i < _options.Count; i++)
                {
                    var idx = i;
                    var o = _options[i];
                    var btn = new Button
                    {
                        Text = $"{i + 1}. [{o.Label}] {o.Text}",
                        Dock = DockStyle.Top,
                        Height = 48,
                        TextAlign = ContentAlignment.MiddleLeft,
                        Padding = new Padding(8, 4, 8, 4),
                    };
                    btn.Click += (_, _) => AcceptOption(idx);
                    body.Controls.Add(btn);
                }
            }
        }

        var bottom = new FlowLayoutPanel
        {
            FlowDirection = FlowDirection.RightToLeft,
            Dock = DockStyle.Fill,
            Height = 40,
            Padding = new Padding(0, 8, 0, 0),
        };
        var cancel = new Button { Text = "取消 (Esc)", DialogResult = DialogResult.Cancel, Width = 100 };
        var bad = new Button { Text = "都不对…", Width = 90 };
        bad.Click += (_, _) =>
        {
            using var fb = new TsfFeedbackForm(raw, _nbest, _options, _mode);
            fb.ShowDialog(this);
        };
        bottom.Controls.Add(cancel);
        bottom.Controls.Add(bad);
        root.Controls.Add(bottom, 0, 2);

        CancelButton = cancel;
        KeyDown += OnKeyDown;
    }

    void OnKeyDown(object? sender, KeyEventArgs e)
    {
        if (e.KeyCode == Keys.Enter && _options.Count > 0)
        {
            AcceptOption(0);
            e.Handled = true;
            return;
        }
        if (e.KeyCode >= Keys.D1 && e.KeyCode <= Keys.D3)
        {
            var idx = e.KeyCode - Keys.D1;
            if (idx < _options.Count)
            {
                AcceptOption(idx);
                e.Handled = true;
            }
        }
    }

    void AcceptOption(int index)
    {
        if (index < 0 || index >= _options.Count) return;
        SelectedText = _options[index].Text;
        DialogResult = DialogResult.OK;
        Close();
    }
}

/// <summary>Quick feedback when no candidate fits.</summary>
sealed class TsfFeedbackForm : Form
{
    public TsfFeedbackForm(
        string raw,
        string[]? nbest = null,
        IReadOnlyList<CandidateOption>? candidates = null,
        string mode = "default")
    {
        Text = "反馈 — 为什么不对？";
        Width = 440;
        Height = 260;
        StartPosition = FormStartPosition.CenterParent;
        FormBorderStyle = FormBorderStyle.FixedDialog;
        Font = new Font("Microsoft YaHei UI", 9.5f);

        Controls.Add(new Label
        {
            Text = $"原文: {raw}",
            Location = new Point(12, 12),
            Size = new Size(400, 36),
        });
        var box = new TextBox
        {
            Location = new Point(12, 52),
            Size = new Size(400, 80),
            Multiline = true,
        };
        Controls.Add(box);
        Controls.Add(new Label
        {
            Text = "例如：太正式 / 丢了我原来的语气 / 对象搞错了…",
            Location = new Point(12, 136),
            AutoSize = true,
            ForeColor = Color.Gray,
        });
        var ok = new Button { Text = "记录反馈", Location = new Point(12, 188), Width = 100 };
        ok.Click += (_, _) =>
        {
            var note = box.Text.Trim();
            if (!string.IsNullOrWhiteSpace(note))
            {
                try
                {
                    var url = new CoreApiClient().Feedback(
                        raw,
                        $"[user_feedback] {note}",
                        nbest,
                        candidates,
                        mode);
                    if (!string.IsNullOrEmpty(url))
                    {
                        try { Clipboard.SetText(url); } catch { /* ignore */ }
                        MessageBox.Show(
                            $"反馈已记录。\n\nN-best bundle（已复制）:\n{url}",
                            "ClarityIME",
                            MessageBoxButtons.OK,
                            MessageBoxIcon.Information);
                    }
                }
                catch { /* ignore */ }
            }
            Close();
        };
        Controls.Add(ok);
    }
}

static class TsfCandidatePicker
{
    public static string? Pick(
        string raw,
        IReadOnlyList<CandidateOption> options,
        string[]? nbest = null,
        string mode = "default")
    {
        if (options.Count == 0) return null;

        if (Thread.CurrentThread.GetApartmentState() != ApartmentState.STA)
        {
            string? result = null;
            var thread = new Thread(() =>
            {
                using var f = new TsfCandidatePickerForm(raw, options, nbest, mode);
                result = f.ShowDialog() == DialogResult.OK ? f.SelectedText : null;
            });
            thread.SetApartmentState(ApartmentState.STA);
            thread.Start();
            thread.Join();
            return result;
        }

        using var form = new TsfCandidatePickerForm(raw, options, nbest, mode);
        return form.ShowDialog() == DialogResult.OK ? form.SelectedText : null;
    }
}
