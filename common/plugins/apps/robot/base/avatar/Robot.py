import re
import settings
from kbe.protocol import Type, Property, Client, ClientMethod, Base, BaseMethodExposed
from kbe.xml import settings_kbengine
from CORE import python_server


class Robot:
    base = Base(
        reqRobProtocol=BaseMethodExposed(Type.PYTHON)
    )

    client = Client(
        onRobAuth=ClientMethod(),
    )

    robotMark = Property(
        Type=Type.BOOL,
        Flags=Property.Flags.BASE,
        Persistent=Property.Persistent.true
    )

    def __init__(self):
        super().__init__()
        self.__robotMark = False

    def reqRobProtocol(self, data):
        if self.getClientType() != 6:
            return
        args = python_server(data, list)
        if len(args) >= 1:
            req_name = args[0]
            if isinstance(req_name, str) and re.match("rob[A-Z]", req_name):
                if self.isRobot() or req_name == "robAuth":
                    method = getattr(self, req_name, None)
                    if method:
                        method(*args[1:])

    def robAuth(self, auth):
        if auth == settings_kbengine.bots.loginAuth.value or self.robotMark:
            if not self.robotMark:
                self.robotMark = True
            settings.Robot.onLogin(self)
            self.client.onRobAuth()
        else:
            self.logout()

    def robDisconnect(self):
        self.disconnect()

    def isRobot(self):
        return self.robotMark

    @property
    def pk(self):
        pk = self.accountEntity.__ACCOUNT_NAME__
        if self.isRobot():
            return pk.rsplit("_", 1)[-1]
        return pk
