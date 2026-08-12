namespace ClarityIMEHost;

sealed class HotkeyWindow : NativeWindow, IDisposable
{
    private const int WmHotkey = 0x0312;
    private readonly Action _onHotkey;

    [System.Runtime.InteropServices.DllImport("user32.dll")]
    private static extern bool RegisterHotKey(IntPtr hWnd, int id, uint fsModifiers, uint vk);

    [System.Runtime.InteropServices.DllImport("user32.dll")]
    private static extern bool UnregisterHotKey(IntPtr hWnd, int id);

    public HotkeyWindow(Action onHotkey)
    {
        _onHotkey = onHotkey;
        CreateHandle(new CreateParams());
        RegisterHotKey(Handle, 1, 0x0002 | 0x0004, 0x20); // Ctrl+Shift+Space
    }

    protected override void WndProc(ref Message m)
    {
        if (m.Msg == WmHotkey && m.WParam == (IntPtr)1)
            _onHotkey();
        base.WndProc(ref m);
    }

    public void Dispose()
    {
        UnregisterHotKey(Handle, 1);
        DestroyHandle();
    }
}
