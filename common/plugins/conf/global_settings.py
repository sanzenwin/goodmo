# coding:utf-8
from . import SettingsEntity
from kbe.xml import settings_kbengine


class Global(SettingsEntity):
    enableAsyncHttp = False
    enableAsyncio = False
    gameTimeInterval = 0.5 / settings_kbengine.gameUpdateHertz.value


class BaseApp(SettingsEntity):
    equalizationBaseappAmount = 1
    readyForLoginWarringSeconds = 20
