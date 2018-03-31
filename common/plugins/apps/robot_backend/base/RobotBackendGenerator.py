# -*- coding: utf-8 -*-
import KBEngine
from kbe.core import Equalization
from kbe.utils import TimerProxy
from kbe.protocol import Base, BaseMethod, Property, Client, ClientMethod, Type
from robot_backend_common import robotManager


class RobotBackendGenerator(KBEngine.Entity, TimerProxy):
    base = Base(
        addBots=BaseMethod(Type.UNICODE, Type.UINT32, Type.PYTHON),
        addBotsInner=BaseMethod(Type.UNICODE, Type.UINT32, Type.PYTHON)
    )

    def addBots(self, name, amount, data):
        generator_list = Equalization[self.__class__.__name__].list()
        d = self.div(range(len(generator_list)), amount)
        for i, a in d.items():
            generator_list[i].addBotsInner(name, a, data)

    def addBotsInner(self, name, amount, data):
        robotManager.addBots(name, amount, data)

    @staticmethod
    def div(s, total):
        length = len(s)
        e = total // length
        r = total % length
        return {x: (e + 1 if i < r else e) for i, x in enumerate(s)}
