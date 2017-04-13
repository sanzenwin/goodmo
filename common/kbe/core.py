# -*- coding: utf-8 -*-
import os
import importlib
import redis
import KBEngine
from kbe.log import DEBUG_MSG, INFO_MSG, ERROR_MSG
from kbe.xml import Xml
from .signals import redis_discover
try:
    import cPickle as pickle
except ImportError:
    import pickle


class MetaOfEqualization(type):
    def __getitem__(cls, item):
        return getattr(cls, item)


class Equalization(object, metaclass=MetaOfEqualization):
    class Proxy(object):
        def __init__(self, entity):
            super().__init__()
            self.entity = entity

        def __call__(self, *keys):
            path = self.entity.equalization(*keys)
            key = self.entity.equalization_format % tuple(path)
            return KBEngine.globalData["Equalization"][key]

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
                if defs[methods][nodeName]["Exposed"]:
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
            if entities[nodeName].attrs.get("hasClient") == "true":
                module = importlib.import_module(nodeName)
                proxy_class = getattr(module, nodeName)
                bind(proxy_class)
                setattr(module, nodeName, cls.optimize(proxy_class))


class Redis(object):
    class Proxy(object):
        def attach(self, key, r):
            setattr(self, key, r)

    @classmethod
    def dumps(cls, s):
        return pickle.dumps(s)

    @classmethod
    def loads(cls, s):
        return pickle.loads(s)

    @classmethod
    def discover(cls):
        settings = importlib.import_module("settings")
        redis_set = set()
        objects = {}
        for k, v in settings.__dict__.items():
            if hasattr(v, "redis"):
                objects[k] = v.redis()
                for r in objects[k].values():
                    redis_set.add(r)
        redis_map = dict()
        for r in redis_set:
            redis_map[r] = redis.StrictRedis(host=r[0], port=r[1], db=r[2])
        for k, v in objects.items():
            for m, n in v.items():
                proxy = getattr(cls, k, None) or cls.Proxy()
                proxy.attach(m, redis_map[n])
                setattr(cls, k, proxy)
        redis_discover.send(sender=cls)
