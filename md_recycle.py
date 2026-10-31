"""Move a file to the Windows Recycle Bin, shared by every script and GUI.

Only the strict IFileOperation path lives here. FOFX_RECYCLEONDELETE makes the
shell refuse the legacy SHFileOperation fallback to a permanent delete, so a
note is never destroyed when the bin is unavailable on that drive.
"""
import ctypes
import os
import uuid
from pathlib import Path


def to_recycle_bin(src):
    """Send one file to the Recycle Bin. Raises OSError if it cannot."""
    if os.name != "nt":
        raise OSError("Replacing originals requires the Windows Recycle Bin")
    ole32 = ctypes.OleDLL("ole32")
    shell32 = ctypes.OleDLL("shell32")
    pointer = ctypes.c_void_p
    ole32.CoInitializeEx.argtypes = [pointer, ctypes.c_ulong]
    ole32.CoCreateInstance.argtypes = [pointer, pointer, ctypes.c_ulong, pointer, ctypes.POINTER(pointer)]
    shell32.SHCreateItemFromParsingName.argtypes = [ctypes.c_wchar_p, pointer, pointer, ctypes.POINTER(pointer)]
    ole32.CoUninitialize.argtypes = []
    ole32.CoUninitialize.restype = None

    def guid(value):
        return (ctypes.c_ubyte * 16).from_buffer_copy(uuid.UUID(value).bytes_le)

    def call(interface, index, argtypes=(), *args):
        vtable = ctypes.cast(interface, ctypes.POINTER(ctypes.POINTER(pointer))).contents
        method = ctypes.WINFUNCTYPE(ctypes.c_long, pointer, *argtypes)(vtable[index])
        hr = method(interface, *args)
        if hr < 0:
            raise OSError(f"Recycle Bin operation failed (HRESULT 0x{hr & 0xFFFFFFFF:08X})")

    operation, item = pointer(), pointer()
    ole32.CoInitializeEx(None, 2)
    try:
        ole32.CoCreateInstance(
            guid("3ad05575-8857-4850-9277-11b85bdb8e09"), None, 1,
            guid("947aab5f-0a5c-4c13-b4d6-4bf7836fc9f8"), ctypes.byref(operation),
        )
        shell32.SHCreateItemFromParsingName(
            str(Path(src).resolve()), None, guid("43826d1e-e718-42ee-bc55-a1e261c37bfe"), ctypes.byref(item),
        )
        # RECYCLEONDELETE forbids the legacy API's permanent-delete fallback.
        flags = 0x00080000 | 0x00100000 | 0x0040 | 0x0010 | 0x0400 | 0x0004 | 0x2000
        call(operation, 5, (ctypes.c_ulong,), flags)
        call(operation, 18, (pointer, pointer), item, None)
        call(operation, 21)
        aborted = ctypes.c_int()
        call(operation, 22, (ctypes.POINTER(ctypes.c_int),), ctypes.byref(aborted))
        if aborted.value:
            raise OSError("Recycle Bin operation was aborted")
    finally:
        if item:
            call(item, 2)
        if operation:
            call(operation, 2)
        ole32.CoUninitialize()
