import ctypes

from ._common import page_size

__all__ = ["page_size", "rss"]


class _PTI_RESIDENT(ctypes.Structure):
    """
    prefix of proc_taskinfo (libproc.h) through pti_resident_size.

    the kernel's struct is 96 bytes (18 fields, int32 tail) on every
    xnu from 10.13 to current main; only the 16-byte prefix is needed
    here, and a wrong full-struct transcription (uint64 tail counters,
    120 bytes) previously rejected successful kernel calls
    """
    _fields_ = [
        ("pti_virtual_size", ctypes.c_uint64),
        ("pti_resident_size", ctypes.c_uint64),
    ]


_PROC_PIDTASKINFO = 4     # flavor id from libproc.h
_PROC_TASKINFO_SIZE = 96  # sizeof(proc_taskinfo), every xnu from 10.13 on

_libc = ctypes.CDLL(None, use_errno=True)  # libSystem, contains libproc
_libc.proc_pidinfo.argtypes = (
    ctypes.c_int,
    ctypes.c_int,
    ctypes.c_uint64,
    ctypes.c_void_p,
    ctypes.c_int,
)
_libc.proc_pidinfo.restype = ctypes.c_int


def rss(pid):
    buffer = ctypes.create_string_buffer(_PROC_TASKINFO_SIZE)
    ret = _libc.proc_pidinfo(
        pid, _PROC_PIDTASKINFO, 0, buffer, _PROC_TASKINFO_SIZE)
    if ret < ctypes.sizeof(_PTI_RESIDENT):
        errno = ctypes.get_errno()
        detail = f"errno {errno}" if errno else "invalid pid or access denied"
        raise OSError(
            f"proc_pidinfo(PROC_PIDTASKINFO) for pid {pid} failed: {detail}")
    info = _PTI_RESIDENT()
    ctypes.memmove(ctypes.byref(info), buffer, ctypes.sizeof(info))
    return info.pti_resident_size
