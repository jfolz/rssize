import ctypes
import errno

from ._common import page_size, process_error
from ._sysctl import sysctl

__all__ = ["page_size", "rss"]


_CTL_KERN = 1       # sys/sysctl.h
_KERN_PROC = 66
_KERN_PROC_PID = 1
_KI_NGROUPS = 16
_KI_MAXCOMLEN = 24  # includes NUL
_KI_WMESGLEN = 8
_KI_MAXLOGNAME = 32
_KI_EMULNAMELEN = 8


class _KINFO_PROC(ctypes.Structure):
    """
    struct kinfo_proc (sys/sysctl.h).
    """
    _fields_ = [
        ("p_forw", ctypes.c_uint64),
        ("p_back", ctypes.c_uint64),
        ("p_paddr", ctypes.c_uint64),
        ("p_addr", ctypes.c_uint64),
        ("p_fd", ctypes.c_uint64),
        ("p_stats", ctypes.c_uint64),
        ("p_limit", ctypes.c_uint64),
        ("p_vmspace", ctypes.c_uint64),
        ("p_sigacts", ctypes.c_uint64),
        ("p_sess", ctypes.c_uint64),
        ("p_tsess", ctypes.c_uint64),
        ("p_ru", ctypes.c_uint64),
        ("p_eflag", ctypes.c_int32),
        ("p_exitsig", ctypes.c_int32),
        ("p_flag", ctypes.c_int32),
        ("p_pid", ctypes.c_int32),
        ("p_ppid", ctypes.c_int32),
        ("p_sid", ctypes.c_int32),
        ("p__pgid", ctypes.c_int32),
        ("p_tpgid", ctypes.c_int32),
        ("p_uid", ctypes.c_uint32),
        ("p_ruid", ctypes.c_uint32),
        ("p_gid", ctypes.c_uint32),
        ("p_rgid", ctypes.c_uint32),
        ("p_groups", ctypes.c_uint32 * _KI_NGROUPS),
        ("p_ngroups", ctypes.c_int16),
        ("p_jobc", ctypes.c_int16),
        ("p_tdev", ctypes.c_uint32),
        ("p_estcpu", ctypes.c_uint32),
        ("p_rtime_sec", ctypes.c_uint32),
        ("p_rtime_usec", ctypes.c_uint32),
        ("p_cpticks", ctypes.c_int32),
        ("p_pctcpu", ctypes.c_uint32),
        ("p_swtime", ctypes.c_uint32),
        ("p_slptime", ctypes.c_uint32),
        ("p_schedflags", ctypes.c_int32),
        ("p_uticks", ctypes.c_uint64),
        ("p_sticks", ctypes.c_uint64),
        ("p_iticks", ctypes.c_uint64),
        ("p_tracep", ctypes.c_uint64),
        ("p_traceflag", ctypes.c_int32),
        ("p_holdcnt", ctypes.c_int32),
        ("p_siglist", ctypes.c_int32),
        ("p_sigmask", ctypes.c_uint32),
        ("p_sigignore", ctypes.c_uint32),
        ("p_sigcatch", ctypes.c_uint32),
        ("p_stat", ctypes.c_int8),
        ("p_priority", ctypes.c_uint8),
        ("p_usrpri", ctypes.c_uint8),
        ("p_nice", ctypes.c_uint8),
        ("p_xstat", ctypes.c_uint16),
        ("p_spare", ctypes.c_uint16),
        ("p_comm", ctypes.c_char * _KI_MAXCOMLEN),
        ("p_wmesg", ctypes.c_char * _KI_WMESGLEN),
        ("p_wchan", ctypes.c_uint64),
        ("p_login", ctypes.c_char * _KI_MAXLOGNAME),
        ("p_vm_rssize", ctypes.c_int32),  # resident set in pages
        ("p_vm_tsize", ctypes.c_int32),
        ("p_vm_dsize", ctypes.c_int32),
        ("p_vm_ssize", ctypes.c_int32),
        ("p_uvalid", ctypes.c_int64),
        ("p_ustart_sec", ctypes.c_uint64),
        ("p_ustart_usec", ctypes.c_uint32),
        ("p_uutime_sec", ctypes.c_uint32),
        ("p_uutime_usec", ctypes.c_uint32),
        ("p_ustime_sec", ctypes.c_uint32),
        ("p_ustime_usec", ctypes.c_uint32),
        ("p_uru_maxrss", ctypes.c_uint64),
        ("p_uru_ixrss", ctypes.c_uint64),
        ("p_uru_idrss", ctypes.c_uint64),
        ("p_uru_isrss", ctypes.c_uint64),
        ("p_uru_minflt", ctypes.c_uint64),
        ("p_uru_majflt", ctypes.c_uint64),
        ("p_uru_nswap", ctypes.c_uint64),
        ("p_uru_inblock", ctypes.c_uint64),
        ("p_uru_oublock", ctypes.c_uint64),
        ("p_uru_msgsnd", ctypes.c_uint64),
        ("p_uru_msgrcv", ctypes.c_uint64),
        ("p_uru_nsignals", ctypes.c_uint64),
        ("p_uru_nvcsw", ctypes.c_uint64),
        ("p_uru_nivcsw", ctypes.c_uint64),
        ("p_uctime_sec", ctypes.c_uint32),
        ("p_uctime_usec", ctypes.c_uint32),
        ("p_psflags", ctypes.c_uint32),
        ("p_acflag", ctypes.c_uint32),
        ("p_svuid", ctypes.c_uint32),
        ("p_svgid", ctypes.c_uint32),
        ("p_emul", ctypes.c_char * _KI_EMULNAMELEN),
        ("p_rlim_rss_cur", ctypes.c_uint64),
        ("p_cpuid", ctypes.c_uint64),
        ("p_vm_map_size", ctypes.c_uint64),
        ("p_tid", ctypes.c_int32),
        ("p_rtableid", ctypes.c_uint32),
        ("p_pledge", ctypes.c_uint64),
        ("p_name", ctypes.c_char * _KI_MAXCOMLEN),
    ]


def rss(pid):
    # two-phase call as in libkvm's kvm_getprocs:
    # first ask for the length, then read one element of sizeof(kinfo_proc)
    # bytes that is passed to the kernel as the element size in the MiB
    element_size = ctypes.sizeof(_KINFO_PROC)
    mib = [_CTL_KERN, _KERN_PROC, _KERN_PROC_PID, pid, element_size, 0]
    size = ctypes.c_size_t(0)
    if not sysctl(mib, None, ctypes.byref(size)):
        raise process_error(pid, "sysctl(kinfo_proc)", ctypes.get_errno())
    # sysctl reports success with a zero length if the pid doesn't
    # exist; the buffer max() below would still read a zeroed struct
    if size.value == 0:
        raise process_error(pid, "sysctl(kinfo_proc)", errno.ESRCH)
    buffer = ctypes.create_string_buffer(max(size.value, element_size))
    size = ctypes.c_size_t(ctypes.sizeof(buffer))
    mib[5] = ctypes.sizeof(buffer) // element_size
    if not sysctl(mib, ctypes.byref(buffer), ctypes.byref(size)):
        raise process_error(pid, "sysctl(kinfo_proc)", ctypes.get_errno())
    if size.value == 0:
        raise process_error(pid, "sysctl(kinfo_proc)", errno.ESRCH)
    info = _KINFO_PROC()
    ctypes.memmove(ctypes.byref(info), buffer, ctypes.sizeof(info))
    return info.p_vm_rssize * page_size()
