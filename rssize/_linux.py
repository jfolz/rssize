from ._common import page_size, process_error

__all__ = ["page_size", "rss"]


def rss(pid):
    try:
        with open(f"/proc/{pid}/statm", "rb") as f:
            resident = int(f.readline().split()[1])
    except OSError as err:
        raise process_error(pid, f"/proc/{pid}/statm lookup",
                            err.errno) from None
    return resident * page_size()
