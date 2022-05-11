# cd PycharmProjects/ImlaRL
# assume a console window of 120 x 30

"""
print(f'The value is {foo}')
print(f"{foo = }")
print(f"{foo!r}") prints the repper of the value
print(f"{foo!a}") prints out all non-ascii characters as a unicode string
print(f"{foo!s}") calls the string conversion operater, mostly for the below ones
print(f"{foo=:%Y-%m-%d}") The ':' operator prefaces some formatting function
print(f"{foo:.2f}")



"""
from typing import List, Tuple

import blessed
import random
import logging
from enum import Enum, auto
from dataclasses import dataclass, field
from skimage.draw import line

logging.basicConfig(filename='Imladebug.log', filemode='w', level=logging.CRITICAL)


class Tile:
    def __init__(self, world_x: int, world_y: int, floor_char: str, is_blocking_move: bool, is_blocking_LOS: bool,
                 is_visible, has_been_visible=False):
        self.x = world_x
        self.y = world_y
        self.char = floor_char
        self.is_blocking_move = is_blocking_move
        self.is_blocking_LOS = is_blocking_LOS
        self.is_visible = is_visible
        self.has_been_visible = has_been_visible


class EntityType(Enum):
    """Entity types"""
    PLAYER = auto()
    EFFECT = auto()
    MONSTER = auto()
    ITEM = auto()
    STAIRS = auto()


class Entity:
    def __init__(self, world_x: int, world_y: int, char: str, entity_type: EntityType, is_visible: bool):
        self.x = world_x
        self.y = world_y
        self.char = char
        self.etype = entity_type
        self.is_visible = is_visible

    def unchecked_place(self, world_x: int, world_y: int):
        # This is similar to move_to, but really only checks of x,y is positive and non-None
        if world_x is not None and world_y is not None:
            if world_x >= 0 and world_y >= 0:
                self.x = world_x
                self.y = world_y

    def move_to(self, world_x: int, world_y: int, level_data: list[Tile]) -> int:
        # Returns 0 if move was successful
        # Returns 1 if move was invalid for some reason
        # Check if x,y is non-None/non-negative
        if world_x is None or world_y is None:
            return 1

        # Check if x,y is valid for level data
        try:
            _tile = level_data[world_x][world_y]
        except IndexError:
            return 1

        if _tile is None:
            return 1

        # Check if that tile is_blocking_move
        if _tile.is_blocking_move is True:
            return 1

        # Check if other entities exist on that tile and if they block

        self.x = world_x
        self.y = world_y
        return 0
        # print("!")


@dataclass(frozen=True)
class Room:
    """A dataclass to store the two points that define a rectangular room. x1,y1 is top-left, x2,y2 is bottom-right"""
    x1: int
    y1: int
    x2: int
    y2: int


@dataclass
class Shadow:
    start: float
    end: float

    def contains(self, other) -> bool:
        """Returns True if *other* is completely covered by this shadow"""
        return self.start <= other.start and self.end >= other.end


