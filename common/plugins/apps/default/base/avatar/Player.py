# -*- coding: utf-8 -*-
from common.utils import Event
from kbe.core import Equalization


@Event.interface
class Player(object):
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

    def onLogout(self):
        Equalization.PlayerManager(self.guaranteeID).removePlayer(self.guaranteeID)

    def onCreated(self):
        pass
