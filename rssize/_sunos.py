import ctypes

from ._common import page_size

__all__ = ["page_size", "rss"]


class _PSINFO(ctypes.Structure):
    """
    psinfo_t prefix (sys/procfs.h) up to pr_rssize.
    """
    _fields_ = [
        ("pr_flag", ctypes.c_int),
        ("pr_nlwp", ctypes.c_int),
        ("pr_pid", ctypes.c_int),      # pid_t
        ("pr_ppid", ctypes.c_int),
        ("pr_pgid", ctypes.c_int),
        ("pr_sid", ctypes.c_int),
        ("pr_uid", ctypes.c_uint32),
        ("pr_euid", ctypes.c_uint32),
        ("pr_gid", ctypes.c_uint32),
        ("pr_egid", ctypes.c_uint32),
        ("pr_addr", ctypes.c_size_t),  # uintptr_t
        ("pr_size", ctypes.c_size_t),
        ("pr_rssize", ctypes.c_size_t),  # resident set in Kbytes
    ]


def rss(pid):
    info = _PSINFO()
    with open(f"/proc/{pid}/psinfo", "rb") as f:
        raw = f.read(ctypes.sizeof(info))
    if len(raw) != ctypes.sizeof(info):
        raise OSError(f"short read on /proc/{pid}/psinfo")
    info = _PSINFO.from_buffer_copy(raw)
    return info.pr_rssize * 1024
