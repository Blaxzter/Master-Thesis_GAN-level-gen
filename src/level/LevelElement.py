from __future__ import annotations

import itertools
from typing import Optional

import numpy as np
from shapely import affinity
from shapely.geometry import Polygon, Point

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

        if rotation is not None:
            self.rotation = float(rotation)
            self.is_vertical = False
            if round(self.rotation / 90) in [1, 3]:
                self.is_vertical = True

        self.coordinates = np.array([self.x, self.y])

        if self.type == "Platform":
            self.size = round_cord(float(scaleX) * 0.65,  float(scaleY) * 0.65)
        elif self.type in Constants.pig_types.values():
            self.size = Constants.pig_size
        elif self.type in Constants.additional_objects.values():
            self.index = list(Constants.additional_objects.values()).index(self.type) + 1
            self.size = Constants.additional_object_sizes[str(self.index)]
        elif self.type == "Slingshot":
            self.size = (0.25, 0.75)
        else:
            self.index = list(Constants.block_names.values()).index(self.type) + 1
            if self.is_vertical:
                self.index += 1
            self.size = Constants.block_sizes[str(self.index)]

        self.width = self.size[0]
        self.height = self.size[1]

        self.shape_polygon: Optional[Polygon] = None

    def get_bottom_left(self):
        horizontal_offset = self.size[0] / 2
        vertical_offset = self.size[1] / 2
        return round_cord(self.x - horizontal_offset, self.y - vertical_offset)

    def create_geometry(self):

        horizontal_offset = self.size[0] / 2
        vertical_offset = self.size[1] / 2

        if self.type in Constants.pig_types.values():
            return Point(self.x, self.y).buffer(self.size[0] / 2)
        elif self.type in Constants.additional_objects.values():
            if "Circle" in self.type:
                return Point(self.x, self.y).buffer(self.size[0] / 2)
            if "Triangle" in self.type:
                p1 = round_cord(self.x - horizontal_offset, self.y - vertical_offset)
                p2 = round_cord(self.x + horizontal_offset, self.y - vertical_offset)
                p3 = round_cord(self.x + horizontal_offset, self.y + vertical_offset)

                poly = Polygon([p1, p2, p3])
                return affinity.rotate(poly, self.rotation - 90, 'center')
        else:
            p1 = round_cord(self.x + horizontal_offset, self.y + vertical_offset)
            p2 = round_cord(self.x + horizontal_offset, self.y - vertical_offset)
            p3 = round_cord(self.x - horizontal_offset, self.y - vertical_offset)
            p4 = round_cord(self.x - horizontal_offset, self.y + vertical_offset)

            return Polygon([p1, p2, p3, p4])

    def distance(self, o: LevelElement):
        if not self.shape_polygon.disjoint(o.shape_polygon):
            return 0

        return self.shape_polygon.distance(o.shape_polygon)

    def get_identifier(self):
        return self.id

        if "Basic" in self.type:
            return 5
        if "Platform" in self.type:
            return 6
        return Constants.materials.index(self.material) + 1

    def __str__(self):
        return f"id: {self.id} " \
               f"type: {self.type} " \
               f"material: {self.material} " \
               f"x: {self.x} " \
               f"y: {self.y} " \
               f"rotation: {self.rotation} " \
               f"size: {self.size} "
