"""
Code shared by the platform modules.
"""

import os


def page_size():
    """Return the number of bytes per memory page of the running OS."""
    return os.sysconf("SC_PAGE_SIZE")


def process_error(pid, action, errno_=None, winerror=None):
    """
    Uniform process-access error across platform modules.
    """
    message = f"rss for pid {pid}: {action} failed"
    if winerror is not None:
        return OSError(None, message, None, winerror)
    if errno_:
        return OSError(errno_, message)
    return OSError(message)
