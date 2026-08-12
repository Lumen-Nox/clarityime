using System.Runtime.InteropServices;
using ClarityIMETSF.Core;
using ClarityIMETSF.Interop;

namespace ClarityIMETSF.Services;

/// <summary>Commits clarified text into the active TSF context via ITfInsertAtSelection.</summary>
static class TextCommitHelper
{
    public static bool TryCommit(ITfContext? context, string text)
    {
        if (context == null || string.IsNullOrEmpty(text))
            return false;

        try
        {
            var session = new InsertTextEditSession(context, text);
            context.RequestEditSession(
                0,
                session,
                TsfConstants.TF_ES_READWRITE | TsfConstants.TF_ES_SYNC,
                out _);
            return session.Success;
        }
        catch (Exception ex)
        {
            DebugLog.Write($"TryCommit failed: {ex.Message}");
            return false;
        }
    }

    // DebugLog moved to Services/DebugLog.cs

    sealed class InsertTextEditSession : ITfEditSession
    {
        private readonly ITfContext _context;
        private readonly string _text;

        public bool Success { get; private set; }

        public InsertTextEditSession(ITfContext context, string text)
        {
            _context = context;
            _text = text;
        }

        public void DoEditSession(uint ec)
        {
            var iid = TsfConstants.IID_ITfInsertAtSelection;
            var hr = MarshalQueryInterface(_context, ref iid, out var insertPtr);
            if (hr != 0 || insertPtr == IntPtr.Zero)
            {
                DebugLog.Write($"ITfInsertAtSelection QI failed hr=0x{hr:X8}");
                return;
            }

            try
            {
                var insert = (ITfInsertAtSelection)Marshal.GetObjectForIUnknown(insertPtr)!;
                insert.InsertTextAtSelection(ec, _text, (uint)_text.Length, out _);
                Success = true;
            }
            finally
            {
                if (insertPtr != IntPtr.Zero)
                    Marshal.Release(insertPtr);
            }
        }

        static int MarshalQueryInterface(object obj, ref Guid riid, out IntPtr ppv)
        {
            var unk = Marshal.GetIUnknownForObject(obj);
            try
            {
                return Marshal.QueryInterface(unk, ref riid, out ppv);
            }
            finally
            {
                Marshal.Release(unk);
            }
        }
    }
}
