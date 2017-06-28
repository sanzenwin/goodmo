# -*- coding: utf-8 -*-
import importlib
import KBEngine
import settings
from kbe.core import Equalization as EqualizationCore
from kbe.protocol import Type, Base, BaseMethod
from plugins.conf import SettingsEntity


class Equalization(KBEngine.Base):
    base = Base(
        addEntity=BaseMethod(Type.UNICODE, Type.PY_LIST, Type.MAILBOX),
    )

    class EqualizationBase:
        def __init__(self):
            super().__init__()
            if not EqualizationCore.isCompleted():
                KBEngine.globalData["Equalization"].addEntity(self.__class__.__name__, self.equalizationPath, self)

    class DatabaseBase(KBEngine.Base):
        def writeToDB(self, callback=None, shouldAutoLoad=False):
            super().writeToDB(callback, shouldAutoLoad, self.dbInterfaceName)

        def executeRawDatabaseCommand(self, command, callback=None, threadID=-1):
            KBEngine.executeRawDatabaseCommand(command, callback, threadID, self.dbInterfaceName)

    @classmethod
    def markAll(cls):
        for name in EqualizationCore.entities:
            module = importlib.import_module(name)
            entityClass = getattr(module, name)
            setattr(module, name, type(entityClass.__name__, (entityClass, cls.EqualizationBase), {}))

    @classmethod
    def databaseAll(cls):
        for name, v in settings.__dict__.items():
            if not isinstance(v, SettingsEntity):
                continue
            try:
                module = importlib.import_module(name)
                entityClass = getattr(module, name)
                if not issubclass(entityClass, KBEngine.Base):
                    continue
                dbInterfaceName = getattr(v, "database", None) or "default"
                setattr(module, name, type(entityClass.__name__, (cls.DatabaseBase, entityClass),
                                           dict(dbInterfaceName=dbInterfaceName)))
            except ImportError:
                pass

    @classmethod
    def discover(cls):
        cls.markAll()
        cls.databaseAll()

    def __init__(self):
        super().__init__()
        KBEngine.globalData["Equalization"] = self
        self.entities = {}

    def addEntity(self, name, path, entity):
        self.entities[name + "_%s" * len(path) % tuple(path)] = entity
        self.checkCompleted()

    def checkCompleted(self):
        for path in EqualizationCore.getAllPath():
            if "_".join([str(i) for i in path]) not in self.entities:
                return
        self.onCompleted()

    def onCompleted(self):
        KBEngine.globalData["Equalization"] = self.entities
        self.destroy()
