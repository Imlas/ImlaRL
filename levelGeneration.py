import logging
from dataclasses import dataclass
import random

from entity import Monster, FloorItem, melee_monster_update
from globalEnums import TermColor, DamageType, ItemType
from levelData import LevelData, Tile

logging.basicConfig(filename='Imladebug.log', filemode='w', level=logging.DEBUG)


@dataclass(frozen=True)
class Room:
    """A dataclass to store the two points that define a rectangular room. x1,y1 is top-left, x2,y2 is bottom-right"""
    x1: int
    y1: int
    x2: int
    y2: int

    def is_point_in_room(self, px: int, py: int) -> bool:
        """Returns if the given x,y point is within the room"""
        if self.x1 <= px <= self.x2 and self.y1 <= py <= self.y2:
            return True
        return False

    def is_room_intersecting_other(self, other_rooms: list, buffer: int = 0) -> bool:
        """Returns if this room intersects any room in other_rooms"""
        """ buffer is an added area to trigger collision"""
        for oroom in other_rooms:
            for x in range(self.x1 - buffer, self.x2 + buffer + 1):
                for y in range(self.y1 - buffer, self.y2 + buffer + 1):
                    if oroom.is_point_in_room(x, y):
                        return True
        return False


def is_point_in_rect(px: int, py: int, room: Room) -> bool:
    """Checks if a point exists within a given room"""
    if room.x1 <= px <= room.x2 and room.y1 <= py <= room.y2:
        # logging.debug(f"Overlap checking {px},{py} vs {room}")
        return True
    else:
        # logging.debug(f"No overlap checking {px},{py} vs {room}")
        return False


def is_room_intersecting_other(room: Room, other_rooms: list[Room], buffer: int = 0) -> bool:
    """Checks if any point in a given room intersects with any other room in other_rooms """
    # logging.debug(f"Beginning intersection check")
    # logging.debug(f"Room: {room}. Against {len(other_rooms)} other rooms")
    for oroom in other_rooms:
        for x in range(room.x1 - buffer, room.x2 + buffer + 1):
            for y in range(room.y1 - buffer, room.y2 + buffer + 1):
                if is_point_in_rect(x, y, oroom):
                    return True
    """
    room_x_min, room_y_min, room_x_max, room_y_max = room[0], room[1], room[2], room[3]
    logging.debug(room_x_min, room_y_min, room_x_max, room_y_max)
    for oroom in other_rooms:
        logging.debug(f"Checking against room {oroom}")
        if is_point_in_rect(room_x_min, room_y_min, oroom, 1):
            return True
        if is_point_in_rect(room_x_min, room_y_max, oroom, 1):
            return True
        if is_point_in_rect(room_x_max, room_y_min, oroom, 1):
            return True
        if is_point_in_rect(room_x_max, room_y_max, oroom, 1):
            return True
    """
    # logging.debug(f"Cleared against all rooms, returning False")
    return False


