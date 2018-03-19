import os
import sys
import re
import codecs
import pymysql
import KBEngine
from copy import deepcopy
from importlib import import_module
from collections import OrderedDict
from common.utils import get_module, get_module_list, get_module_attr, get_module_all
from kbe.protocol import Type, Property, Parent, Interfaces, Volatile, Properties, Client, Base, Cell, Entity, Entities
from plugins.conf import SettingsNode, EqualizationMixin
from plugins.conf.start_server import shell_maker
from plugins.conf.xml import config
from plugins.utils.excel.xlsx2py import xlsx2py
from .install_third_package import Plugins as Plugins_

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
        self.valid = plugins.add_entity(self)
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
        impl = Interfaces()

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
            return os.path.join(plugins.DEF_DIR, "%s.def" % self.entity.__name__)
        else:
            if self.is_avatar_base_cls():
                return os.path.join(plugins.DEF_DIR, "interfaces", "avatar", "%s.def" % self.entity.__name__)
            else:
                return os.path.join(plugins.DEF_DIR, "interfaces", "%s.def" % self.entity.__name__)

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
        dir_name = os.path.normpath(os.path.dirname(import_module(self.entity.__module__).__file__))
        for name, path in plugins.apps.items():
            if os.path.normpath(os.path.join(path, self.app, "avatar")) in dir_name:
                return True
        return False

    def _is_plugin_object(self):
        dir_name = os.path.normpath(os.path.dirname(import_module(self.entity.__module__).__file__))
        return os.path.normpath(plugins.BASE_DIR) not in dir_name


class ObjectOfBase(Object):
    app = "base"

    def base(self):
        v = self.entity.__dict__.get(self.app)
        return v if isinstance(v, Base) else Base()


class EntityOfBase(ObjectOfBase):
    types = (KBEngine.Entity, KBEngine.Proxy)
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


