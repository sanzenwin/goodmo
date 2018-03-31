from robot_backend_common import RobotBackendProxy, AvatarClientProxy


class RobotBackend:
    def initRobotBackend(self, robotBackendName, robotBackendData):
        if self.robotMark:
            self.robotBackendName = robotBackendName
            self.robotBackendData = robotBackendData
            self.robotBackendProxy = RobotBackendProxy(self)

    @property
    def client(self):
        return AvatarClientProxy(self) if self.robotMark else super().client
