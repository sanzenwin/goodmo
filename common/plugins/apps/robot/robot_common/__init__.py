import re
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
from DEFAULT import TEvent


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


def factory(name, controller=""):
    def wrapper(c):
        c.name = name
        c.controller = controller
        robotManager.addType(name, c)
        return c

    return wrapper


class RobotManager:
    def __init__(self):
        self.index = 0
        self.typeMap = {}
        self.ic = OrderedDict()
        self.ii = {}

    def addType(self, name, c):
        self.typeMap[name] = c

    def getType(self, name):
        return self.typeMap[name]

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
del RobotManager


class Robot:
    stop = object()

    class Empty:
        def __getitem__(self, item):
            return self.proxy

        def __getattr__(self, item):
            return self.proxy

        @staticmethod
        def proxy(*args, **kwargs):
            pass

    class Entity:
        app = ""

        def __init__(self, entity):
            super().__init__()
            self.entity = entity
            self.method = ""

        def __getattr__(self, item):
            self.method = item
            return self.proxy

        def proxy(self, *args):
            if self.entity:
                entity_call = getattr(self.entity, self.app)
                if re.match("rob[A-Z]", self.method):
                    entity_call.reqRobProtocol([self.method] + list(args))
                else:
                    getattr(entity_call, self.method)(*args)

    class Base(Entity):
        app = "base"

    class Cell(Entity):
        app = "cell"

    name = ""
    controller = ""

    def __init__(self):
        self.index = 0
        self.data = None
        self.entity = None
        self.__forever__ = {}
        self.__timer__ = {}

    def __getattr__(self, item):
        entity = self.entity()
        if entity is None:
            return self.Empty()
        return getattr(entity, item)

    @property
    def base(self):
        return self.Base(self.entity())

    @property
    def cell(self):
        return self.Cell(self.entity())

    def isValid(self):
        return bool(self.entity())

    def init(self, entity, data):
        self.index = robotManager.newId()
        self.data = data
        self.entity = weakref.ref(entity)

    def from_user_type_data(self, data, user_type=None):
        return user_type().createFromRecursionDict(data)

    def to_user_type_data(self, data):
        return data.asDict()

    def onRobEvent(self, event):
        event = self.from_user_type_data(event, TEvent)
        action, args = event.func, event.args
        action_method = getattr(self, 'rob_event__' + action, None)
        if action_method is not None:
            action_method(*args)

    def rob_event__auth(self):
        self.onLogin()

    def rob_event__control(self, *args):
        pass

    def onLogin(self):
        pass

    def getEntities(self):
        return {entity.id: entity for entity in
                itertools.chain(*[client.entities.values() for client in KBEngine.bots.values()])}

    def addTimerProxy(self, time, callback):
        def proxy():
            callback()
            del self.__timer__[timerID]

        timerID = KBEngine.callback(time, proxy)
        self.__timer__[timerID] = callback
        return timerID

    def delTimerProxy(self, timerID):
        self.__timer__.pop(timerID, None)
        KBEngine.cancelCallback(timerID)

    def getTimerProxy(self, callback):
        return next((tid for tid, call in self.__timer__.items() if call == callback), None)

    def foreverRun(self, offset, callback):
        def run():
            if self.__forever__.get(callback.__name__) is self.stop:
                del self.__forever__[callback.__name__]
            assert callback.__name__ not in self.__forever__, "duplicate callback %s" % callback.__name__
            self.__forever__[callback.__name__] = KBEngine.callback(offset, proxy)

        def proxy():
            del self.__forever__[callback.__name__]
            callback()
            if self.__forever__.get(callback.__name__) is not self.stop:
                run()

        run()

    def killForeverRun(self, callback):
        callback = callback if isinstance(callback, str) else callback.__name__
        timerID = self.__forever__.pop(callback, None)
        self.__forever__[callback] = self.stop
        if timerID is None:
            return False
        KBEngine.cancelCallback(timerID)
        return True

    def getForeverRun(self, callback):
        return self.__forever__.get(callback.__name__)


@factory("default")
class RobotDefault(Robot):
    def onLogin(self):
        self.foreverRun(1, self.base.robDisconnect)


@factory("factory")
class RobotFactory(Robot):
    addBotsKey = settings_kbengine.bots.account_infos.account_name_prefix.value

    @classmethod
    def addBots(cls, key, c, count, data=None):
        if not robotManager.checkType(c):
            ERROR_MSG("RobotFactory::addBots:type error: %s" % c)
            return
        asyncio.async(pushAddBots_generation(key, c, count, data or dict()))

    def onLogin(self):
        self.foreverRun(settings.Global.gameTimeInterval * 2, self.onCheckCommond)

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


def createRobots(data):
    RobotFactory.addBots(data["type"], data["name"], data["amount"])


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


@receiver(plugins_completed)
def discover(signal, sender):
    sender.load_all_module("robot_common.robots")
