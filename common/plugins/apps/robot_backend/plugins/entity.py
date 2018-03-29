from kbe.protocol import BaseMethod


def def_entity(plugins, entity_base, entity_cell, parent, volatile, implements, properties, base, cell, client):
    if entity_base.entity_name == "Avatar":
        for k, v in client.items():
            base["ClientProxy__%s" % k] = BaseMethod(*v)


def base_content(plugins, entity_name):
    if entity_name != "Avatar":
        return None
    template_str = """\
    def ClientProxy__%(method)s(self, *args):
        proxy = getattr(self.robotBackendProxy, '%(method)s', None)
        if proxy:
            self.runInNextFrame(partial(proxy, *args))"""
    d = plugins.m_entity_client_methods[entity_name]
    str_list = []
    for method in d:
        str_list.append(template_str % dict(method=method))
    return "from functools import partial", "\n\n".join(str_list)
