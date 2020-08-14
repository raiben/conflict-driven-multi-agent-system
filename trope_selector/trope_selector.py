import json
import sys
from collections import OrderedDict
from sys import stderr

from common.event import Event, EventType
from common.story_tropes import StoryTropes
from trope_selector.genetic_algorithms.genetic_algorithm import GeneticAlgorithm


class TropeSelector(object):
    def __init__(self, random, world_resource, tropes_resource, old_style_seed, extended_dataset_resource=None,
                 neural_network_file=None, output_solution_file=None):
        self.random = random
        self.world_resource = world_resource
        self.tropes_resource = tropes_resource
        self.old_style_seed = old_style_seed
        self.extended_dataset_resource = extended_dataset_resource
        self.tropes_to_consider = set()
        self.tropes_excluded = set()
        self.global_events = []
        self.grid_size = 0
        self.character_events = OrderedDict()
        self.events_by_id = OrderedDict()
        self.neural_network_file = neural_network_file
        self.output_solution_file = output_solution_file

        self.places = []
        self.characters = []
        self.original_positions = []
        self.move_tropes = []
        self.confront_tropes = []
        self.chase_resolution_tropes = []
        self.resolve_tropes = []
        self.character_tropes = []
        self.place_tropes = []

        self.story_introduction_sentence_picker = None
        self.character_introduction_sentence_picker = None
        self.move_event_sentence_picker = None
        self.confront_event_sentence_picker = None
        self.chase_resolution_event_sentence_picker = None
        self.resolve_event_sentence_picker = None
        self.noop_event_sentence_picker = None
        self.output_file = None

    def prepare(self):
        if self.output_solution_file:
            self.output_file = open(self.output_solution_file, 'w')

        with open(self.world_resource, 'r') as handler:
            log_content = handler.read()
            log = json.loads(log_content)

        for character in log['CHARACTERS']:
            self.characters.append(character)

        for place in log['PLACES']:
            self.places.append(place)

        self.initial_positions = log['INITIAL_POSITIONS']

        for event_dictionary in log['EVENTS']['GLOBAL']:
            event = Event(**event_dictionary)
            self.global_events.append(event)
            self.events_by_id[event.id] = event

        for character in self.characters:
            self.character_events[character] = []
            for event_dictionary in log['EVENTS'][character]:
                id = event_dictionary['id']
                event = self.events_by_id[id]
                self.character_events[character].append(event)

        if self.extended_dataset_resource:
            with open(self.extended_dataset_resource, 'r') as handler:
                line = handler.readline()
                columns = line.split(',')
                self.tropes_to_consider = set(columns[6:])

        with open(self.tropes_resource, 'r') as handler:
            tropes_content = handler.read()
            tropes_dictionary = json.loads(tropes_content)

        self.move_tropes = sorted(list(self._tropes_in(tropes_dictionary['MOVE'])))
        self.confront_tropes = sorted(list(self._tropes_in(tropes_dictionary['CONFRONT'])))
        self.chase_resolution_tropes = sorted(list(self._tropes_in(tropes_dictionary['CHASE_RESOLUTION'])))
        self.resolve_tropes = sorted(list(self._tropes_in(tropes_dictionary['RESOLVE'])))
        self.character_tropes = sorted(list(self._tropes_in(tropes_dictionary['CHARACTER'])))
        self.place_tropes = sorted(list(self._tropes_in(tropes_dictionary['PLACE'])))

        self._print_summary()

    def _tropes_in(self, element, parent=None):
        all_tropes = set()
        # name = f'{element["name"]} ({parent})' if parent else element['name']
        name = element['name']
        if not self.tropes_to_consider or element['name'] in self.tropes_to_consider:
            all_tropes.add(name)
        else:
            self.tropes_excluded.add(name)

        children = element.get('children', [])
        for child in children:
            all_tropes = all_tropes.union(self._tropes_in(child, element['name']))

        return all_tropes

    def _print_summary(self):
        summary = ['Considering:']
        summary.append(f'- {len(self.character_tropes)} character tropes')
        summary.append(f'- {len(self.move_tropes)} move tropes')
        summary.append(f'- {len(self.confront_tropes)} confront tropes')
        summary.append(f'- {len(self.chase_resolution_tropes)} chase-resolution tropes')
        summary.append(f'- {len(self.resolve_tropes)} resolve tropes')
        summary.append(f'{len(self.tropes_excluded)} tropes excluded')
        print('\n'.join(summary), file=stderr)

    def select_random_tropes(self):
        character_tropes = []
        for character in self.characters:
            character_tropes.append(self.random.choice(self.character_tropes))

        place_tropes = []
        for place in self.places:
            place_tropes.append(self.random.choice(self.place_tropes))

        event_tropes = []
        for event in self.global_events:
            candidates = []
            if event.action == EventType.MOVE.value:
                candidates = self.move_tropes
            if event.action == EventType.CONFRONT.value:
                candidates = self.confront_tropes
            if event.action == EventType.CHASE_RESOLUTION.value:
                candidates = self.chase_resolution_tropes
            if event.action == EventType.RESOLVE.value:
                candidates = self.resolve_tropes

            index = self.random.choice(candidates) if candidates else None
            event_tropes.append(index)

        return StoryTropes(character_tropes, place_tropes, event_tropes)

    def select_best_tropes(self):
        if not self.neural_network_file:
            raise Exception('No neural network file provided')

        algorithm = GeneticAlgorithm(self.random, self.characters, self.places, self.initial_positions,
                                     self.global_events, self.character_events, self.character_tropes,
                                     self.place_tropes, self.move_tropes, self.confront_tropes,
                                     self.chase_resolution_tropes, self.resolve_tropes,
                                     self.neural_network_file, self.old_style_seed, write=self.build_output_writer())
        algorithm.prepare()
        algorithm.run()
        best = algorithm.get_best()

        character_tropes = best[0:len(self.characters)]
        place_tropes = best[len(self.characters):len(self.characters)+len(self.places)]
        event_tropes = best[len(self.characters)+len(self.places):]

        return StoryTropes(character_tropes, place_tropes, event_tropes)

    def build_output_writer(self):
        def write(text):
            output = self.output_file if self.output_file else sys.stdout
            print(text, file=output)

        return write

    def close(self):
        if self.output_file and not self.output_file.closed:
            self.output_file.close()