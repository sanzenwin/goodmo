# -*- coding: utf-8 -*-
import KBEngine
import ret_code
from common.utils import get_module_attr
from kbe.protocol import Property, Volatile, Type, Base, BaseMethod, BaseMethodExposed, Client, ClientMethod
from CORE import python_client


class InnerCommand:
    base = Base(
        reqExecuteInnerCommand=BaseMethodExposed(Type.UNICODE),
        reqGetInnerCommands=BaseMethodExposed()
    )

    client = Client(
        onInnerCommands=ClientMethod(Type.PYTHON.client)
    )

    def reqExecuteInnerCommand(self, s):
        if self.canExecuteInnerCommand():
            self.executeInnerCommand(s)

    def reqGetInnerCommands(self):
        if self.canExecuteInnerCommand():
            self.client.onInnerCommands(python_client(get_module_attr("inner_command_utils.c").doc))

    def canExecuteInnerCommand(self):
        return not KBEngine.publish()

    def executeInnerCommand(self, s):
        try:
            exec(s)
        except (SyntaxError, TypeError) as e:
            if self.client:
                self.client.onRetCode(ret_code.INNER_COMMAND_SYNTAX_ERROR)
            print(e)
