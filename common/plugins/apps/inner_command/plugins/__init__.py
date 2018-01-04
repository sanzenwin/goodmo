import simplejson as json
from common.utils import get_module_attr


def completed(plugins, name):
    for app in plugins.app_component.values():
        plugins.load_all_module("inner_command_common.%s" % app)
    plugins.write(json.dumps(get_module_attr("inner_command_utils.c").doc, sort_keys=True),
                  plugins.PLUGINS_PROXY_COMMON_DIR, "inner_command.json")
