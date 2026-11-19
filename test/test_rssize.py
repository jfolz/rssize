import gc
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


def test_rss_realistic_value():
    value = rssize.rss()
    assert isinstance(value, int)
    assert 0 < value < RSS_MAX


def test_rss_default_pid():
    assert abs(rssize.rss(pid=os.getpid()) - rssize.rss()) < CHURN_TOLERANCE


def test_rss_child_process():
    child = subprocess.Popen(
        [sys.executable, "-c", "import time; time.sleep(60)"])
    try:
        value = rssize.rss(pid=child.pid)
    finally:
        child.kill()
        child.wait()
    assert isinstance(value, int)
    assert 0 < value < RSS_MAX


def test_rss_repeatability():
    first = rssize.rss()
    second = rssize.rss()
    assert abs(second - first) < CHURN_TOLERANCE


def test_rss_allocation_growth():
    gc.collect()
    before = rssize.rss()
    alloc = bytearray(RSS_MAX)  # noqa: F841
    after = rssize.rss()
    assert after - before > RSS_MAX // 2


def test_page_size_power_of_2():
    pg = rssize.page_size()
    assert isinstance(pg, int)
    # assume page size is always a power of 2
    # if we read gargabe it's highly unlikely to be 2^n
    assert pg > 0 and pg.bit_count() == 1


def test_rss_bad_pid_raises():
    for bad_pid in (-1, 2**31 - 1):  # largest possible pid_t, never real
        with pytest.raises(OSError) as excinfo:
            rssize.rss(pid=bad_pid)
        err = excinfo.value
        # the string is os-generated and localized; the numeric code is
        # the only portable truth (absent code == a made-up error)
        assert err.errno or getattr(err, "winerror", None)
