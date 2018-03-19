from __future__ import absolute_import
from __future__ import print_function

import sys
from traceback import format_exception as traceback_format_exception
from .formatter import THEME, MAX_LENGTH, PIPE_CHAR, CAP_CHAR, ExceptionFormatter
from better_exceptions.signals import better_exceptions_catch

THEME = THEME.copy()


def excepthook(exc, value, tb):
    better_exceptions_catch.send(exception_format, args=(exc, value, tb))


def hook():
    sys.excepthook = excepthook


def unhook():
    sys.excepthook = exception_format.standard_sys_except_hook


class Format:
    standard_sys_except_hook = sys.excepthook

    @staticmethod
    def format_better_exception(exc, value, tb):
        _formatter = ExceptionFormatter(colored=False, theme=THEME, max_length=MAX_LENGTH, pipe_char=PIPE_CHAR,
                                        cap_char=CAP_CHAR)
        return _formatter.format_exception(exc, value, tb)

    @staticmethod
    def format_normal_exception(exc, value, tb):
        return traceback_format_exception(exc, value, tb)


exception_format = Format()
del Format
