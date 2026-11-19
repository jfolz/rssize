"""
Pure Python package to read the current resident set size (RSS)
and page size of the system.
Supports Linux, Windows, MacOS, Free/Net/OpenBSD, and Solaris.

Unless you have very specific requirements,
you should probably use psutil instead.
"""

import os
import sys

__all__ = ["page_size", "rss"]
__version__ = "1.0.0"


if sys.platform.startswith("linux"):
    from . import _linux as _impl
elif sys.platform == "win32":
    from . import _win32 as _impl
elif sys.platform == "darwin":
    from . import _darwin as _impl
elif sys.platform.startswith("freebsd"):
    from . import _freebsd as _impl
elif sys.platform.startswith("openbsd"):
    from . import _openbsd as _impl
elif sys.platform.startswith("netbsd"):
    from . import _netbsd as _impl
elif sys.platform.startswith("sunos"):
    from . import _sunos as _impl
else:  # unsupported platform: fail at import time
    raise ImportError(f"{sys.platform} is not supported")


def page_size():
    """
    Returns the system's page size in bytes.
    """
    return _impl.page_size()


def rss(pid=None):
    """
    Return the current resident set size of a process in bytes.
    Defaults to calling process if pid is not given.
    """
    if pid is None:
        pid = os.getpid()
    return _impl.rss(pid)
