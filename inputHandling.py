import logging

from globalEnums import Point, TermColor
from levelData import LevelData
from screenDrawing import TopMessage, draw_line, draw_cursor, WindowManager, line_as_points

logging.basicConfig(filename='Imladebug.log', filemode='w', level=logging.DEBUG)


def move_or_attack(pos: Point, level_data: LevelData):
    player = level_data.player
    # Check if there are any monsters in pos and attack them
    for monster in level_data.monsters:
        if monster.pos == pos:
            player.default_melee_attack(monster, level_data)
            return None
    # Try to move into pos
    player.move_to(pos, level_data)


def handle_input(key, level_data: LevelData, term) -> bool:
    """Returns a bool indicating if the player's turn is done and time should advance (monster update/etc.)"""
    # I feel like we'll need to add some level of flags to this at some point to deal with menus/etc.
    if key.is_sequence:
        key = key.name

    player = level_data.player

    if key == 'KEY_UP' or key == '8':
        """Move/attack up"""
        move_or_attack_pos = Point(player.pos.x + 0, player.pos.y - 1)
        move_or_attack(move_or_attack_pos, level_data)
        return True

    elif key == 'KEY_DOWN' or key == '2':
        """Move/attack down"""
        move_or_attack_pos = Point(player.pos.x + 0, player.pos.y + 1)
        move_or_attack(move_or_attack_pos, level_data)
        return True

    elif key == 'KEY_LEFT' or key == '4':
        """Move/attack left"""
        move_or_attack_pos = Point(player.pos.x - 1, player.pos.y + 0)
        move_or_attack(move_or_attack_pos, level_data)
        return True

    elif key == 'KEY_RIGHT' or key == '6':
        """Move/attack right"""
        move_or_attack_pos = Point(player.pos.x + 1, player.pos.y + 0)
        move_or_attack(move_or_attack_pos, level_data)
        return True

    elif key == '1':
        """Move/attack down-left"""
        move_or_attack_pos = Point(player.pos.x - 1, player.pos.y + 1)
        move_or_attack(move_or_attack_pos, level_data)
        return True

    elif key == '3':
        """Move/attack down-right"""
        move_or_attack_pos = Point(player.pos.x + 1, player.pos.y + 1)
        move_or_attack(move_or_attack_pos, level_data)
        return True

    elif key == '7':
        """Move/attack up-left"""
        move_or_attack_pos = Point(player.pos.x - 1, player.pos.y - 1)
        move_or_attack(move_or_attack_pos, level_data)
        return True

    elif key == '9':
        """Move/attack up-right"""
        move_or_attack_pos = Point(player.pos.x + 1, player.pos.y - 1)
        move_or_attack(move_or_attack_pos, level_data)
        return True

    elif key == '5':
        """Player wait"""
        return True

    elif key == '>':
        """Going down stairs"""
        return False

    elif key == '<':
        """Going up stairs"""
        return False

    elif key == '?':
        """Opens a help menu"""
        return False

    elif key == "a" or key == "A":
        """Begins a targeted attack"""
        return False

    elif key == "f" or key == "F":
        """Begins a ranged attack"""
        target_pos = begin_targeting(term, level_data, 10, True)
        if target_pos is None:
            # Canceled out of the targeting
            return False
        else:
            # Attempt to ranged attack the target in target_pos (if any)
            return True

    elif key == "j" or key == "J":
        """Opens the journal/log"""
        return False

    elif key == " ":
        """Dunno what this'll be used for yet. Maybe an alternate confirmation for attacks?"""
        return False

    elif key == "KEY_ENTER":
        """Confirms dialogues/selects in menus"""
        return False

    elif key == "KEY_ESCAPE":
        """Closes/cancels active menu? Maybe opens a main menu if nothing else open?"""
        return False

    elif key == 'KEY_F1':
        logging.debug("F1 pressed!")
        TopMessage.add_message("Top message here! Reporting for duty!")

        # set_message(_term=term,
          #           message=f"{term.white_on_black}White on black {term.bright_black_on_black} Bright black on black{term.normal}")
        return False

    elif key == 'KEY_F2':
        logging.debug("F2 pressed!")
        TopMessage.add_message("This is a very long test message so long in fact that it will be longer")
        TopMessage.add_message("than the screen width, which seems very very long indeed. Let's see how this")
        TopMessage.add_message("turns out for our messaging system!")

        return False

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
        return False

    elif key == 'KEY_F4':
        logging.debug("F4 pressed!")
        draw_line(level_data=level_data, p1=level_data.player.pos, p2=Point(40, 15), char='x', end_char='X', color=TermColor.RED)
        return False

    elif key == 'KEY_F5':
        logging.debug("F5 pressed!")
        return False

    elif key == 'KEY_F6':
        logging.debug("F6 pressed!")
        return False

    elif key == 'KEY_F7':
        logging.debug("F7 pressed!")
        return False

    elif key == 'KEY_F8':
        logging.debug("F8 pressed!")
        return False

    elif key == 'KEY_F9':
        logging.debug("F9 pressed!")
        return False

    else:
        logging.debug(f"Undefined key {key} pressed")
        return False


