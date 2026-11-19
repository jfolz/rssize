# rssize

Pure Python package to read the current resident set size (RSS)
of a process and memory page size of the system.
Supports Linux, Windows, MacOS, Free/Net/OpenBSD, and Solaris.

Unless you have very specific requirements,
you should probably use psutil instead.

```python
import rssize
rssize.rss()  # -> 51_203_072
rssize.page_size()  # -> 4096
```
