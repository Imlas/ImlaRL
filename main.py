# cd PycharmProjects/ImlaRL
# assume a console window of 120 x 30
# Packages installed for this: blessed, skimage

# https://pypi.org/project/perlin-noise/
"""
print(f'The value is {foo}')
print(f"{foo = }")
print(f"{foo!r}") prints the repper of the value
print(f"{foo!a}") prints out all non-ascii characters as a unicode string
print(f"{foo!s}") calls the string conversion operater, mostly for the below ones
print(f"{foo=:%Y-%m-%d}") The ':' operator prefaces some formatting function
print(f"{foo:.2f}")



"""
# from typing import List, Tuple
# import time
from typing import TypeVar, Protocol, List, Dict, Tuple, Iterator

import blessed
import logging
from dataclasses import dataclass, field
from skimage.draw import line

from entity import Player
from globalEnums import DamageType, Point, Entity
from levelData import TermColor, LevelData, dijkstra_search, \
    reconstruct_path, a_star_search
from levelGeneration import generate_level

logging.basicConfig(filename='Imladebug.log', filemode='w', level=logging.DEBUG)


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

    # Note - without the field/factory, all ShadowLines share the same list, which is very not what we want

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


def draw_line(level_data: LevelData, x1: int, y1: int, x2: int, y2: int, char: str):
    # Adds a line to the effects "buffer"
    # The coords are in world space
    # Likely use this for stuff like targeting lines?
    rr, cc = line(y1, x1, y2, x2)
    logging.debug(f"rr: {rr}, cc: {cc}")
    for n in range(len(rr)):
        # e = Entity(int(cc[n]), int(rr[n]), char, EntityType.EFFECT, True, TermColor.RED)
        logging.debug(f"Line entity at {cc[n]},{rr[n]}, {char}, {type(cc[n])}, {type(rr[n])}")
        # level_data.effects.append(e)


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


def refresh_visibility(origin_x: int, origin_y: int, max_range: int, level_data: LevelData):
    # TODO: correctly implement sight range
    #  and later on, light sources
    for octant in range(8):
        refresh_octant(origin_x, origin_y, max_range, octant, level_data)


def refresh_octant(origin_x: int, origin_y: int, max_range: int, octant: int, level_data: LevelData):
    s_line = ShadowLine()
    full_shadow = False

    # logging.debug(f"Beginning an octant refresh starting at {origin_x},{origin_y}")

    # Be mindful that the row,col numbers here are in octant coordinates
    for row in range(1, max_range + 1):
        # logging.debug(f"{row = }")
        test_x, test_y = transform_octant(row, 0, octant)
        if (octant == 0 or octant == 7) and test_y + origin_y < 0:
            # logging.debug(f"Breaking octant {octant} due to hitting map boundary")
            break
        if (octant == 3 or octant == 4) and test_y + origin_y >= level_data.height:
            # logging.debug(f"Breaking octant {octant} due to hitting map boundary")
            break
        if (octant == 1 or octant == 2) and test_x + origin_x >= level_data.width:
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
            pos = Point(x, y)
            # logging.debug(f"-----Tile {x},{y}-----")

            # For now we'll just check each tile
            if x < 0 or y < 0 or x >= level_data.width or y >= level_data.height or pos not in level_data.tiles:
                # if level_data[x][y] is None:
                # logging.debug("Tile not valid. breaking to next tile")
                continue

            if full_shadow:
                # logging.debug(f"Shadow line is full. Setting is_visible False")
                level_data.tiles[pos].is_visible = False
            else:
                # logging.debug(f"Shadow line is not full. Calcing projection")

                projection = ShadowLine.project_tile(row, col)
                # logging.debug(f"{projection = }")
                # See if this tile is visible/currently in the shadow line
                # TODO: add in checking entities on this Tile to see if they block LOS
                visible = not s_line.is_in_shadow(projection)
                level_data.tiles[pos].is_visible = visible
                if visible is True:
                    level_data.tiles[pos].has_been_visible = True
                # logging.debug(f"Tile is vis: {visible} Blocks?: {level_data[x][y].is_blocking_LOS}")

                # Add the projection to the shadow line if this tile blocks LOS
                if visible and level_data.tiles[pos].is_blocking_LOS:
                    # logging.debug(f"Adding projection to shadow line")
                    s_line.add(projection)
                    full_shadow = s_line.is_full_shadow()


