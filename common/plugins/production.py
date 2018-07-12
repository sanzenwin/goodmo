import os
import sys
import re
import types
import importlib
import site
import KBEngine
from collections import OrderedDict
from common.utils import get_module_list, get_module_attr, get_module, get_module_all
from kbe.protocol import Type, Property, AnyProperty, Volatile, Base, Cell, Client
from plugins.conf import SettingsNode, EqualizationMixin
from plugins.conf.signals import plugins_completed

# import for hook
from common.asyncio import *
from kbe.log import *
from kbe.core import *


class Plugins:
    HOME_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    BASE_DIR = os.path.join(HOME_DIR, "base")
    CELL_DIR = os.path.join(HOME_DIR, "base")
    DEF_DIR = os.path.join(HOME_DIR, "entity_defs")
    COMMON_DIR = os.path.join(HOME_DIR, "common")
    PLUGINS_APPS_DIR = os.path.join(COMMON_DIR, "plugins", "apps")
    PLUGINS_OUTER_APPS_DIR = os.path.join(os.path.dirname(HOME_DIR), "apps")

    apps_path = site.getsitepackages() + [PLUGINS_OUTER_APPS_DIR, PLUGINS_APPS_DIR]

    uid = os.getenv("uid")
    r = re.compile("^[a-zA-Z_][a-zA-Z0-9_]*$")

    empty = object()

    apps = OrderedDict()

    app = dict(
        baseapp="base",
        cellapp="cell",
        interfaces="interface",
        bots="bots",
        loginapp="login"
    )[KBEngine.component]

    PLUGINS_PROXY_DIR = os.path.join(COMMON_DIR, "plugins", "proxy", app)
    PLUGINS_PROXY_COMMON_DIR = os.path.join(COMMON_DIR, "plugins", "proxy", "common")

    interface_handle_map = {}

    entities = {}

    user_types = OrderedDict()

    def get_module_list(self, *path):
        return get_module_list(*path)

    def get_cur_app_name(self, file):
        for p in self.apps_path:
            if p in file:
                f = file.replace(p, "")
                name = f.split(os.sep)[1]
                if name in self.apps:
                    return name

    def init__sys_path(self):
        sys.path = [self.PLUGINS_OUTER_APPS_DIR, self.PLUGINS_APPS_DIR] + sys.path
        settings = importlib.import_module("settings")
        for name in reversed(settings.installed_apps):
            for path in sys.path:
                dir_name = os.path.join(path, name)
                if os.path.isdir(dir_name):
                    self.apps[name] = dir_name
                    break
            else:
                assert False, "can not find the app [%s] by name" % name
        sys.path = [self.PLUGINS_PROXY_COMMON_DIR, self.PLUGINS_PROXY_DIR] + sys.path
        for name, path in self.apps.items():
            sys.path.append(path)
            if self.app in ("base", "cell", "bots"):
                app_path = os.path.join(path, self.app)
                if os.path.exists(app_path):
                    sys.path.append(app_path)

    def init__settings(self):
        settings_dict = {}
        for name in ["%s.settings" % name for name in self.apps] + ["plugins.conf.global_settings"]:
            try:
                settings = importlib.import_module(name)
                for k, v in settings.__dict__.items():
                    if isinstance(v, type) and issubclass(v, SettingsNode):
                        base_list = settings_dict.setdefault(k, [])
                        if v not in base_list:
                            base_list.append(v)
            except ImportError:
                pass

        settings = importlib.import_module("settings")
        for k, base_list in settings_dict.items():
            c = type(k, tuple(base_list), {})()
            c.collect_nodes()
            if isinstance(c, EqualizationMixin):
                c.init_equalization_format()
            setattr(settings, k, c)
        settings.get = lambda x: getattr(settings, x, None)

    def init__entity(self):

        def entity():
            def check(v):
                return 'A' <= v[0] <= 'Z'

            ret = OrderedDict()
            for m in self.get_module_list(self.HOME_DIR, self.app):
                if check(m):
                    ret[m] = m
            for path in self.apps.values():
                for m in self.get_module_list(path, self.app):
                    if m not in ret and check(m):
                        ret[m] = m
            return ret

        def avatar():
            def check(v):
                return 'A' <= v[0] <= 'Z'

            ret = OrderedDict()
            for name, path in self.apps.items():
                for m in self.get_module_list(path, self.app, "avatar"):
                    if m not in ret and check(m):
                        ret[m] = "%s.%s.avatar.%s" % (name, self.app, m)
            return ret

        m_entity_avatars = avatar()

        base_avatar_cls_list = []
        for m, v in m_entity_avatars.items():
            mm = importlib.import_module(v)
            avatar_cls = getattr(mm, m, None)
            if avatar_cls is None:
                continue
            if not issubclass(avatar_cls, tuple(base_avatar_cls_list)):
                base_avatar_cls_list.append(avatar_cls)

        if base_avatar_cls_list:
            try:
                avatar_module = importlib.import_module("Avatar")
                base_avatar_cls_list.append(avatar_module.Avatar)
                avatar_module.Avatar = type(avatar_module.Avatar.__name__, tuple(base_avatar_cls_list), {})
                req_list = set()
                for c in avatar_module.Avatar.mro():
                    for k, v in c.__dict__.items():
                        if isinstance(v, (Property, AnyProperty)) and v.get("Req"):
                            req_list.add(k)
                setattr(avatar_module.Avatar, "_reqReadyList", req_list)
            except ImportError:
                pass

        entities = entity()
        del_attr = dict()
        set_none = dict()
        properties = dict()
        for m, v in entities.items():
            mm = importlib.import_module(v)
            c = getattr(mm, m)
            self.entities[m] = c
            for cc in c.mro():
                for k, vv in cc.__dict__.items():
                    if isinstance(vv, (Property, AnyProperty, Volatile, Base, Cell, Client)):
                        d = del_attr.setdefault(cc, set())
                        d.add(k)
                        if isinstance(vv, (Property, AnyProperty)):
                            d = properties.setdefault(c, dict())
                            if k not in vv:
                                d[k] = vv
                        if isinstance(vv, (Base, Cell)):
                            d = set_none.setdefault(cc, dict())
                            for km, vm in vv.items():
                                if km not in d:
                                    d[km] = vm

        for c, s in del_attr.items():
            setattr(c, "__kbe_properties__", s)
            for a in s:
                g = getattr(c, a)
                if isinstance(g, AnyProperty) and g.get("defaultValue", self.empty) is not self.empty:
                    setattr(c, a, g["defaultValue"])
                else:
                    delattr(c, a)

        for c, d in set_none.items():
            for k, v in d.items():
                if v is None:
                    setattr(c, k, lambda *args: None)

        for c, p in properties.items():
            setattr(c, "properties", p)

        Type.finish_dict_type()

    def init__user_type(self):
        user_types = []
        for path in self.apps.values():
            for m in self.get_module_list(path):
                if m.upper() == m and m not in user_types:
                    user_types.append(m)
        for m in reversed(user_types):
            im = importlib.import_module(m)
            self.user_types[im.__name__] = im
        Type.finish_dict_type()

    def init__charge(self):
        for name in self.apps:
            m = get_module("%s.interface" % name)
            if m:
                for k in dir(m):
                    f = getattr(m, k)
                    if isinstance(f, types.FunctionType) and k not in self.interface_handle_map:
                        self.interface_handle_map[k] = f

    def onRequestCharge(self, ordersID, entityDBID, data):
        handle = self.interface_handle_map.get(data.pop("interface", None))
        if handle:
            handle(ordersID, entityDBID, data)

    def init_bots(self):
        assert self.app == "bots"

        class Tid(int):
            def __init__(self, *args, **kwargs):
                super().__init__(*args, **kwargs)
                self.tid = 0

            def __int__(self):
                return self.tid

        def addTimer(start, interval, callback):
            tidObj = Tid()

            def callback2():
                callback(tidObj)
                if interval > 0:
                    tidObj.tid = KBEngine.callback(interval, callback2)

            tidObj.tid = KBEngine.callback(start, callback2)
            return tidObj

        def delTimer(tidObj):
            KBEngine.cancelCallback(tidObj.tid)

        KBEngine.addTimer = addTimer
        KBEngine.delTimer = delTimer

    def open_async(self):
        assert self.app not in ("base", "cell")
        settings = get_module("settings")
        AsyncHttp = get_module_attr("common.asyncHttp.AsyncHttp")
        asyncio_loop = get_module_attr("common.asyncio.asyncio_loop")

        def onAsyncHttpTick(timerID):
            AsyncHttp.run_frame()

        def onAsyncioTick(timerID):
            asyncio_loop.run_frame()

        gameTimeInterval = settings.Global.gameTimeInterval
        if self.app == "bots":
            gameTimeInterval *= 2
        if settings.Global.enableAsyncHttp:
            KBEngine.addTimer(gameTimeInterval, gameTimeInterval, onAsyncHttpTick)
        if settings.Global.enableAsyncio:
            KBEngine.addTimer(gameTimeInterval, gameTimeInterval, onAsyncioTick)

    def load_all_module(self, module_name):
        d = {}
        for name in reversed(self.apps):
            md = get_module_all("%s.%s" % (name, module_name))
            if "__ignore__" not in md:
                d.update(md)
        return d

    def runtime(self, entity):
        return self.entities[entity.__name__]

    def find_user_type(self, name):
        for n in reversed(self.user_types):
            m = self.user_types[n]
            t = getattr(m, name, None)
            if t is not None:
                return t
        return None

    def discover(self):
        self.init__sys_path()
        self.init__settings()
        if self.app in ("base", "cell", "bots"):
            self.init__user_type()
        if self.app in ("base", "cell"):
            self.init__entity()
        if self.app == "interface":
            self.init__charge()
        self.load_all_module("plugins.setup")
        Type.init_dict_types()
        KBEngine.TAvatar = plugins.find_user_type("TAvatar")
        plugins_completed.send(self)


plugins = Plugins()

KBEngine.find_user_type = plugins.find_user_type
