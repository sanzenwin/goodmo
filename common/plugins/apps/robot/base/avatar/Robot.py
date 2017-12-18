from kbe.protocol import Type, Property, Client, ClientMethod, Base, BaseMethodExposed


class Robot:
    base = Base(
        robDisconnect=BaseMethodExposed()
    )

    def robDisconnect(self):
        self.disconnect()

    def isRobot(self):
        return self.getClientType() == 6
