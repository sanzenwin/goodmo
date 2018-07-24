import sys


class SettingsNode:
    index = 0

    @classmethod
    def new_id(cls):
        cls.index += 1
        return cls.index

    def __init__(self, **kwargs):
        self.index = self.new_id()
        self.nodeNames = []
        self.multi = {}
        self.dict = {}
        for k, v in kwargs.items():
            setattr(self, k, v)
            self.dict[k] = v.dict if isinstance(v, SettingsNode) else v

    def __getitem__(self, item):
        return getattr(self, item)

    def __getattr__(self, item):
        return None

    def merge(self, lst):
        for x in reversed(lst):
            self.dict.update(x.dict)
        return self

    def collect_nodes(self):
        s = set()
        d = dict()
        for c in self.__class__.mro():
            for k, v in c.__dict__.items():
                if isinstance(v, SettingsNode):
                    s.add(k)
                    lst = d.setdefault(k, [])
                    lst.append(v)
        self.nodeNames = sorted(s)
        for k, v in d.items():
            self.multi[k] = SettingsNode().merge(v)


class SettingsEntity(SettingsNode):
    def isAutoLoaded(self):
        return getattr(self, "autoLoaded", False) or getattr(self, "autoLoadedOrCreate", False)

    def get_mro_set(self, key):
        r = {}
        for c in self.__class__.mro():
            d = c.__dict__.get(key)
            if d:
                r.update(d)
        return r


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
        equalization_list = self.equalization_list()
        if equalization_list:
            item = self.equalization_list()[0]
            amount = len(item)
        else:
            amount = 0
        self.equalization_format = self.__class__.__name__ + "_" + "_".join(["%s"] * amount)


class SingletonMixin(EqualizationMixin):
    def equalization_list(self):
        return [[0]]

    def equalization(self, *args):
        return [0]


class Str(str):
    pass


class Tuple(tuple):
    pass


class Dict(dict):
    pass


class List(list):
    pass


class Set(set):
    pass
