import numpy as np
from shapely.geometry import Point
from tqdm import tqdm

from level import Constants
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

        for i, y_cord in enumerate(y_cords):
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
            cord_list.append(self.extract_element_data(element, x_cords, y_cords))

        picture = self.convert_into_img(cord_list)

        return self.remove_empty_line(picture)

    def create_calculated_img(self, element_list):
        min_x, min_y, max_x, max_y = calc_structure_dimensions(element_list)

        cord_list = []

        # logger.debug(f"New Structure {(round((max_x - min_x) / resolution), round((max_y - min_y) / resolution))}")
        for element in element_list:

            left_block_pos = element.x - element.width / 2 - min_x
            right_block_pos = element.x + element.width / 2 - min_x
            bottom_block_pos = element.y - element.height / 2 - min_y
            top_block_pos = element.y + element.height / 2 - min_y

            x_cord_range = np.linspace(left_block_pos + resolution / 2, right_block_pos - resolution / 2) + 0.00001
            y_cord_range = np.linspace(bottom_block_pos + resolution / 2, top_block_pos - resolution / 2) + 0.00001

            x_cords = np.unique(np.round(x_cord_range / resolution)).astype(np.int)
            y_cords = np.unique(np.round(y_cord_range / resolution)).astype(np.int)

            if len(x_cords) != element.int_width:
                right_stop = right_block_pos - resolution

                if len(x_cords) < element.int_width:
                    right_stop = right_block_pos + resolution / 2
                    pass

                x_cord_range = np.linspace(left_block_pos + resolution / 2, right_stop)
                x_cords = np.unique(np.round(x_cord_range / resolution)).astype(np.int)

            if len(y_cords) != element.int_height:
                top_stop = top_block_pos - resolution

                if len(x_cords) < element.int_width:
                    top_stop = top_block_pos + resolution / 2
                    pass

                y_cord_range = np.linspace(bottom_block_pos + resolution / 2, top_stop)
                y_cords = np.unique(np.round(y_cord_range / resolution)).astype(np.int)

            cord_list.append(self.extract_element_data(element, x_cords, y_cords))

        picture = self.convert_into_img(cord_list)

        return self.remove_empty_line(picture)

    def create_one_element_img(self, element_list, multilayer = False):
        min_x, min_y, max_x, max_y = calc_structure_dimensions(element_list)

        if multilayer:
            picture = np.zeros((int(max_y - resolution / 2), int(max_x - resolution / 2)))
        else:
            picture = np.zeros((int(max_y - resolution / 2), int(max_x - resolution / 2), 4))

        # logger.debug(f"New Structure {(round((max_x - min_x) / resolution), round((max_y - min_y) / resolution))}")
        for element in element_list:
            material_idx = Constants.materials.index(element.material) + 1
            type_idx = list(Constants.block_names.values()).index(element.type) + 1
            if element.is_vertical:
                type_idx += 1
            if multilayer:
                picture[element.x, element.y, material_idx] = type_idx
            else:
                element_idx = 40
                if element.object_type == ObjectType.Block:
                    element_idx = type_idx * material_idx

                picture[element.x, element.y] = element_idx

        return picture

    def remove_empty_line(self, picture):
        ret_img = picture[0, :]
        for y_value in range(1, picture.shape[0]):
            if np.max(picture[y_value, :]) != 0:
                ret_img = np.row_stack([ret_img, picture[y_value, :]])

        return ret_img

    def extract_element_data(self, element, x_cords, y_cords):
        return dict(
            x_cords = x_cords,
            y_cords = y_cords,
            is_pig = element.object_type == ObjectType.Pig,
            min_x = np.min(x_cords),
            min_y = np.min(y_cords),
            max_x = np.max(x_cords),
            max_y = np.max(y_cords),
            width = np.max(x_cords) - np.min(x_cords),
            height = np.max(y_cords) - np.min(y_cords),
            material = element.get_identifier()
        )

    def convert_into_img(self, cord_list):
        min_x = np.min(list(map(lambda x: x['min_x'], cord_list)))
        min_y = np.min(list(map(lambda x: x['min_y'], cord_list)))
        img_width = np.max(list(map(lambda x: x['max_x'] - min_x, cord_list)))
        img_height = np.max(list(map(lambda x: x['max_y'] - min_y, cord_list)))
        picture = np.zeros((img_height + 1, img_width + 1))
        for cords in cord_list:
            cords['y_cords'] -= min_y
            cords['x_cords'] -= min_x
            x_pos, y_pos = np.meshgrid(img_height - cords['y_cords'], cords['x_cords'])
            if cords['is_pig']:
                x_center = np.average(x_pos)
                y_center = np.average(y_pos)
                r = np.sqrt((x_pos - x_center) ** 2 + (y_pos - y_center) ** 2)
                inside = r < 3.17
                picture[x_pos[inside], y_pos[inside]] = cords['material']
            else:
                picture[x_pos, y_pos] = cords['material']

        return picture
