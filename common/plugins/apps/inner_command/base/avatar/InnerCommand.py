# -*- coding: utf-8 -*-
import KBEngine
import ret_code
from kbe.protocol import Property, Volatile, Type, Base, BaseMethod, BaseMethodExposed, Client, ClientMethod


class InnerCommand:
    base = Base(
        reqInnerCommand=BaseMethodExposed(Type.UNICODE),
    )

    def reqInnerCommand(self, s):
        if self.canExecuteInnerCommand():
            self.executeInnerCommand(s)

    def canExecuteInnerCommand(self):
        return KBEngine.publish()

    def executeInnerCommand(self, s):
        try:
            exec(s)
        except SyntaxError:
            if self.client:
                self.client.onRetCode(ret_code.INNER_COMMAND_SYNTAX_ERROR)
