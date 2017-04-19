import sys


class Proxy:
    def __getattr__(self, item):
        return 0

sys.modules[__name__] = Proxy()