def begin_targeting(term, level_data: LevelData, max_range: int, should_draw_line: bool) -> Point | None:
    TopMessage.add_message("Targeting ranged attack. Space to confirm, ESC to cancel.")
    TopMessage.flush_message()

    player_pos = level_data.player.pos
    cursor_pos = level_data.player.pos

    valid_color = TermColor.LIME
    invalid_color = TermColor.RED

    while True:
        line_points = line_as_points(player_pos, cursor_pos)
        draw_color = valid_color
        for i in range(1, len(line_points)):
            if level_data.tiles[line_points[i]].is_blocking_LOS:
                draw_color = invalid_color

        if should_draw_line:
            draw_line(level_data, level_data.player.pos, cursor_pos, '.', 'X', draw_color)
        else:
            draw_cursor(level_data, cursor_pos, 'X', draw_color)

        # Draw the screen
        WindowManager.get_main_camera().draw_camera(level_data)

        # wait for a key input
        key = term.inkey()
        if key.is_sequence:
            key = key.name

        # esc exits returning None
        if key == "KEY_ESCAPE":
            return None

        # space/enter returns point
        if key == "KEY_ENTER" or key == " ":
            break

        # numpad/nums move cursor_pos
        new_cursor_pos = None
        if key == 'KEY_UP' or key == '8':
            """UP"""
            new_cursor_pos = Point(cursor_pos.x + 0, cursor_pos.y - 1)
        elif key == 'KEY_DOWN' or key == '2':
            """DOWN"""
            new_cursor_pos = Point(cursor_pos.x + 0, cursor_pos.y + 1)
        elif key == 'KEY_LEFT' or key == '4':
            """LEFT"""
            new_cursor_pos = Point(cursor_pos.x - 1, cursor_pos.y + 0)
        elif key == 'KEY_RIGHT' or key == '6':
            """RIGHT"""
            new_cursor_pos = Point(cursor_pos.x + 1, cursor_pos.y + 0)
        elif key == '1':
            """down-left"""
            new_cursor_pos = Point(cursor_pos.x - 1, cursor_pos.y + 1)
        elif key == '3':
            """down-right"""
            new_cursor_pos = Point(cursor_pos.x + 1, cursor_pos.y + 1)
        elif key == '7':
            """up-left"""
            new_cursor_pos = Point(cursor_pos.x - 1, cursor_pos.y - 1)
        elif key == '9':
            """up-right"""
            new_cursor_pos = Point(cursor_pos.x + 1, cursor_pos.y - 1)
        if new_cursor_pos is not None and abs(new_cursor_pos.x - player_pos.x) <= max_range and abs(new_cursor_pos.y - player_pos.y) <= max_range:
            cursor_pos = new_cursor_pos

    # Need to check if this is actually valid still
    return cursor_pos


