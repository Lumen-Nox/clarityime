namespace ClarityIMEHost;

using System.Text.Json;

/// <summary>Main settings UI — no terminal required.</summary>
sealed class SettingsForm : Form
{
    readonly CoreClient _core = new();
    readonly Label _coreStatus;
    readonly ComboBox _modeBox;
    readonly ComboBox _contactBox;
    readonly ComboBox _langBox;
    readonly ComboBox _modelBox;
    readonly ComboBox _applyBox;
    readonly ListView _contactList;
    readonly TextBox _newName;
    readonly TextBox _newRelation;
    readonly TextBox _newStyle;
    readonly TextBox _newComprehension;
    readonly TrackBar _tbClarity;
    readonly TrackBar _tbWarmth;
    readonly TrackBar _tbEfficiency;
    readonly TrackBar _tbPrecision;
    readonly TrackBar _tbHumor;
    readonly ComboBox _moodBox;
    readonly Label _securityStatus;
    readonly CheckBox _cloudSync;
    readonly CheckBox _aggregateResearch;
    readonly CheckBox _autoApplyTop;

    public string Mode =>
        (_modeBox.SelectedItem as ModeOption)?.Value
        ?? AudienceModes.Normalize(_modeBox.SelectedItem?.ToString());
    public string? ContactName =>
        _contactBox.SelectedItem?.ToString() is { } s && s != "(none)" ? s : null;

