import os
import sys
import platform

if platform.system() == 'Windows':
    sys.dllhandle = 1407057920

if os.getenv("KBE_PLUGINS__AUTO_GENERATE"):
    from .auto_generate import plugins
elif os.getenv("KBE_PLUGINS__INSTALL_THIRD_PACKAGE"):
    from .install_third_package import plugins
else:
    from .production import plugins

plugins.discover()
