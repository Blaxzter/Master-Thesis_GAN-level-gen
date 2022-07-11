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

    def create_calculated_img(self, element_list):
        min_x, min_y, max_x, max_y = calc_structure_dimensions(element_list)

        cord_list = [

        ]

        print(f'\n')

        # logger.debug(f"New Structure {(round((max_x - min_x) / resolution), round((max_y - min_y) / resolution))}")
        for element in element_list:

            left_block_pos = element.x - element.width / 2 - min_x
            right_block_pos = element.x + element.width / 2 - min_x
            bottom_block_pos = element.y - element.height / 2 - min_y
            top_block_pos = element.y + element.height / 2 - min_y

            x_cord_range = np.linspace(left_block_pos + resolution / 2, right_block_pos - resolution / 2)
            y_cord_range = np.linspace(bottom_block_pos + resolution / 2, top_block_pos - resolution / 2)

            x_cords = np.unique(np.round(x_cord_range / resolution)).astype(np.int)
            y_cords = np.unique(np.round(y_cord_range / resolution)).astype(np.int)

            if len(x_cords) != element.int_width:
                right_stop = right_block_pos - resolution

                if len(x_cords) < element.int_width:
                    right_stop = right_block_pos + resolution / 2
                    pass

                x_cord_range = np.linspace(left_block_pos + resolution / 2, right_stop)
                x_cords = np.unique(np.round(x_cord_range / resolution)).astype(np.int)
                print(f"Hilfe hilfe: {len(x_cords)} != {element.int_width}")

            if len(y_cords) != element.int_height:
                top_stop = top_block_pos - resolution

                if len(x_cords) < element.int_width:
                    top_stop = top_block_pos + resolution / 2
                    pass

                y_cord_range = np.linspace(bottom_block_pos + resolution / 2, top_stop)
                y_cords = np.unique(np.round(y_cord_range / resolution)).astype(np.int)
                print(f"Hilfe hilfe: {len(y_cords)} != {element.int_height}")

            print(f'ID: {element.id} -> ({len(x_cords)}, {len(y_cords)})')

            cord_list.append(dict(
                x_cords = x_cords,
                y_cords = y_cords,
                max_x = np.max(x_cords),
                max_y = np.max(y_cords),
                material = element.get_identifier()
            ))

        img_width = np.max(list(map(lambda x: x['max_x'], cord_list)))
        img_height = np.max(list(map(lambda x: x['max_y'], cord_list)))

        picture = np.zeros((img_height + 1, img_width + 1))
        for cords in cord_list:
            picture[tuple(np.meshgrid(img_height - cords['y_cords'], cords['x_cords']))] = cords['material']

            # if len(x_cords) < element.int_width:
            #     x_cords = np.unique(np.round(
            #         np.linspace(left_block_pos + resolution / 2, right_block_pos) / resolution)).astype(np.int)
            #
            # if len(y_cords) < element.int_height:
            #     y_cords = np.unique(np.round(
            #         np.linspace(bottom_block_pos + resolution / 2, top_block_pos) / resolution)).astype(np.int)
            #
            # for x_pos in x_cords:
            #     for y_pos in y_cords:
            #
            #         # if element.object_type is ObjectType.Pig:
            #         #     dist = np.linalg.norm(np.array([element.x, element.y]) - np.array([x_pos, y_pos]))
            #         #     if dist > 0.21:
            #         #         continue
            #
            #         # x_cord = round(x_pos / resolution)
            #         # y_cord = round(y_pos / resolution)
            #         # print(f"picture[{x_cord}, {y_cord}] = {element.get_identifier()} of element {element.id}"
            #         #       f"{f'x {x_cord} out of bounds {x_len}' if x_cord > x_len - 1 else ''} "
            #         #       f"{f'y {y_cord} out of bounds {y_len}' if y_cord > y_len - 1 else ''}")
            #         picture[y_len - y_pos, x_pos] = element.get_identifier()

        return picture
