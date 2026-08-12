using System.Runtime.InteropServices;

namespace ClarityIMETSF.Interop;
// ClarityImeGuids referenced from parent namespace for TsfConstants.

// TSF COM interfaces — minimal subset for ITfTextInputProcessor skeleton.
// Full IME: ITfKeyEventSink, ITfCompositionSink, ITfDisplayAttributeProvider, etc.
// Ref: https://learn.microsoft.com/en-us/windows/win32/api/msctf/nn-msctf-itftextinputprocessor

[ComImport]
[Guid("AA80E905-2021-11D2-93E0-0060B067B86E")]
[InterfaceType(ComInterfaceType.InterfaceIsIUnknown)]
public interface ITfTextInputProcessor
{
    void Activate(ITfThreadMgr ptim, uint clientId);
    void Deactivate();
}

[ComImport]
[Guid("AA80E801-2021-11D2-93E0-0060B067B86E")]
[InterfaceType(ComInterfaceType.InterfaceIsIUnknown)]
public interface ITfThreadMgr
{
    void Activate(out uint clientId);
    void Deactivate();
    void CreateDocumentMgr(out ITfDocumentMgr ppdim);
    void EnumDocumentMgrs(out IntPtr ppEnum);
    void GetFocus(out ITfDocumentMgr ppdimFocus);
    void SetFocus(ITfDocumentMgr pdimFocus);
    void AssociateFocus(IntPtr hwnd, ITfDocumentMgr pdimNew, out ITfDocumentMgr ppdimPrev);
    void IsThreadFocus([MarshalAs(UnmanagedType.Bool)] out bool pfThreadFocus);
    void GetFunctionProvider([In] ref Guid clsid, out ITfFunctionProvider ppFuncProv);
    void EnumFunctionProviders(out IntPtr ppEnum);
    void GetGlobalCompartment(out ITfCompartmentMgr ppCompMgr);
}

[ComImport]
[Guid("AA80E7FF-2021-11D2-93E0-0060B067B86E")]
[InterfaceType(ComInterfaceType.InterfaceIsIUnknown)]
public interface ITfContext
{
    void RequestEditSession(uint ec, ITfEditSession pes, uint dwFlags, out int pfEcs);
    void InWriteSession(out int pfWriteSession);
    void GetSelection(uint ec, uint ulIndex, uint ulCount, [Out] TF_SELECTION[] pSelection, out uint pcFetched);
    void SetSelection(uint ec, uint ulCount, [In] TF_SELECTION[] pSelection);
    void GetStart(out ITfRange ppStart);
    void GetEnd(out ITfRange ppEnd);
    void GetActiveView(out ITfContextView ppView);
    void EnumViews(out IntPtr ppEnum);
    void GetStatus(out TF_STATUS pdcs);
    void GetProperty([In] ref Guid refguid, out ITfProperty ppProp);
    void GetAppProperty([In] ref Guid refguid, out ITfReadOnlyProperty ppProp);
    void TrackProperties([In] ref Guid prgProp, uint cProp, [In] ref Guid prgAppProp, uint cAppProp, ITfRangeAnchor ppRange, ITfPropertyChangeSink pSink, out uint pdwCookie);
    void EnumProperties(out IntPtr ppEnum);
    void GetDocumentMgr(out ITfDocumentMgr ppdm);
    void CreateRangeBackup(uint ec, ITfRange pRange, out ITfRangeBackup ppBackup, out int pfSuccess);
    void CreateRange(uint cpStart, uint cpEnd, out ITfRange ppRange);
    void GetCompartment(out ITfCompartmentMgr ppCompMgr);
    void GetLangId(out ushort plangid);
    void GetOwnerClsid(out Guid pclsid);
}

[ComImport]
[Guid("AA80E804-2021-11D2-93E0-0060B067B86E")]
[InterfaceType(ComInterfaceType.InterfaceIsIUnknown)]
public interface ITfEditSession
{
    void DoEditSession(uint ec);
}

[ComImport]
[Guid("AA80E7FD-2021-11D2-93E0-0060B067B86E")]
[InterfaceType(ComInterfaceType.InterfaceIsIUnknown)]
public interface ITfInsertAtSelection
{
    void InsertTextAtSelection(uint ec, [MarshalAs(UnmanagedType.LPWStr)] string pchText, uint cch, out ITfRange ppRange);
}