@dataclass
class ShadowLine:
    _shadows: list = field(default_factory=list)

    def add(self, shadow: Shadow):
        # Figure out where to add the new shadow in the list
        # Shadows are sorted based on starting edge
        # Then we see if they need to combine
        index = 0
        # logging.debug(f"Adding new shadow {shadow.start},{shadow.end}. Total shadows {len(self._shadows)}")
        while index < len(self._shadows):
            if self._shadows[index].start >= shadow.start:
                break
            index += 1
        # logging.debug(f"Placing new shadow at index {index}")

        # See if this shadow overlaps the previous shadow.
        overlapping_previous = None
        if index > 0 and self._shadows[index - 1].end > shadow.start:
            overlapping_previous = self._shadows[index - 1]

        # And see if it overlaps the next shadow
        overlapping_next = None
        if index < len(self._shadows) and self._shadows[index].start < shadow.end:
            overlapping_next = self._shadows[index]

        # Insert the new shadow, and unify it with any overlapping shadows
        if overlapping_next is not None:
            if overlapping_previous is not None:
                # Overlapping on both ends, so unify one and delete the other
                overlapping_previous.end = overlapping_next.end
                self._shadows.remove(overlapping_next)
            else:
                # Only overlapping on the far edge, so move its starting edge over
                overlapping_next.start = shadow.start
        else:
            if overlapping_previous is not None:
                # Only overlaps the previous, so update its end point
                overlapping_previous.end = shadow.end
            else:
                # Does not overlap on either end, so just insert it at the appropriate position
                self._shadows.insert(index, shadow)
        # logging.debug(f"Shadow add finished. Shadows: {self._shadows}")

    def is_in_shadow(self, projection: Shadow) -> bool:
        for shadow in self._shadows:
            if shadow.contains(projection):
                return True

        return False

    def is_full_shadow(self) -> bool:
        return len(self._shadows) == 1 and self._shadows[0].start == 0.0 and self._shadows[0].end == 1.0

    @staticmethod
    def project_tile(row: int, col: int) -> Shadow:
        """Note that row,col are in octant coords, NOT world/terminal coords"""
        top_left = col / (row + 2)
        bottom_right = (col + 1) / (row + 1)
        return Shadow(top_left, bottom_right)

    """
    def project_shadow_debug(self, max_range: int, origin_x: int, origin_y: int, level_data: list[Tile],
                             octant_num: int = 0):
        # Not sure yet if s_line needs to be passed in, or if we just use self for this kinda thing
        # and then make 8 ShadowLines each pass

        for row in range(0, max_range + 1):
            for col in range(0, row + 1):
                # Starts with a projection of every tile.
                # If that projection is inside of the current ShadowLine, then it's not visible
                # If the tile *is* visible, and also blocks LOS, then we add it's projection to the ShadowLine
                projection = ShadowLine._project_tile(row, col)
                logging.debug(f"{projection.start = }, {projection.end = }")
                x, y = transform_octant(row + origin_x, col + origin_y, octant_num)
                level_data[x][y].is_visible = not self.is_in_shadow(projection)
                if level_data[x][y].is_blocking_LOS:
                    self.add(projection)
    """


def draw_line(effects: list[Entity], x1: int, y1: int, x2: int, y2: int, char: str):
    # Adds a line to the effects "buffer"
    # The coords are in world space
    rr, cc = line(y1, x1, y2, x2)
    logging.debug(f"rr: {rr}, cc: {cc}")
    for n in range(len(rr)):
        e = Entity(int(cc[n]), int(rr[n]), char, EntityType.EFFECT, True)
        logging.debug(f"Line entity at {cc[n]},{rr[n]}, {char}, {type(cc[n])}, {type(rr[n])}")
        effects.append(e)


def generate_octant(origin_x: int, origin_y: int, max_distance: int, octant_num: int) -> list[(int, int)]:
    # octant_num is an int 0-7 that decides *which* octant is returned
    # octant_num = 0 is the 12-2 o'clock, and it goes clockwise from there
    # The octant generated is a list of (x,y) tuples

    octant = []

    for row in range(max_distance):
        for col in range(row + 1):
            if octant_num == 0:
                x = origin_x + col
                y = origin_y - row  # The minus here is intentional
            elif octant_num == 1:
                x = origin_x + row
                y = origin_y - col
            elif octant_num == 2:
                x = origin_x + row
                y = origin_y + col
            elif octant_num == 3:
                x = origin_x + col
                y = origin_y + row
            elif octant_num == 4:
                x = origin_x - col
                y = origin_y + row
            elif octant_num == 5:
                x = origin_x - row
                y = origin_y + col
            elif octant_num == 6:
                x = origin_x - row
                y = origin_y - col
            elif octant_num == 7:
                x = origin_x - col
                y = origin_y - row
            else:
                return None
            octant.append((x, y))
    return octant


def transform_octant(row: int, col: int, octant_num: int) -> (int, int):
    if octant_num == 0:
        return col, -row
    elif octant_num == 1:
        return row, -col
    elif octant_num == 2:
        return row, col
    elif octant_num == 3:
        return col, row
    elif octant_num == 4:
        return -col, row
    elif octant_num == 5:
        return -row, col
    elif octant_num == 6:
        return -row, -col
    elif octant_num == 7:
        return -col, -row
    else:
        return None


def draw_octant(origin_x: int, origin_y: int, max_distance: int, octant_num: int, effects: list[Entity], char: str):
    # Adds a drawing of the given octant to the effects buffer for drawing
    # This is just a debug thing
    octant = generate_octant(origin_x, origin_y, max_distance, octant_num)
    for x, y in octant:
        e = Entity(x, y, char, EntityType.EFFECT, True)
        effects.append(e)


