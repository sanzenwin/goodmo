import json
from common.utils import get_module_attr


def completed(plugins, name):
    d = {}
    for app in plugins.app_component.values():
        plugins.load_all_module("inner_command_common.%s" % app)
    for k, v in get_module_attr("inner_command_utils.c").commands.items():
        d[k] = v.doc()
    plugins.write(json.dumps(d), plugins.PLUGINS_PROXY_COMMON_DIR, "inner_command.json")
