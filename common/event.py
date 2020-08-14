from enum import Enum
from typing import NamedTuple, List


class EventType(Enum):
    NOOP = 'noop'
    MOVE = 'move'
    CONFRONT = 'confront'
    CHASE_RESOLUTION = 'chase_resolution'
    RESOLVE = 'resolve'


Event = NamedTuple('Event', [
    ('t', int), ('id', int), ('is_story_arc', bool), ('action', str), ('protagonists', List[str]),
    ('antagonists', List[str]), ('direct_complements', List[str]), ('indirect_complements', List[str]),
    ('places', List[str])
])
