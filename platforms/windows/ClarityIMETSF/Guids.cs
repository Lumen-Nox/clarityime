namespace ClarityIMETSF;

/// <summary>COM / TSF identifiers for ClarityIME TIP registration.</summary>
static class ClarityImeGuids
{
    /// <summary>ClarityIME Text Input Processor CLSID — must match ComRegisterFunction.</summary>
    public const string TextInputProcessor = "8F3C2A1E-4B5D-6E7F-8091-A2B3C4D5E6F7";

    /// <summary>Windows TSF keyboard category.</summary>
    public const string KeyboardCategory = "34745C63-B2F0-4784-8B67-5E12C8701A31";

    public static readonly Guid TextInputProcessorGuid = new(TextInputProcessor);

    // Language profile IDs (LANGID hex as used under CTF\TIP\{}\LanguageProfile\)
    public const string LangEnUs = "00000409";
    public const string LangZhCn = "00000804";
}
