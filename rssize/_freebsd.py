import ctypes
import errno

from ._common import page_size, process_error, sysctl

__all__ = ["page_size", "rss"]


_CTL_KERN = 1       # sys/sysctl.h
_KERN_PROC = 14
_KERN_PROC_PID = 1


class _SIGSET(ctypes.Structure):
    """sigset_t: 4 x 32-bit bitmaps on every supported FreeBSD ABI."""
    _fields_ = [("__bits", ctypes.c_uint32 * 4)]


class _KINFO_PROC_PREFIX(ctypes.Structure):
    """struct kinfo_proc (sys/user.h), prefix up to ki_rssize.

    Field order, types and natural alignment follow the header; ctypes
    reproduces the C layout of the Python build's own model. The sysctl
    copies the full (larger) structure, so the request buffer is bigger
    than this prefix view.
    """
    _fields_ = [
        ("ki_structsize", ctypes.c_int),
        ("ki_layout", ctypes.c_int),
        ("ki_args", ctypes.c_void_p),
        ("ki_paddr", ctypes.c_void_p),
        ("ki_addr", ctypes.c_void_p),
        ("ki_tracep", ctypes.c_void_p),
        ("ki_textvp", ctypes.c_void_p),
        ("ki_fd", ctypes.c_void_p),
        ("ki_vmspace", ctypes.c_void_p),
        ("ki_wchan", ctypes.c_void_p),
        ("ki_pid", ctypes.c_int),
        ("ki_ppid", ctypes.c_int),
        ("ki_pgid", ctypes.c_int),
        ("ki_tpgid", ctypes.c_int),
        ("ki_sid", ctypes.c_int),
        ("ki_tsid", ctypes.c_int),
        ("ki_jobc", ctypes.c_short),
        ("ki_spare_short1", ctypes.c_short),
        ("ki_tdev_freebsd11", ctypes.c_uint32),
        ("ki_siglist", _SIGSET),
        ("ki_sigmask", _SIGSET),
        ("ki_sigignore", _SIGSET),
        ("ki_sigcatch", _SIGSET),
        ("ki_uid", ctypes.c_uint32),
        ("ki_ruid", ctypes.c_uint32),
        ("ki_svuid", ctypes.c_uint32),
        ("ki_rgid", ctypes.c_uint32),
        ("ki_svgid", ctypes.c_uint32),
        ("ki_ngroups", ctypes.c_short),
        ("ki_spare_short2", ctypes.c_short),
        ("ki_groups", ctypes.c_uint32 * 16),
        ("ki_size", ctypes.c_size_t),    # vm_size_t
        ("ki_rssize", ctypes.c_size_t),  # segsz_t, resident set in pages
    ]


def rss(pid):
    buffer = ctypes.create_string_buffer(4096)  # >= sizeof(kinfo_proc)
    size = ctypes.c_size_t(ctypes.sizeof(buffer))
    mib = [_CTL_KERN, _KERN_PROC, _KERN_PROC_PID, pid]
    if not sysctl(mib, ctypes.byref(buffer), ctypes.byref(size)):
        raise process_error(pid, "sysctl(kinfo_proc)", ctypes.get_errno())
    # sysctl reports success with a zero length if the pid doesn't
    # exist; parsing the zeroed buffer would return an rss of 0
    if size.value == 0:
        raise process_error(pid, "sysctl(kinfo_proc)", errno.ESRCH)
    info = _KINFO_PROC_PREFIX()
    ctypes.memmove(ctypes.byref(info), buffer, ctypes.sizeof(info))
    return info.ki_rssize * page_size()
