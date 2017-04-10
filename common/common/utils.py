# -*- coding: utf-8 -*-
import types
import time
import datetime
from importlib import import_module


class ServerTime(object):
    def __init__(self):
        self.cursor = 0.0

    def __str__(self):
        time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(time.mktime(self.genesis.timetuple())))

    def set_cursor(self, cursor):
        self.cursor = cursor  # microseconds

    def reset(self):
        self.set_cursor(0.0)

    @property
    def genesis(self):
        return self.make_time(1986, 2, 28) + datetime.timedelta(microseconds=self.cursor)

    def stamp(self, to=None):
        if to is None:
            to = datetime.datetime.now()
        delta = to - self.genesis
        return int(delta.total_seconds() * 1000)

    def get_date(self, stamp):
        return self.genesis + datetime.timedelta(milliseconds=float(stamp))

    def make_time(self, *args):
        return datetime.datetime(*args)


server_time = ServerTime()
del ServerTime


class Event(object):
    class Meta(type):
        def __new__(mcs, *args, **kwargs):
            target = super().__new__(mcs, *args, **kwargs)
            if Event.is_opened(target):
                return target
            else:
                return Event.open(target)

    @classmethod
    def open(cls, target):
        def bind(func_name):
            def proxy(self, *args, **kwargs):
                for func in new_target.__event__[func_name]:
                    func(self, *args, **kwargs)

            proxy.__proxy__ = cls
            setattr(new_target, func_name, proxy)

        event_name_set = set()
        for c in target.mro():
            for n, f in c.__dict__.items():
                if isinstance(f, types.FunctionType) and getattr(f, "__event__", None) is cls:
                    event_name_set.add(n)

        if not event_name_set:
            return target

        event = {}
        for c in target.mro():
            for n, f in c.__dict__.items():
                if n in event_name_set and getattr(f, "__proxy__", None) is not cls:
                    lst = event.setdefault(n, [])
                    lst.append(f)
        new_target = type(target.__name__, (target,), dict(__event__=event))
        for name in event_name_set:
            bind(name)
        return new_target

    @classmethod
    def is_opened(cls, target):
        return "__event__" in target.__dict__

    @classmethod
    def method(cls, target):
        target.__event__ = cls
        return target

    @classmethod
    def interface(cls, target):
        for n, f in target.__dict__.items():
            if isinstance(f, types.FunctionType):
                setattr(target, n, cls.method(f))
        return target


class Container(object, metaclass=Event.Meta):
    pass


Event.Container = Container
del Container


def load_class(path):
    """
    Loads class from path.
    """

    mod_name, klass_name = path.rsplit('.', 1)

    try:
        mod = import_module(mod_name)
    except AttributeError as e:
        raise Exception('Error importing {0}: "{1}"'.format(mod_name, e))

    try:
        klass = getattr(mod, klass_name)
    except AttributeError:
        raise Exception('Module "{0}" does not define a "{1}" class'.format(mod_name, klass_name))

    return klass

