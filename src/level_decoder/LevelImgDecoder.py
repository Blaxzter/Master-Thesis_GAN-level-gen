import itertools
import pickle
import time
from itertools import islice

import cv2
import matplotlib.pyplot as plt
import numpy as np
from matplotlib import patches

from level import Constants
from level_decoder import MathUtil
from util.Config import Config


class LevelImgDecoder:

    def __init__(self):
        self.block_data = Constants.get_sizes(print_data = False)

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

                ret_dict = dict(rectangle = rectangle)
                for key, value in MathUtil.get_contour_dims(rectangle).items():
                    ret_dict[key] = value

                rectangle_dict[rec_idx] = ret_dict

            all_space_assigned = False
            print(" ")
            # Sort by rectangle size
            for rec_idx, rectangle in enumerate(sorted(rectangle_dict.values(), key = lambda x: x['size'], reverse = True)):
                print(rec_idx, rectangle)



        axs.imshow(original_img)
        axs.axis('off')

        plt.tight_layout()
        plt.show()



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
