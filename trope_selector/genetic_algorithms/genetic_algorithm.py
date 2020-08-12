import random

from deap import creator, base, tools, algorithms

from common.event import EventType
from trope_selector.evaluators.neural_network_tropes_evaluator import NeuralNetworkTropesEvaluator


class GeneticAlgorithm(object):
    def __init__(self, random, characters, global_events, events_by_id, character_tropes, move_tropes, confront_tropes,
                 chase_resolution_tropes,resolve_tropes, neural_network_file, old_style_seed):

        self.random = random
        self.characters = characters
        self.global_events = global_events
        self.events_by_id = events_by_id
        self.character_tropes = character_tropes
        self.move_tropes = move_tropes
        self.confront_tropes = confront_tropes
        self.chase_resolution_tropes = chase_resolution_tropes
        self.resolve_tropes = resolve_tropes
        self.neural_network_file = neural_network_file
        self.old_style_seed = old_style_seed
        self.evaluator = None
        self.best = None

    def prepare(self):
        self.evaluator = NeuralNetworkTropesEvaluator(self.neural_network_file)

    def run(self):
        creator.create("FitnessMax", base.Fitness, weights=(1.0,))
        creator.create("Individual", list, fitness=creator.FitnessMax)

        toolbox = base.Toolbox()
        toolbox.register("population", self.build_population(), creator.Individual)
        toolbox.register("evaluate", self.build_evaluator())
        toolbox.register("mate", tools.cxTwoPoint)

        toolbox.register("mutate", self.build_mutator(), indpb=0.05)
        toolbox.register("select", tools.selTournament, tournsize=3)

        random.seed(self.old_style_seed)
        population = toolbox.population(n=300)

        NGEN = 20
        for gen in range(NGEN):
            offspring = algorithms.varAnd(population, toolbox, cxpb=0.5, mutpb=0.1)
            fits = toolbox.map(toolbox.evaluate, offspring)
            for fit, ind in zip(fits, offspring):
                ind.fitness.values = fit
            population = toolbox.select(offspring, k=len(population))
            best = tools.selBest(population, k=1)[0]
            print(f'Generation={gen}, fitness={best.fitness.values[0]}, tropes={list(best)}')

        self.best = tools.selBest(population, k=1)[0]
        self.fitness = self.best.fitness.values[0]

    def build_population(self):
        def load_individuals(creator, n):
            individuals = []
            for i in range(n):
                character_tropes = []
                for character in self.characters:
                    character_tropes.append(self.random.choice(self.character_tropes))

                event_tropes = []
                for event in self.global_events:
                    candidates = []
                    if event.action == EventType.MOVE.value:
                        candidates = self.move_tropes
                    if event.action == EventType.CONFRONT.value:
                        candidates = self.confront_tropes
                    if event.action == EventType.CHASE_RESOLUTION.value:
                        candidates = self.chase_resolution_tropes
                    if event.action == EventType.RESOLVE.value:
                        candidates = self.resolve_tropes

                    index = self.random.choice(candidates) if candidates else None
                    event_tropes.append(index)

                individual = creator(character_tropes + event_tropes)
                individuals.append(individual)

            return individuals

        return load_individuals

    def build_evaluator(self):
        def evaluate(individual):
            evaluator = self.evaluator
            trope_set = set(individual)
            if None in trope_set:
                trope_set.remove(None)
            evaluation = evaluator.evaluate(trope_set)
            return evaluation.rating[0],

        return evaluate

    def build_mutator(self):
        def mutator(individual, indpb):
            for i in range(len(individual)):
                if self.random.random() < indpb:
                    candidates = []
                    if i<len(self.characters):
                        candidates = self.character_tropes
                    else:
                        events_index = i - len(self.characters)
                        action = self.global_events[events_index].action
                        if action == EventType.MOVE.value:
                            candidates = self.move_tropes
                        if action == EventType.CONFRONT.value:
                            candidates = self.confront_tropes
                        if action == EventType.CHASE_RESOLUTION.value:
                            candidates = self.chase_resolution_tropes
                        if action == EventType.RESOLVE.value:
                            candidates = self.resolve_tropes

                    trope = self.random.choice(candidates) if candidates else None
                    individual[i] = trope

            return individual,

        return mutator

    def get_best(self):
        return self.best