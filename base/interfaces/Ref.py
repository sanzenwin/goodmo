# -*- coding: utf-8 -*-
from kbe.protocol import Base, BaseMethod


class Ref:
    base = Base(
        release=BaseMethod()
    )

    def __init__(self):
        super().__init__()
        self.__lifeCount = 0

    def addRef(self, count=1):
        self.__lifeCount += count

    def release(self):
        self.__lifeCount -= 1
        if self.__lifeCount <= 0:
            self.destroy()
        self.onRelease()

    def onRelease(self):
        pass

    @property
    def lifeCount(self):
        return self.__lifeCount

    @property
    def object(self):
        self.addRef()
        return self
