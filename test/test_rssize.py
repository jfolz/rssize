import os
import subprocess
import sys

import pytest

import rssize

PROCESS_UPPER_BOUND = 1024 * 1024 * 1024


def test_positive_int():
    value = rssize.rss()
    assert isinstance(value, int)
    assert value > 0


def test_page_size():
    page = rssize.page_size()
    assert isinstance(page, int)
    assert 0 < page <= 1024 * 1024
    assert page & (page - 1) == 0  # page sizes are powers of two


def test_default_pid_is_own():
    # same tolerance as the repeatability test: a few pages may churn
    # between the two calls
    assert abs(rssize.rss(pid=os.getpid()) - rssize.rss()) < 1024 * 1024


def test_child_process():
    child = subprocess.Popen(
        [sys.executable, "-c", "import time; time.sleep(10)"])
    try:
        # the child is same-user, so its counters are accessible on
        # every supported platform; the fresh interpreter sits well
        # below the upper bound
        value = rssize.rss(pid=child.pid)
    finally:
        child.wait()
    assert isinstance(value, int)
    assert 0 < value < PROCESS_UPPER_BOUND


def test_repeatable():
    first = rssize.rss()
    second = rssize.rss()
    # the working set may churn by pages between calls but stays in the
    # same ballpark: the process does not quadruple out of nowhere
    assert abs(second - first) < 1024 * 1024


def test_allocation_growth():
    import gc
    gc.collect()
    before = rssize.rss()

    page = rssize.page_size()
    alloc = 64 * 1024 * 1024
    ballast = bytearray(alloc)
    # touch every page at the page's own stride: working set counters
    # only count resident pages, and the page size is 16K on macos/arm,
    # up to 64K on other systems
    ballast[::page] = b"x" * len(range(0, alloc, page))
    after = rssize.rss()

    del ballast
    assert after - before > 32 * 1024 * 1024


def test_rss_matches_psutil_when_installed():
    psutil = pytest.importorskip("psutil")
    # both instruments read the same kernel counter within microseconds,
    # so they agree within a small churn tolerance, independent of the
    # page size
    assert abs(rssize.rss() - psutil.Process().memory_info().rss) < 64 * 1024
