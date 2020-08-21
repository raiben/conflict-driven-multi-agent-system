from sys import stderr
from time import sleep

from pip._vendor import requests


class RequestUtils(object):
    @staticmethod
    def get_content(cache, trope_url):
        cached_value = cache.get(trope_url, default=None)
        if cached_value is not None:
            return cached_value

        sleep(1)
        try:
            request = requests.get(trope_url)
            content = ''
            if request.status_code == 200:
                content = request.text
            if request.status_code == 200 or request.status_code == 404:
                cache.set(trope_url, content)
            return content
        except Exception as exception:
            print(exception, file=stderr)
            return ''
