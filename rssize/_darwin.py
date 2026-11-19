import ctypes

from ._common import page_size

__all__ = ["page_size", "rss"]


class _PROC_TASKINFO(ctypes.Structure):
    """
    proc_taskinfo (libproc.h).
    """
    _fields_ = [
        ("pti_virtual_size", ctypes.c_uint64),
        ("pti_resident_size", ctypes.c_uint64),
        ("pti_total_user", ctypes.c_uint64),
        ("pti_total_system", ctypes.c_uint64),
        ("pti_threads_user", ctypes.c_uint64),
        ("pti_threads_system", ctypes.c_uint64),
        ("pti_policy", ctypes.c_int32),
        ("pti_faults", ctypes.c_int32),
        ("pti_pageins", ctypes.c_int32),
        ("pti_cow_faults", ctypes.c_int32),
        ("pti_messages_sent", ctypes.c_uint64),
        ("pti_messages_received", ctypes.c_uint64),
        ("pti_syscalls_mach", ctypes.c_uint64),
        ("pti_syscalls_unix", ctypes.c_uint64),
        ("pti_csw", ctypes.c_uint64),
        ("pti_threadnum", ctypes.c_int32),
        ("pti_numrunning", ctypes.c_int32),
        ("pti_priority", ctypes.c_int32),
    ]


_PROC_PIDTASKINFO = 4  # flavor id from libproc.h

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
    info = _PROC_TASKINFO()
    if _libc.proc_pidinfo(
            pid, _PROC_PIDTASKINFO, 0, ctypes.byref(info),
            ctypes.sizeof(info)) != ctypes.sizeof(info):
        errno = ctypes.get_errno()
        detail = f"errno {errno}" if errno else "invalid pid or access denied"
        raise OSError(
            f"proc_pidinfo(PROC_PIDTASKINFO) for pid {pid} failed: {detail}")
    return info.pti_resident_size