    public SettingsForm(string currentMode, string? currentContact)
    {
        Text = "ClarityIME 设置";
        Width = 620;
        Height = 680;
        StartPosition = FormStartPosition.CenterScreen;
        Font = UiTheme.BodyFont;
        BackColor = UiTheme.Surface;

        var tabs = new TabControl { Dock = DockStyle.Fill };
        Controls.Add(tabs);

        // --- General tab ---
        var general = new TabPage("常规");
        tabs.TabPages.Add(general);

        _coreStatus = new Label
        {
            Text = "Core: …",
            AutoSize = true,
            Location = new Point(12, 16),
        };
        general.Controls.Add(_coreStatus);

        var btnStartCore = new Button { Text = "启动 Core", Location = new Point(12, 44), Width = 100 };
        btnStartCore.Click += (_, _) => StartCore();
        general.Controls.Add(btnStartCore);

        var btnRefresh = new Button { Text = "刷新", Location = new Point(120, 44), Width = 80 };
        btnRefresh.Click += (_, _) => RefreshAll();
        general.Controls.Add(btnRefresh);

        general.Controls.Add(new Label { Text = "面向对象", Location = new Point(12, 88), AutoSize = true, Font = UiTheme.TitleFont });
        _modeBox = new ComboBox
        {
            Location = new Point(12, 108),
            Width = 240,
            DropDownStyle = ComboBoxStyle.DropDownList,
        };
        foreach (var m in AudienceModes.All)
            _modeBox.Items.Add(m);
        var normMode = AudienceModes.Normalize(currentMode);
        _modeBox.SelectedItem = AudienceModes.All.FirstOrDefault(m => m.Value == normMode)
            ?? AudienceModes.All[0];
        general.Controls.Add(_modeBox);

        general.Controls.Add(new Label
        {
            Text = "本地规则清晰化，不调用在线模型。同一句话 + 同一对象 → 结果一致。",
            Location = new Point(12, 136),
            Size = new Size(520, 32),
            ForeColor = UiTheme.TextMuted,
        });

        general.Controls.Add(new Label { Text = "联系人（contact 模式）", Location = new Point(12, 172), AutoSize = true });
        _contactBox = new ComboBox
        {
            Location = new Point(12, 192),
            Width = 240,
            DropDownStyle = ComboBoxStyle.DropDownList,
        };
        general.Controls.Add(_contactBox);

        general.Controls.Add(new Label { Text = "语音识别语言 (auto=自动)", Location = new Point(12, 228), AutoSize = true });
        _langBox = new ComboBox
        {
            Location = new Point(12, 248),
            Width = 200,
            Items = { "auto", "zh", "en", "ja", "ko" },
        };
        general.Controls.Add(_langBox);

        general.Controls.Add(new Label { Text = "本地语音识别模型", Location = new Point(260, 228), AutoSize = true });
        _modelBox = new ComboBox
        {
            Location = new Point(260, 248),
            Width = 120,
            Items = { "tiny", "base", "small", "medium" },
        };
        general.Controls.Add(_modelBox);

        general.Controls.Add(new Label { Text = "应用到光标", Location = new Point(12, 284), AutoSize = true });
        _applyBox = new ComboBox
        {
            Location = new Point(12, 304),
            Width = 200,
            DropDownStyle = ComboBoxStyle.DropDownList,
            Items = { "auto", "paste", "clipboard_only" },
        };
        general.Controls.Add(_applyBox);

        _autoApplyTop = new CheckBox
        {
            Text = "一键发送推荐（跳过候选窗）",
            Location = new Point(12, 332),
            AutoSize = true,
        };
        general.Controls.Add(_autoApplyTop);

        general.Controls.Add(new Label
        {
            Text = "快捷键: Ctrl+Shift+Space 说话 → Enter 发送推荐 → 自动粘贴",
            Location = new Point(12, 360),
            AutoSize = true,
            ForeColor = UiTheme.TextMuted,
        });

        // --- Contacts tab ---
        var contactsTab = new TabPage("联系人");
        tabs.TabPages.Add(contactsTab);

        _contactList = new ListView
        {
            View = View.Details,
            FullRowSelect = true,
            Location = new Point(8, 8),
            Size = new Size(520, 120),
        };
        _contactList.Columns.Add("姓名", 90);
        _contactList.Columns.Add("关系", 70);
        _contactList.Columns.Add("Cerome", 100);
        _contactList.Columns.Add("风格", 100);
        _contactList.Columns.Add("误解备注", 140);
        _contactList.SelectedIndexChanged += (_, _) => LoadSelectedContactIntoForm();
        contactsTab.Controls.Add(_contactList);

        _newName = AddField(contactsTab, "姓名", 136);
        _newRelation = AddField(contactsTab, "关系", 164);
        _newStyle = AddField(contactsTab, "风格/标签", 192);
        _newComprehension = AddField(contactsTab, "TA 常误解你什么", 220);

        contactsTab.Controls.Add(new Label
        {
            Text = "沟通偏好（L2）",
            Location = new Point(8, 252),
            AutoSize = true,
            Font = UiTheme.TitleFont,
        });
        _tbClarity = AddCeromeSlider(contactsTab, "清晰", 272);
        _tbWarmth = AddCeromeSlider(contactsTab, "温和", 296);
        _tbEfficiency = AddCeromeSlider(contactsTab, "效率", 320);
        _tbPrecision = AddCeromeSlider(contactsTab, "精确", 344);
        _tbHumor = AddCeromeSlider(contactsTab, "幽默", 368);
        contactsTab.Controls.Add(new Label { Text = "当前状态", Location = new Point(8, 396), AutoSize = true });
        _moodBox = new ComboBox
        {
            Location = new Point(140, 392),
            Width = 160,
            DropDownStyle = ComboBoxStyle.DropDownList,
        };
        _moodBox.Items.AddRange(["steady", "stressed", "upbeat", "tired", "focused"]);
        _moodBox.SelectedIndex = 0;
        contactsTab.Controls.Add(_moodBox);

        var btnAddContact = new Button { Text = "添加/更新", Location = new Point(8, 428), Width = 100 };
        btnAddContact.Click += (_, _) => AddContact();
        contactsTab.Controls.Add(btnAddContact);

        var btnDelContact = new Button { Text = "删除选中", Location = new Point(116, 428), Width = 100 };
        btnDelContact.Click += (_, _) => DeleteContact();
        contactsTab.Controls.Add(btnDelContact);

        var btnExportContact = new Button { Text = "导出联系人 JSON", Location = new Point(224, 428), Width = 130 };
        btnExportContact.Click += (_, _) => ExportContactJson();
        contactsTab.Controls.Add(btnExportContact);

        var btnImportContact = new Button { Text = "从文件导入", Location = new Point(362, 428), Width = 100 };
        btnImportContact.Click += (_, _) => ImportContactJson();
        contactsTab.Controls.Add(btnImportContact);

        // --- Privacy tab ---
        var privacy = new TabPage("隐私");
        tabs.TabPages.Add(privacy);

        _cloudSync = new CheckBox
        {
            Text = "加密备份（可选，默认关）",
            Location = new Point(12, 20),
            AutoSize = true,
        };
        privacy.Controls.Add(_cloudSync);

        _aggregateResearch = new CheckBox
        {
            Text = "匿名聚合研究贡献 (默认关)",
            Location = new Point(12, 52),
            AutoSize = true,
        };
        privacy.Controls.Add(_aggregateResearch);

        _securityStatus = new Label
        {
            Text = "Security: …",
            Location = new Point(12, 84),
            Size = new Size(480, 36),
            ForeColor = Color.Gray,
        };
        privacy.Controls.Add(_securityStatus);

        privacy.Controls.Add(new Label
        {
            Text = "清晰化在本地完成，使用确定性规则，不调用生成式 AI。L3 私密词不出设备。",
            Location = new Point(12, 124),
            Size = new Size(480, 40),
            ForeColor = UiTheme.TextMuted,
        });

        // --- Bottom buttons ---
        var bottom = new Panel { Dock = DockStyle.Bottom, Height = 48 };
        Controls.Add(bottom);

        var save = new Button { Text = "保存", DialogResult = DialogResult.OK, Width = 90, Location = new Point(360, 10) };
        var cancel = new Button { Text = "取消", DialogResult = DialogResult.Cancel, Width = 90, Location = new Point(456, 10) };
        bottom.Controls.Add(save);
        bottom.Controls.Add(cancel);
        AcceptButton = save;
        CancelButton = cancel;

        Load += (_, _) =>
        {
            SetCeromeSliders(null, "steady");
            RefreshAll();
        };
        if (!string.IsNullOrEmpty(currentContact))
            _contactBox.Tag = currentContact;
    }

