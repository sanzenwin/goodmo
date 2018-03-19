import settings
from kbe.log import ERROR_MSG
from kbe.protocol import Type
from CORE import DictType


class DefaultType:
    Type.DBID(Type.UINT64)
    Type.BOOL(Type.UINT8)
    Type.TIME_STAMP(Type.UINT64)
    Type.URL(Type.UNICODE)
    Type.GOLD(Type.UINT32)
    Type.GOLD64(Type.UINT64)
    Type.GOLD_X(Type.UINT64) if settings.Avatar.gold64 else Type.GOLD_X(Type.UINT32)


class TAvatarInfo(DictType):
    properties_type = dict(dbid=Type.DBID, name=Type.UNICODE)


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

    @classmethod
    def pkg(cls, func, *args):
        return cls(func=func, args=args).client


class TAvatar(DictType):
    properties_type = dict(entity=Type.ENTITYCALL)

    def __init__(self, entity):
        super().__init__(entity=entity)
