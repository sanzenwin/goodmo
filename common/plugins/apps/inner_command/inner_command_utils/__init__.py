import builtins
import settings
from kbe.core import Equalization
from DEFAULT import TCall


class C:
    def __init__(self):
        self.command = None
        self.commands = dict()

    def __getattr__(self, item):
        com_cls = self.commands.get(item, UnknownCommand)
        com = com_cls()
        return com if com.args_conditions else None


c = C()
setattr(builtins, settings.InnerCommand.name, c)


def command(com):
    global c
    c.commands[com.command_name()] = com
    return com


class Command:
    name = None
    args_conditions = ()

    @classmethod
    def command_name(cls):
        return cls.name or cls.__name__.lower()

    def __init__(self):
        super().__init__()
        self.args = []
        self.valid = True
        self.max_args_length = len(self.args_conditions)
        if self.max_args_length == 0:
            self.do_execute()

    def __str__(self):
        return None

    def __truediv__(self, arg):
        self.args.append(arg)
        if len(self.args) >= self.max_args_length:
            self.do_execute()
            return None
        return self

    def __floordiv__(self, arg):
        self.args.append(arg)
        self.do_execute()

    @staticmethod
    def doc():
        return ""

    def check_args(self):
        if not self.args_conditions:
            return True
        if self.args_conditions == tuple(type(arg) for arg in self.args):
            return True
        return False

    def error_args(self):
        print("Wrong args. current is %s,should be %s" % (self.args, str(self.args_conditions)))

    def success_execute(self):
        print("Command executed success: %s, %s" % (self.command_name(), self.args))

    def do_execute(self):
        if not self.valid:
            return
        if self.check_args():
            self.execute()
            self.on_execute()
            self.success_execute()
        else:
            self.error_args()
        self.valid = False

    def execute(self):
        raise NotImplementedError("subclass[%s] should implement this method!" % self.__class__.__name__)

    def on_execute(self):
        pass


class UnknownCommand(Command):
    help_str = "Unknown command executed."

    def __str__(self):
        return self.help_str

    def execute(self):
        print(self.help_str)


class AddAsset(Command):
    args_conditions = (int, int)

    def asset_name(self):
        return self.__class__.__name__.replace("Add", "")

    def asset_amount(self):
        return self.args[1]

    def execute(self):
        pid = self.args[0]
        Equalization.PlayerManager(pid).run(pid,
                                            [TCall(method='modify%s' % self.asset_name(), args=[self.asset_amount()])])
