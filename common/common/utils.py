# -*- coding: utf-8 -*-
import os
import re
import types
import time
import datetime
import json
from importlib import import_module


class ServerTime:
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
            to = self.now()
        delta = to - self.genesis
        return int(delta.total_seconds() * 1000)

    def passed(self, stamp):
        return (self.stamp() - stamp) / 1000.0

    @staticmethod
    def now():
        return datetime.datetime.now()

    def get_date(self, stamp):
        return self.genesis + datetime.timedelta(milliseconds=float(stamp))

    @staticmethod
    def make_time(*args, **kwargs):
        return datetime.datetime(*args, **kwargs)


server_time = ServerTime()
del ServerTime


class Event:
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
                ret = []
                for func in new_target.__event__[func_name]:
                    ret.append(func(self, *args, **kwargs))
                return ret

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
        for c in reversed(target.mro()):
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


def get_module(mod_name):
    try:
        mod = import_module(mod_name)
    except ImportError as e:
        m = re.search("No module named '(\S*)'", e.args[0])
        if m and m.group(1) in mod_name:
            return None
        raise ImportError("%s from '%s'" % (e.args[0], mod_name))
    return mod


def get_module_attr(path, default=None):
    mod_name, attr_name = path.rsplit('.', 1)
    mod = get_module(mod_name)
    if mod is None:
        return default
    return getattr(mod, attr_name, default)


module_name_re = re.compile("^[a-zA-Z_][a-zA-Z0-9_]*$")


def get_module_list(*path):
    target_dir = os.path.join(*path)
    try:
        for filename in os.listdir(target_dir):
            pathname = os.path.join(target_dir, filename)
            if os.path.isfile(pathname):
                if filename.endswith('.py') and filename != "__init__.py" and module_name_re.match(filename[:-3]):
                    yield filename[:-3]
            else:
                if module_name_re.match(filename) and filename != "__pycache__" and os.path.isfile(
                        os.path.join(pathname, '__init__.py')):
                    yield filename
    except FileNotFoundError:
        pass


def get_module_list_m(module_name):
    m = import_module(module_name)
    path = os.path.dirname(m.__file__)
    return get_module_list(path)


def get_module_all(module_name):
    m = get_module(module_name)
    if not m:
        return dict()
    d = m.__dict__
    try:
        x = m.__all__
    except AttributeError:
        x = [name for name in d if not name.startswith('_')]
    return {name: d[name] for name in x}


class Data:
    def __init__(self, data):
        self.data = data

    def get(self, key, default=None):
        return self.data.get(key, default)

    def set(self, key, value):
        self.data[key] = value

    def pop(self, key, default=None):
        return self.data.pop(key, default)


class StampData(Data):
    def __init__(self, data):
        super().__init__(data)
        self.__stamp__ = self.data.setdefault("__stamp__", dict())

    def _is_expired(self, key):
        stamp = self.__stamp__.get(key)
        if stamp is None:
            return False
        return not self.check_stamp(key, stamp)

    def check_stamp(self, key, stamp):
        raise NotImplementedError()

    def set(self, key, value, stamp=True):
        super().set(key, value)
        if stamp:
            self.__stamp__[key] = server_time.stamp()

    def get(self, key, default=None):
        if self._is_expired(key):
            self.pop(key)
            return default
        return super().get(key, default)

    def pop(self, key, default=None):
        self.__stamp__.pop(key, None)
        return super().pop(key, default)


class ExpiredData(StampData):
    def __init__(self, data):
        super().__init__(data)
        self.__expired__ = self.data.setdefault("__expired__", dict())

    def check_stamp(self, key, stamp):
        expired = self.__expired__.get(key)
        if expired is not None and expired + stamp <= server_time.stamp():
            return False
        return True

    def set(self, key, value, expired=None):
        has_expired = expired is not None
        if has_expired:
            self.__expired__[key] = expired
        super().set(key, value, has_expired)

    def pop(self, key, default=None):
        self.__expired__.pop(key, None)
        return super().pop(key, default)


class DateDate(StampData):
    def check_stamp(self, key, stamp):
        date = server_time.get_date(stamp)
        now = server_time.now()
        return self.check_date(date, now)

    def check_date(self, date, now):
        raise NotImplementedError()


class TodayData(DateDate):
    def check_date(self, date, now):
        return date.year == now.year and date.month == now.month and date.day == now.day


class WeekData(DateDate):
    week_seconds = 7 * 24 * 60 * 60

    def check_date(self, date, now):
        if now.isoweekday() < date.isoweekday():
            return False
        return (now - date).total_seconds() < self.week_seconds


class MonthData(DateDate):
    def check_date(self, date, now):
        return date.year == now.year and date.month == now.month


class YearData(DateDate):
    def check_date(self, date, now):
        return date.year == now.year


class PerformanceWatcher:
    def __init__(self, debug=True):
        self.debug = debug
        self.count = 1
        self.last_count = 0
        self.last_time = time.monotonic()
        self._t0 = 0

    def incr(self):
        self.count += 1

    def log_result(self):
        if not self.debug:
            return
        print("\nlog_result: %sms\n" % (
            (time.monotonic() - self.last_time) / ((self.count - self.last_count) or 1) * 1e3))
        self.last_count = self.count
        self.last_time = time.monotonic()

    def t0(self):
        self._t0 = time.monotonic()

    def log_t(self):
        if not self.debug:
            return
        print((time.monotonic() - self._t0) * 1e3, "ms")
        self.t0()


class ClassPropertyDescriptor(object):
    def __init__(self, fget, fset=None):
        self.fget = fget
        self.fset = fset

    def __get__(self, obj, klass=None):
        if klass is None:
            klass = type(obj)
        return self.fget.__get__(obj, klass)()

    def __set__(self, obj, value):
        if not self.fset:
            raise AttributeError("can't set attribute")
        type_ = type(obj)
        return self.fset.__get__(obj, type_)(value)

    def setter(self, func):
        if not isinstance(func, (classmethod, staticmethod)):
            func = classmethod(func)
        self.fset = func
        return self


def classproperty(func):
    if not isinstance(func, (classmethod, staticmethod)):
        func = classmethod(func)
    return ClassPropertyDescriptor(func)


class Bytes(dict):
    class Dict(dict):
        def loads(self, s):
            try:
                data = json.loads(s.decode('utf-8'))
            except ValueError:
                data = {}
            data = data if isinstance(data, dict) else {}
            self.update(data)

        def dumps(self):
            return bytes(json.dumps(self), "utf-8")

    def __new__(cls, s=None, **kwargs):
        c = cls.Dict(**kwargs)
        if s:
            c.loads(s)
        return c


class Export:
    @staticmethod
    def method(f):
        f.__export__ = True
        return f

    @staticmethod
    def is_method(f):
        return getattr(f, "__export__", False)
