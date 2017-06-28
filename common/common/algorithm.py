import heapq


class Node:
    def __init__(self, key):
        self.key = key
        self.left = None
        self.right = None
        self.height = 0


class AVLTree:
    def __init__(self):
        self.root = None

    def find(self, key):
        return self._find(key, self.root)

    def _find(self, key, node):
        if node is None:
            return None
        elif key < node.key:
            return self._find(key, node.left)
        elif key > node.key:
            return self._find(key, node.right)
        else:
            return node

    def find_min(self):
        if self.root is None:
            return None
        else:
            return self._find_min(self.root)

    def _find_min(self, node):
        if node.left:
            return self._find_min(node.left)
        else:
            return node

    def find_max(self):
        if self.root is None:
            return None
        else:
            return self._find_max(self.root)

    def _find_max(self, node):
        if node.right:
            return self._find_max(node.right)
        else:
            return node

    def height(self, node):
        if node is None:
            return -1
        else:
            return node.height

    def single_left_rotate(self, node):
        k1 = node.left
        node.left = k1.right
        k1.right = node
        node.height = max(self.height(node.right), self.height(node.left)) + 1
        k1.height = max(self.height(k1.left), node.height) + 1
        return k1

    def single_right_rotate(self, node):
        k1 = node.right
        node.right = k1.left
        k1.left = node
        node.height = max(self.height(node.right), self.height(node.left)) + 1
        k1.height = max(self.height(k1.right), node.height) + 1
        return k1

    def double_left_rotate(self, node):
        node.left = self.single_right_rotate(node.left)
        return self.single_left_rotate(node)

    def double_right_rotate(self, node):
        node.right = self.single_left_rotate(node.right)
        return self.single_right_rotate(node)

    def put(self, node):
        if not self.root:
            self.root = node
        else:
            self.root = self._put(node, self.root)

    def _put(self, cur_node, node):
        key = cur_node.key
        if node is None:
            node = cur_node
        elif key < node.key:
            node.left = self._put(cur_node, node.left)
            if (self.height(node.left) - self.height(node.right)) == 2:
                if key < node.left.key:
                    node = self.single_left_rotate(node)
                else:
                    node = self.double_left_rotate(node)

        elif key > node.key:
            node.right = self._put(cur_node, node.right)
            if (self.height(node.right) - self.height(node.left)) == 2:
                if key < node.right.key:
                    node = self.double_right_rotate(node)
                else:
                    node = self.single_right_rotate(node)

        node.height = max(self.height(node.right), self.height(node.left)) + 1
        return node

    def delete(self, key):
        self.root = self._delete(key, self.root)

    def _delete(self, key, node):
        if node is None:
            raise KeyError
        elif key < node.key:
            node.left = self._delete(key, node.left)
            if (self.height(node.right) - self.height(node.left)) == 2:
                if self.height(node.right.right) >= self.height(node.right.left):
                    node = self.single_right_rotate(node)
                else:
                    node = self.double_right_rotate(node)
            node.height = max(self.height(node.left), self.height(node.right)) + 1
        elif key > node.key:
            node.right = self._delete(key, node.right)
            if (self.height(node.left) - self.height(node.right)) == 2:
                if self.height(node.left.left) >= self.height(node.left.right):
                    node = self.single_left_rotate(node)
                else:
                    node = self.double_left_rotate(node)
            node.height = max(self.height(node.left), self.height(node.right)) + 1
        elif node.left and node.right:
            if node.left.height <= node.right.height:
                node.key = self._find_min(node.right).key
                node.right = self._delete(node.key, node.right)
            else:
                node.key = self._find_max(node.left).key
                node.left = self._delete(node.key, node.left)
            node.height = max(self.height(node.left), self.height(node.right)) + 1
        else:
            if node.right:
                node = node.right
            else:
                node = node.left
        return node


class MinHeap:
    def __init__(self, k):
        self.k = k
        self.heap = []

    def push(self, elem):
        if len(self.heap) < self.k:
            heapq.heappush(self.heap, elem)
        else:
            if elem > self.heap[0]:
                heapq.heapreplace(self.heap, elem)

    def get(self):
        return self.heap

    def reset(self):
        heapq.heapify(self.heap)
