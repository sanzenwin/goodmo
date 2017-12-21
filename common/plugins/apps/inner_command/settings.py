from plugins.conf import SettingsNode, Str


class InnerCommand(SettingsNode):
    name = "c"


class RetCode(SettingsNode):
    INNER_COMMAND_SYNTAX_ERROR = Str("命令存在语法错误")
