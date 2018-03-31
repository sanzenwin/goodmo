from plugins.conf import SettingsEntity, EqualizationMixin


class RobotBackendGenerator(SettingsEntity, EqualizationMixin):
    equalization__mod_base = 1

    def equalization_list(self):
        return [[i] for i in range(self.equalization__mod_base)]

    def equalization(self, any_id):
        return [self.mod(any_id, self.equalization__mod_base)]
