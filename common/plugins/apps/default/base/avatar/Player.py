# -*- coding: utf-8 -*-
from common.utils import Event
from kbe.core import Equalization


@Event.interface
class Player:
    isValid = False

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
        self.isValid = True

    def onLogout(self):
        self.isValid = False
        Equalization.PlayerManager(self.guaranteeID).removePlayer(self.guaranteeID)
