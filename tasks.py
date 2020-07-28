import time
from random import Random
from sys import stderr

from invoke import task

from elements.world import World
from scraper.tropes_resource_builder import TropesResourceBuilder


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
