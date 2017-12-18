from inner_command_utils import command, Command
from robot_common import RobotFactory


@command
class AddRobot(Command):
    args_conditions = (str, str, int)

    def execute(self):
        type_name, robot_name, amount = self.args
        RobotFactory.addBots(type_name, robot_name, amount)
