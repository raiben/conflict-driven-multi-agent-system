import csv
import logging
from functools import lru_cache

import joblib

from common.string_utils import humanize_list


class NeuralNetworkTropesEvaluator():
    _logger = logging.getLogger(__name__)

    def __init__(self, neural_network_dumped_file: str):
        self._load_neural_network(neural_network_dumped_file)

    def _load_neural_network(self, neural_network_dumped_file):
        self.evaluator_resources = joblib.load(neural_network_dumped_file)
        self.neural_network = self.evaluator_resources['evaluator']
        self.tropes = self.evaluator_resources['inputs']
        self.tropes_reverse_index = {}
        for index, trope in enumerate(self.tropes):
            self.tropes_reverse_index[trope] = index

        self.base_empty_input = [0 for index in range(0, len(self.tropes))]

    def evaluate(self, list_of_tropes: list):
        trope_indexes = self._build_list_of_trope_indexes(list_of_tropes)
        input = self._build_input(trope_indexes)
        predicted_rating = self.neural_network.predict([input])

        evaluation_tropes = [EvaluationTrope(name=self.tropes[index], index=index) for index in trope_indexes]
        evaluation = Evaluation(tropes=evaluation_tropes, rating=predicted_rating)
        return evaluation

    @lru_cache(maxsize=None)
    def evaluate_just_rating(self, list_of_tropes: list):
        trope_indexes = self._build_list_of_trope_indexes(list_of_tropes)
        input = self._build_input(trope_indexes)
        return self.neural_network.predict([input])

    def _build_input(self, trope_indexes):
        input = self.base_empty_input.copy()
        for index in trope_indexes:
            input[index] = 1
        return input

    def _build_list_of_trope_indexes(self, list_of_tropes):
        indexes = [element if isinstance(element, int) else self.tropes_reverse_index.get(element, None)
                   for element in list_of_tropes]
        return [index for index in indexes if index is not None]


class Evaluation(object):
    def __init__(self, tropes, rating: float):
        self.tropes = tropes
        self.rating = rating

    def __str__(self):
        return f'Evaluation [{humanize_list(self.tropes)}]->{self.rating}'


class EvaluationTrope(object):
    def __init__(self, name: str, index: int):
        self.name = name
        self.index = index

    def __str__(self):
        return f'{self.name}:{self.index}'


if __name__ == "__main__":
    neural_network_file = u'/Users/phd/Downloads/imdb_tvtropes_datasets_202008/evaluator_[37343, 193, 1].sav'
    evaluator = NeuralNetworkTropesEvaluator(neural_network_file)

    import bz2
    import json
    films = [] # {name, rating, tropes}
    with open('/Users/phd/Downloads/imdb_tvtropes_datasets_202008/extended_dataset_202008.csv', "r") as f:
        heading = f.readline()
        columns = heading.split(',')
        lines = f.readlines()
        reader = csv.reader(lines)
        for index, line in enumerate(reader):
            if index%1000 == 0:
                print(f'Read {index} films')
            film = {'name': '', 'rating':0, 'tropes':[]}
            zipped_column_values = zip(columns, line)
            for column, value in zipped_column_values:
                if column == 'NameIMDB':
                    film['name'] = value
                if column == 'Rating':
                    film['rating'] = float(value)
                if column not in ['Id','NameTvTropes','NameIMDB','Rating','Votes','Year'] and value == '1':
                    film['tropes'].append(column)
            films.append(film)

    for film in films:
        film['evaluation'] = evaluator.evaluate_just_rating(film['tropes'])[0]

    average_error = sum([abs(film['rating']-film['evaluation']) for film in films])/len(films)
    print (f'average error={average_error}')

    errors_by_tropes = {}
    for film in films:
        key = len(film['tropes'])
        if key not in errors_by_tropes:
            errors_by_tropes[key] = []
        errors_by_tropes[key].append(abs(film['rating']-film['evaluation']))

    average_error_by_tropes = {key:sum(errors_by_tropes[key])/len(errors_by_tropes[key])
                               for key in errors_by_tropes.keys()}

    print('Average error by number of tropes')
    print(json.dumps(average_error_by_tropes, sort_keys=True, indent=2))

    print('Evaluation of 1 genre')
    genres = [trope for trope in evaluator.tropes if '[GENRE]' in trope]
    genres_evaluation = {genre:evaluator.evaluate_just_rating(genre)[0] for genre in genres}
    print(json.dumps(genres_evaluation, sort_keys=True, indent=2))
