import itertools

from sympy.geometry import *

from level import Constants
from util.Utils import round_cord


class LevelElement:

    id_iter = itertools.count(1)

    def __init__(self, type, material, x, y, rotation, scaleX = None, scaleY = None):
        self.id = next(LevelElement.id_iter)
        self.type = type
        self.material = material
        self.x = round(float(x) * Constants.coordinate_round) / Constants.coordinate_round
        self.y = round(float(y) * Constants.coordinate_round) / Constants.coordinate_round
        self.rotation = float(rotation)

        self.is_vertical = False
        if round(self.rotation / 90) in [1, 3]:
            self.is_vertical = True

        if self.type == "Platform":
            self.size = round_cord(float(scaleX),  float(scaleY))
        elif self.type in Constants.pig_types.values():
            self.size = Constants.pig_size
        else:
            self.index = list(Constants.block_names.values()).index(self.type) + 1
            if self.is_vertical:
                self.index += 1
            self.size = Constants.block_sizes[str(self.index)]

        self.polygon = None

    def get_bottom_left(self):
        horizontal_offset = self.size[0] / 2
        vertical_offset = self.size[1] / 2
        return round_cord(self.x - horizontal_offset, self.y - vertical_offset)

    def create_geometry(self):
        horizontal_offset = self.size[0] / 2
        vertical_offset = self.size[1] / 2
        p1 = round_cord(self.x + horizontal_offset, self.y + vertical_offset)
        p2 = round_cord(self.x + horizontal_offset, self.y - vertical_offset)
        p3 = round_cord(self.x - horizontal_offset, self.y - vertical_offset)
        p4 = round_cord(self.x - horizontal_offset, self.y + vertical_offset)

        return Polygon(p1, p2, p3, p4)

    def distance(self, o: Polygon):
        if self.polygon.intersect(o.polygon):
            return 0

        return self.polygon.distance(o.polygon)

    def __str__(self):
        return f"type: {self.type} " \
               f"material: {self.material} " \
               f"x: {self.x} " \
               f"y: {self.y} " \
               f"rotation: {self.rotation} " \
               f"size: {self.size} "
