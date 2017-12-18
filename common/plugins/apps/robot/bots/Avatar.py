# -*- coding: utf-8 -*-
from default.bots.Avatar import Avatar as Avatar_, PlayerAvatar as PlayerAvatar_
from robot_common import robotManager


class Avatar(Avatar_):
    def __init__(self):
        super().__init__()
        rc, data = robotManager.getRobot()
        self.robot = rc()
        self.robot.init(self, data)


class PlayerAvatar(PlayerAvatar_):
    pass
