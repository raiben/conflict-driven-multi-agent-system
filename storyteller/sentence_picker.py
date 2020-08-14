import json


class SentencePicker(object):
    def __init__(self, random, sentences_resource_file):
        self.random = random
        self.sentences_resource_file = sentences_resource_file
        self.sentences = []
        self.used_sentences = set()

    def get_sentence(self, **kwargs):
        self._lazy_load()
        if len(self.used_sentences) == len(self.sentences):
            self.reset()

        available_sentences = [sentence for sentence in self.sentences if sentence not in self.used_sentences]
        sentence_template = self.random.choice(available_sentences)
        self.used_sentences.add(sentence_template)
        try:
            return sentence_template.format(**kwargs)
        except KeyError:
            raise Exception(f'Please, review the template: {sentence_template} with keywords {json.dumps(kwargs)}')


    def _lazy_load(self):
        if not self.sentences:
            current_folder_directories = __file__.split('/')[:-1]
            resource_full_path = '/'.join(current_folder_directories + [self.sentences_resource_file])
            with open(resource_full_path, 'r') as handler:
                for line in handler.readlines():
                    if line.strip() and not line.startswith('#'):
                        self.sentences.append(line.strip())
            self.reset()

    def reset(self):
        self.used_sentences = set()
