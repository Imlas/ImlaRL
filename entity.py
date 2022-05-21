import logging
from dataclasses import dataclass, field
from typing import Callable, Protocol

from globalEnums import TermColor, DamageType, ItemType
from levelData import LevelData

logging.basicConfig(filename='Imladebug.log', filemode='w', level=logging.DEBUG)


class Targetable(Protocol):
    def take_damage(self, damage: float, damage_type: DamageType):
        ...


@dataclass()
class Player:
    name: str
    pos: (int, int)
    display_char: str
    display_color: TermColor
    health_max: float
    health: float
    armor: dict[DamageType, int]
    attack_power: int
    xp: int
    next_level_xp: int
    inventory: list = field(default_factory=list)  # This will almost certainly get tweaked later
    speed: int = 12
    action_points: int = 0

    def take_damage(self, damage: float, damage_type: DamageType):
        pass

    def move_to(self, new_pos: (int, int), level_data: LevelData):
        # Should likely be a little more involved
        if 0 <= new_pos[0] <= level_data.width and 0 <= new_pos[1] <= level_data.height:
            if not level_data.tiles[new_pos[0]][new_pos[1]].is_blocking_move:
                self.pos = new_pos

    def melee_attack(self, target: Targetable):
        pass


@dataclass()
class FloorItem:
    name: str
    pos: (int, int)
    display_char: str
    display_color: TermColor
    is_visible: bool
    blocks_LOS: bool
    item_type: ItemType
    item_amount: int

    def look_at(self) -> str:
        """Returns an in-game formatted string describing the item"""
        pass

    def pick_up(self, player: Player):
        pass


@dataclass()
class Monster:
    name: str
    pos: (int, int)
    display_char: str
    display_color: TermColor
    health_max: float
    health: float
    armor: dict[DamageType, int]
    attack_power: int
    monster_update: Callable
    on_death_drop: (ItemType, int)
    is_visible: bool = True
    blocks_LOS: bool = False
    speed: int = 12
    action_points: int = 0

    def update(self, level_data: LevelData):
        self.monster_update(self, level_data)

    def take_damage(self, damage: float, damage_type: DamageType) -> float:
        # Damage multiplier = 1 - (0.06 * total armor) / (1 + 0.06 * abs(total armor))
        # Pull in appropriate armor value
        # Calc damage multiplier
        # Reduce HP
        # Check if it should die
        # If yes, drop items, award xp
        # Return how much damage was taken
        pass

    def move_towards(self, goal_pos: (int, int), level_data: LevelData):
        """Will pathfind towards goal_pos and (if a path is valid) take the first move"""
        pass

    def move_to(self, new_pos: (int, int)):
        """Updates position, but does not check validity of new_pos"""
        pass

    def look_at(self) -> str:
        """This may end up just being a separate 'long_name' field for monsters"""
        pass

    def attack(self, target: Targetable):
        pass


def melee_monster_update(self, level_data: LevelData):
    """Tick up action points"""

    """while action points are > NORMAL_SPEED (12), do stuff"""
    """ -subtract 12 AP"""
    """ Look to see if player is in melee range, if so attack, if not then see if player is in LOS"""
    """ If player is in LOS, pathfind towards player, if not then either stay still, or move to last pathfind target"""
    pass


def ranged_monster_update(self, level_data: LevelData):
    pass


@dataclass()
class FloorEffect:
    """This is for things like fire/poison clouds that have an effect each turn, but aren't targetable"""
    name: str
    pos: (int, int)  # TODO: migrate all of these into named tuples
    display_char: str
    display_color: TermColor  # have this effect the background color?
    attack_power: int
    effect_update: Callable
    ticks_remaining: int
    is_visible: bool = True
    blocks_LOS: bool = False

    def update(self, level_data: LevelData):
        self.effect_update(self, level_data)
        # if ticks_remaining == 0, then destroy self


def fire_burn_update(self, level_data: LevelData):
    """An example floor effect"""
    """Check level_data for a player or monster in range
        if they exist, then make them take_damage()"""
    pass


@dataclass()
class Interactable:
    """This is for things like fire/poison clouds that have an effect each turn, but aren't targetable"""
    name: str
    pos: (int, int)
    display_char: str
    display_color: TermColor
    interaction_update: Callable
    is_visible: bool = True
    blocks_LOS: bool = False

    def on_interact(self, level_data: LevelData):
        """Do some specific thing, like drop loot, or open a door"""
        self.interaction_update(self, level_data)


def chest_on_open(self, level_data: LevelData):
    """Example interaction_update function"""
    """These are going to be odd/diverse, I think"""
    """Spawns/drops a floor_item"""
    pass
