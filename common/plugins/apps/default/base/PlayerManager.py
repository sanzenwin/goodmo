# -*- coding: utf-8 -*-
import KBEngine
from kbe.log import DEBUG_MSG, INFO_MSG, ERROR_MSG
from kbe.protocol import Type, Base, BaseMethod


class PlayerManager(KBEngine.Base):
    base = Base(
        addPlayer=BaseMethod(Type.DBID, Type.MAILBOX),
        removePlayer=BaseMethod(Type.DBID),
        run=BaseMethod(Type.DBID, Type.CALL.array),
        runOnline=BaseMethod(Type.DBID, Type.CALL.array),
        sendEvent=BaseMethod(Type.DBID, Type.EVENT)
    )

    errorDeepMax = 3

    def __init__(self):
        super().__init__()
        self.guarantees = {}
        self.products = {}
        self.players = {}

    def addPlayer(self, guaranteeID, player):
        self.players[guaranteeID] = player

    def removePlayer(self, guaranteeID):
        player = self.players.pop(guaranteeID)
        player.release()

    def addGuarantee(self, guaranteeID, guarantee):
        self.guarantees[guaranteeID] = guarantee

    def removeGuarantee(self, guaranteeID):
        self.guarantees.pop(guaranteeID)

    def run(self, guaranteeID, callList):
        product = self.products.get(guaranteeID)
        if product is not None:
            product.extend(callList)
            return
        player = self.players.get(guaranteeID)
        if player:
            player.run(callList)
        else:
            guarantee = self.guarantees.get(guaranteeID)
            if guarantee:
                guarantee.run(None, callList)
            else:
                self.products[guaranteeID] = callList
                self.loadGuarantee(guaranteeID)

    def runOnline(self, guaranteeID, callList):
        player = self.players.get(guaranteeID)
        if player:
            player.run(callList)

    def sendEvent(self, guaranteeID, event):
        player = self.players.get(guaranteeID)
        if player and player.client:
            player.client.onEvent(event.client)

    def loadGuarantee(self, guaranteeID, errorDeep=0):
        def callback(baseRef, dbid, wasActive):
            try:
                if wasActive:
                    raise RunException(
                        "PlayerManager::callback:(%i): this guarantee is in world now! %s, %s, %s, %s" % (
                            guaranteeID, self.id, baseRef, dbid, wasActive))
                if baseRef is None:
                    raise RunException(
                        "PlayerManager::callback:(%i): the guarantee you wanted to created is not exist! %s, %s, %s, %s" % (
                            guaranteeID, self.id, baseRef, dbid, wasActive))
                guarantee = KBEngine.entities.get(baseRef.id)
                if guarantee is None:
                    raise RunException(
                        "PlayerManager::callback:(%i): when guarantee was created, it died as well! %s, %s, %s, %s" % (
                            guaranteeID, self.id, baseRef, dbid, wasActive))
                if self.isDestroyed:
                    raise RunException("PlayerManager::callback:(%i): i dead! %s, %s, %s, %s" % (
                        guaranteeID, self.id, baseRef, dbid, wasActive))
            except RunException as e:
                ERROR_MSG(e.args[0])
                if errorDeep < self.errorDeepMax:
                    self.loadGuarantee(guaranteeID, errorDeep + 1)
                else:
                    ERROR_MSG(
                        "PlayerManager::loadGuarantee:(%i): load failed! %s, %s, %s, %s" % (
                            guaranteeID, self.id, baseRef, dbid, wasActive))
            else:
                guarantee.run(self.players.get(guarantee.databaseID), self.products.pop(guarantee.databaseID))

        KBEngine.createBaseFromDBID('Guarantee', guaranteeID, callback)


class RunException(Exception):
    pass
