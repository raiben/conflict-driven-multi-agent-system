import re


def uncamel(text):
    return re.sub(r'([a-z])([A-Z])', r'\1 \2', text)
