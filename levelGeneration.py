import logging
from dataclasses import dataclass
import random

from entity import Monster, FloorItem, melee_monster_update
from globalEnums import TermColor, DamageType, ItemType, Point
from levelData import LevelData, Tile

logging.basicConfig(filename='Imladebug.log', filemode='w', level=logging.DEBUG)


@dataclass(frozen=True)
class Room:
    """A dataclass to store the two points that define a rectangular room. x1,y1 is top-left, x2,y2 is bottom-right"""
    p1: Point
    p2: Point

    def is_point_in_room(self, p: Point) -> bool:
        """Returns if the given x,y point is within the room"""
        if self.p1.x <= p.x <= self.p2.x and self.p1.y <= p.y <= self.p2.y:
            return True
        return False

    def is_room_intersecting_other(self, other_rooms: list, buffer: int = 0) -> bool:
        """Returns if this room intersects any room in other_rooms"""
        """ buffer is an added area to trigger collision"""
        for oroom in other_rooms:
            for x in range(self.p1.x - buffer, self.p2.x + buffer + 1):
                for y in range(self.p1.y - buffer, self.p2.y + buffer + 1):
                    if oroom.is_point_in_room(Point(x, y)):
                        return True
        return False

    def get_random_point(self) -> Point:
        """Returns a random point within this room"""
        x = random.randint(self.p1.x + 1, self.p2.x - 1)
        y = random.randint(self.p1.y + 1, self.p2.y - 1)
        return Point(x, y)


def is_point_in_rect(p: Point, room: Room) -> bool:
    """Checks if a point exists within a given room"""
    return room.p1.x <= p.x <= room.p2.x and room.p1.y <= p.y <= room.p2.y


def generate_blank_tile_data(width: int, height: int, template_tile: Tile) -> dict[Point, Tile]:
    """Generates a dict of Tiles copying the non-location data of the template_tile"""
    tile_data: dict[Point, Tile] = {}
    for i in range(0, width):
        for j in range(0, height):
            p = Point(i, j)
            t = Tile(world_x=i, world_y=j, floor_char=template_tile.floor_char,
                     is_blocking_move=template_tile.is_blocking_move, is_blocking_LOS=template_tile.is_blocking_LOS,
                     is_visible=template_tile.is_visible, visible_color=template_tile.visible_color,
                     fow_color=template_tile.fow_color, has_been_visible=template_tile.has_been_visible,
                     movement_weight=template_tile.movement_weight)
            tile_data[p] = t

    return tile_data


def generate_level(**kwargs) -> LevelData:
    """Generates/returns level data based on given kwargs"""

    logging.debug(f"Beginning level generation with kwargs: {kwargs}")
    if kwargs["generation_type"] == 0:
        """
        # args: generation_type, height, width
        map_height = kwargs["height"]
        map_width = kwargs["width"]
        tile_data = [[None for i in range(map_height)] for j in range(map_width)]

        for x in range(0, map_width):
            for y in range(0, map_height):
                # num = (x + y) % 10
                _tile = Tile(world_x=x, world_y=y, floor_char=".",
                             is_blocking_move=False, is_blocking_LOS=False, is_visible=True,
                             visible_color=TermColor.MID_GREY, fow_color=TermColor.DARK_GREY)
                tile_data[x][y] = _tile

        entities = []
        level_data = LevelData(tile_data=tile_data, entities=entities, player_start_pos=(5, 5))

        return level_data
        """
    elif kwargs["generation_type"] == 1:
        # args: generation_type, height, width, room_density, room_size, room_size_mod
        logging.debug("level gen type 1 - rewritten")
        map_height = kwargs["height"]
        map_width = kwargs["width"]

        num_rooms = kwargs["num_rooms"]
        room_size = kwargs["room_size"]
        room_size_mod = kwargs["room_size_mod"]
        rooms: list[Room] = []
        rooms_attempted = 0  # For now we're just going to naively attempt to make 2 x the num rooms
        logging.debug(f"Numrooms: {num_rooms}")

        while rooms_attempted <= num_rooms * 2:
            # logging.debug(f"Rooms attempted: {rooms_attempted} out of {num_rooms * 2}")
            # logging.debug(f"Rooms done: {len(rooms)}")
            if len(rooms) >= num_rooms:
                # If we've reached enough rooms, then stop generating
                break

            gen_room = generate_room(map_height, map_width, room_size, room_size_mod)
            rooms_attempted += 1

            # Now we check to see if this will intersect with any existing rooms
            if gen_room.is_room_intersecting_other(other_rooms=rooms, buffer=1):
                # Room is invalid, discard
                continue
            else:
                rooms.append(gen_room)

        # Now that we have a list of rooms, actually generate the level data
        # We'll start by filling the world with walls, and then carve out the rooms/hallways
        # Todo: maybe store these tile templates somewhere?
        template_wall_tile = Tile(world_x=0, world_y=0, floor_char="#", is_blocking_move=True, is_blocking_LOS=True,
                                  is_visible=False, visible_color=TermColor.LIGHT_GREY, fow_color=TermColor.MID_GREY,
                                  has_been_visible=False, movement_weight=1)

        tile_data = generate_blank_tile_data(width=map_width, height=map_height, template_tile=template_wall_tile)

        # Next we'll carve out the rooms
        template_floor_tile = Tile(world_x=0, world_y=0, floor_char=".", is_blocking_move=False, is_blocking_LOS=False,
                                   is_visible=False, visible_color=TermColor.MID_GREY, fow_color=TermColor.DARK_GREY,
                                   has_been_visible=False, movement_weight=1)

        for room in rooms:
            fill_room_with_template(room, template_floor_tile, tile_data)

        # Next we'll carve out hallways
        for i in range(len(rooms) - 1):
            # We'll do this by picking a point in the current room, and a point in the next room
            # And connecting them with a single-bend hallway
            starting_point = rooms[i].get_random_point()
            ending_point = rooms[i+1].get_random_point()

            fill_hallway(starting_point, ending_point, template_floor_tile, tile_data)

        # Choose a valid staring spot for the player
        # We'll do this by picking a random room, and then picking a spot in that room
        player_room_num = random.randint(0, len(rooms) - 1)
        player_start_point = rooms[player_room_num].get_random_point()

        # Populate the rooms with stuff!
        monsters = []
        floor_items = []
        floor_effects = []
        interactables = []

        # For now, let's put a single orc in a room
        monster_room = random.randint(0, len(rooms) - 1)
        monster_start_point = rooms[monster_room].get_random_point()

        monster_armor = {DamageType.PHYSICAL: 0, DamageType.FIRE: 0, DamageType.LIGHTNING: 0, DamageType.COLD: 0,
                         DamageType.CORROSIVE: 0}
        monster_drop = FloorItem(name="gold", pos=(None, None), display_char="$", display_color=TermColor.GOLD,
                                 is_visible=True, blocks_LOS=False, item_type=ItemType.GOLD, item_amount=10)
        monster = Monster(name="Orc", pos=monster_start_point,
                          display_char="o", display_color=TermColor.GREEN,
                          health_max=5.0, health=5.0, armor=monster_armor, attack_power=2,
                          monster_update=melee_monster_update, on_death_drop=monster_drop)
        monsters.append(monster)

        level_data = LevelData(tile_data=tile_data, width=map_width, height=map_height,
                               player_start_pos=player_start_point,
                               monsters=monsters, floor_items=floor_items, floor_effects=floor_effects,
                               interactables=interactables)

        return level_data
    else:
        return None


