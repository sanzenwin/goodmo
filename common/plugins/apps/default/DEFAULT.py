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

    real_type = dict

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        if not isinstance(self.x, self.real_type):
            self.x = self.real_type()


class TClientPythonDict(TClientPython):
    real_type = dict


class TClientPythonList(TClientPython):
    real_type = list


class DefaultType:
    Type.BOOL(Type.UINT8)
    Type.TIME_STAMP(Type.UINT64)
