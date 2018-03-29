from inner_command_utils import command, Command
from robot_backend_common import robotManager


@command
class AddRobotDefault(Command):
    args_conditions = (str, int)
    robot_name = "default"

    def execute(self):
        amount = self.args[0]
        robotManager.addBots(self.robot_name, amount)
