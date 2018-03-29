from kbe.protocol import Type
from DEFAULT import AvatarClient as AvatarClient_, TAvatar as TAvatar_


class AvatarClient(AvatarClient_):
    def get_attr(self, item):
        if self.avatar.isRobot:
            return getattr(self.avatar, "ClientProxy__%s" % item)
        else:
            return super().get_attr(item)


class TAvatar(TAvatar_):
    client_class = AvatarClient
    properties_type = dict(isRobot=Type.BOOL, **TAvatar_.properties_type)

    def __init__(self, entity=None):
        super().__init__(entity, isRobot=entity.robotBackendMark if entity else False)
