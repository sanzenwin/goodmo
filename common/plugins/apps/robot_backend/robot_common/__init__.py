from robot.robot_common import *
from robot_backend_common import robotManager, factory, Robot


def createRobots(data):
    robotManager.addBots(data["name"], data["amount"])
