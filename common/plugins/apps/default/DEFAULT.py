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


class AvatarClientProxy:
    def __init__(self, avatar, method):
        self.avatar = avatar
        self.method = method

    def __call__(self, *args):
        self.call(*args)

    def call(self, *args):
        pass


class AvatarClient:
    proxy_class = AvatarClientProxy

    def __init__(self, avatar):
        self.avatar = avatar

    def __getattr__(self, item):
        return getattr(self.avatar.client, item) if self.avatar.client else self.proxy_class(self.avatar, item)


class TAvatar(DictType):
    properties_type = dict(avatar=Type.ENTITYCALL)

    client_class = AvatarClient

    def __init__(self, avatar):
        super().__init__(avatar=avatar)

    @property
    def client(self):
        return self.client_class(self)

    def __getattr__(self, item):
        return getattr(self.avatar, item)
