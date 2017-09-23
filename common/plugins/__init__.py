import os
import sys

if os.name == "nt":
    sys.dllhandle = 1407057920

if os.getenv("KBE_PLUGINS__AUTO_GENERATE"):
    from .auto_generate import Plugins
elif os.getenv("KBE_PLUGINS__INSTALL_THIRD_PACKAGE"):
    from .install_third_package import Plugins
else:
    from .production import Plugins

Plugins.discover()