    static TextBox AddField(Control parent, string label, int y)
    {
        parent.Controls.Add(new Label { Text = label, Location = new Point(8, y + 2), AutoSize = true });
        var tb = new TextBox { Location = new Point(140, y), Width = 380 };
        parent.Controls.Add(tb);
        return tb;
    }

    static TrackBar AddCeromeSlider(Control parent, string label, int y)
    {
        parent.Controls.Add(new Label { Text = label, Location = new Point(8, y + 4), Width = 48 });
        var tb = new TrackBar
        {
            Location = new Point(60, y),
            Width = 460,
            Minimum = 0,
            Maximum = 100,
            TickFrequency = 10,
        };
        parent.Controls.Add(tb);
        return tb;
    }

    void SetCeromeSliders(CeromeL2Values? cerome, string mood)
    {
        var c = cerome ?? new CeromeL2Values(0.7, 0.5, 0.5, 0.5, 0.3);
        _tbClarity.Value = (int)Math.Round(c.Clarity * 100);
        _tbWarmth.Value = (int)Math.Round(c.Warmth * 100);
        _tbEfficiency.Value = (int)Math.Round(c.Efficiency * 100);
        _tbPrecision.Value = (int)Math.Round(c.Precision * 100);
        _tbHumor.Value = (int)Math.Round(c.Humor * 100);
        var moodIdx = _moodBox.Items.IndexOf(mood);
        _moodBox.SelectedIndex = moodIdx >= 0 ? moodIdx : 0;
    }

    CeromeL2Values CeromeFromSliders() => new(
        _tbClarity.Value / 100.0,
        _tbWarmth.Value / 100.0,
        _tbEfficiency.Value / 100.0,
        _tbPrecision.Value / 100.0,
        _tbHumor.Value / 100.0);

