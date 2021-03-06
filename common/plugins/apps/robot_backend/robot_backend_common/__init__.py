import weakref
import KBEngine
from functools import partial
from kbe.xml import settings_kbengine
from kbe.log import ERROR_MSG
from DEFAULT import TEvent


def factory(name, controller=""):
    def wrapper(c):
        c.name = name
        c.controller = controller
        robotManager.addType(name, c)
        return c

    return wrapper


class RobotManager:
    def __init__(self):
        self.typeMap = {}
        self.robots = {}

    def addType(self, name, c):
        self.typeMap[name] = c

    def getType(self, name):
        return self.typeMap[name]

    def checkType(self, c):
        return c in self.typeMap

    def addBots(self, dbidList, name, data):
        for dbid in dbidList:
            KBEngine.createEntityFromDBID(settings_kbengine.dbmgr.account_system.accountEntityScriptType.value, dbid,
                                          partial(self.__onLoadAccount, name, data))

    def __onLoadAccount(self, name, data, baseRef, dbid, wasActive):
        def onAvatarLoaded():
            account.activeAvatar.initRobotBackend(name, data)
            account.activeAvatar.onReqReady()

        if wasActive:
            ERROR_MSG("%s::__onLoadAccount:(%s): this account is in world now!" % (self.__class__.__name__, name))
            return
        if baseRef is None:
            ERROR_MSG("%s::__onLoadAccount:(%s): the account you wanted to created is not exist!" % (
                self.__class__.__name__, name))
            return
        account = KBEngine.entities.get(baseRef.id)
        if account is None:
            ERROR_MSG("%s::__onLoadAccount:(%s): when account was created, it died as well!" % (
                self.__class__.__name__, name))
            return
        if not account.lastSelectAvatar:
            ERROR_MSG("%s::__onLoadAccount:(%s): this account(%d) has no character!" % (
                self.__class__.__name__, name, account.databaseID))
            return
        account.onAvatarLoaded = onAvatarLoaded
        account.reqSelectAvatar(account.lastSelectAvatar)

    def createBots(self, count, name, data=None):
        for _ in range(count):
            account = KBEngine.createEntityLocally(settings_kbengine.dbmgr.account_system.accountEntityScriptType.value,
                                                   dict(robotBackendName=name, robotBackendData=data))
            self.__onCompleteAccount(account)

    def __onCompleteAccount(self, account):
        def onAvatarPrevCreated(data):
            data["robotMark"] = True

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

    @property
    def base(self):
        return self.Base(self)

    @property
    def cell(self):
        return self.Cell(self)

    def isValid(self):
        return bool(self.entity())

    def from_user_type_data(self, data, user_type=None):
        return data

    def to_user_type_data(self, data):
        return data

    def onRobEvent(self, event):
        event = self.from_user_type_data(event, TEvent)
        action, args = event.func, event.args
        action_method = getattr(self, 'rob_event__' + action, None)
        if action_method is not None:
            action_method(*args)

    def rob_event__control(self, *args):
        method, args = args[0], args[1:]
        action_method = getattr(self, 'control__' + method, None)
        if action_method is not None:
            action_method(*args)

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
        self.robotBackendName = entity.robotName
        self.robotBackendData = entity.robotData
        self.entity = weakref.ref(entity)
        self.robot = robotManager.typeMap[self.robotBackendName]()
        self.robot.init(self.entity, self.robotBackendData)

    def reset(self, name, data):
        self.entity().clearTimerProxy()
        self.__queueCall = []
        self.__queueRunMark = False
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


@factory("controller")
class RobotController(RobotDefault):
    def onLogin(self):
        self.base.robController()
