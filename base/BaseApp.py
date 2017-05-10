# -*- coding: utf-8 -*-
import os
import KBEngine
import settings
from common.asyncHttp import AsyncHttp
from kbe.utils import TimerProxy
from kbe.core import Equalization, Database


class BaseApp(KBEngine.Base, TimerProxy):
    @classmethod
    def onReadyForLogin(cls):
        return 1.0 if Equalization.isCompleted() and Database.isCompleted() else 0.0

    @classmethod
    def onBaseAppReady(cls):
        KBEngine.createBaseLocally('BaseApp', dict(groupIndex=int(os.getenv("KBE_BOOTIDX_GROUP")),
                                                   globalIndex=int(os.getenv("KBE_BOOTIDX_GLOBAL"))))

    @classmethod
    def onInit(cls, isReload):
        pass

    def __init__(self):
        super().__init__()
        if settings.BaseApp.enableAsyncHttp:
            self.addTimerProxy(settings.BaseApp.asyncHttpTickFrequency, AsyncHttp.run_frame,
                               settings.BaseApp.asyncHttpTickFrequency)

        if self.groupIndex == 1:
            KBEngine.createBaseLocally('Equalization', dict())
            Database.discover()
        self.checkEqualizationTimerID = self.addTimerProxy(0.1, self.checkEqualization, 0.1)

    def checkEqualization(self):
        if KBEngine.globalData.get("Equalization"):
            self.delTimerProxy(self.checkEqualizationTimerID)
            self.checkEqualizationTimerID = None
            Equalization.createBaseLocally()
