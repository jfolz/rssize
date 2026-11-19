import ctypes

__all__ = ["sysctl"]


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


def sysctl(mib, oldp, oldlenp):
    """Call sysctl(3); return True on success, False on failure."""
    mib_buffer = (ctypes.c_int * len(mib))(*mib)
    return _libc.sysctl(mib_buffer, len(mib), oldp, oldlenp, None, 0) != -1
