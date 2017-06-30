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


class DefaultType:
    Type.BOOL(Type.UINT8)
