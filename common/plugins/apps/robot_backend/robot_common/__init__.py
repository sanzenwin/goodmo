from robot.robot_common import *
from robot_backend_common import *
from kbe.core import Equalization


def createRobots(data):
    Equalization.RobotBackendGenerator(0).addBots(data["name"], data["amount"], data.get("data"))
