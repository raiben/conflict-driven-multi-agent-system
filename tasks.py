import time
from random import Random
from sys import stderr

from invoke import task

from skeleton.world import World
from scraper.tropes_resource_builder import TropesResourceBuilder
from storyteller.forgetful_story_teller import ForgetfulStoryTeller
from trope_selector.trope_selector import TropeSelector


@task
def world(context, seed=None, grid_size=2, characters=5, iterations=10, show_labels=False, output_file=None):
    seed = int(time.time() * 1000000) if seed is None else seed
    random = Random(seed)
    print(f'Seed: {seed}', file=stderr)

    world = World(random, grid_size, characters, iterations)
    world.build()
    world.run()
    world.store_events_as_json(seed, show_labels, output_file)


@task
def build_tropes_resource(context, recursion_level=2, output_file=None):
    builder = TropesResourceBuilder(recursion_level)
    builder.retrieve_resource()
    builder.store_tree_as_json(output_file)


@task
def make_up_random_story(context, world_resource, tropes_resource, seed=None, extended_dataset_resource=None):
    seed = int(time.time() * 1000000) if seed is None else int(seed)
    random = Random(x=seed)
    print(f'Seed: {seed}', file=stderr)

    general_seed = seed + 1
    print(f'General seed (old-style): {general_seed}', file=stderr)

    selector = TropeSelector(random, world_resource, tropes_resource, general_seed, extended_dataset_resource)
    selector.prepare()
    tropes = selector.select_random_tropes()

    teller = ForgetfulStoryTeller(random, world_resource)
    teller.prepare()
    story = teller.tell_story(tropes)
    print(story)

@task
def make_up_best_story(context, world_resource, tropes_resource, neural_network_file, seed=None,
                       extended_dataset_resource=None):
    seed = int(time.time() * 1000000) if seed is None else int(seed)
    random = Random(x=seed)
    print(f'Seed: {seed}', file=stderr)

    general_seed = seed+1
    print(f'General seed (old-style): {general_seed}', file=stderr)

    selector = TropeSelector(random, world_resource, tropes_resource, general_seed, extended_dataset_resource,
                             neural_network_file)
    selector.prepare()
    tropes = selector.select_best_tropes()

    teller = ForgetfulStoryTeller(random, world_resource)
    teller.prepare()
    story = teller.tell_story(tropes)
    print(story)