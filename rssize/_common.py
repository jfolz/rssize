"""
Code shared by multiple platform modules.
"""

import ctypes
import os

_sysctl = None  # resolved on first use: sysctl(3) is not in every libc


def page_size():
    """Return the number of bytes per memory page of the running OS."""
    return os.sysconf("SC_PAGE_SIZE")


def sysctl(mib, oldp, oldlenp):
    """Call sysctl(3); return True on success, False on failure."""
    global _sysctl
    if _sysctl is None:
        _libc = ctypes.CDLL(None, use_errno=True)
        _libc.sysctl.argtypes = (
            ctypes.POINTER(ctypes.c_int),
            ctypes.c_uint,
            ctypes.c_void_p,
            ctypes.POINTER(ctypes.c_size_t),
            ctypes.c_void_p,
            ctypes.c_size_t,
        )
        _libc.sysctl.restype = ctypes.c_int
        _sysctl = _libc.sysctl
    mib_buffer = (ctypes.c_int * len(mib))(*mib)
    return _sysctl(mib_buffer, len(mib), oldp, oldlenp, None, 0) != -1
