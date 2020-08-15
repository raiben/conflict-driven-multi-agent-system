import json
import os
import tempfile
import pydot

import networkx as nx


class SkeletonPresenter(object):
    NORMAL_NODE = {'fontname': 'Ubuntu', 'style': 'setlinewidth(1)', 'color': '#888888', 'fontcolor': '#555555'}
    MARKED_ELEMENT = {**NORMAL_NODE, 'style': 'setlinewidth(1)', 'color': '#000', 'fontcolor': '#000'}
    OUTPUT_EDGE = {**MARKED_ELEMENT, 'color': '#008800'}
    INPUT_EDGE = {**MARKED_ELEMENT, 'color': '#990000'}

    def __init__(self, world_resource, output_prefix, solution_resource=None):
        self.world_resource = world_resource
        self.output_prefix = output_prefix
        self.solution_resource = solution_resource
        self.world = None
        self.places_index = {}

    def present(self):
        with open(self.world_resource, 'r') as handler:
            content = handler.read()
            self.world = json.loads(content)

        if self.solution_resource:
            tropes_length = len(self.world['CHARACTERS']) + len(self.world['PLACES']) + len(
                self.world['EVENTS']['GLOBAL'])
            tropes = [None for index in range(tropes_length)]
            with open(self.solution_resource, 'r') as handler:
                lines = handler.readlines()
                tropes_as_text = lines[-1].split(', tropes=')[1]
                tropes = eval(tropes_as_text)

        self.places_index = {id:index for index, id in enumerate(self.world['PLACES'])}

        G = nx.MultiDiGraph()

        for event in self.world['EVENTS']['GLOBAL']:

            event_trope = tropes[event["id"]+len(self.world['CHARACTERS']) + len(self.world['PLACES'])]
            if event_trope:
                event_node = f'{event_trope}\n\n(Event\n{event["action"]}\n#{event["id"]})'.replace('_', '\n')
            else:
                event_node = f'Event\n{event["action"]})\n#{event["id"]}'.replace('_', '\n')

            if event['action'] == 'move':
                G.add_node(event_node, shape='rect', **self.NORMAL_NODE)
            elif event['action'] == 'confront':
                G.add_node(event_node, shape='rect', **self.MARKED_ELEMENT)
            elif event['action'] == 'chase_resolution':
                G.add_node(event_node, shape='rect', **self.MARKED_ELEMENT)
            elif event['action'] == 'resolve':
                G.add_node(event_node, shape='rect', **self.MARKED_ELEMENT)

            if event['action'] != 'noop':
                protagonist = event["protagonists"][0]
                protagonist_index = int(protagonist.replace('c',''))
                protagonist_trope = tropes[protagonist_index]
                if protagonist_trope:
                    protagonist_node = f'{protagonist_trope}\n\n(Character\n{event["protagonists"][0]})'
                else:
                    protagonist_node = f'Character\n{event["protagonists"][0]}'

                if event['action'] == 'confront' or event['action'] == 'chase_resolution' or event[
                    'action'] == 'resolve':
                    G.add_node(protagonist_node, shape='oval', **self.MARKED_ELEMENT)
                    G.add_edge(protagonist_node, event_node, **self.OUTPUT_EDGE)
                else:
                    G.add_node(protagonist_node, shape='oval', **self.NORMAL_NODE)
                    G.add_edge(protagonist_node, event_node, **self.NORMAL_NODE)

                if event['antagonists']:
                    antagonist = event["antagonists"][0]
                    antagonist_index = int(antagonist.replace('c', ''))
                    antagonist_trope = tropes[antagonist_index]
                    if antagonist_trope:
                        antagonist_node = f'{antagonist_trope}\n\n(Character\n{event["antagonists"][0]})'
                    else:
                        antagonist_node = f'Character\n{event["antagonists"][0]}'


                    if event['action'] == 'confront' or event['action'] == 'chase_resolution' or event[
                        'action'] == 'resolve':
                        G.add_node(antagonist_node, shape='oval', **self.MARKED_ELEMENT)
                        G.add_edge(event_node, antagonist_node, **self.INPUT_EDGE)
                    else:
                        G.add_node(antagonist_node, shape='oval', **self.NORMAL_NODE)
                        G.add_edge(event_node, antagonist_node, **self.NORMAL_NODE)

                if event['action'] == 'move':
                    place = event["places"][1]
                    place_index = self.places_index[place]
                    place_trope = tropes[place_index + len(self.world['CHARACTERS'])]
                    if place_trope:
                        place_node = f'{place_trope}\n\n(Place {place})'
                    else:
                        place_node = f'Place\n{place}'


                    G.add_node(place_node, shape='hexagon', **self.NORMAL_NODE)
                    G.add_edge(event_node, place_node, **self.NORMAL_NODE)

        dot = nx.nx_pydot.to_pydot(G)

        with tempfile.NamedTemporaryFile() as fp:
            dot.write(fp.name)
            fp.seek(0)
            with tempfile.NamedTemporaryFile() as fp2:
                os.system(f'unflatten -f -l 3 {fp.name} > {fp2.name}')
                (graph,) = pydot.graph_from_dot_file(fp2.name)
                graph.write_png(f'{self.output_prefix}.png')
                graph.write_pdf(f'{self.output_prefix}.pdf')

        nx.write_gexf(G, f'{self.output_prefix}.gexf')
