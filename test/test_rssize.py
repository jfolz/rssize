import os
import subprocess
import sys

import pytest

import rssize

# interpreter with pytest suite should consume < 50 MiB,
# plus a few MiB as safety margin
RSS_MAX = 64 * 1024 * 1024
# allow a few pages of churn in adjacent reads
# assume page size is less than
CHURN_TOLERANCE = 256 * 1024


def test_positive_int():
    value = rssize.rss()
    assert isinstance(value, int)
    assert 0 < value < RSS_MAX


def test_page_size():
    pg = rssize.page_size()
    assert isinstance(pg, int)
    # assume page size is always a power of 2
    # if we read gargabe it's highly unlikely to be 2^n
    assert pg > 0 and pg.bit_count() == 1


def test_default_pid_is_own():
    assert abs(rssize.rss(pid=os.getpid()) - rssize.rss()) < CHURN_TOLERANCE


def test_child_process():
    child = subprocess.Popen(
        [sys.executable, "-c", "import time; time.sleep(60)"])
    try:
        value = rssize.rss(pid=child.pid)
    finally:
        child.kill()
        child.wait()
    assert isinstance(value, int)
    assert 0 < value < RSS_MAX


def test_repeatable():
    first = rssize.rss()
    second = rssize.rss()
    assert abs(second - first) < CHURN_TOLERANCE


def test_allocation_growth():
    import gc
    gc.collect()
    before = rssize.rss()
    alloc = bytearray(RSS_MAX)  # noqa: F841
    after = rssize.rss()
    assert after - before > RSS_MAX // 2
