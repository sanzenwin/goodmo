# -*- coding: utf-8 -*-
import builtins
import KBEngine


def printMsg(args, isPrintPath):
    __print__(*args)


def TRACE_MSG(*args):
    KBEngine.scriptLogType(KBEngine.LOG_TYPE_NORMAL)
    printMsg(args, False)


def DEBUG_MSG(*args):
    if KBEngine.publish() == 0:
        KBEngine.scriptLogType(KBEngine.LOG_TYPE_DBG)
        printMsg(args, True)


def INFO_MSG(*args):
    KBEngine.scriptLogType(KBEngine.LOG_TYPE_INFO)
    printMsg(args, False)


def WARNING_MSG(*args):
    KBEngine.scriptLogType(KBEngine.LOG_TYPE_WAR)
    printMsg(args, True)


def ERROR_MSG(*args):
    KBEngine.scriptLogType(KBEngine.LOG_TYPE_ERR)
    printMsg(args, True)


def SHOW_MSG(*args):
    ERROR_MSG(*args)


def _print(*args, sep=' ', end='\n', file=None):
    ERROR_MSG(*args)

__print__ = print
builtins.print = _print
