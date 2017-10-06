import os
import sys
import re
import types
import importlib
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
    PLUGINS_DIR = os.path.join(COMMON_DIR, "plugins", "apps")
    PLUGINS_OUTER_DIR = os.path.join(os.path.dirname(HOME_DIR), "apps")

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

    @classmethod
    def get_module_list(cls, *path):
        return get_module_list(*path)

    @classmethod
    def init__sys_path(cls):
        sys.path = [cls.PLUGINS_OUTER_DIR, cls.PLUGINS_DIR] + sys.path
        sys.path = [cls.PLUGINS_PROXY_COMMON_DIR, cls.PLUGINS_PROXY_DIR] + sys.path
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
            if cls.app in ("base", "cell", "bots"):
                app_path = os.path.join(path, cls.app)
                if os.path.exists(app_path):
                    sys.path.append(app_path)

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
                pass

        settings = importlib.import_module("settings")
        for k, base_list in settings_dict.items():
            c = type(k, tuple(base_list), {})()
            c.collect_nodes()
            if isinstance(c, EqualizationMixin):
                c.init_equalization_format()
            setattr(settings, k, c)
        settings.get = lambda x: getattr(settings, x, None)

    @classmethod
    def init__entity(cls):

        def entity():
            def check(v):
                return 'A' <= v[0] <= 'Z'

            ret = OrderedDict()
            for m in cls.get_module_list(cls.HOME_DIR, cls.app):
                if check(m):
                    ret[m] = m
            for path in cls.apps.values():
                for m in cls.get_module_list(path, cls.app):
                    if m not in ret and check(m):
                        ret[m] = m
            return ret

        def avatar():
            def check(v):
                return 'A' <= v[0] <= 'Z'

            ret = OrderedDict()
            for name, path in cls.apps.items():
                for m in cls.get_module_list(path, cls.app, "avatar"):
                    if m not in ret and check(m):
                        ret[m] = "%s.%s.avatar.%s" % (name, cls.app, m)
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
            cls.entities[m] = c
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
            for a in s:
                g = getattr(c, a)
                if isinstance(g, AnyProperty) and g.get("defaultValue", cls.empty) is not cls.empty:
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

    @classmethod
    def init__user_type(cls):
        user_types = []
        for path in cls.apps.values():
            for m in cls.get_module_list(path):
                if m.upper() == m and m not in user_types:
                    user_types.append(m)
        for m in user_types:
            importlib.import_module(m)
        Type.finish_dict_type()

    @classmethod
    def init__charge(cls):
        for name in cls.apps:
            m = get_module("%s.interface" % name)
            if m:
                for k in dir(m):
                    f = getattr(m, k)
                    if isinstance(f, types.FunctionType) and k not in cls.interface_handle_map:
                        cls.interface_handle_map[k] = f

    @classmethod
    def onRequestCharge(cls, ordersID, entityDBID, data):
        handle = cls.interface_handle_map.get(data.pop("interface", None))
        if handle:
            handle(ordersID, entityDBID, data)

    @classmethod
    def init_bots(cls):
        assert cls.app == "bots"

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

    @classmethod
    def open_async(cls):
        assert cls.app not in ("base", "cell")
        settings = get_module("settings")
        AsyncHttp = get_module_attr("common.asyncHttp.AsyncHttp")
        asyncio_loop = get_module_attr("common.asyncio.asyncio_loop")

        def onAsyncHttpTick(timerID):
            AsyncHttp.run_frame()

        def onAsyncioTick(timerID):
            asyncio_loop.run_frame()

        gameTimeInterval = settings.Global.gameTimeInterval
        if cls.app == "bots":
            gameTimeInterval *= 2
        if settings.Global.enableAsyncHttp:
            KBEngine.addTimer(gameTimeInterval, gameTimeInterval, onAsyncHttpTick)
        if settings.Global.enableAsyncio:
            KBEngine.addTimer(gameTimeInterval, gameTimeInterval, onAsyncioTick)

    @classmethod
    def load_all_module(cls, module_name):
        d = {}
        for name in cls.apps:
            md = get_module_all("%s.%s" % (name, module_name))
            if "__ignore__" not in md:
                d.update(md)
        return d

    @classmethod
    def runtime(cls, entity):
        return cls.entities[entity.__name__]

    @classmethod
    def discover(cls):
        cls.init__sys_path()
        cls.init__settings()
        if cls.app in ("base", "cell", "bots"):
            cls.init__user_type()
        if cls.app in ("base", "cell"):
            cls.init__entity()
        if cls.app == "interface":
            cls.init__charge()
        cls.load_all_module("plugins.setup")
        Type.init_dict_types()
        plugins_completed.send(cls)
