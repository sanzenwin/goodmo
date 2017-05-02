# -*- coding: utf-8 -*-
import os
import KBEngine
from common.asyncHttp import AsyncHttp
from kbe.utils import TimerProxy
from kbe.core import Equalization


class BaseApp(KBEngine.Base, TimerProxy):
    @classmethod
    def onReadyForLogin(cls):
        return 1.0 if Equalization.isCompleted() else 0.0

    @classmethod
    def createBaseLocally(cls):
        KBEngine.createBaseLocally('BaseApp', dict(groupIndex=int(os.getenv("KBE_BOOTIDX_GROUP")),
                                                   globalIndex=int(os.getenv("KBE_BOOTIDX_GLOBAL"))))

    def __init__(self):
        super().__init__()
        import settings
        if settings.BaseApp.enableAsyncHttp:
            self.addTimerProxy(settings.BaseApp.asyncHttpTickFrequency, AsyncHttp.run_frame,
                               settings.BaseApp.asyncHttpTickFrequency)

        if self.groupIndex == 1:
            KBEngine.createBaseLocally('Equalization', dict())
        self.checkEqualizationTimerID = self.addTimerProxy(0.1, self.checkEqualization, 0.1)

    def checkEqualization(self):
        if KBEngine.globalData.get("Equalization"):
            self.delTimerProxy(self.checkEqualizationTimerID)
            self.checkEqualizationTimerID = None
            Equalization.createBaseLocally()
