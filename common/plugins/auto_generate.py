import os
import sys
import re
import importlib
import codecs
import shutil
import KBEngine
import kbe.log
from collections import OrderedDict
from common.utils import get_module_list, load_module_attr
from kbe.protocol import Type, Property, Parent, Implements, Volatile, Properties, Client, Base, Cell, Entity, Entities
from plugins.conf import SettingsNode, EqualizationMixin

for i in range(len(sys.path)):
    sys.path[i] = os.path.normpath(sys.path[i])

KBEngine.Entity = type("Entity", (object,), {})


class Object:
    types = (object,)
    is_entity = False
    app = ""

    union_set = set()

    @classmethod
    def check_type(cls, c):
        if c in cls.types:
            return None
        if not cls.has_kbe_element(c):
            return None
        if issubclass(c, cls.types):
            return cls
        return cls.__base__

    @staticmethod
    def has_kbe_element(c):
        for m in c.mro():
            for v in m.__dict__.values():
                if isinstance(v, (Property, Volatile, Base, Cell, Client)):
                    return True
        return False

    def __init__(self, entity, entity_name=None):
        self.entity_name = entity.__name__ if entity_name is None else entity_name
        self.entity = entity
        self.bases = []
        self.plugin = self._is_plugin_object()
        self.valid = Plugins.add_entity(self)
        self.generate_bases()

    def generate_bases(self):
        for c in self.entity.__bases__:
            init = self.check_type(c)
            if init:
                self.bases.append(init(c, self.entity_name))
        if not self.is_entity:
            self.interface_union()
        for c in self.bases:
            if c.is_entity and not c.valid:
                self.entity_union(self, c)

    def entity_union(self, obj, obj2):
        rr1, rr2, rr3, rr4 = obj.client(), obj.base(), obj.cell(), obj.properties()
        rr1 += obj2.client()
        rr2 += obj2.base()
        rr3 += obj2.cell()
        rr4 += obj2.properties()
        if rr1:
            obj.entity.client = rr1
        if rr2:
            obj.entity.base = rr2
        if rr3:
            obj.entity.cell = rr3
        if rr4:
            for k, v in rr4.items():
                setattr(obj.entity, k, v)

    def interface_union(self):

        def travel(obj):
            client, base, cell, props = obj.client(), obj.base(), obj.cell(), obj.properties()
            for c in obj.bases:
                if c.entity in self.union_set:
                    continue
                r1, r2, r3, r4 = travel(c)
                client += r1
                base += r2
                cell += r3
                props += r4
                self.union_set.add(c.entity)
            return client, base, cell, props

        rr1, rr2, rr3, rr4 = travel(self)
        if rr1:
            self.entity.client = rr1
        if rr2:
            self.entity.base = rr2
        if rr3:
            self.entity.cell = rr3
        if rr4:
            for k, v in rr4.items():
                setattr(self.entity, k, v)

    def volatile(self):
        return Volatile()

    def properties(self):
        properties = {}
        for k, v in self.entity.__dict__.items():
            if isinstance(v, Property):
                properties[k] = v
        return Properties(**properties)

    def client(self):
        v = self.entity.__dict__.get("client")
        return v if isinstance(v, Client) else Client()

    def base(self):
        return Base()

    def cell(self):
        return Cell()

    def parent(self):
        return Parent()

    def implements(self):
        impl = Implements()

        def travel(obj):
            for c in obj.bases:
                if c.is_entity:
                    if not c.valid:
                        travel(c)
                else:
                    if c.valid and not c.is_entity:
                        impl.append(c.implement_path())

        if self.is_entity:
            travel(self)
            impl.reverse()
        return impl

    def def_file_path(self):
        assert self.valid, "def_file_path: %s should be valid" % self.entity
        if self.is_entity:
            return os.path.join(Plugins.DEF_DIR, "%s.def" % self.entity.__name__)
        else:
            if self.is_avatar_base_cls():
                return os.path.join(Plugins.DEF_DIR, "interfaces", "avatar", "%s.def" % self.entity.__name__)
            else:
                return os.path.join(Plugins.DEF_DIR, "interfaces", "%s.def" % self.entity.__name__)

    def implement_path(self):
        assert self.valid, "implement_path: %s should be valid" % self.entity
        assert not self.is_entity, "implement_path: %s should be implement" % self.entity
        if self.is_avatar_base_cls():
            return os.path.join("avatar", self.entity.__name__)
        else:
            return os.path.join(self.entity.__name__)

    def is_avatar_base_cls(self):
        if self.entity_name != "Avatar":
            return False
        dir_name = os.path.normpath(os.path.dirname(importlib.import_module(self.entity.__module__).__file__))
        for name, path in Plugins.apps.items():
            if os.path.normpath(os.path.join(path, self.app, "avatar")) in dir_name:
                return True
        return False

    def _is_plugin_object(self):
        dir_name = os.path.normpath(os.path.dirname(importlib.import_module(self.entity.__module__).__file__))
        return os.path.normpath(Plugins.BASE_DIR) not in dir_name


