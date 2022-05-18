import math

from level.LevelElement import LevelElement


class Level:

    def __init__(self, original_doc = None):

        self.original_doc = original_doc

        self.blocks: [LevelElement] = []
        self.pigs: [LevelElement] = []
        self.platform: [LevelElement] = []
        self.birds: [LevelElement] = []

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
        test_list = self.create_element_list(blocks, pigs, platform)
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
                    print(f"Block {current_element_id} -> {struct_element.id}: {float(dist_to_element)}")
                    if dist_to_element < 0.1:
                        closest_structures.append(structure)

            if len(closest_structures) == 0:
                print("Create new Structure")
                self.structures.append([element])
            elif len(closest_structures) == 1:
                print("Add to closest structure")
                closest_structures[0].append(element)
            else:
                print("Merge all closest structures")
                merge_into = closest_structures[0]
                for closest_structure in closest_structures[1:]:
                    for merge_element in closest_structure:
                        merge_into.append(merge_element)

        for structure in self.structures:
            print(f"Structure amount: {len(structure)}")

    def create_img(self):
        pass

    def normalize(self, blocks = True, pigs = True, platform = False):

        test_list = self.create_element_list(blocks, pigs, platform)

        smallest_x = 100000
        smallest_y = 100000

        for element in test_list:
            if element.x < smallest_x:
                smallest_x = element.x
            if element.y < smallest_y:
                smallest_y = element.y

        for element in test_list:
            element.x += abs(smallest_x)
            element.y += abs(smallest_y)

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
            element.polygon = element.create_geometry()

    def create_element_list(self, blocks, pigs, platform):
        test_list = []
        if blocks:   test_list += self.blocks
        if pigs:     test_list += self.pigs
        if platform: test_list += self.platform
        return test_list