[ComImport]
[Guid("AA80E808-2021-11D2-93E0-0060B067B86E")]
[InterfaceType(ComInterfaceType.InterfaceIsIUnknown)]
public interface ITfKeyEventSink
{
    void OnSetFocus([MarshalAs(UnmanagedType.Bool)] bool fForeground);
    void OnTestKeyDown(ITfContext pic, uint wParam, uint lParam, [MarshalAs(UnmanagedType.Bool)] out bool pfEaten);
    void OnTestKeyUp(ITfContext pic, uint wParam, uint lParam, [MarshalAs(UnmanagedType.Bool)] out bool pfEaten);
    void OnKeyDown(ITfContext pic, uint wParam, uint lParam, [MarshalAs(UnmanagedType.Bool)] out bool pfEaten);
    void OnKeyUp(ITfContext pic, uint wParam, uint lParam, [MarshalAs(UnmanagedType.Bool)] out bool pfEaten);
}

[ComImport]
[Guid("AA80E802-2021-11D2-93E0-0060B067B86E")]
[InterfaceType(ComInterfaceType.InterfaceIsIUnknown)]
public interface ITfDocumentMgr
{
    void CreateContext(uint ec, uint dwFlags, [In] ref Guid riid, out IntPtr ppv, out uint pdwContextOut);
    void Push(ITfContext pic);
    void Pop(uint dwFlags);
    void GetTop(out ITfContext ppic);
    void GetBase(out ITfContext ppic);
    void EnumContexts(out IntPtr ppEnum);
    void GetContextFromPosition(uint ec, uint cpPos, uint cch, out ITfContext ppic, out uint plcpPos);
    void GetAssociated(out IntPtr ppEnum);
    void IsEmpty(out int pfEmpty);
}

// Stub interfaces referenced above — only what we need for compilation / future work.

[ComImport]
[Guid("AA80E803-2021-11D2-93E0-0060B067B86E")]
[InterfaceType(ComInterfaceType.InterfaceIsIUnknown)]
public interface ITfRange
{
    void GetText(uint ec, uint dwFlags, [Out] char[] pchText, uint cchMax, out uint pcch);
    void SetText(uint ec, uint dwFlags, [MarshalAs(UnmanagedType.LPWStr)] string pchText, int cch);
    void GetFormattedText(uint ec, [In] ref Guid pguidService, [In] ref Guid riid, out IntPtr ppv);
    void GetEmbedded(uint ec, [In] ref Guid rguidService, [In] ref Guid riid, out IntPtr ppv);
    void InsertEmbedded(uint ec, uint dwFlags, IntPtr pBlob);
    void ShiftStart(uint ec, int cchReq, out int pcch, [In] ref TF_HALTCONDITION pHalt);
    void ShiftEnd(uint ec, int cchReq, out int pcch, [In] ref TF_HALTCONDITION pHalt);
    void ShiftStartToRange(uint ec, ITfRange pRange, TFAnchor aPos);
    void ShiftEndToRange(uint ec, ITfRange pRange, TFAnchor aPos);
    void ShiftStartRegion(uint ec, TFShiftDir dir, [MarshalAs(UnmanagedType.Bool)] out bool pfNoRegion);
    void ShiftEndRegion(uint ec, TFShiftDir dir, [MarshalAs(UnmanagedType.Bool)] out bool pfNoRegion);
    void IsEmpty(uint ec, TFAnchor aPos, [MarshalAs(UnmanagedType.Bool)] out bool pfEmpty);
    void CompareStart(uint ec, ITfRange pWith, TFAnchor aPos, out int plResult);
    void CompareEnd(uint ec, ITfRange pWith, TFAnchor aPos, out int plResult);
    void CompareRange(uint ec, ITfRange pWith, out int plResult);
    void GetExtent(uint ec, TFAnchor aPos, out int pcpStart, out int pcpEnd);
    void Collapse(uint ec, TFAnchor aPos);
    void Clone(out ITfRange ppClone);
    void GetContext(out ITfContext ppContext);
    void GetEmbeddedContext(uint ec, out IntPtr ppContext);
    void GetStatus(out TF_STATUS pdcs);
    void GetLanguageId(uint ec, out ushort plangid);
    void AdjustForInsert(uint ec, uint cchInsert, [MarshalAs(UnmanagedType.Bool)] out bool pfInsertOk);
    void GetGravity(out TFGravity pgStart, out TFGravity pgEnd);
    void SetGravity(uint ec, TFGravity gStart, TFGravity gEnd);
    void ShiftStartToEnd(uint ec, ITfRange pRange, uint dwFlags);
    void ShiftEndToEnd(uint ec, ITfRange pRange, uint dwFlags);
    void ShiftStartToStart(uint ec, ITfRange pRange, uint dwFlags);
    void ShiftEndToStart(uint ec, ITfRange pRange, uint dwFlags);
}

