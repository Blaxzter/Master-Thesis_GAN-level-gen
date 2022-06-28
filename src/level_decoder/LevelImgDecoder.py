import itertools
import pickle
import time
from itertools import islice

import cv2
import matplotlib.pyplot as plt
import numpy as np
from matplotlib import patches
from shapely.geometry import Polygon

from level import Constants
from level_decoder import MathUtil
from util.Config import Config


class LevelImgDecoder:

    def __init__(self):
        self.block_data = Constants.get_sizes(print_data = False)
        self.block_data = sorted(self.block_data, key = lambda x: x[1] * x[2], reverse = True)

    def visualize_contours(self, level_img):

        level_img_8 = level_img.astype(np.uint8)
        top_value = np.max(level_img_8)
        bottom_value = np.min(level_img_8)

        fig, axd = plt.subplot_mosaic(
            [['original', 'original']] +
            [[f'thresh_{i}', f'in_img_{i}'] for i in range(bottom_value + 1, top_value + 1)],
            dpi = 300
        )

        axd['original'].imshow(level_img_8)
        axd['original'].axis('off')

        for color_idx in range(bottom_value + 1, top_value + 1):
            contour_img = np.copy(level_img_8)
            current_img = np.copy(level_img_8)

            current_img[current_img != color_idx] = 0
            axd[f'thresh_{color_idx}'].imshow(current_img)
            axd[f'thresh_{color_idx}'].axis('off')

            contours, _ = cv2.findContours(current_img, cv2.RETR_LIST, cv2.CHAIN_APPROX_SIMPLE)

            cv2.drawContours(contour_img, contours, -1, 8, 1)

            if color_idx != top_value:
                for contour in contours:

                    rectangles = [contour]
                    if len(contour) > 4:
                        rectangles, contour_list = MathUtil.get_rectangles(contour)

                    for rectangle in rectangles:
                        new_patch = patches.Polygon(rectangle.reshape(4, 2), closed = True)
                        new_patch.set_linewidth(1)
                        new_patch.set_edgecolor('Green')
                        axd[f'in_img_{color_idx}'].add_patch(new_patch)
                        contour_dims = MathUtil.get_contour_dims(rectangle)
                        print(contour_dims)


            axd[f'in_img_{color_idx}'].imshow(contour_img)
            axd[f'in_img_{color_idx}'].axis('off')

        plt.tight_layout()
        plt.show()


    def visualize_contour(self, level_img, contour_color = 0):

        level_img_8 = level_img.astype(np.uint8)
        original_img = level_img_8.copy()

        fig, axs = plt.subplots(1, 1, figsize = (10, 3), dpi = 300)
        #
        # axs[0].imshow(level_img_8)
        # axs[0].axis('off')

        level_img_8[level_img_8 != contour_color] = 0
        contours, _ = cv2.findContours(level_img_8, cv2.RETR_LIST, cv2.CHAIN_APPROX_SIMPLE)
        poly = Polygon(contours)
        required_area = poly.area

        # cv2.drawContours(level_img_8, contours, -1, 8, 1)
        # axs[1].imshow(level_img_8)
        # axs[1].axis('off')

        counter = 0
        for contour_idx, contour in enumerate(contours):

            rectangles = [contour]
            contour_list = list(contour)
            if len(contour) > 4:
                # if counter < 1:
                #     counter += 1
                #     continue
                rectangles, contour_list = MathUtil.get_rectangles(contour)

            hsv = plt.get_cmap('brg')
            dot_colors = hsv(np.linspace(0, 0.8, len(contour_list)))
            for dot_idx, (contour_point, dot_color) in enumerate(zip(contour_list, dot_colors)):
                point_flatten = contour_point.flatten()
                plt.text(point_flatten[0] + 2, point_flatten[1], str(dot_idx), color = dot_color, fontsize = 6,
                         ha = 'center', va = 'center')
                dot = patches.Circle(point_flatten, 0.4)
                dot.set_facecolor(dot_color)
                axs.add_patch(dot)

            rectangle_dict = dict()

            hsv = plt.get_cmap('brg')
            colors = hsv(np.linspace(0, 0.8, len(rectangles)))
            for rec_idx, rectangle in enumerate(rectangles):
                for dot, dot_color in zip(rectangle, ['red', 'green', 'blue', 'black']):
                    dot = patches.Circle(dot.flatten(), 0.2)
                    dot.set_facecolor(dot_color)
                    axs.add_patch(dot)

                new_patch = patches.Polygon(rectangle.reshape(4, 2), closed = True)
                new_patch.set_linewidth(0.6)
                new_patch.set_edgecolor(colors[rec_idx])
                new_patch.set_facecolor('none')
                axs.add_patch(new_patch)

                rectangle = rectangle.reshape((4, 2))

                ret_dict = dict(rectangle = rectangle)
                for key, value in MathUtil.get_contour_dims(rectangle).items():
                    ret_dict[key] = value

                rectangle_dict[rec_idx] = ret_dict

            all_space_assigned = False
            print(" ")

            # Sort by rectangle size
            rectangles = sorted(rectangle_dict.values(), key = lambda x: x['size'], reverse = True)
            blocks = self.select_blocks(rectangles = rectangles, used_blocks = [], required_area = required_area)

        axs.imshow(original_img)
        axs.axis('off')

        plt.tight_layout()
        plt.show()

    def select_blocks(self, rectangles, used_blocks, required_area, occupied_area = 0):
        # Break condition
        if required_area > occupied_area:
            return used_blocks

        # Go over each rectangle
        for rec_idx, rec in enumerate(rectangles):
            rx_1, rx_2, ry_1, ry_2 = (rec['min_x'], rec['max_x'], rec['min_y'], rec['max_y'])

            # check if rec overlaps a existing block significantly
            for used_block in used_blocks:
                block_rec = used_block['rec']
                bx_1, bx_2, by_1, by_2 = (block_rec['min_x'], block_rec['max_x'], block_rec['min_y'], block_rec['max_y'])
                dx = np.min(rx_2, bx_2) - np.max(rx_1, bx_1)
                dy = np.min(ry_2, by_2) - np.may(ry_1, by_1)
                if (dx >= 0) and (dy >= 0):
                    return dx * dy

            # Search for matching block sizes
            for possible_block in self.block_data:
                block_width, block_height = (possible_block[1], possible_block[2])

                width_divisions = rec['width'] / block_width
                height_divisions = rec['width'] / block_width

                # If the possible block is bigger then the rectangle we can continue
                if width_divisions < 1 or height_divisions < 1:
                    continue

                # Matching block found
                if width_divisions - 1 < 0.01 and height_divisions - 1 < 0.01:
                    next_rectangles = rectangles.copy()
                    next_rectangles.remove(rec)
                    new_block = dict(
                        block_type = possible_block,
                        rec = rec
                    )

                    used_blocks.append(new_block)
                    return self.select_blocks(
                        rectangles = next_rectangles,
                        used_blocks = used_blocks.copy(),
                        required_area = required_area,
                        occupied_area = occupied_area + rec['area']
                    )

            # The rectangle is bigger than any available block
            # That means it consists out of multiple smaller one
            # Divide the area into divisions of possible blocks

            # Only work with fitting blocks
            horizontal_fitting = list(filter(lambda block: block[2] < rec['height'] and block < rec['width'], self.block_data))

            # No combination found for this block
            if len(horizontal_fitting) == 0:
                continue

            for combination_amount in range(2, 5):
                combinations = itertools.product(horizontal_fitting, repeat = combination_amount)
                to_big_counter = 0
                for combination in combinations:
                    possible_block_1 = combination[0]
                    possible_block_2 = combination[1]

                    # Check if the two blocks combined can fit in the space
                    combined_height = possible_block_1[2] + possible_block_2[2]
                    height_difference = rec['height'] - combined_height
                    if abs(height_difference) < 0.1:
                        # the two blocks fit in the space

                        # TODO check if there is remaining space horizontally
                        # If so create a new rectangle there
                        # Or if the horizontal space is not filled then create a rec there


                        continue

                    if height_difference > 0:
                        # bigger means doesnt fit
                        to_big_counter += 1
                        continue


                # If all blocks combined were to big, we dont need to check more block combinations
                if to_big_counter > len(list(combinations)):
                    break

        # We tested everything and nothing worked :(
        return None








if __name__ == '__main__':
    config = Config.get_instance()
    file_filtered = config.get_pickle_file("single_structure_full_filtered")
    with open(file_filtered, 'rb') as f:
        data = pickle.load(f)

    start = time.time_ns()
    level_idx = 3
    level_img = next(islice(iter(data.values()), level_idx, level_idx + 1))['img_data']
    end = time.time_ns()
    print(end - start)

    level_img_decoder = LevelImgDecoder()
    level_img_decoder.visualize_contour(level_img, contour_color = 2)
