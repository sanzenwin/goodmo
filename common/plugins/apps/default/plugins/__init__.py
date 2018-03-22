import settings
from collections import OrderedDict
from plugins.conf import Str


def run(plugins, _):
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
