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


class AvatarClient:
    def __init__(self, avatar):
        self.avatar = avatar

    def __getattr__(self, item):
        return self.get_attr(item)

    def get_attr(self, item):
        return getattr(self.avatar.entity.client, item) if self.avatar.entity.client else self._proxy

    def _proxy(self, *args):
        pass


class TAvatar(DictType):
    properties_type = dict(entity=Type.ENTITYCALL)

    client_class = AvatarClient
    contain_none = True
    entity = None

    def __init__(self, entity=None, **kwargs):
        super().__init__(entity=entity, **kwargs)

    def __getattr__(self, item):
        return getattr(self.entity, item)

    def __bool__(self):
        return bool(self.entity)

    @property
    def client(self):
        return self.client_class(self)
