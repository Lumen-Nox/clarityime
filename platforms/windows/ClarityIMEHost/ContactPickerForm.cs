namespace ClarityIMEHost;

sealed class ContactPickerForm : Form
{
    public string? SelectedContactName { get; private set; }

    public ContactPickerForm(IReadOnlyList<ContactRow> contacts, string? currentName)
    {
        Text = "ClarityIME — pick contact";
        Width = 420;
        Height = 320;
        StartPosition = FormStartPosition.CenterScreen;
        FormBorderStyle = FormBorderStyle.FixedDialog;
        MaximizeBox = false;

        var list = new ListBox { Dock = DockStyle.Fill, Font = new Font(Font.FontFamily, 11f) };
        var names = new List<string?>();
        list.Items.Add("(none)");
        names.Add(null);
        foreach (var c in contacts)
        {
            list.Items.Add(string.IsNullOrEmpty(c.Relationship) ? c.Name : $"{c.Name} ({c.Relationship})");
            names.Add(c.Name);
        }
        var idx = names.IndexOf(currentName);
        if (idx >= 0) list.SelectedIndex = idx;
        else if (list.Items.Count > 0) list.SelectedIndex = 0;
        Controls.Add(list);

        var panel = new FlowLayoutPanel
        {
            Dock = DockStyle.Bottom,
            Height = 44,
            FlowDirection = FlowDirection.RightToLeft,
            Padding = new Padding(8),
        };
        var ok = new Button { Text = "OK", DialogResult = DialogResult.OK, Width = 90 };
        var cancel = new Button { Text = "Cancel", DialogResult = DialogResult.Cancel, Width = 90 };
        panel.Controls.Add(ok);
        panel.Controls.Add(cancel);
        Controls.Add(panel);

        AcceptButton = ok;
        CancelButton = cancel;
        ok.Click += (_, _) =>
        {
            if (list.SelectedIndex >= 0 && list.SelectedIndex < names.Count)
                SelectedContactName = names[list.SelectedIndex];
        };
    }

    public static string? Pick(IReadOnlyList<ContactRow> contacts, string? currentName)
    {
        using var f = new ContactPickerForm(contacts, currentName);
        return f.ShowDialog() == DialogResult.OK ? f.SelectedContactName : currentName;
    }
}
