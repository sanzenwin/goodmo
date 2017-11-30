# -*- coding: utf-8 -*-
from kbe.protocol import Type, Base, BaseMethod


class Ref:
    base = Base(
        delete=BaseMethod(),
        release=BaseMethod(),
        releases=BaseMethod(Type.UINT8),
    )

    def __init__(self):
        super().__init__()
        self.__del = False
        self.__lifeCount = 0

    def addRef(self, count=1):
        self.__lifeCount += count

    def releases(self, count=1):
        self.__lifeCount -= count
        if self.__lifeCount <= 0:
            self.destroy(self.__del)
        self.onRelease()

    def release(self):
        self.releases(1)

    def onRelease(self):
        pass

    def delete(self):
        self.__del = True
        self.release()

    @property
    def deleted(self):
        return self.__del

    @property
    def lifeCount(self):
        return self.__lifeCount

    @property
    def object(self):
        self.addRef()
        return self

    def objects(self, count):
        self.addRef(count)
        return self
