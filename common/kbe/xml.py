import os
import re
import codecs
import xml.dom.minidom
import KBEngine

if KBEngine.component == "bots":
    resPathList = re.split(';|:', os.getenv("KBE_RES_PATH"))[::-1]

    def getResFullPath(filename):
        for resPath in resPathList:
            fullPath = os.path.join(resPath, filename)
            if os.path.exists(fullPath):
                return fullPath
        return ""
    KBEngine.getResFullPath = getResFullPath


class Node:
    class MultipleNode(list):
        def __getitem__(self, item):
            try:
                return super().__getitem__(item)
            except IndexError:
                return None

        def list(self):
            return self

    def __init__(self, name='', attrs={}):
        super().__init__()
        self.nodeNames = []
        self.attrs = attrs
        self.value = []
        self.name = name

    def __str__(self):
        return "nodeNames: %s, attrs: %s, value: %s, name: %s" % (self.nodeNames, self.attrs, self.value, self.name)

    def __getitem__(self, item):
        return getattr(self, item, None)

    def path(self, path):
        path = path.split(".")
        node = self
        for name in path:
            if re.match("^[\d]+$", name):
                name = int(name)
            node = node[name]
            if not node:
                break
        return node

    def list(self):
        return [self]

    def toDict(self):
        if not hasattr(self, "_dict"):
            self._dict = self.__dict()
        return self._dict

    @staticmethod
    def get_py_value(value):
        value = value.strip()
        try:
            value = eval(value)
        except(SyntaxError, NameError):
            pass
        return value

    @staticmethod
    def get_dict_value(value):
        # if hasattr(value, "__iter__") and not isinstance(value, str):
        #     value = tuple(value)
        return value

    def addNode(self, node):
        if node.name in self.nodeNames:
            nodeOrList = getattr(self, node.name)
            if not isinstance(nodeOrList, list):
                nodeOrList = self.MultipleNode([nodeOrList])
                setattr(self, node.name, nodeOrList)
            nodeOrList.append(node)
        else:
            self.nodeNames.append(node.name)
            setattr(self, node.name, node)

    def __dict(self):
        dict_data = {}
        for nodeName in self.nodeNames:
            childNode = self[nodeName]
            if isinstance(childNode, list):
                dict_data[nodeName] = []
                for node in childNode:
                    dict_data[nodeName].append(node.__dict())
            elif childNode.nodeNames:
                dict_data[nodeName] = childNode.__dict()
            else:
                dict_data[childNode.name] = self.get_dict_value(childNode.value)
        return dict_data

    def copy(self):
        node = Node(self.name, self.attrs)
        node.value = self.value
        for nodeName in self.nodeNames:
            nodeOrList = self[nodeName]
            if isinstance(nodeOrList, list):
                for n in nodeOrList:
                    node.addNode(n.copy())
            else:
                node.addNode(nodeOrList.copy())
        return node

    def over(self, node):

        def over(n, n2):
            if isinstance(n, list):
                if not isinstance(n2, list):
                    n2 = [n2]
                for i in range(len(n2)):
                    over(n[i], n2[i])
            else:
                n.value = n2.value
                n.attrs.update(n2.attrs)
                for nodeName in n2.nodeNames:
                    over(n[nodeName], n2[nodeName])

        over(self, node)
        return self


class Xml(Node):
    def __init__(self, filename):
        super().__init__()
        filename = KBEngine.getResFullPath(filename)
        with codecs.open(filename, 'r', 'utf-8') as f:
            dom = xml.dom.minidom.parse(f)
            root = dom.documentElement
            self.recursive(self, root)

    def recursive(self, obj, node):
        for child in node.childNodes:
            if isinstance(child, xml.dom.minidom.Text):
                value = self.get_py_value(child.data)
                if value:
                    obj.value.append(value)
            elif not isinstance(child, xml.dom.minidom.Comment):
                new_obj = Node(
                    child.nodeName,
                    {k: self.get_py_value(v.value) for k, v in child._attrs.items()} if child._attrs else {}
                )
                obj.addNode(new_obj)
                if len(child.childNodes) > 1:
                    self.recursive(new_obj, child)
                elif len(child.childNodes) == 1:
                    new_obj.value = self.get_py_value(child.firstChild.data)

settings_kbengine_defs = Xml(os.path.join('server', 'kbengine_defs.xml'))
settings_kbengine_custom = Xml(os.path.join('server', 'kbengine.xml'))
settings_kbengine = settings_kbengine_defs.copy().over(settings_kbengine_custom)
