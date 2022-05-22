from collections import namedtuple
from enum import Enum
from typing import Protocol


class TermColor(Enum):
    BLACK = (0, 0, 0)
    DARK_GREY = (50, 50, 50)
    MID_GREY = (96, 96, 96)
    LIGHT_GREY = (192, 192, 192)
    WHITE = (255, 255, 255)
    RED = (197, 15, 31)
    MAGENTA = (136, 23, 152)
    GREEN = (19, 161, 14)
    GOLD = (255, 215, 0)


class DamageType(Enum):
    PHYSICAL = 0
    FIRE = 1
    LIGHTNING = 2
    COLD = 3
    CORROSIVE = 4


class ItemType(Enum):
    GOLD = 0
    DAGGER = 1
    SWORD = 2


class ImlaConstants:
    BASE_SPEED = 12


Point = namedtuple('Point', 'x y')


class Entity(Protocol):
    pos: Point
    display_char: str
    display_color: TermColor
    is_visible: bool


class Updatable(Protocol):
    def update(self, level_data):  # Unfortunately can't typehint level_data without circ references
        ...
