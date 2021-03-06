# -*- coding: utf-8 -*-
import KBEngine
from common.utils import Event
from kbe.core import Equalization
from kbe.protocol import Property, Volatile, Type, Base, BaseMethod, BaseMethodExposed, Client, ClientMethod


class Guarantee:
    guaranteeID = Property(
        Type=Type.DBID,
        Flags=Property.Flags.BASE_AND_CLIENT,
        Persistent=Property.Persistent.true,
        Req=True
    )

    def __init__(self):
        super().__init__()
        if self.databaseID and not self.guaranteeID:
            self.createGuarantee()

    @Event.method
    def onGuaranteeCreated(self):
        self.onCreatedAndCompleted()

    def createGuarantee(self):
        def callback(success, guarantee):
            def callback(success, baseRef):
                if success:
                    guarantee.destroy(False, False)
                    self.onGuaranteeCreated()
                else:
                    guarantee.destroy(True)
                    self.destroy()

            if self.isDestroyed:
                if guarantee:
                    guarantee.destroy(True)
            elif success:
                self.guaranteeID = guarantee.databaseID
                self.writeToDB(callback)
            else:
                self.destroy()
        guarantee = KBEngine.createEntityLocally('Guarantee', {})
        if guarantee:
            guarantee.writeToDB(callback)
        else:
            self.destroy()

    def onLogin(self):
        Equalization.PlayerManager(self.guaranteeID).run(self.guaranteeID, [])
