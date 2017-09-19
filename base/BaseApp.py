# -*- coding: utf-8 -*-
import os
import KBEngine
import settings
from common.asyncHttp import AsyncHttp
from common.asyncio import asyncio_loop
from common.utils import server_time
from kbe.utils import TimerProxy
from kbe.signals import baseapp_ready, global_data_change, global_data_del
from kbe.log import ERROR_MSG


class BaseApp(KBEngine.Base, TimerProxy):
    readyStamp = None
    notReadyTimeStamp = 0

    instance = None
    completedSet = set()

    @classmethod
    def checkType(cls, obj):
        return isinstance(obj, KBEngine.Base) or obj.__class__.__name__ == "EntityMailbox"

    @classmethod
    def onBaseAppReady(cls):
        cls.readyStamp = server_time.stamp()
        cls.instance = KBEngine.createBaseLocally('BaseApp', dict(groupIndex=int(os.getenv("KBE_BOOTIDX_GROUP")),
                                                                  globalIndex=int(os.getenv("KBE_BOOTIDX_GLOBAL"))))
        cls.instance.init()
        baseapp_ready.send(cls.instance)

    @classmethod
    def onReadyForLogin(cls):
        waiting = [x for x in cls.completedSet if not x.isCompleted()]
        ready = cls.instance and not waiting
        if ready:
            cls.notReadyTimeStamp = 0
        else:
            if server_time.passed(cls.readyStamp) > settings.BaseApp.readyForLoginWarringSeconds:
                if server_time.stamp() - cls.notReadyTimeStamp > settings.BaseApp.readyForLoginIntervalSeconds * 1000:
                    cls.notReadyTimeStamp = server_time.stamp()
                    ERROR_MSG(
                        "waring :: base app is waiting for ready took %s seconds, waiting for: %s" %
                        (server_time.passed(cls.readyStamp), waiting))
        return 1.0 if ready else 0.0

    @classmethod
    def onInit(cls, isReload):
        pass

    @classmethod
    def onBaseAppShutDown(cls, state):
        pass

    @classmethod
    def onFini(cls):
        pass

    @classmethod
    def onCellAppDeath(cls, addr):
        pass

    @classmethod
    def onGlobalData(cls, key, value):
        global_data_change.send(cls.instance, key=key, value=value)

    @classmethod
    def onGlobalDataDel(cls, key):
        global_data_del.send(cls.instance, key=key)

    @classmethod
    def onGlobalBases(cls, key, value):
        pass

    @classmethod
    def onGlobalBasesDel(cls, key):
        pass

    @classmethod
    def onLoseChargeCB(cls, ordersID, dbid, success, datas):
        pass

    def init(self):
        self.tickLoop()

    def addCompletedObject(self, *args):
        self.completedSet.update(args)

    def tickLoop(self):
        gameTimeInterval = settings.Global.gameTimeInterval
        if settings.Global.enableAsyncHttp:
            self.addTimerProxy(gameTimeInterval, AsyncHttp.run_frame, gameTimeInterval)
        if settings.Global.enableAsyncio:
            self.addTimerProxy(gameTimeInterval, asyncio_loop.run_frame, gameTimeInterval)


KBEngine.BaseApp = BaseApp