def generate_level(**kwargs) -> LevelData:
    """Generates/returns level data based on given kwargs"""
    # TODO: Huge chunks of this code can be refactored/broken into smaller methods for later use

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
        # TODO: There's a lot of code repetition with the creation of walls/floors - possibly find a way to standardize that
        #  Also it might be beneficial to instead fill with walls, and then just "carve out" floors for rooms/hallways
        # args: generation_type, height, width, room_density, room_size, room_size_mod
        logging.debug("level gen type 1")
        map_height = kwargs["height"]
        map_width = kwargs["width"]
        tile_data = [[None for i in range(map_height)] for j in range(map_width)]

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

            room_width = random.randint(room_size - room_size_mod, room_size + room_size_mod)
            room_height = random.randint(room_size - room_size_mod, room_size + room_size_mod)
            room_x = random.randint(1, map_width - 2 - room_width)  # randint is inclusive on both
            room_y = random.randint(1,
                                    map_height - 2 - room_height)  # we move in by one so it doesn't touch edge of map

            gen_room = Room(room_x, room_y, room_x + room_width - 1, room_y + room_height - 1)
            # logging.debug(f"Newly generated room {rooms_attempted}: {gen_room}. Checking to see intersections")

            # Now we check to see if this will intersect with any existing rooms
            if is_room_intersecting_other(gen_room, rooms, buffer=1):
                # Room is invalid, discard
                rooms_attempted += 1
                continue
            else:
                rooms_attempted += 1
                rooms.append(gen_room)

        # Now that we have a list of rooms, actually generate the level data
        # First the rooms
        for room in rooms:
            # First the interior of the room
            for room_x in range(room.x1, room.x2 + 1):
                for room_y in range(room.y1, room.y2 + 1):
                    _tile = Tile(world_x=room_x, world_y=room_y, floor_char=".",
                                 is_blocking_move=False, is_blocking_LOS=False, is_visible=True,
                                 visible_color=TermColor.MID_GREY, fow_color=TermColor.DARK_GREY)
                    tile_data[room_x][room_y] = _tile

            # Now we put up walls around the room
            # Top and bottom first
            # logging.debug(f"Constructing walls of room {room}")
            for wall_x in range(room.x1 - 1, room.x2 + 2):
                # Top
                # logging.debug(f"Wall: {wall_x}, {room.y1 - 1}")
                _tile = Tile(world_x=wall_x, world_y=room.y1 - 1, floor_char='#',
                             is_blocking_move=True, is_blocking_LOS=True, is_visible=True,
                             visible_color=TermColor.LIGHT_GREY, fow_color=TermColor.MID_GREY)
                tile_data[wall_x][room.y1 - 1] = _tile

                # Bottom
                # logging.debug(f"Wall: {wall_x}, {room.y2 + 1}")
                _tile = Tile(world_x=wall_x, world_y=room.y2 + 1, floor_char='#',
                             is_blocking_move=True, is_blocking_LOS=True, is_visible=True,
                             visible_color=TermColor.LIGHT_GREY, fow_color=TermColor.MID_GREY)
                tile_data[wall_x][room.y2 + 1] = _tile

            # Then sides
            for wall_y in range(room.y1 - 1, room.y2 + 2):
                # Left
                # logging.debug(f"Wall: {room.x1 - 1}, {wall_y}")
                _tile = Tile(world_x=room.x1 - 1, world_y=wall_y, floor_char='#',
                             is_blocking_move=True, is_blocking_LOS=True, is_visible=True,
                             visible_color=TermColor.LIGHT_GREY, fow_color=TermColor.MID_GREY)
                tile_data[room.x1 - 1][wall_y] = _tile

                # Right
                # logging.debug(f"Wall: {room.x2 + 1}, {wall_y}")
                _tile = Tile(world_x=room.x2 + 1, world_y=wall_y, floor_char='#',
                             is_blocking_move=True, is_blocking_LOS=True, is_visible=True,
                             visible_color=TermColor.LIGHT_GREY, fow_color=TermColor.MID_GREY)
                tile_data[room.x2 + 1][wall_y] = _tile
        for i in range(len(rooms) - 1):
            # Next we generate tiles for the hallways
            # We'll do this by picking a point in the current room, and a point in the next room
            # And connecting them with a single-bend hallway
            starting_x = random.randint(rooms[i].x1 + 1, rooms[i].x2 - 1)
            starting_y = random.randint(rooms[i].y1 + 1, rooms[i].y2 - 1)
            # logging.debug(f"Starting hallway at point {starting_x}, {starting_y}")

            ending_x = random.randint(rooms[i + 1].x1 + 1, rooms[i + 1].x2 - 1)
            ending_y = random.randint(rooms[i + 1].y1 + 1, rooms[i + 1].y2 - 1)
            # logging.debug(f"Starting hallway at point {ending_x}, {ending_y}")

            # Horizontal leg first
            for x in range(min(starting_x, ending_x), max(starting_x, ending_x) + 1):
                _tile = Tile(world_x=x, world_y=starting_y, floor_char=".",
                             is_blocking_move=False, is_blocking_LOS=False, is_visible=True,
                             visible_color=TermColor.MID_GREY, fow_color=TermColor.DARK_GREY)
                tile_data[x][starting_y] = _tile
                # Walls on either side if that tile isn't already assigned
                if tile_data[x][starting_y - 1] is None:
                    _tile = Tile(world_x=x, world_y=starting_y - 1, floor_char='#',
                                 is_blocking_move=True, is_blocking_LOS=True, is_visible=True,
                                 visible_color=TermColor.LIGHT_GREY, fow_color=TermColor.MID_GREY)
                    tile_data[x][starting_y - 1] = _tile

                if tile_data[x][starting_y + 1] is None:
                    _tile = Tile(world_x=x, world_y=starting_y + 1, floor_char='#',
                                 is_blocking_move=True, is_blocking_LOS=True, is_visible=True,
                                 visible_color=TermColor.LIGHT_GREY, fow_color=TermColor.MID_GREY)
                    tile_data[x][starting_y + 1] = _tile

            # Then the vertical leg
            for y in range(min(starting_y, ending_y), max(starting_y, ending_y) + 1):
                _tile = Tile(world_x=ending_x, world_y=y, floor_char=".",
                             is_blocking_move=False, is_blocking_LOS=False, is_visible=True,
                             visible_color=TermColor.MID_GREY, fow_color=TermColor.DARK_GREY)
                tile_data[ending_x][y] = _tile
                # And then walls
                if tile_data[ending_x - 1][y] is None:
                    _tile = Tile(world_x=ending_x - 1, world_y=y, floor_char='#',
                                 is_blocking_move=True, is_blocking_LOS=True, is_visible=True,
                                 visible_color=TermColor.LIGHT_GREY, fow_color=TermColor.MID_GREY)
                    tile_data[ending_x - 1][y] = _tile
                if tile_data[ending_x + 1][y] is None:
                    _tile = Tile(world_x=ending_x + 1, world_y=y, floor_char='#',
                                 is_blocking_move=True, is_blocking_LOS=True, is_visible=True,
                                 visible_color=TermColor.LIGHT_GREY, fow_color=TermColor.MID_GREY)
                    tile_data[ending_x + 1][y] = _tile

            # Attempt to fill in the outside corner of the bend
            # Corner is (maybe) always at fx, sy - so we hit the 4 spots around
            x, y = None, None
            if tile_data[ending_x - 1][starting_y - 1] is None:
                x, y = ending_x - 1, starting_y - 1
            if tile_data[ending_x + 1][starting_y - 1] is None:
                x, y = ending_x + 1, starting_y - 1
            if tile_data[ending_x - 1][starting_y + 1] is None:
                x, y = ending_x - 1, starting_y + 1
            if tile_data[ending_x + 1][starting_y + 1] is None:
                x, y = ending_x + 1, starting_y + 1
            if x is not None and y is not None:
                _tile = Tile(world_x=x, world_y=y, floor_char='#',
                             is_blocking_move=True, is_blocking_LOS=True, is_visible=True,
                             visible_color=TermColor.LIGHT_GREY, fow_color=TermColor.MID_GREY)
                tile_data[x][y] = _tile

        # Choose a valid staring spot for the player
        # We'll do this by picking a random room, and then picking a spot in that room
        player_room_num = random.randint(0, len(rooms) - 1)
        player_start_x = random.randint(rooms[player_room_num].x1, rooms[player_room_num].x2)
        player_start_y = random.randint(rooms[player_room_num].y1, rooms[player_room_num].y2)

        # Populate the rooms with stuff!
        monsters = []
        floor_items = []
        floor_effects = []
        interactables = []

        # For now, let's put a single orc in a room
        monster_room = random.randint(0, len(rooms) - 1)
        monster_start_x = random.randint(rooms[monster_room].x1, rooms[monster_room].x2)
        monster_start_y = random.randint(rooms[monster_room].y1, rooms[monster_room].y2)

        monster_armor = {DamageType.PHYSICAL: 0, DamageType.FIRE: 0, DamageType.LIGHTNING: 0, DamageType.COLD: 0, DamageType.CORROSIVE: 0}
        monster_drop = FloorItem(name="gold", pos=(None, None), display_char="$", display_color=TermColor.GOLD,
                                 is_visible=True, blocks_LOS=False, item_type=ItemType.GOLD, item_amount=10)
        monster = Monster(name="Orc", pos=(monster_start_x, monster_start_y),
                          display_char="o", display_color=TermColor.GREEN,
                          health_max=5.0, health=5.0, armor=monster_armor, attack_power=2,
                          monster_update=melee_monster_update, on_death_drop=monster_drop)
        monsters.append(monster)

        level_data = LevelData(tile_data=tile_data, player_start_pos=(player_start_x, player_start_y),
                               monsters=monsters, floor_items=floor_items, floor_effects=floor_effects,
                               interactables=interactables)

        return level_data
    else:
        return None