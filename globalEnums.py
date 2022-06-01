from collections import namedtuple
from enum import Enum
from typing import Protocol


class TermColor(Enum):
    # https://html-color.codes/
    BLACK = (0, 0, 0)
    DARK_GREY = (50, 50, 50)
    MID_GREY = (96, 96, 96)
    LIGHT_GREY = (192, 192, 192)
    WHITE = (255, 255, 255)
    SLATE = (112, 128, 144)
    RED = (255, 0, 0)
    CRIMSON = (197, 15, 31)
    FIREBRICK = (178, 34, 34)
    SOFT_RED = (205, 92, 92)
    ORANGE_RED = (255, 69, 0)
    BROWN = (165, 42, 42)
    SIENNA = (160, 82, 45)
    TAN = (210, 180, 140)
    ORANGE = (255, 165, 0)
    CORAL = (255, 127, 80)
    GOLD = (255, 215, 0)
    YELLOW = (255, 255, 0)
    LEMON = (255, 244, 79)
    BANANA = (255, 225, 53)
    LIME = (0, 255, 0)
    OLIVE = (128, 128, 0)
    DARK_OLIVE = (85, 107, 47)
    GREEN = (19, 161, 14)
    DARK_GREEN = (0, 100, 0)
    TEAL = (0, 128, 128)
    CYAN = (0, 255, 255)
    DIAMOND = (185, 242, 255)
    BLUE = (0, 0, 255)
    LIGHT_BLUE = (173, 216, 230)
    DARK_BLUE = (0, 0, 139)
    PURPLE = (128, 0, 128)
    LAVENDER = (230, 230, 250)
    MAGENTA = (255, 0, 255)
    VIOLET = (238, 130, 238)
    HOT_MAGENTA = (255, 29, 206)
    PINK = (255, 192, 203)
    HOT_PINK = (255, 105, 180)


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