def draw_border(_term, origin_x, origin_y, box_width, box_height, border_char):
    """Draws a hollow box."""
    # draw a box from the top left corner
    print(_term.move_xy(origin_x, origin_y) + border_char * box_width)
    for i in range(origin_y + 1, box_height - 1):
        print(_term.move_xy(origin_x, i) + border_char + _term.move_xy(box_width - 1, i) + border_char)
    print(border_char * box_width + _term.home)  # Adding the term.home avoids corner/scrolling issues


def entities_in_frame(all_entities: list[Entity], cam_origin_x: int, cam_origin_y: int, cam_width: int,
                      cam_height: int, visibility: bool) -> list[Entity]:
    """Returns a list of all of the entities that are within the frame of the camera with matching visibility"""
    entities = []

    if len(all_entities) == 0:
        return entities

    # logging.debug(f"{all_entities = }")

    min_x, max_x = cam_origin_x, cam_origin_x + cam_width
    min_y, max_y = cam_origin_y, cam_origin_y + cam_height

    for e in all_entities:
        if min_x <= e.pos.x <= max_x and min_y <= e.pos.y <= max_y and e.is_visible == visibility:
            entities.append(e)

    return entities


def draw_camera(term, cam_origin_x: int, cam_origin_y: int, cam_width: int, cam_height: int,
                term_origin_x: int, term_origin_y: int, level_data: LevelData):
    """Draws everything in the camera view"""
    # Todo: Look into increasing performance in ths method (or seeing if this is actually the issue)
    # cam_origin x/y are in world-space
    # term_origin are the top-left corner in the console
    # Draw the tiles first
    for rows in range(cam_origin_y, cam_origin_y + cam_height):
        rowstr = ""
        for cols in range(cam_origin_x, cam_origin_x + cam_width):
            pos = Point(cols, rows)
            try:
                tile = level_data.tiles[pos]
                if tile.is_visible:
                    tile_char = term.color_rgb(*tile.visible_color.value) + \
                                tile.floor_char
                elif tile.has_been_visible:
                    tile_char = term.color_rgb(*tile.fow_color.value) + \
                                tile.floor_char
                else:
                    tile_char = " "
            except KeyError:
                tile_char = " "

            rowstr += tile_char
        print(term.move_xy(term_origin_x, rows + term_origin_y - cam_origin_y) + rowstr + term.normal)
    # Todo: I suspect it'll be faster/more performant to work the entity/vfx displays into the above loop
    #   instead of multiple loops/draw cycles
    #   term.move_xy(...) seems to be relatively expensive
    #   Also need to handle multiple Entities in one tile

    # Draw the floor items
    frame_items = entities_in_frame(all_entities=level_data.floor_items, cam_origin_x=cam_origin_x,
                                    cam_origin_y=cam_origin_y, cam_width=cam_width, cam_height=cam_height,
                                    visibility=True)
    frame_items = filter(lambda entity: level_data.tiles[entity.pos].is_visible, frame_items)
    draw_list_of_entities(frame_items, term, cam_origin_x, cam_origin_y, term_origin_x, term_origin_y)

    # Draw the interactables
    frame_interactables = entities_in_frame(all_entities=level_data.interactables, cam_origin_x=cam_origin_x,
                                            cam_origin_y=cam_origin_y, cam_width=cam_width, cam_height=cam_height,
                                            visibility=True)
    frame_interactables = filter(lambda entity: level_data.tiles[entity.pos].is_visible, frame_interactables)
    draw_list_of_entities(frame_interactables, term, cam_origin_x, cam_origin_y, term_origin_x, term_origin_y)

    # Draw the monsters
    frame_monsters = entities_in_frame(all_entities=level_data.monsters, cam_origin_x=cam_origin_x,
                                       cam_origin_y=cam_origin_y, cam_width=cam_width, cam_height=cam_height,
                                       visibility=True)
    frame_monsters = filter(lambda entity: level_data.tiles[entity.pos].is_visible, frame_monsters)
    draw_list_of_entities(frame_monsters, term, cam_origin_x, cam_origin_y, term_origin_x, term_origin_y)

    # Draw the floor effects
    frame_floor_effects = entities_in_frame(all_entities=level_data.floor_effects, cam_origin_x=cam_origin_x,
                                            cam_origin_y=cam_origin_y, cam_width=cam_width, cam_height=cam_height,
                                            visibility=True)
    frame_floor_effects = filter(lambda entity: level_data.tiles[entity.pos].is_visible, frame_floor_effects)
    draw_list_of_entities(frame_floor_effects, term, cam_origin_x, cam_origin_y, term_origin_x, term_origin_y)

    # Draw the vfx

    # Last - draw the player on top of everything else
    player = level_data.player
    print(term.move_xy(player.pos.x + term_origin_x - cam_origin_x, player.pos.y + term_origin_y - cam_origin_y)
          + term.color_rgb(*player.display_color.value) + player.display_char + term.normal)