def refresh_visibility(origin_x: int, origin_y: int, max_range: int, level_data: list[Tile]):
    for octant in range(8):
        refresh_octant(origin_x, origin_y, max_range, octant, level_data)


def refresh_octant(origin_x: int, origin_y: int, max_range: int, octant: int, level_data: list[Tile]):
    s_line = ShadowLine()
    full_shadow = False

    logging.debug(f"Beginning an octant refresh starting at {origin_x},{origin_y}")

    # Be mindful that the row,col numbers here are in octant coordinates
    for row in range(1, max_range + 1):
        # logging.debug(f"{row = }")
        test_x, test_y = transform_octant(row, 0, octant)
        if (octant == 0 or octant == 7) and test_y + origin_y < 0:
            # logging.debug(f"Breaking octant {octant} due to hitting map boundary")
            break
        if (octant == 3 or octant == 4) and test_y + origin_y >= len(level_data[0]):
            # logging.debug(f"Breaking octant {octant} due to hitting map boundary")
            break
        if (octant == 1 or octant == 2) and test_x + origin_x >= len(level_data):
            # logging.debug(f"Breaking octant {octant} due to hitting map boundary")
            break
        if (octant == 5 or octant == 6) and test_x + origin_x < 0:
            # logging.debug(f"Breaking octant {octant} due to hitting map boundary")
            break

        for col in range(0, row + 1):
            # logging.debug(f"{col = }")
            # I need some out of bounds check here
            # Both for col and row to break early
            x, y = transform_octant(row, col, octant)
            x += origin_x
            y += origin_y
            # logging.debug(f"-----Tile {x},{y}-----")

            # For now we'll just check each tile
            if x < 0 or y < 0 or x >= len(level_data) or y >= len(level_data[0]) or level_data[x][y] is None:
                # if level_data[x][y] is None:
                # logging.debug("Tile not valid. breaking to next tile")
                continue

            if full_shadow:
                # logging.debug(f"Shadow line is full. Setting is_visible False")
                level_data[x][y].is_visible = False
            else:
                # logging.debug(f"Shadow line is not full. Calcing projection")

                projection = ShadowLine.project_tile(row, col)
                # logging.debug(f"{projection = }")
                # See if this tile is visible/currently in the shadow line
                visible = not s_line.is_in_shadow(projection)
                level_data[x][y].is_visible = visible
                # logging.debug(f"Tile is vis: {visible} Blocks?: {level_data[x][y].is_blocking_LOS}")

                # Add the projection to the shadow line if this tile blocks LOS
                if visible and level_data[x][y].is_blocking_LOS:
                    # logging.debug(f"Adding projection to shadow line")
                    s_line.add(projection)
                    full_shadow = s_line.is_full_shadow()


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


