# coding:utf-8
from . import SettingsEntity


class BaseApp(SettingsEntity):
    enableAsyncHttp = False
    asyncHttpTickFrequency = 1 / 1000
    equalizationBaseappAmount = 1
