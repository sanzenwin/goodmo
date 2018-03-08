# -*- coding: utf-8 -*-
import os
import asyncio
import importlib
import pickle
import redis
import aioredis
import KBEngine
import functools
from motor.motor_asyncio import AsyncIOMotorClient
from kbe.log import DEBUG_MSG, INFO_MSG, ERROR_MSG
from kbe.xml import Xml
from common.dispatcher import receiver
from kbe.signals import database_completed, redis_completed, mongodb_completed, baseapp_ready
from plugins.conf.signals import plugins_completed


class MetaOfEqualization(type):
    def __getitem__(cls, item):
        return getattr(cls, item)


class Equalization(metaclass=MetaOfEqualization):
    class Proxy:
        class InvalidProxy:
            def __init__(self, entity_name, keys):
                self.entity_name = entity_name
                self.keys = keys
                self.call = ""

            def __getattr__(self, item):
                self.call = item
                return self.proxy

            def __bool__(self):
                return False

            def proxy(self, *args, **kwargs):
                print("Equalization error call: %s, %s, %s" % (self.entity_name, self.keys, self.call))

        class AllProxy:
            def __init__(self, entity):
                self.entity = entity
                self.call = ""

            def real(self, item):
                self.call = item
                return self.proxy

            def proxy(self, *args, **kwargs):
                for keys in self.entity.equalization_list():
                    path = self.entity.equalization(*keys)
                    key = self.entity.equalization_format % tuple(path)
                    obj = KBEngine.globalData["Equalization"].get(key, None)
                    if obj:
                        getattr(obj, self.call)(*args, **kwargs)
                    else:
                        print("Equalization error call: %s, %s, %s" % (
                            self.entity.__class__.__name__, self.keys, self.call))

        def __init__(self, entity):
            super().__init__()
            self.entity = entity

        def __call__(self, *keys):
            path = self.entity.equalization(*keys)
            key = self.entity.equalization_format % tuple(path)
            return KBEngine.globalData["Equalization"].get(key, self.InvalidProxy(self.entity.__class__.__name__, keys))

        def __getattr__(self, item):
            return self.AllProxy(self.entity).real(item)

        def list(self):
            result = []
            for keys in self.entity.equalization_list():
                path = self.entity.equalization(*keys)
                key = self.entity.equalization_format % tuple(path)
                obj = KBEngine.globalData["Equalization"].get(key, None)
                result.append(obj)
            return result

        def path(self, *keys):
            return self.entity.equalization(*keys)

    memEntities = {}
    autoLoadedEntities = {}
    autoLoadedIDMap = {}

    @classmethod
    def discover(cls):
        settings = importlib.import_module("settings")
        equalization = importlib.import_module("Equalization")
        for k, v in settings.__dict__.items():
            if getattr(v, "equalization", False):
                setattr(cls, k, cls.Proxy(v))
                cls.memEntities[k] = v
            if getattr(v, "autoLoaded", False) or getattr(v, "autoLoadedOrCreate", False):
                cls.autoLoadedEntities[k] = v
        equalization.Equalization.discover()

    @classmethod
    def getAllPath(cls):
        allPath = []
        for name in sorted(cls.memEntities):
            entity = cls.memEntities[name]
            for path in entity.equalization_list():
                allPath.append([entity.__class__.__name__] + list(entity.equalization(*path)))
        return allPath

    @classmethod
    def createBaseLocally(cls):
        settings = importlib.import_module("settings")
        index = KBEngine.BaseApp.instance.groupIndex
        paths = cls.getAllPath()
        if index > settings.BaseApp.equalizationBaseappAmount:
            ERROR_MSG("BaseApp[%d] has not parted in equalization!" % index)
            return
        for i in range(index - 1, len(paths), settings.BaseApp.equalizationBaseappAmount):
            path = paths[i]
            # print(path)
            KBEngine.createEntityLocally(path[0], dict(equalizationPath=path[1:]))

    @classmethod
    def loadEntities(cls, success):
        def callback(name, result, lines, insertid, error):
            if error:
                ERROR_MSG("loadEntities: error! args: %s, %s, %s, %s, %s" % (name, result, lines, insertid, error))
            else:
                cls.autoLoadedIDMap[name] = sorted([int(x[0]) for x in result])
                if set(cls.autoLoadedIDMap) == set(cls.autoLoadedEntities):
                    success()

        for name, v in cls.autoLoadedEntities.items():
            sql_select = "select id from tbl_%s;" % name
            KBEngine.executeRawDatabaseCommand(sql_select, functools.partial(callback, name), -1, v.database)
        if not cls.autoLoadedEntities:
            success()

    @classmethod
    def getBaseIndexInfo(cls, n):
        settings = importlib.import_module("settings")
        cursor = settings.BaseApp.equalizationBaseappAmount + 1
        independence = settings.BaseApp.multi["baseappIndependence"].dict
        for name in sorted(independence):
            v = independence[name]
            count = v if isinstance(v, int) else len(v)
            if name == n:
                return list(range(cursor, cursor + count)), v
            else:
                cursor += count
        return list(), None

    @classmethod
    def isCompleted(cls):
        return isinstance(KBEngine.globalData.get("Equalization", None), dict) and KBEngine.globalData.get(
            "EqualizationEntity", None) is None


