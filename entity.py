import logging
from dataclasses import dataclass, field
from typing import Callable, Protocol

from globalEnums import TermColor, DamageType, ItemType, Point, ImlaConstants
from levelData import LevelData, are_points_in_LOS, a_star_search, reconstruct_path

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

    def move_to(self, new_pos: Point, level_data: LevelData):
        # Should likely be a little more involved
        if 0 <= new_pos.x <= level_data.width and 0 <= new_pos.y <= level_data.height:
            if not level_data.tiles[new_pos].is_blocking_move:
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
    pos: Point
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

    def move_to(self, new_pos: Point):
        """Updates position, but does not check validity of new_pos"""
        logging.debug(f"{self.name} is moving to {new_pos = } from {self.pos}")
        self.pos = new_pos

    def look_at(self) -> str:
        """This may end up just being a separate 'long_name' field for monsters"""
        logging.debug(f"Something is standing here named {self.name}")
        return f"Something is standing here named {self.name}"

    def attack(self, target: Targetable):
        logging.debug(f"{self.name} attacks {target}!")


def melee_monster_update(self: Monster, level_data: LevelData):
    """Tick up action points"""
    self.action_points += self.speed

    # while action points are > NORMAL_SPEED (12), do stuff
    while self.action_points >= ImlaConstants.BASE_SPEED:
        # -subtract 12 AP
        self.action_points -= ImlaConstants.BASE_SPEED

        # Look to see if player is in melee range, if so attack, if not then see if player is in LOS
        player = level_data.player
        if abs(self.pos.x - player.pos.x) <= 1 and abs(self.pos.y - player.pos.y) <= 1:
            # If player is in melee range
            logging.debug(f"Monster is adjacent to player, attacking!")
            # Actually attack here
        else:
            # Player is not in melee range, so check if they are in LOS
            if are_points_in_LOS(self.pos, player.pos, level_data):
                # Player is in LOS, so store path and path towards them
                # logging.debug(f"Monster at {self.pos} can see player at {player.pos}")
                came_from, cost_so_far = a_star_search(level_data=level_data, start_pos=self.pos, goal_pos=player.pos)
                self.stored_path = reconstruct_path(came_from=came_from, start_point=self.pos, goal_point=player.pos)
                self.move_to(self.stored_path.pop(0))
            else:
                # Player is not in LOS, check if monster has a path already (ie. previously saw player)
                # logging.debug(f"Monster at {self.pos} cannot see player at {player.pos}, {hasattr(self, 'stored_path')}")
                if hasattr(self, 'stored_path') and len(self.stored_path) > 0:
                    self.move_to(self.stored_path.pop(0))


def ranged_monster_update(self: Monster, level_data: LevelData):
    pass


def hunter_monster_update(self: Monster, level_data: LevelData):
    pass


@dataclass()
class FloorEffect:
    """This is for things like fire/poison clouds that have an effect each turn, but aren't targetable"""
    name: str
    pos: Point
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


def fire_burn_update(self: FloorEffect, level_data: LevelData):
    """An example floor effect"""
    """Check level_data for a player or monster in range
        if they exist, then make them take_damage()"""
    pass


@dataclass()
class Interactable:
    """This is for things like fire/poison clouds that have an effect each turn, but aren't targetable"""
    name: str
    pos: Point
    display_char: str
    display_color: TermColor
    interaction_update: Callable
    is_visible: bool = True
    blocks_LOS: bool = False

    def on_interact(self, level_data: LevelData):
        """Do some specific thing, like drop loot, or open a door"""
        self.interaction_update(self, level_data)


def chest_on_open(self: Interactable, level_data: LevelData):
    """Example interaction_update function"""
    """These are going to be odd/diverse, I think"""
    """Spawns/drops a floor_item"""
    pass
