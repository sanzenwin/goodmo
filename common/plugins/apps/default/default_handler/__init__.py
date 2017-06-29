from weakref import proxy
from DEFAULT import TEvent


class BillHandler:
    def __init__(self, manager):
        self.manager = proxy(manager)

    @property
    def entity(self):
        return self.manager.entity


class EventHandler:
    def __init__(self, manager):
        self.manager = proxy(manager)
        self.avatar = None
        self.avatar_dbid = 0

    @property
    def entity(self):
        return self.manager.entity

    def init_context(self, *args):
        avatar_dbid, avatar = args
        self.avatar = avatar
        self.avatar_dbid = avatar_dbid

    def destroy_context(self):
        self.avatar = None
        self.avatar_dbid = 0

    def process(self, avatar_dbid, avatar, event_context):
        self.init_context(avatar_dbid, avatar)
        try:
            action, args = event_context.func, event_context.param
            action_method = getattr(self, 'event__' + action, None)
            if not action_method:
                print('%s::process:method not found: %s' % (self.__class__.__name__, event_context))
                return
            action_method(self, *args)
        finally:
            self.destroy_context()


class AvatarEventHandler:
    def __init__(self, avatar):
        self.avatar = proxy(avatar)

    def process(self, event_context):
        action, args = event_context.func, event_context.param
        action_method = getattr(self, 'params__' + action, None)
        if not action_method:
            return event_context
        param = action_method(self, *args)
        if param is None:
            return None
        event_context.param = param
        return event_context


class ManagerHandler:
    bill_handler_class = BillHandler
    event_handler_class = EventHandler

    def __init__(self, entity, event_client):
        self.entity = proxy(entity)
        self.event_client = event_client
        self.bill_handler = self.bill_handler_class(proxy(self))
        self.event_handler = self.event_handler_class(proxy(self))

    @staticmethod
    def _pkg_event(event_context):
        return TEvent(func=event_context[0], param=event_context[1:]).client

    def send_event(self, *event_context):
        client = self.event_handler.avatar.client
        if client:
            getattr(client, self.event_client)(self._pkg_event(event_context))

    def send_multi_event(self, avatars, *event_context):
        event = self._pkg_event(event_context)
        for avatar in avatars:
            if avatar.client:
                getattr(avatar.client, self.event_client)(event)
