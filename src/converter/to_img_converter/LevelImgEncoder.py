import numpy as np
from shapely.geometry import Point
from tqdm import tqdm

from level.Constants import resolution, ObjectType
from level.LevelUtil import calc_structure_dimensions
from util.Config import Config


class LevelImgEncoder:

    def __init__(self, config = None):
        self.config = config
        if self.config is None:
            self.config = Config.get_instance()

    def create_img_of_structures(self, element_lists, dot_version):
        ret_images = []
        if not dot_version:
            for element_list in element_lists:
                ret_images.append(
                    self.create_calculated_img(element_list)
                )

        else:
            for element_list in element_lists:
                ret_images.append(
                    self.create_dot_img(element_list)
                )
        return ret_images

    def create_dot_img(self, element_list):
        working_list = element_list.copy()

        min_x, min_y, max_x, max_y = calc_structure_dimensions(working_list)

        x_cords = np.arange(min_x + resolution / 2, max_x - resolution / 2, resolution)
        y_cords = np.arange(min_y + resolution / 2, max_y - resolution / 2, resolution)

        picture = np.zeros((len(y_cords), len(x_cords)))

        coordinate_lists = np.array([[element.x, element.y] for element in working_list])

        for i, y_cord in tqdm(enumerate(y_cords), total = len(y_cords)):
            for j, x_cord in enumerate(x_cords):
                in_location = []

                norm = np.linalg.norm(coordinate_lists - np.array([x_cord, y_cord]), axis = 1)
                sorted = np.argsort(norm)

                for element_idx in sorted:
                    element = working_list[element_idx.item()]
                    if element.shape_polygon.intersects(Point(x_cord, y_cord)):
                        in_location.append(element)
                        break

                if len(in_location) == 0:
                    continue
                elif len(in_location) >= 1:
                    picture[len(y_cords) - i - 1, j] = in_location[0].get_identifier()

        return picture

    def create_calculated_img_no_size_check(self, element_list):
        min_x, min_y, max_x, max_y = calc_structure_dimensions(element_list)

        cord_list = []

        print(f'\n')

        # logger.debug(f"New Structure {(round((max_x - min_x) / resolution), round((max_y - min_y) / resolution))}")
        for element in element_list:

            left_block_pos = element.x - element.width / 2 - min_x
            right_block_pos = element.x + element.width / 2 - min_x
            bottom_block_pos = element.y - element.height / 2 - min_y
            top_block_pos = element.y + element.height / 2 - min_y

            x_cord_range = np.linspace(left_block_pos + resolution / 2, right_block_pos - resolution / 2) + 0.001
            y_cord_range = np.linspace(bottom_block_pos + resolution / 2, top_block_pos - resolution / 2) + 0.001

            x_cords = np.unique(np.round(x_cord_range / resolution)).astype(np.int)
            y_cords = np.unique(np.round(y_cord_range / resolution)).astype(np.int)

            # print(f'ID: {element.id} -> ({len(x_cords)}, {len(y_cords)})')

            cord_list.append(dict(
                x_cords = x_cords,
                y_cords = y_cords,
                max_x = np.max(x_cords),
                max_y = np.max(y_cords),
                material = element.get_identifier()
            ))

        img_width = np.max(list(map(lambda x: x['max_x'], cord_list)))
        img_height = np.max(list(map(lambda x: x['max_y'], cord_list)))

        picture = np.zeros((img_height, img_width))
        for cords in cord_list:
            picture[tuple(np.meshgrid(img_height - cords['y_cords'], cords['x_cords'] - 1))] = cords['material']

        return picture

    def create_calculated_img(self, element_list):
        min_x, min_y, max_x, max_y = calc_structure_dimensions(element_list)

        cord_list = []

        print(f'\n')

        # logger.debug(f"New Structure {(round((max_x - min_x) / resolution), round((max_y - min_y) / resolution))}")
        for element in element_list:

            left_block_pos = element.x - element.width / 2 - min_x
            right_block_pos = element.x + element.width / 2 - min_x
            bottom_block_pos = element.y - element.height / 2 - min_y
            top_block_pos = element.y + element.height / 2 - min_y

            x_cord_range = np.linspace(left_block_pos + resolution / 2, right_block_pos - resolution / 2) + 0.001
            y_cord_range = np.linspace(bottom_block_pos + resolution / 2, top_block_pos - resolution / 2) + 0.001

            x_cords = np.unique(np.round(x_cord_range / resolution)).astype(np.int)
            y_cords = np.unique(np.round(y_cord_range / resolution)).astype(np.int)

            if len(x_cords) != element.int_width:
                print(f"Id {element.id}: x_wrong {len(x_cords)} != {element.int_width}")
                right_stop = right_block_pos - resolution

                if len(x_cords) < element.int_width:
                    right_stop = right_block_pos + resolution / 2
                    pass

                x_cord_range = np.linspace(left_block_pos + resolution / 2, right_stop)
                x_cords = np.unique(np.round(x_cord_range / resolution)).astype(np.int)

            if len(y_cords) != element.int_height:
                print(f"Id {element.id}: y_wrong {len(y_cords)} != {element.int_height}")
                top_stop = top_block_pos - resolution

                if len(x_cords) < element.int_width:
                    top_stop = top_block_pos + resolution / 2
                    pass

                y_cord_range = np.linspace(bottom_block_pos + resolution / 2, top_stop)
                y_cords = np.unique(np.round(y_cord_range / resolution)).astype(np.int)

            cord_list.append(dict(
                x_cords = x_cords,
                y_cords = y_cords,
                max_x = np.max(x_cords),
                max_y = np.max(y_cords),
                material = element.get_identifier()
            ))

        img_width = np.max(list(map(lambda x: x['max_x'], cord_list)))
        img_height = np.max(list(map(lambda x: x['max_y'], cord_list)))

        picture = np.zeros((img_height, img_width))
        for cords in cord_list:
            picture[tuple(np.meshgrid(img_height - cords['y_cords'], cords['x_cords'] - 1))] = cords['material']

        return picture