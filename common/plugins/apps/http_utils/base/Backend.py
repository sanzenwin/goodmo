import KBEngine
from kbe.protocol import Property, Type, Base, BaseMethod
from kbe.utils import generate_runtime_pk

globalInstance_ = None


class Backend(KBEngine.Entity):
    base = Base(
        complete=BaseMethod(Type.UNICODE, Type.PYTHON)
    )

    @classmethod
    def getInstance(cls):
        global globalInstance_
        if globalInstance_ is None:
            globalInstance_ = KBEngine.createEntityLocally(cls.__name__)
        return globalInstance_

    def __init__(self):
        super().__init__()
        self.receivers = {}

    def complete(self, orderID, data):
        receiver = self.receivers.pop(orderID, None)
        if receiver:
            receiver(data)

    def insertInfo(self, entity, receiver, data):
        order = generate_runtime_pk()
        self.receivers[order] = receiver
        entity.insertBackendInfo(order, self, data)

    def queryInfo(self, entity, receiver, data):
        order = generate_runtime_pk()
        self.receivers[order] = receiver
        entity.queryBackendInfo(order, self, data)

    def delInfo(self, entity, receiver, data):
        order = generate_runtime_pk()
        self.receivers[order] = receiver
        entity.delBackendInfo(order, self, data)

    def editInfo(self, entity, receiver, data):
        order = generate_runtime_pk()
        self.receivers[order] = receiver
        entity.editBackendInfo(order, self, data)