    void LoadSelectedContactIntoForm()
    {
        if (_contactList.SelectedItems.Count == 0) return;
        var name = _contactList.SelectedItems[0].Text;
        var contact = _core.ListContacts().FirstOrDefault(c => c.Name == name);
        if (contact == null) return;
        _newName.Text = contact.Name;
        _newRelation.Text = contact.Relationship;
        _newStyle.Text = contact.StyleNotes;
        _newComprehension.Text = contact.ComprehensionNotes;
        SetCeromeSliders(contact.Cerome, contact.MoodLabel);
    }

    void StartCore()
    {
        CoreProcessManager.EnsureRunning();
        _coreStatus.Text = CoreProcessManager.WaitForHealthy()
            ? "Core: ✓ 运行中 (127.0.0.1:17800)"
            : "Core: ✗ 未连接 — 请检查 Python/venv";
        _coreStatus.ForeColor = _coreStatus.Text.Contains("✓") ? Color.Green : Color.DarkRed;
    }

    void RefreshAll()
    {
        var ok = _core.IsHealthy();
        _coreStatus.Text = ok ? "Core: ✓ 运行中 (127.0.0.1:17800)" : "Core: ✗ 未连接 — 点「启动 Core」";
        _coreStatus.ForeColor = ok ? Color.Green : Color.DarkRed;

        if (!ok) CoreProcessManager.EnsureRunning();

        LoadContacts();
        LoadSettings();
        LoadConsent();
        LoadSecurity();
    }

    void LoadSecurity()
    {
        var sec = _core.GetSecurityStatus();
        _securityStatus.Text = sec == null
            ? "Security: Core offline"
            : $"Security: loopback={sec.Value.Loopback} · key={sec.Value.KeyBackend} · cerome={sec.Value.CeromeTags}";
    }

    void LoadContacts()
    {
        _contactList.Items.Clear();
        _contactBox.Items.Clear();
        _contactBox.Items.Add("(none)");
        foreach (var c in _core.ListContacts())
        {
            var ceromeHint = c.Cerome == null
                ? c.MoodLabel
                : $"{c.MoodLabel} · {c.Cerome.Clarity:0.0}";
            _contactList.Items.Add(new ListViewItem(new[]
            {
                c.Name, c.Relationship, ceromeHint, c.StyleNotes, c.ComprehensionNotes,
            }));
            _contactBox.Items.Add(c.Name);
        }
        var tag = _contactBox.Tag as string;
        if (!string.IsNullOrEmpty(tag) && _contactBox.Items.Contains(tag))
            _contactBox.SelectedItem = tag;
        else
            _contactBox.SelectedIndex = 0;
    }

    void LoadSettings()
    {
        using var doc = _core.GetSettings();
        if (doc == null) return;
        var root = doc.RootElement;
        if (root.TryGetProperty("asr_language", out var lang))
            _langBox.Text = lang.GetString() ?? "auto";
        if (root.TryGetProperty("whisper_model", out var model))
            _modelBox.Text = model.GetString() ?? "base";
        if (root.TryGetProperty("default_audience", out var aud) && aud.GetString() is { } a)
        {
            var norm = AudienceModes.Normalize(a);
            _modeBox.SelectedItem = AudienceModes.All.FirstOrDefault(m => m.Value == norm)
                ?? AudienceModes.All[0];
        }
        if (root.TryGetProperty("apply_mode", out var ap) && ap.GetString() is { } am)
            _applyBox.SelectedItem = am;
        if (root.TryGetProperty("default_contact", out var dc) && dc.ValueKind == JsonValueKind.String)
        {
            var name = dc.GetString();
            if (!string.IsNullOrEmpty(name) && _contactBox.Items.Contains(name))
                _contactBox.SelectedItem = name;
        }
        if (root.TryGetProperty("auto_apply_top", out var aat))
            _autoApplyTop.Checked = aat.ValueKind == JsonValueKind.True;
    }

    void LoadConsent()
    {
        var c = _core.GetConsent();
        if (c == null) return;
        _cloudSync.Checked = c.Value.CloudSync;
        _aggregateResearch.Checked = c.Value.AggregateResearch;
    }