class Plugins(Plugins_):
    HOME_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    BOTS_DIR = os.path.join(HOME_DIR, "bots")
    BASE_DIR = os.path.join(HOME_DIR, "base")
    CELL_DIR = os.path.join(HOME_DIR, "cell")
    DATA_DIR = os.path.join(HOME_DIR, "data")
    SHELL_DIR = os.path.join(HOME_DIR, "shell")
    COMMON_DIR = os.path.join(HOME_DIR, "common")
    TELNET_DIR = os.path.join(SHELL_DIR, "telnet")
    DEF_DIR = os.path.join(HOME_DIR, "entity_defs")
    RES_DIR = os.path.join(os.path.dirname(HOME_DIR), "res")
    RES_KEY_DIR = os.path.join(RES_DIR, "key")
    RES_SERVER_DIR = os.path.join(RES_DIR, "server")
    RES_EXCEL_DIR = os.path.join(RES_DIR, "excel")
    EXCEL_DATA_DIR = os.path.join(DATA_DIR, "excel_data")

    PLUGINS_PROXY_BASE_DIR = os.path.join(COMMON_DIR, "plugins", "proxy", "base")
    PLUGINS_PROXY_CELL_DIR = os.path.join(COMMON_DIR, "plugins", "proxy", "cell")
    PLUGINS_PROXY_BOTS_DIR = os.path.join(COMMON_DIR, "plugins", "proxy", "bots")

    uid = os.getenv("uid")
    public_key = None
    r = re.compile("^[a-zA-Z_][a-zA-Z0-9_]*$")

    m_entities = OrderedDict()
    m_entity_avatars = OrderedDict()
    m_entity_plugins = dict(base={}, cell={})

    m_entity_client_methods = dict()

    m_user_types_modules = list()

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

    def __init__(self):
        super().__init__()
        self.xml_config = None

    def add_entity(self, entity):
        maps = self.entities[entity.__class__]
        maps = maps.setdefault(entity.entity_name, {})
        if entity.entity.__name__ in maps:
            if str(entity.entity) != str(maps[entity.entity.__name__].entity):
                print("warring :: %s is covered by %s" % (entity.entity, maps[entity.entity.__name__].entity))
            return False
        maps[entity.entity.__name__] = entity
        return True

    def get_module_list(self, *path):
        return get_module_list(*path)

    def init_entity(self, app):
        def entity(ret2):
            def check(v):
                return 'A' <= v[0] <= 'Z'

            ret = OrderedDict()
            for m in self.get_module_list(self.HOME_DIR, app):
                if check(m):
                    ret[m] = m
            for name, path in self.apps.items():
                for m in self.get_module_list(path, app):
                    if m not in ret and check(m):
                        ret[m] = m
                        ret2[app][m] = name
            return ret

        def avatar():
            def check(v):
                return 'A' <= v[0] <= 'Z'

            ret = OrderedDict()
            for name, path in self.apps.items():
                for m in self.get_module_list(path, app, "avatar"):
                    if m not in ret and check(m):
                        ret[m] = "%s.%s.avatar.%s" % (name, app, m)
            return ret

        self.m_entities = entity(self.m_entity_plugins)
        self.m_entity_avatars = avatar()

        base_avatar_cls_list = []
        for m, v in self.m_entity_avatars.items():
            mm = import_module(v)
            avatar_cls = getattr(mm, m, None)
            if avatar_cls is None:
                print("warring :: module[{0}] has no class named [{0}]".format(m))
                continue
            if not issubclass(avatar_cls, tuple(base_avatar_cls_list)):
                base_avatar_cls_list.append(avatar_cls)

        if base_avatar_cls_list:
            try:
                avatar_module = import_module("Avatar")
                base_avatar_cls_list.append(avatar_module.Avatar)
                avatar_module.Avatar = type(avatar_module.Avatar.__name__, tuple(base_avatar_cls_list), {})
            except ImportError:
                pass

        entity_cls = dict(base=EntityOfBase, cell=EntityOfCell)[app]
        for m, v in self.m_entities.items():
            mm = import_module(v)
            c = getattr(mm, m)
            entity_cls(c)
            self.init_clients(c)

    def switch_to_cell(self):
        if self.BASE_DIR in sys.path:
            index = sys.path.index(self.BASE_DIR)
            sys.path[index] = self.CELL_DIR

        for path in self.apps.values():
            path = os.path.join(path, "base")
            if path in sys.path:
                sys.path.remove(path)

        for path in self.apps.values():
            path = os.path.join(path, "cell")
            sys.path.append(path)

        for m in self.m_entity_avatars.values():
            sys.modules.pop(m)
        for m in self.m_entities.values():
            sys.modules.pop(m)

    def switch_to_base(self):
        if self.CELL_DIR in sys.path:
            index = sys.path.index(self.CELL_DIR)
            sys.path[index] = self.BASE_DIR

        for path in self.apps.values():
            path = os.path.join(path, "cell")
            if path in sys.path:
                sys.path.remove(path)

        for path in self.apps.values():
            path = os.path.join(path, "base")
            sys.path.append(path)

        for m in self.m_entity_avatars.values():
            sys.modules.pop(m)
        for m in self.m_entities.values():
            sys.modules.pop(m)

    def clear_dir(self):
        self.clear(self.DEF_DIR)
        self.clear(self.DATA_DIR, True)
        self.clear(self.TELNET_DIR)
        self.clear(self.PLUGINS_PROXY_BASE_DIR)
        self.clear(self.PLUGINS_PROXY_CELL_DIR)
        self.clear(self.PLUGINS_PROXY_COMMON_DIR, True)
        self.clear(self.PLUGINS_PROXY_BOTS_DIR)

    def read(self, *path):
        filename = os.path.join(*path)
        with codecs.open(filename, 'r', 'utf-8') as f:
            return f.read()

    def get_app_path(self, name):
        path = os.path.join(self.PLUGINS_OUTER_DIR, name)
        if os.path.exists(path):
            return path
        return os.path.join(self.PLUGINS_DIR, name)

    def init__settings(self):
        settings_dict = {}
        for name in ["%s.settings" % name for name in self.apps] + ["plugins.conf.global_settings"]:
            try:
                settings = import_module(name)
                for k, v in settings.__dict__.items():
                    if isinstance(v, type) and issubclass(v, SettingsNode):
                        base_list = settings_dict.setdefault(k, [])
                        if v not in base_list:
                            base_list.append(v)
            except ImportError:
                print("import warring: %s is not found" % name)

        settings = import_module("settings")
        for k, base_list in settings_dict.items():
            c = type(k, tuple(base_list), {})()
            c.collect_nodes()
            if isinstance(c, EqualizationMixin):
                c.init_equalization_format()
            setattr(settings, k, c)

    def init__user_type(self):
        user_types = []
        for path in self.apps.values():
            for m in self.get_module_list(path):
                if m.upper() == m and m not in user_types:
                    user_types.append(m)
        for m in user_types:
            self.m_user_types_modules.append(import_module(m))

    def init__entity(self):
        self.init_entity("base")
        self.switch_to_cell()
        self.init_entity("cell")
        self.switch_to_base()
        self.init_entity("base")

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
            self.write(s, entity_base.def_file_path())

        for k, v in self.entities[ObjectOfBase].items():
            for k2, v2 in v.items():
                v2c = self.entities[ObjectOfCell].get(k, {}).get(k2)
                print(v2.entity)
                handle(v2, v2c)

        entities = Entities()
        for k, v in self.entities[EntityOfBase].items():
            for k2, v2 in v.items():
                v2c = self.entities[EntityOfCell].get(k, {}).get(k2)
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
        self.write(entities.str(), self.HOME_DIR, "entities.xml")

        for k in self.m_entity_plugins["base"].keys():
            self.write(
                self.template_proxy_str % dict(app="base", cls_name=k, plugin_name=self.m_entity_plugins["base"][k]),
                self.PLUGINS_PROXY_BASE_DIR, k + ".py")
        for k in self.m_entity_plugins["cell"].keys():
            self.write(
                self.template_proxy_str % dict(app="cell", cls_name=k, plugin_name=self.m_entity_plugins["cell"][k]),
                self.PLUGINS_PROXY_CELL_DIR, k + ".py")

        Type.finish_dict_type()
        self.write(Type.str(), self.DEF_DIR, 'types.xml')

    def init_clients(self, entity_class):
        dct = self.m_entity_client_methods.setdefault(entity_class.__name__, OrderedDict())
        for c in entity_class.mro():
            client = c.__dict__.get("client", {})
            if isinstance(client, Client):
                for k in sorted(client):
                    dct[k] = client[k]

    def init__apps_setup(self):
        # class Proxy(types.ModuleType):
        #     def __getattr__(self, item):
        #         return None
        #
        # all_proxy_modules = []
        #
        # for name in self.apps:
        #     proxy_modules = get_module_attr("%s.plugins.__proxy_modules__" % name, [])
        #     for modules in proxy_modules:
        #         modules = modules.split(".")
        #         for i in range(len(modules)):
        #             m = ".".join(modules[:i + 1])
        #             if m not in sys.modules:
        #                 sys.modules[m] = Proxy(m)
        #                 all_proxy_modules.append(m)

        self.run_plugins("setup")

        # for m in all_proxy_modules:
        #     sys.modules.pop(m)
        #     try:
        #         mm = import_module(m)
        #     except ImportError as e:
        #         print(e.args[0])
        #         continue
        #     else:
        #         reload(mm)

    def init__apps_run(self):
        self.run_plugins("run")

    def init__apps_completed(self):
        self.run_plugins("completed")

    def init__rsa(self):
        crypto = get_module("oscrypto.asymmetric")
        public_key, private_key = crypto.generate_pair("rsa", 1024)
        self.public_key = public_key
        self.write(crypto.dump_private_key(private_key, None).decode("utf-8"), self.RES_KEY_DIR, "kbengine_private.key")
        self.write(crypto.dump_public_key(public_key).decode("utf-8"), self.RES_KEY_DIR, "kbengine_public.key")

    def init__xml_config(self):
        settings = import_module("settings")
        xml = get_module_attr("kbe.xml.Xml")
        client = get_module_attr("pymongo.MongoClient")
        data = dict()
        data_default = dict()
        for name in reversed(self.apps):
            d = get_module_attr("%s.__kbengine_xml__" % name, dict())
            d_default = get_module_attr("%s.__kbengine_xml_default__" % name, dict())
            data = config.update_recursive(data, d)
            data_default = config.update_recursive(data_default, d_default)
        default = config.get_default_with_telnet(deepcopy(data_default), settings.Global.telnetOnePassword)
        data = config.update_recursive(data, default)
        data = config.update_recursive(data, config.get_default_data())
        db_name = "goodmo__%s" % self.uid
        if "uri" in settings.Global.kbengine_xml_mongodb:
            c = dict(host=settings.Global.kbengine_xml_mongodb["uri"])
        else:
            c = dict(authSource=db_name, **settings.Global.kbengine_xml_mongodb)
        db = client(**c)[db_name]
        collection = db.kbengine_xml
        try:
            d = collection.find({}, dict(_id=False)).next()
        except StopIteration:
            collection.save(deepcopy(data_default))
            d = dict()
        data = config.update_recursive(data, d)
        data = config.final(data, lambda x: x)
        self.xml_config = data
        s = xml.dict2xml(data)
        self.write(s, self.RES_SERVER_DIR, "kbengine.xml")

    def init__database(self):
        for _, database in self.xml_config["dbmgr"]["databaseInterfaces"].items():
            try:
                conn = pymysql.connect(host=database["host"],
                                       port=database["port"],
                                       user=database["auth"]["username"],
                                       passwd=database["auth"]["password"],
                                       db=database["databaseName"],
                                       charset='utf8')
            except pymysql.err.InternalError:
                pass
            else:
                cursor = conn.cursor()
                cursor.execute("delete from kbe_entitylog")
                conn.commit()
                cursor.close()
                conn.close()

    def init__shell(self):
        settings = import_module("settings")
        bc = settings.BaseApp.equalizationBaseappAmount + len(settings.BaseApp.multi["baseappIndependence"].dict)
        base = dict(
            machine=1,
            logger=1,
            interfaces=1,
            dbmgr=1,
            baseappmgr=1,
            cellappmgr=1,
            loginapp=1,
            baseapp=bc
        )
        bots = dict(bots=1)
        self.write(shell_maker.apps_shell(base, True, True), self.SHELL_DIR, "start_server.cmd")
        self.write(shell_maker.apps_shell(base, True, False), self.SHELL_DIR, "start_server.sh")
        self.write(shell_maker.apps_shell(bots, False, True), self.SHELL_DIR, "start_bots.cmd")
        self.write(shell_maker.apps_shell(bots, False, False), self.SHELL_DIR, "start_bots.sh")

        telnet = dict(
            bots=1,
            logger=1,
            interfaces=1,
            dbmgr=1,
            loginapp=1,
            baseapp=bc,
            cellapp=1
        )
        internal_ip_address = get_module_attr("kbe.utils.internal_ip_address")
        for app, count in telnet.items():
            data = dict(
                ip=internal_ip_address(),
                port=self.xml_config[app]["telnet_service"]["port"],
                password=self.xml_config[app]["telnet_service"]["password"]
            )
            port = data["port"]
            for i in range(count):
                data["port"] = port + i
                self.write(shell_maker.app_telnet_shell(data, True), self.TELNET_DIR,
                           "%s%s.%s" % (app, "" if i == 0 else i, "cmd"))
                self.write(shell_maker.app_telnet_shell(data, False), self.TELNET_DIR,
                           "%s%s.%s" % (app, "" if i == 0 else i, "sh"))

    def run_plugins(self, method):
        for name in reversed(self.apps):
            entry = get_module_attr("%s.plugins.%s" % (name, method))
            if entry:
                entry(self, name)

    def load_all_module(self, module_name):
        d = {}
        for name in reversed(self.apps):
            md = get_module_all("%s.%s" % (name, module_name))
            if "__ignore__" not in md:
                d.update(md)
        return d

    def get_res(self, app_name, res_type, path_or_filename):
        path_list = os.path.split(path_or_filename)
        real_path = os.path.join(self.RES_DIR, res_type, app_name, *path_list)
        if os.path.exists(real_path):
            return real_path
        for name in self.apps:
            app_path = self.get_app_path(name)
            real_path = os.path.join(app_path, "res", res_type, app_name, *path_list)
            if os.path.exists(real_path):
                return real_path
        return None

    def export_excel(self, app_name_or_list, *module_list):
        if not isinstance(app_name_or_list, (list, tuple)):
            app_name_or_list = [app_name_or_list]
        for app_name in app_name_or_list:
            for module_name in module_list:
                path = self.get_res(app_name, "excel", "%s.xlsx" % module_name)
                if path is not None:
                    xlsx2py(path, os.path.join(self.EXCEL_DATA_DIR, app_name, "%s.py" % module_name)).run()

    def discover(self):
        self.clear_dir()
        self.init__sys_path()
        self.init__apps_setup()
        self.init__settings()
        self.init__apps_run()
        self.init__user_type()
        self.init__entity()
        self.init__apps_completed()
        self.init__rsa()
        self.init__xml_config()
        self.init__database()
        self.init__shell()
        self.completed()


plugins = Plugins()
