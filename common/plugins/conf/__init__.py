import sys


class SettingsNode(object):
    nodeNames = []

    def __init__(self, **kwargs):
        self.dict = {}
        for k, v in kwargs.items():
            setattr(self, k, v)
            self.dict[k] = v.dict if isinstance(v, SettingsNode) else v

    def __getitem__(self, item):
        return getattr(self, item)

    def __getattr__(self, item):
        return None

    def collect_nodes(self):
        nodeNames = set()
        for c in self.__class__.mro():
            for k, v in c.__dict__.items():
                if isinstance(v, SettingsNode):
                    nodeNames.add(k)
        self.nodeNames = sorted(nodeNames)


class SettingsEntity(SettingsNode):
    pass


class EqualizationMixin:
    min_int = -sys.maxsize
    equalization_format = "%s"

    def mod(self, x, y):
        return x % y

    def range(self, x, xx):
        find = self.min_int
        for n in xx:
            if x < n:
                break
            find = n
        return find

    def equalization(self):
        raise NotImplementedError("subclass[%s] should implement this method!" % self.__class__.__name__)

    def equalization_list(self):
        raise NotImplementedError("subclass[%s] should implement this method!" % self.__class__.__name__)

    def init_equalization_format(self):
        item = self.equalization_list()[0]
        self.equalization_format = self.__class__.__name__ + "_" + "_".join(["%s"] * len(item))


class Str(str):
    pass
