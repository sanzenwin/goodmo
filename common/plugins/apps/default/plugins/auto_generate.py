import settings
from collections import OrderedDict
from plugins.conf import Str


def run(plugins, _):
    template_str = '# coding:utf-8\r\n\r\n%s\r\n'
    name_map = {}
    client_dict = {}
    server_dict = OrderedDict()
    for c in reversed(settings.RetCode.__class__.mro()):
        j = 1
        appname_list = c.__module__.split(".")
        if len(appname_list) != 2 or appname_list[-1] != "settings":
            continue
        appname = appname_list[0]
        appid = plugins.m_app_id_map[appname]
        client_dict[appname] = OrderedDict()
        for k in sorted(c.__dict__):
            v = c.__dict__[k]
            if isinstance(v, Str):
                code = appid * 10000 + j
                if k in server_dict:
                    client_dict[appname].pop(server_dict[k], None)
                client_dict[appname][code] = v
                server_dict[k] = code
                name_map[k] = appname
                j += 1
    client_map = {}
    for name, d in client_dict.items():
        client_map[name] = []
        for k, v in d.items():
            client_map[name].append('    "%s": "%s"' % (k, v))
    server_list = []
    for k, v in server_dict.items():
        server_list.append("%s = %s" % (k, v))
        client_map[name_map[k]].append('    "%s": %s' % (k, v))

    s = template_str % "\r\n".join(server_list)
    plugins.write(s, plugins.PLUGINS_PROXY_COMMON_DIR, "ret_code.py")
    for name, lst in client_map.items():
        plugins.write("{\r\n%s\r\n}" % ",\r\n".join(lst), plugins.PLUGINS_PROXY_COMMON_DIR, name, "ret_code.json")
