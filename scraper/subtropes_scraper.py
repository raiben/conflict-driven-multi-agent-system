from sys import stderr
from time import sleep

from pip._vendor import requests
from diskcache import Cache
from lxml.html import fromstring

class SubTropesScraper(object):
    TROPE_URL_PREFIX = 'https://tvtropes.org/pmwiki/pmwiki.php/Main/'
    TROPE_DETECTOR = '/Main/'

    cache = Cache('cache')
    def __init__(self, trope_name):
        self.trope_name = trope_name

    def get_related(self):
        trope_url = f'{self.TROPE_URL_PREFIX}{self.trope_name}'
        content = self._get_content(trope_url)
        if not content:
            return []

        related_list = []
        document = fromstring(content)
        links = document.cssselect('#main-article a')
        for link in links:
            try:
                reference = link.attrib['href']
                if self.TROPE_DETECTOR in reference:
                    trope = reference.split(self.TROPE_DETECTOR)[1]
                    related_list.append(trope)
            except KeyError:
                print(f'Link {link} with no href. Skipping', file=stderr)

        return related_list


    def _get_content(self, trope_url):
        cached_value = self.cache.get(trope_url, default=None)
        if cached_value is not None:
            return cached_value

        sleep(1)
        request = requests.get(trope_url)
        content = ''

        if request.status_code == 200:
            content = request.text

        if request.status_code == 200 or request.status_code == 404:
            self.cache.set(trope_url, content)

        return content
