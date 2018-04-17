# -*- coding: utf-8 -*-
import KBEngine
from kbe.protocol import Type, Base, BaseMethod
from robot_common import createRobots


class RobotController:
    base = Base(
        addEntity=BaseMethod(Type.UNICODE, Type.ENTITYCALL),
        removeEntity=BaseMethod(Type.ENTITY_ID),
        controllerEvent=BaseMethod(Type.ENTITY_ID, Type.PYTHON)
    )

    controllerBotName = ""

    def __init__(self):
        super().__init__()
        self.bots = {}
        self.names = {}
        self.controllerBot = None

    def addEntity(self, name, entity):
        self.bots[entity.id] = entity
        self.names[entity.id] = name
        if name == self.controllerBotName:
            self.controllerBot = entity
            KBEngine.BaseApp.instance.runInNextFrame(self.onGetController)
        self.onAddEntity(entity.id)

    def removeEntity(self, entityID):
        del self.bots[entityID]
        del self.names[entityID]
        if self.controllerBot and self.controllerBot.id == entityID:
            self.controllerBot = None
        self.onRemoveEntity(entityID)

    def controllerEvent(self, entityID, event):
        handler = getattr(self, "controller__" + event[0], None)
        if handler:
            handler(entityID, *event[1:])

    def onGetController(self):
        pass

    def onAddEntity(self, entityID):
        pass

    def onRemoveEntity(self, entityID):
        pass

    @staticmethod
    def generateBots(name, amount, data=None):
        createRobots(dict(name=name, amount=amount, data=data))

    @classmethod
    def generateControllerBots(cls):
        cls.generateBots(cls.controllerBotName, 1)
