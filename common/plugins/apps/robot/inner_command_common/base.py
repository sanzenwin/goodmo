from inner_command_utils import command, Command
from robot_common import createRobots


@command
class AddRobot(Command):
    args_conditions = (str, str, int)

    def execute(self):
        type_name, robot_name, amount = self.args
        createRobots(dict(type=type_name, name=robot_name, amount=amount))


@command
class AddRobotDefault(Command):
    args_conditions = (int, )

    type_name = "bot_"
    robot_name = "default"

    def execute(self):
        amount = self.args[0]
        createRobots(dict(type=self.type_name, name=self.robot_name, amount=amount))
