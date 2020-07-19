from elements.event import Event


class BackStory(list):
    def add_event(self, event: Event) -> None:
        self.append(event)
