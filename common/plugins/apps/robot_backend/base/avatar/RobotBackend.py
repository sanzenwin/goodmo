from kbe.protocol import Type, Property, Client, ClientMethod, Base, BaseMethodExposed
from robot_backend_common import RobotBackendProxy, AvatarClientProxy


class RobotBackend:
    robotBackendMark = Property(
        Type=Type.BOOL,
        Flags=Property.Flags.BASE,
        Persistent=Property.Persistent.true
    )

    def initRobotBackend(self, robotBackendName, robotBackendData):
        if self.robotBackendMark:
            self.robotBackendName = robotBackendName
            self.robotBackendData = robotBackendData
            self.robotBackendProxy = RobotBackendProxy(self)

    def isRobot(self):
        return self.robotBackendMark

    @property
    def client(self):
        return AvatarClientProxy(self) if self.robotBackendMark else super().client
