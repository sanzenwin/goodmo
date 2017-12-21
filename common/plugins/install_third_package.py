import os
import sys
import time
import codecs
import shutil
import kbe.log
from collections import OrderedDict
from importlib import import_module
from common.utils import get_module_attr


class Plugins:
    HOME_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    THIRD_PACKAGE_DIR = os.path.join(os.path.dirname(os.path.dirname(HOME_DIR)), "kbe", "res", "scripts", "common",
                                     "Lib", "site-packages")
    COMMON_DIR = os.path.join(HOME_DIR, "common")
    PLUGINS_DIR = os.path.join(COMMON_DIR, "plugins", "apps")
    PLUGINS_OUTER_DIR = os.path.join(os.path.dirname(HOME_DIR), "apps")
    PLUGINS_PROXY_COMMON_DIR = os.path.join(COMMON_DIR, "plugins", "proxy", "common")

    apps = OrderedDict()

    app_component = dict(
        baseapp="base",
        cellapp="cell",
        interfaces="interface",
        bots="bots",
        loginapp="login"
    )

    def init__sys_path(self):
        sys.path = [self.PLUGINS_OUTER_DIR, self.PLUGINS_DIR] + sys.path
        sys.path = [self.PLUGINS_PROXY_COMMON_DIR] + sys.path
        settings = import_module("settings")
        for name in reversed(settings.install_apps):
            for path in sys.path:
                dir_name = os.path.join(path, name)
                if os.path.isdir(dir_name):
                    self.apps[name] = dir_name
                    break
            else:
                assert False, "can not find the app [%s] by name" % name
        for name, path in self.apps.items():
            sys.path.append(path)
            sys.path.append(os.path.join(path, "base"))
            sys.path.append(os.path.join(path, "plugins"))

    def init__third_package(self):
        install = []
        for name in self.apps:
            install.extend(list(get_module_attr("%s.__third_package__" % name) or []))
        self.clear(self.THIRD_PACKAGE_DIR)
        os.system("pip3 install -t %s %s" % (self.THIRD_PACKAGE_DIR, " ".join(set(install))))

    def clear(self, dir_name, need_keep=False):
        if os.path.isdir(dir_name):
            shutil.rmtree(dir_name)
        os.makedirs(dir_name)
        if need_keep:
            self.write("", dir_name, ".gitkeep")

    def to_pep8(self, s):
        from yapf.yapflib.yapf_api import FormatCode
        return FormatCode(s)[0]

    def write(self, s, *path):
        filename = os.path.join(*path)
        dir_name = os.path.dirname(filename)
        if not os.path.isdir(dir_name):
            os.makedirs(dir_name)
        mode = "w" if os.path.isfile(filename) else "x"
        with codecs.open(filename, mode, 'utf-8') as f:
            f.write(s)
            f.close()

    def write_py(self, s, *path):
        self.write(self.to_pep8(s), *path)

    def completed(self, wait=2):
        print("""==================\n""")
        print("""plugins completed!!""")
        time.sleep(wait)
        sys.exit()

    def discover(self):
        self.init__sys_path()
        self.init__third_package()
        self.completed()


plugins = Plugins()