[ComImport]
[Guid("AA80E805-2021-11D2-93E0-0060B067B86E")]
[InterfaceType(ComInterfaceType.InterfaceIsIUnknown)]
public interface ITfContextView { }

[ComImport]
[Guid("AA80E806-2021-11D2-93E0-0060B067B86E")]
[InterfaceType(ComInterfaceType.InterfaceIsIUnknown)]
public interface ITfProperty { }

[ComImport]
[Guid("AA80E807-2021-11D2-93E0-0060B067B86E")]
[InterfaceType(ComInterfaceType.InterfaceIsIUnknown)]
public interface ITfReadOnlyProperty { }

[ComImport]
[Guid("AA80E809-2021-11D2-93E0-0060B067B86E")]
[InterfaceType(ComInterfaceType.InterfaceIsIUnknown)]
public interface ITfRangeAnchor { }

[ComImport]
[Guid("AA80E80A-2021-11D2-93E0-0060B067B86E")]
[InterfaceType(ComInterfaceType.InterfaceIsIUnknown)]
public interface ITfPropertyChangeSink { }

[ComImport]
[Guid("AA80E80B-2021-11D2-93E0-0060B067B86E")]
[InterfaceType(ComInterfaceType.InterfaceIsIUnknown)]
public interface ITfRangeBackup { }

[ComImport]
[Guid("AA80E80C-2021-11D2-93E0-0060B067B86E")]
[InterfaceType(ComInterfaceType.InterfaceIsIUnknown)]
public interface ITfCompartmentMgr { }

[ComImport]
[Guid("AA80E80D-2021-11D2-93E0-0060B067B86E")]
[InterfaceType(ComInterfaceType.InterfaceIsIUnknown)]
public interface ITfFunctionProvider { }

[StructLayout(LayoutKind.Sequential)]
public struct TF_SELECTION
{
    public ITfRange Range;
    public TFSelectionStyle Style;
}

[StructLayout(LayoutKind.Sequential)]
public struct TFSelectionStyle
{
    public TFAnchor ase;
    public TFGravity aGravity;
}

[StructLayout(LayoutKind.Sequential)]
public struct TF_STATUS
{
    public uint dwStaticFlags;
    public uint dwDynamicFlags;
}

[StructLayout(LayoutKind.Sequential)]
public struct TF_HALTCONDITION
{
    public TFHalt Halt;
    public uint aHalt;
}

public enum TFAnchor
{
    TF_ANCHOR_START = 0,
    TF_ANCHOR_END = 1,
}

public enum TFGravity
{
    TF_GRAVITY_BACKWARD = 0,
    TF_GRAVITY_FORWARD = 1,
}

public enum TFShiftDir
{
    TF_SD_BACKWARD = 0,
    TF_SD_FORWARD = 1,
}

public enum TFHalt
{
    TF_HF_NONE = 0,
}

public enum TFSelectionStyleFlags
{
    TF_ST_NONE = 0,
}

public static class TsfConstants
{
    public const uint TF_ES_READ = 0x0002;
    public const uint TF_ES_READWRITE = 0x0006;
    public const uint TF_ES_SYNC = 0x0001;
    public const uint TF_ES_ASYNCDONTCARE = 0x0000;

    public static readonly Guid IID_ITfInsertAtSelection = new("AA80E7FD-2021-11D2-93E0-0060B067B86E");
    public static readonly Guid GUID_TFCAT_TIP_KEYBOARD = new("34745C63-B2F0-4784-8B67-5E12C8701A31");
}
