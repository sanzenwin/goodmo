# -*- coding: utf-8 -*-
import os
import KBEngine
import settings
from common.asyncHttp import AsyncHttp
from common.asyncio import asyncio_loop
from common.utils import server_time
from kbe.utils import TimerProxy
from kbe.core import Equalization, Database
from kbe.signals import baseapp_ready
from kbe.xml import settings_kbengine
from kbe.log import ERROR_MSG


class BaseApp(KBEngine.Base, TimerProxy):
    gameTimeInterval = 0.5 / settings_kbengine.gameUpdateHertz.value
    readyStamp = None

    instance = None
    completedSet = set()

    @classmethod
    def onReadyForLogin(cls):
        ready = cls.instance and all([x.isCompleted() for x in cls.completedSet])
        if not ready and server_time.passed(cls.readyStamp) > settings.BaseApp.readyForLoginWarringSeconds:
            ERROR_MSG("waring :: base app is waiting for ready took %s seconds" % server_time.passed(cls.readyStamp))
        return 1.0 if ready else 0.0

    @classmethod
    def onBaseAppReady(cls):
        cls.readyStamp = server_time.stamp()
        cls.instance = KBEngine.createBaseLocally('BaseApp', dict(groupIndex=int(os.getenv("KBE_BOOTIDX_GROUP")),
                                                                  globalIndex=int(os.getenv("KBE_BOOTIDX_GLOBAL"))))
        baseapp_ready.send(sender=cls.instance)

    @classmethod
    def onInit(cls, isReload):
        pass

    def __init__(self):
        super().__init__()
        self.tickLoop()
        if self.groupIndex == 1:
            KBEngine.createBaseLocally('Equalization', dict())
            Database.discover()
        self.checkEqualizationTimerID = self.addTimerProxy(0.1, self.checkEqualization, 0.1)

    def addCompletedObject(self, *args):
        self.completedSet.update(args)

    def checkEqualization(self):
        if KBEngine.globalData.get("Equalization"):
            self.delTimerProxy(self.checkEqualizationTimerID)
            self.checkEqualizationTimerID = None
            Equalization.createBaseLocally()

    def tickLoop(self):
        if settings.Global.enableAsyncHttp:
            self.addTimerProxy(self.gameTimeInterval, AsyncHttp.run_frame, self.gameTimeInterval)
        if settings.Global.enableAsyncio:
            self.addTimerProxy(self.gameTimeInterval, asyncio_loop.run_frame, self.gameTimeInterval)
