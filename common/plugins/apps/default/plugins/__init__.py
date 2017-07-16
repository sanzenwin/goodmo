import os
import shutil
import settings
from collections import OrderedDict
from plugins.conf import Str

__proxy_modules__ = "ret_code",


def run(plugins, name):
    init_ret_code(plugins)


def init_ret_code(plugins):
    template_str = '# coding:utf-8\r\n\r\n%s\r\n'
    client_dict = OrderedDict()
    server_dict = OrderedDict()
    i = 1
    for c in reversed(settings.RetCode.__class__.mro()):
        b = len(client_dict)
        j = 1
        for k in sorted(c.__dict__):
            v = c.__dict__[k]
            if isinstance(v, Str):
                code = i * 100 + j
                if k in server_dict:
                    client_dict.pop(server_dict[k])
                client_dict[code] = v
                server_dict[k] = code
                j += 1
        if b != len(client_dict):
            i += 1

    client_list = []
    for k, v in client_dict.items():
        client_list.append('    "%s": "%s"' % (k, v))
    server_list = []
    for k, v in server_dict.items():
        server_list.append("%s = %s" % (k, v))
        client_list.append('    "%s": %s' % (k, v))

    s = template_str % "\r\n".join(server_list)
    plugins.write(s, plugins.PLUGINS_PROXY_COMMON_DIR, "ret_code.py")
    plugins.write("{\r\n%s\r\n}" % ",\r\n".join(client_list), plugins.PLUGINS_PROXY_COMMON_DIR, "ret_code.json")


def completed(plugins, name):
    client_data = os.path.join(plugins.DATA_DIR, "client_data")
    plugins.clear(client_data)
    for dirpath, dirnames, filenames in os.walk(plugins.HOME_DIR):
        for name in filenames:
            path = os.path.normpath(os.path.join(dirpath, name))
            if os.path.isfile(path) and path.endswith(".json"):
                shutil.move(path, os.path.join(client_data, name))
