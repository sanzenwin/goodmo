class Node:
    _cursor_id = 0

    def __init__(self, delegate=None):
        self.id = 0
        self.delegate = delegate
        self.parent = None
        self.group = None
        self.children = {}

    def clear(self):
        self.delegate = None

    def add_child(self, child):
        assert child.parent is None, "This child already added, it can't be added again."
        self.__class__._cursor_id += 1
        child.id = self._cursor_id
        child.parent = self
        self.children[child.id] = child
        child.on_get_parent()

    def remove_child(self, _id):
        child = self.children.pop(_id, None)
        if child:
            child.parent = None
            child.children = {}

    def remove_from_parent(self, only_self):
        if not self.parent:
            return
        if only_self:
            for child in self.children:
                child.parent = None
                self.parent.add_child(child)
        self.parent.remove_child(self.id)

    def get_delegate(self):
        if self.delegate:
            return self.delegate
        p = self.parent
        parent = None
        while p:
            parent = p
            p = parent.parent
        if parent:
            return parent.delegate
        return None

    def on_get_parent(self):
        delegate = self.get_delegate()
        if delegate:
            delegate.on_node_get_parent(self)


class RootNode(Node):
    pass


class Tree:
    def __init__(self, delegate):
        self.delegate = delegate
        self.root = RootNode(delegate)

    def clear(self):
        def clear(node):
            node.clear()

        self.travel(clear)
        self.root = RootNode(self.delegate)

    def is_on_top(self, node):
        return node.parent is self.root

    def add_node(self, node, parent=None):
        if parent is None:
            parent = self.root
        parent.add_child(node)

    def get_tail_node(self, parent):
        def travel(p, depth):
            nonlocal node, depth_most
            if depth > depth_most:
                node, depth_most = p, depth
            for child in p.children.values():
                travel(child, depth + 1)

        node = None
        depth_most = 0
        travel(parent or self.root, 0)
        return node

    def count(self):
        def count_call():
            nonlocal count
            count += 1

        count = 0
        self.travel(count_call)
        return count

    def find(self, callback):
        def find(n):
            nonlocal node
            if callback(n):
                node = n
                return True
            return False

        node = None
        self.travel(find)
        return node

    def travel(self, callback, node=None):
        p = node or self.root
        for child in p.children.values():
            if callback(child):
                return
            self.travel(callback, child)

    def travel_only_on_top(self, callback):
        for child in self.root.children.values():
            callback(child)


class ActionBase(Node):
    quiet = False

    def __init__(self):
        super().__init__()
        self.playing = False
        self.completed = False

    def get_manager(self):
        return self.get_delegate()

    def delay_run(self, callback, seconds=0, repeat=1):
        pass

    def start(self):
        if self.playing:
            return
        self.playing = True
        manager = self.get_manager()
        manager.on_action_start_prev(self, self.quiet)
        self.on_start()
        manager.on_action_start(self, self.quiet)

    def bind_complete(self, quiet):
        def bind_complete():
            self.complete(quiet)

        return bind_complete

    def complete(self, quiet=False):
        def complete():
            self.get_manager().on_action_completed(self, quiet)
            self.clear()
            self.on_completed()

        if self.completed:
            return
        self.completed = True
        self.delay_run(complete)

    def catch_action(self, action_cls, action, callback):
        if action.__class__ is action_cls:
            return not not callback(self)
        return False

    def catch_action_generic(self, action_cls, action, callback):
        if isinstance(action, action_cls):
            return callback(self)

    def on_start(self):
        pass

    def on_completed(self):
        pass

    def on_other_start_prev(self, action):
        pass

    def on_other_start(self, action):
        pass

    def on_other_completed(self, action):
        pass


class ActionNone(ActionBase):
    def on_start(self):
        self.complete()


class ActionEvent(ActionNone):
    pass


class ActionManager:
    def __init__(self, start):
        self.playing = start
        self.tree = Tree(self)

    def start(self):
        if self.playing:
            return
        self.playing = True
        self.on_start()

    def stop(self):
        self.playing = False

    def clear(self):
        self.tree.clear()

    def delay_run(self, callback, seconds=0, repeat=1):
        pass

    def add_node(self, node, parent=None, group=None):
        node.group = group
        self.tree.add_node(node, parent)
        self.on_start()

    def add_node_to_tail(self, node, group):
        group_node = self.find_node_by_group(group)
        parent = self.tree.get_tail_node(group_node) if group_node else group_node
        self.add_node(node, parent, group)

    def find_node_by_type(self, node_cls):
        def find(node):
            return isinstance(node, node_cls)

        return self.tree.find(find)

    def find_node_by_group(self, group):
        def find(node):
            return node.group == group

        return self.tree.find(find)

    def on_start(self):
        def start(action):
            action.start()

        if self.playing:
            self.tree.travel_only_on_top(start)

    def on_action_start_prev(self, action, quiet):
        if not quiet:
            self.broadcast_action_start_prev(action)

    def on_action_start(self, action, quiet):
        if not quiet:
            self.broadcast_action_start(action)

    def on_action_completed(self, action, quiet):
        if not quiet:
            self.broadcast_action_completed(action)
        action.remove_from_parent(True)
        if self.tree.count() == 0:
            self.on_completed()

    def broadcast_action_start_prev(self, action):
        self.on_other_start_prev(action)

    def broadcast_action_start(self, action):
        self.on_other_start(action)

    def broadcast_action_completed(self, action):
        self.on_other_completed(action)

    def on_other_start_prev(self, action):
        def on_other_start_prev(a):
            if a is not action and a.playing:
                a.on_other_start_prev(action)

        self.tree.travel_only_on_top(on_other_start_prev)

    def on_other_start(self, action):
        def on_other_start(a):
            if a is not action and a.playing:
                a.on_other_start(action)

        self.tree.travel_only_on_top(on_other_start)

    def on_other_completed(self, action):
        def on_other_completed(a):
            if a is not action and a.playing:
                a.on_other_completed(action)

        self.tree.travel_only_on_top(on_other_completed)

    def on_completed(self):
        pass

    def on_node_get_parent(self, action):
        if self.tree.is_on_top(action) and self.playing:
            action.start()
