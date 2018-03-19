from plugins.conf import Str, SettingsNode, SettingsEntity


class BaseApp(SettingsEntity):
    baseappIndependence = SettingsNode(http_utils=[
        dict(externalIP=True, port=9006),
    ])
