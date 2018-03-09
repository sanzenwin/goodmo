# -*- coding: utf-8 -*-
from kbe.xml import settings_kbengine
from default.bots.Avatar import Avatar as Avatar_, PlayerAvatar as PlayerAvatar_
from robot_common import robotManager


class Avatar(Avatar_):
    def __init__(self):
        super().__init__()
        rc, data = robotManager.getRobot()
        self.robot = rc()
        self.robot.init(self, data)
        self.robot.base.robAuth(settings_kbengine.bots.loginAuth.value)

    def onRobAuth(self):
        self.robot.onLogin()


class PlayerAvatar(PlayerAvatar_):
    pass
