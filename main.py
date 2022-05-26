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
# import math
# from dataclasses import dataclass, field
from skimage.draw import line

from entity import Player
from globalEnums import DamageType, Point, Entity
from inputHandling import handle_input
from levelData import TermColor, LevelData, dijkstra_search, \
    reconstruct_path, a_star_search
from levelGeneration import generate_level
from screenDrawing import draw_camera, update_bottom_status, TopMessage
from shadowCasting import refresh_visibility

logging.basicConfig(filename='Imladebug.log', filemode='w', level=logging.DEBUG)


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
        TopMessage.set_terminal(term)
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
            refresh_visibility(player.pos.x, player.pos.y, player.sight_range, level_data)
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
            TopMessage.flush_message()

            # test_str = "X"
            # r, g, b = TermColor.RED.value
            # print(term.move_xy(2, 10) + term.color_rgb(*TermColor.RED.value) + test_str + term.normal)

            # Wait for an input
            key_input = term.inkey()
            if key_input == 'Q':
                break
            else:
                player_turn_done = handle_input(key_input, level_data, term)
                # set_message(_term=term, message="Message is set!")
                # player.x += 1
                # player.y += 1

            if player_turn_done:
                for m in level_data.monsters:
                    m.update(level_data)
                # Other update bits will go here as well. Floor effects ticking/etc.

    print("Exiting program...")


if __name__ == '__main__':
    main()
