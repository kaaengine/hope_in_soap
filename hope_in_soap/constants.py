import enum
from pathlib import Path

from kaa.geometry import Vector
from kaa.sprites import Sprite, split_spritesheet


LANE_HERO_SLOTS = [
    Vector(3 + (109 * i), 220)
    for i in range(-2, 3)
]

LANE_ENEMY_SLOTS = [
    Vector(3 + (109 * i), -500)
    for i in range(-2, 3)
]


class CollisionTrigger(enum.IntEnum):
    border = enum.auto()
    soap = enum.auto()
    runner_enemy = enum.auto()
    runner_pickup = enum.auto()


ASSETS_DIRECTORY = Path(__file__).parent / 'assets'
assert ASSETS_DIRECTORY.is_dir()

SPRITE_WATER_BACK = Sprite(str(ASSETS_DIRECTORY / 'bg.png'))
SPRITE_WATER_FRONT = Sprite(str(ASSETS_DIRECTORY / 'fasterbg.png'))
SPRITE_HAND = Sprite(str(ASSETS_DIRECTORY / 'hand.png'))
SPRITE_FRAMES_SOAP = split_spritesheet(
    Sprite(str(ASSETS_DIRECTORY / 'soapthis.png')), Vector(138, 364),
)
SPRITE_SOAP_METER = Sprite(str(ASSETS_DIRECTORY / 'sopaometer.png')).crop(Vector(10, 0),
                                                                     Vector(285, 24))
SPRITE_FRAMES_VIRUS = split_spritesheet(
    Sprite(str(ASSETS_DIRECTORY / 'coronavirus.png')), Vector(90, 109),
)
SPRITE_ANTIVIRUS = Sprite(str(ASSETS_DIRECTORY / 'antiv.png'))
SPRITE_LIQUID_SOAP = Sprite(str(ASSETS_DIRECTORY / 'liquidsoap.png'))
SPRITE_OIL = Sprite(str(ASSETS_DIRECTORY / 'oil.png'))
SPRITE_FRAMES_MINI_SOAP = split_spritesheet(
    Sprite(str(ASSETS_DIRECTORY / 'bonus1.png')), Vector(100, 100),
)
SPRITE_FRAMES_PEOPLE = [
    Sprite(str(ASSETS_DIRECTORY / f'person{i}.png'))
    for i in range(1, 7)
]
