import bz2
import csv
import gc
import os
import pickle
from typing import NamedTuple, Set

AssociationRule = NamedTuple('AssociationRule', [('antecedents', Set), ('consequents', Set), ('confidence', float)])


class AssociationRulesEvaluator(object):
    def __init__(self, association_rules_resource):
        self.association_rules_resource = association_rules_resource
        self.pickle_file = f'{self.association_rules_resource}.plk'
        self.trope_rules = {}
        self.rules = []

    def prepare(self):
        if os.path.exists(self.pickle_file):
            with open(self.pickle_file, 'rb') as handler:
                try:
                    gc.disable()
                    self.rules = pickle.load(handler)
                finally:
                    gc.enable()
        else:
            with bz2.open(self.association_rules_resource) as handler:
                binary_content = handler.read()
            content = binary_content.decode()
            lines = content.split('\n')
            reader = csv.reader(lines)
            header = next(reader)
            for index, row in enumerate(reader):
                if not row:
                    continue
                if index % 100000 == 0:
                    print(f'rows processed: {index}')

                antecedents = eval(row[0])
                consequents = eval(row[1])
                confidence = eval(row[5])

                rule = AssociationRule(antecedents, consequents, confidence)
                self.rules.append(rule)

            with open(self.pickle_file, 'wb') as handler:
                pickle.dump(self.rules, handler, protocol=pickle.HIGHEST_PROTOCOL)

        for index, rule in enumerate(self.rules):
            if index % 100000 == 0:
                print(f'rules indexed: {index}')

            for trope in rule.antecedents.union(rule.consequents):
                if trope not in self.trope_rules:
                    self.trope_rules[trope] = set()
                self.trope_rules[trope].add(rule)

    # @lru_cache(maxsize=None)
    def evaluate_just_rating(self, list_of_tropes: list):
        candidate_rules = set()
        for trope in list_of_tropes:
            if trope in self.trope_rules:
                candidate_rules = candidate_rules.union(self.trope_rules[trope])

        confidences = []
        for candidate_consequent in list_of_tropes:
            confidence = 0
            required_antecedents = set([trope for trope in list_of_tropes if trope != candidate_consequent])
            for rule in candidate_rules:
                if rule.antecedents.issubset(required_antecedents) and candidate_consequent in rule.consequents:
                    confidence = max(confidence, rule.confidence)
            confidences.append(confidence)

        return sum(confidences)


def evaluate(evaluator, tropes):
    rating = evaluator.evaluate_just_rating(tuple(tropes))
    print(f'Rating for {tropes}: {rating}')


if __name__ == '__main__':
    evaluator = AssociationRulesEvaluator(
        '/Users/phd/Downloads/imdb_tvtropes_datasets_202008/association_rules_[0_01, 0_5].csv.bz2')
    evaluator.prepare()
    evaluate(evaluator, ['BigBad', 'ChekhovsGun', 'ExplodingFishTanks'])
    evaluate(evaluator,
             ['ActuallyPrettyFunny', 'Adorkable', 'AlmostKiss', 'AsHimself', 'AustralianMovies', 'BigHeroicRun',
              'ButNowIMustGo', 'ButtMonkey', 'CelebCrush', 'ContrivedCoincidence', 'CreatorCameo', 'DayInTheLife',
              'DeadpanSnarker', 'DirtyOldMan', 'DoubleEntendre', 'EveryoneIsJesusInPurgatory', 'FilmsOfThe1970s',
              'GettingCrapPastTheRadar', 'InsistentTerminology', 'Instrumentals', 'LandingGearShot', 'LifeEmbellished',
              'ManipulativeEditing', 'MsFanservice', 'MusicStories', 'MythologyGag', 'NonActorVehicle', 'Paparazzi',
              'RaceAgainstTheClock', 'RealityHasNoSubtitles', 'ReluctantFanserviceGirl', 'SexyDiscretionShot',
              'SilentSnarker', 'Squee', 'SwedishMedia', 'TheCameo', 'TheIngenue', 'ThemeMusicPowerUp', 'ThemeTuneCameo',
              'ThreeWaySex', 'TroubledProduction', 'VoxPops', 'WardrobeMalfunction', 'WhoWearsShortShorts'])
    evaluate(evaluator, ['AmericanFilms', 'InUniverse', 'ChekhovsGun'])
    
