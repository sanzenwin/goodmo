import os
from common.utils import get_module_attr
from .auto_generate import Plugins as PluginsBase


class Plugins(PluginsBase):
    HOME_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    THIRD_PACKAGE_DIR = os.path.join(os.path.dirname(os.path.dirname(HOME_DIR)), "kbe", "res", "scripts", "common",
                                     "Lib", "site-packages")

    @classmethod
    def init__third_package(cls):
        install = []
        for name in cls.apps:
            install.extend(list(get_module_attr("%s.settings.__third_package__" % name) or []))
        os.system("pip3 install -t %s %s" % (cls.THIRD_PACKAGE_DIR, " ".join(set(install))))

    @classmethod
    def discover(cls):
        cls.init__sys_path()
        cls.init__third_package()
        print("""==============\n""")
        print("""plugins completed!!""")
