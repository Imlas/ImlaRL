import logging
import random
from dataclasses import dataclass, field
from typing import Callable, Protocol

from globalEnums import TermColor, DamageType, ItemType, Point, ImlaConstants
from levelData import LevelData, are_points_in_LOS, a_star_search, reconstruct_path, are_points_within_distance

logging.basicConfig(filename='Imladebug.log', filemode='w', level=logging.DEBUG)


class Targetable(Protocol):
    def take_damage(self, damage: float, damage_type: DamageType, level_data: LevelData) -> float:
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
    sight_range: int = 12

    def take_damage(self, damage: float, damage_type: DamageType, level_data: LevelData) -> float:
        logging.debug(f"Taking damage, {damage = } {damage_type = } against {self.armor[damage_type]} armor")
        net_damage = damage_after_mitigation(damage, self.armor[damage_type])
        self.health -= net_damage
        if self.health <= 0:
            logging.debug(f"Player health is below zero. Player is dead!")

        return net_damage

    def move_to(self, new_pos: Point, level_data: LevelData):
        # Should likely be a little more involved
        if 0 <= new_pos.x <= level_data.width and 0 <= new_pos.y <= level_data.height:
            if not level_data.tiles[new_pos].is_blocking_move:
                self.pos = new_pos

    def default_melee_attack(self, target: Targetable, level_data: LevelData):
        # logging.debug(f"{self.name} attacks {target}!")
        return target.take_damage(self.attack_power * 2, DamageType.PHYSICAL, level_data)


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
        """Adds the item to the player's inventory and removes it from the floor"""
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
    sight_range: int
    monster_update: Callable
    on_death_drop: (ItemType, int)
    is_visible: bool = True
    blocks_LOS: bool = False
    speed: int = 12
    action_points: int = 0

    def update(self, level_data: LevelData):
        self.monster_update(self, level_data)

    def take_damage(self, damage: float, damage_type: DamageType, level_data: LevelData) -> float:
        # logging.debug(f"Taking damage, {damage = } {damage_type = } against {self.armor[damage_type]} armor")
        net_damage = damage_after_mitigation(damage, self.armor[damage_type])
        self.health -= net_damage
        if self.health <= 0:
            logging.debug(f"Monster health is below zero. Monster is dead!")
            # Drop items
            # Reward XP?
            # Die
            level_data.monsters.remove(self)
        return net_damage

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

    def attack(self, target: Targetable, damage_amount: float, damage_type: DamageType, level_data: LevelData) -> float:
        """ """
        # logging.debug(f"{self.name} attacks {target}!")
        return target.take_damage(damage_amount, damage_type, level_data)


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
            raw_damage = random.randint(self.attack_power - 1, self.attack_power + 1)
            damage_done = self.attack(player, raw_damage, DamageType.PHYSICAL, level_data)
            # Display a some status message and/or update ui bits
            logging.debug(f"{self.name} attacked the player for {damage_done} damage!")
        else:
            # Player is not in melee range, so check if they are in LOS
            if level_data.tiles[self.pos].is_in_LOS and are_points_within_distance(player.pos, self.pos, self.sight_range):
                # Player is in LOS, so store path and path towards them
                logging.debug(f"Monster at {self.pos} can see player at {player.pos}")
                came_from, cost_so_far = a_star_search(level_data=level_data, start_pos=self.pos, goal_pos=player.pos)
                self.stored_path = reconstruct_path(came_from=came_from, start_point=self.pos, goal_point=player.pos)
                self.move_to(self.stored_path.pop(0))
            else:
                # Player is not in LOS, check if monster has a path already (ie. previously saw player)
                logging.debug(f"Monster at {self.pos} cannot see player at {player.pos}, {hasattr(self, 'stored_path')}")
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


def damage_after_mitigation(raw_amount: float, armor: int) -> float:
    # Damage multiplier = 1 - (0.06 * total armor) / (1 + 0.06 * abs(total armor))
    multiplier = 1 - (0.06 * armor) / (1 + 0.06 * abs(armor))
    return raw_amount * multiplier
