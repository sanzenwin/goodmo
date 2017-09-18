# -*- coding: utf-8 -*-
import settings
import KBEngine
from kbe.protocol import Property, Volatile, Type, Base, BaseMethod, BaseMethodExposed, Client, ClientMethod
from common.utils import Bytes, ExpiredData, TodayData, WeekData, MonthData, YearData
from common.dispatcher import receiver
from kbe.utils import LockAsset
from default.signals import avatar_common_login, consume_data
from CORE import python_client


class Asset(LockAsset("gold")):
    base = Base(
        reqSyncData=BaseMethodExposed(),
    )

    client = Client(
        onSyncData=ClientMethod(),
        onOperate=ClientMethod(Type.UNICODE, Type.UNICODE, Type.PYTHON),
    )

    name = Property(
        Type=Type.UNICODE,
        Flags=Property.Flags.BASE_AND_CLIENT,
        # Index=Property.Index.UNIQUE,
        DatabaseLength=settings.Avatar.nameLimit,
        Persistent=Property.Persistent.true
    )

    gold = Property(
        Type=Type.GOLD64 if settings.Avatar.gold64 else Type.GOLD,
        Flags=Property.Flags.BASE_AND_CLIENT,
        Persistent=Property.Persistent.true
    )

    avatarUrl = Property(
        Type=Type.UNICODE,
        Flags=Property.Flags.BASE_AND_CLIENT,
        Persistent=Property.Persistent.true
    )

    data = Property(
        Type=Type.PYTHON,
        Flags=Property.Flags.BASE,
        Default={},
        Persistent=Property.Persistent.true
    )

    def reqSyncData(self):
        def callback(orderID, dbID, success, datas):
            if uid != orderID:
                return
            data = Bytes(datas)
            dataList = data.get("x", [])
            self.consumeData(dataList)
            if self.client:
                self.client.onSyncData()
            self.release()

        self.addRef()
        uid = str(KBEngine.genUUID64())
        KBEngine.charge(uid, self.databaseID,
                        Bytes(interface="syncData", pk=self.pk).dumps(), callback)

    def interfaceOperate(self, operate, t, d):
        def callback(orderID, dbID, success, datas):
            if uid != orderID:
                return
            if self.client:
                self.client.onOperate(operate, t, python_client(Bytes(datas)))
            self.release()

        self.addRef()
        uid = str(KBEngine.genUUID64())
        KBEngine.charge(uid, self.databaseID,
                        Bytes(interface="operate", operate=operate, type=t, data=d).dumps(), callback)

    def consumeData(self, dataList):
        for data in dataList:
            consume_data.send(sender=self, data=data)
            handler = getattr(self, "%s%sConsumeData" % (data["pay_type"], data["attach"]["type"]))
            handler(data["attach"])

    def modifyName(self, changed):
        self.name = changed


@receiver(avatar_common_login)
def syncData(signal, sender):
    data = Bytes(sender.accountEntity.getClientDatas()[0])
    dataList = data.get("consume_data", {}).get("x", [])
    sender.consumeData(dataList)
