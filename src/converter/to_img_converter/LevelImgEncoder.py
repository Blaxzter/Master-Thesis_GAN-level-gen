import numpy as np
from shapely.geometry import Point
from tqdm import tqdm

from level.Constants import resolution
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
        x_len = round((max_x - min_x) / resolution)
        y_len = round((max_y - min_y) / resolution)
        picture = np.zeros((y_len + 1, x_len + 1))

        # logger.debug(f"New Structure {(round((max_x - min_x) / resolution), round((max_y - min_y) / resolution))}")
        for element in element_list:

            left_block_pos = element.x - element.width / 2 - min_x
            right_block_pos = element.x + element.width / 2 - min_x
            bottom_block_pos = element.y - element.height / 2 - min_y
            top_block_pos = element.y + element.height / 2 - min_y
            for x_pos in np.arange(left_block_pos, right_block_pos, resolution):
                for y_pos in np.arange(bottom_block_pos, top_block_pos, resolution):
                    x_cord = round(x_pos / resolution)
                    y_cord = round(y_pos / resolution)
                    # print(f"picture[{x_cord}, {y_cord}] = {element.get_identifier()} of element {element.id}"
                    #       f"{f'x {x_cord} out of bounds {x_len}' if x_cord > x_len - 1 else ''} "
                    #       f"{f'y {y_cord} out of bounds {y_len}' if y_cord > y_len - 1 else ''}")
                    picture[y_len - y_cord - 1, x_cord] = element.get_identifier()

        return picture
