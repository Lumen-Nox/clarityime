using System.Runtime.InteropServices;
using ClarityIMETSF.Interop;
using ClarityIMETSF.Services;

namespace ClarityIMETSF;

/// <summary>P/Invoke helpers for msctf.dll — partial ITfKeystrokeMgr access.</summary>
static class TsfNativeMethods
{
    const string Msctf = "msctf.dll";

    [DllImport(Msctf, PreserveSig = true)]
    static extern int TF_CreateThreadMgr(out ITfThreadMgr ppThreadMgr);

    // ITfKeystrokeMgr is obtained via QueryInterface on ITfThreadMgr.
    static readonly Guid IID_ITfKeystrokeMgr = new("AA80E4F0-2021-11D2-93E0-0060B067B86E");

    [ComImport]
    [Guid("AA80E4F0-2021-11D2-93E0-0060B067B86E")]
    [InterfaceType(ComInterfaceType.InterfaceIsIUnknown)]
    interface ITfKeystrokeMgr
    {
        void AdviseKeyEventSink(uint tid, ITfKeyEventSink pSink, [MarshalAs(UnmanagedType.Bool)] bool fForeground);
        void UnadviseKeyEventSink(uint dwCookie);
        void GetForeground(out uint pdwForeground);
        void TestKeyDown(uint wParam, uint lParam, [MarshalAs(UnmanagedType.Bool)] out bool pfEaten);
        void TestKeyUp(uint wParam, uint lParam, [MarshalAs(UnmanagedType.Bool)] out bool pfEaten);
        void KeyDown(uint wParam, uint lParam, [MarshalAs(UnmanagedType.Bool)] out bool pfEaten);
        void KeyUp(uint wParam, uint lParam, [MarshalAs(UnmanagedType.Bool)] out bool pfEaten);
        void GetPreservedKey(out Guid pguid, out TF_PRESERVEDKEY pPreservedKey, out uint pdwCookie);
        void SetPreservedKey(uint uVKey, uint uModifiers, [MarshalAs(UnmanagedType.LPWStr)] string pszDescription, out uint pdwCookie);
        void UnsetPreservedKey(uint uVKey, uint uModifiers);
        void PreserveKey(uint uVKey, uint uModifiers, [MarshalAs(UnmanagedType.LPWStr)] string pszDescription, out uint pdwCookie);
        void UnpreserveKey(uint uVKey, uint uModifiers);
        void UnpreserveAllKeys();
        void GetPreservedKeys(out IntPtr ppPreservedKeys, out uint pcPreservedKeys);
    }

    [StructLayout(LayoutKind.Sequential, CharSet = CharSet.Unicode)]
    struct TF_PRESERVEDKEY
    {
        public uint uVKey;
        public uint uModifiers;
    }

    public static bool TryAdviseKeyEventSink(ITfThreadMgr threadMgr, uint tid, ITfKeyEventSink sink, out uint cookie)
    {
        cookie = 0;
        try
        {
            var iid = IID_ITfKeystrokeMgr;
            var unk = Marshal.GetIUnknownForObject(threadMgr);
            try
            {
                var hr = Marshal.QueryInterface(unk, ref iid, out var ptr);
                if (hr != 0 || ptr == IntPtr.Zero) return false;
                try
                {
                    var ks = (ITfKeystrokeMgr)Marshal.GetObjectForIUnknown(ptr)!;
                    ks.AdviseKeyEventSink(tid, sink, true);
                    cookie = 1; // TODO: real cookie from AdviseKeyEventSink overload if available
                    return true;
                }
                finally
                {
                    Marshal.Release(ptr);
                }
            }
            finally
            {
                Marshal.Release(unk);
            }
        }
        catch (Exception ex)
        {
            DebugLog.Write($"TryAdviseKeyEventSink: {ex.Message}");
            return false;
        }
    }

    public static void TryUnviseKeyEventSink(ITfThreadMgr threadMgr, uint tid, uint cookie)
    {
        if (cookie == 0) return;
        try
        {
            var iid = IID_ITfKeystrokeMgr;
            var unk = Marshal.GetIUnknownForObject(threadMgr);
            try
            {
                if (Marshal.QueryInterface(unk, ref iid, out var ptr) != 0 || ptr == IntPtr.Zero) return;
                try
                {
                    var ks = (ITfKeystrokeMgr)Marshal.GetObjectForIUnknown(ptr)!;
                    ks.UnadviseKeyEventSink(cookie);
                }
                finally
                {
                    Marshal.Release(ptr);
                }
            }
            finally
            {
                Marshal.Release(unk);
            }
        }
        catch (Exception ex)
        {
            DebugLog.Write($"TryUnviseKeyEventSink: {ex.Message}");
        }
    }
}