def generate_level(**kwargs) -> list[Tile]:
    """Generates/returns level data based on given kwargs"""
    # TODO: Huge chunks of this code can be refactored/broken into smaller methods for later use
    logging.debug(f"Beginning level generation with kwargs: {kwargs}")
    if kwargs["generation_type"] == 0:
        # args: generation_type, height, width
        map_height = kwargs["height"]
        map_width = kwargs["width"]
        level_data = [[None for i in range(map_height)] for j in range(map_width)]

        for x in range(0, map_width):
            for y in range(0, map_height):
                # num = (x + y) % 10
                _tile = Tile(world_x=x, world_y=y, floor_char=".",
                             is_blocking_move=False, is_blocking_LOS=False, is_visible=True)
                level_data[x][y] = _tile

        return level_data
    elif kwargs["generation_type"] == 1:
        # args: generation_type, height, width, room_density, room_size, room_size_mod, player
        logging.debug("level gen type 1")
        map_height = kwargs["height"]
        map_width = kwargs["width"]
        level_data = [[None for i in range(map_height)] for j in range(map_width)]

        num_rooms = kwargs["num_rooms"]
        room_size = kwargs["room_size"]
        room_size_mod = kwargs["room_size_mod"]
        rooms: list[Room] = []
        rooms_attempted = 0  # For now we're just going to nievely attempt to make 2 x the num rooms

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
                                 is_blocking_move=False, is_blocking_LOS=False, is_visible=True)
                    level_data[room_x][room_y] = _tile

            # Now we put up walls around the room
            # Top and bottom first
            # logging.debug(f"Contructing walls of room {room}")
            for wall_x in range(room.x1 - 1, room.x2 + 2):
                # Top
                # logging.debug(f"Wall: {wall_x}, {room.y1 - 1}")
                _tile = Tile(world_x=wall_x, world_y=room.y1 - 1, floor_char='#',
                             is_blocking_move=True, is_blocking_LOS=True, is_visible=True)
                level_data[wall_x][room.y1 - 1] = _tile

                # Bottom
                # logging.debug(f"Wall: {wall_x}, {room.y2 + 1}")
                _tile = Tile(world_x=wall_x, world_y=room.y2 + 1, floor_char='#',
                             is_blocking_move=True, is_blocking_LOS=True, is_visible=True)
                level_data[wall_x][room.y2 + 1] = _tile

            # Then sides
            for wall_y in range(room.y1 - 1, room.y2 + 2):
                # Left
                # logging.debug(f"Wall: {room.x1 - 1}, {wall_y}")
                _tile = Tile(world_x=room.x1 - 1, world_y=wall_y, floor_char='#',
                             is_blocking_move=True, is_blocking_LOS=True, is_visible=True)
                level_data[room.x1 - 1][wall_y] = _tile

                # Right
                # logging.debug(f"Wall: {room.x2 + 1}, {wall_y}")
                _tile = Tile(world_x=room.x2 + 1, world_y=wall_y, floor_char='#',
                             is_blocking_move=True, is_blocking_LOS=True, is_visible=True)
                level_data[room.x2 + 1][wall_y] = _tile
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
                             is_blocking_move=False, is_blocking_LOS=False, is_visible=True)
                level_data[x][starting_y] = _tile
                # Walls on either side if that tile isn't already assigned
                if level_data[x][starting_y - 1] is None:
                    _tile = Tile(world_x=x, world_y=starting_y - 1, floor_char='#',
                                 is_blocking_move=True, is_blocking_LOS=True, is_visible=True)
                    level_data[x][starting_y - 1] = _tile

                if level_data[x][starting_y + 1] is None:
                    _tile = Tile(world_x=x, world_y=starting_y + 1, floor_char='#',
                                 is_blocking_move=True, is_blocking_LOS=True, is_visible=True)
                    level_data[x][starting_y + 1] = _tile

            # Then the vertical leg
            for y in range(min(starting_y, ending_y), max(starting_y, ending_y) + 1):
                _tile = Tile(world_x=ending_x, world_y=y, floor_char=".",
                             is_blocking_move=False, is_blocking_LOS=False, is_visible=True)
                level_data[ending_x][y] = _tile
                # And then walls
                if level_data[ending_x - 1][y] is None:
                    _tile = Tile(world_x=ending_x - 1, world_y=y, floor_char='#',
                                 is_blocking_move=True, is_blocking_LOS=True, is_visible=True)
                    level_data[ending_x - 1][y] = _tile
                if level_data[ending_x + 1][y] is None:
                    _tile = Tile(world_x=ending_x + 1, world_y=y, floor_char='#',
                                 is_blocking_move=True, is_blocking_LOS=True, is_visible=True)
                    level_data[ending_x + 1][y] = _tile

            # Attempt to fill in the outside corner of the bend
            # Corner is (maybe) always at fx, sy - so we hit the 4 spots around
            x, y = None, None
            if level_data[ending_x - 1][starting_y - 1] is None:
                x, y = ending_x - 1, starting_y - 1
            if level_data[ending_x + 1][starting_y - 1] is None:
                x, y = ending_x + 1, starting_y - 1
            if level_data[ending_x - 1][starting_y + 1] is None:
                x, y = ending_x - 1, starting_y + 1
            if level_data[ending_x + 1][starting_y + 1] is None:
                x, y = ending_x + 1, starting_y + 1
            if x is not None and y is not None:
                _tile = Tile(world_x=x, world_y=y, floor_char='#',
                             is_blocking_move=True, is_blocking_LOS=True, is_visible=True)
                level_data[x][y] = _tile

        # Choose a valid staring spot for the player
        # We'll do this by picking a random room, and then picking a spot in that room
        player_room_num = random.randint(0, len(rooms) - 1)
        player_start_x = random.randint(rooms[player_room_num].x1, rooms[player_room_num].x2)
        player_start_y = random.randint(rooms[player_room_num].y1, rooms[player_room_num].y2)
        player = kwargs["player"]
        player.unchecked_place(player_start_x, player_start_y)

        # Populate the rooms with stuff!
        return level_data
    else:
        return None


