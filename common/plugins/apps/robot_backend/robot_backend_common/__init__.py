import weakref
import KBEngine
from functools import partial
from kbe.xml import settings_kbengine


def factory(name):
    def wrapper(c):
        robotManager.addType(name, c)
        return c

    return wrapper


class RobotManager:
    def __init__(self):
        self.typeMap = {}
        self.robots = {}

    def addType(self, name, c):
        self.typeMap[name] = c

    def checkType(self, c):
        return c in self.typeMap

    def addBots(self, name, count, data=None):
        for _ in range(count):
            account = KBEngine.createEntityLocally(settings_kbengine.dbmgr.account_system.accountEntityScriptType.value,
                                                   dict(robotBackendName=name,
                                                        robotBackendData=data))
            self._completeAccount(account)

    def _completeAccount(self, account):
        def onAvatarPrevCreated(data):
            data["robotBackendMark"] = True

        def onAvatarCreated(dbid):
            account.reqSelectAvatar(dbid)

        def onAvatarLoaded():
            account.activeAvatar.initRobotBackend(account.robotBackendName, account.robotBackendData)

        account.onAvatarPrevCreated = onAvatarPrevCreated
        account.onAvatarCreated = onAvatarCreated
        account.onAvatarLoaded = onAvatarLoaded
        account.__ACCOUNT_NAME__ = "0"
        account.reqCreateAvatar()


robotManager = RobotManager()
del RobotManager


class Robot:
    class Empty:
        def __getitem__(self, item):
            return self.proxy

        def __getattr__(self, item):
            return self.proxy

        @staticmethod
        def proxy(*args, **kwargs):
            pass

    class Entity:
        def __init__(self, robot):
            super().__init__()
            self.robot = robot
            self.method = ""

        def __getattr__(self, item):
            self.method = item
            return self.proxy

        def proxy(self, *args):
            pass

    class Base(Entity):
        def proxy(self, *args):
            entity = self.robot.entity()
            if entity:
                self.robot.call(getattr(entity, self.method), args)

    class Cell(Entity):
        def proxy(self, *args):
            entity = self.robot.entity()
            if entity:
                self.robot.call(getattr(getattr(entity, "cell"), self.method), args)

    def __init__(self):
        self.entity = None
        self.data = None
        self.__queueCall = []
        self.__queueRunMark = False

    def __getattr__(self, item):
        entity = self.entity()
        if entity is None:
            return self.Empty()
        return getattr(entity, item)

    def init(self, entity, data):
        self.entity = entity
        self.data = data
        self.onLogin()

    @property
    def base(self):
        return self.Base(self)

    @property
    def cell(self):
        return self.Cell(self)

    def isValid(self):
        return bool(self.entity())

    def from_user_type_data(self, data, user_type):
        return data

    def to_user_type_data(self, data):
        return data

    def onLogin(self):
        pass

    def foreverRun(self, offset, callback):
        self.addTimerProxy(offset, callback, offset)

    def killForeverRun(self, callback):
        tid = self.getTimerProxy(callback)
        if tid:
            self.delTimerProxy(tid)
            return True
        return False

    def getForeverRun(self, callback):
        return self.getTimerProxy(callback)

    def call(self, proxy, args):
        entity = self.entity()
        if entity:
            self.__queueCall.append((proxy, args))
            if not self.__queueRunMark:
                self.__queueRunMark = True
                entity.runInNextFrame(self.__callQueue)
        else:
            self.__queueCall = []

    def __callQueue(self):
        self.__queueRunMark = False
        for proxy, args in self.__queueCall:
            proxy(*args)
        self.__queueCall = []


class RobotBackendProxy:
    def __init__(self, entity):
        self.__queueCall = []
        self.__queueRunMark = False
        self.robotBackendName = entity.robotBackendName
        self.robotBackendData = entity.robotBackendData
        self.entity = weakref.ref(entity)
        self.robot = robotManager.typeMap[self.robotBackendName]()
        self.robot.init(self.entity, self.robotBackendData)

    def reset(self, name, data):
        self.robotBackendName = name
        self.robotBackendData = data
        self.robot = robotManager.typeMap[self.robotBackendName]()
        self.robot.init(self.entity, self.robotBackendData)

    def call(self, method, *args):
        proxy = getattr(self.robot, method, None)
        if proxy:
            entity = self.entity()
            if entity:
                self.__queueCall.append((proxy, args))
                if not self.__queueRunMark:
                    self.__queueRunMark = True
                    entity.runInNextFrame(self.__callQueue)
            else:
                self.__queueCall = []

    def __callQueue(self):
        self.__queueRunMark = False
        for proxy, args in self.__queueCall:
            proxy(*args)
        self.__queueCall = []


class AvatarClientProxy:
    def __init__(self, entity):
        self.entity = entity

    def __getattr__(self, item):
        return getattr(self.entity, "ClientProxy__%s" % item)


@factory("default")
class RobotDefault(Robot):
    def onLogin(self):
        self.foreverRun(1, self.base.robDisconnect)
