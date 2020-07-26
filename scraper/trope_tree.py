from scraper.trope_node import TropeNode


class TropeTree(object):
    def __init__(self, root_name):
        self._root = TropeNode(name=root_name)
        self._trope_node_by_name = {root_name: self._root}

    def add_child_from_values(self, parent_name, child_name, child_description=None):
        parent = self._trope_node_by_name[parent_name]
        child = TropeNode(name=child_name, parent=parent, description=child_description)
        parent.add_child(child)
        if child_name in self._trope_node_by_name:
            previous_child = self._trope_node_by_name[child_name]
            if child.get_level() < previous_child.get_level():
                self._trope_node_by_name[child_name] = child
        else:
            self._trope_node_by_name[child_name] = child

    def node_exists(self, node_name):
        return node_name in self._trope_node_by_name

    def get_node(self, node_name):
        return self._trope_node_by_name.get(node_name)

    def get_level(self, node_name):
        return self._trope_node_by_name[node_name].get_level()

    def is_parent(self, child_name, expected_parent_name):
        if expected_parent_name not in self._trope_node_by_name or child_name not in self._trope_node_by_name:
            return False

        child_node = self._trope_node_by_name[child_name]
        while child_node.parent is not None:
            parent_node = child_node.parent
            parent_name = parent_node.name
            if parent_name == expected_parent_name:
                return True
            child_node = parent_node

        return False

    def _read_post_order_as_ete3_string(self, node):
        if not node.children:
            return node.name

        chidren_as_text = []
        for child in node.children:
            child_as_text = self._read_post_order_as_ete3_string(child)
            chidren_as_text.append(child_as_text)

        return f'({",".join(chidren_as_text)}){node.name}'

    def as_ete3_string(self):
        text = self._read_post_order_as_ete3_string(self._root)
        return f'{text};'
