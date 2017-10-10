# -*- coding: utf-8 -*-
import KBEngine
from common.utils import server_time, Event, Bytes
from kbe.protocol import Base, BaseMethodExposed, Property, Client, ClientMethod, Type


class Request:
    base = Base(
        reqOpenUrl=BaseMethodExposed(Type.UNICODE),
    )

    client = Client(
        onOpenUrl=ClientMethod(Type.UNICODE, Type.UNICODE)
    )

    def reqOpenUrl(self, operation):
        def callback(orderID, dbID, success, datas):
            if uid != orderID:
                return
            if self.client:
                data = Bytes(datas)
                self.client.onOpenUrl(operation, data.get("url", ""))
            self.release()

        data = dict()
        passed = False
        for d in self.openUrlData(operation):
            if isinstance(d, dict):
                data.update(d)
                passed = True
        if not passed:
            return
        self.addRef()
        uid = str(KBEngine.genUUID64())
        KBEngine.charge(uid, self.databaseID,
                        Bytes(interface="openUrl", id=self.guaranteeID, operation=operation, data=data).dumps(),
                        callback)

    @Event.method
    def openUrlData(self, operation):
        return None
