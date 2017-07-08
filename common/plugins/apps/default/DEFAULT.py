from kbe.log import ERROR_MSG
from kbe.protocol import Type
from CORE import DictType


class TAvatarInfo(DictType):
    properties_type = dict(dbid=Type.DBID(Type.UINT64), name=Type.UNICODE)


class TCall(DictType):
    properties_type = dict(method=Type.UNICODE, args=Type.PYTHON)

    def __call__(self, obj):
        method = getattr(obj, self.method, None)
        if method:
            method(*self.args)
        else:
            ERROR_MSG('error call:%s, %s, %s' % (obj, self.method, self.args))


class TEvent(DictType):
    properties_type = dict(func=Type.UNICODE, args=Type.PYTHON.client)


class TClientPython(DictType):
    properties_type = dict(x=Type.PYTHON.client)

    client_python_type = dict

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        if not isinstance(self.x, self.client_python_type):
            self.x = self.client_python_type()


class TClientPythonDict(TClientPython):
    client_python_type = dict


class TClientPythonList(TClientPython):
    client_python_type = list


class DefaultType:
    Type.BOOL(Type.UINT8)
    Type.TIME_STAMP(Type.UINT64)
