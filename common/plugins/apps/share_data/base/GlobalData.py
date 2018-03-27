import KBEngine
from common.utils import SteadyData
from kbe.protocol import Property, Type, Base, BaseMethod
from kbe.core import Singleton
from kbe.signals import global_data_change, global_data_del
from Singleton import Singleton as Singleton_


class GlobalData(Singleton_):
    base = Base(
        updateSteadyDataRemote=BaseMethod(Type.PYTHON),
        delSteadyDataRemote=BaseMethod(Type.UNICODE.array),
    )

    _steadyData = Property(
        Type=Type.PYTHON,
        Flags=Property.Flags.BASE,
        Default={},
        Persistent=Property.Persistent.true
    )

    def __init__(self):
        super().__init__()
        self.steadyData = SteadyData(self._steadyData)
        self.update(self.steadyData.data)

    def updateSteadyDataRemote(self, data):
        self.steadyData.update(data)
        self.update(data)

    def delSteadyDataRemote(self, keys):
        for key in keys:
            self.steadyData.pop(key)
            self.pop(key)

    @classmethod
    def get(cls, key, default=None):
        return KBEngine.globalData.get(key, default)

    @classmethod
    def set(cls, key, value):
        KBEngine.globalData[key] = value
        global_data_change.send(cls, key=key, value=value)

    @classmethod
    def pop(cls, key, default=None):
        if key in KBEngine.globalData:
            ret = KBEngine.globalData.pop(key)
            global_data_del.send(cls, key=key)
            return ret
        return default

    @classmethod
    def update(cls, data):
        for key, value in data.items():
            cls.set(key, value)

    @classmethod
    def updateSteadyData(cls, data):
        Singleton[cls.__name__].updateSteadyDataRemote(data)