def fill_hallway(starting_point, ending_point, template_floor_tile, tile_data):
    """Fills the tiles in tile_data in two hallways connecting the starting and ending points
        with tiles that mimic the template"""

    # This should maybe be split further into a "fill_line" method
    # Horizontal leg first
    for x in range(min(starting_point.x, ending_point.x), max(starting_point.x, ending_point.x) + 1):
        new_tile = Tile(world_x=x, world_y=starting_point.y, floor_char=template_floor_tile.floor_char,
                        is_blocking_move=template_floor_tile.is_blocking_move,
                        is_blocking_LOS=template_floor_tile.is_blocking_LOS,
                        is_visible=template_floor_tile.is_visible,
                        visible_color=template_floor_tile.visible_color,
                        fow_color=template_floor_tile.fow_color,
                        has_been_visible=template_floor_tile.has_been_visible,
                        movement_weight=template_floor_tile.movement_weight)
        tile_data[Point(x, starting_point.y)] = new_tile
    # Then the vertical leg
    for y in range(min(starting_point.y, ending_point.y), max(starting_point.y, ending_point.y) + 1):
        new_tile = Tile(world_x=ending_point.x, world_y=y, floor_char=template_floor_tile.floor_char,
                        is_blocking_move=template_floor_tile.is_blocking_move,
                        is_blocking_LOS=template_floor_tile.is_blocking_LOS,
                        is_visible=template_floor_tile.is_visible,
                        visible_color=template_floor_tile.visible_color,
                        fow_color=template_floor_tile.fow_color,
                        has_been_visible=template_floor_tile.has_been_visible,
                        movement_weight=template_floor_tile.movement_weight)
        tile_data[Point(ending_point.x, y)] = new_tile


def fill_room_with_template(room, template_tile, tile_data):
    """Fills the tiles in tile_data in the area of room with tiles that mimic the template"""
    for room_x in range(room.p1.x, room.p2.x + 1):
        for room_y in range(room.p1.y, room.p2.y + 1):
            new_tile = Tile(world_x=room_x, world_y=room_y, floor_char=template_tile.floor_char,
                            is_blocking_move=template_tile.is_blocking_move,
                            is_blocking_LOS=template_tile.is_blocking_LOS,
                            is_visible=template_tile.is_visible,
                            visible_color=template_tile.visible_color,
                            fow_color=template_tile.fow_color,
                            has_been_visible=template_tile.has_been_visible,
                            movement_weight=template_tile.movement_weight)
            tile_data[Point(room_x, room_y)] = new_tile


def generate_room(map_height, map_width, room_size, room_size_mod):
    """Generates a room of the given size +/- size_mod, that will fit in the given map size"""
    room_width = random.randint(room_size - room_size_mod, room_size + room_size_mod)
    room_height = random.randint(room_size - room_size_mod, room_size + room_size_mod)
    room_x = random.randint(1, map_width - 2 - room_width)  # randint is inclusive on both
    room_y = random.randint(1, map_height - 2 - room_height)  # move in by one so it doesn't touch edge of map

    return Room(Point(room_x, room_y), Point(room_x + room_width - 1, room_y + room_height - 1))