    void AddContact()
    {
        var name = _newName.Text.Trim();
        if (string.IsNullOrEmpty(name))
        {
            MessageBox.Show("请填写姓名", "ClarityIME", MessageBoxButtons.OK, MessageBoxIcon.Warning);
            return;
        }
        if (!_core.IsHealthy()) StartCore();
        if (!_core.SaveContact(
                name,
                _newRelation.Text.Trim(),
                _newStyle.Text.Trim(),
                _newComprehension.Text.Trim(),
                CeromeFromSliders(),
                _moodBox.SelectedItem?.ToString() ?? "steady"))
        {
            MessageBox.Show("保存失败 — Core 是否运行？", "ClarityIME", MessageBoxButtons.OK, MessageBoxIcon.Error);
            return;
        }
        _newName.Clear();
        LoadContacts();
    }

    void DeleteContact()
    {
        if (_contactList.SelectedItems.Count == 0) return;
        var name = _contactList.SelectedItems[0].Text;
        if (MessageBox.Show($"删除联系人 {name}？", "ClarityIME", MessageBoxButtons.YesNo) != DialogResult.Yes)
            return;
        _core.DeleteContact(name);
        LoadContacts();
    }

    void ExportContactJson()
    {
        if (_contactList.SelectedItems.Count == 0)
        {
            MessageBox.Show("请先选中要导出的联系人", "ClarityIME", MessageBoxButtons.OK, MessageBoxIcon.Information);
            return;
        }
        if (!_core.IsHealthy()) StartCore();
        var name = _contactList.SelectedItems[0].Text;
        var json = _core.ExportContactBundle(name);
        if (string.IsNullOrEmpty(json))
        {
            MessageBox.Show("导出失败 — Core 是否运行？", "ClarityIME", MessageBoxButtons.OK, MessageBoxIcon.Error);
            return;
        }
        using var dlg = new SaveFileDialog
        {
            Title = "导出联系人 JSON",
            Filter = "JSON (*.json)|*.json|All files (*.*)|*.*",
            FileName = $"{name}-clarityime-contact.json",
            OverwritePrompt = true,
        };
        if (dlg.ShowDialog(this) != DialogResult.OK) return;
        File.WriteAllText(dlg.FileName, json, System.Text.Encoding.UTF8);
        MessageBox.Show($"已导出 → {dlg.FileName}", "ClarityIME", MessageBoxButtons.OK, MessageBoxIcon.Information);
    }

    void ImportContactJson()
    {
        using var dlg = new OpenFileDialog
        {
            Title = "从文件导入联系人",
            Filter = "JSON (*.json)|*.json|All files (*.*)|*.*",
        };
        if (dlg.ShowDialog(this) != DialogResult.OK) return;
        string json;
        try
        {
            json = File.ReadAllText(dlg.FileName, System.Text.Encoding.UTF8);
        }
        catch (Exception ex)
        {
            MessageBox.Show($"无法读取文件: {ex.Message}", "ClarityIME", MessageBoxButtons.OK, MessageBoxIcon.Error);
            return;
        }
        if (!_core.IsHealthy()) StartCore();
        if (!_core.ImportContactBundle(json))
        {
            MessageBox.Show("导入失败 — 检查 JSON 格式与 Core 连接", "ClarityIME", MessageBoxButtons.OK, MessageBoxIcon.Error);
            return;
        }
        LoadContacts();
        MessageBox.Show("联系人已导入", "ClarityIME", MessageBoxButtons.OK, MessageBoxIcon.Information);
    }

    public void Persist()
    {
        _core.SaveSettings(
            _langBox.Text.Trim(),
            _modelBox.Text.Trim(),
            Mode,
            _applyBox.SelectedItem?.ToString(),
            _autoApplyTop.Checked);
        _core.SaveConsent(_cloudSync.Checked, _aggregateResearch.Checked);
    }

    public static (string Mode, string? Contact)? ShowDialog(IWin32Window? owner, string mode, string? contact)
    {
        using var f = new SettingsForm(mode, contact);
        if (f.ShowDialog(owner) != DialogResult.OK) return null;
        f.Persist();
        return (f.Mode, f.ContactName);
    }
}
