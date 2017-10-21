# coding:utf-8
from . import SettingsEntity, SettingsNode
from kbe.xml import settings_kbengine


class Global(SettingsEntity):
    enableAsyncHttp = True
    enableAsyncio = True
    gameTimeInterval = 0.5 / settings_kbengine.gameUpdateHertz.value
    telnetOnePassword = True
    kbengine_xml_mongodb = dict(host='localhost', port=27017, username=None, password=None)


class BaseApp(SettingsEntity):
    readyForLoginWarringSeconds = 20
    readyForLoginIntervalSeconds = 2
    equalizationBaseappAmount = 1
    baseappIndependence = SettingsNode()
