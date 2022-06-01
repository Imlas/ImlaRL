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
from screenDrawing import draw_camera, update_bottom_status, TopMessage, center_camera_on_player, Camera, WindowManager
from shadowCasting import refresh_visibility

logging.basicConfig(filename='Imladebug.log', filemode='w', level=logging.DEBUG)


def main():
    term = blessed.Terminal()
    print(f"height:{term.height} width:{term.width}")
    print(f"Colors:{term.number_of_colors}")

    logging.debug("Program beginning. Terminal initialized.")

    camera_width = term.width
    camera_height = term.height - 3
    camera_window_origin_x, camera_window_origin_y = 0, 1  # The x, y console-coords of the top-left of the camera view
    camera_x, camera_y = 0, 0  # The x,y world-coords of the top-left of the camera
    main_cam = Camera(cam_origin_x=camera_window_origin_x, cam_origin_y=camera_window_origin_y, cam_width=camera_width,
                      cam_height=camera_height, term_origin_x=camera_window_origin_x,
                      term_origin_y=camera_window_origin_y, term=term)

    WindowManager.set_main_camera(main_cam)

    with term.fullscreen(), term.hidden_cursor(), term.cbreak():
        # Fun note! hidden_cursor needs to come after fullscreen
        print(term.home + term.clear, end='')
        TopMessage.set_terminal(term)

        # tic = time.perf_counter()
        lvlargs = {"generation_type": 1, "height": 40, "width": 140,
                   "num_rooms": 20, "room_size": 9, "room_size_mod": 3}
        level_data = generate_level(**lvlargs)
        # toc = time.perf_counter()
        # logging.debug(f"Level generation completed after {toc-tic:0.4f} seconds")

        # Generate fresh player entity
        # This should likely also pull from an XML file or some such
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

            # Resize camera (in-case window size has changed)
            main_cam.resize_camera()
            # Center camera on player (as best as possible)
            main_cam.center_camera_on_player(level_data)

            # Draw camera contents
            main_cam.draw_camera(level_data)
            """draw_camera(term=term, cam_origin_x=camera_x, cam_origin_y=camera_y, cam_width=camera_width,
                        cam_height=camera_height,
                        term_origin_x=camera_window_origin_x, term_origin_y=camera_window_origin_y,
                        level_data=level_data)"""

            # Update bottom status and push messages to top message line
            update_bottom_status(term, level_data)
            TopMessage.flush_message()

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
