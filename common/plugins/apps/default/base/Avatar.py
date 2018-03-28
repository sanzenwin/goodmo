# -*- coding: utf-8 -*-
import KBEngine
import settings
from common.utils import server_time, Event, Bytes, PublicAttrMap
from kbe.utils import TimerProxy
from interfaces.Ref import Ref
from default.interfaces.RunObject import RunObject
from kbe.protocol import Base, BaseMethodExposed, Property, Client, ClientMethod, Type
from default.signals import avatar_created, avatar_common_login, avatar_common_login_post, avatar_quick_login, \
    avatar_login, avatar_logout, avatar_modify, avatar_modify_multi, avatar_modify_common

TAvatar = KBEngine.find_user_type("TAvatar")


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
        self.publicAttrMap = PublicAttrMap()

    def onCreatedAndCompleted(self):
        avatar_created.send(self)
        if self.isReqReady():
            self.onReqReady()

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
        self.onCommonLogin()
        avatar_common_login.send(self)
        if self.isFirstLogin:
            avatar_login.send(self)
            self.onLogin()
            self.isFirstLogin = False
        else:
            avatar_quick_login.send(self)
            self.onQuickLogin()
        avatar_common_login_post.send(self)

    def onClientEnabled(self):
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
            self.logout()

        self.onLogoff()
        self.destroyTimerID = self.addTimerProxy(settings.Avatar.delayDestroySeconds, callback)

    def onModifyAttr(self, key, value, old):
        avatar_modify.send(self, key=key, value=value, old=old)
        avatar_modify_common.send(self, key=key, value=value, old=old)

    def onModifyAttrMulti(self, data, old):
        avatar_modify_multi.send(self, data=data, old=old)
        for key, value in data.items():
            avatar_modify_common.send(self, key=key, value=value, old=old[key])

    def logout(self):
        if self.isReqReady():
            avatar_logout.send(self)
            self.onLogout()

    def destroy(self, deleteFromDB=False, writeToDB=True):
        if self.accountEntity:
            self.accountEntity.activeAvatar = None
            self.accountEntity.destroy()
            self.accountEntity = None
        self.clearTimerProxy()
        super().destroy(deleteFromDB, writeToDB)

    @property
    def pk(self):
        return self.accountEntity.__ACCOUNT_NAME__

    @property
    def ip(self):
        return ".".join(reversed(list(map(str, self.clientAddr[0].to_bytes(4, 'big')))))

    @property
    def avatar(self):
        return TAvatar(self)
