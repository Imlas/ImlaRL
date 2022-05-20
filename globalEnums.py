from enum import Enum


class TermColor(Enum):
    BLACK = (0, 0, 0)
    DARK_GREY = (50, 50, 50)
    MID_GREY = (96, 96, 96)
    LIGHT_GREY = (192, 192, 192)
    WHITE = (255, 255, 255)
    RED = (197, 15, 31)
    MAGENTA = (136, 23, 152)
    GREEN = (19, 161, 14)


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
