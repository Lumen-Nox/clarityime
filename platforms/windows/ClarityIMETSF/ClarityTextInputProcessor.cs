using System.Runtime.InteropServices;
using ClarityIMETSF.Interop;
using ClarityIMETSF.Services;

namespace ClarityIMETSF;

/// <summary>ClarityIME TSF Text Input Processor — F9 voice clarify, commit via ITfContext.</summary>
[ComVisible(true)]
[Guid("8F3C2A1E-4B5D-6E7F-8091-A2B3C4D5E6F7")]
[ClassInterface(ClassInterfaceType.None)]
[ComDefaultInterface(typeof(ITfTextInputProcessor))]
public sealed class ClarityTextInputProcessor : ITfTextInputProcessor, ITfKeyEventSink
{
    private ITfThreadMgr? _threadMgr;
    private uint _clientId;
    private uint _keySinkCookie;
    private ITfContext? _activeContext;

    public void Activate(ITfThreadMgr ptim, uint clientId)
    {
        _threadMgr = ptim;
        _clientId = clientId;
        DebugLog.Write("TSF Activate");
        TryInstallKeySink();
    }

    public void Deactivate()
    {
        DebugLog.Write("TSF Deactivate");
        if (_keySinkCookie != 0 && _threadMgr != null)
            TsfNativeMethods.TryUnviseKeyEventSink(_threadMgr, _clientId, _keySinkCookie);
        _keySinkCookie = 0;
        _activeContext = null;
        _threadMgr = null;
    }

    public void OnSetFocus(bool fForeground)
    {
        if (!fForeground || _threadMgr == null) return;
        try
        {
            _threadMgr.GetFocus(out var docMgr);
            docMgr?.GetTop(out _activeContext);
        }
        catch
        {
            _activeContext = null;
        }
    }

    public void OnTestKeyDown(ITfContext pic, uint wParam, uint lParam, out bool pfEaten) =>
        pfEaten = IsVoiceHotkey(wParam);

    public void OnTestKeyUp(ITfContext pic, uint wParam, uint lParam, out bool pfEaten) =>
        pfEaten = false;

    public void OnKeyDown(ITfContext pic, uint wParam, uint lParam, out bool pfEaten)
    {
        pfEaten = false;
        if (!IsVoiceHotkey(wParam)) return;
        pfEaten = true;
        _activeContext = pic;
        Task.Run(() => VoiceClarifyPipeline.Run(pic));
    }

    public void OnKeyUp(ITfContext pic, uint wParam, uint lParam, out bool pfEaten) =>
        pfEaten = false;

    static bool IsVoiceHotkey(uint wParam) => wParam == 0x78; // VK_F9

    void TryInstallKeySink()
    {
        if (_threadMgr == null) return;
        if (TsfNativeMethods.TryAdviseKeyEventSink(_threadMgr, _clientId, this, out _keySinkCookie))
            DebugLog.Write("TSF key sink installed (F9 = voice clarify)");
        else
            DebugLog.Write("TSF key sink install failed — TODO: ITfKeystrokeMgr in native shim");
    }
}

/// <summary>Registers ClarityIME TIP in HKCU (no admin).</summary>
public static class TipRegistration
{
    public const string ProfileGuid = "9A1B2C3D-4E5F-6789-ABCD-EF0123456789";

    public static void RegisterForCurrentUser(string comHostDllPath)
    {
        var clsid = ClarityImeGuids.TextInputProcessor;
        var baseKey = $@"Software\Microsoft\CTF\TIP\{clsid}";

        using (var tip = Microsoft.Win32.Registry.CurrentUser.CreateSubKey(baseKey))
        {
            tip?.SetValue("Description", "ClarityIME (voice clarify)");
            tip?.SetValue("Category", ClarityImeGuids.KeyboardCategory);
        }

        foreach (var lang in new[] { ClarityImeGuids.LangZhCn, ClarityImeGuids.LangEnUs })
        {
            var lp = $@"{baseKey}\LanguageProfile\{lang}\{ProfileGuid}";
            using var profile = Microsoft.Win32.Registry.CurrentUser.CreateSubKey(lp);
            profile?.SetValue("Description", "ClarityIME");
            profile?.SetValue("Enable", 1, Microsoft.Win32.RegistryValueKind.DWord);
        }

        using (var clsidKey = Microsoft.Win32.Registry.CurrentUser.CreateSubKey($@"Software\Classes\CLSID\{clsid}\InProcServer32"))
        {
            clsidKey?.SetValue(null, comHostDllPath);
            clsidKey?.SetValue("ThreadingModel", "Apartment");
        }

        DebugLog.Write($"TIP registered HKCU: {comHostDllPath}");
    }

    public static void UnregisterForCurrentUser()
    {
        var clsid = ClarityImeGuids.TextInputProcessor;
        Microsoft.Win32.Registry.CurrentUser.DeleteSubKeyTree($@"Software\Microsoft\CTF\TIP\{clsid}", false);
        Microsoft.Win32.Registry.CurrentUser.DeleteSubKeyTree($@"Software\Classes\CLSID\{clsid}", false);
    }
}
