import settings
from collections import OrderedDict
from plugins.conf import Str


def main(plugins, name):
    init_ret_code(plugins)


def init_ret_code(plugins):
    template_str = '# coding:utf-8\r\n"""\r\n{\r\n%s\r\n}\r\n"""\r\n\r\n\r\n%s\r\n'
    client_dict = OrderedDict()
    server_dict = OrderedDict()
    for i, c in enumerate(reversed(settings.RetCode.__class__.mro())):
        for j, k in enumerate(sorted(c.__dict__)):
            v = c.__dict__[k]
            if isinstance(v, Str):
                code = (i + 1) * 100 + j
                client_dict[code] = v
                server_dict[k] = code
    client_list = []
    for k, v in client_dict.items():
        client_list.append('%s: "%s"' % (k, v))
    server_list = []
    for k, v in server_dict.items():
        server_list.append("%s = %s" % (k, v))

    s = template_str % (",\r\n".join(client_list), "\r\n".join(server_list))
    plugins.write(s, plugins.PLUGINS_PROXY_COMMON_DIR, "ret_code.py")
