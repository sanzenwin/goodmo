from plugins.conf import SettingsNode


class Robot(SettingsNode):
    totalTime = 1
    tickCount = 10

    def onLogin(self, avatar):
        pass

    def mongodb(self):
        return dict(
            Factory=dict(host='localhost', port=27017, username=None, password=None)
        )
