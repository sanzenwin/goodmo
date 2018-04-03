# -*- coding: utf-8 -*-
from kbe.protocol import Type, Base, BaseMethod
from robot_common import createRobots


class RobotController:
    base = Base(
        addEntity=BaseMethod(Type.ENTITYCALL)
    )

    def __init__(self):
        super().__init__()
        self.bots = {}
        self.names = {}

    def addEntity(self, name, entity):
        self.bots[entity.id] = entity
        self.names[entity.id] = name

    def generateBots(self, name, amount, data=None):
        createRobots(dict(name=name, amount=amount, data=data))