def draw_border(_term, origin_x, origin_y, box_width, box_height, border_char):
    """Draws a hollow box."""
    # draw a box from the top left corner
    print(_term.move_xy(origin_x, origin_y) + border_char * box_width)
    for i in range(origin_y + 1, box_height - 1):
        print(_term.move_xy(origin_x, i) + border_char + _term.move_xy(box_width - 1, i) + border_char)
    print(border_char * box_width + _term.home)  # Adding the term.home avoids corner/scrolling issues


def entities_in_frame(all_entities: list[Entity], cam_origin_x: int, cam_origin_y: int, cam_width: int,
                      cam_height: int) -> list[Entity]:
    """Returns a list of all entities that exist within the given frame of the camera"""
    # Returns a list of all of the entities that are within the frame of the camera
    # It does not check if the entities are is_visible
    entities = []

    min_x, max_x = cam_origin_x, cam_origin_x + cam_width
    min_y, max_y = cam_origin_y, cam_origin_y + cam_height

    for e in all_entities:
        if min_x <= e.x <= max_x and min_y <= e.y <= max_y:
            entities.append(e)

    return entities


def draw_camera(_term, cam_origin_x: int, cam_origin_y: int, cam_width: int, cam_height: int,
                term_origin_x, term_origin_y, level_data, entities, effects):
    """Draws everything in the camera view"""
    # cam_origin x/y are in world-space
    # term_origin are the top-left corner in the console
    # Draw the tiles

    for rows in range(cam_origin_y, cam_origin_y + cam_height):
        rowstr = ""
        for cols in range(cam_origin_x, cam_origin_x + cam_width):
            tile_char = " "
            try:
                if cols >= 0 and rows >= 0:
                    if level_data[cols][rows] is not None and level_data[cols][rows].is_visible:
                        tile_char = level_data[cols][rows].char
            except IndexError:
                pass
            rowstr += tile_char
        print(_term.move_xy(term_origin_x, rows + term_origin_y - cam_origin_y) + rowstr)

    # Draw the entities
    # We'll later need to add some logic to handle two entities on
    frame_entities = entities_in_frame(entities, cam_origin_x, cam_origin_y, cam_width, cam_height)
    for ent in frame_entities:
        print(_term.move_xy(ent.x + term_origin_x - cam_origin_x, ent.y + term_origin_y - cam_origin_y) + ent.char)

    # Draw the effects
    # These are similar to entities, but they don't "exist" in the world
    # They also go on-top of everything else
    # This is used for UI bits, and animations?
    # logging.debug(f"Num effects total: {len(effects)}")
    frame_effects = entities_in_frame(effects, cam_origin_x, cam_origin_y, cam_width, cam_height)
    # logging.debug(f"Drawing {len(frame_effects)} effects that are in-frame")
    for eff in frame_effects:
        # logging.debug(f"eff draw {eff.x},{eff.y} {eff.char}")
        print(_term.move_xy(eff.x + term_origin_x - cam_origin_x, eff.y + term_origin_y - cam_origin_y) + eff.char)


def set_message(_term, message: str):
    """Sets the single line message at the top of the screen"""
    # Need to check how this behaves for longer messages
    # And determine the behavior for multi-line messages/etc.
    print(_term.move_xy(0, 0) + message)


def update_bottom_status(_term, player: Entity, level_data: list[Tile]):
    print(_term.move_xy(0, _term.height - 2) + "Status text like health etc")
    print(_term.move_xy(0, _term.height - 1) + f"Player loc: {player.x:02d},{player.y:02d}" + _term.home)
    # f"{number:02d}"


