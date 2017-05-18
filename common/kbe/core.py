# -*- coding: utf-8 -*-
import os
import asyncio
import importlib
import pickle
import redis
import aioredis
import KBEngine
from kbe.log import DEBUG_MSG, INFO_MSG, ERROR_MSG
from kbe.xml import Xml, settings_kbengine
from common.dispatcher import receiver
from kbe.signals import database_completed
from plugins.conf.signals import plugins_completed
from kbe.signals import baseapp_ready


class MetaOfEqualization(type):
    def __getitem__(cls, item):
        return getattr(cls, item)


class Equalization(object, metaclass=MetaOfEqualization):
    class Proxy(object):
        class InvalidProxy(object):
            def __init__(self, entity_name, keys):
                self.entity_name = entity_name
                self.keys = keys
                self.call = ""

            def __getattr__(self, item):
                self.call = item
                return self.proxy

            def proxy(self, *args, **kwargs):
                ERROR_MSG("Equalization error call: %s, %s, %s" % (self.entity_name, self.keys, self.call))

        def __init__(self, entity):
            super().__init__()
            self.entity = entity

        def __call__(self, *keys):
            path = self.entity.equalization(*keys)
            key = self.entity.equalization_format % tuple(path)
            return KBEngine.globalData["Equalization"].get(key, self.InvalidProxy(self.entity.__class__.__name__, keys))

        def path(self, *keys):
            return self.entity.equalization(*keys)

    entities = {}

    @classmethod
    def discover(cls):
        settings = importlib.import_module("settings")
        equalization = importlib.import_module("Equalization")
        for k, v in settings.__dict__.items():
            if hasattr(v, "equalization"):
                setattr(cls, k, cls.Proxy(v))
                cls.entities[k] = v
        equalization.Equalization.discover()

    @classmethod
    def getAllPath(cls):
        allPath = []
        for name in sorted(cls.entities):
            entity = cls.entities[name]
            for path in entity.equalization_list():
                allPath.append([entity.__class__.__name__] + list(entity.equalization(*path)))
        return allPath

    @classmethod
    def createBaseLocally(cls):
        settings = importlib.import_module("settings")
        index = int(os.getenv("KBE_BOOTIDX_GROUP")) - 1
        paths = cls.getAllPath()
        for i in range(index, len(paths), settings.BaseApp.equalizationBaseappAmount):
            path = paths[i]
            KBEngine.createBaseLocally(path[0], dict(equalizationPath=path[1:]))

    @classmethod
    def isCompleted(cls):
        return isinstance(KBEngine.globalData.get("Equalization"), dict)


class KBEngineProxy(object):
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
                if defs[methods][nodeName]["Exposed"]or cls.bindAll:
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
                module = importlib.import_module(nodeName)
                proxy_class = getattr(module, nodeName)
                bind(proxy_class)
                setattr(module, nodeName, cls.optimize(proxy_class))


class Redis(object):
    class Proxy(object):
        ready = False

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
            if hasattr(v, "redis"):
                objects[k] = v.redis()
                for r in objects[k].values():
                    redis_set.add(cls.dumps(r))
        if settings.BaseApp.enableAsyncio:
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

        asyncio.async(init_connections())

    @classmethod
    def isCompleted(cls):
        return cls.Proxy.ready


class Database(object):
    __taskID = 0
    __taskSet = set()

    @classmethod
    def discover(cls):
        database_completed.send(sender=cls)

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
    if sender.app in ("base", "cell"):
        Equalization.discover()
        KBEngineProxy.discover()
    Redis.discover()


@receiver(baseapp_ready)
def registerCompleted(signal, sender):
    sender.addCompletedObject(Equalization, Redis, Database)
