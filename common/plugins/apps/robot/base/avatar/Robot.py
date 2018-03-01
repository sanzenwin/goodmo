import settings
from kbe.protocol import Type, Property, Client, ClientMethod, Base, BaseMethodExposed


class Robot:
    base = Base(
        robDisconnect=BaseMethodExposed()
    )

    def onLogin(self):
        if self.isRobot():
            settings.Robot.onLogin(self)

    def robDisconnect(self):
        self.disconnect()

    def isRobot(self):
        return self.getClientType() == 6

    @property
    def pk(self):
        pk = self.accountEntity.__ACCOUNT_NAME__
        if self.isRobot():
            return pk.rsplit("_", 1)[-1]
        return pk
