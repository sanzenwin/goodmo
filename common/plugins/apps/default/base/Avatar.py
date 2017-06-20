# -*- coding: utf-8 -*-
import KBEngine
import settings
from common.utils import Event
from kbe.log import DEBUG_MSG, INFO_MSG, ERROR_MSG
from kbe.utils import TimerProxy
from interfaces.Object import Object
from kbe.protocol import Property, Client, ClientMethod, Type


class Avatar(KBEngine.Proxy, Object, TimerProxy, Event.Container):
    client = Client(
        onRetCode=ClientMethod(Type.RET_CODE),
        onLogOnAttempt=ClientMethod(Type.BOOL, Type.UNICODE)
    )

    databaseID = Property(Req=True)

    def __init__(self):
        super().__init__()
        self.accountEntity = None
        self.destroyTimerID = None
        self.isFirstLogin = True

    def isReqReady(self):
        if not self.isValid:
            return False
        if hasattr(self, "_reqReady"):
            return True
        if all((getattr(self, req, None) for req in self._reqReadyList)):
            setattr(self, "_reqReady", True)
            return True
        return False

    def onReqReady(self):
        self.onLogin()

    def onEntitiesEnabled(self):
        INFO_MSG("Avatar[%i] entities enable. mailbox:%s" % (self.id, self.client))
        if self.isReqReady():
            if self.isFirstLogin:
                self.onLogin()
                self.isFirstLogin = False
            else:
                self.onQuickLogin()
            self.onCommonLogin()

        if self.destroyTimerID is not None:
            self.delTimerProxy(self.destroyTimerID)

    def onClientDeath(self):
        def callback():
            self.destroyTimerID = None
            if self.client:
                return
            if self.isReqReady():
                self.onLogout()
        DEBUG_MSG("Avatar[%i]::onClientDeath." % self.id)
        self.destroyTimerID = self.addTimerProxy(settings.Avatar.delayDestroySeconds, callback)

    def destroy(self, deleteFromDB=False, writeToDB=True):
        if self.accountEntity:
            self.accountEntity.activeAvatar = None
            self.accountEntity.destroy()
            self.accountEntity = None
        super().destroy(deleteFromDB, writeToDB)
