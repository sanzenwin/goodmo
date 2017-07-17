# coding:utf-8
from . import SettingsEntity


class Global(SettingsEntity):
    enableAsyncHttp = False
    enableAsyncio = False


class BaseApp(SettingsEntity):
    equalizationBaseappAmount = 1
    readyForLoginWarringSeconds = 20
