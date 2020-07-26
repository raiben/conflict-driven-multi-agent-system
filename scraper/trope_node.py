class TropeNode(object):
    def __init__(self, name, parent=None, description='', children=None):
        self.name = name
        self.parent = parent
        self.description = description
        self.children = [] if children is None else children
        self.visited = False

    def get_level(self):
        level = 0
        node = self

        while node.parent is not None:
            level += 1
            node = node.parent

        return level

    def add_child(self, child_node):
        child_node.parent = self
        self.children.append(child_node)


