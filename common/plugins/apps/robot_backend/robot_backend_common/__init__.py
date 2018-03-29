import weakref
import KBEngine
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

    def __init__(self):
        self.entity = None
        self.data = None

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
        return self.entity() or self.Empty()

    @property
    def cell(self):
        entity = self.entity()
        if entity:
            return entity.cell
        return self.Empty()

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


class RobotBackendProxy:
    def __init__(self, entity):
        self.robotBackendName = entity.robotBackendName
        self.robotBackendData = entity.robotBackendData
        self.entity = weakref.ref(entity)
        self.robot = robotManager.typeMap[self.robotBackendName]()
        self.robot.init(self.entity, self.robotBackendData)

    def __getattr__(self, item):
        return getattr(self.robot, item)

    def reset(self, name, data):
        self.robotBackendName = name
        self.robotBackendData = data
        self.robot = robotManager.typeMap[self.robotBackendName]()
        self.robot.init(self.entity, self.robotBackendData)


class AvatarClientProxy:
    def __init__(self, entity):
        self.entity = entity

    def __getattr__(self, item):
        return getattr(self.entity, "ClientProxy__%s" % item)


@factory("default")
class RobotDefault(Robot):
    def onLogin(self):
        self.foreverRun(1, self.base.robDisconnect)
