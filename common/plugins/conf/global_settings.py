# coding:utf-8
from . import SettingsEntity, SettingsNode
from kbe.xml import settings_kbengine


class Global(SettingsEntity):
    enableAsyncHttp = True
    enableAsyncio = True
    gameTimeInterval = 0.5 / settings_kbengine.gameUpdateHertz.value


class BaseApp(SettingsEntity):
    readyForLoginWarringSeconds = 20
    readyForLoginIntervalSeconds = 2
    equalizationBaseappAmount = 1
    baseappIndependence = SettingsNode()
