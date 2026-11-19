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


def test_rss_concurrent_reads():
    from concurrent.futures import ThreadPoolExecutor

    def batch(_):
        return [rssize.rss() for _ in range(4)]

    with ThreadPoolExecutor(max_workers=8) as executor:
        chunks = list(executor.map(batch, range(8)))
    values = [v for chunk in chunks for v in chunk]
    assert len(values) == 32
    non_positive = [
        v for v in values if not (isinstance(v, int) and v > 0)]
    assert not non_positive, f"non-positive reads: {non_positive[:8]}"
    lo, hi = min(values), max(values)
    assert hi - lo < CHURN_TOLERANCE, (
        f"reads disagree: min={lo} max={hi} spread={hi - lo} "
        f"tolerance={CHURN_TOLERANCE} chunks={chunks}")


def test_rss_concurrent_errors():
    # interleaved reads of the own pid and of a dead pid: an OSError in
    # one thread must not disturb another thread's result; this also
    # races the lazy sysctl binding in _common on the bsd legs
    from concurrent.futures import ThreadPoolExecutor

    def one(task):
        kind, pid = task
        try:
            return kind, rssize.rss(pid=pid)
        except OSError as err:
            return kind, err

    tasks = [("self", None), ("dead", -1)] * 16
    with ThreadPoolExecutor(max_workers=8) as executor:
        outcomes = list(executor.map(one, tasks))
    self_results = [o for kind, o in outcomes if kind == "self"]
    dead_errors = [o for kind, o in outcomes if kind == "dead"]
    assert len(self_results) == len(dead_errors) == 16
    bad_self = [v for v in self_results if not (isinstance(v, int) and v > 0)]
    assert not bad_self, f"bad self reads: {bad_self[:8]} all={self_results}"
    lo, hi = min(self_results), max(self_results)
    assert hi - lo < CHURN_TOLERANCE, (
        f"self reads disagree: min={lo} max={hi} spread={hi - lo} "
        f"tolerance={CHURN_TOLERANCE} all={self_results}")
    bad_dead = [e for e in dead_errors if not isinstance(e, OSError)]
    assert not bad_dead, (
        f"dead pid did not raise OSError: {bad_dead[:4]} all={dead_errors!r}")
    dead_types = {type(e).__name__ for e in dead_errors}
    assert len(dead_types) == 1, (
        f"mixed dead-pid error types: "
        f"{[(type(e).__name__, getattr(e, 'errno', None)) for e in dead_errors]}")
