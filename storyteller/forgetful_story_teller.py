import itertools
import json
from collections import OrderedDict

from common.event import Event, EventType
from common.utils import uncamel
from storyteller.random_word_generator import RandomWordGenerator
from storyteller.sentence_picker import SentencePicker


class ForgetfulStoryTeller(object):
    def __init__(self, random, world_resource):
        self.random = random
        self.world_resource = world_resource

        self.global_events = []
        self.grid_size = 0
        self.character_events = OrderedDict()
        self.events_by_id = OrderedDict()

        self.places = []
        self.characters = []

        self.character_names = {}
        self.place_names = {}

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

        self.story_introduction_sentence_picker = SentencePicker(
            self.random, 'sentence_templates/story_introduction.txt')
        self.character_introduction_sentence_picker = SentencePicker(
            self.random, 'sentence_templates/character_introduction.txt')
        self.move_event_sentence_picker = SentencePicker(
            self.random, 'sentence_templates/move_event.txt')
        self.confront_event_sentence_picker = SentencePicker(
            self.random, 'sentence_templates/confront_event.txt')
        self.chase_resolution_event_sentence_picker = SentencePicker(
            self.random, 'sentence_templates/chase_resolution_event.txt')
        self.resolve_event_sentence_picker = SentencePicker(
            self.random, 'sentence_templates/resolve_event.txt')
        self.noop_event_sentence_picker = SentencePicker(
            self.random, 'sentence_templates/noop_event.txt')

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
        trope_name = uncamel(trope_id)
        sentence = self.story_introduction_sentence_picker.get_sentence(
            protagonist=self.character_names[character_id], trope=trope_name)
        return [sentence]

    def describe_event(self, story_tropes, event, character_id, elements_introduced, previous_event_time):
        if event.action == EventType.MOVE.value:
            return self.describe_move(story_tropes, event, character_id, elements_introduced)
        if event.action == EventType.CONFRONT.value:
            return self.describe_confront(story_tropes, event, character_id, elements_introduced)
        if event.action == EventType.CHASE_RESOLUTION.value:
            return self.describe_chase_resolution(story_tropes, event, character_id, elements_introduced)
        if event.action == EventType.RESOLVE.value:
            return self.describe_resolve(story_tropes, event, character_id, elements_introduced)

    def describe_noop(self, character_id):
        return [self.noop_event_sentence_picker.get_sentence(protagonist=self.character_names[character_id])]

    def describe_move(self, story_tropes, event, character_id, elements_introduced):
        trope_id = story_tropes.event_tropes[event.id]
        trope_name = uncamel(trope_id)
        sentence = self.move_event_sentence_picker.get_sentence(
            protagonist=self.character_names[character_id], trope=trope_name,
            place=self.place_names[event.places[1]])
        return [sentence]

    def describe_confront(self, story_tropes, event, character_id, elements_introduced):
        story = self._introduce_new_characters(story_tropes, event.protagonists + event.antagonists,
                                               elements_introduced)

        trope_id = story_tropes.event_tropes[event.id]
        trope_name = uncamel(trope_id)
        sentence = self.confront_event_sentence_picker.get_sentence(
            protagonist=self.character_names[event.protagonists[0]],
            antagonist=self.character_names[event.antagonists[0]], trope=trope_name)
        story += [sentence]
        return story

    def describe_chase_resolution(self, story_tropes, event, character_id, elements_introduced):
        story = self._introduce_new_characters(story_tropes, event.protagonists + event.antagonists,
                                               elements_introduced)

        trope_id = story_tropes.event_tropes[event.id]
        trope_name = uncamel(trope_id)
        sentence = self.chase_resolution_event_sentence_picker.get_sentence(
            protagonist=self.character_names[event.protagonists[0]],
            antagonist=self.character_names[event.antagonists[0]], place=self.place_names[event.places[1]],
            trope=trope_name)
        story += [sentence]
        return story

    def describe_resolve(self, story_tropes, event, character_id, elements_introduced):
        story = self._introduce_new_characters(story_tropes, event.protagonists + event.antagonists,
                                               elements_introduced)

        trope_id = story_tropes.event_tropes[event.id]
        trope_name = uncamel(trope_id)
        sentence = self.resolve_event_sentence_picker.get_sentence(
            protagonist=self.character_names[event.protagonists[0]],
            antagonist=self.character_names[event.antagonists[0]], trope=trope_name)
        story += [sentence]
        return story

    def _introduce_new_characters(self, story_tropes, characters, elements_introduced):
        story = []
        for character_id in characters:
            if character_id not in elements_introduced:
                character_index = int(character_id[1:])
                trope_id = story_tropes.character_tropes[character_index]
                trope_name = uncamel(trope_id)
                sentence = self.character_introduction_sentence_picker.get_sentence(
                    character=self.character_names[character_id], trope=trope_name)
                story.append(sentence)
                elements_introduced.add(character_id)
        return story
