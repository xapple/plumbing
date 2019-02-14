"""Who doesn't need his own k-ary tree data strucutre ?"""

from collections import OrderedDict

###############################################################################
class Node(object):
    """Generic n-ary tree node object."""

    def __repr__(self): return '<%s object "%s">' % (self.__class__.__name__, self.name)
    def __str__(self): return self.name

    def __init__(self, parent, name, **kwargs):
        # Attributes #
        self.parent = parent
        self.children = OrderedDict()
        self.name = name
        # Extra data #
        self.__dict__.update(kwargs)

    def __getitem__(self, name):
        if name not in self.children: self.children[name] = self.__class__(self, name)
        return self.children[name]

    #-------------------------- Getting nodes --------------------------------#
    @property
    def first(self): return self.children.values()[0]

    @property
    def root(self):
        if not self.parent: return self
        return self.parent.root

    def __iter__(self):
        """Iterate over all children nodes and one-self."""
        yield self
        for child in self.children.values():
            for node in child: yield node

    @property
    def path(self):
        """Iterate over all parent nodes and one-self."""
        yield self
        if not self.parent: return
        for node in self.parent.path: yield node

    @property
    def others(self):
        """Iterate over all nodes of the tree excluding one self and one's children."""
        if not self.parent: return
        yield self.parent
        for sibling in self.parent.children.values():
            if sibling.name == self.name: continue
            for node in sibling: yield node
        for node in self.parent.others: yield node

    def get_children(self, depth=1):
        """Iterate over all children (until a certain level) and one-self."""
        yield self
        if depth == 0: return
        for child in self.children.values():
            for node in child.get_children(depth-1): yield node

    def get_level(self, level=2):
        """Get all nodes that are exactly this far away."""
        if level == 1:
            for child in self.children.values(): yield child
        else:
            for child in self.children.values():
                for node in child.get_level(level-1): yield node

    #------------------------- Getting numbers -------------------------------#
    def __len__(self):
        """How many steps to the deepest leaf ?"""
        return self.len_counter(0)
    def len_counter(self, count):
        if not self.children: return count
        return max((child.len_counter(count+1) for child in self.children.values()))

    @property
    def level(self):
        """How many steps away from the root ?"""
        return self.level_counter(0)
    def level_counter(self, count):
        if not self.parent: return count
        return self.parent.level_counter(count+1)

    #------------------------- Modify topology -------------------------------#
    def trim(self, length):
        """Cut all branches over a certain length making new leaves at *length*."""
        if length > 0:
            for child in self.children.values(): child.trim(length-1)
        else:
            if hasattr(self, 'count'): self.count = sum(map(lambda x: x.count, self))
            self.children = OrderedDict()

    def mend(self, length):
        """Cut all branches from this node to its children and adopt
        all nodes at certain level."""
        if length == 0: raise Exception("Can't mend the root !")
        if length == 1: return
        self.children = OrderedDict((node.name, node) for node in self.get_level(length))
        for child in self.children.values(): child.parent = self

    def cut(self, length):
        pass

    def prune(self, length):
        pass

    def reroot(self, length):
        pass
