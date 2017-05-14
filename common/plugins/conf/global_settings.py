# coding:utf-8
from . import SettingsEntity


class BaseApp(SettingsEntity):
    enableAsyncHttp = False
    enableAsyncio = False
    equalizationBaseappAmount = 1
