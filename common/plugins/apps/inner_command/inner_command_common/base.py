from kbe.core import Equalization
from inner_command_utils import command, Command, AddAsset
from DEFAULT import TEvent, TCall


@command
class AddGold(AddAsset):
    pass


@command
class SendEventOnline(Command):
    args_conditions = (str,)

    def execute(self):
        Equalization.PlayerManager.sendEventAll(TEvent.pkg(self.args[0]))


@command
class KickPlayersOnline(Command):
    def execute(self):
        Equalization.PlayerManager.runOnlineAll([TCall(method='modifyKickOnline')])
