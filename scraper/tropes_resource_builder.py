import json
from collections import OrderedDict
from datetime import datetime
from sys import stderr

from ete3 import Tree, TreeStyle, AttrFace
from ete3.treeview import faces

from scraper.subtropes_scraper import SubTropesScraper
from scraper.trope_tree import TropeTree


class TropesResourceBuilder(object):

    def __init__(self, recursion_level=2):
        self.recursion_level = recursion_level
        self.move_trope_tree = None
        self.confront_trope_tree = None
        self.chase_resolution_tree = None
        self.resolve_ending_tree = None
        self.resolve_fight_tree = None
        self.character_tree = None
        self.run_at = None
        self.trees = OrderedDict()

    def retrieve_resource(self):
        self.run_at = datetime.now()
        self.move_trope_tree = self._retrieve_and_build_trope_tree('LocomotionSuperindex')
        self.confront_trope_tree = self._retrieve_and_build_trope_tree('Conflict')
        self.chase_resolution_tree = self._retrieve_and_build_trope_tree('ChaseScene')
        self.resolve_ending_tree = self._retrieve_and_build_trope_tree('EndingTropes', in_level=1)
        self.resolve_fight_tree = self._retrieve_and_build_trope_tree('FightScene', in_level=1)
        self.character_tree = self._retrieve_and_build_trope_tree('Characters')

    def _retrieve_and_build_trope_tree(self, root_trope, in_level=0):
        queue = [root_trope]
        trope_tree = TropeTree(root_name=root_trope)
        while (queue):
            element = queue.pop(0)
            level = trope_tree.get_level(element)
            node = trope_tree.get_node(element)
            if level + in_level < self.recursion_level and not node.visited:
                node.visited = True
                scraper = SubTropesScraper(element)
                children_names = scraper.get_related()

                for child_name in children_names:
                    if not trope_tree.is_parent(child_name, element):
                        queue.append(child_name)
                        # TODO description
                        trope_tree.add_child_from_values(element, child_name)
                    else:
                        print(f'Trope {child_name} already parsed', file=stderr)
            else:
                print(f'Ignoring trope {element} of level {level}', file=stderr)
        return trope_tree

    def store_tree_as_json(self, output_file_name=None):
        base_tree = OrderedDict()
        base_tree['META'] = OrderedDict(
            [('RECURSION_LEVEL', self.recursion_level), ('RUN_AT', self.run_at.isoformat())])
        base_tree['MOVE'] = self.move_trope_tree.as_dictionary()
        base_tree['CONFRONT'] = self.confront_trope_tree.as_dictionary()
        base_tree['CHASE_RESOLUTION'] = self.chase_resolution_tree.as_dictionary()
        base_tree['RESOLVE'] = OrderedDict([
            ('name', 'EndingTropes/FightScene'),
            ('children', [self.resolve_ending_tree.as_dictionary(), self.resolve_fight_tree.as_dictionary()])])
        base_tree['CHARACTER'] = self.character_tree.as_dictionary()

        content = json.dumps(base_tree, indent=2)
        if output_file_name:
            with open(output_file_name, 'w') as handler:
                handler.write(content)
        else:
            print(content)

    def _store_tree(self, name, trope_tree):
        ete_tree = Tree(trope_tree.as_ete3_string(), format=1)
        print(ete_tree.get_ascii(show_internal=True, compact=True))
        tree_style = TreeStyle()
        tree_style.show_leaf_name = False
        tree_style.layout_fn = self._build_layout()
        ete_tree.render(f'{name}_tropes.pdf', tree_style=tree_style)

    def _build_layout(self):
        def layout(node):
            if node.is_leaf():
                name_face = AttrFace("name")
            else:
                name_face = AttrFace("name", fsize=20)
            faces.add_face_to_node(name_face, node, column=0, position="branch-right")

        return layout
