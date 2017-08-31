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


class Log:
    tag_template = "[{0}]"

    def __init__(self, tag):
        self.tag = tag
        self.__tag = self.tag_template.format(self.tag)

    def d(self, s):
        DEBUG_MSG("%s %s" % (self.__tag, s))

    def i(self, s):
        INFO_MSG("%s %s" % (self.__tag, s))

    def w(self, s):
        WARNING_MSG("%s %s" % (self.__tag, s))

    def e(self, s):
        ERROR_MSG("%s %s" % (self.__tag, s))


def _print(*args, sep=' ', end='\n', file=None):
    ERROR_MSG(*args)

__print__ = print
builtins.print = _print