class ObjectOfBase(Object):
    app = "base"

    def base(self):
        v = self.entity.__dict__.get(self.app)
        return v if isinstance(v, Base) else Base()


class EntityOfBase(ObjectOfBase):
    types = (KBEngine.Base, KBEngine.Proxy)
    is_entity = True

    def parent(self):
        for c in self.bases:
            if issubclass(c.entity, self.types) and c.valid:
                return Parent(c.entity.__name__)
        return Parent()


class ObjectOfCell(Object):
    app = "cell"

    def cell(self):
        v = self.entity.__dict__.get(self.app)
        return v if isinstance(v, Cell) else Cell()


class EntityOfCell(ObjectOfCell):
    types = (KBEngine.Entity,)
    is_entity = True

    def parent(self):
        for c in self.bases:
            if issubclass(c.entity, self.types) and c.valid:
                return Parent(c.__name__)
        return Parent()

    def volatile(self):
        v = getattr(self.entity, "volatile")
        if isinstance(v, Volatile):
            return v
        return Volatile()


class Plugins:
    HOME_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    BOTS_DIR = os.path.join(HOME_DIR, "bots")
    BASE_DIR = os.path.join(HOME_DIR, "base")
    CELL_DIR = os.path.join(HOME_DIR, "cell")
    DATA_DIR = os.path.join(HOME_DIR, "data")
    DEF_DIR = os.path.join(HOME_DIR, "entity_defs")
    COMMON_DIR = os.path.join(HOME_DIR, "common")
    RES_DIR = os.path.join(os.path.dirname(HOME_DIR), "res")
    EXCEL_DIR = os.path.join(RES_DIR, "excel")
    EXCEL_DATA_DIR = os.path.join(DATA_DIR, "excel_data")
    PLUGINS_DIR = os.path.join(COMMON_DIR, "plugins", "apps")
    PLUGINS_OUTER_DIR = os.path.join(os.path.dirname(HOME_DIR), "apps")

    PLUGINS_PROXY_BASE_DIR = os.path.join(COMMON_DIR, "plugins", "proxy", "base")
    PLUGINS_PROXY_CELL_DIR = os.path.join(COMMON_DIR, "plugins", "proxy", "cell")
    PLUGINS_PROXY_BOTS_DIR = os.path.join(COMMON_DIR, "plugins", "proxy", "bots")
    PLUGINS_PROXY_COMMON_DIR = os.path.join(COMMON_DIR, "plugins", "proxy", "common")

    r = re.compile("^[a-zA-Z_][a-zA-Z0-9_]*$")
    apps = OrderedDict()

    m_entities = OrderedDict()
    m_entity_avatars = OrderedDict()
    m_entity_plugins = dict(base={}, cell={})

    m_entity_client_methods = dict()

    entities = {
        ObjectOfBase: {},
        EntityOfBase: {},
        ObjectOfCell: {},
        EntityOfCell: {}
    }

    template_proxy_str = """from %(plugin_name)s.%(app)s.%(cls_name)s import *
from %(plugin_name)s.%(app)s.%(cls_name)s import %(cls_name)s as %(cls_name)sBase\n\n
class %(cls_name)s(%(cls_name)sBase):
    pass
"""

    @classmethod
    def add_entity(cls, entity):
        maps = cls.entities[entity.__class__]
        maps = maps.setdefault(entity.entity_name, {})
        if entity.entity.__name__ in maps:
            if str(entity.entity) != str(maps[entity.entity.__name__].entity):
                print("warring :: %s is covered by %s" % (entity.entity, maps[entity.entity.__name__].entity))
            return False
        maps[entity.entity.__name__] = entity
        return True

    @classmethod
    def get_module_list(cls, *path):
        return get_module_list(*path)

    @classmethod
    def init_entity(cls, app):
        def entity(ret2):
            def check(v):
                return 'A' <= v[0] <= 'Z'

            ret = OrderedDict()
            for m in cls.get_module_list(cls.HOME_DIR, app):
                if check(m):
                    ret[m] = m
            for name, path in cls.apps.items():
                for m in cls.get_module_list(path, app):
                    if m not in ret and check(m):
                        ret[m] = m
                        ret2[app][m] = name
            return ret

        def avatar():
            def check(v):
                return 'A' <= v[0] <= 'Z'

            ret = OrderedDict()
            for name, path in cls.apps.items():
                for m in cls.get_module_list(path, app, "avatar"):
                    if m not in ret and check(m):
                        ret[m] = "%s.%s.avatar.%s" % (name, app, m)
            return ret

        cls.m_entities = entity(cls.m_entity_plugins)
        cls.m_entity_avatars = avatar()

        base_avatar_cls_list = []
        for m, v in cls.m_entity_avatars.items():
            module = importlib.import_module(v)
            avatar_cls = getattr(module, m, None)
            if avatar_cls is None:
                print("warring :: module[{0}] has no class named [{0}]".format(m))
                continue
            if not issubclass(avatar_cls, tuple(base_avatar_cls_list)):
                base_avatar_cls_list.append(avatar_cls)

        if base_avatar_cls_list:
            try:
                avatar_module = importlib.import_module("Avatar")
                base_avatar_cls_list.append(avatar_module.Avatar)
                avatar_module.Avatar = type(avatar_module.Avatar.__name__, tuple(base_avatar_cls_list), {})
            except ImportError:
                pass

        entity_cls = dict(base=EntityOfBase, cell=EntityOfCell)[app]
        for m, v in cls.m_entities.items():
            module = importlib.import_module(v)
            c = getattr(module, m)
            entity_cls(c)
            cls.init_clients(c)

    @classmethod
    def switch_to_cell(cls):
        if cls.BASE_DIR in sys.path:
            index = sys.path.index(cls.BASE_DIR)
            sys.path[index] = cls.CELL_DIR

        for path in cls.apps.values():
            path = os.path.join(path, "base")
            if path in sys.path:
                sys.path.remove(path)

        for path in cls.apps.values():
            path = os.path.join(path, "cell")
            sys.path.append(path)

        for m in cls.m_entity_avatars.values():
            sys.modules.pop(m)
        for m in cls.m_entities.values():
            sys.modules.pop(m)

    @classmethod
    def switch_to_base(cls):
        if cls.CELL_DIR in sys.path:
            index = sys.path.index(cls.CELL_DIR)
            sys.path[index] = cls.BASE_DIR

        for path in cls.apps.values():
            path = os.path.join(path, "cell")
            if path in sys.path:
                sys.path.remove(path)

        for path in cls.apps.values():
            path = os.path.join(path, "base")
            sys.path.append(path)

        for m in cls.m_entity_avatars.values():
            sys.modules.pop(m)
        for m in cls.m_entities.values():
            sys.modules.pop(m)

    @classmethod
    def clear_dir(cls):
        cls.clear(cls.DEF_DIR)
        cls.clear(cls.DATA_DIR)
        cls.clear(cls.PLUGINS_PROXY_BASE_DIR)
        cls.clear(cls.PLUGINS_PROXY_CELL_DIR)
        cls.clear(cls.PLUGINS_PROXY_COMMON_DIR, True)
        cls.clear(cls.PLUGINS_PROXY_BOTS_DIR)

    @classmethod
    def clear(cls, dir_name, need_keep=False):
        if os.path.isdir(dir_name):
            shutil.rmtree(dir_name)
        os.makedirs(dir_name)
        if need_keep:
            cls.write("", dir_name, ".gitkeep")

    @classmethod
    def write(cls, s, *path):
        filename = os.path.join(*path)
        dir_name = os.path.dirname(filename)
        if not os.path.isdir(dir_name):
            os.makedirs(dir_name)
        mode = "w" if os.path.isfile(filename) else "x"
        with codecs.open(filename, mode, 'utf-8') as f:
            f.write(s)
            f.close()

    @classmethod
    def read(cls, *path):
        filename = os.path.join(*path)
        with codecs.open(filename, 'r', 'utf-8') as f:
            return f.read()

    @classmethod
    def get_app_path(cls, name):
        path = os.path.join(cls.PLUGINS_OUTER_DIR, name)
        if os.path.exists(path):
            return path
        return os.path.join(cls.PLUGINS_DIR, name)

    @classmethod
    def init__sys_path(cls):
        sys.path = [cls.PLUGINS_OUTER_DIR, cls.PLUGINS_DIR] + sys.path
        sys.path = [cls.PLUGINS_PROXY_COMMON_DIR] + sys.path
        settings = importlib.import_module("settings")
        for name in reversed(settings.install_apps):
            for path in sys.path:
                dir_name = os.path.join(path, name)
                if os.path.isdir(dir_name):
                    cls.apps[name] = dir_name
                    break
            else:
                assert False, "can not find the app [%s] by name" % name
        for name, path in cls.apps.items():
            sys.path.append(path)
            sys.path.append(os.path.join(path, "base"))
            sys.path.append(os.path.join(path, "plugins"))

    @classmethod
    def init__settings(cls):
        settings_dict = {}
        for name in ["%s.settings" % name for name in cls.apps] + ["plugins.conf.global_settings"]:
            try:
                settings = importlib.import_module(name)
                for k, v in settings.__dict__.items():
                    if isinstance(v, type) and issubclass(v, SettingsNode):
                        base_list = settings_dict.setdefault(k, [])
                        if v not in base_list:
                            base_list.append(v)
            except ImportError:
                print("import warring: %s is not found" % name)

        settings = importlib.import_module("settings")
        for k, base_list in settings_dict.items():
            c = type(k, tuple(base_list), {})()
            c.collect_nodes()
            if isinstance(c, EqualizationMixin):
                c.init_equalization_format()
            setattr(settings, k, c)

    @classmethod
    def init__user_type(cls):
        user_types = []
        for path in cls.apps.values():
            for m in cls.get_module_list(path):
                if m.upper() == m and m not in user_types:
                    user_types.append(m)
        for m in user_types:
            importlib.import_module(m)

    @classmethod
    def init__entity(cls):
        cls.init_entity("base")
        cls.switch_to_cell()
        cls.init_entity("cell")
        cls.switch_to_base()
        cls.init_entity("base")

        def handle(entity_base, entity_cell):
            parent = entity_base.parent()
            volatile = entity_base.volatile()
            properties = entity_base.properties()
            implements = entity_base.implements()
            base = entity_base.base()
            cell = Cell()
            client = entity_base.client()
            if entity_cell:
                assert parent == entity_cell.parent()
                volatile = entity_cell.volatile()
                properties += entity_cell.properties()
                assert implements == entity_cell.implements()
                cell = entity_cell.cell()
                client += entity_cell.client()
            s = Entity(
                parent=parent.str(),
                volatile=volatile.str(),
                implements=implements.str(),
                properties=properties.str(),
                base=base.str(),
                cell=cell.str(),
                client=client.str()
            ).str()
            cls.write(s, entity_base.def_file_path())

        for k, v in cls.entities[ObjectOfBase].items():
            for k2, v2 in v.items():
                v2c = cls.entities[ObjectOfCell].get(k, {}).get(k2)
                print(v2.entity)
                handle(v2, v2c)

        entities = Entities()
        for k, v in cls.entities[EntityOfBase].items():
            for k2, v2 in v.items():
                v2c = cls.entities[EntityOfCell].get(k, {}).get(k2)
                print(v2.entity)
                handle(v2, v2c)
                has_client = issubclass(v2.entity, KBEngine.Proxy) or (v2c and hasattr(v2c.entity, "client"))
                info = dict(
                    key=("A" if v2.entity_name == "Equalization" else "") + ("B" if v2.plugin else "A") + (
                        "A" if has_client else "B") + v2.entity_name,
                    name=v2.entity_name,
                    hasCell=bool(v2c),
                    hasBase=True,
                    hasClient=has_client
                )
                entities.append(info)
        cls.write(entities.str(), cls.HOME_DIR, "entities.xml")

        for k in cls.m_entity_plugins["base"].keys():
            cls.write(
                cls.template_proxy_str % dict(app="base", cls_name=k, plugin_name=cls.m_entity_plugins["base"][k]),
                cls.PLUGINS_PROXY_BASE_DIR, k + ".py")
        for k in cls.m_entity_plugins["cell"].keys():
            cls.write(
                cls.template_proxy_str % dict(app="cell", cls_name=k, plugin_name=cls.m_entity_plugins["cell"][k]),
                cls.PLUGINS_PROXY_CELL_DIR, k + ".py")

        Type.finish_dict_type()
        cls.write(Type.str(), cls.DEF_DIR, 'alias.xml')

    @classmethod
    def init_clients(cls, entity_class):
        dct = cls.m_entity_client_methods.setdefault(entity_class.__name__, OrderedDict())
        for c in entity_class.mro():
            client = c.__dict__.get("client", {})
            if isinstance(client, Client):
                for k in sorted(client):
                    dct[k] = client[k]

    @classmethod
    def init__apps_setup(cls):
        class Proxy:
            def __getattr__(self, item):
                return None

        all_proxy_modules = []

        for name in cls.apps:
            proxy_modules = load_module_attr("%s.plugins.__proxy_modules__" % name, [])
            for modules in proxy_modules:
                modules = modules.split(".")
                for i in range(len(modules)):
                    m = ".".join(modules[:i + 1])
                    if m not in sys.modules:
                        sys.modules[m] = Proxy()
                        all_proxy_modules.append(m)

        cls.run_plugins("setup")

        for m in all_proxy_modules:
            sys.modules.pop(m)

    @classmethod
    def init__apps_run(cls):
        cls.run_plugins("run")

    @classmethod
    def init__apps_completed(cls):
        cls.run_plugins("completed")

    @classmethod
    def run_plugins(cls, method):
        for name in cls.apps:
            entry = load_module_attr("%s.plugins.%s" % (name, method))
            if entry:
                entry(cls, name)

    @classmethod
    def discover(cls):
        cls.clear_dir()
        cls.init__sys_path()
        cls.init__apps_setup()
        cls.init__settings()
        cls.init__apps_run()
        cls.init__user_type()
        cls.init__entity()
        cls.init__apps_completed()
        print("""==============\n""")
        print("""plugins completed!!""")
