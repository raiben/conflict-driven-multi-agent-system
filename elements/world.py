import json
import math
from collections import OrderedDict
from datetime import datetime
from random import Random

from elements.backstory import BackStory
from elements.character import Character


class World(object):
    def __init__(self, random: Random, grid_size: int, character_size: int, iterations: int) -> None:
        self.random = random
        self.grid_size = grid_size
        self.character_size = character_size
        self.iterations = iterations

        self.positions = None
        self.characters = None
        self.backstory = None
        self.run_at = None

    def build(self):
        self.backstory = BackStory()

        self.positions = []
        for x in range(0, self.grid_size):
            row = []
            for y in range(0, self.grid_size):
                position = set()
                row.append(position)
            self.positions.append(row)

        self.characters = []
        for c in range(0, self.character_size):
            character = Character(self, c, self.random)
            self.characters.append(character)

            random_x = self.random.randint(0, self.grid_size - 1)
            random_y = self.random.randint(0, self.grid_size - 1)
            random_position = self.positions[random_x][random_y]
            random_position.add(character)

    def run(self):
        self.run_at = datetime.now()
        t = 0
        event_id = 0

        for iteration in range(0, self.iterations):
            randomized_characters = self.characters.copy()
            self.random.shuffle(randomized_characters)

            for character in randomized_characters:
                character.play(t, event_id)
                event_id += 1
            t += 1

    def add_world_event(self, event):
        self.backstory.add_event(event)

    def get_position(self, character):
        for y in range(0, self.grid_size):
            for x in range(0, self.grid_size):
                if character in self.positions[x][y]:
                    return f'{x}, {y}'

        return 'Unknown'

    def get_characters_around(self, character):
        for y in range(0, self.grid_size):
            for x in range(0, self.grid_size):
                if character in self.positions[x][y]:
                    return self.positions[x][y].difference({character})

        return set()

    def get_events(self, show_labels):
        return self.backstory.get_events_as_dictionary(show_labels)

    def move_character(self, character, direction=None):
        move_map = {'up': self._move_up, 'down': self._move_down, 'left': self._move_left, 'right': self._move_right}
        if direction is None:
            move = self.random.choice(list(move_map.values()))
        else:
            move = move_map[direction]
        move(character)

    def _move_up(self, character):
        def calculator(world, x, y):
            return x, (y + 1) % world.grid_size

        self._move_handler(character, calculator)

    def _move_down(self, character):
        def calculator(world, x, y):
            return x, (y - 1 + world.grid_size) % world.grid_size

        self._move_handler(character, calculator)

    def _move_left(self, character):
        def calculator(world, x, y):
            return (x - 1 + world.grid_size) % world.grid_size, y

        self._move_handler(character, calculator)

    def _move_right(self, character):
        def calculator(world, x, y):
            return (x + 1) % world.grid_size, y

        self._move_handler(character, calculator)

    def _move_handler(self, character, new_position_calculator):
        for y in range(0, self.grid_size):
            for x in range(0, self.grid_size):
                if character in self.positions[x][y]:
                    self.positions[x][y].remove(character)
                    new_x, new_y = new_position_calculator(self, x, y)
                    self.positions[new_x][new_y].add(character)
                    return

    def get_closer_antagonist(self, character, antagonists):
        if not antagonists:
            return None, None

        characters_map = {character: None for character in [character] + antagonists}
        for y in range(0, self.grid_size):
            for x in range(0, self.grid_size):
                candidates_not_found = [key for key in characters_map.keys() if characters_map[key] is None]
                for candidate in candidates_not_found:
                    if candidate in self.positions[x][y]:
                        characters_map[candidate] = (x, y)

        x1, y1 = characters_map[character]
        del characters_map[character]

        min_distance = float('inf')
        min_x_mov = None
        min_y_mov = None
        min_candidate = None

        for candidate, position in characters_map.items():
            x, y = position
            for y_diff in [-self.grid_size, 0, self.grid_size]:
                for x_diff in [-self.grid_size, 0, self.grid_size]:
                    x2 = x + x_diff
                    y2 = y + y_diff
                    distance = self.calculate_distance(x1, y1, x2, y2)
                    if distance < min_distance:
                        min_x_mov = x2 - x1
                        min_y_mov = y2 - y1
                        min_candidate = candidate

        option_y = 'up' if min_y_mov < 0 else 'down'
        option_x = 'left' if min_x_mov < 0 else 'right'
        option = option_x if abs(min_x_mov) > abs(min_y_mov) else option_y

        return min_candidate, option

    def calculate_distance(self, x1, y1, x2, y2):
        return math.sqrt((x2 - x1) ** 2 + (y2 - y1) ** 2)

    def store_events_as_json(self, seed, show_labels=False, output_file=None):
        world_dictionary = OrderedDict()
        world_dictionary['META'] = OrderedDict([
            ('SEED', seed), ('GRID_SIZE', self.grid_size), ('CHARACTER_SIZE', self.character_size),
            ('ITERATIONS', self.iterations), ('RUN_AT', self.run_at.isoformat())])
        world_dictionary['CHARACTERS'] = [character.name for character in self.characters]
        world_dictionary['CHARACTERS'] = [character.name for character in self.characters]
        world_dictionary['EVENTS'] = OrderedDict()
        world_dictionary['EVENTS']['GLOBAL'] = self.backstory.get_events_as_dictionary(show_labels)
        for character in self.characters:
            world_dictionary['EVENTS'][character.name] = character.backstory.get_events_as_dictionary(show_labels)
        content = json.dumps(world_dictionary, indent=2)

        if output_file:
            with open(output_file, 'w') as handler:
                handler.write(content)
        else:
            print(content)
