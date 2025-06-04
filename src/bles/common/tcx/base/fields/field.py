from datetime import datetime


class NodeFinder:

    def find(self, root):
        raise NotImplemented()

    def __call__(self, root):
        found = self.find(root)
        return list(found) if found else []

class XpathNodeFinder(NodeFinder):

    def __init__(self, xpath):
        self.xpath = xpath

    def get_ns(self, root):
        ns = dict(root.nsmap)
        ns["_"] = ns.pop(None)
        return ns

    def find(self, root):
        return root.xpath(self.xpath, namespaces=self.get_ns(root))

class XpathTagFinder(XpathNodeFinder):

    def __init__(self, *nodes):
        xpath = ["."]
        for n in nodes:
            if ":" in n:
                xpath.append(n)
            else:
                xpath.append(f"_:{n}")

        xpath = "//".join(xpath)
        super().__init__(xpath)

class XpathStrictTagFinder(XpathNodeFinder):

    def __init__(self, *nodes):
        xpath = ["."]
        for n in nodes:
            if ":" in n:
                xpath.append(n)
            else:
                xpath.append(f"_:{n}")

        xpath = "/".join(xpath)
        super().__init__(xpath)


class NodeAccess:

    def __call__(self, x):
        return x


class TextAccess(NodeAccess):
    def __call__(self, x):
        return x.text


class AttributeAccess(NodeAccess):
    def __init__(self, name , default):
        self.name = name
        self.default = default

    def __call__(self, x):
        return x.attrib.get(self.name, self.default)


class Field:
    class Empty: pass
    _xpath_ = None
    _unit_ = None
    _type_ = str
    _access_ = TextAccess()
    _single_ = True

    def __init__(self, xpath=Empty, unit=Empty, type=Empty, access=Empty, single=Empty, default=Empty,
                 required=False):
        self.xpath = self.get_param(xpath, self._xpath_)
        if isinstance(self.xpath, str):
            self.xpath = XpathNodeFinder(self.xpath)
        self.unit = self.get_param(unit, self._unit_)
        self.type = self.get_param(type, self._type_)
        self.access = self.get_param(access, self._access_)
        self.single = self.get_param(single, self._single_)
        self.default = default
        self.required = required
        self.name = None

    def get_param(self, v, default):
        return v if v is not self.Empty else default

    def get_node(self, parent):
        ret = self.xpath(parent)
        if not self.single: return ret
        for x in ret: return x
        return None

    def get_node_value(self, node):
        return self.access(node)

    def parse(self, value):
        return self.type(value)

    def get_value(self, parent_node):
        if parent_node is None:
            if self.required and self.default is self.Empty:
                raise ValueError(f"Error")
            if self.default is not self.Empty:
                return self.default
            return None

        node = self.get_node(parent_node)
        value = self.get_node_value(node)
        return self.parse(value)

    def __call__(self, parent_node, data=Empty):
        return self.get_value(parent_node)


class SingleValueField(Field):
    _single_ = True

class MultipleValueField(Field):
    _single_ = False
    _access_ = NodeAccess()

    def __init__(self, type, container=list, **kwargs):
        super().__init__(type=type, **kwargs)
        self.container = container


    def get_value(self, parent_node):
        nodes = self.get_node(parent_node)
        ret = self.container()
        for n in nodes:
            value = self.get_node_value(n)
            ret.append(self.parse(value))
        return ret

class IdField(SingleValueField):
    _xpath_ = XpathStrictTagFinder("Id")


class NotesField(SingleValueField):
    _xpath_ = XpathStrictTagFinder("Notes")

class CreatorField(SingleValueField):
    _xpath_ = XpathStrictTagFinder("Creator", "Name")

class FloatField(SingleValueField):
    _type_ = float


class DateTimeField(SingleValueField):
    _type_ = datetime.fromisoformat