def handle_input(key: str, level_data: list[Tile], entities: list[Entity], player: Entity, effects: list[Entity]):
    # I feel like we'll need to add some level of flags to this at some point to deal with menus/etc.
    if key.is_sequence:
        key = key.name

    if key == 'KEY_UP' or key == '8':
        player.move_to(player.x, player.y - 1, level_data)
    elif key == 'KEY_DOWN' or key == '2':
        player.move_to(player.x, player.y + 1, level_data)
    elif key == 'KEY_LEFT' or key == '4':
        player.move_to(player.x - 1, player.y, level_data)
    elif key == 'KEY_RIGHT' or key == '6':
        player.move_to(player.x + 1, player.y, level_data)
    elif key == '1':
        player.move_to(player.x - 1, player.y + 1, level_data)
    elif key == '3':
        player.move_to(player.x + 1, player.y + 1, level_data)
    elif key == '7':
        player.move_to(player.x - 1, player.y - 1, level_data)
    elif key == '9':
        player.move_to(player.x + 1, player.y - 1, level_data)
    elif key == 'KEY_F1':
        logging.debug("F1 pressed!")
        refresh_visibility(player.x, player.y, 20, level_data)
    elif key == 'KEY_F2':
        logging.debug("F2 pressed!")

    elif key == 'KEY_F3':
        logging.debug("F3 pressed!")

    elif key == 'KEY_F4':
        logging.debug("F4 pressed!")

    elif key == 'KEY_F5':
        logging.debug("F5 pressed!")

    elif key == 'KEY_F6':
        logging.debug("F6 pressed!")

    elif key == 'KEY_F7':
        logging.debug("F7 pressed!")

    elif key == 'KEY_F8':
        logging.debug("F8 pressed!")

    elif key == 'KEY_F9':
        logging.debug("F9 pressed!")


def main():
    term = blessed.Terminal()
    print(f"height:{term.height} width:{term.width}")
    print(f"Colors:{term.number_of_colors}")

    logging.debug("Program beginning. Terminal initialized.")

    origin_x, origin_y = 0, 1
    box_width, box_height = term.width, term.height - 2
    border_char = '#'

    level_width = 20
    level_height = 20

    camera_width = term.width - 2  # room for border on both sides
    camera_height = term.height - 5  # room for border + 3 lines of status (1 on top, 2 on bottom)
    camera_window_origin_x, camera_window_origin_y = 1, 1  # The x, y console-coords of the top-left of the camera view
    camera_x, camera_y = 0, 0  # The x,y world-coords of the top-left of the camera

    level_data = []
    entities = []
    effects = []

    """
    mydict = {'width': 80, 'height': 20, 'generation_type': 0}
    print(mydict)
    print(mydict.keys())
    print(mydict.values())
    print(mydict["width"], mydict["height"], mydict["generation_type"])

    def myfunct(**kwargs):
        print(kwargs)
        print(kwargs.keys())
        print(kwargs.values())
        print(kwargs["width"], kwargs["height"], kwargs["generation_type"])

    myfunct(**mydict)

    return None
    """

    # clear the terminal
    with term.fullscreen(), term.hidden_cursor(), term.cbreak():
        # Fun note! hidden_cursor needs to come after fullscreen
        print(term.home + term.clear, end='')
        # Draw border
        # draw_border(term, origin_x, origin_y, box_width, box_height, border_char)

        # Generate player entity
        player = Entity(world_x=0, world_y=0, char="@", entity_type=EntityType.PLAYER, is_visible=True)
        entities.append(player)

        # Generate level data
        # lvlargs = {"generation_type": 0, "height": 30, "width": 150}
        # args: generation_type, height, width, room_density, room_size

        lvlargs = {"generation_type": 1, "height": 25, "width": 118,
                   "num_rooms": 20, "room_size": 9, "room_size_mod": 3, "player": player}
        level_data = generate_level(**lvlargs)

        while True:
            # Recalc visibility
            refresh_visibility(player.x, player.y, 200, level_data)
            # refresh_octant(player.x, player.y, 200, 0, level_data)

            # Center camera on player (as best as possible)

            # Draw camera contents
            # draw_camera(term, 0, 0, 25, 10, 1, 2)
            draw_camera(_term=term, cam_origin_x=0, cam_origin_y=0, cam_width=120, cam_height=27,
                        term_origin_x=0, term_origin_y=1, level_data=level_data, entities=entities, effects=effects)

            effects = []

            update_bottom_status(term, player, level_data)

            # Wait for an input
            key_input = term.inkey()
            if key_input == 'Q':
                break
            else:
                handle_input(key_input, level_data, entities, player, effects)
                set_message(_term=term, message="Message is set!")
                # player.x += 1
                # player.y += 1

    print("Exiting program...")


if __name__ == '__main__':
    main()
