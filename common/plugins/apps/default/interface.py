import KBEngine
import settings
from functools import partial
from common.utils import Bytes
from common.asyncHttp import AsyncHttp


def callback(ordersID, response):
    datas = b''
    if response.code in (200, 400):
        data = AsyncHttp.parse_json(response.body)
        datas = Bytes(**data).dumps()
    KBEngine.chargeResponse(ordersID, datas,
                            KBEngine.SERVER_SUCCESS if response.code == 200 else KBEngine.SERVER_ERR_OP_FAILED)


def syncData(ordersID, entityDBID, data):
    AsyncHttp().post(settings.Account.url.syncData, partial(callback, ordersID), data)


def operate(ordersID, entityDBID, data):
    AsyncHttp().post(settings.Account.url.operateUser, partial(callback, ordersID), data)
