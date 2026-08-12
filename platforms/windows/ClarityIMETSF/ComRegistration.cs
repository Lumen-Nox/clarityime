using System.Runtime.InteropServices;
using Microsoft.Win32;

namespace ClarityIMETSF;

/// <summary>Registers ClarityIME as a Windows TSF Text Input Processor (TIP).</summary>
[ComVisible(false)]
public static class ComRegistration
{
    const string TipRegBase = @"SOFTWARE\Microsoft\CTF\TIP";
    const string ClsIdBase = @"SOFTWARE\Classes\CLSID";

    [ComRegisterFunction]
    public static void Register(Type t)
    {
        if (t != typeof(ClarityTextInputProcessor))
            return;

        RegisterTipKeys(GetAssemblyPath(t));
    }

    [ComUnregisterFunction]
    public static void Unregister(Type t)
    {
        if (t != typeof(ClarityTextInputProcessor))
            return;

        UnregisterTipKeys();
    }

    static string GetAssemblyPath(Type t)
    {
        // For .NET COM hosting, registration script uses .comhost.dll path.
        return t.Assembly.Location;
    }

    internal static void RegisterTipKeys(string comhostDllPath)
    {
        var tipGuid = ClarityImeGuids.TextInputProcessor;
        var tipKey = $@"{TipRegBase}\{{{tipGuid}}}";
        var clsidKey = $@"{ClsIdBase}\{{{tipGuid}}}";

        using (var tip = Registry.LocalMachine.CreateSubKey(tipKey))
        {
            tip?.SetValue("Description", "ClarityIME Voice Clarify");
            tip?.SetValue("IconIndex", 0, RegistryValueKind.DWord);
            tip?.SetValue("IconFile", comhostDllPath);
            tip?.SetValue("Category", $"{{{ClarityImeGuids.KeyboardCategory}}}");
        }

        foreach (var (langId, desc) in new[] { (ClarityImeGuids.LangEnUs, "ClarityIME (English)"), (ClarityImeGuids.LangZhCn, "ClarityIME (中文)") })
        {
            using var prof = Registry.LocalMachine.CreateSubKey($@"{tipKey}\LanguageProfile\{langId}");
            prof?.SetValue("Description", desc);
            prof?.SetValue("IconFile", comhostDllPath);
            prof?.SetValue("Enable", 1, RegistryValueKind.DWord);
        }

        using (var clsid = Registry.LocalMachine.CreateSubKey(clsidKey))
        {
            clsid?.SetValue(null, "ClarityIME Text Input Processor");
            using var inproc = clsid?.CreateSubKey("InprocServer32");
            inproc?.SetValue(null, comhostDllPath);
            inproc?.SetValue("ThreadingModel", "Apartment");
        }
    }

    internal static void UnregisterTipKeys()
    {
        var tipGuid = ClarityImeGuids.TextInputProcessor;
        Registry.LocalMachine.DeleteSubKeyTree($@"{TipRegBase}\{{{tipGuid}}}", false);
        Registry.LocalMachine.DeleteSubKeyTree($@"{ClsIdBase}\{{{tipGuid}}}", false);
    }
}
