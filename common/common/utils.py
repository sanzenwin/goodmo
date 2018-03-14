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
        return self.format("%Y-%m-%d %H:%M:%S", self.genesis)

    def format(self, s, t=None):
        t = t or self.now()
        return time.strftime(s, time.localtime(time.mktime(t.timetuple())))

    def set_cursor(self, cursor):
        self.cursor = cursor  # microseconds

    def set_date(self, to):
        self.cursor = int((to - self.genesis).total_seconds() * 1000)

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

    def last_month(self, to=None):
        if to is None:
            to = self.now()
        return to.replace(day=1) - datetime.timedelta(days=1)

    def last_week(self, to=None):
        if to is None:
            to = self.now()
        return to - datetime.timedelta(days=to.weekday(), weeks=1)

    def passed(self, stamp):
        return (self.stamp() - stamp) / 1000.0

    def get_date(self, stamp):
        return self.genesis + datetime.timedelta(milliseconds=float(stamp))

    def from_s14(self, s):
        return self.make_time(int(s[:4]), int(s[4:6]), int(s[6:8]), int(s[8:10]), int(s[10:12]), int(s[12:]))

    @staticmethod
    def now():
        return datetime.datetime.now()

    @staticmethod
    def offset(date, offset):
        return date + datetime.timedelta(microseconds=float(offset))

    @staticmethod
    def make_time(*args, **kwargs):
        return datetime.datetime(*args, **kwargs)


server_time = ServerTime()
del ServerTime


class TimeIndex:
    def __init__(self, to=None):
        self.to = server_time.now() if to is None else to
        self.genesis = server_time.genesis

    def __getitem__(self, item):
        return getattr(self, item)

    @property
    def year(self):
        return self.to.year - self.genesis.year

    @property
    def month(self):
        year = self.year
        if year == 0:
            return self.to.month - self.genesis.month
        else:
            return year * 12 - self.genesis.month + self.to.month

    @property
    def week(self):
        start_date = self.genesis - datetime.timedelta(days=self.genesis.weekday())
        new_date = server_time.make_time(start_date.year, start_date.month, start_date.day)
        return int((self.to - new_date).total_seconds()) // (7 * 24 * 60 * 60)

    @property
    def day(self):
        new_date = server_time.make_time(self.genesis.year, self.genesis.month, self.genesis.day)
        return int((self.to - new_date).total_seconds()) // (24 * 60 * 60)


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
        local_name_set = set()
        for c in target.mro():
            for n, f in c.__dict__.items():
                if isinstance(f, types.FunctionType):
                    if getattr(f, "__event__", None) is cls:
                        event_name_set.add(n)
                    if getattr(f, "__local__", None) is cls:
                        local_name_set.add((c.__name__, n))

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
        for cls_name, name in local_name_set:
            setattr(new_target, "%s__%s" % (cls_name, name), getattr(target, name))
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

    @classmethod
    def local(cls, target):
        target.__local__ = cls


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


class SteadyData:
    def __init__(self, data):
        self.data = data

    def get(self, key, default=None):
        return self.data.get(key, default)

    def set(self, key, value):
        self.data[key] = value

    def pop(self, key, default=None):
        return self.data.pop(key, default)

    def add(self, key, value=1):
        self.set(key, self.get(key, 0) + value)


class StampData(SteadyData):
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

    def set(self, key, value, stamp=None):
        super().set(key, value)
        self.__stamp__[key] = stamp or server_time.stamp()

    def get(self, key, default=None):
        if self._is_expired(key):
            self.pop(key)
            return default
        return super().get(key, default)

    def pop(self, key, default=None, stamp=None):
        self.__stamp__.pop(key, None)
        return super().pop(key, default)

    def add(self, key, value=1, stamp=True):
        self.set(key, self.get(key, 0) + value, stamp)


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
        super().set(key, value, None)

    def pop(self, key, default=None, expired=None):
        self.__expired__.pop(key, None)
        return super().pop(key, default)

    def add(self, key, value=1, expired=None):
        self.set(key, self.get(key, 0) + value, expired)


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


class List:
    def __init__(self, obj):
        self.object = obj

    def __getitem__(self, item):
        if isinstance(item, slice):
            lst = len(self.object)
            return [self.object[i] for i in
                    range(item.start or 0, len(self.object) if item.stop is None else item.stop, item.step or 1) if
                    0 <= i < lst]
        return self.object[item]

    def sort(self, key=None, reverse=False):
        new_list = self[:]
        new_list.sort(key=key, reverse=reverse)
        return new_list


class PublicAttrMap:
    class Attr(dict):
        def init(self):
            pass

        def __getattr__(self, item):
            return self[item]

    def __init__(self):
        self.map = {}

    def __getattr__(self, item):
        return self.map.setdefault(item, self.Attr())
