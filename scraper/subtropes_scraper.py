from sys import stderr

from diskcache import Cache
from lxml.html import fromstring

from scraper.utils.request_utils import RequestUtils


class SubTropesScraper(object):
    TROPE_URL_PREFIX = 'https://tvtropes.org/pmwiki/pmwiki.php/Main/'
    TROPE_DETECTOR = '/Main/'

    cache = Cache('cache')

    def __init__(self, trope_name):
        self.trope_name = trope_name

    def get_related(self):
        trope_url = f'{self.TROPE_URL_PREFIX}{self.trope_name}'
        content = RequestUtils.get_content(self.cache, trope_url)
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
