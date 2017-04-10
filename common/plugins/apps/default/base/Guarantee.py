# -*- coding: utf-8 -*-
import KBEngine
import settings
from kbe.utils import TimerProxy
from kbe.core import Equalization
from kbe.protocol import Property, Type


class Guarantee(KBEngine.Base, TimerProxy):
    callList = Property(
        Type=Type.CALL.array,
        Flags=Property.Flags.BASE,
        Persistent=Property.Persistent.true
    )

    def __init__(self):
        super().__init__()
        self.destroyTimerID = None
        if self.databaseID:
            self.onInit()
            self.resetDestroy()
        self.normal = bool(self.databaseID)

    def timerDestroy(self):
        self.destroyTimerID = None
        self.destroy()

    def onDestroy(self):
        if self.normal:
            Equalization.PlayerManager(self.databaseID).removeGuarantee(self.databaseID)

    def onInit(self):
        Equalization.PlayerManager(self.databaseID).addGuarantee(self.databaseID, self)

    def resetDestroy(self):
        if self.destroyTimerID is not None:
            self.delTimerProxy(self.destroyTimerID)
        self.destroyTimerID = self.addTimerProxy(settings.Guarantee.delayDestroySeconds, self.timerDestroy)

    def run(self, entity, callList):
        if callList:
            self.resetDestroy()
        self.callList.extend(callList)
        if entity and self.callList:
            callList = self.callList
            self.callList = []
            entity.run(callList)
