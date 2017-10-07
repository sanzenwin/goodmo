# -*- coding: utf-8 -*-
import plugins
import robot_main


def onInit(isReload):
    """
    KBEngine method.
    当引擎启动后初始化完所有的脚本后这个接口被调用
    @param isReload: 是否是被重写加载脚本后触发的
    @type isReload: bool
    """
    plugins.plugins.init_bots()
    plugins.plugins.open_async()
    robot_main.start()


def onFinish():
    """
    KBEngine method.
    客户端将要关闭时， 引擎调用这个接口
    可以在此做一些游戏资源清理工作
    """
