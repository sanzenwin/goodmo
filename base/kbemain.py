# -*- coding: utf-8 -*-
import os
import KBEngine
import plugins
from kbe.log import DEBUG_MSG, INFO_MSG, WARNING_MSG, ERROR_MSG


def onBaseAppReady(isBootstrap):
    """
    KBEngine method.
    baseapp已经准备好了
    @param isBootstrap: 是否为第一个启动的baseapp
    @type isBootstrap: BOOL
    """
    INFO_MSG('onBaseAppReady: isBootstrap=%s, appID=%s, bootstrapGroupIndex=%s, bootstrapGlobalIndex=%s' % \
             (isBootstrap, os.getenv("KBE_COMPONENTID"), os.getenv("KBE_BOOTIDX_GROUP"),
              os.getenv("KBE_BOOTIDX_GLOBAL")))
    KBEngine.BaseApp.onBaseAppReady()


def onReadyForLogin(isBootstrap):
    """
    KBEngine method.
    如果返回值大于等于1.0则初始化全部完成, 否则返回准备的进度值0.0~1.0。
    在此可以确保脚本层全部初始化完成之后才开放登录。
    @param isBootstrap: 是否为第一个启动的baseapp
    @type isBootstrap: BOOL
    """
    return KBEngine.BaseApp.onReadyForLogin()


def onBaseAppShutDown(state):
    """
    KBEngine method.
    这个baseapp被关闭前的回调函数
    @param state: 0 : 在断开所有客户端之前
                  1 : 在将所有entity写入数据库之前
                  2 : 所有entity被写入数据库之后
    @type state: int
    """
    KBEngine.BaseApp.onBaseAppShutDown(state)


def onInit(isReload):
    """
    KBEngine method.
    当引擎启动后初始化完所有的脚本后这个接口被调用
    @param isReload: 是否是被重写加载脚本后触发的
    @type isReload: bool
    """
    INFO_MSG('onInit::isReload:%s' % isReload)
    KBEngine.BaseApp.onInit(isReload)


def onFini():
    """
    KBEngine method.
    引擎正式关闭
    """
    KBEngine.BaseApp.onFini()


def onCellAppDeath(addr):
    """
    KBEngine method.
    某个cellapp死亡
    """
    KBEngine.BaseApp.onCellAppDeath(addr)


def onGlobalData(key, value):
    """
    KBEngine method.
    globalData有改变
    """
    KBEngine.BaseApp.onGlobalData(key, value)


def onGlobalDataDel(key):
    """
    KBEngine method.
    globalData有删除
    """
    KBEngine.BaseApp.onGlobalDataDel(key)


def onGlobalBases(key, value):
    """
    KBEngine method.
    globalBases有改变
    """
    KBEngine.BaseApp.onGlobalBases(key, value)


def onGlobalBasesDel(key):
    """
    KBEngine method.
    globalBases有删除
    """
    KBEngine.BaseApp.onGlobalBasesDel(key)


def onLoseChargeCB(ordersID, dbid, success, datas):
    """
    KBEngine method.
    有一个不明订单被处理， 可能是超时导致记录被billing
    清除， 而又收到第三方充值的处理回调
    """
    KBEngine.BaseApp.onLoseChargeCB(ordersID, dbid, success, datas)
