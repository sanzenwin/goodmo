from inner_command_utils import command, Command
from robot_common import RobotFactory


@command
class AddRobot(Command):
    args_conditions = (str, str, int)

    def execute(self):
        type_name, robot_name, amount = self.args
        RobotFactory.addBots(type_name, robot_name, amount)


@command
class AddRobotDefault(Command):
    args_conditions = (int, )

    type_name = "bot_"
    robot_name = "default"

    def execute(self):
        amount = self.args[0]
        RobotFactory.addBots(self.type_name, self.robot_name, amount)
