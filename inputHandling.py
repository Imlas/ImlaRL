import logging

from globalEnums import Point
from levelData import LevelData
from screenDrawing import set_message

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
        move_or_attack_pos = Point(player.pos.x + 0, player.pos.y - 1)
        move_or_attack(move_or_attack_pos, level_data)
        return True

    elif key == 'KEY_DOWN' or key == '2':
        move_or_attack_pos = Point(player.pos.x + 0, player.pos.y + 1)
        move_or_attack(move_or_attack_pos, level_data)
        return True

    elif key == 'KEY_LEFT' or key == '4':
        move_or_attack_pos = Point(player.pos.x - 1, player.pos.y + 0)
        move_or_attack(move_or_attack_pos, level_data)
        return True

    elif key == 'KEY_RIGHT' or key == '6':
        move_or_attack_pos = Point(player.pos.x + 1, player.pos.y + 0)
        move_or_attack(move_or_attack_pos, level_data)
        return True

    elif key == '1':
        move_or_attack_pos = Point(player.pos.x - 1, player.pos.y + 1)
        move_or_attack(move_or_attack_pos, level_data)
        return True

    elif key == '3':
        move_or_attack_pos = Point(player.pos.x + 1, player.pos.y + 1)
        move_or_attack(move_or_attack_pos, level_data)
        return True

    elif key == '7':
        move_or_attack_pos = Point(player.pos.x - 1, player.pos.y - 1)
        move_or_attack(move_or_attack_pos, level_data)
        return True

    elif key == '9':
        move_or_attack_pos = Point(player.pos.x + 1, player.pos.y - 1)
        move_or_attack(move_or_attack_pos, level_data)
        return True

    elif key == '5':
        return True

    elif key == 'KEY_F1':
        logging.debug("F1 pressed!")
        set_message(_term=term,
                    message=f"{term.white_on_black}White on black {term.bright_black_on_black} Bright black on black{term.normal}")
        return False

    elif key == 'KEY_F2':
        logging.debug("F2 pressed!")
        player = level_data.player
        neighbors = level_data.get_neighbors(player.pos)
        logging.debug(f"{neighbors = }")
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
