import re
from common.utils import Event
from kbe.core import Equalization
from kbe.protocol import Type, Property, Client, ClientMethod, Base, BaseMethod, BaseMethodExposed
from kbe.xml import settings_kbengine
from robot_common import robotManager
from robot.signals import robot_login
from CORE import python_server
from DEFAULT import TEvent


class Robot:
    base = Base(
        reqRobProtocol=BaseMethodExposed(Type.PYTHON),
        robExecute=BaseMethod(Type.PYTHON),
        robControl=BaseMethod(Type.PYTHON)
    )

    client = Client(
        onRobEvent=ClientMethod(Type.EVENT)
    )

    robotMark = Property(
        Type=Type.BOOL,
        Flags=Property.Flags.BASE,
        Persistent=Property.Persistent.true
    )

    robotName = Property(
        Type=Type.UNICODE,
        Flags=Property.Flags.BASE
    )

    robotData = Property(
        Type=Type.PYTHON,
        Flags=Property.Flags.BASE
    )

    def reqRobProtocol(self, data):
        if self.getClientType() != 6:
            return
        self.robExecute(data)

    def robExecute(self, data):
        args = python_server(data, list)
        if len(args) >= 1:
            req_name = args[0]
            if isinstance(req_name, str) and re.match("rob[A-Z]", req_name):
                if self.isRobot() or req_name == "robAuth":
                    method = getattr(self, req_name, None)
                    if method:
                        method(*args[1:])

    def robAuth(self, auth, name, data):
        if auth == settings_kbengine.bots.loginAuth.value or self.robotMark:
            if not self.robotMark:
                self.robotMark = True
            self.initRobotInfo(name, data)
            robot_login.send(self)
            self.client.onRobEvent(self.pkgEvent("auth"))
        else:
            self.logout()

    def robControl(self, data):
        args = python_server(data, list)
        self.client.onRobEvent(self.pkgEvent("control", *args))

    def robDisconnect(self):
        self.disconnect()

    def initRobotInfo(self, name, data):
        self.robotName = name
        self.robotData = data
        self.onRobotInit()

    @Event.method
    def onRobotInit(self):
        controller = robotManager.getType(self.robotName).controller
        if controller:
            Equalization[controller].addEntity(self.robotName, self)

    def isRobot(self):
        return self.robotMark

    @staticmethod
    def pkgEvent(func, *args):
        return TEvent(func=func, args=args).client

    @property
    def pk(self):
        pk = self.accountEntity.__ACCOUNT_NAME__
        if self.isRobot():
            return pk.rsplit("_", 1)[-1]
        return pk
