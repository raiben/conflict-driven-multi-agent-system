import json
import os
import tempfile

import networkx as nx


class SkeletonRepresenter(object):
    def __init__(self, world_resource, output_file):
        self.world_resource = world_resource
        self.output_file = output_file
        self.world = None

    def present(self):
        with open(self.world_resource, 'r') as handler:
            content = handler.read()
            self.world = json.loads(content)

        G = nx.MultiDiGraph()

        for event in self.world['EVENTS']['GLOBAL']:
            event_node = f'Event\n({event["action"]})\n#{event["id"]}'.replace('_', '\n')
            if event['action'] == 'move':
                G.add_node(event_node, shape='box', fontname='Ubuntu')
            elif event['action'] == 'confront':
                G.add_node(event_node, shape='rect', fontname='Ubuntu', style='setlinewidth(3)', color='#ff0000')
            elif event['action'] == 'chase_resolution':
                G.add_node(event_node, shape='rect', fontname='Ubuntu', style='setlinewidth(3)', color='#ff0000')
            elif event['action'] == 'resolve':
                G.add_node(event_node, shape='rect', fontname='Ubuntu', style='setlinewidth(3)', color='#ff0000')

            if event['action'] != 'noop':
                protagonist_node = f'Character\n{event["protagonists"][0]}'

                if event['action'] == 'confront' or event['action'] == 'chase_resolution' or event[
                    'action'] == 'resolve':
                    G.add_node(protagonist_node, shape='oval', fontname='Ubuntu', style='setlinewidth(3)')
                    G.add_edge(protagonist_node, event_node, style='setlinewidth(3)', color='#ff0000')
                else:
                    G.add_node(protagonist_node, shape='oval', fontname='Ubuntu')
                    G.add_edge(protagonist_node, event_node)

                if event['antagonists']:
                    antagonist_node = f'Character\n{event["antagonists"][0]}'
                    if event['action'] == 'confront' or event['action'] == 'chase_resolution' or event[
                        'action'] == 'resolve':
                        G.add_node(antagonist_node, shape='oval', fontname='Ubuntu', style='setlinewidth(3)')
                        G.add_edge(event_node, antagonist_node, style='setlinewidth(3)', color='#0000ff')
                    else:
                        G.add_node(antagonist_node, shape='oval', fontname='Ubuntu')
                        G.add_edge(event_node, antagonist_node)
                if event['action'] == 'move':
                    place_node = f'Place\n{event["places"][1]}'
                    G.add_node(place_node, shape='folder', fontname='Ubuntu')
                    G.add_edge(event_node, place_node)

        dot = nx.nx_pydot.to_pydot(G)

        with tempfile.NamedTemporaryFile() as fp:
            dot.write(fp.name)
            fp.seek(0)
            with tempfile.NamedTemporaryFile() as fp2:
                os.system(f'unflatten -f -l 3 {fp.name} > {fp2.name}')
                import pydot
                (graph,) = pydot.graph_from_dot_file(fp2.name)
                graph.write_png(self.output_file)
