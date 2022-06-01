from loguru import logger
from shapely.geometry import Polygon, Point
import numpy as np

from level.Constants import resolution, ObjectType, LevelMetaData
from level.LevelElement import LevelElement
from util import RunConfig
from util.Utils import round_to_cord


class Level:

    def __init__(self, path: str, original_doc = None, blocks = True, pigs = True, platform = False):

        self.path = path
        self.original_doc = original_doc

        self.slingshot = None

        self.blocks: [LevelElement] = []
        self.pigs: [LevelElement] = []
        self.platform: [LevelElement] = []
        self.birds: [LevelElement] = []

        self.use_blocks = blocks
        self.use_pigs = pigs
        self.use_platform = platform

        self.is_normalized = False

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
        elif item == "Slingshot":
            return self.slingshot

    def __str__(self):
        return f"Path: {self.path}, Blocks: {len(self.blocks)} Pigs: {len(self.pigs)} Platform: {len(self.platform)} Bird: {len(self.birds)}"

    def separate_structures(self):
        test_list = self.create_element_list(self.use_blocks, self.use_pigs, self.use_platform, sort_list = True)

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
                        logger.debug(f"Block {current_element_id} -> {struct_element.id}: {float(dist_to_element)}")
                    if dist_to_element < 0.3:
                        closest_structures.append(structure)
                        break

            # Go over the structures closest to the element
            if len(closest_structures) == 0:
                # If there is no structure close means that it could be a new structure
                if RunConfig.verbose:
                    logger.debug("Create new Structure")
                self.structures.append([element])
            elif len(closest_structures) == 1:
                # Just one structure means it belongs to it
                if RunConfig.verbose:
                    logger.debug("Add to closest structure")
                closest_structures[0].append(element)
            else:
                # More than one structure means it adds all structures together
                if RunConfig.verbose:
                    logger.debug("Merge all closest structures")
                merge_into = closest_structures[0]
                for closest_structure in closest_structures[1:]:
                    for merge_element in closest_structure:
                        merge_into.append(merge_element)
                    self.structures.remove(closest_structure)
                merge_into.append(element)

        if RunConfig.verbose:
            for structure in self.structures:
                logger.debug(f"Structure amount: {len(structure)}")

        return self.structures

    def create_img(self, per_structure = True, dot_version = False):
        logger.debug("Create level img")
        if not per_structure:
            element_lists: [[LevelElement]] = [self.create_element_list(self.use_blocks, self.use_pigs, self.use_platform)]
        else:
            # Check if the level has been structurised
            if self.structures is None:
                self.separate_structures()

            element_lists: [[LevelElement]] = self.structures

        ret_pictures = []

        if not dot_version:

            for element_list in element_lists:
                min_x, min_y, max_x, max_y = self.calc_structure_dimensions(element_list)
                x_len = round((max_x - min_x) / resolution)
                y_len = round((max_y - min_y) / resolution)
                picture = np.zeros((y_len + 1, x_len + 1))

                # logger.debug(f"New Structure {(round((max_x - min_x) / resolution), round((max_y - min_y) / resolution))}")
                for element in element_list:

                    left_block_pos = element.x - element.width / 2 - min_x
                    right_block_pos = element.x + element.width / 2 - min_x
                    bottom_block_pos = element.y - element.height / 2 - min_y
                    top_block_pos = element.y + element.height / 2 - min_y
                    for x_pos in np.arange(left_block_pos, right_block_pos - resolution / 2, resolution):
                        for y_pos in np.arange(bottom_block_pos, top_block_pos - resolution / 2, resolution):

                            x_cord = round(x_pos / resolution)
                            y_cord = round(y_pos / resolution)
                            # print(f"picture[{x_cord}, {y_cord}] = {element.get_identifier()} of element {element.id}"
                            #       f"{f'x {x_cord} out of bounds {x_len}' if x_cord > x_len - 1 else ''} "
                            #       f"{f'y {y_cord} out of bounds {y_len}' if y_cord > y_len - 1 else ''}")
                            picture[y_len - y_cord - 1, x_cord] = element.get_identifier()

                ret_pictures.append(picture)

        else:
            for element_list in element_lists:
                min_x, min_y, max_x, max_y = self.calc_structure_dimensions(element_list)

                x_cords = np.arange(min_x + resolution / 2, max_x - resolution / 2, resolution)
                y_cords = np.arange(min_y + resolution / 2, max_y - resolution / 2, resolution)

                picture = np.zeros((len(y_cords), len(x_cords)))

                for i, y_cord in enumerate(y_cords):
                    for j, x_cord in enumerate(x_cords):
                        in_location = []

                        for element in element_list:
                            if element.shape_polygon.intersects(Point(x_cord, y_cord)):
                                in_location.append(element)
                                break

                        if len(in_location) == 0:
                            continue
                        elif len(in_location) >= 1:
                            picture[len(y_cords) - i - 1, j] = in_location[0].get_identifier()

                ret_pictures.append(picture)

        return ret_pictures

    def normalize(self):

        test_list: [LevelElement] = self.create_element_list(self.use_blocks, self.use_pigs, self.use_platform)

        min_x, min_y, max_x, max_y = self.calc_structure_dimensions(test_list)

        for element in test_list:
            element.x -= min_x
            element.y -= min_y
            element.coordinates[0] -= min_x
            element.coordinates[1] -= min_y

        self.is_normalized = True

    def print_elements(self, as_table = False):
        if not as_table:
            for element in self.blocks + self.pigs + self.platform:
                logger.debug(element)
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

            logger.debug(tabulate(data, headers = ["type", "material", "x", "y", "rotation", "sizes"]))

    def contains_od_rotation(self):

        test_list = self.create_element_list(self.use_blocks, self.use_pigs, self.use_platform)

        for element in test_list:
            orientation = element.rotation / 90
            next_integer = round(orientation)
            dist_to_next_int = abs(next_integer - orientation)
            if dist_to_next_int > 0.1:
                logger.debug(str(element))
                return True

        return False

    def create_polygons(self):
        test_list = self.create_element_list(self.use_blocks, self.use_pigs, self.use_platform)
        for element in test_list:
            element.shape_polygon = element.create_geometry()

    def get_used_elements(self):
        return self.create_element_list(self.use_blocks, self.use_pigs, self.use_platform)

    def create_element_list(self, blocks, pigs, platform, sort_list = False):
        test_list = []
        if blocks:   test_list += self.blocks
        if pigs:     test_list += self.pigs
        if platform: test_list += self.platform

        if sort_list:
            norm_list = np.linalg.norm(list(map(lambda x: x.coordinates, test_list)), axis = 1)
            index_list = np.argsort(norm_list)

            return list(np.array(test_list)[index_list])

        return test_list

    def filter_slingshot_platform(self):
        if len(self.platform) == 0:
            logger.debug("No Platform")
            return

        platform_coords = np.asarray(list(map(lambda p: p.coordinates, self.platform)))
        dist_to_slingshot = platform_coords - self.slingshot.coordinates
        norms = np.linalg.norm(dist_to_slingshot, axis = 1)

        remove_platforms = []

        for idx, norm in enumerate(norms):
            if norm < 4:
                remove_platforms.append(self.platform[idx])

        for remove_platform in remove_platforms:
            self.platform.remove(remove_platform)

    def get_level_metadata(self):
        current_elements = self.get_used_elements()
        return Level.calc_structure_meta_data(current_elements)

    @staticmethod
    def calc_structure_meta_data(element_list: [LevelElement]) -> LevelMetaData:
        min_x, min_y, max_x, max_y = Level.calc_structure_dimensions(element_list)
        block_amount = len([x for x in element_list if x.object_type == ObjectType.Block])
        pig_amount = len([x for x in element_list if x.object_type == ObjectType.Pig])
        platform_amount = len([x for x in element_list if x.object_type == ObjectType.Platform])
        special_block_amount = len([x for x in element_list if x.object_type == ObjectType.SpecialBlock])
        return LevelMetaData(
            height = max_y - min_y,
            width = max_x - min_x,
            block_amount = block_amount,
            pig_amount = pig_amount,
            platform_amount = platform_amount,
            special_block_amount = special_block_amount,
            total = block_amount + pig_amount + platform_amount + special_block_amount,
            stable = None,
        )

    @staticmethod
    def calc_structure_dimensions(element_list: [LevelElement], use_original = False):
        """
        Calculates with the given elements the metadata wanted
        :param element_list: The list of level elements which are included in the calculation
        """
        min_x, min_y, max_x, max_y = 10000, 10000, -10000, -10000
        for element in element_list:
            min_x = min(min_x, (element.x if not use_original else element.original_x) - element.width / 2)
            min_y = min(min_y, (element.y if not use_original else element.original_y) - element.height / 2)
            max_x = max(max_x, (element.x if not use_original else element.original_x) + element.width / 2)
            max_y = max(max_y, (element.y if not use_original else element.original_y) + element.height / 2)

        return round_to_cord(min_x), round_to_cord(min_y), round_to_cord(max_x), round_to_cord(max_y)
