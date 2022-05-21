import heapq
from collections import deque
from enum import Enum, auto
from dataclasses import dataclass, field
import random
import logging
from typing import List

from globalEnums import TermColor

logging.basicConfig(filename='Imladebug.log', filemode='w', level=logging.DEBUG)


@dataclass()
class Tile:
    world_x: int
    world_y: int
    floor_char: str
    is_blocking_move: bool
    is_blocking_LOS: bool
    is_visible: bool
    visible_color: TermColor
    fow_color: TermColor
    has_been_visible: bool = False
    movement_weight: int = 1


class LevelData:
    def __init__(self, tile_data, player_start_pos: (int, int), monsters: List, floor_items: List,
                 floor_effects: List, interactables: List):
        self.tiles = tile_data  # TODO: restructure this as a dict[(int, int), Tile] setup
        self.width = len(self.tiles)
        self.height = len(self.tiles[0])
        self.player_start_pos = player_start_pos
        self.monsters = monsters
        self.floor_items = floor_items
        self.floor_effects = floor_effects
        self.interactables = interactables
        self.player = None

    def is_point_in_range(self, px, py):
        if 0 <= px < self.width and 0 <= py < self.height:
            return True
        return False

    def get_neighbors(self, px: int, py: int):
        """Returns a list of tuples of neighbors to tile (px,py) that are valid tiles and
            that are not is_blocking_move
            Right now we don't check to see if any monsters/etc. block the Tile
            Maybe add a bool to add that feature?"""
        if not self.is_point_in_range(px, py) or self.tiles[px][py] is None:
            return None

        neighbors = [(px - 1, py + 1), (px + 1, py + 1), (px + 1, py - 1), (px - 1, py - 1),
                     (px + 1, py + 0), (px - 1, py + 0), (px + 0, py + 1), (px + 0, py - 1)]
        results = filter(lambda point: self.is_point_in_range(point[0], point[1]), neighbors)
        results = filter(lambda point: not self.tiles[point[0]][point[1]].is_blocking_move, results)
        return list(results)

    def get_weight(self, x1, y1, x2, y2):
        """Returns the movement weight if moving from point (x1,y1) to (x2,y2)
            For now this is just the movement_weight of tile (x2,y2)
            And if the two tiles are diagonal to each other, a very small extra weight is added
            This is to encourage straight horizontal/vert lines over diag zigzags"""
        weight = self.tiles[x2][y2].movement_weight

        if abs(x2 - x1) == 1 and abs(y2 - y1) == 1:
            weight += 0.01

        return weight


def breadth_first_search(level_data: LevelData, start_x: int, start_y: int, goal_x: int, goal_y: int):
    frontier = deque()
    frontier.append((start_x, start_y))
    came_from = {}
    came_from[(start_x, start_y)] = None

    while not len(frontier) == 0:
        current = frontier.popleft()

        if current == (goal_x, goal_y):
            break

        # logging.debug(f"Visiting {current = }")
        for next_point in level_data.get_neighbors(*current):
            if next_point not in came_from:
                frontier.append(next_point)
                came_from[next_point] = current

    return came_from


def dijkstra_search(level_data: LevelData, start_x: int, start_y: int, goal_x: int, goal_y: int):
    frontier = []
    heapq.heappush(frontier, (0, (start_x, start_y)))
    came_from = {}
    cost_so_far = {}
    came_from[(start_x, start_y)] = None
    cost_so_far[(start_x, start_y)] = 0

    while not len(frontier) == 0:
        current = heapq.heappop(frontier)[1]

        if current == (goal_x, goal_y):
            break

        for next in level_data.get_neighbors(*current):
            new_cost = cost_so_far[current] + level_data.get_weight(current[0], current[1], next[0], next[1])
            if next not in cost_so_far or new_cost < cost_so_far[next]:
                cost_so_far[next] = new_cost
                priority = new_cost
                heapq.heappush(frontier, (new_cost, next))
                came_from[next] = current

    return came_from, cost_so_far


def a_star_heuristic(x1, y1, x2, y2):
    return abs(x1 - x2) + abs(y1 - y2)


def a_star_search(level_data: LevelData, start_x: int, start_y: int, goal_x: int, goal_y: int):
    frontier = []
    heapq.heappush(frontier, (0, (start_x, start_y)))
    came_from = {}
    cost_so_far = {}
    came_from[(start_x, start_y)] = None
    cost_so_far[(start_x, start_y)] = 0

    while not len(frontier) == 0:
        current = heapq.heappop(frontier)[1]

        if current == (goal_x, goal_y):
            break

        for next in level_data.get_neighbors(*current):
            new_cost = cost_so_far[current] + level_data.get_weight(current[0], current[1], next[0], next[1])
            if next not in cost_so_far or new_cost < cost_so_far[next]:
                cost_so_far[next] = new_cost
                priority = new_cost + a_star_heuristic(next[0], next[1], goal_x, goal_y)
                heapq.heappush(frontier, (new_cost, next))
                came_from[next] = current

    return came_from, cost_so_far


def reconstruct_path(came_from, start_x, start_y, goal_x, goal_y):
    current = (goal_x, goal_y)
    path = []
    while current != (start_x, start_y):  # This will fail if there's no path
        path.append(current)
        current = came_from[current]
    # path.append((start_x, start_y))
    path.reverse()
    return path
