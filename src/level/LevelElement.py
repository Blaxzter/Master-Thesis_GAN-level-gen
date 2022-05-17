from sympy.geometry import *

from level import Constants
from level.Constants import block_names, block_sizes


class LevelElement:

    def __init__(self, type, material, x, y, rotation, scaleX = None, scaleY = None):
        self.type = type
        self.material = material
        self.x = round(float(x) * Constants.coordinate_round) / Constants.coordinate_round
        self.y = round(float(y) * Constants.coordinate_round) / Constants.coordinate_round
        self.rotation = float(rotation)
        self.scaleX = float(scaleX) if scaleX is not None else None
        self.scaleY = float(scaleY) if scaleY is not None else None

        self.is_vertical = False
        if round(self.rotation / 90) in [1, 3]:
            self.is_vertical = True

        self.index = list(block_names.values()).index("RectSmall") + 1
        if self.is_vertical:
            self.index += 1

        self.polygon = None

    def create_geometry(self):
        horizontal_offset = block_sizes[str(self.index)][0] / 2
        vertical_offset = block_sizes[str(self.index)][1] / 2
        p1 = (self.x + horizontal_offset, self.y + vertical_offset)
        p2 = (self.x + horizontal_offset, self.y - vertical_offset)
        p3 = (self.x - horizontal_offset, self.y + vertical_offset)
        p4 = (self.x + horizontal_offset, self.y + vertical_offset)

        return Polygon(p1, p2, p3, p4)

    def distance(self, o):
        return self.polygon.distance(o.polygon)

    def __str__(self):
        return f"type: {self.type} " \
               f"material: {self.material} " \
               f"x: {self.x} " \
               f"y: {self.y} " \
               f"rotation: {self.rotation} " \
               f"scaleX: {self.scaleX} " \
               f"scaleY: {self.scaleY}"
