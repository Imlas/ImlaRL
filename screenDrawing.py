import logging
import math
import textwrap

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


def center_camera_on_player(cam_width: int, cam_height: int, level_data: LevelData) -> (int, int):
    """Returns a tuple with new (cam_origin_x, cam_origin_y) such that the camera is centered on the player"""
    """
    if level_width <= cam_width:
        new_cam_origin_x = 0
    else:
        new_cam_origin_x = min(level_width - cam_width, level_data.player.pos.x - int(cam_width/2))

    if level_height <= cam_height:
        new_cam_origin_y = 0
    else:
        new_cam_origin_y = min(level_height - cam_height, level_data.player.pos.y - int(cam_height / 2))
    """
    new_cam_origin_x = level_data.player.pos.x - int(cam_width / 2)
    new_cam_origin_y = level_data.player.pos.y - int(cam_height / 2)

    return new_cam_origin_x, new_cam_origin_y


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


class TopMessage:
    """TopMessage is a static class (I'm sure this isn't the right term) that handles pushing messages
        to the top of the screen"""
    # Tentative intended order of average message is "Foo attacks foo2! Foo2 takes 3 damage!"
    #  So the attacks message should post first.
    term = None
    message_buffer: str = ""

    @staticmethod
    def set_terminal(_term):
        """Sets the reference to the terminal that we'll be pushing to"""
        TopMessage.term = _term

    @staticmethod
    def add_message(message: str):
        """Appends 'message' to the current buffer to be displayed at the end of that update tick"""
        TopMessage.message_buffer = TopMessage.message_buffer + " " + message

    @staticmethod
    def flush_message():
        """Pushes the current message buffer to the screen and resets it"""
        # Todo: This still needs work
        # Need to check how this behaves for longer messages
        # And determine the behavior for multi-line messages/etc.

        if TopMessage.term is not None:
            _term = TopMessage.term
            _message = TopMessage.message_buffer
            target_width = _term.width - 3

            chunks = textwrap.wrap(_message, width=target_width)
            if len(chunks) > 0:
                _message = chunks.pop(0)
                if len(chunks) > 0:
                    _message = _message + "..."
            else:
                _message = ""

            print(_term.move_xy(0, 0) + format(_message, f'<{target_width}'))
            # print(_term.move_xy(0, 0) + "{:<{target_width}}".format(_message))  # Both this and the above line work
            TopMessage.message_buffer = ""


def update_bottom_status(_term, level_data: LevelData):
    player = level_data.player
    rounded_health = math.ceil(player.health)  # Small chance of float precision errors here
    rounded_max_health = math.ceil(player.health_max)
    formatted_health = "{:<7}".format(str(rounded_health) + "/" + str(rounded_max_health))
    formatted_pos = "{:<7}".format(str(player.pos.x) + "," + str(player.pos.y))

    # Todo: break this into some extra functions? Also add a health bar
    print(_term.normal + _term.move_xy(0,
                                       _term.height - 2) + f"Health: {_term.color_rgb(*TermColor.RED.value)}{formatted_health}" + _term.normal)
    print(_term.magenta_on_black + _term.move_xy(0,
                                                 _term.height - 1) + f"Player loc: {formatted_pos}" + _term.home + _term.normal)
    # f"{number:02d}"


class OverlayMenu:
    term = None
    root_menu = None

    def __init__(self, text: str, options: list[str] | None):
        self.text = text
        self.options = options
        if options is not None:
            self.active_option = 0  # The index of the list
        else:
            self.active_option = None

        # I'm debating heavily on how robust of a parent/child/root relationship I need to implement with this
        if OverlayMenu.root_menu is None:
            OverlayMenu.root_menu = self

    def close_menu(self):
        if OverlayMenu.root_menu is self:
            OverlayMenu.root_menu = None

    def navigate_next_option(self):
        if self.active_option is not None:
            if self.active_option < len(self.options) - 1:
                self.active_option += 1

    def navigate_previous_option(self):
        if self.active_option is not None:
            if self.active_option > 0:
                self.active_option -= 1

    def return_selected_option(self):
        if self.active_option is not None:
            return self.options[self.active_option]
        return None

    @staticmethod
    def draw_menu():
        if OverlayMenu.term is None or OverlayMenu.root_menu is None:
            return None

        # Draw a border to make it clearer that it's a menu
        # By default, let's have menus just occupy the camera area? Maybe 8-10 chars less wide

        # Actually display the menu here. Just focus on static text first before designing selection bits

    @staticmethod
    def set_terminal(_term):
        OverlayMenu.term = _term


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
