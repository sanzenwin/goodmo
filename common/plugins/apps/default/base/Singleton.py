import KBEngine
from kbe.core import Singleton as Singleton_
from kbe.log import ERROR_MSG


class Singleton(KBEngine.Base):
    def __init__(self):
        super().__init__()
        if self.databaseID:
            self.onInit()
        else:
            self.writeToDB(self.onSaved)

    def onSaved(self, success, entity):
        if self.isDestroyed:
            ERROR_MSG("%s::__onSaved:(%i): i dead!" % (self.__class__.__name__, self.id))
            return
        self.onInit()

    def onInit(self):
        Singleton_.add(self)
        self.onSetup()

    def onDestroy(self):
        Singleton_.remove(self)

    def onSetup(self):
        pass
