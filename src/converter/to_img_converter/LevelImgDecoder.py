import itertools

import cv2
import matplotlib.pyplot as plt
import numpy as np
from matplotlib import patches
from shapely.geometry import Polygon, Point

from converter import MathUtil
from converter.to_img_converter.DecoderUtils import recalibrate_blocks
from level import Constants
from level.LevelElement import LevelElement
from level.LevelVisualizer import LevelVisualizer
from util.Config import Config


class LevelImgDecoder:

    def __init__(self):
        self.config = Config.get_instance()
        self.block_data = self.config.get_encoding_data(f"encoding_res_{Constants.resolution}")
        if type(self.block_data) is not str:
            self.resolution = self.block_data['resolution']
            del self.block_data['resolution']

        self.level_viz = LevelVisualizer()

    def decode_level(self, level_img):
        flipped = np.flip(level_img, axis = 0)
        level_img_8 = flipped.astype(np.uint8)
        top_value = np.max(level_img_8)
        bottom_value = np.min(level_img_8)

        no_birds = top_value != 4

        ret_blocks = []
        # Go over each contour color
        for contour_color in range(bottom_value + 1, top_value - (-1 if no_birds else + 0)):

            # Get the contour through open cv
            current_img = np.copy(level_img_8)
            current_img[current_img != contour_color] = 0
            contours, _ = cv2.findContours(current_img, cv2.RETR_LIST, cv2.CHAIN_APPROX_SIMPLE)

            def create_contour_dict(_contour):
                _contour_reshaped = _contour.reshape((len(_contour), 2))
                _poly = Polygon(_contour_reshaped)
                _required_area = _poly.area
                return dict(
                    contour = _contour_reshaped,
                    poly = _poly,
                    required_area = _required_area,
                    min_x = _contour_reshaped[:, 0].min()
                )

            # Create the contour data list and sort by required area
            contour_data_list = [create_contour_dict(contour) for contour in contours]
            contour_data_list = sorted(contour_data_list, key = lambda x: x['min_x'])

            # Go over each found contour
            for contour_idx, contour_data in enumerate(contour_data_list):

                # If more then 4 contour points then search for rectangles
                poly = contour_data['poly']
                contour = contour_data['contour']
                rectangles = [contour]
                if len(contour) > 4:
                    rectangles, _ = MathUtil.get_rectangles(contour, poly)

                # Calc data for each rectangle required in the find blocks method
                rectangles_with_data = []
                for rectangle in rectangles:
                    rectangles_with_data.append(
                        self.create_rect_dict(rectangle.reshape((4, 2)))
                    )

                # Sort the rectangles by area and create a dictionary out of them
                sorted_rectangles = sorted(rectangles_with_data, key = lambda x: x['area'], reverse = True)
                rect_dict = dict()
                for rec_idx, rec in enumerate(sorted_rectangles):
                    rect_dict[rec_idx] = rec

                # Select the blocks and designate the correct contour color as material
                selected_blocks = self.select_blocks(
                    rectangles = rect_dict,
                    used_blocks = [],
                    required_area = contour_data['required_area'],
                    poly = poly
                )
                if selected_blocks is None:
                    selected_blocks = self.select_blocks(
                        rectangles = rect_dict,
                        used_blocks = [],
                        required_area = contour_data['required_area'],
                        poly = poly
                    )
                    raise Exception('No Block Selected')

                if selected_blocks is not None:
                    for selected_block in selected_blocks:
                        selected_block['material'] = contour_color
                    ret_blocks.append(selected_blocks)

        # Maybe do a bit of block adjustment to fit better
        # Only required between selected blocks i guess :D

        flattend_blocks = list(itertools.chain(*ret_blocks))

        pig_positions = []
        if not no_birds:
            pig_positions = self.get_pig_position(flipped)

        # Create block elements out of the possible blocks and the rectangle
        level_elements = self.create_level_elements(flattend_blocks, pig_positions)

        created_level_elements = recalibrate_blocks(level_elements)

        return created_level_elements

    def get_pig_position(self, level_img):

        level_img_8 = level_img.astype(np.uint8)
        top_value = np.max(level_img_8)
        current_img = np.copy(level_img_8)
        current_img[current_img != top_value] = 0

        kernel = MathUtil.get_circular_kernel(6)
        erosion = cv2.erode(current_img, kernel, iterations = 1)
        contours, _ = cv2.findContours(erosion, cv2.RETR_LIST, cv2.CHAIN_APPROX_SIMPLE)
        bird_positions = []
        for contour in contours:
            contour_reshaped = contour.reshape((len(contour), 2))
            pos = np.average(contour_reshaped, axis = 0)
            bird_positions.append(pos)
        return bird_positions

    def select_blocks(self, rectangles, used_blocks, required_area, poly, occupied_area = 0):
        # Break condition
        if occupied_area != 0 and abs(required_area / occupied_area - 1) < 0.01:
            return used_blocks

        # Go over each rectangle
        for rec_idx, rec in rectangles.items():
            rx_1, rx_2, ry_1, ry_2 = (rec['min_x'], rec['max_x'], rec['min_y'], rec['max_y'])

            # check if rec overlaps a existing block significantly
            overlap = False
            for used_block in used_blocks:
                block_rec = used_block['rec']
                bx_1, bx_2, by_1, by_2 = (
                    block_rec['min_x'], block_rec['max_x'], block_rec['min_y'], block_rec['max_y'])
                dx = np.min([rx_2, bx_2]) - np.max([rx_1, bx_1])
                dy = np.min([ry_2, by_2]) - np.max([ry_1, by_1])
                if (dx > 0) and (dy > 0):
                    overlap = True
                    break

            if overlap:
                continue

            # Search for matching block sizes
            for block_idx, block in self.block_data.items():
                block_width, block_height = block['dim']
                width_diff = abs(block_width / rec['width'] - 1)
                height_diff = abs(block_height / rec['height'] - 1)

                if width_diff > 0.001 or height_diff > 0.001:
                    continue

                next_rectangles = rectangles.copy()
                del next_rectangles[rec_idx]
                new_block = dict(
                    block_type = block,
                    rec = rec
                )

                next_used_blocks = used_blocks.copy()
                next_used_blocks.append(new_block)

                def _get_direct_vectors():
                    return [
                        (np.array([rec['width'] / 2 + 1, 0]), rec['height']),
                        (np.array([-rec['width'] / 2 - 1, 0]), rec['height']),
                        (np.array([0, rec['height'] / 2 + 1]), rec['width']),
                        (np.array([0, - rec['height'] / 2 - 1]), rec['width']),
                    ]

                dots_outside = [(Point(rec['center_pos'] + c_vec), add_amount) for c_vec, add_amount in _get_direct_vectors()]
                sum_add_amount = np.sum(list(
                    map(lambda x: x[1],  # Map to the amount to be added if the dot is inside the poly
                        filter(lambda dot_outside: poly.intersects(dot_outside[0]), dots_outside)
                        )))

                selected_blocks = self.select_blocks(
                    rectangles = next_rectangles,
                    used_blocks = next_used_blocks,
                    required_area = required_area,
                    occupied_area = occupied_area + rec['area'] + sum_add_amount,
                    poly = poly
                )

                if selected_blocks is not None:
                    return selected_blocks

            # The rectangle is bigger than any available block
            # That means it consists out of multiple smaller one
            # Divide the area into divisions of possible blocks

            # Go over both orientations
            for (idx_1, primary_orientation), (idx_2, secondary_orientation) in \
                    [((1, 'height'), (0, 'width')), ((0, 'width'), (1, 'height'))]:

                # for rec_idx, rec in rectangles.items():
                # Only work with fitting blocks
                fitting_blocks = {
                    k: _block for k, _block in self.block_data.items()
                    if (_block[primary_orientation] + 2) / rec[primary_orientation] - 1 < 0.001 and \
                       abs((_block[secondary_orientation]) / rec[secondary_orientation] - 1) < 0.001
                }

                # No combination found for this block
                if len(fitting_blocks) == 0:
                    continue

                for combination_amount in range(2, 5):
                    combinations = itertools.product(fitting_blocks.items(), repeat = combination_amount)
                    to_big_counter = 0
                    for combination in combinations:

                        secondary_size = rec[secondary_orientation]

                        # Only elements with the same secondary_orientation
                        # secondary_direction_difference = np.sum(
                        #     list(map(lambda block: abs(block[1][secondary_orientation] - secondary_size), combination)))
                        # if secondary_direction_difference > 0.01:
                        #     continue

                        # Check if the two blocks combined can fit in the space
                        combined_height = np.sum(list(map(lambda block: block[1][primary_orientation], combination))) \
                                          + (combination_amount - 1)

                        height_difference = rec[primary_orientation] / (combined_height) - 1
                        if abs(height_difference) < 0.001:
                            # the two blocks fit in the space

                            next_rectangles = rectangles.copy()
                            # Check if there is remaining space in the secondary direction
                            # If so create a new rectangle there
                            # Or if the horizontal space is not filled then create a rec there
                            all_space_used = True
                            if rec[secondary_orientation] / secondary_size - 1 > 0.001:
                                rectangle = np.ndarray.copy(rec['rectangle'])
                                rectangle[0][idx_2] += secondary_size
                                rectangle[1][idx_2] += secondary_size

                                new_dict = self.create_rect_dict(rectangle)
                                next_rectangles[len(rectangles)] = new_dict
                                all_space_used = False

                            # Create the blocks of each block from bottom to top
                            next_used_blocks = used_blocks.copy()
                            start_value = ry_1 if primary_orientation == 'height' else rx_1
                            used_area = 0
                            for block_idx, block in combination:
                                block_rectangle = np.ndarray.copy(rec['rectangle'])
                                block_rectangle[1][idx_1] = start_value
                                block_rectangle[2][idx_1] = start_value

                                block_rectangle[0][idx_1] = start_value + block[f'{primary_orientation}']
                                block_rectangle[3][idx_1] = start_value + block[f'{primary_orientation}']
                                new_block = dict(
                                    block_type = block,
                                    rec = self.create_rect_dict(block_rectangle)
                                )
                                next_used_blocks.append(new_block)
                                used_area += block['area']
                                start_value += block[f'{primary_orientation}'] + 1

                            # Remove the current big rectangle
                            del next_rectangles[rec_idx]

                            selected_blocks = self.select_blocks(
                                rectangles = next_rectangles,
                                used_blocks = next_used_blocks,
                                required_area = required_area,
                                poly = poly,
                                occupied_area = occupied_area + (rec['area'] if all_space_used else used_area)
                            )

                            if selected_blocks is not None:
                                return selected_blocks

                        # This means the block were to big which means doesnt fit
                        if height_difference < 0:
                            to_big_counter += 1

                    # If all blocks combined were to big, we dont need to check more block combinations
                    if to_big_counter > len(list(combinations)):
                        break

        # We tested everything and nothing worked :(
        return None

    @staticmethod
    def create_level_elements(blocks, pig_position):
        ret_level_elements = []
        block_idx = 0
        for block_idx, block in enumerate(blocks):
            block_attribute = dict(
                type = block['block_type']['name'],
                material = Constants.materials[block['material'] - 1],
                x = np.average(block['rec']['rectangle'][:, 0]) * Constants.resolution,
                y = np.average(block['rec']['rectangle'][:, 1]) * Constants.resolution,
                rotation = 90 if block['block_type']['rotated'] else 0
            )
            element = LevelElement(id = block_idx, **block_attribute)
            element.create_set_geometry()
            ret_level_elements.append(element)
        block_idx += 1

        for pig_idx, pig in enumerate(pig_position):
            pig_attribute = dict(
                type = "BasicSmall",
                material = None,
                x = pig[0] * Constants.resolution,
                y = pig[1] * Constants.resolution,
                rotation = 0
            )
            element = LevelElement(id = pig_idx + block_idx, **pig_attribute)
            element.create_set_geometry()
            ret_level_elements.append(element)
        return ret_level_elements

    def create_rect_dict(self, rectangle, poly = None):
        ret_dict = dict(rectangle = rectangle)
        if poly is not None:
            ret_dict['contour_area'] = poly.area
        for key, value in MathUtil.get_contour_dims(rectangle).items():
            ret_dict[key] = value
        return ret_dict

    def visualize_contours(self, level_img):
        flipped = np.flip(level_img, axis = 0)
        level_img_8 = flipped.astype(np.uint8)
        top_value = np.max(level_img_8)
        bottom_value = np.min(level_img_8)

        no_birds = False
        if top_value == bottom_value + 1:
            no_birds = True

        ax_plot_positions = [['original', 'original', 'original']] + \
                            [[f'thresh_{i}', f'rectangle_{i}', f'decoded_{i}']
                             for i in range(bottom_value + 1, top_value - (-1 if no_birds else + 1))]
        if not no_birds:
            ax_plot_positions += [[f'pig_thresh', f'eroded', f'positions']]

        fig, axd = plt.subplot_mosaic(
            ax_plot_positions,
            dpi = 300,
            figsize = (8, 10)
        )

        axd['original'].imshow(level_img_8)
        axd['original'].axis('off')

        for color_idx in range(bottom_value + 1, top_value - (-1 if no_birds else + 1)):
            axs = [axd[ax_name] for ax_name in
                   [f'thresh_{color_idx}', f'rectangle_{color_idx}', f'decoded_{color_idx}']]

            self.visualize_one_decoding(level_img, material_id = color_idx, axs = axs)
            for ax in axs:
                ax.axis('off')

        if not no_birds:
            axs = [axd[ax_name] for ax_name in [f'pig_thresh', f'eroded', f'positions']]
            self.visualize_pig_position(level_img, axs = axs)

        plt.tight_layout()
        plt.show()

    def visualize_one_decoding(self, level_img, material_id = 0, axs = None):
        flipped = np.flip(level_img, axis = 0)
        level_img_8 = flipped.astype(np.uint8)
        original_img = level_img_8.copy()

        skip_first = True
        axs_idx = 0
        if axs is None:
            skip_first = False
            fig, axs = plt.subplots(1, 4, figsize = (10, 3), dpi = 300)

        if not skip_first:
            axs[axs_idx].imshow(level_img_8, origin='lower')
            axs[axs_idx].axis('off')
            axs_idx += 1

        level_img_8[level_img_8 != material_id] = 0
        contours, _ = cv2.findContours(level_img_8, cv2.RETR_LIST, cv2.CHAIN_APPROX_SIMPLE)

        contour_viz = level_img_8.copy()
        cv2.drawContours(contour_viz, contours, -1, 8, 1)
        axs[axs_idx].imshow(contour_viz, origin='lower')
        axs_idx += 1

        blocks = []

        for contour_idx, contour in enumerate(contours):
            contour_reshaped = contour.reshape((len(contour), 2))
            poly = Polygon(contour_reshaped)
            required_area = poly.area

            rectangles = [contour]
            contour_list = list(contour)
            if len(contour) > 4:
                rectangles, contour_list = MathUtil.get_rectangles(contour_reshaped, poly)

            hsv = plt.get_cmap('brg')
            dot_colors = hsv(np.linspace(0, 0.8, len(contour_list)))
            for dot_idx, (contour_point, dot_color) in enumerate(zip(contour_list, dot_colors)):
                point_flatten = contour_point.flatten()
                if len(contour_list) < 12:
                    axs[axs_idx].text(point_flatten[0], point_flatten[1], str(dot_idx), color = 'white',
                                      fontsize = 3, ha = 'center', va = 'center')
                dot = patches.Circle(point_flatten, 0.4)
                dot.set_facecolor(dot_color)
                axs[axs_idx].add_patch(dot)

            rectangle_data = []

            hsv = plt.get_cmap('brg')
            colors = hsv(np.linspace(0, 0.8, len(rectangles)))
            for rec_idx, rectangle in enumerate(rectangles):
                rect_reshaped = rectangle.reshape(4, 2)
                center = np.average(rect_reshaped, axis = 0)
                if len(contour_list) < 12:
                    axs[axs_idx].text(center[0], center[1], str(rec_idx), color = 'White', fontsize = 6,
                                      ha = 'center', va = 'center')
                new_patch = patches.Polygon(rect_reshaped, closed = True)
                new_patch.set_linewidth(0.6)
                new_patch.set_edgecolor(colors[rec_idx])
                new_patch.set_facecolor('none')
                axs[axs_idx].add_patch(new_patch)

                rectangle_data.append(self.create_rect_dict(rectangle.reshape((4, 2))))

            axs[axs_idx].imshow(original_img, origin='lower')

            # Sort by rectangle size
            rectangles = sorted(rectangle_data, key = lambda x: x['area'], reverse = True)

            rect_dict = dict()
            for rec_idx, rec in enumerate(rectangles):
                rect_dict[rec_idx] = rec

            selected_blocks = self.select_blocks(
                rectangles = rect_dict.copy(),
                used_blocks = [],
                required_area = required_area,
                poly = poly
            )

            if selected_blocks is None:
                print(rect_dict)
                print(len(contour))
                selected_blocks = self.select_blocks(
                    rectangles = rect_dict,
                    used_blocks = [],
                    required_area = required_area,
                    poly = poly
                )
                raise Exception("No Block Selected")
            if selected_blocks is not None:
                for selected_block in selected_blocks:
                    selected_block['material'] = material_id
                blocks.append(selected_blocks)

        # Maybe do a bit of block adjustment to fit better
        # Only required between selected blocks i guess :D

        flattend_blocks = list(itertools.chain(*blocks))
        axs_idx += 1
        # Create block elements out of the possible blocks and the rectangle
        level_elements = self.create_level_elements(flattend_blocks, [])
        axs[axs_idx].imshow(level_img_8, origin='lower')
        self.level_viz.create_img_of_structure(level_elements, ax = axs[axs_idx], scaled = True)

        if not skip_first:
            plt.tight_layout()
            plt.show()

    def visualize_pig_position(self, level_img, axs = None):

        if axs is None:
            fig, axs = plt.subplots(1, 3)

        level_img_8 = level_img.astype(np.uint8)
        top_value = np.max(level_img_8)
        current_img = np.copy(level_img_8)
        current_img[current_img != top_value] = 0
        axs[0].imshow(current_img)
        axs[0].axis('off')

        kernel = MathUtil.get_circular_kernel(6)
        erosion = cv2.erode(current_img, kernel, iterations = 1)
        contours, _ = cv2.findContours(erosion, cv2.RETR_LIST, cv2.CHAIN_APPROX_SIMPLE)
        axs[1].imshow(erosion)
        axs[1].axis('off')

        pig_positions = []
        for contour in contours:
            contour_reshaped = contour.reshape((len(contour), 2))
            pos = np.average(contour_reshaped, axis = 0)
            pig_positions.append(pos)

        for position in pig_positions:
            new_patch = patches.Circle((position[0], position[1]), radius = 0.5 / 2 * 1 / Constants.resolution)
            new_patch.set_facecolor('red')
            axs[2].add_patch(new_patch)

        axs[2].imshow(erosion)
        axs[2].axis('off')

        return pig_positions

    def visualize_rectangles(self, level_img, material_id = 1, axs = None):
        # Create a copy of the img to manipulate it for the contour finding
        current_img = np.ndarray.copy(level_img)
        current_img = current_img.astype(np.uint8)
        current_img[current_img != material_id] = 0

        show_img = False
        if axs is None:
            show_img = True
            fig, axs = plt.subplots(1, 3, dpi = 500, figsize = (12, 3))

        axs[0].set_title("Original Dots")
        axs[0].imshow(current_img)

        axs[1].set_title("With Added Dots")
        axs[1].imshow(current_img)

        axs[2].set_title("Found Rectangles")
        axs[2].imshow(current_img)

        # get the contours
        contours, _ = cv2.findContours(current_img, cv2.RETR_LIST, cv2.CHAIN_APPROX_SIMPLE)

        for contour_idx, contour in enumerate(contours):
            contour_reshaped = contour.reshape((len(contour), 2))
            poly = Polygon(contour_reshaped)

            contour_list = contour_reshaped

            hsv = plt.get_cmap('brg')
            dot_colors = hsv(np.linspace(0, 0.8, len(contour_list)))
            for dot_idx, (contour_point, dot_color) in enumerate(zip(contour_list, dot_colors)):
                point_flatten = contour_point.flatten()
                if len(contour_list) < 12:
                    axs[0].text(point_flatten[0], point_flatten[1], str(dot_idx), color = 'white',
                                fontsize = 2.5, ha = 'center', va = 'center')
                dot = patches.Circle(point_flatten, 0.4)
                dot.set_facecolor(dot_color)
                axs[0].add_patch(dot)

            rectangles, contour_list = MathUtil.get_rectangles(contour_reshaped, poly)

            hsv = plt.get_cmap('brg')
            dot_colors = hsv(np.linspace(0, 0.8, len(contour_list)))
            for dot_idx, (contour_point, dot_color) in enumerate(zip(contour_list, dot_colors)):
                point_flatten = contour_point.flatten()
                axs[1].text(point_flatten[0], point_flatten[1], str(dot_idx), color = 'white',
                            fontsize = 2.5, ha = 'center', va = 'center')
                dot = patches.Circle(point_flatten, 0.4)
                dot.set_facecolor(dot_color)
                axs[1].add_patch(dot)

            hsv = plt.get_cmap('brg')
            colors = hsv(np.linspace(0, 0.8, len(rectangles)))
            for rec_idx, rectangle in enumerate(rectangles):
                new_patch = patches.Polygon(rectangle.reshape(4, 2), closed = True)
                new_patch.set_linewidth(0.6)
                new_patch.set_edgecolor(colors[rec_idx])
                new_patch.set_facecolor('none')
                axs[2].add_patch(new_patch)

                for dot, dot_color in zip(rectangle, ['red', 'green', 'blue', 'black']):
                    dot = patches.Circle(dot.flatten(), 0.4)
                    dot.set_facecolor(dot_color)
                    axs[2].add_patch(dot)

        if show_img:
            plt.tight_layout()
            plt.show()

    def visualize_rectangle(self, level_img, material_id, ax = None):
        """
        Visualizes the rectangles of one level img
        """
        current_img = np.ndarray.copy(level_img)
        current_img = current_img.astype(np.uint8)
        current_img[current_img != material_id] = 0

        show_img = False
        if ax is None:
            show_img = True
            fig, ax = plt.subplots(1, 1, dpi = 300)

        # get the contours
        contours, _ = cv2.findContours(current_img, cv2.RETR_LIST, cv2.CHAIN_APPROX_SIMPLE)
        ax.imshow(current_img)
        for contour_idx, contour in enumerate(contours):
            contour_reshaped = contour.reshape((len(contour), 2))
            poly = Polygon(contour_reshaped)

            rectangles, contour_list = MathUtil.get_rectangles(contour_reshaped, poly)

            hsv = plt.get_cmap('brg')
            colors = hsv(np.linspace(0, 0.8, len(rectangles)))
            for rec_idx, rectangle in enumerate(rectangles):
                new_patch = patches.Polygon(rectangle.reshape(4, 2), closed = True)
                new_patch.set_linewidth(0.6)
                new_patch.set_edgecolor(colors[rec_idx])
                new_patch.set_facecolor('none')
                ax.add_patch(new_patch)

                for dot, dot_color in zip(rectangle, ['red', 'green', 'blue', 'black']):
                    dot = patches.Circle(dot.flatten(), 0.4)
                    dot.set_facecolor(dot_color)
                    ax.add_patch(dot)

        if show_img:
            plt.tight_layout()
            plt.show()

    def get_rectangles(self, level_img, material_id = 1):
        # Create a copy of the img to manipulate it for the contour finding
        current_img = np.ndarray.copy(level_img)
        current_img = current_img.astype(np.uint8)
        current_img[current_img != material_id] = 0

        # get the contours
        contours, _ = cv2.findContours(current_img, cv2.RETR_LIST, cv2.CHAIN_APPROX_SIMPLE)

        ret_list = []
        for contour_idx, contour in enumerate(contours):
            contour_reshaped = contour.reshape((len(contour), 2))
            poly = Polygon(contour_reshaped)

            rectangles, contour_list = MathUtil.get_rectangles(contour_reshaped, poly)
            rect_data = list(map(lambda rectangle: self.create_rect_dict(rectangle.reshape((4, 2)), poly), rectangles))
            ret_list += rect_data

        return ret_list
