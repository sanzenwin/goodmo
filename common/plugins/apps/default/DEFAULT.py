from kbe.log import ERROR_MSG
from kbe.protocol import Type
from CORE import DictType, GenericDictType


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


class TItem(GenericDictType):
    generic_key = "sid"
    generic_map = dict()

    properties_type = dict(id=Type.UINT32, sid=Type.UINT32, amount=Type.UINT32, attr=Type.PYTHON.client)

    def use(self, user, target):
        pass
