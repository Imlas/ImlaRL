import heapq
from collections import deque
from enum import Enum, auto
from dataclasses import dataclass, field
import random
import logging
from typing import List, Protocol

from skimage.draw import line as draw_line

from globalEnums import TermColor, Entity, Point, Updatable

logging.basicConfig(filename='Imladebug.log', filemode='w', level=logging.DEBUG)





@dataclass()
class Tile:
    world_x: int
    world_y: int
    floor_char: str
    is_blocking_move: bool
    is_blocking_LOS: bool
    is_visible: bool  # This is more restrictive than is_in_LOS, since it must also be in range/in light/etc.
    is_in_LOS: bool
    visible_color: TermColor
    fow_color: TermColor
    has_been_visible: bool = False
    movement_weight: int = 1


class LevelData:
    def __init__(self, tile_data: dict[Point, Tile], height: int, width: int, player_start_pos: Point,
                 monsters: List[Entity | Updatable], floor_items: List[Entity], floor_effects: List[Entity | Updatable],
                 interactables: List[Entity], vfx: List[Entity]):
        self.tiles = tile_data
        self.width = width
        self.height = height
        self.player_start_pos = player_start_pos
        self.monsters = monsters
        self.floor_items = floor_items
        self.floor_effects = floor_effects
        self.interactables = interactables
        self.vfx = vfx
        self.player = None

    def is_point_in_range(self, point: Point) -> bool:
        """Returns true if point is greater than 0,0 but within bounds of width/height"""
        return 0 <= point.x < self.width and 0 <= point.y < self.height

    def get_neighbors(self, p: Point) -> list[Point] | None:
        """Returns a list of tuples of neighbors to tile (px,py) that are valid tiles and
            that are not is_blocking_move
            Right now we don't check to see if any monsters/etc. block the Tile
            Maybe add a bool to add that feature?"""
        # logging.debug(f"getting neighbors for {p = }")
        if not self.is_point_in_range(p) or p not in self.tiles:
            logging.debug(f"{self.is_point_in_range(p)}, {p in self.tiles}")
            return None

        neighbors = [Point(p.x - 1, p.y + 1), Point(p.x + 1, p.y + 1), Point(p.x + 1, p.y - 1), Point(p.x - 1, p.y - 1),
                     Point(p.x + 1, p.y + 0), Point(p.x - 1, p.y + 0), Point(p.x + 0, p.y + 1), Point(p.x + 0, p.y - 1)]
        # logging.debug(f"{neighbors = }")
        results = filter(lambda pt: self.is_point_in_range(pt), neighbors)
        results = filter(lambda pt: not self.tiles[pt].is_blocking_move, results)
        return list(results)

    def get_weight(self, p1: Point, p2: Point) -> float:
        """Returns the movement weight if moving from point p1 to p2
            For now this is just the movement_weight of tile (x2,y2)
            And if the two tiles are diagonal to each other, a very small extra weight is added
            This is to encourage straight horizontal/vert lines over diag zigzags"""
        weight = self.tiles[p2].movement_weight

        if abs(p2.x - p1.x) == 1 and abs(p2.y - p1.y) == 1:
            weight += 0.01

        return weight

    def set_visibility_of_all(self, new_vis: bool):
        """Sets both the is_visible and has_been_visible flags to new_vis for all tiles
            Meant for debugging purposes"""
        for point in self.tiles:
            self.tiles[point].is_visible = new_vis
            self.tiles[point].has_been_visible = new_vis


"""
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
"""


def dijkstra_search(level_data: LevelData, start_pos: Point, goal_pos: Point):
    frontier: List[(float, Point)] = []
    heapq.heappush(frontier, (0, start_pos))
    came_from: dict[Point, Point | None] = {}
    cost_so_far: dict[Point, float] = {}
    came_from[start_pos] = None
    cost_so_far[start_pos] = 0

    while not len(frontier) == 0:
        current = heapq.heappop(frontier)[1]

        if current == goal_pos:
            break

        for next_pos in level_data.get_neighbors(*current):
            new_cost = cost_so_far[current] + level_data.get_weight(current, next_pos)
            if next_pos not in cost_so_far or new_cost < cost_so_far[next_pos]:
                cost_so_far[next_pos] = new_cost
                priority = new_cost
                heapq.heappush(frontier, (new_cost, next_pos))
                came_from[next_pos] = current

    return came_from, cost_so_far


def a_star_heuristic(p1: Point, p2: Point):
    return abs(p1.x - p2.x) + abs(p1.y - p2.y)


def a_star_search(level_data: LevelData, start_pos: Point, goal_pos: Point) -> \
        tuple[dict[Point, Point | None], dict[Point, float]]:
    # TODO: perhaps add a return flag here if a valid path was not found
    frontier: list[(float, Point)] = []
    heapq.heappush(frontier, (0, start_pos))
    came_from: dict[Point, Point | None] = {}
    cost_so_far: dict[Point, float] = {}

    came_from[start_pos] = None
    cost_so_far[start_pos] = 0

    while not len(frontier) == 0:
        current = heapq.heappop(frontier)[1]
        # logging.debug(f"astar {current = }")

        if current == goal_pos:
            break

        for next_pos in level_data.get_neighbors(current):
            new_cost = cost_so_far[current] + level_data.get_weight(current, next_pos)
            if next_pos not in cost_so_far or new_cost < cost_so_far[next_pos]:
                cost_so_far[next_pos] = new_cost
                priority = new_cost + a_star_heuristic(next_pos, goal_pos)
                heapq.heappush(frontier, (priority, next_pos))
                came_from[next_pos] = current

    return came_from, cost_so_far


def reconstruct_path(came_from: dict[Point, Point | None], start_point: Point, goal_point: Point) -> list[Point]:
    current = goal_point
    path: List[Point] = []
    while current != start_point:  # This will fail if there's no path
        # TODO: this can fail if there's no valid path - check here or in the search
        path.append(current)
        current = came_from[current]
    # path.append(start_point)
    path.reverse()
    return path


def are_points_in_LOS(p1: Point, p2: Point, level_data: LevelData) -> bool:
    """Returns True if the line between p1 and p2 does not contain any tiles that block LOS
        This includes p1 and p2"""
    # TODO: right now this is overly restrictive.
    #   Possible fixes include casting this line to/from all the squares around each point (ick)
    #   Better is using the shadow-casting slope somehow
    #   Or keeping another property on Tiles to distinguish "within-LOS" and "visible"
    #   Where visible is only true if within sight-range and lit
    rr, cc = draw_line(p1.y, p1.x, p2.y, p2.x)

    for n in range(len(rr)):
        line_point = Point(cc[n], rr[n])
        if level_data.tiles[line_point].is_blocking_LOS:
            return False

    return True


def are_points_within_distance(p1: Point, p2: Point, distance: int) -> bool:
    """Checks if the square of the distance between p1 and p2 is <= the square of distance
        Using squares saves the cpu-intensive sqroot call"""
    abs_x = abs(p1.x - p2.x)
    abs_y = abs(p1.y - p2.y)
    return abs_x * abs_x + abs_y * abs_y <= distance * distance


