import json

from elements.event import Event


class BackStory(list):
    def add_event(self, event: Event) -> None:
        self.append(event)

    def get_events_as_text(self, show_labels=False):
        content = []
        for event in self:
            event_info = event._asdict() if show_labels else event
            content.append(f'  {json.dumps(event_info)}')
        content_as_text = ',\n'.join(content)

        lines = ['[', content_as_text, ']']
        return '\n'.join(lines)

    def get_events_as_dictionary(self, show_labels=False):
        events = []
        for event in self:
            events.append(event._asdict() if show_labels else list(event))
        return events
