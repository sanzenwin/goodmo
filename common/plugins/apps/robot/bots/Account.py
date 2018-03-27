# -*- coding: utf-8 -*-
import KBEngine


class Account(KBEngine.Entity):
    def __init__(self):
        KBEngine.Entity.__init__(self)
        self.base.reqAvatarList()

    def onReqAvatarList(self, infos):
        if infos:
            self.base.reqSelectAvatar(infos[0]["dbid"])
        else:
            self.base.reqCreateAvatar()

    def onCreateAvatarResult(self, info):
        self.base.reqSelectAvatar(info["dbid"])

    def onRemoveAvatar(self, dbid):
        pass
