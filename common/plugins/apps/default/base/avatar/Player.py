# -*- coding: utf-8 -*-
from common.utils import Event
from kbe.core import Equalization


@Event.interface
class Player:
    needRemove = True

    def onClientDeath(self):
        pass

    def onReqReady(self):
        pass

    def onCommonLogin(self):
        self.needRemove = False
        if self.lifeCount == 0:
            Equalization.PlayerManager(self.guaranteeID).addPlayer(self.guaranteeID, self.object)

    def onQuickLogin(self):
        pass

    def onLogin(self):
        pass

    def onLogout(self):
        self.needRemove = True
        if self.lifeCount == 1:
            Equalization.PlayerManager(self.guaranteeID).removePlayer(self.guaranteeID)

    def onRelease(self):
        if self.needRemove and self.lifeCount == 1:
            Equalization.PlayerManager(self.guaranteeID).removePlayer(self.guaranteeID)
