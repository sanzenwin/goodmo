# -*- coding: utf-8 -*-
from kbe.protocol import Property, Type, Base, BaseMethod


class BackendConnector:
    base = Base(
        insertBackendInfo=BaseMethod(Type.UNICODE, Type.ENTITYCALL, Type.PYTHON),
        queryBackendInfo=BaseMethod(Type.UNICODE, Type.ENTITYCALL, Type.PYTHON),
        delBackendInfo=BaseMethod(Type.UNICODE, Type.ENTITYCALL, Type.PYTHON),
        editBackendInfo=BaseMethod(Type.UNICODE, Type.ENTITYCALL, Type.PYTHON)
    )

    def insertBackendInfo(self, order, backend, data):
        pass

    def queryBackendInfo(self, order, backend, data):
        pass

    def delBackendInfo(self, order, backend, data):
        pass

    def editBackendInfo(self, order, backend, data):
        pass
