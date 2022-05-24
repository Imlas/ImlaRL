import logging
import math

from skimage.draw import line

from globalEnums import Entity, Point, TermColor
from levelData import LevelData

logging.basicConfig(filename='Imladebug.log', filemode='w', level=logging.DEBUG)


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
    # Todo: split this into two methods - one to append to the message, and another to "flush" it out to the screen
    # Need to check how this behaves for longer messages
    # And determine the behavior for multi-line messages/etc.
    print(_term.move_xy(0, 0) + message)


def update_bottom_status(_term, level_data: LevelData):
    player = level_data.player
    formatted_health = math.ceil(player.health)  # Small chance of float precision errors here
    formatted_max_health = math.ceil(player.health_max)

    # Todo: break this into some extra functions? Also add a health bar
    print(_term.normal + _term.move_xy(0, _term.height - 2) + f"Health: {_term.color_rgb(*TermColor.RED.value)}{formatted_health:02d}/{formatted_max_health:02d}" + _term.normal)
    print(_term.magenta_on_black + _term.move_xy(0,
                                                 _term.height - 1) + f"Player loc: {player.pos.x:02d},{player.pos.y:02d}" + _term.home + _term.normal)
    # f"{number:02d}"


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
