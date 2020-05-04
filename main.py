import sys

from kaa.engine import Engine
from kaa.geometry import Vector


sys.path.append('')

from hope_in_soap.scenes import GameplayScene 


if __name__ == '__main__':
    with Engine(virtual_resolution=Vector(1280, 720)) as engine:
        engine.run(GameplayScene())