class MetaOfSingleton(type):
    class Proxy:
        class Call:
            def __init__(self, entity, method):
                self.entity = entity
                self.method = method

            def __call__(self, *args, **kwargs):
                print("Singleton error call: %s, %s" % (self.entity, self.method))

        def __init__(self, entity):
            super().__init__()
            self.entity = entity

        def __getattr__(self, method):
            return self.Call(self.entity, method)

        def __bool__(self):
            return False

    def __getattr__(cls, base):
        return KBEngine.globalData.get(cls.getKey(base), cls.Proxy(base))

    def __getitem__(cls, item):
        return getattr(cls, item)


class Singleton(metaclass=MetaOfSingleton):
    @classmethod
    def getKey(cls, name):
        return "%s_%s" % (cls.__name__, name)

    @classmethod
    def add(cls, obj):
        name = obj.__class__.__name__
        assert cls.getKey(name) not in KBEngine.globalData, "[%s], [%s] is in global data." % (name, cls.getKey(name))
        KBEngine.globalData[cls.getKey(name)] = obj

    @classmethod
    def remove(cls, obj):
        del KBEngine.globalData[cls.getKey(obj.__class__.__name__)]


class KBEngineProxy:
    bindAll = False

    @classmethod
    def optimize(cls, target):
        def bind(func_name):
            def proxy(self, *args, **kwargs):
                if self.isReqReady():
                    method(self, *args, **kwargs)
                else:
                    ERROR_MSG("%s is not ready: %s" % (self, func_name))

            method = getattr(target, func_name)
            setattr(target, func_name, proxy)

        defs = Xml(os.path.join('entity_defs', target.__name__ + ".def"))
        methods = dict(baseapp="BaseMethods", cellapp="CellMethods")[KBEngine.component]
        if defs[methods]:
            for nodeName in defs[methods].nodeNames:
                if defs[methods][nodeName]["Exposed"] or cls.bindAll:
                    bind(nodeName)
        return target

    @classmethod
    def discover(cls):

        def bind(proxy_cls):

            def isReqReady(self):
                return not self.isDestroyed

            setattr(proxy_cls, "isReqReady", getattr(proxy_cls, "isReqReady", isReqReady))

        entities = Xml("entities.xml")
        for nodeName in entities.nodeNames:
            if entities[nodeName].attrs.get("hasClient") == "true" or cls.bindAll:
                try:
                    m = importlib.import_module(nodeName)
                except ImportError:
                    continue
                proxy_class = getattr(m, nodeName)
                bind(proxy_class)
                setattr(m, nodeName, cls.optimize(proxy_class))


class Subscriptable(type):
    def __getitem__(self, item):
        return getattr(self, item)


