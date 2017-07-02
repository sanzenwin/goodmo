# -*- coding: utf-8 -*-
from common.utils import Event
from kbe.core import Equalization


@Event.interface
class Player:
    logOff = False

    def onClientDeath(self):
        pass

    def onReqReady(self):
        pass

    def onCommonLogin(self):
        pass

    def onQuickLogin(self):
        pass

    def onLogin(self):
        Equalization.PlayerManager(self.guaranteeID).addPlayer(self.guaranteeID, self.object)
        self.logOff = False

    def onLogout(self):
        self.logOff = True
        if self.lifeCount <= 1:
            Equalization.PlayerManager(self.guaranteeID).removePlayer(self.guaranteeID)

    def onRelease(self):
        if self.logOff and self.lifeCount == 1:
            Equalization.PlayerManager(self.guaranteeID).removePlayer(self.guaranteeID)
