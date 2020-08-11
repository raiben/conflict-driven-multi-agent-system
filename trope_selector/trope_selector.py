import json
from collections import OrderedDict
from sys import stderr

from common.event import Event, EventType
from common.story_tropes import StoryTropes


class TropeSelector(object):
    def __init__(self, random, world_resource, tropes_resource, extended_dataset_resource=None):
        self.random = random
        self.world_resource = world_resource
        self.tropes_resource = tropes_resource
        self.extended_dataset_resource = extended_dataset_resource
        self.tropes_to_consider = set()
        self.tropes_excluded = set()
        self.global_events = []
        self.grid_size = 0
        self.character_events = OrderedDict()
        self.events_by_id = OrderedDict()

        self.places = []
        self.characters = []
        self.move_tropes = []
        self.confront_tropes = []
        self.chase_resolution_tropes = []
        self.resolve_tropes = []
        self.character_tropes = []

        self.story_introduction_sentence_picker = None
        self.character_introduction_sentence_picker = None
        self.move_event_sentence_picker = None
        self.confront_event_sentence_picker = None
        self.chase_resolution_event_sentence_picker = None
        self.resolve_event_sentence_picker = None
        self.noop_event_sentence_picker = None

    def prepare(self):
        with open(self.world_resource, 'r') as handler:
            log_content = handler.read()
            log = json.loads(log_content)

        for character in log['CHARACTERS']:
            self.characters.append(character)

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

        return StoryTropes(character_tropes, event_tropes)
