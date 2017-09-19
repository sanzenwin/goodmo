# -*- coding: utf-8 -*-
import KBEngine
import settings
from common.utils import server_time, Event
from kbe.utils import TimerProxy
from interfaces.Ref import Ref
from default.interfaces.RunObject import RunObject
from kbe.protocol import Property, Client, ClientMethod, Type
from default.signals import avatar_created, avatar_common_login, avatar_quick_login, avatar_login


class Avatar(KBEngine.Proxy, Ref, RunObject, TimerProxy, Event.Container):
    client = Client(
        onEvent=ClientMethod(Type.EVENT),
        onRetCode=ClientMethod(Type.RET_CODE),
        onServerTime=ClientMethod(Type.TIME_STAMP),
        # onLogOnAttempt=ClientMethod(Type.BOOL, Type.UNICODE),
    )

    databaseID = Property(Req=True)

    def __init__(self):
        super().__init__()
        self.accountEntity = None
        self.destroyTimerID = None
        self.isFirstLogin = True

    def onCreatedAndCompleted(self):
        if self.isReqReady():
            self.onReqReady()
            avatar_created.send(self)

    def isReqReady(self):
        if self.isDestroyed:
            return False
        if hasattr(self, "_reqReady"):
            return True
        if all(getattr(self, req, None) for req in self._reqReadyList):
            setattr(self, "_reqReady", True)
            return True
        return False

    def onReqReady(self):
        if self.isFirstLogin:
            avatar_login.send(self)
            self.onLogin()
            self.isFirstLogin = False
        else:
            avatar_quick_login.send(self)
            self.onQuickLogin()
        avatar_common_login.send(self)
        self.onCommonLogin()

    def onEntitiesEnabled(self):
        self.client.onServerTime(server_time.stamp())
        if self.isReqReady():
            self.onReqReady()
        if self.destroyTimerID is not None:
            self.delTimerProxy(self.destroyTimerID)

    def onClientDeath(self):
        def callback():
            self.destroyTimerID = None
            if self.client:
                return
            if self.isReqReady():
                self.onLogout()
        self.destroyTimerID = self.addTimerProxy(settings.Avatar.delayDestroySeconds, callback)

    def destroy(self, deleteFromDB=False, writeToDB=True):
        if self.accountEntity:
            self.accountEntity.activeAvatar = None
            self.accountEntity.destroy()
            self.accountEntity = None
        super().destroy(deleteFromDB, writeToDB)

    @property
    def pk(self):
        return self.accountEntity.__ACCOUNT_NAME__

    @property
    def ip(self):
        return ".".join(reversed(list(map(str, self.clientAddr[0].to_bytes(4, 'big')))))
