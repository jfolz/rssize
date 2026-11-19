import ctypes
import os

__all__ = ["page_size", "rss"]


class _PROCESS_MEMORY_COUNTERS(ctypes.Structure):
    """
    PROCESS_MEMORY_COUNTERS (psapi.h).
    """
    _fields_ = [
        ("cb", ctypes.c_uint32),
        ("page_fault_count", ctypes.c_uint32),
        ("peak_working_set", ctypes.c_size_t),
        ("working_set", ctypes.c_size_t),
        ("quota_peak_paged_pool", ctypes.c_size_t),
        ("quota_paged_pool", ctypes.c_size_t),
        ("quota_peak_non_paged_pool", ctypes.c_size_t),
        ("quota_non_paged_pool", ctypes.c_size_t),
        ("pagefile", ctypes.c_size_t),
        ("peak_pagefile", ctypes.c_size_t),
    ]


_PROCESS_QUERY_LIMITED_INFORMATION = 0x1000


class _SYSTEM_INFO(ctypes.Structure):
    """
    SYSTEM_INFO (sysinfoapi.h).
    """
    _fields_ = [
        ("w_processor_architecture", ctypes.c_uint16),
        ("w_reserved", ctypes.c_uint16),
        ("dw_page_size", ctypes.c_uint32),
        ("lp_minimum_application_address", ctypes.c_void_p),
        ("lp_maximum_application_address", ctypes.c_void_p),
        ("dw_active_processor_mask", ctypes.c_size_t),
        ("dw_number_of_processors", ctypes.c_uint32),
        ("dw_processor_type", ctypes.c_uint32),
        ("dw_allocation_granularity", ctypes.c_uint32),
        ("w_processor_level", ctypes.c_uint16),
        ("w_processor_revision", ctypes.c_uint16),
    ]

# use_last_error makes ctypes keep a private copy of the LastError of
# each call, safe from clobbering by interpreter work between the
# failing call and the exception raise; ctypes.WinError() reads only
# the live thread value, which is not safe here
_kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
_kernel32.GetCurrentProcess.restype = ctypes.c_void_p
_kernel32.OpenProcess.argtypes = (ctypes.c_uint32, ctypes.c_int,
                                  ctypes.c_uint32)
_kernel32.OpenProcess.restype = ctypes.c_void_p
_kernel32.CloseHandle.argtypes = (ctypes.c_void_p,)
_kernel32.CloseHandle.restype = ctypes.c_int
_kernel32.GetSystemInfo.argtypes = (ctypes.POINTER(_SYSTEM_INFO),)
_kernel32.GetSystemInfo.restype = None
_psapi = ctypes.WinDLL("psapi", use_last_error=True)
_psapi.GetProcessMemoryInfo.argtypes = (
    ctypes.c_void_p,
    ctypes.POINTER(_PROCESS_MEMORY_COUNTERS),
    ctypes.c_uint32,
)
_psapi.GetProcessMemoryInfo.restype = ctypes.c_int


def page_size():
    info = _SYSTEM_INFO()
    _kernel32.GetSystemInfo(ctypes.byref(info))
    return info.dw_page_size


def rss(pid):
    if pid == os.getpid():
        process = _kernel32.GetCurrentProcess()
        close = False
    else:
        process = _kernel32.OpenProcess(
            _PROCESS_QUERY_LIMITED_INFORMATION, False, pid)
        if not process:
            raise ctypes.WinError(ctypes.get_last_error())
        close = True
    try:
        counters = _PROCESS_MEMORY_COUNTERS()
        counters.cb = ctypes.sizeof(counters)
        if not _psapi.GetProcessMemoryInfo(
                process, ctypes.byref(counters), counters.cb):
            raise ctypes.WinError(ctypes.get_last_error())
        return counters.working_set
    finally:
        if close:
            _kernel32.CloseHandle(process)
