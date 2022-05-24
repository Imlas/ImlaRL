import logging
from dataclasses import dataclass, field

from globalEnums import Point
from levelData import LevelData

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


def refresh_visibility(origin_x: int, origin_y: int, sight_range: int, level_data: LevelData):
    """Toggles the values of is_in_LOS for the tiles of level_data"""
    # TODO: correctly implement sight range
    #  and later on, light sources
    for octant in range(8):
        refresh_octant(origin_x, origin_y, sight_range, octant, level_data)


def refresh_octant(origin_x: int, origin_y: int, sight_range: int, octant: int, level_data: LevelData):
    s_line = ShadowLine()
    full_shadow = False

    # logging.debug(f"Beginning an octant refresh starting at {origin_x},{origin_y}")

    # Be mindful that the row,col numbers here are in octant coordinates
    for row in range(1, max(level_data.width, level_data.height)-1):
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
                level_data.tiles[pos].is_in_LOS = visible

                level_data.tiles[pos].is_visible = False
                if row <= sight_range:
                    # Later add a "is_lit" check here
                    level_data.tiles[pos].is_visible = visible
                    if visible is True:
                        level_data.tiles[pos].has_been_visible = True
                        # logging.debug(f"Tile is vis: {visible} Blocks?: {level_data[x][y].is_blocking_LOS}")

                # Add the projection to the shadow line if this tile blocks LOS
                if visible and level_data.tiles[pos].is_blocking_LOS:
                    # logging.debug(f"Adding projection to shadow line")
                    s_line.add(projection)
                    full_shadow = s_line.is_full_shadow()
