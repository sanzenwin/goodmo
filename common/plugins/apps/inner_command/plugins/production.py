from plugins import plugins

plugins.load_all_module("inner_command_common.%s" % plugins.app)