def draw_list_of_entities(entities, term, cam_origin_x, cam_origin_y, term_origin_x, term_origin_y):
    for ent in entities:
        print(term.move_xy(ent.pos.x + term_origin_x - cam_origin_x, ent.pos.y + term_origin_y - cam_origin_y)
              + term.color_rgb(*ent.display_color.value) + ent.display_char + term.normal)


def set_message(_term, message: str):
    """Sets the single line message at the top of the screen"""
    # Need to check how this behaves for longer messages
    # And determine the behavior for multi-line messages/etc.
    print(_term.move_xy(0, 0) + message)


def update_bottom_status(_term, level_data: LevelData):
    print(_term.normal + _term.move_xy(0, _term.height - 2) + "Status text like health etc" + _term.normal)
    player = level_data.player
    print(_term.magenta_on_black + _term.move_xy(0,
                                                 _term.height - 1) + f"Player loc: {player.pos[0]:02d},{player.pos[1]:02d}" + _term.home + _term.normal)
    # f"{number:02d}"


def handle_input(key, level_data: LevelData, term):
    # I feel like we'll need to add some level of flags to this at some point to deal with menus/etc.
    if key.is_sequence:
        key = key.name

    player = level_data.player

    if key == 'KEY_UP' or key == '8':
        player.move_to(Point(player.pos.x + 0, player.pos.y - 1), level_data)
    elif key == 'KEY_DOWN' or key == '2':
        player.move_to(Point(player.pos.x + 0, player.pos.y + 1), level_data)
    elif key == 'KEY_LEFT' or key == '4':
        player.move_to(Point(player.pos.x - 1, player.pos.y + 0), level_data)
    elif key == 'KEY_RIGHT' or key == '6':
        player.move_to(Point(player.pos.x + 1, player.pos.y + 0), level_data)
    elif key == '1':
        player.move_to(Point(player.pos.x - 1, player.pos.y + 1), level_data)
    elif key == '3':
        player.move_to(Point(player.pos.x + 1, player.pos.y + 1), level_data)
    elif key == '7':
        player.move_to(Point(player.pos.x - 1, player.pos.y - 1), level_data)
    elif key == '9':
        player.move_to(Point(player.pos.x + 1, player.pos.y - 1), level_data)
    elif key == 'KEY_F1':
        logging.debug("F1 pressed!")
        set_message(_term=term,
                    message=f"{term.white_on_black}White on black {term.bright_black_on_black} Bright black on black{term.normal}")
    elif key == 'KEY_F2':
        logging.debug("F2 pressed!")
        player = level_data.player
        neighbors = level_data.get_neighbors(player.x, player.y)
        logging.debug(f"{neighbors = }")
    elif key == 'KEY_F3':
        logging.debug("F3 pressed!")
        """
        player = level_data.get_player()
        for e in level_data.entities:
            if e.etype == EntityType.MONSTER:
                logging.debug("--Starting dijkstra search--")
                came_from, cost_so_far = dijkstra_search(level_data, e.x, e.y, player.x, player.y)
                logging.debug(f"{came_from = }")
                logging.debug(f"{cost_so_far = }")
                logging.debug(f"Cost to reach player: {cost_so_far[(player.x, player.y)]}")
                path = reconstruct_path(came_from, e.x, e.y, player.x, player.y)
                logging.debug(f"Path from orc to player: {path}")

                logging.debug("--Starting AStar search--")
                came_from, cost_so_far = a_star_search(level_data, e.x, e.y, player.x, player.y)
                logging.debug(f"{came_from = }")
                logging.debug(f"{cost_so_far = }")
                logging.debug(f"Cost to reach player: {cost_so_far[(player.x, player.y)]}")
                path = reconstruct_path(came_from, e.x, e.y, player.x, player.y)
                logging.debug(f"Path from orc to player: {path}")
        """
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

    # origin_x, origin_y = 0, 1
    # box_width, box_height = term.width, term.height - 2
    # border_char = '#'

    # level_width = 20
    # level_height = 20

    # Should eventually make sure these update when the window is resized (if available in windows....)
    camera_width = term.width
    camera_height = term.height - 3
    camera_window_origin_x, camera_window_origin_y = 0, 1  # The x, y console-coords of the top-left of the camera view
    camera_x, camera_y = 0, 0  # The x,y world-coords of the top-left of the camera

    # level_data = []
    # entities = []
    # effects = []

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

        # Generate level data
        # lvlargs = {"generation_type": 0, "height": 30, "width": 150}
        # args: generation_type, height, width, room_density, room_size

        # tic = time.perf_counter()
        lvlargs = {"generation_type": 1, "height": 25, "width": 118,
                   "num_rooms": 20, "room_size": 9, "room_size_mod": 3}
        level_data = generate_level(**lvlargs)
        # toc = time.perf_counter()
        # logging.debug(f"Level generation completed after {toc-tic:0.4f} seconds")

        # Generate player entity
        player_armor = {DamageType.PHYSICAL: 0, DamageType.FIRE: 0, DamageType.LIGHTNING: 0, DamageType.COLD: 0,
                        DamageType.CORROSIVE: 0}
        player = Player(name="PlayerName", pos=level_data.player_start_pos,
                        display_char="@", display_color=TermColor.WHITE,
                        health_max=10.0, health=10, armor=player_armor, attack_power=5,
                        xp=0, next_level_xp=10, inventory=[])

        level_data.player = player

        # level_data.set_visibility_of_all(True)

        # logging.debug(f"Color Enum red: {TermColor.RED} {TermColor.RED.value}")

        while True:
            # Recalc visibility
            # tic = time.perf_counter()
            refresh_visibility(player.pos.x, player.pos.y, 200, level_data)
            # toc = time.perf_counter()
            # logging.debug(f"Visibility refresh completed after {toc - tic:0.4f} seconds")
            # refresh_octant(player.x, player.y, 200, 0, level_data)

            # Center camera on player (as best as possible)

            # Draw camera contents
            # draw_camera(term, 0, 0, 25, 10, 1, 2)
            draw_camera(term=term, cam_origin_x=camera_x, cam_origin_y=camera_y, cam_width=camera_width,
                        cam_height=camera_height,
                        term_origin_x=camera_window_origin_x, term_origin_y=camera_window_origin_y,
                        level_data=level_data)

            # level_data.vfx = []

            update_bottom_status(term, level_data)

            # test_str = "X"
            # r, g, b = TermColor.RED.value
            # print(term.move_xy(2, 10) + term.color_rgb(*TermColor.RED.value) + test_str + term.normal)

            # Wait for an input
            key_input = term.inkey()
            if key_input == 'Q':
                break
            else:
                handle_input(key_input, level_data, term)
                # set_message(_term=term, message="Message is set!")
                # player.x += 1
                # player.y += 1

            for m in level_data.monsters:
                m.update(level_data)

    print("Exiting program...")


if __name__ == '__main__':
    main()
