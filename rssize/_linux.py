from ._common import page_size

__all__ = ["page_size", "rss"]


def rss(pid):
    with open(f"/proc/{pid}/statm", "rb") as f:
        resident = int(f.readline().split()[1])
    return resident * page_size()
