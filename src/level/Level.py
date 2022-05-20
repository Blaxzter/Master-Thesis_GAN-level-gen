import math

import numpy as np

from level.LevelElement import LevelElement
from util import RunConfig


class Level:

    def __init__(self, path: str, original_doc = None):

        self.path = path
        self.original_doc = original_doc

        self.blocks: [LevelElement] = []
        self.pigs: [LevelElement] = []
        self.platform: [LevelElement] = []
        self.birds: [LevelElement] = []

        # Level meta data
        self.min_x = None
        self.min_y = None
        self.max_x = None
        self.max_y = None

        self.structures = None

    def __getitem__(self, item):
        if item == "Block":
            return self.blocks
        elif item == "Pig":
            return self.pigs
        elif item == "Platform":
            return self.platform
        elif item == "Bird":
            return self.birds

    def __str__(self):
        return f"Blocks: {len(self.blocks)} Pigs: {len(self.pigs)} Platform: {len(self.platform)} Bird: {len(self.birds)}"

    def separate_structures(self, blocks = True, pigs = True, platform = False):
        test_list = self.create_element_list(blocks, pigs, platform, sorted = True)

        # A structure is a list of
        self.structures = []
        for element in test_list:

            current_element_id = element.id

            if len(self.structures) == 0:
                self.structures.append([element])
                continue

            closest_structures = []

            # Calculate distance between groups
            for structure in self.structures:

                for struct_element in structure:
                    dist_to_element = element.distance(struct_element)
                    if RunConfig.verbose:
                        print(f"Block {current_element_id} -> {struct_element.id}: {float(dist_to_element)}")
                    if dist_to_element < 0.1:
                        closest_structures.append(structure)
                        break

            # Go over the structures closest to the element
            if len(closest_structures) == 0:
                # If there is no structure close means that it could be a new structure
                if RunConfig.verbose:
                    print("Create new Structure")
                self.structures.append([element])
            elif len(closest_structures) == 1:
                # Just one structure means it belongs to it
                if RunConfig.verbose:
                    print("Add to closest structure")
                closest_structures[0].append(element)
            else:
                # More than one structure means it adds all structures together
                if RunConfig.verbose:
                    print("Merge all closest structures")
                merge_into = closest_structures[0]
                for closest_structure in closest_structures[1:]:
                    for merge_element in closest_structure:
                        merge_into.append(merge_element)
                    self.structures.remove(closest_structure)
                merge_into.append(element)

        if RunConfig.verbose:
            for structure in self.structures:
                print(f"Structure amount: {len(structure)}")

    def create_img(self, for_structures = True):
        pass

    def normalize(self, blocks = True, pigs = True, platform = False):

        test_list: [LevelElement] = self.create_element_list(blocks, pigs, platform)

        self.calc_level_metadata(test_list)

        for element in test_list:
            element.x -= self.min_x
            element.y -= self.min_y
            element.coordinates[0] -= self.min_x
            element.coordinates[1] -= self.min_y

    def calc_level_metadata(self, test_list: [LevelElement]):
        """
        Calculates with the given elements the metadata wanted
        :param test_list: The list of level elements which are included in the calculation
        """
        self.min_x, self.min_y, self.max_x, self.max_y = 10000, 10000, -10000, -10000
        for element in test_list:
            self.min_x = min(self.min_x, element.x)
            self.min_y = min(self.min_y, element.y)
            self.max_x = max(self.max_x, element.x)
            self.max_y = max(self.max_y, element.y)

    def print_elements(self, as_table = False):
        if not as_table:
            for element in self.blocks + self.pigs + self.platform:
                print(element)
        else:
            from tabulate import tabulate

            data = [[
                element.type,
                element.material,
                element.x,
                element.y,
                element.rotation,
                element.size
            ] for element in self.blocks + self.pigs + self.platform]

            print(tabulate(data, headers = ["type", "material", "x", "y", "rotation", "sizes"]))

    def contains_od_rotation(self, blocks = True, pigs = False, platform = False):

        test_list = self.create_element_list(blocks, pigs, platform)

        for element in test_list:
            orientation = element.rotation / 90
            next_integer = round(orientation)
            dist_to_next_int = abs(next_integer - orientation)
            if dist_to_next_int > 0.1:
                print(str(element))
                return True

        return False

    def create_polygons(self, blocks = True, pigs = True, platform = False):
        test_list = self.create_element_list(blocks, pigs, platform)
        for element in test_list:
            element.shape_polygon = element.create_geometry()

    def create_element_list(self, blocks, pigs, platform, sorted = False):
        test_list = []
        if blocks:   test_list += self.blocks
        if pigs:     test_list += self.pigs
        if platform: test_list += self.platform

        if sorted:
            norm_list = np.linalg.norm(list(map(lambda x: x.coordinates, test_list)), axis = 1)
            index_list = np.argsort(norm_list)

            return list(np.array(test_list)[index_list])

        return test_list
