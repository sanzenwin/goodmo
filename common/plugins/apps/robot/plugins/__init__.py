import os
from common.utils import get_module


def completed(plugins, name):
    entity_client_methods = {k: v for k, v in plugins.m_entity_client_methods.items() if v}
    template_proxy_str = """# -*- coding: utf-8 -*-
from %(plugin_name)s.%(app)s.%(cls_name)s import %(cls_name)s as %(cls_name)sBase


class Client:
    %(method_list_str)s

class %(cls_name)s(%(cls_name)sBase, Client):
    pass
"""
    template_player_str = """# -*- coding: utf-8 -*-
from robot.robot_common import robot
from %(plugin_name)s.%(app)s.%(cls_name)s import %(cls_name)s as %(cls_name)sBase, \
Player%(cls_name)s as Player%(cls_name)sBase


@robot
class Client:
    %(method_list_str)s

class %(cls_name)s(%(cls_name)sBase, Client):
    pass


class Player%(cls_name)s(Player%(cls_name)sBase, %(cls_name)s):
    pass
"""

    def find_plugins(n):
        for name in plugins.apps:
            m = get_module("%s.bots.%s" % (name, n))
            if m is not None:
                break
        else:
            assert False, "[%s] client class should be added!" % n
        return m.__file__.split(os.sep)[-3]

    for entity_name, client_methods in entity_client_methods.items():
        plugin_name = find_plugins(entity_name)
        method = "def %s(%s):\r\n        pass"
        method_list = []
        for k, v in client_methods.items():
            # method_list.append(method % (k, ", ".join(["self"] + ["arg%s" % (i + 1) for i in range(len(v))])))
            method_list.append(method % (k, ", ".join(["self", "*args"])))
        method_list_str = ("\r\n\r\n    ".join(method_list) if method_list else "pass") + "\r\n"

        plugins.write((template_player_str if entity_name == "Avatar" else template_proxy_str) %
                      dict(app="bots", cls_name=entity_name, plugin_name=plugin_name, method_list_str=method_list_str),
                      plugins.PLUGINS_PROXY_BOTS_DIR, "%s.py" % entity_name)
