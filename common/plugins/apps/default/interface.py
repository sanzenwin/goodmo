import KBEngine
import settings
from common.utils import Bytes
from common.asyncHttp import AsyncHttp


def syncData(ordersID, entityDBID, data):
    def callback(response):
        datas = b''
        if response.code in (200, 400):
            data = AsyncHttp.parse_json(response.body)
            datas = Bytes(**data).dumps()
        KBEngine.chargeResponse(ordersID, datas,
                                KBEngine.SERVER_SUCCESS if response.code == 200 else KBEngine.SERVER_ERR_OP_FAILED)

    AsyncHttp().post(settings.Account.url.syncData, callback, data)


def operate(ordersID, entityDBID, data):
    def callback(response):
        datas = b''
        if response.code in (200, 400):
            data = AsyncHttp.parse_json(response.body)
            datas = Bytes(**data).dumps()
        KBEngine.chargeResponse(ordersID, datas,
                                KBEngine.SERVER_SUCCESS if response.code == 200 else KBEngine.SERVER_ERR_OP_FAILED)

    AsyncHttp().post(settings.Account.url.operateUser, callback, data)
