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

    def __init__(self):
        super().__init__()
        self.__queueRun = []
        self.__queueRunMark = False

    def addBots(self, name, amount, data):
        generator_list = Equalization[self.__class__.__name__].list()
        d = self.div(range(len(generator_list)), amount)
        for i, a in d.items():
            generator_list[i].addBotsInner(name, a, data)

    def addBotsInner(self, name, amount, data):
        self.__queueRun.append([name, amount, data])
        if not self.__queueRunMark:
            self.__queueRunMark = True
            self.runInNextFrame(self.__runQueue)

    def __runQueue(self):
        self.doRunQueue(self.perGenerateAmount)
        if self.__queueRun:
            self.runInNextFrame(self.__runQueue)
        else:
            self.__queueRunMark = False

    def doRunQueue(self, left):
        if left <= 0 or not self.__queueRun:
            return
        d = self.__queueRun[0]
        if d[1] >= self.perGenerateAmount:
            run_amount = self.perGenerateAmount
            d[1] -= run_amount
        else:
            run_amount = d[1]
            d[1] -= self.perGenerateAmount
        if d[1] <= 0:
            self.__queueRun.pop(0)
        robotManager.addBots(d[0], run_amount, d[2])
        self.doRunQueue(self.perGenerateAmount - run_amount)

    @staticmethod
    def div(s, total):
        length = len(s)
        e = total // length
        r = total % length
        return {x: (e + 1 if i < r else e) for i, x in enumerate(s) if (e + 1 if i < r else e) > 0}

    @property
    def perGenerateAmount(self):
        if not hasattr(self, "_perGenerateAmount"):
            generator_list = Equalization[self.__class__.__name__].list()
            setattr(self, "_perGenerateAmount", len(generator_list) * 2)
        return self._perGenerateAmount
