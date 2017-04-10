# -*- coding: utf-8 -*-
import KBEngine
from kbe.log import DEBUG_MSG
from kbe import status_code


class Account(KBEngine.Entity):
    def __init__(self):
        KBEngine.Entity.__init__(self)
        DEBUG_MSG("Account::__init__:%s." % (self.__dict__))
        self.base.reqAvatarList()

    def onReqAvatarList(self, infos):
        """
        defined method.
        """

        DEBUG_MSG("Account:onReqAvatarList::%s" % (list(infos)))
        self.base.reqCreateAvatar()

    def onCreateAvatarResult(self, retcode, info):
        """
        defined method.
        """
        DEBUG_MSG("Account:onCreateAvatarResult::%s, retcode=%i" % (dict(info), retcode))
        if retcode == status_code.RESULT_CREATE_AVATAR_SUCCESS:
            self.base.reqSelectAvatar(info["dbid"])

    def onRemoveAvatar(self, dbid):
        """
        defined method.
        """
        DEBUG_MSG("Account:onRemoveAvatar:: dbid=%i" % (dbid))
