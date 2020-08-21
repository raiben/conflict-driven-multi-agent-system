import json
from sys import stderr

from diskcache import Cache
from lxml.html import fromstring
import statistics as st

from scraper.utils.request_utils import RequestUtils


class CharactersByFilmBuilder(object):
    cache = Cache('cache')

    def __init__(self, extended_dataset_resource, output_file):
        self.extended_dataset_resource = extended_dataset_resource
        self.output_file = output_file
        self.films = []
        self.characters_by_film = {}

    def prepare(self):
        with open(self.extended_dataset_resource, 'r') as handler:
            handler.readline()
            line = handler.readline()
            while line:
                line = line.strip()
                if line:
                    film = line.split(',')[1]
                    self.films.append(film)
                line = handler.readline()

    def run(self):
        for film in self.films:
            film_characters = self._get_film_characters(film)
            if film_characters:
                if len(film_characters) < 4 or len(film_characters)>30:
                    print(f'Please, check that the characters in the {film} are fine: {film_characters}', file=stderr)
                self.characters_by_film[film] = film_characters
            pass

    def _get_film_characters(self, film):
        film_url = f'https://tvtropes.org/pmwiki/pmwiki.php/Characters/{film}'
        characters = []

        content = RequestUtils.get_content(self.cache, film_url)
        if not content:
            return characters

        document = fromstring(content)
        subpage_links = document.cssselect('ul.subpage-links li a')
        for link in subpage_links:
            if 'href' in link.attrib and '/pmwiki.php/Characters/' in link.attrib['href']:
                url = link.attrib['href']
                url = url if url.startswith('https://tvtropes.org/') \
                    else f'https://tvtropes.org{url}'
                url = url.split('?')[0]
                content = RequestUtils.get_content(self.cache, url)
                document = fromstring(content)
                character_elements_folder = document.cssselect('div.folderlabel')
                character_elements_folder = [element for element in character_elements_folder if 'open/close all folders' not in element.text_content()]
                character_elements_h2 = document.cssselect('h2') #'div.folderlabel')
                character_elements = character_elements_folder \
                    if len(character_elements_folder) > len(character_elements_h2) \
                    else character_elements_h2

                if len(character_elements)>0 and all(element.text_content().startswith('Characters ') for element in character_elements):
                    print(f'Please, confirm that the film {film} is not using tropes...', file=stderr)
                    character_elements = document.cssselect('a.twikilink')
                    character_elements = [element for element in character_elements if
                                          '/Character/' in element.attrib['href']]

                for element in character_elements:
                    character = element.text_content().replace('\xa0', '').strip()
                    characters.append(character)

                    # should_consider_character = all(word not in character for word in self.NON_CHARACTER_WORDS)
                    # is_valid_character = all(word not in character for word in self.WRONG_CHARACTER_WORDS)
                    # if should_consider_character and is_valid_character:
                    #     characters.append(character)
                    # elif should_consider_character:
                    #     print(f'Film: {url} has wrong character {character}', file=stderr)

        return characters


    def get_summaries(self):
        characters = [len(characters) for characters in self.characters_by_film.values()]
        return {
            'mean': st.mean(characters),
        }


    def _scrape_number_of_character(self, film_characters_page):
        pass

    def store(self):
        content = json.dumps(self.characters_by_film, sort_keys=True, indent=2)
        if self.output_file:
            with open(self.output_file, 'w') as handler:
                handler.write(content)
        else:
            print(content)
