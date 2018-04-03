from robot_backend_common import RobotBackendProxy, AvatarClientProxy


class RobotBackend:
    def onReqReady(self):
        if self.robotMark:
            self.robotBackendProxy.robot.onLogin()

    def initRobotBackend(self, robotBackendName, robotBackendData):
        if self.robotMark:
            self.initRobotInfo(robotBackendName, robotBackendData)
            self.robotBackendProxy = RobotBackendProxy(self)

    @property
    def client(self):
        return AvatarClientProxy(self) if self.robotMark else super().client
