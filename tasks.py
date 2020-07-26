import time
from random import Random

from invoke import task

from elements.world import World
from scraper.tropes_resource_builder import TropesResourceBuilder


@task
def world(context, seed=None, grid_size=2, characters=5, iterations=10, show_labels=False):
    seed = int(time.time() * 1000000) if seed is None else seed
    random = Random(seed)
    print(f'Seed: {seed}')

    world = World(random, grid_size, characters, iterations)
    world.build()
    world.run()
    print(world.get_events(show_labels) + '\n')
    print(world.get_characters_events(show_labels))


@task
def build_tropes_resource(context, recursion_level=2):
    builder = TropesResourceBuilder(recursion_level=recursion_level)
    builder.build_resource()
    builder.store_tree()
