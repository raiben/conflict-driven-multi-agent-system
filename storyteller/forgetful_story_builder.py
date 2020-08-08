import itertools
import json
from collections import OrderedDict
from sys import stderr

from common.event import Event, EventType
from common.utils import uncamel
from storyteller.random_word_generator import RandomWordGenerator
from storyteller.story_tropes import StoryTropes


class ForgetfulStoryBuilder(object):
    def __init__(self, world_resource, tropes_resource):
        self.random = None
        self.world_resource = world_resource
        self.tropes_resource = tropes_resource
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

        self.character_names = {}
        self.place_names = {}

    def prepare(self):
        with open(self.world_resource, 'r') as handler:
            log_content = handler.read()
            log = json.loads(log_content)

        size = log['META']['GRID_SIZE']
        self.places = [f'{x}, {y}' for x, y in list(itertools.product(range(0, size), range(0, size)))]

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

        with open(self.tropes_resource, 'r') as handler:
            tropes_content = handler.read()
            tropes_dictionary = json.loads(tropes_content)

        self.move_tropes = list(self._tropes_in(tropes_dictionary['MOVE']))
        self.confront_tropes = list(self._tropes_in(tropes_dictionary['CONFRONT']))
        self.chase_resolution_tropes = list(self._tropes_in(tropes_dictionary['CHASE_RESOLUTION']))
        self.resolve_tropes = list(self._tropes_in(tropes_dictionary['RESOLVE']))
        self.character_tropes = list(self._tropes_in(tropes_dictionary['CHARACTER']))

        self._print_summary()

    def _tropes_in(self, element, parent=None):
        all_tropes = set()
        name = f'{element["name"]} ({parent})' if parent else element['name']
        all_tropes.add(name)
        children = element.get('children', [])
        for child in children:
            all_tropes = all_tropes.union(self._tropes_in(child, element['name']))

        return all_tropes

    def select_tropes(self, random):
        self.random = random
        character_tropes = []
        for character in self.characters:
            character_tropes.append(random.randint(0, len(self.character_tropes) - 1))

        event_tropes = []
        for event in self.global_events:
            length = 0
            if event.action == EventType.MOVE.value:
                length = len(self.move_tropes)
            if event.action == EventType.CONFRONT.value:
                length = len(self.confront_tropes)
            if event.action == EventType.CHASE_RESOLUTION.value:
                length = len(self.chase_resolution_tropes)
            if event.action == EventType.RESOLVE.value:
                length = len(self.resolve_tropes)

            index = random.randint(0, length - 1) if length else 0
            event_tropes.append(index)

        return StoryTropes(character_tropes, event_tropes)

    def _print_summary(self):
        summary = ['Considering:']
        summary.append(f'- {len(self.character_tropes)} character tropes')
        summary.append(f'- {len(self.move_tropes)} move tropes')
        summary.append(f'- {len(self.confront_tropes)} confront tropes')
        summary.append(f'- {len(self.chase_resolution_tropes)} chase-resolution tropes')
        summary.append(f'- {len(self.resolve_tropes)} resolve tropes')
        print('\n'.join(summary), file=stderr)

    def tell_story(self, tropes):
        self._lazy_init_names()
        self._lazy_init_places()

        stories = []
        for character_id in self.characters:
            story = self.tell_character_story(tropes, character_id)
            stories.append(story)
        return '\n\n'.join(stories)

    def _lazy_init_names(self):
        if not self.character_names:
            self.character_names = {}
            name_generator = RandomWordGenerator(random=self.random)

            for character_id in self.characters:
                character_name = name_generator.get_character_name()
                while character_name in self.character_names.values():
                    character_name = name_generator.get_character_name()
                self.character_names[character_id] = character_name

    def _lazy_init_places(self):
        if not self.place_names:
            self.place_names = {}
            name_generator = RandomWordGenerator(random=self.random)

            for place_id in self.places:
                place_name = name_generator.get_place_name()
                while place_name in self.character_names.values():
                    place_name = name_generator.get_place_name()
                self.place_names[place_id] = place_name

    def tell_character_story(self, story_tropes, character_id):
        story = self.describe_character(story_tropes, character_id)
        elements_introduced = {character_id}
        previous_event_time = -1
        for event in self.character_events[character_id]:
            if event.action != EventType.NOOP.value:
                if previous_event_time != event.t - 1:
                    story += self.describe_noop(character_id)
                story += self.describe_event(story_tropes, event, character_id, elements_introduced,
                                             previous_event_time)
                previous_event_time = event.t
        return '. '.join(story)

    def describe_character(self, story_tropes, character_id):
        character_index = int(character_id[1:])
        trope_id = story_tropes.character_tropes[character_index]
        trope_name = uncamel(self.character_tropes[trope_id])
        return [f'This is the story of {self.character_names[character_id]}, '
                f'the classical "{trope_name}" character']

    def describe_event(self, story_tropes, event, character_id, elements_introduced, previous_event_time):
        if event.action == EventType.MOVE.value:
            return self.describe_move(story_tropes, event, character_id, elements_introduced, previous_event_time)
        if event.action == EventType.CONFRONT.value:
            return self.describe_confront(story_tropes, event, character_id, elements_introduced, previous_event_time)
        if event.action == EventType.CHASE_RESOLUTION.value:
            return self.describe_chase_resolution(story_tropes, event, character_id, elements_introduced,
                                                  previous_event_time)
        if event.action == EventType.RESOLVE.value:
            return self.describe_resolve(story_tropes, event, character_id, elements_introduced)

    def describe_noop(self, character_id):
        time_passed_expressions = [f'Nothing special happened for a while for {self.character_names[character_id]}',
                                   'Days passed', 'Time passed',
                                   f'Life kept going for {self.character_names[character_id]}']
        return [self.random.choice(time_passed_expressions)]

    def describe_move(self, story_tropes, event, character_id, elements_introduced, previous_event_time):
        trope_id = story_tropes.event_tropes[event.id]
        trope_name = uncamel(self.move_tropes[trope_id])
        return [f'{self.character_names[character_id]} moved to {self.place_names[event.places[1]]} '
                f'in the classical "{trope_name}" event']

    def describe_confront(self, story_tropes, event, character_id, elements_introduced, previous_event_time):
        story = self._introduce_new_characters(story_tropes, event.protagonists + event.antagonists,
                                               elements_introduced)

        trope_id = story_tropes.event_tropes[event.id]
        trope_name = uncamel(self.confront_tropes[trope_id])
        story += [f'{self.character_names[event.protagonists[0]]} had a conflict '
                  f'with {self.character_names[event.antagonists[0]]} '
                  f'related to the classical "{trope_name}" event']
        return story

    def describe_chase_resolution(self, story_tropes, event, character_id, elements_introduced, previous_event_time):
        story = self._introduce_new_characters(story_tropes, event.protagonists + event.antagonists,
                                               elements_introduced)

        trope_id = story_tropes.event_tropes[event.id]
        trope_name = uncamel(self.chase_resolution_tropes[trope_id])
        story += [f'{self.character_names[event.protagonists[0]]} '
                  f'chased {self.character_names[event.antagonists[0]]} '
                  f'to {self.place_names[event.places[1]]} '
                  f'in the classical "{trope_name}" event']
        return story

    def describe_resolve(self, story_tropes, event, character_id, elements_introduced):
        story = self._introduce_new_characters(story_tropes, event.protagonists + event.antagonists,
                                               elements_introduced)

        trope_id = story_tropes.event_tropes[event.id]
        trope_name = uncamel(self.resolve_tropes[trope_id])
        story += [f'{self.character_names[event.protagonists[0]]} '
                  f'finally resolved the conflict with {self.character_names[event.antagonists[0]]} '
                  f'in the classical "{trope_name}" event']
        return story

    def _introduce_new_characters(self, story_tropes, characters, elements_introduced):
        story = []
        for character_id in characters:
            if character_id not in elements_introduced:
                character_index = int(character_id[1:])
                trope_id = story_tropes.character_tropes[character_index]
                trope_name = uncamel(self.character_tropes[trope_id])
                story.append(f'{self.character_names[character_id]}, '
                             f'the classical "{trope_name}" character, was also there')
                elements_introduced.add(character_id)
        return story
