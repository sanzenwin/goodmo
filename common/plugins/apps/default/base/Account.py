# -*- coding: utf-8 -*-
import KBEngine
import settings
import ret_code
from copy import deepcopy
from kbe.log import INFO_MSG, ERROR_MSG
from kbe.protocol import Property, Volatile, Type, Base, BaseMethod, BaseMethodExposed, Client, ClientMethod
from default.signals import avatar_newbie
from DEFAULT import TAvatarInfo


class Account(KBEngine.Proxy):
    base = Base(
        reqAvatarList=BaseMethodExposed(),
        reqCreateAvatar=BaseMethodExposed(),
        reqSelectAvatar=BaseMethodExposed(Type.DBID),
        reqRemoveAvatar=BaseMethodExposed(Type.DBID)
    )

    client = Client(
        onRetCode=ClientMethod(Type.RET_CODE(Type.UINT16)),
        onReqAvatarList=ClientMethod(Type.AVATAR_INFO.array),
        onCreateAvatarResult=ClientMethod(Type.AVATAR_INFO),
        onRemoveAvatar=ClientMethod(Type.DBID)
    )

    avatars = Property(
        Type=Type.AVATAR_INFO.array,
        Flags=Property.Flags.BASE,
        Persistent=Property.Persistent.true
    )

    lastSelectAvatar = Property(
        Type=Type.DBID,
        Flags=Property.Flags.BASE_AND_CLIENT,
        Persistent=Property.Persistent.true
    )

    activeAvatar = Property(
        Type=Type.ENTITYCALL,
        Flags=Property.Flags.BASE,
        Persistent=Property.Persistent.true
    )

    def onLogOnAttempt(self, ip, port, password):
        if self.isDestroyed:
            return KBEngine.LOG_ON_WAIT_FOR_DESTROY
        # 如果一个在线的账号被一个客户端登陆并且onLogOnAttempt返回允许
        # 那么会踢掉之前的客户端连接
        if self.activeAvatar and self.activeAvatar.client:
            # isSelf = self.activeAvatar.clientAddr == (ip, port)
            # self.activeAvatar.client.onLogOnAttempt(isSelf, "" if isSelf else ip)
            self.activeAvatar.giveClientTo(self)
        return KBEngine.LOG_ON_ACCEPT

    def onClientDeath(self):
        if not self.activeAvatar:
            self.destroy()

    def reqAvatarList(self):
        self.client.onReqAvatarList(self.avatars)

    def reqCreateAvatar(self):
        if len(self.avatars) >= settings.Account.avatarTotalLimit:
            self.client.onRetCode(ret_code.ACCOUNT_CREATE_AVATAR_TOP_LIMIT)
            return
        prefix = settings.Avatar.namePrefix
        newbieData = deepcopy(settings.Avatar.newbieData.dict)
        newbieData["name"] = prefix + str(len(self.avatars) + 1) + str(
            self.databaseID + settings.Avatar.nameIndexRadix)
        avatar_newbie.send(self, newbieData=newbieData)
        self.onAvatarPrevCreated(newbieData)
        avatar = KBEngine.createEntityLocally('Avatar', newbieData)
        if avatar:
            avatar.writeToDB(self.__onAvatarSaved)

    def reqRemoveAvatar(self, dbid):
        if not settings.Account.removeAvatarEnabled:
            self.client.onRetCode(ret_code.ACCOUNT_REMOVE_AVATAR_FAILED)
            return
        oldNum = len(self.avatars)
        self.avatars = [avatar for avatar in self.avatars if dbid == avatar.dbid]
        self.client.onRemoveAvatar(0 if oldNum == len(self.avatars) else dbid)

    def reqSelectAvatar(self, dbid):
        # 注意:使用giveClientTo的entity必须是当前baseapp上的entity
        if self.activeAvatar is None:
            for avatar in self.avatars:
                if avatar.dbid == dbid:
                    self.lastSelectAvatar = dbid
                    KBEngine.createEntityFromDBID("Avatar", dbid, self.__onAvatarLoaded)
                    break
            else:
                ERROR_MSG("Account[%i]::reqSelectAvatar: not found dbid(%i)" % (self.id, dbid))
        else:
            if self.client:
                self.activeAvatar.isReLogin = False
                self.giveClientTo(self.activeAvatar)

    def onAvatarPrevCreated(self, data):
        pass

    def onAvatarCreated(self, dbid):
        pass

    def onAvatarLoaded(self):
        pass

    def __onAvatarLoaded(self, baseRef, dbid, wasActive):
        if wasActive:
            ERROR_MSG("Account::__onAvatarLoaded:(%i): this character is in world now!" % self.id)
            return
        if baseRef is None:
            ERROR_MSG("Account::__onAvatarLoaded:(%i): the character you wanted to created is not exist!" % self.id)
            return
        avatar = KBEngine.entities.get(baseRef.id)
        if avatar is None:
            ERROR_MSG("Account::__onAvatarLoaded:(%i): when character was created, it died as well!" % self.id)
            return
        if self.isDestroyed:
            ERROR_MSG("Account::__onAvatarLoaded:(%i): i dead, will the destroy of Avatar!" % self.id)
            avatar.destroy()
            return
        avatar.accountEntity = self
        self.activeAvatar = avatar
        if self.client:
            self.giveClientTo(avatar)
        self.onAvatarLoaded()

    def __onAvatarSaved(self, success, avatar):
        INFO_MSG('Account::_onAvatarSaved:(%i) create avatar state: %i, %i' % (
            self.id, success, avatar.databaseID))
        # 如果此时账号已经销毁， 角色已经无法被记录则我们清除这个角色
        if self.isDestroyed:
            ERROR_MSG("Account::__onAvatarSaved:(%i): i dead!" % self.id)
            if avatar:
                avatar.destroy(True)
            return
        avatarinfo = TAvatarInfo()
        if success:
            avatarinfo.dbid = avatar.databaseID
            avatarinfo.name = avatar.name
            self.avatars.append(avatarinfo)
            self.writeToDB()
            avatar.destroy()
            if self.client:
                self.client.onCreateAvatarResult(avatarinfo)
            self.onAvatarCreated(avatarinfo.dbid)
        else:
            ERROR_MSG("Account::__onAvatarSaved:(%i): failed!" % self.id)
