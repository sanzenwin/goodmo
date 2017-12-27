import asyncio
import types
import weakref
import itertools
import pymongo
import KBEngine
import settings
from collections import OrderedDict
from common.dispatcher import receiver
from kbe.core import Mongodb
from kbe.signals import mongodb_completed
from kbe.log import ERROR_MSG
from kbe.xml import settings_kbengine
from plugins.conf.signals import plugins_completed


def robot(c):
    def attach(m):

        def proxy(self, *args):
            if m in dir(self.robot):
                getattr(self.robot, m)(*args)

        setattr(c, m, proxy)

    for n, f in c.__dict__.items():
        if isinstance(f, types.FunctionType):
            attach(n)
    return c


def factory(name):
    def wrapper(c):
        RobotManager.addType(name, c)
        return c

    return wrapper


class RobotManager:
    typeMap = {}

    def __init__(self):
        self.index = 0
        self.ic = OrderedDict()
        self.ii = {}

    @classmethod
    def addType(cls, name, c):
        cls.typeMap[name] = c

    def newId(self):
        index = self.index
        self.index += 1
        return index

    def curId(self):
        return self.index

    def start(self):
        self.addFactory()

    def checkType(self, c):
        return c in self.typeMap

    def getRobot(self):
        index = self.curId()
        it = None
        for i in reversed(self.ic):
            if it is None:
                it = i
            if i <= index:
                break
            it = i
        return self.ic[it]

    def addBots(self, c, count, data):
        last_id = next(reversed(self.ic), 0)
        self.ic[last_id + count] = (self.typeMap[c], data)
        t = min(1, settings.Robot.totalTime / (count / settings.Robot.tickCount))
        KBEngine.addBots(count, settings.Robot.tickCount, t)

    def addFactory(self):
        self.ic[1] = (RobotFactory, dict)
        KBEngine.addBots(1, 1, 0)


robotManager = RobotManager()


class Robot:
    stop = object()

    def __init__(self):
        self.index = 0
        self.data = None
        self.entity = None
        self.forever = {}

    def __getattr__(self, item):
        return getattr(self.entity, item)

    def init(self, entity, data):
        self.index = robotManager.newId()
        self.data = data
        self.entity = weakref.proxy(entity)
        self.onStart()

    def onStart(self):
        pass

    def getEntities(self):
        return {entity.id: entity for entity in
                itertools.chain(*[client.entities.values() for client in KBEngine.bots.values()])}

    def addTimerProxy(self, time, callback):
        return KBEngine.callback(time, callback)

    def delTimerProxy(self, timerID):
        KBEngine.cancelCallback(timerID)

    def runForever(self, offset, callback):
        def run():
            if self.forever.get(callback.__name__) is self.stop:
                del self.forever[callback.__name__]
            assert callback.__name__ not in self.forever, "duplicate callback %s" % callback.__name__
            self.forever[callback.__name__] = self.addTimerProxy(offset, proxy)

        def proxy():
            del self.forever[callback.__name__]
            callback()
            if self.forever.get(callback.__name__) is not self.stop:
                run()

        run()

    def killRun(self, callback):
        callback = callback if isinstance(callback, str) else callback.__name__
        timerID = self.forever.pop(callback, None)
        self.forever[callback] = self.stop
        if timerID is None:
            return False
        KBEngine.cancelCallback(timerID)
        return True


@factory("default")
class RobotDefault(Robot):
    def onStart(self):
        self.runForever(1, self.base.robDisconnect)


class RobotFactory(Robot):
    addBotsKey = settings_kbengine.bots.account_infos.account_name_prefix.value

    @classmethod
    def addBots(cls, key, c, count, data=None):
        if not robotManager.checkType(c):
            ERROR_MSG("RobotFactory::addBots:type error: %s" % c)
            return
        asyncio.async(pushAddBots_generation(key, c, count, data or dict()))

    def onStart(self):
        self.runForever(settings.Global.gameTimeInterval * 2, self.onCheckCommond)

    def onCheckCommond(self):
        def callback(data):
            if data is None:
                return
            c, count, d = data["type"], data["count"], data["data"]
            if not robotManager.checkType(c):
                return
            robotManager.addBots(c, count, d)

        global cache_factory
        if cache_factory:
            asyncio.async(popAddBots_generation()).add_done_callback(
                lambda future: callback(future.result()))


cache_factory = None


@asyncio.coroutine
def pushAddBots_generation(key, c, count, d=None):
    yield from cache_factory.insert(dict(key=key, type=c, count=count, data=d or dict()))


@asyncio.coroutine
def popAddBots_generation():
    data = yield from cache_factory.find_and_modify(dict(key=RobotFactory.addBotsKey),
                                                    sort={"$natural": pymongo.ASCENDING}, remove=True)
    return data


@receiver(mongodb_completed)
def init_robot(signal, sender):
    global cache_factory
    cache_factory = Mongodb.Robot.Factory
    if KBEngine.component == "bots":
        pass
        # RobotFactory.addBots("bot_", "holdem_Mtt", 10)
        # RobotFactory.addBots("bot_", "holdem_FreeTableMember", 1)
        # RobotFactory.addBots("bot_", "holdem_FreeTableMaster", 1)


@receiver(plugins_completed)
def discover(signal, sender):
    sender.load_all_module("robot_common.robots")
