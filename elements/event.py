from typing import NamedTuple, List

Event = NamedTuple('Event', [
    ('t', int), ('id', int), ('action', str), ('is_story_arc', bool), ('protagonists', List[str]),
    ('antagonists', List[str]), ('direct_complements', List[str]), ('indirect_complements', List[str]),
    ('places', List[str])
])
