from collections import Sequence
from .core import ActionManager, ActionNone, ActionBase, Action


def shortcut(action_cls):
    def _shortcut(*args, **kwargs):
        return action_cls(*args, **kwargs)

    assert type(action_cls) is type, "The shortcut should be a class!"
    return _shortcut


def shortcut_once(action_cls):
    def _shortcut_once(*args):
        return box.corner(box.none, sc(*args))

    sc = shortcut(action_cls)
    return _shortcut_once


class ActionSet(Action):
    bind_sub_manager = True

    def __init__(self, *args):
        super().__init__()
        self.action_list = []
        for x in args:
            if isinstance(x, Sequence):
                self.action_list.extend(x)
            else:
                self.action_list.append(x)

    def on_start(self):
        super().on_start()
        self.handle_node_list()
        self.action_list = None

    def handle_node_list(self):
        for a in self.action_list:
            self.sub_manager.add_node(a)


class ActionChains(ActionSet):
    def handle_node_list(self):
        for i, a in enumerate(self.action_list):
            self.sub_manager.add_node(a, None if i == 0 else self.action_list[i])


class ActionCorner(Action):
    def __init__(self, row, col):
        super().__init__()
        self.row = row
        self.col = col

    def on_start(self):
        super().on_start()
        self.sub_manager.add_node(self.row)
        self.row = None
        self.sub_manager.add_completed(self.con_row_completed)

    def con_row_completed(self):
        self.get_manager().add_node(self.col)
        self.col = None
        self.complete()


class ActionDelayTime(ActionBase):
    def __init__(self, delay):
        super().__init__()
        self.delay = delay

    def on_start(self):
        self.delay_run(self.bind_complete(), self.delay)


class Box:
    am = shortcut(ActionManager)
    none = shortcut(ActionNone)
    set = shortcut(ActionSet)
    chains = shortcut(ActionChains)
    corner = shortcut(ActionCorner)
    delay = shortcut(ActionDelayTime)


box = Box()
del Box
