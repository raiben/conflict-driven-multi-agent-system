from typing import List

from elements.backstory import BackStory
from elements.conflict import Conflict
from elements.event import Event


class Character(object):
    def __init__(self, world, id, random) -> None:
        self.world = world
        self.id = id
        self.random = random
        self.name = f'c{self.id}'
        self.backstory = BackStory()
        self.open_conflicts: List[Conflict] = []

    def play(self, t, event_id):
        actions = [self._no_operation, self._move_randomly, self._try_resolve_existing_conflict,
                   self._try_new_confrontation]

        characters_around = self.world.get_characters_around(self)
        action = self.random.choice(actions)
        action(t, event_id, characters_around)

    def _with_probability(self, probability):
        value = self.random.uniform(0, 1)
        return value <= probability

    def _no_operation(self, t, event_id, *args, **kwargs):
        event = Event(t, event_id, False, 'noop', [self.name], [], [], [], [])
        self.backstory.add_event(event)
        self.world.add_world_event(event)

    def _move_randomly(self, t, event_id, *args, **kwargs):
        old_position = self.world.get_position(self)
        self.world.move_character(self)
        new_position = self.world.get_position(self)

        event = Event(t, event_id, False, 'move', [self.name], [], [], [], [old_position, new_position])
        self.backstory.add_event(event)
        self.world.add_world_event(event)

    def _try_resolve_existing_conflict(self, t, event_id, characters_around):
        if self.open_conflicts:
            for conflict in self.open_conflicts:
                if conflict.antagonist in characters_around:
                    self._resolve_conflict(conflict, t, event_id)
                    return

            self._chase_conflict_resolution(t, event_id)

    def _resolve_conflict(self, conflict, t, event_id):
        # TODO What if the conflict is not resolved this time? What kind of tropes would it enable?
        self.open_conflicts.remove(conflict)

        event = Event(t, event_id, conflict.is_story_arc, 'resolve', [self.name], [conflict.antagonist.name],
                      [], [], [])
        conflict.antagonist.add_event(event)
        self.backstory.add_event(event)
        self.world.add_world_event(event)

    def _chase_conflict_resolution(self, t, event_id):
        old_position = self.world.get_position(self)
        antagonists = [conflict.antagonist for conflict in self.open_conflicts]
        closer_antagonist, direction = self.world.get_closer_antagonist(self, antagonists)
        self.world.move_character(self, direction)
        new_position = self.world.get_position(self)

        conflict_to_resolve = next(conflict for conflict in self.open_conflicts
                                   if conflict.antagonist == closer_antagonist)
        event = Event(t, event_id, conflict_to_resolve.is_story_arc, 'chase_resolution', [self.name],
                      [closer_antagonist.name], [], [], [old_position, new_position])
        closer_antagonist.add_event(event)
        self.backstory.add_event(event)
        self.world.add_world_event(event)

    def _try_new_confrontation(self, t, event_id, characters_around):
        characters_with_open_confrontation = set([conflict.antagonist for conflict in self.open_conflicts])
        characters_around_and_without_conflicts = [character for character in characters_around
                                                   if character not in characters_with_open_confrontation]
        if characters_around_and_without_conflicts:
            candidate = self.random.choice(list(characters_around_and_without_conflicts))
            self._confront(candidate, t, event_id)
            return

        self._move_randomly(t, event_id, characters_around)

    def _confront(self, antagonist, t, event_id):
        character_has_open_story_arcs = any(conflict for conflict in self.open_conflicts if conflict.is_story_arc)

        is_story_arc = False if character_has_open_story_arcs else bool(self.random.getrandbits(1))

        conflict = Conflict(antagonist, is_story_arc)
        self.open_conflicts.append(conflict)

        event = Event(t, event_id, is_story_arc, 'confront', [self.name], [antagonist.name], [], [], [])
        antagonist.add_event(event)
        self.backstory.add_event(event)
        self.world.add_world_event(event)

    def add_event(self, event):
        self.backstory.add_event(event)
