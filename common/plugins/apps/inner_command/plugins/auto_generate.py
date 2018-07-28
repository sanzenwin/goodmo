import simplejson as json
from common.utils import get_module_attr


def completed(plugins, name):
    for app in plugins.app_component.values():
        plugins.load_all_module("inner_command_common.%s" % app)
    c = get_module_attr("inner_command_utils.c")
    doc = c.get_doc()
    info = c.get_app_info()
    collect = {}
    for k, v in doc.items():
        d = collect.setdefault(info[k], {})
        d[k] = v
    for appname, d in collect.items():
        plugins.write(json.dumps(d, sort_keys=True), plugins.PLUGINS_PROXY_COMMON_DIR, appname, "inner_command.json")
