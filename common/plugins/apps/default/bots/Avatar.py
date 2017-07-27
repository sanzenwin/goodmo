# -*- coding: utf-8 -*-
import KBEngine
from kbe.log import DEBUG_MSG


class Avatar(KBEngine.Entity):
    pass


class PlayerAvatar(Avatar):
    def __init__(self):
        pass

    def onEnterSpace(self):
        """
        KBEngine method.
        这个entity进入了一个新的space
        """
        DEBUG_MSG("%s::onEnterSpace: %i" % (self.__class__.__name__, self.id))

        # 注意：由于PlayerAvatar是引擎底层强制由Avatar转换过来，__init__并不会再调用
        # 这里手动进行初始化一下
        self.__init__()

    def onLeaveSpace(self):
        """
        KBEngine method.
        这个entity将要离开当前space
        """
        DEBUG_MSG("%s::onLeaveSpace: %i" % (self.__class__.__name__, self.id))