class Redis(metaclass=Subscriptable):
    class Proxy:
        ready = False

        def __getitem__(self, item):
            return getattr(self, item)

        def attach(self, key, r):
            setattr(self, key, r)

    @classmethod
    def dumps(cls, s):
        return pickle.dumps(s)

    @classmethod
    def loads(cls, s):
        return s if s is None else pickle.loads(s)

    @classmethod
    def discover(cls):
        settings = importlib.import_module("settings")
        redis_set = set()
        objects = {}
        for k, v in settings.__dict__.items():
            if hasattr(v, "redis") and v.redis:
                objects[k] = v.redis()
                for r in objects[k].values():
                    redis_set.add(cls.dumps(r))
        if settings.Global.enableAsyncio:
            cls.generateAsyncRedis(redis_set, objects)
        else:
            cls.generateRedis(redis_set, objects)

    @classmethod
    def attach(cls, redis_map, objects):
        for k, v in objects.items():
            for m, n in v.items():
                proxy = getattr(cls, k, None) or cls.Proxy()
                proxy.attach(m, redis_map[cls.dumps(n)])
                setattr(cls, k, proxy)
        cls.Proxy.ready = True

    @classmethod
    def generateRedis(cls, redis_set, objects):
        redis_map = dict()
        for p in redis_set:
            r = cls.loads(p)
            redis_map[p] = redis.StrictRedis(host=r["host"], port=r["port"], db=r["db"], password=r.get("password"))
        cls.attach(redis_map, objects)
        redis_completed.send(cls)

    @classmethod
    def generateAsyncRedis(cls, redis_set, objects):
        @asyncio.coroutine
        def init_connections():
            redis_map = dict()
            for p in redis_set:
                r = cls.loads(p)
                redis_map[p] = yield from aioredis.create_redis((r["host"], r["port"]), db=r["db"],
                                                                password=r.get("password"))
            cls.attach(redis_map, objects)
            redis_completed.send(cls)

        asyncio.async(init_connections())

    @classmethod
    def isCompleted(cls):
        return cls.Proxy.ready


class Mongodb(metaclass=Subscriptable):
    class Proxy:
        ready = False

        def __getitem__(self, item):
            return getattr(self, item)

        def attach(self, key, r):
            setattr(self, key, r)

    @classmethod
    def dumps(cls, s):
        return pickle.dumps(s)

    @classmethod
    def loads(cls, s):
        return s if s is None else pickle.loads(s)

    @classmethod
    def discover(cls):
        settings = importlib.import_module("settings")
        mongodb_set = set()
        objects = {}
        for k, v in settings.__dict__.items():
            if hasattr(v, "mongodb") and v.mongodb:
                objects[k] = v.mongodb()
                for r in objects[k].values():
                    mongodb_set.add(cls.dumps(r))
        if settings.Global.enableAsyncio:
            cls.generateAsyncMongodb(mongodb_set, objects)

    @classmethod
    def attach(cls, mongodb_map, objects):
        for k, v in objects.items():
            for m, n in v.items():
                proxy = getattr(cls, k, None) or cls.Proxy()
                proxy.attach(m, mongodb_map[cls.dumps(n)]["goodmo__%s" % os.getenv("uid")][k + m])
                setattr(cls, k, proxy)
        cls.Proxy.ready = True

    @classmethod
    def generateAsyncMongodb(cls, mongodb_set, objects):
        @asyncio.coroutine
        def init_connections():
            mongodb_map = dict()
            for p in mongodb_set:
                r = cls.loads(p)
                if "uri" in r:
                    c = dict(host=r["uri"])
                else:
                    c = dict(authSource="goodmo__%s" % os.getenv("uid"), **r)
                mongodb_map[p] = AsyncIOMotorClient(**c)
            cls.attach(mongodb_map, objects)
            mongodb_completed.send(cls)

        asyncio.async(init_connections())

    @classmethod
    def isCompleted(cls):
        return cls.Proxy.ready


class Database:
    __taskID = 0
    __taskSet = set()

    @classmethod
    def discover(cls):
        database_completed.send(cls)

    @classmethod
    def addTask(cls):
        cls.__taskID += 1
        cls.__taskSet.add(cls.__taskID)
        return cls.__taskID

    @classmethod
    def completeTask(cls, taskID):
        cls.__taskSet.remove(taskID)

    @classmethod
    def isCompleted(cls):
        return not cls.__taskSet


@receiver(plugins_completed)
def discover(signal, sender):
    if sender.app in ("base",):
        Equalization.discover()
    if sender.app in ("base", "cell"):
        KBEngineProxy.discover()
    if sender.app not in ("login",):
        Redis.discover()
        Mongodb.discover()


@receiver(baseapp_ready)
def baseappReady(signal, sender):
    if sender.groupIndex == 1:
        Database.discover()
    lst = [Redis, Mongodb, Database]
    settings = importlib.import_module("settings")
    if sender.groupIndex <= settings.BaseApp.equalizationBaseappAmount:
        lst.append(Equalization)
    sender.addCompletedObject(*lst)
