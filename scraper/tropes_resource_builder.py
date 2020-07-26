from ete3 import Tree, TreeStyle, AttrFace
from ete3.treeview import faces

from scraper.subtropes_scraper import SubTropesScraper
from scraper.trope_tree import TropeTree


class TropesResourceBuilder(object):
    def __init__(self, recursion_level=2):
        self.recursion_level = recursion_level
        self.move_trope_tree = None

    def build_resource(self):
        queue = ['LocomotionSuperindex']
        self.move_trope_tree = TropeTree(root_name='LocomotionSuperindex')

        while (queue):
            element = queue.pop(0)
            level = self.move_trope_tree.get_level(element)
            node = self.move_trope_tree.get_node(element)
            if level < self.recursion_level and not node.visited:
                node.visited = True
                print(f'Retrieving trope {element} of level {level}')
                scraper = SubTropesScraper(element)
                children_names = scraper.get_related()

                for child_name in children_names:
                    if not self.move_trope_tree.is_parent(child_name, element):
                        queue.append(child_name)
                        # TODO description
                        self.move_trope_tree.add_child_from_values(element, child_name)
                    else:
                        print(f'Trope {child_name} already parsed')
            else:
                print(f'Ignoring trope {element} of level {level}')

    def store_tree(self):
        ete_tree = Tree(self.move_trope_tree.as_ete3_string(), format=1)
        print(ete_tree.get_ascii(show_internal=True, compact=True))
        tree_style = TreeStyle()
        tree_style.show_leaf_name = False
        tree_style.layout_fn = self._build_layout()
        ete_tree.render('tree.pdf', tree_style=tree_style)

    def _build_layout(self):
        def layout(node):
            if node.is_leaf():
                name_face = AttrFace("name")
            else:
                name_face = AttrFace("name", fsize=20)
            faces.add_face_to_node(name_face, node, column=0, position="branch-right")

        return layout
