using System.Runtime.InteropServices;
using System.Threading;
using System.Windows.Forms;

namespace ClarityIMEHost;

static class TextInjector
{
    [DllImport("user32.dll")]
    private static extern IntPtr GetForegroundWindow();

    /// <summary>IME caret insert: clipboard + synthetic Ctrl+V (works for CJK).</summary>
    public static void Apply(string text)
    {
        var old = ClipboardGet();
        ClipboardSet(text);
        Thread.Sleep(40);
        keybd_event(0x11, 0, 0, UIntPtr.Zero); // Ctrl down
        keybd_event(0x56, 0, 0, UIntPtr.Zero); // V down
        keybd_event(0x56, 0, 2, UIntPtr.Zero); // V up
        keybd_event(0x11, 0, 2, UIntPtr.Zero); // Ctrl up
        Thread.Sleep(40);
        if (old != null) ClipboardSet(old);
    }

    [DllImport("user32.dll")]
    private static extern void keybd_event(byte bVk, byte bScan, uint dwFlags, UIntPtr dwExtraInfo);

    static void ClipboardSet(string s)
    {
        Thread sta = new(() => { System.Windows.Forms.Clipboard.SetText(s); });
        sta.SetApartmentState(ApartmentState.STA);
        sta.Start();
        sta.Join();
    }

    static string? ClipboardGet()
    {
        string? result = null;
        Thread sta = new(() =>
        {
            try { result = System.Windows.Forms.Clipboard.GetText(); } catch { }
        });
        sta.SetApartmentState(ApartmentState.STA);
        sta.Start();
        sta.Join();
        return result;
    }
}
