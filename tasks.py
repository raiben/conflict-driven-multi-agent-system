import time
from random import Random

from invoke import task

from elements.world import World


@task
def world(context, seed=None, grid_size=20, characters=200, iterations=10, show_labels=False):
    seed = int(time.time() * 1000000) if seed is None else seed
    random = Random(seed)
    print(f'Seed: {seed}')

    world = World(random, grid_size, characters, iterations)
    world.build()
    world.run()
    print(world.get_events(show_labels))
